# xat-practice

XAT 2026 training from foundation to mock. One subtopic at a time, four rungs
(`FOUNDATION -> EASY -> MEDIUM -> HARD`), then timed mocks.

The design is not "an LLM writes questions". It is that a **wrong answer key
actively teaches a wrong fact and the student cannot detect it** — a wrong key is
a learner who now believes something false and answers the next five questions
consistently with that belief. So:

| claim | how it is kept honest |
|---|---|
| The key is **right** | `solver.py` **recomputes** it in exact rational/sympy arithmetic from the item's own derivation. Agreement is arithmetic; disagreement is a **refusal** (`G5`), never a repair. Zero LLM calls. |
| The level is **right** | `derive_level` computes the tier from structure. Level is never *requested*. Requesting two levels from a model returned the identical stem on 4 of 6 items in measurement. |
| The answer is not **leaked** | The bundle splits into two files. The page loads `paper.json` (stem, options, level) and fetches `answerkey.json` **inside `check()` only**. |
| The distractors **teach** | Every distractor carries a distinct named misconception from `syllabus.SUBTOPICS` — 90 named traps. `G12` refuses a blank or duplicated one. |

**The honest limit.** The guarantee is per stratum. `QUANT` keys are *computed*.
`LOGIC` keys are *delegated* to an unbuilt enumerator, so they are labelled
unverified rather than verified. `JUDGEMENT` (VALR, DM) keys would be delegated
to a blind second model call, which is a second **opinion**. A percentile figure
that does not name its strata is overstated.

## Status

Waves 0 and 1 landed. **1 of 40 subtopics is written** (Simple Interest, four
rungs, all four admitted, all keys recomputed). Measured on 2026-10-02:

```
.venv/bin/python -m pytest -q --strict-markers --cov      -> 161 passed
.venv/bin/python -m coverage report --include="src/xat_practice/*.py" \
    --fail-under=95 --precision=2                        -> TOTAL 95.19%
.venv/bin/ruff check src tests                           -> All checks passed
.venv/bin/mypy src                                       -> no issues, 9 files
.venv/bin/xat-practice gates
    population: 4 items (lesson lesson-01-simple-interest)
    admitted: 4   refused: 0  (rate 0.0 over 4)
```

Not built, and not to be reported as if they were: any mock (28-question quant or
75-question full paper), any timer, any result screen, negative marking in a
running product, `enumeration.py`, the blind second call, attempts 2–40. There is
no percentile claim anywhere in this repository, because nothing has been sat
long enough to earn one.

## Install on WSL

Tested on Ubuntu under WSL2. Commands are bash, run inside WSL, not PowerShell.

### 0. Keep the repo off `/mnt/c`

```bash
mkdir -p ~/agentic && cd ~/agentic
```

Put the project in your **WSL filesystem** (`/home/you/...`), not on the Windows
drive (`/mnt/c/...`). On `/mnt/c` the `9p` filesystem does not honour Linux
permissions, so the `.venv/bin/*` console scripts lose their executable bit and
every command fails with `permission denied` — which reads like a broken install
and is not. If you must keep it on `/mnt/c`, run
`git config --global core.fileMode false` and invoke scripts as
`.venv/bin/python -m xat_practice.cli` instead.

### 1. System packages

```bash
sudo apt update && sudo apt install -y git curl build-essential
```

`build-essential` is only needed if a wheel has to be compiled. sympy, pydantic
and requests all ship wheels for CPython 3.12 on x86-64, so it is usually a
no-op — it is listed because a missing compiler produces a build error that reads
like a dependency problem and is not.

### 2. Install `uv`

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source "$HOME/.local/bin/env"      # or: exec $SHELL
uv --version
```

`uv` manages the virtualenv, the interpreter and the installs. It is not
optional decoration — the commands below assume `.venv/bin/xat-practice` exists.

### 3. Clone and install

```bash
git clone git@github.com:03dipak/xat-practice.git     # SSH
cd xat-practice

