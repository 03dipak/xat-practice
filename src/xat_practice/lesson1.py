"""Lesson 1 -- Simple Interest, one subtopic, four levels.

This module is the worked example the whole product is built around, and it is
deliberately the EASIEST possible instance of the shape, because if the shape
is wrong it will be wrong here first and most legibly.

THE SHAPE (PEDAGOGY.md 1)
    One subtopic. Four levels. Each rung is reachable from the one below it,
    because the hard rung's only extra step is the one the foundation rung
    isolated. `LESSON_SHAPE` is 4 questions, 1 per level, and `subtopic_id` is
    the same on all four -- asserted by `test_lesson_is_one_subtopic_four_levels`.

WHY SIMPLE INTEREST IS THE FIRST LESSON
    It is `pl_int:simple-interest`, a P1 subtopic (SI is inside
    Profit/Loss/Interest at 1.86 q/yr, the most consistent earner after
    geometry), and it is nearly prerequisite-free: one formula, three
    variables, no diagram, no algebra. Every one of the mistakes below is a
    MISTAKE ABOUT WHAT THE FORMULA MEANS, not about arithmetic. That is the
    right first lesson, because the thing being trained is the reading of the
    formula, and reading a formula is the skill every later topic reuses.

THE FOUR ITEMS AND WHY EACH IS HARD
    FOUNDATION  the formula, one move. Its two real distractors are the two
                ways to read the formula wrongly: the rate applied to the
                amount instead of the principal, and the time read off by one.
    EASY        the same formula plus the SI->amount step, and the distractors
                now include COMPOUNDING, which is the single most common
                XAT quant error in this topic.
    MEDIUM      two sums, one ratio, and the insight is that the ratio cannot
                be read off the interest ratio. The distractors are both
                directions of a dropped division.
    HARD        an instalment problem where the insight is that the interest
                must be split across instalments rather than paid once. The
                distractors include SUBTRACTING the interest, which is the sign
                error this topic produces most reliably.

Every `derivation` is a sympy expression and every key is checked by G5 against
it. None of these keys is asserted; see `test_lesson1_every_key_is_recomputed`.
"""

from __future__ import annotations

import sympy as sp

from .items import LEVEL_RECIPES, Distractor, Item, Level
from .syllabus import Stratum

LESSON_ID = "lesson-01-simple-interest"
SUBTOPIC = "pl_int:simple-interest"

R = sp.Rational

# ---------------------------------------------------------------------------
# 1. FOUNDATION -- one move. SI = PRT/100.
# ---------------------------------------------------------------------------

FOUNDATION = Item(
    id="L1-F",
    subtopic_id=SUBTOPIC,
    stratum=Stratum.QUANT,
    stem="What simple interest does a principal of Rs 1,000 earn at 10% per "
         "annum for 2 years?",
    options=("Rs 200", "Rs 220", "Rs 100", "Rs 1,200", "Rs 120"),
    option_values=(
        "200",
        "220",
        "100",
        "1200",
        "120",
    ),
    key_index=0,
    derivation="1000*10*2/100",
    distractors=(
        Distractor(
            text="Rs 220",
            misconception="the rate applied to the AMOUNT rather than the "
                          "principal, i.e. 1000 x 11 x 2 / 100 -- the same "
                          "shape as compounding",
            is_real_near_miss=True,
        ),
        Distractor(
            text="Rs 100",
            misconception="the time read as 1 year instead of 2, which is what "
                          "happens when a year count is skimmed",
            is_real_near_miss=True,
        ),
        Distractor(
            text="Rs 1,200",
            misconception="the principal added to the interest, so an AMOUNT "
                          "was returned where the question asked for the "
                          "interest. Reading the question's noun",
            is_real_near_miss=False,
        ),
        Distractor(
            text="Rs 120",
            # MEASURED 2026-10-02: this text said "the percentage left
            # un-divided by 100, so 1,000 x 10 x 2 was never scaled down", and
            # 1,000 x 10 x 2 is 20,000 -- not 120. The stated cause did not
            # produce the option, which `key-auditor` did not catch and which
            # every gate had passed. The move that DOES produce 120 is adding
            # the rate and the time instead of multiplying them.
            misconception="the rate and the time ADDED instead of multiplied, so "
                          "1000 x (10 + 2) / 100 = 120. On a two-year sum, 10 and "
                          "2 look like neighbours on the page and an addition "
                          "reads as naturally as a multiplication",
            is_real_near_miss=False,
        ),
    ),
    derivation_steps=int(LEVEL_RECIPES[Level.FOUNDATION]["derivation_steps"]),
    needs_substitution=False,
    insight_required=False,
    calculator_minutes=0.4,
)

