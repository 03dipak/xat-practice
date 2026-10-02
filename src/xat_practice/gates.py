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
    "G14_option_value_matches_label",
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

        blocked = {r.gate for r in res.refusals if r.item_id == it.id}
        if not blocked:
            res.admitted.append(it)

    res.admitted = _enforce_mix(res, items)
    return res


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
