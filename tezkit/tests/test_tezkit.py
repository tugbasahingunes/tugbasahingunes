"""pytest -q  (önce: python samples/make_samples.py)"""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from tezkit import citation_check, format_check, literature_table, power, scale_scoring, survey_report

K = Path(__file__).parent.parent
S = K / "samples"


# ---------------- 5 · güç analizi: G*Power 3.1 referans değerleri
@pytest.mark.parametrize("d,toplam", [(0.2, 788), (0.5, 128), (0.8, 52)])
def test_ttest_gpower(d, toplam):
    assert power.ttest(d).n == toplam


def test_anova_gpower():
    assert power.anova(0.25, 3).n == 159
    assert power.anova(0.10, 4).n == 1096


def test_kikare_gpower():
    assert power.kikare(0.3, 1).n == 88


def test_korelasyon_yakin():
    assert abs(power.korelasyon(0.3).n - 84) <= 1


def test_evren_formulu():
    assert power.oran(5000).n == 357      # klasik tablo değeri
    assert power.oran(None).n == 385


# ---------------- 1 · biçim
def test_bicim_hatalari_yakalar():
    r = format_check.denetle(S / "ornek_tez.docx", K / "profiles" / "genel_apa.yaml")
    kat = {b.kategori for b in r.bulgular}
    assert {"Kenar boşluğu", "Font", "Satır aralığı", "Punto", "Şekil başlığı", "Tablo numarası"} <= kat
    assert 0 <= r.puan() < 100


# ---------------- 3 · kaynakça
def test_kaynakca():
    r = citation_check.denetle(S / "ornek_tez.docx")
    eksik = {(a.ad, a.yil) for a in r.eksik}
    assert ("Smith", "2019") in eksik and ("Demir", "2021") in eksik
    assert any("Kaplan" in x for x in r.kullanilmayan)
    assert any("Yilmaz (2021)" in x for x in r.yil_uyusmazligi)
    assert any("doi.org" in x for x in r.bicim)


def test_atif_kaliplari():
    m = "Önceki çalışmalar (Yılmaz, 2020; Kaya ve Demir, 2019a) ve Smith et al. (2018) ile Arslan (2017, s. 12) bunu gösterir."
    bulunan = {(a.ad, a.yil) for a in citation_check.atiflari_bul(m)}
    assert {("Yılmaz", "2020"), ("Kaya", "2019a"), ("Smith", "2018")} <= bulunan


# ---------------- 2 · anket
def test_cronbach_bilinen():
    x = pd.DataFrame({"a": [1, 2, 3, 4, 5], "b": [1, 2, 3, 4, 5], "c": [1, 2, 3, 4, 5]})
    assert survey_report.cronbach(x) == pytest.approx(1.0)


def test_bulgular_docx(tmp_path):
    out = tmp_path / "b.docx"
    res = survey_report.rapor(S / "ornek_anket.sav", {"AD": [f"AD{i}" for i in range(1, 7)], "GU": [f"GU{i}" for i in range(1, 6)]},
                              ["cinsiyet", "egitim"], ["yas"], [("cinsiyet", "neet")], out, ters=["AD3", "AD6"], likert=(1, 5))
    assert out.exists() and len(res) >= 8
    alfa = res[2].tablo["Cronbach α"].astype(float)
    assert (alfa > .7).all()


def test_mann_whitney_secilir():
    rng = np.random.default_rng(0)
    df = pd.DataFrame({"p": np.r_[rng.exponential(1, 80), rng.exponential(2, 80)], "g": ["A"] * 80 + ["B"] * 80})
    r = survey_report.grup_karsilastir(df, "p", "g", normal=False, etiket={})
    assert "Mann-Whitney" in r.baslik


# ---------------- 4 · ölçek
def test_ters_madde_ve_aralik():
    df = pd.DataFrame({"m1": [5, 1, 3], "m2": [1, 5, 9]})
    t = {"min": 1, "max": 5, "ters_maddeler": ["m2"], "min_yanit_orani": 0.5, "boyutlar": {"B": {"maddeler": ["m1", "m2"]}}}
    out, ozet, uy = scale_scoring.puanla(df, t)
    assert out["B"].tolist() == [5.0, 1.0, 3.0]       # 9 aralık dışı → boş, yalnız m1 ile puan
    assert uy and "aralık dışı" in uy[0]


def test_ornek_olcek():
    df, _ = survey_report.oku(S / "ornek_anket.xlsx")
    out, ozet, _ = scale_scoring.puanla(df, yaml.safe_load((S / "olcek_tanimi.yaml").read_text(encoding="utf-8")))
    assert set(ozet["Boyut"]) == {"Aile_Destegi", "Gelecek_Umudu"} and "Aile_Destegi_duzey" in out


# ---------------- 6 · literatür
def test_literatur_tablosu():
    df = literature_table.tablo(S / "makaleler")
    satir = df.set_index("Dosya")
    assert satir.loc["ornek_nicel.pdf", "Yıl"] == "2022"
    assert satir.loc["ornek_nicel.pdf", "Örneklem (n)"] == "2450"
    assert satir.loc["ornek_nitel.pdf", "Yöntem türü"].startswith("Nitel")
    assert satir.loc["ornek_derleme.pdf", "Yöntem türü"].startswith("Derleme")
    assert satir.loc["ornek_nicel.pdf", "DOI"].startswith("10.0000/jys")
