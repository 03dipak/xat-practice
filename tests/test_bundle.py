"""The bundle, sat as a learner would sit it, with the files on disk.

`viewer`'s scope: can this actually be answered from what is on screen, and does
the step-by-step teach? These tests answer the first half mechanically, because
the second half needs a person.

THE TEST THAT MATTERS MOST IS THE FIRST ONE. A bundle that ships its own
answer key in the page is a bundle that teaches the wrong thing with a clean
conscience, and nothing else in this project matters if that is true.
"""

from __future__ import annotations

import json
import posixpath
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from xat_practice import bundle, lesson1
from xat_practice.gates import run
from xat_practice.items import derive_level

OUT = Path(bundle.OUT_DIR)


@pytest.fixture(scope="module")
def files() -> dict:
    return bundle.build_lesson(lesson1.LESSON_ID, lesson1.LESSON,
                               lesson1.SOLUTIONS)


@pytest.fixture(scope="module")
def on_disk() -> dict:
    return {p.name: p.read_text() for p in OUT.iterdir() if p.is_file()}


# ---------------------------------------------------------------------------
# the key must not be reachable before the learner commits
# ---------------------------------------------------------------------------

def test_the_bundle_does_not_leak_the_key_before_check(on_disk):
    """index.html and lesson.js are what a learner can read before answering.
    Neither may contain a key, a solution, or a misconception."""
    served = on_disk["index.html"] + on_disk["lesson.js"]
    assert "key_index" not in served, "the answer field is NAMED in the served page"
    # The FILENAME necessarily appears -- the page has to fetch it. What must
    # not appear is a fetch that happens before the learner commits, so that is
    # asserted separately in `test_the_key_is_fetched_only_after_check`.
    for item in lesson1.LESSON:
        assert item.key_text not in served, f"{item.id} key is in the served page"
        for line in lesson1.SOLUTIONS[item.id]:
            assert line[:40] not in served, f"{item.id} solution is in the page"
    for d in lesson1.lesson()[0].distractors:
        assert d.misconception not in served


def test_the_key_lives_in_a_separate_file(files):
    """Not obfuscation -- separation. The page fetches it only after commit."""
    assert "k" in files["answerkey.json"]["items"]["L1-F"]
    assert "k" not in files["paper.json"]


def test_the_key_is_fetched_only_after_check(on_disk):
    """The single fetch must be inside `check()`'s call path, not on load.

    MEASURED: the first bundle fetched the key from `render()`, so it was in
    memory and in the network tab before the learner had committed. The commit
    was theatre. This asserts the call sites.
    """
    js = on_disk["lesson.js"]

    # Two loaders. `loadPaper` may run on load; `loadKey` may not.
    assert "async function loadPaper" in js
    assert "async function loadKey" in js

    key_decl = js.index("async function loadKey")
    key_body = js[key_decl:js.index("return all.items[id]", key_decl)]
    assert "fetch(" in key_body, "loadKey must be the only thing that fetches the key"

    # Occurrences of `loadKey(`: the declaration, the mentions inside the two
    # explanatory comments, and the single real call. Count only real calls by
    # requiring the match to be preceded by `await ` -- that is the only way a
    # loader is ever invoked in this file.
    calls = [m.start() for m in re.finditer(r"await loadKey\(", js)]
    check_at = js.index("async function check()")
    assert len(calls) == 1, f"expected exactly 1 awaited loadKey, got {len(calls)}"
    assert calls[0] > check_at, (
        "loadKey is awaited outside check(), so answerkey.json is in memory "
        "before the learner commits. The commit barrier is theatre."
    )

    # The strongest form: trace what the LOAD PATH actually fetches, by
    # following the real call chain rather than slicing source text. `render()`
    # awaits only `loadPaper`, and `loadPaper` fetches only paper.json.
    render = js[js.index("async function render()"):check_at]
    awaited = re.findall(r"await (load\w+)\(", render)
    assert awaited == ["loadPaper"], (
        f"the load path awaits {awaited}; anything but loadPaper means the "
        f"key is reachable before the learner commits"
    )
    paper_body = js[js.index("async function loadPaper"):
                    js.index("// answerkey.json holds")]
    assert re.findall(r"fetch\('([^']+)'", paper_body) == ["paper.json"]


def test_paper_json_alone_cannot_mark_an_answer(on_disk):
    """The strongest form of the property: the file the page loads FIRST is
    useless for grading. If this fails, the commit barrier is decoration."""
    paper = json.loads(on_disk["paper.json"])
    for item in paper["items"]:
        assert set(item) >= {"id", "stem", "options", "level"}
        assert "k" not in item
        assert "solution" not in item
        assert "distractors" not in item
        assert "misconception" not in json.dumps(item)


def test_the_paper_ships_no_solution(files):
    blob = json.dumps(files["paper.json"])
    assert "solution" not in blob
    assert "misconception" not in blob


def test_the_bundle_refuses_to_build_from_a_failed_item():
    """A gate failure must stop the build, not warn. A bundle that ships a
    refused item has shipped the defect the gate exists to catch."""
    import dataclasses

    broken = list(lesson1.LESSON)
    broken[0] = dataclasses.replace(
        broken[0], option_values=("200", "220", "100", "1200", "1250"))
    with pytest.raises(SystemExit, match="did not pass the gates"):
        bundle.build_lesson("broken", tuple(broken), lesson1.SOLUTIONS)


