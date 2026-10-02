"""The item schema, and the difficulty model that is DERIVED rather than
REQUESTED.

WHY THIS FILE IS THE IMPORTANT ONE
    The owner's requirement: "question and paper not hallucinate this level of
    question." The reference project already paid for this lesson the hard way.
    It MEASURED that requesting `Apply` and then `Analyse` from a model returned
    the IDENTICAL stem on 4 of 6 segments. A paper built by asking for several
    levels therefore counts one question twice, and satisfies its own
    distribution gate by duplication.

    So: never ask a model for a level. DERIVE the level from the item's own
    structure, after the fact, in code. `derive_level` reads the derivation, the
    distractor set and the stem, and returns a tier. A drafter that CLAIMS a
    level is recorded as claiming one; the claim is checked against the
    derivation and a disagreement is a finding, not a repair (D3).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum

from .syllabus import Stratum


class Level(StrEnum):
    FOUNDATION = "foundation"
    """The concept, isolated. One move. The learner has met the idea but not
    the problem. If they cannot do this, nothing above it is learnable."""

    EASY = "easy"
    """One concept, two moves, or one concept plus one recall."""

    MEDIUM = "medium"
    """Two concepts combined, or one concept needing a substitution. This is
    where the real XAT paper lives."""

    HARD = "hard"
    """Multi-concept, or an insight step, or a large integer count. The 85->95
    band. HARD must stay rare: an exam with many hard items measures the wrong
    thing."""


LEVEL_ORDER = (Level.FOUNDATION, Level.EASY, Level.MEDIUM, Level.HARD)

#: Share of questions per level in a LEARNING practice. A mock is different --
#: see `MOCK_SHAPE`.
LEVEL_MIX = {
    Level.FOUNDATION: 0.10,
    Level.EASY: 0.25,
    Level.MEDIUM: 0.40,
    Level.HARD: 0.25,
}


@dataclass(frozen=True, slots=True)
class Distractor:
    text: str
    misconception: str
    """A NAME for the wrong idea this option encodes. A distractor nobody can
    name is a distractor nobody can rule out, so it teaches nothing."""

    is_real_near_miss: bool = False
    """True when this option is the value produced by an actual plausible
    wrong move (dropping a sign, halving a base, averaging two speeds). A paper
    of five options where four are random numbers measures guessing, not
    reasoning -- D9."""

    produces: str | float | None = None
    """The arithmetic of the wrong move, as a sympy expression over this item's
    own numbers, which MUST equal the option's `option_values` entry.

    MEASURED 2026-10-02, and this field exists because of it. Four of Lesson 1's
    options were DIGIT TRANSPOSITIONS of what their own named mistake produced --
    an option reading Rs 10,250 beside an explanation saying 10,000 x 5 / 100,
    which is 10,500 -- and a fifth claimed a cause that is arithmetically
    impossible. All five passed every gate, because `G8` counts near-misses, `G12`
    checks that a misconception exists and is distinct, and NOT ONE GATE ASKED
    whether the named mistake PRODUCES the option it is attached to.

    A distractor whose cause is false is worse than a bad distractor: a learner
    cannot rule it out, and the explanation teaches a rule that is not true.

    So the cause is now a machine-checkable expression and `G16` refuses the item
    when it does not evaluate to the option.

    **What this does NOT buy, stated plainly.** `G16` proves the move computes
    the option. It cannot prove the move is a mistake a learner would actually
    make -- `1440*100/18` is arithmetically valid and pedagogically absurd, and
    no arithmetic check will ever say so. Plausibility stays a `key-auditor`
    judgement; arithmetic is a gate. That division is the point.

    `None` means unproven, and on a QUANT item `G16` REFUSES it rather than
    skipping it. A distractor nobody can reproduce is a distractor nobody has
    verified."""


@dataclass(frozen=True, slots=True)
class Item:
    """One question, in both the form a learner reads and the form code checks.

    `options` are DISPLAY strings and display strings are not arithmetic:
    `Rs 200` and `2 : 3` do not parse as sympy. MEASURED while building
    Lesson 1 -- all four of its keys were REFUSED by G5 for exactly this.

    `option_values` is the arithmetic twin of `options`, in the same order, and
    it is what the solver reads. Making it a separate field rather than parsing
    the label is deliberate: it means a drafter states the number it wants
    checked, and `G14_option_value_matches_label` then asserts the number is
    actually visible in the option the learner reads.

    WORSE, and the reason G14 is a gate rather than a comment: `'14,400'` does
    not fail to parse. `sympify` returns the TUPLE `(14, 400)`, so a thousands
    separator turns one amount into a pair and slips PAST the parse check
    instead of being caught by it.
    """

    id: str
    subtopic_id: str
    stratum: Stratum
    stem: str
    options: tuple[str, ...]
    key_index: int
    option_values: tuple[str, ...]
    """Machine-readable values, parallel to `options`, in the same order. See
    the class docstring for why this is separate from `options`, and for the
    `(14, 400)` trap that `G14` exists to catch. Empty `()` for JUDGEMENT,
    where there is no arithmetic to do."""

    derivation: str | None
    """sympy-parseable expression evaluating to the keyed value. REQUIRED for
    QUANT, FORBIDDEN for JUDGEMENT."""

    distractors: tuple[Distractor, ...]
    derivation_steps: int
    needs_substitution: bool
    insight_required: bool
    enumeration_size: int | None = None
    """For LOGIC: the number of assignments enumerated. A large enumeration is
    itself the difficulty."""

    calculator_minutes: float = 1.5
    claimed_level: Level | None = None
    """What the drafter SAID. Never used as the level. Recorded only so the
    derivation can be checked against it."""

    time_budget_seconds: float = 120.0

    def __post_init__(self) -> None:
        if self.stratum is Stratum.QUANT and not self.derivation:
            raise ValueError(
                f"{self.id}: QUANT item without a derivation. An item whose key "
                f"cannot be recomputed is exactly the item we cannot vouch for."
            )
        if self.stratum is Stratum.JUDGEMENT and self.derivation:
            raise ValueError(
                f"{self.id}: JUDGEMENT item carries a derivation. Prose has no "
                f"solver, so a derivation here is a fabricated proof."
            )
        if self.option_values and len(self.option_values) != len(self.options):
            raise ValueError(
                f"{self.id}: {len(self.option_values)} option values for "
                f"{len(self.options)} options. They are parallel arrays, so a "
                f"length mismatch means the value checked is not the value of "
                f"the option the learner will read."
            )
        if self.stratum is Stratum.QUANT and not self.option_values:
            raise ValueError(
                f"{self.id}: a QUANT item carries no `option_values`, so its key "
                f"cannot be recomputed and cannot be vouched for. Display strings "
                f"are not arithmetic: 'Rs 200' and '2 : 3' do not parse."
            )

    @property
    def key_value(self) -> str:
        """The keyed option's machine-readable value.

        Falls back to the label ONLY for a stratum with no solver, where there
        is no arithmetic to do. For QUANT the fallback is a bug waiting to
        happen and G5 will refuse it.
        """
        if self.option_values:
            return self.option_values[self.key_index]
        return self.key_text

    @property
    def key_text(self) -> str:
        """The keyed option's own text.

        Raises `IndexError` on an out-of-range key rather than returning a
        placeholder. Returning `""` here would let the solver compare a
        derivation against an empty expression and report it as a KEY_MISMATCH,
        which is a *different defect wearing the same coat* -- it would put
        "the key is wrong" in the refusal log when the truth is "the key does
        not exist". `gates.run` bounds-checks first and short-circuits.
        """
        return self.options[self.key_index]

    @property
    def option_count(self) -> int:
        return len(self.options)


# --------------------------------------------------------------------------
# The derivation. STRUCTURE, not a request.
# --------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class DifficultyReport:
    level: Level
    score: float
    drivers: tuple[str, ...]
    """What actually made it hard, so a hard item can be TAUGHT rather than
    merely attempted. A hard question with no named driver is not hard, it is
    long."""

    verdict: str
    """AGREES | CLAIM_MISMATCH | NO_CLAIM"""

    @property
    def claimed(self) -> Level | None:
        return None


def derive_level(item: Item) -> DifficultyReport:
    """Compute an item's level from its own structure.

    Deliberately not a rubric the drafter fills in. Every input is a property of
    the item that already exists: how many operations its derivation takes,
    whether it needs a substitution, whether it needs an insight, how large its
    enumeration is, and how well its distractors discriminate.
    """
    score = 0.0
    drivers: list[str] = []

    steps = item.derivation_steps
    score += min(steps, 4) * 0.85
    if steps >= 2:
        drivers.append(f"{steps}-step derivation")
    elif steps:
        drivers.append("single move")

    if item.needs_substitution:
        score += 1.2
        drivers.append("requires a substitution before the method applies")

    if item.insight_required:
        score += 2.0
        drivers.append("requires an insight the topic does not name")

    if item.enumeration_size:
        if item.enumeration_size > 500:
            score += 2.2
            drivers.append(f"enumeration over {item.enumeration_size} assignments")
        elif item.enumeration_size > 60:
            score += 1.4
            drivers.append(f"enumeration over {item.enumeration_size} assignments")

    # LINEAR, not a cliff. The first version of this charged a flat +0.8 at
    # `real >= 3`, which meant an item with 2 real near-misses landed in a
    # different level from an otherwise identical item with 3. One extra
    # plausible wrong move cannot be worth a whole level, and a level boundary
    # that sits on an arbitrary threshold is a boundary the paper drifts across.
    real = sum(d.is_real_near_miss for d in item.distractors)
    score += 0.2 * real
    if real >= 3:
        drivers.append(f"{real} distractors are real computed near-misses")
    elif real <= 1 and item.stratum is Stratum.QUANT:
        drivers.append("distractors are mostly arbitrary -- item reads as easy "
                       "whether or not it is")

    if item.calculator_minutes > 2.0:
        score += 0.5
        drivers.append("not finishable inside the 2-minute budget with the "
                       "on-screen calculator")

    if score >= 5.0:
        level = Level.HARD
    elif score >= 3.0:
        level = Level.MEDIUM
    elif score >= 1.5:
        level = Level.EASY
    else:
        level = Level.FOUNDATION

    if item.claimed_level is None:
        verdict = "NO_CLAIM"
    elif item.claimed_level is level:
        verdict = "AGREES"
    else:
        verdict = "CLAIM_MISMATCH"

    return DifficultyReport(level=level, score=round(score, 2),
                            drivers=tuple(drivers), verdict=verdict)


def claimed(report: DifficultyReport, item: Item) -> Level | None:
    return item.claimed_level if report.verdict == "CLAIM_MISMATCH" else None


#: The structural profile of each level, MEASURED against `derive_level` and
#: asserted in the test suite by `test_every_level_is_reachable`.
#:
#: This is the one place a level may be REQUESTED -- and it is requested of
#: CODE, never of a model. The drafter picks a structural profile and then has
#: to live with whatever `derive_level` says it built. That inversion is the
#: whole defence against the reference project's measured finding that a model
#: asked for `Apply` and then `Analyse` returns the identical stem.
LEVEL_RECIPES: dict[Level, dict[str, int | bool]] = {
    # 0.85 (1 step) + 0.4 (2 near-misses) = 1.25 -> FOUNDATION
    Level.FOUNDATION: {"derivation_steps": 1, "needs_substitution": False,
                       "insight_required": False, "real_near_misses": 2},
    # 1.7 (2 steps) + 0.8 (4 near-misses) = 2.5 -> EASY
    Level.EASY: {"derivation_steps": 2, "needs_substitution": False,
                 "insight_required": False, "real_near_misses": 4},
    # 2.55 (3 steps) + 1.2 (substitution) + 0.8 = 4.55 -> MEDIUM
    Level.MEDIUM: {"derivation_steps": 3, "needs_substitution": True,
                   "insight_required": False, "real_near_misses": 4},
    # 3.4 (4 steps) + 1.2 + 2.0 + 0.8 = 7.4 -> HARD
    Level.HARD: {"derivation_steps": 4, "needs_substitution": True,
                 "insight_required": True, "real_near_misses": 4},
}


def recipe(level: Level, options: int = 5) -> tuple[Distractor, ...]:
    """Build the distractor set a level's profile calls for."""
    n = options - 1
    real = int(LEVEL_RECIPES[level]["real_near_misses"])
    return tuple(
        Distractor(text=f"d{i}", misconception=f"trap {i}",
                   is_real_near_miss=i < real)
        for i in range(n)
    )


