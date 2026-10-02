# ADOPT / REJECT — the review ledger

**Written 2026-10-02.** Five reviews of `docs/LLD.md` and the exam layer landed on
the same day. This file records what each one claimed, what was decided, and why.
It exists because the alternative is losing the reasoning: a rejection with no
stated reason gets re-litigated, and an acceptance with no stated reason gets
applied to things nobody asked for.

**Read this before changing `docs/LLD.md`.** Every P0 entry below is already in the
code; every DEFER is a deliberate hole, not an oversight.

---

## 0. Provenance — what actually ran

| # | review | ran on | how |
|---|---|---|---|
| R1 | `doc-reviewer` (opencode.json agent) | `docs/LLD.md` + the half-applied code | `uv run`, read-only |
| R2 | `code-reviewer` (opencode.json agent) | `docs/LLD.md` + `git diff` | `uv run`, read-only |
| R3 | `viewer` (opencode.json agent) | the **navigation**, not the LLD — earlier the same day; included because it produced the committed `viewer` findings | real headless Chromium |
| R4 | Claude.ai | `docs/LLD.md` | pasted into this session |
| R5 | Perplexity.ai | `docs/LLD.md` | pasted into this session |

Stated precisely because this project cares: **two** internal agents reviewed the
LLD (R1, R2). R3 reviewed the UI flow, not the document. `ui-inspector` from
`opencode.json` **could not be run** — it is not an available task type in this
harness — so the browser-render role was not applied to the LLD.

Both internal agents were told to use `uv run` and were **denied** `.venv/bin/*`:
that permission flip was the earlier owner ruling, and the review was the first
thing to exercise it.

---

## 1. P0 — correctness. Fixed, with the falsifying input written.

### 1.1 The blank penalty was on the wrong level — ADOPT (R4, R5, independently)

**They said.** `blank_penalty` / `blank_penalty_after` on `SectionSpec` imply
**eight free blanks per section**. XAT's rule is "−0.10 for every unattempted
question after the first eight", and **Part 1 is one pool of 75 questions** across
QA&DI + VA&LR + DM in a shared 170 minutes. So the truth is eight free blanks *in
total*.

**Why this is the most serious finding in the set.** It is not a wrong default; it
is a false *attempt strategy*. A learner told "8 free per section" skips 24 and
loses ≈1.6 marks. This product's entire output is strategy.

**Decided: ADOPT in full.** `PartSpec` added; the two fields and `minutes` moved
off `SectionSpec`; `SectionSpec` gained `part_id`.

**Falsifying input:** `test_the_blank_penalty_counts_across_the_part_not_within_a_
section` — 4 + 3 + 3 = 10 blanks ⇒ `−0.20`, while no section exceeds eight. Plus
`test_no_section_may_carry_the_parts_clock_or_blank_rule`, which fails if anyone
adds the fields back.

### 1.2 `minutes = 170` was on a section — ADOPT (R2, R4, R5)

**They said.** Part 1's shared clock is not any section's allowance, and XAT 2026
has **no sectional time limit**.

**Decided: ADOPT.** `PartSpec.minutes = 170`. No `minutes` on any section.
`test_part_one_has_the_clock_and_no_section_does` pins it.

R4 additionally suggested a separate `recommended_mock_minutes` for app-invented
sectional durations — **DEFERRED**: no sectional mock exists yet, and a
`minutes`-lookalike field that is not an exam fact is the same confusion in a new
name.

### 1.3 `SectionSpec.stratum` was a single value and it was wrong — ADOPT (R5)

**They said.** §1 measures QA&DI as 37 QUANT + 3 LOGIC, yet the spec held one
`Stratum`. A section is a **mix**.

**Verified before adopting:** `ds:sufficiency-statements`,
`puzzle:routing-and-network-puzzles`, `venn:venn-counting` are LOGIC.

**Decided: ADOPT.** The field is gone. `strata()` derives the distribution.
`test_a_section_is_a_mix_of_strata_not_one_value` pins 37 and 3.

### 1.4 The guess-EV formula dropped `mark_correct` — ADOPT (R1, R2, independently)

**They said.** `1/options + (options−1)/options × mark_wrong` hardcodes +1, so CAT's
reported +3/−1 returns **−0.6000** where the truth is **−0.2000**. It was right for
XAT only because XAT's `mark_correct` happens to be 1.

**Decided: ADOPT.** The property now delegates to the `items.expected_ev` that
already existed — it was a *second* implementation of a function already in the
tree. `test_the_guess_ev_is_computed_not_hardcoded` pins both numbers.