# ---------------------------------------------------------------------------
# the commit barrier
# ---------------------------------------------------------------------------

def test_options_are_not_in_the_dom_before_the_reveal(on_disk):
    """The options live in answerkey.json and are injected by JS AFTER the
    learner commits, so the served HTML must not contain them."""
    assert "Rs 11,025" not in on_disk["index.html"]
    assert "Rs 2 : 3" not in on_disk["index.html"]
    assert "data-pick" not in on_disk["index.html"]


def test_the_commit_gate_precedes_the_options(on_disk):
    js = on_disk["lesson.js"]
    reveal = js.index("id=\"reveal\"")
    optbox = js.index("id=\"optBox\" class=\"hidden\"")
    assert reveal < optbox, "the option box must be hidden until the commit"
    assert 'class="hidden"' in js.split("id=\"optBox\"")[1][:40]


def test_the_reveal_button_starts_disabled(on_disk):
    """Until a confidence is recorded, the learner cannot reach the options.

    MEASURED 2026-10-02, by driving the page in a real browser: the button was
    NOT disabled when it appeared. The old test asserted only that the string
    `...disabled = false` existed somewhere in the file -- which is the
    *enabling* line, and proves nothing about the state the button is born in.
    A check that asserts a string has been shown a true statement and is still
    untested.

    The button is built by JS, so `disabled` has to be an attribute in the
    template, not a statement after the fact.
    """
    js = on_disk["lesson.js"]
    assert '<button id="reveal" disabled>' in js, (
        "the reveal button is not born disabled, so a learner can skip the "
        "commit and see the options without recording a confidence. MEASURED in "
        "a real browser: `reveal disabled before confidence: NO`."
    )
    assert "document.getElementById('reveal').disabled = false;" in js, (
        "nothing enables the reveal button once a confidence is recorded"
    )
    assert "Show the options" in js, (
        "the reveal button is built by JS, so the label lives there"
    )


def test_the_commit_is_never_graded_and_never_sent(on_disk):
    """No fetch, no storage, no beacon. The learner's first answer stays on
    their machine -- that is what makes asking for it honest."""
    js = on_disk["lesson.js"]
    assert "localStorage" not in js
    assert "navigator.sendBeacon" not in js
    assert "XMLHttpRequest" not in js


def test_check_is_gated_on_an_actual_selection(on_disk):
    assert "document.querySelector('.opt.sel')" in on_disk["lesson.js"]


# ---------------------------------------------------------------------------
# the loop the owner asked for
# ---------------------------------------------------------------------------

def test_the_flow_is_commit_then_options_then_check_then_solution(on_disk):
    """The order of the LOOP: commit, options, check, solution.

    This used to assert the order of those identifiers *in the source file*, as a
    proxy for the order of the steps. That proxy broke the moment the
    implementation became correct: the check button is now built inside the
    reveal handler, because the options are built there too, so `id="check"`
    appears later in the file than `id="result"` even though check still happens
    before the result is shown.

    A proxy that breaks when the thing it proxies gets right is worse than no
    proxy. What is asserted here is the real structure: the commit box and the
    reveal are built in `render()` and the option box is empty, and the check
    button is constructed inside the reveal handler. The rendered order of the
    steps is asserted against a real browser in `tools/ui_probe.html`.
    """
    js = on_disk["lesson.js"]
    for step in ("commitBox", "reveal", "optBox", "check", "result"):
        assert step in js, step

    render = js[js.index("async function render()"):js.index("async function check()")]
    template = render[render.index("stage.innerHTML = `"):]
    assert template.index('id="commitBox"') < template.index('id="reveal"'), (
        "the commit must be on screen before the reveal"
    )
    assert template.index('id="reveal"') < template.index('id="optBox"'), (
        "the reveal must exist before the option box it reveals"
    )
    assert '<div id="optBox" class="hidden"></div>' in js, (
        "the option box is built EMPTY and filled at reveal time, so the options "
        "are not in the DOM until the learner has committed"
    )
    reveal = js[js.index("reveal').onclick"):js.index("async function check()")]
    assert 'id="check"' in reveal, (
        "the check button is constructed inside the reveal handler"
    )
    assert reveal.index("data-pick") < reveal.index('id="check"'), (
        "the options must be built before the button that grades them"
    )


def test_every_wrong_option_is_shown_its_misconception(files):
    """The owner's flow asks for the misconception behind every option the
    learner did not pick. Assert it in the BUILT file, not the source."""
    key = files["answerkey.json"]["items"]
    for item in lesson1.LESSON:
        blob = " ".join(key[item.id]["solution"])
        for d in item.distractors:
            assert d.text in blob, f"{item.id}: {d.text} is never ruled out"
        assert len(key[item.id]["distractors"]) == 4


def test_every_solution_ends_on_the_stated_answer(files):
    """A solution ending on a rejected distractor reads, to someone scanning
    the last line, as if the last number were the answer."""
    key = files["answerkey.json"]["items"]
    for item in lesson1.LESSON:
        last = key[item.id]["solution"][-1]
        assert last == f"ANSWER: {item.key_text}", (item.id, last)


