"""Author-controlled physical peak domain and pre-convergence audit."""

from __future__ import annotations

import math
from typing import Any

import torch

from src.modulation.qam256 import reference_pmf, square_qam256


PEAK_DOMAIN_SCOPES = ("complete_preregistered_realizations",)
ALL_COMPARISON_SCHEMES = (
    "uniform", "binomial", "fixed_mb", "optimized_mb", "ps", "gs", "va",
    "ps_gs", "ps_va", "gs_va", "full",
)


def approved_peak_photon_limit(config: dict[str, Any]) -> float:
    """Return the author-approved limit or fail before scientific execution."""

    cvqkd = config.get("cvqkd")
    if not isinstance(cvqkd, dict):
        raise ValueError("Configuration is missing the cvqkd mapping.")
    value = cvqkd.get("n_peak_photons")
    if not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0.0:
        raise ValueError("cvqkd.n_peak_photons must be finite and positive.")
    if cvqkd.get("n_peak_author_approved") is not True:
        raise ValueError("cvqkd.n_peak_author_approved must be explicitly true.")
    if cvqkd.get("peak_domain_scope") not in PEAK_DOMAIN_SCOPES:
        raise ValueError(
            "cvqkd.peak_domain_scope must be one of: " + ", ".join(PEAK_DOMAIN_SCOPES)
        )
    return float(value)


def square_reference_papr(kind: str, *, nu_mb: float | None = None) -> float:
    """Compute the physical peak-to-average ratio of a square-QAM PMF."""

    points = square_qam256()
    probabilities = reference_pmf(kind, nu_mb=nu_mb)
    energy = points.abs().square()
    mean = torch.sum(probabilities * energy)
    return float((energy.max() / mean).detach())


def peak_feasible_reference_va_grid(
    kind: str,
    va_grid: list[float] | tuple[float, ...],
    *,
    n_peak_photons: float,
    nu_mb: float | None = None,
) -> tuple[float, ...]:
    """Return preregistered fixed-VA candidates satisfying the exact peak rule."""

    if not _finite_positive(n_peak_photons):
        raise ValueError("n_peak_photons must be finite and positive.")
    values = tuple(float(value) for value in va_grid)
    if not values or any(not _finite_positive(value) for value in values):
        raise ValueError("va_grid must be nonempty, finite, and positive.")
    papr = square_reference_papr(kind, nu_mb=nu_mb)
    return tuple(
        va for va in values
        if 0.5 * va * papr <= float(n_peak_photons) * (1.0 + 1e-12)
    )


def _numerical_reference_peak_energy(
    kind: str, modulation_variance_snu: float, *, nu_mb: float | None = None
) -> float:
    """Construct the normalized reference ensemble and return max |alpha|^2."""

    points = square_qam256()
    probabilities = reference_pmf(kind, nu_mb=nu_mb)
    relative_energy = points.abs().square()
    mean_relative_energy = torch.sum(probabilities * relative_energy)
    scale = torch.sqrt(
        torch.as_tensor(modulation_variance_snu, dtype=torch.float64)
        / (2.0 * mean_relative_energy)
    )
    return float((scale * points).abs().square().max().detach())


