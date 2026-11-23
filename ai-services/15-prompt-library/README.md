# Prompt library for teams

**Service:** I write a shared, tested library of prompts for your team's recurring tasks, so everyone gets consistent, safe results from ChatGPT, Claude or Copilot instead of improvising each time.

**Demo:** [`prompts.yaml`](prompts.yaml) holds 6 prompts for 6 teams:

| Prompt | Team | Built-in safeguard |
|---|---|---|
| email-reply-complaint | Support | Only promises what the pasted policy allows |
| meeting-summary | Operations | Never invents owners or dates ("TBC") |
| survey-question-review | Research | Flags leading and double-barrelled questions |
| job-ad-inclusive | HR | Keeps all requirements, removes coded wording |
| data-insight-explainer | Analytics | Uses only numbers in the table; no causal claims |
| product-description | E-commerce | No claims beyond the specs |

Every prompt follows the same structure (**ROLE / TASK / RULES / FORMAT**) and is checked automatically by [`prompt_lib.py`](prompt_lib.py): declared vs used variables, required sections, length limit and unique ids.

```bash
python prompt_lib.py     # lint the library
pytest -q
```

Client deliverable: the library (YAML, Notion or a shared doc), a one-page usage guide, and a short test log showing each prompt's output on 3 real examples from your team.
