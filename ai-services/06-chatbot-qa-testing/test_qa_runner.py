from qa_runner import Case, DemoBot, check, load_cases, run


def test_check_flags_forbidden_and_length():
    c = Case("x", "c", "q", ["ok"], ["bad"], 3)
    o = check(c, "ok but bad answer here")
    assert not o.passed and len(o.failures) == 2


def test_demo_suite_finds_paraphrase_weakness():
    res = run(load_cases("test_cases.csv"), DemoBot())
    para = [o for o in res if o.case.category == "Paraphrase"]
    assert len(res) == 14 and not any(o.passed for o in para)
    assert all(o.passed for o in res if o.case.category == "Accuracy")
