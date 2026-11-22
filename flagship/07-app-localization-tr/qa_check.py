"""Localization QA for JSON/ICU resource files. Checks every key for:
missing/extra keys · placeholder mismatch · ICU plural structure · glossary terms · length budget
· Turkish-specific: suffix attached to a placeholder, plural noun after number, dotted/dotless I casing,
sen/siz consistency. Exit code 1 if errors (CI-friendly)."""
import csv, json, re, sys
SRC, TGT = (sys.argv[1:3] if len(sys.argv) > 2 else ("locales/en.json", "locales/tr.json"))
en, tr = json.load(open(SRC, encoding="utf-8")), json.load(open(TGT, encoding="utf-8"))
gl = list(csv.DictReader(open("glossary.csv", encoding="utf-8")))
E, W = [], []
ph = lambda s: sorted(set(re.findall(r"\{(\w+)(?=[,}])", s)))
for k in en.keys() - tr.keys(): E.append((k, "missing translation"))
for k in tr.keys() - en.keys(): E.append((k, "extra key not in source"))
for k in en.keys() & tr.keys():
    s, t = en[k], tr[k]
    if ph(s) != ph(t): E.append((k, f"placeholders differ: {ph(s)} vs {ph(t)}"))
    if "plural" in s and not re.search(r"plural,\s*one\s*\{.*\}\s*other\s*\{.*\}", t): E.append((k, "ICU plural structure broken"))
    if re.search(r"\}'\w|\}(?:'?(?:u|ü|ı|i|a|e|da|de|ta|te|dan|den))\b", t): E.append((k, "suffix attached to placeholder (vowel harmony unknown)"))
    if re.search(r"(\d|#|\})\s+\w+(lar|ler)\b", t): E.append((k, "plural suffix after a number (use singular)"))
    if re.search(r"\bInternet|\bIstanbul|\bIzmir", t): W.append((k, "check Turkish capital İ"))
    bare = lambda x: re.sub(r"\{\w+\}", "", x).lower()      # ignore placeholder names like {workout}
    for g in gl:
        if g["source"].lower() in bare(s) and g["target"].lower() not in bare(t): E.append((k, f"glossary: '{g['source']}' → '{g['target']}'"))
    budget = 1.2 if k.endswith((".cta", ".title")) else 1.6
    if len(t) > len(s) * budget + 4: W.append((k, f"length {len(t)} vs {len(s)} (budget ×{budget})"))
    if k.startswith("reminder.push") and len(t) > 90: E.append((k, "push notification over 90 chars"))
sen = sum(bool(re.search(r"\b(dene|başla|aç|et|sil)\b|\b\w+(ın|in|un|ün)\b", v)) for v in tr.values())
siz = sum(bool(re.search(r"\b\w+(iniz|ınız|unuz|ünüz|yin|yın|yun|yün)\b", v)) for v in tr.values())
if sen and siz: W.append(("*", f"mixed address forms: {sen} 'sen' vs {siz} 'siz' strings"))
print(f"{len(en)} keys · {len(E)} errors · {len(W)} warnings")
for k, m in E: print(f"  ERROR  {k}: {m}")
for k, m in W: print(f"  warn   {k}: {m}")
sys.exit(1 if E else 0)
