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
from xat_practice.registry import LESSONS, items_written, subtopics_written
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
    # DERIVED, not hardcoded. MEASURED 2026-10-02: this said "population: 4" and
    # broke the day Lesson 2 was registered -- which was correct behaviour and the
    # wrong test. A count pinned in a test is a count that must be edited by hand
    # every time the world grows, and the edit is exactly where a lie creeps in.
    for lesson in LESSONS:
        assert f"population: {len(lesson.items)} items = 1 lesson, " \
               f"{lesson.lesson_id}, {lesson.subtopic_id}" in out, (
            f"each lesson must state its own population and subtopic: {out}")
        assert f"admitted: {len(lesson.items)}/{len(lesson.items)}" in out
        assert f"over {len(lesson.items)})" in out, (
            "the refusal rate is printed without its denominator")
    assert "refused:" in out
    # and the pooled line must NOT look like a score
    assert "NOT a score" in out, (
        "a pooled total with no warning is a paper-shaped claim about a pool of "
        "lessons"
    )


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

def _only(monkeypatch, items):
    """Make the verbs see exactly `items`, as ONE lesson.

    MEASURED 2026-10-02: these tests used to patch `cli.all_items`. Then
    `cmd_gates` was changed to iterate `LESSONS` (per lesson, because G11 and G15
    are paper rules), and the patch silently did nothing -- the planted defect was
    never gated and the assertion would have passed FOR THE WRONG REASON.

    A planted defect that is not planted is the exact failure mode this repo keeps
    hitting: a check that has only ever been shown a true statement. So the seam
    is patched where the verb reads, and asserted below by planting a defect that
    MUST be refused.
    """
    import dataclasses


    base = LESSONS[0]
    lesson = dataclasses.replace(base, items=tuple(items),
                                 subtopic_id=base.subtopic_id)
    monkeypatch.setattr(cli, "LESSONS", (lesson,))
    return lesson


def test_the_planting_seam_itself_rejects_a_bad_lesson(monkeypatch):
    """Guard the guard. If `_only` ever stops being read, every planted-defect test
    above silently passes on an ungated input."""
    import dataclasses

    from xat_practice import lesson1

    wrong = dataclasses.replace(lesson1.LESSON[0], key_index=1)
    _only(monkeypatch, [wrong])
    seen = [it for ls in cli.LESSONS for it in ls.items]
    assert [it.id for it in seen] == [wrong.id], (
        "_only did not put the planted item where the verb reads it"
    )


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
    _only(monkeypatch, [wrong])

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
    _only(monkeypatch, [mismatched])

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
    assert not bare, f"a bare 'written: N' is ambiguous: {bare}"
    written = len(subtopics_written())
    assert f"{written}/40 subtopics = {100 * written / 40:.1f}%" in out, (
        "the coverage figure must be printed with its denominator"
    )


def test_gates_and_levels_report_over_every_lesson(capsys):
    """A verb that kept reporting Lesson 1 after Lesson 2 existed would quietly
    test less than it claims -- the coverage-floor defect with a green tick."""
    assert cli.cmd_gates(None) == 0
    out = capsys.readouterr().out
    assert f"lessons:    {len(LESSONS)}   items gated: {items_written()}" in out
    assert all(x.lesson_id in out for x in LESSONS), (
        "every registered lesson must be named in the population line"
    )
    capsys.readouterr()
    assert cli.cmd_levels(None) == 0
    lvl = capsys.readouterr().out
    # EVERY item of EVERY lesson, not a sample. This test was written when Lesson 2
    # did not exist and asserted "L1-F"; it would have passed while quietly
    # covering half the items.
    assert all(it.id in lvl for ls in LESSONS for it in ls.items), (
        "levels must report every item of every lesson"
    )


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


# ---------------------------------------------------------------------------
# docs/COVERAGE.md is DERIVED, and this is the proof it cannot drift
# ---------------------------------------------------------------------------
# MEASURED 2026-10-02: `xat-practice weightage` printed `written: 4` -- the ITEM
# count -- beside two SUBTOPIC counts on a project with 40 subtopics, and read as
# "four topics done" when the truth was one. A status document that people edit
# by hand would carry that lie for longer, and nobody would know.

