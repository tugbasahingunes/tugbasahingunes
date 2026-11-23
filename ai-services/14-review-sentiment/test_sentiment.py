from sentiment import make_demo, tag_aspects, train


def test_aspect_tagging():
    assert tag_aspects("Arrived late, but great value") == ["price", "delivery"]
    assert tag_aspects("ordered the blue one") == []


def test_model_beats_majority_baseline():
    df = make_demo()
    _, te, rep = train(df)
    baseline = te.sentiment.value_counts(normalize=True).max()
    assert rep["accuracy"] > baseline + 0.3