def amplitude_domain_certification(config: dict[str, Any]) -> dict[str, Any]:
    """Certify fixed-reference peaks and audit the common rule for all modes.

    This is deliberately not a global certificate for learned constellations.
    Those ensembles are generated only after optimization and therefore remain
    subject to the same fail-closed runtime guard and selected-roster audit.
    """

    domain = require_preconvergence_domain_ready(config)
    cvqkd = config["cvqkd"]
    search = config["baseline_search"]
    n_peak = float(cvqkd["n_peak_photons"])
    v_min = float(cvqkd["v_min_snu"])
    v_max = float(cvqkd["v_max_snu"])
    va_budget = float(cvqkd["v_a_budget_snu"])
    fixed_search_ceiling = min(v_max, va_budget)
    va_grid = tuple(float(value) for value in search["va_grid_snu"])
    nu_grid = tuple(float(value) for value in search["optimized_mb_nu_grid"])

    def fixed_reference(
        kind: str,
        *,
        nu: float | None = None,
        exact_papr: str | None = None,
    ) -> dict[str, Any]:
        papr = square_reference_papr(kind, nu_mb=nu)
        analytic_at_vmax = 0.5 * v_max * papr
        numeric_at_vmax = _numerical_reference_peak_energy(kind, v_max, nu_mb=nu)
        feasible = peak_feasible_reference_va_grid(
            kind, va_grid, n_peak_photons=n_peak, nu_mb=nu
        )
        excluded = [value for value in va_grid if value not in feasible]
        unconstrained_upper = 2.0 * n_peak / papr
        return {
            "nu_mb": nu,
            "papr": papr,
            "papr_exact": exact_papr,
            "analytic_peak_energy_at_v_max_photons": analytic_at_vmax,
            "numerical_peak_energy_at_v_max_photons": numeric_at_vmax,
            "analytic_numerical_absolute_error": abs(analytic_at_vmax - numeric_at_vmax),
            "peak_energy_at_fixed_search_ceiling_photons": 0.5 * fixed_search_ceiling * papr,
            "peak_feasible_va_upper_unclipped_snu": unconstrained_upper,
            "peak_feasible_va_range_within_common_box_snu": [
                v_min, min(v_max, unconstrained_upper)
            ],
            "full_common_va_box_certified": analytic_at_vmax <= n_peak * (1.0 + 1e-12),
            "fixed_search_feasible_va_candidates_snu": list(feasible),
            "fixed_search_peak_excluded_va_candidates_snu": excluded,
            "excluded_from_comparison": not bool(feasible),
        }

    uniform = fixed_reference("uniform", exact_papr="45/17")
    binomial = fixed_reference("binomial", exact_papr="15")
    fixed_mb = fixed_reference("mb", nu=float(cvqkd["mb_nu"]))
    optimized_mb_candidates = []
    for nu in nu_grid:
        row = fixed_reference("mb", nu=nu)
        row["all_preregistered_va_candidates_feasible"] = not bool(
            row["fixed_search_peak_excluded_va_candidates_snu"]
        )
        # The common grid is recorded once at report level; avoid duplicating
        # all 15 values in each of the 31 candidate records.
        del row["fixed_search_feasible_va_candidates_snu"]
        optimized_mb_candidates.append(row)

    analytic_modes = {"uniform", "binomial", "fixed_mb", "optimized_mb", "va"}
    scheme_audit: dict[str, Any] = {}
    for scheme in ALL_COMPARISON_SCHEMES:
        is_analytic = scheme in analytic_modes
        scheme_audit[scheme] = {
            "same_hard_peak_rule_photons": n_peak,
            "rule_applied_to_final_physical_amplitudes": True,
            "clipping_or_posthoc_renormalization": False,
            "fixed_reference_full_va_box_certified": is_analytic,
            "learned_selected_roster_required": not is_analytic,
            "status": (
                "ANALYTIC_AND_NUMERIC_FIXED_FAMILY_CERTIFIED"
                if is_analytic
                else "RUNTIME_ENFORCED_NOT_GLOBALLY_CERTIFIED_PRETRAINING"
            ),
        }
    # VA-only retains the fixed Uniform geometry and merely selects V_A(s).
    scheme_audit["va"]["reference_family"] = "uniform"

    all_fixed_feasible = (
        uniform["full_common_va_box_certified"]
        and binomial["full_common_va_box_certified"]
        and fixed_mb["full_common_va_box_certified"]
        and all(row["full_common_va_box_certified"] for row in optimized_mb_candidates)
    )
    return {
        "schema_version": "amplitude-domain-certification-v1",
        "status": (
            "PASS_FIXED_BASELINES_LEARNED_RUNTIME_GUARD_PENDING_SELECTED_ROSTER"
            if all_fixed_feasible else "FAIL_FIXED_BASELINE_DOMAIN"
        ),
        "is_fock_cutoff_certification": False,
        "publication_training_performed": False,
        "test_set_used": False,
        "classifications": {
            "beta_reconciliation": "AUTHOR_APPROVED",
            "v_min_snu": "AUTHOR_APPROVED",
            "v_max_snu": "AUTHOR_APPROVED",
            "v_a_budget_snu": "AUTHOR_APPROVED",
            "mean_photon_budget": "DERIVED",
            "n_peak_photons": "AUTHOR_APPROVED",
            "fixed_mb_nu": "AUTHOR_APPROVED",
            "optimized_mb_nu_domain": "AUTHOR_APPROVED",
            "va_grid_snu": "SOFTWARE_PREREGISTERED",
            "optimized_mb_nu_grid": "SOFTWARE_PREREGISTERED",
            "papr_and_peak_values": "DERIVED",
            "mi_samples_and_fock_cutoff": "PENDING_CONVERGENCE_SELECTION",
        },
        "classification_status": {
            "mi_samples_and_fock_cutoff": "PENDING_NOT_YET_SELECTED",
        },
        "approved_domain": {
            "beta_reconciliation": float(cvqkd["beta_reconciliation"]),
            "v_min_snu": v_min,
            "v_max_snu": v_max,
            "v_a_budget_snu": va_budget,
            "mean_photon_budget": va_budget / 2.0,
            "n_peak_photons": n_peak,
            "maximum_amplitude_abs": math.sqrt(n_peak),
            "fixed_mb_nu": float(cvqkd["mb_nu"]),
            "optimized_mb_nu_domain": [min(nu_grid), max(nu_grid)],
            "numerical_precision": config.get("evaluation", {}).get("numerical_precision"),
        },
        "software_preregistered_discretization": {
            "selection_data": "validation_only",
            "fixed_va_grid_snu": list(va_grid),
            "fixed_va_grid_step_snu": 0.1,
            "optimized_mb_nu_grid": list(nu_grid),
            "optimized_mb_nu_grid_step": 0.01,
            "chosen_before_validation_or_test_outcomes": True,
            "test_selection_forbidden": True,
        },
        "fixed_baseline_certification": {
            "uniform": uniform,
            "binomial": binomial,
            "fixed_mb": fixed_mb,
            "optimized_mb_candidates": optimized_mb_candidates,
            "all_fixed_families_full_common_va_box_certified": all_fixed_feasible,
            "binomial_v_max_boundary": {
                "v_a_snu": v_max,
                "analytic_peak_photons": binomial[
                    "analytic_peak_energy_at_v_max_photons"
                ],
                "equals_n_peak": abs(
                    binomial["analytic_peak_energy_at_v_max_photons"] - n_peak
                ) <= 1e-12,
                "purpose": "physical-domain boundary diagnostic; not a budget-feasible fixed-policy candidate",
            },
        },
        "all_eleven_rule_audit": scheme_audit,
        "all_eleven_modes_covered": set(scheme_audit) == set(ALL_COMPARISON_SCHEMES),
        "common_fail_closed_rule": domain["physical_rule"],
        "learned_roster": {
            "status": "UNRESOLVED_PRETRAINING",
            "global_peak_certification_claimed": False,
            "runtime_guard_required": True,
            "selected_roster_recertification_required": True,
        },
        "blockers_for_numerical_convergence_handoff": (
            [] if all_fixed_feasible else ["at least one fixed reference violates n_peak"]
        ),
    }


