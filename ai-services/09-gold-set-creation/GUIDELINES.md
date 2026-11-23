# Annotation guidelines: customer message intent

Assign **one** label per message: the main thing the customer needs.

| Label | Use when | Example |
|---|---|---|
| billing | Charges, invoices, payment failures | "I was charged twice" |
| delivery | Where a parcel is, delays, address changes | "Where is my parcel?" |
| returns | Sending back, refunds, exchanges, broken items | "Wrong size, can I exchange it?" |
| technical | App, website, login, error messages | "I can't reset my password" |
| other | Everything else: questions about the company, praise, suggestions | "Are you hiring?" |

**Edge rules**
1. Refund not received after a return → `returns` (not billing).
2. Promo code error → `technical` if the field fails, `billing` if the discount was not applied to the charge.
3. Two topics in one message → the one the customer asks to be solved first.
4. Unsure → pick the best label and add a note; do not skip items.
