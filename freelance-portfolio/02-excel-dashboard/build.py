"""Builds a sales dashboard workbook with live formulas, a pivot-style summary and charts."""
import numpy as np, pandas as pd
from openpyxl import Workbook
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.formatting.rule import ColorScaleRule
rng=np.random.default_rng(3)
months=pd.date_range("2025-01-01",periods=12,freq="MS")
regions=["Marmara","İç Anadolu","Ege","Akdeniz","Karadeniz"]
products=["Ürün A","Ürün B","Ürün C"]
rows=[[m.strftime("%Y-%m"),r,p,int(rng.integers(20,200)),int(rng.integers(80,150))] for m in months for r in regions for p in products]
wb=Workbook(); ws=wb.active; ws.title="Data"
ws.append(["Ay","Bölge","Ürün","Adet","Birim Fiyat","Ciro"])
for i,r in enumerate(rows,start=2): ws.append(r+[f"=D{i}*E{i}"])
n=len(rows)+1
hdr=PatternFill("solid",fgColor="1F4E78")
for c in ws[1]: c.font=Font(bold=True,color="FFFFFF"); c.fill=hdr
ws.auto_filter.ref=f"A1:F{n}"; ws.freeze_panes="A2"
d=wb.create_sheet("Dashboard",0)
d["A1"]="Satış Paneli 2025"; d["A1"].font=Font(size=18,bold=True,color="1F4E78")
kpis=[("Toplam Ciro",f"=SUM(Data!F2:F{n})"),("Toplam Adet",f"=SUM(Data!D2:D{n})"),("Ort. Birim Fiyat",f"=SUMPRODUCT(Data!D2:D{n},Data!E2:E{n})/SUM(Data!D2:D{n})")]
for i,(k,f) in enumerate(kpis):
    col=chr(65+i*2); d[f"{col}3"]=k; d[f"{col}4"]=f
    d[f"{col}3"].font=Font(bold=True); d[f"{col}4"].font=Font(size=14,bold=True); d[f"{col}4"].number_format="#,##0"
d["A6"]="Bölge"; d["B6"]="Ciro"
for i,r in enumerate(regions,start=7):
    d[f"A{i}"]=r; d[f"B{i}"]=f'=SUMIF(Data!B2:B{n},A{i},Data!F2:F{n})'; d[f"B{i}"].number_format="#,##0"
d.conditional_formatting.add("B7:B11",ColorScaleRule(start_type="min",start_color="F8696B",end_type="max",end_color="63BE7B"))
d["D6"]="Ay"; d["E6"]="Ciro"
for i,m in enumerate(months,start=7):
    d[f"D{i}"]=m.strftime("%Y-%m"); d[f"E{i}"]=f'=SUMIF(Data!A2:A{n},D{i},Data!F2:F{n})'; d[f"E{i}"].number_format="#,##0"
b=BarChart(); b.title="Bölgelere Göre Ciro"; b.add_data(Reference(d,min_col=2,min_row=6,max_row=11),titles_from_data=True); b.set_categories(Reference(d,min_col=1,min_row=7,max_row=11)); d.add_chart(b,"G3")
l=LineChart(); l.title="Aylık Ciro Trendi"; l.add_data(Reference(d,min_col=5,min_row=6,max_row=18),titles_from_data=True); l.set_categories(Reference(d,min_col=4,min_row=7,max_row=18)); d.add_chart(l,"G20")
for c in "ABCDE": d.column_dimensions[c].width=18
wb.save("sales_dashboard.xlsx"); print("saved")
