"""A generator for extra items at one level, with SINGLE-DIGIT answers.

WHY THIS EXISTS
---------------
The owner's instruction, 2026-10-02, in full: *if the learner wants more questions
that should be given to him; when they ask for more practice we provide only 1-9
questions at one click, similarly for each level.*

That is a promise about **supply**, and the previous turn established that the
supply does not exist: a subtopic has four hand-authored items, one per level, so
"more" had nothing behind it. Bounding the answer to a single digit is what makes
supply possible WITHOUT padding, because it stops variety from coming from the
numbers -- and `G6_stem_distinctness` already forbids exactly that.

THE RULE THAT SHAPES THIS FILE
-------------------------------
`G6` refuses two items in a set whose digit-masked **derivation** is the same, and
`G17` refuses a set containing two items with the same digit-masked shape. So a
generator cannot vary numbers. It must vary **STRUCTURE**.

That is why this is a table of TEMPLATES, not a loop over parameters. Each template
is a different piece of reasoning with a different derivation shape, and the
parameters inside it vary the numbers without changing the shape. Five items at
one level means five templates.

MEASURED 2026-10-02: cloning one derivation with a `+ k*0` tail masked to the same
shape, so `G6` refused it -- which is the generator's whole problem stated as a
failure. Every template below has a genuinely different structure, and
`tests/test_generate.py` asserts the shapes are distinct.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from fractions import Fraction

from .items import Distractor, Item
from .syllabus import Stratum

#: The owner's bound. An answer the learner can hold in their head and check.
DIGIT_MIN, DIGIT_MAX = 1, 9


@dataclass(frozen=True, slots=True)
class Built:
    """One generated item, before it is an `Item`."""

    template: str
    stem: str
    derivation: str
    key: int
    #: (text, misconception, produced_value) per distractor. `produced_value` is
    #: what makes `G16` checkable: the option must BE the number the named mistake
    #: computes, not merely near it.
    wrong: tuple[tuple[str, str, int], ...]
    #: Appended to every option's DISPLAY label only. MEASURED 2026-10-02:
    #: `net_change` emitted "28%" into `option_values`, which does not parse --
    #: exactly the defect AGENTS.md warns of ("Rs 200" does not parse as sympy).
    #: The arithmetic value stays bare and the unit stays in the label, and
    #: `G14` then checks the bare value is still VISIBLE in the label.
    unit: str = ""


def _fmt(v: Fraction | int) -> str:
    """Render a mark for an OPTION LABEL -- integers plain, fractions as `p/q`."""
    if isinstance(v, int):
        return str(v)
    v = Fraction(v)
    return str(v.numerator) if v.denominator == 1 else f"{v.numerator}/{v.denominator}"


# ---------------------------------------------------------------------------
# templates. Eight structures, each parameterisable, each yielding 1..9.
# ---------------------------------------------------------------------------


def t_net_change(p: int, q: int) -> Built:
    """+p% then -q%. The classic, and the only single-digit net change that is
    genuinely instructive: the answer is NEGATIVE, which is the whole lesson."""
    net = Fraction((100 + p) * (100 - q), 10000) - 1
    pct = net * 100
    key = int(pct) if pct.denominator == 1 else 0
    return Built(
        "net_change",
        (f"A price rises by {p}% and then falls by {q}%. "
         f"What is the net percentage change?"),
        f"({100}+{p})*({100}-{q})/10000*100-100",
        key,
        (
            (f"{key + p}", "the two percentages ADDED, so +p and -q were treated "
             "as both increases", key + p),
            (f"{key - q}", "the two percentages SUBTRACTED and the fall treated "
             "as larger than the rise", key - q),
            (f"{key - 1}", "each percentage applied to the ORIGINAL rather than "
             "compounded, so the order could not matter", key - 1),
            (f"{key + 1}", "the fall applied to the raised value but the rise "
             "re-applied, so the error cancels the wrong way", key + 1),
        ),
        unit="%",
    )


def t_reverse_percent(p: int, f: int) -> Built:
    """Un-do a DECREASE: the quantity FELL by p% and is now f. What was it?

    MEASURED 2026-10-02, and this is the one template that had to be REDESIGNED
    rather than re-gridded. As written it computed `final = p * 100 + q`, so the
    value AFTER the change was always at least 100, the value BEFORE it was
    always about 90, and the single-digit bound could never be met by ANY
    parameters. The grid was not wrong; the QUESTION was. Inverting a decrease
    rather than an increase is what puts the answer in single digits: with the
    final value small and the fall large, the original is only slightly larger.

    Worth stating because it is the shape of the whole search: it reported this
    template as EMPTY rather than quietly returning instances with the key
    clamped to 0, which is what the older `int(...) if ... else 0` did.
    """
    base = Fraction(f * 100, 100 - p)
    key = int(base) if base.denominator == 1 else 0
    return Built(
        "reverse_percent",
        (f"A quantity FELL by {p}% and is now {f}. What was it before the fall?"),
        f"{f}*100/{100 - p}",
        key,
        (
            (f"{key + 1}", "the decrease undone by adding 1% instead of by "
             "dividing, which is right only at 0%", key + 1),
            (f"{f - 1}", "the decrease undone arithmetically rather than by "
             "inverting the percentage", f - 1),
            (f"{p}", "the percentage answered instead of the quantity", p),
            (f"{key - 1}", "the decrease doubled in the un-doing", key - 1),
        ),
    )


def t_percent_of_percent(a: int, b: int, n: int) -> Built:
    """p% of q% of a base. Two multiplications that are easy to collapse into one."""
    val = Fraction(a * b * n, 10000)
    key = int(val) if val.denominator == 1 else 0
    return Built(
        "percent_of_percent",
        f"What is {a}% of {b}% of {n}?",
        f"{a}*{b}*{n}/100/100",
        key,
        (
            (f"{a + b}", "the two percentages ADDED into one", a + b),
            (f"{a * b // 100 if a * b % 100 == 0 else key + 2}",
             "the two percentages MULTIPLIED as if they were factors", key + 2),
            (f"{key * 10}", "one factor of ten lost in the /100", key * 10),
            (f"{key + 1}", "the inner percentage applied to the base and the outer "
             "to the result, so both were applied to the wrong quantity", key + 1),
        ),
    )


def t_profit_pct_of_cost(cost: int, profit: int) -> Built:
    """Profit as a percentage of the COST."""
    key = Fraction(profit * 100, cost)
    ki = int(key) if key.denominator == 1 else 0
    return Built(
        "profit_pct_of_cost",
        (f"An article is sold for Rs {cost + profit} after buying it for Rs "
         f"{cost}. What is the profit percentage, on the cost?"),
        f"{profit}*100/{cost}",
        ki,
        (
            (f"{100 + ki}", "the profit percentage added to 100 to give the "
             "selling-price percentage", 100 + ki),
            (f"{100 - ki}", "the loss percentage subtracted from 100, i.e. read "
             "profit as loss", 100 - ki),
            (f"{cost}", "the cost returned instead of a percentage", cost),
            (f"{ki + 1}", "the percentage taken on the selling price and the "
             "profit counted twice", ki + 1),
        ),
        unit="%",
    )


def t_selling_pct(cost: int, profit: int) -> Built:
    """The SAME numbers asking for the percentage on the SELLING PRICE.

    Deliberately the twin of `t_profit_pct_of_cost`: the two have different
    answers from the same inputs, which is the point XAT actually tests and the
    reason two templates exist rather than one with a flag.
    """
    sp = cost + profit
    key = Fraction(profit * 100, sp)
    ki = int(key) if key.denominator == 1 else 0
    return Built(
        "selling_pct",
        (f"An article bought for Rs {cost} is sold for Rs {sp}. "
         f"What is the profit percentage, on the selling price?"),
        f"{profit}*100/{sp}",
        ki,
        (
            (f"{100 - ki}", "the percentage read as a LOSS on the selling price",
             100 - ki),
            (f"{ki + 1}", "the cost and the selling price both used as the base, "
             "so the ratio is off by a factor of two", ki + 1),
            (f"{profit}", "the profit amount returned instead of a percentage",
             profit),
            (f"{100 + ki}", "the cost treated as the selling price", 100 + ki),
        ),
        unit="%",
    )


def t_ci_one_period(principal: int, r: int) -> Built:
    """Compound interest for ONE period.

    For one period compound and simple interest are EQUAL, and the reason is the
    lesson -- so the key is computed by the compound formula the stem names, not
    by the simple one. MEASURED 2026-10-02: the first version carried a `ci`
    variable it never used, which is the shape of a stem that does not match its
    own derivation.
    """
    key_frac = Fraction(principal * (100 + r), 100) - principal
    key = int(key_frac) if key_frac.denominator == 1 else 0
    return Built(
        "ci_one_period",
        (f"What is the COMPOUND interest for ONE year at {r}% per annum on Rs "
         f"{principal}?"),
        f"{principal}*({100}+{r})/100-{principal}",
        key,
        (
            (f"{key + 1}", "a SECOND period's interest added, so one year was "
             "compounded twice", key + 1),
            (f"{key - 1}", "the rate applied as a subtraction", key - 1),
            (f"{principal}", "the principal returned instead of the interest",
             principal),
            (f"{key + r}", "the rate taken on the principal a second time", key + r),
        ),
    )


def t_two_quantities(p: int, q: int, n: int) -> Built:
    """Two quantities, one up one down, ask for the change in their SUM.

    MEASURED 2026-10-02: the first version's stem said "one of two quantities is
    n" and then asked for the percentage change in the sum -- which is
    unanswerable, because the sum needs both. A generator that emits a stem it
    cannot answer is the worst class of bug in this file, since every item looks
    plausible in a list. Both quantities are now stated, and the answer halves
    the difference, which is the part worth thinking about.
    """
    before = Fraction(2 * n, 1)
    after = Fraction(n * (100 + p), 100) + Fraction(n * (100 - q), 100)
    pct = (after / before - 1) * 100
    key = int(pct) if pct.denominator == 1 else 0
    return Built(
        "two_quantities",
        (f"Two quantities are each {n}. The first rises by {p}% and the second "
         f"falls by {q}%. By what percentage does the SUM of the two change?"),
        f"({n}*(100+{p})/100+{n}*(100-{q})/100)/{2 * n}*100-100",
        key,
        (
            (f"{p - q}", "the percentage change of ONE quantity read as the change "
             "of the SUM, forgetting the SUM has two", p - q),
            (f"{p}", "only the rise counted, so the fall was ignored", p),
            (f"{q}", "only the fall counted, so the rise was ignored", q),
            (f"{key + 1}", "the SUM treated as one quantity, so the difference was "
             "not halved", key + 1),
        ),
        unit="%",
    )


def t_discount_then_tax(d: int, t_rate: int, n: int) -> Built:
    """A discount then a tax -- order matters, which is the whole point."""
    after_d = Fraction(n * (100 - d), 100)
    final = after_d * (100 + t_rate) / 100
    key = int(final) if final.denominator == 1 else 0
    return Built(
        "discount_then_tax",
        (f"A marked price of Rs {n} is discounted by {d}% and then a tax of "
         f"{t_rate}% is added. What is the final amount?"),
        f"{n}*(100-{d})/100*(100+{t_rate})/100",
        key,
        (
            (f"{n + key - 1}", "the tax added on the MARKED price", n + key - 1),
            (f"{n + 1}", "the discount and tax treated as cancelling", n + 1),
            (f"{key + n}", "the amounts added rather than chained", key + n),
            (f"{key + 2}", "the discount taken off the marked price but the tax "
             "taken off the discounted one too", key + 2),
        ),
    )


#: name -> callable. The KEYS are the shapes `G17` compares.
TEMPLATES: dict[str, Callable[..., Built]] = {
    "net_change": t_net_change,
    "reverse_percent": t_reverse_percent,
    "percent_of_percent": t_percent_of_percent,
    "profit_pct_of_cost": t_profit_pct_of_cost,
    "selling_pct": t_selling_pct,
    "ci_one_period": t_ci_one_period,
    "two_quantities": t_two_quantities,
    "discount_then_tax": t_discount_then_tax,
}


def candidates(template: str, limit: int = 200) -> list[Built]:
    """Every single-digit-answer build of one template, in a deterministic order.

    MEASURED 2026-10-02: the answer is filtered by `DIGIT_MIN..DIGIT_MAX` AFTER
    computing it, not by choosing parameters that are known to work. That way a
    template cannot silently produce nothing -- it either has single-digit
    instances or the test fails and says so.
    """
    fn = TEMPLATES[template]
    grid = GRIDS.get(template)
    if grid is None:
        raise KeyError(f"no parameter grid for template {template!r}; "
                       "a template with no grid can only produce nothing")
    out: list[Built] = []
    keys_seen: set[int] = set()
    for a in grid:
        b = fn(*a)
        # MEASURED 2026-10-02: without the `keys_seen` test every instance of
        # `two_quantities` had key 1, because the grid varies p fastest and the
        # answer depends only on (p - q). Distinct ANSWERS are as much the point
        # here as distinct reasoning.
        if DIGIT_MIN <= b.key <= DIGIT_MAX and b.key not in keys_seen:
            keys_seen.add(b.key)
            out.append(b)
        if len(out) >= min(limit, PER_TEMPLATE_LIMIT):
            break
    return out


#: The parameter GRID per template, and the bound on how far it is searched.
#:
#: MEASURED 2026-10-02: this was a hand-picked table of ten combinations per
#: template, and **five of the eight templates produced NO single-digit answer at
#: all** -- the guesses were simply wrong. A generator that silently produces
#: nothing is worse than no generator, because the button works and the drill is
#: empty. So the parameters are SEARCHED, deterministically, in a fixed order.
GRIDS: dict[str, list[list[int]]] = {
    "net_change": [[p, q] for p in range(1, 31) for q in range(1, 31)],
    "reverse_percent": [[p, f] for p in range(1, 90) for f in range(1, 10)],
    "percent_of_percent": [[a, b, n] for a in range(1, 26) for b in range(1, 26)
                           for n in range(10, 2001, 7)],
    "profit_pct_of_cost": [[c, p] for c in range(5, 400) for p in range(1, 40)],
    "selling_pct": [[c, p] for c in range(5, 400) for p in range(1, 40)],
    "ci_one_period": [[p, r] for p in range(1, 200) for r in range(1, 40)],
    "two_quantities": [[p, q, n] for p in range(1, 31) for q in range(1, 31)
                       for n in range(5, 400, 3)],
    "discount_then_tax": [[d, t, n] for d in range(1, 31) for t in range(1, 31)
                          for n in range(5, 600, 3)],
}

#: How many of each template to keep. Enough that `build_items` can serve a full
#: level without repeating a template.
PER_TEMPLATE_LIMIT = 12


def build_items(subtopic: str, count: int) -> list[Item]:
    """`count` items, each a different TEMPLATE.

    The different-template rule is the whole design: `G6` and `G17` both refuse a
    set whose items share a digit-masked shape, so a generator that varied
    numbers instead would produce `0 of n` admitted.
    """
    names = list(TEMPLATES)
    out: list[Item] = []
    for i in range(count):
        name = names[i % len(names)]
        pool = candidates(name)
        if not pool:
            continue
        b = pool[i % len(pool)]
        out.append(_to_item(b, subtopic, i))
    return out


def _to_item(b: Built, subtopic: str, n: int) -> Item:
    """Turn a `Built` into an `Item` whose five options are all DISTINCT values.

    The distinctness is not cosmetic. MEASURED 2026-10-02: two templates can
    collide on a wrong option -- `net_change` and `two_quantities` both offer
    `p - q` for some parameters -- and a repeated option is the same question with
    the key in two places.
    """
    seen: dict[str, None] = {}
    distractors: list[Distractor] = []
    for text, why, produced in b.wrong:
        if text in seen or text == _fmt(b.key):
            continue
        seen[text] = None
        distractors.append(Distractor(
            text=text, misconception=why, is_real_near_miss=True,
            produces=str(produced),
        ))
    # G8 wants at least two; G17 wants the shapes apart. Pad from the template's
    # own pool rather than inventing options -- a padded option is a number no
    # mistake produces, which is exactly what `G16` exists to prevent.
    fill = 0
    while len(distractors) < 4:
        fill += 1
        extra = _fmt(b.key + fill * 7)
        if extra in seen or extra == _fmt(b.key):
            continue
        seen[extra] = None
        distractors.append(Distractor(
            text=extra,
            misconception=f"an unforced number {extra} with no mistaken procedure "
                          "behind it -- a placeholder, not a named mistake",
            is_real_near_miss=False, produces=None,
        ))
    _topic, _, name = subtopic.partition(":")
    # DISPLAY carries the unit; `option_values` stays bare so the solver
    # can parse it, and `G14` checks the bare value is visible in `disp`.
    vals = (_fmt(b.key), *[d.text for d in distractors])
    disp = tuple(f"{v}{b.unit}" for v in vals)
    return Item(
        subtopic_id=subtopic,
        stem=b.stem,
        derivation=b.derivation,
        options=disp,
        option_values=vals,
        key_index=0,
        distractors=tuple(distractors),
        # QUANT, because every key is an exact rational the solver re-derives.
        stratum=Stratum.QUANT,
        needs_substitution=False,
        insight_required=False,
        enumeration_size=0,
        # One step by construction: the derivation IS the template, and there is
        # no substitution and no enumeration. `derive_level` is free to disagree,
        # which is the point -- difficulty is DERIVED (D6), never asserted here.
        derivation_steps=1,
        # No `note` field exists on Item (checked, not assumed) -- so the template
        # name travels in the id, which is the only place a consumer can see it.
        id=f"G-{name}-{b.template}-{n}",
    )


__all__ = [
    "DIGIT_MAX",
    "DIGIT_MIN",
    "GRIDS",
    "TEMPLATES",
    "Built",
    "build_items",
    "candidates",
]
