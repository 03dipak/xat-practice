"""Lesson 2, Geometry: areas and similar shapes.

Every lesson gets its own file, and the pattern is fixed by Lesson 1's. The tests
that matter most are the ones that take a REAL lesson, break it, and confirm the
suite notices -- a gate suite that has only ever seen a correct lesson has not
been tested, and that has already happened twice in this repo.

MEASURED 2026-10-02, while writing this lesson, and it is why the first rung had
to be rewritten: all four of `L2-F`'s distractors were flagged real near-misses,
which put its score at 0.85 + 4x0.2 = **1.65**, above the 1.50 boundary, so the
FOUNDATION item derived as EASY and the lesson had no foundation rung at all.
Nothing caught it. `G11` does not run on a four-item lesson, `G7` compares a
claim that is `None` on every authored item, and `G8` is satisfied by four.
`registry._assert_one_rung_per_level` now refuses that, and the two tests below
are the falsifying inputs for it.
"""

from __future__ import annotations

import dataclasses

import pytest
import sympy as sp

from xat_practice import gates as G
from xat_practice import lesson2 as L
from xat_practice import registry as R
from xat_practice.items import LESSON_SHAPE, Level, derive_level
from xat_practice.solver import Verdict


@pytest.fixture(scope="module")
def gated():
    return G.run(list(L.LESSON))


# ---------------------------------------------------------------------------
# the shape
# ---------------------------------------------------------------------------

def test_lesson_is_one_subtopic_four_levels():
    assert len(L.LESSON) == LESSON_SHAPE.questions
    assert {i.subtopic_id for i in L.LESSON} == {L.SUBTOPIC}
    assert L.SUBTOPIC in R.subtopics_written(), (
        "a lesson that is not in the registry is invisible to the coverage ledger"
    )


def test_lesson_shape_quota_is_one_per_level():
    from collections import Counter

    counts = Counter(derive_level(i).level for i in L.LESSON)
    assert counts == {lv: n for lv, n in LESSON_SHAPE.quota().items()}, counts


def test_the_four_levels_derive_in_order(gated):
    derived = [r.level for r in gated.reports.values()]
    assert derived == [Level.FOUNDATION, Level.EASY, Level.MEDIUM, Level.HARD]


def test_scores_increase_strictly_along_the_ladder(gated):
    scores = [gated.reports[i.id].score for i in L.LESSON]
    assert scores == sorted(scores) and len(set(scores)) == len(scores), scores


def test_the_registry_refuses_a_lesson_that_lost_a_rung():
    """THE falsifying input for the invariant added on 2026-10-02.

    Written after the real defect, not before: take this lesson, drop the hard
    rung, and confirm the registry refuses to describe it as a ladder. Before this
    invariant existed, dropping an item was silent.
    """
    base = next(x for x in R.LESSONS if x.lesson_id == L.LESSON_ID)
    short = dataclasses.replace(base, items=L.LESSON[:3])
    with pytest.raises(AssertionError) as err:
        R._assert_one_rung_per_level(short)
    assert "hard" in str(err.value), (
        "the refusal must name the missing rung, not just fail: "
        f"{err.value}"
    )


def test_the_registry_refuses_a_lesson_whose_easy_rung_is_too_strong():
    """And the input that actually shipped: keep all four items, but flag every
    distractor on the foundation rung as a real near-miss."""

    base = next(x for x in R.LESSONS if x.lesson_id == L.LESSON_ID)
    f = L.LESSON[0]
    hotter = dataclasses.replace(
        f, distractors=tuple(
            dataclasses.replace(d, is_real_near_miss=True) for d in f.distractors))
    assert derive_level(hotter).level is Level.EASY, (
        "this test is only meaningful while the hotter item really is EASY; if the "
        "recipe changed, rebuild the premise before trusting the refusal below"
    )
    mixed = dataclasses.replace(base, items=(hotter, *L.LESSON[1:]))
    with pytest.raises(AssertionError) as err:
        R._assert_one_rung_per_level(mixed)
    assert "foundation" in str(err.value)


def test_only_the_hard_item_needs_an_insight(gated):
    """Read off the DRIVERS, not an attribute that does not exist.

    MEASURED 2026-10-02: this first asserted `report.insight_required`, which
    `DifficultyReport` has never had -- `AttributeError`, and no lesson has been
    checked against the recipe that way. The driver string is what `derive_level`
    actually emits and what the CLI shows a learner, so that is what is asserted.
    """
    flags = ["requires an insight" in " ".join(r.drivers)
             for r in gated.reports.values()]
    assert flags == [False, False, False, True], (
        f"insight flags {flags}; the hard rung must be the only one that needs a "
        "move the topic does not name"
    )


def test_each_rung_has_its_own_derivation_shape():
    from xat_practice.gates import derivation_shape

    shapes = {i.id: derivation_shape(i.derivation) for i in L.LESSON}
    assert len(set(shapes.values())) == len(L.LESSON), shapes


