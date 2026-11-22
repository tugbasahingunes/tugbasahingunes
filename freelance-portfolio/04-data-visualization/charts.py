"""Publication-ready charts from one tidy dataset: line, ranked bar, small multiples, slope."""
import numpy as np, pandas as pd, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams.update({"font.family":"DejaVu Sans","axes.spines.top":False,"axes.spines.right":False,"axes.grid":True,"grid.alpha":.3})
rng=np.random.default_rng(5); C=["Finlandiya","Almanya","Fransa","İspanya","Türkiye","İtalya"]
base=dict(zip(C,[9,8,12,15,24,19])); yrs=range(2014,2025)
df=pd.DataFrame([(c,y,max(4,base[c]-(y-2014)*.35+rng.normal(0,.6))) for c in C for y in yrs],columns=["ulke","yil","oran"])
df.to_csv("data.csv",index=False); P=["#1f4e79","#2e86ab","#a23b72","#f18f01","#c73e1d","#6a994e"]
fig,ax=plt.subplots(figsize=(9,5))
for c,col in zip(C,P):
    s=df[df.ulke==c]; ax.plot(s.yil,s.oran,color=col,lw=2.5 if c=="Türkiye" else 1.5,alpha=1 if c=="Türkiye" else .7)
    ax.text(2024.2,s.oran.iloc[-1],c,color=col,va="center",fontsize=9)
ax.set_title("Gösterge oranı, 2014–2024 (%)",loc="left",fontweight="bold"); ax.set_xlim(2014,2026)
fig.text(.01,.01,"Kaynak: sentetik örnek veri",fontsize=8,color="gray"); fig.tight_layout(); fig.savefig("01_line.png",dpi=150)
last=df[df.yil==2024].sort_values("oran")
fig,ax=plt.subplots(figsize=(8,4.5)); ax.barh(last.ulke,last.oran,color=["#c73e1d" if u=="Türkiye" else "#9db4c0" for u in last.ulke])
for y,v in enumerate(last.oran): ax.text(v+.2,y,f"{v:.1f}",va="center")
ax.set_title("2024 sıralaması",loc="left",fontweight="bold"); ax.grid(axis="y"); fig.tight_layout(); fig.savefig("02_ranked_bar.png",dpi=150)
fig,axs=plt.subplots(2,3,figsize=(10,5.5),sharey=True)
for a,c in zip(axs.flat,C):
    for o in C: s=df[df.ulke==o]; a.plot(s.yil,s.oran,color="#ddd",lw=1)
    s=df[df.ulke==c]; a.plot(s.yil,s.oran,color="#1f4e79",lw=2); a.set_title(c,fontsize=10)
fig.suptitle("Küçük çoklu grafikler: her ülke diğerlerinin arka planında",x=.01,ha="left",fontweight="bold"); fig.tight_layout(); fig.savefig("03_small_multiples.png",dpi=150)
fig,ax=plt.subplots(figsize=(5,6))
for c,col in zip(C,P):
    a,b=df[(df.ulke==c)&(df.yil==2014)].oran.iloc[0],df[(df.ulke==c)&(df.yil==2024)].oran.iloc[0]
    ax.plot([0,1],[a,b],marker="o",color=col); ax.text(1.05,b,f"{c} {b:.1f}",va="center",fontsize=9,color=col)
ax.set_xticks([0,1],["2014","2024"]); ax.set_xlim(-.2,1.6); ax.set_title("2014 → 2024 değişim",loc="left",fontweight="bold"); fig.tight_layout(); fig.savefig("04_slope.png",dpi=150)
print("4 charts")
