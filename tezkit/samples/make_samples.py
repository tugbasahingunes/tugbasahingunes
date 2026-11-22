"""Örnek dosyaları üretir (tamamen kurgusal). python samples/make_samples.py"""
from pathlib import Path

import numpy as np
import pandas as pd
import pyreadstat
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from reportlab.lib.styles import getSampleStyleSheet

D = Path(__file__).parent


# ------------------------------------------------ 1+3: kasıtlı hatalı örnek tez
def ornek_tez():
    doc = Document()
    n = doc.styles["Normal"]; n.font.name = "Times New Roman"; n.font.size = Pt(12)
    n.paragraph_format.line_spacing = 1.5; n.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    s = doc.sections[0]; s.left_margin = Cm(3); s.right_margin = s.top_margin = Cm(2.5); s.bottom_margin = Cm(2.0)  # HATA: alt 2.0
    doc.add_heading("ÖZET", 1)
    doc.add_paragraph("Bu çalışmada genç yetişkinlerin eğitim ve istihdam dışında kalma durumlarını etkileyen aile temelli etkenler incelenmiştir. "
                      "Araştırma nicel desende yürütülmüş, 420 katılımcıdan veri toplanmıştır.")
    doc.add_heading("ABSTRACT", 1)
    doc.add_paragraph("This study examines family-related factors associated with young adults being outside employment and education.")
    doc.add_heading("İÇİNDEKİLER", 1)
    doc.add_heading("1. GİRİŞ", 1)
    doc.add_paragraph("Eğitim ve istihdam dışında kalan gençler (NEET) uzun dönemli dezavantajlarla karşılaşmaktadır (Eurofound, 2016). "
                      "Yılmaz ve Kaya (2020) aile desteğinin belirleyici olduğunu göstermiştir. Benzer biçimde erken müdahalenin önemi "
                      "vurgulanmaktadır (OECD, 2016; Demir vd., 2021). Bazı çalışmalar ise farklı sonuçlar raporlamıştır (Şahin, 2018).")
    p = doc.add_paragraph("Bu paragraf  yanlışlıkla Arial yazı tipi ile yazılmış ve çift boşluk içermektedir; ayrıca satır aralığı tek "
                          "satır olarak bırakılmıştır, bu da tez yazım kılavuzuna aykırıdır (Smith & Jones, 2019).")
    for r in p.runs: r.font.name = "Arial"  # HATA
    p.paragraph_format.line_spacing = 1.0  # HATA
    doc.add_heading("Kuramsal Çerçeve", 2)  # UYARI: numarasız alt başlık
    doc.add_paragraph("Ekolojik sistemler kuramı (Bronfenbrenner, 1979) bireyin gelişimini iç içe geçmiş sistemler içinde ele alır. "
                      "Coleman (1988) ise aileyi sosyal sermayenin temel kaynağı olarak tanımlar. Bu tezde Becker (1964) yaklaşımı da kullanılmıştır.")
    doc.add_heading("2. YÖNTEM", 1)
    doc.add_paragraph("Tablo 2.1. Katılımcıların demografik özellikleri")
    t = doc.add_table(rows=3, cols=3); t.style = "Table Grid"
    for i, row in enumerate([["Değişken", "n", "%"], ["Kadın", "230", "54.8"], ["Erkek", "190", "45.2"]]):
        for j, v in enumerate(row): t.cell(i, j).text = v
    doc.add_paragraph("Tablo 2.1 Örneklem dağılımı")  # HATA: noktasız ve tekrar numara
    doc.add_table(rows=2, cols=2).style = "Table Grid"
    doc.add_paragraph("Sekil 1 Araştırma modeli")  # HATA: biçim
    doc.add_heading("3. SONUÇ", 1)
    p = doc.add_paragraph("Bulgular, aile temelli müdahalelerin NEET riskini azaltabileceğini göstermektedir (Yilmaz & Kaya, 2021).")
    p.runs[0].font.size = Pt(11)  # HATA: punto
    doc.add_paragraph("KAYNAKÇA")
    for k in [
        "Becker, G. S. (1964). Human capital. University of Chicago Press.",
        "Coleman, J. S. (1988). Social capital in the creation of human capital. American Journal of Sociology, 94, S95–S120. doi: 10.1086/228943",
        "Bronfenbrenner, U. (1979). The ecology of human development. Harvard University Press.",  # alfabe bozuk
        "Eurofound. (2016). Exploring the diversity of NEETs. Publications Office of the European Union.",
        "OECD. (2016). Society at a glance 2016: A spotlight on youth. OECD Publishing.",
        "Kaplan, M. (2017). Gençlik ve istihdam politikaları. Ankara: Örnek Yayınları.",  # metinde yok
        "Şahin, A. (2018). Ailenin eğitim kararlarındaki rolü. Sosyal Politika Dergisi, 12(2), 45–60.",
        "Yılmaz, E., & Kaya, B. (2020). Aile desteği ve gençlerin istihdamı. Çalışma ve Toplum, 3, 1201–1224. https://doi.org/10.0000/ornek.2020",
    ]:
        doc.add_paragraph(k)
    doc.save(D / "ornek_tez.docx")


