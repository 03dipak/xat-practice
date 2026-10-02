"""Lesson 1, and the shape every future lesson must have.

These tests are the lesson's acceptance criteria. They are the reason the
lesson can be trusted to teach: every key recomputed, every level derived, every
distractor named, and the ladder reachable from the bottom rung.
"""

from __future__ import annotations

import pytest
import sympy as sp

from xat_practice import gates as G
from xat_practice import lesson1 as L
from xat_practice.items import LESSON_SHAPE, Level, derive_level
from xat_practice.solver import Verdict


@pytest.fixture(scope="module")
def gated():
    return G.run(list(L.lesson()))


# ---------------------------------------------------------------------------
# the shape
# ---------------------------------------------------------------------------

def test_lesson_is_one_subtopic_four_levels():
    assert len(L.LESSON) == 4
    assert {i.subtopic_id for i in L.LESSON} == {L.SUBTOPIC}
    assert {derive_level(i).level for i in L.LESSON} == set(Level)


def test_lesson_shape_quota_is_one_per_level():
    assert LESSON_SHAPE.quota() == {Level.FOUNDATION: 1, Level.EASY: 1,
                                    Level.MEDIUM: 1, Level.HARD: 1}


def test_the_four_levels_derive_in_order(gated):
    """Not requested, not claimed -- derived, and asserted in order."""
    levels = [gated.reports[i.id].level for i in L.LESSON]
    assert levels == [Level.FOUNDATION, Level.EASY, Level.MEDIUM, Level.HARD]


def test_scores_increase_strictly_along_the_ladder(gated):
    scores = [gated.reports[i.id].score for i in L.LESSON]
    assert scores == sorted(scores), f"ladder is not monotonic: {scores}"


def test_every_level_names_its_drivers(gated):
    """A hard item with no named driver is not hard, it is long."""
    for item in L.LESSON:
        assert gated.reports[item.id].drivers, f"{item.id} names no driver"


def test_only_the_hard_item_needs_an_insight(gated):
    for item in L.LESSON:
        assert gated.reports[item.id].drivers, item.id
    assert L.HARD.insight_required is True
    assert all(not i.insight_required for i in (L.FOUNDATION, L.EASY, L.MEDIUM))


def test_the_hard_rung_is_built_on_the_easy_one():
    """The ladder claim, mechanically: MEDIUM needs a substitution, which is
    the step EASY does not, and HARD adds an insight on top. If this stops
    being true the lesson has become four unrelated questions."""
    assert not L.EASY.needs_substitution
    assert L.MEDIUM.needs_substitution
    assert L.MEDIUM.insight_required is False
    assert L.HARD.insight_required is True


# ---------------------------------------------------------------------------
# the keys -- the property that outranks the rest
# ---------------------------------------------------------------------------

def test_lesson1_every_key_is_recomputed(gated):
    """Not asserted. RECOMPUTED, and HOLD means the derivation agrees."""
    for item in L.LESSON:
        chk = gated.checks[item.id]
        assert chk.verdict is Verdict.HOLD, f"{item.id}: {chk.detail}"
        assert chk.grounded is True


def test_lesson1_all_four_are_admitted(gated):
    assert len(gated.admitted) == 4, [r.detail for r in gated.refusals]
    assert gated.refusal_rate == 0.0


def test_every_key_equals_its_derivation_by_hand():
    """The same check, written out independently of the gate. If the gate and
    this disagree, one of them is wrong and that is worth knowing."""
    expected = {
        "L1-F": sp.Rational(1000 * 10 * 2, 100),
        "L1-E": 10000 + 10000 * 5 * 2 // 100,
        "L1-M": sp.Rational(2, 3),
        "L1-H": 12000 + 12000 * 10 * 2 // 100,
    }
    for item in L.LESSON:
        assert sp.nsimplify(sp.sympify(item.derivation)) == expected[item.id]
        assert sp.nsimplify(sp.sympify(item.key_value)) == expected[item.id]


def test_a_planted_wrong_key_on_this_lesson_is_refused():
    """THE lesson-specific falsifying input. Take the real lesson, corrupt one
    key, and confirm the gate catches it. A gate that has only ever seen a
    correct lesson has not been tested."""
    import dataclasses

    good = L.lesson()
    broken = list(good)
    # Reorder BOTH arrays. Reordering only the labels is not a wrong key at
    # all: `key_value` reads `option_values[key_index]`, so the solver still
    # checks 11000 and still returns HOLD. The first version of this test did
    # exactly that and passed for the wrong reason.
    broken[1] = dataclasses.replace(
        broken[1],
        options=("Rs 1,000", "Rs 11,000", "Rs 10,250", "Rs 11,025", "Rs 10,200"),
        option_values=("1000", "11000", "10250", "11025", "10200"),
        key_index=0,
    )
    res = G.run(broken)
    assert "L1-E" not in {i.id for i in res.admitted}
    assert res.checks["L1-E"].verdict is Verdict.REFUSE


