#!/usr/bin/env python3
"""Run the UI probe in a real headless Chromium and report what the browser did.

WHY THIS EXISTS. `lesson.js` did not parse for the whole of Wave 1 -- an
apostrophe in prose, `item's`, closed a JavaScript string literal -- so the
browser executed none of the file and the page showed only the static HTML. The
lesson had never been clickable, not once, and 161 tests passed throughout because
every one of them asserted on the file's TEXT.

A static bundle's correctness is not a property of its text. It is a property of
what a browser does when it loads it, so the artefact is rendered and driven here
rather than read.

The method is lifted from the sibling project `photos_graphics`, where the same
class of defect had already produced a green suite: "all the earlier tests were
static string assertions, and a script that threw ReferenceError before measuring
once had a green suite. This executes the real script."

    .venv/bin/python tools/ui_probe.py              # check, exit 1 on any failure
    .venv/bin/python tools/ui_probe.py --shot-dir DIR  # PNGs of each stage
    .venv/bin/python tools/ui_probe.py --keep       # leave the temp dir behind

Exit codes: 0 every check passed. 1 a check failed. 2 no usable browser, so
nothing was proven -- deliberately NOT 0, because a check that cannot run must not
be reported as a pass.
"""

from __future__ import annotations

import argparse
import html as html_mod
import json
import re
import shutil
import socket
import subprocess
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROBE = ROOT / "tools" / "ui_probe.html"
#: The bundle under test. DERIVED, never hardcoded.
#:
#: MEASURED 2026-10-02: this was `out/lesson-01`, which was correct only while
#: there was exactly one lesson and wrong the moment there were two. A UI check
#: pointed at a directory nobody builds is a UI check that silently stops testing
#: anything, so the path comes from the registry.
def _registry():
    import sys as _sys

    _sys.path.insert(0, str(ROOT / "src"))
    from xat_practice.registry import LESSONS

    return LESSONS


def _bundle_dir(lesson_id: str | None = None):
    from xat_practice.bundle import out_dir

    lessons = _registry()
    if lesson_id is None:
        return out_dir(lessons[0].lesson_id)
    for lesson in lessons:
        if lesson.lesson_id == lesson_id:
            return out_dir(lesson_id)
    raise SystemExit(
        f"unknown lesson {lesson_id!r}. Registered: "
        + ", ".join(x.lesson_id for x in lessons)
    )


#: Resolved from argv by `main`, because the checks must be runnable against ANY
#: registered lesson. MEASURED 2026-10-02: this was `LESSONS[0]` evaluated at
#: import, so `47/47` was a statement about Lesson 1 alone and said nothing about
#: every other bundle -- the coverage-floor defect with a green tick, one level up.
BUNDLE = _bundle_dir()


