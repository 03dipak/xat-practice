# Working rules — xat_practice

This folder turns one thing into another: **the XAT 2026 syllabus into a
trainer that takes a single student from "I don't know what simple interest is"
to a percentile they can defend.**

Before anything else, read [`docs/DECISIONS.md`](docs/DECISIONS.md) §1 (the one
ledger) and [`docs/PEDAGOGY.md`](docs/PEDAGOGY.md) (what a good question *is*,
as countable rules). This file is how you work, not what the product is.

**Design lineage.** The working discipline is inherited from
[`../agentic_protracted_test`](../agentic_protracted_test) — read its `AGENTS.md`
and `opencode.json`. Its rules about evidence, denominators, falsifying inputs
and reviewer scoping are deliberate and are reused wholesale. Its code is not
imported and its *product* is not ours.

**Four load-bearing things differ, and every difference below exists because of
one of them.** Read these before copying anything from the reference project.

| | reference project | here | why |
|---|---|---|---|
| 1 | Source is **18 transcripts**; grounding = a cited quote | No corpus. Grounding = **the derivation itself** | D1 |
| 2 | 4 options, negative marking **refused** | **5 options, −0.25, and −0.10 per blank after the 8th** | D2, D3 |
| 3 | Difficulty = Bloom level **requested** from a model | Difficulty = **derived from the item's structure** | D6 |
| 4 | One section, depth ladder | Quant + LR&DI + VA, **section mocks AND full paper** | D7 |

Everything subordinate to keeping these four honest.

## The one failure that outranks the rest

**A wrong answer key actively teaches a wrong fact, and the student cannot
detect it.** A wrong analogy is one bad frame. A wrong key is a learner who now
believes something false and who will answer the next five questions
consistently with that belief.

So the key is **never model-asserted**. Here it is better than that: **a
quantitative key is a number, so it is RE-DERIVED, not second-guessed.**
`Solver.verify` evaluates the item's own derivation with exact rational/sympy
arithmetic and compares it to the keyed option. Disagreement is a **REFUSAL**
(`G5`), never a repair. That is strictly stronger evidence than the reference
project's blind second LLM call, and it costs zero LLM calls.

**The honest limit, stated once and never blurred.** The guarantee is *per
stratum*, and the strata are not equal:

- `Stratum.QUANT` — key **computed**. A percentile claim here is a statement
  about code.
- `Stratum.LOGIC` — key **enumerated** over a constraint set. Still computed.
- `Stratum.JUDGEMENT` (VALR, DM) — key **not computed**. Re-derived by an
  independent blind second call. This is a second *opinion*.

`Verdict.DELEGATED` exists solely to stop a judgement key from being reported
as `HOLD`. If a paper mixes strata, it reports them **separately**. A percentile
figure for the full paper that does not name its strata is overstated, and
saying so is cheaper than being wrong.

## Evidence, not opinion

1. **Run it.** Never review statically when the code can be executed. Generate
   a real paper and *sit* it.
2. **Cross-check the code's own invariants** — `GATE_IDS`, `_stem_fingerprint`,
   `self_check`, `guess_ev_report` — against real output, not against their
   logic.
3. **Root cause with numbers.** "3 of 13 gates never fire because `G7` compares
   against a claim the drafter never made" is a finding. "level logic may be
   improvable" is not.
4. **Disprove before reporting.** Re-check at a second subtopic, module, or
   paper size. If it does not survive, drop it and say you dropped it.
5. **Rank by evidence strength.** Confirmed-with-exact-cause first. Never bury
   one confirmed bug under ten nitpicks.
6. **Minimal fix, and why the old logic was wrong** — at the level of the wrong
   comparison, not "add a check here".
7. **Check for regressions of past defects.** **Half-fixes are findings.**
8. **A check that has only ever been shown a true statement is untested.**
   Write the *wrong* input first and confirm it fails. Each test in
   `tests/test_gates.py` is named after what it disproves, and
   `test_G5_planted_wrong_key_is_REFUSED` is the one that matters most.

## Numbers carry their basis

**Measured** = re-derived on this box, command written down. **Assumption** is
written as the word *assumption* and is a debt, not a fact.

- State the population. **A count with no denominator is a lie that looks like
  a pass.** The topic weightage is **196 questions = 7 papers × 28**
  (`syllabus.py`, 2020–2026), and `self_check()` asserts every year's rows sum
  to 28 — because that closure is the only reason the table is quotable at all.
- The weight table is `measured-from-secondary-source`: a coaching compilation.
  XLRI publishes no per-topic breakdown. Say which one you mean.
