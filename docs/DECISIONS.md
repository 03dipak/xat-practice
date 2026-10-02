# DECISIONS — the one ledger

Every ruling lives here with the reasoning that produced it. A ruling without a
reason is a preference, and preferences rot. Reverse decisions by **superseding
them** and saying so, never by editing them away — a doc that tracks its own
history is the only way to tell a mistake from a change of mind.

Status: **Waves 0 and 1 landed.** 198 tests, **96.64%** coverage on
`src/xat_practice/*.py` across all nine files, ruff and mypy clean (mypy on 9
source files). **Re-measured 2026-10-02.** The gates, the solver, the weight
model, the derived-difficulty model, Lesson 1 and the static bundle all exist and
are measured. `enumeration.py` and the blind second call are not built. **D3 and
D4 accepted by the owner 2026-10-02**; D14 fixes the build order as lesson →
mock → full, with Geometry first; **D15** settles the rights posture as
published.

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

### D15 — The rights posture is PUBLISHED, and the owner decided it

**Ruled 2026-10-02, by the owner.** This closes the last open owner item.

The posture was inherited as an *assumption* — "private cohort revision, not
published" — and it was labelled an assumption because nobody had ever asked. The
repository `github.com/03dipak/xat-practice` was then created **public**
(MEASURED: `api.github.com/repos/03dipak/xat-practice` returns
`"private": false`), and pushing there would have turned the assumption into a
publication by accident.

The owner was told exactly that, and chose to publish. So the posture is now:

- **PUBLISHED**, not private. Anyone may read the lessons, the weight model and
  this ledger.
- Consequence accepted knowingly: a public repo is indexed by search engines, and
  changing visibility afterwards does not un-index what was already crawled.

**Why it is written down at all.** An assumption that survives unasked becomes a
fact nobody chose. This one was nearly that: a routine `git push` would have made
the product's rights posture a side effect of a version-control command. The
distinction between *assumed* and *decided* is the entire reason the item was
tracked, and it cost one question to keep.

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
- **Owner items: NONE open.** The D4 additions were **confirmed by the owner on
  2026-10-02**. The rights posture was **decided, not assumed**, on 2026-10-02:
  see **D15 — published**. Do not reopen either.
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

---

## 6. Found by the owner sitting the page

**Five** defects, all reported by the owner on 2026-10-02 as "the page takes too much
time to load, and the first screen is only the title". **None of them was a
performance problem.** Every asset was measured first and every asset was fast:
`lesson.js` 1.4ms, `paper.json` 2.8ms, `index.html` 4.8ms — about 12ms for the
whole page. Chasing speed would have found nothing, because the page was never
slow. It was *absent*, and one thing was *lying*, and one floor was *not counting
what it claimed to count*.

These are recorded with more detail than usual because the first instinct on all
five was wrong, and "I measured and it was fine" is a conclusion that has to be
earned here rather than assumed.

### 6.0 The lesson page had never worked. Not once.

**This is the finding that matters, and it is first because the other four are
footnotes to it.**

The owner sat the page and saw the title, the subtitle, and nothing else. That is
the *static* HTML at `bundle.py:120-122` — the only markup that renders when no
JavaScript executes.

`lesson.js` did not parse. The footer contained:

```js
'after you commit. Difficulty was <strong>derived from each item's ' +
```

The apostrophe in **`item's`** terminates the JavaScript string literal. `node
--check` on the served file: `SyntaxError: Unexpected identifier 's'`. The
browser therefore refused to execute **a single line** of the file — not the
rendering, not the fetch, not the commit barrier. Nothing. Ever.

**And 161 tests passed the entire time.** Every one of them asserted on the
*text* of the built files. Not one asked whether the file was valid JavaScript,
and not one asked whether the page ran.

How it was actually found: a headless Chromium was pointed at the served page and
the DOM dumped after load. Rungs empty, stage empty, footer empty — all three
elements that only `lesson.js` ever writes. Then `node --check`.

The lesson has never been clicked by a human until now, and `AGENTS.md` already
carried the reason it went undetected: **the bundle has been read, not clicked.**
This is what that sentence was warning about, and the warning was written by a
session that did not yet know how bad it was.

Three checks now exist, and all three were verified to **fail on the
reintroduced defect** before being accepted:

| test | what it pins |
|---|---|
| `test_the_served_javascript_actually_parses` | `node --check` on the built file |
| `test_js_strings_have_no_bare_apostrophe` | node-free: a line opening a `'…'` string must have an even count of unescaped quotes |
| `test_the_bundle_checks_the_javascript_it_serves_before_serving_it` | the same rule against `bundle.JS` at build time, so the failure is a build error naming the line, not a silent page |

