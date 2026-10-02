# DECISIONS — the one ledger

Every ruling lives here with the reasoning that produced it. A ruling without a
reason is a preference, and preferences rot. Reverse decisions by **superseding
them** and saying so, never by editing them away — a doc that tracks its own
history is the only way to tell a mistake from a change of mind.

Status: **Waves 0 and 1 landed.** 161 tests, 95.19% coverage on
`src/xat_practice/*.py`, ruff and mypy clean (mypy on 9 source files). **Re-measured
2026-10-02.** The gates, the solver, the weight model, the derived-difficulty
model, Lesson 1 and the static bundle all exist and are measured.
`enumeration.py` and the blind second call are not built. **D3 and D4 accepted by
the owner 2026-10-02**; D14 fixes the build order as lesson → mock → full, with
Geometry first.

---

## 1. The load-bearing rulings

### D1 — The key is RE-DERIVED by computation, not second-guessed by a model

**Ruled 2026-10-02. Load-bearing.**

The reference project grounds every item in a cited transcript span and
re-derives the key with a blind second LLM call (`G16`). That is the best
available answer when the source material is prose.

We have no corpus, and for quantitative items we do not need one, because **a
quantitative key is a number, not an opinion.** `Solver.verify` evaluates the
item's own `derivation` in exact rational/sympy arithmetic and compares it to
the keyed option. Agreement is arithmetic; disagreement is a **REFUSAL** (`G5`),
never a repair.

This is strictly stronger evidence than a blind second call and costs **zero LLM
calls**. A `Stratum.QUANT` percentile claim is a statement about code.

**What it does not buy.** Prose has no solver. `Stratum.JUDGEMENT` (VALR, DM)
keys get the blind second call, which is a second *opinion*. See D2.

### D2 — `Verdict.DELEGATED`, and the guarantee is reported per stratum

**Ruled 2026-10-02. Load-bearing.**

`HOLD` / `REFUSE` is a false pair for a paper that mixes three strata,
because it cannot express "not checked here, and deliberately so."

`DELEGATED` is the third outcome. It means the key was not verified by this
module and the enum refuses to pretend otherwise.

- QUANT → `HOLD` (computed) or `REFUSE`
- LOGIC → `DELEGATED` to `enumeration.py` (exhaustive search — still computed)
- JUDGEMENT → `DELEGATED` to a blind second call (an opinion)

**Measured, during the build:** before `DELEGATED` existed, a JUDGEMENT item with
no derivation fell through to the logic branch and returned
`REFUSE/NO_DERIVATION` — which would have rejected **every VALR and DM item, a
third of the exam.** Returning `HOLD` instead would have been worse: it would
label an unverified prose key as one that code confirmed. Neither is acceptable,
so the enum grew a third arm.

A paper that mixes strata **must report them separately**. A single percentile
figure that does not name its strata is overstated, and saying so is cheaper
than being wrong.

### D3 — 5 options, −0.25, and the −0.10 blank penalty are REPLICATED, not refused

**Ruled 2026-10-02. Load-bearing. This reverses the reference project's D5 and
D6.**

**Accepted by the owner 2026-10-02**, who had never been asked and had never
specified the marking scheme: "5 options, −0.25, −0.10 per blank after the 8th.
You never specified these. Update this." An owner acceptance of a ruling that was
already load-bearing is worth recording, because it removes the last chance that a
future session reopens it as "the owner never agreed."

The reference project refused 5-option questions and refused negative marking.
Both were correct **there** and are wrong **here**, and the arithmetic says so:

| | measured EV of a random guess |
|---|---|
| 4 options, −0.25 | **+0.0625** — guessing *pays* |
| **5 options, −0.25** | **0.0000** — guessing is a wash |

A 4-option negatively-marked paper pays a student to guess, which rewards a
second skill this product does not teach. XAT 2026 uses 5 options and the wash is
deliberate. Replicating anything else would mean training against a paper the
student does not sit.