# --------------------------------------------------------------------------
# Paper-level distribution. Mirrors the reference project's A26 split: a
# LEARNING shape and an EXAM shape are DIFFERENT PRODUCTS, not one product
# with a length setting.
# --------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class PaperShape:
    """The shape of a THING: a paper, a lesson, or a single-level drill.

    `level_filtered` is the field that keeps D26 true in code rather than in a
    comment. A drill is the learner's chosen level, repeated; a paper has a mix
    because the exam has one. MEASURED 2026-10-02: `_enforce_mix` returns early
    below `MIX_ENFORCEMENT_FLOOR` (8), which protected a five-item drill -- but a
    learner asking for **twenty** single-digit items at one level is above the
    floor, so G11 would have dropped fifteen of them for "foundation over quota".
    That is D12's defect exactly: a paper rule handed a non-paper.

    So the shape says what it is, and G11 refuses to enforce a mix on a shape that
    has none.
    """
    name: str
    questions: int
    minutes: int
    level_mix: dict[Level, float]
    stratum: Stratum
    negative_marking: bool
    options: int = 5
    level_filtered: bool = False

    def quota(self) -> dict[Level, int]:
        """Per-level question counts that sum to `questions`.

        Largest-remainder apportionment, so the quotas are integers and they
        always close. A distribution gate that does not sum to the paper length
        is a gate nobody trusts.
        """
        exact = {lv: self.level_mix[lv] * self.questions for lv in LEVEL_ORDER}
        base = {lv: int(v) for lv, v in exact.items()}
        short = self.questions - sum(base.values())
        order = sorted(LEVEL_ORDER, key=lambda lv: (-(exact[lv] - base[lv]), lv))
        for lv in order[:short]:
            base[lv] += 1
        return base