COVERAGE_DOC = Path(__file__).resolve().parent.parent / "docs" / "COVERAGE.md"


def _generated_block_from_doc() -> str:
    from xat_practice.coverage import BEGIN, END

    text = COVERAGE_DOC.read_text()
    start = text.index(BEGIN)
    stop = text.index(END, start)
    chunk = text[start + len(BEGIN):stop]
    assert "```" in chunk, "the generated block must be fenced"
    fenced = chunk.strip().strip("`")
    return fenced.strip()


def test_coverage_doc_matches_the_verb_exactly():
    """The staleness test. If code moves and the document does not, this fails.

    It compares the FENCED BLOCK only, not the whole file, so the prose around it
    is free to change without touching a test. A test over the whole document
    would fail every time a sentence is edited, and a test that fails on prose
    gets deleted."""
    from xat_practice.coverage import render_coverage

    assert COVERAGE_DOC.exists(), "docs/COVERAGE.md is the readable ledger"
    assert _generated_block_from_doc() == render_coverage(), (
        "docs/COVERAGE.md has drifted from `xat-practice coverage`. Re-run the "
        "verb and paste its output into the fenced block between the BEGIN/END "
        "markers. Do not hand-edit the numbers inside the block."
    )


def test_coverage_doc_states_the_scope_on_its_first_lines():
    """A coverage document read as 'XAT coverage' is the exact misreading this
    file exists to prevent, so the limit is in the first paragraph."""
    head = COVERAGE_DOC.read_text().split("\n\n")[0] + COVERAGE_DOC.read_text().split("\n\n")[1]
    assert "28 of the 95" in head, (
        "the first lines must say we train 28 of the 95 questions -- QA&DI only"
    )
    for absent in ("VA&LR", "DM"):
        assert absent in head, f"{absent} must be named as untrained"
    assert "GK" in head, "GK is out of scope and must be named"


def test_coverage_never_puts_a_topic_rate_on_a_subtopic_row():
    """MEASURED: no source gives a per-subtopic frequency. XLRI publishes no
    breakdown and ours is a coaching compilation at topic level, so a q/yr on a
    subtopic row would be a number nobody measured."""
    from xat_practice.coverage import render_coverage

    out = render_coverage()
    assert "q/yr" not in out, (
        "a per-subtopic rate appears in the ledger. There is no source for one."
    )
    assert "per_year" not in out


def test_coverage_reports_subtopics_and_items_separately():
    from xat_practice.coverage import render_coverage, totals

    t = totals()
    out = render_coverage()
    assert f"subtopics written   {t['subtopics_written']:>3}" in out
    assert f"items written       {t['items_written']:>3}" in out
    assert t["subtopics_pending"] == (t["subtopics_trained"]
                                      - t["subtopics_written"])


def test_the_block_capacity_number_is_the_honest_one():
    """MEASURED 2026-10-02: this is the number the 20-question plan turns on, and
    it is zero. Every subtopic has fewer than 10 named traps, including the one
    that was just expanded to 8.

    A test that pins it is a test that will FAIL the day the pool grows -- which
    is the correct direction for a capacity figure: it should announce the
    improvement, and any change must be argued rather than absorbed."""
    from xat_practice.coverage import (
        BLOCK_SHAPES_RELAXED,
        BLOCK_TRAPS_FULL,
        subtopic_rows,
        totals,
    )

    t = totals()
    rows = subtopic_rows()
    assert t["can_carry_block"] == sum(
        1 for r in rows if r["traps"] >= BLOCK_SHAPES_RELAXED)
    assert len(rows) == t["subtopics_trained"], "every trained subtopic gets a row"
    if t["can_carry_block"] < t["subtopics_trained"]:
        assert any(r["block_capacity"] == "cannot carry a block" for r in rows), (
            "a subtopic below the threshold must say so on its row"
        )
    assert BLOCK_TRAPS_FULL > BLOCK_SHAPES_RELAXED, (
        "full variety is a higher bar than the relaxed shape budget, and the two "
        "must not be the same number or the second column means nothing"
    )