**The blank penalty is the lesson nobody teaches.** A random guess is EV 0.0. The
**9th** blank is **−0.10**. So past eight blanks, guessing strictly dominates
leaving it empty — the reverse of the usual "skip if unsure" advice. Verified:
`guess_ev_report()` → `one_blank_9th = -0.1`, `ten_blanks = -0.2`.

Two consequences: mocks carry negative marking, and a **practice** set does not
(see D8).

### D4 — Additions to the owner's focus list, with the evidence

**Ruled 2026-10-02.**

**Accepted by the owner 2026-10-02**, with one override recorded at D14: the
syllabus additions stand as written, and the *order* they are trained in is
Geometry first, not Data Interpretation.

**Correction to the provenance sentence, 2026-10-02.** This heading used to read
"the owner's 17-topic list". The owner's pasted list is **15 lines**, not 17.
Seventeen is the size of `syllabus.TOPICS`, which is 8 `owner_listed` + 9 added.
The number was wrong and it was wrong in the one place a reader would check it,
so it is corrected here rather than quietly left. `AGENTS.md` carries the same
error and is corrected in the same pass. The owner asked for a percentile focus rather than full
coverage, and asked that additions be justified.

Measured on **196 questions = 7 papers × 28** (`syllabus.py`, 2020–2026):

| added | q/yr | why |
|---|---|---|
| **Data Interpretation** | **6.71** | the single largest block. Absent from the list. Not on the list and not trained is the difference between 70 and 90 |
| **Number System** | **2.86** | speed marks, near-zero learning cost |
| **Inequalities** | 0.57 | extends the algebra block; appears every year |
| **Graphs & Functions** | 0.43 | **new in 2026, 3 questions** |
| **Venn & Sets** | 0.57 | cheap marks |
| **Data Sufficiency** | 0.57 | a *question type*, not a topic. Appears every year. Needs its own shape, not a chapter |
| **Puzzle & Charts** | 1.29 | |
| **Prob & Combinatorics** | 1.00 | **minimal slice only** — 1–2/yr, high variance |

**Excluded, each with a reason** (`syllabus.EXCLUDED`): trigonometry beyond
Pythagorean/heights, complex numbers, vectors & 3-D, matrices & determinants,
binomial, calculus, statistics. These would pad the syllabus to look complete
without adding marks in the 80–100 band.

`Topic("pct", ...)` is recorded at **0.0 to mean UNMEASURED, not absent**.
Percentage is folded into `avg_ratio` and into the CollegeDekho "Arithmetic"
row. A test asserts this stays 0.

### D5 — The weight table is `measured-from-secondary-source`, and it must close

**Ruled 2026-10-02.**

XLRI publishes no per-topic breakdown. The figures come from a coaching
compilation, so they are **secondary**. They are quotable only because they
pass an internal check: every year's rows sum to exactly 28
(`self_check()`). A table that does not close to the paper length is a table of
opinions wearing the costume of data.

Every year-over-year rate in the docs names its denominator. A count with no
denominator is a lie that looks like a pass.

### D6 — Difficulty is DERIVED from the item's structure, never requested

**Ruled 2026-10-02. Load-bearing.**

Inherited MEASUREMENT from the reference project: requesting `Apply` then
`Analyse` from a model returned the **identical stem on 4 of 6 segments**. A
paper built by asking for several levels therefore counts one question twice and
satisfies its own distribution gate by duplication.

So `derive_level` computes the tier from structure that already exists:
`derivation_steps`, `needs_substitution`, `insight_required`,
`enumeration_size`, distractor quality, and calculator budget. A drafter's
*claimed* level is recorded and checked; a disagreement is a **refusal** (`G7`),
never a repair.

`LEVEL_RECIPES` is the one place a level may be requested — and it is requested
of **code**, as a structural profile the drafter then has to live with.

