"""Build a gold-standard evaluation set from two annotators plus adjudication.

Steps: validate both annotation files against the label schema → measure
agreement (Cohen's kappa, per-label confusion) → items where annotators agree
become gold → disagreements go to an adjudicator → final gold set + report.

Demo data: 80 short customer messages, labelled by two simulated annotators
(about 85% accurate) and an adjudicator. The texts are synthetic.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score, confusion_matrix

LABELS = ["billing", "delivery", "returns", "technical", "other"]
TEMPLATES = {
    "billing": ["I was charged twice for my order", "Why is there an extra fee on my invoice?", "My card payment failed but money left my account", "Can I get a copy of my invoice?"],
    "delivery": ["Where is my parcel?", "The courier says delivered but I have nothing", "Can I change my delivery address?", "My package is late by a week"],
    "returns": ["How do I send this back?", "The item is broken, I want a refund", "Wrong size, can I exchange it?", "I returned it but no refund yet"],
    "technical": ["The app crashes when I log in", "I can't reset my password", "The checkout page won't load", "Promo code field gives an error"],
    "other": ["Do you have a store in Izmir?", "Are you hiring?", "Love your products!", "Can I suggest a new colour?"],
}


def make_demo(n: int = 80, seed: int = 3) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    true = rng.choice(LABELS, n)
    text = [rng.choice(TEMPLATES[t]) for t in true]
    def annot(acc):
        return [t if rng.random() < acc else rng.choice([l for l in LABELS if l != t]) for t in true]
    items = pd.DataFrame({"item_id": range(n), "text": text, "_true": true})
    a1 = pd.DataFrame({"item_id": range(n), "label": annot(.86)})
    a2 = pd.DataFrame({"item_id": range(n), "label": annot(.84)})
    return items, a1, a2


def validate(df: pd.DataFrame, n_items: int) -> list[str]:
    errs = []
    bad = ~df.label.isin(LABELS)
    if bad.any():
        errs.append(f"{bad.sum()} invalid labels: {sorted(df.label[bad].unique())}")
    if df.item_id.duplicated().any():
        errs.append("duplicate item_id")
    if set(df.item_id) != set(range(n_items)):
        errs.append("missing items")
    return errs


def build(items, a1, a2, adjudicate) -> tuple[pd.DataFrame, dict]:
    for name, d in (("annotator_1", a1), ("annotator_2", a2)):
        e = validate(d, len(items))
        if e:
            raise ValueError(f"{name}: {e}")
    m = items.merge(a1.rename(columns={"label": "a1"}), on="item_id").merge(
        a2.rename(columns={"label": "a2"}), on="item_id")
    m["agree"] = m.a1 == m.a2
    m["gold"] = np.where(m.agree, m.a1, None)
    m["source"] = np.where(m.agree, "agreement", "adjudicated")
    for i in m.index[~m.agree]:
        m.at[i, "gold"] = adjudicate(m.loc[i])
    stats = {"items": len(m), "raw_agreement": round(m.agree.mean(), 3),
             "kappa": round(cohen_kappa_score(m.a1, m.a2), 3),
             "adjudicated": int((~m.agree).sum()),
             "confusion": confusion_matrix(m.a1, m.a2, labels=LABELS).tolist()}
    return m, stats


def demo_adjudicator(row) -> str:  # expert reads the text; here: the true label
    return row["_true"]


if __name__ == "__main__":
    items, a1, a2 = make_demo()
    gold, s = build(items, a1, a2, demo_adjudicator)
    gold[["item_id", "text", "a1", "a2", "gold", "source"]].to_csv("gold_set.csv", index=False)
    acc = (gold.gold == gold._true).mean()
    cm = pd.DataFrame(s["confusion"], index=LABELS, columns=LABELS)
    md = ["# Gold set build report (demo)", "",
          f"- Items: **{s['items']}**", f"- Raw agreement: **{s['raw_agreement']:.0%}**",
          f"- Cohen's kappa: **{s['kappa']:.2f}**", f"- Sent to adjudication: **{s['adjudicated']}**",
          f"- Gold labels matching the simulated truth: **{acc:.0%}**", "",
          "Confusion between annotators (rows = annotator 1):", "", cm.to_markdown(), "",
          "*Synthetic texts and simulated annotators.*"]
    open("REPORT.md", "w").write("\n".join(md)); print("\n".join(md))
