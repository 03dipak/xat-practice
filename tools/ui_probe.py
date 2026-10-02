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
    .venv/bin/python tools/ui_probe.py --shot PATH  # also write a screenshot
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
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROBE = ROOT / "tools" / "ui_probe.html"
BUNDLE = ROOT / "out" / "lesson-01"


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
    for name in ("index.html", "lesson.js", "paper.json", "answerkey.json"):
        shutil.copy(BUNDLE / name, tmp / name)
    key = json.loads((BUNDLE / "answerkey.json").read_text())["items"]
    expected = {i: key[i]["k"] for i in key}
    html = PROBE.read_text()
    assert "<!-- EXPECTED is injected" in html, "the probe lost its injection point"
    html = html.replace(
        "<!-- EXPECTED is injected by tools/ui_probe.py before this script runs.",
        f"<script>const EXPECTED = {json.dumps(expected)};window.EXPECTED="
        "EXPECTED;</script>\n<!-- injected by tools/ui_probe.py; the original note"
        " follows.", 1)
    (tmp / "ui_probe.html").write_text(html)
    return tmp


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--shot", help="also write a PNG of the first screen here")
    ap.add_argument("--keep", action="store_true", help="leave the temp dir")
    ap.add_argument("--timeout", type=int, default=60)
    args = ap.parse_args(argv)

    for required in (PROBE, BUNDLE / "lesson.js", BUNDLE / "answerkey.json"):
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

    import subprocess

    url = f"http://127.0.0.1:{port}/ui_probe.html"
    cmd = [browser, "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
           "--virtual-time-budget=15000", "--dump-dom", url]
    if args.shot:
        cmd.insert(-1, f"--screenshot={args.shot}")
        cmd.insert(-1, "--window-size=900,760")
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
    if args.shot:
        print(f"screenshot: {args.shot}")
    return 1 if (failed or malformed or payload.get("done") != "done") else 0


if __name__ == "__main__":
    raise SystemExit(main())
