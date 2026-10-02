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
from .syllabus import EXAMS, SECTIONS, TOPICS, ExamSpec, SectionSpec, Subtopic, part_of_id

#: Which Part-1 section each topic belongs to. The syllabus trains QA&DI only
#: (D7), so this is the whole truth about the other two sections rather than a
#: guess about them.
SECTION_QA_DI = "QA&DI"


@dataclass(frozen=True, slots=True)
class Entry:
    """One selectable line: a written lesson, placed in the exam/section tree."""

    lesson_id: str
    exam_id: str
    section_id: str
    topic_id: str
    subtopic_id: str
    label: str
    subtopic_label: str

    @property
    def href(self) -> str:
        """Where the link goes. Includes the exam, so two exams cannot collide on a
        `lesson_id` -- and so the URL shape `/<exam>/<section>/<lesson>/` is the same
        whether one exam or six are loaded."""
        return f"{self.exam_id}/{self.section_id}/{self.lesson_id}/"


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
        # `lesson.exam_id`/`section_id` are DERIVED on the registry, not stored
        # here, so a topic cannot be filed under two parents (D20).
        out.append(Entry(
            lesson_id=lesson.lesson_id,
            exam_id=lesson.exam_id,
            section_id=lesson.section_id,
            topic_id=lesson.topic_id,
            subtopic_id=lesson.subtopic_id,
            label=lesson.topic_label,
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


def paper_shape_lines(exam_id: str = "xat") -> list[str]:
    """The exam's shape, read from `EXAMS`/`SECTIONS` rather than restated.

    MEASURED 2026-10-02: this read `syllabus.PAPER_SHAPE`, a single dict describing
    ONE paper. Deleting it in favour of `EXAMS`/`SECTIONS` broke this module's
    import -- and `ruff` passed, because ruff cannot see a name deleted from
    another module. Both agents reviewing the LLD found a broken package in a
    working tree that linted clean.
    """
    exam = EXAMS[exam_id]
    secs = [SECTIONS[f"{exam.exam_id}:{s}"] for s in exam.sections()]
    counted = [x for x in secs if x.counts_for_percentile(exam)]
    scored = sum(x.questions for x in counted)
    lines = [
        f"{exam.name} {exam.edition} -- {exam.total_questions} questions, of which "
        f"{scored} carry a raw score in {exam.part_minutes()} minutes.",
    ]
    # PARTS, not a flat section list. MEASURED 2026-10-02: the clock and the blank
    # rule are Part-level facts, so a flat list implies each section is timed and
    # penalised on its own -- the exact error corrected in docs/LLD.md §3.3.
    for pid in exam.parts:
        part = part_of_id(exam.exam_id, pid)
        names = " ".join(SECTIONS[f"{exam.exam_id}:{s}"].name for s in part.sections)
        clock = f"{part.minutes} min" if part.minutes else "no time limit"
        rule = ""
        if part.blank_penalty_after:
            rule = (f", {part.blank_penalty:.2f} per blank after the first "
                    f"{part.blank_penalty_after} ACROSS THE WHOLE PART")
        counted_here = "" if part.in_percentile else ", excluded from the percentile"
        lines.append(f"  {part.name}: {names} - {part.questions}q in {clock}{rule}"
                     f"{counted_here}")
    if exam.counted_questions != exam.total_questions:
        lines.append(
            f"  {exam.total_questions - exam.counted_questions} questions "
            "carry NO raw score: GK is excluded from the percentile by XLRI, so it "
            "is out of scope here."
        )
    # PER-ANSWER marking only. The blank rule is NOT here: it is on the part, and
    # the per-part lines above already state it with its correct scope. Printing it
    # again beside a single section is how the eight-free-blanks claim came to be
    # read as eight PER SECTION in the first place.
    marking = counted[0] if counted else secs[0]
    lines.append(
        f"  Per-answer marking: {marking.mark_correct:+g} correct, "
        f"{marking.mark_wrong:.2f} wrong, {marking.options} options."
    )
    return lines


def sections_of(exam_id: str = "xat") -> list[SectionSpec]:
    """Every section of an exam, in paper order."""
    exam = EXAMS[exam_id]
    return [SECTIONS[f"{exam.exam_id}:{s}"] for s in exam.sections()]


def exam_choices() -> list[ExamSpec]:
    """Every exam, for a chooser.

    MEASURED 2026-10-02: the owner ruled that with ONE exam the chooser is a click
    that buys nothing -- `serve` prompting and `serve` defaulting were both
    rejected. So the caller renders a chooser only when `len(this) > 1`, and the
    decision is driven by the data rather than hardcoded either way.
    """
    return [EXAMS[k] for k in sorted(EXAMS)]


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


def section_label(sec: SectionSpec, exam: ExamSpec) -> str:
    """One line describing a section, from its own data."""
    bits = [f"{sec.questions} questions"]
    if sec.calculator:
        bits.append("on-screen calculator")
    if not sec.counts_for_percentile(exam):
        bits.append("EXCLUDED from the percentile")
    return " \u00b7 ".join(bits)


def render_index_html(exam_id: str = "xat") -> str:
    """The page at `/`: the exam's sections, then its topics.

    Navigation lives HERE, in the browser, not in a shell prompt, and there is no
    exam chooser while only one exam exists.

    MEASURED 2026-10-02, this shape went wrong three times before it worked, and
    each failure is a lesson the page must not repeat:

    1. `serve` opened the FIRST registered lesson, so anyone who wanted Geometry got
       Simple Interest with nothing saying a choice existed -- safe by being
       invisible.
    2. The fix was to ASK in the terminal. Rejected: "I don't wanna invest the time
       in running commands."
    3. Adding the exam layer introduced a fourth click for a single-exam product.
       So the chooser is driven by `len(EXAMS) > 1`, not hardcoded either way: with
       one exam the exam step is invisible, and with two it appears for free.

    Everything here is DERIVED from `EXAMS`/`SECTIONS`/`TOPICS`. MEASURED: this
    function once listed VA&LR and DM as a hardcoded pair, so a third section -- or
    a second exam's sections -- would have been silently absent from the one page
    whose whole job is to be honest about what is missing.
    """
    from html import escape

    exam = EXAMS[exam_id]
    sections = sections_of(exam_id)
    entries = [e for e in written_entries() if e.exam_id == exam_id]
    total = _len_subtopics()

    o: list[str] = []
    o.append('<!doctype html><html lang="en"><head><meta charset="utf-8">')
    o.append('<meta name="viewport" content="width=device-width,initial-scale=1">')
    o.append(f"<title>{escape(exam.name)} Practice &middot; choose a section</title>")
    o.append(f"<style>{_NAV_CSS}</style></head><body><main>")

    o.append(f"<h1>{escape(exam.name)} {escape(exam.edition)}</h1>")
    o.append('<p class="sub">Choose a section, then a topic. Inside a lesson the '
             "four levels are tabs &mdash; take them in any order you like.</p>")

    # The exam, stated from data so the page cannot quote a spec we do not hold.
    o.append('<div class="box"><h3>The paper</h3><ul>')
    for line in paper_shape_lines(exam_id):
        o.append(f"<li>{escape(line)}</li>")
    o.append("</ul></div>")

    for sec in sections:
        mine = [e for e in entries if e.section_id == sec.section_id]
        built = sec.built and bool(mine)
        cls = "box" if built else "box off"
        o.append(f'<h2>{escape(sec.name)}</h2>')
        o.append(f'<div class="{cls}">')
        o.append(f"<p>{escape(section_label(sec, exam))}</p>")
        if built:
            o.append(f"<p>{len(mine)} lesson(s) written, ordered by measured "
                     "questions-per-year.</p>")
            for e in mine:
                o.append(
                    f'<div class="lesson"><div><h3>{escape(e.label)}</h3>'
                    f'<p class="levels">{escape(e.subtopic_label)}</p></div>'
                    f'<a href="{escape(e.href)}">Open &rarr;</a></div>')
        elif not sec.counts_for_percentile(exam):
            o.append("<p>Out of scope: it does not move the percentile.</p>")
        else:
            o.append("<p>Nothing written here yet. This project trains "
                     "QA&amp;DI only.</p>")
        o.append("</div>")

    o.append(f'<p class="sub" style="margin-top:24px">{len(entries)} of {total} '
             "subtopics written. "
             "<code>uv run xat-practice coverage</code> for the full ledger.</p>")
    o.append("</main></body></html>")
    return "".join(o)