def _finite_positive(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(value) and value > 0.0


def preconvergence_domain_report(config: dict[str, Any]) -> dict[str, Any]:
    """Describe the proposed domain without certifying a numerical cutoff."""

    cvqkd = config.get("cvqkd", {})
    search = config.get("baseline_search", {})
    n_peak = cvqkd.get("n_peak_photons")
    approved = cvqkd.get("n_peak_author_approved") is True
    scope = cvqkd.get("peak_domain_scope")
    finite_limit = _finite_positive(n_peak)
    v_min = cvqkd.get("v_min_snu")
    v_max = cvqkd.get("v_max_snu")
    va_budget = cvqkd.get("v_a_budget_snu")
    finite_v_min = _finite_positive(v_min)
    finite_v_max = _finite_positive(v_max)
    finite_budget = _finite_positive(va_budget)
    va_grid = search.get("va_grid_snu")
    finite_va_grid = (
        isinstance(va_grid, list) and bool(va_grid)
        and all(_finite_positive(value) for value in va_grid)
        and all(right > left for left, right in zip(va_grid, va_grid[1:]))
    )
    domain_ready = finite_limit and approved and scope in PEAK_DOMAIN_SCOPES

    maximum_amplitude = math.sqrt(float(n_peak)) if finite_limit else None
    maximum_papr = (
        2.0 * float(n_peak) / float(v_min)
        if finite_limit and finite_v_min else None
    )
    references: dict[str, Any] = {
        "uniform": {"papr": square_reference_papr("uniform")},
        "binomial": {"papr": square_reference_papr("binomial")},
    }
    nu_ref = cvqkd.get("mb_nu")
    if isinstance(nu_ref, (int, float)) and math.isfinite(nu_ref) and nu_ref >= 0.0:
        references["fixed_mb"] = {
            "nu": float(nu_ref), "papr": square_reference_papr("mb", nu_mb=float(nu_ref))
        }
    else:
        references["fixed_mb"] = {"nu": None, "papr": None, "status": "unresolved"}
    nu_grid = search.get("optimized_mb_nu_grid")
    if isinstance(nu_grid, list) and nu_grid and all(
        isinstance(value, (int, float)) and math.isfinite(value) and value >= 0.0
        for value in nu_grid
    ):
        values = [square_reference_papr("mb", nu_mb=float(value)) for value in nu_grid]
        references["optimized_mb"] = {
            "nu_grid": [float(value) for value in nu_grid],
            "minimum_papr_on_grid": min(values),
            "maximum_papr_on_grid": max(values),
        }
    else:
        references["optimized_mb"] = {
            "nu_grid": None, "minimum_papr_on_grid": None,
            "maximum_papr_on_grid": None, "status": "unresolved",
        }

    for value in references.values():
        papr = value.get("papr", value.get("maximum_papr_on_grid"))
        value["minimum_peak_photons_at_v_min"] = (
            0.5 * float(v_min) * float(papr)
            if finite_v_min and isinstance(papr, (int, float)) else None
        )
        value["v_min_feasible_under_proposed_peak"] = (
            bool(0.5 * float(v_min) * float(papr) <= float(n_peak) * (1.0 + 1e-12))
            if finite_limit and finite_v_min and isinstance(papr, (int, float)) else None
        )
        papr_for_grid = value.get("papr", value.get("minimum_papr_on_grid"))
        value["peak_feasible_va_candidates"] = (
            [
                float(va) for va in va_grid
                if 0.5 * float(va) * float(papr_for_grid)
                <= float(n_peak) * (1.0 + 1e-12)
            ]
            if finite_limit and finite_va_grid and isinstance(papr_for_grid, (int, float))
            else None
        )

    mandatory_baselines_feasible = all(
        isinstance(value.get("peak_feasible_va_candidates"), list)
        and bool(value["peak_feasible_va_candidates"])
        for value in references.values()
    )
    blockers: list[str] = []
    if not finite_limit:
        blockers.append("cvqkd.n_peak_photons is not finite and positive")
    if not approved:
        blockers.append("cvqkd.n_peak_author_approved is not true")
    if scope not in PEAK_DOMAIN_SCOPES:
        blockers.append("cvqkd.peak_domain_scope is unresolved")
    if not finite_v_min or not finite_v_max or float(v_min) >= float(v_max):
        blockers.append("the common finite 0 < V_min < V_max box is unresolved")
    if not finite_budget or (finite_v_min and float(va_budget) < float(v_min)):
        blockers.append("the common finite V_A budget is unresolved or below V_min")
    if not finite_va_grid:
        blockers.append("the common fixed-V_A validation grid is unresolved")
    elif finite_v_min and finite_v_max and finite_budget and any(
        float(value) < float(v_min)
        or float(value) > min(float(v_max), float(va_budget)) for value in va_grid
    ):
        blockers.append("the fixed-V_A validation grid violates the common energy domain")
    if references["fixed_mb"].get("papr") is None:
        blockers.append("fixed-MB reference nu is unresolved")
    if references["optimized_mb"].get("maximum_papr_on_grid") is None:
        blockers.append("optimized-MB validation nu grid is unresolved")
    if domain_ready and finite_v_min and not mandatory_baselines_feasible:
        blockers.append("the proposed domain excludes at least one mandatory fixed benchmark at V_min")

    scheme_fairness = {
        scheme: {
            "same_va_box": True,
            "same_average_photon_budget": True,
            "same_hard_peak_photon_rule": True,
            "mandatory_benchmark_excluded": (
                not bool(references[scheme]["peak_feasible_va_candidates"])
                if scheme in references
                and isinstance(references[scheme].get("peak_feasible_va_candidates"), list)
                else None
            ),
        }
        for scheme in ALL_COMPARISON_SCHEMES
    }
    return {
        "schema_version": "preconvergence-domain-report-v1",
        "status": "READY_FOR_CONVERGENCE_EXECUTION" if not blockers else "BLOCKED_UNRESOLVED",
        "is_fock_cutoff_certification": False,
        "test_set_used": False,
        "physical_rule": "max_i |alpha_i(T,epsilon)|^2 <= n_peak",
        "n_peak_photons": float(n_peak) if finite_limit else None,
        "n_peak_author_approved": approved,
        "peak_domain_scope": scope,
        "maximum_permitted_amplitude_abs": maximum_amplitude,
        "maximum_permitted_photon_number": float(n_peak) if finite_limit else None,
        "maximum_permitted_papr_over_va_box": maximum_papr,
        "worst_case_domain_statement": (
            "The hard rule directly bounds every final physical symbol by sqrt(n_peak); "
            "the worst PAPR occurs at V_A=V_min and is at most 2*n_peak/V_min. "
            "No separate q or z bound is used, and no post-hoc clipping is allowed."
        ),
        "reference_baseline_domain_audit": references,
        "scheme_fairness_audit": scheme_fairness,
        "all_eleven_schemes": list(ALL_COMPARISON_SCHEMES),
        "common_rule_applies_to_all_eleven": True,
        "mandatory_fixed_benchmarks_feasible": mandatory_baselines_feasible,
        "physical_domain_configuration_complete": bool(
            domain_ready and finite_v_min and finite_v_max and mandatory_baselines_feasible
        ),
        "blockers": blockers,
    }


def require_preconvergence_domain_ready(config: dict[str, Any]) -> dict[str, Any]:
    """Fail before expensive selection/training when the common domain is unresolved."""

    report = preconvergence_domain_report(config)
    if report["status"] != "READY_FOR_CONVERGENCE_EXECUTION":
        raise ValueError("Physical amplitude domain is unresolved: " + "; ".join(report["blockers"]))
    return report
