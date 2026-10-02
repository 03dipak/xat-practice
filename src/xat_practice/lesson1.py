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

from .items import LEVEL_RECIPES, Distractor, Item, Level, with_answers
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
            produces=(1000*11*2/100),
            misconception="the rate applied to the AMOUNT rather than the "
                          "principal, i.e. 1000 x 11 x 2 / 100 -- the same "
                          "shape as compounding",
            is_real_near_miss=True,
        ),
        Distractor(
            text="Rs 100",
            produces=(1000*10*1/100),
            misconception="the time read as 1 year instead of 2, which is what "
                          "happens when a year count is skimmed",
            is_real_near_miss=True,
        ),
        Distractor(
            text="Rs 1,200",
            produces=(1000 + 1000*10*2/100),
            misconception="the principal added to the interest, so an AMOUNT "
                          "was returned where the question asked for the "
                          "interest. Reading the question's noun",
            is_real_near_miss=False,
        ),
        Distractor(
            text="Rs 120",
            produces=(1000*(10+2)/100),
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
            produces=(10000*5*2/100),
            misconception="the simple interest reported where the question "
                          "asked for the amount, i.e. the SI computed correctly "
                          "and then stopped one line early",
            is_real_near_miss=True,
        ),
        Distractor(
            text="Rs 11,025",
            produces=(10000*(1+sp.Rational(5,100))**2),
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
            produces=(10000 + 10000*5*1/100),
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
            produces=(10000 + 10000*10*2/100),
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
    # MEASURED 2026-10-02: this item was REBUILT, and the reason is the whole
    # point of it. The previous version had both sums on a rate-time product of
    # 24 -- 8 x 3 and 12 x 2 -- so the interest ratio 1,440 : 2,160 WAS 2 : 3, and
    # so was the principal ratio 6,000 : 9,000. The lesson's headline claim,
    # "the ratio of two INTERESTS is not the ratio of two PRINCIPALS", was FALSE
    # for its own data, and a learner who skipped the recovery entirely landed on
    # the key by accident.
    #
    # Two changes fix it:
    #   1. the second sum is now 15% for 3 years, so r x t is 45 and the two ratios
    #      genuinely DIFFER: interest 1,440 : 2,160 is 2 : 3, principals 6,000 :
    #      4,800 is 5 : 4. The shortcut is now wrong, which is what makes the
    #      item worth the marks.
    #   2. the old "r x t collapsed to 18" distractor is replaced by one that
    #      REACHES 18 -- because 15 + 3 = 18. The old denominator was unreachable
    #      from anything in the item, so a learner could not rule the option out.
    stem="A sum earns simple interest of Rs 1,440 at 8% per annum for 3 years. "
         "Another sum earns simple interest of Rs 2,160 at 15% per annum for 3 "
         "years. What is the ratio of the first sum to the second?",
    options=("2 : 3", "8 : 15", "5 : 4", "1 : 2", "3 : 2"),
    option_values=(
        "2/3",
        "8/15",
        "5/4",
        "1/2",
        "3/2",
    ),
    key_index=2,
    derivation="(1440*100/(8*3)) / (2160*100/(15*3))",
    distractors=(
        Distractor(
            text="2 : 3",
            misconception="the interest ratio read straight off, 1,440 : 2,160. "
                          "This is THE trap for this subtopic and it used to be "
                          "the key by coincidence; the rates are now different "
                          "precisely so the shortcut cannot work",
            is_real_near_miss=True,
            produces="(1440)/(2160)",
        ),
        Distractor(
            text="8 : 15",
            misconception="each interest divided by its OWN principal instead of "
                          "the principal recovered from the formula: 1,440/6,000 "
                          "and 2,160/4,800 are 6/25 and 9/20",
            is_real_near_miss=True,
            produces="(1440/6000)/(2160/4800)",
        ),
        Distractor(
            text="1 : 2",
            misconception="the rate and the time on the second sum ADDED, 15 + 3 = "
                          "18, giving 2,160 x 100 / 18 = 12,000 and halving the "
                          "ratio. Multiplying and adding look alike on a small "
                          "screen; keep the brackets",
            is_real_near_miss=True,
            produces="(1440*100/(8*3))/(2160*100/(15+3))",
        ),
        Distractor(
            text="3 : 2",
            misconception="the interest ratio inverted, 2,160 : 1,440. Same wrong "
                          "idea as the first option, stated the other way round",
            is_real_near_miss=True,
            produces="(2160)/(1440)",
        ),
    ),
    derivation_steps=int(LEVEL_RECIPES[Level.MEDIUM]["derivation_steps"]),
    needs_substitution=True,
    insight_required=False,
    calculator_minutes=1.1,
)