uv python install 3.12
uv venv --python 3.12
uv pip install -e . mypy pytest pytest-cov ruff
```

Verify:

```bash
.venv/bin/xat-practice weightage
```

It must print `population: 196 questions = 28 per paper x 7 papers, 2020-2026`
and exit 0. That command runs `syllabus.self_check()`, which raises unless every
year's topic rows sum to exactly 28 — the table is quotable only because it
closes.

> If `mypy` dies with `timeout: failed to execute process: No such file or
> directory`, the venv is stale, not the package. `rm -rf .venv && uv venv
> --python 3.12 && uv pip install -e . mypy pytest pytest-cov ruff`. Every
> console script in `.venv/bin/` shebangs an absolute interpreter path.

## Run it

### Sit a lesson in the browser

```bash
.venv/bin/xat-practice build     # writes out/lesson-01/
.venv/bin/xat-practice serve     # http://127.0.0.1:8000/
```

`serve` binds **loopback only** and serves one directory. It exists for one
reason: browsers block `fetch()` of a sibling JSON on `file://`, so opening
`out/lesson-01/index.html` directly cannot load `paper.json`. Ctrl-C to stop.

Currently served: **Lesson 1, Simple Interest, 4 questions.** There is no
Geometry lesson yet.

### The verbs

| command | what it does |
|---|---|
| `xat-practice build` | build the static bundle; refuses if any item fails a gate |
| `xat-practice serve` | serve the bundle at `http://127.0.0.1:8000/` |
| `xat-practice gates` | run the gate suite; per-gate refusal counts over a named population |
| `xat-practice levels` | each item's **derived** level with its drivers |
| `xat-practice weightage` | the topic weight model + `self_check()` |
| `xat-practice ev` | the three marking numbers the pedagogy rests on |
| `xat-practice shapes` | paper shapes, level quotas, level recipes |
| `xat-practice agents` | rebuild `opencode.json` from `build_opencode.py` |

`gates` and `levels` currently report on Lesson 1 only.

### The four gate commands

All four, not three:

```bash
.venv/bin/ruff check src tests
.venv/bin/mypy src
.venv/bin/python -m pytest -q --strict-markers --cov
.venv/bin/python -m coverage report --include="src/xat_practice/*.py" \
    --fail-under=95 --precision=2
```

The fourth is a **separate command**, not a coverage `include`: one `include`
cannot both scope the floor to our own package and leave the whole tree visible in
the printed table. Scoping the printed table hides the population you most want
to watch, silently.

`--cov` lives in `addopts` in `pyproject.toml`. Removing it to speed the suite up
means `pytest -q` writes **no** coverage data and the fourth command then reports
whatever `.coverage` is on disk — possibly hours stale — as a fresh measurement. A
floor reading stale data is worse than no floor, because it looks like a
measurement.

## Layout

```
docs/DECISIONS.md    the one ledger: D1-D14, every ruling with its reason
docs/PEDAGOGY.md     what a good question is, as countable rules
AGENTS.md            how to work here; the four load-bearing differences
src/xat_practice/
  syllabus.py        weight model, 196 questions, self_check() closes to 28/yr
  solver.py          RE-DERIVES the key by computation
  items.py           schema, derived difficulty, LEVEL_RECIPES
  gates.py           14 gates; GATE_IDS is normative
  lesson1.py         Lesson 1: Simple Interest, 4 rungs
  bundle.py          static bundle + paper/key file split
  cli.py             8 verbs
tests/               161 tests
```

## The exam this trains for

Measured from XLRI's own 2026 notification. Most material online describes the
pre-2025 pattern and is wrong.

- **95 questions, 180 minutes.** Part 1 = **170 min**: QA&DI **28** + VA&LR
  **26** + DM **21** = 75, with **no sectional time limit**. Part 2 = GK 20 in
  10 min, **excluded from the percentile**, no negative marking.
- **5 options.** +1 correct, **−0.25** incorrect, **−0.10 per unattempted after
  the first eight**. On-screen calculator in QA&DI. Essay moved to GD/PI.
- **Guessing EV is exactly 0.0 at 5 options**: `+1/5 + 4/5×(−0.25) = 0.20 −
  0.20`. At 4 options it is **+0.0625**, i.e. a 4-option negatively-marked paper
  *pays* you to guess.
- **The 9th blank is the trap.** EV of the 9th blank is **−0.10**, strictly worse
  than guessing. Past eight blanks, guessing dominates leaving it blank — the
  reverse of the usual "skip if unsure" advice.

## Working rules

Read `AGENTS.md` and `docs/DECISIONS.md` §1 before changing anything. The short
version:

1. Never assert a key. Recompute it. Disagreement refuses the item.
2. Never request a level. Derive it, and refuse a drafter whose claim disagrees.
3. Never report a number without its population and its limitations.
4. Never repair a gate's finding — after a repair the gate has rejected nothing.
5. Run it. A defect visible only by running has been found before, four times.