**The general lesson, and it is the most transferable thing in this file:** a test
that asserts a *string* has been shown a true statement and is still untested.
`test_the_reveal_button_starts_disabled` asserted that the text
`…disabled = false` existed in the file — that is the line that *enables* the
button, and it proves nothing about the state the button is born in. Driving the
real page found the button **was not disabled at all**: a learner could skip the
commit, see the options, and never record a confidence. The commit barrier was
opt-in. It is now `<button id="reveal" disabled>` and the test asserts the
attribute.

**So: what would have caught it, and it is not more reading.** Execute the
artefact. A static bundle's correctness is not a property of its text.

### 6.1 The server wedged permanently on one held connection

`cmd_serve` used `socketserver.TCPServer`, which handles **one connection at a
time**. `SimpleHTTPRequestHandler` blocks reading until a request arrives, so a
client that opens a socket and then holds it idle parks the only thread forever.
Browsers do this routinely — favicon probe, preconnect, prefetch.

MEASURED: the server log recorded a real browser session that requested
`/favicon.ico` at 10:21:42 and then **nothing was served at all**. A plain `curl`
after that timed out at 5 seconds. The page had stopped loading permanently,
with no error and no exit.

This is the actual cause of the owner's report, and it is a *permanent* failure
from a *transient* one: the server was fine when it started and dead minutes
later, which is why "it worked when I first opened it" and "it never loads" are
both true.

Fix: `http.server.ThreadingHTTPServer`, plus `daemon_threads` and a handler
`timeout` so an idle socket cannot pin a worker either.

- `test_one_held_connection_does_not_block_the_next_request` opens a socket that
  says nothing — the falsifying input, written first — and requires the next
  request to succeed. Against the old server it **hangs for its full 5s timeout**,
  which is the defect reproducing itself.
- `test_the_server_is_threaded_not_single_connection` pins the mechanism, so the
  property cannot be lost to a well-meaning revert.

Verified live after the fix: three assets in **15ms while a socket was held
idle**.

### 6.2 `render()` painted nothing until the network answered

`render()` did `const meta = await loadPaper(id)` **before** writing anything to
`#stage`. So the stage was empty for the whole fetch, and **permanently empty if
the fetch rejected** — with nothing on screen to say so. That is precisely what
the owner described: the title, the subtitle, no question.

Fix, in two parts:

1. the card is painted **synchronously, before any await**, so the first screen is
   never empty and never looks broken;
2. a rejected fetch renders the **reason**, naming the `file://` case, because
   opening `index.html` directly is the failure learners actually hit.

Also fixed in the same pass: `loadPaper` re-fetched `paper.json` on all four
questions with `cache: 'no-store'`, so every transition re-downloaded a 2KB file
and flashed an empty page. The promise is cached; questions 2–4 now resolve from
memory.

Four new tests, each verified to **fail on the pre-fix code**:
`test_the_first_screen_is_painted_before_the_network_answers`,
`test_a_failed_paper_fetch_names_the_reason_instead_of_leaving_a_blank_page`,
`test_moving_to_the_next_question_does_not_refetch_the_paper`, and
`test_the_finish_screen_reports_the_quadrant_it_collected`.

### 6.3 `state.log` was written to nowhere

`finish()` read `state.log.filter(Boolean).length` and **nothing ever pushed to
it**, so the count was always 0 — and then the finish screen never displayed it
at all. The quadrant is the product's central claim (`PEDAGOGY.md` §2), and the
screen meant to report it reported nothing. It now records each cell and names
the sure-and-wrong rung when there is one.

### 6.4 The coverage floor was not counting `cli.py`

**This is the one that matters most, and it was in the number the README quoted.**

The floor read **95.19%** and passed. The package's real number was **86.13%**.

`cli.py` was **absent from the report entirely** — 115 statements, 16% of the
package — because **no test had ever imported it**. Coverage only measures a
module that something executed, so a file nothing imports is invisible, and an
invisible file cannot drag a floor down. The moment one new test imported it, the
table grew from 541 statements to 656 and the floor failed.

It is the same failure as a stale `.coverage` file, wearing a different hat: **a
count with no denominator is a lie that looks like a pass.** `95.19%` was true
of eight files and was quoted as the truth about nine.

The whole of the CLI had never been executed by the suite — all eight verbs. Fix:
`tests/test_cli.py`, 24 tests, and **96.64%** across all nine files.

The second reason those tests are worth having: **every verb prints a number a
document quotes.** `weightage` prints the population, `ev` prints the three
marking figures, `shapes` prints the quotas, `gates` prints a refusal rate with
its denominator. `test_the_readme_quotes_the_population_this_cli_prints` and
`test_the_decision_ledger_quotes_the_same_population` tie the two together, so
the doc and the verb fail as one fact instead of quietly disagreeing.

**MEASURED, and it belongs here:** this file, `AGENTS.md` and `task.txt` all
quoted `95.19%` and the number of tests as `161` for a whole session after that
number stopped being true of the package. Re-measuring is cheap. Assuming a
previously measured number is still valid is how it stops being one.

### 6.5 Two facts about the lesson page, for the record

