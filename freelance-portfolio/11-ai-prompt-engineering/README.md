# 11 · AI Prompt Engineering, Chatbot Setup & LLM Evaluation

**Client problem:** "We want a ChatGPT/Claude-based support bot, but we're afraid it will make things up or say something risky."

**This example**
- `system_prompt.md`: a production-style system prompt: scope, policy grounding, style, safety rules, handover signal
- `test_cases.jsonl`: 7 test cases covering normal questions, out-of-scope, a medical-risk message, a payment-security case and a **prompt-injection** attempt
- `evaluate.py`: automatic pass/fail scoring of any model's answers (`must_include` / `must_not`)

```bash
python evaluate.py sample_responses.jsonl   # 7/7 passed
```

Also offered: prompt libraries for teams, RLHF-style response rating and annotation (Turkish & English), custom GPTs, safety testing for vulnerable users. See my larger work: [When a child tells a chatbot](https://github.com/tugbasahingunes/vulnerable-user-ai-test) (547 tests) and [CaseNote AI](https://github.com/tugbasahingunes/casenote-ai).
