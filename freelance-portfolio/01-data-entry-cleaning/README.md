# 01 · Data Entry & Data Cleaning

**Client problem:** "I have a customer list exported from three different systems. Names are in mixed case, phone numbers in five formats, duplicates everywhere. I need one clean Excel file."

**What I deliver**
- Standardised names with correct Turkish capitalisation (i/İ, ı/I)
- Phone numbers in one format (`+90 532 123 45 67`)
- Validated e-mails, unified dates (ISO), numbers in one decimal system (`1.250,50` → `1250.50`)
- Duplicates removed, and a **cleaning log** so the client sees exactly what changed

| File | What it is |
|---|---|
| `raw_customers.csv` | Synthetic messy input (135 rows) |
| `clean.py` | Reproducible cleaning script |
| `clean_customers.xlsx` | Clean output |
| `cleaning_log.csv` | Rows in/out, duplicates, missing values |

```bash
python clean.py raw_customers.csv
```
Typical turnaround: 1,000–10,000 rows in 24 hours. Manual data entry from PDFs/scans also available.
