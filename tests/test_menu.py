"""The navigator page the learner actually lands on.

This was a TERMINAL PROMPT, twice, and both were wrong:

1. `serve` opened the FIRST registered lesson, so a learner who wanted Geometry
   typed the documented command and got Simple Interest, with nothing saying a
   choice existed. Safe by being invisible.
2. The fix was to ask in the terminal. MEASURED 2026-10-02, the owner rejected it:
   "I don't wanna invest the time in running commands". A CLI menu is the right
   shape for a CLI and the wrong shape for someone who wants to think about
   geometry rather than about process.

So it is a page. `serve` prints one URL and every choice after that is a click.
The tests that matter are the falsifying ones: a page that lists only what exists
passes trivially, and so does one that lies about the count.
"""

from __future__ import annotations

import re
from html import unescape
from pathlib import Path

import pytest

from xat_practice import cli
from xat_practice import menu as M
from xat_practice.registry import LESSONS


@pytest.fixture
def built_fake(tmp_path: Path) -> Path:
    """A directory that LOOKS built, so `cmd_serve` gets past its "nothing built"
    guard and reaches the branch under test.

    MEASURED while writing these: without it the verb returns 1 immediately, which
    is a correct result for the wrong reason, and every assertion about what it
    would have printed passes vacuously.
    """
    d = tmp_path / "out"
    (d / "lesson-01-simple-interest").mkdir(parents=True)
    (d / "index.html").write_text("<!doctype html><title>navigator</title>")
    (d / "lesson-01-simple-interest" / "index.html").write_text(
        "<!doctype html><title>lesson</title>")
    return d


class _Boom:
    """Stands in for the HTTPServer. `serve_forever` never returns, so raising
    KeyboardInterrupt is what Ctrl-C does for a real learner, and it is how the
    test escapes `cmd_serve` without a socket."""

    def serve_forever(self) -> None:
        raise KeyboardInterrupt

    def server_close(self) -> None:
        return None


# ---------------------------------------------------------------------------
# the page
# ---------------------------------------------------------------------------

def test_the_page_links_every_written_lesson_and_only_those():
    entries = M.written_entries()
    assert {e.lesson_id for e in entries} == {x.lesson_id for x in LESSONS}
    text = M.render_index_html()
    # UNESCAPED before comparing. MEASURED 2026-10-02: the first version asserted
    # `"Geometry & Mensuration" in text` against generated HTML and failed, because
    # the page correctly escapes it to `Geometry &amp; Mensuration`. The generator
    # was right and the test was wrong -- an assertion that fails on correct output
    # is how a correct escaping fix gets "reverted".
    plain = unescape(text)
    for e in entries:
        assert e.label in plain, f"{e.lesson_id}: topic name not offered"
        assert e.subtopic_label in plain, f"{e.lesson_id}: subtopic not offered"

    # And the links point at each lesson DIRECTORY, because the whole layout depends
    # on one origin: `serve` roots at `out/`, so `/<lesson_id>/` is what makes the
    # sibling `fetch('paper.json')` resolve.
    links = re.findall(r'href="([^"]+)"', text)
    assert links == [f"{e.lesson_id}/" for e in entries], links


def test_the_page_states_the_unwritten_count_and_it_is_true():
    """The honesty check.

    MEASURED 2026-10-02: `2 of 40 subtopics written`. If the menu hid the other 38
    it would look finished, and the learner would have no way to know the project
    is 5% done. The number printed must equal the number the registry derives --
    and both are checked against `syllabus`, so the menu cannot drift from the
    ledger by editing one string.
    """
    text = unescape(M.render_index_html())
    total = M._len_subtopics()
    written = len(LESSONS)
    assert f"{written} of {total} subtopics written" in text, text
    assert total == 40, (
        f"the syllabus now has {total} subtopics, so the menu's framing needs "
        "re-reading before this test is trusted again"
    )


def test_the_page_quotes_the_paper_shape_from_the_data_not_from_prose():
    """MEASURED: `-0.10` printed as `-0.1` looks like a different penalty.

    Every figure here comes from `syllabus.PAPER_SHAPE`, so the menu cannot state
    a spec the code does not hold.
    """
    from xat_practice.syllabus import PAPER_SHAPE

    text = unescape(M.render_index_html())
    assert f"{PAPER_SHAPE['total_questions']} questions" in text
    assert f"QA&DI {PAPER_SHAPE['part1']['qa_di']}" in text
    assert f"VA&LR {PAPER_SHAPE['part1']['va_lr']}" in text
    assert f"DM {PAPER_SHAPE['part1']['dm']}" in text
    assert "EXCLUDED" in text, "GK's exclusion from the percentile must be stated"
    assert "-0.10" in text, "the blank penalty must print to two decimals"
    assert "-0.1 " not in text, "-0.1 is the wrong precision for a penalty"
    assert "-0.25" in text