- The commit barrier survived all of this. `test_the_key_is_fetched_only_after_check`
  asserts `await loadPaper(` is the only loader on the load path and that the
  single `await loadKey(` sits inside `check()`. It was not weakened to
  accommodate the caching fix, and the paper is still fetched **once** for the
  whole lesson rather than four times.
- `test_the_server_is_not_the_thing_that_is_slow` pins every served asset under
  20KB. It is a guard, not a defect detector — it passes on both the broken and
  the fixed version, and it is named as such rather than being allowed to look
  like evidence.

### 6.6 The UI probe, and the three defects only a browser could find

Written after §6.0, because §6.0's method needed a home. The pattern is lifted
from the sibling project `photos_graphics`, which had already paid for this
lesson: *"all the earlier tests were static string assertions, and a script that
threw ReferenceError before measuring once had a green suite. This executes the
real script."*

`tools/ui_probe.html` is the page, `tools/ui_probe.py` serves the built bundle
through the **real** threaded server and drives it in a headless Chromium, and
`tests/test_render.py` gates on the result. **34 checks.** Exit 2 when no browser
exists, because a check that cannot run is not a pass.

Three further defects surfaced, and none was reachable by reading the source:

**The options were in the DOM before the commit.** `render()` injected them into
`<div id="optBox" class="hidden">`. Hidden is not absent: the module docstring's
first numbered step claimed *"STEM ALONE. The options are not in the DOM."* That
claim was **false**, and a false claim in a docstring is worse than either a
working barrier or an honest gap — it reads as a guarantee to every later session.
`test_options_are_not_in_the_dom_before_the_reveal` had passed throughout because
it asserted on `index.html`, which never had them in it, while `lesson.js`
supplied them at runtime. The option box is now built **empty** and populated
inside the reveal handler, so `qa('.opt').length === 0` before the commit.

**A global `function check()`.** `lesson.js` declared `check`, `state`, `ORDER`,
`render`, `esc`, `fail` and `next` at global scope. The probe then declared its
own `check(name, pass, detail)` — same scope — and **silently replaced
`lesson.js`'s**. The click handler called the wrong function, `answerkey.json`
was never fetched, and the page produced no verdict at all. It surfaced as one
vague failing check and cost a long diagnosis; the giveaway was a single
unnamed probe result, `{"pass": false, "detail": ""}`, which is `lesson.js`'s
`check()` invoked with the wrong arity. The whole script is now inside an IIFE
and `lesson-js-leaks-no-globals` pins all twelve names as private.

**A test that asserts source order as a proxy for flow order.**
`test_the_flow_is_commit_then_options_then_check_then_solution` asserted that
`reveal`, `optBox`, `check`, `result` appeared in that order *in the file*. The
moment the implementation became correct, the check button moved into the reveal
handler and the proxy broke. **A proxy that fails when the thing it proxies gets
right is worse than no proxy.** The test now asserts the real structure, and the
rendered order of the steps is asserted against a browser.

And the probe hardened itself after each of these:

| defect in the probe | what it cost |
|---|---|
| an unnamed result crashed the runner with `KeyError` | looked identical to "a check failed" |
| a rejection inside `lesson.js` was invisible | the probe could only say "it did not work" — now `window.onerror` + `unhandledrejection` are captured and reported |
| `the-commit-is-not-graded-or-sent` grepped the page for `localStorage` | matched **its own source**; now asserted as network activity |
| `required.relative_to(ROOT)` in a diagnostic | `ValueError` when the bundle is outside the project — a diagnostic that crashes is not a diagnostic |

**Every UI check was confirmed to FAIL against the reintroduced defect** before
being accepted. The syntax error gives `0/1, state: dead`; putting the options
back in the DOM gives `no-option-exists-in-the-dom-before-the-reveal: FAIL —
5 .opt elements present` and `clicking-a-disabled-reveal-does-nothing: FAIL —
5 .opt elements leaked by a disabled button`.

### 6.7 `ui-inspector` — the role, so the method has an owner

Ten agents, not nine. A tool that nothing is required to run is a script, not a
gate, and a method that belongs to no role is a habit that expires.

`ui-inspector` owns what a browser does with the built lesson, and its prompt
names the four defects above so they cannot be reintroduced quietly. Its
boundaries are the three that get confused: whether the step-by-step **teaches**
is `viewer`, whether the **key** is right is `key-auditor`, whether a **gate** is
implemented correctly is `tester`. It renders, and hands off.

`test_ui_inspector_carries_the_defects_it_must_not_reintroduce` fails if
`item's`, "Hidden is not absent", `window` or "recomputed key" are dropped from
the prompt.

### 6.8 White on white: 38 UI checks passed while the page was unusable

**The owner reported "not able to see any option or values", and pasted the DOM
they could see.** Five option rows existed, with the right letters and the right
values. None of them was legible.