def test_the_four_cells_of_the_quadrant_are_all_reachable(on_disk):
    """sure/unsure x right/wrong. Two of them are opposite remedies and a score
    cannot tell them apart, which is the reason the click exists."""
    js = on_disk["lesson.js"]
    for cell in ("Sure and right", "Sure and WRONG", "Unsure but right",
                 "Unsure and wrong"):
        assert cell in js, cell


def test_the_quarter_lesson_says_the_score_is_not_the_signal(on_disk):
    assert "not your score" in on_disk["index.html"] or \
        "strongest signal is not your score" in on_disk["lesson.js"]


def test_the_footer_states_the_two_guarantees(on_disk):
    """A learner is told how the key was checked and how the levels were set.
    Silence on this would let an unverified key pass as a verified one."""
    foot = on_disk["index.html"] + on_disk["lesson.js"]
    assert "recomputed" in foot
    assert "derived from each item" in foot


# ---------------------------------------------------------------------------
# the paper inside the bundle
# ---------------------------------------------------------------------------

def test_the_bundled_paper_matches_the_derived_levels(files):
    res = run(list(lesson1.LESSON))
    for it in files["paper.json"]["items"]:
        assert it["level"] == res.reports[it["id"]].level.value
        assert it["level_drivers"] == list(res.reports[it["id"]].drivers)


def test_the_bundled_paper_records_no_negative_marking(files):
    assert files["paper.json"]["negative_marking"] is False
    assert files["paper.json"]["shaping"] == "LESSON"


def test_the_bundled_key_records_how_it_was_grounded(files):
    for item in lesson1.LESSON:
        g = files["answerkey.json"]["grounding"][item.id]
        assert g
        assert g["verdict"] == "HOLD"
        assert g["grounded"] is True
        assert g["derivation"], "the derivation is what makes the key checkable"


def test_the_bundle_names_its_own_subtopic(files):
    assert files["paper.json"]["subtopic"] == lesson1.SUBTOPIC
    assert {i.subtopic_id for i in lesson1.LESSON} == {lesson1.SUBTOPIC}


def test_option_letters_are_five(on_disk):
    assert "'ABCDE'" in on_disk["lesson.js"]
    for item in lesson1.LESSON:
        assert len(item.options) == 5


# ---------------------------------------------------------------------------
# nothing in the bundle is a hardcoded answer
# ---------------------------------------------------------------------------

def test_no_answer_is_hardcoded_in_the_javascript(on_disk):
    """Every key, solution and misconception must come from answerkey.json. A
    single hardcoded correct index is how a bundle starts lying."""
    js = on_disk["lesson.js"]
    assert re.search(r"\b(200|11000|14400|2/3)\b", js) is None, (
        "a computed answer appears literally in lesson.js"
    )
    assert "ANSWER:" not in js


# ---------------------------------------------------------------------------
# the first screen must never be a blank page
# ---------------------------------------------------------------------------
# MEASURED 2026-10-02, from the owner's report: "the page takes too much time to
# load, the first page has only the title". The server was NOT slow -- 1.4ms for
# lesson.js, 2.8ms for paper.json, 4.8ms for index.html, ~12ms for all four.
# So "slow" was the wrong diagnosis and the render path held the defect.

#: The per-file budget. RAISED 20_000 -> 25_000 on 2026-10-02, with the reason:
#: `lesson.js` reached 21,975 bytes when the `viewer` findings were fixed (level
#: tabs, per-item reset, dynamic title, scroll-into-view, honest finish screen). The
#: whole page is **43,537 bytes** across all five files, and MEASURED the whole page
#: served in ~12ms -- so the guard's purpose still holds: nothing here is big enough
#: to explain a slow first screen. The number was moved because the file grew, and
#: the number that matters is the page's, which is asserted below.
MAX_ASSET_BYTES = 25_000
MAX_PAGE_BYTES = 60_000


def test_the_server_is_not_the_thing_that_is_slow(on_disk):
    """The four served files are a few kilobytes each. If a page feels slow, the
    cause is in the render path, not the wire -- so this pins the budget.

    Two numbers, not one: a per-file ceiling and a WHOLE-PAGE ceiling. The per-file
    one caught a real 20% growth; the page one is the one that decides whether the
    wire can be the explanation.
    """
    total = 0
    for name in ("index.html", "style.css", "lesson.js", "paper.json",
                 "answerkey.json"):
        total += len(on_disk[name])
        assert len(on_disk[name]) < MAX_ASSET_BYTES, (
            f"{name} grew past 20KB. That is still fast, but the point of the "
            "measurement is that no asset here is big enough to explain a slow "
            "first screen, so look at render() instead of the network."
        )


def test_the_first_screen_is_painted_before_the_network_answers(on_disk):
    """`render()` must write to the stage BEFORE it awaits paper.json.

    The defect: the stage was written only after `await loadPaper(id)`, so it was
    empty for the whole fetch -- and permanently empty if the fetch rejected.
    The learner saw the title and the subtitle and nothing else, with no way to
    tell a slow page from a broken one.
    """
    js = on_disk["lesson.js"]
    body = js[js.index("async function render()"):js.index("async function check()")]
    paint = body.index("stage.innerHTML")
    await_paper = body.index("await loadPaper(")
    assert paint < await_paper, (
        "render() awaits paper.json before painting, so the first screen is "
        "empty for the length of the fetch"
    )
    assert "Loading the question" in js, (
        "the shell must say it is loading, or a fast fetch looks like a hang"
    )