def test_the_page_does_not_claim_the_unbuilt_sections_exist():
    assert "not built" in unescape(M.render_index_html()), (
        "VA&LR and DM are in the paper and NOT in this project. The menu must say "
        "so rather than listing them as if they were available."
    )


def test_the_page_is_ordered_by_measured_topic_weight():
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
# the verb
# ---------------------------------------------------------------------------


def test_serve_with_no_lesson_roots_the_whole_tree():
    """THE layout the UI navigation depends on.

    MEASURED 2026-10-02: with `serve` rooting at ONE lesson directory, the other
    lesson was unreachable without restarting on another port -- and the level tabs
    are useless if switching subtopic means leaving the page.

    Asserted through `serve_root()` rather than `cmd_serve`. The first version drove
    `cmd_serve` with a monkeypatched `make_server`, which replaced the very code
    under test, so the verb returned at its "nothing built" guard and all three
    assertions passed without ever reaching the branch they claimed to check.
    """
    root = cli.serve_root()
    assert root.name == "out", root
    assert root == cli.OUT_ROOT


def test_a_busy_port_is_reported_in_words_not_a_traceback():
    """The most likely thing a learner types twice.

    MEASURED 2026-10-02: a second `serve` raised a bare
    `OSError: [Errno 98] Address already in use` with a six-frame traceback ending
    in `socketserver.py`. The whole point of a one-command flow is that a mistake
    costs no time.

    Driven through the REAL `make_server` -- a monkeypatched one would skip the very
    conversion under test, which is how the previous version of this passed
    vacuously.
    """
    import socket

    held = socket.socket()
    held.bind(("127.0.0.1", 0))
    held.listen(1)
    port = held.getsockname()[1]
    try:
        with pytest.raises(SystemExit) as err:
            cli.make_server(Path("/tmp"), port)
    finally:
        held.close()
    msg = str(err.value)
    assert "already in use" in msg
    assert f"--port {port + 1}" in msg, (
        "the message must say what to DO, not only what happened"
    )
    assert "traceback" not in msg.lower()


def test_serve_rejects_an_unknown_lesson_id(capsys):
    import argparse

    rc = cli.cmd_serve(argparse.Namespace(lesson="lesson-99-nope", port=0))
    err = capsys.readouterr().err
    assert rc == 1
    assert "no lesson" in err
    # The message must list what IS available, or the learner is stuck.
    assert LESSONS[0].lesson_id in err


def test_serve_with_no_lesson_serves_the_whole_tree_and_prints_one_url(
        monkeypatch, capsys, built_fake):
    """`serve` with no `--lesson`: bind, print ONE url, and read nothing from
    stdin.

    The patch target is `cli.OUT_ROOT`, not `xat_practice.bundle.OUT_ROOT`.
    MEASURED while writing this: patching the `bundle` attribute left `cmd_serve`
    using the value bound at import time, so the verb returned at its
    "nothing built" guard and the test passed without reaching the branch.
    """
    import argparse

    seen: dict[str, object] = {}

    class _Server:
        def serve_forever(self) -> None:
            raise KeyboardInterrupt

        def server_close(self) -> None:
            seen["closed"] = True

    monkeypatch.setattr(cli, "OUT_ROOT", built_fake)
    monkeypatch.setattr(cli, "make_server",
                        lambda root, port: seen.update(root=root, port=port)
                        or _Server())

    # NOT pytest.raises: `cmd_serve` catches KeyboardInterrupt itself and returns 0,
    # which is what Ctrl-C should do. MEASURED: the first version expected the
    # exception to propagate and failed with "DID NOT RAISE", which reads as "the
    # branch did not run" when it did.
    rc = cli.cmd_serve(argparse.Namespace(lesson=None, port=8000))
    assert rc == 0

    out = capsys.readouterr().out
    assert seen["root"] == built_fake, seen
    assert "http://127.0.0.1:8000/" in out
    assert out.count("http://127.0.0.1:8000/") == 1, (
        f"one url, not a list of commands -- a second command is exactly what the "
        f"owner did not want:\n{out}"
    )
    assert "choose" not in out.lower(), f"it must not prompt: {out}"
    assert seen.get("closed") is True, "the socket must be released on Ctrl-C"
    assert "\n" in out.strip(), "it must actually print something"


def test_serve_with_no_lesson_and_nothing_built_says_so(monkeypatch, capsys,
                                                        tmp_path):
    import argparse

    empty = tmp_path / "unbuilt"
    empty.mkdir()
    monkeypatch.setattr(cli, "OUT_ROOT", empty)
    rc = cli.cmd_serve(argparse.Namespace(lesson=None, port=0))
    assert rc == 1
    err = capsys.readouterr().err
    assert "nothing built" in err
    assert "uv run xat-practice build" in err, "the fix must be in the message"