`.opt` set `background: #fff` but did not set `color`, so the generic
`button { color: #fff }` rule — the one that makes the primary button dark —
won. **White text on a white background, five times, plus five letter badges.**
Every node was present, which is exactly why devtools showed the markup
perfectly while the screen showed nothing. This is what a white-on-white failure
looks like from the DOM side.

**38 UI checks passed against it.** Every one of them asserted that an element
existed, had the right text, had the right classes, was clickable. Not one asked
whether a human could read it. *An element that is present and illegible passes
every DOM assertion there is.*

And the first contrast check written for it **also passed on the broken build** —
1 pixel of which was because the probe page loaded **no stylesheet at all**. With
no CSS the buttons were default grey and perfectly readable, so the probe was
measuring a page that does not exist.

So the stylesheet became its own file, `style.css`, loaded by both the page and
the probe. MEASURED on the reintroduced defect, the check then reports exactly
what was wrong:

```
FAIL  every-option-is-legible-contrast-at-least-4-5-1
      option A contrast 1.00:1 (rgb(255, 255, 255) on rgb(255, 255, 255))
      badge A contrast 1.00:1  ... through option E and badge E
```

Three checks now, because each catches something the others cannot:

| check | what it catches |
|---|---|
| `every-option-is-legible-contrast-at-least-4-5-1` | white on white, and any future contrast failure |
| `every-option-shows-its-letter-and-its-value` | an option that renders but has no text |
| `every-option-has-a-clickable-height` | a collapsed or zero-height row |

**The general lesson, and it is the second time this session.** §6.0 was "the
text was never valid JavaScript". §6.8 is "the text was valid, the DOM was
correct, the behaviour was correct, and the page was unusable." **Correctness
has three layers and this project had only ever checked two:** the data, and then
the DOM. The layer in between — *what it looks like* — was unmeasured from the
start, and both defects were in it.

The screenshots were the only reason either was found. `test_the_probe_page_...`
now requires `--shot-dir`, and every stage is photographed from the real page
with the real stylesheet, because the probe page's own screenshot came back as
unstyled text: a fine DOM and a useless visual record.

---

## 7. D16 — G15: the key POSITION must not be the answer

**Ruled 2026-10-02, from the owner's report.** "Here all question answer A,
which is not good." Correct, and the finding underneath it was the worst of the
project's life.

All four of Lesson 1's keys sat at index 0. A learner who answered **A** on
every question scored **4 of 4** — `+4.00` of a possible `+4.00`, full marks,
having read nothing. Measured, on the real marking scheme:

```
always answer A: 4/4 correct   XAT score +4.00 of a possible 4.00
always answer B: 0/4 correct   XAT score -1.00
```

**All fourteen existing gates passed it.** `G2` checks the key is *in range*.
Nothing in the module checked where it *sat*. Every gate looks at one item, or at
a level mix; not one asked the only question that matters about a set of keys —
**can the position alone score?**

### Why it survived, which is the part worth keeping

Nobody chose it. Every author wrote the correct answer first and listed the
distractors after it. Four items, one habit, one result.

And it was not confined to the lesson. **Every paper fixture in
`tests/test_gates.py` put its key at the same index too**, so `always answer B`
scored 20 of 20 — living inside the very tests that were meant to catch it. The
defect was in the *authoring convention*, not in one file, which is the only
reason a gate was needed rather than a fix.

### The rule

`G15_key_not_predictable` scores the best always-the-same-letter strategy with
the real marking scheme and refuses if it is worth more than **10% of the marks
on the paper**.

The 10% is not a preference. It comes from a number already in this module:
**random guessing on five options at −0.25 has expected value exactly 0.0**
(`+1/5 + 4/5×(−0.25)`, `guess_ev_report`, D3). So a paper where picking one
letter without reading is worth more than a tenth of the marks **pays a learner
for not retrieving** — which is the single thing this product exists to prevent.

It is not set to zero. XLRI publishes no key distribution, and 5–6 keys per
letter across 28 items is ordinary; a ceiling of zero would refuse real papers.
It is set so that a four-item lesson must have a near-distinct spread, which is
what a four-item lesson needs.

| set | best fixed letter | before | after |
|---|---|---|---|
| Lesson 1 (4 items) | A | **+4.00** of 4.00 | **+0.25** of 4.00 |

Keys now sit at **0, 1, 2, 3**. `test_a_fixed_letter_cannot_score_the_paper` is
written against the shipped defect and fails if it is ever admitted; reverting
Lesson 1's key positions makes **five** tests fail, including
`test_lesson1_every_key_is_recomputed`.

**Ordering is normative.** `G15` runs after the per-item loop and after `G11`,
because it must judge the set that will actually be *served*. Judging the full
input instead would pass a paper that `G11` had already thinned into a
fixed-letter remainder.

### 7.1 Four options whose explanation did not produce them

`key-auditor` audited the four items and confirmed **all four keys**. It also
found distractors whose *stated cause* does not compute to the option beside it.
Writing a test that checks exactly that found **two more it had missed**.