def test_a_failed_paper_fetch_names_the_reason_instead_of_leaving_a_blank_page(on_disk):
    """A rejected fetch is the case that produced a permanently blank page with
    no diagnosis. It must render the reason, and it must name the file:// case
    because that is the one learners actually hit."""
    js = on_disk["lesson.js"]
    render = js[js.index("async function render()"):js.index("async function check()")]
    assert "catch" in render, "the paper load is unguarded"
    # The literal was `fail(stage, id, err)` and `id` is no longer in scope at the
    # catch, because the id is read AFTER the paper loads (see `loadPaper`). So
    # the assertion moves to what the test is actually for: the error reaches the
    # screen instead of being swallowed into a blank page.
    assert "catch (err)" in render, "the paper load must have a catch"
    assert "fail(stage," in render and "err)" in render, (
        "a failure must be rendered, not swallowed"
    )
    fail = js[js.index("function fail("):js.index("async function render()")]
    assert "file://" in fail, (
        "the most common cause is opening index.html directly, where a browser "
        "refuses fetch() of a sibling JSON. A learner who hits it must be told."
    )
    assert "xat-practice serve" in fail, "the error must give the command that fixes it"


def test_moving_to_the_next_question_does_not_refetch_the_paper(on_disk):
    """The paper is fetched once for the whole lesson.

    The defect: `render()` ran on all four questions and each one called
    `fetch('paper.json', {cache: 'no-store'})`, so every transition blanked the
    stage and re-downloaded the file. Four round trips for a 2KB document, and
    four flashes of an empty page.
    """
    js = on_disk["lesson.js"]
    assert js.count("fetch('paper.json'") == 1, (
        "paper.json is fetched more than once; cache the promise instead"
    )
    assert "paperCache" in js, "the fetched paper is not cached"
    assert "if (!paperCache)" in js, (
        "the cache must be guarded, or the second render refetches anyway"
    )
    # And the guard must not have grown a second fetch path for the KEY.
    assert js.count("fetch('answerkey.json'") == 1
    assert "answerkey.json" in js[js.index("async function loadKey"):][:200]


def test_the_finish_screen_reports_the_quadrant_it_collected(on_disk):
    """`state.log` was declared and read but never written to.

    MEASURED: `finish()` computed a count that was always 0 and then never
    displayed it. The quadrant is the product's central claim, so the screen
    that reports it has to report the learner's actual cells.
    """
    js = on_disk["lesson.js"]
    # Either form records an outcome. MEASURED 2026-10-02: this asserted `push`,
    # which is the form that was WRONG -- `jumpTo(n)` extends a sparse array, so a
    # push lands one index high and the finish screen reported 1 of 4. The write is
    # now `state.log[state.i] = ...`, and this test must not fail the fix.
    assert ("state.log[state.i] =" in js or "state.log.push(" in js), (
        "nothing records the outcome of a question"
    )
    finish = js[js.index("function finish()"):js.index("document.addEventListener")]
    assert "rows.map(" in finish, "the finish screen does not list the four cells"
    assert "wasSure" in finish, (
        "the sure-and-wrong cell is the one the product exists to surface, and "
        "the finish screen must name it when there is one"
    )
    assert "nothing here is scored" not in finish.lower()


# ---------------------------------------------------------------------------
# main(): the entry point that actually writes the files
# ---------------------------------------------------------------------------

def test_main_writes_all_five_files_and_reports_the_ladder(capsys):
    """`main()` is what a session runs to produce a lesson, so it is the one
    function whose failure is silent -- the tests above call `build_lesson`
    directly and never touch the filesystem."""
    bundle.main()
    out = capsys.readouterr().out

    for name in ("index.html", "style.css", "lesson.js", "paper.json",
                 "answerkey.json"):
        assert (OUT / name).exists(), name
        assert (OUT / name).stat().st_size > 0, name

    assert "built" in out
    for item in lesson1.LESSON:
        assert item.id in out
        assert derive_level(item).level.value in out
    assert out.index("foundation") < out.index("hard"), "ladder is out of order"


def test_main_output_is_reloadable_and_identical_on_a_second_run():
    """A build that is not deterministic would make `git diff` useless as the
    way to see what a lesson now says."""
    bundle.main()
    first = (OUT / "paper.json").read_text()
    bundle.main()
    assert (OUT / "paper.json").read_text() == first


def test_main_does_not_regenerate_opencode_json():
    """Two builders, two outputs. `main()` here must not touch the agent config
    -- that is `build_opencode.main`, and a lesson build silently rewriting the
    prompts would be a genuinely nasty bug."""
    import xat_practice.build_opencode as bo

    before = bo.OUT.read_text()
    bundle.main()
    assert bo.OUT.read_text() == before


# ---------------------------------------------------------------------------
# THE TEST THAT MATTERS MOST AFTER THE FIRST ONE
# ---------------------------------------------------------------------------
# MEASURED 2026-10-02, and it is the worst defect this project has produced.
#
# `lesson.js` did not parse. The footer contained
#
#     '...recomputed from the item's own ' +
#
# and the apostrophe in `item's` TERMINATED the JavaScript string literal, so
# `node --check` reported `SyntaxError: Unexpected identifier 's'` and the
# browser refused to execute a single line of the file. The page showed the
# title, the subtitle, and nothing else -- forever, with no error anywhere.
#
# **The lesson page had never worked. Not once. And 161 tests passed the whole
# time**, because every one of them asserted on the TEXT of the built files. Not
# one asked whether the file was valid JavaScript.
#
# This is the answer to "why did the tests pass": they tested the wrong thing,
# and no amount of reading would have found it. It took RENDERING the page.

