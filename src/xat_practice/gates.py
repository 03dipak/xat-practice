"""The gate. LLM decides what a question MIGHT say. Code decides WHETHER it is
admissible. No exceptions.

Gate ids are stable and referenced by name in every doc. Renumbering one is a
breaking change; retiring one needs a line in DECISIONS.md saying what it used
to catch, because the reference project's real lesson was that a gate nobody
remembers the purpose of is a gate nobody dares remove.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import sympy as sp

from .items import DifficultyReport, Item, Level, derive_level
from .solver import SOLVER, Check
from .syllabus import Stratum

GATE_IDS = (
    "G1_options", "G2_key_in_range", "G3_no_all_of_above", "G4_distinct_options",
    "G5_key_grounded", "G6_stem_distinctness", "G7_level_agrees",
    "G8_near_miss_distractors", "G9_calc_budget", "G10_stratum_shape",
    "G11_mix_within_tolerance", "G12_misconceptions_named", "G13_no_leak",
    "G14_option_value_matches_label", "G15_key_not_predictable",
    "G16_distractor_produces_its_option",
)


@dataclass(frozen=True, slots=True)
class Refusal:
    gate: str
    item_id: str
    detail: str


@dataclass(slots=True)
class GateResult:
    admitted: list[Item] = field(default_factory=list)
    refusals: list[Refusal] = field(default_factory=list)
    reports: dict[str, DifficultyReport] = field(default_factory=dict)
    checks: dict[str, Check] = field(default_factory=dict)

    @property
    def refusal_rate(self) -> float:
        total = len(self.admitted) + len(self.refusals)
        return round(len(self.refusals) / total, 4) if total else 0.0

    def by_gate(self) -> dict[str, int]:
        out: dict[str, int] = {g: 0 for g in GATE_IDS}
        for r in self.refusals:
            out[r.gate] = out.get(r.gate, 0) + 1
        return out


def _stem_fingerprint(stem: str) -> str:
    """Digits and lowercase letters only.

    Two items asking 'what is 15% of 480?' and 'what is 20% of 360?' are the
    SAME question twice, and both pass a naive pairwise string comparison.
    Numbers are the part of a quant stem that varies without changing the
    reasoning, so they are removed before comparing.
    """
    return "".join(c for c in stem.lower() if c.isalpha())


def _as_number(expr: str | float) -> float | None:
    """Evaluate an arithmetic expression to a number, or None if it is not one.

    Returns None rather than raising: a `produces` that does not parse is a
    missing proof, and G16's caller already refuses an absent one. A gate that
    raises is a gate that is not run."""
    import sympy

    if isinstance(expr, (int, float)):
        return float(expr)
    try:
        value = sympy.sympify(expr)
    except (sympy.SympifyError, TypeError, SyntaxError):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _value_visible_in_label(label: str, value: str) -> bool:
    """Is the checked number actually visible in the option the learner reads?

    `G14` exists because `sympify('14,400')` returns the TUPLE `(14, 400)` -- a
    thousands separator turns one amount into a pair and slips PAST the parse
    check instead of being caught by it. So the gate cannot rely on the solver
    to complain.

    It must also not fire on a number written two ways. The first version
    compared the label's digit run against the value string, which REFUSED
    `2 : 3` against `2/3` -- the same ratio in the notation XAT actually uses.
    So both sides are reduced to a normalised decimal and compared as numbers,
    and a ratio is compared component-wise.

    Returns True when the value cannot be read as a number at all, because a
    prose option has no number to be inconsistent with and inventing a check
    for it would be theatre.
    """
    try:
        parsed = sp.sympify(value, rational=True)
    except (sp.SympifyError, SyntaxError, TypeError):
        # Not an expression at all. A prose option ("Cannot be determined") has
        # no number to be inconsistent with, so there is nothing to check and
        # inventing a check for it would be theatre.
        return True

    if isinstance(parsed, sp.Tuple) or not isinstance(parsed, sp.Expr):
        # It PARSED, but as something that is not a single number -- most often
        # the tuple `sympify('14,400')` returns because of a thousands
        # separator. A value that is not a scalar cannot be the value of a
        # single option, so this is a REFUSAL. Distinguishing this from the
        # branch above is the whole point: one is prose and the other is a
        # number-shaped mistake, and only the second is a defect.
        return False

    try:
        want = sp.nsimplify(parsed)
    except (sp.SympifyError, SyntaxError, TypeError, AttributeError):
        # AttributeError is not decoration: `nsimplify` calls `.evalf()` on
        # whatever `sympify` returned, and some expressions have no `evalf`.
        # Measured: this function raised on the `(14, 400)` input and took the
        # gate down with it. This function must never raise -- a gate that
        # raises has silently become a gate that is not run.
        return False

    if getattr(want, "is_Rational", False) and want.is_Rational:
        # A plain number: every digit group in the label must appear in the
        # value, ignoring separators and the currency symbol.
        target = f"{sp.nsimplify(want)}"
        stripped = target.replace(",", "").lstrip("-")
        groups = [g for g in "".join(
            c if c.isdigit() else " " for c in label).split() if g]
        return all(g.lstrip("0") in stripped or g in stripped
                   for g in groups)

    # A ratio or surd: fall back to comparing the two sides numerically, which
    # accepts `2 : 3`, `2/3` and `2:3` as the same value.
    nums = "".join(c if c.isdigit() else " " for c in label).split()
    if len(nums) == 2:
        try:
            shown = sp.Rational(int(nums[0]), int(nums[1]))
        except (ValueError, ZeroDivisionError):
            return True
        return bool(sp.simplify(shown - want) == 0)
    return True


def run(items: list[Item]) -> GateResult:
    res = GateResult()
    seen: dict[str, str] = {}

    for it in items:
        # Bound as a default argument, not read from the enclosing scope. Ruff's
        # B023 is right that a closure over a loop variable is a bug waiting to
        # happen, and the fix is to not have the closure at all where possible.
        def refuse(gate: str, detail: str, _id: str = it.id) -> None:
            res.refusals.append(Refusal(gate, _id, detail))

        if it.option_count != 5:
            refuse("G1_options",
                   f"{it.option_count} options. XAT 2026 has 5; a 4-option item "
                   f"is a CAT habit and changes the guessing equilibrium.")
        if not 0 <= it.key_index < it.option_count:
            refuse("G2_key_in_range",
                   f"key index {it.key_index} outside 0..{it.option_count - 1}")
            # SHORT-CIRCUIT. The solver reads `it.key_text`, which indexes the
            # options tuple, so an out-of-range key raised IndexError inside
            # `SOLVER.verify` and took the whole run down before G2 could
            # refuse the item. MEASURED. A gate that crashes on bad input is
            # not a gate: it is a way to lose a paper.
        else:
            check = SOLVER.verify(stratum=it.stratum, derivation=it.derivation,
                                  keyed_value=it.key_value,
                                  keys=list(it.options))
            res.checks[it.id] = check
            if not check.ok:
                refuse("G5_key_grounded", f"{check.failure}: {check.detail}")
        lowered = [o.strip().lower() for o in it.options]
        if any(o.startswith("all of the above") or o.startswith("none of the above")
               for o in lowered):
            refuse("G3_no_all_of_above",
                   "'all/none of the above' is eliminable without reading the "
                   "stem. It measures pattern-matching, not the concept.")
        if len(set(lowered)) != len(lowered):
            dupes = [o for o in lowered if lowered.count(o) > 1]
            refuse("G4_distinct_options", f"duplicate options: {sorted(set(dupes))}")

        fp = _stem_fingerprint(it.stem)
        if fp in seen:
            refuse("G6_stem_distinctness",
                   f"same reasoning shape as {seen[fp]} -- only the numbers "
                   f"differ, so this counts one question twice")
        else:
            seen[fp] = it.id

        rep = derive_level(it)
        res.reports[it.id] = rep
        if rep.verdict == "CLAIM_MISMATCH":
            refuse("G7_level_agrees",
                   f"drafter claimed {it.claimed_level}, structure derives "
                   f"{rep.level} (score {rep.score}, drivers: "
                   f"{'; '.join(rep.drivers)})")

        if it.stratum is Stratum.QUANT:
            real = sum(d.is_real_near_miss for d in it.distractors)
            if real < 2:
                refuse("G8_near_miss_distractors",
                       f"only {real} of 4 distractors is a real computed "
                       f"near-miss; the rest are arbitrary numbers, so the "
                       f"item measures guessing")

        if it.calculator_minutes > 2.0:
            refuse("G9_calc_budget",
                   f"{it.calculator_minutes:.1f} min exceeds the 2-minute "
                   f"budget; XAT 2026 provides an on-screen calculator, so "
                   f"hand-computation difficulty is the wrong axis")

        # Only QUANT and JUDGEMENT are checked. LOGIC items legitimately carry a
        # derivation -- it is the enumeration `enumeration.py` re-runs -- so
        # folding all three strata into one comparison refused 100% of logic
        # items. MEASURED: G10 was unreachable-by-inversion before this fix.
        if it.stratum is Stratum.JUDGEMENT and it.derivation is not None:
            refuse("G10_stratum_shape",
                   "a judgement item carries a derivation; prose has no solver, "
                   "so a derivation here is a fabricated proof")
        if it.stratum is Stratum.QUANT and not it.derivation:
            refuse("G10_stratum_shape",
                   "a quant item carries no derivation, so its key cannot be "
                   "recomputed and cannot be vouched for")

        if len({d.misconception for d in it.distractors}) != len(it.distractors):
            refuse("G12_misconceptions_named",
                   "two distractors share a misconception name, so one of them "
                   "teaches nothing")
        if any(not d.misconception.strip() for d in it.distractors):
            refuse("G12_misconceptions_named", "a distractor has no named misconception")
        if len(it.distractors) != it.option_count - 1:
            refuse("G12_misconceptions_named",
                   f"{len(it.distractors)} distractors for "
                   f"{it.option_count - 1} wrong options")

        if any(k in it.stem for k in ("answer is", "correct option is", "key:")):
            refuse("G13_no_leak", "stem leaks its own key")

        # G14. The value the solver checked must be the value the learner will
        # read. Without this, an item can pass G5 on a value that its own label
        # contradicts, and the learner is marked against arithmetic they never
        # saw. MEASURED: '14,400' does not fail to parse -- sympify returns the
        # TUPLE (14, 400) -- so a thousands separator slips past the parse check
        # rather than being caught.
        # Skip when there are no values. `zip(..., strict=True)` against an
        # empty `option_values` raised ValueError and took the run down on
        # every LOGIC and JUDGEMENT item -- MEASURED, and the third
        # crash-on-bad-input defect in this module. A JUDGEMENT item has no
        # arithmetic to be inconsistent with, so there is nothing to check.
        for idx, (label, value) in enumerate(
            zip(it.options, it.option_values, strict=True) if it.option_values
            else ()
        ):
            if not _value_visible_in_label(label, value):
                refuse("G14_option_value_matches_label",
                       f"option {idx} is labelled {label!r} but its value is "
                       f"{value!r}; the learner would be marked against a "
                       f"number they cannot see in the option")

        # G16. Every distractor must equal what its own named mistake computes
        # to.
        #
        # MEASURED 2026-10-02. Four of Lesson 1's options were digit
        # transpositions of their own stated cause -- Rs 10,250 beside an
        # explanation saying 10,000 x 5 / 100, which is 10,500 -- and a fifth
        # claimed a cause that is arithmetically impossible. All five passed G8,
        # G12, G13 and G5, because those gates check that a distractor HAS a
        # misconception and NOT that the misconception PRODUCES the distractor.
        #
        # Skipped where there is no arithmetic to check: a LOGIC or JUDGEMENT
        # item has no `option_values`, and a distractor there is refuted by a
        # counterexample rather than by a number. Requiring `produces` on those
        # would be a rule with no meaning.
        if it.option_values:
            for d in it.distractors:
                if d.produces is None:
                    refuse("G16_distractor_produces_its_option",
                           f"the distractor {d.text!r} has no `produces`, so the "
                           f"move its misconception names is not machine-checked. "
                           f"Give it the arithmetic, or drop the option: a trap "
                           f"nobody can reproduce is a trap nobody has verified.")
                    continue
                shown = (it.options.index(d.text) if d.text in it.options else -1)
                if shown < 0:
                    refuse("G16_distractor_produces_its_option",
                           f"the distractor {d.text!r} is not among the options")
                    continue
                want = _as_number(it.option_values[shown])
                got = _as_number(d.produces)
                if want is None or got is None:
                    continue
                if abs(got - want) > 1e-9:
                    refuse("G16_distractor_produces_its_option",
                           f"the option {d.text!r} is {want:g} but the move its "
                           f"own misconception names, {d.produces!r}, computes "
                           f"{got:g}. Either the option or the explanation is "
                           f"wrong, and a learner following the lesson cannot "
                           f"reconcile them.")

        blocked = {r.gate for r in res.refusals if r.item_id == it.id}
        if not blocked:
            res.admitted.append(it)

    res.admitted = _enforce_mix(res, items)
    _refuse_predictable_keys(res, res.admitted)
    return res


#: The most a FIXED-LETTER strategy may be worth, as a fraction of the marks on
#: the paper.
#:
#: The reasoning is already in the module's own numbers. Random guessing on five
#: options at -0.25 has expected value **exactly 0.0** -- `+1/5 + 4/5 x -0.25`,
#: measured in `guess_ev_report` and quoted in D3. So a paper in which picking one
#: letter without reading anything is worth more than 10% of the marks is a paper
#: that pays for NOT retrieving, and the whole product is built to prevent that.
KEY_EXPLOIT_CEILING = 0.10


def fixed_letter_best(items: list[Item]) -> tuple[int, float, int]:
    """The best always-the-same-letter strategy: (letter, score, correct).

    Measured with the real marking scheme, not approximated. One bad fact about
    a paper is always worth more than any number of good ones, and that is
    exactly the kind of fact that survives a review nobody thought to ask the
    right question of."""
    if not items:
        return -1, 0.0, 0
    best_letter, best_score, best_hits = -1, float("-inf"), 0
    for letter in range(len(items[0].options)):
        hits = sum(1 for it in items if it.key_index == letter)
        score = hits * 1.0 + (len(items) - hits) * -0.25
        if score > best_score:
            best_letter, best_score, best_hits = letter, score, hits
    return best_letter, best_score, best_hits


def _refuse_predictable_keys(res: GateResult, items: list[Item]) -> None:
    """G15 -- refuse a set whose key positions reward not reading the stem.

    MEASURED 2026-10-02, from the owner: "here all question answer A, which is
    not good." Correct, and worse than it looks. All four of Lesson 1's keys sat
    at index 0, so a learner who answered A four times scored **4 of 4** --
    `+4.00` of a possible `+4.00`, full marks, having read nothing.

    **All fourteen existing gates passed it.** `G2` checks the key is IN RANGE.
    Nothing checked where it SAT. Every gate in this module looks at one item, or
    at a level mix, and none of them asks the only question that matters about a
    set of keys: can the position alone score?

    The reason it survived is worth recording. The keys were not chosen to be
    predictable; every author simply wrote the correct answer first and listed
    the distractors after it. Four items, same habit, same result -- and the
    result was a paper that measures nothing.

    Ordering matters and is normative: this runs AFTER the per-item loop and
    after `G11`, so it sees the set that will actually be served. Refusing on the
    full input instead would pass a paper that `G11` had already thinned.
    """
    if len(items) < 2:
        return
    letter, score, hits = fixed_letter_best(items)
    ceiling = KEY_EXPLOIT_CEILING * len(items)
    if score <= ceiling:
        return
    wrong = sum(1 for it in items if it.key_index != letter)
    res.refusals.append(Refusal(
        gate="G15_key_not_predictable",
        item_id=items[0].id,
        detail=(
            f"answering {'ABCDE'[letter]} on every question scores {score:+.2f} "
            f"of a possible {float(len(items)):+.2f} ({hits} correct, {wrong} "
            f"wrong), above the {ceiling:.2f} ceiling -- so the KEY POSITION "
            f"alone scores. Positions: {[it.key_index for it in items]}. "
            f"Random guessing is worth 0.0000, so this paper pays for not "
            f"reading."
        ),
    ))
    res.admitted = []


#: Below this size a set is a LESSON, not a paper, and `G11` must not run.
#:
#: MEASURED: `G11`'s quota for 4 items came out `{foundation 1, easy 1, medium 1,
#: hard 0}` -- it apportions the PAPER mix (10/25/40/25) down to a lesson, and
#: the hard item was dropped by a gate whose whole job is to shape a paper. That
#: is the product's central claim -- four levels, the hard one reachable from the
#: foundation one -- deleted by a paper-level rule. `LESSON_SHAPE.quota()` is the
#: authority on a lesson's mix and it says 1/1/1/1.
MIX_ENFORCEMENT_FLOOR = 8


def _enforce_mix(res: GateResult, items: list[Item]) -> list[Item]:
    """Drop the OVER-quota items, keeping the lower tiers.

    `D3`: a paper that cannot fill its quota is SHORT, never padded. And when
    two items must go, the hard one is kept -- because a learner who cannot
    reach the hard item has not understood the foundation item, and the paper
    already contains enough easy items to send that message.
    """
    from .items import LEVEL_ORDER

    if len(items) < MIX_ENFORCEMENT_FLOOR:
        return res.admitted

    quota = {Level.FOUNDATION: max(1, round(0.10 * max(len(items), 1))),
             Level.EASY: max(1, round(0.25 * max(len(items), 1))),
             Level.MEDIUM: max(1, round(0.40 * max(len(items), 1)))}
    quota[Level.HARD] = max(0, len(items) - sum(quota.values()))
    if quota[Level.HARD] < 0:
        quota[Level.HARD] = 0

    kept: list[Item] = []
    counts = dict.fromkeys(LEVEL_ORDER, 0)
    for lv in LEVEL_ORDER:  # lowest first: the head of the ladder is kept
        for it in res.admitted:
            rep = res.reports[it.id]
            if rep.level is lv and counts[lv] < quota[lv]:
                kept.append(it)
                counts[lv] += 1
            elif rep.level is lv:
                # Over quota. `it` was never appended, so there is nothing to
                # remove -- the first version of this branch also called
                # `kept.remove(it)` defensively, which would raise on the
                # second over-quota item at a level rather than on the first.
                res.refusals.append(
                    Refusal("G11_mix_within_tolerance", it.id,
                            f"{lv} over quota ({counts[lv]}/{quota[lv]}); the "
                            f"paper keeps the lower rungs and drops this one"))
    return kept


def guess_ev_report() -> dict[str, float]:
    from .items import expected_ev

    return {
        "guess_5_options": expected_ev(),
        "guess_4_options": expected_ev(options=4),
        "one_blank_9th": expected_ev(blanks=9),
        "ten_blanks": expected_ev(blanks=10),
    }
