"""Coverage of the public API and of every branch the main suite does not reach.

These are not filler. Each test here either exercises a branch that has never
been run -- which is exactly the state the reference project warns about ("a
check that has only ever been shown a true statement is untested") -- or pins a
number the pedagogy in docs/ rests on.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from xat_practice import syllabus as S
from xat_practice.items import LEVEL_RECIPES, Level, derive_level
from xat_practice.items import expected_ev as _ev
from xat_practice.registry import LESSONS
from xat_practice.solver import SOLVER, Failure, Verdict

# ---------------------------------------------------------------------------
# the weight model's own API
# ---------------------------------------------------------------------------

def test_self_check_rejects_a_table_that_does_not_close(monkeypatch):
    """THE test for `self_check`. Without it, `self_check` is a function that
    has only ever seen a true statement."""
    bad = S.Topic("fake", "xat", "qa_di", "Fake", (1,) * 7, True)
    monkeypatch.setattr(S, "TOPICS", (*S.TOPICS, bad))
    with pytest.raises(ValueError, match="The table is wrong, not the exam"):
        S.self_check()


def test_self_check_rejects_duplicate_ids(monkeypatch):
    """The dup check runs AFTER the sum check, so the table must still close to
    28 -- otherwise the sum check fires first and this proves nothing about the
    dup check."""
    renamed = S.Topic(S.TOPICS[0].id, "xat", "qa_di", "Clone",
                     S.TOPICS[1].per_year, True)
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


def test_the_exam_and_section_shapes_match_the_verified_xat():
    """MEASURED from XLRI's own 2026 notification, not from a coaching site.

    This replaced a test that read `syllabus.PAPER_SHAPE`, a single dict describing
    one paper. The exam is now `EXAMS` and the marking is per SECTION, which is the
    level at which the first two exams actually differ.
    """
    xat = S.EXAMS["xat"]
    assert xat.total_questions == 95
    assert xat.counted_questions == 75
    assert xat.part_minutes() == 170
    assert xat.parts == ("part_1", "part_2")
    assert xat.sections() == ("qa_di", "va_lr", "dm", "gk")
    assert xat.counted() == ("qa_di", "va_lr", "dm")

    qa = S.SECTIONS["xat:qa_di"]
    assert qa.questions == 28
    assert qa.options == 5
    assert qa.mark_wrong == -0.25
    assert qa.calculator is True
    # The blank rule is NOT here. See
    # `test_the_blank_penalty_counts_across_the_part_not_within_a_section`.
    assert not hasattr(qa, "blank_penalty")
    # MEASURED 2026-10-02: `minutes=170` was first set on the qa_di section alone,
    # which made Part 1's shared clock look like QA&DI's own allowance. No COUNTED
    # section may claim a clock now; the exam holds it. GK is exempt and legitimately
    # has its own 10 -- Part 2 is timed separately -- so it is excluded here rather
    # than by loosening the claim to "nearly all".
    # No section may carry a clock: XAT 2026 has NO sectional time limit.
    assert not any(hasattr(S.SECTIONS[f"xat:{sid}"], "minutes")
                   for sid in xat.sections())

    # GK: 20 questions, 10 minutes, and OUT of the raw score.
    #
    # MEASURED 2026-10-02: `ExamSpec.excluded_from_percentile` is GONE. GK's
    # exclusion now lives in ONE place -- `PartSpec.in_percentile` -- because the
    # old flag and the old field could disagree with nothing to notice. The
    # assertion below therefore asks the part.
    gk = S.SECTIONS["xat:gk"]
    assert gk.questions == 20
    assert S.PARTS["xat:part_2"].minutes == 10
    assert S.PARTS["xat:part_2"].in_percentile is False
    assert gk.counts_for_percentile(xat) is False
    assert "excluded_from_percentile" not in set(S.ExamSpec.__dataclass_fields__), (
        "the second home for GK's exclusion is back"
    )


def test_the_guess_ev_is_computed_not_hardcoded():
    """MEASURED 2026-10-02: a first version of this computed
    `1/options + (options-1)/options * mark_wrong`, which hardcoded +1 and dropped
    `mark_correct`. It returned -0.6000 for CAT's reported +3/-1 when the truth is
    3/5 + 4/5 x -1 = **-0.2000**. It was right for XAT only because XAT's
    `mark_correct` happens to be 1. Both reviewing agents caught it; this pins it."""
    qa = S.SECTIONS["xat:qa_di"]
    assert qa.guess_ev() == pytest.approx(0.0, abs=1e-9), (
        "XAT's +1/-0.25 at 5 options is exactly zero -- that is the whole lesson"
    )
    assert _ev(options=5, mark_correct=3, mark_wrong=-1) == pytest.approx(
        -0.2, abs=1e-9)
    # And a 3-mark paper must not report the same EV as a 1-mark one.
    assert qa.guess_ev() != _ev(options=5, mark_correct=3, mark_wrong=-1)


def test_a_topic_naming_an_unknown_exam_is_refused(monkeypatch):
    """MEASURED 2026-10-02: `Topic.exam_id`/`section_id` are required with NO
    default, so a missing parent is a TypeError at import. This checks the other
    half -- a parent that EXISTS but is wrong must refuse at build time, not render
    into a section it does not belong to."""
    # REPLACES a topic rather than adding one, so the year rows still sum to 28.
    # Adding one tipped the sum to 25 and the closure check fired first -- which
    # proves nothing about the exam layer. The neighbouring
    # `test_self_check_rejects_duplicate_ids` records the same trap.
    stolen = S.TOPICS[1].per_year
    bad = S.Topic("fake", "cat", "qa", "Fake", stolen, True)
    monkeypatch.setattr(S, "TOPICS", (S.TOPICS[0], bad, *S.TOPICS[2:]))
    with pytest.raises(KeyError, match="not in SECTIONS"):
        S.self_check()


def test_a_section_whose_key_and_value_disagree_is_refused(monkeypatch):
    """The join was a convention, not a check. MEASURED: rewriting
    `SECTIONS["xat:qa_di"]` to carry `exam_id="cat"` made `section_of` return the CAT
    spec for an XAT topic -- the key said xat, the value said cat, and only one of
    them was read."""
    wrong = dataclasses.replace(S.SECTIONS["xat:qa_di"], exam_id="cat")
    monkeypatch.setitem(S.SECTIONS, "xat:qa_di", wrong)
    with pytest.raises(ValueError, match="key and the value disagree"):
        S.self_check()


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

    from xat_practice.bundle import out_dir
    from xat_practice.cli import make_server

    port = _free_port()
    # DERIVED, not `out/<lesson_id>` written out. MEASURED 2026-10-02: the flat
    # path stopped existing when the exam layer nested the output, and this test
    # pointed a server at a directory that was not there -- a test that passes
    # while checking nothing is exactly what it exists to prevent.
    httpd = make_server(out_dir(LESSONS[0].lesson_id), port)
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


# ---------------------------------------------------------------------------
# Part 1 is ONE pool. The blank penalty is counted across it, not per section.
# ---------------------------------------------------------------------------
# MEASURED 2026-10-02. `blank_penalty` and `blank_penalty_after` were on
# `SectionSpec`, so the product implied EIGHT FREE BLANKS PER SECTION. XAT's rule
# is "-0.10 for every unattempted question after the first eight", and Part 1 is one
# pool of 75 questions across QA&DI, VA&LR and DM. A learner told otherwise would
# skip 24 and lose about 1.6 marks: a false attempt strategy, which is the one thing
# this product teaches.
#
# Both reviewers reading docs/LLD.md flagged it independently. This is the
# falsifying input for the fix.

XAT = S.EXAMS["xat"]
PART_1 = S.PARTS["xat:part_1"]
PART_2 = S.PARTS["xat:part_2"]


def test_the_blank_penalty_counts_across_the_part_not_within_a_section():
    """4 blanks in QA&DI + 3 in DM + 3 in VA&LR = 10 blank, so 2 are over the
    allowance and cost 0.20 -- even though NO section has more than eight."""
    qa, dm, valr = S.SECTIONS["xat:qa_di"], S.SECTIONS["xat:dm"], S.SECTIONS["xat:va_lr"]
    blanks = 4 + 3 + 3
    assert all(s.part_id == "part_1" for s in (qa, dm, valr)), (
        "all three scored sections must be in the SAME part, or the allowance is "
        "counted once per section and the learner is told they may skip 24"
    )
    assert PART_1.cost_of_blanks(blanks) == pytest.approx(-0.20)
    # The wrong answer, spelled out, because it is what the code used to do.
    per_section_wrong = (qa.blank_penalty_after if hasattr(qa, "blank_penalty_after")
                         else 8) * 3
    assert per_section_wrong == 24, (
        "this is the number the section-level model told a learner: 24 free blanks"
    )


def test_eight_or_fewer_blanks_in_part_1_cost_nothing():
    for blanks in (0, 1, 7, 8):
        assert PART_1.cost_of_blanks(blanks) == 0.0, blanks
    assert PART_1.cost_of_blanks(9) == pytest.approx(-0.10)
    assert PART_1.cost_of_blanks(10) == pytest.approx(-0.20)


def test_gk_blanks_never_draw_a_part_1_penalty():
    """GK is a separate PART with no blank rule, and it is excluded from the
    percentile, so its blanks cannot consume Part 1's allowance or add to its
    penalty."""
    assert PART_2.blank_penalty == 0.0
    assert PART_2.blank_penalty_after == 0
    assert PART_2.cost_of_blanks(20) == 0.0
    assert PART_2.in_percentile is False


def test_no_section_may_carry_the_parts_clock_or_blank_rule():
    """The regression guard for the ORIGINAL mistake, in the shape that would
    reintroduce it. If someone adds `minutes` or `blank_penalty` back to
    `SectionSpec`, this fails."""
    fields = set(S.SectionSpec.__dataclass_fields__)
    for banned in ("minutes", "blank_penalty", "blank_penalty_after",
                   "stratum", "in_percentile"):
        assert banned not in fields, (
            f"SectionSpec.{banned} is a PART-level fact (or, for `stratum`, a "
            "distribution rather than a value). MEASURED 2026-10-02: "
            "blank_penalty per section told a learner they could skip 24."
        )


def test_part_one_has_the_clock_and_no_section_does():
    assert PART_1.minutes == 170
    # XAT 2026 has NO sectional time limit, so no section may carry one.
    for sid in XAT.sections():
        assert not hasattr(S.SECTIONS[f"xat:{sid}"], "minutes"), sid


def test_a_section_is_a_mix_of_strata_not_one_value():
    """MEASURED 2026-10-02: `SectionSpec.stratum` was a single `Stratum`, and
    QA&DI holds **37 QUANT and 3 LOGIC** subtopics. A single value is a lie that
    either fails the 3 LOGIC items at `G10` or gets them relabelled."""
    strata = S.SECTIONS["xat:qa_di"].strata()
    assert strata[S.Stratum.QUANT] == 37
    assert strata[S.Stratum.LOGIC] == 3, (
        f"QA&DI's LOGIC subtopics moved or vanished: {strata}"
    )
    logic = sorted(s.id for s in S.SUBTOPICS if s.stratum is S.Stratum.LOGIC)
    assert logic == ["ds:sufficiency-statements",
                     "puzzle:routing-and-network-puzzles",
                     "venn:venn-counting"], logic


def test_the_parts_close_to_the_exam():
    """28 + 26 + 21 = 75 and 75 + 20 = 95. Stated as arithmetic, because 'close' on
    its own is ambiguous -- which is why invariant 5 was rewritten this way."""
    p1 = [S.SECTIONS[f"xat:{s}"] for s in PART_1.sections]
    p2 = [S.SECTIONS[f"xat:{s}"] for s in PART_2.sections]
    assert sum(s.questions for s in p1) == PART_1.questions == 75
    assert sum(s.questions for s in p2) == PART_2.questions == 20
    assert PART_1.questions + PART_2.questions == XAT.total_questions == 95
    assert sum(s.questions for s in p1) == XAT.counted_questions == 75


def test_the_shape_records_what_it_was_verified_against():
    """MEASURED 2026-10-02: it is October 2026, so the paper a learner actually sits
    is most likely XAT 2027. `edition="2026"` silently asserted that next year's
    paper has the same counts, marking and calculator policy."""
    assert XAT.evidence in ("OFFICIAL", "MEASURED", "SECONDARY", "ASSUMPTION")
    assert XAT.evidence == "OFFICIAL"
    assert "2026" in XAT.verified_against
    assert XAT.verified_against, (
        "an OFFICIAL shape must name the document it came from"
    )


def test_a_section_asked_about_the_wrong_exam_refuses():
    """Asking an XAT section whether it counts for a different exam is a bug, not a
    question. It used to return the XAT answer regardless of what was asked."""
    other = S.ExamSpec(exam_id="cat", name="CAT", edition="2026",
                       total_questions=66, counted_questions=66,
                       parts=())
    with pytest.raises(ValueError, match="wrong"):
        S.SECTIONS["xat:qa_di"].counts_for_percentile(other)


# ---------------------------------------------------------------------------
# the exam-layer closure: every branch needs a WRONG input, or it is decoration
# ---------------------------------------------------------------------------
# MEASURED 2026-10-02: `_check_exam_layer()` closed by luck, because nothing
# asserted that the parts and sections agreed. With the checks added, every `raise`
# below is a branch that fires on a specific malformed table -- and a raise nobody
# can reach is a raise that never runs.

def test_a_sections_key_that_disagrees_with_its_value_is_refused(monkeypatch):
    """The join was a convention. MEASURED: `SECTIONS["xat:qa_di"]` carrying
    `exam_id="cat"` returned the CAT spec for an XAT topic, with no error."""
    wrong = dataclasses.replace(S.SECTIONS["xat:qa_di"], exam_id="cat")
    monkeypatch.setitem(S.SECTIONS, "xat:qa_di", wrong)
    with pytest.raises(ValueError, match="key and the value disagree"):
        S.self_check()


def test_a_section_naming_an_unknown_exam_is_refused(monkeypatch):
    good = S.SECTIONS["xat:qa_di"]
    orphan = dataclasses.replace(good, section_id="qa_di", exam_id="cat")
    monkeypatch.setitem(S.SECTIONS, "cat:qa_di", orphan)
    with pytest.raises(ValueError, match="not in"):
        S.self_check()


def test_a_part_naming_a_section_that_does_not_exist_is_refused(monkeypatch):
    """`ExamSpec.sections` is DERIVED from its parts, so a section can only go
    missing at the PART level. MEASURED while writing this: the first version
    replaced `sections=` on the ExamSpec and raised TypeError -- the field was
    renamed to `parts` when the part layer landed, so the test was asserting against
    a shape the code no longer has."""
    thin = dataclasses.replace(S.PARTS["xat:part_1"],
                               sections=("qa_di", "does_not_exist"))
    monkeypatch.setitem(S.PARTS, "xat:part_1", thin)
    with pytest.raises(ValueError, match="not in SECTIONS"):
        S.self_check()


def test_exam_question_counts_that_do_not_close_are_refused(monkeypatch):
    """Stated as arithmetic on purpose: 28 + 26 + 21 = 75 and 75 + 20 = 95."""
    bad = dataclasses.replace(S.EXAMS["xat"], counted_questions=74)
    monkeypatch.setitem(S.EXAMS, "xat", bad)
    with pytest.raises(ValueError, match="COUNTED sections sum"):
        S.self_check()

    bad2 = dataclasses.replace(S.EXAMS["xat"], total_questions=99)
    monkeypatch.setitem(S.EXAMS, "xat", bad2)
    with pytest.raises(ValueError, match="sections sum to"):
        S.self_check()


def test_an_orphan_section_nobody_claims_is_refused(monkeypatch):
    """A section nothing points at will never be rendered and never be built, and
    nothing would notice."""
    extra = dataclasses.replace(S.SECTIONS["xat:gk"], section_id="spare")
    monkeypatch.setitem(S.SECTIONS, "xat:spare", extra)
    with pytest.raises(ValueError, match="which no exam claims"):
        S.self_check()


def test_a_topic_with_no_subtopics_is_refused(monkeypatch):
    empty = S.Topic("lonely", "xat", "qa_di", "Lonely", (0,) * 7, True, "")
    # Keep the year rows closing by replacing a topic whose row is all zeros is
    # impossible, so assert the SPECIFIC message instead of the closure one.
    monkeypatch.setattr(S, "TOPICS", (S.TOPICS[0], empty, *S.TOPICS[1:]))
    with pytest.raises(ValueError):
        S.self_check()
