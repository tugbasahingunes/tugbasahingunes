"""Builds a project-management workbook: task tracker with live Gantt, RACI matrix, risk register,
meeting-action log. Pure Excel formulas + conditional formatting, so it works in Excel and Google Sheets."""
import datetime as dt
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.formatting.rule import FormulaRule, CellIsRule
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import get_column_letter as L

H = PatternFill("solid", fgColor="1F4E78"); W = Font(bold=True, color="FFFFFF"); thin = Side(style="thin", color="DDDDDD")
START = dt.date(2026, 12, 1)
tasks = [  # id, workstream, task, owner, start offset (days), duration, status, % done
 ("T1", "Planning", "Kick-off meeting & scope sign-off", "Project lead", 0, 2, "Done", 1),
 ("T2", "Planning", "Stakeholder map & communication plan", "Project lead", 2, 4, "Done", 1),
 ("T3", "Research", "Questionnaire design", "Researcher", 4, 6, "In progress", .6),
 ("T4", "Research", "Ethics / data-protection review", "Legal", 8, 5, "Not started", 0),
 ("T5", "Research", "Fieldwork (online survey)", "Researcher", 13, 14, "Not started", 0),
 ("T6", "Analysis", "Data cleaning & weighting", "Analyst", 27, 4, "Not started", 0),
 ("T7", "Analysis", "Statistical analysis", "Analyst", 31, 6, "Not started", 0),
 ("T8", "Reporting", "Draft report", "Researcher", 37, 7, "Not started", 0),
 ("T9", "Reporting", "Client review & revisions", "Project lead", 44, 5, "Not started", 0),
 ("T10", "Reporting", "Final presentation", "Project lead", 49, 1, "Not started", 0),
]
wb = Workbook(); ws = wb.active; ws.title = "Tracker"
ws["A1"] = "Project: Customer Survey 2027"; ws["A1"].font = Font(size=16, bold=True, color="1F4E78")
ws["A2"] = "Today"; ws["B2"] = "=TODAY()"; ws["B2"].number_format = "dd.mm.yyyy"
ws["D2"] = "Overall progress"; ws["E2"] = "=SUMPRODUCT(F5:F14,H5:H14)/SUM(F5:F14)"; ws["E2"].number_format = "0%"
ws["G2"] = "Overdue tasks"; ws["H2"] = '=COUNTIFS(E5:E14,"<"&TODAY(),G5:G14,"<>Done")'
hdr = ["ID", "Workstream", "Task", "Owner", "Start", "Days", "End", "% done", "Status", "Health"]
weeks = 8
for i, h in enumerate(hdr, 1):
    c = ws.cell(4, i, h); c.fill = H; c.font = W
for d in range(weeks * 7):
    col = len(hdr) + 1 + d
    c = ws.cell(4, col, f"=$E$5+{d}"); c.number_format = "dd"; c.fill = H; c.font = Font(color="FFFFFF", size=8)
    c.alignment = Alignment(horizontal="center"); ws.column_dimensions[L(col)].width = 3
    ws.cell(3, col, f'=IF(WEEKDAY({L(col)}4,2)=1,"W"&WEEKNUM({L(col)}4,2),"")').font = Font(size=8, color="1F4E78")
for r, (tid, wsn, t, o, s, du, st, p) in enumerate(tasks, 5):
    ws.append([]) if False else None
    vals = [tid, wsn, t, o, START + dt.timedelta(days=s), du, f"=E{r}+F{r}-1", p, st,
            f'=IF(I{r}="Done","✔ done",IF(G{r}<TODAY(),"⚠ late",IF(AND(E{r}<=TODAY(),H{r}<(TODAY()-E{r}+1)/F{r}),"● behind","○ on track")))']
    for c, v in enumerate(vals, 1):
        cell = ws.cell(r, c, v); cell.border = Border(bottom=thin)
    ws.cell(r, 5).number_format = ws.cell(r, 7).number_format = "dd.mm.yyyy"; ws.cell(r, 8).number_format = "0%"
