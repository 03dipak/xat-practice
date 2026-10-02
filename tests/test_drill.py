"""The owner's two asks, and what they cost in gates.

1. **Five questions at each level to begin with** -- twenty for a subtopic.
2. **"Give me more at this level, single-digit answers"** -- 1..9, on demand.

Both are D26 made visible: the level is the learner's, and the mix belongs to a
paper. The measurements below are the reason this file exists rather than a comment.
"""

from __future__ import annotations

import dataclasses

import pytest

from xat_practice import gates
from xat_practice import lesson1 as L
from xat_practice.items import (
    LESSON_20_SHAPE,
    LESSON_SHAPE,
    LEVEL_DRILL_SHAPES,
    LEVEL_ORDER,
    PaperShape,
    answer_is_single_digit,
    derive_level,
    single_digit_items,
)

# ---------------------------------------------------------------------------
# 5 / 5 / 5 / 5
# ---------------------------------------------------------------------------

def test_the_twenty_item_lesson_shape_closes_at_five_per_level():
    """Uniform mix over 20 questions, apportioned by largest remainder."""
    assert LESSON_20_SHAPE.questions == 20
    assert LESSON_20_SHAPE.quota() == {lv: 5 for lv in LEVEL_ORDER}
    assert sum(LESSON_20_SHAPE.quota().values()) == 20, (
        "a distribution that does not sum to the paper length is a gate nobody "
        "trusts"
    )
    assert LESSON_20_SHAPE.level_filtered is False, (
        "5/5/5/5 is a LESSON with a uniform mix, not a drill at one level"
    )


def test_the_four_item_lesson_shape_is_unchanged():
    """A single pass up the ladder is still four items -- the 20-item shape is
    ADDITIVE, so an existing lesson does not silently become 20 items."""
    assert LESSON_SHAPE.questions == 4
    assert LESSON_SHAPE.quota() == {lv: 1 for lv in LEVEL_ORDER}


def test_five_per_level_does_NOT_mean_five_copies_of_one_question():
    """THE measurement, and the reason the naive version of this feature fails.

    MEASURED 2026-10-02: cloning Lesson 1's items to five per level and running the
    gates admitted **4 of 20**. `G6_stem_distinctness` refused sixteen of them with
    "same reasoning shape, only the numbers differ, so this counts one question
    twice".

    So `G6` is RIGHT and this is not a bug to work around: five questions at a level
    means five genuinely different REASONINGS. That is a content cost, and it is the
    honest price of the feature.
    """
    cloned = tuple(dataclasses.replace(it, id=f"{it.id}-{k}")
                   for it in L.LESSON for k in range(5))
    assert len(cloned) == 20
    res = gates.run(cloned)
    assert len(res.admitted) < 20, (
        "if 20 clones were admitted, G6 would have stopped enforcing distinct "
        "reasoning and 'five per level' would mean padding"
    )
    assert {r.gate for r in res.refusals} == {"G6_stem_distinctness"}, (
        f"expected G6 to be the wall, got {sorted({r.gate for r in res.refusals})}"
    )


# ---------------------------------------------------------------------------
# the mix must NOT be enforced on a drill
# ---------------------------------------------------------------------------

def test_a_level_drill_shape_has_one_level_and_no_mix_to_enforce():
    for lv, shape in LEVEL_DRILL_SHAPES.items():
        quota = shape.quota()
        assert quota[lv] == shape.questions
        assert all(quota[other] == 0 for other in LEVEL_ORDER if other is not lv)
        assert shape.level_filtered is True


def _twenty_foundation_items() -> list:
    """Twenty items, all FOUNDATION, with twenty STRUCTURALLY distinct derivations.

    The distinct derivations matter: without them `G6` refuses them first and the
    mix question is never reached. MEASURED while writing this -- the first version
    cloned one derivation with a `+ k*0` tail, which masks to the same shape, so
    BOTH paths admitted 1 and the test proved nothing.
    """
    distinct = ["18*10/2", "7+8", "9-4", "3*3", "12/4", "81/9", "6+6", "2*5",
                "45-19", "100/25", "8-8", "7*7", "64/8", "5+9", "30/6", "1+1",
                "16/4", "11-6", "9*1", "72/8"]
    assert len(set(distinct)) == len(distinct)
    out = []
    for i, d in enumerate(distinct):
        v = str(int(eval(d)))
        others = ["997", "998", "999", "996"]
        vals = tuple([v, *others])
        out.append(dataclasses.replace(L.LESSON[0], id=f"D{i:02d}", derivation=d,
                                       options=vals, option_values=vals))
    return out