**Measured, during the build:** the first version charged a flat **+0.8** for
`real_near_miss >= 3`, so an item with 2 real near-misses landed in a different
level from an otherwise identical item with 3. One extra plausible wrong move
cannot be worth a whole level. Now linear at **+0.2 each**, asserted by
`test_level_boundaries_are_not_surprising`.

### D7 — Section mocks AND the full paper, and section mocks are labelled as training

**Ruled 2026-10-02.**

The owner asked for all three shapes: quant-only, section-by-section, and the
full paper. All three are built.

**The honest limit:** XAT 2026 Part 1 has **no sectional time limit** — 170
minutes for all 75 questions, with free movement between sections. A section
mock that gives QA&DI its own clock therefore *flatters* the student, and a
student who only ever practises that way will run out of time in a way that has
nothing to do with their quant. Every section mock is labelled as a training
artifact, and the full paper is the only instrument that measures exam
allocation.

### D8 — PRACTICE carries no negative marking; MOCK does

**Ruled 2026-10-02.**

The two shapes are different products, not one product with a length setting.
This mirrors the reference project's A26 split.

- **LESSON** (4 questions, one subtopic, F→E→M→H): no marking, step-by-step
  shown on demand. Teaching.
- **PRACTICE** (20): no marking. A student who skips a question here has learned
  nothing; the −0.10 blank penalty is an *exam* mechanic and teaching it during
  a lesson teaches the wrong lesson.
- **MOCK** (28 quant / 75 full): −0.25 and the blank penalty are live, because
  that is the thing being measured.

### D9 — A distractor must be a real computed near-miss with a named misconception

**Ruled 2026-10-02.**

With 5 options, a paper where three options are arbitrary numbers measures
guessing, not reasoning. `G8` requires **≥2 of 4** distractors to be real
computed near-misses, and `G12` requires every distractor to carry a **distinct
non-empty `misconception`** naming the wrong idea the student actually holds.

The traps are not free text. They are enumerated in `syllabus.SUBTOPICS` —
**90 named traps across 40 subtopics** — and each becomes a distractor. A trap we
cannot name is a trap we cannot set.

A test asserts every trap is at least 5 words: a trap that does not say what the
learner does *wrong* produces a vague distractor. **Measured:** the first draft
had 5 such traps, and they were rewritten.

### D10 — Static browser bundle, no server, no accounts

**Ruled 2026-10-02.** Inherited from the reference project's D9.

A static bundle is inspectable by the owner and cannot leak a key to a network.

### D14 — Build order is LESSON, then MOCK, then FULL, and Geometry is first

**Ruled 2026-10-02, by the owner, overriding the recommendation on record.**

The owner asked for the learner to be able to sit a URL, and then for a mock,
and then for the full paper, in that order. Geometry was named first.

**The recommendation this overrides.** `task.txt` §7 proposed Data
Interpretation next, on the measured ground that DI is the largest block at
**6.71 q/yr** and Geometry is second at **4.57 q/yr**. On raw marks per hour,
DI was the better next block, and that reasoning was not wrong.

**Why the override is defensible anyway**, and this is the reason it is recorded
rather than just obeyed:

- Geometry holds the **deepest dependency chain** in the syllabus —
  `similarity-and-area-ratios` → `angle-bisector-and-cevian` →
  `triangle-angle-sine-rule` → `circle-tangents` → `circle-power-of-a-point` →
  `cyclic-quadrilateral` → `mensuration-2d-3d` → `coordinate-geometry`. Eight of
  the forty subtopics, and each HARD rung is only reachable from the rung below
  it. It is the one block where building it late means re-building it.
- DI is a **throughput** block: high marks per hour, low depth per hour, and it
  degrades gracefully if met late in training.
- A mock needs a **rung ladder the learner has already walked**. Geometry
  supplies that ladder; DI alone does not.

**What this decision does not buy.** Geometry first does not make the DI gap go
away. **6.71 q/yr is still the largest untrained block** after Lesson 2, and the
honest statement is that the owner has chosen the deeper block first and the DI
debt is deferred, not cancelled.

