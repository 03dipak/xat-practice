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
from .registry import LESSONS, items_written, subtopics_written
from .syllabus import Tier, by_tier, self_check, stratum_counts

if TYPE_CHECKING:
    import http.server


def cmd_gates(_: argparse.Namespace) -> int:
    """Run the gate suite PER LESSON and report per-gate counts.

    Refusal counts are over a NAMED population, because a count with no
    denominator is a lie that looks like a pass.

    MEASURED 2026-10-02, on the first build with two lessons registered. Running
    the suite over the pooled 8 items admitted **0 of 8** and refused two items
    that are individually perfect:

    - `G11` refused `L2-F`, "foundation over quota (1/1)". It apportions the
      20-item PAPER mix, and `MIX_ENFORCEMENT_FLOOR` is 8 -- a number chosen to
      mean "smaller than a paper". **Two lessons now reach it**, so a paper-shaped
      rule ran against something that is not a paper. This is D12's defect one
      step up: G11 was removed from lessons, and nothing stopped the *pool of
      lessons* from becoming the new fake paper.
    - `G15` refused `L1-F` because answering B throughout both lessons scores
      above its ceiling. True of the pool, and meaningless: no candidate is ever
      given both lessons in one sitting, and no XAT paper holds two Simple Interest
      items and two Geometry items at the same key indices.

    Neither gate is loosened. A paper rule is given a paper, so each lesson is
    gated on its own and the refusal rate is reported per lesson, where the
    denominator is unambiguous. The pooled figure is printed as ITEMS ONLY and
    explicitly not as a pass.
    """
    total_items = total_refused = 0
    failed = False
    for lesson in LESSONS:
        res = gates.run(lesson.items)
        total_items += len(lesson.items)
        total_refused += len(res.refusals)
        failed = failed or bool(res.refusals)
        # lesson_id AND subtopic_id. `lesson_id` is the bundle directory and the
        # URL a learner is given, so dropping it from the report when this verb
        # went per-lesson made two lessons indistinguishable in the output.
        print(f"population: {len(lesson.items)} items = 1 lesson, "
              f"{lesson.lesson_id}, {lesson.subtopic_id}")
        print(f"  admitted: {len(res.admitted)}/{len(lesson.items)}")
        print(f"  refused:  {len(res.refusals)}  "
              f"(rate {res.refusal_rate} over {len(lesson.items)})")
        for gate, n in sorted(res.by_gate().items()):
            if n:
                print(f"    {gate}: {n}")
        for r in res.refusals:
            print(f"    REFUSED {r.gate} {r.item_id}: {r.detail}")
    print(f"\nlessons:    {len(LESSONS)}   items gated: {total_items}   "
          f"refused: {total_refused} across {total_items}")
    print("NOTE: the pooled total above is an item count, NOT a score. Paper-shaped "
          "gates (G11 mix, G15 key position) are run per lesson on purpose; "
          "pooling two lessons into one population invents a paper that is never "
          "sat.")
    return 1 if failed else 0


def cmd_levels(_: argparse.Namespace) -> int:
    """Print each item's DERIVED level with its drivers.

    The drafter's claimed level is shown beside it when there is one, because a
    disagreement is a refusal (G7) and a silent overwrite would hide it.
    """
    # Per lesson, for the reason measured in `cmd_gates`: G11 and G15 are paper
    # rules and a pool of lessons is not a paper.
    for lesson in LESSONS:
        print(f"\n{lesson.lesson_id}  ({lesson.subtopic_id})")
        res = gates.run(lesson.items)
        for item in lesson.items:
            rep = res.reports[item.id]
            claim = (f"claimed {item.claimed_level}" if item.claimed_level
                     else "no claim")
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
    # A LESSON ID, not a path. MEASURED 2026-10-02: this took a filesystem path
    # and defaulted to `bundle.OUT_DIR`, which is `out/` -- a directory of lesson
    # directories. Serving it gave a directory listing, so with two lessons the
    # learner had to know the exact `out/lesson-02-...` path to reach the second
    # one at all, and the default served nothing.
    #
    # It still accepts a path, because that is how you inspect a bundle that is not
    # in the registry, and because a path is what `build` prints.
    resolved = Path(args.lesson).resolve()
    if (resolved / "index.html").exists():
        root, label = resolved, str(resolved)
    else:
        known = {x.lesson_id for x in LESSONS}
        if args.lesson not in known:
            print(f"no lesson {args.lesson!r} and no index.html in {resolved}. "
                  f"Registered: {', '.join(sorted(known))}. Build first with "
                  f"`xat-practice build`.", file=sys.stderr)
            return 1
        from xat_practice.bundle import out_dir

        root = out_dir(args.lesson)
        label = args.lesson
        if not (root / "index.html").exists():
            print(f"{args.lesson} is registered but not built: no index.html in "
                  f"{root}. Run `xat-practice build`.", file=sys.stderr)
            return 1

    httpd = make_server(root, args.port)
    print(f"serving {label} at http://127.0.0.1:{args.port}/  (ctrl-c to stop)")
    print("every lesson, one port each:")
    for lesson in LESSONS:
        print(f"  .venv/bin/xat-practice serve --lesson {lesson.lesson_id}")
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
    s.add_argument(
        "--lesson",
        default=LESSONS[0].lesson_id,
        help="lesson_id from the registry, or a path to a bundle directory. "
             f"One of: {', '.join(x.lesson_id for x in LESSONS)}",
    )
    s.set_defaults(fn=cmd_serve)

    args = p.parse_args(argv)
    return int(args.fn(args))


if __name__ == "__main__":
    raise SystemExit(main())
