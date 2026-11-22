"""Consumer research for a new product: a phonics-based reading app for parents of 5–7-year-olds.
Synthetic survey (n=600) → Van Westendorp price sensitivity, segmentation (k-means),
feature importance (purchase-intent drivers), TAM/SAM/SOM, client report."""
import numpy as np, pandas as pd, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
rng = np.random.default_rng(21); n = 600
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, "font.family": "DejaVu Sans"})

# ---------- survey
income = rng.choice(["<30k", "30-60k", "60-100k", ">100k"], n, p=[.25, .35, .25, .15])
inc_w = pd.Series(income).map({"<30k": .7, "30-60k": 1, "60-100k": 1.3, ">100k": 1.7}).values
city = rng.choice(["Metropol", "Büyükşehir", "Diğer"], n, p=[.45, .35, .2])
screen_worry = rng.integers(1, 6, n); app_use = rng.integers(0, 4, n)
f = {k: np.clip(np.round(rng.normal(m, 1, n)), 1, 5) for k, m in
     [("f_curriculum_fit", 4.3), ("f_no_ads", 4.1), ("f_progress_report", 3.6), ("f_offline", 3.0), ("f_teacher_mode", 2.7), ("f_games", 3.4)]}
base = 120 * inc_w * rng.lognormal(0, .25, n)
vw = pd.DataFrame({"too_cheap": base * .35, "cheap": base * .65, "expensive": base * 1.25, "too_expensive": base * 1.8}).round(-1)
z = -2 + .55 * (f["f_curriculum_fit"] - 3) + .4 * (f["f_no_ads"] - 3) + .25 * (f["f_progress_report"] - 3) + .3 * app_use + .2 * (screen_worry - 3) + .4 * (inc_w - 1)
intent = (rng.random(n) < 1 / (1 + np.exp(-z))).astype(int)
df = pd.DataFrame({"income": income, "city": city, "screen_worry": screen_worry, "edu_app_use": app_use, **f, **vw, "would_buy": intent})
df.to_csv("survey_data.csv", index=False)

# ---------- Van Westendorp
grid = np.arange(20, 500, 5)
tc = [(df.too_cheap >= p).mean() for p in grid]; ch = [(df.cheap >= p).mean() for p in grid]
ex = [(df.expensive <= p).mean() for p in grid]; te = [(df.too_expensive <= p).mean() for p in grid]
cross = lambda a, b: grid[np.argmin(np.abs(np.array(a) - np.array(b)))]
PMC, OPP, IPP, PME = cross(tc, ex), cross(tc, te), cross(ch, ex), cross(ch, te)
fig, ax = plt.subplots(figsize=(8, 4.5))
for y, l, c, s in [(tc, "Too cheap", "#9db4c0", "--"), (ch, "Cheap", "#2e86ab", "-"), (ex, "Expensive", "#f18f01", "-"), (te, "Too expensive", "#c73e1d", "--")]:
    ax.plot(grid, y, s, color=c, label=l, lw=2)
ax.axvspan(PMC, PME, color="#6a994e", alpha=.12, label=f"Acceptable range {PMC}–{PME} TL")
ax.axvline(OPP, color="#1f4e79", lw=1); ax.text(OPP + 4, .92, f"Optimal {OPP} TL", color="#1f4e79")
ax.set(xlabel="Annual subscription price (TL)", ylabel="Share of parents", title="Van Westendorp price sensitivity"); ax.legend(frameon=False, fontsize=8, loc="center right")
fig.tight_layout(); fig.savefig("fig_price_sensitivity.png", dpi=150)

# ---------- segmentation
X = df[["screen_worry", "edu_app_use"] + list(f)].values
Xs = StandardScaler().fit_transform(X)
km = KMeans(4, n_init=20, random_state=0).fit(Xs); df["segment"] = km.labels_
prof = df.groupby("segment").agg(size=("would_buy", "size"), buy_rate=("would_buy", "mean"), screen_worry=("screen_worry", "mean"),
    app_use=("edu_app_use", "mean"), curriculum=("f_curriculum_fit", "mean"), no_ads=("f_no_ads", "mean"),
    reports=("f_progress_report", "mean"), games=("f_games", "mean"), wtp_ok=("expensive", "median")).round(2)
