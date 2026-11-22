"""5 · Örneklem Büyüklüğü ve Güç Analizi

Tezlerde en çok kullanılan hesaplar, Türkçe açıklamalı:
- Evren biliniyorsa / bilinmiyorsa oran tahmini: n = N·t²·p·q / (d²(N−1) + t²·p·q)
- Ortalama tahmini (σ ve hata payı ile)
- İki bağımsız grup t-testi (Cohen d)
- Tek yönlü ANOVA (Cohen f)
- Korelasyon (r, Fisher z)
- Ki-kare (Cohen w)
- Mevcut örneklemle ulaşılan güç (post-hoc / duyarlılık)

G*Power ile aynı mantığı kullanır; sonuçlar G*Power ile ±1 kişi uyumludur (testlerde doğrulanmıştır).

Kullanım:
    python -m tezkit.power oran --N 5000 --hata 0.05
    python -m tezkit.power ttest --d 0.5
    python -m tezkit.power anova --f 0.25 --k 3
"""
from __future__ import annotations

import argparse
import math
from dataclasses import dataclass

from scipy import stats, optimize


@dataclass
class Hesap:
    n: int
    aciklama: str
    formul: str = ""

    def __str__(self):
        return f"Gerekli örneklem: {self.n}\n{self.aciklama}" + (f"\nFormül: {self.formul}" if self.formul else "")


def oran(N: int | None = None, p: float = 0.5, hata: float = 0.05, guven: float = 0.95) -> Hesap:
    t = stats.norm.ppf(1 - (1 - guven) / 2)
    n0 = t ** 2 * p * (1 - p) / hata ** 2
    if N:
        n = N * t ** 2 * p * (1 - p) / (hata ** 2 * (N - 1) + t ** 2 * p * (1 - p))
        acik = (f"Evren büyüklüğü {N:,}".replace(",", ".") + f" olan çalışmada, %{guven*100:.0f} güven düzeyi ve ±%{hata*100:g} örnekleme hatası ile, "
                f"p = q = {p} kabul edilerek en az {math.ceil(n)} kişiye ulaşılması gerekmektedir.")
        return Hesap(math.ceil(n), acik, "n = N·t²·p·q / (d²·(N−1) + t²·p·q)")
    acik = (f"Evren büyüklüğü bilinmediğinden, %{guven*100:.0f} güven düzeyi ve ±%{hata*100:g} hata payı ile "
            f"en az {math.ceil(n0)} kişilik örneklem gereklidir.")
    return Hesap(math.ceil(n0), acik, "n = t²·p·q / d²")


def ortalama(sigma: float, hata: float, N: int | None = None, guven: float = 0.95) -> Hesap:
    t = stats.norm.ppf(1 - (1 - guven) / 2)
    n0 = (t * sigma / hata) ** 2
    n = n0 / (1 + (n0 - 1) / N) if N else n0
    return Hesap(math.ceil(n), f"σ = {sigma}, hata payı ±{hata}, %{guven*100:.0f} güven ile gerekli örneklem {math.ceil(n)}.",
                 "n = (t·σ/d)²" + (" · sonlu evren düzeltmesi" if N else ""))


def _ttest_guc(n_grup: float, d: float, alfa: float, iki_yonlu=True) -> float:
    df = 2 * n_grup - 2
    nc = d * math.sqrt(n_grup / 2)
    tc = stats.t.ppf(1 - alfa / (2 if iki_yonlu else 1), df)
    return 1 - stats.nct.cdf(tc, df, nc) + (stats.nct.cdf(-tc, df, nc) if iki_yonlu else 0)


def _coz(fn, alt: float) -> float:
    """fn(n) = güç − hedef. Üst sınırı katlayarak bulur, sonra kökü çözer (büyük n'de NaN'ı önler)."""
    ust = alt * 2
    while fn(ust) < 0:
        alt, ust = ust, ust * 2
        if ust > 1e7:
            raise ValueError("Çok küçük etki büyüklüğü: gerekli örneklem 10 milyonun üzerinde.")
    return optimize.brentq(fn, alt, ust)


def ttest(d: float = 0.5, alfa: float = 0.05, guc: float = 0.80, iki_yonlu=True) -> Hesap:
    n = _coz(lambda x: _ttest_guc(x, d, alfa, iki_yonlu) - guc, 2)
    ng = math.ceil(n)
    return Hesap(2 * ng, f"İki bağımsız grubu karşılaştırmak için (d = {d}, α = {alfa}, güç = {guc}) "
                         f"her grupta {ng}, toplam {2*ng} katılımcı gereklidir.", "Noncentral t (G*Power: t tests – two groups)")


