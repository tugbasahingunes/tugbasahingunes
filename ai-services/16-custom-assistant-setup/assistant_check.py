"""Offline acceptance test for a custom GPT / Claude Project setup.

Before handing an assistant to a client, its knowledge files are checked to see
whether they actually contain the answers to the questions customers will ask.
A TF-IDF retriever finds the best passage for each test question; the expected
fact must appear in it. Out-of-scope questions must NOT match strongly
(so the assistant should fall back to the hand-over message).
Also checks the instructions fit the platform limit.
"""
from __future__ import annotations
import re
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

INSTRUCTION_LIMIT = 8000  # characters; custom GPT instructions limit
TESTS = [  # question, expected fact (None = should not be answerable)
    ("How many days do I have to return something?", "14 days"),
    ("When will I get my refund?", "5-7 business days"),
    ("Can I get my money back for a sale item?", "exchanged but not refunded"),
    ("How much is express delivery?", "89 TL"),
    ("Do you deliver to PO boxes?", "do not ship to PO boxes"),
    ("What temperature should I wash cotton sheets at?", "40°C"),
    ("How heavy are your towels?", "550 gsm"),
    ("Do you have a physical store in Ankara?", None),
    ("Can I pay in instalments?", None),
]


def passages(folder="knowledge_v2") -> list[tuple[str, str]]:
    out = []
    for f in sorted(Path(folder).glob("*.md")):
        for sent in re.split(r"(?<=[.!])\s+", f.read_text(encoding="utf-8")):
            if len(sent.split()) > 3:
                out.append((f.name, sent.strip()))
    return out


def check(folder: str = "knowledge_v2", threshold: float = 0.2) -> list[dict]:
    ps = passages(folder)
    vec = TfidfVectorizer(stop_words="english").fit([p[1] for p in ps] + [q for q, _ in TESTS])
    P = vec.transform([p[1] for p in ps])
    res = []
    for q, fact in TESTS:
        sims = cosine_similarity(vec.transform([q]), P)[0]
        i = sims.argmax()
        if fact is None:
            ok = sims[i] < threshold
        else:
            ok = sims[i] >= threshold and fact.lower() in ps[i][1].lower()
        res.append({"question": q, "expected": fact or "(hand over)", "best_source": ps[i][0],
                    "similarity": round(float(sims[i]), 2), "pass": bool(ok)})
    return res


if __name__ == "__main__":
    n = len(Path("instructions.md").read_text(encoding="utf-8"))
    print(f"Instructions: {n} / {INSTRUCTION_LIMIT} characters")
    lines = ["# Assistant acceptance test (demo)", "", f"Instructions: {n} characters (limit {INSTRUCTION_LIMIT})."]
    for folder in ("knowledge_v1", "knowledge_v2"):
        r = check(folder)
        lines += ["", f"## {folder}: {sum(x['pass'] for x in r)} of {len(r)} checks passed", "",
                  "| Question | Expected | Best source | Similarity | Pass |", "|---|---|---|---|---|"]
        for x in r:
            lines.append(f"| {x['question']} | {x['expected']} | {x['best_source']} | {x['similarity']} | {'✓' if x['pass'] else '✗'} |")
    open("REPORT.md", "w").write("\n".join(lines)); print("\n".join(lines))