#: THE LESSON. This is the product the owner actually asked for: one subtopic,
#: four levels, each rung reachable from the one below it. The mix is FRACTIONAL
#: -- `quota()` is an apportionment, so absolute counts silently collapse
#: (measured: {1,1,1,0} returned {4,4,4,0} before this was fixed).
LESSON_SHAPE = PaperShape(
    name="LESSON",
    questions=4,
    minutes=0,
    level_mix={Level.FOUNDATION: 0.25, Level.EASY: 0.25,
               Level.MEDIUM: 0.25, Level.HARD: 0.25},
    stratum=Stratum.QUANT,
    negative_marking=False,
)

#: A practice set is not an exam. 20 questions, no clock pressure on the
#: concept, and the ladder runs FOUNDATION->HARD on ONE subtopic so that the
#: hard item is reachable from the foundation item.
PRACTICE_SHAPE = PaperShape(
    name="PRACTICE",
    questions=20,
    minutes=0,
    level_mix=LEVEL_MIX,
    stratum=Stratum.QUANT,
    negative_marking=False,
)

#: THE OWNER'S "INITIAL SET": five questions at every level.
#:
#: MEASURED 2026-10-02: `LESSON_SHAPE` above is ONE question per level -- four in
#: total -- and the owner asked for five at each level, so twenty for a subtopic.
#: The quota closes at 5/5/5/5 because the mix is uniform (0.25 each) over 20.
LESSON_20_SHAPE = PaperShape(
    name="LESSON-20",
    questions=20,
    minutes=0,
    level_mix={Level.FOUNDATION: 0.25, Level.EASY: 0.25,
               Level.MEDIUM: 0.25, Level.HARD: 0.25},
    stratum=Stratum.QUANT,
    negative_marking=False,
)