- `Topic("pct", ...)` is recorded at weight **0.0 to mean UNMEASURED, not
  absent**. Percentage is inside `avg_ratio` and inside the CollegeDekho
  "Arithmetic" row. Do not "fix" it to a number.
- Prefer the measured form to the configured one.

## Which reviewer to use

Each role may only use the evidence it is scoped to.

`G11` does not run on a lesson: it apportions the 20-item PAPER mix, and applied
to 4 items it produced `{1,1,1,0}` and dropped the hard rung. `MIX_ENFORCEMENT_FLOOR`
is 8. This is the third time a paper-shaped rule has tried to delete a lesson
shape, and it is why `LESSON` and `MOCK` are separate products rather than one
product with a length setting.

| role | evidence | use for |
|---|---|---|
| `ui-inspector` | the **rendered DOM** from `tools/ui_probe.py`, plus the pixels | what a browser actually does: does the script run at all, is the commit barrier real AS RENDERED, does the verdict agree with the solver |
| `viewer` | a rendered paper, **sat as a student would sit it** | answerable from the screen, readability, whether the step-by-step actually teaches |
| `question-setter` | paper vs [`PEDAGOGY.md`](docs/PEDAGOGY.md) | whether it is a *paper*: level spread, distractor diagnosability, key balance |
| `key-auditor` | derivation vs stem/options/key | **whether the key is right.** Expected to disagree |
| `level-auditor` | `derive_level` output vs claimed level | whether an item is **really** at the tier it claims. The XAT-specific role, born of D6 |
| `paper-auditor` | two papers vs the mock spec | section counts, option counts, marking, blank-penalty realism |
| `tester` | the gate suite + a real generated paper | gate behaviour, refusal counts per gate, wall clock |
| `doc-reviewer` | prose claims vs the files | docs accuracy — explicitly **not** whether code works |
| `code-reviewer` | the source | duplication, dead paths, complexity |
| `mentor` | all of the above, plus product calls | rulings and trade-offs |

**Three boundaries `key-auditor` must not cross.** It does not decide whether the
paper is well-made (that is `question-setter`), it does not decide whether a gate
is implemented correctly (that is `tester`), and it is **never** asked "does this
look right?" — a question phrased that way gets agreement. It is asked **"find
the option that is also correct, or prove the key is wrong."**

**A beautiful and wrong paper is the failure mode.** `question-setter` is the
only role that sees "well-crafted and unanswerable"; `key-auditor` is the only
one that sees "answerable and wrong". A paper can pass both and still unfit to
teach.

## Facts that will bite you

- **The exam changed and most material online is stale.** MEASURED from XLRI's
  own 2026 notification: **95 questions, 180 min**, Part 1 = **QA&DI 28 +
  VA&LR 26 + DM 21** under **170 min with NO sectional limit**, Part 2 = GK 20
  in 10 min. **5 options** (not 4). **−0.25** wrong, **−0.10 per blank after the
  8th**. **On-screen calculator in QA&DI.** GK is **excluded from percentile**.
  Anything you remember about "60 questions, 3×20, sectional timing" is the
  pre-2025 pattern and is wrong here.
- **A key POSITION is as dangerous as a wrong key.** MEASURED: all four of Lesson
  1's keys sat at index 0, so `always answer A` scored 4 of 4 — full marks for
  reading nothing — and all 14 gates passed it. `G15` now refuses a set whose best
  fixed-letter strategy beats random guessing by more than 10% of the marks. Every
  paper fixture in `tests/test_gates.py` had the same defect, which is why the rule
  had to be a gate and not a fix: it was in the authoring **convention**.
- **Guessing has EV exactly 0.0 at 5 options** (measured, `expected_ev`:
  `+1/5 + 4/5×(−0.25) = 0.20 − 0.20`). It is **+0.0625 at 4 options**. This is
  the arithmetic behind reversing the reference project's D5 and D6: a 4-option
  −0.25 paper *pays you to guess*. Do not import that ruling.
- **The 9th blank is the trap.** EV of the 9th blank = **−0.10**, worse than
  guessing at 0.0. So "skip if unsure" is wrong past eight blanks. This inverts
  the standard advice and is a whole lesson.
- **Hand-computation difficulty is the wrong axis** — the exam supplies a
  calculator. `G9` refuses any item over 2 minutes. An item that needs
  arithmetic a human cannot do *with a calculator* is badly set, not hard.