# ------------------------------------------------ 2+4: anket verisi (.sav ve .xlsx)
def ornek_anket():
    rng = np.random.default_rng(2026); n = 420
    cins = rng.choice([1, 2], n); egit = rng.choice([1, 2, 3, 4], n, p=[.15, .35, .35, .15])
    yas = rng.integers(18, 30, n)
    destek = rng.normal(0, 1, n) + (egit - 2.5) * .25
    def lik(lat, k, ters=()):
        out = np.clip(np.round(3 + lat[:, None] * .9 + rng.normal(0, .85, (n, k))), 1, 5)
        for j in ters: out[:, j] = 6 - out[:, j]
        return out
    ad = lik(destek, 6, ters=(2, 5))                       # Aile Desteği AD1..AD6 (AD3, AD6 ters)
    umut = .5 * destek + rng.normal(0, .9, n) - (cins == 1) * .25
    ug = lik(umut, 5)                                       # Gelecek Umudu GU1..GU5
    df = pd.DataFrame(np.column_stack([ad, ug]).astype(int), columns=[f"AD{i}" for i in range(1, 7)] + [f"GU{i}" for i in range(1, 6)])
    df.insert(0, "yas", yas); df.insert(0, "egitim", egit); df.insert(0, "cinsiyet", cins)
    df["neet"] = np.where(umut + rng.normal(0, 1, n) < -.6, 1, 2)
    df.loc[rng.choice(n, 6, replace=False), "AD2"] = np.nan  # eksik veri
    df.loc[rng.choice(n, 2, replace=False), "GU3"] = 7      # aralık dışı (ölçek puanlamada yakalanacak)
    etiket = {"cinsiyet": {1: "Kadın", 2: "Erkek"}, "egitim": {1: "İlkokul", 2: "Lise", 3: "Lisans", 4: "Lisansüstü"}, "neet": {1: "Evet", 2: "Hayır"}}
    pyreadstat.write_sav(df, D / "ornek_anket.sav", column_labels={"cinsiyet": "Cinsiyet", "egitim": "Eğitim Durumu", "yas": "Yaş", "neet": "NEET Durumu"},
                         variable_value_labels=etiket)
    x = df.copy()
    for k, m in etiket.items(): x[k] = x[k].map(m)
    x.to_excel(D / "ornek_anket.xlsx", index=False)


# ------------------------------------------------ 6: örnek makale PDF'leri
def ornek_pdfler():
    pdfmetrics.registerFont(TTFont("DV", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
    st = getSampleStyleSheet()
    for s in st.byName.values(): s.fontName = "DV"
    klasor = D / "makaleler"; klasor.mkdir(exist_ok=True)
    makaleler = [
        ("ornek_nicel.pdf", "Journal of Youth Studies (örnek) · Vol. 12 · 2022",
         "Family Support and NEET Status Among Young Adults: Evidence from a National Survey",
         "A. Example, B. Sample", "https://doi.org/10.0000/jys.2022.001",
         "This study uses survey data from 2,450 respondents aged 15–29 in Türkiye. Using logistic regression and multilevel models, "
         "we find that perceived family support is associated with a lower probability of NEET status.",
         "NEET; family support; youth employment; Türkiye"),
        ("ornek_nitel.pdf", "Sosyal Politika Çalışmaları (örnek) · Cilt 8 · 2021",
         "Eğitim ve İstihdam Dışındaki Genç Kadınların Deneyimleri: Nitel Bir Çalışma",
         "C. Örnek", "https://doi.org/10.0000/spc.2021.044",
         "Bu çalışmada 24 genç kadınla yarı yapılandırılmış görüşme yapılmış, veriler tematik analiz ile çözümlenmiştir. "
         "Bulgular bakım sorumluluklarının ve ulaşım güçlüklerinin belirleyici olduğunu göstermektedir.",
         "NEET; genç kadınlar; bakım; nitel araştırma"),
        ("ornek_derleme.pdf", "European Policy Review (örnek) · 2019",
         "What Works for NEET Youth? A Systematic Review of Activation Programmes in Europe",
         "D. Review, E. Author", "https://doi.org/10.0000/epr.2019.310",
         "We conducted a systematic review and meta-analysis of 38 evaluations of youth activation programmes in Europe and OECD countries.",
         "systematic review; Youth Guarantee; activation; Europe"),
    ]
    for dosya, dergi, baslik, yazar, doi, ozet, kel in makaleler:
        tr = "Öz" if "Çalışma" in dergi else "Abstract"
        kw = "Anahtar Kelimeler" if tr == "Öz" else "Keywords"
        icerik = [Paragraph(dergi, st["Normal"]), Spacer(1, 8), Paragraph(baslik, st["Title"]), Paragraph(yazar, st["Normal"]),
                  Paragraph(doi, st["Normal"]), Spacer(1, 12), Paragraph(f"<b>{tr}</b>", st["Normal"]), Paragraph(ozet, st["Normal"]),
                  Spacer(1, 6), Paragraph(f"<b>{kw}:</b> {kel}", st["Normal"]), Spacer(1, 12),
                  Paragraph("<b>1. Introduction</b>" if tr == "Abstract" else "<b>1. Giriş</b>", st["Normal"]),
                  Paragraph("Kurgusal örnek metin. " * 30, st["Normal"])]
        SimpleDocTemplate(str(klasor / dosya), pagesize=A4, title=baslik, author=yazar).build(icerik)


if __name__ == "__main__":
    ornek_tez(); ornek_anket(); ornek_pdfler()
    print("Örnekler üretildi:", sorted(p.name for p in D.rglob("*.*") if p.suffix in (".docx", ".sav", ".xlsx", ".pdf")))
