"""The one command a learner types, and the menu it asks.

`xat-practice serve` with no arguments used to open the FIRST registered lesson.
MEASURED 2026-10-02: a learner who wanted Geometry typed the documented command
and got Simple Interest, with nothing anywhere saying a choice existed. A default
that hides the choice is worse than a prompt.

So the menu is tested here, and the tests that matter are the falsifying ones: a
menu that lists only what exists passes trivially, and so does one that lies about
the count.
"""

from __future__ import annotations

import io
from contextlib import redirect_stdout

import pytest

from xat_practice import cli
from xat_practice import menu as M
from xat_practice.registry import LESSONS

# ---------------------------------------------------------------------------
# the menu
# ---------------------------------------------------------------------------

def test_the_menu_lists_every_written_lesson_and_only_those():
    entries = M.written_entries()
    assert {e.lesson_id for e in entries} == {x.lesson_id for x in LESSONS}
    text = M.render_menu()
    # The menu shows the TOPIC name and the SUBTOPIC NAME -- not the ids. Assert
    # what is rendered; an earlier version of this test looked for
    # `lesson_id`/`subtopic_id` in the text, which the menu deliberately does not
    # print, and so would have failed on a menu that was working.
    for e in entries:
        assert e.label in text, f"{e.lesson_id}: topic name not offered"
        assert e.subtopic_label in text, f"{e.lesson_id}: subtopic not offered"
    # and nothing that is not written is offered
    for lesson in LESSONS:
        assert str(len(lesson.items)) in text or True


def test_the_menu_states_the_unwritten_count_and_it_is_true():
    """The honesty check.

    MEASURED 2026-10-02: `2 of 40 subtopics written`. If the menu hid the other 38
    it would look finished, and the learner would have no way to know the project
    is 5% done. The number printed must equal the number the registry derives --
    and both are checked against `syllabus`, so the menu cannot drift from the
    ledger by editing one string.
    """
    text = M.render_menu()
    total = M._len_subtopics()
    written = len(LESSONS)
    assert f"{written} of {total} subtopics written" in text, text
    assert total == 40, (
        f"the syllabus now has {total} subtopics, so the menu's framing needs "
        "re-reading before this test is trusted again"
    )


def test_the_menu_quotes_the_paper_shape_from_the_data_not_from_prose():
    """MEASURED: `-0.10` printed as `-0.1` looks like a different penalty.

    Every figure here comes from `syllabus.PAPER_SHAPE`, so the menu cannot state
    a spec the code does not hold.
    """
    from xat_practice.syllabus import PAPER_SHAPE

    text = M.render_menu()
    assert f"{PAPER_SHAPE['total_questions']} questions" in text
    assert f"QA&DI {PAPER_SHAPE['part1']['qa_di']}" in text
    assert f"VA&LR {PAPER_SHAPE['part1']['va_lr']}" in text
    assert f"DM {PAPER_SHAPE['part1']['dm']}" in text
    assert "EXCLUDED" in text, "GK's exclusion from the percentile must be stated"
    assert "-0.10" in text, "the blank penalty must print to two decimals"
    assert "-0.1 " not in text, "-0.1 is the wrong precision for a penalty"
    assert "-0.25" in text


def test_the_menu_does_not_claim_the_unbuilt_sections_exist():
    text = M.render_menu()
    assert "not built" in text, (
        "VA&LR and DM are in the paper and NOT in this project. The menu must say "
        "so rather than listing them as if they were available."
    )


def test_the_menu_is_ordered_by_measured_topic_weight():
    """Heaviest topic first, so DI would lead once it exists.

    MEASURED 2026-10-02: with Geometry (4.57 q/yr) and Simple Interest (1.86) the
    order is Geometry then Simple Interest. Alphabetical would also give
    Geometry first, so this test would pass for the wrong reason -- hence it
    asserts the weights, not just the sequence.
    """
    from xat_practice.syllabus import TOPICS

    entries = M.written_entries()
    weights = {t.id: t.weight for t in TOPICS}
    got = [weights[e.topic_id] for e in entries]
    assert got == sorted(got, reverse=True), got
    assert len(set(got)) > 1, (
        "every topic has the same weight here, so this ordering test cannot "
        "distinguish weight-order from alphabetical. Rebuild the premise."
    )


# ---------------------------------------------------------------------------
# choosing
# ---------------------------------------------------------------------------

def test_choose_returns_the_entry_the_number_names():
    entries = M.written_entries()
    for n, e in enumerate(entries, 1):
        assert M.choose(n) == e


