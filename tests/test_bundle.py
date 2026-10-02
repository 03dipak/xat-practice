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
import re
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
    """Until a confidence is recorded, the learner cannot reach the options."""
    assert "document.getElementById('reveal').disabled = false;" in on_disk["lesson.js"]
    assert "Show the options" in on_disk["lesson.js"], (
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
    js = on_disk["lesson.js"]
    for step in ("commitBox", "reveal", "optBox", "check", "result"):
        assert step in js, step
    order = [js.index(s) for s in ("id=\"reveal\"", "id=\"optBox\"",
                                   "id=\"check\"", "id=\"result\"")]
    assert order == sorted(order), "the loop is out of order"


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
# main(): the entry point that actually writes the files
# ---------------------------------------------------------------------------

def test_main_writes_all_four_files_and_reports_the_ladder(capsys):
    """`main()` is what a session runs to produce a lesson, so it is the one
    function whose failure is silent -- the tests above call `build_lesson`
    directly and never touch the filesystem."""
    bundle.main()
    out = capsys.readouterr().out

    for name in ("index.html", "lesson.js", "paper.json", "answerkey.json"):
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
