"""Topic weight model for the XAT 2026 QA&DI paper.

NUMBERS CARRY THEIR BASIS (AGENTS.md). Every weight here names its population.

POPULATION
    196 questions = 7 papers x 28 QA&DI questions, XAT 2020..2026 inclusive.
    SOURCE: cracku.in "XAT Quants Topic Wise Weightage", per-year row sums
    verified to 28 by us (see `self_check`). The source is a coaching
    compilation, NOT XLRI -- XLRI publishes no per-topic breakdown. Treat the
    figures as `measured-from-secondary-source`, never as `measured-officially`.

INTERNAL CONSISTENCY CHECK
    `sum(weight for each year)` == 28 for all 7 years. `self_check()` asserts
    this. It is the only reason this table is trusted at all: a table that does
    not close to the paper length is a table of guesses.

TIER
    P1  must be trained to zero-error.  >= 2.0 questions/year.
    P2  high ROI, small and cheap to learn.   0.5 - 2.0
    P3  occasional; learn the single most common shape, not the chapter. < 0.5
    --  deliberately absent from the syllabus. See EXCLUDED and D7.

THE 80-100 PERCENTILE WEIGHTING
    Raw frequency is NOT the target metric. This paper is trained for the
    80th-100th percentile band, and in that band a P3 topic asked once is worth
    less than a P1 topic asked 5 times -- but the P1 topics are also where a
    single careless error costs most, because they are the ones you can be
    certain about. So `band_value` deliberately flattens the head of the
    distribution relative to raw frequency. This is a judgement call and is
    recorded as D4, not measured.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

PAPERS = (2020, 2021, 2022, 2023, 2024, 2025, 2026)
QUESTIONS_PER_PAPER = 28
POPULATION = len(PAPERS) * QUESTIONS_PER_PAPER  # 196


class Tier(StrEnum):
    P1 = "P1"  # train to zero error
    P2 = "P2"  # high ROI, cheap
    P3 = "P3"  # one shape only


class Stratum(StrEnum):
    """Which grounding guarantee applies to an item of this kind.

    This is the most important concept in the codebase and the reason the
    product can state honestly what it does and does not guarantee.
    """

    QUANT = "quant"
    """GROUNDED BY COMPUTATION. The key is re-derived by a solver in
    `solver.py`. The drafter's key is never trusted; if solver and drafter
    disagree the item is REFUSED. A percent claim on this stratum is a
    statement about code, not about a model's opinion."""

    LOGIC = "logic"
    """GROUNDED BY FORMAL ENUMERATION. Syllogisms, sets, seating, games,
    inequalities-regions: the key is re-derived by exhaustive enumeration over
    a constraint set, so it is still computed, not asserted."""

    JUDGEMENT = "judgement"
    """NOT GROUNDED BY COMPUTATION. VALR and Decision Making. There is no solver
    and no enumeration. The key is re-derived by an INDEPENDENT second call
    that sees only the stimulus and the option texts -- never the key, never
    the rationale, never the stem -- and a disagreement is a REFUSAL.

    This stratum is strictly weaker evidence than QUANT and the product must
    never present it otherwise (AGENTS.md; D2)."""


@dataclass(frozen=True, slots=True)
class Topic:
    id: str
    name: str
    per_year: tuple[int, ...]  # 2020..2026, None-coded as 0
    owner_listed: bool
    note: str = ""

    @property
    def weight(self) -> float:
        """Mean questions per paper. The denominator is 7 papers."""
        return sum(self.per_year) / len(PAPERS)

    @property
    def tier(self) -> Tier:
        w = self.weight
        if w >= 2.0:
            return Tier.P1
        if w >= 0.5:
            return Tier.P2
        return Tier.P3

    @property
    def band_value(self) -> float:
        """Weight for the 80-100 percentile target. See module docstring, D4."""
        w = self.weight
        if w >= 4.0:
            return 1.00  # DI, Geometry
        if w >= 2.0:
            return 0.95  # the dependable core
        if w >= 1.0:
            return 0.80  # cheap marks, learn the shape
        return 0.50  # one shape only


