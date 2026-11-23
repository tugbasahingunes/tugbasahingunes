# Chatbot QA testing

**Service:** I write a structured test suite for your chatbot (accuracy, paraphrases, out-of-scope questions, safety, policy and tone), run it, and give you a pass/fail report with the exact failing answers.

**Demo:** 14 test cases ([`test_cases.csv`](test_cases.csv)) run against a small FAQ bot for a fictional shop. Result: **9 of 14 passed (64%)**. Full output in [`REPORT.md`](REPORT.md).

| Finding | Why it matters |
|---|---|
| All 3 paraphrased questions failed ("I want my money back") | The bot only matches keywords; real customers rarely use them |
| It offered a public discount code to a student-discount question | Policy risk: answers a different question than asked |
| A two-topic question got only one answer | Customers asking several things get partial help |
| Prompt-injection and staff-code requests were handled safely | Safety basics are in place |

Note: the "tone" case passed only because the fallback message happens to say "sorry". Automatic checks catch a lot, but I always read the answers as well, and a human review column is part of the client report.

```bash
python qa_runner.py
pytest -q
```

To test a real bot, replace `DemoBot.ask()` with a call to its API.