first, last = L(len(hdr) + 1), L(len(hdr) + weeks * 7)
rng = f"{first}5:{last}14"
ws.conditional_formatting.add(rng, FormulaRule(formula=[f"AND({first}$4>=$E5,{first}$4<$E5+$F5*$H5)"], fill=PatternFill("solid", fgColor="2457A6")))
ws.conditional_formatting.add(rng, FormulaRule(formula=[f"AND({first}$4>=$E5,{first}$4<=$G5)"], fill=PatternFill("solid", fgColor="A9C4EB")))
ws.conditional_formatting.add(rng, FormulaRule(formula=[f"{first}$4=TODAY()"], fill=PatternFill("solid", fgColor="F4C95D")))
ws.conditional_formatting.add("J5:J14", FormulaRule(formula=['LEFT(J5,1)="⚠"'], font=Font(color="C73E1D", bold=True)))
dv = DataValidation(type="list", formula1='"Not started,In progress,Blocked,Done"'); ws.add_data_validation(dv); dv.add("I5:I14")
for col, w in zip("ABCDEFGHIJ", [5, 12, 38, 14, 11, 6, 11, 8, 12, 12]): ws.column_dimensions[col].width = w
ws.freeze_panes = "E5"

# RACI
r = wb.create_sheet("RACI"); roles = ["Project lead", "Researcher", "Analyst", "Legal", "Client"]
r.append(["Task"] + roles)
raci = {"T1": "ARIII", "T2": "ACIIC", "T3": "ARCCC", "T4": "AICRI", "T5": "ARIII", "T6": "ACRII", "T7": "ACRII", "T8": "ARCII", "T9": "RCCIA", "T10": "RCCIA"}
for t in tasks: r.append([f"{t[0]} {t[2]}"] + list(raci[t[0]]))
for c in r[1]: c.fill = H; c.font = W
colors = {"R": "2457A6", "A": "1D2A3A", "C": "F4C95D", "I": "DDE6F0"}
for k, v in colors.items():
    r.conditional_formatting.add("B2:F11", CellIsRule(operator="equal", formula=[f'"{k}"'], fill=PatternFill("solid", fgColor=v), font=Font(color="FFFFFF" if k in "RA" else "1D2A3A", bold=True)))
r.column_dimensions["A"].width = 42; r.append([]); r.append(["R = Responsible · A = Accountable · C = Consulted · I = Informed"])

# Risk register
k = wb.create_sheet("Risks"); k.append(["ID", "Risk", "Likelihood (1-5)", "Impact (1-5)", "Score", "Mitigation", "Owner"])
for row in [("R1", "Low survey response rate", 3, 4, "Reminder e-mails, incentive, extend fieldwork 1 week", "Researcher"),
            ("R2", "Data-protection approval delayed", 2, 5, "Submit early; use anonymous survey design", "Legal"),
            ("R3", "Client feedback late", 4, 3, "Fixed review window in contract", "Project lead"),
            ("R4", "Key analyst unavailable", 2, 4, "Documented analysis scripts; backup analyst", "Project lead")]:
    k.append(list(row[:4]) + [None] + list(row[4:]))
for i in range(2, 6): k[f"E{i}"] = f"=C{i}*D{i}"
for c in k[1]: c.fill = H; c.font = W
k.conditional_formatting.add("E2:E5", CellIsRule(operator="greaterThanOrEqual", formula=["12"], fill=PatternFill("solid", fgColor="F8696B")))
k.conditional_formatting.add("E2:E5", CellIsRule(operator="between", formula=["6", "11"], fill=PatternFill("solid", fgColor="FFD966")))
k.column_dimensions["B"].width = 34; k.column_dimensions["F"].width = 50

# Actions log
a = wb.create_sheet("Actions"); a.append(["Date", "Meeting", "Action", "Owner", "Due", "Done?"])
a.append([dt.date(2026, 12, 1), "Kick-off", "Share final scope document", "Project lead", dt.date(2026, 12, 3), "Yes"])
a.append([dt.date(2026, 12, 1), "Kick-off", "Send sample questionnaire to client", "Researcher", dt.date(2026, 12, 8), "No"])
for c in a[1]: c.fill = H; c.font = W
wb.save("project_tracker.xlsx"); print("project_tracker.xlsx")
