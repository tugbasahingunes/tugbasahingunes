# Counterfactual bias audit (demo model)

Same 300 CVs, one attribute changed at a time. Shortlist = top 30% of scores.

| Attribute | Comparison | Avg score gap | p | Shortlist rate | Impact ratio | Flag |
|---|---|---|---|---|---|---|
| name_group | B vs A | -4.0 | 0.001 | 36% → 24% | 0.68 | FAIL (<0.8) |
| sex | man vs woman | +0.0 | 1.000 | 30% → 30% | 1.00 | ok |
| age | 52 vs 30 | -3.0 | 0.001 | 35% → 25% | 0.73 | FAIL (<0.8) |

*Demo model with a deliberately planted penalty; fictional CVs.*