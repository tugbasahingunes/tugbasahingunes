import pandas as pd
import pytest
from build_gold import build, demo_adjudicator, make_demo, validate


def test_validate_catches_bad_labels():
    d = pd.DataFrame({"item_id": [0, 1], "label": ["billing", "shipping"]})
    assert any("invalid" in e for e in validate(d, 2))


def test_build_rejects_invalid_file():
    items, a1, a2 = make_demo()
    a2.loc[0, "label"] = "typo"
    with pytest.raises(ValueError):
        build(items, a1, a2, demo_adjudicator)


def test_gold_complete_and_kappa_range():
    items, a1, a2 = make_demo()
    g, s = build(items, a1, a2, demo_adjudicator)
    assert g.gold.notna().all() and 0.6 < s["kappa"] < 0.9
    assert s["adjudicated"] == (~g.agree).sum()
