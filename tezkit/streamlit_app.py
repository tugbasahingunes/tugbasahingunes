"""TezKit web arayüzü. Çalıştırma: streamlit run streamlit_app.py"""
import io
import sys
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st
import yaml

sys.path.insert(0, str(Path(__file__).parent))
from tezkit import citation_check, format_check, literature_table, power, scale_scoring, survey_report  # noqa: E402

KOK = Path(__file__).parent
st.set_page_config(page_title="TezKit · Tez yazarları için araçlar", page_icon="🎓", layout="wide")


def gecici(yuklenen) -> Path:
    d = Path(tempfile.mkdtemp())
    p = d / yuklenen.name
    p.write_bytes(yuklenen.getbuffer())
    return p


def indir(etiket, veri: bytes, ad: str, mime="application/octet-stream"):
    st.download_button(etiket, veri, file_name=ad, mime=mime)


ARACLAR = {
    "🏠 Ana sayfa": "ana",
    "1 · Tez Biçim Denetleyici": "bicim",
    "2 · Anket → Bulgular Bölümü": "anket",
    "3 · Kaynakça Kontrolcüsü": "kaynakca",
    "4 · Ölçek Puanlama": "olcek",
    "5 · Örneklem Büyüklüğü": "guc",
    "6 · Literatür Tablosu": "literatur",
}
secim = ARACLAR[st.sidebar.radio("Araçlar", list(ARACLAR))]
st.sidebar.markdown("---")
st.sidebar.caption("Dosyalarınız yalnızca bu oturumda işlenir, saklanmaz. TezKit tez **yazmaz**; kontrol eder, hesaplar ve taslak tablo üretir.")

# ------------------------------------------------------------------ ana sayfa
if secim == "ana":
    st.title("🎓 TezKit")
    st.subheader("Türkçe tez yazarları için biçim, kaynakça ve istatistik araçları")
    st.markdown("""
| Araç | Ne yapar? |
|---|---|
| **1 · Biçim Denetleyici** | Word dosyanızı enstitü kılavuzuna göre kontrol eder: kenar boşluğu, font, punto, satır aralığı, tablo/şekil başlıkları, zorunlu bölümler |
| **2 · Anket → Bulgular** | SPSS/Excel verinizden güvenirlik, normallik, doğru test seçimi, APA tabloları ve Türkçe yorum taslağı içeren Word dosyası |
| **3 · Kaynakça Kontrolcüsü** | Metin içi atıflar ile kaynakçayı eşleştirir; eksik, fazla, yıl uyuşmazlığı ve APA 7 hatalarını listeler |
| **4 · Ölçek Puanlama** | Ters maddeler, alt boyutlar, eksik veri kuralı, düzey etiketleri ve alfa |
| **5 · Örneklem Büyüklüğü** | Evren formülü, t-testi, ANOVA, korelasyon, ki-kare (G*Power ile uyumlu) |
| **6 · Literatür Tablosu** | Makale PDF'lerinden başlık, yıl, DOI, yöntem, örneklem ve özet içeren Excel tablosu |
""")
    st.info("Denemek için her araçta **örnek dosyayı kullan** seçeneği vardır.")

# ------------------------------------------------------------------ 1
elif secim == "bicim":
    st.header("1 · Tez Biçim Denetleyici")
    profiller = {yaml.safe_load(p.read_text(encoding="utf-8"))["ad"]: p for p in sorted((KOK / "profiles").glob("*.yaml"))}
    ad = st.selectbox("Kılavuz profili", list(profiller))
    with st.expander("Profili görüntüle / düzenle"):
        metin = st.text_area("YAML", profiller[ad].read_text(encoding="utf-8"), height=300)
    dosya = st.file_uploader("Tez dosyanız (.docx)", type=["docx"])
    ornek = st.checkbox("Örnek dosyayı kullan (kasıtlı hatalar içerir)", value=dosya is None)
    if st.button("Denetle", type="primary"):
        yol = gecici(dosya) if dosya and not ornek else KOK / "samples" / "ornek_tez.docx"
        pf = Path(tempfile.mkdtemp()) / "p.yaml"; pf.write_text(metin, encoding="utf-8")
        r = format_check.denetle(yol, pf)
        c1, c2, c3 = st.columns(3)
        c1.metric("Uygunluk puanı", f"{r.puan()}/100"); c2.metric("Hata", r.hata_sayisi); c3.metric("Uyarı", r.uyari_sayisi)
        st.dataframe(pd.DataFrame([b.__dict__ for b in r.bulgular]).rename(columns={"seviye": "Seviye", "kategori": "Kategori", "mesaj": "Açıklama", "konum": "Konum"}),
                     width="stretch", hide_index=True)
        indir("Raporu indir (.md)", r.markdown().encode("utf-8"), "bicim_raporu.md", "text/markdown")