HARD = Item(
    id="L1-H",
    subtopic_id=SUBTOPIC,
    stratum=Stratum.QUANT,
    stem="Simple interest on a sum for 3 years is 30% of the sum. At the same "
         "rate, what is the total amount after 5 years?",
    # MEASURED 2026-10-02, and this item is the SECOND attempt at the hard rung.
    #
    # The first one derived `12000 + 12000*10*2/100`, which digit-masks to
    # `N + N*N*N/N` -- IDENTICAL to L1-E. Changing only its flags and nothing a
    # learner sees dropped it from 7.40 to 2.50, the EASY tier. So 66% of its
    # difficulty was a declared flag with nothing in the derivation to prove it,
    # `G17` refused the lesson, and the rung was arithmetic with new numbers on
    # it.
    #
    # This one adds an OPERATION no lower rung performs: infer the RATE from a
    # stated interest, then re-apply it over a different time. The rate is never
    # given. Digit-masked this is `N + (N*N/(N*N))*N*N*N/N`, distinct from
    # `N*N*N/N`, `N + N*N*N/N` and `(N*N/(N*N)) / (N*N/(N*N))`.
    #
    # The trap it creates is the best one in the lesson: interest is linear in
    # time, so the tempting move is to take the 3-year figure and carry it.
    options=("Rs 1,300", "Rs 2,500", "Rs 1,750", "Rs 1,500", "Rs 700"),
    option_values=(
        "1300",
        "2500",
        "1750",
        "1500",
        "700",
    ),
    # key_index 3, which keeps the four rungs on four different letters. G15
    # refuses a set whose best fixed-letter strategy beats random guessing by
    # more than 10% of the marks, and this position is what lets it pass.
    key_index=3,
    # The parenthesised group is the SUBSTITUTION, and it is now visible in the
    # string rather than asserted: 300 x 100 / (1000 x 3) is computed first and
    # fed into the main formula as a rate.
    derivation="1000 + (300*100/(1000*3))*1000*5/100",
    distractors=(
        Distractor(
            text="Rs 1,300",
            misconception="the 3-year interest carried over untouched, 1,000 + 300. "
                          "Interest IS linear in time, which is exactly why this "
                          "feels right: the rate never has to be found at all",
            is_real_near_miss=True,
            produces=1000 + 300,
        ),
        Distractor(
            text="Rs 2,500",
            misconception="the 30% read as the ANNUAL rate, 1,000 + 1,000 x 30 x 5 "
                          "/ 100. The percentage was quoted for three years and "
                          "used for one",
            is_real_near_miss=True,
            produces=1000 + 1000 * 30 * 5 / 100,
        ),
        Distractor(
            text="Rs 1,750",
            misconception="the 30% halved to 15% to 'fit' a year, 1,000 + 1,000 x "
                          "15 x 5 / 100. Scaling a percentage without asking what "
                          "it was a percentage OF",
            is_real_near_miss=True,
            produces=1000 + 1000 * 15 * 5 / 100,
        ),
        Distractor(
            text="Rs 700",
            misconception="the interest SUBTRACTED, 1,000 - 300. A sum you are "
                          "adding to always ends above where it started",
            is_real_near_miss=True,
            produces=1000 - 300,
        ),
    ),
    derivation_steps=int(LEVEL_RECIPES[Level.HARD]["derivation_steps"]),
    needs_substitution=True,
    insight_required=True,
    calculator_minutes=1.6,
)


# ---------------------------------------------------------------------------
# D18 -- THE TEACHING, shown before the first question.
# ---------------------------------------------------------------------------
# The owner's flow was "question, options, answer, explanation". `viewer` found
# the cost of that ordering: the step-by-step renders only inside `check()`, so
# the formula first reached the screen AFTER question 1 was answered. A learner
# who does not know what simple interest IS cannot learn it from this lesson. For
# a "zero to pro" goal that is the whole product failing at step one.
#
# The owner chose TEACH THEN ASK. So this block is rendered first, and it needs
# four things a beginner does not have (MEASURED missing 3 of the 4):
#
#   1. the formula
#   2. what each SYMBOL MEANS  -- was absent entirely; nothing said principal is
#      "the money you start with"
#   3. one worked example
#   4. the UNITS rule           -- was absent, so a monthly rate can be dropped in
#      as annual and nothing on the page says that is illegal
#
# THE EXAMPLE MUST NOT REUSE QUESTION 1's NUMBERS. MEASURED, and this is the trap:
# the only worked example in the file was question 1 verbatim (1,000 at 10% for 2
# years -> 200). Reusing it hands over Q1's key BEFORE the commit and destroys Q1
# as a check. This one runs on 2,000 at 5% for 4 years -> 400, so it tests
# TRANSFER rather than recall, and `test_the_teaching_example_does_not_hand_over_
# question_ones_key` refuses it if the numbers ever converge.
#
# It lives in `paper.json`, not `answerkey.json`: it is shown before the learner
# commits, so putting it behind the commit barrier would mean it never appears
# until it is too late to help.