@dataclass(frozen=True, slots=True)
class Subtopic:
    """A trained shape inside a topic. The unit a lesson is actually built on."""

    id: str
    topic_id: str
    name: str
    tier: Tier
    stratum: Stratum
    traps: tuple[str, ...] = ()
    """The specific wrong ideas this subtopic reliably produces. Each one must
    become a named distractor (D9). A trap we cannot name is a trap we cannot
    set."""


# --------------------------------------------------------------------------
# The table. Values are the per-year counts from the source. Rows sum to 28.
# --------------------------------------------------------------------------

TOPICS: tuple[Topic, ...] = (
    Topic("di", "Data Interpretation (tables, pie, bar, graphs, caselets)",
          (6, 9, 2, 6, 9, 9, 6), False,
          "Largest single block. Highest frequency AND lowest difficulty-per-mark. "
          "Not in the owner's list -- added, D4."),
    Topic("geo_mens", "Geometry & Mensuration", (6, 6, 2, 5, 2, 5, 6), True,
          "Most consistent P1 in the whole paper. 2 questions every single year."),
    Topic("num_sys", "Number System (factors, HCF/LCM, remainder, base)",
          (2, 2, 2, 5, 4, 2, 3), False, "Added, D4. Speed marks, near-zero learning cost."),
    Topic("avg_ratio", "Averages, Ratio & Proportion", (1, 3, 7, 2, 0, 2, 3), True, ""),
    Topic("lin_quad", "Linear & Quadratic Equations", (1, 1, 5, 2, 2, 2, 1), True,
          "The 2024 spike to 5 is instructive: a hard year leans on equations."),
    Topic("pct", "Percentage, % change, growth, CAGR", (0, 0, 0, 0, 0, 0, 0), False,
          "NOT SEPARATELY MEASURED. Inside `avg_ratio` and inside the "
          "CollegeDekho 'Arithmetic' row (8,8,4-5,4,5,5 ~= 5.8/yr). Recorded at "
          "0 to mean UNMEASURED, not absent -- see D5. Do not read weight 0 as "
          "'never asked'."),
    Topic("pl_int", "Profit, Loss & Interest", (1, 1, 5, 3, 1, 1, 1), True, ""),
    Topic("tsd", "Time, Speed & Distance", (2, 0, 1, 0, 1, 4, 2), True, ""),
    Topic("puzzle", "Puzzle & Charts", (3, 3, 0, 0, 3, 0, 0), False, ""),
    Topic("prob_comb", "Probability & Combinatorics", (2, 1, 0, 1, 1, 1, 1), False,
          "Minimal slice only, D6. 1-2/yr, high variance, spikes derail 95th."),
    Topic("prog", "Progressions & Series", (0, 0, 1, 1, 3, 0, 1), True, ""),
    Topic("ds", "Data Sufficiency", (0, 0, 1, 2, 1, 0, 0), False,
          "Added, D4. A question TYPE, not a topic -- it needs its own gate "
          "(G14). Not in the owner's list."),
    Topic("ineq", "Inequalities", (0, 0, 0, 1, 1, 1, 1), False, "Added, D4."),
    Topic("venn", "Venn & Sets", (1, 0, 1, 0, 0, 0, 2), False, "Added, D4. Cheap marks."),
    Topic("log", "Logarithms, Surds & Indices", (0, 1, 1, 0, 0, 1, 0), True, ""),
    Topic("func", "Graphs & Functions", (3, 0, 0, 0, 0, 0, 0), False,
          "Added, D4. Brand new category in 2026 with 3 questions."),
    Topic("time_work", "Time & Work", (0, 1, 0, 0, 0, 0, 1), True,
          "Real weight is higher than the row shows: it is folded into "
          "`avg_ratio` and into DI caselets in several years."),
)

EXCLUDED: dict[str, str] = {
    "trigonometry": "0-3 per year, and only the Pythagorean and "
                    "heights-and-distances forms are worth training, because those "
                    "reuse geometry we already train. Not on the owner's list. Excluded, D7.",
    "complex_numbers": "Asked at most occasionally and never in a form that rewards "
                     "morethan two minutes. Excluded from training, D7.",
    "vectors_3d": "Appears only as a one-line direction question at most, and a "
                  "direction question is closer to a ratio question we already "
                  "train. Excluded, D7.",
    "matrices_determinants": "The only recurring use is a 3x3 determinant expanded as "
                               "a linear equation in one unknown, which the linear-equations "
                               "training already covers. Excluded as a separate chapter, D7.",
    "binomial": "Almost never asked standalone. Excluded, D7.",
    "calculus": "Not in the QA&DI syllabus at this level. Excluded, D7.",
    "statistics_mean_mode_variance": "Asked roughly once in five years, so at best "
                                     "a P3 shape. A mode question is a frequency-table "
                                     "read, which the DI training covers. Excluded, D7.",
}


