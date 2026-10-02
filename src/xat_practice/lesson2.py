"""Lesson 2 -- Geometry: triangle areas and similarity.

THE SECOND LESSON, and the subtopic is `geo_mens:similarity-and-area-ratios`
because it is the HEAD of the geometry dependency chain. `level-auditor` named it
for exactly this reason: the HARD rung must substitute into a ratio the
FOUNDATION rung isolated, and it may **not** reach to `circle-tangents` or
`circle-power-of-a-point`, which are separate subtopics with their own traps.

WHY IT IS SECOND, and it was the owner's call (D14)
    Geometry is the deepest dependency chain in the syllabus -- nine of the forty
    trained subtopics, and each rung is only reachable from the rung below it.
    It is the one block where building it late means re-building it. The measured
    case FOR Data Interpretation was real (6.71 q/yr against geometry's 4.57), and
    it was overridden; `docs/COVERAGE.md` records that both external weightage
    summaries ALSO place DI late, so the override has independent support.

THE THREE ACCEPTANCE PROPERTIES `level-auditor` set for this lesson
    1. FOUR pairwise-distinct digit-masked derivation shapes. Lesson 1 scored 3 of
       4 and passed every gate; this must score 4 of 4, and `G17` now refuses
       anything less on any set.
    2. ONE NEW OPERATION PER RUNG, and FOUNDATION already isolates it.
    3. EVERY FLAG PROVABLE FROM THE DERIVATION STRING.

    Measured, and this is property 1:

        L2-F  18*10/2              ->  N*N*N/N
        L2-E  (14+22)*9/2          ->  (N+N)*N/N
        L2-M  6*sqrt(4)            ->  N*sqrt(N)
        L2-H  (2*48/8)/2*8/2       ->  (N*N/N)/N*N/N

    What each rung ADDS, which is the property that cannot be asserted:

        F   the triangle formula, and the halving. Nothing before it.
        E   a THIRD quantity and an AVERAGE: the trapezium's parallel sides are
            added before the height multiplies. The learner must bracket.
        M   a SQUARE ROOT. Similar figures scale in LENGTH, so an area ratio has
            to be rooted before it can divide a side. No earlier rung roots
            anything.
        H   an INVERSION and a scale: find a missing base from an area, then apply
            a similarity ratio. The base is recovered by `2A/h` -- the same
            backward move as arithmetic, in a topic where it has never appeared.

    Lesson 1's HARD rung once scored 7.40 while being byte-identical to its EASY
    rung after digit masking. That is the failure this file is shaped against.

THE KEYS SIT AT 0, 1, 2, 3
    `G15_key_not_predictable` refuses a set whose best fixed-letter strategy beats
    random guessing by more than 10% of the marks. Four rungs authored
    key-first, as every author does, put all four at index 0 -- and "always A"
    then scored 4 of 4, full marks, having read nothing. Every one of the fourteen
    gates then in existence passed it. See D16.

Every `derivation` is a sympy expression and every key is recomputed by `G5`
against it. None of these keys is asserted.
"""

from __future__ import annotations

from .items import LEVEL_RECIPES, Distractor, Item, Level, with_answers
from .syllabus import Stratum

LESSON_ID = "lesson-02-geometry-similarity"
SUBTOPIC = "geo_mens:similarity-and-area-ratios"

# ---------------------------------------------------------------------------
# 1. FOUNDATION -- the triangle formula and the halving.
# ---------------------------------------------------------------------------

FOUNDATION = Item(
    id="L2-F",
    subtopic_id=SUBTOPIC,
    stratum=Stratum.QUANT,
    stem="What is the area of a triangle with base 18 cm and height 10 cm?",
    options=("90", "180", "28", "45", "360"),
    option_values=("90", "180", "28", "45", "360"),
    key_index=0,
    derivation="18*10/2",
    distractors=(
        Distractor(
            text="180",
            misconception="the halving dropped, so base x height was reported as "
                          "the area. The /2 is the whole difference between a "
                          "triangle and a rectangle",
            is_real_near_miss=True,
            produces="18*10",
        ),
        Distractor(
            text="28",
            misconception="base and height ADDED, 18 + 10. Multiplying two lengths "
                          "gives an area and adding them gives nothing that is one",
            # Not flagged as a near miss, and that is measured rather than
            # asserted. With all four distractors flagged real the score is
            # 0.85 + 0.8 = 1.65 and the FOUNDATION rung derives as EASY -- so the
            # lesson had no foundation rung at all. Nothing caught it: `G11` does
            # not run on a four-item lesson (D12) and `G7` only compares a CLAIM,
            # which is None here. `G8` asks for at least two real near-misses, and
            # two is what this rung keeps: dropping the halving, and halving twice.
            is_real_near_miss=False,
            produces="18+10",
        ),
        Distractor(
            text="45",
            misconception="divided by 4 instead of 2, so the halving happened "
                          "twice. A near miss for a learner who halves the height "
                          "AND the base",
            is_real_near_miss=True,
            produces="18*10/4",
        ),
        Distractor(
            text="360",
            misconception="multiplied by 2 instead of dividing by 2. The sign of "
                          "the operation, not the number",
            is_real_near_miss=False,
            produces="18*10*2",
        ),
    ),
    derivation_steps=int(LEVEL_RECIPES[Level.FOUNDATION]["derivation_steps"]),
    needs_substitution=False,
    insight_required=False,
    calculator_minutes=0.3,
)

