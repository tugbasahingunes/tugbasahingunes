"""6 · Literatür Tablosu Oluşturucu

Bir klasördeki makale PDF'lerinden literatür özet tablosu (Excel) çıkarır:
başlık, yazar(lar), yıl, DOI, dergi, anahtar kelimeler, özet, yöntem türü, örneklem büyüklüğü,
kullanılan istatistiksel teknikler, ülke/bağlam. Boş bırakılan "Temel bulgu" ve "Tezimle ilişkisi"
sütunları araştırmacının kendi notları içindir.

Çıkarım kural tabanlıdır (yapay zekâ kullanmaz, internete bağlanmaz). PDF'lerin yapısı farklı olduğu için
sonuçlar mutlaka kontrol edilmelidir; tablo literatür okumasını HIZLANDIRIR, yerine geçmez.
DOI bulunursa CrossRef ile doğrulama isteğe bağlıdır (--crossref).

Kullanım:
    python -m tezkit.literature_table makaleler/ --cikti literatur.xlsx
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd
from pypdf import PdfReader

DOI = re.compile(r"\b(10\.\d{4,9}/[^\s\"<>]+)", re.I)
YIL = re.compile(r"\b(19[5-9]\d|20[0-4]\d)\b")
OZET_BAS = re.compile(r"\b(abstract|öz|özet)\b[:.\s]*", re.I)
OZET_SON = re.compile(r"\b(keywords|key words|anahtar kelimeler|anahtar sözcükler|introduction|giriş|1\.\s+giriş|1\.\s+introduction)\b", re.I)
ANAHTAR = re.compile(r"(keywords|key words|anahtar kelimeler|anahtar sözcükler)\s*[:—–-]?\s*(.{5,250}?)(?:\n\n|\n[A-ZÇĞİÖŞÜ1-9]|$)", re.I | re.S)
ORNEKLEM = re.compile(r"\b(?:n\s*=\s*|N\s*=\s*)([\d.,]{2,7})|\b([\d.,]{2,7})(?:\s+[A-Za-zçğıöşüÇĞİÖŞÜ]+)?\s+(?:participants|respondents|students|evaluations|studies|interviewees|katılımcı|öğrenci|kişi|yetişkin|ebeveyn|öğretmen|kadın|erkek|genç|çalışma)", re.I)

YONTEM = {
    "Nicel": ["survey", "questionnaire", "regression", "anova", "t-test", "anket", "ölçek", "regresyon", "korelasyon",
              "structural equation", "yapısal eşitlik", "quantitative", "nicel"],
    "Nitel": ["interview", "focus group", "thematic analysis", "grounded theory", "phenomenolog", "görüşme",
              "odak grup", "tematik analiz", "olgubilim", "nitel", "qualitative", "içerik analizi"],
    "Karma": ["mixed method", "mixed-method", "karma yöntem"],
    "Derleme/Meta-analiz": ["systematic review", "meta-analysis", "meta analysis", "sistematik derleme", "meta-analiz", "literature review"],
    "Deneysel": ["randomized", "randomised", "experimental design", "control group", "deneysel", "kontrol grubu", "rct"],
}
TEKNIK = ["regression", "logistic regression", "multilevel", "structural equation", "SEM", "ANOVA", "MANOVA", "t-test",
          "chi-square", "correlation", "factor analysis", "CFA", "EFA", "difference-in-differences", "propensity score",
          "fixed effects", "panel data", "Oaxaca", "machine learning", "thematic analysis", "content analysis",
          "regresyon", "lojistik regresyon", "çok düzeyli", "yapısal eşitlik", "faktör analizi", "doğrulayıcı faktör",
          "korelasyon", "ki-kare", "içerik analizi", "tematik analiz", "panel veri"]
ULKELER = ["Türkiye", "Turkey", "Türkiye's", "Finland", "Germany", "United Kingdom", "UK", "United States", "USA", "Italy", "Spain",
           "France", "Netherlands", "Sweden", "European Union", "EU", "OECD", "Europe", "China", "India", "Brazil"]


def pdf_metin(yol: Path, max_sayfa: int = 4) -> tuple[str, dict]:
    r = PdfReader(str(yol))
    meta = {k.strip("/"): v for k, v in (r.metadata or {}).items()} if r.metadata else {}
    metin = "\n".join((p.extract_text() or "") for p in r.pages[:max_sayfa])
    return metin, meta


def _ilk(r, s, grup=1):
    m = r.search(s)
    return m.group(grup).strip() if m else ""


def cikar(yol: Path) -> dict:
    metin, meta = pdf_metin(yol)
    satirlar = [x.strip() for x in metin.splitlines() if x.strip()]
    baslik = (meta.get("Title") or "").strip()
    if not baslik or len(baslik) < 10 or baslik.lower().endswith((".doc", ".docx", ".pdf")):
        aday = [s for s in satirlar[:15] if 15 < len(s) < 220 and not DOI.search(s) and not re.search(r"journal|vol\.|cilt|sayı|issn|http", s, re.I)]
        baslik = max(aday[:5], key=len) if aday else yol.stem
    yazar = (meta.get("Author") or "").strip()
    doi = _ilk(DOI, metin).rstrip(".,;)")
    yillar = [int(y) for y in YIL.findall(metin[:3000])]
    yil = str(max(set(yillar), key=yillar.count)) if yillar else ""

    ozet = ""
    m = OZET_BAS.search(metin)
    if m:
        kalan = metin[m.end():]
        son = OZET_SON.search(kalan)
        ozet = re.sub(r"\s+", " ", kalan[: son.start() if son else 1500]).strip()[:1500]
    anahtar = ""
    m = ANAHTAR.search(metin)
    if m:
        anahtar = re.sub(r"\s+", " ", m.group(2)).strip(" .")

    dusuk = metin.lower()
    yontem = [k for k, kel in YONTEM.items() if any(w in dusuk for w in kel)]
    if "Karma" in yontem:
        yontem = ["Karma"] + [y for y in yontem if y not in ("Nicel", "Nitel", "Karma")]
    teknik = sorted({t for t in TEKNIK if re.search(r"\b" + re.escape(t.lower()), dusuk)})
    n = ""
    for m in ORNEKLEM.finditer(metin):
        v = (m.group(1) or m.group(2)).replace(".", "").replace(",", "")
        if v.isdigit() and 10 <= int(v) <= 10_000_000:
            n = v
            break
    ulke = sorted({u for u in ULKELER if re.search(r"\b" + re.escape(u) + r"\b", metin)})

    return {"Dosya": yol.name, "Başlık": baslik, "Yazar(lar)": yazar, "Yıl": yil, "DOI": doi,
            "Anahtar kelimeler": anahtar, "Yöntem türü": ", ".join(yontem) or "Belirlenemedi",
            "Örneklem (n)": n, "Analiz teknikleri": ", ".join(teknik), "Ülke/bağlam": ", ".join(ulke[:5]),
            "Özet": ozet, "Temel bulgu (siz doldurun)": "", "Tezimle ilişkisi (siz doldurun)": ""}


def crossref_dogrula(satir: dict) -> dict:
    """DOI varsa CrossRef'ten başlık/yazar/yıl/dergi alır (internet gerekir)."""
    if not satir.get("DOI"):
        return satir
    try:
        import requests
        r = requests.get(f"https://api.crossref.org/works/{satir['DOI']}", timeout=10)
        if r.ok:
            m = r.json()["message"]
            satir["Başlık"] = (m.get("title") or [satir["Başlık"]])[0]
            satir["Yazar(lar)"] = "; ".join(f"{a.get('family','')}, {a.get('given','')[:1]}." for a in m.get("author", [])) or satir["Yazar(lar)"]
            yil = (m.get("issued", {}).get("date-parts") or [[None]])[0][0]
            satir["Yıl"] = str(yil or satir["Yıl"])
            satir["Dergi"] = (m.get("container-title") or [""])[0]
    except Exception:
        pass
    return satir