def find_browser() -> str | None:
    """The headless shell Playwright installed, or anything Chromium-shaped.

    MEASURED: this box has `~/.cache/ms-playwright/chromium_headless_shell-*/`.
    A probe that silently skips when it cannot find a browser is worse than no
    probe, so a miss is exit 2 and never a pass."""
    for name in ("chromium", "chromium-browser", "google-chrome",
                 "google-chrome-stable", "headless_shell"):
        found = shutil.which(name)
        if found:
            return found
    cache = Path.home() / ".cache" / "ms-playwright"
    if cache.is_dir():
        hits = sorted(cache.glob("chromium_headless_shell-*/chrome-linux/"
                                 "headless_shell"))
        if hits:
            return str(hits[-1])
    return None


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def stage(tmp: Path, expected: dict[str, int]) -> Path:
    """A served copy of the built bundle plus the probe, with the keys injected.

    The expected keys come from `answerkey.json`, i.e. from the keys the SOLVER
    recomputed. Injecting them is what lets the probe assert that the browser's
    own verdict agrees with the solver rather than with itself."""
    for name in ("lesson.js", "paper.json", "answerkey.json", "style.css"):
        shutil.copy(BUNDLE / name, tmp / name)
    key = json.loads((BUNDLE / "answerkey.json").read_text())["items"]
    expected = {i: key[i]["k"] for i in key}

    # The teach card and question 1, read from the BUNDLE UNDER TEST.
    #
    # MEASURED 2026-10-02: the probe asserted Lesson 1's formula, Lesson 1's
    # legend words and Lesson 1's principal, written into the HTML. Run against
    # Lesson 2 it failed 4 checks that were correct and passed every leak check
    # vacuously, because it was looking for a key that Lesson 2 does not have.
    # A leak check that cannot see the lesson's own answer is not a leak check.
    # So both the card's content and Q1's key text and numbers now travel with the
    # probe, read from the same files the page is served from.
    paper = json.loads((BUNDLE / "paper.json").read_text())
    teach_block = paper.get("teach") or {}
    first = paper["items"][0]
    first_key = key[first["id"]]
    q1 = {
        "key_text": first_key.get("key_text", ""),
        "numbers": sorted(set(_numbers(first.get("stem", "")))),
    }
    # THE REAL PAGE, NOT A COPY OF ITS SHELL.
    #
    # MEASURED 2026-10-02: `ui_probe.html` carried its own hand-written `<main>` --
    # its own `<h1>Lesson 1 &middot; Simple Interest</h1>`, its own `.rungs`, its own
    # `#stage` -- and only borrowed `lesson.js`. So the probe was auditing a
    # DUPLICATE of the markup, kept in sync by hand, and it had already drifted: its
    # heading still said "Lesson 1 - Simple Interest" on the GEOMETRY lesson, and it
    # had no back link at all. Two copies of a shell are two rules that can disagree,
    # which is the defect this repo keeps paying for.
    #
    # So the probe now starts from the served `index.html` and injects only itself:
    # the one script tag, plus a `#probe-out` element to read the verdict back from.
    index = (BUNDLE / "index.html").read_text()
    probe_js = PROBE.read_text()
    assert "<!-- EXPECTED is injected" in probe_js, \
        "the probe lost its injection point"
    inject = (
        "<script>const EXPECTED = " + json.dumps(expected) + ";window.EXPECTED="
        "EXPECTED;window.TEACH=" + json.dumps(teach_block) + ";window.Q1="
        + json.dumps(q1) + ";</script>\n"
    )
    probe_js = probe_js.replace(
        "<!-- EXPECTED is injected by tools/ui_probe.py before this script runs.",
        inject + "<!-- injected by tools/ui_probe.py; the original note"
        " follows.", 1)
    # Lift the probe's own <script> blocks out of its file, so the page under test
    # keeps ITS OWN markup and gains only the probe.
    blocks = re.findall(r"<script>(.*?)</script>", probe_js, re.S)
    assert blocks, "the probe has no inline script to inject"
    injected = inject + "\n".join(f"<script>{b}</script>" for b in blocks)
    html = index.replace("</body>", f'<h1 id="probe-out">PENDING</h1>'
                                   f"{injected}\n</body>")
    assert 'id="probe-out"' in html, "failed to add the element the verdict is read from"
    (tmp / "index.html").write_text(html)
    return tmp


def _numbers(text: str) -> list[str]:
    """The numeric literals in a stem, comma-formatted both ways.

    `'14,400'` has to be found when the card says `14400`, and both forms are
    returned because the leak check compares against CARD text, which is free to
    format differently from the stem.
    """
    out: list[str] = []
    for raw in re.findall(r"\d[\d,]*(?:\.\d+)?", text):
        out.append(raw)
        if "," in raw:
            out.append(raw.replace(",", ""))
    return out


