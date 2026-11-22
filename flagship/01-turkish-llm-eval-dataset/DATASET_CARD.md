# Dataset Card: Turkish LLM Pairwise Preference Set (sample)

- **Items:** 20 prompts × 2 responses, 8 categories
- **Labels:** pairwise preference, 5-criterion scores (1–5), error tags, adjudication notes
- **Inter-annotator agreement (preference):** raw 90%, Cohen's κ = 0.71
- **Disagreements adjudicated:** 2 (see `adjudication_note`)

## Category distribution
| category      |   items |
|:--------------|--------:|
| instruction   |       3 |
| safety        |       3 |
| cultural      |       3 |
| reasoning     |       3 |
| factual       |       2 |
| grammar       |       2 |
| tone          |       2 |
| hallucination |       2 |

## Error tags on rejected responses
|                      |   count |
|:---------------------|--------:|
| factual_error        |       6 |
| wrong_register       |       4 |
| missed_risk          |       2 |
| math_error           |       2 |
| cultural_inaccuracy  |       2 |
| hallucinated_source  |       2 |
| constraint_violation |       1 |
| unsafe_compliance    |       1 |
| spelling_grammar     |       1 |

## Intended use
Evaluating and fine-tuning (RLHF/DPO) Turkish assistants on correctness, safety, register and cultural accuracy.

## Limitations
Small illustrative sample written by one expert; responses are hand-crafted to cover common failure modes, not sampled from a specific model.
