import pandas as pd
from tracker import make_demo_log, summarise, report


def test_rates_bounded_and_sov_sums_to_one():
    s = summarise(make_demo_log())
    assert s.mention_rate.between(0, 1).all()
    assert (s.groupby("month").share_of_voice.sum().round(6) == 1).all()


def test_known_small_log():
    log = pd.DataFrame({"month": ["2025-01"] * 2, "engine": ["A", "B"], "prompt_id": [0, 0],
                        "brands": ["Mavi Kalem;NotaBene", "NotaBene"]})
    s = summarise(log).set_index("brand")
    assert s.loc["NotaBene", "mention_rate"] == 1.0
    assert abs(s.loc["Mavi Kalem", "share_of_voice"] - 1 / 3) < 1e-9


def test_report_mentions_rank():
    assert "Rank this month" in report(summarise(make_demo_log()))