def shot_pages(tmp: Path, browser: str, out_dir: Path, port: int,
               timeout: int) -> list[str]:
    """Photograph the REAL page at each stage, with the real stylesheet.

    The probe page carries no CSS, so its screenshots are unstyled text -- a fine
    DOM and a useless visual record. `index.html` has the CSS but cannot be
    photographed mid-flow, because nothing clicks for it.

    So each stage gets a copy of the real `index.html` with a small driver
    appended. The driver only ever CLICKS -- it never reaches into `lesson.js`,
    which is inside an IIFE and deliberately has no public surface. That is the
    point: the photograph is taken along the path a learner's mouse takes.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    drivers = {
        "start": "/* nothing: the first screen as it loads */",
        "options": """
      await waitForEl(() => document.querySelector('.stem') &&
        !document.querySelector('.stem').classList.contains('pending'));
      document.querySelector('[data-conf="sure"]').click();
      document.getElementById('reveal').click();
""",
        "result": """
      await waitForEl(() => document.querySelector('.stem') &&
        !document.querySelector('.stem').classList.contains('pending'));
      document.querySelector('[data-conf="sure"]').click();
      document.getElementById('reveal').click();
      await waitForEl(() => document.querySelectorAll('.opt').length === 5);
      document.querySelectorAll('.opt')[1].click();
      document.getElementById('check').click();
      await waitForEl(() => document.querySelector('.verdict'));
""",
    }
    preamble = """