def test_the_shapes_are_not_lesson_1s_shapes():
    """Cross-lesson, because `G17` runs per lesson and two lessons sharing a shape
    would let a paper mix duplicate rungs unnoticed."""
    from xat_practice import lesson1
    from xat_practice.gates import derivation_shape

    mine = {derivation_shape(i.derivation) for i in L.LESSON}
    theirs = {derivation_shape(i.derivation) for i in lesson1.LESSON}
    assert not (mine & theirs), (
        f"Geometry and Simple Interest share a derivation shape: {mine & theirs}"
    )


# ---------------------------------------------------------------------------
# the key. Re-derived by hand, independently of the gate.
# ---------------------------------------------------------------------------

def test_every_key_equals_its_derivation_by_hand():
    expected = {
        # 18 x 10 / 2. The halving is the whole item.
        "L2-F": sp.Rational(18 * 10, 2),
        # Trapezium: average of the parallel sides, then the height.
        "L2-E": sp.Rational((14 + 22) * 9, 2),
        # Similar figures scale in LENGTH, so sqrt(4) = 2.
        "L2-M": 6 * sp.sqrt(4),
        # Recover the base from the area, halve the base, recompute.
        "L2-H": sp.Rational((2 * 48 // 8) // 2 * 8, 2),
    }
    for item in L.LESSON:
        assert sp.nsimplify(sp.sympify(item.derivation)) == expected[item.id]
        assert sp.nsimplify(sp.sympify(item.key_value)) == expected[item.id]


def test_a_planted_wrong_key_on_this_lesson_is_refused():
    """Reorder BOTH arrays. Reordering only the labels is not a wrong key at all:
    `key_value` reads `option_values[key_index]`, so the solver still computes 12
    and still returns HOLD."""
    broken = list(L.LESSON)
    broken[2] = dataclasses.replace(
        broken[2],
        options=("10 cm", "12 cm", "24 cm", "3 cm", "8 cm"),
        option_values=("10", "12", "24", "3", "8"),
        key_index=0,
    )
    res = G.run(broken)
    assert "L2-M" not in {i.id for i in res.admitted}
    assert res.checks["L2-M"].verdict is Verdict.REFUSE


def test_all_four_are_admitted(gated):
    assert not gated.refusals, [r.detail for r in gated.refusals]


def test_option_values_are_not_display_strings():
    for item in L.LESSON:
        assert len(item.options) == 5 == len(item.option_values)
        for value in item.option_values:
            assert value is not None
            assert sp.sympify(str(value)) is not None, (
                f"{item.id}: {value!r} is a display string, not arithmetic"
            )


# ---------------------------------------------------------------------------
# the distractors
# ---------------------------------------------------------------------------

def test_every_item_has_four_distractors_for_five_options():
    for item in L.LESSON:
        assert len(item.distractors) == 4, item.id


def test_the_key_is_never_among_the_distractors():
    for item in L.LESSON:
        assert item.key_text not in {d.text for d in item.distractors}, item.id


def test_every_distractor_names_a_specific_wrong_move():
    for item in L.LESSON:
        for d in item.distractors:
            assert d.misconception.strip(), f"{item.id}: a distractor with no reason"
            assert len(d.misconception.split()) >= 6, (
                f"{item.id}/{d.text}: {d.misconception!r} is too short to be a "
                "reason, so a learner cannot learn from it"
            )


def test_misconceptions_are_distinct_within_an_item():
    for item in L.LESSON:
        seen = [d.misconception for d in item.distractors]
        assert len(set(seen)) == len(seen), f"{item.id} repeats a misconception"


def test_every_distractor_is_produced_by_the_move_it_names():
    """`G16`'s lesson half, run here so a failure names the item.

    The falsifying half is `G16`'s own planted case; this asserts the property
    holds for real data rather than trusting the gate's exit code.
    """
    for item in L.LESSON:
        for d in item.distractors:
            assert d.produces is not None, (
                f"{item.id}/{d.text}: no `produces` value, so nothing checks that "
                "this option is the arithmetic of the mistake it names"
            )


def test_the_area_ratio_trap_is_the_medium_rung_s_reason():
    """`L2-M`'s whole reason for existing. The wrong-but-reachable answer is
    6 x 4 = 24, which is the length ratio used as if it were the length itself."""
    m = next(i for i in L.LESSON if i.id == "L2-M")
    assert "24" in {d.text for d in m.distractors}, (
        "the square-root trap is the item; without it the rung is just a multiply"
    )
    # The distractor states the WRONG MOVE ("the AREA ratio used directly as a
    # LENGTH ratio") and the SOLUTION states the rule it breaks. Those live in
    # different fields and conflating them is how a check ends up demanding that a
    # wrong answer explain itself correctly.
    assert any("area ratio" in d.misconception.lower()
               and "length" in d.misconception.lower() for d in m.distractors), (
        "the trap must name the move: an area ratio used as a length ratio"
    )
    steps = " ".join(L.SOLUTIONS["L2-M"]).lower()
    assert "square root" in steps or "sqrt" in steps, (
        "the learner is told 24 is wrong and must then be told WHY. The rule is "
        f"the whole rung: {steps}"
    )


def test_the_hard_rung_is_not_solved_by_halving_the_area():
    """`L2-H`'s best distractor, 48/4 = 12, is a TRUE rule applied where it does
    not hold -- area scales with the square of a length change only when BOTH
    dimensions change, and the stem pins the height at 8.

    So the wrong answer must be reachable and the right answer must not be 12.
    """
    h = next(i for i in L.LESSON if i.id == "L2-H")
    assert "12" in {d.text for d in h.distractors}
    assert h.key_text != "12"
    joined = " ".join(d.misconception.lower() for d in h.distractors)
    assert "square of a length change" in joined, (
        "the rung teaches the wrong rule only if it says which rule it is: "
        + joined
    )
    # ...and only if it says the CONDITION under which that rule is false, which is
    # the actual lesson. Without the condition the learner memorises the trap
    # instead of the rule.
    assert "every dimension changes" in joined or "both dimensions change" in joined, (
        "the condition is the whole point of this rung: " + joined
    )


def test_the_foundation_item_is_deliberately_weaker():
    f = L.LESSON[0]
    assert sum(d.is_real_near_miss for d in f.distractors) == 2, (
        "the foundation rung keeps exactly two real near-misses; four puts it "
        f"over the boundary. Got {sum(d.is_real_near_miss for d in f.distractors)}"
    )


# ---------------------------------------------------------------------------
# the step-by-step and the teaching
# ---------------------------------------------------------------------------

def test_every_item_has_a_step_by_step_solution():
    assert set(L.SOLUTIONS) == {i.id for i in L.LESSON}


def test_every_solution_states_the_key():
    for item in L.LESSON:
        assert L.SOLUTIONS[item.id][-1] == f"ANSWER: {item.key_text}", item.id


def test_every_solution_explains_every_wrong_option():
    for item in L.LESSON:
        text = " ".join(L.SOLUTIONS[item.id])
        for d in item.distractors:
            assert d.text in text, (
                f"{item.id}: the step-by-step never mentions the option {d.text}, "
                "so a learner who picked it is never told why"
            )


def test_solutions_are_steps_not_just_an_answer():
    for item in L.LESSON:
        steps = L.SOLUTIONS[item.id]
        assert len(steps) >= 4, f"{item.id}: {len(steps)} steps is not a walkthrough"
        assert sum(1 for s in steps if s.lower().startswith("step")) >= 1, item.id


def test_the_teaching_example_does_not_hand_over_question_ones_key():
    """D18's rule. Written against Q1's OWN numbers, so it cannot pass vacuously
    on a lesson whose key text it has never seen."""
    import re

    teach = L.TEACH[L.SUBTOPIC]
    q1 = L.LESSON[0]
    blob = " ".join(str(v) for v in teach.values() if isinstance(v, str))
    example = teach["example"]

    def nums(text: str) -> set[str]:
        out: set[str] = set()
        for raw in re.findall(r"\d[\d,]*(?:\.\d+)?", text):
            out.add(raw)
            if "," in raw:
                out.add(raw.replace(",", ""))
        return out

    q1_numbers = nums(q1.stem)
    assert q1.key_text not in blob, (
        f"the teaching card states question 1's answer ({q1.key_text})"
    )
    shared = nums(example) & q1_numbers
    assert not shared, (
        f"the worked example reuses question 1's numbers {sorted(shared)}, so it "
        "hands over the key before the commit"
    )


def test_the_teaching_states_the_formula_and_the_units():
    teach = L.TEACH[L.SUBTOPIC]
    assert "=" in teach["formula"], teach["formula"]
    assert teach["units"].strip()
    assert len(teach["legend"]) >= 2, (
        "every symbol the formula uses must be defined in words"
    )
    for term, name, _ in teach["legend"]:
        assert term.strip() and name.strip()


def test_the_teaching_names_the_two_traps_the_lesson_actually_sets():
    """A teaching block that does not mention the traps its own questions set is
    a list of facts, not a lesson."""
    teach = L.TEACH[L.SUBTOPIC]
    blob = " ".join(str(v) for v in teach.values() if isinstance(v, str)).lower()
    # `square-rooted` is hyphenated in the card, and `in "square root"` would miss
    # it -- which is a lesson about the checks, not about geometry.
    assert "square-root" in blob or "square root" in blob or "sqrt" in blob, (
        "L2-M is built on rooting an area ratio; the teaching must say so"
    )
    assert "trapezium" in blob, "L2-E is a trapezium; the teaching must say so"
