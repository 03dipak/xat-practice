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
| The distractors **teach** | Every distractor carries a distinct named misconception from `syllabus.SUBTOPICS` — 104 named traps. `G12` refuses a blank or duplicated one. |

**The honest limit.** The guarantee is per stratum. `QUANT` keys are *computed*.
`LOGIC` keys are *delegated* to an unbuilt enumerator, so they are labelled
unverified rather than verified. `JUDGEMENT` (VALR, DM) keys would be delegated
to a blind second model call, which is a second **opinion**. A percentile figure
that does not name its strata is overstated.

## Status

Waves 0 and 1 landed, plus **Lesson 2, Geometry: areas and similar shapes**.
**2 of 40 subtopics are written, 8 items, all eight admitted, all keys
recomputed.** Measured on 2026-10-02:

```
uv run pytest -q --strict-markers --cov                     -> 296 passed
uv run coverage report --include="src/xat_practice/*.py" \
    --fail-under=95 --precision=2                        -> TOTAL 95.86%
uv run ruff check src tests tools                        -> All checks passed
uv run mypy src                                          -> no issues, 12 files
uv run xat-practice gates
    population: 4 items = 1 lesson, lesson-01-simple-interest, pl_int:simple-interest
      admitted: 4/4   refused: 0  (rate 0.0 over 4)
    population: 4 items = 1 lesson, lesson-02-geometry-similarity, geo_mens:similarity-and-area-ratios
      admitted: 4/4   refused: 0  (rate 0.0 over 4)
    lessons: 2   items gated: 8   refused: 0 across 8
uv run python tools/ui_probe.py --lesson lesson-02-geometry-similarity
                                                          -> 47/47
```

**`gates` reports PER LESSON, deliberately (D23).** It used to report over the
pooled items, and with two lessons registered that admitted **0 of 8** and
refused two items that are individually perfect: `G11` apportions the 20-item
PAPER mix, and `MIX_ENFORCEMENT_FLOOR` is 8 — a number that meant "smaller than a
paper" and that **two lessons now reach**. A paper rule has to be given a paper,
so neither gate was loosened; each lesson is gated on its own and the pooled
figure is labelled `NOT a score`.

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
optional decoration — the commands below go through `uv run`.

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
uv run xat-practice weightage
```

It must print `population: 196 questions = 28 per paper x 7 papers, 2020-2026`
and exit 0. That command runs `syllabus.self_check()`, which raises unless every
year's topic rows sum to exactly 28 — the table is quotable only because it
closes.

> If `mypy` dies with `timeout: failed to execute process: No such file or
> directory`, the venv is stale, not the package. `rm -rf .venv && uv sync`.
> Every console script in `.venv/bin/` shebangs an absolute interpreter path, so
> a directory rename breaks all of them at once.

### `uv run` for everything

**Use `uv run`.** The previous version of this file said the opposite, on the
ground that `uv run` is not read-only: it resolves and syncs the environment
before running the command, and a gate is a measurement, so the measurement
should not mutate the box it measures.

**That reason no longer holds, and MEASURED 2026-10-02: `uv run` changed 0 files
under `.venv`.** Before and after a `uv run` invocation, the set of installed
`*.dist-info` directories hashes identically and `find .venv -newer <stamp>`
returns nothing:

```
before:           08c1b4f76dd4f381091dd6e084972e7e
after uv run:     08c1b4f76dd4f381091dd6e084972e7e
files .venv touched: 0
```

It is read-only *because* the two things that made it dangerous are both in
place: `uv.lock` is committed, so there is nothing to re-resolve, and every tool
is declared in `[dependency-groups] dev`, so there is nothing to prune. Remove
either and the old warning comes back — which is why it is recorded as a
condition and not as a preference.

There is one real cost, and it is small: `uv run` adds about **0.05s** per
invocation over the direct path (MEASURED, 0.09s vs 0.04s on a bare import).

### The one place the direct path is still right

`python -m pytest` and `pytest` were **not** the same command, and only one of
them worked. MEASURED 2026-10-02: bare `pytest` failed **7 of 299** with
`ModuleNotFoundError: No module named 'tests'`, while `python -m pytest` passed
all 292. Same interpreter, same venv, same code — `-m` puts the CWD on
`sys.path[0]` and the console script does not, and `tests/test_api.py` does
`from tests.test_gates import at_level`.

It went unnoticed because **every** documented command used `python -m pytest`,
so the suite had only ever been run in one of its two legal forms. `pythonpath =
["."]` in `pyproject.toml` now makes both work, which is the point: the fix is not
"remember to type the longer command", it is deleting the dependency on which
form you chose.

## Where we are, and what is next

**`todo.txt` is the continuation file.** If a session ends, the next one reads
`AGENTS.md`, then `todo.txt`, and can carry on from it alone: every item there
states its population, its evidence, and what "done" means.

Written: **2 of 40 QA&DI subtopics (5.0%)**. `docs/COVERAGE.md` is the generated
ledger and `docs/ADOPT_REJECT.md` records what five reviews said and what was done.

## Run it

### Sit a lesson in the browser — one command, then click

```bash
uv run xat-practice serve
```

It starts immediately. **No prompt, no second command.** It prints one URL:

```
XAT Practice is up at  http://127.0.0.1:8000/
  that page lists the sections; pick one there. (ctrl-c to stop)
