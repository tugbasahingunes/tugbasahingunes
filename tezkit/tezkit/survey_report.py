"""2 · Anket → Bulgular Bölümü

SPSS (.sav), Excel (.xlsx) veya CSV veri dosyasından tez "Bulgular" bölümü taslağı üretir:
- Demografik frekans tabloları
- Ölçek güvenirliği (Cronbach alfa, madde silinirse alfa)
- Normallik (Shapiro-Wilk / Kolmogorov-Smirnov, çarpıklık-basıklık)
- Doğru testin otomatik seçimi: t-testi / Mann-Whitney U, ANOVA / Kruskal-Wallis,
  Pearson / Spearman korelasyon, ki-kare
- Etki büyüklükleri (Cohen d, eta kare, r, Cramér V)
- APA 7 biçiminde tablolar ve Türkçe yorum taslağı içeren .docx

Yorumlar TASLAKTIR: araştırmacı tarafından okunmalı, alanyazınla tartışılmalıdır.

Kullanım:
    python -m tezkit.survey_report veri.sav --olcek "Memnuniyet=S1,S2,S3,S4,S5" \
        --gruplar cinsiyet,egitim --surekli yas --cikti bulgular.docx
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, Cm


# ---------------------------------------------------------------- veri okuma
def oku(yol: str | Path) -> tuple[pd.DataFrame, dict]:
    """Veriyi okur; SPSS ise değer etiketlerini uygular. (df, değişken_etiketleri) döner."""
    yol = Path(yol)
    etiket = {}
    if yol.suffix.lower() == ".sav":
        import pyreadstat
        df, meta = pyreadstat.read_sav(str(yol), apply_value_formats=True)
        etiket = dict(zip(meta.column_names, meta.column_labels or [None] * len(meta.column_names)))
    elif yol.suffix.lower() in (".xlsx", ".xls"):
        df = pd.read_excel(yol)
    else:
        df = pd.read_csv(yol)
    return df, {k: v for k, v in etiket.items() if v}


# ---------------------------------------------------------------- istatistik yardımcıları
def p_apa(p: float) -> str:
    return "p < .001" if p < .001 else f"p = {p:.3f}".replace("0.", ".")


def f2(x: float, d: int = 2) -> str:
    return f"{x:.{d}f}"


def cronbach(items: pd.DataFrame) -> float:
    items = items.dropna()
    k = items.shape[1]
    if k < 2:
        return float("nan")
    return k / (k - 1) * (1 - items.var(ddof=1).sum() / items.sum(axis=1).var(ddof=1))


def alfa_yorum(a: float) -> str:
    if a >= .90: return "mükemmel"
    if a >= .80: return "yüksek"
    if a >= .70: return "kabul edilebilir"
    if a >= .60: return "sınırda"
    return "düşük"


def normallik(x: pd.Series) -> dict:
    x = x.dropna()
    n = len(x)
    if n < 3:
        return {"test": "-", "stat": np.nan, "p": np.nan, "skew": np.nan, "kurt": np.nan, "normal": False, "n": n}
    if n <= 50:
        st, p, test = *stats.shapiro(x), "Shapiro-Wilk"
    else:
        z = (x - x.mean()) / x.std(ddof=1)
        st, p = stats.kstest(z, "norm")
        test = "Kolmogorov-Smirnov"
    skew, kurt = stats.skew(x, bias=False), stats.kurtosis(x, bias=False)
    # Tez pratiğinde sık kullanılan ölçüt: çarpıklık ve basıklık ±1.5 aralığında ise normal kabul (Tabachnick & Fidell, 2013)
    normal = (p > .05) or (abs(skew) <= 1.5 and abs(kurt) <= 1.5)
    return {"test": test, "stat": st, "p": p, "skew": skew, "kurt": kurt, "normal": bool(normal), "n": n}


def cohen_d(a, b):
    na, nb = len(a), len(b)
    sp = np.sqrt(((na - 1) * a.var(ddof=1) + (nb - 1) * b.var(ddof=1)) / (na + nb - 2))
    return (a.mean() - b.mean()) / sp if sp else np.nan


def d_yorum(d):
    d = abs(d)
    return "küçük" if d < .5 else "orta" if d < .8 else "büyük"


def eta_yorum(e):
    return "küçük" if e < .06 else "orta" if e < .14 else "büyük"


@dataclass
class Sonuc:
    baslik: str
    tablo: pd.DataFrame
    yorum: str
    not_: str = ""


# ---------------------------------------------------------------- analizler
def demografik(df: pd.DataFrame, degiskenler: list[str], etiket: dict) -> list[Sonuc]:
    out = []
    for v in degiskenler:
        f = df[v].value_counts(dropna=True)
        t = pd.DataFrame({"Kategori": f.index.astype(str), "n": f.values, "%": (100 * f.values / f.sum()).round(1)})
        en = t.iloc[0]
        out.append(Sonuc(f"Katılımcıların {etiket.get(v, v)} Değişkenine Göre Dağılımı", t,
                         f"Katılımcıların %{en['%']}’i “{en['Kategori']}” kategorisindedir (n = {en['n']})."))
    return out


def guvenirlik(df: pd.DataFrame, olcekler: dict[str, list[str]]) -> list[Sonuc]:
    rows, yorumlar = [], []
    for ad, maddeler in olcekler.items():
        a = cronbach(df[maddeler])
        rows.append({"Ölçek / Alt boyut": ad, "Madde sayısı": len(maddeler), "Cronbach α": f2(a)})
        # madde silinirse alfa
        sil = {m: cronbach(df[[x for x in maddeler if x != m]]) for m in maddeler} if len(maddeler) > 2 else {}
        artan = [m for m, v in sil.items() if v > a + .02]
        top = df[maddeler].sum(axis=1)
        negatif = [m for m in maddeler if df[m].corr(top - df[m]) < 0]
        y = f"{ad} ölçeğinin iç tutarlılık katsayısı α = {f2(a)} olup {alfa_yorum(a)} düzeydedir."
        if negatif:
            y += (f" UYARI: {', '.join(negatif)} maddesinin düzeltilmiş madde-toplam korelasyonu negatiftir; "
                  "bu madde ters puanlanması gereken bir madde olabilir (--ters ile belirtin).")
        if artan:
            y += f" {', '.join(artan)} maddesinin çıkarılması güvenirliği artırmaktadır; madde içeriği gözden geçirilmelidir."
        yorumlar.append(y)
    return [Sonuc("Ölçeklerin Güvenirlik Katsayıları", pd.DataFrame(rows), " ".join(yorumlar))]


def normallik_tablosu(df: pd.DataFrame, puanlar: list[str]) -> tuple[Sonuc, dict]:
    rows, durum = [], {}
    for v in puanlar:
        r = normallik(df[v])
        durum[v] = r["normal"]
        rows.append({"Değişken": v, "n": r["n"], "Ort.": f2(df[v].mean()), "SS": f2(df[v].std()),
                     "Çarpıklık": f2(r["skew"]), "Basıklık": f2(r["kurt"]), "Test": r["test"],
                     "İstatistik": f2(r["stat"], 3), "p": p_apa(r["p"]).replace("p ", "")})
    normaller = [k for k, v in durum.items() if v]
    y = ("Çarpıklık ve basıklık değerlerinin ±1,5 aralığında olması normal dağılım varsayımı için ölçüt alınmıştır "
         "(Tabachnick ve Fidell, 2013). ")
    y += (f"{', '.join(normaller)} puanlarının normal dağıldığı görülmüş, bu değişkenlerde parametrik testler kullanılmıştır. "
          if normaller else "")
    non = [k for k, v in durum.items() if not v]
    if non:
        y += f"{', '.join(non)} puanları normal dağılmadığından bu değişkenlerde parametrik olmayan testler tercih edilmiştir."
    return Sonuc("Ölçek Puanlarına İlişkin Betimsel İstatistikler ve Normallik Testi Sonuçları", pd.DataFrame(rows), y), durum


def grup_karsilastir(df: pd.DataFrame, puan: str, grup: str, normal: bool, etiket: dict) -> Sonuc | None:
    d = df[[puan, grup]].dropna()
    gruplar = [g for g in d[grup].unique() if (d[grup] == g).sum() >= 2]
    d = d[d[grup].isin(gruplar)]
    gad = etiket.get(grup, grup)
    if len(gruplar) < 2:
        return None
    ozet = d.groupby(grup, observed=True)[puan].agg(n="count", Ort="mean", SS="std", Medyan="median").reset_index()
    ozet = ozet.rename(columns={grup: gad, "Ort": "Ort.", "SS": "SS"})
    for c in ["Ort.", "SS", "Medyan"]:
        ozet[c] = ozet[c].map(f2)
    vals = [d.loc[d[grup] == g, puan] for g in gruplar]

    if len(gruplar) == 2:
        a, b = vals
        if normal:
            lev = stats.levene(a, b)
            t = stats.ttest_ind(a, b, equal_var=lev.pvalue > .05)
            es = cohen_d(a, b)
            df_ = len(a) + len(b) - 2
            test = f"Bağımsız örneklemler t-testi{' (Welch)' if lev.pvalue <= .05 else ''}"
            ozet["Test"] = ""; ozet.loc[0, "Test"] = f"t({df_}) = {f2(t.statistic)}, {p_apa(t.pvalue)}, d = {f2(es)}"
            p = t.pvalue
            y = (f"{puan} puanlarının {gad} değişkenine göre farklılaşıp farklılaşmadığını belirlemek amacıyla {test.lower()} yapılmıştır. "
                 + (f"Gruplar arasında istatistiksel olarak anlamlı bir fark bulunmuştur, t({df_}) = {f2(t.statistic)}, {p_apa(p)}. "
                    f"{gruplar[0] if a.mean() > b.mean() else gruplar[1]} grubunun ortalaması daha yüksektir; etki büyüklüğü {d_yorum(es)} düzeydedir (d = {f2(abs(es))})."
                    if p < .05 else f"Gruplar arasında anlamlı bir fark bulunmamıştır, t({df_}) = {f2(t.statistic)}, {p_apa(p)}."))
        else:
            u = stats.mannwhitneyu(a, b, alternative="two-sided")
            z = stats.norm.isf(u.pvalue / 2)
            r = z / np.sqrt(len(a) + len(b))
            test = "Mann-Whitney U testi"
            ozet["Test"] = ""; ozet.loc[0, "Test"] = f"U = {f2(u.statistic, 1)}, {p_apa(u.pvalue)}, r = {f2(r)}"
            p = u.pvalue
            y = (f"{puan} puanlarının {gad} değişkenine göre karşılaştırılmasında, veriler normal dağılmadığı için Mann-Whitney U testi kullanılmıştır. "
                 + (f"Gruplar arasında anlamlı fark vardır, U = {f2(u.statistic, 1)}, {p_apa(p)}, r = {f2(r)}. "
                    f"Medyanı daha yüksek olan grup {gruplar[0] if a.median() > b.median() else gruplar[1]} grubudur."
                    if p < .05 else f"Gruplar arasında anlamlı fark bulunmamıştır, U = {f2(u.statistic, 1)}, {p_apa(p)}."))
    else:
        if normal:
            f = stats.f_oneway(*vals)
            n_tot = sum(len(v) for v in vals); k = len(vals)
            grand = d[puan].mean()
            ssb = sum(len(v) * (v.mean() - grand) ** 2 for v in vals); sst = ((d[puan] - grand) ** 2).sum()
            eta = ssb / sst
            test = "Tek yönlü ANOVA"
            ozet["Test"] = ""; ozet.loc[0, "Test"] = f"F({k-1}, {n_tot-k}) = {f2(f.statistic)}, {p_apa(f.pvalue)}, η² = {f2(eta, 3)}"
            p = f.pvalue
            y = f"{puan} puanlarının {gad} değişkenine göre farklılaşmasını incelemek için tek yönlü varyans analizi (ANOVA) yapılmıştır. "
            if p < .05:
                post = _posthoc(d, puan, grup, gruplar, parametrik=True)
                y += (f"Gruplar arasında anlamlı fark bulunmuştur, F({k-1}, {n_tot-k}) = {f2(f.statistic)}, {p_apa(p)}, η² = {f2(eta, 3)} ({eta_yorum(eta)} etki). "
                      f"Bonferroni düzeltmeli ikili karşılaştırmalara göre {post}.")
            else:
                y += f"Gruplar arasında anlamlı fark bulunmamıştır, F({k-1}, {n_tot-k}) = {f2(f.statistic)}, {p_apa(p)}."
        else:
            h = stats.kruskal(*vals)
            n_tot = sum(len(v) for v in vals); k = len(vals)
            eps = (h.statistic - k + 1) / (n_tot - k)
            test = "Kruskal-Wallis H testi"
            ozet["Test"] = ""; ozet.loc[0, "Test"] = f"H({k-1}) = {f2(h.statistic)}, {p_apa(h.pvalue)}, ε² = {f2(max(eps, 0), 3)}"
            p = h.pvalue
            y = f"{puan} puanlarının {gad} değişkenine göre karşılaştırılmasında Kruskal-Wallis H testi kullanılmıştır. "
            if p < .05:
                post = _posthoc(d, puan, grup, gruplar, parametrik=False)
                y += f"Gruplar arasında anlamlı fark vardır, H({k-1}) = {f2(h.statistic)}, {p_apa(p)}. Bonferroni düzeltmeli Mann-Whitney U karşılaştırmalarına göre {post}."
            else:
                y += f"Gruplar arasında anlamlı fark bulunmamıştır, H({k-1}) = {f2(h.statistic)}, {p_apa(p)}."
    return Sonuc(f"{puan} Puanlarının {gad} Değişkenine Göre {test} Sonuçları", ozet, y)


def _posthoc(d, puan, grup, gruplar, parametrik: bool) -> str:
    from itertools import combinations
    pairs = list(combinations(gruplar, 2))
    anlamli = []
    for a, b in pairs:
        x, y = d.loc[d[grup] == a, puan], d.loc[d[grup] == b, puan]
        p = (stats.ttest_ind(x, y).pvalue if parametrik else stats.mannwhitneyu(x, y).pvalue) * len(pairs)
        if p < .05:
            yuksek, dusuk = (a, b) if (x.mean() if parametrik else x.median()) > (y.mean() if parametrik else y.median()) else (b, a)
            anlamli.append(f"{yuksek} grubunun puanları {dusuk} grubundan yüksektir")
    return "; ".join(anlamli) if anlamli else "ikili karşılaştırmalarda Bonferroni düzeltmesi sonrası anlamlı fark kalmamıştır"


def korelasyon(df: pd.DataFrame, degiskenler: list[str], normal: dict) -> Sonuc:
    yontem = "pearson" if all(normal.get(v, True) for v in degiskenler) else "spearman"
    k = len(degiskenler)
    tab = pd.DataFrame("", index=[f"{i+1}. {v}" for i, v in enumerate(degiskenler)], columns=[str(i + 1) for i in range(k)])
    anlam = []
    for i in range(k):
        for j in range(k):
            if j > i:
                continue
            if i == j:
                tab.iat[i, j] = "1"
                continue
            x = df[[degiskenler[i], degiskenler[j]]].dropna()
            r, p = (stats.pearsonr if yontem == "pearson" else stats.spearmanr)(x.iloc[:, 0], x.iloc[:, 1])
            yildiz = "**" if p < .01 else "*" if p < .05 else ""
            tab.iat[i, j] = f"{f2(r)}{yildiz}".replace("0.", ".")
            if p < .05:
                guc = "zayıf" if abs(r) < .3 else "orta" if abs(r) < .7 else "güçlü"
                yon = "pozitif" if r > 0 else "negatif"
                anlam.append(f"{degiskenler[i]} ile {degiskenler[j]} arasında {yon} yönde, {guc} düzeyde anlamlı ilişki vardır (r = {f2(r)}, {p_apa(p)})")
    tab = tab.reset_index().rename(columns={"index": "Değişken"})
    ad = "Pearson" if yontem == "pearson" else "Spearman sıra farkları"
    y = f"Değişkenler arasındaki ilişkiler {ad} korelasyon katsayısı ile incelenmiştir. " + (
        "; ".join(anlam) + "." if anlam else "Değişkenler arasında anlamlı ilişki bulunmamıştır.")
    return Sonuc(f"Değişkenler Arası {ad} Korelasyon Katsayıları", tab, y, "*p < .05, **p < .01")


def ki_kare(df: pd.DataFrame, a: str, b: str, etiket: dict) -> Sonuc:
    ct = pd.crosstab(df[a], df[b])
    chi, p, dof, exp = stats.chi2_contingency(ct)
    n = ct.values.sum()
    v = np.sqrt(chi / (n * (min(ct.shape) - 1)))
    dusuk_beklenen = (exp < 5).mean()
    tab = ct.copy().astype(str)
    for c in ct.columns:
        tab[c] = [f"{ct.loc[i, c]} (%{100 * ct.loc[i, c] / ct.loc[i].sum():.1f})" for i in ct.index]
    tab = tab.reset_index().rename(columns={a: etiket.get(a, a)})
    y = (f"{etiket.get(a, a)} ile {etiket.get(b, b)} arasındaki ilişki ki-kare bağımsızlık testi ile incelenmiştir. "
         + (f"İki değişken arasında anlamlı ilişki bulunmuştur, χ²({dof}, N = {n}) = {f2(chi)}, {p_apa(p)}, Cramér V = {f2(v)}."
            if p < .05 else f"İki değişken arasında anlamlı ilişki bulunmamıştır, χ²({dof}, N = {n}) = {f2(chi)}, {p_apa(p)}."))
    if dusuk_beklenen > .2:
        y += " Hücrelerin %20’sinden fazlasında beklenen frekans 5’in altında olduğundan Fisher kesin testi veya kategori birleştirme düşünülmelidir."
    return Sonuc(f"{etiket.get(a, a)} ile {etiket.get(b, b)} Arasındaki İlişkiye Yönelik Ki-Kare Testi Sonuçları", tab, y)


# ---------------------------------------------------------------- Word çıktısı
def _tablo_ekle(doc: Document, no: int, s: Sonuc):
    p = doc.add_paragraph()
    r = p.add_run(f"Tablo {no}"); r.bold = True
    p2 = doc.add_paragraph(); r2 = p2.add_run(s.baslik); r2.italic = True
    t = doc.add_table(rows=1, cols=len(s.tablo.columns))
    t.style = "Table Grid"
    for i, c in enumerate(s.tablo.columns):
        t.rows[0].cells[i].text = str(c)
        t.rows[0].cells[i].paragraphs[0].runs[0].bold = True
    for _, row in s.tablo.iterrows():
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = "" if pd.isna(v) else str(v)
    for row in t.rows:
        for c in row.cells:
            for pp in c.paragraphs:
                pp.paragraph_format.space_after = Pt(0)
                for rr in pp.runs:
                    rr.font.size = Pt(10)
    if s.not_:
        n = doc.add_paragraph(); n.add_run("Not. ").italic = True; n.add_run(s.not_)
    yp = doc.add_paragraph(s.yorum)
    yp.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY


def word_yaz(sonuclar: list[Sonuc], cikti: str | Path, baslik_no: str = "4"):
    doc = Document()
    st = doc.styles["Normal"]
    st.font.name = "Times New Roman"; st.font.size = Pt(12)
    st.paragraph_format.line_spacing = 1.5
    for s in doc.sections:
        s.left_margin = Cm(3); s.right_margin = s.top_margin = s.bottom_margin = Cm(2.5)
    doc.add_heading(f"{baslik_no}. BULGULAR", level=1)
    uyari = doc.add_paragraph()
    uyari.add_run("[TezKit taslağıdır. Yorumları kontrol edip araştırma sorularınızla ve alanyazınla ilişkilendiriniz; "
                  "bu kutuyu teslimden önce siliniz.]").italic = True
    for i, s in enumerate(sonuclar, 1):
        doc.add_heading(f"{baslik_no}.{i}. {s.baslik}", level=2)
        _tablo_ekle(doc, f"{baslik_no}.{i}", s)
    doc.save(str(cikti))


# ---------------------------------------------------------------- uçtan uca
def rapor(veri, olcekler: dict[str, list[str]], gruplar: list[str] = (), surekli: list[str] = (),
          ki_kare_ciftleri: list[tuple[str, str]] = (), cikti="bulgular.docx",
          ters: list[str] = (), likert: tuple[int, int] | None = None) -> list[Sonuc]:
    df, et = (veri, {}) if isinstance(veri, pd.DataFrame) else oku(veri)
    df = df.copy()
    for ad, m in olcekler.items():
        df[m] = df[m].apply(pd.to_numeric, errors="coerce")
        lo, hi = likert or (int(np.nanmin(df[m].values)), int(np.nanmax(df[m].values)))
        for c in m:
            df.loc[(df[c] < lo) | (df[c] > hi), c] = np.nan
            if c in ters:
                df[c] = (lo + hi) - df[c]
        df[ad] = df[m].mean(axis=1)
    sonuc = []
    sonuc += demografik(df, list(gruplar), et)
    sonuc += guvenirlik(df, olcekler)
    puanlar = list(olcekler) + list(surekli)
    nt, normal = normallik_tablosu(df, puanlar)
    sonuc.append(nt)
    for g in gruplar:
        for pu in olcekler:
            r = grup_karsilastir(df, pu, g, normal[pu], et)
            if r:
                sonuc.append(r)
    if len(puanlar) >= 2:
        sonuc.append(korelasyon(df, puanlar, normal))
    for a, b in ki_kare_ciftleri:
        sonuc.append(ki_kare(df, a, b, et))
    if cikti:
        word_yaz(sonuc, cikti)
    return sonuc


def _olcek_parse(liste: list[str]) -> dict[str, list[str]]:
    out = {}
    for s in liste:
        ad, m = s.split("=")
        out[ad.strip()] = [x.strip() for x in m.split(",")]
    return out


def main():
    ap = argparse.ArgumentParser(description="Anket verisinden Bulgular bölümü (.docx)")
    ap.add_argument("veri")
    ap.add_argument("--olcek", action="append", required=True, help='"Ad=S1,S2,S3" (birden çok verilebilir)')
    ap.add_argument("--gruplar", default="", help="virgülle: cinsiyet,egitim")
    ap.add_argument("--surekli", default="", help="virgülle: yas,kidem")
    ap.add_argument("--kikare", action="append", default=[], help="degisken1:degisken2")
    ap.add_argument("--ters", default="", help="ters puanlanacak maddeler, virgülle: AD3,AD6")
    ap.add_argument("--likert", default="", help="ölçek aralığı, ör. 1-5 (verilmezse veriden okunur)")
    ap.add_argument("--cikti", default="bulgular.docx")
    a = ap.parse_args()
    rapor(a.veri, _olcek_parse(a.olcek), [x for x in a.gruplar.split(",") if x], [x for x in a.surekli.split(",") if x],
          [tuple(x.split(":")) for x in a.kikare], a.cikti, [x for x in a.ters.split(",") if x],
          tuple(map(int, a.likert.split("-"))) if a.likert else None)
    print(f"Kaydedildi: {a.cikti}")


if __name__ == "__main__":
    main()
