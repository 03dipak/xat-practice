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
    """One syllabus topic, with the exam and section it belongs to.

    `exam_id` and `section_id` are REQUIRED, with no default, on purpose. A
    defaulted parent is a silent parent: the next topic added would inherit
    `"xat"/"qa_di"` and appear in the ledger, the navigator and the coverage
    numbers without anyone deciding it belongs there. A missing argument is a
    TypeError at import, which is a gate; an inherited default is not.

    This is the layer above section (D27). Today every topic is `xat`/`qa_di`
    because D7 trains QA&DI only -- and that is stated 17 times rather than
    assumed once.
    """
    id: str
    exam_id: str
    section_id: str
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
    Topic("di", "xat", "qa_di", "Data Interpretation (tables, pie, bar, graphs, caselets)",
          (6, 9, 2, 6, 9, 9, 6), False,
          "Largest single block. Highest frequency AND lowest difficulty-per-mark. "
          "Not in the owner's list -- added, D4."),
    Topic("geo_mens", "xat", "qa_di", "Geometry & Mensuration", (6, 6, 2, 5, 2, 5, 6), True,
          "Most consistent P1 in the whole paper. 2 questions every single year."),
    Topic("num_sys", "xat", "qa_di", "Number System (factors, HCF/LCM, remainder, base)",
          (2, 2, 2, 5, 4, 2, 3), False, "Added, D4. Speed marks, near-zero learning cost."),
    Topic("avg_ratio", "xat", "qa_di", "Averages, Ratio & Proportion",
          (1, 3, 7, 2, 0, 2, 3), True, ""),
    Topic("lin_quad", "xat", "qa_di", "Linear & Quadratic Equations", (1, 1, 5, 2, 2, 2, 1), True,
          "The 2024 spike to 5 is instructive: a hard year leans on equations."),
    Topic("pct", "xat", "qa_di", "Percentage, % change, growth, CAGR", (0, 0, 0, 0, 0, 0, 0), False,
          "NOT SEPARATELY MEASURED. Inside `avg_ratio` and inside the "
          "CollegeDekho 'Arithmetic' row (8,8,4-5,4,5,5 ~= 5.8/yr). Recorded at "
          "0 to mean UNMEASURED, not absent -- see D5. Do not read weight 0 as "
          "'never asked'."),
    Topic("pl_int", "xat", "qa_di", "Profit, Loss & Interest", (1, 1, 5, 3, 1, 1, 1), True, ""),
    Topic("tsd", "xat", "qa_di", "Time, Speed & Distance", (2, 0, 1, 0, 1, 4, 2), True, ""),
    Topic("puzzle", "xat", "qa_di", "Puzzle & Charts", (3, 3, 0, 0, 3, 0, 0), False, ""),
    Topic("prob_comb", "xat", "qa_di", "Probability & Combinatorics", (2, 1, 0, 1, 1, 1, 1), False,
          "Minimal slice only, D6. 1-2/yr, high variance, spikes derail 95th."),
    Topic("prog", "xat", "qa_di", "Progressions & Series", (0, 0, 1, 1, 3, 0, 1), True, ""),
    Topic("ds", "xat", "qa_di", "Data Sufficiency", (0, 0, 1, 2, 1, 0, 0), False,
          "Added, D4. A question TYPE, not a topic -- it needs its own gate "
          "(G14). Not in the owner's list."),
    Topic("ineq", "xat", "qa_di", "Inequalities", (0, 0, 0, 1, 1, 1, 1), False, "Added, D4."),
    Topic("venn", "xat", "qa_di", "Venn & Sets", (1, 0, 1, 0, 0, 0, 2), False,
          "Added, D4. Cheap marks."),
    Topic("log", "xat", "qa_di", "Logarithms, Surds & Indices", (0, 1, 1, 0, 0, 1, 0), True, ""),
    Topic("func", "xat", "qa_di", "Graphs & Functions", (3, 0, 0, 0, 0, 0, 0), False,
          "Added, D4. Brand new category in 2026 with 3 questions."),
    Topic("time_work", "xat", "qa_di", "Time & Work", (0, 1, 0, 0, 0, 0, 1), True,
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
    """Assert the paper closes, and that the exam/section layer closes too.

    A weight table that does not sum to the paper length is a table of
    opinions wearing the costume of data. This is the check that makes the rest
    quotable, so it runs in the test suite on every paper.

    The exam/section checks live HERE, not in `registry.assert_registry_is_honest`,
    because they are TABLE invariants and this function already guards the table's
    other closure. `registry` owns lessons; `self_check` owns what a topic may point
    at. MEASURED 2026-10-02: both dicts closed by luck -- `total_questions` matched
    the section sum and `counted_questions` matched the counted sum, with nothing
    asserting either, because `ExamSpec.sections` held bare ids while `SECTIONS` was
    keyed `"<exam>:<section>"` and the join was a convention.
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

    _check_exam_layer()


def _check_exam_layer() -> None:
    """Every link in EXAMS <-> SECTIONS <-> TOPICS must resolve, and both question
    counts must close. Raises with the specific broken link."""
    # 1. SECTIONS is keyed "<exam>:<section>" and its value must agree with its key.
    for key, spec in SECTIONS.items():
        if key != f"{spec.exam_id}:{spec.section_id}":
            raise ValueError(
                f"SECTIONS[{key!r}] holds exam_id={spec.exam_id!r} "
                f"section_id={spec.section_id!r}; the key and the value disagree"
            )
        if spec.exam_id not in EXAMS:
            raise ValueError(
                f"SECTIONS[{key!r}] names exam {spec.exam_id!r}, which is not in "
                f"EXAMS. Known: {sorted(EXAMS)}"
            )

    # 2. Every section an exam claims must exist, and the sums must close.
    for exam in EXAMS.values():
        for sid in exam.sections():
            if f"{exam.exam_id}:{sid}" not in SECTIONS:
                raise ValueError(
                    f"EXAMS[{exam.exam_id!r}] lists section {sid!r}, which is not in "
                    "SECTIONS"
                )
        all_sum = sum(SECTIONS[f"{exam.exam_id}:{s}"].questions
                      for s in exam.sections())
        if all_sum != exam.total_questions:
            raise ValueError(
                f"{exam.name} {exam.edition}: sections sum to {all_sum}, "
                f"total_questions says {exam.total_questions}"
            )
        counted_sum = sum(SECTIONS[f"{exam.exam_id}:{s}"].questions
                          for s in exam.counted())
        if counted_sum != exam.counted_questions:
            raise ValueError(
                f"{exam.name} {exam.edition}: COUNTED sections sum to "
                f"{counted_sum}, counted_questions says {exam.counted_questions}"
            )

    # 3. Every topic must resolve to a section of ITS OWN exam.
    for topic in TOPICS:
        section_of(topic)
        subtopics_of = [s for s in SUBTOPICS if s.id.startswith(f"{topic.id}:")]
        if not subtopics_of:
            raise ValueError(f"topic {topic.id!r} has no subtopics")

    # 4. No orphan section: every declared section belongs to a claimed exam.
    claimed = {f"{e.exam_id}:{s}" for e in EXAMS.values() for s in e.sections()}
    for key in SECTIONS:
        if key not in claimed:
            raise ValueError(
                f"SECTIONS has {key!r}, which no exam claims. A section that "
                "nothing points at will never be rendered and never be built."
            )


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


@dataclass(frozen=True, slots=True)
class PartSpec:
    """One PART of an exam, with the rules that are shared ACROSS its sections.

    This type exists because of a measured modelling error, caught independently by
    two reviewers reading `docs/LLD.md` on 2026-10-02.

    `blank_penalty` and `blank_penalty_after` were on `SectionSpec`, so the product
    implied **eight free blanks per section**. XAT's rule is "minus 0.10 for every
    unattempted question after the first eight", and Part 1 is ONE pool of 75
    questions across QA&DI, VA&LR and DM in a shared 170 minutes. So the truth is
    **eight free blanks in total**, and a learner told otherwise would skip 24 and
    lose about 1.6 marks. `minutes=170` was wrong for the same reason: it is Part 1's
    clock, not any section's, and XAT 2026 has **no sectional time limit**.

    A per-section penalty is not merely a different default. It is a false attempt
    strategy, and strategy is the thing this product teaches.
    """
    part_id: str
    exam_id: str
    name: str
    sections: tuple[str, ...]
    questions: int
    minutes: int
    in_percentile: bool
    blank_penalty: float = 0.0
    blank_penalty_after: int = 0

    def cost_of_blanks(self, blanks: int) -> float:
        """Marks lost to `blanks` unattempted questions IN THIS PART.

        `blanks` is a count of the WHOLE part, not of one section. That is the whole
        point of this type, and the argument is falsified in
        `test_the_blank_penalty_counts_across_the_part_not_within_a_section`.
        """
        over = max(0, blanks - self.blank_penalty_after)
        return over * self.blank_penalty


@dataclass(frozen=True, slots=True)
class SectionSpec:
    """One SECTION of one exam: its questions, options and per-answer marking.

    MEASURED 2026-10-02, and the reason this is separate from `PartSpec`: XAT 2026
    is -0.25 throughout Part 1 with GK excluded, while CAT is reported to differ
    *per section*. So per-ANSWER marking belongs here and the cross-section blank
    rule does not.

    It carries NO `stratum`. A single value was a lie: QA&DI holds **37 QUANT and 3
    LOGIC** subtopics (`ds:sufficiency-statements`, `venn:venn-counting`,
    `puzzle:routing-and-network-puzzles`), so a section is a MIX. `strata()` derives
    the distribution instead, and nothing has to be relabelled when one is added.
    """
    section_id: str
    exam_id: str
    part_id: str
    name: str
    questions: int
    options: int = 5
    mark_correct: float = 1.0
    mark_wrong: float = -0.25
    calculator: bool = False
    built: bool = False         # is a LESSON written for this section yet?

    def strata(self) -> dict[Stratum, int]:
        """How many subtopics of each stratum this section holds.

        DERIVED, never stored. MEASURED 2026-10-02: `SectionSpec.stratum` was a
        single `Stratum`, which is wrong for any section holding more than one --
        QA&DI holds 3 LOGIC subtopics out of 40.
        """
        out: dict[Stratum, int] = {}
        for sub in SUBTOPICS:
            topic_id = sub.id.split(":", 1)[0]
            for topic in TOPICS:
                if (topic.id == topic_id
                        and topic.exam_id == self.exam_id
                        and topic.section_id == self.section_id):
                    out[sub.stratum] = out.get(sub.stratum, 0) + 1
        return out

    def counts_for_percentile(self, exam: ExamSpec) -> bool:
        """Does this section decide the percentile in `exam`?

        A METHOD, not a stored `in_percentile` flag. MEASURED 2026-10-02: the flag
        was removed because it duplicated the part's `in_percentile` with nothing to
        keep them in step -- GK could be "in" the percentile on one line and out on
        another. One home: the PART decides; the section asks on its exam's behalf.

        `exam` is not optional decoration. Asking an XAT section whether it counts
        inside a DIFFERENT exam is a bug that should be loud, not a question that
        quietly returns the XAT answer.
        """
        if exam.exam_id != self.exam_id:
            raise ValueError(
                f"{self.exam_id}:{self.section_id} was asked whether it counts for "
                f"{exam.exam_id!r}. Refusing rather than answering about the wrong "
                "exam."
            )
        return part_of(self).in_percentile

    def guess_ev(self) -> float:
        """EV of guessing at random, from THIS section's per-answer marking.

        DELEGATED to `items.expected_ev`, which already existed. MEASURED
        2026-10-02: the first version of this computed
        `1/options + (options-1)/options * mark_wrong` -- it hardcoded `1.0` for a
        correct answer and so DROPPED `mark_correct` entirely. For the one case it
        was written to illustrate (CAT's reported +3/-1) it returned **-0.6000** when
        the truth is 3/5 + 4/5 x -1 = **-0.2000**. The XAT case was right only
        because XAT's `mark_correct` happens to be 1.0.

        Both agents reviewing the LLD caught it independently. A second
        implementation of a function that already exists is not a convenience, it is
        a second thing to be wrong.
        """
        from .items import expected_ev

        return expected_ev(options=self.options, mark_correct=self.mark_correct,
                           mark_wrong=self.mark_wrong)


@dataclass(frozen=True, slots=True)
class ExamSpec:
    """One exam, as measured from its own official notification.

    `counted_questions` is the DENOMINATOR for every raw-score claim, and it is
    separate from `total_questions` on purpose: XAT is 95 questions but only 75 of
    them are scored, because GK is excluded by XLRI (D7).
    """
    exam_id: str
    name: str
    edition: str
    total_questions: int
    counted_questions: int
    parts: tuple[str, ...]
    #: The edition this shape was VERIFIED against, and how. MEASURED 2026-10-02:
    #: it is October 2026, so the paper a learner actually sits is most likely
    #: XAT 2027. Hardcoding `edition="2026"` silently asserts that next year's paper
    #: has the same counts, marking and calculator policy. It must be re-verified
    #: against that year's brochure, and this says so in data rather than in prose.
    verified_against: str = ""
    #: What `verified_against` is: OFFICIAL / MEASURED / SECONDARY / ASSUMPTION.
    evidence: str = "OFFICIAL"

    def sections(self) -> tuple[str, ...]:
        """Every section, in paper order."""
        out: list[str] = []
        for pid in self.parts:
            out.extend(part_of_id(self.exam_id, pid).sections)
        return tuple(out)

    def counted(self) -> tuple[str, ...]:
        """The sections that carry a raw score, in paper order.

        Derived from the PART, never stored. XAT's counted sections are QA&DI +
        VA&LR + DM = 75; GK is 20 and excluded by XLRI. MEASURED 2026-10-02:
        keeping this as a stored flag let GK be "in" the percentile on one line and
        out on another, with nothing to notice.
        """
        out: list[str] = []
        for pid in self.parts:
            part = part_of_id(self.exam_id, pid)
            if part.in_percentile:
                out.extend(part.sections)
        return tuple(out)

    def part_minutes(self) -> int:
        """Minutes shared by the COUNTED sections. XAT 2026: 170 for all of Part 1.

        A METHOD, not a field: with more parts the number belongs to whichever part
        is scored, and a stored total would have to be updated by hand when a second
        part appears.
        """
        return sum(part_of_id(self.exam_id, pid).minutes
                   for pid in self.parts
                   if part_of_id(self.exam_id, pid).in_percentile)


#: Every exam this project knows the SHAPE of. ONE entry today, on purpose: the
#: owner ruled (2026-10-02) that XAT is completed before any other exam is added, so
#: the layers above are modelled and proven with a single key rather than populated
#: with content nobody has verified.
#:
#: MEASURED from XLRI's own 2026 notification, not from a coaching site.
#: `verified_against` / `evidence` record that. See `ExamSpec.evidence`.
EXAMS: dict[str, ExamSpec] = {
    "xat": ExamSpec(
        exam_id="xat",
        name="XAT",
        edition="2026",
        total_questions=95,
        counted_questions=75,
        parts=("part_1", "part_2"),
        verified_against="XLRI Important Instructions, XAT 2026",
        evidence="OFFICIAL",
    ),
}

#: Every PART, keyed `"<exam>:<part>"`.
#:
#: Part 1 is ONE pool of 75 questions in 170 minutes with NO sectional limit, and
#: the eight free blanks are counted across all of it -- that is why this type
#: exists. Part 2 is GK: 20 questions, 10 minutes, no negative marking, and EXCLUDED
#: from the percentile.
PARTS: dict[str, PartSpec] = {
    "xat:part_1": PartSpec(
        part_id="part_1", exam_id="xat", name="Part 1",
        sections=("qa_di", "va_lr", "dm"),
        questions=75, minutes=170, in_percentile=True,
        blank_penalty=-0.10, blank_penalty_after=8,
    ),
    "xat:part_2": PartSpec(
        part_id="part_2", exam_id="xat", name="Part 2: General Knowledge",
        sections=("gk",), questions=20, minutes=10, in_percentile=False,
    ),
}

#: Every section, by `"<exam>:<section>"`. Keyed that way so a section id is never
#: ambiguous across exams -- CAT has its own `di`, and `"di"` alone would collide.
#:
#: No `minutes` and no blank penalty here: both belong to the PART. See `PartSpec`.
SECTIONS: dict[str, SectionSpec] = {
    "xat:qa_di": SectionSpec(
        section_id="qa_di", exam_id="xat", part_id="part_1", name="QA&DI",
        questions=28, calculator=True, built=True,
    ),
    "xat:va_lr": SectionSpec(
        section_id="va_lr", exam_id="xat", part_id="part_1", name="VA&LR",
        questions=26,
    ),
    "xat:dm": SectionSpec(
        section_id="dm", exam_id="xat", part_id="part_1", name="DM", questions=21,
    ),
    "xat:gk": SectionSpec(
        section_id="gk", exam_id="xat", part_id="part_2", name="GK", questions=20,
    ),
}


def part_of_id(exam_id: str, part_id: str) -> PartSpec:
    try:
        return PARTS[f"{exam_id}:{part_id}"]
    except KeyError:
        raise KeyError(f"no part {exam_id}:{part_id}; have {sorted(PARTS)}") from None


def part_of(section: SectionSpec) -> PartSpec:
    """The `PartSpec` a section belongs to. Checks BOTH directions.

    MEASURED 2026-10-02: with `SECTIONS["xat:qa_di"]` rewritten to carry
    `exam_id="cat"`, the join returned the CAT spec for an XAT section with no
    error -- the key said one exam, the value another, and only one was read. A join
    that is a convention is a join that drifts.
    """
    spec = part_of_id(section.exam_id, section.part_id)
    if spec.exam_id != section.exam_id:
        raise KeyError(
            f"SECTIONS[{section.exam_id}:{section.section_id}] claims part "
            f"{section.part_id!r}, whose PARTS entry belongs to "
            f"{spec.exam_id!r}. Refusing rather than borrowing another exam's rules."
        )
    return spec


def section_of(topic: Topic) -> SectionSpec:
    """The `SectionSpec` a topic belongs to. Raises if it names one that is absent.

    Keyed by `exam_id` and `section_id` together rather than trusting the id alone,
    so `topic.section_id` naming another exam's section is a `KeyError` rather than
    a silently borrowed marking scheme.
    """
    key = f"{topic.exam_id}:{topic.section_id}"
    try:
        spec = SECTIONS[key]
    except KeyError:
        raise KeyError(
            f"topic {topic.id!r} declares section {key}, which is not in "
            f"SECTIONS. Known: {sorted(SECTIONS)}"
        ) from None
    # BOTH directions. MEASURED 2026-10-02: with SECTIONS["xat:qa_di"] rewritten to
    # carry exam_id="cat", `section_of(geo_mens)` returned the CAT spec with no
    # error -- the key said xat, the value said cat, and only one of them was read.
    # The join was a convention rather than a check, which is the thing that drifts.
    if spec.exam_id != topic.exam_id:
        raise KeyError(
            f"SECTIONS[{key!r}] claims exam {spec.exam_id!r}, so its key and its "
            f"value disagree. Refusing rather than borrowing another exam's "
            "marking."
        )
    part_of(spec)  # the section must also name a part that agrees with its exam
    return spec
