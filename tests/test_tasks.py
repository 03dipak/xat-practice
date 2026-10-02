"""The task board must be GENERATED, and every record must be answerable.

`docs/TASKS.csv` is a view of `xat_practice/tasks.py`. MEASURED 2026-10-02: the
project had a narrative `todo.txt` and, separately, five reviews whose verdicts
lived in prose. Three places to change one task is how they drift -- so the records
have ONE home and the file is derived, with this test comparing them.
"""

from __future__ import annotations

import csv
import io
import re

import pytest

from xat_practice import tasks as T

CSV_PATH = str(__import__("pathlib").Path(__file__).resolve().parent.parent / "docs" / "TASKS.csv")


def test_the_csv_matches_the_records():
    """The staleness test. `uv run xat-practice tasks --write` regenerates it."""
    assert CSV_PATH.endswith("/docs/TASKS.csv"), CSV_PATH
    from pathlib import Path

    path = Path(CSV_PATH)
    assert path.exists(), (
        "docs/TASKS.csv is missing. Run `uv run xat-practice tasks --write`. It is "
        "GENERATED: the records live in xat_practice/tasks.py, so a task has one "
        "home and the CSV is a view of it."
    )
    assert path.read_text() == T.render_csv(), (
        "docs/TASKS.csv has drifted from the records. Re-run "
        "`uv run xat-practice tasks --write`. Do not hand-edit the CSV."
    )


def test_the_csv_is_readable_by_a_csv_reader():
    """A CSV that only this project's own writer can read is not a board."""
    rows = list(csv.DictReader(io.StringIO(T.render_csv())))
    assert len(rows) == len(T.TASKS)
    for row, task in zip(rows, T.TASKS, strict=True):
        assert row["id"] == task.id
        # Every field must survive quoting: prose containing commas and newlines
        # is the whole point of the `why` column.
        assert row["why"], f"{task.id} has no reason"


@pytest.mark.parametrize("task", T.TASKS, ids=lambda t: t.id)
def test_every_record_is_answerable(task):
    """No record may be declared done by a task with nothing to check.

    MEASURED 2026-10-02: `test_the_reveal_button_starts_disabled` asserted that a
    line reading `...disabled = false` existed -- the ENABLING line -- and passed
    while the button was never disabled. A record with no falsifying input is that
    failure waiting to happen.
    """
    for col in ("type", "epic", "priority", "status", "owner", "evidence",
                "title", "why", "acceptance", "falsifying_input"):
        assert getattr(task, col).strip(), f"{task.id}: {col} is empty"
    assert task.priority in T.PRIORITY_LEGEND, (
        f"{task.id}: priority {task.priority!r} has no meaning; add it to "
        "PRIORITY_LEGEND or the column is a mood"
    )
    assert task.status in T.STATUS_LEGEND, f"{task.id}: unknown status {task.status!r}"
    # `owner` must be a role that EXISTS in the generated agent config, or a task
    # is assigned to nobody.
    import json
    from pathlib import Path

    cfg = json.loads((Path(CSV_PATH).parent.parent / "opencode.json").read_text())
    agents = set(cfg.get("agent", {}))
    assert task.owner in agents or task.owner == "mentor", (
        f"{task.id}: owner {task.owner!r} is not one of the "
        f"{len(agents)} roles in opencode.json"
    )


def test_blockers_point_at_records_that_exist():
    ids = {t.id for t in T.TASKS}
    for task in T.TASKS:
        for b in filter(None, (x.strip() for x in task.blocked_by.split(","))):
            assert b in ids, f"{task.id} is blocked by {b}, which is not a record"
    # And nothing marked BLOCKED may name no blocker -- that is a stall, not a
    # block.
    for task in T.TASKS:
        if task.status == "BLOCKED":
            assert task.blocked_by.strip(), (
                f"{task.id} is BLOCKED with nothing blocking it"
            )


def test_a_circular_block_chain_is_refused():
    """A board whose blockers form a cycle has no startable task and looks fine."""
    blocked = {t.id: [x.strip() for x in t.blocked_by.split(",") if x.strip()]
               for t in T.TASKS}

    # Path-scoped, NOT a global `seen`. MEASURED 2026-10-02: the first version used
    # one `seen` set for every walk, so TASK-014 -- reachable by two separate chains,
    # which is a DAG DIAMOND and not a cycle -- raised "cycle in the blocker graph"
    # and would have had a real fix reverted as a bug. A cycle is a node on the
    # CURRENT path.
    def walk(node: str, path: tuple[str, ...]) -> None:
        if node in path:
            raise AssertionError(
                f"cycle in the blocker graph: {' -> '.join([*path, node])}")
        for nxt in blocked.get(node, []):
            walk(nxt, (*path, node))

    for node in blocked:
        walk(node, ())


def test_the_board_renders_without_inventing_work():
    out = T.render_board()
    assert "OPEN, worst first" in out
    assert out.count("P0") <= len(T.TASKS) + 4, "the legend is longer than the board"
    # Every id appears exactly once in the CLOSED list, and open ids appear once
    # in the OPEN list.
    # Once as its OWN row. A task may also be named inside another row's
    # `blocked by`, and that is not a duplicate -- asserting a single occurrence
    # would fail any board that has a dependency.
    rows = [ln for ln in out.splitlines() if re.search(r"TASK-\d{3}", ln)]
    for task in T.TASKS:
        own = [ln for ln in rows
               if re.search(rf"\b{task.id}\b", ln)
               and not re.search(rf"blocked by .*\b{task.id}\b", ln)]
        assert len(own) == 1, (
            f"{task.id} has {len(own)} row(s) of its own on the board:\n"
            + "\n".join(own)
        )


def test_the_csv_has_no_stray_newlines_inside_a_cell():
    """A newline inside a quoted CSV cell is legal but breaks every naive reader.

    MEASURED 2026-10-02: not a defect found in this project -- a rule kept so the
    first naive `cut`/`awk` over the board does not silently produce nonsense.
    """
    rows = list(csv.DictReader(io.StringIO(T.render_csv())))
    for row in rows:
        for col, value in row.items():
            assert "\n" not in value, f"{row['id']}: {col} contains a newline"
            assert not re.search(r"\s{3,}", value), (
                f"{row['id']}: {col} has a run of spaces, usually a wrapped sentence"
            )
