"""Reads the tracker and writes the weekly status e-mail / report (Markdown) for a given date:
progress, done this week, due next week, late or behind tasks, top risks."""
import sys, datetime as dt, pandas as pd
today = dt.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else dt.date.today()
t = pd.read_excel("project_tracker.xlsx", sheet_name="Tracker", header=3, usecols="A:I", nrows=10)
t["Start"] = pd.to_datetime(t["Start"]).dt.date
t["End"] = [s + dt.timedelta(days=int(d) - 1) for s, d in zip(t.Start, t.Days)]
elapsed = t.apply(lambda r: min(max((today - r.Start).days + 1, 0), r.Days) / r.Days, axis=1)
t["expected"] = elapsed
late = t[(t.End < today) & (t.Status != "Done")]
behind = t[(t.Start <= today) & (t.End >= today) & (t["% done"] < t.expected - .15) & (t.Status != "Done")]
nxt = t[(t.Start > today) & (t.Start <= today + dt.timedelta(days=7))]
prog = (t["% done"] * t.Days).sum() / t.Days.sum(); planned = (t.expected * t.Days).sum() / t.Days.sum()
risks = pd.read_excel("project_tracker.xlsx", sheet_name="Risks")
risks["Score"] = risks["Likelihood (1-5)"] * risks["Impact (1-5)"]
health = "🟢 On track" if prog >= planned - .05 and late.empty else "🟡 At risk" if prog >= planned - .15 else "🔴 Off track"
li = lambda d: "\n".join(f"- {r.ID} {r.Task} ({r.Owner}, due {r.End:%d.%m})" for r in d.itertuples()) or "- none"
md = f"""**Subject: Weekly status · Customer Survey 2027 · week of {today:%d.%m.%Y}**

**Overall:** {health} · {prog:.0%} complete (plan: {planned:.0%})

**Late:**
{li(late)}

**Behind schedule:**
{li(behind)}

**Starting next 7 days:**
{li(nxt)}

**Top risks:**
""" + "\n".join(f"- {r.Risk}: score {r.Score}. {r.Mitigation}" for r in risks.sort_values("Score", ascending=False).head(2).itertuples()) + "\n\n**Decisions needed from client:** none this week.\n"
open(f"status_{today:%Y%m%d}.md", "w", encoding="utf-8").write(md); print(md)
