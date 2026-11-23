"""GEO content audit: score how 'quotable' a web page is for AI answer engines.

AI assistants tend to quote pages that answer the question directly, define the
entity clearly, give sourced numbers and use scannable structure. This script
scores a page (Markdown) on eight transparent checks and lists fixes.

Usage:  python geo_rewrite.py pages/before.md pages/after.md
"""
from __future__ import annotations
import re
import sys
from dataclasses import dataclass
from pathlib import Path

CHECKS = {
    "direct_answer": "First paragraph answers the main question in <= 60 words",
    "entity_definition": "Brand/product is defined with 'X is a ...' sentence",
    "sourced_numbers": "At least 2 numbers with a named source",
    "question_headings": "At least 2 headings phrased as questions",
    "faq_block": "Has an FAQ section",
    "lists": "Uses bullet or numbered lists",
    "short_paragraphs": "Average paragraph <= 80 words",
    "updated_date_or_author": "Shows author or expert attribution",
}


@dataclass
class Result:
    score: int
    passed: dict[str, bool]

    @property
    def fixes(self) -> list[str]:
        return [CHECKS[k] for k, ok in self.passed.items() if not ok]


def _paragraphs(text: str) -> list[str]:
    blocks = [b.strip() for b in re.split(r"\n\s*\n", text)]
    return [b for b in blocks if b and not b.startswith(("#", "-", "*", "1."))]


def audit(text: str, brand: str) -> Result:
    paras = _paragraphs(text)
    headings = re.findall(r"^#{1,4}\s+(.+)$", text, flags=re.M)
    first = paras[0] if paras else ""
    p = {
        "direct_answer": 0 < len(first.split()) <= 60,
        "entity_definition": bool(re.search(rf"\b{re.escape(brand)}\b is an? ", text)),
        "sourced_numbers": len(re.findall(r"\d[\d.,%]*[^.\n]{0,80}\((?:source|according to)[^)]+\)", text, flags=re.I)) >= 2,
        "question_headings": sum(h.strip().endswith("?") for h in headings) >= 2,
        "faq_block": any(re.search(r"\bFAQ\b|frequently asked", h, re.I) for h in headings),
        "lists": bool(re.search(r"^\s*(?:[-*]|\d+\.)\s+", text, flags=re.M)),
        "short_paragraphs": bool(paras) and sum(len(x.split()) for x in paras) / len(paras) <= 80,
        "updated_date_or_author": bool(re.search(r"(written|reviewed) by|author:", text, re.I)),
    }
    return Result(score=round(100 * sum(p.values()) / len(p)), passed=p)


def main(argv: list[str]) -> None:
    brand = "Mavi Kalem"
    for path in argv[1:]:
        r = audit(Path(path).read_text(encoding="utf-8"), brand)
        print(f"{path}: GEO readiness {r.score}/100")
        for f in r.fixes:
            print(f"   fix: {f}")


if __name__ == "__main__":
    main(sys.argv)