def _anova_guc(n_toplam: float, f: float, k: int, alfa: float) -> float:
    df1, df2 = k - 1, n_toplam - k
    lam = f ** 2 * n_toplam
    fc = stats.f.ppf(1 - alfa, df1, df2)
    return 1 - stats.ncf.cdf(fc, df1, df2, lam)


def anova(f: float = 0.25, k: int = 3, alfa: float = 0.05, guc: float = 0.80) -> Hesap:
    n = _coz(lambda x: _anova_guc(x, f, k, alfa) - guc, k + 2)
    ng = math.ceil(n / k)
    return Hesap(ng * k, f"{k} grup için tek yönlü ANOVA (f = {f}, α = {alfa}, güç = {guc}): her grupta {ng}, toplam {ng*k} katılımcı.",
                 "Noncentral F, λ = f²·N")


def korelasyon(r: float = 0.3, alfa: float = 0.05, guc: float = 0.80) -> Hesap:
    za, zb = stats.norm.ppf(1 - alfa / 2), stats.norm.ppf(guc)
    n = ((za + zb) / math.atanh(r)) ** 2 + 3
    return Hesap(math.ceil(n), f"r = {r} büyüklüğündeki ilişkiyi α = {alfa}, güç = {guc} ile saptamak için en az {math.ceil(n)} katılımcı.",
                 "n = ((z_α/2 + z_β) / atanh(r))² + 3")


def kikare(w: float = 0.3, df: int = 1, alfa: float = 0.05, guc: float = 0.80) -> Hesap:
    def g(n):
        c = stats.chi2.ppf(1 - alfa, df)
        return 1 - stats.ncx2.cdf(c, df, w ** 2 * n) - guc
    n = _coz(g, 5)
    return Hesap(math.ceil(n), f"Ki-kare (w = {w}, sd = {df}, α = {alfa}, güç = {guc}) için en az {math.ceil(n)} katılımcı.",
                 "Noncentral χ², λ = w²·N")


def ulasilan_guc(test: str, n: int, etki: float, k: int = 3, alfa: float = 0.05) -> float:
    if test == "ttest":
        return _ttest_guc(n / 2, etki, alfa)
    if test == "anova":
        return _anova_guc(n, etki, k, alfa)
    if test == "korelasyon":
        za = stats.norm.ppf(1 - alfa / 2)
        return float(stats.norm.cdf(math.atanh(etki) * math.sqrt(n - 3) - za))
    raise ValueError(test)


ETKI_REHBERI = {
    "d (t-testi)": "küçük 0.20 · orta 0.50 · büyük 0.80",
    "f (ANOVA)": "küçük 0.10 · orta 0.25 · büyük 0.40",
    "r (korelasyon)": "küçük 0.10 · orta 0.30 · büyük 0.50",
    "w (ki-kare)": "küçük 0.10 · orta 0.30 · büyük 0.50",
}


def main():
    ap = argparse.ArgumentParser(description="Örneklem büyüklüğü hesapları")
    sp = ap.add_subparsers(dest="tur", required=True)
    o = sp.add_parser("oran"); o.add_argument("--N", type=int); o.add_argument("--p", type=float, default=.5); o.add_argument("--hata", type=float, default=.05); o.add_argument("--guven", type=float, default=.95)
    t = sp.add_parser("ttest"); t.add_argument("--d", type=float, default=.5); t.add_argument("--alfa", type=float, default=.05); t.add_argument("--guc", type=float, default=.8)
    a = sp.add_parser("anova"); a.add_argument("--f", type=float, default=.25); a.add_argument("--k", type=int, default=3); a.add_argument("--alfa", type=float, default=.05); a.add_argument("--guc", type=float, default=.8)
    r = sp.add_parser("korelasyon"); r.add_argument("--r", type=float, default=.3); r.add_argument("--alfa", type=float, default=.05); r.add_argument("--guc", type=float, default=.8)
    c = sp.add_parser("kikare"); c.add_argument("--w", type=float, default=.3); c.add_argument("--df", type=int, default=1); c.add_argument("--alfa", type=float, default=.05); c.add_argument("--guc", type=float, default=.8)
    x = ap.parse_args()
    if x.tur == "oran": print(oran(x.N, x.p, x.hata, x.guven))
    elif x.tur == "ttest": print(ttest(x.d, x.alfa, x.guc))
    elif x.tur == "anova": print(anova(x.f, x.k, x.alfa, x.guc))
    elif x.tur == "korelasyon": print(korelasyon(x.r, x.alfa, x.guc))
    else: print(kikare(x.w, x.df, x.alfa, x.guc))


if __name__ == "__main__":
    main()
