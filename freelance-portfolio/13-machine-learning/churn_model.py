"""Customer churn prediction: baseline vs gradient boosting, proper validation, business-readable output."""
import numpy as np, pandas as pd, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.inspection import permutation_importance
from sklearn.metrics import roc_auc_score, classification_report
rng=np.random.default_rng(42); n=4000
df=pd.DataFrame({"ay_sayisi":rng.integers(1,60,n),"aylik_ucret":rng.normal(350,90,n).round(),
 "destek_talebi":rng.poisson(1.2,n),"sozlesme":rng.choice(["Aylık","Yıllık"],n,p=[.6,.4]),
 "kampanya":rng.choice([0,1],n,p=[.7,.3])})
z=-1.2-0.04*df.ay_sayisi+0.004*(df.aylik_ucret-350)+0.45*df.destek_talebi+1.1*(df.sozlesme=="Aylık")-0.6*df.kampanya
df["ayrildi"]=(rng.random(n)<1/(1+np.exp(-z))).astype(int); df.to_csv("customers.csv",index=False)
X=pd.get_dummies(df.drop(columns="ayrildi"),drop_first=True).astype(float); y=df.ayrildi
Xtr,Xte,ytr,yte=train_test_split(X,y,test_size=.25,stratify=y,random_state=0)
lr=LogisticRegression(max_iter=1000).fit(Xtr,ytr); gb=HistGradientBoostingClassifier(max_depth=3,random_state=0).fit(Xtr,ytr)
res={m:roc_auc_score(yte,mod.predict_proba(Xte)[:,1]) for m,mod in [("Logistic",lr),("GradBoost",gb)]}
best=max(res,key=res.get); mod={"Logistic":lr,"GradBoost":gb}[best]
p=mod.predict_proba(Xte)[:,1]
imp=permutation_importance(mod,Xte,yte,scoring="roc_auc",n_repeats=10,random_state=0)
fi=pd.Series(imp.importances_mean,index=X.columns).sort_values()
fi.plot.barh(color="#2457a6",figsize=(6,3.5),title="What drives churn (permutation importance)"); plt.tight_layout(); plt.savefig("feature_importance.png",dpi=150)
top=pd.DataFrame({"risk":p},index=Xte.index).join(df).sort_values("risk",ascending=False)
top.head(200).to_csv("high_risk_customers.csv")
lift=yte.loc[top.index[:200]].mean()/yte.mean()
txt=f"AUC: {res}\nBest: {best}\nTop-200 risk list catches churners at {lift:.1f}x the base rate ({yte.mean():.1%}).\n\n"+classification_report(yte,(p>.5).astype(int))
open("model_report.txt","w").write(txt); print(txt)
