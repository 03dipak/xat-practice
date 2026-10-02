"""The registry: every lesson that EXISTS, in one place.

MEASURED 2026-10-02. Before this module there were **11 references to `lesson1`
across 6 files**, and `bundle.OUT_DIR` was a hardcoded `out/lesson-01`. So Lesson
2 did not mean adding a file; it meant editing six of them by hand and remembering
that `out/` could hold exactly one lesson. A second lesson is the normal case, not
an edge case, and the codebase treated it as an edge case.

This module is the single answer to "what is written". Everything that needs to
know -- `cli.py`, `bundle.py`, and the `coverage` ledger -- reads it from here, so
adding a lesson is adding one `Lesson` to `LESSONS` and nothing else.

**Why it is a registry and not a folder scan.** A scan would discover files. This
holds the lessons that have passed their gates, with the solutions and the
teaching attached, because a lesson is a *unit*: four rungs, the step-by-step, and
the "before you start" block belong together and are meaningless apart.

**What "written" means, stated once because the CLI got it wrong.** A lesson
covers exactly ONE subtopic. So the coverage ledger reports two separate numbers
and never conflates them:

    subtopics written   1     <- `len({l.subtopic_id for l in LESSONS})`
    items written       4     <- `sum(len(l.items) for l in LESSONS)`

MEASURED: `xat-practice weightage` printed `written: 4` for a long time, which is
the item count, on a line whose neighbours were subtopic counts. It read as "four
topics done" on a project with 40. A count printed without saying what it counts
is a lie that looks like a pass, and it was one.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from . import lesson1, lesson2
from .items import Item
from .syllabus import TOPICS, Topic


@dataclass(frozen=True, slots=True)
class Lesson:
    """One written lesson.

    `items` is the four-rung ladder, `solutions` the step-by-step the learner
    reads, and `teach` the block rendered BEFORE question 1 (D18).
    """

    lesson_id: str
    subtopic_id: str
    items: tuple[Item, ...]
    solutions: Mapping[str, tuple[str, ...]]
    teach: Mapping[str, Mapping[str, object]]

    @property
    def topic_id(self) -> str:
        """The topic this lesson's subtopic belongs to."""
        return self.subtopic_id.split(":", 1)[0]

    @property
    def exam_id(self) -> str:
        """The exam, DERIVED from the subtopic's topic.

        A property, not a field. MEASURED 2026-10-02: `Topic` now carries
        `exam_id`/`section_id`, so a lesson could also have stored its own -- and
        then a lesson could disagree with its own subtopic about which exam it is
        in, with nothing to notice. Two homes for one fact is the D12 shape; the
        registry derives.
        """
        return self._topic().exam_id

    @property
    def section_id(self) -> str:
        """The section, derived. See `exam_id` for why this is not a field."""
        return self._topic().section_id

    @property
    def topic_label(self) -> str:
        for t in TOPICS:
            if t.id == self.topic_id:
                return t.name
        return self.topic_id

    def _topic(self) -> Topic:
        topic_id = self.topic_id
        for t in TOPICS:
            if t.id == topic_id:
                return t
        raise KeyError(
            f"{self.lesson_id}: subtopic {self.subtopic_id!r} names topic "
            f"{topic_id!r}, which is not in the syllabus. A lesson whose topic does "
            "not exist cannot be filed under a section."
        )

    @property
    def subtopics(self) -> set[str]:
        """How many SUBTOPICS this lesson covers. One, by construction -- a lesson
        is one subtopic at four levels, and conflating that with the item count is
        the bug this class exists to make impossible to repeat."""
        return {it.subtopic_id for it in self.items}


#: Every lesson that exists. Adding one here is the whole of "adding a lesson".
LESSONS: tuple[Lesson, ...] = (
    Lesson(
        lesson_id=lesson1.LESSON_ID,
        subtopic_id=lesson1.SUBTOPIC,
        items=lesson1.LESSON,
        solutions=lesson1.SOLUTIONS,
        teach=lesson1.TEACH,
    ),
    Lesson(
        lesson_id=lesson2.LESSON_ID,
        subtopic_id=lesson2.SUBTOPIC,
        items=lesson2.LESSON,
        solutions=lesson2.SOLUTIONS,
        teach=lesson2.TEACH,
    ),
)


