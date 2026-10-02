"""The one command a learner types.

`xat-practice serve` with no arguments asks what you want to work on and serves
it. The learner never assembles a path, never learns what a `lesson_id` is, and
never runs a second command.

THIS IS A PAGE, NOT A PROMPT
-----------------------------
It was a prompt first, and that was wrong. MEASURED 2026-10-02: `serve` defaulted
to the FIRST registered lesson, so anyone who wanted Geometry typed the documented
command and got Simple Interest with nothing saying a choice existed -- safe by
being invisible. The fix was to ASK in the terminal, and the owner rejected that
too: "I don't wanna invest the time in running commands". A CLI menu is the right
shape for a CLI and the wrong shape for someone who wants to think about geometry
rather than about process.

So: `serve` starts immediately, prints one URL, and every choice after that is a
click on a web page. `render_index_html` writes that page to `out/index.html`, and
`serve` serves `out/` as the root so each lesson is at `/<lesson_id>/` -- one
origin, so switching subtopic needs no restart.

`render_menu`, `choose` and `pick` were deleted rather than kept: the prompt had
one caller and that caller is gone, and a function with no caller made to pass by
a test is the coverage-floor defect with extra steps.

THE LEVEL IS THE LEARNER'S CHOICE, NOT THE QUOTA'S
-------------------------------------------------
There are two different things called "a mix", and conflating them is the trap:

* `LEVEL_MIX` (10/25/40/25) is derived from the exam's own timing and is correct
  for a MOCK, which must reproduce the paper's shape. At 20 items it yields
  2/5/8/5.
* A DRILL is level-filtered. A learner who says "give me foundation" gets
  foundation. Quotas do not apply, and `G11` must not be run on it -- a paper rule
  handed a non-paper is the defect behind D12 and D23.

So this menu offers the level the learner asked for, and the mix is applied only
where a paper is being simulated. See `docs/DECISIONS.md` D23/D24.

HONESTY IS THE DEFAULT
----------------------
Every subtopic in the syllabus is listed, and the 38 that have no lesson are
marked `not written` rather than hidden. Hiding them would make the menu look
finished; showing them is the ledger, which is the honest position: **2 of 40**
subtopics are written and this menu says so.
"""

from __future__ import annotations

from dataclasses import dataclass

from .registry import LESSONS
from .syllabus import PAPER_SHAPE, TOPICS, Subtopic

#: Which Part-1 section each topic belongs to. The syllabus trains QA&DI only
#: (D7), so this is the whole truth about the other two sections rather than a
#: guess about them.
SECTION_QA_DI = "QA&DI"


@dataclass(frozen=True, slots=True)
class Entry:
    """One selectable line: a written lesson."""

    lesson_id: str
    topic_id: str
    subtopic_id: str
    label: str
    subtopic_label: str


def written_entries() -> list[Entry]:
    """The lessons that exist, in topic-weight order (heaviest first).

    Sorted by measured topic weight so the learner meets the biggest block
    first -- DI at 6.71 q/yr down to Time & Work at 0.29 -- rather than
    alphabetically, which would put Averages before Data Interpretation for no
    reason a learner could infer.
    """
    subs: dict[str, Subtopic] = {s.id: s for s in _all_subtopics()}
    order = {t.id: -t.weight for t in TOPICS}
    out: list[Entry] = []
    for lesson in LESSONS:
        sub = subs.get(lesson.subtopic_id)
        out.append(Entry(
            lesson_id=lesson.lesson_id,
            topic_id=lesson.subtopic_id.split(":", 1)[0],
            subtopic_id=lesson.subtopic_id,
            label=_topic_name(lesson.subtopic_id.split(":", 1)[0]),
            subtopic_label=sub.name if sub else lesson.subtopic_id,
        ))
    return sorted(out, key=lambda e: (order.get(e.topic_id, 0.0), e.subtopic_id))


def _all_subtopics() -> list[Subtopic]:
    from .syllabus import subtopics

    return list(subtopics().values())


def _topic_name(topic_id: str) -> str:
    """A lesson's topic name, falling back to the id.

    The fallback is reachable: `Lesson.subtopic_id` is a plain string and nothing
    validates that its `topic:` prefix names a declared topic. So a typo would
    otherwise raise deep inside menu rendering, where the learner sees a stack
    trace instead of a menu.
    """
    for t in TOPICS:
        if t.id == topic_id:
            return t.name
    return topic_id


def paper_shape_lines() -> list[str]:
    """The XAT 2026 shape, read from `PAPER_SHAPE` rather than restated."""
    part1 = PAPER_SHAPE["part1"]
    total = PAPER_SHAPE["total_questions"]
    part2 = PAPER_SHAPE["part2"]
    return [
        f"XAT 2026 -- {total} questions, Part 1 is {sum(part1.values())} "
        f"questions in {PAPER_SHAPE['part1_minutes']} minutes with NO sectional "
        f"time limit.",
        f"  QA&DI {part1['qa_di']}   VA&LR {part1['va_lr']}   "
        f"DM {part1['dm']}",
        f"  Part 2 GK {part2['gk']} in {part2['minutes']} minutes -- EXCLUDED from "
        f"the percentile by XLRI, so it is out of scope here.",
        # `:.2f` on both marking figures: Python prints -0.1 for -0.10, and the
        # penaltys are quoted to two decimals everywhere else because "-0.1" and
        # "-0.10" are different-looking numbers for the same value.
        f"  {PAPER_SHAPE['options']} options, "
        f"{PAPER_SHAPE['mark_correct']:+g} correct, "
        f"{PAPER_SHAPE['mark_wrong']:.2f} wrong, and "
        f"{PAPER_SHAPE['blank_penalty']:.2f} per blank after the first "
        f"{PAPER_SHAPE['blank_penalty_after']}.",
    ]