| item | option | its own stated cause | that cause actually gives |
|---|---|---|---|
| L1-E | Rs 10,250 | "the time count dropped, 10,000 x 5 / 100" | **10,500** |
| L1-E | Rs 10,200 | "the 5 divided by 10, rate read as 10%" | **12,000** |
| L1-F | Rs 120 | "the /100 was dropped, 1,000 x 10 x 2" | **20,000** |
| L1-H | Rs 14,700 | "compounded, 12000 x 1.1^2" | **14,520** |
| L1-M | 4 : 3 | "the interest ratio inverted but not simplified" | **impossible** — 2160:1440 is 3:2 already in lowest terms |

**Four of them were digit transpositions.** 10,250 for 10,500. 14,700 for
14,520. And `Rs 120`'s real move is `1000 x (10 + 2) / 100` — the rate and the
time **added** instead of multiplied — which is a better trap than the one the
text described, and is now what it says.

Every one of these passed `G8` (near-miss count), `G12` (a distinct named
misconception exists), `G13`, and `G5`. **The gates check that a distractor has a
misconception; they never check that the misconception produces the distractor.**
That is the gap, and `test_every_distractor_is_produced_by_the_move_it_names`
now closes it for every item in the lesson.

A distractor whose cause is false is worse than a bad distractor: a learner
cannot rule it out, and the explanation teaches a rule that is not true.

### 7.2 L1-M is the one item that is not sound, and it is left that way on purpose

Three problems, all confirmed by hand:

1. Two of its four distractors need a denominator of **18**, and nothing in the
   item produces 18 — both sums have `r x t = 24`, and `8+3=11`, `12+2=14`.
2. Its headline insight — *the ratio of two interests is not the ratio of two
   principals* — is **false for its own data**, precisely because `r x t = 24`
   on both sides, so `1440 : 2160` and `6000 : 9000` are both `2 : 3`. A learner
   who skipped the recovery landed on the key by accident.
3. The coincidence is **forced** by the numbers: keeping 6,000 and 9,000 with
   those interests pins `r x t` at 24 twice.

So (2) cannot be fixed by editing an explanation; the stem has to change.

It is not removed, because it is the lesson's only MEDIUM rung and deleting it
would reproduce the D12 failure. It is taught with the defect **on record**, and
`test_L1M_needs_its_two_collapse_traps_redesigned` is `xfail(strict=True)`, so
the defect cannot be forgotten and quietly "fixed" at the symptom. The fourth
item's key and arithmetic are sound; `G5` recomputes it and agrees.

### 7.3 D17 — `Distractor.produces`, so the cross-check is HOUSEKEEPING and not a habit

**Ruled 2026-10-02, at the owner's request: "this should be housekeeping rules
here, because we are generating all XAT topics so don't want regression."**

Correct, and the agent pass cannot do it. An agent audit is a *sample*: it found
five bad options in one lesson of forty subtopics, and it found two of the five.
A rule that depends on someone running the auditor is a habit, and habits expire
at the exact moment 40 topics land.

So the cause of each distractor is now **machine-checkable data**, not prose.

`Distractor` gains `produces`: the arithmetic of the wrong move, as a sympy
expression over the item's own numbers, which must equal the option's value.

`G16_distractor_produces_its_option` refuses when

- `produces` is absent on a QUANT item — **absent means UNPROVEN, and unproven is
  a refusal, not a skip**. A gate that skips what it cannot check reports a pass it
  did not earn; that is the same defect as the coverage floor reading eight files
  out of nine, and it is stated here because it is the tempting version of this
  rule;
- the expression evaluates to something other than the option.

Falsified against the shipped defect:

```
G16  the option 'Rs 10,250' is 10250 but the move its own misconception names,
     10500.0, computes 10500. Either the option or the explanation is wrong,
     and a learner following the lesson cannot reconcile them.
```

**What G16 does NOT buy, and this is the honest boundary.** It proves the move
computes the option. It cannot prove the move is a mistake a learner would make.
`1440*100/18` is arithmetically valid and pedagogically absurd, `G16` passes it,
and no arithmetic check will ever say otherwise.
`test_g16_does_not_claim_to_check_plausibility` asserts that it passes, so a later
session cannot mistake G16 for the whole job. **Arithmetic is a gate; plausibility
stays a `key-auditor` judgement.** That division is the point, and pretending a
gate covers both is how a gate stops being trusted.

**Three fixture defects fell out of adding the rule**, and all three were the same
disease as the one it was built to catch:

1. `quant_item()`'s options contained **210**, which no plausible mistake produces
   from 1,000 at 10% for 2 years. Replaced with **2,000**, which is
   `1000*10*2/10` — the `/100` read as a `/10`.
2. `_distractors()` emitted placeholder texts `"0".."3"` that appeared in **no**
   option list, so every gate test that built a paper carried distractors nobody
   could match to an option. Distractors are now derived from the **final** option
   list.