def subtopics_written() -> set[str]:
    """The distinct subtopics covered by a written lesson."""
    out: set[str] = set()
    for lesson in LESSONS:
        out |= lesson.subtopics
    return out


def items_written() -> int:
    """The number of ITEMS written. Never reported under the word 'topics'."""
    return sum(len(lesson.items) for lesson in LESSONS)



def _assert_one_rung_per_level(lesson: Lesson) -> None:
    """A LESSON must actually derive one item per level.

    MEASURED 2026-10-02, on Lesson 2's first build. Its FOUNDATION item came out
    at **1.65, which is EASY**, because all four distractors were flagged real
    near-misses and 4 x 0.2 pushed a 0.85 base over the 1.5 boundary. The lesson
    therefore had **no foundation rung at all** -- and nothing said so.

    Why nothing said so is the part worth keeping:

    - `G11` enforces the level mix and **does not run on a four-item lesson**.
      `MIX_ENFORCEMENT_FLOOR` is 8, and D12 records that as a FIX: the paper-level
      rule once deleted the hard rung of Lesson 1. That fix was right, and it left
      the lesson's own mix ungoverned.
    - `G7` compares a `claimed_level` to the derived level, and `claimed_level` is
      `None` on every authored item, so it has nothing to compare.
    - `G8` asks for at least two real near-misses and is satisfied by four.

    So a lesson could lose a rung silently, and did. This is the guard D12's fix
    left missing: not `G11` loosened, but a check that belongs to the lesson.
    """
    from .items import LEVEL_ORDER, derive_level

    derived = [derive_level(it).level for it in lesson.items]
    missing = [lv.value for lv in LEVEL_ORDER if lv not in derived]
    if missing:
        raise AssertionError(
            f"{lesson.lesson_id} has no item that derives {missing}. Derived: "
            + ", ".join(f"{it.id}={lv.value}" for it, lv
                        in zip(lesson.items, derived, strict=True))
            + ". A lesson whose rungs do not derive is not a ladder, however well "
              "written the four questions are."
        )


def assert_registry_is_honest() -> None:
    """Fail the build if the registry disagrees with itself.

    Three invariants, each of which has been true by luck rather than by check:

    1. every lesson covers exactly ONE subtopic -- a lesson spanning two is a
       mock, and calling it a lesson would make the coverage ledger lie;
    2. every item has a solution and a step-by-step that ends on its own key;
    3. a subtopic is taught by at most one lesson, so 'written' is a count and
       not a sum with a duplicate in it;
    4. a lesson derives one item per level -- added when Lesson 2's foundation
       item came out as EASY and the lesson silently had no foundation rung.
    """
    seen: dict[str, str] = {}
    for lesson in LESSONS:
        # ORDER IS NORMATIVE, and moving this line is a regression that already
        # happened once. MEASURED 2026-10-02: the rung check ran FIRST, so a
        # deliberately malformed two-item lesson was reported as "has no item that
        # derives medium, hard" and the test asserting the "ONE subtopic" message
        # failed. The lesson was wrong for TWO reasons and the report named the
        # less useful one. A lesson spanning two subtopics is a MOCK, so that is
        # the fact worth stating first.
        if len(lesson.subtopics) != 1:
            raise AssertionError(
                f"{lesson.lesson_id} covers {len(lesson.subtopics)} subtopics "
                f"{sorted(lesson.subtopics)}; a lesson is ONE subtopic at four "
                "levels"
            )
        _assert_one_rung_per_level(lesson)
        (subtopic,) = tuple(lesson.subtopics)
        if subtopic in seen:
            raise AssertionError(
                f"{subtopic} is taught by both {seen[subtopic]!r} and "
                f"{lesson.lesson_id!r}; 'subtopics written' would double-count"
            )
        seen[subtopic] = lesson.lesson_id
        for item in lesson.items:
            steps = lesson.solutions.get(item.id)
            if not steps:
                raise AssertionError(f"{item.id} has no step-by-step")
            if not steps[-1].endswith(f"ANSWER: {item.key_text}"):
                raise AssertionError(
                    f"{item.id}'s step-by-step ends {steps[-1]!r}, which does not "
                    f"state its own key {item.key_text!r}"
                )


