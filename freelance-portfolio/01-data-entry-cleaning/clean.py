"""Clean a messy customer list: fix names, phones, emails, dates, duplicates.
Usage: python clean.py raw_customers.csv"""
import re, sys, pandas as pd, numpy as np

def make_raw(path):
    rng = np.random.default_rng(7)
    first = ["ayşe","MEHMET","  Zeynep","ali ","Elif","burak","Selin","CAN","deniz","Emre"]
    last  = ["yılmaz","KAYA","demir ","Şahin","çelik","Aydın","öztürk","ARSLAN","doğan","kılıç"]
    cities= ["ankara","Ankara ","ANKARA","istanbul","İstanbul","izmir","Izmir","bursa"]
    rows=[]
    for i in range(120):
        f,l=rng.choice(first),rng.choice(last)
        phone=rng.choice(["0532 {} {} {}","+90 (532) {}-{}-{}","532{}{}{}","0532-{}-{}-{}"]).format(
            rng.integers(100,999),rng.integers(10,99),rng.integers(10,99))
        email=f"{f.strip().lower()}.{l.strip().lower()}@{rng.choice(['gmail.com','GMAIL.COM','hotmail','outlook.com'])}"
        date=rng.choice(["2025-03-{:02d}","{:02d}/04/2025","{:02d}.05.2025"]).format(rng.integers(1,28))
        rows.append([f"{f} {l}",phone,email,rng.choice(cities),date,rng.choice(["1.250,50","980","1250.5","", "n/a"])])
    df=pd.DataFrame(rows,columns=["Ad Soyad","Telefon","E-posta","Şehir","Kayıt Tarihi","Tutar"])
    df=pd.concat([df,df.sample(15,random_state=1)])  # duplicates
    df.to_csv(path,index=False)

TR_UP = str.maketrans("iı","İI")
def title_tr(s):
    return " ".join(w[:1].translate(TR_UP).upper()+w[1:].lower() for w in str(s).split())

def phone(s):
    d=re.sub(r"\D","",str(s))[-10:]
    return f"+90 {d[:3]} {d[3:6]} {d[6:8]} {d[8:]}" if len(d)==10 else None

def email(s):
    s=str(s).strip().lower()
    if re.fullmatch(r"[\w.]+@[\w-]+",s): s+=".com"
    return s if re.fullmatch(r"[\w.]+@[\w-]+\.\w+",s) else None

def amount(s):
    s=str(s).strip()
    if s in ("","nan","n/a"): return np.nan
    if "," in s: s=s.replace(".","").replace(",",".")
    return float(s)

def run(src):
    df=pd.read_csv(src,dtype=str)
    log={"raw_rows":len(df)}
    out=pd.DataFrame({
      "ad_soyad":df["Ad Soyad"].map(title_tr),
      "telefon":df["Telefon"].map(phone),
      "eposta":df["E-posta"].map(email),
      "sehir":df["Şehir"].str.strip().str.replace("I","İ",regex=False).map(title_tr).replace({"Izmir":"İzmir","Istanbul":"İstanbul"}),
      "kayit_tarihi":pd.to_datetime(df["Kayıt Tarihi"].str.replace(".","/"),format="mixed",dayfirst=True).dt.date,
      "tutar_tl":df["Tutar"].map(amount)})
    out=out.drop_duplicates(); log["duplicates_removed"]=log["raw_rows"]-len(out)
    log["missing_amount"]=int(out.tutar_tl.isna().sum()); log["clean_rows"]=len(out)
    out.to_excel("clean_customers.xlsx",index=False)
    pd.Series(log).to_csv("cleaning_log.csv",header=["value"])
    print(log)

if __name__=="__main__":
    src=sys.argv[1] if len(sys.argv)>1 else "raw_customers.csv"
    import os
    if not os.path.exists(src): make_raw(src)
    run(src)