# ---------------------------------------------------------------------------
# 2. EASY -- the same formula, then principal + interest. The trap is
#    COMPOUNDING, which is the most common error in this topic.
# ---------------------------------------------------------------------------

EASY = Item(
    id="L1-E",
    subtopic_id=SUBTOPIC,
    stratum=Stratum.QUANT,
    stem="Rs 10,000 is invested at 5% per annum simple interest. What is the "
         "amount owed after 2 years?",
    options=("Rs 1,000", "Rs 11,000", "Rs 10,500", "Rs 11,025", "Rs 12,000"),
    option_values=(
        "1000",
        "11000",
        "10500",
        "11025",
        "12000",
    ),
    key_index=1,
    derivation="10000 + 10000*5*2/100",
    distractors=(
        Distractor(
            text="Rs 1,000",
            misconception="the simple interest reported where the question "
                          "asked for the amount, i.e. the SI computed correctly "
                          "and then stopped one line early",
            is_real_near_miss=True,
        ),
        Distractor(
            text="Rs 11,025",
            misconception="COMPOUNDED: 10000 x 1.05^2 instead of "
                          "10000 + 10000 x 5 x 2 / 100. The single most common "
                          "error in this topic -- simple interest never "
                          "multiplies the principal by (1+r)^t",
            is_real_near_miss=True,
        ),
        Distractor(
            # MEASURED 2026-10-02: this was Rs 10,250 while both the
            # misconception and the step-by-step said the move is 10,000 x 5 / 100,
            # which is 10,500. A digit transposition in the option, the same
            # disease as Rs 14,700. The option now equals the move it names.
            text="Rs 10,500",
            misconception="the rate applied once instead of for the full 2 "
                          "years, i.e. the time count dropped, so 10,000 x 5 / 100 "
                          "= 500 and not the full 1,000",
            is_real_near_miss=True,
        ),
        Distractor(
            # MEASURED 2026-10-02: this was Rs 10,200, but the move its own
            # misconception names -- the 5 read as 10 -- gives 10,000 + 2,000 =
            # 12,000. Four options in this lesson had an explanation that did
            # not produce them, and all four had passed every gate.
            text="Rs 12,000",
            misconception="the 5 divided by 10 rather than 100, so the rate "
                          "was read as 10% and the interest doubled to 2,000",
            is_real_near_miss=True,
        ),
    ),
    derivation_steps=int(LEVEL_RECIPES[Level.EASY]["derivation_steps"]),
    needs_substitution=False,
    insight_required=False,
    calculator_minutes=0.8,
)

# ---------------------------------------------------------------------------
# 3. MEDIUM -- two sums, one ratio. The insight is that the RATIO OF THE
#    INTERESTS is not the ratio of the principals.
# ---------------------------------------------------------------------------

