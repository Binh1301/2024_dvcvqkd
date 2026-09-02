"""Bisection, one-sided CRN derivatives, and adversarial rollback near support boundaries."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import time
from typing import Any, Callable

import torch

from _common import ROOT, load_yaml
from _numerical_validation import (
    representative_ensembles, unique_ensemble_roster, validation_representative_states,
)
from audit_direct_support_boundaries import _single_state, _support
from src.cvqkd.holevo import holevo_information
from src.cvqkd.mutual_information import discrete_mutual_information, standard_complex_noise
from src.modulation.joint_ps_gs import Ensemble
from src.modulation.normalization import physical_amplitudes
from src.modulation.qam256 import (
    c4_orbit_indices, c4_orbit_masses, expand_c4_orbit_masses, expand_c4_orbit_values,
)


THRESHOLD = 1e-13
BISECTION_MAX_ITERATIONS = 60
BISECTION_WIDTH = 1e-12
CRN_SEED = 202615
N_MC = 2048
NOISE_CHUNK_SIZE = 64
VA_RHOS = (1e-4, 1e-5, 1e-6, 1e-7, 1e-8)
PS_RHOS = (1e-4, 1e-6, 1e-7)
GS_RHOS = (1e-4, 1e-6)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _path_ensemble(
    base: Ensemble, state_index: int, family: str, u: torch.Tensor, *, sign: float = 1.0,
) -> Ensemble:
    probability, raw, va = _single_state(base, state_index)
    indices = c4_orbit_indices(device=probability.device)
    if family == "ps_eta0_negative":
        q = c4_orbit_masses(probability)
        direction = torch.zeros_like(q)
        direction[0] = -1.0
        probability = expand_c4_orbit_masses(torch.softmax(torch.log(q) + u * direction, -1))
    elif family == "gs_z0_real_positive":
        prototypes = raw[indices[:, 0]]
        real = torch.view_as_real(prototypes)
        direction = torch.zeros_like(real)
        direction[0, 0] = 1.0
        prototypes = torch.view_as_complex(real + u * direction)
        prototypes = prototypes / torch.sqrt(torch.mean(prototypes.abs().square()))
        raw = expand_c4_orbit_values(prototypes)
    elif family == "log_va":
        va = va * torch.exp(sign * u)
    else:
        raise ValueError(f"Unknown path {family}.")
    amplitudes = physical_amplitudes(probability, raw, va)
    result = Ensemble(
        probability.unsqueeze(0), amplitudes, va.reshape(1), raw,
        exact_csi_oracle=True, c4_symmetric=True,
    )
    result.validate()
    return result


def _bisection(
    builder: Callable[[torch.Tensor], Ensemble], lower: float, upper: float,
) -> dict[str, Any]:
    lower_support = _support(builder(torch.tensor(lower, dtype=torch.float64)))
    upper_support = _support(builder(torch.tensor(upper, dtype=torch.float64)))
    if lower_support["mask"] == upper_support["mask"]:
        raise ValueError("Bisection bracket does not straddle a support transition.")
    iterations = 0
    while upper - lower > BISECTION_WIDTH and iterations < BISECTION_MAX_ITERATIONS:
        midpoint = 0.5 * (lower + upper)
        middle_support = _support(builder(torch.tensor(midpoint, dtype=torch.float64)))
        if middle_support["mask"] == lower_support["mask"]:
            lower = midpoint
            lower_support = middle_support
        else:
            upper = midpoint
            upper_support = middle_support
        iterations += 1
    if upper - lower > BISECTION_WIDTH:
        raise RuntimeError("Bisection failed to reach the preregistered width.")
    return {
        "lower": lower,
        "upper": upper,
        "center": 0.5 * (lower + upper),
        "width": upper - lower,
        "iterations": iterations,
        "rank_lower": lower_support["rank"],
        "rank_upper": upper_support["rank"],
        "nearest_eigenvalue_lower": lower_support["nearest_eigenvalue"],
        "nearest_eigenvalue_upper": upper_support["nearest_eigenvalue"],
    }


def _metrics(
    ensemble: Ensemble, transmittance: torch.Tensor, epsilon: torch.Tensor,
    noise: torch.Tensor, beta: float,
) -> dict[str, torch.Tensor]:
    mi = discrete_mutual_information(
        ensemble, transmittance.reshape(1), epsilon.reshape(1),
        noise_samples_per_symbol=N_MC, standard_noise_samples=noise,
        noise_sample_chunk_size=NOISE_CHUNK_SIZE, implementation="optimized",
    )[0]
    holevo = holevo_information(
        ensemble, transmittance.reshape(1), epsilon.reshape(1),
        backend="c4_gram", fock_cutoff=None, density_trace_tolerance=1e-10,
        density_eigenvalue_tolerance=THRESHOLD, physicality_tolerance=1e-10,
    )
    chi = holevo.chi_be[0]
    return {"MI": mi, "chi_BE": chi, "raw_K": beta * mi - chi}


def _center_derivatives(
    builder: Callable[[torch.Tensor], Ensemble], center: float, h: float,
    transmittance: torch.Tensor, epsilon: torch.Tensor, noise: torch.Tensor, beta: float,
) -> dict[str, Any]:
    u = torch.tensor(center, dtype=torch.float64, requires_grad=True)
    automatic_values = _metrics(builder(u), transmittance, epsilon, noise, beta)
    automatic = {}
    for index, metric in enumerate(("chi_BE", "raw_K")):
        automatic[metric] = float(torch.autograd.grad(
            automatic_values[metric], u, retain_graph=index == 0
        )[0])
    finite_values = {}
    with torch.no_grad():
        for side, offset in (("plus", h), ("minus", -h)):
            values = _metrics(
                builder(torch.tensor(center + offset, dtype=torch.float64)),
                transmittance, epsilon, noise, beta,
            )
            finite_values[side] = {name: float(value) for name, value in values.items()}
    finite_difference = {
        metric: (finite_values["plus"][metric] - finite_values["minus"][metric]) / (2 * h)
        for metric in ("chi_BE", "raw_K")
    }
    return {
        "center": center,
        "h": h,
        "values": {name: float(value.detach()) for name, value in automatic_values.items()},
        "rank": _support(builder(torch.tensor(center, dtype=torch.float64)))["rank"],
        "autograd": automatic,
        "central_finite_difference": finite_difference,
        "relative_autograd_fd_error": {
            metric: abs(automatic[metric] - finite_difference[metric])
            / max(abs(automatic[metric]), torch.finfo(torch.float64).tiny)
            for metric in automatic
        },
    }


def _one_sided(
    builder: Callable[[torch.Tensor], Ensemble], boundary: float, rhos: tuple[float, ...],
    transmittance: torch.Tensor, epsilon: torch.Tensor, beta: float,
) -> list[dict[str, Any]]:
    noise = standard_complex_noise(
        (1, 256, N_MC), generator=torch.Generator().manual_seed(CRN_SEED),
        device=transmittance.device,
    )
    rows = []
    for rho in rhos:
        left = _center_derivatives(
            builder, boundary - rho, rho / 4, transmittance, epsilon, noise, beta
        )
        right = _center_derivatives(
            builder, boundary + rho, rho / 4, transmittance, epsilon, noise, beta
        )
        rows.append({
            "rho": rho,
            "left": left,
            "right": right,
            "forward_gap": {
                metric: abs(right["values"][metric] - left["values"][metric])
                for metric in ("chi_BE", "raw_K")
            },
        })
    return rows


def _outward_rollback(
    builder: Callable[[torch.Tensor], Ensemble], boundary: float,
) -> list[dict[str, Any]]:
    rows = []
    for offset in (5e-5, 5e-4, 5e-3):
        current = boundary - offset
        current_support = _support(builder(torch.tensor(current, dtype=torch.float64)))
        accepted = 0
        rejected = 0
        current_streak = 0
        maximum_streak = 0
        for _ in range(50):
            proposed = current + 1e-4
            proposed_support = _support(builder(torch.tensor(proposed, dtype=torch.float64)))
            if proposed_support["mask"] == current_support["mask"]:
                current = proposed
                current_support = proposed_support
                accepted += 1
                current_streak = 0
            else:
                rejected += 1
                current_streak += 1
                maximum_streak = max(maximum_streak, current_streak)
        rows.append({
            "starting_offset_below_boundary": offset,
            "proposal_increment": 1e-4,
            "horizon": 50,
            "accepted": accepted,
            "rejected": rejected,
            "maximum_consecutive_rejections": maximum_streak,
            "final_u": current,
        })
    return rows


def run(config: dict[str, Any], *, config_path: Path, output_path: Path,
        environment_manifest_path: Path, confirmation_roster_path: Path,
        schema_path: Path, skip_crn: bool) -> dict[str, Any]:
    validation, labels, transmittance, epsilon = validation_representative_states(config)
    ensembles, _ = unique_ensemble_roster(
        representative_ensembles(config, transmittance, epsilon)
    )
    deformed = ensembles["deterministic_deformed_full"]
    binomial = ensembles["binomial_high_va_1.5"]
    builders: dict[str, tuple[Callable[[torch.Tensor], Ensemble], int, tuple[float, float]]] = {}
    for state_index, label, upper in ((0, "bad", 0.003), (1, "medium", 0.03), (2, "good", 0.03)):
        builders[f"deformed_full_logva_{label}"] = (
            lambda u, index=state_index: _path_ensemble(deformed, index, "log_va", u),
            state_index, (0.0, upper),
        )
    builders.update({
        "binomial_high_ps_bad": (
            lambda u: _path_ensemble(binomial, 0, "ps_eta0_negative", u), 0, (0.0, 0.3)
        ),
        "binomial_high_gs_bad": (
            lambda u: _path_ensemble(binomial, 0, "gs_z0_real_positive", u), 0, (0.0, 0.1)
        ),
        "binomial_high_logva_negative_bad": (
            lambda u: _path_ensemble(binomial, 0, "log_va", u, sign=-1.0), 0, (0.0, 0.03)
        ),
    })
    started = time.perf_counter()
    bisections = {
        name: {"state": labels[state_index], **_bisection(builder, *bracket)}
        for name, (builder, state_index, bracket) in builders.items()
    }
    va_builder = builders["deformed_full_logva_bad"][0]
    ps_builder = builders["binomial_high_ps_bad"][0]
    gs_builder = builders["binomial_high_gs_bad"][0]
    crn = None
    if not skip_crn:
        beta = float(config["cvqkd"]["beta_reconciliation"])
        crn = {
            "deformed_full_logva_bad": _one_sided(
                va_builder, bisections["deformed_full_logva_bad"]["center"], VA_RHOS,
                transmittance[0], epsilon[0], beta,
            ),
            "binomial_high_ps_bad": _one_sided(
                ps_builder, bisections["binomial_high_ps_bad"]["center"], PS_RHOS,
                transmittance[0], epsilon[0], beta,
            ),
            "binomial_high_gs_bad": _one_sided(
                gs_builder, bisections["binomial_high_gs_bad"]["center"], GS_RHOS,
                transmittance[0], epsilon[0], beta,
            ),
        }
    rollback = _outward_rollback(
        va_builder, bisections["deformed_full_logva_bad"]["center"]
    )
    dependencies = {
        "config": config_path,
        "final_model_spec": ROOT / "docs" / "FINAL_MODEL_SPEC.md",
        "holevo": ROOT / "src" / "cvqkd" / "holevo.py",
        "gram": ROOT / "src" / "cvqkd" / "gram_moments.py",
        "mutual_information": ROOT / "src" / "cvqkd" / "mutual_information.py",
        "script": Path(__file__).resolve(),
        "environment_manifest": environment_manifest_path,
        "confirmation_roster": confirmation_roster_path,
        "schema": schema_path,
    }
    hashes = {
        name: {"path": str(path.relative_to(ROOT)), "sha256": _sha256(path)}
        for name, path in dependencies.items()
    }
    if hashes["final_model_spec"]["sha256"] != (
        "561fecc97cdf9967034ffd6865c1605804b624b98f47a091e47f17e520a2a7b1"
    ):
        raise ValueError("FINAL_MODEL_SPEC.md hash changed.")
    result = {
        "schema_version": "support-boundary-bisection-crn-v1",
        "status": "PROPOSED_DIAGNOSTIC_ONLY_NOT_FROZEN",
        "preregistered_design": {
            "threshold": THRESHOLD,
            "bisection_max_iterations": BISECTION_MAX_ITERATIONS,
            "bisection_stop_width": BISECTION_WIDTH,
            "crn_seed": CRN_SEED,
            "mutual_information_sample_count": N_MC,
            "noise_chunk_size": NOISE_CHUNK_SIZE,
            "va_rhos": list(VA_RHOS), "ps_rhos": list(PS_RHOS), "gs_rhos": list(GS_RHOS),
            "one_sided_center_rule": "b-rho and b+rho; central FD h=rho/4 on each side",
            "rollback_rule": (
                "start b-offset; propose fixed outward +1e-4 for 50 segments; accept only "
                "when the exact support mask equals current, otherwise retain current"
            ),
        },
        "lifecycle_guards": {
            "publication_training_performed": False, "test_set_accessed": False,
            "final_held_out_evaluation_performed": False,
            "optimized_mb_grid_performed": False, "baseline_selection_performed": False,
            "active_config_changed": False, "physical_or_security_functional_changed": False,
        },
        "validation_state_realization_sha256": validation.realization_sha256,
        "bisections": bisections,
        "one_sided_crn": crn,
        "outward_rollback": rollback,
        "interpretation": (
            "This artifact contains only values regenerated by this script. Naive exact-mask "
            "rollback can trap outward motion near a boundary; any proposed protocol needs an "
            "enhanced segment guard/backtracking rule and fresh prospective review."
        ),
        "runtime_seconds": time.perf_counter() - started,
        "provenance": {
            "input_and_source_hashes": hashes,
            "output_path": str(output_path.relative_to(ROOT)),
            "repository_commit": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            "producer_sha256": hashes["script"]["sha256"],
            "config_sha256": hashes["config"]["sha256"],
            "input_roster_sha256": hashes["confirmation_roster"]["sha256"],
            "environment_manifest_sha256": hashes["environment_manifest"]["sha256"],
            "schema_sha256": hashes["schema"]["sha256"],
            "numerical_precision": "torch.float64 / torch.complex128 on CPU",
            "threshold_under_evaluation": THRESHOLD,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        },
    }
    result["provenance"]["runtime_environment"] = {
        "torch_version": torch.__version__,
        "torch_num_threads": torch.get_num_threads(),
        "torch_num_interop_threads": torch.get_num_interop_threads(),
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "default.yaml")
    parser.add_argument("--environment-manifest", type=Path, default=ROOT / "results" / "current_environment_manifest.json")
    parser.add_argument("--confirmation-roster", type=Path, default=ROOT / "results" / "independent_confirmation_roster.json")
    parser.add_argument("--schema", type=Path, default=ROOT / "schemas" / "support_boundary_bisection_crn.schema.json")
    parser.add_argument("--output", type=Path, default=ROOT / "results" / "support_boundary_bisection_crn_regenerated.json")
    parser.add_argument("--skip-crn", action="store_true")
    args = parser.parse_args()
    result = run(
        load_yaml(args.config), config_path=args.config.resolve(),
        output_path=args.output.resolve(),
        environment_manifest_path=args.environment_manifest.resolve(),
        confirmation_roster_path=args.confirmation_roster.resolve(),
        schema_path=args.schema.resolve(), skip_crn=args.skip_crn,
    )
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"], "bisections": result["bisections"],
        "outward_rollback": result["outward_rollback"],
        "runtime_seconds": result["runtime_seconds"], "output": str(args.output),
    }, indent=2))


if __name__ == "__main__":
    main()