#: "GIVE ME MORE AT THIS LEVEL, single-digit answers" -- the owner's second ask.
#:
#: One shape per level, `level_filtered=True`, so `G11` cannot enforce a paper mix
#: on a drill. The count is a CAP, not a quota: `quota()` would apportion, and
#: `max(1, ...)` in `_enforce_mix` is exactly what makes a one-level paper
#: impossible to express.
LEVEL_DRILL_SHAPES: dict[Level, PaperShape] = {
    lv: PaperShape(
        name=f"DRILL-{lv.value.upper()}",
        questions=5,
        minutes=0,
        level_mix={other: (1.0 if other is lv else 0.0) for other in LEVEL_ORDER},
        stratum=Stratum.QUANT,
        negative_marking=False,
        level_filtered=True,
    )
    for lv in LEVEL_ORDER
}

#: Answers a learner can hold in their head and check. The owner's "single digit
#: question" -- MEASURED 2026-10-02: giving a bounded answer space is what makes
#: unlimited extra questions possible WITHOUT padding, because the variety has to
#: come from the reasoning (which G6 already enforces) rather than the numbers.
SINGLE_DIGIT_MIN = 1
SINGLE_DIGIT_MAX = 9


def answer_is_single_digit(value: object) -> bool:
    """True when `value` is an integer 1..9 inclusive.

    Deliberately a PREDICATE and not a stored flag. MEASURED 2026-10-02: a stored
    `single_digit: bool` on the item would be a claim the code never re-derived, and
    this project's whole thesis is that a claim code did not compute is not evidence.
    """
    try:
        n = float(str(value))
    except (TypeError, ValueError):
        return False
    return n.is_integer() and SINGLE_DIGIT_MIN <= n <= SINGLE_DIGIT_MAX


