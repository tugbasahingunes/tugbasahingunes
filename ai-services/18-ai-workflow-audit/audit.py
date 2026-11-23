"""AI workflow audit: where can AI save a team time, safely?

Input: a task inventory from staff interviews (hours per week, plus 1-5 ratings).
AI potential = how repetitive, text-heavy and rule-based a task is.
Risk = data sensitivity and the cost of an error.
Each task lands in one of four recommendations:
  AI assist, quick human check (high potential, low risk)
  AI drafts, human approves (high potential, high risk)
  Simple tools first (low potential, low risk): templates, forms, Excel
  Keep manual (low potential with high risk, or very high risk)
Hours saved use conservative rates per recommendation.
"""
from __future__ import annotations
import pandas as pd

SAVING_RATE = {"AI assist, quick human check": .5, "AI drafts, human approves": .25,
               "Simple tools first": .15, "Keep manual": 0.0}


def score(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    d["ai_potential"] = d[["repetitive", "text_heavy", "rule_based"]].mean(axis=1)
    d["risk"] = d[["data_sensitivity", "error_cost"]].mean(axis=1)
    hi_pot, hi_risk = d.ai_potential >= 3.5, d.risk >= 3.5
    d["recommendation"] = "Keep manual"
    d.loc[hi_pot & ~hi_risk, "recommendation"] = "AI assist, quick human check"
    d.loc[hi_pot & hi_risk, "recommendation"] = "AI drafts, human approves"
    d.loc[~hi_pot & ~hi_risk, "recommendation"] = "Simple tools first"
    d.loc[d.risk >= 4.5, "recommendation"] = "Keep manual"  # e.g. payroll, sensitive case data
    d["hours_saved_week"] = (d.hours_per_week * d.recommendation.map(SAVING_RATE)).round(1)
    return d.sort_values("hours_saved_week", ascending=False)


if __name__ == "__main__":
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    d = score(pd.read_csv("tasks.csv")).reset_index(drop=True)
    d.insert(0, "no", range(1, len(d) + 1))
    d.to_csv("audit_results.csv", index=False)
    colors = {"AI assist, quick human check": "#2E8B57", "AI drafts, human approves": "#F2C14E",
              "Simple tools first": "#7A9CC6", "Keep manual": "#D9592B"}
    fig, ax = plt.subplots(figsize=(8, 5))
    for rec, g in d.groupby("recommendation"):
        ax.scatter(g.ai_potential, g.risk, s=g.hours_per_week * 60 + 120, color=colors[rec], alpha=.8, label=rec)
        for _, r in g.iterrows():
            ax.annotate(str(r.no), (r.ai_potential, r.risk), fontsize=8, ha="center", va="center", color="white", weight="bold")
    ax.axvline(3.5, color="grey", ls="--"); ax.axhline(3.5, color="grey", ls="--")
    ax.set_xlabel("AI potential (1-5)"); ax.set_ylabel("Risk (1-5)"); ax.set_xlim(1, 5.6); ax.set_ylim(1, 5.4)
    ax.set_title("Task map: numbers match the report table, bubble size = hours per week"); ax.legend(fontsize=8, frameon=False, loc="lower left")
    ax.spines[["top", "right"]].set_visible(False); fig.tight_layout(); fig.savefig("task_map.png", dpi=160)
    total = d.hours_saved_week.sum()
    md = ["# AI workflow audit (demo: fictional 15-person NGO)", "",
          f"Estimated time saved: **{total:.1f} hours per week** (about {total * 46 / 1720:.1f} of a full-time post over a year).", "",
          "| # | Task | Hours/week | Recommendation | Hours saved/week |", "|---|---|---|---|---|"]
    for _, r in d.iterrows():
        md.append(f"| {r.no} | {r.task} | {r.hours_per_week} | {r.recommendation} | {r.hours_saved_week} |")
    md += ["", "![map](task_map.png)", "", "*Illustrative task inventory; saving rates are conservative assumptions.*"]
    open("REPORT.md", "w").write("\n".join(md)); print("\n".join(md[:3]))
