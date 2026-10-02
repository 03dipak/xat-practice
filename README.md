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
.venv/bin/python -m pytest -q --strict-markers --cov      -> 248 passed
.venv/bin/python -m coverage report --include="src/xat_practice/*.py" \
    --fail-under=95 --precision=2                        -> TOTAL 96.64%
.venv/bin/ruff check src tests                           -> All checks passed
.venv/bin/mypy src                                       -> no issues, 9 files
.venv/bin/xat-practice gates
    population: 4 items (lesson lesson-01-simple-interest)
    admitted: 4   refused: 0  (rate 0.0 over 4)
```

**That 96.64% is the second number this file has ever quoted for coverage, and
the first was wrong.** It read `95.19%` and passed, because `cli.py` was absent
from the report: 115 statements, 16% of the package, excluded because **no test
had ever imported it**. Coverage only measures a module something executed, so a
file nothing imports is invisible and an invisible file cannot drag a floor
down. The package's real number was **86.13%**. The fix was 24 tests, not a
rounder number — see `tests/test_cli.py`, which exists mostly so this cannot
happen silently again.

Not built, and not to be reported as if they were: any mock (28-question quant or
75-question full paper), any timer, no marking screen, negative marking in a
running product, `enumeration.py`, the blind second call, attempts 2–40. There is
no percentile claim anywhere in this repository, because nothing has been sat
long enough to earn one.

**The page has now been rendered, not just read.** Until 2026-10-02 the lesson had
never executed in a browser: `lesson.js` contained a syntax error, so the browser
ran none of it and showed only the static HTML, and 161 tests passed throughout
because every one of them asserted on the file's *text*. It is fixed, and both
`node --check` and a real headless-browser render are now part of the suite. See
`docs/DECISIONS.md` §6.0 — the most important entry in that section.

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
uv sync
```

`uv sync` is the whole install. It reads `uv.lock`, so you get the exact versions
the coverage figure in this file was measured on — `uv pip install -e . mypy
pytest pytest-cov ruff` installs *unpinned* latest, so a fresh clone could get a
different sympy and a different coverage number from the same code.

> **`uv sync` PRUNES.** Anything in `.venv` that is not declared in
> `pyproject.toml` is **removed**. MEASURED: before the dev group was declared,
> `uv sync` deleted `mypy`, `pytest`, `pytest-cov` and `ruff` — the four tools
> the gate commands run with — and the next import raised
> `ModuleNotFoundError`. The tools now live in `[dependency-groups] dev`, so
> `uv sync` is correct. If you add a tool, add it there too, or the next
> `uv sync` will eat it.

Verify:

```bash
.venv/bin/xat-practice weightage
```

It must print `population: 196 questions = 28 per paper x 7 papers, 2020-2026`
and exit 0. That command runs `syllabus.self_check()`, which raises unless every
year's topic rows sum to exactly 28 — the table is quotable only because it
closes.

> If `mypy` dies with `timeout: failed to execute process: No such file or
> directory`, the venv is stale, not the package. `rm -rf .venv && uv sync`.
> Every console script in `.venv/bin/` shebangs an absolute interpreter path, so
> a directory rename breaks all of them at once.

### `uv run` vs `.venv/bin/...` — which to use when

Both work. `uv run mypy src` takes **1.58s** against **0.36s** for
`.venv/bin/mypy src` (MEASURED), and that is fine for day-to-day use.

The gate commands use the direct path anyway, for one reason: **`uv run` is not
read-only.** It resolves and syncs the environment *before* running the command,
so it can create `uv.lock` and change what is installed as a side effect of
asking for a type check. A gate is a *measurement*, and the measurement should
not mutate the box it measures.

| | use |
|---|---|
| `.venv/bin/mypy src` | the four gate commands, and any number you intend to quote |
| `uv run mypy src` | scratch work, when you do not care what it syncs |

Once `uv.lock` is committed the difference is much smaller, because `uv run` has
nothing to re-resolve. The separation is kept anyway, because it is the
difference between reading a measurement and making one.

## Run it

### Sit a lesson in the browser

```bash
.venv/bin/xat-practice build     # writes out/lesson-01/
.venv/bin/xat-practice serve     # http://127.0.0.1:8000/
```

`serve` binds **loopback only** and serves one directory. It exists for one
reason: browsers block `fetch()` of a sibling JSON on `file://`, so opening
`out/lesson-01/index.html` directly cannot load `paper.json`. Ctrl-C to stop.

It is **threaded**, and that is not an optimisation. It used to be a
single-connection `TCPServer`, which parked its only thread forever the first
time a browser held a connection open — a favicon probe, a preconnect — and then
served nothing at all, with no error and no exit. The symptom was a lesson page
that "takes too much time to load"; the cause was the server, not the page. See
`cli.make_server` and
`test_one_held_connection_does_not_block_the_next_request`.

If the page ever shows **"The question could not be loaded"** instead of a
question, that is the fetch failing, and the card will tell you why — including
the case where `index.html` was opened directly rather than served.

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

### Check the UI in a real browser

```bash
.venv/bin/xat-practice build
.venv/bin/python tools/ui_probe.py                    # 38 checks, exit 1 on failure
.venv/bin/python tools/ui_probe.py --shot-dir /tmp/ui # start/options/result PNGs
```

The PNGs are the **real** `index.html` with the **real** stylesheet, driven by
clicking — not the probe page. That is deliberate: with the CSS inline, the probe
could not load it, was blind to every appearance defect, and its own contrast
check passed against a build where all five options were white on white.

This serves the built bundle through the real threaded server, drives it in a
headless Chromium, and asserts on the DOM the browser actually built — 34 checks,
including:

| check | what it holds |
|---|---|
| `page-renders` | the stage is not empty, i.e. the script executed at all |
| `no-option-exists-in-the-dom-before-the-reveal` | the commit barrier, as **rendered** — hidden is not absent |
| `reveal-is-born-disabled` | the button's born state, not a line that enables it |
| `answerkey-not-fetched-before-check` | the key is unreachable before the learner commits |
| `the-browser-verdict-matches-the-recomputed-key` | the screen agrees with the key `Solver.verify` computed |
| `the-solution-ends-on-the-stated-answer` | the step-by-step ends on the key |
| `every-option-is-legible-contrast-at-least-4-5-1` | **readable**, not merely present — this caught the options rendering white on white |
| `the-page-states-which-build-it-is` | the build id, so a stale script is self-evident |
| `lesson-js-leaks-no-globals` | twelve internals stay off `window` |

Exit **2** means no browser was found and therefore nothing was proven — never
0. A check that cannot run must not be reported as a pass. The same discipline as
the coverage floor that read eight files out of nine.

It is also part of the suite (`tests/test_render.py`), and the `ui-inspector`
agent owns it.

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
  gates.py           17 gates; GATE_IDS is normative
  lesson1.py         Lesson 1: Simple Interest, 4 rungs
  bundle.py          static bundle + paper/key file split
  cli.py             8 verbs
  registry.py       every lesson that EXISTS, in one place
tests/               248 tests, 8 modules
tools/
  ui_probe.html       the probe page a browser actually runs
  ui_probe.py         serves the bundle, drives Chromium, reports

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