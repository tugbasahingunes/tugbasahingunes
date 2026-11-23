import re
from pathlib import Path

TEXT = Path(__file__).with_name("POLICY.md").read_text(encoding="utf-8")
REQUIRED = ["Purpose", "Scope", "Approved tools", "Data rules", "Human responsibility",
            "Transparency", "Fairness", "Intellectual property", "Training and review", "Breaches"]


def test_all_sections_present_and_numbered():
    heads = re.findall(r"^## (\d+)\. (.+)$", TEXT, flags=re.M)
    assert [int(n) for n, _ in heads] == list(range(1, len(REQUIRED) + 1))
    for r in REQUIRED:
        assert any(r in h for _, h in heads), r


def test_red_category_and_checklist():
    assert "Red: never enter" in TEXT and TEXT.count("- [ ]") == 5
