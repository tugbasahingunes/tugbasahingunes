# Interactive Results Dashboard: NGO / Programme Monitoring

**Service:** dashboards · KPI tracking · monitoring & evaluation (M&E) · donor reporting · Excel / Looker Studio / Power BI / web dashboards

**Client problem:** "Every quarter we rebuild the donor report by hand from six regional spreadsheets. Management can't see which regions are off track."

**Deliverable:** [`index.html`](index.html), a single-file interactive dashboard (open it in a browser; works fully offline):
- Region and quarter filters
- KPI cards with **RAG status** against logframe targets (completion, employment within 6 months, share of young women, satisfaction)
- Results chain by quarter (enrolled → completed → employed)
- Employment rate by region vs target line
- Indicator tracking table with gaps
- **Cost per job outcome**, the number donors ask for

Data pipeline: [`build.py`](build.py) → `monitoring_data.csv` → dashboard. For a client the same structure connects to Google Sheets, KoboToolbox or a database.

```bash
python build.py && open index.html
```
Background: 10+ years of monitoring social programmes and official statistics in the public sector. *All data here is fictional.*