### 1.5 "37% of percentile" was overstated — ADOPT (R4)

**They said.** 28/75 is 37.33% of Part 1 **question count**, not of percentile.
Percentile depends on cohort performance, scaled scores and sectional cutoffs.

**Decided: ADOPT.** The LLD wording is corrected. This is AGENTS.md's own rule
("a percentile figure that does not name its strata is overstated") applied to a
sentence I had written.

### 1.6 "Guess is free" was imprecise — ADOPT (R5)

**They said.** EV = 0 is measured against a *skip worth 0.0*. Below eight blanks,
skipping is free, so a pure guess is merely **neutral** — the right advice is *only
guess after eliminating options*. Past eight blanks a skip costs −0.10, so guessing
is **+0.10 better** and the right advice is *always answer*.

**Decided: ADOPT.** The sharpest pedagogical correction in the set, and it changes
what the lesson should say. Both halves are now in the LLD.

### 1.7 The package did not import — ADOPT (R1, R2)

**They said.** `menu.py` imported the `PAPER_SHAPE` I had deleted.
`ruff` **passed**; `import xat_practice.cli` raised `ImportError`; four test modules
failed to collect; mypy reported four errors.

**Decided: ADOPT, and it became a standing rule.** A green linter is not a green
build. `uv run python -c "import xat_practice.cli"` is now part of the documented
commands, and R5 independently asked for the same smoke test.

### 1.8 `edition = "2026"` asserts next year's paper — ADOPT (R5)

**They said.** It is October 2026; the paper a learner sits is most likely XAT
**2027**. A hardcoded edition silently claims next year has identical counts,
marking and calculator policy.

**Decided: ADOPT (partial).** `ExamSpec.verified_against` and `.evidence` added, and
`test_the_shape_records_what_it_was_verified_against` requires an OFFICIAL shape to
name its document. Full per-edition keying (`xat@2026` / `xat@2027`) and per-item
edition tagging are **DEFERRED** — they matter the moment a second edition exists,
and one shape does not need two names.

---

## 2. REJECTED — and why, so it is not re-proposed

### 2.1 Replace the "≥10 traps" gate with a coverage matrix — REJECTED (R4, R5 agreed)

**They proposed.** Named misconceptions 8–10, distinct skill templates 5,
foundation items 4, medium 6, hard 4, transfer 2, solver-verified 100%, similarity
threshold, ambiguity review 100%.

**Why rejected.** Those numbers are **unmeasured**. Making them a gate is precisely
D13's error — inventing a threshold and enforcing it. A subtopic with ten
near-duplicate labels would pass, which is the padding incentive R4 was trying to
remove; it just moves the gaming.

**What was adopted instead.** R4's *vocabulary*: **authoring / drill / mock
readiness** are three different bars, and a subtopic reaching one does not reach
the others. `block capacity` already reports readiness rather than enforcing it.

### 2.2 Per-level target times of 30–75s … 150–300s — REJECTED as stated (R4)

**Why.** `G9` refuses any item over **2 minutes**. R4's Hard band of 150–300s is
*refused by our own gate*. Adopting the numbers would either break G9 or require
silently raising it, and G9's rule is measured and deliberate ("hand-computation
difficulty is the wrong axis — the exam supplies a calculator").

**Adopted instead:** the *concept* — a level needs a stated time budget — recorded
as open work, to be reconciled against G9 rather than asserted over it.

### 2.3 A wholesale `ItemBlueprint` type — PARTIALLY REJECTED (R4)

**They proposed** `primary_skill`, `cognitive_operation`, `target_time_seconds`,
`solution_path_count`, `source_kind`, plus `CognitiveOperation` and `SourceKind`
enums.

**Why mostly rejected.** Most already exist under different names:
`derive_level` computes the tier from `derivation_steps`, `needs_substitution`,
`insight_required`, `enumeration_size` and distractor quality (D6, and the reason
`level-auditor` exists); `G16` proves every distractor is produced by the move it
names; `G9` is the time budget. Re-adding them as a second vocabulary is how two
rules that disagree get created.

**Adopted:** `trap_id` only — see §3.1.

### 2.4 `MockSpec`, `SectionShape`-as-runtime-object, `effective_options()` — DEFERRED

All three are reasonable and all three are premature with one exam and one section
built. Recorded so they are adopted *when the thing they describe exists*, not
discarded.

### 2.5 Thin vertical slice instead of depth-first — DEFERRED, not rejected