def self_check() -> None:
    """Assert every year's rows close to 28.

    A weight table that does not sum to the paper length is a table of
    opinions wearing the costume of data. This is the check that makes the rest
    quotable, so it runs in the test suite on every paper.
    """
    for i, year in enumerate(PAPERS):
        total = sum(t.per_year[i] for t in TOPICS)
        if total != QUESTIONS_PER_PAPER:
            raise ValueError(
                f"{year}: topic rows sum to {total}, paper has "
                f"{QUESTIONS_PER_PAPER}. The table is wrong, not the exam."
            )
    if len(TOPICS) != len({t.id for t in TOPICS}):
        raise ValueError("duplicate topic id")


def measured_topics() -> tuple[Topic, ...]:
    """Topics whose weight is actually measured. `pct` is excluded -- D5."""
    return tuple(t for t in TOPICS if t.id != "pct")


def by_tier(tier: Tier) -> tuple[Topic, ...]:
    return tuple(sorted((t for t in measured_topics() if t.tier == tier),
                        key=lambda t: -t.weight))


@dataclass(frozen=True, slots=True)
class SubtopicIndex:
    items: dict[str, Subtopic] = field(default_factory=dict)

    def __getitem__(self, key: str) -> Subtopic:
        return self.items[key]


def subtopic(topic_id: str, name: str, tier: Tier, stratum: Stratum,
             *traps: str) -> Subtopic:
    return Subtopic(f"{topic_id}:{name}", topic_id, name, tier, stratum, traps)


# --------------------------------------------------------------------------
# The trained syllabus. Only subtopics the 80-100 band actually needs.
# Every `traps` entry is a promise: it becomes a named distractor (D9).
# --------------------------------------------------------------------------

