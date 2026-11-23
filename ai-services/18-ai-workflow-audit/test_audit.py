import pandas as pd
from audit import score


def row(**kw):
    base = dict(task="t", team="x", hours_per_week=10, repetitive=5, text_heavy=5, rule_based=5,
                data_sensitivity=1, error_cost=1)
    base.update(kw)
    return base


def test_quadrants():
    d = score(pd.DataFrame([
        row(task="easy"),
        row(task="risky", data_sensitivity=4, error_cost=3),
        row(task="very_risky", data_sensitivity=5, error_cost=5),
        row(task="low", repetitive=1, text_heavy=1, rule_based=2),
    ])).set_index("task")
    assert d.loc["easy", "recommendation"] == "AI assist, quick human check"
    assert d.loc["risky", "recommendation"] == "AI drafts, human approves"
    assert d.loc["very_risky", "recommendation"] == "Keep manual"
    assert d.loc["low", "recommendation"] == "Simple tools first"
    assert d.loc["easy", "hours_saved_week"] == 5.0


def test_demo_file_runs():
    d = score(pd.read_csv("tasks.csv"))
    assert (d[d.task == "Payroll"].recommendation == "Keep manual").all()
