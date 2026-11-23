# AI bias testing: counterfactual audit of a screening model

**Service:** I test whether your AI system (a CV screener, a credit or risk score, or an LLM prompt that rates people) treats people differently because of name, sex or age, and report it in a format compliance teams and non-technical managers can read.

**Method:** identical CVs, one attribute changed at a time. A fair model gives the same score. I report the average score gap, a permutation-test p-value, and the shortlist **impact ratio** (the US "four-fifths rule": below 0.80 is a red flag).

**Demo result** (a stand-in model with a planted penalty, so the audit has something to find): [`REPORT.md`](REPORT.md)

| Attribute | Avg score gap | Impact ratio | Flag |
|---|---|---|---|
| Name group B vs A | −4.0 | 0.68 | FAIL |
| Man vs woman | 0.0 | 1.00 | ok |
| Age 52 vs 30 | −3.0 | 0.73 | FAIL |

A 4-point gap looks small, but at the shortlist cut-off it means 36% vs 24% of otherwise identical candidates get through.

```bash
python bias_test.py
pytest -q      # includes a fair model that must pass with zero gap
```

To audit a real system, replace `demo_model()` with a call to it. For LLM-based screening I also repeat each prompt several times, because answers vary between runs.
