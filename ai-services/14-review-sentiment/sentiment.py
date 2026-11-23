"""Sentiment and aspect analysis of customer reviews.

Classifier: TF-IDF + logistic regression trained on labelled reviews, evaluated
on a held-out set (precision/recall per class). Aspects (price, delivery,
quality, service) are tagged with a transparent keyword list, then crossed with
sentiment to show *what* customers are unhappy about.

Demo: 1,200 synthetic product reviews for a fictional home-goods shop.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline

ASPECTS = {"price": ["price", "expensive", "cheap", "value"], "delivery": ["delivery", "arrived", "shipping", "late"],
           "quality": ["quality", "broke", "sturdy", "material"], "service": ["support", "service", "staff", "refund"]}
PHRASES = {
    "positive": {"price": ["great value", "fair price"], "delivery": ["arrived quickly", "fast delivery"],
                 "quality": ["sturdy and well made", "excellent quality material"], "service": ["helpful support team", "friendly staff"]},
    "negative": {"price": ["too expensive", "not worth the price"], "delivery": ["arrived late", "shipping took forever"],
                 "quality": ["broke after a week", "cheap material, poor quality"], "service": ["support never replied", "refund was refused"]},
}
NEUTRAL = ["it is a lamp", "ordered the blue one", "bought it for the kitchen", "it is okay I guess",
           "delivery was normal, quality is average", "fine for the price"]


def make_demo(n=1200, seed=5):
    rng = np.random.default_rng(seed)
    rows = []
    for _ in range(n):
        s = rng.choice(["positive", "negative", "neutral"], p=[.5, .35, .15])
        if s == "neutral":
            txt = rng.choice(NEUTRAL)
        else:
            asp = rng.choice(list(ASPECTS), p=[.2, .35, .3, .15] if s == "negative" else [.25, .25, .35, .15])
            txt = rng.choice(PHRASES[s][asp])
            if rng.random() < .25:  # mixed review: opposite remark on another aspect
                other = "positive" if s == "negative" else "negative"
                a2 = rng.choice([a for a in ASPECTS if a != asp])
                txt = f"{txt}, but {rng.choice(PHRASES[other][a2])}"
        if rng.random() < .08:  # real labels are noisy: raters disagree on some reviews
            s = rng.choice([x for x in ["positive", "negative", "neutral"] if x != s])
        rows.append({"review": txt, "sentiment": s})
    return pd.DataFrame(rows)


def tag_aspects(text: str) -> list[str]:
    t = text.lower()
    return [a for a, kws in ASPECTS.items() if any(k in t for k in kws)]


def train(df, seed=0):
    tr, te = train_test_split(df, test_size=.3, stratify=df.sentiment, random_state=seed)
    m = make_pipeline(TfidfVectorizer(ngram_range=(1, 2)), LogisticRegression(max_iter=1000))
    m.fit(tr.review, tr.sentiment)
    te = te.assign(pred=m.predict(te.review))
    return m, te, classification_report(te.sentiment, te.pred, output_dict=True)


if __name__ == "__main__":
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    df = make_demo()
    m, te, rep = train(df)
    df["pred"] = m.predict(df.review)
    df["aspects"] = df.review.apply(tag_aspects)
    ex = df.explode("aspects").dropna(subset=["aspects"])
    neg = ex[ex.pred == "negative"].aspects.value_counts(normalize=True)
    fig, ax = plt.subplots(figsize=(7, 3)); neg.sort_values().plot.barh(ax=ax, color="#D9592B")
    ax.set_xlabel("Share of negative mentions"); ax.set_title("What negative reviews are about (synthetic)")
    ax.spines[["top", "right"]].set_visible(False); fig.tight_layout(); fig.savefig("negative_aspects.png", dpi=160)
    df.to_csv("scored_reviews.csv", index=False)
    md = ["# Review sentiment report (demo)", "",
          f"Held-out accuracy: **{rep['accuracy']:.0%}** (n = {len(te)}), macro F1 = **{rep['macro avg']['f1-score']:.2f}**", "",
          "| Class | Precision | Recall |", "|---|---|---|"]
    for c in ["positive", "negative", "neutral"]:
        md.append(f"| {c} | {rep[c]['precision']:.2f} | {rep[c]['recall']:.2f} |")
    md += ["", "Top complaint: **" + neg.idxmax() + f"** ({neg.max():.0%} of negative aspect mentions).", "",
           "![aspects](negative_aspects.png)", "", "*Synthetic reviews for a fictional shop.*"]
    open("REPORT.md", "w").write("\n".join(md)); print("\n".join(md))