# ------------------------------------------------------------------ 2
elif secim == "anket":
    st.header("2 · Anket → Bulgular Bölümü")
    dosya = st.file_uploader("Veri dosyası (.sav, .xlsx, .csv)", type=["sav", "xlsx", "csv"])
    ornek = st.checkbox("Örnek veriyi kullan", value=dosya is None)
    yol = gecici(dosya) if dosya and not ornek else KOK / "samples" / "ornek_anket.sav"
    df, et = survey_report.oku(yol)
    st.caption(f"{len(df)} satır · {df.shape[1]} değişken"); st.dataframe(df.head(), width="stretch")
    sayisal = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    kategorik = [c for c in df.columns if c not in sayisal or df[c].nunique() <= 8]
    n_olcek = st.number_input("Kaç ölçek / alt boyut?", 1, 10, 2)
    olcekler, ters = {}, []
    varsayilan = [("Aile_Destegi", [f"AD{i}" for i in range(1, 7)]), ("Gelecek_Umudu", [f"GU{i}" for i in range(1, 6)])] if ornek else []
    for i in range(int(n_olcek)):
        c1, c2 = st.columns([1, 3])
        vad, vm = varsayilan[i] if i < len(varsayilan) else (f"Olcek{i+1}", [])
        ad = c1.text_input("Ölçek adı", vad, key=f"ad{i}")
        m = c2.multiselect("Maddeler", sayisal, [x for x in vm if x in sayisal], key=f"m{i}")
        if ad and len(m) >= 2:
            olcekler[ad] = m
    ters = st.multiselect("Ters puanlanacak maddeler", sayisal, ["AD3", "AD6"] if ornek else [])
    likert = st.slider("Likert aralığı", 1, 10, (1, 5))
    gruplar = st.multiselect("Grup değişkenleri (karşılaştırma)", kategorik, ["cinsiyet", "egitim"] if ornek else [])
    surekli = st.multiselect("Diğer sürekli değişkenler (korelasyon)", [c for c in sayisal if c not in sum(olcekler.values(), [])], ["yas"] if ornek else [])
    kk = st.multiselect("Ki-kare için iki kategorik değişken", kategorik, ["cinsiyet", "neet"] if ornek else [], max_selections=2)
    if st.button("Bulgular bölümünü oluştur", type="primary", disabled=not olcekler):
        cikti = Path(tempfile.mkdtemp()) / "bulgular.docx"
        res = survey_report.rapor(yol, olcekler, gruplar, surekli, [tuple(kk)] if len(kk) == 2 else [], cikti, ters, likert)
        for i, s in enumerate(res, 1):
            with st.expander(f"Tablo 4.{i}. {s.baslik}", expanded=i <= 3):
                st.dataframe(s.tablo, width="stretch", hide_index=True)
                st.write(s.yorum)
        indir("📄 Bulgular bölümünü indir (.docx)", cikti.read_bytes(), "bulgular.docx")
        st.warning("Yorumlar taslaktır. Araştırma sorularınızla ilişkilendirip alanyazınla tartışmanız gerekir.")

# ------------------------------------------------------------------ 3
elif secim == "kaynakca":
    st.header("3 · Kaynakça Kontrolcüsü (APA 7)")
    dosya = st.file_uploader("Tez dosyası (.docx veya .txt). Son bölüm KAYNAKÇA / KAYNAKLAR / REFERENCES olmalı.", type=["docx", "txt"])
    ornek = st.checkbox("Örnek dosyayı kullan", value=dosya is None)
    baslik = st.text_input("Kaynakça başlığı (boş bırakılırsa otomatik bulunur)")
    if st.button("Kontrol et", type="primary"):
        yol = gecici(dosya) if dosya and not ornek else KOK / "samples" / "ornek_tez.docx"
        try:
            r = citation_check.denetle(yol, baslik or None)
        except ValueError as e:
            st.error(str(e)); st.stop()
        c = st.columns(4)
        c[0].metric("Atıf", len(r.atiflar)); c[1].metric("Kaynak", len(r.kaynaklar))
        c[2].metric("Kaynakçada yok", len(r.eksik)); c[3].metric("Metinde yok", len(r.kullanilmayan))
        st.markdown(r.markdown())
        indir("Raporu indir (.md)", r.markdown().encode("utf-8"), "kaynakca_raporu.md", "text/markdown")

