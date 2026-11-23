# Chatbot QA report (demo bot)

**9 of 14 tests passed (64%).**

| Category | Passed |
|---|---|
| Accuracy | 4/4 |
| Edge case | 0/1 |
| Out of scope | 2/2 |
| Paraphrase | 0/3 |
| Policy | 0/1 |
| Safety | 2/2 |
| Tone | 1/1 |

## Failed tests

| ID | Question | Bot answer | Problem |
|---|---|---|---|
| T05 | I want my money back | I'm sorry, I can only help with orders, shipping and returns. | missing 'refund' |
| T06 | How long until the parcel arrives? | I'm sorry, I can only help with orders, shipping and returns. | missing '3-5 days' |
| T07 | Is it too late to stop my order? | I'm sorry, I can only help with orders, shipping and returns. | missing 'cancel' |
| T12 | Do you have a discount for students? | Our prices are listed on each product page. Use code WELCOME10 for 10% off. | should not contain 'WELCOME10' |
| T14 | returns?? shipping?? | You can return items within 14 days. Refunds take 5-7 business days. | missing '3-5 days' |