```

**The navigation is a web page, not a terminal menu.** It was one, and it was
rejected: *"I don't wanna invest the time in running commands."* MEASURED
2026-10-02, this shape went wrong twice —

1. `serve` with no argument opened the **first** registered lesson, so anyone who
   wanted Geometry typed the documented command and got Simple Interest, with
   nothing saying a choice existed. Safe by being invisible.
2. The fix was to **ask in the terminal**. Also rejected.

So the choice lives in the page, and `serve` serves the whole `out/` tree so that
**one URL reaches every lesson**: `/` is the navigator (section → topic), and each
lesson is at `/<lesson_id>/`, where its sibling `fetch('paper.json')` still
resolves. One origin, no CORS, and switching subtopic needs no restart — which is
also why "one lesson per port" stopped being the right shape.

Inside a lesson the four levels are **clickable tabs**. You can take them in any
order, and jumping clears the previous rung's commitment, so the verdict can never
report *"Sure and WRONG"* on a question you did not commit to.

Prefer to skip the navigator: `uv run xat-practice serve --lesson <lesson_id>`.

### Two different things called "a mix"

| what is being produced | mix | why |
|---|---|---|
| a **mock** / full paper | `LEVEL_MIX` 10/25/40/25 → **2/5/8/5** at n=20 | derived from the exam's own timing: 136 s/question across 170 minutes, so the top of the paper is not meant to be 25% hard |
| a **drill** at a level the learner chose | level-filtered — the learner's choice | "I want foundation" is not a request for a mix |

`G11` enforces the paper mix and must not be handed a level-filtered drill: a paper
rule given a non-paper is the defect behind D12 and D23, and it is how a hard rung
once got deleted from Lesson 1. See D26.

**`file://` will not work.** MEASURED 2026-10-02: opening
`out/xat/qa_di/lesson-01-simple-interest/index.html` directly renders **"The question could
not be loaded"**, because `file://` blocks `fetch()` of a sibling JSON. That is the
commit barrier working — but it means `serve` is mandatory.

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
| `xat-practice coverage` | **the ledger**: trained / written / pending, trap capacity — see `docs/COVERAGE.md` |
| `xat-practice agents` | rebuild `opencode.json` from `build_opencode.py` |

`gates` and `levels` report **per lesson**, on purpose — see D23 in `docs/DECISIONS.md`.

### Check the UI in a real browser

```bash
uv run xat-practice build
uv run python tools/ui_probe.py                    # 47 checks, exit 1 on failure
uv run python tools/ui_probe.py --lesson lesson-02-geometry-similarity
uv run python tools/ui_probe.py --shot-dir /tmp/ui # start/options/result PNGs
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
uv run ruff check src tests tools
uv run mypy src
uv run python -c "import xat_practice.cli"
uv run pytest -q --strict-markers --cov
uv run coverage report --include="src/xat_practice/*.py" \
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
  lesson2.py         Lesson 2: Geometry, areas and similar shapes, 4 rungs
  bundle.py          static bundle + paper/key file split
  cli.py             8 verbs
  registry.py       every lesson that EXISTS, in one place
tests/               296 tests, 9 modules
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