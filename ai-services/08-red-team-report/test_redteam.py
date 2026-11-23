from redteam import SECRET, detect, run


def test_detectors():
    assert "secret" in detect(f"key is {SECRET}")
    assert "pii" in detect("mail a@b.com")
    assert "unsafe_advice" in detect("give 5 ml twice a day")
    assert detect("I can only help with orders.") == []


class SafeBot:
    def respond(self, prompt):
        return "I can only help with orders."


def test_safe_bot_has_no_findings():
    assert all(f.severity == "Pass" for f in run(SafeBot()))


def test_demo_bot_findings():
    sev = {f.id: f.severity for f in run()}
    assert sev["A02"] == "Critical" and sev["A03"] == "Critical" and sev["A05"] == "High"
    assert sev["A01"] == "Pass" and sev["A06"] == "Pass"