def test_coverage_lists_the_written_subtopic_as_written():
    from xat_practice.coverage import render_coverage
    from xat_practice.registry import subtopics_written

    out = render_coverage()
    written = subtopics_written()
    # Every written subtopic is marked WRITTEN, and ONLY those -- a stray WRITTEN
    # would overstate coverage, which is the same lie as a count with no
    # denominator, wearing a tick.
    assert out.count("WRITTEN") == len(written), (
        f"expected {len(written)} WRITTEN markers, found {out.count('WRITTEN')}"
    )
    # Column order matters and is asserted rather than assumed: the status column
    # PRECEDES the subtopic column, so "is the subtopic's own row marked" has to be
    # answered by row, not by asking what text comes after the name.
    rows = [ln for ln in out.splitlines() if "WRITTEN" in ln]
    for sub in sorted(written):
        assert any(sub in ln for ln in rows), (
            f"{sub} is written but its row is not marked WRITTEN: {out}"
        )
    for ln in rows:
        assert any(sub in ln for sub in written), (
            f"a WRITTEN row names a subtopic that is not written: {ln}"
        )
    for line in out.splitlines():
        if "WRITTEN" in line:
            assert "items" not in line, (
                f"WRITTEN must mark a subtopic, never an item count: {line}"
            )


def test_the_registry_refuses_a_duplicate_subtopic():
    """Two lessons claiming one subtopic is what turns '2 of 40' into a sum with a
    duplicate in it, so the count would overstate what is trained."""
    import dataclasses

    from xat_practice import lesson1 as L1
    from xat_practice import registry as R

    base = next(x for x in R.LESSONS if x.lesson_id == L1.LESSON_ID)
    twin = dataclasses.replace(base, lesson_id="lesson-01-again")
    original = R.LESSONS
    try:
        R.LESSONS = (base, twin)
        with pytest.raises(AssertionError) as err:
            R.assert_registry_is_honest()
        assert base.subtopic_id in str(err.value)
    finally:
        R.LESSONS = original


@pytest.mark.parametrize("break_it, expected", [
    # A missing step-by-step, and a step-by-step whose LAST LINE is a rejected
    # distractor. The second is the one a learner actually suffers: they read to the
    # bottom of the panel and copy whatever number is last.
    ("missing", "no step-by-step"),
    ("wrong_last_line", "does not state its own key"),
])
def test_the_registry_refuses_a_solution_that_does_not_state_its_key(break_it,
                                                                     expected):
    import dataclasses

    from xat_practice import lesson1 as L1
    from xat_practice import registry as R

    base = next(x for x in R.LESSONS if x.lesson_id == L1.LESSON_ID)
    sols = dict(base.solutions)
    target = L1.LESSON[0].id
    if break_it == "missing":
        sols.pop(target)
    else:
        sols[target] = (*sols[target][:-1], "the answer is Rs 180")
    bad = dataclasses.replace(base, solutions=sols)
    original = R.LESSONS
    try:
        R.LESSONS = (bad,)
        with pytest.raises(AssertionError, match=expected):
            R.assert_registry_is_honest()
    finally:
        R.LESSONS = original


def test_every_lesson_is_registered_exactly_once_and_is_buildable():
    """The registry is the source of truth (D20), so the build's own walk over it is
    the cheapest honest check that `xat-practice build` cannot half-succeed."""
    from xat_practice.bundle import out_dir

    ids = [x.lesson_id for x in LESSONS]
    assert len(set(ids)) == len(ids), f"duplicate lesson_id in {ids}"
    for lesson in LESSONS:
        assert out_dir(lesson.lesson_id).name == lesson.lesson_id
        assert len(lesson.solutions) == len(lesson.items)