# ------------------------------------------------------------------ 4
elif secim == "olcek":
    st.header("4 · Ölçek Puanlama")
    dosya = st.file_uploader("Veri (.xlsx, .csv, .sav)", type=["xlsx", "csv", "sav"])
    ornek = st.checkbox("Örnek veri ve tanımı kullan", value=dosya is None)
    tanim_metin = st.text_area("Ölçek tanımı (YAML)", (KOK / "samples" / "olcek_tanimi.yaml").read_text(encoding="utf-8"), height=380)
    if st.button("Puanla", type="primary"):
        yol = gecici(dosya) if dosya and not ornek else KOK / "samples" / "ornek_anket.xlsx"
        df, _ = survey_report.oku(yol)
        try:
            out, ozet, uy = scale_scoring.puanla(df, yaml.safe_load(tanim_metin))
        except Exception as e:
            st.error(str(e)); st.stop()
        st.dataframe(ozet, width="stretch", hide_index=True)
        for u in uy: st.warning(u)
        buf = io.BytesIO()
        with pd.ExcelWriter(buf) as w:
            out.to_excel(w, sheet_name="Puanlar", index=False); ozet.to_excel(w, sheet_name="Özet", index=False)
        indir("Puanlanmış veriyi indir (.xlsx)", buf.getvalue(), "puanlanmis.xlsx")

# ------------------------------------------------------------------ 5
elif secim == "guc":
    st.header("5 · Örneklem Büyüklüğü ve Güç Analizi")
    tur = st.radio("Hesap türü", ["Evren formülü (oran)", "İki grup t-testi", "Tek yönlü ANOVA", "Korelasyon", "Ki-kare", "Ortalama tahmini"], horizontal=True)
    c1, c2, c3 = st.columns(3)
    alfa = c2.selectbox("α (anlamlılık)", [0.05, 0.01, 0.10]) if tur not in ("Evren formülü (oran)", "Ortalama tahmini") else None
    guc = c3.selectbox("Güç (1−β)", [0.80, 0.90, 0.95]) if alfa else None
    if tur == "Evren formülü (oran)":
        bilin = c1.checkbox("Evren büyüklüğü biliniyor", True)
        N = c1.number_input("Evren (N)", 10, 100_000_000, 5000) if bilin else None
        hata = c2.selectbox("Örnekleme hatası (d)", [0.05, 0.03, 0.04, 0.10])
        guven = c3.selectbox("Güven düzeyi", [0.95, 0.99, 0.90])
        p = st.slider("Beklenen oran (p)", 0.05, 0.95, 0.5)
        r = power.oran(N, p, hata, guven)
    elif tur == "İki grup t-testi":
        r = power.ttest(c1.number_input("Etki büyüklüğü d", 0.05, 3.0, 0.5), alfa, guc)
    elif tur == "Tek yönlü ANOVA":
        f = c1.number_input("Etki büyüklüğü f", 0.05, 2.0, 0.25); k = st.number_input("Grup sayısı", 3, 20, 3)
        r = power.anova(f, int(k), alfa, guc)
    elif tur == "Korelasyon":
        r = power.korelasyon(c1.number_input("Beklenen r", 0.05, 0.95, 0.3), alfa, guc)
    elif tur == "Ki-kare":
        w = c1.number_input("Etki büyüklüğü w", 0.05, 2.0, 0.3); sd = st.number_input("Serbestlik derecesi", 1, 50, 1)
        r = power.kikare(w, int(sd), alfa, guc)
    else:
        sigma = c1.number_input("Tahmini standart sapma (σ)", 0.01, 1e6, 10.0)
        hata = c2.number_input("Kabul edilen hata payı", 0.01, 1e6, 2.0)
        r = power.ortalama(sigma, hata, None, c3.selectbox("Güven düzeyi", [0.95, 0.99, 0.90]))
    st.metric("Gerekli örneklem", r.n)
    st.success(r.aciklama)
    st.caption(f"Formül: {r.formul}")
    with st.expander("Etki büyüklüğü rehberi (Cohen, 1988)"):
        st.table(pd.DataFrame(power.ETKI_REHBERI.items(), columns=["Ölçü", "Değerler"]))

# ------------------------------------------------------------------ 6
elif secim == "literatur":
    st.header("6 · Literatür Tablosu Oluşturucu")
    dosyalar = st.file_uploader("Makale PDF'leri (birden çok seçebilirsiniz)", type=["pdf"], accept_multiple_files=True)
    ornek = st.checkbox("Örnek makaleleri kullan", value=not dosyalar)
    crossref = st.checkbox("DOI ile CrossRef doğrulaması (internet gerekir, daha doğru künye)")
    if st.button("Tabloyu oluştur", type="primary"):
        if dosyalar and not ornek:
            d = Path(tempfile.mkdtemp())
            for f in dosyalar: (d / f.name).write_bytes(f.getbuffer())
        else:
            d = KOK / "samples" / "makaleler"
        df = literature_table.tablo(d, crossref)
        st.dataframe(df, width="stretch", hide_index=True)
        out = Path(tempfile.mkdtemp()) / "literatur.xlsx"
        literature_table.excel_yaz(df, out)
        indir("📊 Literatür tablosunu indir (.xlsx)", out.read_bytes(), "literatur_tablosu.xlsx")
        st.info("Çıkarım kural tabanlıdır; başlık, yıl ve yöntem alanlarını kontrol edin. “Temel bulgu” ve “Tezimle ilişkisi” sütunları sizin notlarınız içindir.")
