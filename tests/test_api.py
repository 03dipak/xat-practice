"""Coverage of the public API and of every branch the main suite does not reach.

These are not filler. Each test here either exercises a branch that has never
been run -- which is exactly the state the reference project warns about ("a
check that has only ever been shown a true statement is untested") -- or pins a
number the pedagogy in docs/ rests on.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from xat_practice import syllabus as S
from xat_practice.items import LEVEL_RECIPES, Level, derive_level
from xat_practice.registry import LESSONS
from xat_practice.solver import SOLVER, Failure, Verdict

# ---------------------------------------------------------------------------
# the weight model's own API
# ---------------------------------------------------------------------------

def test_self_check_rejects_a_table_that_does_not_close(monkeypatch):
    """THE test for `self_check`. Without it, `self_check` is a function that
    has only ever seen a true statement."""
    bad = S.Topic("fake", "Fake", (1,) * 7, True)
    monkeypatch.setattr(S, "TOPICS", (*S.TOPICS, bad))
    with pytest.raises(ValueError, match="The table is wrong, not the exam"):
        S.self_check()


def test_self_check_rejects_duplicate_ids(monkeypatch):
    """The dup check runs AFTER the sum check, so the table must still close to
    28 -- otherwise the sum check fires first and this proves nothing about the
    dup check."""
    renamed = S.Topic(S.TOPICS[0].id, "Clone", S.TOPICS[1].per_year, True)
    monkeypatch.setattr(S, "TOPICS", (S.TOPICS[0], renamed, *S.TOPICS[2:]))
    with pytest.raises(ValueError, match="duplicate topic id"):
        S.self_check()


def test_band_value_flattens_the_head():
    """DI (6.71/yr) and Geometry (4.57/yr) both earn 1.00 -- a 47% frequency
    difference does not earn a 47% study-time difference in the 80-100 band."""
    di = next(t for t in S.TOPICS if t.id == "di")
    geo = next(t for t in S.TOPICS if t.id == "geo_mens")
    num = next(t for t in S.TOPICS if t.id == "num_sys")
    tw = next(t for t in S.TOPICS if t.id == "time_work")

    assert di.band_value == geo.band_value == 1.00
    assert di.weight > geo.weight          # frequency differs
    assert num.band_value == 0.95
    assert tw.band_value == 0.50


def test_measured_topics_excludes_the_unmeasured_pct_row():
    ids = {t.id for t in S.measured_topics()}
    assert "pct" not in ids
    assert "di" in ids


def test_by_tier_is_sorted_by_descending_weight():
    for tier in S.Tier:
        ws = [t.weight for t in S.by_tier(tier)]
        assert ws == sorted(ws, reverse=True)


def test_subtopic_index_and_lookup():
    idx = S.subtopics()
    assert len(idx) == len(S.SUBTOPICS)
    si = idx["geo_mens:circle-tangents"]
    assert si.tier is S.Tier.P1
    assert si.stratum is S.Stratum.QUANT
    assert len(si.traps) >= 3, "a subtopic with no named trap cannot set one"


def test_every_subtopic_names_at_least_one_trap():
    """D9: a trap we cannot name is a trap we cannot set as a distractor."""
    for s in S.SUBTOPICS:
        assert s.traps, f"{s.id} names no trap"


def test_every_subtopic_trap_is_a_full_sentence_with_a_concrete_wrong_move():
    """Vague traps become vague distractors. Each must say what the learner
    actually does wrong."""
    for s in S.SUBTOPICS:
        for t in s.traps:
            assert len(t.split()) >= 5, f"{s.id}: trap too vague -> {t!r}"


def test_paper_shape_constants_match_the_verified_xat():
    ps = S.PAPER_SHAPE
    assert ps["total_questions"] == 95
    assert ps["part1"] == {"qa_di": 28, "va_lr": 26, "dm": 21}
    assert sum(ps["part1"].values()) == 75
    assert ps["options"] == 5
    assert ps["mark_wrong"] == -0.25
    assert ps["blank_penalty_after"] == 8
    assert ps["blank_penalty"] == -0.10
    assert ps["gk_in_percentile"] is False
    assert ps["sectional_time_limit"] is False
    assert ps["calculator"] == "qa_di"


def test_excluded_topics_all_carry_a_reason():
    for name in S.EXCLUDED:
        assert len(S.EXCLUDED[name]) > 20, f"{name} excluded with no reason"


def test_subtopic_index_class_is_constructible():
    ix = S.SubtopicIndex({s.id: s for s in S.SUBTOPICS})
    assert ix["pl_int:simple-interest"].tier is S.Tier.P1


# ---------------------------------------------------------------------------
# every solver branch
# ---------------------------------------------------------------------------

def test_solver_refuses_a_quant_item_with_no_derivation():
    chk = SOLVER.verify(stratum=S.Stratum.QUANT, derivation=None,
                        keyed_value="200", keys=[])
    assert chk.verdict is Verdict.REFUSE
    assert chk.failure is Failure.NO_DERIVATION


def test_solver_refuses_an_unparseable_derivation():
    chk = SOLVER.verify(stratum=S.Stratum.QUANT, derivation="((((",
                        keyed_value="200", keys=[])
    assert chk.failure is Failure.UNRESOLVED_DERIVATION
    assert "does not parse" in chk.detail


def test_solver_refuses_an_unparseable_keyed_option():
    """Asymmetric: the key itself failing to parse is a different defect from
    the derivation failing to parse, and the detail must say which."""
    chk = SOLVER.verify(stratum=S.Stratum.QUANT, derivation="200",
                        keyed_value="@@@", keys=[])
    assert chk.failure is Failure.UNRESOLVED_DERIVATION


def test_solver_refuses_unevaluated_calculus():
    """The bound must be DEFINITE, or the free-symbol check fires first and the
    calculus branch is never reached -- which is what the first version of this
    test did, and it passed for the wrong reason."""
    chk = SOLVER.verify(stratum=S.Stratum.QUANT,
                        derivation="Integral(x**2, (x, 0, 1))",
                        keyed_value="200", keys=[])
    assert chk.failure is Failure.UNRESOLVED_DERIVATION
    assert "calculus" in chk.detail


def test_free_symbols_are_caught_before_calculus():
    chk = SOLVER.verify(stratum=S.Stratum.QUANT, derivation="Integral(x, x)",
                        keyed_value="200", keys=[])
    assert chk.failure is Failure.UNRESOLVED_DERIVATION
    assert "free symbols" in chk.detail


def test_judgement_item_with_no_derivation_is_delegated_not_refused():
    """MEASURED: this returned REFUSE/NO_DERIVATION, which would have rejected
    every VALR and DM item -- a third of the exam. It must be DELEGATED."""
    chk = SOLVER.verify(stratum=S.Stratum.JUDGEMENT, derivation=None,
                        keyed_value="a", keys=[])
    assert chk.verdict is Verdict.DELEGATED
    assert chk.ok is False, "DELEGATED is not HOLD"
    assert chk.grounded is False, "an opinion is not a computation"
    assert "second opinion" in chk.detail


def test_only_a_computed_key_may_claim_to_be_grounded():
    """The single property that keeps a percentile claim honest."""
    quant = SOLVER.verify(stratum=S.Stratum.QUANT, derivation="200",
                          keyed_value="200", keys=[])
    logic = SOLVER.verify(stratum=S.Stratum.LOGIC, derivation="enumerated",
                          keyed_value="a", keys=[])
    judge = SOLVER.verify(stratum=S.Stratum.JUDGEMENT, derivation=None,
                          keyed_value="a", keys=[])
    assert quant.grounded and quant.verdict is Verdict.HOLD
    assert not logic.grounded and not judge.grounded


def test_logic_item_with_no_derivation_is_refused():
    chk = SOLVER.verify(stratum=S.Stratum.LOGIC, derivation=None,
                        keyed_value="a", keys=[])
    assert chk.verdict is Verdict.REFUSE
    assert chk.failure is Failure.NO_DERIVATION


def test_key_mismatch_detail_names_the_values_and_the_options():
    chk = SOLVER.verify(stratum=S.Stratum.QUANT, derivation="200",
                        keyed_value="999",
                        keys=["100", "200", "999", "220", "1200"])
    assert chk.failure is Failure.KEY_MISMATCH
    assert "200" in chk.detail and "999" in chk.detail
    assert "1200" in chk.detail, "the detail must show what the options were"
    assert "not repairing" in chk.detail


def test_refusals_are_never_silent_about_being_a_refusal():
    chk = SOLVER.verify(stratum=S.Stratum.QUANT, derivation=None,
                        keyed_value="1", keys=[])
    assert chk.ok is False
    assert chk.detail.strip() != ""


# ---------------------------------------------------------------------------
# level recipes: the drafter's contract
# ---------------------------------------------------------------------------

def test_every_recipe_key_is_a_real_level():
    for level in Level:
        r = LEVEL_RECIPES[level]
        assert set(r) == {"derivation_steps", "needs_substitution",
                          "insight_required", "real_near_misses"}
        assert r["real_near_misses"] >= 2, (
            f"{level} needs >= 2 real near-misses or G8 refuses the item, so "
            f"the recipe and the gate contradict each other"
        )


def test_recipe_distractors_satisfy_gate_G8():
    """The recipe must produce an item G8 actually admits."""
    from xat_practice.items import recipe as make

    for level in Level:
        ds = make(level)
        assert len(ds) == 4
        assert sum(d.is_real_near_miss for d in ds) >= 2


def test_insight_alone_does_not_make_an_item_hard():
    """An item with one insight and nothing else is MEDIUM, not HARD. If
    insight alone reached HARD, the label would stop meaning anything."""
    from dataclasses import replace

    from tests.test_gates import at_level

    it = at_level(Level.EASY, 0)
    rep = derive_level(replace(it, insight_required=True))
    assert rep.level is Level.MEDIUM
    assert any("insight" in d for d in rep.drivers)


def test_enumeration_size_drives_difficulty_for_logic():

    from tests.test_gates import logic_item

    small = derive_level(logic_item(enumeration_size=10))
    big = derive_level(logic_item(enumeration_size=900))
    assert big.score > small.score
    assert any("enumeration" in d for d in big.drivers)
    assert small.level is not big.level


def test_calculator_budget_is_reflected_in_the_score():
    from dataclasses import replace

    from tests.test_gates import at_level

    fast = derive_level(at_level(Level.MEDIUM, 1))
    slow = derive_level(replace(at_level(Level.MEDIUM, 1), calculator_minutes=3.0))
    assert slow.score == fast.score + 0.5


# ---------------------------------------------------------------------------
# gate bookkeeping
# ---------------------------------------------------------------------------

def test_gate_result_bookkeeping():
    from tests.test_gates import quant_item

    from xat_practice.gates import run

    res = run([quant_item(id="a", stem="Alpha one", options=("1", "2", "3")),
               quant_item(id="b", stem="Beta two",
                          options=("1", "2", "3", "All of the above", "5"))])
    assert res.refusal_rate == 1.0
    assert res.by_gate()["G1_options"] == 1, "only item a has the wrong count"
    assert res.by_gate()["G3_no_all_of_above"] == 1
    assert res.by_gate()["G4_distinct_options"] == 0
    assert res.by_gate()["G2_key_in_range"] == 0, "index 1 is valid in 3 options"
    assert res.by_gate()["G5_key_grounded"] == 2, (
        "both keys are in range and both are wrong: the derivation gives 200 "
        "and each keyed option reads 2"
    )
    # G12 no longer fires here, and that is the fix rather than a regression.
    # MEASURED 2026-10-02: this fixture used to give item a four placeholder
    # distractors ("0".."3") for only two wrong options, so G12 fired -- but for
    # a reason that had nothing to do with the gate's purpose. Those placeholders
    # also matched no option at all, which is the defect G16 now refuses. The
    # fixture builders derive distractors from the final option list, so the count
    # matches by construction and the count check belongs to a G12 test of its own.
    assert res.by_gate()["G12_misconceptions_named"] == 0


def test_gate_result_on_an_empty_paper():
    from xat_practice.gates import run

    res = run([])
    assert res.refusal_rate == 0.0
    assert res.admitted == []


def test_G11_drops_the_over_quota_item_rather_than_removing_it_later():
    """The first version of the G11 branch called `kept.remove(it)`
    defensively on an item it had never appended. With two over-quota items at
    one level that would raise ValueError on the second. Ten MEDIUM items
    against a quota of 4 must produce six refusals and not raise."""
    from tests.test_gates import at_level

    from xat_practice.gates import run

    items = [at_level(Level.MEDIUM, i) for i in range(10)]
    res = run(items)
    over = [r for r in res.refusals if r.gate == "G11_mix_within_tolerance"]
    assert len(over) == 6, "ten MEDIUM items against a quota of 4"
    assert len(res.admitted) == 4
    assert {i.id for i in res.admitted} == {f"medium-{i}" for i in range(4)}


def test_guess_ev_report_matches_the_documented_numbers():
    """These four figures are quoted in docs/ and in the pedagogy. If this
    moves, every one of those documents is wrong."""
    from xat_practice.gates import guess_ev_report

    assert guess_ev_report() == {
        "guess_5_options": 0.0,
        "guess_4_options": 0.0625,
        "one_blank_9th": -0.1,
        "ten_blanks": -0.2,
    }


def test_all_gates_get_refusal_counts_for_every_id():
    from tests.test_gates import quant_item

    from xat_practice.gates import GATE_IDS, run

    res = run([quant_item()])
    assert set(res.by_gate()) == set(GATE_IDS)
    assert res.refusal_rate == 0.0


# ---------------------------------------------------------------------------
# the static server cannot be wedged
# ---------------------------------------------------------------------------
# MEASURED 2026-10-02. The owner reported that the lesson page "takes too much
# time to load". The assets were never the cause -- 1.4ms for lesson.js, 2.8ms
# for paper.json, 4.8ms for index.html, ~12ms for all four, measured by fetch.
#
# The cause was `socketserver.TCPServer`, which serves ONE connection at a time.
# A client that opens a socket and then holds it idle parks the only thread
# forever. Browsers do this routinely -- the server log recorded a session that
# requested /favicon.ico at 10:21:42 and then served nothing at all, and a
# plain curl after that timed out. The page stopped loading permanently, with
# no error and no exit.

def _free_port() -> int:
    import socket

    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def test_one_held_connection_does_not_block_the_next_request():
    """The falsifying input, written first: a socket that connects and then says
    NOTHING -- exactly what a browser preconnect or a favicon probe does.

    Against `TCPServer` this hangs the server for good. It must return."""
    import socket
    import threading
    import urllib.request

    from xat_practice.cli import make_server

    port = _free_port()
    httpd = make_server(Path(__file__).resolve().parent.parent
                        / "out" / LESSONS[0].lesson_id, port)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    held = socket.create_connection(("127.0.0.1", port))
    try:
        # The wedging input: connected, silent, will never send a request.
        assert held.fileno() >= 0
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/",
                                    timeout=5) as r:
            assert r.status == 200
            assert b"<title>" in r.read()
        # And the lesson's own assets still load.
        for name in ("lesson.js", "paper.json"):
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/{name}",
                                        timeout=5) as r:
                assert r.status == 200
                assert r.read()
    finally:
        held.close()
        httpd.shutdown()
        httpd.server_close()


def test_the_server_is_threaded_not_single_connection():
    """Pins the mechanism, so the property cannot be lost to a well-meaning
    revert to TCPServer. Threading is the fix; this says so explicitly."""
    import http.server

    from xat_practice.cli import make_server

    httpd = make_server(Path("."), _free_port())
    try:
        assert isinstance(httpd, http.server.ThreadingHTTPServer)
        assert httpd.daemon_threads is True
    finally:
        httpd.server_close()


def test_serve_refuses_to_start_without_an_index_html(tmp_path, capsys):
    """A server that starts on an empty directory serves a listing of nothing
    and looks like a working lesson with no questions in it."""
    from xat_practice.cli import main

    rc = main(["serve", "--lesson", str(tmp_path), "--port", str(_free_port())])
    assert rc == 1
    err = capsys.readouterr().err
    assert "no index.html" in err
    assert "xat-practice build" in err, "the error must say the command that fixes it"
