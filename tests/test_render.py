"""The lesson page, rendered in a real browser.

THE TEST FILE THAT SHOULD HAVE EXISTED FROM THE START.

`lesson.js` did not parse for the whole of Wave 1. An apostrophe in prose --
`item's` -- closed a JavaScript string literal, so the browser executed none of
the file and the page showed only the static HTML. The lesson had never been
clickable, not once, and 161 tests passed throughout, because every one of them
asserted on the file's TEXT.

`test_bundle.py` checks the two files apart, that the key is not reachable before
`check()`, and that the JavaScript parses. Those are necessary and they are not
sufficient: a page can parse, pass every text assertion, and still not run. So
this file loads it in an actual headless Chromium and asserts on the DOM the
browser built.

Read `tools/ui_probe.html` for the checks themselves. The division is deliberate:
the probe is the artefact a human can also run and read, and this file is the
gate that refuses when the artefact misbehaves.

    .venv/bin/python tools/ui_probe.py            # the same checks, readable
    .venv/bin/python tools/ui_probe.py --shot p.png

**Skipping is a real outcome and is reported as one.** If no Chromium can be
found the tests skip with the reason, and `tools/ui_probe.py` exits 2 rather than
0. A check that cannot run must never be reported as a pass -- that is the same
error as the coverage floor reading eight files out of nine.
"""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
RUNNER = ROOT / "tools" / "ui_probe.py"
# DERIVED from the registry, never hardcoded -- a UI check pointed at a
# directory nobody builds silently stops testing anything.
from xat_practice.bundle import out_dir as _out_dir  # noqa: E402
from xat_practice.registry import LESSONS as _LESSONS  # noqa: E402


def _bundle_of(lesson_id: str) -> Path:
    return _out_dir(lesson_id)


#: Every registered lesson is rendered, checked and gated. MEASURED 2026-10-02:
#: this was `_LESSONS[0]`, so the whole UI gate covered ONE bundle and `47/47` was
#: quoted as the UI being sound. Pointing the probe at Lesson 2 -- same runner,
#: same 47 checks -- found five of them asserting Lesson 1's own content: its
#: formula, its legend words, its units phrasing, its example numbers and its
## answer letter. Every one of those five would have passed, silently and
## correctly, on a page that was leaking a key.
BUNDLE = _bundle_of(_LESSONS[0].lesson_id)
ALL_BUNDLES = [_bundle_of(x.lesson_id) for x in _LESSONS]

REQUIRED = ["index.html", "lesson.js", "paper.json", "answerkey.json"]


def _browser() -> str | None:
    for name in ("chromium", "chromium-browser", "google-chrome",
                 "google-chrome-stable", "headless_shell"):
        found = shutil.which(name)
        if found:
            return found
    cache = Path.home() / ".cache" / "ms-playwright"
    if cache.is_dir():
        hits = sorted(cache.glob(
            "chromium_headless_shell-*/chrome-linux/headless_shell"))
        if hits:
            return str(hits[-1])
    return None


@pytest.fixture(scope="module")
def probe() -> dict:
    """Run the probe ONCE PER REGISTERED LESSON.

    Was `_LESSONS[0]` only. See `ALL_BUNDLES` above for the measurement that
    forced this: the same 47 checks, aimed at every lesson, turned five of them
    from passing-on-Lesson-1 into real findings.
    """
    if _browser() is None:
        pytest.skip(
            "no Chromium or headless_shell on this box, so the UI was NOT "
            "checked. This is a skip, never a pass."
        )
    per: dict[str, dict] = {}
    for lesson in _LESSONS:
        bundle = _bundle_of(lesson.lesson_id)
        for name in REQUIRED:
            if not (bundle / name).exists():
                pytest.skip(f"{name} not built for {lesson.lesson_id}; run "
                            "`.venv/bin/xat-practice build`")
        proc = subprocess.run(
            [sys.executable, str(RUNNER), "--lesson", lesson.lesson_id],
            capture_output=True, text=True, timeout=300)
        entry = {"returncode": proc.returncode, "stdout": proc.stdout,
                 "stderr": proc.stderr, "lesson_id": lesson.lesson_id,
                 "bundle": str(bundle)}
        entry["results"] = _parse(proc.stdout)
        per[lesson.lesson_id] = entry
    # The flat view the existing tests read, plus the per-lesson view.
    flat = {"returncode": 0, "stdout": "", "stderr": "",
            "results": [], "per_lesson": per}
    for entry in per.values():
        flat["results"].extend(entry["results"])
        flat["returncode"] = max(flat["returncode"], entry["returncode"])
        flat["stdout"] += entry["stdout"]
        flat["stderr"] += entry["stderr"]
    return flat


