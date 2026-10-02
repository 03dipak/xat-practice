"""The gate suite.

THE RULE (reference project, AC-10): a check that has only ever been shown a
true statement is untested. Every gate below is exercised with a WRONG input
first, and that test is named after what it disproves. `test_G5_planted_wrong_key`
is the one that matters most: it plants a bad key and asserts the item is
REFUSED, because that exact defect shipped through all 19 gates in the reference
project and the bundle on disk still contains it.
"""

from __future__ import annotations

import pytest

from xat_practice.gates import GATE_IDS, _stem_fingerprint, run
from xat_practice.items import (
    LEVEL_ORDER,
    LEVEL_RECIPES,
    Distractor,
    Item,
    Level,
    PaperShape,
    derive_level,
    expected_ev,
    recipe,
)
from xat_practice.solver import SOLVER, Failure, Verdict
from xat_practice.syllabus import POPULATION, QUESTIONS_PER_PAPER, TOPICS, Stratum

# ---------------------------------------------------------------------------
# fixtures: one clean item per stratum
# ---------------------------------------------------------------------------

def _distractors(n: int = 4) -> tuple[Distractor, ...]:
    return tuple(
        Distractor(text=f"{i}", misconception=f"trap {i}", is_real_near_miss=True)
        for i in range(n)
    )


def quant_item(**kw) -> Item:
    base = dict(
        id="q1",
        subtopic_id="pl_int:simple-interest",
        stratum=Stratum.QUANT,
        stem="What simple interest does 1000 earn at 10% for 2 years?",
        options=("100", "200", "210", "220", "1200"),
        key_index=1,
        option_values=("100", "200", "210", "220", "1200"),
        derivation="1000*10*2/100",
        distractors=_distractors(),
        derivation_steps=2,
        needs_substitution=False,
        insight_required=False,
    )
    base.update(kw)
    # A test that overrides `options` without `option_values` is testing the
    # OPTION, not the value, and inventing values for it would be noise. So
    # when only `options` is given, derive the values from them. This is why
    # several tests below broke when `option_values` became required: the
    # invariant is real and the fixtures were incomplete, not the gate.
    if "options" in kw and "option_values" not in kw:
        base["option_values"] = tuple(
            str(int("".join(c for c in o if c.isdigit()))) if any(
                c.isdigit() for c in o) else o
            for o in kw["options"]
        )
    return Item(**base)


def logic_item(**kw) -> Item:
    base = dict(
        id="l1",
        subtopic_id="ds:sufficiency-statements",
        stratum=Stratum.LOGIC,
        stem="Statement I and II",
        options=("a", "b", "c", "d", "e"),
        key_index=0,
        option_values=(),
        derivation="enumerated",
        distractors=_distractors(),
        derivation_steps=1,
        needs_substitution=False,
        insight_required=False,
        enumeration_size=12,
    )
    base.update(kw)
    # A test that overrides `options` without `option_values` is testing the
    # OPTION, not the value, and inventing values for it would be noise. So
    # when only `options` is given, derive the values from them. This is why
    # several tests below broke when `option_values` became required: the
    # invariant is real and the fixtures were incomplete, not the gate.
    if "options" in kw and "option_values" not in kw:
        base["option_values"] = tuple(
            str(int("".join(c for c in o if c.isdigit()))) if any(
                c.isdigit() for c in o) else o
            for o in kw["options"]
        )
    return Item(**base)


def judgement_item(**kw) -> Item:
    base = dict(
        id="j1",
        subtopic_id="va_lr:critical-reasoning",
        stratum=Stratum.JUDGEMENT,
        stem="The author of the passage would most likely agree that...",
        options=("a", "b", "c", "d", "e"),
        key_index=0,
        option_values=(),
        derivation=None,
        distractors=_distractors(),
        derivation_steps=0,
        needs_substitution=False,
        insight_required=False,
    )
    base.update(kw)
    # A test that overrides `options` without `option_values` is testing the
    # OPTION, not the value, and inventing values for it would be noise. So
    # when only `options` is given, derive the values from them. This is why
    # several tests below broke when `option_values` became required: the
    # invariant is real and the fixtures were incomplete, not the gate.
    if "options" in kw and "option_values" not in kw:
        base["option_values"] = tuple(
            str(int("".join(c for c in o if c.isdigit()))) if any(
                c.isdigit() for c in o) else o
            for o in kw["options"]
        )
    return Item(**base)