R5 argues 40 subtopics × 4 levels × 20 items ≈ 3,200 items does not close in three
months. The arithmetic is right and the scheduling truth is real. It is a **product
priority** decision, not a design one, and D14 already fixes the order. Recorded,
not applied.

---

## 3. ADOPTED as recorded gaps — real, not yet built

Each of these is a hole both or one reviewer found, none of which blocks the layer.

### 3.1 `Distractor.trap_id` (R4, R5)

`syllabus.Subtopic.traps` and `Item.distractors[].misconception` are two parallel
lists of named errors with **nothing linking them**. `G16` proves a distractor's
arithmetic; `G12` proves it is named. Nothing proves the distractor draws from the
subtopic's declared trap set. Worth closing, and it is the link that makes a
learner response log analysable.

### 3.2 `Item.Set` for shared stimuli (R5)

XAT DI and caselet questions arrive as 3–5 items over **one** stimulus. `G11`'s mix
and `_assert_one_rung_per_level` both assume one item, one key, one rung. Must land
before any DI content. Also the strongest available use of D1: DI data generated
**parametrically** and solved by exact arithmetic.

### 3.3 A prerequisite graph — and it REVERSES my own recommendation (R5)

DI is built on percentages, ratio, averages and growth. Measured: `avg_ratio` has
**0 of 3** subtopics written, `pct` is **0.0 UNMEASURED**. So "DI next" would teach
calculation shortcuts to a learner without the foundations — the exact error the
foundation→hard ladder exists to prevent.

**This reverses the recommendation I made earlier in the session.** Percentages /
ratio / averages come before DI. Recorded as a todo, not applied silently.

### 3.4 Phase E is not one thing (R5)

Part of VA&LR and DM is verifiable **by construction**, so it is not
`DELEGATED`:

- **para-jumbles** — the key is the source paragraph's order, checkable.
- **arrangement / constraint sets, syllogisms, conditional logic** — brute-force
  enumerable, which is exactly what `Stratum.LOGIC` means, and it is already 3
  subtopics wide.

Only **RC inference and ethical caselets** are genuinely `DELEGATED`. "Phase E
parked" hid a tractable share of the 47 non-Quant counted questions.

### 3.5 Percentile evidence (R4, R5)

Raw score and percentile must be reported separately, and any estimate is
`UNMEASURED` until there is edition-labelled cohort data. Adopted as a labelling
rule for everything this project prints.

### 3.6 Calculator: exam permission ≠ training affordance (R4, R5)

`SectionSpec.calculator` records what the exam allows. Whether the *app* offers one
is a product decision, and the default must not let a calculator hide arithmetic
weakness — which sits in tension with G9's own rationale. **Open decision, not
resolved.**

### 3.7 Learner response logging (R5)

No learner model exists: attempts, time, which trap was chosen, re-testing. For one
learner aiming at 80+ that is where the improvement comes from, and the level bands
are currently our assumption rather than a calibration. Store locally, exportable.

### 3.8 Marking must reach the browser from data (R5)

`lesson.js` must read marking from `paper.json` and keep no copy of its own, or the
two-rules-that-disagree defect is recreated in the client.

### 3.9 Invariant 5, stated as arithmetic (R5)

"Closes" is ambiguous. Now: `Σ questions` over all sections = `total_questions`
(75 + 20 = 95) and over counted sections = `counted_questions` (75).
`test_the_parts_close_to_the_exam` spells both out.

---

## 4. Smaller corrections, all accepted

| # | from | finding | action |
|---|---|---|---|
| 4.1 | R1 | "28.00" was an ad-hoc calculation promoted to an invariant | demoted; LLD §9 records it as **not re-derivable** and the invariant is withdrawn |
| 4.2 | R1 | LLD §1 said "DI is next" while §7 called it an open decision | contradiction fixed; DI ordering now follows §3.3 |
| 4.3 | R1 | D7 miscited for "QA&DI only" | D7 is about section mocks; the scope fact is now attributed to the syllabus module |
| 4.4 | R1 | "3 src sites" for `PAPER_SHAPE` | measured: **2 modules / 15 references, 2 test modules, 2 documents** |
| 4.5 | R1, R2 | LLD's data-model sketch drifted from the shipped code | LLD re-synced; the LLD must be edited with the code, not after |
| 4.6 | R1 | `README.md` and `DECISIONS.md` said "90 named traps"; code says **104** | both corrected |
| 4.7 | R2 | `in_percentile` duplicated the exam's exclusion list | removed; now a method that refuses a cross-exam question |
| 4.8 | R2 | `section_of` checked only one direction of the join | both directions now checked |
| 4.9 | R2 | table invariants were headed for `registry` | moved to `syllabus._check_exam_layer()`, beside the 28-closure |
| 4.10 | R2 | a *wrong* parent (`"qa-di"`) imported cleanly | `self_check()` now resolves every topic's parent at build time |
| 4.11 | R2 | `gates.py` hardcodes +1/−0.25 — a third home | **deferred to Phase B** with the other marking duplicates |
| 4.12 | R5 | `subtopic_id` contains `:` — awkward in paths | noted; it is not in any path today, and the URL uses `lesson_id` |

