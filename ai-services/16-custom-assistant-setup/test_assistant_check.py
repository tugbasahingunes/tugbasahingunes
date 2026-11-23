from pathlib import Path
from assistant_check import INSTRUCTION_LIMIT, check


def test_v1_has_gaps_v2_passes():
    assert sum(r["pass"] for r in check("knowledge_v1")) < 9
    assert all(r["pass"] for r in check("knowledge_v2"))


def test_out_of_scope_questions_hand_over():
    r = [x for x in check("knowledge_v2") if x["expected"] == "(hand over)"]
    assert r and all(x["similarity"] < 0.2 for x in r)


def test_instructions_within_limit():
    assert len(Path("instructions.md").read_text()) < INSTRUCTION_LIMIT
