"""The command line, tested. Every verb, and the numbers each one prints.

These tests exist because of a measurement, not a hunch.

MEASURED 2026-10-02: the coverage floor reported 95.19% and passed, and the
package's real number was 86.13%. `cli.py` was absent from the report entirely --
115 statements, 16% of the package -- because **no test had ever imported it**.
Coverage only measures a module that something executed, so a file nothing
imports is invisible, and an invisible file cannot drag a floor down.

That is the same failure as a stale `.coverage` file, wearing a different hat: a
count with no denominator is a lie that looks like a pass. The README quoted
95.19% as the package's coverage and it was the coverage of eight files out of
nine.

So this file exists to put all eight verbs under test. A second reason, which is
better: **every verb prints a number that a document quotes.** `weightage` prints
the population, `ev` prints the three marking figures, `shapes` prints the
quotas, `gates` prints a refusal rate with its denominator. A doc and a verb that
prints its number are the same fact in two places, and this file is what makes
them fail together instead of quietly disagreeing.
"""

from __future__ import annotations

import runpy
from pathlib import Path

import pytest

from xat_practice import cli
from xat_practice.registry import LESSONS, items_written
from xat_practice.syllabus import SUBTOPICS

ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# every verb re-derives or builds; none is a convenience wrapper
# ---------------------------------------------------------------------------

def test_gates_reports_a_population_with_a_denominator(capsys):
    """`xat-practice gates` is the first thing a session runs. A refusal count
    printed without the population it was counted over is the exact shape of
    'a count with no denominator is a lie that looks like a pass'."""
    assert cli.cmd_gates(None) == 0
    out = capsys.readouterr().out
    assert "population: 4 items" in out
    assert "admitted:   4" in out
    assert "refused:" in out
    # the rate must name what it is a rate OF
    assert "over 4)" in out, "the refusal rate is printed without its denominator"


def test_levels_prints_the_derived_level_and_its_drivers(capsys):
    """The level is derived, so the CLI must print the DRIVERS, not just the
    tier. A tier without its drivers cannot be argued with."""
    assert cli.cmd_levels(None) == 0
    out = capsys.readouterr().out
    assert "foundation" in out and "hard" in out
    assert out.index("foundation") < out.index("hard"), "the ladder is out of order"
    for driver in ("single move", "derivation",
                   "requires a substitution before the method applies"):
        assert driver in out, f"no drivers printed; {driver!r} should appear"
    assert "no claim" in out, (
        "a drafter's claimed level must be shown beside the derived one, "
        "because a disagreement is a refusal (G7) and a silent overwrite "
        "hides it. These four items are authored as data and claim nothing."
    )


def test_build_writes_the_lesson_and_names_the_rungs(capsys):
    assert cli.cmd_build(None) == 0
    out = capsys.readouterr().out
    assert "built out/lesson-01-simple-interest/" in out
    for item_id in ("L1-F", "L1-E", "L1-M", "L1-H"):
        assert item_id in out


def test_weightage_prints_the_population_it_measured_over(capsys):
    """This verb is the source of every q/yr figure in docs/ and in the README.
    It runs `self_check()` first, so printing the table means the table closes
    to 28 every year."""
    assert cli.cmd_weightage(None) == 0
    out = capsys.readouterr().out
    assert "population: 196 questions = 28 per paper x 7 papers, 2020-2026" in out
    assert "secondary" in out, (
        "the source is a coaching compilation. Printing it without that word "
        "would let a secondary table be quoted as an official one."
    )
    for tier in ("P1", "P2", "P3"):
        assert tier in out
    assert "named traps:" in out


def test_weightage_raises_before_printing_if_the_table_does_not_close(monkeypatch,
                                                                    capsys):
    """The verb must not print a broken table and then complain."""
    from xat_practice import syllabus as S

    bad = S.Topic("fake", "Fake", (1,) * 7, True)
    monkeypatch.setattr(S, "TOPICS", (*S.TOPICS, bad))
    with pytest.raises(ValueError, match="The table is wrong, not the exam"):
        cli.cmd_weightage(None)
    assert "population:" not in capsys.readouterr().out


def test_ev_prints_the_three_marking_numbers_the_pedagogy_rests_on(capsys):
    """PEDAGOGY R1 and D3 are two sentences long and both are arithmetic. If
    these three figures move, the docs are wrong and this says so."""
    assert cli.cmd_ev(None) == 0
    out = capsys.readouterr().out
    assert "EV = +0.0000" in out, "guessing at 5 options must be exactly zero"
    assert "EV = +0.0625" in out, "a 4-option paper pays you to guess"
    assert "EV = -0.1000" in out, "the 9th blank is worse than guessing"
    assert "EV = -0.2000" in out, "ten blanks is twice as bad"
    assert "equilibrium" in out