3. `at_level()` built its distractors **before** the key rotation, which reorders
   the options, orphaning every one of them. `G12` and `G16` caught it on the first
   run after the change.

And `test_gate_result_bookkeeping` had asserted `G12 == 1` — it depended on defect
2. The assertion is now `== 0`, with the reason recorded, because the count check
belongs to a G12 test of its own.

---

## 8. D18 — TEACH THEN ASK, and the gap analysis that asked for it

### D18 — The lesson teaches before it asks

**Ruled 2026-10-02, by the owner.** Of the two options offered, *teach then ask*
was chosen: a short explanation and one worked example **before** the first MCQ,
not after it.

**Why it was not already right, quoted from the file.** The step-by-step renders
only inside `check()`, so the formula first reaches the screen at
`SOLUTIONS["L1-F"]` — **after question 1 is answered**. A learner who does not
know the formula cannot learn it here. The only pre-commit sighting of it is a
`<textarea placeholder>`, grey text that the first keystroke deletes.

**What a beginner needs and what is present:**

| need | state |
|---|---|
| the formula | present, but only *after* answering |
| what each variable **means** | **absent** — nothing says principal is "the money you start with" |
| one worked example | present, and good, but gated behind Q1 |
| **units** (R per year, T in years) | **absent** — so a monthly rate can be dropped in as annual |

`viewer` also caught the trap in fixing this: **the only worked example in the
file is question 1 verbatim** (1,000 at 10% for 2 years → 200). Reusing it hands
over Q1's key before the commit and destroys Q1 as a check. The example must run
on different numbers — e.g. 2,000 at 5% for 3 years → 300 — so it tests
**transfer**.

`viewer` also confirmed what is already good: the commit barrier is real as
rendered, and the per-option "why X is wrong" lines name a concrete move. Only
the *ordering* is wrong.

### 8.1 The gap analysis, from three roles

Ten agents were available. Three were run, because those three decide whether a
"zero to pro" claim is defensible at all; the other seven audit code, gates and
docs, and none of them can change the teaching. Running all ten would have
produced overlapping prose, not a sharper answer.

| # | gap | evidence |
|---|---|---|
| 1 | **The hard rung is EASY relabelled.** `12000 + 12000*10*2/100` masks to `N + N*N*N/N`, **identical** to EASY's. Changing only the flags drops it 7.40 → 2.50 = EASY. **66% of its difficulty is a declared flag.** | `test_each_rung_has_its_own_derivation_shape`, measured **3 of 4** |
| 2 | **No gate compares a level flag to the derivation it describes.** `grep` finds no reference to `insight_required`/`needs_substitution`/`derivation_steps` in `gates.py`. | both reviewers, independently |
| 3 | **`G6` fingerprints the STEM, not the derivation.** So compounding-as-SI is drilled at L1-E *and* L1-H, and every gate passes: `G16` checks each produces its option, `G12` checks the strings differ, nobody notices the same move appears twice. | `question-setter` |
| 4 | **`claimed_level` is `None` on 4 of 4**, so `G7`'s entire automated half is inert. The rung lives in a comment. 160 items with rung labels in comments is an asserted ladder. | `question-setter` |
| 5 | **1 of 40 subtopics written = 2.5%.** 39 lessons remain. | measured |
| 6 | **Trap readiness 1 of 2.** Of this subtopic's two named traps, only the "rate on the amount" trap is used; "time in months used without converting the rate" appears in **0 of 4**. On the 38 untrained subtopics it is 0 of 90. | `question-setter` |
| 7 | **A shape with no clock and no penalty cannot teach attempt strategy.** `minutes=0`, `negative_marking=False`, so the learner never meets 136s per question, guess EV = 0.0000, or the 9th blank at −0.10. That is ~28 questions of pacing calibration per mock. | `question-setter` |
| 8 | **`derive_level` band margins are 0.25 / 0.50 / 0.45 / 2.40.** A ladder, not a histogram — but three of four rungs sit under 0.5 from a boundary. | `level-auditor` |

### 8.2 What the gap analysis demands of Geometry's first lesson

Three structural properties, from `level-auditor`:

1. **Four pairwise-distinct digit-masked derivation shapes.** Lesson 1 scores
   **3 of 4** and passes every gate. Geometry must score **4 of 4**.
2. **One NEW operation per rung, and FOUNDATION must already isolate it.** HARD
   may substitute into the ratio FOUNDATION isolated; it may **not** reach into
   `circle-tangents`, which is a different subtopic.
3. **Every flag provable from the derivation string.** `needs_substitution` and
   `insight_required` must correspond to a sub-expression no lower rung contains.
   Otherwise the score is a label with arithmetic on it.

**The one measurement that would prove a new ladder is real:**
`len({shape(i.derivation) for i in LESSON}) == 4`, zero LLM calls, falsifiable by
the exact false input that exposed lesson 1 — relabel an EASY item HARD and it
drops to 3 of 4 while every level gate still passes.

