"""The gate suite.

THE RULE (reference project, AC-10): a check that has only ever been shown a
true statement is untested. Every gate below is exercised with a WRONG input
first, and that test is named after what it disproves. `test_G5_planted_wrong_key`
is the one that matters most: it plants a bad key and asserts the item is
REFUSED, because that exact defect shipped through all 19 gates in the reference
project and the bundle on disk still contains it.
"""

from __future__ import annotations

import dataclasses

import pytest

from xat_practice import lesson1
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
)
from xat_practice.solver import SOLVER, Failure, Verdict
from xat_practice.syllabus import POPULATION, QUESTIONS_PER_PAPER, TOPICS, Stratum

# ---------------------------------------------------------------------------
# fixtures: one clean item per stratum
# ---------------------------------------------------------------------------

#: The real arithmetic of each wrong move in the fixture below: 1,000 at 10% for
#: 2 years, so the interest is 200. MEASURED 2026-10-02: `_distractors` used to
#: emit placeholder texts "0".."3" that appeared in NO option list, so every gate
#: test that built a paper was quietly carrying distractors nobody could match to
#: an option -- the same class of defect G16 exists to refuse.
_CAUSES = {
    "100": "1000*10*1/100",          # the time skimmed to one year
    "2,000": "1000*10*2/10",         # the /100 became a /10
    "220": "1000*11*2/100",          # the rate applied to the amount
    "1,200": "1000 + 1000*10*2/100",  # the amount returned, not the interest
}


def _distractors(options: tuple[str, ...] = (), key_index: int = 1,
                 real: int | None = None) -> tuple[Distractor, ...]:
    """One distractor per non-key option, each with the arithmetic that makes it.

    Where the cause is known from the scenario it is the REAL expression. Where a
    test has overridden the options with abstract strings, `produces` falls back to
    the option's own value -- which makes G16 inert for that test and is stated
    here rather than hidden, because a test about G5 is not a test about G16."""
    pool = options or ("100", "2,000", "220", "1,200")
    out = []
    for i, text in enumerate(pool):
        if i == key_index:
            continue
        # `real` sets how many count as real near-misses, which is what makes
        # each level derive to its own tier. All four still carry `produces`,
        # because G16 asks for the arithmetic of EVERY distractor, not only the
        # plausible ones -- an implausible option still needs to be reachable.
        is_real = True if real is None else (len(out) < real)
        out.append(Distractor(text=text, misconception=f"the move behind {text}",
                              is_real_near_miss=is_real,
                              produces=_CAUSES.get(text, text)))
    return tuple(out)


def quant_item(**kw) -> Item:
    base = dict(
        id="q1",
        subtopic_id="pl_int:simple-interest",
        stratum=Stratum.QUANT,
        stem="What simple interest does 1000 earn at 10% for 2 years?",
        # 2,000 replaces a former 210. MEASURED 2026-10-02: 210 had NO plausible
        # cause from 1000 at 10% for 2 years, which is the exact defect G16
        # exists to catch -- and this fixture, the one every gate test builds on,
        # was carrying it. Each option below now equals a real wrong move.
        options=("100", "200", "2,000", "220", "1200"),
        key_index=1,
        option_values=("100", "200", "2000", "220", "1200"),
        derivation="1000*10*2/100",
        derivation_steps=2,
        needs_substitution=False,
        insight_required=False,
    )
    base.update(kw)
    # The distractors are built from the FINAL option list, so they always name a
    # real option. Built inside the literal they would see a half-defined dict.
    if "distractors" not in kw:
        base["distractors"] = _distractors(base["options"], base["key_index"])
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
        derivation_steps=1,
        needs_substitution=False,
        insight_required=False,
        enumeration_size=12,
    )
    base.update(kw)
    # The distractors are built from the FINAL option list, so they always name a
    # real option. Built inside the literal they would see a half-defined dict.
    if "distractors" not in kw:
        base["distractors"] = _distractors(base["options"], base["key_index"])
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
        derivation_steps=0,
        needs_substitution=False,
        insight_required=False,
    )
    base.update(kw)
    # The distractors are built from the FINAL option list, so they always name a
    # real option. Built inside the literal they would see a half-defined dict.
    if "distractors" not in kw:
        base["distractors"] = _distractors(base["options"], base["key_index"])
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
    res = run([quant_item(options=("100", "200", "2,000", "220"))])
    assert any(r.gate == "G1_options" for r in res.refusals)


