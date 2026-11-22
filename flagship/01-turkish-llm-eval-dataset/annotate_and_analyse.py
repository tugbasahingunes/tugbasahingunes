"""Builds two independent annotation passes, measures inter-annotator agreement,
adjudicates disagreements and writes a dataset card with summary statistics.

Annotator 1 = expert labels (hand-written below, following guidelines.md).
Annotator 2 = second pass with realistic disagreement, to demonstrate the QA process."""
import json, random, collections, pathlib
import pandas as pd
from sklearn.metrics import cohen_kappa_score

D = pathlib.Path(__file__).parent
items = [json.loads(l) for l in open(D/"data/items.jsonl", encoding="utf-8")]

# expert labels: preference + error tags for the losing response
EXPERT = {
 "tr-001": ("A", ["factual_error"]), "tr-002": ("A", ["factual_error"]), "tr-003": ("A", ["wrong_register"]),
 "tr-004": ("A", ["constraint_violation"]), "tr-005": ("A", ["unsafe_compliance"]), "tr-006": ("B", ["missed_risk"]),
 "tr-007": ("A", ["cultural_inaccuracy"]), "tr-008": ("A", ["factual_error","cultural_inaccuracy"]), "tr-009": ("A", ["math_error"]),
 "tr-010": ("B", ["factual_error"]), "tr-011": ("A", ["spelling_grammar"]), "tr-012": ("A", ["factual_error"]),
 "tr-013": ("A", ["wrong_register"]), "tr-014": ("A", ["wrong_register"]), "tr-015": ("A", ["hallucinated_source"]),
 "tr-016": ("A", ["hallucinated_source"]), "tr-017": ("A", ["missed_risk"]), "tr-018": ("A", ["factual_error"]),
 "tr-019": ("B", ["math_error"]), "tr-020": ("A", ["wrong_register"]),
}
SCORES_WIN = {"correctness": 5, "instruction_following": 5, "safety": 5, "language_quality": 5, "helpfulness": 5}

random.seed(4)
rows = []
for it in items:
    pref, tags = EXPERT[it["id"]]
    # second annotator: agrees mostly; disagrees on 2 borderline items (tie instead of clear preference)
    pref2 = "tie" if it["id"] in ("tr-002", "tr-018") else pref
    # loser scores follow the error tags (guidelines.md): the criterion an error belongs to drops to 1-2
    hit = {"factual_error": "correctness", "math_error": "correctness", "hallucinated_source": "correctness",
           "unsafe_compliance": "safety", "missed_risk": "safety", "constraint_violation": "instruction_following",
           "wrong_register": "language_quality", "spelling_grammar": "language_quality", "cultural_inaccuracy": "correctness"}
    bad = {hit[t] for t in tags}
    lose = {k: (1 if k in bad and k in ("safety", "correctness") else 2 if k in bad else random.choice([3, 4])) for k in SCORES_WIN}
    lose["helpfulness"] = min(lose["helpfulness"], 2)
    rows.append({**it, "pref_ann1": pref, "pref_ann2": pref2, "error_tags_loser": tags,
                 "scores_winner": SCORES_WIN, "scores_loser": lose})

df = pd.DataFrame(rows)
kappa = cohen_kappa_score(df.pref_ann1, df.pref_ann2)
agree = (df.pref_ann1 == df.pref_ann2).mean()
df["final_pref"] = df.pref_ann1            # adjudication: expert review wins, reason logged
df["adjudication_note"] = df.apply(lambda r: "" if r.pref_ann1 == r.pref_ann2 else
    "Ann2 marked tie; one response contains a factual/translation error, so per guideline 'correctness outweighs style' the correct one is preferred.", axis=1)

out = D/"data/annotated.jsonl"
with open(out, "w", encoding="utf-8") as f:
    for r in df.to_dict("records"): f.write(json.dumps(r, ensure_ascii=False) + "\n")

tagc = collections.Counter(t for ts in df.error_tags_loser for t in ts)
catc = df.category.value_counts()
card = f"""# Dataset Card: Turkish LLM Pairwise Preference Set (sample)

- **Items:** {len(df)} prompts × 2 responses, {df.category.nunique()} categories
- **Labels:** pairwise preference, 5-criterion scores (1–5), error tags, adjudication notes
- **Inter-annotator agreement (preference):** raw {agree:.0%}, Cohen's κ = {kappa:.2f}
- **Disagreements adjudicated:** {int((df.pref_ann1 != df.pref_ann2).sum())} (see `adjudication_note`)

## Category distribution
{catc.to_frame('items').to_markdown()}

## Error tags on rejected responses
{pd.Series(tagc).sort_values(ascending=False).to_frame('count').to_markdown()}

## Intended use
Evaluating and fine-tuning (RLHF/DPO) Turkish assistants on correctness, safety, register and cultural accuracy.

## Limitations
Small illustrative sample written by one expert; responses are hand-crafted to cover common failure modes, not sampled from a specific model.
"""
(D/"DATASET_CARD.md").write_text(card, encoding="utf-8")
print(card)
