"""Translation QA: paragraph count, numbers and glossary-term consistency between source and target."""
import csv, re
src=open("source_tr.md",encoding="utf-8").read(); tgt=open("target_en.md",encoding="utf-8").read()
issues=[]
p=lambda t:[x for x in t.split("\n\n") if x.strip()]
if len(p(src))!=len(p(tgt)): issues.append(f"paragraph count {len(p(src))} vs {len(p(tgt))}")
if re.findall(r"\d+",src)!=re.findall(r"\d+",tgt): issues.append("digits differ")
for row in csv.DictReader(open("glossary.csv",encoding="utf-8")):
    if row["tr"].lower() in src.lower() and row["en"].lower() not in tgt.lower():
        issues.append(f"glossary: '{row['tr']}' should be '{row['en']}'")
print("QA passed" if not issues else "\n".join(issues))
