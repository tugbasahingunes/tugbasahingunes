# Assistant acceptance test (demo)

Instructions: 480 characters (limit 8000).

## knowledge_v1: 7 of 9 checks passed

| Question | Expected | Best source | Similarity | Pass |
|---|---|---|---|---|
| How many days do I have to return something? | 14 days | returns_policy.md | 0.41 | ✓ |
| When will I get my refund? | 5-7 business days | products.md | 0.0 | ✗ |
| Can I get my money back for a sale item? | exchanged but not refunded | returns_policy.md | 0.26 | ✓ |
| How much is express delivery? | 89 TL | shipping.md | 0.49 | ✓ |
| Do you deliver to PO boxes? | do not ship to PO boxes | shipping.md | 0.64 | ✓ |
| What temperature should I wash cotton sheets at? | 40°C | products.md | 0.14 | ✗ |
| How heavy are your towels? | 550 gsm | products.md | 0.25 | ✓ |
| Do you have a physical store in Ankara? | (hand over) | products.md | 0.0 | ✓ |
| Can I pay in instalments? | (hand over) | products.md | 0.0 | ✓ |

## knowledge_v2: 9 of 9 checks passed

| Question | Expected | Best source | Similarity | Pass |
|---|---|---|---|---|
| How many days do I have to return something? | 14 days | faq.md | 0.77 | ✓ |
| When will I get my refund? | 5-7 business days | faq.md | 0.52 | ✓ |
| Can I get my money back for a sale item? | exchanged but not refunded | returns_policy.md | 0.27 | ✓ |
| How much is express delivery? | 89 TL | shipping.md | 0.48 | ✓ |
| Do you deliver to PO boxes? | do not ship to PO boxes | shipping.md | 0.64 | ✓ |
| What temperature should I wash cotton sheets at? | 40°C | faq.md | 0.87 | ✓ |
| How heavy are your towels? | 550 gsm | products.md | 0.25 | ✓ |
| Do you have a physical store in Ankara? | (hand over) | faq.md | 0.0 | ✓ |
| Can I pay in instalments? | (hand over) | faq.md | 0.0 | ✓ |