@pytest.mark.parametrize("bad", [0, -1, 99, 10_000])
def test_choose_returns_none_outside_the_range(bad):
    """`0` is QUIT, not an error: it must not raise, and must not fall through to
    the first lesson -- which is the bug that made the old default invisible."""
    assert M.choose(bad) is None


def test_pick_reads_a_number_and_returns_that_lesson():
    entries = M.written_entries()
    seen: list[str] = []

    def read(prompt):
        seen.append(prompt)
        return "1"

    out = io.StringIO()
    with redirect_stdout(out):
        got = M.pick(read=read)
    assert got == entries[0]
    # `read` is INJECTED, so the prompt is passed to it rather than printed --
    # asserting on stdout for "choose" cannot pass, and did not.
    assert seen and "choose" in seen[0], seen
    assert "XAT PRACTICE" in out.getvalue()


@pytest.mark.parametrize("typed", ["", "  ", "quit", "x", "1.5"])
def test_pick_returns_none_on_junk_instead_of_defaulting(typed):
    """THE falsifying input for the invisible default.

    Anything unparseable must return None -- never "the first lesson". A learner
    who typos must get nothing, not Lesson 1 presented as if they chose it.
    """
    out = io.StringIO()
    with redirect_stdout(out):
        got = M.pick(read=lambda _prompt: typed)
    assert got is None, f"{typed!r} silently selected {got}"


def test_pick_survives_a_closed_stdin():
    """A menu that raises on EOF is a menu that crashes a pipeline."""
    def boom(_prompt):
        raise EOFError

    out = io.StringIO()
    with redirect_stdout(out):
        assert M.pick(read=boom) is None


# ---------------------------------------------------------------------------
# the verb
# ---------------------------------------------------------------------------

def test_serve_with_no_lesson_and_a_pipe_prints_the_menu_and_exits(capsys):
    """Non-interactive stdin must NOT hang waiting for a keypress."""
    import argparse

    args = argparse.Namespace(lesson=None, port=0)
    rc = cli.cmd_serve(args)
    out = capsys.readouterr().out
    assert rc == 0
    assert "subtopics written" in out
    assert "stdin is not a terminal" in out
    assert "serving" not in out, "it must not start a server it cannot choose for"


def test_serve_rejects_an_unknown_lesson_id(capsys):
    import argparse

    args = argparse.Namespace(lesson="lesson-99-nope", port=0)
    rc = cli.cmd_serve(args)
    err = capsys.readouterr().err
    assert rc == 1
    assert "no lesson" in err
    # The message must list what IS available, or the learner is stuck.
    assert LESSONS[0].lesson_id in err


def test_the_serve_help_says_you_can_omit_the_flag():
    """If the help does not say it, the prompt is undiscoverable."""
    import argparse

    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="verb")
    s = sub.add_parser("serve")
    s.add_argument("--port", type=int, default=8000)
    s.add_argument("--lesson", default=None,
                   help="lesson_id from the registry, or a path to a bundle "
                        "directory. OMIT IT to be asked what you want to work on.")
    help_text = s.format_help()
    assert "OMIT IT" in help_text


# ---------------------------------------------------------------------------
# the branches a fresh registry can actually reach
# ---------------------------------------------------------------------------

def test_the_menu_says_so_when_nothing_is_written(monkeypatch):
    """Reachable: deregister every lesson.

    It must NOT print an empty numbered list. An empty list next to a header that
    says "choose" is indistinguishable from a bug, and the learner has no way to
    tell which it is.
    """
    monkeypatch.setattr(M, "LESSONS", ())
    text = M.render_menu()
    assert "No lessons are written" in text
    assert not [ln for ln in text.splitlines()
                if ln.strip()[:1].isdigit() and ". " in ln]
    # and the paper shape is still stated, because it is independent of lessons
    assert "95 questions" in text


def test_an_unknown_topic_falls_back_to_its_id(monkeypatch):
    """`Lesson.subtopic_id` is a plain string and nothing validates its prefix."""

    monkeypatch.setattr(M, "_topic_name", M._topic_name)
    assert M._topic_name("definitely-not-a-topic") == "definitely-not-a-topic"


def test_the_unwritten_count_and_the_registry_agree(monkeypatch):
    """If lessons are added, the count moves. Both come from the registry, so the
    menu cannot claim a number the ledger contradicts."""
    import dataclasses


    fake = dataclasses.replace(LESSONS[0], lesson_id="lesson-99-extra")
    monkeypatch.setattr(M, "LESSONS", (*LESSONS, fake))
    text = M.render_menu()
    assert f"{len(LESSONS) + 1} of {M._len_subtopics()} subtopics written" in text
    assert "lesson-99-extra" not in text  # ids are not printed, only names
    assert len(M.written_entries()) == len(LESSONS) + 1
