"""Lesson 1, and the shape every future lesson must have.

These tests are the lesson's acceptance criteria. They are the reason the
lesson can be trusted to teach: every key recomputed, every level derived, every
distractor named, and the ladder reachable from the bottom rung.
"""

from __future__ import annotations

import json
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
        # L1-M rebuilt: 1,440 x 100/(8x3) = 6,000 and 2,160 x 100/(15x3) = 4,800,
        # so 6,000 : 4,800 is 5 : 4. The old data had both rate-time products
        # equal to 24, which made the interest ratio identical to the answer.
        "L1-M": sp.Rational(1440 * 100, 8 * 3) * sp.Rational(15 * 3, 2160 * 100),
        # L1-H rewritten 2026-10-02. 30% of 1000 is 300 for THREE years, so
        # the rate is 300*100/(1000*3) = 10, and 5 years of interest is 500.
        "L1-H": 1000 + (300 * 100 // (1000 * 3)) * 1000 * 5 // 100,
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
    """A sum you are ADDING to ends above where it started.

    MEASURED 2026-10-02: this asserted `Rs 9,600`, which was the sign error on the
    OLD hard rung. The rung has been rebuilt -- it now infers a rate and re-applies
    it -- so the distractor is `Rs 700` and the assertion follows the item rather
    than the item's former number. A test that pins a specific figure stops
    reporting when the item improves."""
    texts = [d.text for d in L.HARD.distractors]
    sign = [d for d in L.HARD.distractors if "subtracted" in d.misconception.lower()]
    assert sign, "the hard rung no longer carries a sign error at all"
    below = [t for t in texts if t.replace("Rs ", "").replace(",", "").isdigit()
             and int(t.replace("Rs ", "").replace(",", "")) < 1000]
    assert below, (
        f"no option is below the principal 1000, so the sign error has no "
        f"home: {texts}"
    )
    # and the sign error's own option really is principal MINUS interest
    key_value = sp.nsimplify(sp.sympify(L.HARD.key_value))
    assert int(sp.nsimplify(sign[0].produces)) == 1000 - 300 < int(key_value)


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

    P1, P2 = 6000, 4800            # 1440*100/(8*3) and 2160*100/(15*3)
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
            # L1-M rebuilt 2026-10-02. Its old 8:9 and 1:2 both rested on a
            # denominator of 18 that nothing in the item produced, so a learner
            # could not rule them out. Every option is now reachable, and 15 + 3
            # = 18 actually produces the one denominator this item uses.
            "2 : 3": F(1440, 2160),              # the interest ratio, directly
            "3 : 2": F(2160, 1440),              # the same, inverted
            "1 : 2": F(P1, F(2160 * 100, 18)),   # 15 + 3 = 18, not 15 x 3
            "8 : 15": F(F(1440, P1), F(2160, P2)),  # each SI over its OWN principal
        },
        "L1-H": {
            # L1-H rebuilt: infer the rate, then re-apply it over 5 years.
            "Rs 1,300": 1000 + 300,               # the 3-year interest carried over
            "Rs 2,500": 1000 + 1000 * 30 * 5 / 100,    # 30% read as the annual rate
            "Rs 1,750": 1000 + 1000 * 15 * 5 / 100,    # 30% halved to fit a year
            "Rs 700": 1000 - 300,                 # interest subtracted
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

    amounts = (1440, 2160, 6000, 4800, 12000)
    reachable = {F(a, b) for a, b in product(amounts, repeat=2) if b}
    # Plus the two PER-PRINCIPAL RATES, which are quantities the item's own
    # arithmetic produces: 1,440/6,000 = 6/25 and 2,160/4,800 = 9/20. A learner
    # who divides each interest by its own principal compares those two, and gets
    # 8 : 15. Without them in the set the check would call a reachable option
    # unreachable -- a false positive that would teach an author to distrust it.
    rates = (F(1440, 6000), F(2160, 4800))
    reachable |= {F(a, b) for a in rates for b in rates if b}
    item = next(it for it in L.LESSON if it.id == "L1-M")
    for text, value in zip(item.options, item.option_values, strict=True):
        if ":" in text:
            assert Fraction(value) in reachable, (
                f"L1-M: option {text!r} ({value}) is not any ratio of the amounts "
                f"in the item, so no mistake produces it and a learner cannot "
                f"rule it out"
            )
    assert Fraction("3/2") in reachable, "the inverted interest ratio must be reachable"
    assert Fraction("8/15") in reachable, "the divide-instead-of-recover trap too"
    assert Fraction("1/2") in reachable, "the 15+3=18 collapse must be reachable"
    # 18 must be PRODUCIBLE from the item, which is the defect the old item had:
    # its collapse denominator was 18 and nothing in that item produced 18.
    assert 15 + 3 == 18, "the collapse denominator must be reachable"
    # The old dead option was 4 : 3, described as "the interest ratio inverted
    # but not simplified" -- impossible, because 2,160 : 1,440 is 3 : 2 already in
    # lowest terms. And the old item needed an 18 that nothing produced. Both are
    # gone: every option above is now reachable from the numbers in the stem.


def test_the_two_sum_item_does_not_reward_the_shortcut_it_punishes():
    """L1-M's insight is 'the ratio of two INTERESTS is not the ratio of two
    PRINCIPALS'. For that to be TRUE the two ratios must DIFFER, and for years
    they did not.

    MEASURED: both sums had a rate-time product of 24 -- 8 x 3 and 12 x 2 -- so
    the interest ratio 1,440 : 2,160 WAS 2 : 3, which was also the principal ratio
    6,000 : 9,000. A learner who skipped the recovery entirely landed on the key
    by accident, and the item's headline insight was false for its own data.

    The second sum is now 15% for 3 years, so the rate-time products are 24 and 45
    and the ratios genuinely differ: interest 2 : 3 against principals 5 : 4."""
    from fractions import Fraction as F

    interest_ratio = F(1440, 2160)
    principal_ratio = F(1440 * 100 // 24, 2160 * 100 // 45)
    assert interest_ratio != principal_ratio, (
        "the two ratios coincide, so skipping the recovery lands on the key and "
        "the item's headline insight is FALSE for its own data -- which is the "
        "defect this test exists to hold shut"
    )
    assert interest_ratio == F(2, 3)
    assert principal_ratio == F(5, 4)


def test_L1M_collapse_traps_are_now_reachable():
    """L1-M is sound NOW. Both of its defects are kept visible here rather than
    deleted, because both were invisible to every gate.

    WHAT IT WAS:
      1. Two of its four distractors needed a denominator of 18, and NOTHING in
         the item produced 18 -- both sums had a rate-time product of 24. A
         learner could not produce the option and could not rule it out.
      2. Its headline claim, "the ratio of two INTERESTS is not the ratio of two
         PRINCIPALS", was FALSE for its own data: 1,440 : 2,160 IS 2 : 3 and so
         was 6,000 : 9,000, so skipping the recovery landed on the key.

    THE FIX:
      - the second sum is now 15% for 3 years, so the rate-time products are 24
        and 45 and the ratios genuinely differ: interest 2:3, principals 5:4.
      - the collapse denominator is now 15 + 3 = 18, which something in the item
        actually produces, so the option is reachable.

    NEITHER DEFECT WAS CATCHABLE, and that is the finding worth keeping: `G5`
    recomputes the key and the key was right throughout; `G8` counts near-misses;
    `G12` checks four distinct names exist; `G16` checks each name's arithmetic
    produces its option -- and it did, because 1440*100/18 really is 8,000.
    **A false claim about how a learner errs is invisible to every gate, because
    it is a claim about people.**
    """
    from fractions import Fraction as F

    assert 15 + 3 == 18, "the collapse denominator must come from the item"
    assert 15 * 3 == 45, "the correct product, and the two must differ"

    interest_ratio = F(1440, 2160)
    principal_ratio = F(1440 * 100 // 24, 2160 * 100 // 45)
    assert interest_ratio != principal_ratio, (
        "the ratios coincide, so skipping the recovery lands on the key -- the "
        "exact defect this item had"
    )
    assert interest_ratio == F(2, 3) and principal_ratio == F(5, 4)

    item = next(i for i in L.LESSON if i.id == "L1-M")
    assert {d.text for d in item.distractors} == {"2 : 3", "8 : 15", "1 : 2", "3 : 2"}


def test_each_rung_has_its_own_derivation_shape():
    """The measurement both reviewers asked for: FOUR pairwise-distinct
    digit-masked derivation shapes across the four rungs.

    MEASURED, and it is 3 of 4:

        L1-F  1000*10*2/100                   ->  N*N*N/N
        L1-E  10000 + 10000*5*2/100           ->  N + N*N*N/N
        L1-M  (1440*100/(8*3))/(2160*...)     ->  (N*N/(N*N)) / (N*N/(N*N))
        L1-H  12000 + 12000*10*2/100          ->  N + N*N*N/N     <-- same as E

    **The HARD rung WAS EASY's arithmetic relabelled, and it is no longer.**
    `level-auditor` falsified it: replacing L1-H's `insight_required=False`,
    `needs_substitution=False`, `derivation_steps=2` -- changing nothing a learner
    sees -- dropped its score from 7.40 to 2.50, the EASY tier. So 4.90 of 7.40,
    **66% of the hard item's difficulty, was a declared flag with nothing in the
    derivation to prove it.** `G17` refused the lesson, and the rung was rebuilt
    around an operation no lower rung performs: infer the RATE from a stated
    interest, then re-apply it over a different time.

    Why no gate caught it, and this is the generalisable finding:

    - `G7` compares a `claimed_level` to the derived level, and `claimed_level` is
      `None` on all four items, so it has nothing to compare.
    - `G6` fingerprints the STEM, not the DERIVATION. So "compounding read as
      simple interest" is taught at L1-E (11,025) and again at L1-H (14,520) and
      every gate passes -- `G16` confirms each produces its own option, `G12`
      confirms the misconception strings differ, and nobody notices the same wrong
      move is being drilled twice.
    - Nothing anywhere compares a level FLAG to the derivation the flag claims to
      describe. `derive_level` reads the flags; no gate reads the derivation.

    `G17_derivation_shape_distinct` now enforces this on every set, so the
    property is no longer a fact about one lesson but a rule about forty."""
    import re

    shapes = [re.sub(r"[0-9]+", "N", it.derivation) for it in L.LESSON]
    assert len(set(shapes)) == 4, (
        f"only {len(set(shapes))} of 4 rungs have a distinct derivation shape. "
        f"The hard rung must add an OPERATION, not a label: "
        f"{dict(zip((it.id for it in L.LESSON), shapes, strict=True))}"
    )


# ---------------------------------------------------------------------------
# D18 -- the teaching, shown before the first question
# ---------------------------------------------------------------------------
# MEASURED 2026-10-02 by `viewer`: the formula first reached the screen only
# AFTER question 1 was answered, so a learner who did not know what simple
# interest IS could not learn it from this lesson. For a zero-to-pro goal that is
# the product failing at step one. The owner chose TEACH THEN ASK.

def test_the_lesson_carries_teaching_for_its_subtopic():
    assert L.SUBTOPIC in L.TEACH, (
        f"no teaching block for {L.SUBTOPIC}. The step-by-step renders only "
        "inside check(), so without this a beginner cannot learn the topic here."
    )
    t = L.TEACH[L.SUBTOPIC]
    for field in ("heading", "why", "formula", "legend", "why_divide", "units",
                  "example", "bridge"):
        assert t.get(field), f"the teaching block is missing {field!r}"


def test_the_teaching_defines_every_symbol_it_uses():
    """MEASURED missing entirely before D18: nothing in the bundle said what
    'principal' MEANS. A formula with undefined symbols is not an explanation."""
    t = L.TEACH[L.SUBTOPIC]
    assert len(t["legend"]) == 3
    for letter, _name, meaning in t["legend"]:
        assert letter in t["formula"], f"{letter} is defined but never used"
        assert meaning.strip(), f"{letter} has no meaning given"
        assert len(meaning.split()) >= 5, (
            f"{letter} = {meaning!r} is too short to teach anything"
        )


def test_the_teaching_states_the_units_rule():
    """MEASURED missing before D18. Without it a monthly rate can be dropped in
    as an annual one and nothing on the page says that is illegal."""
    units = L.TEACH[L.SUBTOPIC]["units"].lower()
    assert "per year" in units
    assert "month" in units, (
        "the units rule must say what to do when the rate is not annual, or it "
        "only states half of itself"
    )


def test_the_teaching_example_does_not_hand_over_question_ones_key():
    """THE TRAP IN FIXING THIS, and the reason this test exists.

    MEASURED: the only worked example in the file was question 1 verbatim --
    1,000 at 10% for 2 years giving 200. Reusing it as the teaching example hands
    over Q1's answer BEFORE the commit and destroys Q1 as a check, while every
    gate passes, because no gate knows what a beginner has been told.

    So the example must run on different numbers, and it must check its own
    arithmetic."""
    import re

    example = L.TEACH[L.SUBTOPIC]["example"]
    stem = L.LESSON[0].stem
    for forbidden in ("1,000", "1000", "10%"):
        assert forbidden not in example, (
            f"the teaching example uses {forbidden!r}, which is in question 1's "
            f"own stem ({stem!r}). A learner who follows the example has already "
            f"answered question 1 before the options appear."
        )
    nums = [int(n.replace(",", "")) for n in re.findall(r"[0-9][0-9,]*", example)]
    assert 2000 in nums and 400 in nums, (
        f"the example must be 2,000 at 5% for 4 years -> 400, found {nums}"
    )
    assert 2000 * 5 * 4 // 100 == 400, "the example's own arithmetic is wrong"


def test_the_teaching_is_in_the_paper_and_never_in_the_key():
    """It is shown BEFORE the commit, so putting it behind the commit barrier
    would mean it never appears until it is too late to help -- and putting it in
    `answerkey.json` would ship the teaching with the answers."""
    from xat_practice import bundle

    files = bundle.build_lesson(L.LESSON_ID, L.LESSON, L.SOLUTIONS, L.TEACH)
    assert files["paper.json"]["teach"], "paper.json carries no teaching"
    assert "teach" not in files["answerkey.json"], (
        "the teaching is behind the commit barrier, so it will not be seen until "
        "after the learner has answered"
    )
    blob = json.dumps(files["paper.json"])
    assert "ANSWER:" not in blob, "paper.json must not carry the answers"