**Sequencing rule that follows.** No mock is built for a subtopic whose lesson
has not been sat. A mock on an unwalked ladder measures guessing, which is the
thing `PEDAGOGY.md` §1 exists to prevent.

---

## 2. Gate specification

**14 gates**, not 13. `GATE_IDS` in `gates.py` is normative — MEASURED 14 entries
at 2026-10-02 — and renumbering one is a breaking change.
`test_every_gate_id_is_reachable` asserts each can actually fire — an
unreachable gate is a specification, not a gate. **The table below was stale at
13 until 2026-10-02: `G14` was added during the Wave 1 build (D11) and this
section was never updated, so the doc and `gates.py` disagreed with no error
anywhere.** That is the doc-reviewer's whole reason for existing.

| id | refuses | note |
|---|---|---|
| G1 | ≠5 options | D3 |
| G2 | key index out of range | **short-circuits G5** |
| G3 | `all`/`none of the above` | eliminable without reading the stem |
| G4 | duplicate options | |
| G5 | key ≠ recomputation | **the load-bearing gate** |
| G6 | duplicate reasoning shape | digits stripped first |
| G7 | claimed level ≠ derived level | D6 |
| G8 | <2 real near-miss distractors | D9 |
| G9 | >2 min calculator budget | the exam supplies a calculator |
| G10 | stratum/derivation mismatch | QUANT and JUDGEMENT only |
| G11 | level mix over quota | drops, never pads |
| G12 | unnamed/duplicated misconception | D9 |
| G13 | stem leaks its own key | |
| G14 | `option_values` value not visible in the option label | D11 |

**Ordering is normative.** `G2` must precede `G5`, and it must
**short-circuit**: the solver reads `options[key_index]`, so an out-of-range key
used to raise `IndexError` inside `SOLVER.verify` and destroy the whole run
before `G2` could refuse the item. *Measured during the build.* Now covered by
`test_one_bad_item_does_not_destroy_the_paper`.

---

## 3. Open, and honestly open

- **`enumeration.py` is not built.** `Stratum.LOGIC` returns `DELEGATED` and
  nothing discharges it yet. Until it is, a logic item is *labelled* unverified
  rather than *verified*, which is the correct direction to be wrong in.
- **The blind second call for JUDGEMENT is not built.** Same reasoning.
- **The bundle serves one lesson and takes no marks.** It is the LESSON shape
  only: no negative marking, no timer, no quadrant persistence, no section mock
  and no full paper. `QUANT_MOCK` and `FULL_MOCK` exist as shapes in
  `items.py` and are unbuilt.
- **Lesson 1 is one subtopic.** 40 are trained in `syllabus.SUBTOPICS`; 1 is
  written. No claim is made about the other 39.
- **No wall-clock, no cost figures.** One lesson has been built, so any
  per-lesson or per-paper time or token estimate would be a proxy wearing a
  measurement's clothes.
- **The bundle has been read, not clicked.** It was verified by asserting the
  files on disk and by reading the rendered flow. Nobody has yet answered all
  four questions in a browser and reported what it felt like, which is the
  `viewer` role's first job and the one thing a test cannot do.
- **Owner items outstanding — ONE left.** The D4 additions were **confirmed by
  the owner on 2026-10-02** and are no longer open. Still unasked: whether the
  reference project's `D9`-style rights posture (private revision, not
  published) carries over. It is assumed to, and has not been asked. One open
  item, not two.
- **Geometry is next, not Data Interpretation.** See D14. Geometry is **P1 at
  4.57 q/yr**; DI is **P1 at 6.71 q/yr** and is now the largest block with no
  lesson written against it. That debt is deferred, not closed.

## 4. Retired, and why — do not re-open

