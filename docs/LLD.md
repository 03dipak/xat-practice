# LLD — the exam layer

**Status:** Phase A in progress. **Revised 2026-10-02 after five reviews** —
see [`ADOPT_REJECT.md`](ADOPT_REJECT.md) for every verdict and its evidence.
**Scope of this document:** the one layer *above* section — **Exam → Section → Topic**.
**Content scope:** XAT only. Other exams are a *shape*, never content, until XAT is done.

Read `AGENTS.md` and `docs/DECISIONS.md` first. Every number below is re-derivable
and the command is given.

---

## 1. Session context — what constrains this design

This is the context that is easy to lose, and every rule below traces to a
measurement in it.

| # | Ruling / measurement | Effect on this design |
|---|---|---|
| D1 | A quantitative key is **re-derived by exact arithmetic**, never model-asserted | `SectionShape` must carry the marking, because the EV and the gates read it |
| D2 | A `JUDGEMENT` key is a **second opinion**, reported as `DELEGATED`, never `HOLD` | VALR/DM cannot be "completed" on the same evidence as QA&DI |
| D3 | **5 options, −0.25 wrong, −0.10 per blank after the 8th** | These are per-section facts, not per-project facts |
| D7 | Section mocks and the full paper; and the syllabus deliberately omits calculus/trigonometry | The exam layer has exactly one *built* section today — a scope fact from the syllabus module, **not** from D7 (an earlier draft of this table miscited D7 for it) |
| D12 | A paper rule handed a non-paper deleted a hard rung | `G11` must never see a level-filtered drill |
| D14 | Order is **lesson → mock → full paper**; the owner chose Geometry first | Geometry Lesson 2 is done. **DI next is my recommendation, still the owner's call** (§7) |
| D18 | **Teach then ask**, once per lesson | Unchanged by this work |
| D20 | The **registry is the source of truth** | `Lesson` derives, never duplicates |
| D23 | **Gate per lesson** — a pool of lessons is not a paper | Sections are gated per section, not pooled |
| D26 | **The level is the learner's; the mix is only for a paper** | `LEVEL_MIX` belongs to a section shape, not to the syllabus |
| — | `serve` prompting and `serve` defaulting were both **rejected** by the owner | The exam chooser must not add a click while there is one exam |
| — | Measured: `build` alone gives no URL; `file://` shows *"The question could not be loaded"* | One server, `out/` as root, relative fetches |
| — | An ad-hoc check (2026-10-02) aggregated our 17 topics into the external 7 areas and summed to **exactly 28.00** | **Not yet re-derivable from this repo** — see §9 |

**Hard boundary.** "Complete all of XAT" is three bodies of work, not one:

| part | counted | subtopics defined | written | machinery |
|---|---|---|---|---|
| QA&DI | 28 | **40** | **2 (5.0%)** | built and measured |
| VA&LR | 26 | **0** | 0 | not built |
| DM | 21 | **0** | 0 | not built |

Measured: all 40 subtopics are `QUANT` (37) or `LOGIC` (3). **Zero are
`JUDGEMENT`** — structurally, because a prose key has no solver. So QA&DI contributes **28 of the 75 Part 1 raw-score questions — 37.33% by question
count**. That is **not** "37% of the percentile": percentile depends on cohort
performance, scaled scoring and sectional cutoffs, none of which this project
measures. Any percentile figure this product prints is `UNMEASURED` until there is
edition-labelled cohort data, and raw score is always reported separately.

QA&DI is the tractable half. Phase D completes it; Phase E is **split**, not
parked wholesale — see §10.

---

## 2. Why exam is a data dimension, not a code fork

The gates, the solver, level derivation, the item schema and the browser bundle
are **exam-agnostic**. `Stratum` is already `{quant, logic, judgement}` and
`expected_ev()` is already parameterised. What differs between exams is
*shape*: section counts, marking, options, time limits, strata.

So the exam becomes a **key**, and nothing forks.

Rejected: a `xat/` package. It would duplicate the gates, and the first bug a
fork produces is a fix applied to one exam and not the other — which is the
"two rules that disagree" defect this project already records twice.

---

## 3. Data model

### 3.1 `syllabus.py`

```python
@dataclass(frozen=True, slots=True)
class SectionSpec:
    section_id: str            # "qa_di"
    exam_id: str               # "xat"
    name: str                  # "QA&DI"
    questions: int             # 28
    minutes: int               # 170   (0 = no sectional limit)
    stratum: Stratum           # QUANT for every section built so far
    options: int = 5           # CAT differs per section
    mark_correct: float = 1.0
    mark_wrong: float = -0.25
    blank_penalty: float = -0.10
    blank_penalty_after: int = 8
    in_percentile: bool = True
    calculator: bool = True

@dataclass(frozen=True, slots=True)
class ExamSpec:
    exam_id: str               # "xat"
    name: str                  # "XAT"
    edition: str               # "2026"
    total_questions: int       # 95
    counted_questions: int     # 75  -- the denominator for every percentile claim
    sections: tuple[str, ...]  # ("qa_di", "va_lr", "dm", "gk")
    excluded: tuple[str, ...]  # ("gk",) -- excluded from the percentile by XLRI
```

