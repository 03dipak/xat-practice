"""The package must IMPORT and the suite must COLLECT.

MEASURED 2026-10-02, twice in one session. `syllabus.PAPER_SHAPE` was deleted while
`menu.py` kept importing it. `uv run ruff check src` **passed** — ruff cannot see a
name deleted from another module — while `import xat_practice.cli` raised
`ImportError` and four test modules failed to collect.

Three separate reviewers of that change noticed a broken package in a working tree
that linted clean. A green linter is not a green build.

So this file makes the import path a gate rather than a habit, and it is cheap: an
import and a `--collect-only` over the whole suite. Both are run as SUBPROCESSES on
purpose — importing `xat_practice.cli` inside this process would succeed even if the
installed console script's entry point were broken.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYTHON = str(ROOT / ".venv" / "bin" / "python")


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=300)


def test_the_package_imports():
    """`import xat_practice.cli` is the shortest path to every module.

    MEASURED: this is the exact command that failed while `ruff` passed.
    """
    proc = _run([PYTHON, "-c", "import xat_practice.cli"])
    assert proc.returncode == 0, (
        "the package does not import, so NOTHING in it can be measured. "
        "`ruff` will not catch this: it cannot see a name deleted from another "
        f"module.\n{proc.stdout}\n{proc.stderr}"
    )


def test_every_module_imports_on_its_own():
    """One at a time, so a cyclic or side-effecting import is named rather than
    hidden behind whichever module happened to be imported first."""
    modules = sorted(p.stem for p in (ROOT / "src" / "xat_practice").glob("*.py")
                     if p.stem != "__init__")
    assert modules, "no modules found -- has the package moved?"
    bad: list[str] = []
    for name in modules:
        proc = _run([PYTHON, "-c", f"import xat_practice.{name}"])
        if proc.returncode != 0:
            bad.append(f"  xat_practice.{name}: {proc.stderr.strip().splitlines()[-1]}")
    assert not bad, "modules that do not import:\n" + "\n".join(bad)


def test_the_whole_suite_collects():
    """`--collect-only` with the BARE console script.

    This is the second half of the lesson: the seven tests that do
    `from tests.test_gates import at_level` only worked under `python -m pytest`
    until `pythonpath = ["."]` was added, and nobody noticed for a session. Running
    the short form here means the form a reader is most likely to type is the form
    that is checked.
    """
    proc = _run([str(ROOT / ".venv" / "bin" / "pytest"), "--collect-only", "-q",
                 "-p", "no:cacheprovider", "--no-cov"])
    assert proc.returncode == 0, (
        "the suite does not COLLECT, which is different from failing and is the "
        "state a broken import leaves behind.\n"
        f"{proc.stdout[-2000:]}\n{proc.stderr[-2000:]}"
    )
    tail = proc.stdout.strip().splitlines()[-1]
    assert "test" in tail and ("collected" in tail or "no tests" in tail), (
        f"could not read a collected-test count from {tail!r}"
    )


def test_no_source_module_still_names_PAPER_SHAPE():
    """The specific shape of the 2026-10-02 break, as a standing check.

    `PAPER_SHAPE` was DELETED and `menu.py` + `coverage.py` kept importing it.

    Parsed with `ast`, not grepped. MEASURED 2026-10-02, twice in one sitting:
      * a grep for any bare occurrence fired on a DOCSTRING that names the deleted
        constant to explain why it was deleted -- correct code, false alarm;
      * a grep that also covered `blank_penalty_after=` fired on a field that had
        MOVED to `PartSpec` rather than one that was deleted.

    Both failures have the same lesson: a text search cannot tell a name in prose
    from a name in code, and a check that fires on correct code teaches its reader
    to ignore it. `ast` can, so this does.

    The field-level guard ("a section must not carry the clock or the blank rule")
    is a dataclass-field assertion, and lives where it can be exact:
    `test_no_section_may_carry_the_parts_clock_or_blank_rule`.
    """
    import ast

    banned = "PAPER_SHAPE"
    offenders: list[str] = []
    for path in sorted((ROOT / "src" / "xat_practice").glob("*.py")):
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            hit = None
            if isinstance(node, ast.Name) and node.id == banned:
                hit = "name"
            elif isinstance(node, ast.Attribute) and node.attr == banned:
                hit = "attribute"
            elif isinstance(node, ast.alias) and (node.name == banned
                                                 or (node.asname == banned)):
                hit = "import"
            if hit:
                offenders.append(f"  {path.name}:{node.lineno} {hit}")
    assert not offenders, (
        "PAPER_SHAPE was deleted in favour of EXAMS/PARTS/SECTIONS and these are "
        "CODE references to it (docstrings naming it to explain its deletion are "
        "fine, and are not matched):\n" + "\n".join(offenders)
    )