def test_G3_all_of_the_above_is_refused():
    res = run([quant_item(options=("100", "200", "2,000", "All of the above", "x"))])
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


def _rotate_key(item: Item, to_index: int) -> Item:
    """Move the key to `to_index`, keeping `options` and `option_values` in step.

    The rotation is the whole point: `key_index` alone can be moved without
    touching the options, but then the key no longer names the value the solver
    derives and G5 refuses the item. Rotating both together produces an item that
    is CORRECT at a chosen position, which is what a real paper is.
    """
    import dataclasses

    n = len(item.options)
    to_index %= n
    src = (item.key_index - to_index) % n
    opts = item.options[src:] + item.options[:src]
    vals = item.option_values[src:] + item.option_values[:src]
    return dataclasses.replace(item, options=opts, option_values=vals,
                               key_index=to_index)


#: Twenty DISTINCT digit-masked derivation shapes that all evaluate to 200.
#:
#: MEASURED 2026-10-02. Every paper fixture in this file previously carried the
#: single derivation `1000*10*2/100`, so the "clean 20-item paper" was twenty
#: copies of one piece of arithmetic -- and `G17_derivation_shape_distinct`
#: refused the whole set, correctly. A fixture for a paper that admits cleanly
#: has to BE a paper of distinct reasoning shapes.
_SHAPES: tuple[str, ...] = (
    "1000*10*2/100", "(1000*2/100)*10", "1000*(10*2/100)", "(10*1000*2)/100",
    "1000*10*(2/100)", "2000*10/100*1", "(2000/100)*10", "(1000/100)*10*2",
    "1000/100*10*2", "1000*20/10/10", "(1000*20/10)/10", "1000*10*2/100/1",
    "1*1000*10*2/100", "(1000*10*2/100)+0", "(1000*10*2)/100*1",
    "1000*(10*(2/100))", "((1000*2)*10)/100", "1000*((10*2)/100)",
    "(1000*(10*2))/100", "1000*10*2/(100*1)",
)