# ---------------------------------------------------------------------------
# the weight model
# ---------------------------------------------------------------------------

def test_weight_table_closes_to_paper_length():
    """Every year must sum to 28. A table that does not close is opinions."""
    from xat_practice.syllabus import self_check

    self_check()  # raises on mismatch


def test_population_is_196():
    assert POPULATION == 196
    assert QUESTIONS_PER_PAPER == 28


def test_pct_weight_is_zero_and_marked_unmeasured():
    """`pct` is 0 because it is NOT separately measured, not because it is
    absent. If someone 'fixes' this to a real number the docstring lies."""
    pct = next(t for t in TOPICS if t.id == "pct")
    assert pct.weight == 0.0
    assert "NOT SEPARATELY MEASURED" in pct.note


def test_tiers_follow_the_stated_thresholds():
    from xat_practice.syllabus import Tier, by_tier

    for t in by_tier(Tier.P1):
        assert t.weight >= 2.0
    for t in by_tier(Tier.P2):
        assert 0.5 <= t.weight < 2.0
    for t in by_tier(Tier.P3):
        assert 0.0 < t.weight < 0.5


# ---------------------------------------------------------------------------
# G5 -- the one that outranks the rest
# ---------------------------------------------------------------------------

def test_G5_planted_wrong_key_is_REFUSED():
    """THE test. Plants a key that disagrees with the derivation."""
    bad = quant_item(options=("100", "200", "999", "220", "1200"), key_index=2)
    res = run([bad])
    assert res.admitted == []
    assert res.checks["q1"].verdict is Verdict.REFUSE
    assert res.checks["q1"].failure is Failure.KEY_MISMATCH


def test_G5_correct_key_is_admitted():
    good = quant_item()
    res = run([good])
    assert len(res.admitted) == 1
    assert res.checks["q1"].verdict is Verdict.HOLD


def test_quant_item_cannot_be_constructed_without_a_derivation():
    """The schema refuses at construction, so an unverifiable quant item never
    reaches the gate. This is earlier and stronger than a refusal."""
    import pytest as _pt

    with _pt.raises(ValueError, match="cannot be recomputed"):
        quant_item(derivation=None)


def test_judgement_item_cannot_carry_a_derivation():
    """A derivation on a prose item is a fabricated proof of a key nobody
    checked -- the worst available outcome."""
    import pytest as _pt

    with _pt.raises(ValueError, match="fabricated proof"):
        judgement_item(derivation="42")


def test_G5_rounded_key_is_caught_as_a_mismatch_not_a_float():
    """MEASURED: `rational=True` makes `1.41421` exact as `141421/100000`, so
    the NONEXACT branch is unreachable. The real defence is KEY_MISMATCH."""
    chk = SOLVER.verify(stratum=Stratum.QUANT, derivation="sqrt(2)/2",
                        keyed_value="1.41421", keys=[])
    assert chk.verdict is Verdict.REFUSE
    assert chk.failure is Failure.KEY_MISMATCH


def test_G5_exact_surd_key_is_admitted():
    """An XAT key CAN be irrational. Refusing surds would refuse real questions."""
    chk = SOLVER.verify(stratum=Stratum.QUANT, derivation="sqrt(2)/2",
                        keyed_value="sqrt(2)/2", keys=[])
    assert chk.verdict is Verdict.HOLD


def test_G5_solver_refuses_free_symbols():
    chk = SOLVER.verify(stratum=Stratum.QUANT, derivation="x*2",
                        keyed_value="6", keys=[])
    assert chk.failure is Failure.UNRESOLVED_DERIVATION


def test_G5_judgement_item_with_a_derivation_is_refused():
    """A fabricated proof for a prose key is the worst available outcome."""
    chk = SOLVER.verify(stratum=Stratum.JUDGEMENT, derivation="42",
                        keyed_value="a", keys=[])
    assert chk.failure is Failure.WRONG_STRATUM


