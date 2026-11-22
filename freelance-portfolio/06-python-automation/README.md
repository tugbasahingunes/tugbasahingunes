# 06 · Python Automation (Excel → PDF, bulk documents, repetitive tasks)

**Client problem:** "Every month we prepare 300 certificates / invoices / reports by hand in Word."

`generate_reports.py` reads `participants.xlsx` and writes one personalised, print-ready PDF per row to `output/` (Turkish characters supported). Same pattern works for invoices, payslips, offer letters, personalised parent reports, mail-merge e-mails.

Other automations I build: merging hundreds of Excel files, renaming/organising files, scheduled reports by e-mail, PDF table extraction, Google Drive/Sheets API jobs.

```bash
pip install pandas openpyxl reportlab
python generate_reports.py
```
