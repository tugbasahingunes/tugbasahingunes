"""Prompt library: load, lint and render team prompts.

Lint rules (each prompt must pass before it is shared with a team):
- every {placeholder} is declared in `variables`, and every variable is used
- the template has ROLE, TASK, RULES and FORMAT sections
- template under 1,200 characters
- unique ids
"""
from __future__ import annotations
import re
import sys
import yaml

SECTIONS = ["ROLE:", "TASK:", "RULES:", "FORMAT:"]


def load(path: str = "prompts.yaml") -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def lint(prompts: list[dict]) -> dict[str, list[str]]:
    problems: dict[str, list[str]] = {}
    seen = set()
    for p in prompts:
        errs = []
        used = set(re.findall(r"{(\w+)}", p["template"]))
        declared = set(p.get("variables", []))
        if used - declared:
            errs.append(f"undeclared variables: {sorted(used - declared)}")
        if declared - used:
            errs.append(f"unused variables: {sorted(declared - used)}")
        errs += [f"missing section {s}" for s in SECTIONS if s not in p["template"]]
        if len(p["template"]) > 1200:
            errs.append("template too long")
        if p["id"] in seen:
            errs.append("duplicate id")
        seen.add(p["id"])
        if errs:
            problems[p["id"]] = errs
    return problems


def render(prompt: dict, **values) -> str:
    missing = set(prompt["variables"]) - set(values)
    if missing:
        raise KeyError(f"missing values: {sorted(missing)}")
    return prompt["template"].format(**values)


if __name__ == "__main__":
    ps = load()
    probs = lint(ps)
    print(f"{len(ps)} prompts, {len(probs)} with problems")
    for k, v in probs.items():
        print(" ", k, v)
    sys.exit(1 if probs else 0)