def at_level(level: Level, i: int) -> Item:
    """An item whose STRUCTURE is the recipe for `level`. This is the only
    sanctioned way to build a fixture at a target level.

    Two things are deliberate and both came from G15 and G16.

    The key is ROTATED to `1 + i`, so a fixture set has the key spread of a real
    paper. MEASURED 2026-10-02: every paper fixture in this file put the key at
    the same index, so `always answer B` scored 20 of 20 -- the identical defect
    Lesson 1 shipped, living in the tests meant to catch it.

    The distractors are derived from the ROTATED option list, after the rotation,
    never before it. They must name real options and carry the arithmetic that
    produces them (`G16`), and a rotation reorders the options, so building them
    first silently orphans them -- which is exactly what `G12` and `G16` caught."""
    r = LEVEL_RECIPES[level]
    item = _rotate_key(quant_item(
        id=f"{level.value}-{i}",
        stem=_DISTINCT_STEMS[i],
        derivation=_SHAPES[i % len(_SHAPES)],
        derivation_steps=int(r["derivation_steps"]),      # type: ignore[call-overload]
        needs_substitution=bool(r["needs_substitution"]), # type: ignore[call-overload]
        insight_required=bool(r["insight_required"]),     # type: ignore[call-overload]
        distractors=(),
    ), 1 + i)
    return dataclasses.replace(
        item,
        distractors=_distractors(item.options, item.key_index,
                                real=int(r["real_near_misses"])),
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
    # G15: every key in the same position. MEASURED 2026-10-02: Lesson 1 was
    # exactly this and all fourteen other gates passed it -- 'always A' scored
    # 4 of 4. The reachability input is the defect that shipped.
    fire(*[_rotate_key(at_level(LEVEL_ORDER[i], i), 0) for i in range(4)])
    # G16: a distractor whose arithmetic is absent. MEASURED 2026-10-02: four of
    # Lesson 1's options were digit transpositions of the move their own
    # explanation named, and every gate passed them.
    import dataclasses as _dc

    from xat_practice.items import Distractor as _D

    unproven = _dc.replace(
        quant_item(),
        distractors=tuple(_D(text=str(i), misconception=f"m{i}",
                             is_real_near_miss=True) for i in range(4)))
    fire(unproven)

    # G17: two items with the SAME digit-masked derivation. MEASURED 2026-10-02:
    # Lesson 1's L1-E and L1-H both reduced to `N + N*N*N/N` and every other gate
    # passed them, because G6 fingerprints the STEM and nothing looked at the
    # arithmetic.
    fire(_rotate_key(quant_item(id="same-shape-a", stem="Stem alpha one"), 0),
         _rotate_key(quant_item(id="same-shape-b", stem="Stem beta two"), 1))
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



# ---------------------------------------------------------------------------
# G15 -- the key position must not be the answer
# ---------------------------------------------------------------------------
# MEASURED 2026-10-02, from the owner: "here all question answer A, which is not
# good." All four of Lesson 1's keys sat at index 0. Answering A four times
# scored 4 of 4 -- +4.00 of a possible +4.00, full marks, having read nothing.
# Every one of the fourteen existing gates passed it: G2 checks the key is IN
# RANGE, and nothing in the module asked where it SAT.

def test_a_fixed_letter_cannot_score_the_paper():
    """The exploit itself, as a test.

    Written first and against the defect that shipped, not derived from the
    gate's own arithmetic."""
    from xat_practice.gates import fixed_letter_best

    exploited = [_rotate_key(at_level(LEVEL_ORDER[i], i), 0)
                 for i in range(4)]
    letter, score, hits = fixed_letter_best(exploited)
    assert letter == 0
    assert hits == 4
    assert score == pytest.approx(4.0), "the exploit must still score 4.0"

    res = run(exploited)
    assert any(r.gate == "G15_key_not_predictable" for r in res.refusals), (
        "a paper where one letter scores full marks was ADMITTED"
    )
    assert res.admitted == [], (
        "G15 refused but the items were still admitted. A refusal that does not "
        "remove the item is a comment."
    )


def test_the_lesson_is_no_longer_exploitable():
    """And the fix, on the real lesson."""
    from xat_practice.gates import fixed_letter_best

    _letter, score, hits = fixed_letter_best(list(lesson1.LESSON))
    assert hits < 2, (
        f"one letter is still the answer to {hits} of 4 questions (positions "
        f"{[it.key_index for it in lesson1.LESSON]})"
    )
    assert score < 0.4, f"best fixed letter still scores {score:+.2f}"


def test_the_ceiling_is_derived_from_random_guessing_being_worth_nothing():
    """The threshold has a reason, and the reason is a number in this module.

    Random guessing on five options at -0.25 has EV exactly 0.0 (D3,
    `test_guessing_5_options_is_exactly_score_neutral`). So a fixed-letter
    strategy worth more than 10% of the marks is paying a learner for not
    retrieving, which is the one thing this product exists to prevent."""
    from xat_practice.gates import KEY_EXPLOIT_CEILING

    assert KEY_EXPLOIT_CEILING == 0.10
    assert KEY_EXPLOIT_CEILING > 0, (
        "a ceiling of zero would refuse any real XAT key distribution; XLRI "
        "does not publish one, and 5-6 keys per letter over 28 items is normal"
    )


def test_g15_is_scored_with_the_real_marking_scheme():
    """`fixed_letter_best` is arithmetic, so it gets its own arithmetic test.

    MEASURED on the shipped defect: 4 hits at -0.25 for the other 0 is +4.00.
    A gate that estimated this would be a gate that could be fooled by a
    rounding choice."""
    from xat_practice.gates import fixed_letter_best

    # four items, keys A,A,B,B
    items = [quant_item(id=f"m{i}", key_index=i % 2) for i in range(4)]
    letter, score, hits = fixed_letter_best(items)
    assert letter == 0 and hits == 2
    assert score == pytest.approx(2 * 1.0 + 2 * -0.25)


def test_g15_does_not_fire_on_a_normal_key_spread():
    """A guard that fires on everything is not a guard."""
    items = [quant_item(id=f"n{i}", key_index=i % 5) for i in range(20)]
    res = run(items)
    assert not any(r.gate == "G15_key_not_predictable" for r in res.refusals), (
        "a uniform key spread was refused"
    )


def test_g15_runs_after_the_mix_is_enforced():
    """Ordering is normative. It must judge the set that will be SERVED.

    If it judged the full input instead, it could pass a paper that `G11` had
    already thinned down to a fixed-letter remainder."""
    from xat_practice import gates

    src = __import__("inspect").getsource(gates.run)
    assert src.index("_enforce_mix") < src.index("_refuse_predictable_keys"), (
        "G15 must run after G11, or it judges a set that is not the one served"
    )


# ---------------------------------------------------------------------------
# G16 -- a distractor must be produced by the move it names
# ---------------------------------------------------------------------------
# MEASURED 2026-10-02, from the key-auditor's audit of Lesson 1 and then from the
# test written to check its findings. Five options had an explanation that did
# not produce them; four were digit transpositions. Every one of them passed G8,
# G12, G13 and G5 -- those gates check that a distractor HAS a misconception, and
# not one of them asked whether the misconception PRODUCES the distractor.
#
# The owner asked for this to be HOUSEKEEPING rather than a manual agent pass,
# because 40 subtopics are coming and a manual pass does not survive contact with
# them. That is why `Distractor.produces` exists.

def test_g16_refuses_an_option_its_own_explanation_does_not_produce():
    """The historical defect, planted exactly as it shipped."""
    import dataclasses

    from xat_practice.items import Distractor

    item = quant_item(
        id="transposed",
        options=("100", "10,250", "2,000", "220", "1200"),
        option_values=("100", "10250", "2000", "220", "1200"),
        key_index=1,
        derivation="1000*10*2/100",
        distractors=(
            # the move named is 10,500; the option reads 10,250
            Distractor(text="10,250", misconception="the time count dropped",
                       is_real_near_miss=True, produces="10000 + 10000*5*1/100"),
            Distractor(text="100", misconception="m", is_real_near_miss=True,
                       produces="1000*10*1/100"),
            Distractor(text="2,000", misconception="m2", is_real_near_miss=True,
                       produces="1000*10*2/10"),
            Distractor(text="220", misconception="m3", is_real_near_miss=True,
                       produces="1000*11*2/100"),
        ),
    )
    res = run([item])
    fired = [r for r in res.refusals if r.gate == "G16_distractor_produces_its_option"]
    assert fired, "a digit transposition in an option was ADMITTED"
    assert "10250" in fired[0].detail and "10500" in fired[0].detail, (
        "the refusal must name BOTH numbers, or the author cannot tell which one "
        f"is wrong: {fired[0].detail}"
    )
    assert res.admitted == []
    assert dataclasses  # keep the import honest


def test_g16_refuses_a_distractor_with_no_arithmetic_at_all():
    """`produces = None` means UNPROVEN, and on a quantitative item that is a
    refusal rather than a skip.

    A gate that skips what it cannot check is a gate that reports a pass it did
    not earn -- the same defect as the coverage floor that read eight files out
    of nine."""
    from xat_practice.items import Distractor

    item = quant_item(
        id="unproven",
        distractors=tuple(Distractor(text=str(i), misconception=f"m{i}",
                                     is_real_near_miss=True)
                          for i in range(4)))
    res = run([item])
    assert any(r.gate == "G16_distractor_produces_its_option"
               for r in res.refusals), (
        "a distractor with no machine-checkable cause was admitted. Four of them "
        "in Lesson 1 were digit transpositions of their own explanation."
    )


def test_g16_does_not_run_on_items_with_no_arithmetic():
    """A LOGIC or JUDGEMENT item has no `option_values`, so a distractor there is
    refuted by a counterexample, not by a number. A rule with no meaning is not a
    rule."""
    assert not any(r.gate == "G16_distractor_produces_its_option"
                   for r in run([logic_item()]).refusals)


def test_every_distractor_in_the_lesson_is_machine_verified():
    """The housekeeping property the owner asked for: no distractor anywhere in
    the built lesson can carry an unverifiable cause."""
    from xat_practice import lesson1

    for it in lesson1.LESSON:
        for d in it.distractors:
            assert d.produces is not None, (
                f"{it.id}: {d.text!r} has no `produces`, so its cause is prose "
                f"that no gate can check"
            )


def test_g16_does_not_claim_to_check_plausibility():
    """The honest boundary, restated against a FRESH example.

    MEASURED 2026-10-02: the original example here was L1-M's `1440*100/18`, which
    WAS unreachable -- nothing in that item produced an 18. L1-M has since been
    rebuilt and its collapse denominator is now 15 + 3 = 18, genuinely reachable.

    So the example had to be replaced, and the point is unchanged and is now
    proven on a live case rather than a remembered one: **an expression can be
    arithmetically valid, can name a plausible-looking pair of numbers, and still
    describe a mistake no learner makes.** G16 cannot see that, and no arithmetic
    check ever will. Plausibility stays `key-auditor`'s job."""
    from xat_practice import lesson1

    item = next(it for it in lesson1.LESSON if it.id == "L1-M")
    # Every distractor on the rebuilt item is reachable, which is the improvement.
    assert all(d.produces is not None for d in item.distractors)
    assert 15 + 3 == 18, "the collapse denominator is now genuinely reachable"
    res = run([item])
    assert not any(r.gate == "G16_distractor_produces_its_option"
                   for r in res.refusals), (
        "G16 must pass the /18 distractors -- the arithmetic is valid -- which is "
        "exactly why plausibility stays a key-auditor judgement"
    )


# ---------------------------------------------------------------------------
# G17 -- the ladder must add an OPERATION, not a number
# ---------------------------------------------------------------------------
# MEASURED 2026-10-02, by `level-auditor` and `question-setter` independently.
# Lesson 1's L1-E and L1-H both digit-masked to `N + N*N*N/N`. Changing only
# L1-H's flags and nothing a learner sees dropped it 7.40 -> 2.50, the EASY tier,
# so 66% of the hard item's difficulty was a declared flag with nothing in the
# derivation to prove it. Every other gate passed it: G7's `claimed_level` is
# None on all four items, and G6 fingerprints the STEM, not the arithmetic.

def test_derivation_shape_masks_digits_and_keeps_the_structure():
    from xat_practice.gates import derivation_shape

    assert derivation_shape("1000*10*2/100") == "N*N*N/N"
    assert derivation_shape("10000 + 10000*5*2/100") == "N + N*N*N/N"
    assert derivation_shape("1000*10*2/100") == derivation_shape("5000*20*2/100")


def test_G17_refuses_two_items_that_reduce_to_the_same_arithmetic():
    from xat_practice.gates import derivation_shape

    assert derivation_shape(
        "10000 + 10000*5*2/100") == derivation_shape("12000 + 12000*10*2/100")
    items = [
        _rotate_key(quant_item(id="easy", stem="An easy item about alpha"), 1),
        _rotate_key(quant_item(id="hard", stem="A hard item about beta"), 2),
    ]
    res = run(items)
    assert any(r.gate == "G17_derivation_shape_distinct" for r in res.refusals), (
        "two items with the same arithmetic were admitted; one of them is not a "
        "new rung, it is the same question with different numbers"
    )
    assert res.admitted == []


def test_G17_is_satisfied_by_the_real_lesson():
    """Lesson 1 now scores 4 of 4. It was 3 of 4 this morning."""
    from xat_practice.gates import derivation_shape
    from xat_practice.lesson1 import LESSON

    shapes = [derivation_shape(i.derivation) for i in LESSON]
    assert len(set(shapes)) == 4, f"only {len(set(shapes))} distinct shapes: {shapes}"


def test_G17_does_not_claim_to_verify_the_difficulty_flags():
    """The honest boundary, pinned so it cannot be forgotten.

    `derive_level` charges `steps x 0.85 + 1.2 for substitution + 2.0 for
    insight + 0.2 per near-miss`. So the FLAGS ARE THE SCORE -- and they are
    declarations about how many reasoning moves a human makes, not properties of a
    string. `1000*10*2/100` has three operators and Lesson 1's FOUNDATION rung
    correctly claims ONE step, because "steps" means reasoning moves.

    So G17 proves two items are not the same arithmetic. It cannot prove a flag
    is true. Asserted here because a gate that gets credited with more than it
    does is worse than no gate."""
    from xat_practice.items import LEVEL_RECIPES, Level, derive_level
    from xat_practice.lesson1 import FOUNDATION

    assert derive_level(FOUNDATION).score == 1.25
    assert FOUNDATION.derivation.count("*") + FOUNDATION.derivation.count("/") == 3, (
        "three operators, one claimed step -- so step count is NOT operator count, "
        "and no arithmetic check can verify the flag"
    )
    assert LEVEL_RECIPES[Level.HARD]["insight_required"] is True


def test_both_paper_level_gates_report_before_the_admitted_list_is_cleared():
    """MEASURED: G15 cleared `res.admitted` and the gates after it were left with
    nothing to judge, so a second paper-level defect was invisible. That is a
    defect being hidden by an unrelated one, and it made G17 unreachable."""
    items = [
        # keys all on one letter -> G15
        _rotate_key(quant_item(id=f"k{i}", stem=_DISTINCT_STEMS[i]), 1)
        for i in range(3)
    ]
    res = run(items)
    gates = {r.gate for r in res.refusals}
    assert "G15_key_not_predictable" in gates
    assert "G17_derivation_shape_distinct" in gates, (
        f"only {gates} reported; two independent paper-level defects must both be "
        "visible, or an author fixes one and believes the paper is clean"
    )
    assert res.admitted == []