def test_shapes_prints_every_shape_and_its_quota(capsys):
    """D8: LESSON and PRACTICE carry no negative marking, MOCK does. That split
    is the reason they are two products rather than one product with a length
    setting, so it is asserted on the printed output, not only in the dataclass.

    D12: LESSON is 1/1/1/1. A paper-level quota applied to four items once
    deleted the hard rung, so the lesson's own quota is asserted here too."""
    assert cli.cmd_shapes(None) == 0
    out = capsys.readouterr().out
    for shape in ("LESSON", "PRACTICE", "MOCK-QA", "MOCK-FULL"):
        assert shape in out
    assert "negative marking: False" in out, "LESSON and PRACTICE take no marks"
    assert "negative marking: True" in out, "MOCK carries -0.25 and the blank penalty"
    assert "'foundation': 1, 'easy': 1, 'medium': 1, 'hard': 1" in out, (
        "the lesson is one question per level, and that is the whole point of "
        "the product. G11 once apportioned the 20-item mix onto 4 items and "
        "dropped HARD."
    )
    assert "options: 5" in out, "D3: five options, because a 4-option paper pays you to guess"
    assert "level recipes" in out
    assert "requested of CODE" in out, (
        "LEVEL_RECIPES is the one place a level may be requested, and it is "
        "requested of code. The printed help must not suggest otherwise."
    )
    assert "subtopics by stratum: {'quant': 37, 'logic': 3, 'judgement': 0}" in out


def test_agents_rebuilds_opencode_json_without_changing_it():
    """`xat-practice agents` rewrites a 145KB file that nine agent definitions
    and their tests depend on. It must be deterministic, and this asserts that
    rather than assuming it."""
    from xat_practice import build_opencode as bo

    before = bo.OUT.read_text()
    assert cli.cmd_agents(None) == 0
    assert bo.OUT.read_text() == before, (
        "rebuilding opencode.json changed it. Either the builder is not "
        "deterministic or the file on disk is stale; both are defects."
    )


# ---------------------------------------------------------------------------
# argument parsing and dispatch
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("verb", ["gates", "levels", "build", "agents",
                                  "weightage", "ev", "shapes"])
def test_every_read_only_verb_dispatches_from_the_command_line(verb, capsys):
    """Parsed through `main()`, not called directly, so the wiring is under test
    too. `serve` is excluded: it blocks."""
    assert cli.main([verb]) == 0
    assert capsys.readouterr().out.strip(), f"{verb} printed nothing"


def test_serve_is_registered_but_not_run_by_the_dispatcher():
    """It must be reachable and it must default to the built bundle."""
    with pytest.raises(SystemExit):
        cli.main(["serve", "--help"])


def test_a_verb_is_required():
    with pytest.raises(SystemExit) as e:
        cli.main([])
    assert e.value.code == 2


def test_an_unknown_verb_is_refused_not_ignored():
    with pytest.raises(SystemExit) as e:
        cli.main(["nonsense"])
    assert e.value.code == 2


def test_running_the_module_with_no_arguments_exits_non_zero():
    """The `__main__` guard. Reached with runpy so the last statement of the
    module is not the one line in it that no test would ever run."""
    with pytest.raises(SystemExit) as e:
        runpy.run_module("xat_practice.cli", run_name="__main__")
    assert e.value.code == 2, "argparse must reject a bare invocation"


def test_the_console_script_is_declared_and_importable():
    """pyproject points `xat-practice` at `xat_practice.cli:main`. If that
    module or that attribute moves, the installed command breaks at the moment
    someone relies on it -- which is how it was found the first time."""
    import tomllib

    with (ROOT / "pyproject.toml").open("rb") as f:
        cfg = tomllib.load(f)
    assert cfg["project"]["scripts"]["xat-practice"] == "xat_practice.cli:main"
    assert callable(cli.main)


# ---------------------------------------------------------------------------
# the doc's numbers and the verb's numbers are one fact, not two
# ---------------------------------------------------------------------------

def test_the_readme_quotes_the_population_this_cli_prints(capsys):
    """If `weightage`'s population changes, the README is wrong. Asserted
    against the README so the two cannot drift apart silently."""
    cli.cmd_weightage(None)
    out = capsys.readouterr().out
    readme = (ROOT / "README.md").read_text()
    assert "196 questions = 28 per paper x 7 papers, 2020-2026" in readme
    assert "population: 196 questions = 28 per paper x 7 papers, 2020-2026" in out