- **Data Sufficiency is absent from the owner's focus list (15 lines, not the 17
  this file used to claim — that was `TOPICS`' own size) and appears every single
  year.** So do Inequalities, Graphs & Functions (new in 2026, 3 questions) and
  Venn. These are additions, recorded as D4. **The owner confirmed the additions
  2026-10-02**, and chose the *order* himself: **Geometry lesson first, then the
  mock, then the full paper (D14)** — overriding the recommendation that Data
  Interpretation (6.71 q/yr, the largest block) go first. Do not reopen the
  order without saying so.
- **The rights posture is PUBLISHED, and that is a decision, not an oversight.**
  `github.com/03dipak/xat-practice` is public and the owner chose that on
  2026-10-02 (**D15**), after being told the inherited posture was an unasked
  assumption and that a routine `git push` would have published the work as a
  side effect of a version-control command. Do not treat publication as an
  accident to be cleaned up, and do not re-open it without asking.
- **The model ignores a requested difficulty level.** Inherited MEASUREMENT from
  the reference project: requesting `Apply` then `Analyse` returned the
  identical stem on 4 of 6 items. So `derive_level` computes the tier from
  `derivation_steps`, `needs_substitution`, `insight_required`,
  `enumeration_size` and distractor quality. `LEVEL_RECIPES` is the one place a
  level may be requested — and it is requested of **code**.
- **Ordering matters.** Gates read state others write; `G2` short-circuits the
  solver, so it must run before `G5`.
- **A commit barrier is a FILE boundary, not a UI convention.** MEASURED: the
  first bundle served the stem from the same loader that served the key, so the
  whole `answerkey.json` was in memory before the learner committed. Every test
  on it passed, because each checked one property and none checked the fetch
  path. `paper.json` must be useless for grading, and `answerkey.json` is
  fetched inside `check()` only.
- **An untested file cannot drag a floor down — it is INVISIBLE.** MEASURED:
  the coverage floor read **95.19%** and passed for a whole session. `cli.py` was
  absent from the report because **no test had ever imported it** (115 stmts,
  16% of the package). The real number was **86.13%**. Coverage measures only
  what something executed, so a module nothing imports cannot fail a gate it is
  not in. When a new test imports a module, the denominator changes — re-read the
  whole table, not the total.
- **`serve` must stay `ThreadingHTTPServer`.** The single-connection
  `TCPServer` wedged permanently the first time a browser held a connection open
  (favicon probe). Symptom: the page "takes too much time to load"; the server
  log then shows a browser session and **nothing served afterwards**. It looks
  transient and it is permanent.
- **`lesson.js` did not parse for the whole of Wave 1. 161 tests passed.** An
  apostrophe in prose — `item's` — closed a JS string literal, so the browser ran
  **none** of the file and the page showed only the static HTML. Every test
  asserted on the file's TEXT; none asked whether it was valid JavaScript.
  `node --check` on the built file and the node-free quote-parity test now gate
  it. **A test that asserts a string has been shown a true statement and is
  still untested** — `test_the_reveal_button_starts_disabled` asserted that
  `…disabled = false` existed, which is the *enabling* line; driving the real
  page showed the button was never disabled at all. **Render the artefact. A
  static bundle's correctness is not a property of its text.** A headless
  Chromium is at
  `~/.cache/ms-playwright/chromium_headless_shell-*/chrome-linux/headless_shell`
  and takes `--dump-dom` and `--screenshot`, which is how this was found.
- **The commit barrier must be an ATTRIBUTE, not a statement.** `<button
  id="reveal" disabled>` — a `.disabled = false` line cannot make a button start
  disabled, and asserting that line exists proves nothing about the born state.
- **`serve` sends `Cache-Control: no-store`.** `lesson.js` is a `<script src>`;
  without it a learner can run yesterday's script against today's page, which
  renders half of what is on disk with no error anywhere.
- **Measure before believing "slow".** The owner's page was reported slow; every
  asset was 1.4–4.8ms and the whole page was ~12ms. It was not slow, it was
  absent, and one thing was lying. `docs/DECISIONS.md` §6 has all four defects.
- **`ui_probe.py` exits 2 when it has no browser, and that is deliberate.** Two
  checks in this project's history reported success while proving nothing: the
  coverage floor reading eight files out of nine, and
  `test_the_reveal_button_starts_disabled` asserting an *enabling* line. A check
  that cannot execute must not be able to return success.