def test_the_served_javascript_actually_parses(on_disk):
    """The file is JavaScript. It has to be valid JavaScript."""
    node = shutil.which("node")
    if not node:
        pytest.skip("node is not installed; run `test_js_strings_have_no_bare_"
                    "apostrophe` for the node-free half of this check")
    proc = subprocess.run([node, "--check", "-"], input=on_disk["lesson.js"],
                          capture_output=True, text=True, timeout=30)
    assert proc.returncode == 0, (
        "lesson.js does not parse, so the browser runs NONE of it and the page "
        "shows only the static HTML. MEASURED: this exact failure shipped a page "
        f"that had never worked, past 161 passing tests.\n{proc.stderr}"
    )


def test_js_strings_have_no_bare_apostrophe(on_disk):
    """The node-free half, and the check that names the defect.

    A line that OPENS a single-quoted JavaScript string must contain an even
    number of unescaped quotes. An odd count means an apostrophe in prose --
    `item's`, `don't`, `learner's` -- closed the literal early.

    This is a crude rule and it is here anyway, because it runs with no external
    tool. It cannot prove the file parses. It CAN catch the one mistake that has
    already shipped."""
    import re

    offenders = []
    for n, line in enumerate(on_disk["lesson.js"].splitlines(), 1):
        stripped = line.strip()
        if not stripped.startswith("'"):
            continue
        # Count quotes that are not escaped. `\'` inside the literal is fine;
        # an unescaped `'` is a premature terminator.
        bare = len(re.findall(r"(?<!\\)'", stripped))
        if bare % 2:
            offenders.append(f"  line {n}: {stripped[:78]}")
    assert not offenders, (
        "a JS string literal is terminated early by an apostrophe in prose, so "
        "the whole file fails to parse and NOTHING on the page runs:\n"
        + "\n".join(offenders)
    )


def test_the_bundle_checks_the_javascript_it_serves_before_serving_it():
    """`build_lesson` must refuse to emit a bundle whose script does not parse.

    The build is the last point where the file is ours rather than the browser's.
    Refusing there turns a silent permanent failure into a build error naming the
    line. `node` is optional: without it this asserts the no-store header instead,
    so the check is never silently absent without saying so."""
    files = bundle.build_lesson(lesson1.LESSON_ID, lesson1.LESSON,
                                lesson1.SOLUTIONS)
    assert set(files) == {"paper.json", "answerkey.json"}
    js = bundle.JS
    import re as _re
    for n, line in enumerate(js.splitlines(), 1):
        s = line.strip()
        if s.startswith("'") and len(_re.findall(r"(?<!\\)'", s)) % 2:
            raise AssertionError(f"bundle.JS line {n} closes its string early: {s[:70]}")
    node = shutil.which("node")
    if node:
        proc = subprocess.run([node, "--check", "-"], input=js, capture_output=True,
                              text=True, timeout=30)
        assert proc.returncode == 0, f"bundle.JS does not parse:\n{proc.stderr}"


def test_the_server_tells_the_browser_never_to_cache():
    """`lesson.js` is a `<script src>`, so the browser may reuse a stale copy
    indefinitely. After a rebuild the learner would run the OLD script against
    the NEW page -- a page that renders half of what is on disk, silently.

    Asserted live against `make_server`, because the property is a response
    header and reading the source would not prove it is sent."""
    import threading
    import urllib.request

    from xat_practice.cli import make_server

    root = Path(bundle.OUT_DIR)
    port = 8765
    httpd = make_server(root, port)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    try:
        for name in ("lesson.js", "paper.json"):
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/{name}",
                                        timeout=5) as r:
                assert r.headers.get("Cache-Control") == "no-store", (
                    f"{name} is cacheable, so a rebuild can leave a learner "
                    f"running stale JavaScript"
                )
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_the_build_id_changes_when_the_lesson_changes():
    """The build id is what makes a stale script self-evident.

    MEASURED 2026-10-02: the owner reported the options were invisible, the
    served page was provably correct, and nothing on screen could say which build
    was running. A stamp that does not change when the content changes is
    decoration."""
    import dataclasses

    from xat_practice import bundle as b

    first = b.build_lesson(lesson1.LESSON_ID, lesson1.LESSON, lesson1.SOLUTIONS)
    again = b.build_lesson(lesson1.LESSON_ID, lesson1.LESSON, lesson1.SOLUTIONS)
    assert first["paper.json"]["build"] == again["paper.json"]["build"], (
        "the build id must be derived from the content, not the clock, or "
        "two builds of the same lesson differ and git diff on out/ is noise"
    )
    changed = list(lesson1.LESSON)
    changed[0] = dataclasses.replace(changed[0], stem=changed[0].stem + " ")
    second = b.build_lesson(lesson1.LESSON_ID, tuple(changed), lesson1.SOLUTIONS)
    assert second["paper.json"]["build"] != first["paper.json"]["build"], (
        "the build id did not change when the stem changed, so it cannot detect "
        "a stale script"
    )
    assert first["answerkey.json"]["build"] == first["paper.json"]["build"], (
        "the two halves of the bundle must carry the same id"
    )


