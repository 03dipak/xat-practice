"""The suite must pass under BOTH legal ways to start pytest.

MEASURED 2026-10-02. `pytest -q` failed **7 of 299** with
`ModuleNotFoundError: No module named 'tests'`. `python -m pytest` passed all
292. Same interpreter, same venv, same code — the only difference is that `-m`
puts the CWD on `sys.path[0]` and the `pytest` console script does not.

`tests/test_api.py` and `tests/test_lesson1.py` do
`from tests.test_gates import at_level`, which needs the project root
importable, and `tests/` has no `__init__.py`.

It shipped because **every** documented command used `python -m pytest`, so the
suite had only ever run in one of its two legal forms. Then the documented
commands moved to `uv run pytest` — the short form — and the 7 failures appeared
immediately. That is the whole lesson: a suite with an undeclared import
dependency looks identical from inside and behaves differently outside the command
you always type.

So this file does not assert that `pythonpath` is set. It runs the **short** form
against the real modules that do the offending import. A config assertion would
pass on a typo; this cannot.

ONE TRAP, already hit once while writing it: a probe file placed in a tmp dir
cannot test this. `pythonpath` is resolved **relative to pytest's rootdir**, and
pointing pytest at a file outside the project moves the rootdir to the tmp dir —
so the import fails for a reason that has nothing to do with the setting being
tested. Hence: no tmp_path, and the real test modules instead.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PYTEST = str(ROOT / ".venv" / "bin" / "pytest")
PYTHON = str(ROOT / ".venv" / "bin" / "python")

#: The two modules that were failing. Named explicitly so that if they are split
#: or renamed, this file FAILS rather than silently testing nothing -- which is
#: how a regression check becomes decoration.
IMPORTERS = ("tests/test_api.py", "tests/test_lesson1.py")


def _short(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([PYTEST, "-q", "--no-cov", "-p", "no:cacheprovider",
                           *args],
                          cwd=ROOT, capture_output=True, text=True, timeout=300)


def _long(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([PYTHON, "-m", "pytest", "-q", "--no-cov",
                           "-p", "no:cacheprovider", *args],
                          cwd=ROOT, capture_output=True, text=True, timeout=300)


def test_the_modules_that_broke_are_the_ones_named_here():
    """The premise, asserted first.

    If those files stop importing `tests.*` then `pythonpath = ["."]` is defending
    nothing and this file is theatre.
    """
    for rel in IMPORTERS:
        text = (ROOT / rel).read_text()
        assert "from tests." in text, (
            f"{rel} no longer imports `tests.*`, so the pythonpath setting and "
            "this file have nothing left to check. Update IMPORTERS deliberately."
        )


@pytest.mark.parametrize("rel", IMPORTERS)
def test_the_short_pytest_form_can_import_the_tests_package(rel):
    """Run `pytest` — NOT `python -m pytest` — over the real module, in the real
    rootdir. This is the falsifying input: before `pythonpath = ["."]` it failed
    with `ModuleNotFoundError: No module named 'tests'`."""
    proc = _short(rel)
    assert proc.returncode == 0, (
        "the SHORT form of pytest cannot import `tests.*`, so the 7 tests that do "
        "`from tests.test_gates import at_level` only pass under the long form.\n"
        "Fix: `pythonpath = [\".\"]` under [tool.pytest.ini_options] in "
        f"pyproject.toml.\n{proc.stdout}\n{proc.stderr}"
    )


def test_the_two_forms_agree_on_the_population():
    """Run both collect-ions and compare. Separate from the parameterised
    collector above so the comparison cannot be satisfied by one form alone."""
    counts = {}
    for label, runner in (("short", _short), ("long", _long)):
        proc = runner("--collect-only")
        assert proc.returncode == 0, f"{label}: {proc.stderr}"
        tail = proc.stdout.strip().splitlines()[-1]
        counts[label] = int(tail.split()[0].replace(",", ""))
    assert counts["short"] == counts["long"], (
        f"the two forms collect DIFFERENT numbers of tests: {counts}. One of them "
        "is measuring a different population and reporting it as the suite."
    )