`EXAMS: dict[str, ExamSpec]` holds **one** entry today. `Topic` gains
`exam_id` and `section_id`; all 17 become `("xat", "qa_di")`.

**`subtopic_id` stays `topic:subtopic`.** It is *within-exam*; the exam is
namespaced in the URL and in `EXAMS`. This keeps existing `lesson_id`s and test
fixtures stable, and two exams cannot collide because the exam is in the path.

### 3.2 Naming collision removed

| now | after | why |
|---|---|---|
| `syllabus.PAPER_SHAPE` (TypedDict) | `syllabus.EXAMS` (dict of `ExamSpec`) | one exam ≠ one paper |
| `items.PaperShape` (dataclass) | `items.SectionShape` | marking/options/stratum are **per section** |

Two names for two different types, one of them the same word, is a trap that has
already cost this project time.

### 3.3 Where marking must live, and why it matters now

Marking, options, stratum and time **descend to `SectionSpec`**, because:

- **XAT 2026:** one marking scheme (−0.25) across Part 1, and GK excluded.
- **CAT:** reported to differ *per section* (`+3/−1` in QA and LRDI, no negative
  marking in VA and DI), plus a **type-in** Written Ability section and **sectional
  time limits**.

`mark_wrong` is not a constant of the universe:

| marking | guess EV at 5 options | advice |
|---|---|---|
| `+1 / −0.25` (XAT 2026, measured) | **+0.0000** | free — guess past 8 blanks |
| `+3 / −1` (CAT, **to verify**) | **−0.2000** | never guess; skip |

**The lesson, stated precisely (R5).** EV = 0 is measured against a *skip worth
0.0*, so it does not mean "guessing is good":

- **below eight blanks**, skipping is free, so a pure guess is merely **neutral** —
  guess only after eliminating options;
- **past eight blanks**, a skip costs −0.10, so guessing is **+0.10 better** — always
  answer.

**Correction, 2026-10-02.** The first draft of this table said **−0.6000**. That was
wrong: it came from `1/options + (options−1)/options × mark_wrong`, which hardcodes
+1 for a correct answer and so drops `mark_correct` entirely. The truth is
`3/5 + 4/5 × −1 = −0.2000`. It was right for XAT only because XAT's `mark_correct`
happens to be 1. Both agents reviewing this LLD caught it independently, and the
bug reached `syllabus.SectionSpec.guess_ev` as a *second implementation* of the
`items.expected_ev` that already existed. That property now delegates to it, and
`test_the_guess_ev_is_computed_not_hardcoded` pins it.

Re-derive with:
`uv run python -c "from xat_practice.items import expected_ev; print(expected_ev(options=5, mark_correct=3, mark_wrong=-1))"`

So the EV lesson is per-section data, and `build_opencode.py` must stop
hardcoding XAT's three numbers in its ~5 places.

---

## 4. File-by-file changes

### Phase A — the layer (zero behaviour change)

| file | change |
|---|---|
| `syllabus.py` | add `SectionSpec`, `ExamSpec`, `EXAMS`; `Topic.exam_id`/`section_id`; `PAPER_SHAPE` → `EXAMS`; keep a `XAT` convenience alias only if a consumer needs it |
| `registry.py` | `Lesson.exam_id` / `Lesson.section_id` as **derived properties** from `subtopic_id`, never stored (D20) |
| `items.py` | `PaperShape` → `SectionShape` |
| `coverage.py` | ledger gains exam/section columns; totals still XAT-only |
| `menu.py` | read `EXAMS`; section list from `ExamSpec.sections` |

**Consumers of the old constant** — MEASURED, and the first estimate was wrong:
**2 src modules** (`menu.py` 12 references, `coverage.py` 3), **2 test modules**
(`test_menu.py`, `test_api.py`), and `AGENTS.md` + `docs/DECISIONS.md`, which both
stated as current that the navigator "reads every paper figure from
`syllabus.PAPER_SHAPE`".

**And the lesson, because I got this wrong in the act:** deleting the constant and
updating `syllabus.py` alone left `menu.py` importing a name that no longer
existed. `uv run ruff check src` **passed** — ruff cannot see a name deleted from
another module — while `import xat_practice.cli` raised `ImportError` and four test
modules failed to collect. A green linter is not a green build.

### Phase B — marking on the section

