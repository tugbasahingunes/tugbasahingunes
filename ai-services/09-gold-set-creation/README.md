# Gold-standard evaluation set creation

**Service:** I build the "answer key" you need to evaluate an AI model or train a classifier: clear labelling guidelines, two independent annotators, agreement measurement, expert adjudication of disagreements, and a clean, validated gold file.

**Demo:** 80 customer-support messages, 5 intent labels ([`GUIDELINES.md`](GUIDELINES.md)).

| Step | Result |
|---|---|
| Schema validation of both annotation files | invalid labels, duplicates and missing items are rejected |
| Agreement | 79% raw, **Cohen's κ = 0.73** (substantial) |
| Adjudication | 17 disagreements resolved by an expert |
| Quality | 99% of gold labels match the simulated truth. The 1 miss is an item where *both* annotators made the same error, which is why spot-checks of agreed items are part of the process |

The confusion table in [`REPORT.md`](REPORT.md) shows *where* annotators disagree ("other" vs "technical"), which is used to sharpen the guidelines before the next batch.

```bash
python build_gold.py     # writes gold_set.csv and REPORT.md
pytest -q
```

Related: [Turkish LLM evaluation dataset](../../flagship/01-turkish-llm-eval-dataset) (κ = 0.71 on a real annotation round).
