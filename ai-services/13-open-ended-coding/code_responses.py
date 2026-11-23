"""AI-assisted coding of open-ended survey answers.

Codebook → a small human-coded sample → a text classifier trained on it →
codes for the remaining answers, with agreement against held-out human codes
(Cohen's kappa) and a list of low-confidence answers for human review.

Demo: 400 synthetic answers to "What one thing would most improve your work?"
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import cohen_kappa_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline

CODEBOOK = {
    "workload": ["too much work", "understaffed", "constant overtime", "impossible deadlines", "more people on the team"],
    "pay": ["better salary", "pay rise", "bonus system", "pay that matches inflation", "fair wages"],
    "flexibility": ["remote work", "flexible hours", "work from home two days", "hybrid schedule", "shorter commute"],
    "management": ["clearer communication from managers", "less micromanagement", "feedback from my boss", "managers who listen", "transparent decisions"],
    "tools": ["a faster laptop", "better software", "systems that do not crash", "a working VPN", "modern equipment"],
    "training": ["more training", "career development", "learning budget", "mentoring", "courses for new skills"],
}
OPENERS = ["", "Honestly, ", "I think ", "Definitely ", "For me it would be ", "We need "]
FILLERS = ["", " please", " to be honest", " and maybe more breaks", " this year", " as soon as possible"]


def make_demo(n=400, seed=11):
    rng = np.random.default_rng(seed)
    codes = rng.choice(list(CODEBOOK), n, p=[.26, .22, .18, .15, .11, .08])
    text = []
    for c in codes:
        t = f"{rng.choice(OPENERS)}{rng.choice(CODEBOOK[c])}{rng.choice(FILLERS)}"
        if rng.random() < .3:  # mixed answers: a second theme is mentioned too
            other = rng.choice([k for k in CODEBOOK if k != c])
            t += f", also {rng.choice(CODEBOOK[other])}" if rng.random() < .5 else ""
            t = f"{rng.choice(CODEBOOK[other])} would help a bit, but mostly {t.lower()}" if rng.random() < .5 else t
        text.append(t)
    return pd.DataFrame({"id": range(n), "answer": text, "human_code": codes})


def train_and_code(df, n_train=120, seed=0, review_threshold=0.5):
    tr, te = train_test_split(df, train_size=n_train, stratify=df.human_code, random_state=seed)
    model = make_pipeline(TfidfVectorizer(ngram_range=(1, 2)), LogisticRegression(max_iter=1000, C=5))
    model.fit(tr.answer, tr.human_code)
    proba = model.predict_proba(te.answer)
    te = te.assign(ai_code=model.classes_[proba.argmax(1)], confidence=proba.max(1))
    te["needs_review"] = te.confidence < review_threshold
    kappa = cohen_kappa_score(te.human_code, te.ai_code)
    return model, te, kappa


if __name__ == "__main__":
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    df = make_demo()
    model, te, k = train_and_code(df)
    te.to_csv("coded_answers.csv", index=False)
    acc = (te.human_code == te.ai_code).mean()
    freq = te.ai_code.value_counts(normalize=True).sort_values()
    fig, ax = plt.subplots(figsize=(7, 3.2)); ax.barh(freq.index, freq * 100, color="#1C3352")
    for i, v in enumerate(freq): ax.text(v * 100 + .5, i, f"{v:.0%}", va="center")
    ax.set_xlabel("% of answers"); ax.set_title("What would most improve your work? (synthetic)")
    ax.spines[["top", "right"]].set_visible(False); fig.tight_layout(); fig.savefig("themes.png", dpi=160)
    md = ["# Open-ended coding report (demo)", "",
          f"- Human-coded training sample: **120** answers; AI-coded: **{len(te)}**",
          f"- Agreement with held-out human codes: **{acc:.0%}**, Cohen's κ = **{k:.2f}**",
          f"- Flagged for human review (confidence < 0.5): **{te.needs_review.sum()}**", "",
          "![themes](themes.png)", "", "*Synthetic answers.*"]
    open("REPORT.md", "w").write("\n".join(md)); print("\n".join(md))
