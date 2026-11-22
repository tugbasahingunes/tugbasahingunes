"""1 · Tez Biçim Denetleyici

Bir .docx dosyasını üniversite profiline (YAML) göre denetler:
sayfa boyutu ve kenar boşlukları, gövde metni fontu/punto/satır aralığı/hizalama,
başlık numaralandırması, tablo ve şekil başlıkları, zorunlu bölümler, boş paragraflar.

Kullanım:
    python -m tezkit.format_check tez.docx --profil profiles/genel_apa.yaml
"""
from __future__ import annotations

import argparse
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Length

A4_CM = (21.0, 29.7)
HIZALAMA = {"iki_yana": WD_ALIGN_PARAGRAPH.JUSTIFY, "sol": WD_ALIGN_PARAGRAPH.LEFT}
NUMARALI_BASLIK = re.compile(r"^\d+(\.\d+)*\.?\s+\S")


@dataclass
class Bulgu:
    seviye: str  # "HATA" | "UYARI" | "BİLGİ"
    kategori: str
    mesaj: str
    konum: str = ""


@dataclass
class Rapor:
    dosya: str
    profil: str
    bulgular: list[Bulgu] = field(default_factory=list)
    istatistik: dict = field(default_factory=dict)

    def ekle(self, *a, **k):
        self.bulgular.append(Bulgu(*a, **k))

    @property
    def hata_sayisi(self):
        return sum(b.seviye == "HATA" for b in self.bulgular)

    @property
    def uyari_sayisi(self):
        return sum(b.seviye == "UYARI" for b in self.bulgular)

    def puan(self) -> int:
        """0–100 arası basit uygunluk puanı."""
        return max(0, 100 - 5 * self.hata_sayisi - 1 * self.uyari_sayisi)

    def markdown(self) -> str:
        s = [f"# Biçim Denetim Raporu\n", f"**Dosya:** {self.dosya}  ", f"**Profil:** {self.profil}  ",
             f"**Uygunluk puanı:** {self.puan()}/100 · {self.hata_sayisi} hata · {self.uyari_sayisi} uyarı\n"]
        for k, v in self.istatistik.items():
            s.append(f"- {k}: {v}")
        s.append("\n| Seviye | Kategori | Konum | Açıklama |\n|---|---|---|---|")
        for b in self.bulgular:
            s.append(f"| {b.seviye} | {b.kategori} | {b.konum} | {b.mesaj} |")
        return "\n".join(s)


def cm(x: Length | None) -> float | None:
    return None if x is None else round(x.cm, 2)


def _kisa(t: str, n: int = 50) -> str:
    t = t.strip().replace("|", "/")
    return t if len(t) <= n else t[:n] + "…"


def _etkin_font(par, doc) -> tuple[str | None, float | None]:
    """Paragrafın etkin font adını ve puntosunu bulur (run → paragraf stili → Normal)."""
    names, sizes = set(), set()
    for r in par.runs:
        if not r.text.strip():
            continue
        names.add(r.font.name or par.style.font.name or doc.styles["Normal"].font.name)
        sz = r.font.size or par.style.font.size or doc.styles["Normal"].font.size
        sizes.add(sz.pt if sz else None)
    name = names.pop() if len(names) == 1 else (None if not names else "karışık:" + ",".join(sorted(map(str, names))))
    size = sizes.pop() if len(sizes) == 1 else (None if not sizes else -1)
    return name, size


def _satir_araligi(par, doc):
    v = par.paragraph_format.line_spacing
    if v is None:
        v = par.style.paragraph_format.line_spacing
    if v is None:
        v = doc.styles["Normal"].paragraph_format.line_spacing
    if isinstance(v, Length):  # tam değer (pt) verilmiş
        return round(v.pt / 12, 2)
    return v


def _hizalama(par, doc):
    a = par.paragraph_format.alignment
    if a is None:
        a = par.style.paragraph_format.alignment
    if a is None:
        a = doc.styles["Normal"].paragraph_format.alignment
    return a