def test_G5_judgement_item_is_delegated_not_silently_passed():
    """MEASURED REGRESSION. This asserted HOLD, which would have claimed a
    prose key was confirmed by code. It must be DELEGATED -- an outcome that
    refuses to overstate where the evidence came from."""
    chk = SOLVER.verify(stratum=Stratum.LOGIC, derivation="enumerated",
                        keyed_value="a", keys=[])
    assert chk.verdict is Verdict.DELEGATED
    assert chk.grounded is False
    assert chk.detail.startswith("logic stratum delegated to enumeration")


# ---------------------------------------------------------------------------
# G7 -- level is derived, never requested
# ---------------------------------------------------------------------------

def test_G7_claimed_level_that_disagrees_with_structure_is_refused():
    it = quant_item(claimed_level=Level.HARD)
    res = run([it])
    assert res.admitted == []
    assert any(r.gate == "G7_level_agrees" for r in res.refusals)


def test_G7_no_claim_is_not_a_refusal():
    """Not every drafter will volunteer a level. Absent a claim there is
    nothing to disagree with."""
    res = run([quant_item(claimed_level=None)])
    assert len(res.admitted) == 1
    assert res.reports["q1"].verdict == "NO_CLAIM"


def test_derive_level_names_its_drivers():
    """A hard item with no named driver is not hard, it is long."""
    it = quant_item(derivation_steps=4, needs_substitution=True,
                    insight_required=True, claimed_level=None)
    rep = derive_level(it)
    assert rep.level is Level.HARD
    assert len(rep.drivers) >= 3


def test_derive_level_single_move_with_weak_distractors_is_foundation():
    """Difficulty is a function of structure AND discrimination. One move plus
    arbitrary distractors is a foundation item: there is nothing to work out
    and nothing to rule out."""
    it = quant_item(
        derivation_steps=1, needs_substitution=False, insight_required=False,
        distractors=tuple(
            Distractor(text=str(i), misconception=f"m{i}", is_real_near_miss=False)
            for i in range(4)),
        claimed_level=None,
    )
    assert derive_level(it).level is Level.FOUNDATION


def test_derive_level_one_move_with_real_near_misses_is_easy():
    """The same derivation with four genuine computed near-misses is EASY, not
    FOUNDATION: the item is only as hard as its distractors. This
    interaction is deliberate and is why a paper of arbitrary numbers reads as
    easy no matter how long the derivation is."""
    rep = derive_level(quant_item(derivation_steps=1, claimed_level=None))
    assert rep.level is Level.EASY


# ---------------------------------------------------------------------------
# the other gates
# ---------------------------------------------------------------------------

def test_G1_four_options_is_refused():
    """XAT 2026 has 5. A 4-option item is a CAT habit and it moves the
    guessing equilibrium from EV 0.0 to EV +0.0625."""
    res = run([quant_item(options=("100", "200", "210", "220"))])
    assert any(r.gate == "G1_options" for r in res.refusals)


def test_G3_all_of_the_above_is_refused():
    res = run([quant_item(options=("100", "200", "210", "All of the above", "x"))])
    assert any(r.gate == "G3_no_all_of_above" for r in res.refusals)


def test_G4_duplicate_options_refused():
    res = run([quant_item(options=("100", "200", "100", "220", "1200"))])
    assert any(r.gate == "G4_distinct_options" for r in res.refusals)


def test_G6_two_items_differing_only_in_numbers_are_one_item_twice():
    a = quant_item(id="a", stem="What is 15% of 480?")
    b = quant_item(id="b", stem="What is 20% of 360?")
    res = run([a, b])
    assert any(r.gate == "G6_stem_distinctness" for r in res.refusals)


def test_stem_fingerprint_strips_digits():
    assert _stem_fingerprint("What is 15% of 480?") == _stem_fingerprint(
        "What is 20% of 360?")


def test_G8_four_arbitrary_distractors_are_refused():
    it = quant_item(distractors=tuple(
        Distractor(text=str(i), misconception=f"m{i}", is_real_near_miss=False)
        for i in range(4)))
    res = run([it])
    assert any(r.gate == "G8_near_miss_distractors" for r in res.refusals)


def test_G9_item_over_two_minutes_is_refused():
    """The exam provides an on-screen calculator. Hand-computation difficulty
    is the wrong axis."""
    res = run([quant_item(calculator_minutes=3.5)])
    assert any(r.gate == "G9_calc_budget" for r in res.refusals)