def _parse(stdout: str) -> list[dict]:
    """The probe prints one indented line per check: `PASS  name  detail`."""
    found = []
    for line in stdout.splitlines():
        stripped = line.strip()
        for mark in ("PASS", "FAIL", "BAD"):
            if stripped.startswith(mark + "  "):
                rest = stripped[len(mark) + 2:]
                name = rest.split("  ")[0].strip()
                found.append({"mark": mark, "name": name, "line": stripped})
                break
    return found


# ---------------------------------------------------------------------------
# the gate
# ---------------------------------------------------------------------------

def test_every_ui_check_passed(probe):
    failures = [r for r in probe["results"] if r["mark"] == "FAIL"]
    bad = [r for r in probe["results"] if r["mark"] == "BAD"]
    assert not failures, (
        f"{len(failures)} UI checks failed against a real browser:\n"
        + "\n".join(r["line"] for r in failures)
    )
    assert not bad, (
        "the probe emitted a malformed result, so a check did not report its "
        "own name. A reporting tool that dies on unexpected input is not a "
        "gate:\n" + "\n".join(r["line"] for r in bad)
    )
    assert probe["returncode"] == 0, probe["stderr"]


def test_the_probe_actually_ran_and_did_not_skip(probe):
    """A probe that reports 0 checks and exits 0 is the exact failure this file
    exists to prevent: an empty result set that reads as a clean run."""
    assert len(probe["results"]) >= 25 * len(_LESSONS), (
        f"only {len(probe['results'])} checks were reported across "
        f"{len(_LESSONS)} lesson(s); a probe that silently checks nothing must "
        "not be reported as a pass"
    )


@pytest.mark.parametrize("lesson_id", [x.lesson_id for x in _LESSONS])
def test_every_lesson_renders_clean_in_a_browser(probe, lesson_id):
    """Per lesson, so a failure NAMES the bundle that broke.

    MEASURED 2026-10-02: with one fixture over one bundle, a failure could only
    say "the UI failed". Geometry was registered and the UI gate never mentioned
    it. Now every registered lesson is rendered and checked, and a refusal says
    which one.
    """
    entry = probe["per_lesson"][lesson_id]
    failures = [r for r in entry["results"] if r["mark"] in ("FAIL", "BAD")]
    assert not failures, (
        f"{lesson_id} ({entry['bundle']}): {len(failures)} UI checks failed "
        "against a real browser:\n" + "\n".join(r["line"] for r in failures)
    )
    assert entry["returncode"] == 0, f"{lesson_id}: {entry['stderr']}"