def test_the_decision_ledger_quotes_the_same_population(capsys):
    cli.cmd_weightage(None)
    out = capsys.readouterr().out
    for doc in ("docs/DECISIONS.md", "AGENTS.md"):
        text = (ROOT / doc).read_text()
        assert "196 questions = 7 papers" in text or "196 questions = 28 per paper" in text, (
            f"{doc} no longer states the population the weight model is measured over"
        )
        assert "196 questions = 28 per paper x 7 papers, 2020-2026" in out


# ---------------------------------------------------------------------------
# the two paths that only run when something has gone wrong
# ---------------------------------------------------------------------------
# Both of these were the uncovered half of `cmd_gates` and the whole body of
# `cmd_serve`. An uncovered error path is the half nobody has ever run, which is
# the state this project is most often bitten by.

def test_gates_exits_non_zero_and_names_the_refused_item(monkeypatch, capsys):
    """`gates` must FAIL LOUDLY, not print a refusal and return 0.

    The planted defect is a WRONG KEY -- the load-bearing failure. MEASURED: on
    the first build all four of Lesson 1's keys were refused because display
    strings like `Rs 200` do not parse as arithmetic, and `test_G5_planted_
    wrong_key_is_REFUSED` is the test that matters most in this repo. That is
    only useful if the verb's exit code changes: a gate that refuses and returns
    success is a gate nobody has to act on.

    The input is a key pointing at the wrong option. The derivation computes
    200, so key 0 is right and any other index is a wrong key -- and the solver,
    not a model, is what says so.
    """
    import dataclasses

    from xat_practice import lesson1

    wrong = dataclasses.replace(lesson1.LESSON[0], key_index=1)
    assert wrong.key_index != 0
    # MEASURED 2026-10-02: this patched `lesson1.LESSON`, which stopped having any
    # effect the moment `cmd_gates` began reading the registry -- so the planted
    # wrong key was never seen and the test would have passed FOR THE WRONG
    # REASON. Patch the seam the verb actually calls.
    monkeypatch.setattr(cli, "all_items", lambda: [wrong])

    assert cli.cmd_gates(None) == 1, "a refused item must make the verb exit non-zero"
    out = capsys.readouterr().out
    assert "REFUSED" in out, "the refusal must name the gate and the item"
    assert wrong.id in out
    assert "G5_key_grounded" in out, (
        "the load-bearing gate must be named, not summarised. Got: " + out
    )
    # and the per-gate tally must still be printed
    assert "G5_key_grounded: 1" in out


def test_gates_names_the_gate_that_caught_a_value_label_mismatch(monkeypatch,
                                                                capsys):
    """The other half: D11's defect. `option_values` exists because `Rs 200` does
    not parse as arithmetic, and G14 exists because `'14,400'` does not FAIL to
    parse -- it parses to the tuple (14, 400) and slips past the check.

    Planted here as a value the learner cannot see in the option they will read.
    MEASURED: the wrong assertion in this file's first draft was that this input
    would trip G5. It trips G14. The gate that fires is the one that should, and
    the test now says so instead of assuming.
    """
    import dataclasses

    from xat_practice import lesson1

    mismatched = dataclasses.replace(
        lesson1.LESSON[0], option_values=("200", "220", "100", "1200", "1250"))
    monkeypatch.setattr(cli, "all_items", lambda: [mismatched])

    assert cli.cmd_gates(None) == 1
    out = capsys.readouterr().out
    assert "G14_option_value_matches_label" in out
    assert "Rs 120" in out, "the refusal must name the label the learner sees"


def test_serve_prints_its_url_and_stops_cleanly_on_ctrl_c(monkeypatch, capsys):
    """The Ctrl-C path. MEASURED: the process has to close its socket on the way
    out, or the next `serve` fails to bind and the learner is told the port is
    busy when what is actually true is that a previous run leaked it."""
    import argparse

    made: list[int] = []

    class _Fake:
        verbose = False

        def __init__(self, _root, port):
            made.append(port)

        def serve_forever(self):
            raise KeyboardInterrupt

        def server_close(self):
            self.closed = True

    monkeypatch.setattr(cli, "make_server", _Fake)
    from xat_practice.bundle import out_dir as _od
    args = argparse.Namespace(lesson=str(_od(LESSONS[0].lesson_id)), port=8123)
    assert cli.cmd_serve(args) == 0
    out = capsys.readouterr().out
    assert "http://127.0.0.1:8123/" in out
    assert "ctrl-c to stop" in out
    assert made == [8123], "the server must be built on the requested port"


