import numpy as np
from bias_test import audit, make_cvs


def fair_model(df):
    return 30 + 2.5 * df.years_exp + 6 * df.degree + 35 * df.skills_match


def test_fair_model_passes():
    r = audit(make_cvs(), fair_model)
    assert (r.mean_score_gap == 0).all() and (r.impact_ratio == 1).all()


def test_demo_model_penalties_detected():
    r = audit(make_cvs()).set_index("attribute")
    assert r.loc["name_group", "mean_score_gap"] < -3.5
    assert r.loc["age", "mean_score_gap"] < -2.5
    assert r.loc["name_group", "impact_ratio"] < 0.8
    assert r.loc["sex", "impact_ratio"] == 1.0
