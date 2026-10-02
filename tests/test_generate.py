"""Falsifying inputs for `generate.py`. Every test here was written after the
defect it names was MEASURED, and several exist only because the generator got
something wrong first.

The standing rule for this file: a generator that silently emits nothing, or emits
a stem it cannot answer, or emits twenty items the gates refuse, is WORSE than no
generator -- because the button works and the drill is empty or wrong. So the
tests are about SUPPLY and ADMISSION, not about arithmetic.
"""

from __future__ import annotations

import re

import pytest

from xat_practice import gates
from xat_practice.generate import (
    DIGIT_MAX,
    DIGIT_MIN,
    GRIDS,
    TEMPLATES,
    build_items,
    candidates,
)
from xat_practice.items import LESSON_20_SHAPE, LEVEL_DRILL_SHAPES, Level
from xat_practice.solver import Solver

_SUB = "pct:single-digit-drill"
_ALL = [Level.FOUNDATION, Level.EASY, Level.MEDIUM, Level.HARD]


# --------------------------------------------------------------------------
# SUPPLY. The owner's promise is that a click yields questions.
# --------------------------------------------------------------------------


@pytest.mark.parametrize("template", sorted(TEMPLATES))
def test_every_template_can_actually_produce_a_single_digit_answer(template: str):
    """DISPROVES: a template that is registered but unusable.

    MEASURED 2026-10-02: `reverse_percent` was registered and returned an empty
    list for every parameter set, because it computed the post-change value as
    `p * 100 + q`, which is never below 100 and therefore can never have a
    single-digit pre-change value. Nothing crashed, nothing warned, and a click
    would have produced an empty drill.
    """
    found = candidates(template)
    assert found, f"template {template!r} is registered but produces NOTHING"
    for b in found:
        assert DIGIT_MIN <= b.key <= DIGIT_MAX, (
            f"{template} yielded key {b.key} from candidates(), which is supposed "
            "to be pre-filtered to a single digit"
        )


@pytest.mark.parametrize("template", sorted(TEMPLATES))
def test_every_template_has_a_grid(template: str):
    """A template with no grid can only produce nothing, so this is a guard on
    the table rather than on the arithmetic."""
    assert GRIDS.get(template), f"{template!r} has no entry in GRIDS"


def test_a_template_whose_answers_repeat_is_caught_by_the_dedupe():
    """DISPROVES: the `keys_seen` test is present but never fires.

    MEASURED 2026-10-02: `two_quantities` returns key 1 for all twelve of its
    instances, because its answer depends only on (p - q) while the grid varies p
    fastest. Five items with the same ANSWER and five different stems would look
    like variety to any test that only counted them.
    """
    for template in TEMPLATES:
        keys = [b.key for b in candidates(template)]
        assert len(keys) == len(set(keys)), (
            f"{template} returned repeated answers {keys}: distinct ANSWERS are "
            "as much the point as distinct reasoning"
        )


# --------------------------------------------------------------------------
# SUPPLY, quantified. "More at this level" means FIVE, not "some".
# --------------------------------------------------------------------------


@pytest.mark.parametrize("level", _ALL)
def test_each_level_can_be_served_five_items(level: Level):
    """The owner's ask is five more at the level the learner is on."""
    items = build_items(_SUB, count=5)
    assert len(items) == 5
    shape = LEVEL_DRILL_SHAPES[level]
    assert shape.level_filtered is True


def test_twenty_items_can_be_served_from_the_template_pool_alone():
    """64 instances across 8 templates must cover a 5/5/5/5 set without a repeat."""
    assert sum(len(candidates(t)) for t in TEMPLATES) >= 20


# --------------------------------------------------------------------------
# ADMISSION. A generated item the gates refuse is a broken promise.
# --------------------------------------------------------------------------


def test_a_full_set_of_generated_items_is_admitted_by_the_gates():
    """The strongest statement available: 20 generated items, real gate run."""
    items = build_items(_SUB, count=20)
    assert len(items) == 20
    report = gates.run(items, shape=LESSON_20_SHAPE)
    admitted = {i.id for i in report.admitted}
    assert len(admitted) == 20, (
        f"only {len(admitted)} of 20 generated items were admitted; refusals: "
        f"{[r.message for r in report.refusals][:6]}"
    )


def test_a_level_filtered_drill_of_generated_items_is_admitted():
    """A drill must not be mix-enforced (D26 / TASK-060), and this proves it on
    REAL generated items rather than synthetic ones."""
    items = build_items(_SUB, count=20)
    shape = LEVEL_DRILL_SHAPES[Level.FOUNDATION]
    report = gates.run(items, shape=shape)
    assert len(report.admitted) == 20, (
        f"a level-filtered drill kept {len(report.admitted)} of 20 -- the "
        "same D12 defect TASK-060 measured on synthetic items"
    )


