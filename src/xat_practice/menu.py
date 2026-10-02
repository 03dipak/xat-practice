"""The one command a learner types.

`xat-practice serve` with no arguments asks what you want to work on and serves
it. The learner never assembles a path, never learns what a `lesson_id` is, and
never runs a second command.

WHY A MENU AND NOT A FLAG
-------------------------
MEASURED 2026-10-02: the second command was the thing people got wrong. `serve`
defaults to the FIRST registered lesson, so `serve` alone silently opened Simple
Interest, and reaching Geometry meant knowing `lesson-02-geometry-similarity`.
The default was chosen to be safe, and it was safe by being invisible: a learner
who wanted Geometry and typed the documented command got Simple Interest and no
indication that a choice existed.

A default that hides the choice is worse than a prompt.

THE LEVEL IS THE LEARNER'S CHOICE, NOT THE QUOTA'S
-------------------------------------------------
There are two different things called "a mix", and conflating them is the trap:

* `LEVEL_MIX` (10/25/40/25) is derived from the exam's own timing and is correct
  for a MOCK, which must reproduce the paper's shape. At 20 items it yields
  2/5/8/5.
* A DRILL is level-filtered. A learner who says "give me foundation" gets
  foundation. Quotas do not apply, and `G11` must not be run on it -- a paper rule
  handed a non-paper is the defect behind D12 and D23.

So this menu offers the level the learner asked for, and the mix is applied only
where a paper is being simulated. See `docs/DECISIONS.md` D23/D24.

HONESTY IS THE DEFAULT
----------------------
Every subtopic in the syllabus is listed, and the 38 that have no lesson are
marked `not written` rather than hidden. Hiding them would make the menu look
finished; showing them is the ledger, which is the honest position: **2 of 40**
subtopics are written and this menu says so.
"""

from __future__ import annotations

from dataclasses import dataclass

from .registry import LESSONS
from .syllabus import PAPER_SHAPE, TOPICS, Subtopic

#: Which Part-1 section each topic belongs to. The syllabus trains QA&DI only
#: (D7), so this is the whole truth about the other two sections rather than a
#: guess about them.
SECTION_QA_DI = "QA&DI"


@dataclass(frozen=True, slots=True)
class Entry:
    """One selectable line: a written lesson."""

    lesson_id: str
    topic_id: str
    subtopic_id: str
    label: str
    subtopic_label: str


def written_entries() -> list[Entry]:
    """The lessons that exist, in topic-weight order (heaviest first).

    Sorted by measured topic weight so the learner meets the biggest block
    first -- DI at 6.71 q/yr down to Time & Work at 0.29 -- rather than
    alphabetically, which would put Averages before Data Interpretation for no
    reason a learner could infer.
    """
    subs: dict[str, Subtopic] = {s.id: s for s in _all_subtopics()}
    order = {t.id: -t.weight for t in TOPICS}
    out: list[Entry] = []
    for lesson in LESSONS:
        sub = subs.get(lesson.subtopic_id)
        out.append(Entry(
            lesson_id=lesson.lesson_id,
            topic_id=lesson.subtopic_id.split(":", 1)[0],
            subtopic_id=lesson.subtopic_id,
            label=_topic_name(lesson.subtopic_id.split(":", 1)[0]),
            subtopic_label=sub.name if sub else lesson.subtopic_id,
        ))
    return sorted(out, key=lambda e: (order.get(e.topic_id, 0.0), e.subtopic_id))


def _all_subtopics() -> list[Subtopic]:
    from .syllabus import subtopics

    return list(subtopics().values())


def _topic_name(topic_id: str) -> str:
    """A lesson's topic name, falling back to the id.

    The fallback is reachable: `Lesson.subtopic_id` is a plain string and nothing
    validates that its `topic:` prefix names a declared topic. So a typo would
    otherwise raise deep inside menu rendering, where the learner sees a stack
    trace instead of a menu.
    """
    for t in TOPICS:
        if t.id == topic_id:
            return t.name
    return topic_id


def paper_shape_lines() -> list[str]:
    """The XAT 2026 shape, read from `PAPER_SHAPE` rather than restated."""
    part1 = PAPER_SHAPE["part1"]
    total = PAPER_SHAPE["total_questions"]
    part2 = PAPER_SHAPE["part2"]
    return [
        f"XAT 2026 -- {total} questions, Part 1 is {sum(part1.values())} "
        f"questions in {PAPER_SHAPE['part1_minutes']} minutes with NO sectional "
        f"time limit.",
        f"  QA&DI {part1['qa_di']}   VA&LR {part1['va_lr']}   "
        f"DM {part1['dm']}",
        f"  Part 2 GK {part2['gk']} in {part2['minutes']} minutes -- EXCLUDED from "
        f"the percentile by XLRI, so it is out of scope here.",
        # `:.2f` on both marking figures: Python prints -0.1 for -0.10, and the
        # penaltys are quoted to two decimals everywhere else because "-0.1" and
        # "-0.10" are different-looking numbers for the same value.
        f"  {PAPER_SHAPE['options']} options, "
        f"{PAPER_SHAPE['mark_correct']:+g} correct, "
        f"{PAPER_SHAPE['mark_wrong']:.2f} wrong, and "
        f"{PAPER_SHAPE['blank_penalty']:.2f} per blank after the first "
        f"{PAPER_SHAPE['blank_penalty_after']}.",
    ]


def render_menu() -> str:
    """The whole menu as text. Pure function of the registry and the syllabus."""
    entries = written_entries()
    lines: list[str] = []
    lines.append("")
    lines.append("=" * 72)
    lines.append("XAT PRACTICE -- what do you want to work on?")
    lines.append("=" * 72)
    lines.extend(paper_shape_lines())
    lines.append("")

    if not entries:
        # Reachable by deregistering every lesson, and it must say the honest
        # thing rather than print an empty numbered list that looks like a bug.
        lines.append("  No lessons are written yet. Nothing to serve.")
        return "\n".join(lines) + "\n"

    lines.append(f"  {SECTION_QA_DI} -- the only section this project trains, and")
    lines.append("  the only one with lessons written. VA&LR and DM are in the")
    lines.append("  paper above and are not built here; that is the honest state.")
    lines.append("")
    width = max(len(e.label) for e in entries)
    for n, e in enumerate(entries, 1):
        lines.append(f"   {n}. {e.label:<{width}s}  {e.subtopic_label}")
    lines.append("")
    lines.append(f"   {len(entries)} of {_len_subtopics()} subtopics written. "
                 f"Run `uv run xat-practice coverage` for the full ledger.")
    lines.append("   0. quit")
    lines.append("")
    return "\n".join(lines) + "\n"


def _len_subtopics() -> int:
    return len(_all_subtopics())


def choose(number: int) -> Entry | None:
    """Entry `number` (1-based), or None for quit/out of range."""
    entries = written_entries()
    if number < 1 or number > len(entries):
        return None
    return entries[number - 1]


def pick(read: object = input) -> Entry | None:
    """Ask, and return the chosen lesson. `read` is injected so this is testable
    without a TTY -- which is the whole point of putting it in a module."""
    print(render_menu(), end="")
    try:
        raw = read("  choose (or 0 to quit): ")  # type: ignore[operator]
    except EOFError:
        return None
    raw = str(raw).strip()
    if not raw:
        return None
    try:
        n = int(raw)
    except ValueError:
        print(f"  '{raw}' is not a number. Type the number, or 0 to quit.")
        return None
    return choose(n)