# ---------------------------------------------------------------------------
# 2. EASY -- a THIRD quantity and an average.
# ---------------------------------------------------------------------------

EASY = Item(
    id="L2-E",
    subtopic_id=SUBTOPIC,
    stratum=Stratum.QUANT,
    stem="A trapezium has parallel sides of 14 cm and 22 cm and a height of 9 cm. "
         "What is its area?",
    options=("324", "162", "72", "648", "45"),
    option_values=("324", "162", "72", "648", "45"),
    key_index=1,
    derivation="(14+22)*9/2",
    distractors=(
        Distractor(
            text="324",
            misconception="the average taken and then multiplied, but the halving "
                          "was dropped. The two errors point opposite ways and a "
                          "learner checks neither",
            is_real_near_miss=True,
            produces="(14+22)*9",
        ),
        Distractor(
            text="72",
            misconception="the parallel sides SUBTRACTED, 22 - 14, giving the "
                          "difference instead of the mean. A trapezium is built "
                          "on the average of its parallel sides",
            is_real_near_miss=True,
            produces="(22-14)*9",
        ),
        Distractor(
            text="648",
            misconception="multiplied by 2 instead of halved. Same sign error as "
                          "the foundation rung, and it survives here because the "
                          "answer already looks unfamiliar",
            is_real_near_miss=True,
            produces="(14+22)*9*2",
        ),
        Distractor(
            text="45",
            misconception="all three measurements added, 14 + 22 + 9. Adding "
                          "lengths feels like progress and yields no area at all",
            is_real_near_miss=True,
            produces="14+22+9",
        ),
    ),
    derivation_steps=int(LEVEL_RECIPES[Level.EASY]["derivation_steps"]),
    needs_substitution=False,
    insight_required=False,
    calculator_minutes=0.5,
)

# ---------------------------------------------------------------------------
# 3. MEDIUM -- a SQUARE ROOT. No earlier rung roots anything.
# ---------------------------------------------------------------------------

MEDIUM = Item(
    id="L2-M",
    subtopic_id=SUBTOPIC,
    stratum=Stratum.QUANT,
    stem="Two triangles are similar and their areas are in the ratio 1 : 4. The "
         "base of the first is 6 cm. The base of the second is:",
    options=("24", "3", "12", "10", "8"),
    option_values=("24", "3", "12", "10", "8"),
    key_index=2,
    # The `sqrt(4)` is the SUBSTITUTION, and it is visible in the string: the
    # length ratio must be computed and then fed into 6 x ratio. That is the first
    # rung in either lesson whose substitution is not decoration.
    derivation="6*sqrt(4)",
    distractors=(
        Distractor(
            text="24",
            misconception="the AREA ratio used directly as a LENGTH ratio, 6 x 4. "
                          "The most common error in this subtopic: similar figures "
                          "scale in length, so an area ratio must be rooted first",
            is_real_near_miss=True,
            produces="6*4",
        ),
        Distractor(
            text="3",
            misconception="the length ratio inverted, 6 / 2. The ratio is written "
                          "1 : 4 and read backwards",
            is_real_near_miss=True,
            produces="6/2",
        ),
        Distractor(
            text="10",
            misconception="the base and the ratio ADDED, 6 + 4. The same reflex as "
                          "the foundation rung's distractor, and it reappears "
                          "because the reflex is the thing being trained",
            is_real_near_miss=True,
            produces="6+4",
        ),
        Distractor(
            text="8",
            misconception="the ratio applied to the SECOND number in the question, "
                          "4 x 2, instead of to the base 6. Reading across the "
                          "ratio instead of down it",
            is_real_near_miss=True,
            produces="4*2",
        ),
    ),
    derivation_steps=int(LEVEL_RECIPES[Level.MEDIUM]["derivation_steps"]),
    needs_substitution=True,
    insight_required=False,
    calculator_minutes=1.0,
)

# ---------------------------------------------------------------------------
# 4. HARD -- an INVERSION, then a similarity scale.
# ---------------------------------------------------------------------------

