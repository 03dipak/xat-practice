"""opencode.json is BUILT, never hand-edited.

`build_opencode.py` owns every prompt. The reference project pasted a 27 KB
knowledge block into eight agent prompts by hand and the copies drifted; the
shared block here is written once and interpolated, and
`assert_shared_identical` fails the build if a prompt stops containing it
verbatim. These tests are that guard, plus the structural promises the config
makes.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from xat_practice import build_opencode as B

CFG = B.build()
AGENTS = CFG["agent"]


# ---------------------------------------------------------------------------
# the config is well formed
# ---------------------------------------------------------------------------

def test_config_is_valid_json_on_disk_and_matches_the_builder():
    """If someone hand-edits opencode.json, the build must be re-run -- this
    is the test that notices."""
    path = Path(B.ROOT) / "opencode.json"
    assert path.exists(), "run `python -m xat_practice.build_opencode`"
    on_disk = json.loads(path.read_text())
    assert on_disk == CFG, (
        "opencode.json on disk does not match build_opencode.py. Hand-edits "
        "will drift: the shared block exists in nine prompts and the reference "
        "project lost exactly this way. Re-run "
        "`python -m xat_practice.build_opencode`."
    )


def test_build_writes_to_the_project_root():
    """The PROJECT root, whose name is `xat-practice` with a HYPHEN -- the
    directory the owner renamed it to. The Python PACKAGE underneath is
    `xat_practice` with an UNDERSCORE, because a package cannot be imported
    under a name containing a hyphen.

    The two names differ, so this asserts both. MEASURED: the first version
    asserted only the package name and passed while `build_opencode.OUT` had
    been writing opencode.json into `src/`, where opencode would never find it.
    """
    assert Path(B.ROOT).name == "xat-practice"
    assert Path(B.ROOT).parent.name == "agentic"
    assert Path(B.ROOT) / "opencode.json" == B.OUT
    assert B.OUT.exists(), "opencode.json must sit at the project root"
    assert Path(B.__file__).resolve().parent.name == "xat_practice"


def test_every_ten_roles_exist():
    assert len(AGENTS) == 10
    assert set(AGENTS) == set(B.AGENTS)


def test_mentor_is_primary_and_the_rest_are_subagents():
    assert AGENTS["mentor"]["mode"] == "primary"
    for name, agent in AGENTS.items():
        if name != "mentor":
            assert agent["mode"] == "subagent", name


def test_every_subagent_is_read_only_on_edit():
    """A reviewer that can edit the thing it reviews is not a reviewer."""
    for name, agent in AGENTS.items():
        if name == "mentor":
            continue
        assert agent["permission"]["edit"] == "deny", name


def test_reviewers_cannot_broadly_execute():
    """`uv run` and bare `python3` are denied; only the project venv is
    allowed. A reviewer that can run arbitrary commands can quietly rewrite
    what it is auditing."""
    for name, agent in AGENTS.items():
        if name == "mentor":
            continue
        bash = agent["permission"]["bash"]
        assert bash["uv run *"] == "deny", name
        assert bash[".venv/bin/python"] == "allow", name
        assert bash[".venv/bin/python *"] == "allow", name
        assert bash["*"] == "ask", name


def test_every_role_has_a_description_that_states_its_boundary():
    for name, agent in AGENTS.items():
        d = agent["description"]
        assert len(d) > 120, f"{name}: description too thin to scope a role"
        assert "xat_practice" in d, name


# ---------------------------------------------------------------------------
# the shared block
# ---------------------------------------------------------------------------

def test_shared_block_is_in_every_prompt_verbatim():
    B.assert_shared_identical(CFG)


def test_shared_block_divergence_is_detected():
    """The guard must FAIL on a drifted prompt. A guard that has only ever
    seen a good config is untested."""
    broken = B.build()
    broken["agent"]["viewer"]["prompt"] = \
        broken["agent"]["viewer"]["prompt"].replace(
            "MEASURED FACTS", "APPROXIMATE FACTS")
    with pytest.raises(AssertionError, match="shared block"):
        B.assert_shared_identical(broken)


def test_shared_block_carries_the_numbers_the_docs_quote():
    """The block and the docs must not drift apart. These are the figures a
    reviewer is most likely to act on."""
    for fact in ("95 questions", "QA&DI  28", "VA&LR  26", "DM     21",
                 "170 minutes", "FIVE per question", "-0.10", "196 questions",
                 "0.0000", "+0.0625"):
        assert fact in B.SHARED, f"shared block is missing {fact!r}"


def test_shared_block_states_the_exam_not_the_stale_pattern():
    """The single most likely reviewer error is reasoning from the pre-2025
    pattern. The block must actively contradict it."""
    assert "pre-2025 pattern and is wrong" in B.SHARED
    assert "no sectional" in B.SHARED.lower() or "NO SECTIONAL" in B.SHARED


def test_no_role_prompt_contains_a_stale_four_option_ruling():
    """D3 reverses the reference project's D5/D6. A prompt that still implied
    4 options would train the wrong exam."""
    for name, agent in AGENTS.items():
        assert "4 options, -0.25   EV" in agent["prompt"], name
        assert "+0.0625" in agent["prompt"], name


# ---------------------------------------------------------------------------
# scope boundaries
# ---------------------------------------------------------------------------

def test_every_role_hands_off_to_its_overlapping_peers():
    for name, peers in B.HANDOFFS.items():
        for peer in peers:
            assert peer in AGENTS[name]["prompt"], f"{name} -> {peer}"


def test_key_auditor_is_asked_to_disprove_not_confirm():
    p = AGENTS["key-auditor"]["prompt"]
    assert "IS THIS KEY RIGHT?" in p
    assert "does this key look right" in p, (
        "the prompt must state the phrasing it refuses, or a reviewer will "
        "ask it anyway and get agreement"
    )
    assert "second true option" in p.lower()


def test_level_auditor_carries_the_measured_justification():
    """The role exists because of a number. Without the number it looks like
    an arbitrary extra reviewer."""
    p = AGENTS["level-auditor"]["prompt"]
    assert "4 of 6" in p
    assert "never request" in B.SHARED.lower()


def test_viewer_is_asked_to_check_the_commit_barrier():
    p = AGENTS["viewer"]["prompt"]
    assert "commit" in p.lower()
    assert "ZERO LLM calls" in p


def test_paper_auditor_knows_section_mocks_flatter():
    p = AGENTS["paper-auditor"]["prompt"]
    assert "TRAINING" in p or "flatters" in p
    assert "-0.10" in p


def test_tester_is_required_to_run_not_read():
    p = AGENTS["tester"]["prompt"]
    assert "ALWAYS RUN THE CODE" in p
    assert "WRONG input first" in p


def test_doc_reviewer_does_not_audit_code():
    p = AGENTS["doc-reviewer"]["prompt"]
    assert "EXPLICITLY NOT whether the code works" in p


def test_mentor_does_not_rule_for_the_owner():
    p = AGENTS["mentor"]["prompt"]
    assert "NEVER RULE ON BEHALF OF THE OWNER" in p
    assert "cannot supply a legal right" in p


def test_every_prompt_carries_the_owners_brief_and_its_limits():
    for name, agent in AGENTS.items():
        p = agent["prompt"]
        assert "THE OWNER'S BRIEF" in p, name
        assert "WHAT THE BRIEF DOES NOT AUTHORISE" in p, name
        assert "STILL OWNS" in p, name


def test_the_brief_states_the_learner_loop():
    """Every role must be able to judge its finding against the actual loop,
    which is the thing the owner asked for."""
    for name, agent in AGENTS.items():
        assert "options shown" in agent["prompt"], name
        assert "commit" in agent["prompt"].lower(), name
        assert "misconception behind EVERY option" in agent["prompt"], name


def test_no_two_prompts_are_identical():
    """Two identical prompts means one role is not scoped."""
    prompts = [a["prompt"] for a in AGENTS.values()]
    assert len(set(prompts)) == len(prompts)


def test_prompts_are_all_substantial():
    """A prompt too short to carry its assignment will get skimmed."""
    for name, agent in AGENTS.items():
        assert len(agent["prompt"]) > 10_000, name


# ---------------------------------------------------------------------------
# the build script itself
# ---------------------------------------------------------------------------

def test_main_writes_a_config_and_returns_without_raising():
    """`main()` is the entry point a session runs to rebuild the config, and it
    carries three assertions (shared block verbatim, no duplicate prompts, every
    handoff present). Untested, those are the three checks most likely to rot
    out of the file and nobody would notice until a prompt had drifted."""
    B.main()


def test_main_fails_loudly_if_two_roles_share_a_prompt():
    """Proved by construction, then checked: two identical prompts means one
    role is not scoped, and the assertion in `main` is the only guard."""
    original = dict(B.PROMPTS)
    try:
        B.PROMPTS["viewer"] = B.PROMPTS["question-setter"]
        with pytest.raises(AssertionError, match="not scoped"):
            B.main()
    finally:
        B.PROMPTS.clear()
        B.PROMPTS.update(original)


def test_main_fails_loudly_if_a_handoff_is_dropped():
    """A prompt edited to stop naming its peer is the exact drift this project
    exists to prevent, so the guard needs its own falsifying input."""
    original = B.PROMPTS["tester"]
    try:
        B.PROMPTS["tester"] = original.replace("key-auditor", "a-reader")
        with pytest.raises(AssertionError, match="hand off"):
            B.main()
    finally:
        B.PROMPTS["tester"] = original
    B.main()


# ---------------------------------------------------------------------------
# the UI inspector exists because of a measurement
# ---------------------------------------------------------------------------

def test_ui_inspector_exists_and_owns_the_rendered_page():
    """The role is not tidiness. `lesson.js` did not parse for the whole of
    Wave 1, so the browser ran none of it and the page had never worked, and 161
    tests passed because every one asserted on the file's TEXT. Without a role
    that renders the artefact, the next session reads the source again."""
    assert "ui-inspector" in AGENTS
    d = AGENTS["ui-inspector"]["description"]
    assert "did not parse" in d
    assert "headless" in d
    assert "asserted on file TEXT" in d or "TEXT" in d


def test_ui_inspector_is_asked_to_render_not_to_read():
    p = AGENTS["ui-inspector"]["prompt"]
    assert "RENDER IT" in p
    assert "LOOK AT THE PIXELS" in p, (
        "the prompt must require looking at the render. photos_graphics' "
        "render-inspector exists for exactly this: 'LOOK at the pixels, then "
        "measure them. Do not infer from the code.'"
    )
    assert "tools/ui_probe.py" in p, "the role must be given the command that renders"
    assert "UNVERIFIED" in p, (
        "the role must say what to do when it cannot execute, or it will "
        "report static reads as findings"
    )
    assert "is not a property of its text" in p


def test_ui_inspector_carries_the_defects_it_must_not_reintroduce():
    """A role prompt that does not name the past defects will let them back."""
    p = AGENTS["ui-inspector"]["prompt"]
    for fact, why in (
        ("item's", "the exact syntax error that shipped"),
        ("Hidden is not absent", "the options were in the DOM inside a hidden div"),
        ("window", "the globals that let a probe replace lesson.js's check()"),
        ("recomputed key", "the verdict must agree with the solver"),
    ):
        assert fact in p, f"the prompt lost {fact!r} ({why})"


def test_ui_inspector_does_not_steal_another_role_s_job():
    """Three boundaries, each of which has been confused before."""
    p = AGENTS["ui-inspector"]["prompt"].lower()
    assert "is the viewer's job" in p, "whether it TEACHES belongs to the viewer"
    assert "is key-auditor's job" in p, "whether the key is right belongs to key-auditor"
    assert "is tester's job" in p, "whether a gate is right belongs to tester"
    assert "mentor owns the ruling" in p


def test_the_ui_inspector_has_the_commands_it_needs_and_none_it_does_not():
    """It must be able to build the bundle, serve it and drive a browser, or the
    role cannot do its job. It must still not be able to edit what it audits."""
    bash = AGENTS["ui-inspector"]["permission"]["bash"]
    assert AGENTS["ui-inspector"]["permission"]["edit"] == "deny"
    assert bash["*"] == "ask"
    assert bash[".venv/bin/python *"] == "allow"
    assert bash["uv run *"] == "deny", "a reviewer that can run uv run can rewrite the venv"


def test_the_rendered_page_is_checked_by_a_test_and_not_only_by_a_tool():
    """`tools/ui_probe.py` that nothing invokes is a script, not a gate."""
    text = (Path(B.__file__).resolve().parent.parent.parent
            / "tests" / "test_render.py").read_text()
    assert "tools/ui_probe.py" in text or "ui_probe" in text
    assert Path(B.ROOT) / "tools" / "ui_probe.html" in [
        p for p in (Path(B.ROOT) / "tools").iterdir() if p.is_file()
    ], "the probe page must be committed, not a scratch file"
