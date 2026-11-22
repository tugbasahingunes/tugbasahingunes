import os; os.environ.pop("ANTHROPIC_API_KEY", None)
from triage import triage, validate
def test_order():   t = triage("Merhaba, ben Ayşe. #48213 numaralı siparişim gelmedi, kargo nerede?"); assert (t.intent, t.order_id, t.customer_name, t.language) == ("order_status", "#48213", "Ayşe", "tr")
def test_escalate(): t = triage("REZALET!! Kartımdan iki kez çekim yapıldı"); assert t.urgency == "high" and t.needs_human
def test_b2b():     assert triage("We are a distributor, wholesale prices please").needs_human
def test_spam():    t = triage("You have won, click here for bitcoin"); assert t.intent == "spam" and t.reply_draft == ""
def test_english(): assert triage("Where is my order 77120? tracking").language == "en"
def test_schema_guard():
    t = validate({"intent": "hack_the_planet", "urgency": "???", "language": "de", "customer_name": None, "order_id": None, "summary": "", "reply_draft": "", "needs_human": False})
    assert (t.intent, t.urgency, t.language) == ("other", "medium", "tr")