def single_digit_items(items: Iterable[Item]) -> list[Item]:
    """The subset whose KEY is a single digit -- what "more like this" returns."""
    return [it for it in items if answer_is_single_digit(it.key_value)]


#: The verified XAT 2026 paper. 6.71 DI questions/yr at ~2 min each, against a
#: 170-minute budget for all 75 Part-1 questions = 136 s/question. So the top of
#: the paper is NOT meant to be 25% hard. HARD here means "the hardest thing in
#: this paper", not "unsolvable".
QUANT_MOCK = PaperShape(
    name="MOCK-QA",
    questions=28,
    minutes=0,
    level_mix=LEVEL_MIX,
    stratum=Stratum.QUANT,
    negative_marking=True,
)

FULL_MOCK = PaperShape(
    name="MOCK-FULL",
    questions=75,
    minutes=170,
    level_mix=LEVEL_MIX,
    stratum=Stratum.QUANT,
    negative_marking=True,
)


def expected_ev(*, options: int = 5, mark_correct: float = 1.0,
                mark_wrong: float = -0.25, blanks: int = 0,
                blank_penalty_after: int = 8,
                blank_penalty: float = -0.10) -> float:
    """Expected marks from guessing at random.

    `mark_correct` is `float`, not `int`. MEASURED 2026-10-02: it was `int = 1`, and
    the first caller to hold a marking scheme whose correct mark was not an integer
    literal -- CAT's reported +3, passed through `SectionSpec.mark_correct: float` --
    was a mypy error. An over-narrow annotation on a generic function is the same
    defect as `gates.run(items: list[Item])`: it forces callers to lie about their
    data to satisfy the type. XAT's own +1 is an integer by coincidence of the
    paper, not by property of the function.

    Measured, not argued. For the verified XAT 2026 shape this is EXACTLY 0.0
    with 5 options -- +1/5 and -0.25x4/5 cancel -- so random guessing is a
    coin-flip on score, not a leak. What makes a blank cost something is the
    ninth blank, not the first.

    This is the fact that inverts the usual "skip if unsure" advice, and it is
    why the practice shape carries no negative marking: teaching a skill is
    never the same as scoring a percentile.
    """
    guess = (mark_correct / options) + ((options - 1) / options) * mark_wrong
    blank_cost = sum(blank_penalty for _ in range(max(0, blanks - blank_penalty_after)))
    return round(guess + blank_cost, 4)


def with_answers(items: tuple[Item, ...],
                 solutions: dict[str, tuple[str, ...]]) -> dict[str, tuple[str, ...]]:
    """Append the stated answer to every step-by-step.

    Because a solution that ends on a rejected distractor reads, to a learner
    scanning the last line, as though the last number were the answer. The final
    line is the answer and nothing else.

    MEASURED 2026-10-02: this lived in `lesson1.py` and Lesson 2 had to import
    it from there, which would have made the second lesson depend on the first.
    It is here because it is a property of the `Item`, not of any one lesson."""
    out: dict[str, tuple[str, ...]] = {}
    for item in items:
        steps = solutions.get(item.id)
        if not steps:
            raise KeyError(f"{item.id} has no step-by-step")
        out[item.id] = (*steps, f"ANSWER: {item.key_text}")
    return out