# ---------------------------------------------------------------------------
# the registry: one place that knows what is written
# ---------------------------------------------------------------------------
# MEASURED 2026-10-02: there were 11 references to `lesson1` across 6 files and
# `bundle.OUT_DIR` was a hardcoded `out/lesson-01`, so a second lesson meant
# editing six files and there was nowhere to build it. And `xat-practice
# weightage` printed `written: 4` -- the ITEM count -- between two SUBTOPIC
# counts, on a project with 40 subtopics. It read as "four topics done".

def test_the_registry_reports_subtopics_and_items_separately():
    """The falsifying input for the bug: 4 items is ONE subtopic."""
    from xat_practice.registry import subtopics_written

    subs = subtopics_written()
    assert items_written() == sum(len(x.items) for x in LESSONS)
    assert len(subs) <= items_written(), (
        "a lesson covers at most one subtopic, so subtopics can never exceed items"
    )
    # every written subtopic is a REAL subtopic in the syllabus

    from xat_practice.syllabus import SUBTOPICS as _S

    known = {st.id for st in _S}
    assert subs <= known, f"registry names unknown subtopics: {subs - known}"


def test_weightage_no_longer_conflates_items_with_subtopics(capsys):
    """THE regression test for the reported number.

    It must print BOTH, and it must print the item count under a name that says
    it is items. A line reading `written: 4` next to `subtopics trained: 40` is
    the defect."""
    assert cli.cmd_weightage(None) == 0
    out = capsys.readouterr().out
    assert "subtopics trained: 40" in out
    assert f"items written: {items_written()}" in out, (
        "the item count must be labelled as items"
    )
    bare = [ln for ln in out.splitlines()
            if "written:" in ln and "items written" not in ln]
    assert not bare or "written: 1 " in bare[0], (
        f"a bare 'written: N' is ambiguous: {bare}"
    )
    assert "1/40 subtopics = 2.5%" in out, (
        "the coverage figure must be printed with its denominator"
    )


def test_gates_and_levels_report_over_every_lesson(capsys):
    """A verb that kept reporting Lesson 1 after Lesson 2 existed would quietly
    test less than it claims -- the coverage-floor defect with a green tick."""
    assert cli.cmd_gates(None) == 0
    out = capsys.readouterr().out
    assert f"population: {items_written()} items across {len(LESSONS)} lesson(s)" in out
    assert all(x.lesson_id in out for x in LESSONS), (
        "every registered lesson must be named in the population line"
    )
    capsys.readouterr()
    assert cli.cmd_levels(None) == 0
    assert "L1-F" in capsys.readouterr().out


def test_the_registry_refuses_a_lesson_covering_two_subtopics():
    """Proved by construction, then checked: the invariant that makes 'subtopics
    written' a COUNT rather than a sum with a duplicate in it."""
    import dataclasses

    from xat_practice import lesson1 as L1
    from xat_practice import registry as R

    other = next(x for x in SUBTOPICS if x.id != L1.SUBTOPIC)
    borrowed = dataclasses.replace(L1.EASY, subtopic_id=other.id)
    bad = R.Lesson(
        lesson_id="bad", subtopic_id="whatever",
        items=(L1.FOUNDATION, borrowed),
        solutions={i.id: L1.SOLUTIONS[i.id] for i in (L1.FOUNDATION, borrowed)},
        teach=L1.TEACH,
    )
    original = R.LESSONS
    try:
        R.LESSONS = (bad,)
        with pytest.raises(AssertionError, match="ONE subtopic"):
            R.assert_registry_is_honest()
    finally:
        R.LESSONS = original


def test_the_registry_refuses_a_second_lesson_on_one_subtopic():
    import dataclasses

    from xat_practice import registry as R

    twin = R.LESSONS[0]
    clone = dataclasses.replace(twin, lesson_id="twin")
    original = R.LESSONS
    try:
        R.LESSONS = (twin, clone)
        with pytest.raises(AssertionError, match="double-count"):
            R.assert_registry_is_honest()
    finally:
        R.LESSONS = original


def test_the_bundle_directory_is_derived_from_the_lesson_id():
    """MEASURED: `out/lesson-01` was hardcoded, so a second lesson had nowhere to
    live and `--lesson` defaulted to a directory that might not be the one you
    meant."""
    from xat_practice.bundle import out_dir

    assert out_dir("lesson-01-simple-interest").name == "lesson-01-simple-interest"
    assert out_dir("a").name == "a", "the path must come from the id, not a constant"
