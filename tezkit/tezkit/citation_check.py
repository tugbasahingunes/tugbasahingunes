"""3 · Kaynakça Kontrolcüsü (APA 7)

Metin içi atıflar ile Kaynakça listesini karşılaştırır:
- Metinde atıf yapılan ama kaynakçada olmayan kaynaklar
- Kaynakçada olup metinde hiç atıf yapılmayan kaynaklar
- Yıl uyuşmazlıkları (Yılmaz, 2019 ↔ Yılmaz (2020))
- APA 7 biçim uyarıları: alfabetik sıra, yıl parantezi, DOI biçimi, "ve diğerleri / et al.", "&" kullanımı

Türkçe ve İngilizce atıf kalıplarını tanır:
    (Yılmaz, 2020) · (Yılmaz ve Kaya, 2020) · (Yılmaz vd., 2020) · (Smith & Jones, 2019; Kaya, 2021a)
    Yılmaz (2020) · Yılmaz ve Kaya (2020) · Smith et al. (2019) · (Yılmaz, 2020, s. 15)

Kullanım:
    python -m tezkit.citation_check tez.docx
    python -m tezkit.citation_check tez.txt --kaynakca-basligi "KAYNAKLAR"
"""
from __future__ import annotations

import argparse
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

AD = r"[A-ZÇĞİÖŞÜ][A-Za-zÇĞİÖŞÜçğıöşü'’\-]+"
YIL = r"(?:\d{4}[a-z]?|t\.y\.|n\.d\.|baskıda|in press)"
ORTAK = r"(?:\s+(?:ve|&|and)\s+" + AD + r")?"
VD = r"(?:\s+(?:vd\.|ve diğerleri|et al\.))?"

PARANTEZ = re.compile(r"\(([^()]*?\d{4}[a-z]?[^()]*?)\)")
TEK = re.compile(rf"(?P<ad>{AD}){ORTAK}{VD},\s*(?P<yil>{YIL})")
ANLATI = re.compile(rf"(?P<ad>{AD}){ORTAK}{VD}\s*\((?P<yil>{YIL})(?:,\s*s\.\s*\d+)?\)")
KAYNAK = re.compile(rf"^(?P<ad>{AD})(?:,\s.*?|\.\s*)\((?P<yil>{YIL})(?:,[^)]*)?\)")
BASLIKLAR = ["KAYNAKÇA", "KAYNAKLAR", "REFERENCES", "BIBLIOGRAPHY"]
STOP = {"Tablo", "Şekil", "Ek", "Bölüm", "Madde", "Kanun", "Yönetmelik", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs",
        "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık", "Sayı", "Cilt"}


def anahtar(ad: str) -> str:
    s = unicodedata.normalize("NFKD", ad.replace("ı", "i").replace("İ", "I")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z]", "", s)


@dataclass
class Atif:
    ad: str
    yil: str
    baglam: str


@dataclass
class Sonuc:
    atiflar: list[Atif]
    kaynaklar: list[tuple[str, str, str]]  # (ad, yıl, tam satır)
    eksik: list[Atif] = field(default_factory=list)
    kullanilmayan: list[str] = field(default_factory=list)
    yil_uyusmazligi: list[str] = field(default_factory=list)
    bicim: list[str] = field(default_factory=list)

    def markdown(self) -> str:
        s = ["# Kaynakça Kontrol Raporu\n",
             f"- Metin içi atıf: **{len(self.atiflar)}** (benzersiz {len({(anahtar(a.ad), a.yil) for a in self.atiflar})})",
             f"- Kaynakça girdisi: **{len(self.kaynaklar)}**",
             f"- Kaynakçada olmayan atıf: **{len(self.eksik)}**",
             f"- Metinde kullanılmayan kaynak: **{len(self.kullanilmayan)}**",
             f"- Yıl uyuşmazlığı: **{len(self.yil_uyusmazligi)}**",
             f"- Biçim uyarısı: **{len(self.bicim)}**\n"]
        if self.eksik:
            s.append("## Kaynakçada bulunmayan atıflar\n| Atıf | Bağlam |\n|---|---|")
            goruldu = set()
            for a in self.eksik:
                k = (anahtar(a.ad), a.yil)
                if k in goruldu:
                    continue
                goruldu.add(k)
                s.append(f"| {a.ad}, {a.yil} | …{a.baglam}… |")
        for baslik, liste in [("Metinde atıf yapılmayan kaynaklar", self.kullanilmayan),
                              ("Yıl uyuşmazlıkları", self.yil_uyusmazligi), ("APA 7 biçim uyarıları", self.bicim)]:
            if liste:
                s.append(f"\n## {baslik}")
                s += [f"- {x}" for x in liste]
        return "\n".join(s)


def metni_al(yol: str | Path) -> list[str]:
    yol = Path(yol)
    if yol.suffix.lower() == ".docx":
        from docx import Document
        return [p.text for p in Document(str(yol)).paragraphs]
    return yol.read_text(encoding="utf-8").splitlines()


