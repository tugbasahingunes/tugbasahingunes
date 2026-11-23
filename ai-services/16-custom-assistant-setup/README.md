# Custom GPT / Claude Project setup, with an acceptance test

**Service:** I set up a custom assistant (ChatGPT custom GPT, Claude Project or similar) on your documents, with instructions that keep it on-topic, and I **test that it can actually find the answers** before your team or customers use it.

**Demo:** a support assistant for a fictional home-textile shop.

| File | Purpose |
|---|---|
| [`instructions.md`](instructions.md) | System instructions: answer only from files, exact numbers, safe hand-over message |
| `knowledge_v1/` | The client's original documents (policy, shipping, product care) |
| `knowledge_v2/` | Same documents + a short FAQ written in customers' own words |
| [`assistant_check.py`](assistant_check.py) | Offline acceptance test: 7 real questions + 2 out-of-scope questions |

**Result** ([`REPORT.md`](REPORT.md)):

| Knowledge version | Checks passed |
|---|---|
| v1: original documents | **7 / 9**: "When will I get my **refund**?" and "cotton **sheets**" didn't match the documents' wording ("Refunds are paid…", "bed linen") |
| v2: + customer-language FAQ | **9 / 9** |

This is the most common reason custom assistants give vague answers: the information is there, but written differently from how customers ask. The acceptance test finds those gaps before launch.

```bash
python assistant_check.py
pytest -q
```

Client deliverable: the configured assistant, instructions, cleaned knowledge files, test question set and report, plus a re-test after any document update.
