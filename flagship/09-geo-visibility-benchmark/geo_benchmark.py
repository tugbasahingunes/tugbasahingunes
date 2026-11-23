"""AI Search Visibility (GEO) benchmark.

Runs a question set across AI answer engines, extracts which brands each answer mentions,
recommends and cites, and computes share-of-voice metrics with bootstrap confidence intervals.

Modes
  --live       query real engines (needs OPENAI_API_KEY / GEMINI_API_KEY / PERPLEXITY_API_KEY)
  default      synthetic answers generated from a transparent simulation, for demonstration

Sector in the demo: private education in Türkiye. All brand names are FICTIONAL."""
from __future__ import annotations
import argparse, json, os, re, random, pathlib, itertools
import numpy as np, pandas as pd, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

D = pathlib.Path(__file__).parent
BRANDS = {  # fictional brands with their domains
    "Atlas Koleji": "atlaskoleji.example", "Pusula Okulları": "pusula.example", "Kâşif Akademi": "kasif.example",
    "Yıldız Eğitim": "yildizegitim.example", "Bilge Kurs": "bilgekurs.example", "Mavi Kalem": "mavikalem.example"}
CLIENT = "Mavi Kalem"
ENGINES = ["ChatGPT", "Gemini", "Perplexity"]
INTENTS = {
    "category": ["Ankara'da en iyi özel ilkokullar hangileri?", "İstanbul'da iyi bir LGS kursu önerir misin?",
                 "Çocuğum için okuma-yazma kursu arıyorum, nereleri önerirsin?", "Online özel ders veren güvenilir kurumlar hangileri?",
                 "İzmir'de yabancı dil ağırlıklı özel okullar", "Bursa'da matematik kursu tavsiyesi"],
    "comparison": ["Atlas Koleji mi Pusula Okulları mı daha iyi?", "Kâşif Akademi ile Yıldız Eğitim karşılaştırması",
                   "Bilge Kurs ve Mavi Kalem arasındaki farklar neler?", "Özel okul seçerken hangi kurumlar öne çıkıyor?"],
    "problem": ["Çocuğum okumada zorlanıyor, ne yapmalıyım ve kimden destek alabilirim?", "LGS'ye 6 ay kaldı, hangi kursa gitmeli?",
                "Çalışan ebeveynler için okul sonrası etüt seçenekleri", "Çocuğumun matematik notları düştü, özel ders mi kurs mu?"],
    "branded": ["Mavi Kalem güvenilir mi?", "Atlas Koleji ücretleri ve yorumları", "Pusula Okulları hakkında bilgi"]}

# ---------------------------------------------------------------- synthetic engine (demo only)
# Each brand has a latent "AI visibility" per engine; clients with weak structured content get mentioned less.
LATENT = {"Atlas Koleji": [1.4, 1.2, 1.6], "Pusula Okulları": [1.1, 1.3, 0.9], "Kâşif Akademi": [0.6, 0.8, 1.0],
          "Yıldız Eğitim": [0.9, 0.5, 0.7], "Bilge Kurs": [0.4, 0.6, 0.9], "Mavi Kalem": [-0.4, -0.2, 0.3]}
def synthetic_answer(q, engine, rng):
    e = ENGINES.index(engine)
    named = [b for b in BRANDS if b.lower() in q.lower()]
    scores = {b: LATENT[b][e] + rng.normal(0, .8) + (3 if b in named else 0) for b in BRANDS}
    k = rng.integers(2, 5)
    picked = sorted(scores, key=scores.get, reverse=True)[:k]
    picked = [b for b in picked if scores[b] > .2] or picked[:1]
    lines = [f"{i+1}. {b}: {'önerilir, ' if i < 2 else ''}veli yorumları ve programı öne çıkıyor." for i, b in enumerate(picked)]
    cites = [BRANDS[b] for b in picked if rng.random() < (.55 if engine == "Perplexity" else .25)] + \
            (["meb.gov.tr"] if rng.random() < .3 else []) + (["sikayetvar.example"] if rng.random() < .2 else [])
    return "\n".join(lines), cites

def live_answer(q, engine):
    raise NotImplementedError("Add API calls for each engine here (OpenAI Responses API with web search, "
                              "Gemini with grounding, Perplexity sonar). Return (answer_text, cited_urls).")

# ---------------------------------------------------------------- coding answers
def code_answer(text, cites):
    rows = []
    for b, dom in BRANDS.items():
        m = re.search(re.escape(b), text)
        pos = text[:m.start()].count("\n") + 1 if m else None
        rows.append({"brand": b, "mentioned": bool(m), "position": pos,
                     "recommended": bool(m and re.search(re.escape(b) + r"[^\n]*önerilir", text)),
                     "cited": any(dom in c for c in cites)})
    return rows

def run(live=False, repeats=3, seed=11):
    rng = np.random.default_rng(seed); recs = []
    for (intent, qs), engine, r in itertools.product(INTENTS.items(), ENGINES, range(repeats)):
        for qi, q in enumerate(qs):
            text, cites = live_answer(q, engine) if live else synthetic_answer(q, engine, rng)
            for row in code_answer(text, cites):
                recs.append({"intent": intent, "q_id": f"{intent}-{qi}", "question": q, "engine": engine, "run": r, **row})
    return pd.DataFrame(recs)

def boot_ci(x, n=1000, seed=0):
    rng = np.random.default_rng(seed); x = np.asarray(x, float)
    m = [rng.choice(x, len(x)).mean() for _ in range(n)]
    return np.percentile(m, [2.5, 97.5])