def _len_subtopics() -> int:
    return len(_all_subtopics())



# ---------------------------------------------------------------------------
# the navigator: the page the learner actually lands on
# ---------------------------------------------------------------------------

_NAV_CSS = """
:root{--ink:#12212e;--line:#c9d4de;--bg:#fbfcfd;--ok:#1d7a4c;--warn:#a05a00}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
  font:16px/1.55 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif}
main{max-width:900px;margin:0 auto;padding:28px 20px 60px}
h1{font-size:22px;margin:0 0 4px}
h2{font-size:17px;margin:26px 0 8px}
h3{font-size:15px;margin:0 0 6px;font-weight:600}
p{margin:0 0 10px}
.sub{color:#5b6b7a;margin:0 0 18px}
.box{border:1px solid var(--line);border-radius:8px;padding:14px 16px;margin:0 0 12px;
  background:#fff}
.box.off{background:#f4f6f8;color:#5b6b7a}
.tag{display:inline-block;font-size:11px;letter-spacing:.04em;text-transform:uppercase;
  border:1px solid var(--line);border-radius:4px;padding:2px 6px;margin:0 6px 6px 0}
.tag.ok{border-color:var(--ok);color:var(--ok)}
.tag.no{border-color:var(--line);color:#7a8894}
.lesson{display:flex;flex-wrap:wrap;gap:10px;align-items:center;
  justify-content:space-between;border:1px solid var(--line);border-radius:8px;
  padding:12px 14px;margin:0 0 8px;background:#fff}
.lesson a{color:var(--ink);font-weight:600;text-decoration:none;border-bottom:2px solid var(--ink)}
.levels{font-size:12px;color:#5b6b7a}
ul{margin:6px 0 0;padding-left:18px;color:#5b6b7a}
code{background:#eef2f5;padding:1px 4px;border-radius:3px;font-size:13px}
"""


def render_index_html() -> str:
    """The page at `/`: choose a section, then a subtopic, then a level.

    Navigation lives HERE, in the browser, not in a shell prompt.

    MEASURED 2026-10-02: the first attempt put the choice in the terminal --
    `serve` asked, and the learner typed a number. The owner's objection was
    exact: "I don't wanna invest the time in running commands." A CLI menu is the
    right shape for a CLI and the wrong shape for a learner who wants to think
    about geometry, not about process. So `serve` starts immediately, prints one
    URL, and every subsequent choice is a click.

    Served from `out/`, so each lesson is reachable at `/<lesson_id>/` and its own
    `fetch('paper.json')` still resolves as a sibling -- one origin, no CORS, and
    the learner can switch subtopic without restarting anything. That is also why
    "one lesson per port" stopped being the right shape: switching in the UI
    requires ONE origin.
    """
    from html import escape

    entries = written_entries()
    total = _len_subtopics()
    out: list[str] = []
    out.append("<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">")
    out.append("<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">")
    out.append("<title>XAT Practice &middot; choose a topic</title>")
    out.append(f"<style>{_NAV_CSS}</style></head><body><main>")

    out.append("<h1>XAT Practice</h1>")
    out.append("<p class=\"sub\">Choose a section, then a topic. "
               "Inside a lesson the four levels are tabs &mdash; take them "
               "in any order you like.</p>")

    # The paper, stated so the learner knows what they are aiming at.
    out.append("<div class=\"box\"><h3>The paper</h3><ul>")
    for line in paper_shape_lines():
        out.append(f"<li>{escape(line)}</li>")
    out.append("</ul></div>")

    # SECTION: QA&DI is the one this project trains. The other two are listed and
    # marked, because hiding them would make the project look finished.
    out.append("<h2>Section 1 &mdash; QA&amp;DI</h2>")
    if not entries:
        out.append('<div class="box off"><p>No lessons are written yet, so '
                   "there is nothing to open. Run <code>uv run xat-practice "
                   "build</code> after writing one.</p></div>")
        out.append(f'<p class="sub" style="margin-top:24px">0 of {total} '
                   "subtopics written.</p>")
        out.append("</main></body></html>")
        return "".join(out)
    out.append("<p class=\"sub\">"
               f"{len(entries)} lesson(s) written across "
               f"{len({e.topic_id for e in entries})} topic(s), ordered by "
               "measured questions-per-year.</p>")
    for e in entries:
        out.append(
            f'<div class="lesson"><div><h3>{escape(e.label)}</h3>'
            f'<p class="levels">{escape(e.subtopic_label)}</p></div>'
            f'<a href="{escape(e.lesson_id)}/">Open &rarr;</a></div>')

    out.append("<h2>Sections not built yet</h2>")
    for name, key in (("VA&amp;LR", "va_lr"), ("DM", "dm")):
        n = PAPER_SHAPE["part1"][key]
        out.append(f'<div class="box off"><h3>{name}</h3>'
                   f"<p>{n} questions in the real paper. Nothing written here "
                   "yet &mdash; this project trains QA&amp;DI only.</p></div>")
    out.append('<div class="box off"><h3>GK (Part 2)</h3>'
               "<p>Excluded from the percentile by XLRI, so it is out of "
               "scope.</p></div>")

    out.append(f'<p class="sub" style="margin-top:24px">{len(entries)} of '
               f"{total} subtopics written. "
               "<code>uv run xat-practice coverage</code> for the full ledger.</p>")
    out.append("</main></body></html>")
    return "".join(out)
