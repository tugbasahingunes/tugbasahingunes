# AI services: working samples

One folder per service. Every sample runs offline with `python <script>.py`, has automated tests (`pytest -q`), and clearly labels synthetic or fictional data. Samples that already exist elsewhere in this profile are linked instead of duplicated.

| # | Service | Sample | Key result |
|---|---|---|---|
| 1 | AI search visibility audit (GEO) | [flagship/09](../flagship/09-geo-visibility-benchmark) | Client brand found in 18% of AI answers vs 73% for the leader |
| 2 | GEO competitor benchmark | [flagship/09](../flagship/09-geo-visibility-benchmark) | 6-brand ranking across AI engines |
| 3 | GEO content rewrite | [03-geo-content-rewrite](03-geo-content-rewrite) | Page readiness 12 → 100 on 8 checks |
| 4 | Monthly AI visibility tracking | [04-geo-monthly-tracking](04-geo-monthly-tracking) | Mention rate 21% → 49% after rewrite (simulated) |
| 5 | LLM output evaluation with a rubric | [flagship/01](../flagship/01-turkish-llm-eval-dataset) | Rubric, scored dataset, rater agreement |
| 6 | Chatbot QA testing | [06-chatbot-qa-testing](06-chatbot-qa-testing) | 9/14 passed; paraphrases and policy gaps found |
| 7 | AI bias testing | [07-ai-bias-testing](07-ai-bias-testing) | Counterfactual audit; impact ratio 0.68 flagged |
| 8 | Red-team report | [08-red-team-report](08-red-team-report) | 2 critical, 1 high finding with fixes |
| 9 | Gold-standard evaluation set | [09-gold-set-creation](09-gold-set-creation) | κ = 0.73, 17 items adjudicated |
| 10 | Inter-rater agreement analysis | [flagship/01](../flagship/01-turkish-llm-eval-dataset) · [09-gold-set-creation](09-gold-set-creation) | Cohen's κ with confusion tables |
| 11 | Explainable ML with SHAP | [neet-europe-analysis/09](https://github.com/tugbasahingunes/neet-europe-analysis/tree/main/09_ml_neet_explainable) | AUC 0.73, SHAP drivers |
| 12 | Fairness audit of a prediction model | [neet-europe-analysis/09](https://github.com/tugbasahingunes/neet-europe-analysis/tree/main/09_ml_neet_explainable) | Catches 57% of at-risk young women vs 19% of young men |
| 13 | AI coding of open-ended answers | [13-open-ended-coding](13-open-ended-coding) | κ = 0.76 vs human codes; uncertain answers flagged |
| 14 | Review sentiment & aspects | [14-review-sentiment](14-review-sentiment) | 91% held-out accuracy; top complaint identified |
| 15 | Prompt library for teams | [15-prompt-library](15-prompt-library) | 6 linted prompts for 6 teams |
| 16 | Custom GPT / Claude Project setup | [16-custom-assistant-setup](16-custom-assistant-setup) | Acceptance test 7/9 → 9/9 after knowledge fix |
| 17 | AI automation (n8n) | [flagship/02](../flagship/02-ai-automation-lead-triage) | Lead triage workflow + tests |
| 18 | AI workflow audit | [18-ai-workflow-audit](18-ai-workflow-audit) | 17.4 hours/week saved, risk-aware plan |
| 19 | AI use policy | [19-ai-use-policy](19-ai-use-policy) | 10-section template + staff checklist |
| 20 | AI impact research brief | [neet-europe-analysis/05, 06, 08, 11](https://github.com/tugbasahingunes/neet-europe-analysis) | GenAI exposure by gender, education and country |

## Run everything

```bash
pip install pandas numpy scikit-learn matplotlib pyyaml tabulate pytest
for d in ai-services/*/; do (cd "$d" && ls test_*.py >/dev/null 2>&1 && pytest -q); done
```