def _mix_kept(items, shape=None) -> int:
    res = gates.GateResult()
    for it in items:
        res.admitted.append(it)
        res.reports[it.id] = derive_level(it)
    return len(gates._enforce_mix(res, list(items), shape))


def test_g11_drops_a_single_level_set_that_is_not_marked_as_a_drill():
    """THE falsifying input for the guard, and it is the D12 defect verbatim.

    Twenty items, all at FOUNDATION, with twenty distinct reasonings, so `G6` cannot
    be what refuses them. Measured: **2 of 20 kept.** `G11` read them as a paper,
    found a foundation quota, and dropped eighteen.
    """
    items = _twenty_foundation_items()
    assert {derive_level(i).level for i in items} == {LEVEL_ORDER[0]}, (
        "the premise: all twenty must derive at ONE level"
    )
    assert _mix_kept(items) < 20, (
        "a 20-item single-level set passed the mix. If this ever holds, the trap is "
        "not being exercised and this test proves nothing."
    )


def test_g11_does_not_touch_a_shape_marked_as_a_level_drill():
    items = _twenty_foundation_items()
    kept = _mix_kept(items, LEVEL_DRILL_SHAPES[LEVEL_ORDER[0]])
    assert kept == 20, (
        f"the mix dropped {20 - kept} of 20 items from a shape that says it is "
        "level-filtered. MEASURED before the guard: 2 of 20. That is D12 -- a "
        "paper rule handed a non-paper -- reaching the learner through 'give me "
        "more at this level'."
    )


def test_the_decision_is_the_shape_not_the_length():
    """Why the guard cannot be `len(items) < MIX_ENFORCEMENT_FLOOR` alone.

    MEASURED 2026-10-02: that early return is 8, which protected a FIVE-item drill
    by accident. The owner's "give me twenty more" is above the floor, so length
    alone would have dropped eighteen of them. The shape has to decide.
    """
    items = _twenty_foundation_items()
    assert len(items) >= gates.MIX_ENFORCEMENT_FLOOR, (
        "this test is only meaningful ABOVE the floor, which is the whole point"
    )
    assert _mix_kept(items, LEVEL_DRILL_SHAPES[LEVEL_ORDER[0]]) == 20
    assert _mix_kept(items) < 20


def test_a_paper_shape_is_still_enforced():
    """The guard must not become an escape hatch for real papers."""
    items = _twenty_foundation_items()
    assert _mix_kept(items, LESSON_20_SHAPE) < 20, (
        "LESSON_20_SHAPE is a 5/5/5/5 lesson, NOT a drill, so the mix applies"
    )
    assert _mix_kept(items, PaperShape(
        name="X", questions=20, minutes=0,
        level_mix={LEVEL_ORDER[0]: 0.25, LEVEL_ORDER[1]: 0.25,
                   LEVEL_ORDER[2]: 0.25, LEVEL_ORDER[3]: 0.25},
        stratum=LESSON_20_SHAPE.stratum, negative_marking=False)) < 20


# ---------------------------------------------------------------------------
# single-digit answers
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("value, expected", [
    (1, True), (9, True), ("7", True), (5.0, True),
    (0, False), (10, False), (-3, False), (7.5, False),
    ("Rs 7", False), ("", False), (None, False), ("seven", False),
])
def test_single_digit_is_a_predicate_not_a_stored_claim(value, expected):
    """MEASURED 2026-10-02: a stored `single_digit: bool` would be a claim the code
    never re-derived, and this project's thesis is that a claim code did not compute
    is not evidence. So it is derived from the KEY every time."""
    assert answer_is_single_digit(value) is expected, value


def test_single_digit_filters_on_the_key_not_the_options():
    items = _twenty_foundation_items()
    kept = single_digit_items(items)
    assert kept, (
        "the premise: some keys are single digits. The helper computes each item's "
        "key from its own derivation, so if none qualify the arithmetic changed."
    )
    for it in kept:
        assert answer_is_single_digit(it.key_value), it.id
    for it in items:
        if it not in kept:
            assert not answer_is_single_digit(it.key_value), it.id


def test_a_single_digit_promise_is_enforceable_on_a_set():
    """The owner's rule as a property a DRILL must satisfy.

    Not a gate yet -- gating it would mean the generator existed, and it does not.
    What this pins is that the rule is CHECKABLE, so when the route ships the check
    is written rather than asserted.
    """
    items = _twenty_foundation_items()
    drill = single_digit_items(items)
    assert len(drill) < len(items), (
        "the premise: the filter must actually exclude something, or 'single digit' "
        "is not a constraint"
    )
    assert all(1 <= int(float(it.key_value)) <= 9 for it in drill)
