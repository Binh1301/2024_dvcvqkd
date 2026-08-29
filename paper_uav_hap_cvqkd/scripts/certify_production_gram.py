"""Certify the prospective C4-Gram production Holevo path without training/test use."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import time
from typing import Any

import torch

from _common import ROOT, load_yaml
from _numerical_validation import (
    ensemble_sha256,
    representative_ensembles,
    unique_ensemble_roster,
    validation_representative_states,
)
from src.cvqkd.holevo import HolevoResult, holevo_information
from src.cvqkd.mutual_information import (
    discrete_mutual_information,
    standard_complex_noise,
)
from src.modulation.joint_ps_gs import JointTransmitter


GRADIENT_NOISE_CHUNK_SIZE = 64
MOMENT_ABSOLUTE_TOLERANCE = 1e-7
MOMENT_RELATIVE_TOLERANCE = 1e-6
INFORMATION_ABSOLUTE_TOLERANCE = 1e-6
INFORMATION_RELATIVE_TOLERANCE = 1e-5
METRICS = ("C", "w", "Z", "lambda1", "lambda2", "lambda3", "chi_BE", "raw_K")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _metric_bound(name: str, reference: torch.Tensor) -> torch.Tensor:
    if name in {"chi_BE", "raw_K"}:
        return INFORMATION_ABSOLUTE_TOLERANCE + INFORMATION_RELATIVE_TOLERANCE * reference.abs()
    return MOMENT_ABSOLUTE_TOLERANCE + MOMENT_RELATIVE_TOLERANCE * reference.abs()


def _selected_mi_mean(
    evidence: dict[str, Any], fixture: str, required_sample_count: int
) -> torch.Tensor:
    selected = int(evidence["minimum_common_sample_count"])
    if selected != required_sample_count:
        raise ValueError("Maintained MI evidence sample count differs from diagnostic config.")
    trace = evidence["traces"][fixture]
    if "exact_duplicate_of" in trace:
        trace = evidence["traces"][trace["exact_duplicate_of"]]
    rows = []
    for replication in trace["replications"]:
        matches = [
            row for row in replication["rows"]
            if int(row["sample_count"]) == selected
        ]
        if len(matches) != 1:
            raise ValueError(f"Fixture {fixture} lacks one N_MC=2048 row per replication.")
        rows.append(matches[0]["mi_bits"])
    return torch.tensor(rows, dtype=torch.float64).mean(dim=0)


def _result_metrics(
    result: HolevoResult, mutual_information: torch.Tensor, beta: float
) -> dict[str, torch.Tensor]:
    return {
        "C": result.coherent_correlation,
        "w": result.w,
        "Z": result.z,
        "lambda1": result.covariance.lambda1,
        "lambda2": result.covariance.lambda2,
        "lambda3": result.covariance.lambda3,
        "chi_BE": result.chi_be,
        "raw_K": beta * mutual_information - result.chi_be,
    }


def _serial_metrics(values: dict[str, torch.Tensor]) -> dict[str, list[float]]:
    return {name: value.detach().tolist() for name, value in values.items()}


def _observable_comparison(
    candidate: dict[str, torch.Tensor], reference: dict[str, torch.Tensor]
) -> dict[str, Any]:
    errors = {name: (candidate[name] - reference[name]).detach().abs() for name in METRICS}
    bounds = {name: _metric_bound(name, reference[name].detach()) for name in METRICS}
    passes = {name: bool(torch.all(errors[name] <= bounds[name])) for name in METRICS}
    return {
        "maximum_absolute_errors": {name: float(errors[name].max()) for name in METRICS},
        "maximum_allowed_errors": {name: float(bounds[name].max()) for name in METRICS},
        "metric_passes": passes,
        "passes_all_frozen_observable_tolerances": all(passes.values()),
    }


def _source_diagnostics(result: HolevoResult) -> list[dict[str, Any]]:
    rows = result.diagnostics.get("source_moment_diagnostics")
    if not isinstance(rows, tuple):
        raise ValueError("Production result lacks C4-Gram source diagnostics.")
    return [dict(row) for row in rows]


def _support_signature(result: HolevoResult) -> list[list[list[bool]]]:
    return [
        [list(sector) for sector in row["sector_support_masks"]]
        for row in _source_diagnostics(result)
    ]


def _forward_replay(
    config: dict[str, Any],
    mi_evidence: dict[str, Any],
    hp_oracle: dict[str, Any],
    settings: dict[str, Any],
) -> dict[str, Any]:
    states, labels, transmittance, epsilon = validation_representative_states(config)
    complete = representative_ensembles(config, transmittance, epsilon)
    ensembles, aliases = unique_ensemble_roster(complete)
    expected = mi_evidence["certification_roster"]
    if states.realization_sha256 != expected["validation_state_realization_sha256"]:
        raise ValueError("Validation realization differs from the maintained MI evidence.")
    if labels != expected["state_labels"]:
        raise ValueError("Representative state labels differ from maintained MI evidence.")
    if transmittance.tolist() != expected["transmittance"] or epsilon.tolist() != expected["epsilon_snu"]:
        raise ValueError("Representative states differ from the maintained MI evidence.")
    observed_hashes = {name: ensemble_sha256(value) for name, value in ensembles.items()}
    if observed_hashes != expected["canonical_fixtures"] or aliases != expected["exact_duplicate_aliases"]:
        raise ValueError("Current canonical fixture roster differs from its hash binding.")
    beta = float(config["cvqkd"]["beta_reconciliation"])
    common_kwargs = {
        "backend": "c4_gram",
        "fock_cutoff": None,
        "require_supported_symmetry": True,
        "symmetry_tolerance": float(config["cvqkd"]["holevo_numerics"]["symmetry_tolerance"]),
        "density_trace_tolerance": float(config["cvqkd"]["holevo_numerics"]["density_trace_tolerance"]),
        "physicality_tolerance": float(config["cvqkd"]["holevo_numerics"]["physicality_tolerance"]),
    }
    rows = []
    all_observable = True
    support_identical_count = 0
    for name, ensemble in ensembles.items():
        print(f"production forward fixture={name}", flush=True)
        mi = _selected_mi_mean(mi_evidence, name, int(settings["gradient_sample_count"]))
        reference_result = holevo_information(
            ensemble, transmittance, epsilon,
            density_eigenvalue_tolerance=float(
                settings["reference_density_eigenvalue_threshold"]
            ), **common_kwargs,
        )
        production_result = holevo_information(
            ensemble, transmittance, epsilon,
            density_eigenvalue_tolerance=float(
                settings["candidate_density_eigenvalue_threshold"]
            ), **common_kwargs,
        )
        reference_metrics = _result_metrics(reference_result, mi, beta)
        production_metrics = _result_metrics(production_result, mi, beta)
        comparison = _observable_comparison(production_metrics, reference_metrics)
        support_identical = (
            _support_signature(reference_result) == _support_signature(production_result)
        )
        support_identical_count += int(support_identical)
        all_observable = all_observable and comparison[
            "passes_all_frozen_observable_tolerances"
        ]
        rows.append({
            "fixture": name,
            "ensemble_sha256": observed_hashes[name],
            "mutual_information_source": {
                "sample_count": int(mi_evidence["minimum_common_sample_count"]),
                "replication_aggregation": "arithmetic mean over five maintained CRN replications",
                "mi_bits": mi.tolist(),
            },
            "reference_1e_minus_14": {
                "values": _serial_metrics(reference_metrics),
                "source_diagnostics_by_state": _source_diagnostics(reference_result),
            },
            "production_1e_minus_13": {
                "values": _serial_metrics(production_metrics),
                "source_diagnostics_by_state": _source_diagnostics(production_result),
            },
            "observable_plateau": comparison,
            "support_plateau": {
                "support_identical": support_identical,
                "reference_sector_support_sizes_by_state": _support_signature(reference_result),
                "production_sector_support_sizes_by_state": _support_signature(production_result),
                "is_formal_threshold_certification_gate": True,
                "reason": (
                    "Security review requires identical support for formal threshold certification."
                ),
            },
        })

    stress = next(row for row in rows if row["fixture"] == "near_coincident_pseudoinverse_stress")
    hp = hp_oracle["selected_full_support_oracle"]
    hp_values = {
        "C": torch.full((3,), float(hp["C"]), dtype=torch.float64),
        "w": torch.full((3,), float(hp["w"]), dtype=torch.float64),
        **{
            metric: torch.tensor([float(state[metric]) for state in hp["states"]])
            for metric in ("Z", "lambda1", "lambda2", "lambda3", "chi_BE", "raw_K")
        },
    }
    stress_production = {
        name: torch.tensor(stress["production_1e_minus_13"]["values"][name])
        for name in METRICS
    }
    hp_comparison = _observable_comparison(stress_production, hp_values)
    return {
        "coverage_scope": "sixteen_hash_bound_canonical_reference_fixtures_on_three_validation_states",
        "future_selected_checkpoint_roster_covered": False,
        "actual_selected_checkpoint_roster_exists": False,
        "validation_state_realization_sha256": states.realization_sha256,
        "state_labels": labels,
        "transmittance": transmittance.tolist(),
        "epsilon_snu": epsilon.tolist(),
        "certification_roster_sha256": mi_evidence["certification_roster_sha256"],
        "canonical_fixture_count": len(ensembles),
        "exact_duplicate_aliases": aliases,
        "all_hash_bindings_match": True,
        "all_observable_plateaus_pass": all_observable,
        "support_identical_fixture_count": support_identical_count,
        "support_changed_fixture_count": len(ensembles) - support_identical_count,
        "formal_support_identity_gate_passes": support_identical_count == len(ensembles),
        "high_precision_stress_comparison": {
            "oracle_digits": hp_oracle["selected_full_support_oracle_digits"],
            "oracle_confirmation_digits": hp_oracle["confirmation_full_support_oracle_digits"],
            **hp_comparison,
        },
        "rows": rows,
    }


def _family(name: str) -> str | None:
    if name.startswith("ps_network."):
        return "ps"
    if name.startswith("gs_model."):
        return "gs"
    if name.startswith("va_network."):
        return "va"
    return None


def _index_from_flat(parameter: torch.Tensor, flat_index: int) -> tuple[int, ...]:
    return tuple(int(value) for value in torch.unravel_index(
        torch.tensor(flat_index), parameter.shape
    ))


def _gradient_components(
    model: JointTransmitter,
    transmittance: torch.Tensor,
    epsilon: torch.Tensor,
    noise: torch.Tensor,
    beta: float,
    *,
    sample_count: int,
    threshold: float,
) -> tuple[dict[str, torch.Tensor], HolevoResult]:
    ensemble = model(transmittance, epsilon)
    mi = discrete_mutual_information(
        ensemble,
        transmittance,
        epsilon,
        noise_samples_per_symbol=sample_count,
        standard_noise_samples=noise,
        noise_sample_chunk_size=GRADIENT_NOISE_CHUNK_SIZE,
        implementation="optimized",
    )
    holevo = holevo_information(
        ensemble,
        transmittance,
        epsilon,
        backend="c4_gram",
        fock_cutoff=None,
        density_trace_tolerance=1e-10,
        density_eigenvalue_tolerance=threshold,
        physicality_tolerance=1e-10,
    )
    return {
        "MI": mi.mean(),
        "chi_BE": holevo.chi_be.mean(),
        "raw_K": (beta * mi - holevo.chi_be).mean(),
    }, holevo


def _fd_bound(
    left: float, right: float, automatic: float, *, absolute: float, relative: float
) -> float:
    scale = max(abs(left), abs(right), abs(automatic))
    return absolute + relative * scale


def _has_three_adjacent_stable(
    derivatives: list[float], automatic: float, *, steps: tuple[float, ...],
    absolute: float, relative: float, required_pairs: int,
) -> tuple[bool, list[dict[str, Any]]]:
    comparisons = []
    consecutive = 0
    maximum_consecutive = 0
    for index, (left, right) in enumerate(zip(derivatives, derivatives[1:])):
        bound = _fd_bound(
            left, right, automatic, absolute=absolute, relative=relative
        )
        adjacent_error = abs(left - right)
        automatic_errors = (abs(left - automatic), abs(right - automatic))
        passed = adjacent_error <= bound and max(automatic_errors) <= bound
        consecutive = consecutive + 1 if passed else 0
        maximum_consecutive = max(maximum_consecutive, consecutive)
        comparisons.append({
            "larger_h": steps[index],
            "smaller_h": steps[index + 1],
            "adjacent_derivative_error": adjacent_error,
            "maximum_autograd_error": max(automatic_errors),
            "allowed_error": bound,
            "passes": passed,
        })
    return maximum_consecutive >= required_pairs, comparisons


def _gradient_diagnostic(config: dict[str, Any], settings: dict[str, Any]) -> dict[str, Any]:
    _, labels, transmittance, epsilon = validation_representative_states(config)
    cvqkd = config["cvqkd"]
    fixture_seed = int(config["numerical_validation"]["fixture_initialization_seed"])
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(fixture_seed)
        model = JointTransmitter(
            "full",
            v_min=float(cvqkd["v_min_snu"]),
            v_max=float(cvqkd["v_max_snu"]),
            n_peak_photons=float(cvqkd["n_peak_photons"]),
        )
    sample_count = int(settings["gradient_sample_count"])
    candidate_threshold = float(settings["candidate_density_eigenvalue_threshold"])
    steps = tuple(float(value) for value in settings["finite_difference_steps"])
    noise = standard_complex_noise(
        (transmittance.numel(), 256, sample_count),
        generator=torch.Generator().manual_seed(int(settings["gradient_crn_seed"])),
        device=transmittance.device,
    )
    named = [(name, parameter) for name, parameter in model.named_parameters()
             if _family(name) is not None]
    parameters = [parameter for _, parameter in named]
    model.zero_grad(set_to_none=True)
    objectives, center_holevo = _gradient_components(
        model, transmittance, epsilon, noise, float(cvqkd["beta_reconciliation"]),
        sample_count=sample_count, threshold=candidate_threshold,
    )
    gradient_maps: dict[str, dict[str, torch.Tensor]] = {}
    for metric_index, metric in enumerate(("MI", "chi_BE", "raw_K")):
        gradients = torch.autograd.grad(
            objectives[metric], parameters,
            retain_graph=metric_index < 2,
            allow_unused=False,
        )
        gradient_maps[metric] = {
            name: gradient.detach().clone()
            for (name, _), gradient in zip(named, gradients)
        }
    parameter_map = dict(named)
    predetermined: dict[str, list[tuple[str, tuple[int, ...]]]] = {
        "ps": [
            ("ps_network.network.2.bias", (0,)),
            ("ps_network.network.2.bias", (17,)),
            ("ps_network.network.2.bias", (42,)),
        ],
        "gs": [
            ("gs_model.raw_coordinates", (0, 0)),
            ("gs_model.raw_coordinates", (17, 1)),
            ("gs_model.raw_coordinates", (42, 0)),
        ],
        "va": [
            ("va_network.network.2.weight", (0, 0)),
            ("va_network.network.2.weight", (0, 31)),
            ("va_network.network.2.bias", (0,)),
        ],
    }
    coordinates: dict[str, list[dict[str, Any]]] = {}
    for family in ("ps", "gs", "va"):
        family_named = [(name, parameter) for name, parameter in named if _family(name) == family]
        max_name, max_parameter, max_flat, max_value = max(
            ((
                name,
                parameter,
                int(torch.argmax(gradient_maps["raw_K"][name].abs()).item()),
                float(gradient_maps["raw_K"][name].abs().max()),
            ) for name, parameter in family_named),
            key=lambda row: row[3],
        )
        requested = list(predetermined[family]) + [
            (max_name, _index_from_flat(max_parameter, max_flat))
        ]
        deduplicated = []
        for name, index in requested:
            if name not in parameter_map or any(
                axis < 0 or axis >= size for axis, size in zip(index, parameter_map[name].shape)
            ):
                raise ValueError(f"Invalid preregistered gradient coordinate {name}{index}.")
            if (name, index) not in deduplicated:
                deduplicated.append((name, index))
        coordinates[family] = [
            {
                "parameter": name,
                "index": list(index),
                "selection": (
                    "maximum_absolute_raw_K_autograd"
                    if (name, index) == requested[-1] else "predetermined"
                ),
            }
            for name, index in deduplicated
        ]

    center_signature = _support_signature(center_holevo)
    center_diagnostics = _source_diagnostics(center_holevo)
    rows = []
    all_pass = True
    for family, family_coordinates in coordinates.items():
        for coordinate in family_coordinates:
            name = coordinate["parameter"]
            index = tuple(coordinate["index"])
            parameter = parameter_map[name]
            original = float(parameter[index].detach())
            automatic = {
                metric: float(gradient_maps[metric][name][index])
                for metric in ("MI", "chi_BE", "raw_K")
            }
            h_rows = []
            derivatives = {metric: [] for metric in automatic}
            support_unchanged = True
            print(f"gradient family={family} parameter={name} index={index}", flush=True)
            for h in steps:
                evaluations = {}
                try:
                    for sign_name, sign in (("plus", 1.0), ("minus", -1.0)):
                        with torch.no_grad():
                            parameter[index] = original + sign * h
                            components, result = _gradient_components(
                                model, transmittance, epsilon, noise,
                                float(cvqkd["beta_reconciliation"]),
                                sample_count=sample_count,
                                threshold=candidate_threshold,
                            )
                        signature = _support_signature(result)
                        unchanged = signature == center_signature
                        support_unchanged = support_unchanged and unchanged
                        evaluations[sign_name] = {
                            "objectives": {key: float(value) for key, value in components.items()},
                            "support_signature": signature,
                            "support_unchanged_from_center": unchanged,
                            "source_diagnostics_by_state": _source_diagnostics(result),
                        }
                finally:
                    with torch.no_grad():
                        parameter[index] = original
                for metric in automatic:
                    derivative = (
                        evaluations["plus"]["objectives"][metric]
                        - evaluations["minus"]["objectives"][metric]
                    ) / (2.0 * h)
                    derivatives[metric].append(derivative)
                h_rows.append({
                    "h": h,
                    "plus": evaluations["plus"],
                    "minus": evaluations["minus"],
                    "central_derivatives": {
                        metric: derivatives[metric][-1] for metric in automatic
                    },
                })
            component_checks = {}
            coordinate_pass = support_unchanged
            for metric in automatic:
                stable, comparisons = _has_three_adjacent_stable(
                    derivatives[metric], automatic[metric], steps=steps,
                    absolute=float(settings["finite_difference_absolute_tolerance"]),
                    relative=float(settings["finite_difference_relative_tolerance"]),
                    required_pairs=int(settings["required_adjacent_stable_pairs"]),
                )
                component_checks[metric] = {
                    "autograd": automatic[metric],
                    "central_derivatives": derivatives[metric],
                    "adjacent_checks": comparisons,
                    "at_least_three_adjacent_stable_and_autograd_consistent": stable,
                }
                coordinate_pass = coordinate_pass and stable
            all_pass = all_pass and coordinate_pass
            rows.append({
                "family": family,
                **coordinate,
                "center_parameter_value": original,
                "center_support_signature": center_signature,
                "center_source_diagnostics_by_state": center_diagnostics,
                "all_plus_minus_support_masks_unchanged": support_unchanged,
                "component_checks": component_checks,
                "h_rows": h_rows,
                "passes": coordinate_pass,
            })
    return {
        "state_labels": labels,
        "transmittance": transmittance.tolist(),
        "epsilon_snu": epsilon.tolist(),
        "model": "deterministic untrained full transmitter at frozen fixture seed",
        "fixture_initialization_seed": fixture_seed,
        "crn_seed": int(settings["gradient_crn_seed"]),
        "mutual_information_sample_count": sample_count,
        "common_noise_reused_for_center_plus_minus_and_autograd": True,
        "finite_difference_steps": list(steps),
        "finite_difference_rule": {
            "absolute_tolerance": float(settings["finite_difference_absolute_tolerance"]),
            "relative_tolerance": float(settings["finite_difference_relative_tolerance"]),
            "required_adjacent_stable_pairs": int(settings["required_adjacent_stable_pairs"]),
            "support_mask_must_be_unchanged_for_every_plus_minus": True,
        },
        "all_coordinates_pass": all_pass,
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "default.yaml")
    parser.add_argument("--mi-evidence", type=Path, default=ROOT / "results" / "mi_convergence.json")
    parser.add_argument("--hp-oracle", type=Path, default=ROOT / "results" / "near_coincident_gram_oracle.json")
    parser.add_argument("--output", type=Path, default=ROOT / "results" / "production_gram_certification.json")
    args = parser.parse_args()
    started = time.perf_counter()
    config_path = args.config.resolve()
    mi_path = args.mi_evidence.resolve()
    hp_path = args.hp_oracle.resolve()
    config = load_yaml(config_path)
    settings = config["numerical_validation"]["production_gram_candidate_diagnostic"]
    mi_evidence = json.loads(mi_path.read_text(encoding="utf-8"))
    hp_oracle = json.loads(hp_path.read_text(encoding="utf-8"))
    if mi_evidence.get("minimum_common_sample_count") != int(
        settings["gradient_sample_count"]
    ):
        raise ValueError("Diagnostic requires the config-bound maintained MI sample count.")
    if settings.get("formal_threshold_certification") is not False or settings.get(
        "rule_status"
    ) != "OUTCOME_INFORMED_DIAGNOSTIC_NOT_FROZEN":
        raise ValueError("Candidate Gram rule must remain explicitly diagnostic and unfrozen.")
    if not hp_oracle.get("full_mathematical_support_oracle_obtained"):
        raise ValueError("Full-support high-precision stress oracle is unavailable.")
    forward = _forward_replay(config, mi_evidence, hp_oracle, settings)
    gradient = _gradient_diagnostic(config, settings)
    diagnostic_gates = (
        forward["all_hash_bindings_match"]
        and forward["all_observable_plateaus_pass"]
        and forward["high_precision_stress_comparison"][
            "passes_all_frozen_observable_tolerances"
        ]
        and gradient["all_coordinates_pass"]
    )
    formal_support_gate = forward["formal_support_identity_gate_passes"]
    formal_certification = bool(
        diagnostic_gates and formal_support_gate
        and settings["formal_threshold_certification"]
    )
    payload = {
        "schema_version": "production-c4-gram-certification-v1",
        "status": "PROSPECTIVE_DIAGNOSTIC_NOT_READY",
        "is_production_numerical_certification": False,
        "formal_threshold_certification": False,
        "rule_status": settings["rule_status"],
        "publication_training_performed": False,
        "test_set_used": False,
        "mb_grid_or_baseline_selection_performed": False,
        "production_backend": "c4_gram",
        "historical_backend": "fock_diagnostic_explicit_only",
        "candidate_density_eigenvalue_threshold": float(
            settings["candidate_density_eigenvalue_threshold"]
        ),
        "forward_reference_threshold": float(
            settings["reference_density_eigenvalue_threshold"]
        ),
        "support_plateau_is_formal_certification_gate": True,
        "forward_replay": forward,
        "gradient_diagnostic": gradient,
        "all_diagnostic_observable_gradient_hash_gates_pass": diagnostic_gates,
        "formal_support_identity_gate_passes": formal_support_gate,
        "all_required_gates_pass": formal_certification,
        "runtime_seconds": time.perf_counter() - started,
        "provenance": {
            "config_sha256": _sha256(config_path),
            "mi_evidence_sha256": _sha256(mi_path),
            "hp_oracle_sha256": _sha256(hp_path),
            "certification_script_sha256": _sha256(Path(__file__).resolve()),
            "holevo_source_sha256": _sha256(ROOT / "src" / "cvqkd" / "holevo.py"),
            "gram_source_sha256": _sha256(ROOT / "src" / "cvqkd" / "gram_moments.py"),
            "precision": "torch.float64 / torch.complex128 on CPU",
        },
    }
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {output} status={payload['status']}", flush=True)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