MEDIUM = Item(
    id="L1-M",
    subtopic_id=SUBTOPIC,
    stratum=Stratum.QUANT,
    stem="A sum earns simple interest of Rs 1,440 at 8% per annum for 3 years. "
         "Another sum earns simple interest of Rs 2,160 at 12% per annum for "
         "2 years. What is the ratio of the first sum to the second?",
    options=("8 : 9", "1 : 1", "2 : 3", "1 : 2", "3 : 2"),
    option_values=(
        "8/9",
        "1",
        "2/3",
        "1/2",
        "3/2",
    ),
    key_index=2,
    derivation="(1440*100/(8*3)) / (2160*100/(12*2))",
    distractors=(
        Distractor(
            text="8 : 9",
            misconception="the principal of the first sum recovered as "
                          "1440x100/18 = 8,000 because 8x3 was collapsed to 18 "
                          "instead of multiplied as 8x3",
            is_real_near_miss=True,
        ),
        Distractor(
            text="1 : 2",
            misconception="the second principal recovered as "
                          "2160x100/18 = 12,000 by the same collapse, which "
                          "makes the answer too small",
            is_real_near_miss=True,
        ),
        Distractor(
            text="3 : 2",
            misconception="the interest ratio 2160 : 1440 used directly, with "
                          "the rates and times never inverted out. THE named "
                          "trap for this subtopic",
            is_real_near_miss=True,
        ),
        Distractor(
            # MEASURED 2026-10-02 by `key-auditor`, and confirmed by hand: the
            # option this replaces was 4 : 3, whose stated cause was "the
            # interest ratio inverted but not simplified". That is
            # ARITHMETICALLY IMPOSSIBLE -- 2160 : 1440 is 3 : 2 already in lowest
            # terms, so there is no unsimplified form to stop at -- and no ratio
            # of 1440 and 2160 equals 4 : 3 at all. A distractor that cannot be
            # REACHED is worse than none: a learner cannot rule it out, and the
            # explanation teaches a false rule.
            #
            # 1 : 1 is reachable and is a real mistake. Both sums have r x t = 24,
            # so 1,440 / 6,000 and 2,160 / 9,000 are BOTH 6/25, and a learner who
            # DIVIDES each interest by its principal instead of recovering the
            # principal gets a clean 1 : 1. The fact that the two rates coincide
            # is what makes this trap sharp, and it is the same coincidence that
            # weakens this item -- see the note in SOLUTIONS["L1-M"].
            text="1 : 1",
            misconception="each interest divided by its OWN principal instead of "
                          "the principal recovered from the formula, so "
                          "1440/6000 and 2160/9000 both came out 6/25 and the "
                          "ratio flattened to 1 : 1",
            is_real_near_miss=True,
        ),
    ),
    derivation_steps=int(LEVEL_RECIPES[Level.MEDIUM]["derivation_steps"]),
    needs_substitution=True,
    insight_required=False,
    calculator_minutes=1.6,
)

# ---------------------------------------------------------------------------
# 4. HARD -- an instalment problem. The insight is that simple interest is a
#    property of the WHOLE sum for the WHOLE time, so it splits across
#    instalments in the ratio of the time each covers. The sign error this
#    topic produces most reliably is SUBTRACTING the interest.
# ---------------------------------------------------------------------------

HARD = Item(
    id="L1-H",
    subtopic_id=SUBTOPIC,
    stratum=Stratum.QUANT,
    stem="A debt of Rs 12,000 is repaid in two equal annual instalments, and "
         "simple interest at 10% per annum is charged for the 2 years on the "
         "whole amount. The total repaid is:",
    options=("Rs 12,000", "Rs 9,600", "Rs 7,200", "Rs 14,400", "Rs 14,520"),
    option_values=(
        "12000",
        "9600",
        "7200",
        "14400",
        "14520",
    ),
    key_index=3,
    derivation="12000 + 12000*10*2/100",
    distractors=(
        Distractor(
            text="Rs 12,000",
            misconception="the interest IGNORED on the grounds that instalments "
                          "were 'equal', i.e. equal principal and nothing else",
            is_real_near_miss=True,
        ),
        Distractor(
            text="Rs 9,600",
            misconception="the interest SUBTRACTED, 12000 - 12000x10x2/100. The "
                          "sign error: the debt was repaid early, so the amount "
                          "owed is larger than the principal, not smaller",
            is_real_near_miss=True,
        ),
        Distractor(
            text="Rs 7,200",
            misconception="the interest halved as well as the principal, "
                          "treating two instalments as two half-sums each "
                          "accruing half the interest on half the time",
            is_real_near_miss=True,
        ),
        Distractor(
            # MEASURED 2026-10-02 by `key-auditor`, and confirmed by hand: this
            # was Rs 14,700, while its own stated cause, 12000 x 1.1^2, is
            # 14,520. No clean rule reaches 14,700 -- it needs r x t = 0.225.
            # The lesson handed the learner the arithmetic for one number while
            # labelling a different one, so a learner who followed the lesson
            # arrived at 14,520 and could not see why it had been rejected.
            text="Rs 14,520",
            misconception="the rate read as 10% per YEAR compounding, "
                          "12000 x 1.1 x 1.1 = 14,520, instead of simple "
                          "interest on the full sum for 2 years",
            is_real_near_miss=True,
        ),
    ),
    derivation_steps=int(LEVEL_RECIPES[Level.HARD]["derivation_steps"]),
    needs_substitution=True,
    insight_required=True,
    calculator_minutes=1.9,
)

