# 14 · SQL Data Analysis

**Client problem:** "Our data is in a database. I need answers, not a data team."

E-commerce sample database (`shop.db`, SQLite: customers, products, orders, order_items) with five business queries in [`queries.sql`](queries.sql):

1. Monthly revenue + month-over-month growth (CTE, `LAG` window function)
2. Revenue by city × category
3. Top customers by lifetime value (`RANK`)
4. **RFM segmentation** (Sadık / Aktif / Risk altında / Kayıp)
5. Repeat-purchase rate

Results: [`query_results.md`](query_results.md). Rebuild with `python build_db.py`.

I work with SQLite, PostgreSQL, MySQL, BigQuery; can deliver queries, a cleaned extract, or a connected Looker Studio / Excel report.
