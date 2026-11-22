# 02 · Excel Dashboard & Reporting

**Client problem:** "Every month I copy-paste sales numbers into PowerPoint. I want one Excel file that updates itself."

**Deliverable:** `sales_dashboard.xlsx`
- **Data** sheet: formatted table with filters, frozen header, calculated column
- **Dashboard** sheet: KPI cards, `SUMIF` / `SUMPRODUCT` summaries, colour scale, bar and line charts
- Everything is **formula-driven**: paste next month's data and the dashboard updates. No macros, so it opens safely anywhere.

Also offered: pivot tables, XLOOKUP/INDEX-MATCH cleanup, Power Query, Google Sheets versions, KPI templates for HR/finance/NGO reporting.

`build.py` regenerates the workbook (openpyxl).