---

## 5. What all five reviews agreed on, unprompted

Worth recording because agreement across independent reviewers is stronger evidence
than any single argument:

1. **Exam as data, not a code fork.** (R1, R2, R4, R5)
2. **Registry-first; derive, never duplicate.** (R2, R4, R5)
3. **Learner level ≠ paper mix.** (R4, R5 — matching D12 and D26)
4. **A judgement key is never `FULLY_VERIFIED`.** (R4, R5 — matching D2)
5. **The `≥10 traps` number is a weak, gameable gate.** (R4, R5)
6. **"37% of percentile" is the wrong claim.** (R4, R5)
7. **Architecture sound, exam model not.** (R4: 8.5/10 vs 6/10; R5: same split)

The two external reviews reached the same architecture/content split without seeing
each other, and both rated the **exam-model** layer as the weak half. That is the
part §1 fixed.

---

## Review 6 — two external UI-automation reviews (2026-10-02)

Two independent LLM reviews (Claude.ai and Perplexity.ai) of "what UI automation
must check for this LLD". Both, unprompted, opened with the same warning:

> If the test reads the expected answer from the same `paper.json` the page
> renders, a wrong key passes.

**That is not a theoretical caution. It is a live defect in this suite, and it is
the single most valuable thing either review said.** Everything below is ordered by
what the reviews got *right*, because that is rare enough to be worth recording.

### ADOPTED — and one of them was a P0 we had not seen

**A1. The oracle must come from Python, never from the bundle or the DOM.**
Adopted as **TASK-064, P0**. Both reviews stated it; we then MEASURED it:

- `tools/ui_probe.stage()` builds its expected keys by reading
  `answerkey.json` — *the same file the page fetches inside `check()`*.
- The docstring claims this "lets the probe assert that the browser's own verdict
  agrees with the solver rather than with itself". **That claim is false.**
- Falsifying input: plant a valid-index **wrong** key on `L1-F` (0 → 2). Result:

  ```
  PASS  the-browser-verdict-matches-the-recomputed-key
        browser said "Not correct. The answer is C.", key is index 2
  58/58 UI checks passed
  ```

  The page rendered C because the file says 2. The probe expected C because the
  file says 2. **They agree with each other.** A check named
  `the-browser-verdict-matches-the-recomputed-key` cannot fail on a wrong key.

  Note the earlier, weaker version of this measurement: planting the wrong key on
  `L1-E` changed nothing at all, because the check uses `Object.keys(EXPECTED)[0]`
  — which is `L1-F`. **An item that is not the one under test is a silent no-op.**

**A2. "Change the marking in the fixture and the UI follows with no code change."**
Adopted (TASK-066, P2). This is the strongest available anti-hardcode test and it
is exactly our "two rules that disagree" defect aimed at `mark_correct`: if the
bundle carried its own copy of the marking, this would fail.

**A3. The 8-vs-9 blank boundary, sitting ON the boundary.** Adopted (TASK-067).
Both reviews independently state the penalty spans the whole of Part 1, which
**corroborates TASK-001** from outside the project. This is the highest-value
XAT-specific UI assertion we can write.

**A4. Zero console errors and zero failed network requests on every page.** Adopted
(TASK-068). This is the cheapest possible detector for the whole Wave-1 defect
class: `lesson.js` failing to parse for a whole session while 161 tests passed is
precisely an uncaught `SyntaxError` that nobody read.

**A5. Error states are a first-class assertion: a missing or corrupt
`paper.json` must show a recoverable error, never a blank page.** Adopted
(TASK-069). Directly extends the measured `file://` failure.

**A6. Deep link, browser Back, Forward, and Refresh must be exercised.** Adopted
(TASK-070). Currently **0 of 4** covered, and `ORDER` being data rather than a
literal is exactly the change that could have broken them.

**A7. Keyboard-only journey; double-click submit records one attempt; no early
solution leak before commit.** Adopted (TASK-032, already open). The leak check is
scoped to the **worked example** — see the containment note below.