def denetle(docx_yolu: str | Path, profil_yolu: str | Path) -> Rapor:
    prof = yaml.safe_load(Path(profil_yolu).read_text(encoding="utf-8"))
    doc = Document(str(docx_yolu))
    rap = Rapor(dosya=Path(docx_yolu).name, profil=prof.get("ad", Path(profil_yolu).stem))

    # --- Sayfa düzeni
    tol = prof["sayfa"].get("tolerans_cm", 0.1)
    for i, sec in enumerate(doc.sections, 1):
        w, h = cm(sec.page_width), cm(sec.page_height)
        if prof["sayfa"].get("boyut") == "A4" and w and h and (abs(w - A4_CM[0]) > tol or abs(h - A4_CM[1]) > tol):
            rap.ekle("HATA", "Sayfa", f"Sayfa boyutu {w}×{h} cm, A4 (21×29,7) olmalı.", f"Bölüm {i}")
        for ad, attr in [("sol", "left_margin"), ("sag", "right_margin"), ("ust", "top_margin"), ("alt", "bottom_margin")]:
            beklenen = prof["sayfa"]["kenar_cm"][ad]
            gercek = cm(getattr(sec, attr))
            if gercek is not None and abs(gercek - beklenen) > tol:
                rap.ekle("HATA", "Kenar boşluğu", f"{ad.capitalize()} kenar {gercek} cm, {beklenen} cm olmalı.", f"Bölüm {i}")

    g = prof["govde"]
    baslik_metinleri, tablo_basliklari, sekil_basliklari = [], [], []
    bos_ust_uste, govde_sayisi = 0, 0
    t_kalip = re.compile(prof.get("tablo_baslik_kalibi", r"^Tablo\s+\d+"))
    s_kalip = re.compile(prof.get("sekil_baslik_kalibi", r"^Şekil\s+\d+"))

    for idx, p in enumerate(doc.paragraphs, 1):
        txt = p.text.strip()
        stil = p.style.name if p.style is not None else ""
        konum = f"¶{idx} “{_kisa(txt)}”"
        if not txt:
            bos_ust_uste += 1
            if bos_ust_uste == 3:
                rap.ekle("UYARI", "Boşluk", "Üst üste 3+ boş paragraf: boşluğu paragraf aralığı ile verin.", f"¶{idx}")
            continue
        bos_ust_uste = 0

        if stil.lower().startswith(("heading", "başlık")) or stil == "Title":
            baslik_metinleri.append(txt)
            if prof["baslik"].get("numarali") and stil.lower() not in ("heading 1", "başlık 1", "title"):
                if not NUMARALI_BASLIK.match(txt):
                    rap.ekle("UYARI", "Başlık", "Alt başlık numarasız (ör. “2.1. Yöntem”).", konum)
            f, _ = _etkin_font(p, doc)
            if f and f != prof["baslik"]["font"] and not f.startswith("karışık"):
                rap.ekle("UYARI", "Başlık", f"Başlık fontu {f}, {prof['baslik']['font']} olmalı.", konum)
            continue

        if txt.lower().startswith("tablo"):
            tablo_basliklari.append(txt)
            if not t_kalip.match(txt):
                rap.ekle("HATA", "Tablo başlığı", "Biçim “Tablo 3.1. Açıklama” olmalı.", konum)
            continue
        if txt.lower().startswith("şekil") or txt.lower().startswith("sekil"):
            sekil_basliklari.append(txt)
            if not s_kalip.match(txt):
                rap.ekle("HATA", "Şekil başlığı", "Biçim “Şekil 2.1. Açıklama” olmalı.", konum)
            continue

        # Gövde metni
        govde_sayisi += 1
        f, sz = _etkin_font(p, doc)
        if f and f != g["font"]:
            rap.ekle("HATA", "Font", f"Font {f}, {g['font']} olmalı.", konum)
        if sz not in (None, g["punto"]):
            rap.ekle("HATA", "Punto", f"Punto {'karışık' if sz == -1 else sz}, {g['punto']} olmalı.", konum)
        la = _satir_araligi(p, doc)
        if la is not None and abs(float(la) - g["satir_araligi"]) > 0.05:
            rap.ekle("HATA", "Satır aralığı", f"Satır aralığı {la}, {g['satir_araligi']} olmalı.", konum)
        al = _hizalama(p, doc)
        if len(txt) > 120 and al is not None and al != HIZALAMA.get(g["hizalama"]):
            rap.ekle("UYARI", "Hizalama", f"Paragraf {g['hizalama'].replace('_', ' ')} hizalanmalı.", konum)
        if "  " in p.text:
            rap.ekle("UYARI", "Boşluk", "Çift boşluk karakteri var.", konum)

    # Numara sırası (Tablo 1, 2, 3...) kontrolü
    for ad, liste in [("Tablo", tablo_basliklari), ("Şekil", sekil_basliklari)]:
        nolar = [re.search(r"\d+(\.\d+)*", x).group() for x in liste if re.search(r"\d", x)]
        if len(nolar) != len(set(nolar)):
            rap.ekle("HATA", f"{ad} numarası", f"Tekrarlanan {ad.lower()} numarası: {sorted({n for n in nolar if nolar.count(n) > 1})}")

    # Word tabloları ile başlık sayısı
    if len(doc.tables) and len(tablo_basliklari) < len(doc.tables):
        rap.ekle("UYARI", "Tablo başlığı", f"Belgede {len(doc.tables)} tablo var ama {len(tablo_basliklari)} tablo başlığı bulundu.")

    # Zorunlu bölümler
    ust = [b.upper().replace("İ", "İ") for b in baslik_metinleri] + [p.text.strip().upper() for p in doc.paragraphs if p.text.isupper()]
    for bol in prof.get("zorunlu_bolumler", []):
        if not any(bol in x for x in ust):
            rap.ekle("HATA", "Zorunlu bölüm", f"“{bol}” bölümü bulunamadı.")

    rap.istatistik = {"Paragraf (gövde)": govde_sayisi, "Başlık": len(baslik_metinleri), "Tablo": len(doc.tables),
                      "Tablo başlığı": len(tablo_basliklari), "Şekil başlığı": len(sekil_basliklari),
                      "Bölüm (section)": len(doc.sections)}
    if not rap.bulgular:
        rap.ekle("BİLGİ", "Sonuç", "Profilde tanımlı kurallara göre sorun bulunmadı.")
    return rap


def main():
    ap = argparse.ArgumentParser(description="Tez biçim denetleyici")
    ap.add_argument("docx")
    ap.add_argument("--profil", default=str(Path(__file__).parent.parent / "profiles" / "genel_apa.yaml"))
    ap.add_argument("--cikti", help="Raporu .md olarak kaydet")
    a = ap.parse_args()
    r = denetle(a.docx, a.profil)
    md = r.markdown()
    if a.cikti:
        Path(a.cikti).write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