TEACH: dict[str, dict[str, object]] = {
    SUBTOPIC: {
        "heading": "Before you start: what simple interest is",
        "why": (
            "Lending or borrowing money has a cost, and this is the cost of "
            "borrowing. Simple interest charges you only on the ORIGINAL amount, "
            "every year, for as long as you keep it."
        ),
        "formula": "SI = P x R x T / 100",
        "legend": [
            ("P", "Principal", "the amount you start with. It never changes."),
            ("R", "Rate per annum", "the yearly rate, written as a number. 10% "
             "means you write 10."),
            ("T", "Time", "the number of YEARS. 2 means two years."),
        ],
        "why_divide": (
            "Why divide by 100? Because a rate of 10% means TEN IN EVERY HUNDRED. "
            "Writing 10 into the formula without dividing by 100 overstates "
            "everything by a factor of 100."
        ),
        "units": (
            "This is where marks are lost. R must be a rate "
            "PER YEAR and T must be in YEARS. If you are given a monthly rate, "
            "multiply it by 12 first. If you are given the time in months, divide "
            "it by 12. Never mix the two."
        ),
        "example": (
            "On DIFFERENT numbers from the questions below, so it tests transfer "
            "rather than recall. Rs 2,000 at 5% per annum for 4 years: "
            "SI = 2000 x 5 x 4 / 100 = 400. So the interest is Rs 400."
        ),
        "bridge": (
            "One extra step appears in the questions below: if the question asks "
            "for the AMOUNT rather than the interest, add the principal back. "
            "Amount = P + SI."
        ),
    },
}

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
        "PRINCIPALS. Check that it is not: here the interest ratio is 1,440 : "
        "2,160 = 2 : 3, while the principal ratio is 5 : 4. They genuinely "
        "differ, so the shortcut cannot work here.",
        "Step 1 - invert. SI = P x R x T / 100 becomes P = SI x 100 / (R x T). "
        "That is the same formula solved backwards, not a new formula.",
        "Step 2 - first principal. 1,440 x 100 / (8 x 3) = 144,000 / 24 = 6,000.",
        "Step 3 - second principal. 2,160 x 100 / (15 x 3) = 216,000 / 45 = 4,800.",
        "Step 4 - the ratio. 6,000 : 4,800, dividing both by 1,200, is 5 : 4.",
        "Why 2 : 3 is wrong: that is 1,440 : 2,160, the interest ratio used "
        "directly. It is the instinctive answer and it fails here because the "
        "two sums carry different rates. Notice that the two ratios are not even "
        "close: 2:3 against 5:4, so you can see the shortcut break.",
        "Why 3 : 2 is wrong: the same idea the other way round, 2,160 : 1,440.",
        "Why 1 : 2 is wrong: 15 + 3 = 18 instead of 15 x 3 = 45, so the second "
        "principal came out as 2,160 x 100 / 18 = 12,000 and the ratio halved. "
        "Multiplying and adding are easy to confuse on a small screen. Keep the "
        "brackets.",
        "Why 8 : 15 is wrong: 1,440 / 6,000 is 6/25 and 2,160 / 4,800 is 9/20, "
        "and 6/25 against 9/20 is 8/15. Dividing an interest by its own principal "
        "compares two RATES rather than two amounts, which is a different "
        "question from the one asked.",
    ),
    "L1-H": (
        "The insight: the rate is NEVER given. The 30% is an interest for three "
        "years, so it has to be converted back into a rate before it can be used "
        "on five. Interest is linear in time, which is a trap here rather than a "
        "shortcut.",
        "Step 1 - what 30% of the sum is. 30% of 1,000 is 300, and that is the "
        "interest for 3 years.",
        "Step 2 - recover the rate. 300 = 1,000 x R x 3 / 100, so R = 300 x 100 / "
        "(1,000 x 3) = 10 per cent per annum.",
        "Step 3 - interest over 5 years. 1,000 x 10 x 5 / 100 = 500.",
        "Step 4 - the amount. 1,000 + 500 = 1,500.",
        "Why Rs 1,300 is wrong: that is 1,000 + 300, the 3-year interest carried "
        "over untouched. This is the move this item is built to catch, because "
        "interest really is linear in time -- but linearity is about how "
        "interest SCALES once you have a rate, not a substitute for finding one.",
        "Why Rs 2,500 is wrong: 1,000 + 1,000 x 30 x 5 / 100. The 30% was used "
        "as the annual rate. It was quoted for THREE years, so using it for one "
        "overstates the interest by a factor of three.",
        "Why Rs 1,750 is wrong: 1,000 + 1,000 x 15 x 5 / 100. The 30% was halved "
        "to make it 'fit' a year. Scaling a percentage is only valid when you "
        "know what it was a percentage of, and here it was a percentage of the "
        "sum, over three years.",
        "Why Rs 700 is wrong: 1,000 - 300. A sum you are adding interest to ends "
        "above where it started. If an amount owed comes out below the principal, "
        "the sign is wrong.",
    ),
}




SOLUTIONS = with_answers(LESSON, SOLUTIONS)


def lesson() -> tuple[Item, ...]:
    return LESSON