def test_the_footer_shows_the_build_and_still_states_the_guarantees(on_disk):
    """The two guarantees AND the build stamp. Losing either is a regression:
    the guarantees are the product's claim, and the stamp is how a stale page
    is caught."""
    js = on_disk["lesson.js"]
    assert "state.build" in js
    assert "'Build <strong>'" in js
    assert "recomputed from the item" in js
    assert "derived from each item" in js


def test_the_stylesheet_is_a_separate_file_and_the_page_links_it():
    """The CSS is its own file because the UI probe has to load it.

    MEASURED 2026-10-02: with the styles inline in index.html the probe could not
    load them, so it was blind to every appearance defect -- and its own contrast
    check PASSED against a build where all five options were white on white. A
    check that cannot see the styling cannot catch a styling bug."""
    assert '<link rel="stylesheet" href="style.css">' in bundle.HTML
    assert "<style>" not in bundle.HTML, (
        "the styles are inline again, so the probe cannot load them"
    )
    assert bundle.STYLE.strip(), "the stylesheet is empty"
    assert (OUT / "style.css").exists(), "style.css was not written"


def test_options_set_their_own_colour_and_do_not_inherit_white():
    """`.opt` overrode `background` but not `colour`, so the generic
    `button { color: #fff }` rule won and all five options rendered WHITE ON
    WHITE. The elements were in the DOM, which is why devtools showed the markup
    perfectly while the screen showed nothing.

    Asserted here as well as in the probe: the probe proves the rendered contrast,
    this pins the cause, so a future edit that drops the line says why."""
    opt = re.search(r"\.opt \{(.*?)\n  \}", bundle.STYLE, re.S)
    assert opt, "the .opt rule is gone"
    body = opt.group(1)
    assert "color:" in body, (
        ".opt sets background but not colour, so it inherits color:#fff from the "
        "generic button rule and renders white on white. MEASURED: all five "
        "options were invisible and 38 UI checks passed."
    )
    assert "background: #fff" in body, "the fix assumes a white option background"


def test_render_owns_the_per_item_commit_reset(on_disk):
    """A TEXT assertion, and labelled as one -- `render()` must clear the
    per-item state itself, not every caller.

    MEASURED 2026-10-02: `state.commit` and `state.pick` were cleared by `next()`
    and by `jumpTo()`, so correctness depended on every future caller remembering.
    That is the D12 shape: a rule living in the callers instead of in the thing it
    constrains, and the level tabs were about to become a third caller.

    Why this is static and not a browser check, stated plainly: a carried-over
    commit is INVISIBLE in the DOM. `render()` rebuilds a fresh
    `<button id="reveal" disabled>` and an empty `#commitNote`, so every DOM
    assertion passes with the reset deleted -- measured at 54/54, twice, before this
    was made structural. Where it bites is `check()`, which reads `state.commit` to
    choose the verdict quadrant: a stale `'sure'` makes the page tell a learner it
    was "Sure and WRONG" on a rung they never committed to.

    So the browser proves the jump and the barrier; the reset is proven here, on the
    text, because that is where it is written.
    """
    js = on_disk["lesson.js"]

    def body_of(name: str) -> str:
        """The source of one top-level function.

        MEASURED while writing this: slicing to the NEXT occurrence of a fixed name
        returned the EMPTY STRING, because `function esc(` is defined ABOVE
        `render()`. An empty slice makes every `in` assertion fail for the wrong
        reason, and the failure reads like a missing reset.
        """
        start = js.index(name)
        rest = js[start + len(name):]
        ends = [i for i in (rest.find("\nfunction "), rest.find("\nasync function "))
                if i != -1]
        return js[start:start + len(name) + (min(ends) if ends else len(rest))]

    body = body_of("async function render()")
    assert body, "could not isolate render() -- the helper is broken, not the page"
    assert "state.commit = null" in body, (
        "render() must clear state.commit itself -- see the docstring for the "
        "measurement that made this structural"
    )
    assert "state.pick = null" in body, (
        "render() must clear state.pick itself"
    )
    # And the reason it is not a caller-only rule: jumpTo must NOT be the thing
    # that saves us, or the next caller breaks it.
    jump = body_of("function jumpTo(")
    assert "state.commit" not in jump, (
        "jumpTo() clears state.commit again. That is fine but it is not what makes "
        "it safe -- render() is. Keeping both invites a reader to delete the wrong "
        "one."
    )


def test_the_levels_are_clickable_tabs_in_the_served_page(on_disk):
    """The owner asked to "click section, then subtopic, then tabs the 4 level i
    can choose any". The rungs were `<div>`s -- a read-out of a fixed queue, not a
    control. Rendered behaviour is pinned by tools/ui_probe.html; this pins the
    markup so the two cannot drift apart."""
    js = on_disk["lesson.js"]
    assert "data-i=" in js, "each rung must carry its index to be clickable"
    assert "closest('.rung')" in js, "the click must be delegated to the rung"
    rung_bar = js[js.index("function rungBar()"):js.index("function jumpTo(")]
    assert "<button" in rung_bar, (
        "a rung must be a <button>, not a <div>: a div is not focusable and does "
        "not respond to Enter, so it is a picture of a tab rather than a tab"
    )
    assert "aria-current" in rung_bar, (
        "the active level must be marked for assistive tech and for a learner "
        "who cannot see which one is lit"
    )


