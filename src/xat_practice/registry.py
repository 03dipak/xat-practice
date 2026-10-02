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

from . import lesson1
from .items import Item


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


def by_id(lesson_id: str) -> Lesson:
    for lesson in LESSONS:
        if lesson.lesson_id == lesson_id:
            return lesson
    raise KeyError(f"no lesson {lesson_id!r}; have {[x.lesson_id for x in LESSONS]}")


def assert_registry_is_honest() -> None:
    """Fail the build if the registry disagrees with itself.

    Three invariants, each of which has been true by luck rather than by check:

    1. every lesson covers exactly ONE subtopic -- a lesson spanning two is a
       mock, and calling it a lesson would make the coverage ledger lie;
    2. every item has a solution and a step-by-step that ends on its own key;
    3. a subtopic is taught by at most one lesson, so 'written' is a count and
       not a sum with a duplicate in it.
    """
    seen: dict[str, str] = {}
    for lesson in LESSONS:
        if len(lesson.subtopics) != 1:
            raise AssertionError(
                f"{lesson.lesson_id} covers {len(lesson.subtopics)} subtopics "
                f"{sorted(lesson.subtopics)}; a lesson is ONE subtopic at four "
                "levels"
            )
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


def all_items() -> list[Item]:
    """Every item of every lesson, in lesson order.

    The `gates` and `levels` verbs report over this rather than over
    `lesson1.LESSON`, because MEASURED 2026-10-02 a verb that printed "population:
    4 items (lesson lesson-01-simple-interest)" would keep reporting Lesson 1
    after Lesson 2 existed, and a gate suite that quietly tests less than it
    claims is the coverage-floor defect again."""
    out: list[Item] = []
    for lesson in LESSONS:
        out.extend(lesson.items)
    return out