def test_G12_unnamed_misconception_refused():
    it = quant_item(distractors=tuple(
        Distractor(text=str(i), misconception="  ", is_real_near_miss=True)
        for i in range(4)))
    res = run([it])
    assert any(r.gate == "G12_misconceptions_named" for r in res.refusals)


def test_G13_key_leaking_stem_refused():
    res = run([quant_item(stem="The answer is 200. What is the SI?")])
    assert any(r.gate == "G13_no_leak" for r in res.refusals)


def at_level(level: Level, i: int) -> Item:
    """An item whose STRUCTURE is the recipe for `level`. This is the only
    sanctioned way to build a fixture at a target level."""
    r = LEVEL_RECIPES[level]
    return quant_item(
        id=f"{level.value}-{i}",
        stem=_DISTINCT_STEMS[i],
        derivation_steps=int(r["derivation_steps"]),      # type: ignore[call-overload]
        needs_substitution=bool(r["needs_substitution"]), # type: ignore[call-overload]
        insight_required=bool(r["insight_required"]),     # type: ignore[call-overload]
        distractors=recipe(level),
    )


def test_every_level_is_reachable_from_its_recipe():
    """The recipes are the contract between a drafter and `derive_level`. If a
    recipe stops producing its own level, `derive_level` has drifted."""
    for level in LEVEL_ORDER:
        assert derive_level(at_level(level, 0)).level is level, (
            f"recipe for {level} derives something else: "
            f"{derive_level(at_level(level, 0))}"
        )


def test_level_boundaries_are_not_surprising():
    """One extra plausible wrong move must not be worth a whole level."""
    from dataclasses import replace

    base = at_level(Level.EASY, 0)
    base = replace(base, distractors=tuple(
        d if i < 2 else replace(d, is_real_near_miss=False)
        for i, d in enumerate(base.distractors)))

    before = derive_level(base)
    ds = list(base.distractors)
    ds[2] = replace(ds[2], is_real_near_miss=True)
    after = derive_level(replace(base, distractors=tuple(ds)))

    assert after.score - before.score == pytest.approx(0.2), (
        "the near-miss contribution is not linear, so a level boundary can sit "
        "on an arbitrary count of distractors"
    )


def test_G2_out_of_range_key_is_refused_not_raised():
    """MEASURED: an out-of-range key used to raise IndexError inside
    `SOLVER.verify` and destroy the whole run before G2 could refuse the item."""
    res = run([quant_item(key_index=9)])
    assert res.refusals
    assert any(r.gate == "G2_key_in_range" for r in res.refusals)
    # and it must not be misreported as a key mismatch
    assert not any(r.gate == "G5_key_grounded" for r in res.refusals)


def test_one_bad_item_does_not_destroy_the_paper():
    """The robustness property the IndexError bug violated: one malformed item
    costs one item, not the run."""
    mix = ([Level.FOUNDATION] * 2 + [Level.EASY] * 5
           + [Level.MEDIUM] * 8 + [Level.HARD] * 5)
    items = [at_level(lv, i) for i, lv in enumerate(mix)]
    items[7] = quant_item(id="broken", stem="Zeta is broken", key_index=9)
    res = run(items)
    assert len(res.admitted) == 19, f"admitted {len(res.admitted)}, expected 19"


def _judgement_with_forged_derivation() -> Item:
    """A JUDGEMENT item with a derivation is rejected at construction by
    `Item.__post_init__`, so G10 is reachable only by rebuilding the dataclass
    without the constructor's check -- which is exactly what a bad drafter
    would do."""

    j = judgement_item()
    object.__setattr__(j, "derivation", "42")
    return j


def test_G10_does_not_refuse_a_legitimate_logic_item():
    """Regression guard for the inversion that made G10 refuse 100% of logic
    items: a logic item's derivation is its enumeration, and is expected."""
    res = run([logic_item()])
    assert not any(r.gate == "G10_stratum_shape" for r in res.refusals)


def test_G10_refuses_a_judgement_item_that_forged_a_derivation():
    res = run([_judgement_with_forged_derivation()])
    assert any(r.gate == "G10_stratum_shape" for r in res.refusals)


