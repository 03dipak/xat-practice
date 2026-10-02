"""Builds the static lesson bundle. No server, no accounts (D10).

The learner's loop, in the order the owner described it, with one thing placed
in front of it:

    1. STEM ALONE. The options are not in the DOM. A learner who can see five
       options can eliminate two and score "correct" without retrieving
       anything, so both the score and the learner's self-model are wrong.
       With 5 options that elimination is easier than with 4, which is why this
       matters MORE here than in the reference project.
    2. COMMIT. The learner writes or picks a confidence, and the answer is
       recorded. It is never graded at this point and it never leaves the
       machine -- it is pure browser state, so it costs ZERO LLM calls. The
       commit is what carries the learning; the options are only the checker.
    3. OPTIONS APPEAR. Then the learner selects one.
    4. RIGHT OR WRONG, immediately.
    5. STEP BY STEP, ending on the stated answer, ruling out every option the
       learner did not pick BY NAME.
    6. CONFIDENCE, recorded against the result, giving the four-cell quadrant.

The key and the solution are NOT in the served HTML. They are written to a
separate `answerkey.json` that the page fetches only after the learner has
committed and selected. `test_the_bundle_does_not_leak_the_key_before_check`
asserts this against the real files on disk, because a bundle that leaks its
own key is a bundle that teaches the wrong thing with a clean conscience.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path

from .gates import run
from .items import Item
from .registry import LESSONS, Lesson
from .registry import assert_registry_is_honest as registry_assert_honest

OUT_ROOT = Path(__file__).resolve().parent.parent.parent / "out"


def out_dir(lesson_id: str) -> Path:
    """Where a lesson's bundle goes.

    MEASURED 2026-10-02: this was a single hardcoded `out/lesson-01`, so a second
    lesson had nowhere to live. Now the directory is DERIVED from the lesson id,
    which means a lesson cannot be built into the wrong place by accident."""
    return OUT_ROOT / lesson_id


#: Retained for the tests and for `--lesson`'s default, which is the FIRST lesson.
OUT_DIR = out_dir(LESSONS[0].lesson_id)

# The stylesheet is its OWN FILE, and that is load-bearing rather than tidy.
#
# MEASURED 2026-10-02: with the CSS inline in index.html the UI probe could
# not load it, so it was blind to every appearance defect. The worst one:
# `.opt` overrode `background` but not `colour`, so all five options rendered
# WHITE ON WHITE -- and the probe's own contrast check PASSED against the
# broken build, because with no stylesheet the buttons were default grey and
# perfectly readable. A check that cannot see the styling cannot catch a
# styling bug. Both the page and the probe now load the same file.
STYLE = """\
  :root {
    --ink: #14181f; --muted: #5b6673; --line: #d9dee5; --bg: #f7f8fa;
    --ok: #0f7b46; --bad: #b3261e; --key: #1b4dd8;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; padding: 24px 16px 96px; background: var(--bg); color: var(--ink);
    font: 17px/1.6 -apple-system, "Segoe UI", Roboto, sans-serif;
  }
  main { max-width: 720px; margin: 0 auto; }
  h1 { font-size: 21px; margin: 0 0 4px; }
  .sub { color: var(--muted); font-size: 14px; margin-bottom: 20px; }
  .rungs { display: flex; gap: 6px; margin-bottom: 22px; flex-wrap: wrap; }
  .rung {
    flex: 1 1 90px; padding: 9px 8px; border: 1px solid var(--line);
    border-radius: 7px; background: #fff; font-size: 11px; letter-spacing: .07em;
    text-transform: uppercase; color: var(--muted); text-align: center;
  }
  .rung.on { border-color: var(--ink); color: var(--ink); font-weight: 600; }
  .rung.done { background: var(--ok); border-color: var(--ok); color: #fff; }
  .card {
    background: #fff; border: 1px solid var(--line); border-radius: 11px;
    padding: 22px; margin-bottom: 16px;
  }
  .qno { font-size: 12px; letter-spacing: .09em; text-transform: uppercase;
         color: var(--muted); margin-bottom: 10px; }
  .stem { font-size: 19px; line-height: 1.55; margin-bottom: 18px; }
  .lbl { font-size: 13px; color: var(--muted); margin: 0 0 8px; }
  textarea, .commit {
    width: 100%; padding: 11px 13px; border: 1px solid var(--line);
    border-radius: 8px; font: inherit; background: #fff;
  }
  textarea { min-height: 58px; resize: vertical; }
  button {
    font: inherit; font-weight: 600; padding: 11px 20px; border-radius: 8px;
    border: 1px solid var(--ink); background: var(--ink); color: #fff;
    cursor: pointer; margin-top: 12px;
  }
  button.ghost { background: #fff; color: var(--ink); }
  button:disabled { opacity: .4; cursor: not-allowed; }
  /* MEASURED 2026-10-02: the owner's report was "the page takes too long and
     the first screen is only the title". The server was NOT slow -- 1.4-4.8ms
     per asset, ~12ms for all four. The cause was that `render()` awaited the
     network BEFORE painting anything, so `#stage` was empty for the whole fetch
     and PERMANENTLY empty if the fetch rejected, with nothing to tell the
     learner why. Two fixes, both countable:
       1. the card is painted synchronously, before any await; the stem swaps in
          when the fetch lands;
       2. a rejected fetch renders the REASON, including the file:// case,
          instead of a blank page.
     `.pending` and `.bad` exist only to make those two states visible. */
  /* THE TEACHING CARD (D18). Sits above the first question. Deliberately plain:
     it is reference material a beginner scans, not a headline. */
  .teach { background: #fbfcfd; border: 1px solid var(--line); }
  .teach h2 { font-size: 18px; margin: 0 0 10px; }
  .teach .formula {
    font-size: 22px; font-weight: 700; letter-spacing: .02em;
    padding: 12px 14px; margin: 4px 0 14px; background: #eef1f4;
    border-radius: 8px; text-align: center;
  }
  .teach dl { margin: 0 0 14px; }
  .teach dt { font-weight: 700; margin-top: 10px; }
  .teach dd { margin: 2px 0 0 0; color: var(--muted); }
  .teach .unit { border-left: 3px solid var(--key); padding-left: 12px; }
  .teach .ex { background: #eef6f1; border-radius: 8px; padding: 12px 14px; }
  .teach button { margin-top: 4px; }
  .pending { color: var(--muted); font-size: 15px; }
  .bad { border-color: var(--bad); }
  .bad h2 { font-size: 17px; margin: 0 0 8px; color: var(--bad); }
  .bad code { display: inline-block; margin-top: 4px; }
  .opts { display: grid; gap: 8px; }
  .opt {
    display: flex; gap: 11px; align-items: flex-start; text-align: left;
    padding: 13px 15px; border: 1px solid var(--line); border-radius: 9px;
    background: #fff; cursor: pointer; font: inherit; width: 100%; margin: 0;
    /* MEASURED 2026-10-02, from the owner's report "not able to see any option
       or values". The generic `button` rule above sets `color: #fff` for the dark
       primary button. `.opt` overrode `background` but NOT `color`, so every
       option -- the letter badge AND the value -- rendered WHITE ON WHITE. All
       five rows were on screen, correct in the DOM, and completely illegible.

       The owner saw the markup in devtools, which is exactly what a
       white-on-white failure looks like from the DOM side: the nodes are all
       there. And 35 UI checks passed, because every one of them asserted that
       an element EXISTED. Not one asked whether it could be read.

       `.opt` now sets its own colour explicitly. Do not remove it.
    */
    color: var(--ink);
  }
  .opt:hover { border-color: var(--ink); }
  .opt.sel { border-color: var(--ink); background: #f2f4f7; }
  .opt.right { border-color: var(--ok); background: #eaf6ef; }
  .opt.wrong { border-color: var(--bad); background: #fdeeed; }
  .opt .k {
    flex: none; width: 23px; height: 23px; border: 1px solid var(--line);
    border-radius: 5px; display: grid; place-items: center; font-size: 12px;
    font-weight: 700;
  }
  .verdict { font-size: 19px; font-weight: 700; margin: 4px 0 14px; }
  .verdict.ok { color: var(--ok); } .verdict.no { color: var(--bad); }
  .sol li { margin-bottom: 13px; }
  .sol .why { color: var(--muted); }
  .hidden { display: none; }
  .quad { display: grid; grid-template-columns: 1fr 1fr; gap: 9px; margin-top: 6px; }
  .qcell { border: 1px solid var(--line); border-radius: 8px; padding: 13px; }
  .qcell.on { border-color: var(--ink); background: #f2f4f7; }
  .qcell .t { font-size: 11px; letter-spacing: .07em; text-transform: uppercase;
              color: var(--muted); margin-bottom: 5px; }
  .note { font-size: 14px; color: var(--muted); margin-top: 12px; }
  .foot { max-width: 720px; margin: 26px auto 0; font-size: 13px;
          color: var(--muted); }
  code { background: #eef1f4; padding: 1px 5px; border-radius: 4px;
         font-size: 13px; }
"""

HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>XAT Practise &middot; Lesson 1 &middot; Simple Interest</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<main>
  <h1>Lesson 1 &middot; Simple Interest</h1>
  <div class="sub">One subtopic, four levels &mdash; foundation, easy, medium,
    hard. Nothing here is scored; everything here is meant to be understood.</div>
  <div class="rungs" id="rungs"></div>
  <div id="stage"></div>
</main>
<div class="foot" id="foot"></div>
<script src="lesson.js"></script>
</body>
</html>
"""

JS = r"""
// The key is NOT in this file. It is fetched from answerkey.json only after the
// learner has committed AND selected, so a learner cannot read the answer out
// of the page source. `test_the_bundle_does_not_leak_the_key_before_check`
// asserts that against the files on disk.
// EVERYTHING IS INSIDE AN IIFE. MEASURED 2026-10-02: `check` was a GLOBAL
// function, so anything else in the page could replace it. A UI probe that
// declared its own `check(name, pass, detail)` silently took lesson.js's place:
// the click handler called the wrong function, `answerkey.json` was never
// fetched, and the page produced no verdict at all. `ORDER`, `state`, `render`,
// `esc`, `fail`, `check` and `next` were all on `window` where a future script
// could overwrite any of them. Nothing in here is part of the page's contract,
// so none of it belongs in the global scope.
(() => {

const ORDER = ['L1-F', 'L1-E', 'L1-M', 'L1-H'];
const LABEL = {
  'L1-F': 'FOUNDATION', 'L1-E': 'EASY',
  'L1-M': 'MEDIUM',   'L1-H': 'HARD',
};
const state = { i: 0, commit: null, pick: null, meta: null, build: null,
                teach: {}, log: [] };
let paperCache = null;

// paper.json holds ONLY what the learner is allowed to see: the stem, the
// options, and the derived level. It is safe to fetch on load.
//
// ONE FETCH FOR THE WHOLE LESSON. MEASURED: the first version re-fetched
// paper.json on all four questions with `cache: 'no-store'`, so moving to the
// next question blanked the stage and re-downloaded the file. Four questions,
// four round trips, four flashes of empty page. The promise is cached instead,
// so questions 2-4 resolve from memory.
async function loadPaper(id) {
  if (!paperCache) {
    paperCache = fetch('paper.json', { cache: 'no-store' }).then(r => {
      if (!r.ok) throw new Error('paper.json returned HTTP ' + r.status);
      return r.json();
    });
  }
  const all = await paperCache;
  state.build = all.build || 'unknown';
  state.teach = all.teach || {};
  return all.items.find(i => i.id === id);
}

// answerkey.json holds `k`, every solution and every misconception. It is
// fetched ONLY inside check().
//
// MEASURED: the first bundle had ONE loadKey() that served the stem, so the
// whole key file was in memory -- and visible in the network tab -- before the
// learner committed a single character. The commit barrier was theatre.
// `test_the_key_is_fetched_only_after_check` asserts the split.
async function loadKey(id) {
  const r = await fetch('answerkey.json', { cache: 'no-store' });
  const all = await r.json();
  return all.items[id];
}

function rungBar() {
  document.getElementById('rungs').innerHTML = ORDER.map((id, n) => {
    const cls = n === state.i ? 'on' : (n < state.i ? 'done' : '');
    return `<div class="rung ${cls}">${LABEL[id]}</div>`;
  }).join('');
}

function esc(s) {
  return String(s).replace(/[&<>]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
}

// A rejected fetch must SAY SO. The failure this replaces was silent: the
// stage was written only after the await, so a fetch that never resolved left
// the learner staring at the title and the subtitle with no question and no
// clue. The most common cause is opening index.html directly -- browsers block
// fetch() of a sibling file over file:// -- so that case is named.
function fail(stage, id, err) {
  const onFile = location.protocol === 'file:';
  stage.innerHTML = `
    <div class="card bad">
      <h2>The question could not be loaded.</h2>
      <p class="pending">${LABEL[id]} &middot; the paper file did not arrive.</p>
      <p>${esc(onFile
        ? 'This page is open over <code>file://</code>, and a browser refuses to '
          + 'fetch a sibling JSON file from there. It is not a bug in the lesson.'
        : 'The server did not return <code>paper.json</code>.')}</p>
      <p class="pending">Reason: ${esc(err && err.message ? err.message : err)}</p>
      <p class="pending">Fix: run <code>xat-practice build</code>, then
        <code>xat-practice serve</code>, and open
        <code>http://127.0.0.1:8000/</code>.</p>
    </div>`;
}

// D18 TEACH THEN ASK. Shown before question 1 only (OWNER DECISION, 2026-10-02:
// once per lesson, not once per subtopic -- revisit if a learner says it repeats).
//
// It is built from paper.json, which is the file the page already loads, so it
// costs no extra request and it cannot touch the key: the key is not in this file
// and is not fetched until check().
function teachCard(t) {
  if (!t || !t.formula) return '';
  const legend = (t.legend || []).map(
    ([k, name, mean]) => `<dt>${esc(k)} &mdash; ${esc(name)}</dt><dd>${esc(mean)}</dd>`
  ).join('');
  return `<div class="card teach">
    <h2>${esc(t.heading)}</h2>
    <p>${esc(t.why)}</p>
    <div class="formula">${esc(t.formula)}</div>
    <dl>${legend}</dl>
    <p class="unit"><strong>Units.</strong> ${esc(t.units)}</p>
    <p>${esc(t.why_divide)}</p>
    <p class="ex"><strong>Worked example.</strong> ${esc(t.example)}</p>
    <p>${esc(t.bridge)}</p>
    <button id="startQ">I have read this &mdash; show me question 1</button>
  </div>`;
}

async function render() {
  rungBar();
  const id = ORDER[state.i];
  const stage = document.getElementById('stage');

  // PAINTED FIRST, FETCHED SECOND. This assignment happens before any await, so
  // the first screen is never empty and never mistaken for a broken page.
  stage.innerHTML = `
    <div id="teachSlot"></div>
    <div class="card">
      <div class="qno">${LABEL[id]} &middot; question ${state.i + 1} of 4</div>
      <div class="stem pending">Loading the question&hellip;</div>
    </div>`;


  let meta;
  try {
    meta = await loadPaper(id);
  } catch (err) {
    fail(stage, id, err);
    return;
  }
  state.meta = meta;

  // SHOW THE BUILD. If the screen says a build that is not the current one, the
  // browser is running a stale script and nothing below can be trusted.
  const foot = document.getElementById('foot');
  if (foot) foot.innerHTML =
    'Build <strong>' + esc(String(state.build)) + '</strong> &middot; every key in '
    + 'this lesson was <strong>recomputed from the item\'s own derivation</strong> '
    + 'by exact arithmetic, and the answer is served only after you commit. '
    + 'Difficulty was <strong>derived from each item\'s structure</strong>, not '
    + 'requested from a model &mdash; so the four levels are a measured property '
    + 'of these four questions.';

  stage.innerHTML = `
    <div id="teachSlot"></div>
    <div class="card">
      <div class="qno">${LABEL[id]} &middot; question ${state.i + 1} of 4</div>
      <div class="stem">${esc(meta.stem)}</div>

      <div id="commitBox">
        <p class="lbl"><strong>Write your answer before you see the options.</strong>
          Never marked, never leaves your machine.</p>
        <textarea id="freeAnswer" placeholder="e.g. SI = P x R x T / 100 = ..."></textarea>
        <div class="quad" style="margin-top:12px">
          <div class="qcell" id="csure"><div class="t">I am sure</div>
            <button class="ghost" data-conf="sure">Sure</button></div>
          <div class="qcell" id="cunsure"><div class="t">I am unsure</div>
            <button class="ghost" data-conf="unsure">Unsure</button></div>
        </div>
        <button id="reveal" disabled>Show the options</button>
        <div class="note" id="commitNote"></div>
      </div>

      <div id="optBox" class="hidden"></div>

      <div id="result" class="hidden"></div>
    </div>`;

  // The teaching card, on question 1 only. It is NOT on later rungs: the point is
  // to read it once before the ladder starts, and repeating it four times is the
  // "revisit this if a learner says it repeats" case, not the default.
  const slot = document.getElementById('teachSlot');
  if (slot) {
    if (state.i === 0) {
      slot.innerHTML = teachCard(state.teach);
      const b = document.getElementById('startQ');
      if (b) b.onclick = () => { slot.innerHTML = ''; };
    } else {
      slot.innerHTML = '';
    }
  }

  document.querySelectorAll('[data-conf]').forEach(b => b.onclick = () => {
    state.commit = b.dataset.conf;
    document.querySelectorAll('.qcell').forEach(c => c.classList.remove('on'));
    b.parentElement.classList.add('on');
    document.getElementById('commitNote').textContent =
      state.commit === 'sure'
        ? 'Recorded: you said you were sure. Remember that when you see the result.'
        : 'Recorded: you said you were unsure. That is useful information, not a wrong answer.';
    document.getElementById('reveal').disabled = false;
  });

  document.getElementById('reveal').onclick = () => {
    // THE OPTIONS ARE BUILT HERE, not in render(). MEASURED 2026-10-02: the
    // first version rendered them into a hidden <div id="optBox">, so they were
    // in the DOM before the learner committed -- hidden, but present, and one
    // line of devtools away. The module docstring claimed "the options are not
    // in the DOM" and that claim was FALSE, which is worse than either a
    // working barrier or an honest gap.
    //
    // paper.json is cached in memory, so building them here costs no fetch.
    const box = document.getElementById('optBox');
    const a = 'ABCDE';
    box.innerHTML = `
      <div class="opts">
        ${state.meta.options.map((o, n) => `
          <button class="opt" data-pick="${n}">
            <span class="k">${a[n]}</span><span>${esc(o)}</span>
          </button>`).join('')}
      </div>
      <button id="check">Check my answer</button>`;
    document.getElementById('commitBox').classList.add('hidden');
    box.classList.remove('hidden');
  };
}

async function check() {
  const id = ORDER[state.i];
  // The key is fetched HERE and nowhere earlier. The learner has committed a
  // confidence and picked an option; only now is the answer allowed on screen.
  const meta = await loadKey(id);
  const a = 'ABCDE';
  state.pick = Number(
    document.querySelector('.opt.sel')?.dataset.pick ?? -1);

  document.querySelectorAll('.opt').forEach((el, n) => {
    el.classList.remove('sel');
    if (n === meta.k) el.classList.add('right');
    else if (n === state.pick) el.classList.add('wrong');
  });
  document.getElementById('optBox').classList.add('hidden');

  const right = state.pick === meta.k;
  const cell = state.commit === 'sure'
    ? (right ? 'Sure and right — this one is yours.'
              : 'Sure and WRONG — a misconception. This is the cell that matters most.')
    : (right ? 'Unsure but right — a gap in disguise. You got lucky, not fluent.'
              : 'Unsure and wrong — normal, and the cheapest kind of miss.');

  // MEASURED: `state.log` was declared and read by finish() but nothing ever
  // pushed to it, so the finish screen reported a count that was always 0 and
  // then never displayed it. The quadrant is the product's central claim
  // (PEDAGOGY section 2), so the finish screen has to actually show it.
  state.log.push({ id, level: LABEL[id], right, commit: state.commit, cell });

  document.getElementById('result').innerHTML = `
    <div class="verdict ${right ? 'ok' : 'no'}">
      ${right ? 'Correct.' : 'Not correct.'} The answer is ${a[meta.k]}.
    </div>
    <ul class="sol">${meta.solution.map(s => `<li>${esc(s)}</li>`).join('')}</ul>
    <div class="qcell on" style="margin-top:8px"><div class="t">Where you landed</div>
      <div>${esc(cell)}</div></div>
    <button id="next">${state.i < 3 ? 'Next question' : 'Finish lesson'}</button>`;
  document.getElementById('result').classList.remove('hidden');
  document.getElementById('next').onclick = next;
}

function next() {
  if (state.i === 3) return finish();
  state.i += 1;
  state.commit = null; state.pick = null;
  render();
}

function finish() {
  const rows = state.log.filter(Boolean);
  const wasSure = rows.filter(r => r.commit === 'sure' && !r.right);
  document.getElementById('stage').innerHTML = `
    <div class="card">
      <div class="qno">Lesson complete</div>
      <div class="stem">You worked through Simple Interest at four levels.</div>
      <div class="qcell on" style="margin-top:8px"><div class="t">Where you landed</div>
        ${rows.length ? rows.map(r => `<div style="margin-top:6px">
          <strong>${esc(r.level)}</strong> &middot;
          <span style="color:var(--${r.right ? 'ok' : 'bad'})">${r.right ? 'right' : 'wrong'}</span>
          &mdash; ${esc(r.cell)}</div>`).join('')
          : '<div style="margin-top:6px">Nothing was recorded.</div>'}
      </div>
      <p>The ladder is the point. The hard question's only extra step is the
      one the foundation question isolated &mdash; so if the last one felt
      arbitrary, the first one did not land, and redoing it is worth more than
      another hard question.</p>
      <p>Your strongest signal is not your score. It is
      <strong>the one you were <em>sure</em> about and got wrong</strong>:
      that is a misconception with a name, and it is the one to fix tonight.
      ${wasSure.length
        ? `<strong>That is ${wasSure.map(r => r.level.toLowerCase()).join(' and ')}.</strong>`
        : '<strong>You were not sure-and-wrong on any of the four</strong>'
          + ' &mdash; so tonight the fix is retrieval, not a wrong idea.'}
      </p>
    </div>`;
  rungBar();
}

document.addEventListener('click', e => {
  const o = e.target.closest('.opt');
  if (o && !o.classList.contains('right')) {
    document.querySelectorAll('.opt').forEach(x => x.classList.remove('sel'));
    o.classList.add('sel');
  }
  if (e.target.id === 'check' &&
      document.querySelector('.opt.sel')) check();
});

document.getElementById('foot').innerHTML =
  'Every key in this lesson was <strong>recomputed from the item\'s own ' +
  'derivation</strong> by exact arithmetic, and the answer is served only ' +
  'after you commit. Difficulty was <strong>derived from each item\'s ' +
  'structure</strong>, not requested from a model &mdash; so the four levels ' +
  'are a measured property of these four questions.';

render();

})();
"""


def build_id(payload: dict[str, object]) -> str:
    """A short, DETERMINISTIC stamp of the content it describes.

    MEASURED 2026-10-02, from an owner report of the options being invisible.
    The served page was correct -- proven by screenshot -- so the browser was
    running an older copy, and nothing on the screen could tell. A learner (or a
    reviewer) had no way to know which build they were looking at.

    So the build now SAYS which build it is. Derived from the content rather than
    the clock, so two builds of the same lesson produce the same id and
    `git diff` on out/ stays meaningful. `test_the_build_id_changes_when_the_
    lesson_changes` pins that."""
    import hashlib
    import json as _json

    blob = _json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode()).hexdigest()[:8]


def build_lesson(lesson_id: str, items: tuple[Item, ...],
                 solutions: Mapping[str, tuple[str, ...]],
                 teach: Mapping[str, Mapping[str, object]] | None = None
                 ) -> dict[str, object]:
    """Gate the lesson, then emit the two halves of the bundle.

    The paper and the key are SEPARATE FILES on purpose. A single HTML file
    containing its own answers is a file a learner can read the source of, and a
    bundle that leaks its key teaches the wrong thing with a clean conscience.
    """
    res = run(list(items))
    refused = [r for r in res.refusals if r.item_id in {i.id for i in items}]
    if refused:
        raise SystemExit(
            "refusing to build a bundle from items that did not pass the "
            "gates:\n" + "\n".join(f"  {r.gate} {r.item_id}: {r.detail}"
                                   for r in refused)
        )

    paper: dict[str, object] = {
        "lesson_id": lesson_id,
        "subtopic": items[0].subtopic_id,
        # D18: TEACH THEN ASK. MEASURED 2026-10-02 by `viewer`: the formula first
        # reached the screen only AFTER question 1 was answered, so a learner who
        # did not know the formula could not learn it here. This block is rendered
        # BEFORE the first question, so it belongs in the PAPER -- the file the
        # page loads on load. It is not in answerkey.json, and it must never be.
        # D18: the teaching lives in the PAPER, never in answerkey.json -- it has
        # to be seen before the commit.
        "teach": dict((teach or {}).get(items[0].subtopic_id, {})),
        "shaping": "LESSON",
        "negative_marking": False,
        "items": [
            {
                "id": it.id,
                "level": res.reports[it.id].level.value,
                "level_score": res.reports[it.id].score,
                "level_drivers": list(res.reports[it.id].drivers),
                "stratum": it.stratum.value,
                "stem": it.stem,
                "options": list(it.options),
            }
            for it in items
        ],
    }
    # The key field is named `k`, not `key_index`. A served script that names the
    # field holding the answer is one refactor away from shipping it: the
    # property name alone tells a reader which field to look at. MEASURED -- the
    # first bundle put `key_index` in lesson.js and the leak test caught it.
    key: dict[str, object] = {
        "lesson_id": lesson_id,
        "grounding": {
            it.id: {
                "verdict": res.checks[it.id].verdict.value,
                "grounded": res.checks[it.id].grounded,
                "computed": str(res.checks[it.id].computed),
                "derivation": it.derivation,
            }
            for it in items
        },
        "items": {
            it.id: {
                "k": it.key_index,
                "key_text": it.key_text,
                "solution": list(solutions[it.id]),
                "distractors": [
                    {"text": d.text, "misconception": d.misconception,
                     "is_real_near_miss": d.is_real_near_miss}
                    for d in it.distractors
                ],
            }
            for it in items
        },
    }
    paper["build"] = build_id(paper)
    key["build"] = paper["build"]
    return {"paper.json": paper, "answerkey.json": key}


def build_one(lesson: Lesson) -> Path:
    """Gate, split, and write ONE lesson. Raises if any gate refuses."""
    registry_assert_honest()
    files = build_lesson(lesson.lesson_id, lesson.items, lesson.solutions,
                          lesson.teach)
    dest = out_dir(lesson.lesson_id)
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "index.html").write_text(HTML)
    (dest / "lesson.js").write_text(JS)
    (dest / "style.css").write_text(STYLE)
    for name, payload in files.items():
        (dest / name).write_text(json.dumps(payload, indent=2) + "\n")
    return dest


def main() -> None:
    """Build EVERY lesson in the registry.

    Looping rather than building lesson 1 is the point of the registry: a lesson
    that exists in code but is never served is a lesson that does not exist."""
    for lesson in LESSONS:
        dest = build_one(lesson)
        files = build_lesson(lesson.lesson_id, lesson.items, lesson.solutions,
                              lesson.teach)
        paper = files["paper.json"]
        assert isinstance(paper, dict)
        print(f"built {dest.relative_to(OUT_ROOT.parent)}/  build {paper['build']}")
        for it in paper["items"]:
            print(f"  {it['id']:6s} {it['level']:11s} score {it['level_score']:5.2f}  "
                  f"{it['level_drivers']}")


if __name__ == "__main__":
    main()
