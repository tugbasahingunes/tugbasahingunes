"""Creates a small e-commerce SQLite database and runs the analysis queries in queries.sql."""
import sqlite3, numpy as np, pandas as pd, re
rng=np.random.default_rng(8); con=sqlite3.connect("shop.db")
cities=["Ankara","İstanbul","İzmir","Bursa","Antalya"]
pd.DataFrame({"customer_id":range(1,301),"city":rng.choice(cities,300),
  "signup_date":pd.to_datetime("2025-01-01")+pd.to_timedelta(rng.integers(0,300,300),"D")}).to_sql("customers",con,if_exists="replace",index=False)
pd.DataFrame({"product_id":range(1,11),"category":rng.choice(["Kozmetik","Ev","Kitap"],10),"price":rng.integers(80,900,10)}).to_sql("products",con,if_exists="replace",index=False)
o=pd.DataFrame({"order_id":range(1,2001),"customer_id":rng.integers(1,301,2000),
  "order_date":pd.to_datetime("2025-02-01")+pd.to_timedelta(rng.integers(0,330,2000),"D")})
o["order_date"]=o.order_date.dt.strftime("%Y-%m-%d"); o.to_sql("orders",con,if_exists="replace",index=False)
pd.DataFrame({"order_id":rng.integers(1,2001,4000),"product_id":rng.integers(1,11,4000),"qty":rng.integers(1,4,4000)}).to_sql("order_items",con,if_exists="replace",index=False)
out=open("query_results.md","w")
for block in open("queries.sql").read().split(";"):
    if "SELECT" not in block: continue
    title=re.search(r"-- (.+)",block).group(1)
    out.write(f"### {title}\n\n"+pd.read_sql(block,con).head(10).to_markdown(index=False)+"\n\n")
print("done")