- `G10_stratum_shape` and `G11_mix_within_tolerance` take a `SectionShape`.
- `expected_ev` / the `ev` verb read the section's numbers.
- `build_opencode.py` reads marking from `EXAMS` instead of restating it.
- `LESSON_SHAPE` stays a **lesson** shape — a lesson is not a section, and D12
  already recorded what happens when a paper rule is handed a lesson.

### Phase C — navigation

```
/                          exam chooser  ONLY when len(EXAMS) > 1
/xat/                      sections: QA&DI built; VA&LR, DM, GK listed + marked
/xat/qa-di/                topics, ordered by measured weight (DI 6.71 leads)
/xat/qa-di/<lesson_id>/    lesson, four level tabs
```

**Progressive disclosure, and the reason:** the owner rejected the terminal menu
(*"I don't wanna invest the time in running commands"*) and rejected `serve`
defaulting to the first lesson because it *hid* the choice. With one exam a
chooser is a click that buys nothing; with two it is required. So the chooser is
driven by `len(EXAMS)`, not hardcoded either way.

One server, `out/` as root: `out/xat/index.html`, `out/xat/qa-di/<lesson_id>/`,
so the sibling `fetch('paper.json')` resolves and switching needs no restart.

### Phase D — complete QA&DI

1. **Unblock `block capacity 0 of 40`.** Fold authored misconceptions into
   `Subtopic.traps`. Until a subtopic has ≥10 named traps no 20-item block can
   exist, and the ledger says so honestly.
2. **Data Interpretation next** — 6.71 q/yr, 24% of the section, zero lessons.
3. **20-item level-filtered blocks** (D26: the learner picks the level; `G11` is
   never handed the drill).
4. **`MOCK-QA` 28 → `MOCK-FULL` 75.**

### Phase E — parked: VA&LR and DM

Requires, in order: a subtopic syllabus with traps; `enumeration.py`; the blind
second call (D2); prose teaching blocks with no formula. And the honest limit:
a `JUDGEMENT` key can only be `DELEGATED`, so **a full-paper percentile claim must
report its strata separately**.

---

## 5. Invariants the code must enforce

New, enforced at build time (`registry.assert_registry_is_honest`):

1. every `Topic.exam_id` is a key in `EXAMS`
2. every `Topic.section_id` belongs to that exam
3. every `Subtopic.topic_id` names a declared topic
4. every `Lesson`'s subtopic is under a section that exists
5. every exam **closes, stated as arithmetic** — "closes" alone is ambiguous:
   `Σ questions` over all sections = `total_questions` (75 + 20 = 95), and over
   counted sections = `counted_questions` (75)
6. every `PARTS` entry's sections sum to its `questions`
7. no `SectionSpec` may carry `minutes`, `blank_penalty`, `blank_penalty_after` or a
   single `stratum` — all four are PART-level facts or distributions, and each was
   wrong there at least once
Existing and unchanged: one subtopic per lesson; one rung per level (D24);
`GATE_IDS` order is normative.

---

## 6. Forward-compatibility contract

**Must never need a breaking change** when CAT/SNAP/NMAT/IBSAT/NMAT/MH-CET arrive:

- the `exam_id` / `section_id` fields and their ids
- where marking lives (`SectionShape`)
- the URL shape `/<exam>/<section>/<lesson>/`
- `expected_ev` (already parameterised)
- gate signatures (take a `SectionShape`, not a literal)

**May change freely:** nav depth, ledger grouping, which sections are built,
the area grouping display.

**Explicitly not designed for yet** (do not pre-build): CAT's type-in section,
multi-exam percentile maths across exams, or a shared item pool. Each needs its
own decision when the second exam is real.

---

## 7. Decisions taken by default, and reversible

The owner had not answered these when Phase A began, so the defaults are stated
here rather than buried in a commit:

| decision | default taken | reverse? |
|---|---|---|
| `pct` weight | **stays 0.0 = UNMEASURED**, inside `avg_ratio` | yes — a data change, no code |
| display the external 7 areas | **no** — our 17 topics only | yes — a display layer |
| next lesson | **DI** (biggest block) | yes — content only |
| "complete XAT" means | **complete QA&DI**; VALR/DM split, see §10 | yes — Phase E is a phase |
| next lesson after Geometry | **Percentages / Ratio / Averages, NOT DI** — DI has no written prerequisites | yes — content order only |
| the blank penalty | **Part-level**; 8 free blanks across all of Part 1 | no — this is a correctness fix |
| a section's stratum | a **distribution**, never one value | no — QA&DI is 37 QUANT + 3 LOGIC |

Recording the default *is* the point: a silent default is how a decision gets
mistaken for a fact.

---

## 8. Verification plan

Each phase ships independently and is gated by the existing four commands:

```
uv run ruff check src tests tools
uv run mypy src
uv run pytest -q --strict-markers --cov
uv run coverage report --include="src/xat_practice/*.py" --fail-under=95 --precision=2
```

