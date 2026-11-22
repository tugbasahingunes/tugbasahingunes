"""Turn one Excel sheet into one personalised PDF per row (certificates, payslips, invoices,
participant reports). Here: training-completion certificates."""
import pathlib, pandas as pd
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics; from reportlab.pdfbase.ttfonts import TTFont
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
pdfmetrics.registerFont(TTFont("DV",FONT)); pdfmetrics.registerFont(TTFont("DVB",FONT.replace("Sans.","Sans-Bold.")))
src=pathlib.Path("participants.xlsx")
if not src.exists():
    pd.DataFrame({"ad_soyad":["Ayşe Yılmaz","Mehmet Kaya","Zeynep Şahin","Ali Demir","Elif Çelik"],
                  "egitim":["Veri Analizine Giriş"]*3+["Excel ile Raporlama"]*2,
                  "saat":[24,24,24,12,12],"tarih":["15.11.2026"]*5}).to_excel(src,index=False)
out=pathlib.Path("output"); out.mkdir(exist_ok=True)
W,H=landscape(A4)
for i,r in pd.read_excel(src).iterrows():
    c=canvas.Canvas(str(out/f"sertifika_{i+1:03d}.pdf"),pagesize=(W,H))
    c.setStrokeColorRGB(.12,.31,.47); c.setLineWidth(6); c.rect(30,30,W-60,H-60)
    c.setFont("DVB",34); c.drawCentredString(W/2,H-140,"KATILIM SERTİFİKASI")
    c.setFont("DV",16); c.drawCentredString(W/2,H-200,"Bu belge")
    c.setFont("DVB",28); c.drawCentredString(W/2,H-250,r.ad_soyad)
    c.setFont("DV",16); c.drawCentredString(W/2,H-300,f"“{r.egitim}” eğitimini ({r.saat} saat) başarıyla tamamladığını gösterir.")
    c.drawCentredString(W/2,90,f"Tarih: {r.tarih}"); c.save()
print(len(list(out.glob('*.pdf'))),"PDF")