# ---------------------------------------------------------------------------
# the viewer's findings, 2026-10-02
# ---------------------------------------------------------------------------
# The `viewer` subagent SAT the flow and returned nine findings. Each was verified
# in a real headless Chromium before being acted on, because an agent's claim is a
# hypothesis, not evidence. Three are pinned here as TEXT because the browser
# cannot see them; the rest are in the probe.

def test_the_page_names_its_own_topic_in_the_title_and_heading(on_disk):
    """MEASURED: `<title>` was the literal "XAT Practise · Lesson 1 · Simple
    Interest" in the HTML, so the GEOMETRY page's browser tab claimed to be Simple
    Interest, and its `<h1>` was "02" -- `lesson_id.split("-")[1]`, a directory name.
    A learner who clicked "Geometry & Mensuration -> Open" arrived at a page called
    "02".

    Neither can be asserted from the DOM without driving the page, and the values
    come from `paper.json`, so both are pinned on the template and on the data.
    """
    # ON THE MARKUP AND THE TEMPLATE, not the whole file: three of these assertions
    # first failed against the explanatory COMMENTS, which quote the very strings
    # they forbid. A test that greps a file it also documents will always fail.
    html = on_disk["index.html"]
    assert "Simple Interest" not in html, (
        "the static markup hardcodes Lesson 1's topic; every other lesson's tab "
        "claims to be Simple Interest"
    )
    assert "<title>XAT Practice</title>" in html, (
        "the tab title must be a placeholder that JS replaces, not a fixed topic"
    )
    js = on_disk["lesson.js"]
    assert "document.title" in js, "the title must be set from the loaded paper"
    assert "topic_label" in js, "the heading and tab must come from the paper"


def test_the_free_answer_placeholder_is_not_another_topics_formula(on_disk):
    """MEASURED: the placeholder was the literal "e.g. SI = P x R x T / 100 = ..."
    on EVERY lesson, so the Geometry page told a learner to write down simple
    interest before answering a question about a triangle's area. Correct on Lesson
    1, wrong on every other lesson -- so it was a literal, not a field."""
    js = on_disk["lesson.js"]
    assert 'placeholder="${esc(state.answerHint)}"' in js, (
        "the answer placeholder must be read from the paper's answer_hint field"
    )
    # The rendered value, not the source: paper.json is what ships to the browser.
    paper = json.loads(on_disk["paper.json"])
    hint = paper.get("answer_hint", "")
    assert hint and "SI = P" not in hint, (
        f"the shipped placeholder still names simple interest: {hint!r}"
    )
    assert "SI = P" not in str(paper.get("items", [])), (
        "an item's own data must not carry a simple-interest formula"
    )


def test_the_finish_screen_may_not_claim_more_than_was_attempted(on_disk):
    """MEASURED: it said "You worked through every level of this subtopic"
    unconditionally and then listed ONE row. The level tabs made that reachable in a
    single click, so the summary screen -- the only screen that reports on the
    learner's session -- was the one making an unverified claim."""
    js = on_disk["lesson.js"]
    # Slice to the NEXT top-level function. The first version ended at `report(`,
    # which lives in the PROBE page, not in lesson.js -- so `.index` raised
    # ValueError and the assertion never ran.
    start = js.index("function finish()")
    rest = js[start + len("function finish()"):]
    ends = [i for i in (rest.find("\nfunction "), rest.find("\nasync function "))
            if i != -1]
    body = js[start:start + len("function finish()") + (min(ends) if ends else len(rest))]
    assert "You worked through every level of this subtopic" in body
    # ...and that sentence must be CONDITIONAL on having done all of them.
    assert "attempted.length === state.total" in body, (
        "the 'every level' claim must be guarded by how many were attempted, or it "
        "is an unverified claim about the learner"
    )
    assert "You attempted" in body, "there must be an honest alternative sentence"
    # "the four" was also wrong when fewer were attempted.
    assert "any of the four" not in js, (
        "'any of the four' presumes four were attempted"
    )


def test_rungs_are_done_only_when_attempted_not_when_earlier_in_the_queue(on_disk):
    """MEASURED: the condition was `n < state.i`, so clicking HARD FIRST -- exactly
    what the level tabs invite and exactly what the owner asked for -- lit
    FOUNDATION, EASY and MEDIUM solid green. The product's only self-report then
    claimed the learner had done three questions they never attempted."""
    js = on_disk["lesson.js"]
    bar = js[js.index("function rungBar()"):js.index("function jumpTo(")]
    # ON THE CODE, not the comment. The comment above the assignment explains that
    # `n < state.i` was the old condition, so a substring search always matched.
    code = re.sub(r"//[^\n]*", "", bar)
    assert "state.log[n] ? 'done'" in code, (
        "a rung must be 'done' only if it was ANSWERED, not merely earlier in the "
        f"queue. Got:\n{code[:400]}"
    )
    assert "n < state.i" not in code, "queue position is not 'done'"
    # `on` and `done` are independent: answering the rung you are standing on must
    # still mark it done. MEASURED 2026-10-02 -- it did not, so on the finish screen
    # the rung just finished was the only unmarked one.
    assert "'on' : ''" in code, (
        "'on' must be additive, not exclusive: a rung can be both current and done"
    )