Plus, because this touches the browser:

```
uv run xat-practice build
uv run python tools/ui_probe.py --lesson <lesson_id>     # per lesson, never one
node --check out/xat/qa-di/<lesson_id>/lesson.js
```

**Falsifying inputs are required before a phase is called done.** For Phase C,
that means: with `EXAMS` holding two entries, the chooser appears and both exams
are reachable; with one, it does not. For Phase A, that means: a topic naming an
unknown exam must **refuse the build**, not render.

---

## 9. Open: one number in this document is not yet re-derivable

§1 records that our 17 topics, aggregated into the external 7 areas, sum to
**exactly 28.00** = the QA&DI section length. That was an ad-hoc shell calculation
on 2026-10-02. It is not a command in this repo, not a test, and not a function.

It matters because it is currently the strongest evidence that the external
coaching groupings agree with our per-paper counts — and §5 proposes it as an
**invariant the code must enforce**. Promoting an ad-hoc calculation into a gate is
exactly how MEASURED silently becomes ASSUMPTION.

Two honest options, and this is a decision, not a chore:

1. **Promote it.** Add `syllabus.AREAS: dict[str, tuple[str, ...]]` mapping each of
   the 7 external areas to our topic ids, and have `self_check()` assert the areas
   close to `QUESTIONS_PER_PAPER`. Then it is re-derivable and the invariant is
   real. Cost: the grouping enters the code as data, so it starts drifting, and it
   is a **secondary source** (`measured-from-secondary-source`, D13).
2. **Demote it.** Keep it as prose marked *ad-hoc, not re-derivable*, drop it from
   §5's invariant list, and add the display layer only if the owner asks for the
   external grouping.

**Default taken: option 2** — because D13 says second-hand weightages are recorded
and never merged, and a gate is the opposite of recording. The owner was asked
whether to display the 7 areas at all and had not answered when Phase A began.

---

## 10. Two revisions the reviews forced

### 10.1 Phase E is split, not parked (R5)

"VA&LR and DM are parked" hid a tractable share. Part of both is verifiable **by
construction**, which is what `Stratum.LOGIC` means and what the solver is for:

| VA&LR / DM content | key is | stratum |
|---|---|---|
| para-jumbles | the source paragraph's order — checkable | LOGIC |
| arrangement / constraint sets | brute-force enumerable | LOGIC |
| syllogisms, conditional logic | derivable | LOGIC |
| RC inference, ethical caselets | a second opinion | **JUDGEMENT** → `DELEGATED` |

So Phase E becomes **E1** (the LOGIC half — real, computable keys, and it is already
3 subtopics wide in the syllabus) and **E2** (the JUDGEMENT half, which stays parked
and can never claim a recomputed key). Only E2 is genuinely blocked on
`enumeration.py` and the blind second call (D2).

### 10.2 The next lesson is not DI — this reversed my own recommendation (R5)

DI is built on percentages, ratio, averages and growth. Measured: **`avg_ratio` has
0 of 3 subtopics written**, and **`pct` is 0.0 — UNMEASURED**, sitting inside
`avg_ratio`. Writing DI first teaches calculation shortcuts to a learner without the
foundations, which is precisely what the foundation→hard ladder exists to prevent.

So: **Percentages / Ratio / Averages before Data Interpretation**, and a
**prerequisite graph** on subtopics so "next" means *the highest-weight node whose
prerequisites are satisfied* rather than *the biggest block*. DI remains the biggest
block (6.71 q/yr) — it is simply not reachable yet.

### 10.3 Recorded gaps that block later phases, not this one

| gap | blocks | why it matters |
|---|---|---|
| `Item.Set` for shared stimuli | **any DI content** | DI/caselet arrive as 3–5 items over one stimulus; `G11` and the one-rung-per-level check both assume one item, one key |
| `Distractor.trap_id` | trap analytics, learner logs | `Subtopic.traps` and `distractor.misconception` are parallel lists with nothing linking them |
| learner response logging | real difficulty calibration | the level bands are an assumption until real timings exist |
| marking reaching the browser from `paper.json` | full-mock scoring in the UI | a second copy in JS is the two-rules-that-disagree defect |
| `Item.options` override + `effective_options()` | CAT's non-MCQ items | premature with one exam |
| raw-score → percentile evidence layer | any percentile claim | until then every figure is `UNMEASURED` |

---

## 11. What the five reviews did not change

Recorded so the boundary is explicit: exam-as-data, no code fork, registry-first,
learner level vs paper mix, `DELEGATED` for judgement keys, progressive navigation
driven by `len(EXAMS) > 1`, and phase ordering. All five reviews — two internal
agents and three outside — reached the same architecture/content split
independently, and both outside reviews rated the **exam model** as the weak half.

That was accurate, and §1 fixed it.
