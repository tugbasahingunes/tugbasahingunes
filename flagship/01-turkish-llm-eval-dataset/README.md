# Turkish LLM Evaluation & Preference Dataset

**Service:** AI training data · RLHF/DPO preference labelling · LLM evaluation in Turkish

A production-style sample of how I build and quality-control Turkish evaluation data for AI companies.

| File | What it shows |
|---|---|
| [`guidelines.md`](guidelines.md) | Full annotation guideline: 5 scoring criteria, preference rules, 10 error tags, Turkish-specific rules (TDK spelling, register, cultural accuracy), edge cases |
| [`data/items.jsonl`](data/items.jsonl) | 20 prompts × 2 responses across factual, reasoning, instruction-following, safety, grammar, tone, cultural and hallucination categories |
| [`data/annotated.jsonl`](data/annotated.jsonl) | Labels from two annotation passes, scores, error tags, adjudication notes |
| [`DATASET_CARD.md`](DATASET_CARD.md) | Agreement (Cohen's κ), category and error distributions, intended use, limitations |
| [`annotate_and_analyse.py`](annotate_and_analyse.py) | Reproducible QA pipeline |

**What the sample covers:** fluent-but-wrong answers (wrong date of the capital, 4+4+4 education), invented sources (a fake book summary), missed risk (child with high fever, low mood), unsafe compliance (Wi-Fi cracking), register errors (casual reply to a formal request), and Turkish-specific spelling (*herkes*, *de/da*).

**QA process:** two independent passes → agreement measured (κ) → disagreements adjudicated against the guideline with a written reason → dataset card.

```bash
pip install pandas scikit-learn tabulate
python annotate_and_analyse.py
```

Related: [When a child tells a chatbot](https://github.com/tugbasahingunes/vulnerable-user-ai-test) (547-test safety suite).
