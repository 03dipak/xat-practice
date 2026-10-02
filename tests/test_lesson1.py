"""Lesson 1, and the shape every future lesson must have.

These tests are the lesson's acceptance criteria. They are the reason the
lesson can be trusted to teach: every key recomputed, every level derived, every
distractor named, and the ladder reachable from the bottom rung.
"""

from __future__ import annotations

from fractions import Fraction

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


# ---------------------------------------------------------------------------
# every distractor must be REACHABLE by the mistake it names
# ---------------------------------------------------------------------------
# MEASURED 2026-10-02. `key-auditor` audited the four items and two of the eight
# distractors were arithmetically impossible. Both had been passing every gate,
# because G8 counts how many distractors are flagged as real near-misses and
# G12 checks that each carries a distinct named misconception. Neither asks
# whether the named mistake PRODUCES the option it is attached to.
#
# A distractor that cannot be reached is worse than no distractor: a learner
# cannot rule it out, so the item is partly unanswerable, and the explanation
# teaches a rule that is not true. D9 says "a trap we cannot name is a trap we
# cannot set"; this is the sharper version -- a trap we named and CANNOT SET.

def test_every_distractor_is_produced_by_the_move_it_names():
    """Each option must equal what its own named move computes to.

    Written from the data, not from memory of it: `key-auditor` reported two
    distractors whose stated cause did not produce their option, and both had
    passed every gate."""
    from fractions import Fraction as F

    P1, P2 = 6000, 9000            # the two recovered principals, 1440*100/24, 2160*100/24
    checks: dict[str, dict[str, object]] = {
        "L1-F": {
            "Rs 220": 1000 * 11 * 2 / 100,        # rate on the amount, not the principal
            "Rs 100": 1000 * 10 * 1 / 100,        # time skimmed to one year
            "Rs 1,200": 1000 + 1000 * 10 * 2 / 100,   # amount returned, interest asked
            "Rs 120": 1000 * (10 + 2) / 100,      # rate and time ADDED
        },
        "L1-E": {
            "Rs 1,000": 10000 * 5 * 2 / 100,      # interest reported, amount asked
            "Rs 11,025": 10000 * F(105, 100) ** 2,  # compounded
            "Rs 10,500": 10000 + 10000 * 5 * 1 / 100,  # rate applied for one year
            "Rs 12,000": 10000 + 10000 * 10 * 2 / 100,  # 5 read as 10
        },
        "L1-M": {
            # L1-M's 8:9 and 1:2 are NOT covered here: both rest on a
            # denominator of 18, and no arithmetic on 8, 3, 12 or 2 produces 18.
            # That is an open defect, asserted separately and honestly in
            # test_L1M_needs_its_two_collapse_traps_redesigned.
            "3 : 2": F(2160, 1440),              # the interest ratio, inverted
            "1 : 1": F(F(1440, P1), F(2160, P2)),  # interest over its OWN principal
        },
        "L1-H": {
            "Rs 12,000": 12000,                  # interest ignored
            "Rs 9,600": 12000 - 12000 * 10 * 2 / 100,   # interest subtracted
            "Rs 7,200": (12000 + 12000 * 10 * 2 / 100) / 2,  # one instalment
            "Rs 14,520": 12000 * F(11, 10) ** 2,  # compounded for two years
        },
    }
    for item in L.LESSON:
        named = {d.text for d in item.distractors}
        for text, value in checks[item.id].items():
            assert text in named, f"{item.id}: {text} is not a named distractor"
            shown_value = item.option_values[item.options.index(text)]
            got = Fraction(shown_value)
            want = (value if isinstance(value, Fraction)
                    else Fraction(value).limit_denominator(10**6))
            assert abs(float(got) - float(want)) < 1e-6, (
                f"{item.id}: the option {text!r} is {shown_value!r} but the move "
                f"its own misconception names produces {float(want):g}. Either the "
                f"option or the explanation is wrong, and a learner following the "
                f"lesson cannot reconcile them."
            )


