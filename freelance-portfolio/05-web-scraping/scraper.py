"""Paginated product scraper -> CSV/Excel. Works on local sample pages here;
for a live site, swap `fetch` for requests.get with headers, delays and robots.txt check."""
import pathlib, time, pandas as pd
from bs4 import BeautifulSoup
BASE=pathlib.Path(__file__).parent/"sample_pages"
def fetch(name): time.sleep(0.1); return (BASE/name).read_text(encoding="utf-8")
def price(t): return float(t.replace("TL","").strip().replace(".","").replace(",","."))
def scrape(start="page1.html"):
    rows,page=[],start
    while page:
        s=BeautifulSoup(fetch(page),"html.parser")
        for c in s.select(".product"):
            rows.append({"urun":c.select_one(".title").get_text(strip=True),
                         "fiyat_tl":price(c.select_one(".price").text),
                         "puan":float(c.select_one(".rating")["data-score"]),
                         "stokta":c.select_one(".stock").text=="Stokta",
                         "link":c.a["href"],"sayfa":page})
        n=s.select_one("a.next"); page=n["href"] if n else None
    return pd.DataFrame(rows)
if __name__=="__main__":
    df=scrape(); df.to_csv("products.csv",index=False); df.to_excel("products.xlsx",index=False); print(df)