# name each segment by its most distinctive (highest z-score) trait, unique per segment
z = (prof[["curriculum", "games", "screen_worry", "app_use", "reports"]] - prof[["curriculum", "games", "screen_worry", "app_use", "reports"]].mean()) / prof[["curriculum", "games", "screen_worry", "app_use", "reports"]].std()
LAB = {"curriculum": "Curriculum-driven planners", "games": "Fun-first parents", "screen_worry": "Screen-cautious parents",
       "app_use": "App-savvy early adopters", "reports": "Progress trackers"}
used, names = set(), {}
for seg in z.max(axis=1).sort_values(ascending=False).index:
    t = next(c for c in z.loc[seg].sort_values(ascending=False).index if c not in used); used.add(t); names[seg] = LAB[t]
prof["name"] = prof.index.map(names); prof["share"] = (prof["size"] / n).round(2)
prof = prof.sort_values("buy_rate", ascending=False)

# ---------- drivers
fx = df[list(f) + ["screen_worry", "edu_app_use"]]
lr = LogisticRegression(max_iter=1000).fit(StandardScaler().fit_transform(fx), df.would_buy)
drv = pd.Series(lr.coef_[0], index=fx.columns).sort_values()
fig, ax = plt.subplots(figsize=(7, 3.8))
ax.barh([c.replace("f_", "").replace("_", " ") for c in drv.index], drv.values, color=["#c73e1d" if v < 0 else "#2457a6" for v in drv.values])
ax.set_title("What drives purchase intent (standardised log-odds)", loc="left"); fig.tight_layout(); fig.savefig("fig_drivers.png", dpi=150)

# ---------- market sizing (assumptions are explicit and editable)
A = dict(children_5_7=3_600_000, parents_online_share=.85, target_income_share=.65, adoption_y1=.012, price=OPP)
TAM = A["children_5_7"] * A["parents_online_share"] * A["price"]
SAM = TAM * A["target_income_share"]; SOM = A["children_5_7"] * A["parents_online_share"] * A["target_income_share"] * A["adoption_y1"] * A["price"]

rep = f"""# Market Research Report: "Hece Hece" Reading App (illustrative)

**Question:** Will parents of 5–7-year-olds pay for a curriculum-aligned phonics app, at what price, and who should we target first?
**Method:** online survey, n = {n} parents (synthetic data for portfolio purposes); Van Westendorp price sensitivity meter; k-means segmentation on attitudes and feature ratings; logistic regression of purchase intent.

## Key findings
1. **Price:** acceptable range **{PMC}–{PME} TL/year**; optimal price point **{OPP} TL**, indifference point {IPP} TL. Recommend launching at **{int(round(OPP/10)*10 + 9)} TL/year** with a monthly option.
2. **{df.would_buy.mean():.0%}** of parents say they would buy, rising to **{prof.buy_rate.iloc[0]:.0%}** in the best segment.
3. **Strongest drivers** of intent: {', '.join(c.replace('f_','').replace('_',' ') for c in drv.sort_values(ascending=False).index[:3])}. Games rank {list(drv.sort_values(ascending=False).index).index('f_games')+1} of {len(drv)}: reassurance about the curriculum outweighs entertainment.

![](fig_price_sensitivity.png)

## Segments
{prof[['name','share','buy_rate','curriculum','no_ads','games','screen_worry','wtp_ok']].rename(columns={'wtp_ok':'median "expensive" price (TL)'}).to_markdown(index=False)}

**Target first:** *{prof.name.iloc[0]}*. Message: "aligned with the school curriculum, no ads, weekly progress report".

![](fig_drivers.png)

## Market size (year 1, editable assumptions)
| | Value | Assumption |
|---|---|---|
| TAM | {TAM/1e6:,.0f}M TL | {A['children_5_7']:,} children aged 5–7 × {A['parents_online_share']:.0%} online parents × {OPP} TL |
| SAM | {SAM/1e6:,.0f}M TL | × {A['target_income_share']:.0%} in target income band |
| SOM | {SOM/1e6:,.1f}M TL | × {A['adoption_y1']:.1%} year-1 adoption |

## Recommendations
- Lead with curriculum alignment and "no ads" in all messaging; test games as a secondary feature
- Annual plan near {OPP} TL plus a monthly plan; free trial of one sound group
- Launch in metropolitan areas through school-parent WhatsApp groups and teacher referrals

## Limitations
Synthetic illustrative data; stated intent overstates real purchase (apply a 30–50% haircut); child population figure must be refreshed from TÜİK before use.
"""
open("REPORT.md", "w", encoding="utf-8").write(rep); print(rep[:900])