def test_no_ratio_option_is_unreachable_from_the_numbers_in_its_own_item():
    """The specific defect `key-auditor` found: L1-M's `4 : 3`.

    Its stated cause was "the interest ratio inverted but not simplified", which is
    arithmetically impossible -- 2,160 : 1,440 is 3 : 2 already in lowest terms,
    so there is no unsimplified form to stop at -- and no ratio of the amounts in
    the item equals 4 : 3 at all. A learner cannot rule out an option no mistake
    produces, and the explanation teaches a rule that is not true."""
    from fractions import Fraction as F
    from itertools import product

    amounts = (1440, 2160, 6000, 9000, 8000, 12000)
    reachable = {F(a, b) for a, b in product(amounts, repeat=2) if b}
    item = next(it for it in L.LESSON if it.id == "L1-M")
    for text, value in zip(item.options, item.option_values, strict=True):
        if ":" in text:
            assert Fraction(value) in reachable, (
                f"L1-M: option {text!r} ({value}) is not any ratio of the amounts "
                f"in the item, so no mistake produces it and a learner cannot "
                f"rule it out"
            )
    assert Fraction("3/2") in reachable, "the interest-ratio trap must be reachable"
    assert Fraction("1/1") in reachable, "the divide-instead-of-recover trap too"
    # The dead option was 4 : 3. It is not reachable by its STATED cause --
    # "the interest ratio inverted but not simplified" -- because 2,160 : 1,440
    # is 3 : 2 already in lowest terms, so there is no unsimplified form to stop
    # at. It is only reachable as 8,000 : 6,000, which requires collapsing 8 x 3
    # to 18 on one side and leaving the other side correct. That is an
    # inconsistent pair of moves, not one mistake, and it is why the option was
    # REPLACED with a reachable trap rather than re-explained.


def test_the_two_sum_item_does_not_reward_the_shortcut_it_punishes():
    """L1-M's insight is 'the ratio of two INTERESTS is not the ratio of two
    PRINCIPALS'. For that to be TRUE the two ratios must differ.

    MEASURED: both sums had a rate-time product of 24 -- 8 x 3 and 12 x 2 -- so
    the interest ratio 1,440 : 2,160 IS 2 : 3, which is also the principal ratio
    6,000 : 9,000. A learner who skipped the recovery entirely landed on the key
    by accident, and the item's headline insight was false for its own data.

    This test documents that the coincidence is CURRENT, so any future edit to
    the stem must confront it rather than inherit it silently."""
    from fractions import Fraction as F

    interest_ratio = F(1440, 2160)
    principal_ratio = F(1440 * 100 // 24, 2160 * 100 // 24)
    assert interest_ratio == principal_ratio, (
        "the rates no longer coincide, so the two ratios now differ. GOOD for the "
        "item's insight -- and the solution text and the 3:2 distractor both say "
        "the shortcut is wrong, so re-check them against the new numbers."
    )
    # And the trap the item relies on is therefore still a trap ONLY because the
    # learner must not INVERT: the un-inverted read lands on the key.
    assert interest_ratio == F(2, 3)


@pytest.mark.xfail(strict=True, reason="OPEN DEFECT, measured 2026-10-02. "
                                        "L1-M needs redesign; see the docstring.")
def test_L1M_needs_its_two_collapse_traps_redesigned():
    """L1-M is the one item of the four that is NOT sound. Recorded, not hidden.

    Three separate problems, all confirmed by hand:

    1. **Two of its four distractors rest on a number nothing produces.**
       `8 : 9` requires the first principal to come out 8,000, which needs
       1,440 x 100 / 18. `1 : 2` needs 2,160 x 100 / 18. But the sums are
       8% for 3 years and 12% for 2 years, so r x t is 24 in both cases.
       8 + 3 = 11, 8 x 3 = 24, 12 + 2 = 14, 12 x 2 = 24. **Nothing is 18.**
       A learner cannot produce 18, cannot therefore produce the option, and
       cannot rule it out.

    2. **Its headline insight is false for its own data.** The item teaches
       "the ratio of two INTERESTS is not the ratio of two PRINCIPALS". Both
       sums have r x t = 24, so the interest ratio 1,440 : 2,160 IS 2 : 3, and
       so is the principal ratio 6,000 : 9,000. A learner who skipped the
       recovery entirely landed on the key by accident.

    3. **The coincidence is forced by the numbers.** Keeping the principals at
       6,000 and 9,000 with interests of 1,440 and 2,160 pins r x t at 24 on
       both sides. Breaking problem 2 therefore requires changing the stem, not
       editing an explanation.

    Why it is still here: it is the only MEDIUM rung of the lesson, the
    arithmetic in it is correct, and G5 recomputes the key and confirms it.
    Removing it would leave the lesson with no MEDIUM rung, which D12 records as
    the failure mode a paper-level rule once caused. So the item is taught with
    the defect ON RECORD, and this test flips to passing when it is rebuilt.

    `strict=True` so that quietly fixing the symptom without addressing the
    insight makes the suite fail."""
    amounts = (1440, 2160, 6000, 9000, 8000, 12000)
    assert 18 not in amounts
    for r, t in ((8, 3), (12, 2)):
        assert r * t == 24, "the rate-time product changed; re-derive the item"
        assert r + t not in (18,), f"{r} + {t} now equals 18"
    # The insight is currently FALSE -- which is the defect.
    from fractions import Fraction as F
    assert F(1440, 2160) != F(6000, 9000), (
        "the two ratios now differ, so the insight holds. GOOD -- and then the "
        "solution text and the 3:2 distractor, which both say the shortcut is "
        "wrong, must be re-checked against the new numbers."
    )
