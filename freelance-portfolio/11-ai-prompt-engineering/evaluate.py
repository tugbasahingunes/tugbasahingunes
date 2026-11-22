"""Rule-based evaluation of chatbot outputs against test cases.
Plug in any model: write its answers to a JSONL with {id, output} and run this script."""
import json, sys
def load(p): return {r["id"]:r for r in map(json.loads,open(p,encoding="utf-8"))}
tests=load("test_cases.jsonl"); outs=load(sys.argv[1] if len(sys.argv)>1 else "sample_responses.jsonl")
passed=0
for k,t in tests.items():
    o=outs.get(k,{}).get("output","").lower()
    miss=[w for w in t["must_include"] if w.lower() not in o]; bad=[w for w in t["must_not"] if w.lower() in o]
    ok=not miss and not bad; passed+=ok
    print(f"{'PASS' if ok else 'FAIL'}  {k:7s} {'' if ok else f'missing={miss} forbidden={bad}'}")
print(f"\n{passed}/{len(tests)} passed")
