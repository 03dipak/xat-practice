"""The command line. One entry point, eight verbs, no framework.

It existed as a declaration before it existed as code: `pyproject.toml` pointed
`xat-practice` at `xat_practice.cli:main` and no such module did. MEASURED during
the rename to `xat-practice`. A broken console script is worse than a missing
one, because it looks installed and fails at the moment someone relies on it.

EVERY verb here either re-derives a number or builds an artefact. None of them
is a convenience wrapper around a print statement.

The count is eight, and it used to be written down as four in this docstring and
as seven in `task.txt`. Both were wrong and neither raised, which is the whole
argument for the `doc-reviewer` role existing.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from . import build_opencode, bundle, gates
from .items import LESSON_SHAPE, LEVEL_RECIPES
from .registry import LESSONS, all_items, items_written, subtopics_written
from .syllabus import Tier, by_tier, self_check, stratum_counts

if TYPE_CHECKING:
    import http.server


def cmd_gates(_: argparse.Namespace) -> int:
    """Run the gate suite on Lesson 1 and report per-gate counts.

    Refusal counts are over a NAMED population, because a count with no
    denominator is a lie that looks like a pass.
    """
    every = all_items()
    res = gates.run(every)
    print(f"population: {len(every)} items across {len(LESSONS)} lesson(s): "
          + ", ".join(x.lesson_id for x in LESSONS))
    print(f"admitted:   {len(res.admitted)}")
    print(f"refused:    {len(res.refusals)}  "
          f"(rate {res.refusal_rate} over {len(every)})")
    for gate, n in sorted(res.by_gate().items()):
        if n:
            print(f"  {gate}: {n}")
    for r in res.refusals:
        print(f"  REFUSED {r.gate} {r.item_id}: {r.detail}")
    return 0 if not res.refusals else 1


def cmd_levels(_: argparse.Namespace) -> int:
    """Print each item's DERIVED level with its drivers.

    The drafter's claimed level is shown beside it when there is one, because a
    disagreement is a refusal (G7) and a silent overwrite would hide it.
    """
    res = gates.run(all_items())
    for item in all_items():
        rep = res.reports[item.id]
        claim = f"claimed {item.claimed_level}" if item.claimed_level else "no claim"
        print(f"{item.id:6s} {rep.level.value:11s} score {rep.score:5.2f}  "
              f"({claim})")
        for d in rep.drivers:
            print(f"         - {d}")
    return 0


def cmd_build(_: argparse.Namespace) -> int:
    """Build the static bundle. Refuses if any item fails a gate."""
    bundle.main()
    return 0


def cmd_agents(_: argparse.Namespace) -> int:
    """Rebuild opencode.json from build_opencode.py."""
    build_opencode.main()
    return 0


def cmd_weightage(_: argparse.Namespace) -> int:
    """Print the topic weight model with its population and its self-check.

    `self_check()` runs first and raises if the table does not close to 28 for
    every year -- a weight table that does not close to the paper length is a
    table of opinions wearing the costume of data.
    """
    self_check()
    from .syllabus import POPULATION, QUESTIONS_PER_PAPER, SUBTOPICS

    print(f"population: {POPULATION} questions = "
          f"{QUESTIONS_PER_PAPER} per paper x 7 papers, 2020-2026")
    print("source: a coaching compilation. XLRI publishes no per-topic "
          "breakdown, so this is measured-from-secondary-source.\n")
    for tier in (Tier.P1, Tier.P2, Tier.P3):
        print(f"{tier}  (train to zero error / high ROI / one shape only)")
        for t in by_tier(tier):
            mark = "" if t.owner_listed else "   [added, D4]"
            print(f"  {t.weight:5.2f}/yr  {t.name}{mark}")
        print()
    # MEASURED 2026-10-02: this line printed `written: 4`, which is the ITEM
    # count, sitting between two SUBTOPIC counts on a project with 40 subtopics.
    # It read as "four topics done". A count printed without saying what it counts
    # is a lie that looks like a pass.
    written_sub = subtopics_written()
    print(f"subtopics trained: {len(SUBTOPICS)}   "
          f"written: {len(written_sub)}   items written: {items_written()}")
    named_traps = sum(len(s.traps) for s in SUBTOPICS)
    print(f"named traps:       {named_traps}")
    if written_sub:
        print(f"coverage:          {len(written_sub)}/{len(SUBTOPICS)} subtopics "
              f"= {100 * len(written_sub) / len(SUBTOPICS):.1f}%")
    return 0


def cmd_ev(_: argparse.Namespace) -> int:
    """The three marking numbers the pedagogy rests on."""
    from .items import expected_ev

    print("XAT 2026 marking, measured by expected_ev():")
    print(f"  guess, 5 options, -0.25   EV = {expected_ev():+.4f}"
          f"   <- the paper's equilibrium")
    print(f"  guess, 4 options, -0.25   EV = "
          f"{expected_ev(options=4):+.4f}   <- a 4-option paper PAYS you to "
          f"guess, which is why D5/D6 of the reference project do not carry")
    print(f"  the 9th blank, unattempted EV = {expected_ev(blanks=9):+.4f}"
          f"   <- strictly worse than guessing")
    print(f"  ten blanks, unattempted    EV = {expected_ev(blanks=10):+.4f}")
    return 0


def cmd_coverage(_: argparse.Namespace) -> int:
    """The coverage ledger: trained, written, pending, and block capacity.

    DERIVED from `syllabus` and `registry` -- never maintained by hand. MEASURED
    2026-10-02: `weightage` printed `written: 4`, which is the ITEM count, beside
    two SUBTOPIC counts on a project with 40 subtopics. `docs/COVERAGE.md` is a
    committed snapshot of THIS function and a test compares them, so the document
    cannot drift from the code.
    """
    from .coverage import render_coverage

    print(render_coverage())
    return 0


def cmd_shapes(_: argparse.Namespace) -> int:
    """Print the paper shapes and the level quotas they imply."""
    from .items import FULL_MOCK, PRACTICE_SHAPE, QUANT_MOCK

    for shape in (LESSON_SHAPE, PRACTICE_SHAPE, QUANT_MOCK, FULL_MOCK):
        q = shape.quota()
        print(f"{shape.name:10s} {shape.questions:3d} questions  "
              f"negative marking: {shape.negative_marking!s:5s}  "
              f"options: {shape.options}")
        print(f"           quota {dict((k.value, v) for k, v in q.items())}")
    print()
    print("level recipes (requested of CODE, never of a model):")
    for lv, r in LEVEL_RECIPES.items():
        print(f"  {lv.value:11s} {r}")
    print()
    print(f"subtopics by stratum: "
          f"{ {k.value: v for k, v in stratum_counts().items()} }")
    return 0


def make_server(root: Path, port: int) -> http.server.ThreadingHTTPServer:
    """A static server for one directory, on loopback, that cannot be wedged.

    MEASURED 2026-10-02, from the owner's report that the page "takes too much
    time to load". The assets were never the cause: lesson.js served in 1.4ms,
    paper.json in 2.8ms, index.html in 4.8ms -- about 12ms for all four.

    The cause was `socketserver.TCPServer`, which handles ONE connection at a
    time. `SimpleHTTPRequestHandler` blocks reading a request until one arrives,
    so a client that opens a socket and then holds it idle -- which a browser
    does routinely, for favicon, preconnect or prefetch -- parks the only thread
    forever and every subsequent request queues behind it. The server log showed
    a browser session ending at 10:21:42 and then nothing being served at all;
    a plain `curl` after that timed out at 5 seconds. The page had stopped
    loading permanently, with no error and no exit.

    Threading fixes the class of bug, and `daemon_threads` plus a handler
    `timeout` stop an idle socket from pinning a worker either.
    """
    import functools
    import http.server

    class _Handler(http.server.SimpleHTTPRequestHandler):
        # An idle socket must not be able to hold a thread open forever.
        timeout = 30

        def end_headers(self) -> None:
            # A learner must never run yesterday's script against today's
            # lesson. `lesson.js` is a <script src>, so the browser is free to
            # reuse a cached copy indefinitely -- and the symptom is a page that
            # renders half of what is on disk, with no error anywhere.
            self.send_header("Cache-Control", "no-store")
            super().end_headers()

    class _Server(http.server.ThreadingHTTPServer):
        daemon_threads = True
        allow_reuse_address = True

    handler = functools.partial(_Handler, directory=str(root))
    return _Server(("127.0.0.1", port), handler)


def cmd_serve(args: argparse.Namespace) -> int:
    """Serve the bundle over http.

    A real server is forbidden by D10 -- the bundle is static and `file://` is
    the normal way to read it -- but `fetch()` of a sibling JSON is blocked by
    the browser's origin rules on `file://`, so a loopback static server is the
    honest way to sit a lesson. It binds loopback only and serves one directory.

    See `make_server` for why it is threaded. That function is not an
    optimisation: the single-threaded version wedges permanently the first time
    a browser holds a connection open, and the symptom is a page that never
    loads and never errors.
    """
    root = Path(args.lesson).resolve()
    if not (root / "index.html").exists():
        print(f"no index.html in {root}. Build it first: "
              f"xat-practice build", file=sys.stderr)
        return 1
    httpd = make_server(root, args.port)
    print(f"serving {root} at http://127.0.0.1:{args.port}/  (ctrl-c to stop)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print()
    finally:
        httpd.server_close()
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="xat-practice", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("gates", help="run the gate suite on Lesson 1").set_defaults(
        fn=cmd_gates)
    sub.add_parser("levels", help="derived level + drivers per item").set_defaults(
        fn=cmd_levels)
    sub.add_parser("build", help="build the static lesson bundle").set_defaults(
        fn=cmd_build)
    sub.add_parser("agents", help="rebuild opencode.json").set_defaults(
        fn=cmd_agents)
    sub.add_parser("weightage", help="topic weight model + self-check").set_defaults(
        fn=cmd_weightage)
    sub.add_parser("ev", help="the marking numbers the pedagogy rests on").set_defaults(
        fn=cmd_ev)
    sub.add_parser("shapes", help="paper shapes, quotas, level recipes").set_defaults(
        fn=cmd_shapes)
    sub.add_parser("coverage", help="trained / written / pending, and block capacity"
                   ).set_defaults(fn=cmd_coverage)

    s = sub.add_parser("serve", help="serve a lesson over loopback http")
    s.add_argument("--port", type=int, default=8000)
    s.add_argument("--lesson", default=str(bundle.OUT_DIR))
    s.set_defaults(fn=cmd_serve)

    args = p.parse_args(argv)
    return int(args.fn(args))


if __name__ == "__main__":
    raise SystemExit(main())