LESSON = (FOUNDATION, EASY, MEDIUM, HARD)

#: The step-by-step shown after a learner commits. Written as data so the
#: bundle renderer does not have to know how to teach, and so
#: `doc-reviewer` can check a solution against a derivation.
SOLUTIONS: dict[str, tuple[str, ...]] = {
    "L1-F": (
        "Simple interest is SI = P x R x T / 100. The subject never mentions an "
        "amount, so interest is the whole answer.",
        "Step 1 - identify the three variables. P = 1,000. R = 10% per annum, "
        "and T = 2 years, so P x R x T = 1,000 x 10 x 2 = 20,000.",
        "Step 2 - divide by 100 once. The rate is written as 10, not 0.10, so "
        "the /100 is still owed: 20,000 / 100 = 200.",
        "Why Rs 220 is wrong: that is 1,000 x 11 x 2 / 100. The 11 comes from "
        "1,000 + 10% of 1,000. That is compounding one year's interest into the "
        "principal, and it is the most common wrong answer in this entire topic.",
        "Why Rs 100 is wrong: 1,000 x 10 x 1 / 100. One year instead of two -- "
        "the year count was skimmed and only the first year was used.",
        "Why Rs 1,200 is wrong: 1,000 + 200. That is the AMOUNT, not the "
        "interest. Read the noun the question uses: it asks what interest is "
        "EARNED, so the principal is not part of the answer.",
        "Why Rs 120 is wrong: 1,000 x (10 + 2) / 100 = 120. The rate and the "
        "time were ADDED. On a two-year sum, 10 and 2 sit near each other on the "
        "page and an addition reads as naturally as a multiplication -- the "
        "formula needs 10 x 2 = 20, and 10 + 2 = 12 silently halves the time.",
    ),
    "L1-E": (
        "Same formula, then one more step: an amount is the principal PLUS the "
        "interest. Watch for that word -- it is the difference between the key "
        "and the first distractor.",
        "Step 1 - interest. 10,000 x 5 x 2 = 100,000, divided by 100 = 1,000.",
        "Step 2 - amount. 10,000 + 1,000 = 11,000.",
        "Why Rs 11,025 is wrong: 10,000 x 1.05 x 1.05. That is COMPOUND "
        "interest, and the difference from 11,000 is only 25 -- which is exactly "
        "why it is dangerous. It feels close enough to be right. Simple "
        "interest never multiplies the principal by (1 + r) to the power t.",
        "Why Rs 12,000 is wrong: 10,000 + 10,000 x 10 x 2 / 100 = 12,000. The "
        "5 was divided by 10 instead of 100, so the rate was read as 10% and the "
        "interest doubled.",
        "Why Rs 1,000 is wrong: that is the interest, correctly computed, and "
        "then the principal was never added. The question asked for an amount.",
        "Why Rs 10,500 is wrong: 10,000 + 10,000 x 5 / 100 = 10,500. The 5% was "
        "applied for one year only, so the 2 in the formula was dropped. If you "
        "find yourself using only one of the years, check the time you read.",
    ),
    "L1-M": (
        "The insight: the ratio of two INTERESTS is not the ratio of two "
        "PRINCIPALS. You must recover each principal first, and the recovery "
        "is the algebraic inverse of the same formula.",
        "Step 1 - invert. SI = P x R x T / 100 becomes P = SI x 100 / (R x T).",
        "Step 2 - first principal. 1,440 x 100 / (8 x 3) = 144,000 / 24 = 6,000.",
        "Step 3 - second principal. 2,160 x 100 / (12 x 2) = 216,000 / 24 = "
        "9,000.",
        "Step 4 - the ratio. 6,000 : 9,000 = 2 : 3.",
        "Why 3 : 2 is wrong: that is 2,160 : 1,440, the interest ratio used "
        "directly with the rates and times never inverted out. It is the "
        "instinctive answer and it is wrong here because the two sums are on "
        "different rates AND different times.",
        "Why 8 : 9 is wrong: 1,440 x 100 / 18 = 8,000, where 8 x 3 was "
        "collapsed to 18 by addition. Multiplying and adding look similar on a "
        "small screen, and this is the error. Keep the brackets.",
        "Why 1 : 2 is wrong: 2,160 x 100 / 18 = 12,000 by the same collapse, so "
        "the second principal came out too big and the ratio too small.",
        "Why 1 : 1 is wrong: 1,440 / 6,000 and 2,160 / 9,000 are both 6/25, "
        "because BOTH sums have a rate-time product of 24. Dividing an interest "
        "by its own principal compares the two RATES, and the two rates happen "
        "to be equal here -- which is exactly why this item is a trap and not a "
        "shortcut.",
    ),
    "L1-H": (
        "The insight: simple interest belongs to the WHOLE sum for the WHOLE "
        "time. When the debt is repaid in instalments, that total interest is "
        "still owed in full -- the instalments only change WHEN you pay, not "
        "HOW MUCH interest there is.",
        "Step 1 - total interest on the whole sum. 12,000 x 10 x 2 / 100 = "
        "2,400. It does not matter that the debt is split; the rate applies to "
        "12,000 for 2 years either way.",
        "Step 2 - total repaid. 12,000 + 2,400 = 14,400. The instalments "
        "divide this total into two payments of 7,200; they do not change it.",
        "Why Rs 9,600 is wrong: 12,000 - 2,400. The sign. A debt you are "
        "repaying costs you MORE than you borrowed, never less. If the answer "
        "to 'how much do I repay' is below the principal, the sign is wrong.",
        "Why Rs 7,200 is wrong: that is one instalment, not the total. Both "
        "halves of the question -- the sum and the interest -- were halved, "
        "and the question asked for the total repaid.",
        "Why Rs 12,000 is wrong: instalments being equal means equal PAYMENTS. "
        "It does not mean the interest is zero, and it does not mean the "
        "principal is all that is owed.",
        "Why Rs 14,520 is wrong: 12,000 x 1.1 x 1.1 = 14,520, i.e. the rate "
        "compounded for two years on one balance. Simple interest is "
        "12,000 x 10 x 2 / 100 = 2,400 with no compounding, however the debt "
        "happens to be paid off.",
    ),
}


def _with_answers(items: tuple[Item, ...],
                  solutions: dict[str, tuple[str, ...]]) -> dict[str, tuple[str, ...]]:
    """Append the stated answer to every solution.

    Added because a solution that ends on a rejected distractor reads, to a
    learner scanning the last line, as if the last number were the answer. The
    final line is now the answer and nothing else.
    """
    out: dict[str, tuple[str, ...]] = {}
    for item in items:
        out[item.id] = solutions[item.id] + (f"ANSWER: {item.key_text}",)
    return out


SOLUTIONS = _with_answers(LESSON, SOLUTIONS)


def lesson() -> tuple[Item, ...]:
    return LESSON
