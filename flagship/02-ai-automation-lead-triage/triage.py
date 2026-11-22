"""AI lead & message triage for a small business.

Incoming message (web form / e-mail / WhatsApp) → LLM classifies intent, urgency, language,
extracts fields as strict JSON → validated → routed (CRM row, auto-reply draft, Slack/e-mail alert).

Runs with Anthropic Claude if ANTHROPIC_API_KEY is set; otherwise a deterministic rule-based
fallback so the pipeline (and tests) work offline. Same output schema either way."""
from __future__ import annotations
import csv, json, os, re, sys, pathlib
from dataclasses import dataclass, asdict

SYSTEM = """You triage customer messages for a small Turkish e-commerce business.
Return ONLY a JSON object with keys:
intent: one of [order_status, return_refund, product_question, wholesale_b2b, complaint, spam, other]
urgency: one of [high, medium, low]   (high = angry customer, payment problem, or legal threat)
language: "tr" or "en"
customer_name: string or null
order_id: string or null   (format like #12345)
summary: one sentence in English
reply_draft: a polite reply in the customer's language, max 3 sentences, never promise refunds or dates
needs_human: true if complaint, wholesale_b2b, high urgency, or unclear"""

INTENTS = {"order_status","return_refund","product_question","wholesale_b2b","complaint","spam","other"}

@dataclass
class Triage:
    intent: str; urgency: str; language: str; customer_name: str|None; order_id: str|None
    summary: str; reply_draft: str; needs_human: bool

def validate(d: dict) -> Triage:
    if d.get("intent") not in INTENTS: d["intent"] = "other"
    if d.get("urgency") not in ("high","medium","low"): d["urgency"] = "medium"
    if d.get("language") not in ("tr","en"): d["language"] = "tr"
    d["needs_human"] = bool(d.get("needs_human")) or d["intent"] in ("complaint","wholesale_b2b") or d["urgency"] == "high"
    return Triage(**{k: d.get(k) for k in Triage.__annotations__})

def llm(message: str) -> dict:
    import anthropic
    c = anthropic.Anthropic()
    r = c.messages.create(model=os.getenv("MODEL","claude-sonnet-4-5"), max_tokens=500, system=SYSTEM,
                          messages=[{"role":"user","content":message}])
    txt = r.content[0].text
    return json.loads(txt[txt.find("{"): txt.rfind("}")+1])

RULES = [("spam", r"kazandınız|bitcoin|crypto|casino|click here"),
         ("wholesale_b2b", r"toptan|bayilik|wholesale|distributor|kurumsal"),
         ("return_refund", r"iade|geri ödeme|refund|return|değişim"),
         ("complaint", r"rezalet|şikayet|berbat|kabul edilemez|terrible|unacceptable|tüketici hakem"),
         ("order_status", r"kargo|sipariş(im)? (nerede|gelmedi)|where is my order|tracking|teslim"),
         ("product_question", r"stok|beden|renk|içerik|malzeme|size|colour|color|ingredient")]

REPLY = {"tr": {"order_status": "Merhaba{n}, siparişinizin durumunu kontrol ediyoruz ve en kısa sürede size bilgi vereceğiz.",
                "return_refund": "Merhaba{n}, iade talebinizi aldık. İade koşullarımızı ve sonraki adımları ekibimiz size iletecek.",
                "product_question": "Merhaba{n}, sorunuz için teşekkürler. Ürünle ilgili detayları kısa süre içinde paylaşacağız.",
                "wholesale_b2b": "Merhaba{n}, kurumsal talebiniz için teşekkür ederiz. Satış ekibimiz sizinle iletişime geçecek.",
                "complaint": "Merhaba{n}, yaşadığınız sorun için gerçekten üzgünüz. Talebiniz öncelikli olarak bir yetkiliye iletildi.",
                "other": "Merhaba{n}, mesajınız için teşekkürler. Size en kısa sürede dönüş yapacağız.", "spam": ""},
         "en": {"order_status": "Hi{n}, we're checking your order status and will update you shortly.",
                "return_refund": "Hi{n}, we've received your return request. Our team will send you the next steps.",
                "product_question": "Hi{n}, thanks for your question. We'll share the product details shortly.",
                "wholesale_b2b": "Hi{n}, thank you for your business enquiry. Our sales team will contact you.",
                "complaint": "Hi{n}, we're truly sorry about this. Your message has been escalated to a manager.",
                "other": "Hi{n}, thanks for reaching out. We'll get back to you soon.", "spam": ""}}

def rules(message: str) -> dict:
    low = message.lower()
    lang = "tr" if re.search(r"[çğıöşü]|merhaba|sipariş|teşekkür", low) else "en"
    intent = next((i for i, p in RULES if re.search(p, low)), "other")
    urgency = "high" if re.search(r"rezalet|avukat|lawyer|tüketici hakem|!!|kartımdan iki kez|charged twice", low) else \
              "low" if intent in ("spam","product_question") else "medium"
    oid = re.search(r"#?\b(\d{5,})\b", message)
    name = re.search(r"(?:ben|adım|my name is|I'm|I am)\s+([A-ZÇĞİÖŞÜ][a-zçğıöşü]+)", message)
    n = f" {name.group(1)}" if name else ""
    return {"intent": intent, "urgency": urgency, "language": lang, "customer_name": name.group(1) if name else None,
            "order_id": f"#{oid.group(1)}" if oid else None, "summary": f"{intent.replace('_',' ')} message ({lang})",
            "reply_draft": REPLY[lang][intent].format(n=n), "needs_human": False}

def triage(message: str) -> Triage:
    try:
        raw = llm(message) if os.getenv("ANTHROPIC_API_KEY") else rules(message)
    except Exception:
        raw = rules(message)            # never drop a message because the model failed
    return validate(raw)

def run(inbox: str, out_csv: str):
    rows = [json.loads(l) for l in open(inbox, encoding="utf-8")]
    res = []
    for r in rows:
        t = triage(r["message"])
        res.append({"received_at": r["received_at"], "channel": r["channel"], **asdict(t), "message": r["message"]})
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(res[0])); w.writeheader(); w.writerows(res)
    human = [x for x in res if x["needs_human"]]
    print(f"{len(res)} messages → {len(human)} escalated, {sum(x['intent']=='spam' for x in res)} spam filtered")
    for x in res: print(f"  [{x['urgency']:6}] {x['intent']:16} human={x['needs_human']!s:5}  {x['message'][:55]}")

if __name__ == "__main__":
    here = pathlib.Path(__file__).parent
    run(sys.argv[1] if len(sys.argv) > 1 else here/"sample_inbox.jsonl", here/"triaged.csv")
