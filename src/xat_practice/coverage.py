"""The coverage ledger: what is trained, what is written, what is pending.

DERIVED, never maintained by hand. That is the whole design and it is not a
preference.

MEASURED 2026-10-02: `xat-practice weightage` printed `written: 4`, which is the
ITEM count, on a line whose neighbours were SUBTOPIC counts, on a project with 40
subtopics. It read as "four topics done" when the truth is **one**. A status
document anyone edits by hand would have carried that same lie for longer, and
nobody would have known.

So `render_coverage()` is a **pure function over `syllabus` and `registry`**, and
`docs/COVERAGE.md` is a committed snapshot of its output. A test compares the
fenced block in that document against this function, so the two cannot drift:
code moves, document does not, the suite fails.

**What this reports, and what it deliberately does not.**

- It reports **subtopics written** and **items written** as separate numbers,
  forever, because conflating them is the bug that started this.
- It attributes `q/yr` to the **TOPIC**, never to a subtopic. MEASURED: the weight
  model is per topic, from a coaching compilation, and **no per-subtopic
  frequency exists in any source.** Putting a topic's rate on a subtopic row would
  be inventing a number, which is worse than leaving the column out.
- It reports **trap count**, which is a real, checkable capacity: it is what
  bounds how many *different* wrong moves a subtopic can drill.

**The block-capacity rule, and where its numbers come from.** A 20-item block
needs, per item, four distractors carrying four distinct named misconceptions
(`G12`, within the item). `G12` requires **no** variety across items — measured
2026-10-02, and correcting a figure that had been repeated as a blocker without
reading the gate. So a block is limited by two things that are NOT gates:

- **trap variety.** `BLOCK_TRAPS_FULL` distinct traps gives one headline mistake
  per item with none repeated. This is a target, and it is stated as one.
- **derivation shapes.** `G17` as written demands all-distinct shapes, which a
  20-item set cannot satisfy on one subtopic. `BLOCK_SHAPES_RELAXED` is the count
  under a proposed relaxation (no shape more than twice). **That relaxation is NOT
  built and MUST NOT be assumed** — the ceiling here is a reading of what the
  relaxation would have to allow, not a claim about the current gate.
"""

from __future__ import annotations

from typing import TypedDict

from . import syllabus as S
from .registry import items_written, subtopics_written

#: A 20-item block wants one headline trap per item, none repeated.
BLOCK_TRAPS_FULL = 20

#: Under a proposed `G17` relaxation (no shape more than twice), this is how many
#: distinct derivation shapes a 20-item set would need. NOT CURRENTLY ENFORCED --
#: `G17` still demands all-distinct. See the module docstring.
BLOCK_SHAPES_RELAXED = 10

BEGIN = "<!-- BEGIN GENERATED: xat-practice coverage -->"
END = "<!-- END GENERATED: xat-practice coverage -->"


class SubtopicRow(TypedDict):
    """One line of the ledger, typed so the arithmetic on it is checked."""

    topic: str
    topic_name: str
    tier: str
    subtopic: str
    traps: int
    written: bool
    block_capacity: str


def _topic_rate(topic: S.Topic) -> float:
    """q/yr for a TOPIC, from the 7-year measured table."""
    return sum(topic.per_year) / len(topic.per_year)


def capacity(traps: int) -> str:
    """What `traps` named mistakes can support. A target, not a gate."""
    if traps >= BLOCK_TRAPS_FULL:
        return "full trap variety"
    if traps >= BLOCK_SHAPES_RELAXED:
        return "needs more traps"
    return "cannot carry a block"


def subtopic_rows() -> list[SubtopicRow]:
    """One row per trained subtopic, in tier then topic order."""
    written = subtopics_written()
    rows: list[SubtopicRow] = []
    # Ordered by tier, then by the TOPIC order the weight model uses, so the
    # reader sees the priority the syllabus already assigns.
    for topic in S.TOPICS:
        for st in [x for x in S.SUBTOPICS if x.topic_id == topic.id]:
            traps = len(st.traps)
            rows.append({
                "topic": topic.id,
                "topic_name": topic.name,
                "tier": st.tier.value,
                "subtopic": st.id,
                "traps": traps,
                "written": st.id in written,
                "block_capacity": capacity(traps),
            })
    return rows


def totals() -> dict[str, int]:
    """Every headline number this module prints, with its denominator."""
    trained = len(S.SUBTOPICS)
    written = len(subtopics_written())
    rows = subtopic_rows()
    return {
        "sections_in_part1": len(S.EXAMS["xat"].counted()),
        "questions_in_part1": S.EXAMS["xat"].counted_questions,
        "qa_di": S.SECTIONS["xat:qa_di"].questions,
        "topics": len(S.TOPICS),
        "subtopics_trained": trained,
        "subtopics_written": written,
        "subtopics_pending": trained - written,
        "items_written": items_written(),
        "traps": sum(len(x.traps) for x in S.SUBTOPICS),
        "can_carry_block": sum(
            1 for r in rows if r["traps"] >= BLOCK_SHAPES_RELAXED),
    }


def render_coverage() -> str:
    """The ledger. A pure function, so the committed document cannot drift."""
    t = totals()
    out: list[str] = []
    add = out.append

    add(f"subtopics written   {t['subtopics_written']:>3} of {t['subtopics_trained']}"
        f"   ({100 * t['subtopics_written'] / t['subtopics_trained']:.1f}%)")
    add(f"items written       {t['items_written']:>3}")
    add(f"topics              {t['topics']:>3}   named traps {t['traps']}")
    add(f"block capacity      {t['can_carry_block']:>3} of {t['subtopics_trained']}"
        f" subtopics have >= {BLOCK_SHAPES_RELAXED} named traps")
    add("")
    add("tier  traps  block capacity      status   subtopic")
    for tier in (S.Tier.P1, S.Tier.P2, S.Tier.P3):
        add(f"-- {tier} " + "-" * 58)
        for st in [x for x in S.SUBTOPICS if x.tier is tier]:
            n = len(st.traps)
            shown = {"full trap variety": "full variety",
                     "needs more traps": "more traps ",
                     "cannot carry a block": "NO BLOCK    "}[capacity(n)]
            status = "WRITTEN " if st.id in subtopics_written() else "pending "
            add(f"{tier.value[:4]:<5} {n:>4}   {shown:<16}  {status}  {st.id}")
    return "\n".join(out)


def block_markers(block: str) -> str:
    """The document block the staleness test compares."""
    return f"{BEGIN}\n\n```\n{block}\n```\n\n{END}"
