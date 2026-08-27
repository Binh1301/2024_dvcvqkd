"""Validation-only, energy-fair scalar searches for frozen baselines."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Callable, Iterable


@dataclass(frozen=True)
class BaselineCandidate:
    scheme: str
    modulation_variance_snu: float
    mb_nu: float | None
    validation_raw_skr: float | None
    physical_domain_admissible: bool = True
    ineligibility_reason: str | None = None


@dataclass(frozen=True)
class BaselineSelection:
    scheme: str
    selected: BaselineCandidate
    candidates: tuple[BaselineCandidate, ...]
    split_used_for_selection: str = "validation"
    test_set_used: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "scheme": self.scheme,
            "selected": asdict(self.selected),
            "candidates": [asdict(candidate) for candidate in self.candidates],
            "split_used_for_selection": self.split_used_for_selection,
            "test_set_used": self.test_set_used,
        }


def feasible_fixed_va_grid(
    values: Iterable[float], *, v_min: float, v_max: float, va_budget: float
) -> tuple[float, ...]:
    """Validate the common pointwise box and fixed-policy average budget."""

    if not all(math.isfinite(value) for value in (v_min, v_max, va_budget)):
        raise ValueError("V_A bounds and budget must be finite.")
    if not 0.0 < v_min < v_max or not v_min <= va_budget:
        raise ValueError("Require 0 < V_min < V_max and V_A_budget >= V_min.")
    grid = tuple(float(value) for value in values)
    if not grid or any(not math.isfinite(value) for value in grid):
        raise ValueError("V_A search grid must be nonempty and finite.")
    if any(right <= left for left, right in zip(grid, grid[1:])):
        raise ValueError("V_A search grid must be strictly increasing.")
    maximum_feasible = min(v_max, va_budget)
    if any(value < v_min or value > maximum_feasible for value in grid):
        raise ValueError(
            "Every fixed V_A candidate must satisfy the common box and average V_A budget."
        )
    return grid


def validation_only_baseline_search(
    *,
    split_name: str,
    va_grid: Iterable[float],
    v_min: float,
    v_max: float,
    va_budget: float,
    reference_mb_nu: float,
    optimized_mb_nu_grid: Iterable[float],
    score_validation_candidate: Callable[[str, float, float | None], float | None],
) -> dict[str, BaselineSelection]:
    """Select Uniform/Binomial/fixed-MB/optimized-MB on validation only.

    The callback receives ``(scheme, V_A, nu)`` and must evaluate only the
    already frozen validation realization.  This API deliberately has no test
    argument.  Deterministic ties prefer lower V_A, then lower nu.
    """

    if split_name != "validation":
        raise ValueError("Baseline and hyperparameter selection is validation-only.")
    va_values = feasible_fixed_va_grid(
        va_grid, v_min=v_min, v_max=v_max, va_budget=va_budget
    )
    if not math.isfinite(reference_mb_nu) or reference_mb_nu < 0.0:
        raise ValueError("reference_mb_nu must be finite and nonnegative.")
    nu_values = tuple(float(value) for value in optimized_mb_nu_grid)
    if not nu_values or any(not math.isfinite(value) or value < 0.0 for value in nu_values):
        raise ValueError("optimized MB nu grid must be nonempty, finite, and nonnegative.")
    if any(right <= left for left, right in zip(nu_values, nu_values[1:])):
        raise ValueError("optimized MB nu grid must be strictly increasing.")

    definitions = {
        "uniform": ("uniform", (None,)),
        "binomial": ("binomial", (None,)),
        "fixed_mb": ("mb", (reference_mb_nu,)),
        "optimized_mb": ("mb", nu_values),
    }
    selections: dict[str, BaselineSelection] = {}
    for label, (evaluation_scheme, nus) in definitions.items():
        candidates: list[BaselineCandidate] = []
        for nu in nus:
            for va in va_values:
                score_value = score_validation_candidate(evaluation_scheme, va, nu)
                if score_value is None:
                    candidates.append(BaselineCandidate(
                        label, va, nu, None, False,
                        "violates the common hard physical peak-photon domain",
                    ))
                    continue
                score = float(score_value)
                if not math.isfinite(score):
                    raise FloatingPointError(f"Non-finite validation score for {label}.")
                candidates.append(BaselineCandidate(label, va, nu, score))
        eligible = [candidate for candidate in candidates if candidate.physical_domain_admissible]
        if not eligible:
            raise ValueError(
                f"The common energy/peak domain excludes every preregistered {label} candidate."
            )
        # max raw SKR; deterministic conservative-energy tie-break.
        selected = min(
            eligible,
            key=lambda row: (-float(row.validation_raw_skr), row.modulation_variance_snu,
                             -1.0 if row.mb_nu is None else row.mb_nu),
        )
        selections[label] = BaselineSelection(label, selected, tuple(candidates))
    return selections
