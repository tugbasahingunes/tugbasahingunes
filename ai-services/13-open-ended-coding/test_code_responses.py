from code_responses import make_demo, train_and_code


def test_codes_are_from_codebook_and_kappa_reasonable():
    df = make_demo()
    _, te, k = train_and_code(df)
    assert set(te.ai_code) <= set(df.human_code)
    assert 0.6 < k <= 1


def test_low_confidence_items_are_less_accurate():
    _, te, _ = train_and_code(make_demo())
    hi = te[~te.needs_review]; lo = te[te.needs_review]
    assert (hi.human_code == hi.ai_code).mean() > (lo.human_code == lo.ai_code).mean()