**A8. Persistence must be a DECLARED product rule before it is automated.** Adopted
(TASK-071). The decision stands: **no persistence** — `Cache-Control: no-store`,
answers in memory, no `localStorage`. Declaring it is what makes "refresh resets"
a testable contract instead of an accident.

**A9. No fixed sleeps; wait on a condition; capture screenshot, console, URL and
trace on failure; run the import smoke and `build` before the UI suite.** Adopted.
All of this is already the project's discipline, and both reviews arrived at it
independently — which is worth recording as external corroboration of the
housekeeping rules rather than as new work.

**A10. Per-lesson and parameterised from the registry, never typed into a test.**
Already D25. Reaffirmed, not adopted as new.

### REJECTED — with the reason, because "we read it" is not the same as "we did it"

**R1. A TypeScript Playwright `*.spec.ts` suite. REJECTED.**
We are a Python project whose existing probe already drives headless Chromium and
reports 58/58 per lesson. A second runner, a second browser driver and `node` as a
new runtime dependency would mean **two places per fact**, which is precisely the
D12 shape this project has now been bitten by repeatedly. The reviews assume
Playwright; we have a working tool. Adopting both would make the UI *less*
trustworthy, not more.

**R2. Per-question routes (`/xat/qa-di/<lesson>/question/2`) and a section index
page per exam. REJECTED — this is a different product, not a test change.**
We deliberately serve **one page per lesson holding all four rungs**. That design
is the measured fix for `ORDER` being a hardcoded literal and for `loadPaper(id)`
receiving `''`. The reviews then ask us to test that state survives the URL — i.e.
they would have us re-introduce the state-in-URL we removed on purpose.

**R3. Building `localStorage` persistence — with a versioned schema, migrations and
stale-schema reset — so the persistence tests have something to test. REJECTED.**
This is the clearest trap in either review, and it is worth naming: *do not build
a feature nobody asked for in order to satisfy a test.* The product has no
persistence by decision. The test asserts the decision (refresh resets), which is
honest; a versioned storage layer would be a fiction.

**R4. 28-question section mocks, 75-question full mocks, question palettes, timers,
a fake clock and a submit-confirmation modal as *current gate requirements*.
REJECTED as a gate; ADOPTED as roadmap.** None of it exists. Adopting ~20
scenarios that can only fail puts a permanently red gate in place, and a red gate
teaches its reader to ignore it. Recorded as TASK-072 (P1) for the phase that
builds them.

**R5. Chromium + WebKit + Firefox across three viewports at two zoom levels, as a
commit gate. REJECTED as a gate; ADOPTED as nightly.** With two lessons this is 27
runs per lesson, and the layout defect class we actually hit (white-on-white) was
caught by **one** contrast check. Also: `ui_probe.py` deliberately **exits 2 when
no browser is present**, so adding a browser that cannot run makes the gate
unrunnable rather than strict.

**R6. `role="radio"` and a real radio group for the five options. REJECTED for now;
recorded as a product decision (TASK-073, P2), not a test requirement.** A radio
group fights the commit barrier, because the options must be *inert until the
learner commits*. The accessible-name discipline is still adopted — but as a check
that **every control has a stable accessible name**, not as a Playwright API.

**R7. The `UiScenario` dataclass with `part_id`, `mode`, `expected_url`,
`expected_score`, `expected_progress`, `expected_persistence`. PARTIALLY REJECTED.**
The fields that map to something real today (`lesson_id`, `level`,
`initial_state`, `expected_visible_state`) are adopted. A schema where six of
thirteen fields are `None` for every current scenario is a schema for a future
product; writing it now means writing dead fields that no test reads.

### What NEITHER review could have told us

Worth stating, because it is the boundary of the tool:

- **Both reviews are written against a product that is larger than ours** — mocks,
  palettes, timers, GK, two exams. Roughly 70% of their line items are roadmap.
- **Neither can know our UI is a static shell plus a JS-built DOM.** MEASURED: the
  served `index.html` contains **zero** `<button>` elements; all nine are created
  by `lesson.js`. So a text assertion over the HTML is *structurally incapable* of
  finding an interactive bug. Every one of our 161 Wave-1 tests was of that shape.
- **Neither found the dead correct-answer path** (A2 below) — that came from
  MEASURED, after their warning told us where to look. External review is a
  pointer, not an oracle. The same rule this project applies to model-asserted keys
  applies to model-written test plans: *a review is an opinion until something
  falsifies it.*
