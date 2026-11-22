"""4 · Ölçek Puanlama Aracı

Likert tipi ölçekleri bir YAML tanımına göre puanlar:
- Ters maddeleri çevirir (ör. 5'li Likert'te 1↔5)
- Alt boyut ve toplam puanları hesaplar (ortalama veya toplam)
- Eksik veri kuralı: bir alt boyutta en az %X madde yanıtlanmışsa ortalama, aksi halde boş
- Aralık dışı değerleri (ör. 5'li ölçekte 7) raporlar
- Kesme puanlarına göre düzey etiketi (düşük/orta/yüksek) verir
- Alt boyut güvenirlikleri (Cronbach α)

Kullanım:
    python -m tezkit.scale_scoring veri.xlsx --tanim samples/olcek_tanimi.yaml --cikti puanlanmis.xlsx
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from .survey_report import cronbach, oku


def puanla(df: pd.DataFrame, tanim: dict) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    """(puanlanmış_df, özet_tablosu, uyarılar) döner."""
    df = df.copy()
    lo, hi = tanim["min"], tanim["max"]
    yontem = tanim.get("yontem", "ortalama")
    min_oran = tanim.get("min_yanit_orani", 0.8)
    uyarilar: list[str] = []
    tum_maddeler = sorted({m for b in tanim["boyutlar"].values() for m in b["maddeler"]})

    eksik_sutun = [m for m in tum_maddeler if m not in df.columns]
    if eksik_sutun:
        raise ValueError(f"Veride bulunmayan maddeler: {eksik_sutun}")

    for m in tum_maddeler:
        df[m] = pd.to_numeric(df[m], errors="coerce")
        disari = df[(df[m] < lo) | (df[m] > hi)].index.tolist()
        if disari:
            uyarilar.append(f"{m}: {len(disari)} aralık dışı değer ({lo}-{hi}) boş kabul edildi (satır {[i + 2 for i in disari[:5]]}{'…' if len(disari) > 5 else ''}).")
            df.loc[disari, m] = np.nan

    ters = set(tanim.get("ters_maddeler", []))
    calisma = df[tum_maddeler].copy()
    for m in ters:
        calisma[m] = (lo + hi) - calisma[m]

    ozet = []
    for ad, b in tanim["boyutlar"].items():
        maddeler = b["maddeler"]
        blok = calisma[maddeler]
        yanit = blok.notna().sum(axis=1)
        yeterli = yanit >= np.ceil(min_oran * len(maddeler))
        puan = blok.mean(axis=1) if yontem == "ortalama" else blok.mean(axis=1) * len(maddeler)
        df[ad] = puan.where(yeterli).round(3)
        n_eksik = int((~yeterli).sum())
        if n_eksik:
            uyarilar.append(f"{ad}: {n_eksik} katılımcı yetersiz yanıt nedeniyle puanlanmadı (en az %{int(min_oran*100)} gerekli).")
        if "kesme" in b or "kesme" in tanim:
            kes = b.get("kesme", tanim.get("kesme"))
            df[f"{ad}_duzey"] = pd.cut(df[ad], bins=[-np.inf] + kes["sinirlar"] + [np.inf], labels=kes["etiketler"])
        ozet.append({"Boyut": ad, "Madde": len(maddeler), "Ters madde": ", ".join(sorted(ters & set(maddeler))) or "-",
                     "n": int(df[ad].notna().sum()), "Ort.": round(df[ad].mean(), 2), "SS": round(df[ad].std(), 2),
                     "Min": round(df[ad].min(), 2), "Maks": round(df[ad].max(), 2), "α": round(cronbach(calisma[maddeler]), 2)})

    if tanim.get("toplam"):
        ad = tanim["toplam"]
        blok = calisma[tum_maddeler]
        yeterli = blok.notna().sum(axis=1) >= np.ceil(min_oran * len(tum_maddeler))
        puan = blok.mean(axis=1) if yontem == "ortalama" else blok.mean(axis=1) * len(tum_maddeler)
        df[ad] = puan.where(yeterli).round(3)
        ozet.append({"Boyut": ad + " (toplam)", "Madde": len(tum_maddeler), "Ters madde": ", ".join(sorted(ters)) or "-",
                     "n": int(df[ad].notna().sum()), "Ort.": round(df[ad].mean(), 2), "SS": round(df[ad].std(), 2),
                     "Min": round(df[ad].min(), 2), "Maks": round(df[ad].max(), 2), "α": round(cronbach(blok), 2)})
    return df, pd.DataFrame(ozet), uyarilar


def main():
    ap = argparse.ArgumentParser(description="Likert ölçek puanlama")
    ap.add_argument("veri")
    ap.add_argument("--tanim", required=True)
    ap.add_argument("--cikti", default="puanlanmis.xlsx")
    a = ap.parse_args()
    df, _ = oku(a.veri)
    tanim = yaml.safe_load(Path(a.tanim).read_text(encoding="utf-8"))
    out, ozet, uy = puanla(df, tanim)
    with pd.ExcelWriter(a.cikti) as w:
        out.to_excel(w, sheet_name="Puanlar", index=False)
        ozet.to_excel(w, sheet_name="Özet", index=False)
        pd.DataFrame({"Uyarı": uy or ["Uyarı yok"]}).to_excel(w, sheet_name="Uyarılar", index=False)
    print(ozet.to_string(index=False))
    print("\n".join(uy))


if __name__ == "__main__":
    main()