SUBTOPICS: tuple[Subtopic, ...] = (
    # ---- P1 core -----------------------------------------------------------
    subtopic("geo_mens", "similarity-and-area-ratios", Tier.P1, Stratum.QUANT,
             "equal-base triangles have equal area, so someone halves a base",
             "similarity scales LENGTHS squared into AREAS",
             "a ratio of areas read as a ratio of sides"),
    subtopic("geo_mens", "angle-bisector-and-cevian", Tier.P1, Stratum.QUANT,
             "an angle bisector meeting the opposite side at the midpoint",
             "the angle-bisector theorem applied to a median"),
    subtopic("geo_mens", "triangle-angle-sine-rule", Tier.P2, Stratum.QUANT,
             "angle-sum used where a sine rule is needed",
             "sine rule applied to an obtuse triangle without checking"),
    subtopic("geo_mens", "circle-tangents", Tier.P1, Stratum.QUANT,
             "the two tangents from an external point treated as unequal",
             "tangent length taken as the diameter",
             "a tangent read as perpendicular to the chord rather than the radius"),
    subtopic("geo_mens", "circle-power-of-a-point", Tier.P2, Stratum.QUANT,
             "tangent-squared equated to the full secant instead of the "
             "external segment",
             "the chord products equated across two different points"),
    subtopic("geo_mens", "cyclic-quadrilateral", Tier.P2, Stratum.QUANT,
             "opposite angles of a cyclic quadrilateral ADDED to 180 but with "
             "the pair misidentified",
             "any quadrilateral assumed cyclic without the concyclic condition ever being checked"),
    subtopic("geo_mens", "polygon-angle-sums", Tier.P3, Stratum.QUANT,
             "interior angle of an n-gon read as (n-2)/180",
             "the degree symbol dropped from an angle sum"),
    subtopic("geo_mens", "mensuration-2d-3d", Tier.P1, Stratum.QUANT,
             "a volume computed from an area formula, so cubic units never appear",
             "a frustum computed as a cylinder",
             "unit conversion done after the formula instead of before"),
    subtopic("geo_mens", "coordinate-geometry", Tier.P2, Stratum.QUANT,
             "distance formula used for the midpoint",
             "slope of a perpendicular not negated",
             "a circle written with the wrong radius after translating"),
    subtopic("num_sys", "hcf-lcm-and-factors", Tier.P1, Stratum.QUANT,
             "LCM computed as a product",
             "a maximum-count problem answered with LCM when the answer is the "
             "count of multiples"),
    subtopic("num_sys", "remainders-and-modulus", Tier.P2, Stratum.QUANT,
             "modular arithmetic done on the dividend rather than the divisor",
             "a remainder larger than the modulus accepted"),
    subtopic("avg_ratio", "weighted-average", Tier.P1, Stratum.QUANT,
             "a simple average used where the counts differ",
             "a plain average taken where the groups differ in size, so the weights are ignored"),
    subtopic("avg_ratio", "alligation-mixtures", Tier.P1, Stratum.QUANT,
             "alligation ratio confused with the mixture ratio",
             "replacement questions assuming a fixed amount of solvent"),
    subtopic("lin_quad", "quadratic-roots-and-relations", Tier.P1, Stratum.QUANT,
             "the extraneous root kept because a quadratic must have two roots",
             "sum/product of roots applied without checking the leading "
             "coefficient is non-unit"),
    subtopic("lin_quad", "word-problems-modelling", Tier.P2, Stratum.QUANT,
             "two unknowns collapsed into one equation",
             "a percentage change applied to the wrong base"),
    subtopic("pct", "successive-percentage-change", Tier.P1, Stratum.QUANT,
             "successive changes ADDED (x% up then y% down is not x-y)",
             "a net change treated as symmetric about the original",
             "percentage of percentage read as a subtraction"),
    subtopic("pct", "growth-rate-and-cagr", Tier.P2, Stratum.QUANT,
             "CAGR computed as an arithmetic mean of the growth rates",
             "a growth rate applied to the wrong year"),
    # MEASURED 2026-10-02, expanded on all three pl_int subtopics. Every
    # entry is a MISTAKE A LEARNER MAKES, not a topic heading: D9 says a trap
    # becomes a named distractor, and a heading cannot be ruled out on a
    # page. Each one names the wrong MOVE, so `G16` can check the option
    # really is what that move produces.
    subtopic("pl_int", "compound-interest-with-installments", Tier.P2, Stratum.QUANT,
             "simple interest used on an instalment plan",
             "amount and present value confused",
             "interest charged only on the instalment still unpaid",
             "the compounding period counted in months against an annual rate",
             "every instalment compounded for the full term instead of its own",
             "the rate raised to the years instead of compounded year by year"),
    subtopic("pl_int", "false-weight-dishonest-dealer", Tier.P3, Stratum.QUANT,
             "the false gain treated as a percentage of cost price",
             "profit percent computed on selling price",
             "the dishonest weight added to the scale and never to the bill",
             "the next buyer's profit percent taken on his own selling price",
             "the gain expressed as a plain fraction instead of a percentage",
             "cost price recovered as selling price minus the profit percent"),
    subtopic("tsd", "trains", Tier.P2, Stratum.QUANT,
             "the train's own length omitted from the crossing distance",
             "relative speed set to zero for a same-direction chase"),
    subtopic("tsd", "boats-and-streams", Tier.P2, Stratum.QUANT,
             "downstream and upstream speeds not differentiated",
             "still-water speed confused with the boat's speed in still water"),
    subtopic("tsd", "average-speed", Tier.P2, Stratum.QUANT,
             "the two speeds averaged arithmetically",
             "distance divided by distance instead of total time"),
    subtopic("time_work", "a-plus-b", Tier.P2, Stratum.QUANT,
             "rates added instead of combined as a single rate",
             "days treated additively instead of the reciprocal"),
    subtopic("prog", "arithmetic-geometric-progressions", Tier.P2, Stratum.QUANT,
             "a geometric mean treated as an arithmetic mean",
             "an nth-term formula indexed from 0 instead of 1"),
    subtopic("log", "logarithm-rules-and-characteristic", Tier.P2, Stratum.QUANT,
             "log of a product treated as a sum",
             "characteristic and mantissa added together as one number instead "
             "of being placed either side of the decimal point",
             "a base change applied to the argument but not the value"),
    subtopic("di", "tables-and-caselets", Tier.P1, Stratum.QUANT,
             "a total row read as a data row",
             "growth applied to the wrong base year",
             "a missing-value solved from the grand total rather than the row"),
    subtopic("di", "pie-and-bar-ratio-reading", Tier.P1, Stratum.QUANT,
             "a percentage share read as a raw count",
             "two bars compared without converting to a common scale"),
    subtopic("num_sys", "max-min-and-integer-counting", Tier.P1, Stratum.QUANT,
             "the count of integers answered with the extremum itself",
             "an inclusive bound treated as exclusive",
             "a divisibility condition ignored, leaving the whole interval"),
    subtopic("num_sys", "estimation-and-answer-choice", Tier.P1, Stratum.QUANT,
             "an exact decimal computed when bounding would decide the option",
             "options read as ordered when they are not"),
    subtopic("ineq", "linear-quadratic-inequalities", Tier.P2, Stratum.QUANT,
             "a union read as an intersection, or the reverse",
             "an inequality sign flipped on dividing by a negative"),
    subtopic("func", "quadratic-graph-behaviour", Tier.P2, Stratum.QUANT,
             "vertex read off the x-axis instead of computed",
             "range stated instead of domain",
             "a transformation sign error on f(-x)"),
    subtopic("prog", "max-min-and-optimisation", Tier.P2, Stratum.QUANT,
             "the extremum of a function at an interval endpoint when it is interior",
             "an inequality satisfied at a boundary ignored"),
    subtopic("prob_comb", "basic-arrangements-and-permutation", Tier.P3, Stratum.QUANT,
             "arrangements and combinations swapped, so a question about "
             "picking is counted as a question about ordering",
             "identical objects treated as distinct"),
    subtopic("prob_comb", "single-die-and-basic-events", Tier.P3, Stratum.QUANT,
             "events assumed independent when they are not",
             "favourable outcomes not matched to the sample space size"),
    subtopic("ds", "sufficiency-statements", Tier.P2, Stratum.LOGIC,
             "a statement that is relevant treated as sufficient",
             "sufficiency judged for one specific value rather than in general",
             "both statements together treated as necessary as well as sufficient"),
    subtopic("venn", "venn-counting", Tier.P3, Stratum.LOGIC,
             "the union read as the intersection",
             "a three-way overlap omitted from the total"),
    subtopic("log", "surds-and-rationalisation", Tier.P3, Stratum.QUANT,
             "a surd left un-simplified in an option comparison",
             "a surd rationalised by multiplying without changing the sign of the middle term"),
    subtopic("puzzle", "routing-and-network-puzzles", Tier.P2, Stratum.LOGIC,
             "a graph constraint ignored when counting the minimum",
             "an edge counted twice in a degree sum"),
    subtopic("pl_int", "simple-interest", Tier.P1, Stratum.QUANT,
             "rate applied to the wrong principal (amount vs original)",
             "time in months used without converting the rate",
             "one year's interest computed and then never scaled by the years",
             "the percentage written into the formula without dividing by 100",
             "the rate and the time added together instead of multiplied",
             "interest taken on the amount owed rather than the amount lent",
             "a percentage quoted for several years used as if it were annual",
             "simple interest treated as compound, growing by (1 + r) each year"),
    subtopic("avg_ratio", "ratio-of-ratios-partnership", Tier.P2, Stratum.QUANT,
             "partnership shares frozen after a capital change",
             "profit split in the old ratio after the investment changed"),
)


def subtopics() -> dict[str, Subtopic]:
    return {s.id: s for s in SUBTOPICS}


def stratum_counts() -> dict[Stratum, int]:
    out: dict[Stratum, int] = {s: 0 for s in Stratum}
    for s in SUBTOPICS:
        out[s.stratum] += 1
    return out


PAPER_SHAPE = {
    "total_questions": 95,
    "part1_minutes": 170,
    "part1": {"qa_di": 28, "va_lr": 26, "dm": 21},
    "part2": {"gk": 20, "minutes": 10},
    "options": 5,
    "mark_correct": 1,
    "mark_wrong": -0.25,
    "blank_penalty_after": 8,
    "blank_penalty": -0.10,
    "gk_in_percentile": False,
    "sectional_time_limit": False,
    "calculator": "qa_di",
}