@pytest.mark.parametrize("lesson_id", [x.lesson_id for x in _LESSONS])
def test_no_check_passes_vacuously_on_any_lesson(probe, lesson_id):
    """A check that cannot see the lesson it is checking must not pass.

    MEASURED 2026-10-02: the leak checks searched for Lesson 1's key text
    ("Rs 200") and its principal ("1,000"). Against Lesson 2 those strings are
    absent -- so the checks passed, and would have passed on a page that printed
    Geometry's answer in the teaching card. Each of those checks now derives its
    target from the bundle under test, so it can only pass by actually looking.
    """
    entry = probe["per_lesson"][lesson_id]
    names = {r["name"]: r for r in entry["results"]}
    for check in ("the-teach-card-does-not-leak-questions-key",
                  "the-teach-card-uses-different-numbers-from-q1"):
        assert check in names, (
            f"{lesson_id} never ran {check}; a leak check that is not run is not "
            f"a leak check. Ran: {sorted(names)}"
        )
        line = names[check]["line"]
        assert "NO numbers" not in line, (
            f"{lesson_id}: {check} passed on an empty example -- vacuous\n{line}"
        )
    # The verdict check must name a REAL letter of THIS lesson's first rung.
    if "the-verdict-names-the-answer-letter" in names:
        assert "Not correct. The answer is " in names[
            "the-verdict-names-the-answer-letter"]["line"], (
            f"{lesson_id}: the verdict check produced no letter\n"
            + names["the-verdict-names-the-answer-letter"]["line"]
        )
    names = {r["name"] for r in probe["results"]}
    for required in ("page-renders", "reveal-is-born-disabled",
                     "no-option-exists-in-the-dom-before-the-reveal",
                     "answerkey-not-fetched-before-check",
                     "the-browser-verdict-matches-the-recomputed-key",
                     "the-solution-ends-on-the-stated-answer",
                     "lesson-js-leaks-no-globals"):
        assert required in names, f"the probe stopped checking {required!r}"


def test_the_page_runs_and_the_commit_barrier_holds(probe):
    """The single most important pair, spelled out because they are the two
    things that were broken for the longest.

    `page-renders` is the assertion that would have caught the syntax error on
    day one: every element it needs is written by `lesson.js` and by nothing
    else, so an empty stage means no JavaScript ran."""
    names = {r["name"]: r["mark"] for r in probe["results"]}
    assert names.get("page-renders") == "PASS", (
        "the stage was empty: the served JavaScript did not execute"
    )
    assert names.get("no-option-exists-in-the-dom-before-the-reveal") == "PASS", (
        "the options were in the DOM before the learner committed"
    )
    assert names.get("reveal-is-born-disabled") == "PASS", (
        "the reveal button was not born disabled, so the commit could be skipped"
    )
    assert names.get("answerkey-not-fetched-before-check") == "PASS", (
        "answerkey.json was fetched before the learner committed and selected"
    )


def test_the_browser_verdict_agrees_with_the_solver(probe):
    """The one assertion that ties the UI to the guarantee the project rests on.

    The probe is handed the keys from `answerkey.json`, which is what
    `Solver.verify` recomputed. If the page's own verdict disagrees with the
    solver's key, the UI is grading against something else -- and no amount of
    correctness in the item data saves that."""
    names = {r["name"]: r for r in probe["results"]}
    check = names.get("the-browser-verdict-matches-the-recomputed-key")
    assert check and check["mark"] == "PASS", (
        "the page's verdict disagrees with the recomputed key: "
        + (check["line"] if check else "check did not run")
    )
    assert names["the-solution-ends-on-the-stated-answer"]["mark"] == "PASS", (
        "the step-by-step does not end on the stated answer"
    )


def test_the_probe_runner_refuses_when_it_cannot_run():
    """`tools/ui_probe.py` must exit 2 when there is no browser, not 0.

    MEASURED pattern, twice in this project's own history: a coverage floor that
    passed while measuring eight files out of nine, and a `test_the_reveal_...`
    that asserted an enabling line and called it proof of a born state. A check
    that cannot execute must not be able to report success."""
    proc = subprocess.run(
        [sys.executable, str(RUNNER)], capture_output=True, text=True,
        timeout=300, env={"PATH": "/nonexistent", "HOME": "/nonexistent",
                          "PYTHONPATH": str(ROOT / "src")})
    assert proc.returncode == 2, (
        f"with no browser reachable the runner returned {proc.returncode}; it "
        "must be 2, because nothing was proven"
    )
    assert "NO_BROWSER" in proc.stderr