<script>
async function waitForEl(fn, ms) {
  const t0 = Date.now();
  while (Date.now() - t0 < (ms || 8000)) {
    if (fn()) return true;
    await new Promise((r) => setTimeout(r, 50));
  }
  return false;
}
(async () => {
"""
    written: list[str] = []
    for stage, body in drivers.items():
        html = (tmp / "index.html").read_text()
        if stage != "start":
            html = html.replace(
                "</body>",
                preamble + body + "})();\n</script>\n</body>", 1)
        page = f"_shot_{stage}.html"
        (tmp / page).write_text(html)
        png = out_dir / f"{stage}.png"
        port_note = ""
        try:
            subprocess.run(
                [browser, "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
                 "--window-size=900,1000", "--virtual-time-budget=9000",
                 f"--screenshot={png}",
                 # http, NOT file://. MEASURED: the first attempt built the URL
                 # from tmp.as_uri(), and the page then failed to load at all --
                 # a browser refuses fetch() of a sibling JSON over file://, so
                 # every shot was of the error card.
                 f"http://127.0.0.1:{port}/{page}"],
                capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            port_note = f" {stage}: TIMED OUT"
        if png.exists():
            written.append(str(png))
        else:
            written.append(f"{png} NOT WRITTEN{port_note}")
    return written


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--shot-dir", help="write start/options/result PNGs here")
    ap.add_argument("--keep", action="store_true", help="leave the temp dir")
    ap.add_argument("--timeout", type=int, default=60)
    ap.add_argument(
        "--lesson",
        help="lesson_id to check, e.g. lesson-02-geometry-similarity. "
             "Defaults to the first registered lesson.",
    )
    args = ap.parse_args(argv)

    global BUNDLE
    if args.lesson:
        BUNDLE = _bundle_dir(args.lesson)
    print(f"bundle: {BUNDLE}")

    for required in (PROBE, BUNDLE / "lesson.js", BUNDLE / "answerkey.json",
                     BUNDLE / "style.css"):
        if not required.exists():
            # The path is printed absolute on purpose. MEASURED: this printed
            # `required.relative_to(ROOT)`, which raises ValueError when the
            # bundle is not inside the project -- so a caller pointing at a
            # directory elsewhere got a traceback instead of the instruction it
            # needed. A diagnostic that crashes is not a diagnostic.
            print(f"missing {required} -- run `.venv/bin/xat-practice build` "
                  f"first", file=sys.stderr)
            return 2

    browser = find_browser()
    if not browser:
        print("NO_BROWSER: no Chromium or headless_shell found, so the UI was "
              "NOT checked. That is not a pass.", file=sys.stderr)
        return 2

    import tempfile

    sys.path.insert(0, str(ROOT / "src"))
    from xat_practice.cli import make_server

    tmp = Path(tempfile.mkdtemp(prefix="xat-ui-probe-"))
    stage(tmp, {})
    port = free_port()
    httpd = make_server(tmp, port)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()

    base = f"http://127.0.0.1:{port}"
    cmd = [browser, "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
           "--virtual-time-budget=15000", "--dump-dom", f"{base}/"]

    shot_note = ""
    shots: list[str] = []
    if args.shot_dir:
        # Taken BEFORE the server goes down, because the shot pages have to be
        # served over loopback.
        try:
            shots = shot_pages(tmp, browser, Path(args.shot_dir), port,
                               args.timeout)
        except Exception as exc:  # a screenshot failure must not hide the checks
            shot_note = f"SCREENSHOTS FAILED: {exc!r}"
        else:
            shot_note = ("screenshots: " + ", ".join(shots)
                         + "  (real index.html + real CSS, driven by clicking)")
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              timeout=args.timeout)
    finally:
        httpd.shutdown()
        httpd.server_close()
        if not args.keep:
            shutil.rmtree(tmp, ignore_errors=True)
        else:
            print(f"probe dir kept at {tmp}")

    # Match the RESULT ELEMENT, not the string `PROBE_RESULT::` anywhere in the
    # file -- the probe's own comment mentions it, so a loose regex matches the
    # comment first and reports a nonsense verdict. `html.unescape` because the
    # DOM serialiser escapes the JSON's quotes.
    match = re.search(r'<h1 id="probe-out">(.*?)</h1>', proc.stdout, re.S)
    if not match:
        print("NO_VERDICT: the probe never wrote a result, which means the page "
              "did not run to completion.", file=sys.stderr)
        print(proc.stdout[-2000:], file=sys.stderr)
        print(proc.stderr[-2000:], file=sys.stderr)
        return 1

    text = html_mod.unescape(match.group(1)).strip()
    if not text.startswith("PROBE_RESULT::"):
        print(f"NO_VERDICT: #probe-out says {text[:120]!r}, which is not a "
              "verdict. PENDING means the probe never finished, which is a "
              "failure of the page, not of the probe.", file=sys.stderr)
        return 1

    payload = json.loads(text[len("PROBE_RESULT::"):])
    raw = payload.get("checks")
    # A malformed entry is itself a finding, not a reason to crash. MEASURED:
    # this runner raised KeyError on a check that had been pushed without a
    # name, printed a traceback, and exited 1 -- which looks identical to "a
    # check failed" and tells the reader nothing. A reporting tool that dies on
    # unexpected input is not a gate.
    if not isinstance(raw, list):
        print(f"NO_VERDICT: 'checks' is {type(raw).__name__}, not a list",
              file=sys.stderr)
        return 1
    checks: list[dict] = []
    malformed = 0
    for i, c in enumerate(raw):
        if isinstance(c, dict) and isinstance(c.get("name"), str):
            checks.append(c)
        else:
            malformed += 1
            print(f"  BAD   <unnamed check #{i}>  {json.dumps(c)[:120]}")

    failed = [c for c in checks if not c["pass"]]
    width = max((len(c["name"]) for c in checks), default=10)
    for c in checks:
        mark = "PASS" if c["pass"] else "FAIL"
        detail = f"  {c['detail']}" if c["detail"] else ""
        print(f"  {mark}  {c['name']:<{width}}{detail}")
    print(f"\n{len(checks) - len(failed)}/{len(checks)} UI checks passed"
          f"  (state: {payload['done']}, browser: {Path(browser).name}"
          + (f", {malformed} malformed" if malformed else "") + ")")
    if payload.get("done") != "done":
        print("  the probe did not run to completion, so the checks after the "
              "failure point were never evaluated", file=sys.stderr)
    if shot_note:
        print(shot_note)
    return 1 if (failed or malformed or payload.get("done") != "done") else 0


if __name__ == "__main__":
    raise SystemExit(main())