def test_logic_items_are_not_silently_passed_as_grounded():
    """They are delegated to enumeration, and the delegation is visible in the
    detail string. Silently returning HOLD on a closed form is the failure."""
    chk = SOLVER.verify(stratum=Stratum.LOGIC, derivation="enumerated",
                        keyed_value="a", keys=[])
    assert "enumeration" in chk.detail


def test_every_gate_id_is_reachable():
    """An unreachable gate is a specification, not a gate."""
    fired: set[str] = set()

    def fire(*items: Item) -> None:
        fired.update(r.gate for r in run(list(items)).refusals)

    fire(quant_item(options=("1", "2", "3")))                              # G1
    fire(quant_item(options=("1", "2", "3", "All of the above", "5")))     # G3
    fire(quant_item(options=("1", "2", "1", "4", "5")))                   # G4
    fire(quant_item(options=("1", "2", "3", "4", "5"), key_index=2))      # G5
    fire(quant_item(key_index=9))                                         # G2
    fire(quant_item(id="a", stem="Alpha beta gamma 7"),                   # G6
         quant_item(id="b", stem="Alpha beta gamma 11"))
    fire(quant_item(claimed_level=Level.HARD))                            # G7
    fire(quant_item(distractors=tuple(                                  # G8
        Distractor(text=str(i), misconception=f"m{i}", is_real_near_miss=False)
        for i in range(4))))
    fire(quant_item(calculator_minutes=3.0))                             # G9
    fire(logic_item())                                                   # G10 must PASS
    fire(_judgement_with_forged_derivation())                            # G10
    fire(quant_item(distractors=tuple(                                  # G12
        Distractor(text=str(i), misconception="same", is_real_near_miss=True)
        for i in range(4))))
    fire(quant_item(stem="The answer is 200, so what is it?"))           # G13
    fire(quant_item(stem="Alpha value",                     # G14
                    options=("Rs 11,000", "Rs 1,000", "Rs 10,250",
                             "Rs 11,025", "Rs 10,200"),
                    option_values=("1000", "11000", "10250", "11025", "10200"),
                    key_index=1))
    # G11: over-quota. Ten MEDIUM recipes against a quota of 4. The floor is 8,
    # so a 3-item version of this call passed for the wrong reason.
    fire(*[at_level(Level.MEDIUM, i) for i in range(10)])

    missing = set(GATE_IDS) - fired
    assert not missing, f"unreachable gates: {sorted(missing)}"


# ---------------------------------------------------------------------------
# marking arithmetic -- the numbers the pedagogy rests on
# ---------------------------------------------------------------------------

def test_guessing_5_options_is_exactly_score_neutral():
    """+1/5 and -0.25x4/5 cancel. This is a fact, not an argument."""
    assert expected_ev(options=5) == 0.0


def test_guessing_4_options_leaks():
    """Why D5 and D6 are reversed here and were correct in the reference."""
    assert expected_ev(options=4) == pytest.approx(0.0625)


def test_ninth_blank_costs_more_than_a_guess():
    """The trap almost nobody teaches: leaving the 9th blank blank is strictly
    worse than guessing at random."""
    assert expected_ev(blanks=9) < expected_ev()
    assert expected_ev(blanks=10) == pytest.approx(-0.2)


def test_practice_shape_carries_no_negative_marking():
    from xat_practice.items import PRACTICE_SHAPE

    assert PRACTICE_SHAPE.negative_marking is False
    assert PRACTICE_SHAPE.options == 5


def test_level_mix_quotas_close_to_the_paper():
    from xat_practice.items import LEVEL_MIX

    assert sum(LEVEL_MIX.values()) == pytest.approx(1.0)


def test_paper_quota_sums_to_question_count():
    for n in (4, 20, 28):
        shape = PaperShape(name="t", questions=n, minutes=0,
                           level_mix={Level.FOUNDATION: 0.1, Level.EASY: 0.25,
                                      Level.MEDIUM: 0.4, Level.HARD: 0.25},
                           stratum=Stratum.QUANT, negative_marking=False)
        assert sum(shape.quota().values()) == n


def test_lesson_shape_is_one_question_per_level():
    """The owner's request, exactly: foundation, easy, medium, hard."""
    from xat_practice.items import LESSON_SHAPE

    q = LESSON_SHAPE.quota()
    assert q == {Level.FOUNDATION: 1, Level.EASY: 1,
                 Level.MEDIUM: 1, Level.HARD: 1}