def apa_kunye(s: dict) -> str:
    y = s.get("Yazar(lar)") or "Yazar"
    k = f"{y} ({s.get('Yıl') or 't.y.'}). {s.get('Başlık')}."
    if s.get("Dergi"):
        k += f" {s['Dergi']}."
    if s.get("DOI"):
        k += f" https://doi.org/{s['DOI']}"
    return k


def tablo(klasor: str | Path, crossref: bool = False) -> pd.DataFrame:
    pdfler = sorted(Path(klasor).glob("*.pdf"))
    if not pdfler:
        raise FileNotFoundError(f"{klasor} klasöründe PDF bulunamadı.")
    satirlar = []
    for p in pdfler:
        try:
            s = cikar(p)
        except Exception as e:
            s = {"Dosya": p.name, "Başlık": f"OKUNAMADI: {e}"}
        if crossref:
            s = crossref_dogrula(s)
        s["APA künye taslağı"] = apa_kunye(s)
        satirlar.append(s)
    df = pd.DataFrame(satirlar)
    return df.sort_values("Yıl", ascending=False, na_position="last") if "Yıl" in df else df


def excel_yaz(df: pd.DataFrame, cikti: str | Path):
    with pd.ExcelWriter(cikti, engine="openpyxl") as w:
        df.to_excel(w, sheet_name="Literatür", index=False)
        ws = w.sheets["Literatür"]
        genislik = {"Başlık": 50, "Özet": 80, "APA künye taslağı": 60, "Analiz teknikleri": 30}
        from openpyxl.styles import Alignment, Font, PatternFill
        for i, c in enumerate(df.columns, 1):
            col = ws.cell(1, i).column_letter
            ws.column_dimensions[col].width = genislik.get(c, 18)
            ws.cell(1, i).font = Font(bold=True, color="FFFFFF")
            ws.cell(1, i).fill = PatternFill("solid", fgColor="1F4E78")
        for row in ws.iter_rows(min_row=2):
            for c in row:
                c.alignment = Alignment(wrap_text=True, vertical="top")
        ws.freeze_panes = "C2"
        ws.auto_filter.ref = ws.dimensions
        ozet = df["Yöntem türü"].value_counts().rename_axis("Yöntem").reset_index(name="Makale sayısı") if "Yöntem türü" in df else pd.DataFrame()
        ozet.to_excel(w, sheet_name="Yöntem dağılımı", index=False)


def main():
    ap = argparse.ArgumentParser(description="PDF'lerden literatür tablosu")
    ap.add_argument("klasor")
    ap.add_argument("--cikti", default="literatur_tablosu.xlsx")
    ap.add_argument("--crossref", action="store_true", help="DOI ile CrossRef doğrulaması (internet gerekir)")
    a = ap.parse_args()
    df = tablo(a.klasor, a.crossref)
    excel_yaz(df, a.cikti)
    print(df[["Dosya", "Başlık", "Yıl", "Yöntem türü", "Örneklem (n)"]].to_string(index=False))


if __name__ == "__main__":
    main()
