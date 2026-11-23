import pytest
from prompt_lib import lint, load, render


def test_library_is_clean():
    assert lint(load()) == {}


def test_lint_catches_problems():
    bad = [{"id": "x", "variables": ["a", "b"], "template": "ROLE: hi {a} {c}"}]
    errs = lint(bad)["x"]
    assert any("undeclared" in e for e in errs) and any("unused" in e for e in errs)
    assert any("FORMAT" in e for e in errs)


def test_render_requires_all_values():
    p = {p["id"]: p for p in load()}["meeting-summary"]
    assert "Decisions" in render(p, notes="We agreed X")
    with pytest.raises(KeyError):
        render(p)
