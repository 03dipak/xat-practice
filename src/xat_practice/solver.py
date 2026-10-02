"""Key re-derivation by computation. The reason this product can be trusted.

THE GOVERNING RULE (AGENTS.md)
    The LLM decides WHAT a question might say. Code decides WHETHER that
    question is admissible. No exceptions.

    The corollary is the one people get wrong: THE KEY IS ON THE
    PROBABILISTIC SIDE. A key is cheap and fast to generate, so putting it
    there is the obvious engineering choice. It is also the only defect a
    student cannot detect -- a wrong rationale is one bad frame, a wrong key
    is a belief the student will hold for the next five questions.

    The reference project (agentic_protracted_test) handles this with G16: a
    blind second LLM call that sees only the source span and the option texts.
    That is the best available answer when your source material is prose.

    IT IS NOT THE BEST ANSWER HERE. A quantitative item's key is not a matter
    of opinion, it is a number. So for the QUANT stratum we do not take a
    second opinion -- we RE-DERIVE IT. `Solver.verify` evaluates the item's
    own derivation and compares the result to the drafter's key. Agreement is
    arithmetic; disagreement is a REFUSAL. That is strictly stronger evidence
    than a second opinion, and it costs no LLM call.

    The consequence worth stating plainly: a Stratum.QUANT item has a key
    verified by code, and a Stratum.JUDGEMENT item (VALR, DM) does not. Any
    percentile claim for this product must be scoped to a stratum, or it is
    overstated.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

import sympy as sp

from .syllabus import Stratum

CALC_BUDGET_SECONDS = 20.0
"""A derivation that cannot be evaluated in this budget is not a derivation, it
is an unsolvable item. Measured against the on-screen calculator the exam
provides; see DECISIONS.md D8."""


class Verdict(StrEnum):
    HOLD = "HOLD"
    """Key confirmed by RECOMPUTATION. Only a QUANT item may carry this. A HOLD
    is a statement about code, and it is the only outcome in this enum that
    supports a percentile claim."""

    REFUSE = "REFUSE"
    """Key disagrees with the recomputation, or the derivation cannot be
    evaluated. The item is DROPPED. It is never repaired -- see D3."""

    DELEGATED = "DELEGATED"
    """The key was NOT verified here, and this enum refuses to pretend it was.

    Two routes arrive at this:
      * LOGIC -- `enumeration.py` re-runs the constraint set exhaustively.
      * JUDGEMENT -- an independent blind second LLM call (D2), which is a
        second OPINION, not a computation, and is strictly weaker evidence.

    MEASURED: this outcome existed in name only until the third path was added.
    Before it, a JUDGEMENT item with no derivation fell through to the logic
    branch and came back REFUSE/NO_DERIVATION -- which would have rejected
    every VALR and Decision-Making item in the paper, a third of the exam. And
    the alternative, returning HOLD, is worse: it would label an unverified
    prose key as one that code confirmed.

    So `DELEGATED` exists to keep a claim honest about where its evidence came
    from. A paper mixing strata must report them separately or it is
    overstating the weak ones."""


class Failure(StrEnum):
    KEY_MISMATCH = "KEY_MISMATCH"
    """The derivation evaluates to something that is not the keyed option. This
    is the exact defect the reference project shipped once."""

    UNRESOLVED_DERIVATION = "UNRESOLVED_DERIVATION"
    """The derivation contains a free symbol or does not evaluate to a scalar.
    The drafter wrote a plan, not a computation."""

    NONEXACT = "NONEXACT"
    """The derivation evaluates to a float or an unevaluated integral. An XAT
    key is exact; a key we can only get approximately is a key we cannot gate."""

    NO_DERIVATION = "NO_DERIVATION"
    """A QUANT item arrived with no derivation. Refused outright: an item whose
    key cannot be recomputed is exactly the item we cannot vouch for."""

    TIMEOUT = "TIMEOUT"
    """Evaluation exceeded CALC_BUDGET_SECONDS."""

    WRONG_STRATUM = "WRONG_STRATUM"
    """A derivation was offered for a JUDGEMENT item. There is no solver for
    prose, so a derivation here is a hallucinated proof of a key nobody
    checked."""


@dataclass(frozen=True, slots=True)
class Check:
    verdict: Verdict
    failure: Failure | None
    computed: sp.Expr | None
    keyed: sp.Expr | None
    detail: str

    @property
    def ok(self) -> bool:
        return self.verdict is Verdict.HOLD

    @property
    def grounded(self) -> bool:
        """True only when CODE confirmed the key. `DELEGATED` is deliberately
        not grounded, even though it is not a refusal."""
        return self.verdict is Verdict.HOLD


class Solver:
    """Recomputes the key of a quantitative item.

    Deliberately has no LLM fallback. A solver that can fall back to a model is
    a solver that can be talked out of its own evidence.
    """

    def verify(self, *, stratum: Stratum, derivation: str | None,
               keyed_value: str, keys: list[str]) -> Check:
        """Return a `Check`. Never raises; a failed evaluation is a refusal.

        `derivation` is a sympy-parseable expression in the item's own symbols,
        evaluating to the value of the keyed option. `keyed_value` is the keyed
        option's own expression text.
        """
        if stratum is Stratum.JUDGEMENT:
            if derivation:
                return self._refuse(
                    Failure.WRONG_STRATUM,
                    "a derivation was supplied for a judgement item; prose has "
                    "no solver",
                )
            # DELEGATED, never HOLD and never REFUSE. See `Verdict.DELEGATED`:
            # a prose key is verified by an independent blind second call (D2),
            # which is an opinion rather than a computation.
            return Check(verdict=Verdict.DELEGATED, failure=None, computed=None,
                         keyed=None,
                         detail="judgement stratum delegated to the blind second "
                                "call (D2); evidence is a second opinion, not a "
                                "computation")

        if stratum is Stratum.LOGIC:
            return self._check_logical(derivation=derivation,
                                       keyed_value=keyed_value)

        if not derivation:
            return self._refuse(
                Failure.NO_DERIVATION,
                "quant item carries no derivation, so its key cannot be "
                "recomputed and cannot be vouched for",
            )

        try:
            computed = sp.sympify(derivation, rational=True)
            keyed = sp.sympify(keyed_value, rational=True)
        except (sp.SympifyError, SyntaxError, TypeError) as exc:
            return self._refuse(
                Failure.UNRESOLVED_DERIVATION,
                f"derivation does not parse: {exc}",
            )

        if computed.free_symbols or keyed.free_symbols:
            return self._refuse(
                Failure.UNRESOLVED_DERIVATION,
                f"free symbols remain: {computed.free_symbols | keyed.free_symbols}",
            )

        # DEFENCE IN DEPTH, MEASURED UNREACHABLE. `sympify(..., rational=True)`
        # turns every decimal into an exact Rational, so `is_Float` is False on
        # every input and this branch cannot fire. Recorded rather than deleted
        # because the check is cheap and correct; the load-bearing defence
        # against a rounded key is KEY_MISMATCH below -- verified: derivation
        # `sqrt(2)/2` against keyed `1.41421` differs by `-141421/100000 +
        # sqrt(2)/2` and is refused. Do not count this branch in any claim
        # about what the solver catches.
        for expr, label in ((computed, "derivation"), (keyed, "keyed option")):
            if expr.has(sp.Integral, sp.Sum, sp.Derivative):
                return self._refuse(
                    Failure.UNRESOLVED_DERIVATION,
                    f"{label} is unevaluated calculus, not a number",
                )
            if expr.is_Float:  # pragma: no cover -- unreachable, see above
                return self._refuse(
                    Failure.NONEXACT,
                    f"{label} is a float ({expr}); an XAT key is exact",
                )

        try:
            computed_n = sp.nsimplify(computed)
            keyed_n = sp.nsimplify(keyed)
        except (TypeError, ValueError) as exc:
            return self._refuse(Failure.NONEXACT, f"cannot normalise: {exc}")

        if sp.simplify(computed_n - keyed_n) != 0:
            return Check(
                verdict=Verdict.REFUSE,
                failure=Failure.KEY_MISMATCH,
                computed=computed_n,
                keyed=keyed_n,
                detail=(
                    f"derivation gives {computed_n} but the key says {keyed_n}. "
                    f"Options were {keys}. Dropping the item -- not repairing it."
                ),
            )

        return Check(verdict=Verdict.HOLD, failure=None, computed=computed_n,
                     keyed=keyed_n, detail="key confirmed by recomputation")

    # -- logic stratum ------------------------------------------------------

    def _check_logical(self, *, derivation: str | None,
                       keyed_value: str) -> Check:  # noqa: ARG002
        """The logic stratum is enumerated by `enumeration.py`, not here.

        `keyed_value` is accepted and ignored on purpose: the signature is
        uniform across strata so that `verify` is total over `Stratum`, and
        renaming it would make a caller's mistake harder to see. This method
        exists so that a logic item routed through the solver with no
        enumeration is a REFUSE rather than a silent pass. Silently passing it
        would be the worst outcome available -- it would look like a grounded
        key.
        """
        if derivation is None:
            return self._refuse(
                Failure.NO_DERIVATION,
                "logic item needs an enumeration, not a closed-form derivation; "
                "route it through enumeration.py or refuse it",
            )
        return Check(
            verdict=Verdict.DELEGATED,
            failure=None,
            computed=None,
            keyed=None,
            detail="logic stratum delegated to enumeration; evidence is "
                   "exhaustive search, not a closed form",
        )

    @staticmethod
    def _refuse(failure: Failure, detail: str) -> Check:
        return Check(verdict=Verdict.REFUSE, failure=failure, computed=None,
                     keyed=None, detail=detail)


SOLVER = Solver()
