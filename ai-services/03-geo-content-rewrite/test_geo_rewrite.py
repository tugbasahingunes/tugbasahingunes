from pathlib import Path
from geo_rewrite import audit

HERE = Path(__file__).parent


def test_rewrite_improves_score():
    before = audit((HERE / "pages/before.md").read_text(), "Mavi Kalem")
    after = audit((HERE / "pages/after.md").read_text(), "Mavi Kalem")
    assert before.score < 30 and after.score == 100


def test_detects_missing_faq():
    r = audit("# Title\n\nShort answer here.\n", "X")
    assert not r.passed["faq_block"] and "FAQ" in " ".join(r.fixes)


def test_sourced_numbers_need_source():
    text = "Sales grew 40% last year.\n\nUsers rose 12% too."
    assert not audit(text, "X").passed["sourced_numbers"]
    text2 = "Sales grew 40% (source: annual report).\n\nUsers rose 12% (source: app data)."
    assert audit(text2, "X").passed["sourced_numbers"]
