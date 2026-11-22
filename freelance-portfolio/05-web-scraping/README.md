# 05 · Web Scraping & Lead / Price Lists

**Client problem:** "I need the prices and stock status of competitor products every week in a spreadsheet."

`scraper.py` follows pagination, extracts title, price (Turkish number format → float), rating, stock and link, and writes `products.csv` / `products.xlsx`. The demo runs on local HTML pages in `sample_pages/` so it is reproducible.

**How I work on real projects**
- Respect `robots.txt` and site terms; polite delays; no login-protected or personal data scraping
- requests + BeautifulSoup for static pages, Playwright for JavaScript sites
- Scheduled runs (GitHub Actions / cron) with change alerts
- Typical jobs: price monitoring, directory/business listings, real-estate listings, academic data collection