| retired | why |
|---|---|
| `Verdict.HOLD` for a judgement item | would have claimed code confirmed a prose key. See D2 |
| `run(..., expected=n)` | silently truncated the admitted set and could contradict `G11`. `G11` owns the mix |
| `G10` as one comparison over all three strata | refused **100% of logic items**, because `(stratum is QUANT) == (derivation is None)` is true for every logic item. Now QUANT and JUDGEMENT are checked separately |
| flat `+0.8` near-miss bonus at `real >= 3` | made one extra plausible wrong move worth a whole level. Now linear at 0.2 each. D6 |
| `G11`'s defensive `kept.remove(it)` | the branch appends a refusal for an item it never appended, so the `remove` would raise on the second over-quota item at a level. Now impossible by construction |

---

## 5. Wave 1 — what building Lesson 1 actually cost

Recorded because the defects are more useful than the lesson.

### D11 — Options carry a separate arithmetic value, and `G14` guards it

**Ruled 2026-10-02. Load-bearing.**

`Item.options` are **display strings**, and display strings are not arithmetic.
MEASURED: all four of Lesson 1's keys were REFUSED by `G5` on the first run,
because `Rs 200` and `2 : 3` do not parse as sympy. A gate doing its job.

The fix is a second parallel field, `option_values`, which is what the solver
reads. Forcing currency symbols and ratio colons out of options instead would
have forbidden most real XAT options.

**The worse half.** `'14,400'` does not *fail* to parse — `sympify` returns the
**tuple `(14, 400)`**. A thousands separator turns one amount into a pair and
slips *past* the parse check instead of being caught by it. So `G14` asserts the
value the solver checked is actually visible in the label the learner reads.

`G14`'s first version compared digit runs and REFUSED `2 : 3` against `2/3` —
the same ratio in XAT's own notation. It now reduces both sides numerically, and
treats a value that parses to a non-scalar as a refusal while a value that
does not parse at all is prose and is ignored. That distinction is the whole
content of the gate.

### D12 — `G11` does not run on a lesson

**Ruled 2026-10-02. Load-bearing.**

`G11` apportions the **20-item paper mix** (10/25/40/25). Applied to a 4-item
lesson it yields `{foundation 1, easy 1, medium 1, hard 0}` and **dropped the
hard item** — the product's central claim, deleted by a paper-level rule.
`MIX_ENFORCEMENT_FLOOR = 8`; below it, `LESSON_SHAPE.quota()` is the authority
and says 1/1/1/1.

### D13 — The commit barrier must be a *file* boundary, not a UI convention

**Ruled 2026-10-02. Load-bearing.**

The first bundle had a single loader that served the stem, so
`answerkey.json` — every key, every solution, every misconception — was in
memory and in the network tab **before the learner committed a single
character**. The commit barrier was theatre, and every test on it passed,
because each test checked one property and none checked the fetch path.

The bundle now splits in two:

| file | contents | fetched |
|---|---|---|
| `paper.json` | stem, options, derived level, drivers | on load |
| `answerkey.json` | `k`, solutions, misconceptions, grounding | **inside `check()`, only** |

`test_paper_json_alone_cannot_mark_an_answer` is the property that matters: the
file the page loads first must be useless for grading. The key field is named
`k`, not `key_index`, because a served script that *names* the field holding
the answer is one refactor away from shipping it.

### Three crashes on bad input, all the same family

Found by running, never by reading. Each is now a test with a falsifying input.

1. **`IndexError` in `run`** — an out-of-range key reached the solver, which
   indexes `options[key_index]`, and destroyed the whole paper. `G2` now
   short-circuits. One bad item must cost one item.
2. **`AttributeError` in `_value_visible_in_label`** — `nsimplify` calls
   `.evalf()` on whatever `sympify` returned, and a `Tuple` has no `evalf`. The
   function **crashed on the exact input `G14` was built to catch**.
3. **`ValueError` from `zip(strict=True)`** in `G14` against an empty
   `option_values`, which took down every LOGIC and JUDGEMENT item.

A gate that raises has silently become a gate that is not run.