def bol(satirlar: list[str], baslik: str | None = None) -> tuple[str, list[str]]:
    hedef = [baslik.upper()] if baslik else BASLIKLAR
    for i in range(len(satirlar) - 1, -1, -1):
        if satirlar[i].strip().upper() in hedef:
            return "\n".join(satirlar[:i]), [x.strip() for x in satirlar[i + 1:] if x.strip()]
    raise ValueError("Kaynakça başlığı bulunamadı. --kaynakca-basligi ile belirtin.")


def atiflari_bul(metin: str) -> list[Atif]:
    out = []
    for m in PARANTEZ.finditer(metin):
        for parca in m.group(1).split(";"):
            t = TEK.search(parca.strip())
            if t and t.group("ad") not in STOP:
                out.append(Atif(t.group("ad"), t.group("yil"), metin[max(0, m.start() - 40):m.end() + 10].replace("\n", " ")))
    for m in ANLATI.finditer(metin):
        if m.group("ad") not in STOP:
            out.append(Atif(m.group("ad"), m.group("yil"), metin[max(0, m.start() - 30):m.end() + 10].replace("\n", " ")))
    return out


def kaynaklari_bul(satirlar: list[str]) -> tuple[list[tuple[str, str, str]], list[str]]:
    out, bicim = [], []
    for s in satirlar:
        m = KAYNAK.match(s)
        if not m:
            bicim.append(f"Tanınamayan kaynak satırı (Soyad, A. (Yıl). biçiminde olmalı): “{s[:70]}”")
            continue
        out.append((m.group("ad"), m.group("yil"), s))
        if re.search(r"doi:\s*10\.", s, re.I) or re.search(r"dx\.doi\.org", s):
            bicim.append(f"{m.group('ad')} ({m.group('yil')}): DOI https://doi.org/10.xxxx biçiminde yazılmalı.")
        if re.search(r"\bet al\b|\bvd\.", s):
            bicim.append(f"{m.group('ad')} ({m.group('yil')}): Kaynakçada “vd./et al.” kullanılmaz; APA 7'de 20 yazara kadar tüm yazarlar yazılır.")
        if not s.rstrip().endswith((".", ")")) and "doi" not in s.lower() and "http" not in s:
            bicim.append(f"{m.group('ad')} ({m.group('yil')}): Kaynak satırı nokta ile bitmeli.")
    # alfabetik sıra
    anahtarlar = [anahtar(a) for a, _, _ in out]
    for i in range(1, len(anahtarlar)):
        if anahtarlar[i] < anahtarlar[i - 1]:
            bicim.append(f"Alfabetik sıra bozuk: “{out[i][0]} ({out[i][1]})”, “{out[i-1][0]} ({out[i-1][1]})” kaynağından önce gelmeli.")
    return out, bicim


def denetle(yol: str | Path, kaynakca_basligi: str | None = None) -> Sonuc:
    satirlar = metni_al(yol)
    metin, ks = bol(satirlar, kaynakca_basligi)
    atiflar = atiflari_bul(metin)
    kaynaklar, bicim = kaynaklari_bul(ks)
    r = Sonuc(atiflar, kaynaklar, bicim=bicim)

    k_set = {(anahtar(a), y) for a, y, _ in kaynaklar}
    k_yillar: dict[str, set] = {}
    for a, y, _ in kaynaklar:
        k_yillar.setdefault(anahtar(a), set()).add(y)
    a_set = {(anahtar(a.ad), a.yil) for a in atiflar}

    for a in atiflar:
        if (anahtar(a.ad), a.yil) not in k_set:
            r.eksik.append(a)
            ky = k_yillar.get(anahtar(a.ad))
            if ky:
                msg = f"Metinde {a.ad} ({a.yil}), kaynakçada {a.ad} ({', '.join(sorted(ky))})"
                if msg not in r.yil_uyusmazligi:
                    r.yil_uyusmazligi.append(msg)
    for a, y, tam in kaynaklar:
        if (anahtar(a), y) not in a_set:
            r.kullanilmayan.append(f"{a} ({y}): {tam[:90]}")
    # metin içi biçim
    for m in re.finditer(rf"\({AD}\s*&\s*{AD},", metin):
        pass  # parantez içinde & APA'da doğrudur (İngilizce)
    for m in re.finditer(rf"{AD}\s*&\s*{AD}\s*\(\d{{4}}", metin):
        r.bicim.append(f"Anlatı atfında “&” yerine “ve/and” kullanılmalı: “{m.group()}…”")
    for m in re.finditer(rf"\({AD},\s*{AD},\s*{AD}", metin):
        r.bicim.append(f"3+ yazarlı atıfta APA 7: ilk yazar + vd./et al.: “{m.group()}…”")
    return r


def main():
    ap = argparse.ArgumentParser(description="APA 7 kaynakça kontrolü")
    ap.add_argument("dosya")
    ap.add_argument("--kaynakca-basligi")
    ap.add_argument("--cikti")
    a = ap.parse_args()
    md = denetle(a.dosya, a.kaynakca_basligi).markdown()
    if a.cikti:
        Path(a.cikti).write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