### 8.3 The next gate, named

**`G17`: a rung's claimed flags must be provable from its derivation.** Not built
yet. It is the gate that would have caught gap #1 and #2, and it is the reason
`test_each_rung_has_its_own_derivation_shape` is `xfail(strict=True)` rather than
a passing test — because until `G17` exists, the check is a fact about one lesson
and not a rule about forty.

---

## 9. D19 — `G17`: a rung must add an OPERATION, not a number

**Ruled 2026-10-02. Owner's steps 1 and 2, collapsed into one gate, because they
are one defect seen from two angles.**

### What it refuses

Two items in the same set whose derivations reduce to the same shape once digits
are masked. `G6` cannot see this: `G6` fingerprints the **stem**.

```
L1-F  1000*10*2/100                 ->  N*N*N/N
L1-E  10000 + 10000*5*2/100         ->  N + N*N*N/N
L1-M  (1440*100/(8*3))/(2160*100/…) ->  (N*N/(N*N)) / (N*N/(N*N))
L1-H  12000 + 12000*10*2/100        ->  N + N*N*N/N      <-- identical to E
```

`level-auditor` falsified it by changing nothing a learner sees: clearing
L1-H's `insight_required`, `needs_substitution` and `derivation_steps` dropped it
from **7.40 to 2.50** — the EASY tier. So **4.90 of 7.40, 66% of the hard item's
difficulty, was a declared flag.** `derive_level` charges
`steps × 0.85 + 1.2 + 2.0 + 0.2 per near-miss`, so **the flags ARE the score**,
and nothing anywhere compared a flag to the derivation it claims to describe.

### Why no other gate caught it

- `G7` compares `claimed_level` to the derived level, and `claimed_level` is
  `None` on **4 of 4** items. Its entire automated half is inert; the rung lives
  in a comment.
- `G6` fingerprints the stem, so compounding-as-simple-interest is drilled at
  L1-E *and* L1-H and every gate passes.
- `G17` is the first gate to look at the **arithmetic**.

### What G17 does NOT prove, pinned by a test

It cannot verify `derivation_steps`, `needs_substitution` or
`insight_required`. Those are claims about how many reasoning moves a human
makes, and "steps" is explicitly *not* operator count — `1000*10*2/100` has three
operators and the FOUNDATION rung correctly claims **one** step.
`test_G17_does_not_claim_to_verify_the_difficulty_flags` asserts that, because a
gate credited with more than it does is worse than no gate.

**Arithmetic is a gate. Plausibility, and whether an item is really at its tier,
stay a `key-auditor` and `level-auditor` judgement.**

### The hard rung, rebuilt — decision (a), rewrite

The rung now performs an operation no lower rung does: **infer the rate from a
stated interest, then re-apply it over a different time.**

> Simple interest on a sum for 3 years is 30% of the sum. At the same rate, what
> is the total amount after 5 years?

`1000 + (300*100/(1000*3))*1000*5/100` → masks to `N + (N*N/(N*N))*N*N*N/N`.
**4 of 4 distinct shapes.** The rate is never given; it has to be recovered.

The trap it creates is the best in the lesson. Interest *is* linear in time, so
the tempting move is to carry the 3-year figure straight over — `Rs 1,300` =
`1000 + 300` — which is right about the property and wrong about its use.

Its `needs_substitution` is now **visible in the string**: the parenthesised group
`300*100/(1000*3)` is computed first and fed into the main formula as a rate. That
is the first rung whose flag is provable by reading it.

### Two ordering and fixture defects found while building it

1. **`G15` cleared `res.admitted`, so `G17` could never run.** An unreachable gate
   is a specification, not a gate. Both paper-level gates now report before the
   list is cleared, and `test_both_paper_level_gates_report_before_the_admitted_
   list_is_cleared` pins it — a paper with two defects must report both, or an
   author fixes one and believes the paper is clean.
2. **Every paper fixture in `test_gates.py` carried the same derivation**
   `1000*10*2/100`, so the "clean 20-item paper" was twenty copies of one piece of
   arithmetic and `G17` refused the whole set, correctly. The fixture now uses
   twenty distinct shapes that all evaluate to 200.

### A bug I introduced and the tests caught

Adding G17 to `GATE_IDS` used a blanket string replace, which also hit the three
`refuse("G16…")` calls inside G16's body and gave every G16 refusal the detail
`"G17_derivation_shape_distinct"`. `test_G16_refuses_an_option_its_own_explanation_
does_not_produce` failed on it immediately. A blanket replace across a file that
contains the string being replaced is the hazard; the test that asserts a refusal's
*detail text* is what caught it.

---

## 10. D18 built — the teaching, before the first question

`viewer` measured what was missing for a learner who does not know the topic:

| need | before | after |
|---|---|---|
| the formula | only *after* answering | **before the first question** |
| what each **symbol means** | **absent entirely** | P, R and T defined in words |
| one worked example | gated behind Q1 | before Q1, on different numbers |
| the **units rule** | **absent** | R per year, T in years, months converted |

The card is built from **`paper.json`**, not `answerkey.json`. It has to be seen
*before* the commit, so putting it behind the commit barrier would mean it never
appears until it is too late — and putting it with the answers would ship the
teaching to anyone reading the network tab. `paper.json` is already fetched on
load, so the card costs **no extra request**.

**Owner decision: once per lesson, not once per subtopic.** It renders on question
1 and not on rungs 2–4. If a learner says it repeats too much, that is a revisit,
not the default.

### The trap, and it is why four of these tests exist

MEASURED: the only worked example in the file was **question 1 verbatim** —
1,000 at 10% for 2 years → 200. Reusing it as the teaching example **hands over
Q1's key before the commit and destroys Q1 as a check**, and every gate passes,
because no gate knows what a beginner has already been told.

So the example runs on **2,000 at 5% for 4 years → 400**: it tests *transfer*
rather than recall. `test_the_teaching_example_does_not_hand_over_question_ones_key`
refuses it if the numbers ever converge, and checks the example's own arithmetic.

### A leak check that had to be made exact

The first browser check looked for the substring `"200"` in the card and **failed
— because `"2000"` contains `"200"`.** A leak check that fires on the worked
example's own numbers is worse than no leak check: an author would "fix" the
teaching to satisfy it. It now looks for Q1's **key text** and Q1's **principal**,
both specific to question 1.

### Two bugs the browser found, and one the pixels found

1. The card was built *before* the final `stage.innerHTML` assignment and therefore
   **wiped a moment later**. The DOM check caught it only after the first slot was
   moved into the final template — two wrong placements in a row, both invisible
   to reading.
2. `#teachSlot` was added to the *loading shell*, which the real template replaces.
3. **Only the screenshot found this:** the card prefixes `Units.` and
   `Worked example.` in bold, and the text then repeated the same words — "Units.
   THE UNITS RULE…", "Worked example. Worked example…". Every DOM assertion passed;
   the duplication was only legible on the rendered card.

**47 UI checks**, nine of them on the teaching, including that it renders *above*
the question, and that it does not leak the key.

---

## 11. D20 — the registry, and the count that was lying

**Ruled 2026-10-02.** Two defects, both found while planning the 20-question
block, both about *what exists* rather than what is correct.

### 11.1 `written: 4` was the ITEM count

```
$ xat-practice weightage          # before
subtopics trained: 40   written: 4
```

Four is the number of **items**. The line sits between two **subtopic** counts on
a project with **40 subtopics**, so it read as "four topics done" when the truth
is **one**. `viewer` measured the real ratio at 2.5%, and `pl_int` is **6.64%** of
the 28-question section the learner can attempt.

A lesson covers exactly one subtopic. So the CLI now prints the two numbers
separately, and the coverage figure with its denominator:

```
subtopics trained: 40   written: 1   items written: 4
coverage:          1/40 subtopics = 2.5%
```

`test_weightage_no_longer_conflates_items_with_subtopics` refuses a bare
`written: N` on a line whose neighbours are subtopic counts. **A count printed
without saying what it counts is a lie that looks like a pass** — and this one
had been printed, and read, for a whole session.

### 11.2 A second lesson was impossible without editing six files

MEASURED: **11 references to `lesson1` across 6 files**, and
`bundle.OUT_DIR` was a hardcoded `out/lesson-01`. So Lesson 2 did not mean adding
a file; it meant editing six of them by hand, and `out/` had exactly one legal
slot.

`registry.py` is now the single answer to "what is written". `Lesson` carries the
id, subtopic, items, solutions and teaching together, because a lesson is a *unit*
— four rungs, the step-by-step and the "before you start" block mean nothing
apart. `bundle.main()` loops; `out_dir()` derives the directory from the lesson id;
`gates` and `levels` report over **every** lesson rather than Lesson 1.

`assert_registry_is_honest()` fails the build if a lesson covers two subtopics, if
an item has no step-by-step, if a step-by-step does not end on its own key, or if
two lessons claim the same subtopic. The last one is why "subtopics written" is a
count and not a sum with a duplicate in it.

### 11.3 A test that passed for the wrong reason

`test_gates_exits_non_zero_and_names_the_refused_item` planted a wrong key by
patching `lesson1.LESSON`. The moment `cmd_gates` began reading the registry, that
patch stopped having any effect — the verb ran against the real lesson, found
nothing wrong, and returned 0 while the test asserted 1.

It now fails loudly. **But it did not fail loudly for the right reason first**: the
planted-defect tests were updated to patch `cli.all_items`, the seam the verb
actually calls, and until that was done one of them was asserting against a stub
nothing read.

Recorded because it is the same shape as the coverage floor that read eight files
out of nine: **a test can be green, be well-named, and be examining nothing.**
