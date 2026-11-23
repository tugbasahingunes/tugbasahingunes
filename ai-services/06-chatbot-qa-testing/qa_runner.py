"""Chatbot QA test runner.

Test cases live in a CSV: question, category, must_include, must_not_include,
max_words. Each case is sent to the bot and checked automatically. The demo bot
is a small rule-based FAQ bot for a fictional online shop, with realistic
mistakes built in, so the report shows what a failed test looks like.
Swap `DemoBot.ask` for an API call to test a real chatbot.
"""
from __future__ import annotations
import csv
import re
from dataclasses import dataclass


class DemoBot:
    FAQ = {
        r"return|refund": "You can return items within 14 days. Refunds take 5-7 business days.",
        r"ship|deliver": "We ship within 2 business days. Delivery usually takes 3-5 days.",
        r"price|cost|discount": "Our prices are listed on each product page. Use code WELCOME10 for 10% off.",
        r"hours|open": "Our support team is available 9:00-18:00 on weekdays.",
        r"cancel": "Orders can be cancelled before they ship.",
    }

    def ask(self, q: str) -> str:
        for pat, ans in self.FAQ.items():
            if re.search(pat, q, re.I):
                return ans
        return "I'm sorry, I can only help with orders, shipping and returns."


@dataclass
class Case:
    id: str
    category: str
    question: str
    must_include: list[str]
    must_not_include: list[str]
    max_words: int


@dataclass
class Outcome:
    case: Case
    answer: str
    failures: list[str]

    @property
    def passed(self) -> bool:
        return not self.failures


def load_cases(path: str) -> list[Case]:
    out = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            split = lambda s: [x.strip() for x in s.split("|") if x.strip()]
            out.append(Case(r["id"], r["category"], r["question"], split(r["must_include"]),
                            split(r["must_not_include"]), int(r["max_words"] or 999)))
    return out


def check(case: Case, answer: str) -> Outcome:
    fails = []
    low = answer.lower()
    for s in case.must_include:
        if s.lower() not in low:
            fails.append(f"missing '{s}'")
    for s in case.must_not_include:
        if s.lower() in low:
            fails.append(f"should not contain '{s}'")
    if len(answer.split()) > case.max_words:
        fails.append(f"too long ({len(answer.split())} words)")
    return Outcome(case, answer, fails)


def run(cases: list[Case], bot) -> list[Outcome]:
    return [check(c, bot.ask(c.question)) for c in cases]


def report(outcomes: list[Outcome]) -> str:
    n = len(outcomes); p = sum(o.passed for o in outcomes)
    cats = sorted({o.case.category for o in outcomes})
    lines = ["# Chatbot QA report (demo bot)", "", f"**{p} of {n} tests passed ({p/n:.0%}).**", "",
             "| Category | Passed |", "|---|---|"]
    for c in cats:
        sub = [o for o in outcomes if o.case.category == c]
        lines.append(f"| {c} | {sum(o.passed for o in sub)}/{len(sub)} |")
    lines += ["", "## Failed tests", "", "| ID | Question | Bot answer | Problem |", "|---|---|---|---|"]
    for o in outcomes:
        if not o.passed:
            lines.append(f"| {o.case.id} | {o.case.question} | {o.answer} | {'; '.join(o.failures)} |")
    return "\n".join(lines)


if __name__ == "__main__":
    res = run(load_cases("test_cases.csv"), DemoBot())
    open("REPORT.md", "w").write(report(res))
    print(report(res))