- **The CSS is a separate file and must stay one.** MEASURED 2026-10-02: with the
  styles inline in `index.html`, `.opt` set `background` but not `color`, so the
  generic `button { color: #fff }` rule won and **all five options rendered white
  on white**. The nodes were in the DOM — devtools showed the markup perfectly
  while the screen showed nothing — and **38 UI checks passed**, because every one
  asserted that an element *existed*. Worse, the probe loaded no stylesheet at
  all, so its own contrast check passed too: it was measuring a page that does
  not exist. `style.css` is loaded by both the page and `tools/ui_probe.html`,
  and `every-option-is-legible-contrast-at-least-4-5-1` now catches it. **An
  element that is present and illegible passes every DOM assertion there is.**
- **`lesson.js` is wrapped in an IIFE. Keep it that way.** `check`, `state`,
  `ORDER` and `render` were global, and a probe's own `check()` silently replaced
  `lesson.js`'s — the page stopped working with no error. `ui_probe.py` is the
  reason this is now pinned.
- **`ORDER` is DATA, and the id is read AFTER the paper loads.** MEASURED
  2026-10-02: `ORDER` was a hardcoded literal of Lesson 1's four ids, so
  registering Lesson 2 produced a page showing **Lesson 1's stems with Lesson 2's
  key file** — first screen and answers from different lessons. It now comes from
  `paper.json`. The trap that came with it: `loadPaper(id)` took the id, and
  `render()` computed `const id = ORDER[state.i]` **before** calling it, which
  worked only because `ORDER` was a literal. Derived, the first call passed `''`,
  `find` returned `undefined`, and the page went blank with no error. **`loadPaper`
  takes no id** so the dependency cannot be reintroduced.
- **A paper gate must be given a paper.** MEASURED: with two lessons registered,
  `gates` over the pooled 8 items admitted **0 of 8** and refused `L2-F`
  ("foundation over quota (1/1)") and `L1-F` — both individually perfect. `G11`
  apportions the 20-item PAPER mix and `MIX_ENFORCEMENT_FLOOR` is **8**, a number
  chosen to mean "smaller than a paper", which **two lessons now reach**. `G15`
  likewise measured a fixed-letter strategy across a pool no candidate is ever
  handed. `cmd_gates`/`cmd_levels` now iterate `LESSONS` (D23). This is D12's
  defect one level up: removing `G11` from lessons left the *pool of lessons* free
  to become the new fake paper.
- **A lesson must derive one item per level.** MEASURED: Lesson 2's first build
  gave `L2-F` **1.65 — EASY**, because all four distractors were flagged real
  near-misses and `0.85 + 4×0.2` crosses the 1.50 line. The lesson had **no
  foundation rung** and nothing said so: `G11` does not run on 4 items, `G7`
  compares a `claimed_level` that is `None` on every authored item, `G8` is
  satisfied by four. `registry._assert_one_rung_per_level` now refuses it (D24).
  **A flag on a distractor is a difficulty knob**, so four "real" near-misses on a
  one-step item is arithmetic, not taste.
- **A UI check must be able to see the lesson it is checking.** MEASURED: the same
  probe, same 47 checks, aimed at Lesson 2 gave **42/47** — four checks asserted
  Lesson 1's formula/legend/units/example as literals, and the fifth clicked the
  literal item id `L1-F`, which is not in Lesson 2, so it clicked **nothing** and
  reported on a page it had not read. `47/47` was one lesson, quoted as the UI.
  `EXPECTED`, `TEACH` and `Q1` are now injected from the bundle under test, and
  `tests/test_render.py` runs the probe **once per registered lesson** (D25).
  **Run the probe at every lesson before believing a UI number.**
- **A leak check that cannot fail on the bug it names is not evidence.** The two
  leak checks searched for `"Rs 200"` and `"1,000"`; against Geometry those are
  absent, so they passed — and would have passed on a page printing Geometry's
  answer. Second time **containment** has beaten this check (`"200"` is inside
  `"2000"`, then `"10"` inside `"100"`), so numbers are compared as **sets**
  extracted from both sides. And the comparison is scoped to the **worked
  example**: Lesson 1's card was wrongly accused of reusing Q1's `10` and `2`,
  which live in its legend's explanations (`"10% means you write 10"`).
- **`serve --lesson` takes a lesson_id, not a path.** It defaulted to `out/`, a
  directory of lesson directories, so the default served a listing and the second
  lesson was unreachable without knowing its exact path.