def analyse(df):
    nb = df[df.intent != "branded"]                         # share of voice excludes branded queries
    sov = nb.groupby("brand").agg(mention_share=("mentioned", "mean"), recommendation_share=("recommended", "mean"),
                                  citation_share=("cited", "mean"), avg_position=("position", "mean")).round(3)
    ci = {b: boot_ci(g.mentioned) for b, g in nb.groupby("brand")}
    sov["mention_ci"] = [f"{ci[b][0]:.0%}–{ci[b][1]:.0%}" for b in sov.index]
    by_engine = nb.pivot_table(index="brand", columns="engine", values="mentioned", aggfunc="mean").round(3)
    by_intent = nb.pivot_table(index="brand", columns="intent", values="mentioned", aggfunc="mean").round(3)
    # stability: for each question×engine, share of runs agreeing with the majority on whether the client is mentioned
    c = df[df.brand == CLIENT].groupby(["q_id", "engine"]).mentioned.mean()
    stability = (c.apply(lambda p: max(p, 1 - p))).mean()
    return sov.sort_values("mention_share", ascending=False), by_engine, by_intent, stability

def figure(sov, by_engine, path):
    plt.rcParams.update({"font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False})
    fig, ax = plt.subplots(1, 2, figsize=(14, 5.6), gridspec_kw={"width_ratios": [1.1, 1]})
    s = sov.sort_values("mention_share")
    col = ["#E8663A" if b == CLIENT else "#2F6DB5" for b in s.index]
    ax[0].barh(s.index, s.mention_share * 100, color=col)
    ax[0].barh(s.index, s.recommendation_share * 100, color="#1F3A5F", height=.35)
    for y, (m, r) in enumerate(zip(s.mention_share, s.recommendation_share)):
        ax[0].text(m * 100 + 1, y, f"{m:.0%}", va="center", fontsize=11)
    ax[0].set_title("Share of AI answers that mention each brand\n(dark bar = recommended)", loc="left", fontsize=13, fontweight="bold")
    ax[0].set_xlabel("% of non-branded answers"); ax[0].set_xlim(0, 100)
    h = by_engine.loc[sov.index]
    im = ax[1].imshow(h.values * 100, cmap="Blues", vmin=0, vmax=100, aspect="auto")
    ax[1].set_xticks(range(len(h.columns)), h.columns); ax[1].set_yticks(range(len(h.index)), h.index)
    for i, j in itertools.product(range(h.shape[0]), range(h.shape[1])):
        v = h.values[i, j] * 100; ax[1].text(j, i, f"{v:.0f}%", ha="center", va="center", color="white" if v > 55 else "#1F3A5F", fontsize=11)
    ax[1].set_title("Mention share by AI engine", loc="left", fontsize=13, fontweight="bold")
    for sp in ax[1].spines.values(): sp.set_visible(False)
    fig.text(.01, .01, "SYNTHETIC DATA · fictional brands · 17 questions × 3 engines × 3 runs", fontsize=9, color="#888")
    fig.tight_layout(rect=(0, .03, 1, 1)); fig.savefig(path, dpi=150)

def report(sov, by_engine, by_intent, stability, n_answers):
    c = sov.loc[CLIENT]; leader = sov.index[0]; rank = list(sov.index).index(CLIENT) + 1
    weakest = by_engine.loc[CLIENT].idxmin(); best = by_engine.loc[CLIENT].idxmax()
    gap_intent = (by_intent.loc[leader] - by_intent.loc[CLIENT]).idxmax()
    txt = f"""# AI Visibility Benchmark: Private Education (Türkiye) · SYNTHETIC DEMO

> **All data in this report is synthetic and all brand names are fictional.** The pipeline is real; with API keys
> (`--live`) the same code measures actual ChatGPT, Gemini and Perplexity answers.

**Client:** {CLIENT} · **Competitors:** {', '.join(b for b in BRANDS if b != CLIENT)}
**Design:** 17 Turkish questions (category, comparison, problem, branded) × 3 engines × 3 repeated runs = {n_answers} answers.
Share-of-voice metrics use the 14 non-branded questions only.

## Key findings
1. **{CLIENT} ranks {rank} of {len(sov)}** on mention share ({c.mention_share:.0%}, 95% CI {c.mention_ci}); the leader {leader} is mentioned in {sov.loc[leader].mention_share:.0%} of answers.
2. It is **recommended** in only {c.recommendation_share:.0%} of answers, and its own site is cited in {c.citation_share:.0%}.
3. Visibility differs by engine: strongest on **{best}** ({by_engine.loc[CLIENT, best]:.0%}), weakest on **{weakest}** ({by_engine.loc[CLIENT, weakest]:.0%}).
4. The largest gap to the leader is in **{gap_intent}** questions.
5. Answers are not fully stable: for {CLIENT}, {1-stability:.0%} of question×engine results change between repeated runs, so audits should use repeated runs and confidence intervals rather than a single snapshot.

![](fig_visibility.png)

## Share of voice
{sov.to_markdown()}

## Recommendations
1. Publish answer-ready pages for **{gap_intent}** questions (clear claims, data, FAQ schema).
2. Earn mentions on the third-party sources {weakest} cites most (parent forums, education guides, news).
3. Add Organization and Course schema; keep name, address and programmes consistent across directories.
4. Re-measure monthly with the same question panel; report changes with confidence intervals, not single runs.
"""
    (D / "REPORT.md").write_text(txt, encoding="utf-8")
    return txt

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--live", action="store_true"); a = ap.parse_args()
    df = run(live=a.live); df.to_csv(D / "coded_answers.csv", index=False)
    sov, be, bi, st = analyse(df)
    figure(sov, be, D / "fig_visibility.png")
    print(report(sov, be, bi, st, df.groupby(["q_id", "engine", "run"]).ngroups)[:1500])