def test_option_values_are_not_display_strings():
    """The defect that cost all four keys: `Rs 200` and `2 : 3` do not parse.
    If a future lesson reintroduces labels as values, G5 refuses everything."""
    for item in L.LESSON:
        for value in item.option_values:
            sp.sympify(value, rational=True)  # must not raise


# ---------------------------------------------------------------------------
# distractors
# ---------------------------------------------------------------------------

def test_every_distractor_names_a_specific_wrong_move():
    for item in L.LESSON:
        for d in item.distractors:
            assert len(d.misconception.split()) >= 8, f"{item.id}: {d.misconception!r}"


def test_misconceptions_are_distinct_within_an_item():
    for item in L.LESSON:
        names = [d.misconception for d in item.distractors]
        assert len(set(names)) == len(names), item.id


def test_every_item_has_four_distractors_for_five_options():
    for item in L.LESSON:
        assert len(item.distractors) == 4
        assert len(item.options) == 5


def test_the_key_is_never_among_the_distractors():
    for item in L.LESSON:
        assert item.key_text not in [d.text for d in item.distractors]


def test_hard_item_distractors_are_all_real_near_misses():
    assert all(d.is_real_near_miss for d in L.HARD.distractors)


def test_the_foundation_item_is_deliberately_weaker():
    """2 of 4, and that is the point: at foundation the learner is meeting the
    formula, so only two distractors test whether they read it correctly."""
    real = sum(d.is_real_near_miss for d in L.FOUNDATION.distractors)
    assert real == 2
    assert real >= 2, "G8 requires at least 2"


def test_compounding_is_a_named_distractor_at_easy_level():
    """The most common error in this topic, so it is named rather than hoped
    for."""
    text = " ".join(d.misconception for d in L.EASY.distractors).lower()
    assert "compound" in text
    assert "Rs 11,025" in [d.text for d in L.EASY.distractors]


def test_the_sign_error_is_a_named_distractor_at_hard_level():
    """A debt repaid early costs MORE, and `Rs 9,600` is the sign error."""
    texts = [d.text for d in L.HARD.distractors]
    assert "Rs 9,600" in texts
    assert any("subtracted" in d.misconception.lower() for d in L.HARD.distractors)


# ---------------------------------------------------------------------------
# the step-by-step
# ---------------------------------------------------------------------------

def test_every_item_has_a_step_by_step_solution():
    assert set(L.SOLUTIONS) == {i.id for i in L.LESSON}


def test_every_solution_explains_every_wrong_option():
    """The owner's flow asks for the misconception behind every option the
    learner did not pick. A solution that silently omits one teaches less than
    the learner needs."""
    for item in L.LESSON:
        blob = " ".join(L.SOLUTIONS[item.id])
        for d in item.distractors:
            assert d.text in blob, f"{item.id} never rules out {d.text}"


def test_every_solution_states_the_key():
    for item in L.LESSON:
        blob = " ".join(L.SOLUTIONS[item.id])
        assert item.key_text in blob, f"{item.id} never states its own answer"


def test_solutions_are_steps_not_just_an_answer():
    for item in L.LESSON:
        blob = " ".join(L.SOLUTIONS[item.id])
        assert "Step 1" in blob, item.id
        assert len(blob.split()) > 80, f"{item.id} solution is too thin to teach"


# ---------------------------------------------------------------------------
# the mix gate must not eat a lesson
# ---------------------------------------------------------------------------

def test_g11_does_not_run_on_a_lesson():
    """MEASURED: G11's quota for 4 items was {1,1,1,0} and it DROPPED the hard
    item. A paper-level rule deleted the product's central claim."""
    assert G.MIX_ENFORCEMENT_FLOOR == 8
    res = G.run(list(L.lesson()))
    assert not any(r.gate == "G11_mix_within_tolerance" for r in res.refusals)
    assert len(res.admitted) == 4


def test_g11_still_runs_on_a_paper():
    """The floor must not disable the gate it was protecting."""
    from tests.test_gates import at_level

    items = [at_level(Level.MEDIUM, i) for i in range(10)]
    res = G.run(items)
    assert any(r.gate == "G11_mix_within_tolerance" for r in res.refusals)


# ---------------------------------------------------------------------------
# G14 -- the ratio false positive, and the comma trap it was built for
# ---------------------------------------------------------------------------

def test_g14_accepts_a_ratio_written_two_ways():
    """MEASURED: the first version compared digit runs and REFUSED `2 : 3`
    against `2/3` -- the same ratio in the notation XAT actually uses."""
    assert G._value_visible_in_label("2 : 3", "2/3")
    assert G._value_visible_in_label("2:3", "2/3")


def test_g14_catches_a_label_that_contradicts_its_value():
    assert not G._value_visible_in_label("Rs 11,000", "10250")


def test_g14_catches_the_thousands_separator_tuple_trap():
    """`sympify('14,400')` returns the TUPLE (14, 400) rather than failing, so
    the parse check cannot catch it. G14 can."""
    assert not G._value_visible_in_label("Rs 14,400", "(14, 400)")


def test_g14_ignores_prose_options():
    assert G._value_visible_in_label("Cannot be determined", "Cannot be determined")
