# PEDAGOGY — what a good question is, as countable rules

The reference project's rule is that "a good question" is not a matter of taste,
it is a list of things you can check. This file is that list for XAT. Every
rule is countable, and the ones that can be automated **are** automated, in
`gates.py` and `items.py`. A rule that is not automated is marked so, because
an unautomated rule is a preference.

## 1. The shape the owner asked for, and why it is the right shape

**FOUNDATION → EASY → MEDIUM → HARD, one subtopic at a time.**

This is not a difficulty *request*. It is a **dependency order**: the HARD item
on a subtopic is only meaningful if the learner has just done the FOUNDATION item
on the *same* subtopic, because the hard item's only extra step is the one the
foundation item isolated. A hard item on a fresh subtopic measures guessing.

`LESSON_SHAPE` is therefore exactly 4 questions, one per level, **one subtopic**,
and it is asserted by `test_lesson_shape_is_one_question_per_level`.

## 2. The learner's actual loop — and the one decision that makes it work

The owner's flow is: **see the question and options → select one → get told
right or wrong → read a step-by-step solution.**

That flow is correct, and it has one failure mode that is worth more than any
other idea in this file.

**MCQ is a RECOGNITION task. A learner who eliminates two distractors scores
"correct" without retrieving anything — so both the score and the learner's
self-model are wrong.** With 5 options the elimination is even easier than with
4. This is the reference project's single highest-value finding (its `A28`), and
it costs **zero LLM calls**: show the stem alone, make the learner write or
commit an answer, *then* reveal the options.

So the loop is:

```
stem alone  →  COMMIT an answer (never graded, never leaves the machine)
            →  options appear
            →  select
            →  right / wrong
            →  step-by-step solution, naming the misconception for every
                option they did NOT pick
            →  confidence click  →  four-cell quadrant
```

**The commit carries the learning. The options are only the checker.**

**The quadrant is why this is not decoration.** One confidence click gives four
cells, and two of them are opposites that a score cannot tell apart:

| | correct | wrong |
|---|---|---|
| **sure** | real | **misconception** — needs re-teaching |
| **unsure** | **gap in disguise** — needs retrieval practice | a guess that cost nothing |

A score cannot separate "sure and wrong" from "unsure and right", and they need
opposite remedies. This is the reference project's `A30`, and it is free.

## 3. The rules

### 3.1 Automatically enforced (in `gates.py`)

**R1 — Exactly 5 options.** Not 4. D3: 4 options with −0.25 pays you to guess
(EV +0.0625); 5 options makes guessing a wash (EV 0.0). `G1`.

**R2 — No `all of the above` / `none of the above`.** Eliminable without reading
the stem, so it measures pattern-matching. `G3`.

**R3 — The key is computed, not asserted.** `G5`. The single most important rule
in this document. See §4.

**R4 — No two items share a reasoning shape.** Digits are stripped before
comparison, so "15% of 480" and "20% of 360" are the *same question*. `G6`.
**Measured during the build:** a 20-item test fixture whose stems differed only
in digits admitted **1 of 20**.

**R5 — The level is derived, not claimed.** `G7`. D6.

**R6 — At least 2 of 4 distractors are real computed near-misses.** `G8`. D9.

**R7 — Answerable in 2 minutes *with* the on-screen calculator.** `G9`. The
exam supplies a calculator, so hand-computation difficulty is the wrong axis. An
item needing arithmetic a human cannot do *with* a calculator is badly set, not
hard.

**R8 — Every distractor carries a distinct, non-empty named misconception.** `G12`.

**R9 — The stem never leaks its key.** `G13`.

**R10 — The level mix is enforced; the paper is never padded.** `G11` drops
over-quota items. **Measured:** it keeps the *lower* rungs when two must go,
because a learner who cannot reach the hard item has not understood the
foundation item, and the paper already holds enough easy items to say so.

### 3.2 Enforced by a human-in-the-loop reviewer

**R11 — The paper's level spread is a *ladder*, not a histogram.** The
`level-auditor` role's entire job. A paper with 4 easy and 16 hard is not a hard
paper, it is an unusable one.

**R12 — Every distractor is diagnosable by name.** A distractor a learner cannot
rule out teaches nothing. R8 checks the *count*; only a reader checks the *name*.

**R13 — The step-by-step teaches, not just computes.** Showing `200 = 1000×10×2/100`
is arithmetic. Showing *"you added the rates instead of multiplying, which is
the mistake you make when a question has two percentage changes"* is teaching.
The `viewer` role's job, sat as a learner.

**R14 — The commit barrier is on in every learning mode.** §2. Zero LLM calls.

**R15 — No negative marking in LESSON or PRACTICE.** D8. The blank penalty is an
exam mechanic; teaching it mid-lesson teaches the wrong lesson.

## 4. Why R3 is the one that outranks the rest

**A wrong answer key actively teaches a wrong fact, and the student cannot detect
it.**

A wrong *analogy* is one bad frame in a lesson. A wrong *key* is a learner who
now believes something false and who will answer the next five questions
consistently with that belief. The reference project reached the same conclusion
about its own blind second call.

**Here it is stronger than a second opinion.** A quantitative key is a number, so
we do not ask a second model whether it looks right — we **recompute it** and
compare. `Solver.verify` evaluates the item's own derivation in exact rational
arithmetic. Agreement is arithmetic. Disagreement is a **refusal**: the item is
**dropped, never repaired**, because repair makes the gate unfalsifiable — after
repair, the gate has never rejected anything.

**And it is honestly bounded.** Prose has no solver. A `Stratum.JUDGEMENT` key
(VALR, DM) is re-derived by an independent blind second call, which is a second
*opinion*. `Verdict.DELEGATED` exists so that opinion is never reported as
computation. A percentile claim must name its strata or it is overstated.

## 5. What a lesson must not do

- **Not ask for a level.** D6. The model ignores the request; the level is
  derived afterwards from structure.
- **Not test a topic the learner has not met.** The HARD rung is only reachable
  from the FOUNDATION rung of the *same* subtopic.
- **Not present a hard item whose difficulty is nameless.** `derive_level`
  returns `drivers`; a hard item with no named driver is not hard, it is long.
- **Not let a wrong answer pass because it was a confident guess.** The quadrant
  is what makes the score mean something.
- **Not claim percentile from a paper that mixes strata** without saying so.