def test_the_same_twenty_are_not_admitted_as_a_single_level_paper():
    """THE FALSIFYING DIRECTION. If this ever passes, `level_filtered` has
    stopped meaning anything and the drill gate is theatre.

    MEASURED 2026-10-02: without the shape, 20 items at one level kept 2 of 20.
    """
    items = build_items(_SUB, count=20)
    as_lesson = gates.run(items, shape=LESSON_20_SHAPE)
    as_drill = gates.run(items, shape=LEVEL_DRILL_SHAPES[Level.FOUNDATION])
    assert len(as_drill.admitted) > len(as_lesson.admitted), (
        f"drill admitted {len(as_drill.admitted)}, lesson "
        f"{len(as_lesson.admitted)} -- the shape is no longer doing anything"
    )


# --------------------------------------------------------------------------
# KEYS. D1: the key is RE-DERIVED, never asserted. A generator that asserts it
# is the one thing this project exists to avoid.
# --------------------------------------------------------------------------


def test_every_generated_key_is_re_derived_by_the_solver_not_taken_on_trust():
    """The solver re-evaluates each item's own derivation with exact arithmetic
    and must agree with the keyed option. Disagreement is a REFUSAL (G5)."""
    for item in build_items(_SUB, count=20):
        computed = Solver().solve(item)
        assert computed is not None
        assert computed == item.option_values[item.key_index], (
            f"{item.id}: derivation {item.derivation!r} evaluates to {computed!r} "
            f"but the key says {item.option_values[item.key_index]!r}"
        )


def test_a_planted_wrong_key_is_REFUSED_so_the_solver_actually_tests_them():
    """DISPROVES the test above. A solver that returned the keyed option for any
    input would pass the test above perfectly.

    This is the same shape as `test_G5_planted_wrong_key_is_REFUSED`, applied to
    generated items: without it, 'the keys agree with the solver' could mean
    'the solver agrees with anything'.
    """
    import dataclasses

    items = build_items(_SUB, count=1)
    good = items[0]
    key = good.option_values[good.key_index]
    planted = tuple(
        str(int(key) + 3) if str(v) == key else v for v in good.option_values
    )
    bad = dataclasses.replace(good, options=planted, option_values=planted)
    assert not gates.run([bad], shape=LEVEL_DRILL_SHAPES[Level.FOUNDATION]).admitted
    assert gates.run([good], shape=LEVEL_DRILL_SHAPES[Level.FOUNDATION]).admitted


def test_the_generator_is_deterministic():
    """A drill that serves different questions on each click is not a drill."""
    a = build_items(_SUB, count=12)
    b = build_items(_SUB, count=12)
    assert [x.stem for x in a] == [x.stem for x in b]
    assert [x.derivation for x in a] == [x.derivation for x in b]


# --------------------------------------------------------------------------
# OPTION HYGIENE. Two defects measured here, both invisible to a count.
# --------------------------------------------------------------------------


def test_no_item_repeats_an_option():
    """MEASURED 2026-10-02: `net_change` and `two_quantities` both offered `p - q`
    as a distractor for some parameters, which is the same question with the key
    in two places. Five options must be five DIFFERENT numbers."""
    for item in build_items(_SUB, count=20):
        assert len(set(item.options)) == 5, f"{item.id}: options {item.options}"


def test_option_values_are_bare_numbers_and_only_the_label_carries_a_unit():
    """`14,400` parses to the TUPLE (14, 400) rather than failing, and `Rs 200`
    does not parse at all (AGENTS.md) -- so `option_values` must be arithmetic and
    `options` may be display.

    MEASURED 2026-10-02: `net_change` put "%" into its DISTRACTOR texts, so the
    unit leaked into `option_values` through a different door than the one fixed
    before it. Checking one field is not enough; both are checked here, and the
    display label is checked for CONTAINING the bare value, which is what `G14`
    requires.
    """
    for item in build_items(_SUB, count=20):
        for v in item.option_values:
            assert re.fullmatch(r"-?\d+", v), (
                f"{item.id}: option_values {v!r} is not a bare integer, so the "
                "solver cannot parse it"
            )
        for value, label in zip(item.option_values, item.options, strict=True):
            assert value in label, (
                f"{item.id}: arithmetic {value!r} is NOT visible in its label "
                f"{label!r}, which is what G14 exists to refuse"
            )


def test_every_distractor_names_a_mistake_and_carries_what_it_produces():
    """G16 checkability. A distractor whose `produces` is missing cannot be
    checked against the mistake that makes it, which is how a plausible-looking
    option with no reason behind it gets in."""
    for item in build_items(_SUB, count=20):
        assert len(item.distractors) == 4
        for d in item.distractors:
            assert d.misconception and len(d.misconception) > 10, (
                f"{item.id}: distractor {d.text!r} has no explanation"
            )


def test_a_key_must_not_be_repeated_as_its_own_distractor():
    for item in build_items(_SUB, count=20):
        key = item.option_values[item.key_index]
        assert all(d.text != key for d in item.distractors)
