"""Employee-satisfaction survey: reliability, crosstabs, chi-square, t-test, regression.
Produces report tables (CSV/Excel) the way an SPSS user would expect them."""
import numpy as np, pandas as pd, statsmodels.formula.api as smf
from scipy import stats
rng=np.random.default_rng(11); n=420
dept=rng.choice(["Satış","Operasyon","IT","İK"],n,p=[.35,.35,.2,.1])
gender=rng.choice(["Kadın","Erkek"],n); tenure=rng.integers(0,20,n)
latent=rng.normal(0,1,n)+np.where(dept=="IT",.4,0)-tenure*.02
items=np.clip(np.round(3+latent[:,None]+rng.normal(0,.8,(n,5))),1,5).astype(int)
df=pd.DataFrame(items,columns=[f"S{i}" for i in range(1,6)])
df["departman"],df["cinsiyet"],df["kidem"]=dept,gender,tenure
df["ayrilma_niyeti"]=np.where(latent+rng.normal(0,1,n)<-0.5,"Evet","Hayır")
df.to_csv("survey_data.csv",index=False)
it=df[[f"S{i}" for i in range(1,6)]]; k=it.shape[1]
alpha=k/(k-1)*(1-it.var(ddof=1).sum()/it.sum(axis=1).var(ddof=1))
df["memnuniyet"]=it.mean(axis=1)
desc=df.groupby("departman")["memnuniyet"].agg(["count","mean","std"]).round(2)
ct=pd.crosstab(df.departman,df.ayrilma_niyeti,margins=True)
chi=stats.chi2_contingency(pd.crosstab(df.departman,df.ayrilma_niyeti))
t=stats.ttest_ind(df.memnuniyet[df.cinsiyet=="Kadın"],df.memnuniyet[df.cinsiyet=="Erkek"],equal_var=False)
an=stats.f_oneway(*[g.memnuniyet for _,g in df.groupby("departman")])
m=smf.ols("memnuniyet ~ C(departman) + kidem + C(cinsiyet)",df).fit()
with pd.ExcelWriter("survey_report_tables.xlsx") as w:
    desc.to_excel(w,sheet_name="Descriptives"); ct.to_excel(w,sheet_name="Crosstab")
    pd.DataFrame(m.summary2().tables[1]).round(3).to_excel(w,sheet_name="Regression")
summary=f"""Cronbach alpha (5 items): {alpha:.2f}
Chi-square departman x ayrilma niyeti: chi2={chi[0]:.2f}, df={chi[2]}, p={chi[1]:.4f}
Welch t-test kadin vs erkek: t={t.statistic:.2f}, p={t.pvalue:.3f}
One-way ANOVA departman: F={an.statistic:.2f}, p={an.pvalue:.4f}
OLS R2={m.rsquared:.3f}; kidem b={m.params['kidem']:.3f} (p={m.pvalues['kidem']:.4f})"""
open("results_summary.txt","w").write(summary); print(summary)