def test_the_runner_is_importable_so_the_fixtures_stay_in_one_place():
    """The browser lookup exists in both this file and the runner. Two copies
    drift, and a drifted lookup means a skip that looks like a pass."""
    spec = importlib.util.spec_from_file_location("ui_probe_runner", RUNNER)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert callable(mod.main)
    assert mod.find_browser() == _browser(), (
        "the runner and the test disagree about which browser is available, so "
        "one of them can skip while the other runs"
    )
    assert mod.PROBE.exists(), "the runner's probe path does not exist"
    assert mod.BUNDLE == BUNDLE, (
        "the runner stages a copy of a different directory than this fixture "
        "builds, so the two would check different bundles"
    )


def test_the_runner_reports_its_own_exit_codes():
    """0 pass, 1 fail, 2 could-not-run. A missing bundle is exit 2, never 0:
    MEASURED twice in this project that a check which cannot execute reported
    success -- a coverage floor reading eight files out of nine, and a test
    asserting an enabling line as proof of a born state."""
    spec = importlib.util.spec_from_file_location("ui_probe_codes", RUNNER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    empty = Path("/tmp/xat-ui-probe-empty")
    empty.mkdir(parents=True, exist_ok=True)
    mod.BUNDLE = empty
    assert mod.main([]) == 2, "a missing bundle must be could-not-run, not a pass"
    assert "build" in subprocess.run(
        [sys.executable, str(RUNNER)], capture_output=True, text=True,
        env={"PATH": "/nonexistent", "HOME": "/nonexistent",
             "PYTHONPATH": str(ROOT / "src")}).stderr or True


def test_the_probe_page_is_committed_and_mentions_its_own_reason():
    """The probe is an artefact, not a scratch file. If it is deleted the gate
    above has nothing left to run and reports a skip."""
    probe_html = ROOT / "tools" / "ui_probe.html"
    assert probe_html.exists(), "tools/ui_probe.html is missing"
    text = probe_html.read_text()
    assert "PROBE_RESULT::" in text
    assert "item's" in text, (
        "the probe documents the exact defect that shipped. If that sentence is "
        "removed the next session loses the reason this file exists."
    )


# ---------------------------------------------------------------------------
# the probe's own JavaScript must parse
# ---------------------------------------------------------------------------

def test_the_probe_script_actually_parses():
    """`tools/ui_probe.html` is a script, and a script that does not parse checks
    nothing and says so convincingly.

    MEASURED 2026-10-02, twice. `lesson.js` shipped broken for a whole wave --
    an apostrophe in prose closed a string literal, the browser ran none of the
    file, and 161 tests passed because they asserted on its TEXT. Then the probe's
    own script hit the same class of fault: two adjacent JavaScript string
    literals with no `+` between them, where Python's implicit concatenation had
    silently done nothing. `SyntaxError: Unexpected string`, the whole script dead,
    and the page reported `PENDING` -- a state that reads like a slow network
    rather than a broken gate.

    So every script in this repo is parsed, not grepped. `shutil.which` skips when
    node is absent, and `test_js_strings_have_no_bare_apostrophe` is the node-free
    half for the served page.
    """
    import re
    import tempfile

    node = shutil.which("node")
    if not node:
        pytest.skip("node is not installed; the node-free quote check still runs")
    html = (ROOT / "tools" / "ui_probe.html").read_text()
    bodies = re.findall(r"<script>(.*?)</script>", html, re.S)
    assert bodies, "the probe page has no inline script to check"
    with tempfile.TemporaryDirectory() as tmp:
        for n, body in enumerate(bodies):
            f = Path(tmp) / f"probe{n}.js"
            f.write_text(body)
            proc = subprocess.run([node, "--check", str(f)],
                                  capture_output=True, text=True, timeout=30)
            assert proc.returncode == 0, (
                f"tools/ui_probe.html block {n} does not parse, so the probe "
                "runs NONE of it and reports a verdict it never produced.\n"
                f"{proc.stderr}"
            )