def test_mock_shape_matches_the_verified_paper():
    from xat_practice.items import FULL_MOCK, QUANT_MOCK

    assert QUANT_MOCK.questions == 28
    assert QUANT_MOCK.negative_marking is True
    assert QUANT_MOCK.options == 5
    assert FULL_MOCK.questions == 75
    assert FULL_MOCK.minutes == 170
    assert sum(QUANT_MOCK.quota().values()) == 28


# ---------------------------------------------------------------------------
# end to end
# ---------------------------------------------------------------------------

def test_clean_20_item_paper_admits_all():
    """20 items whose structures hit the practice mix (2F 5E 8M 5H), on 20
    genuinely different reasoning shapes.

    The stems must differ in their WORDS, not just their digits -- `G6` strips
    digits on purpose, so 'Question number 3 about X' and 'Question number 7
    about X' are one question. MEASURED: the first version of this fixture
    admitted 1 of 20, and a second version admitted 15 of 20 with `G11`
    refusing five for over-quota. Both were the gates working correctly.
    """
    mix = ([Level.FOUNDATION] * 2 + [Level.EASY] * 5
           + [Level.MEDIUM] * 8 + [Level.HARD] * 5)
    items = [at_level(lv, i) for i, lv in enumerate(mix)]
    res = run(items)
    assert len(res.admitted) == 20, (
        f"admitted {len(res.admitted)}/20; refusals: "
        f"{ {r.gate: r.detail for r in res.refusals} }"
    )
    assert res.refusal_rate == 0.0


def test_g6_rejects_a_degenerate_20_item_fixture():
    """The counter-test for the test above, so the fixture cannot silently
    regress into 20 copies of one question."""
    items = [quant_item(id=f"q{i}", stem=f"Question number {i} about shapes")
             for i in range(20)]
    res = run(items)
    assert len(res.admitted) < 20
    assert any(r.gate == "G6_stem_distinctness" for r in res.refusals)


def test_g11_refuses_an_over_quota_paper():
    """The mix gate drops the over-quota item; it does not pad and it does not
    silently keep them all.

    10 items, not 5: `G11` now applies only at or above
    `MIX_ENFORCEMENT_FLOOR` (8), because apportioning the 20-item paper mix down
    to a lesson dropped the hard rung. MEASURED -- the 3-item version of this
    test passed for the wrong reason before the floor existed.
    """
    items = [at_level(Level.MEDIUM, i) for i in range(10)]
    res = run(items)
    assert len(res.admitted) < 10
    assert any(r.gate == "G11_mix_within_tolerance" for r in res.refusals)


_DISTINCT_STEMS = (
    "A shopkeeper marks an article above cost and then allows a discount",
    "Two pipes can fill a tank independently in differing numbers of hours",
    "The average speed for equal distances differs from the mean of speeds",
    "A train crosses a pole while another train crosses a platform",
    "Successive percentage changes do not combine by simple addition",
    "A geometric progression has a fractional common ratio in this case",
    "Two tangents drawn from an external point to a circle have equal length",
    "The power of a point equals the product of secant segments",
    "Opposite angles of a cyclic quadrilateral are supplementary",
    "A quadratic with real roots has a discriminant that is non-negative",
    "The largest integer dividing both numbers is their highest common factor",
    "A mix of two ingredients in a fixed ratio is sold at a certain price",
    "Partnership profit is shared in the ratio of capital and time",
    "The area of a triangle scales with the square of a similarity ratio",
    "An angle bisector divides the opposite side in the ratio of adjacent sides",
    "Compound interest with annual instalments differs from simple interest",
    "A number leaves the same remainder when divided by two distinct divisors",
    "The range of a quadratic function is bounded below by its vertex",
    "The number of integers satisfying a bound is counted inclusively",
    "A Venn diagram of two circles counts a union and an intersection",
)


def test_refusals_never_mutate_admitted():
    """A refused item must not appear in the admitted set. Asserted directly
    because the reference shipped a bundle where it did."""
    res = run([quant_item(options=("100", "200", "999", "220", "1200"), key_index=2)])
    assert res.admitted == []
    assert all(r.item_id == "q1" for r in res.refusals)