- **`serve` with no `--lesson` ASKS, and it used to guess.** MEASURED 2026-10-02:
  it defaulted to the FIRST registered lesson, so a learner who wanted Geometry
  typed the documented command and got Simple Interest with nothing saying a
  choice existed. Safe by being invisible. `menu.py` now asks, orders by measured
  topic weight, prints `2 of 40 subtopics written` rather than hiding the 38, and
  reads every paper figure from `syllabus.PAPER_SHAPE`. Junk input returns None —
  **never the first lesson**, which is the bug in a new dress.
- **The LEVEL is the learner's; the MIX is only for a paper (D26).**
  `LEVEL_MIX` 10/25/40/25 → 2/5/8/5 at n=20 is *derived* from 136 s/question, so it
  is right for a MOCK. A drill is level-filtered, and **`G11` must not be handed a
  single-level drill** — it would refuse items for "under quota (0/5)", the D12
  defect. Do not "fix" this by flattening `LEVEL_MIX` to 25% each: that would
  change `QUANT_MOCK` and `FULL_MOCK` too, and destroy the measured basis.
- **`uv sync` PRUNES.** It removes anything in `.venv` that is not declared in
  `pyproject.toml`. Before `[dependency-groups] dev` existed it deleted mypy,
  pytest, pytest-cov and ruff — the four tools the gates are run with. Declare
  every tool there.
- **`uv run` is read-only HERE, and the gate commands use it. This file used to
  say otherwise.** The old claim was that `uv run` resolves and syncs *before*
  running, so a measurement would mutate the box it measures. MEASURED
  2026-10-02: it changed **0 files** under `.venv` — the `*.dist-info` set hashes
  identically before and after, and `find .venv -newer <stamp>` is empty. It is
  read-only **because** `uv.lock` is committed and every tool is declared, so
  there is nothing to re-resolve and nothing to prune. **Remove either and the
  old warning comes back**, so this is a condition, not a preference.
  Cost is ~0.05s per call (MEASURED). The owner ruled `uv run` for all documented
  commands on 2026-10-02.
- **`python -m pytest` and `pytest` were NOT the same command, and only one
  worked.** MEASURED: bare `pytest` failed **7 of 299** with `ModuleNotFoundError:
  No module named 'tests'`; `python -m pytest` passed all **292**. Same
  interpreter, same venv, same code — `-m` puts the CWD on `sys.path[0]` and the
  console script does not, and `tests/test_api.py` does
  `from tests.test_gates import at_level`. Invisible because **every** documented
  command used the long form, so the suite had only ever run in one of its two
  legal forms. `pythonpath = ["."]` in `pyproject.toml` fixes it for both. **The
  general trap: a suite with an undeclared import dependency looks identical from
  inside and behaves differently outside the command you always type.**
- **Display strings are not arithmetic.** `Rs 200` and `2 : 3` do not parse as
  sympy, and `14,400` parses to the TUPLE `(14, 400)` rather than failing.
  `Item` carries `option_values` for the arithmetic and `G14` asserts the value
  is visible in the label.

## Retired, and why — do not re-open

- **`Verdict.HOLD` for a judgement item.** Was the first design; it would have
  claimed code confirmed a prose key. Retired in favour of `DELEGATED`.
- **`run(..., expected=n)`.** Silently truncated the admitted set and could
  contradict `G11`. Removed; `G11` owns the mix.
- **`G10` as one comparison over all three strata.** Refused 100% of logic
  items. Now checks QUANT and JUDGEMENT separately.
- **A flat +0.8 near-miss bonus at `real >= 3`.** Made one extra plausible wrong
  move worth a whole level. Now linear at 0.2 each.
- **`G11` on a lesson.** See above. It deleted the hard rung.
- **One loader for the paper and the key.** The commit barrier was theatre.
  Split into two files.

## Numbers you may quote

All re-derivable. Command, population, and limitation stated each time.

```
uv run ruff check src tests tools
uv run mypy src
uv run pytest -q --strict-markers --cov
uv run coverage report --include="src/xat_practice/*.py" \
    --fail-under=95 --precision=2
```

The last command is a **separate** command, not a coverage `include`, because
one `include` cannot both scope the floor to our own package and leave the whole
tree visible. Scoping the printed table hides the population you most want to
watch, with no error and no warning.

`--cov` lives in `addopts` in `pyproject.toml`, not only in the coverage
command. Without it, `pytest -q` writes **no** coverage data and the fourth
command then reports whatever `.coverage` is on disk — possibly hours stale — as
a fresh measurement. A floor reading stale data is **worse** than no floor,
because it looks like a measurement. That defect is the reference project's F1
and it was quoted as current by two separate sessions. Do not remove `--cov` to
speed the suite up.