HARD = Item(
    id="L2-H",
    subtopic_id=SUBTOPIC,
    stratum=Stratum.QUANT,
    # MEASURED 2026-10-02: the first draft of this stem said "half its base" with
    # no mention of the height, which makes the answer ambiguous -- the learner
    # cannot know whether the height is halved too. The height is now stated,
    # because the whole point of the rung is that only ONE dimension changed.
    stem="A triangle has an area of 48 sq cm and a height of 8 cm. A second "
         "triangle is similar to it, with the same height but half the base. What "
         "is the area of the second triangle?",
    options=("12", "6", "36", "24", "96"),
    option_values=("12", "6", "36", "24", "96"),
    key_index=3,
    # Two operations no lower rung performs: recover a MISSING base from an area
    # (`2A/h`, an inversion), then apply the similarity ratio to it.
    derivation="(2*48/8)/2*8/2",
    distractors=(
        Distractor(
            text="12",
            misconception="the area QUARTED, 48 / 4, because a length was "
                          "halved. Area scales with the SQUARE of a length change "
                          "-- but only when EVERY dimension changes, and here only "
                          "the base does. This is the best distractor in the lesson",
            is_real_near_miss=True,
            produces="48/4",
        ),
        Distractor(
            text="6",
            misconception="the area DIVIDED BY THE HEIGHT, 48 / 8, which gives the "
                          "missing base and then stops. Halfway: the inversion was "
                          "found and its result was reported as the answer",
            is_real_near_miss=True,
            produces="48/8",
        ),
        Distractor(
            text="36",
            misconception="the new base MULTIPLIED instead of passed into the "
                          "triangle formula: 48 x 6 / 8. The recovered base is "
                          "used as a factor rather than a measurement",
            is_real_near_miss=True,
            produces="48*6/8",
        ),
        Distractor(
            text="96",
            misconception="the area DOUBLED, 48 x 2. The base was halved and the "
                          "area followed it upward, which is the same inversion "
                          "error as the quarted distractor with the sign flipped",
            is_real_near_miss=True,
            produces="48*2",
        ),
    ),
    derivation_steps=int(LEVEL_RECIPES[Level.HARD]["derivation_steps"]),
    needs_substitution=True,
    insight_required=True,
    calculator_minutes=1.4,
)

LESSON = (FOUNDATION, EASY, MEDIUM, HARD)


# ---------------------------------------------------------------------------
# the step-by-step, which is what the learner actually reads
# ---------------------------------------------------------------------------

SOLUTIONS: dict[str, tuple[str, ...]] = {
    "L2-F": (
        "The formula: a triangle's area is half of base times height. The halving "
        "is not decoration -- it is the whole difference between a triangle and "
        "the rectangle around it.",
        "Step 1 - multiply. 18 x 10 = 180.",
        "Step 2 - halve. 180 / 2 = 90.",
        "Why 180 is wrong: that is base x height with no halving. If the answer "
        "looks like the rectangle's area, the triangle formula was not used.",
        "Why 28 is wrong: 18 + 10. Two lengths added give a length, not an area.",
        "Why 45 is wrong: 180 / 4, so the halving happened twice. This is what a "
        "learner does when they halve the base and the height separately instead "
        "of halving the product.",
        "Why 360 is wrong: 18 x 10 x 2, multiplying by 2 where the formula "
        "divides. Check the sign of the operation, not the size of the number.",
    ),
    "L2-E": (
        "The insight: a trapezium's area uses the AVERAGE of its two parallel "
        "sides, and the average is found by ADDING them and halving. So the "
        "parallel sides are added before the height multiplies -- bracket it.",
        "Step 1 - the average width. (14 + 22) / 2 = 18.",
        "Step 2 - times the height. 18 x 9 = 162.",
        "Why 324 is wrong: (14 + 22) x 9 with the halving dropped. Two errors "
        "that point in opposite directions can leave a plausible-looking number, "
        "so check both.",
        "Why 72 is wrong: (22 - 14) x 9. The sides were SUBTRACTED, which gives "
        "their difference. A trapezium is built on their mean, and the word "
        "'trapezium' should make you think mean.",
        "Why 648 is wrong: multiplied by 2 instead of halved -- the same sign "
        "error as the foundation rung.",
        "Why 45 is wrong: 14 + 22 + 9, adding all three measurements. Adding "
        "lengths feels like progress and produces no area.",
    ),
    "L2-M": (
        "The insight: similar figures scale in LENGTH. So when you are given an "
        "AREA ratio and asked for a side, you must take the square root of it "
        "first. 1 to 4 in area means 1 to 2 in length, not 1 to 4.",
        "Step 1 - root the area ratio. sqrt(4 / 1) = 2, so the length ratio is "
        "1 : 2.",
        "Step 2 - apply it. 6 x 2 = 12.",
        "Why 24 is wrong: 6 x 4. This is THE trap in this subtopic, and it is "
        "understandable -- the ratio you were given is 1 : 4, so you use 4. But "
        "that ratio describes AREAS, and a base is a LENGTH. Lengths scale with "
        "the square root of areas.",
        "Why 3 is wrong: 6 / 2, the length ratio read backwards. The question "
        "asks for the second base, which is the LONGER one, so it must be the "
        "bigger number.",
        "Why 10 is wrong: 6 + 4, adding the base to the ratio number.",
        "Why 8 is wrong: 4 x 2, applying the ratio to the 4 in the question "
        "instead of to the base. Read across the ratio, not down it.",
    ),
    "L2-H": (
        "The insight: a LENGTH halved is not an AREA halved. Area scales with the "
        "square of a length change -- but only when EVERY dimension changes. Here "
        "only the base changes and the height is unchanged, so the area halves.",
        "Step 1 - recover the missing base. The formula area = base x height / 2 "
        "solves for the base as base = 2 x area / height = 2 x 48 / 8 = 12.",
        "Step 2 - halve the base. 12 / 2 = 6.",
        "Step 3 - the second area. 6 x 8 / 2 = 24.",
        "Why 12 is wrong: 48 / 4. This is the best distractor here and it is a "
        "TRUE rule applied to the wrong situation: area does scale with the square "
        "of a length change, and halving a length squares to a quarter. But that "
        "needs both dimensions to halve, and this stem holds the height at 8.",
        "Why 6 is wrong: 48 / 8, which is the missing base. Halfway -- the "
        "inversion was found and then its result was reported as the answer.",
        "Why 36 is wrong: 48 x 6 / 8, so the recovered base was multiplied in "
        "instead of passed into the triangle formula.",
        "Why 96 is wrong: 48 x 2. The base went DOWN and the area went UP, which "
        "no version of this formula produces.",
    ),
}