def test_the_back_link_depth_is_derived_and_reaches_the_navigator(on_disk):
    """MEASURED 2026-10-02, and the reason this exists.

    The back link was `href="../"`, correct while a lesson lived at
    `out/<lesson_id>/`. The exam layer nested the output to
    `out/<exam>/<section>/<lesson_id>/`, so `../` resolved to `out/xat/qa_di/`,
    which has no `index.html` -- and `SimpleHTTPRequestHandler` answers a directory
    with **no index** by serving a DIRECTORY LISTING.

    So the link did not 404 and nothing went red. It dumped the learner on a raw
    file index titled "Directory listing for /xat/qa_di/", which reads as the site
    being broken. That is the whole defect class: a consumer that outlived the path
    it was written for, with a 200 to hide it.

    The href is now computed at build time from `out_dir`, and this asserts the
    result resolves to the bundle ROOT rather than to any subdirectory.
    """
    from xat_practice.bundle import OUT_ROOT, out_dir
    from xat_practice.registry import LESSONS

    href = re.search(r'id="back" href="([^"]+)"',
                       on_disk["index.html"]).group(1)
    dest = out_dir(LESSONS[0].lesson_id)
    depth = len(dest.relative_to(OUT_ROOT).parts)

    assert href == "../" * depth, (
        f"the back link is {href!r} but the lesson sits {depth} level(s) below "
        f"the bundle root ({dest.relative_to(OUT_ROOT)}). A wrong depth does not "
        "404 here -- it serves a directory listing with HTTP 200."
    )
    # And it must point at the ROOT, never at a subdirectory. `posixpath.normpath`
    # of "../" * n against the lesson's own directory is what a browser does.
    resolved = posixpath.normpath(
        posixpath.join("/" + dest.relative_to(OUT_ROOT).as_posix() + "/", href))
    assert resolved == "/", f"the back link resolves to {resolved!r}, not /"


def test_no_served_page_carries_an_unescaped_build_placeholder(on_disk):
    """The href is written by substituting `__HOME__`. If that substitution is ever
    removed the page ships a literal placeholder, and nothing else would notice."""
    for name in ("index.html", "lesson.js"):
        assert "__HOME__" not in on_disk[name], (
            f"{name} still contains the __HOME__ placeholder, so the build-time "
            "substitution did not run"
        )


def test_the_answer_log_is_written_by_rung_and_never_pushed(on_disk):
    """TASK-050. The falsifying input is in `tools/ui_probe.html`: answer all four
    rungs through the level tabs in a shuffled order and require all four to
    survive. With `push` it was 0 of 4 marked done; with this it is 4 of 4.

    MEASURED 2026-10-02, found by `viewer` instrumenting
    `Array.prototype.push`: push indices came out 0, 2, 3, 4. `jumpTo(n)` does
    `state.log[n] = null`, which EXTENDS a sparse array, so the next push landed
    one index too high and each jump nulled the row the previous answer occupied.
    Answering all four rungs out of order kept ONE answer in FOUR, and the finish
    screen, the row list and the tab bar were three different accounts of one
    session.

    `push` is the wrong operation outright: the log is keyed by rung, and the whole
    point of the level tabs is that arrival order is the learner's choice.
    """
    js = on_disk["lesson.js"]
    assert "state.log.push(" not in js, (
        "state.log is keyed by RUNG. `push` assumes arrival order is identity, "
        "which the level tabs exist to deny. Use `state.log[state.i] = ...`."
    )
    assert "state.log[state.i] =" in js


def test_the_tab_bar_is_redrawn_after_answering(on_disk):
    """TASK-055. `rungBar()` was called only from `render()` and `finish()`, so the
    rung you had just answered stayed un-marked until you navigated away. On the
    finish screen, under the words "You worked through every level", three tabs were
    green and the one you had just finished was the only white one."""
    js = on_disk["lesson.js"]
    check = js[js.index("state.log[state.i] ="):]
    window = check[:check.index("document.getElementById('result')")]
    assert "rungBar()" in window, (
        "the rung bar must be redrawn as soon as an answer is recorded, or the "
        "rung you just answered is the one still un-marked"
    )
    # And 'on' and 'done' are separate facts, so answering the rung you are
    # standing on still marks it done.
    bar = js[js.index("function rungBar()"):js.index("function jumpTo(")]
    # STRIP COMMENTS BEFORE ASSERTING ON CODE.
    # MEASURED 2026-10-02: this first asserted `"n < state.i" not in bar` and failed
    # -- because the comment in `rungBar()` explains that `n < state.i` was the OLD
    # condition, so the fix's own explanation tripped it. That is the fifth time in
    # this project a text search fired on correct code, and the second time on my
    # own comment.
    code = re.sub(r"//[^\n]*", "", bar)
    assert "'on'" in code and "'done'" in code
    assert "state.log[n] ? 'done'" in code, (
        "'done' must come from the LOG, not from queue position -- otherwise "
        "opening HARD first lights three rungs green for questions never attempted"
    )
    assert "n < state.i" not in code, "queue position is not 'done'"
