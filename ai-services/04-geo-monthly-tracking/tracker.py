"""Monthly AI-visibility tracker.

Input: a log of AI answers (one row per prompt x engine x month) with the brands
mentioned. Output: mention rate, share of voice and month-on-month change per
brand, a trend chart and a Markdown report.

`make_demo_log()` builds a synthetic log for fictional brands so the pipeline
can be tested without API keys. In a client project the log comes from
scheduled queries to each AI engine.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

BRANDS = ["Mavi Kalem", "Kagit Evi", "NotaBene", "Defterim"]
ENGINES = ["ChatGPT", "Gemini", "Perplexity"]
MONTHS = pd.period_range("2025-01", periods=6, freq="M").astype(str).tolist()


def make_demo_log(n_prompts: int = 30, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    base = {"Mavi Kalem": .18, "Kagit Evi": .70, "NotaBene": .45, "Defterim": .30}
    rows = []
    for m_i, month in enumerate(MONTHS):
        for e in ENGINES:
            for p in range(n_prompts):
                probs = dict(base)
                if m_i >= 3:  # client's GEO rewrite goes live in month 4
                    probs["Mavi Kalem"] = .18 + .12 * (m_i - 2)
                mentioned = [b for b, pr in probs.items() if rng.random() < pr]
                rows.append({"month": month, "engine": e, "prompt_id": p,
                             "brands": ";".join(mentioned)})
    return pd.DataFrame(rows)


def summarise(log: pd.DataFrame) -> pd.DataFrame:
    out = []
    for (month), g in log.groupby("month"):
        lists = g["brands"].fillna("").str.split(";")
        total_mentions = sum(len([b for b in l if b]) for l in lists)
        for b in BRANDS:
            hits = lists.apply(lambda l: b in l).sum()
            out.append({"month": month, "brand": b,
                        "mention_rate": hits / len(g),
                        "share_of_voice": hits / total_mentions if total_mentions else 0})
    df = pd.DataFrame(out)
    df["mom_change_pts"] = df.groupby("brand")["mention_rate"].diff() * 100
    return df


def report(df: pd.DataFrame, client: str = "Mavi Kalem") -> str:
    c = df[df.brand == client].reset_index(drop=True)
    first, last = c.iloc[0], c.iloc[-1]
    latest = df[df.month == df.month.max()].sort_values("mention_rate", ascending=False)
    rank = latest.brand.tolist().index(client) + 1
    lines = [f"# AI visibility report: {client}", "",
             f"Mention rate: **{first.mention_rate:.0%} → {last.mention_rate:.0%}** "
             f"({MONTHS[0]} to {MONTHS[-1]}). Rank this month: **{rank} of {len(BRANDS)}**.", "",
             "| Brand | Mention rate | Share of voice | Change vs last month |",
             "|---|---|---|---|"]
    for _, r in latest.iterrows():
        lines.append(f"| {r.brand} | {r.mention_rate:.0%} | {r.share_of_voice:.0%} | {r.mom_change_pts:+.1f} pts |")
    lines += ["", "*Synthetic demonstration data for fictional brands.*"]
    return "\n".join(lines)


def chart(df: pd.DataFrame, path: str) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(8, 4.2))
    for b in BRANDS:
        s = df[df.brand == b]
        ax.plot(s.month, s.mention_rate * 100, marker="o",
                lw=3 if b == "Mavi Kalem" else 1.5,
                color="#D9592B" if b == "Mavi Kalem" else None, label=b)
    ax.axvline(2.5, ls="--", color="grey"); ax.text(2.55, 5, "GEO rewrite live", color="grey")
    ax.set_ylabel("% of AI answers mentioning brand"); ax.set_ylim(0, 100)
    ax.set_title("Monthly AI visibility (synthetic demo)")
    ax.spines[["top", "right"]].set_visible(False); ax.legend(frameon=False, ncol=4, loc="upper center")
    fig.tight_layout(); fig.savefig(path, dpi=160)


if __name__ == "__main__":
    log = make_demo_log()
    log.to_csv("demo_log.csv", index=False)
    s = summarise(log)
    s.to_csv("monthly_summary.csv", index=False)
    open("REPORT.md", "w").write(report(s))
    chart(s, "trend.png")
    print(report(s))