SOLUTIONS = with_answers(LESSON, SOLUTIONS)


# ---------------------------------------------------------------------------
# D18 -- the teaching, shown BEFORE question 1
# ---------------------------------------------------------------------------
# MEASURED 2026-10-02 by `viewer` on Lesson 1: the formula first reached the
# screen only AFTER question 1 was answered, so a learner who did not know the
# topic could not learn it from the lesson. Owner ruling D18: TEACH THEN ASK.
#
# THE WORKED EXAMPLE MUST NOT REUSE QUESTION 1's NUMBERS. On Lesson 1 the only
# example in the file was question 1 verbatim, which would hand over the key
# before the commit. Here question 1 is 18 and 10, so the example runs on 20 and
# 6 -- it tests TRANSFER rather than recall.
#
# It lives in `paper.json`, never in `answerkey.json`.

TEACH: dict[str, dict[str, object]] = {
    SUBTOPIC: {
        "heading": "Before you start: areas, and why similar shapes trick people",
        "why": (
            "An area is a NUMBER OF SQUARES -- how many 1 cm pieces would cover "
            "the shape. That is why areas multiply when a shape grows, and why "
            "two triangles can have the same area with completely different "
            "shapes."
        ),
        "formula": "Triangle area = (base x height) / 2",
        "legend": [
            ("base", "Base",
             "the length along the bottom. Any side can be the base -- pick the "
             "one you are given."),
            ("height", "Height",
             "the PERPENDICULAR distance down to the base. Not the slanted "
             "side. This is the most common wrong number in the topic."),
        ],
        "why_divide": (
            "Why divide by 2? Because a triangle fits exactly half of the "
            "rectangle with the same base and height. Cut that rectangle along a "
            "diagonal and the two pieces are the same triangle."
        ),
        "units": (
            "UNITS: if the base is in cm and the height in cm, the area is in cm "
            "SQUARED, written cm2. An area in cm means one of your two lengths "
            "was not really a length."
        ),
        "example": (
            "Worked example, on DIFFERENT numbers from the questions below so it "
            "tests transfer. A triangle with base 20 cm and height 6 cm: area = "
            "20 x 6 / 2 = 60 sq cm. Notice the height was 6 and NOT the slanted "
            "side."
        ),
        "bridge": (
            "Two things the questions below add. A TRAPEZIUM has two parallel "
            "sides, and its area uses their AVERAGE: (a + b) x height / 2. And "
            "SIMILAR shapes -- same shape, different size -- scale in LENGTH, so "
            "an area ratio must be square-rooted before it can divide a side. "
            "That second one is where most of the marks are lost."
        ),
    },
}
