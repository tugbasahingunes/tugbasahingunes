# 🎓 TezKit

**Türkçe tez yazarları için biçim, kaynakça ve istatistik araçları.**
Teslimden önce en çok zaman alan kontrolleri otomatikleştirir; anket verisinden APA biçiminde Bulgular bölümü taslağı üretir.

![tests](https://github.com/tugbasahingunes/tugbasahingunes/actions/workflows/tezkit-tests.yml/badge.svg)
· Python 3.10+ · MIT lisansı · Web arayüzü (Streamlit) + komut satırı

> TezKit tez **yazmaz**. Kontrol eder, hesaplar ve tablo üretir. Üretilen yorumlar taslaktır; araştırmacı tarafından okunmalı, araştırma sorularıyla ve alanyazınla ilişkilendirilmelidir.

---

## Araçlar

| # | Araç | Girdi | Çıktı |
|---|---|---|---|
| 1 | **Tez Biçim Denetleyici** | `.docx` + kılavuz profili | Uygunluk puanı ve hata listesi |
| 2 | **Anket → Bulgular Bölümü** | `.sav` / `.xlsx` / `.csv` | APA tabloları + Türkçe yorum içeren `.docx` |
| 3 | **Kaynakça Kontrolcüsü** | `.docx` / `.txt` | Eksik/fazla kaynak, yıl uyuşmazlığı, APA 7 uyarıları |
| 4 | **Ölçek Puanlama** | Veri + ölçek tanımı (YAML) | Alt boyut/toplam puanlar, düzeyler, α |
| 5 | **Örneklem Büyüklüğü** | Parametreler | Gerekli n + tezde kullanılabilir açıklama cümlesi |
| 6 | **Literatür Tablosu** | Makale PDF klasörü | Başlık, yıl, DOI, yöntem, örneklem, özet içeren `.xlsx` |

### 1 · Tez Biçim Denetleyici
Enstitü tez yazım kılavuzunu bir YAML profilinde tanımlarsınız (`profiles/`), araç Word dosyanızı paragraf paragraf denetler:
- Sayfa boyutu (A4), dört kenar boşluğu
- Gövde metninde font, punto, satır aralığı, hizalama (etkin biçim: karakter → paragraf stili → Normal stil)
- Alt başlık numaralandırması (`2.1.`), başlık fontu
- Tablo/şekil başlığı biçimi (`Tablo 3.1. …`), tekrarlanan numaralar, başlıksız tablolar
- Zorunlu bölümler (ÖZET, ABSTRACT, İÇİNDEKİLER, KAYNAKÇA…)
- Çift boşluk, art arda boş satırlar

Örnek çıktı: [`samples/ornek_bicim_raporu.md`](samples/ornek_bicim_raporu.md). Örnek tez dosyasındaki 7 hata ve 2 uyarı yakalanır; Word'ün varsayılan *Letter* sayfa boyutunun A4 olmadığı uyarısı da buna dahil.

**Kendi üniversiteniz için:** `profiles/genel_apa.yaml` dosyasını kopyalayıp kılavuzdaki değerleri yazmanız yeterli.

### 2 · Anket → Bulgular Bölümü
SPSS değer etiketlerini okur ve analizi uçtan uca yapar:
1. Demografik frekans tabloları
2. Ters madde çevirme, aralık dışı değer temizliği
3. **Cronbach α**, madde silinirse α, negatif madde-toplam korelasyonu uyarısı (“bu madde ters olabilir”)
4. **Normallik**: n ≤ 50 için Shapiro-Wilk, n > 50 için Kolmogorov-Smirnov, çarpıklık/basıklık ±1,5 ölçütü
5. **Doğru testin otomatik seçimi**

| Durum | Normal dağılım | Normal değil |
|---|---|---|
| 2 grup | Bağımsız t-testi (Levene'e göre Welch) + Cohen d | Mann-Whitney U + r |
| 3+ grup | ANOVA + η² + Bonferroni post-hoc | Kruskal-Wallis + ε² + Bonferroni |
| İki sürekli değişken | Pearson r | Spearman ρ |
| İki kategorik değişken | Ki-kare + Cramér V (beklenen frekans < 5 uyarısı) | |

6. APA 7 biçiminde tablolar ve “…anlamlı fark bulunmuştur, t(418) = 2.17, p = .031” biçiminde Türkçe yorum taslağı, Times New Roman 12 / 1,5 satır aralığı ile `.docx` olarak

Örnek çıktı: [`samples/ornek_bulgular.docx`](samples/ornek_bulgular.docx) (10 tablo)

### 3 · Kaynakça Kontrolcüsü
Tanıdığı atıf kalıpları: `(Yılmaz, 2020)` · `(Yılmaz ve Kaya, 2020)` · `(Demir vd., 2021)` · `(OECD, 2016; Smith & Jones, 2019a)` · `Yılmaz (2020)` · `Smith et al. (2018)` · `(Arslan, 2017, s. 12)`.
Türkçe karakter farklarını eşler (Yılmaz = Yilmaz). Raporladıkları:
- Kaynakçada olmayan atıflar, bağlamıyla birlikte
- Metinde hiç atıf yapılmayan kaynaklar
- Yıl uyuşmazlıkları
- APA 7: alfabetik sıra, `doi:` → `https://doi.org/`, kaynakçada “vd./et al.”, anlatı atfında “&”

Örnek çıktı: [`samples/ornek_kaynakca_raporu.md`](samples/ornek_kaynakca_raporu.md)

### 4 · Ölçek Puanlama
```yaml
min: 1
max: 5
yontem: ortalama            # veya toplam
min_yanit_orani: 0.8        # alt boyutun en az %80'i yanıtlanmalı
ters_maddeler: [AD3, AD6]
boyutlar:
  Aile_Destegi:  {maddeler: [AD1, AD2, AD3, AD4, AD5, AD6]}
  Gelecek_Umudu: {maddeler: [GU1, GU2, GU3, GU4, GU5]}
kesme: {sinirlar: [2.33, 3.67], etiketler: [Düşük, Orta, Yüksek]}
```

### 5 · Örneklem Büyüklüğü
| Hesap | Örnek | Sonuç |
|---|---|---|
| Evren biliniyor (N = 5.000, ±%5, %95) | `oran --N 5000` | 357 |
| Evren bilinmiyor | `oran` | 385 |
| t-testi, d = 0,5, güç = 0,80 | `ttest --d .5` | 128 (64 + 64) |
| ANOVA, f = 0,25, 3 grup | `anova --f .25 --k 3` | 159 |
| Korelasyon, r = 0,30 | `korelasyon --r .3` | 85 |
| Ki-kare, w = 0,30, sd = 1 | `kikare --w .3` | 88 |

t-testi, ANOVA ve ki-kare sonuçları **G*Power 3.1 ile birebir aynıdır**; bunu testler doğruluyor. Her sonuç, yöntem bölümüne uyarlanabilecek bir açıklama cümlesiyle birlikte gelir.

### 6 · Literatür Tablosu
Kural tabanlıdır: yapay zekâ kullanmaz, isteğe bağlı CrossRef doğrulaması dışında internete bağlanmaz. Çıkardığı alanlar başlık, yazar, yıl, DOI, anahtar kelimeler, özet, yöntem türü (nicel / nitel / karma / derleme / deneysel), örneklem, analiz teknikleri ve ülke/bağlam. “Temel bulgu” ve “Tezimle ilişkisi” sütunlarını siz doldurursunuz.

---

## Kurulum ve kullanım

```bash
git clone https://github.com/tugbasahingunes/tugbasahingunes
cd tugbasahingunes/tezkit
pip install -r requirements.txt
python samples/make_samples.py        # örnek dosyaları üretir
```

**Web arayüzü:**
```bash
streamlit run streamlit_app.py
```
Her araçta “örnek dosyayı kullan” seçeneği vardır.

**Komut satırı:**
```bash
python -m tezkit.format_check   tez.docx --profil profiles/genel_apa.yaml
python -m tezkit.survey_report  veri.sav --olcek "Memnuniyet=S1,S2,S3,S4" --ters S3 --likert 1-5 \
                                --gruplar cinsiyet,egitim --surekli yas --kikare cinsiyet:durum --cikti bulgular.docx
python -m tezkit.citation_check tez.docx
python -m tezkit.scale_scoring  veri.xlsx --tanim olcek.yaml --cikti puanlar.xlsx
python -m tezkit.power          ttest --d 0.5 --guc 0.80
python -m tezkit.literature_table makaleler/ --crossref --cikti literatur.xlsx
```

**Testler:** `pytest -q` (16 test). GitHub Actions'ta her değişiklikte otomatik çalışır.

## Herkese açık web sürümü (ücretsiz)
1. [share.streamlit.io](https://share.streamlit.io) → GitHub ile giriş
2. *Create app* → Repo: `tugbasahingunes/tugbasahingunes`, Branch: `main`, Main file: `tezkit/streamlit_app.py`
3. *Deploy*. Uygulama birkaç dakika içinde `https://….streamlit.app` adresinde açılır.

## Gizlilik
Yüklenen dosyalar yalnızca işlem süresince geçici klasörde tutulur. Kaydedilmez, hiçbir yere gönderilmez. Tek istisna, isteğe bağlı CrossRef doğrulamasında DOI numarası.

## Sınırlar
- Biçim denetimi Word stillerine dayanır. Elle biçimlendirilmiş başlıklar (stil yerine kalın yazı) başlık olarak tanınmayabilir.
- Kaynakça denetimi APA 7'ye göredir. Chicago veya numaralı sistemler henüz desteklenmiyor.
- Literatür tablosu PDF'nin metin katmanına bağlıdır. Taranmış (resim) PDF'ler için önce OCR gerekir.
- İstatistiksel yorumlar karar desteği içindir. Araştırma tasarımına uygunluk araştırmacının sorumluluğundadır.

## Yol haritası
- [ ] Hazır üniversite profilleri (Ankara, Hacettepe, ODTÜ, Gazi, Marmara…)
- [ ] Çoklu regresyon ve aracılık analizi tabloları
- [ ] Doğrulayıcı faktör analizi özet tablosu
- [ ] Biçim hatalarını otomatik düzelten “düzelt ve kaydet” modu

---

### English summary
**TezKit** is a toolkit for Turkish graduate students: a thesis formatting checker driven by university style profiles, an SPSS/Excel survey-to-“Findings chapter” generator with automatic test selection, effect sizes and APA tables, an APA 7 citation-reference cross-checker, a Likert scale scorer, a G*Power-consistent sample-size calculator, and a PDF-to-literature-matrix extractor. It ships with a Streamlit web UI, a CLI, synthetic sample files and a test suite.

Geliştiren: **Tuğba Güneş** · Sosyoloji · 10+ yıl sosyal araştırma ve resmî istatistik deneyimi · [LinkedIn](https://www.linkedin.com/in/tu%C4%9Fba-g-648925260)

Tez verinizin analizi ya da biçim düzeltmesi için profesyonel destek: Upwork / Fiverr / Bionluk üzerinden ulaşabilirsiniz.
