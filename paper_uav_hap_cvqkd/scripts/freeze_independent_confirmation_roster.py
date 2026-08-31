"""Freeze an outcome-uninspected confirmation roster without Holevo evaluation."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import subprocess
from typing import Any

import torch

from _common import ROOT, load_yaml
from _numerical_validation import (
    ensemble_sha256,
    representative_ensembles,
    unique_ensemble_roster,
)
from _train import _channel
from src.modulation.joint_ps_gs import Ensemble, enforce_peak_photon_constraint
from src.modulation.qam256 import expand_c4_orbit_masses, expand_c4_orbit_values
from src.validation.convergence import select_representative_state_indices


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def stress_ensemble(phase_step: float, *, batch_size: int, v_max: float,
                    n_peak: float) -> Ensemble:
    if not math.isfinite(phase_step) or phase_step <= 0.0:
        raise ValueError("Near-coincident phase step must be finite and positive.")
    masses = torch.full((64,), 1.0 / 64.0, dtype=torch.float64)
    index = torch.arange(64, dtype=torch.float64)
    prototypes = math.sqrt(v_max / 2.0) * torch.exp(1j * phase_step * index)
    probabilities = expand_c4_orbit_masses(masses)
    amplitudes = expand_c4_orbit_values(prototypes)
    ensemble = Ensemble(
        probabilities.unsqueeze(0).expand(batch_size, -1),
        amplitudes.unsqueeze(0).expand(batch_size, -1),
        torch.full((batch_size,), v_max, dtype=torch.float64),
        amplitudes,
        exact_csi_oracle=True,
        c4_symmetric=True,
    )
    ensemble.validate()
    enforce_peak_photon_constraint(ensemble, n_peak)
    return ensemble


def fixture_class(name: str) -> str:
    prefixes = (
        ("uniform_", "fixed_uniform"),
        ("binomial_", "fixed_binomial"),
        ("fixed_mb_", "fixed_mb"),
        ("optimized_mb_", "fixed_optimized_mb_domain_extrema"),
        ("untrained_", "untrained_full"),
        ("deterministic_ps_", "deterministic_ps"),
        ("deterministic_gs_", "deterministic_gs"),
        ("deterministic_va_", "deterministic_va"),
        ("deterministic_deformed_", "deterministic_mixed"),
        ("near_coincident_", "analytic_near_coincident"),
        ("hard_peak_", "analytic_peak_boundary"),
    )
    return next((label for prefix, label in prefixes if name.startswith(prefix)), "other")


def run(default_config_path: Path, roster_config_path: Path,
        environment_manifest_path: Path, schema_path: Path, output_path: Path) -> dict[str, Any]:
    if output_path.exists():
        raise FileExistsError(
            f"Immutable confirmation roster already exists: {output_path}. "
            "Use a new certification-cycle path instead of overwriting it."
        )
    config = load_yaml(default_config_path)
    design = load_yaml(roster_config_path)
    if design.get("outcome_inspection_status") != "NOT_INSPECTED":
        raise ValueError("Roster must be frozen before candidate-outcome inspection.")
    if environment_manifest_path.exists() is False:
        raise FileNotFoundError("Capture the locked environment manifest before roster freeze.")

    forbidden_seeds = {
        int(value) for value in config["training"]["seeds"].values()
    }
    forbidden_seeds.update(int(value) for value in config["numerical_validation"]["mi"]["seeds"])
    forbidden_seeds.add(int(config["numerical_validation"]["fixture_initialization_seed"]))
    forbidden_seeds.add(int(config["numerical_validation"]["production_gram_candidate_diagnostic"]["gradient_crn_seed"]))
    channel_seed = int(design["channel_base_seed"])
    fixture_seed = int(design["fixture_initialization_seed"])
    if channel_seed in forbidden_seeds or fixture_seed in forbidden_seeds or channel_seed == fixture_seed:
        raise ValueError("Independent confirmation seeds overlap an existing project seed.")

    states = _channel(config, int(design["channel_sample_count"]), channel_seed)
    indices = select_representative_state_indices(states.transmittance, states.excess_noise_snu)
    labels = ("bad", "medium", "good")
    ordered_indices = [indices[label] for label in labels]
    transmittance = torch.as_tensor(states.transmittance[ordered_indices], dtype=torch.float64)
    epsilon = torch.as_tensor(states.excess_noise_snu[ordered_indices], dtype=torch.float64)

    fixture_config = copy.deepcopy(config)
    fixture_config["numerical_validation"]["fixture_initialization_seed"] = fixture_seed
    complete = representative_ensembles(fixture_config, transmittance, epsilon)
    complete.pop("near_coincident_pseudoinverse_stress", None)
    v_max = float(config["cvqkd"]["v_max_snu"])
    n_peak = float(config["cvqkd"]["n_peak_photons"])
    for phase_step in design["near_coincident_phase_steps_rad"]:
        name = f"near_coincident_phase_step_{float(phase_step):g}"
        complete[name] = stress_ensemble(
            float(phase_step), batch_size=len(labels), v_max=v_max, n_peak=n_peak
        )
    ensembles, aliases = unique_ensemble_roster(complete)

    fixture_rows: list[dict[str, Any]] = []
    for name, ensemble in ensembles.items():
        fixture_rows.append({
            "name": name,
            "configuration_class": fixture_class(name),
            "ensemble_sha256": ensemble_sha256(ensemble),
            "state_count": int(ensemble.probabilities.shape[0]),
            "symbol_count": int(ensemble.probabilities.shape[1]),
            "declared_va_snu": [float(value) for value in ensemble.declared_va],
            "minimum_probability": float(ensemble.probabilities.min()),
            "maximum_symbol_photons": float(ensemble.amplitudes.abs().square().max()),
            "conditioning_risk_descriptor": (
                "analytic_near_coincident_phase_spacing"
                if name.startswith("near_coincident_") else "predefined_configuration_class"
            ),
        })
    fixture_names = {row["name"] for row in fixture_rows}
    oracle_subset = list(design["oracle_subset"])
    missing_oracle = sorted(set(oracle_subset) - fixture_names)
    if missing_oracle:
        raise ValueError(f"Oracle subset references missing fixtures: {missing_oracle}")

    representative_rows = [
        {
            "label": label,
            "realization_index": int(index),
            "transmittance": float(states.transmittance[index]),
            "epsilon_snu": float(states.excess_noise_snu[index]),
        }
        for label, index in zip(labels, ordered_indices)
    ]
    selection_design = {
        "config": design,
        "selection_inputs_are_outcome_independent": True,
        "candidate_threshold_values_read_or_evaluated": False,
        "final_test_data_read": False,
        "representative_state_algorithm": "componentwise quantile targets with interdecile scaling",
        "fixture_generation": "fixed algebraic families and deterministic fresh-seed parameterizations",
        "oracle_subset_selection": "named configuration classes fixed in roster config before evaluation",
    }
    channel_payload = {
        "base_seed": channel_seed,
        "transmittance_seed": int(states.transmittance_seed),
        "excess_noise_seed": int(states.excess_noise_seed),
        "sample_count": int(states.sample_count),
        "realization_sha256": states.realization_sha256,
        "joint_distribution": states.metadata["joint_distribution"],
        "statistical_dependence": states.metadata["statistical_dependence"],
        "transmittance_variance": float(states.metadata["empirical_transmittance_variance"]),
        "epsilon_variance_snu2": float(states.metadata["empirical_epsilon_variance_snu2"]),
    }
    roster_payload = {
        "selection_design": selection_design,
        "channel_realization": channel_payload,
        "representative_states": representative_rows,
        "fixtures": fixture_rows,
        "aliases": aliases,
        "oracle_subset": oracle_subset,
    }
    artifact: dict[str, Any] = {
        "schema_version": "independent-confirmation-roster-v1",
        "status": "FROZEN_OUTCOME_UNINSPECTED",
        "OUTCOME_INSPECTION_STATUS": "NOT_INSPECTED",
        "lifecycle_guards": {
            "publication_training_performed": False,
            "final_test_accessed": False,
            "held_out_evaluation_performed": False,
            "optimized_mb_grid_performed": False,
            "baseline_selection_performed": False,
            "candidate_threshold_evaluated_on_roster": False,
            "threshold_approved": False,
        },
        **roster_payload,
        "roster_payload_sha256": canonical_sha256(roster_payload),
        "provenance": {
            "repository_commit": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            "producer_sha256": sha256(Path(__file__).resolve()),
            "config_sha256": sha256(roster_config_path),
            "default_config_sha256": sha256(default_config_path),
            "environment_manifest_sha256": sha256(environment_manifest_path),
            "final_model_spec_sha256": sha256(ROOT / "docs" / "FINAL_MODEL_SPEC.md"),
            "schema_sha256": sha256(schema_path),
            "output_path": str(output_path.relative_to(ROOT)),
        },
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return artifact


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--default-config", type=Path, default=ROOT / "configs" / "default.yaml")
    parser.add_argument("--roster-config", type=Path, default=ROOT / "configs" / "independent_confirmation_roster.yaml")
    parser.add_argument("--environment-manifest", type=Path, default=ROOT / "results" / "current_environment_manifest.json")
    parser.add_argument("--schema", type=Path, default=ROOT / "schemas" / "independent_confirmation_roster.schema.json")
    parser.add_argument("--output", type=Path, default=ROOT / "results" / "independent_confirmation_roster.json")
    args = parser.parse_args()
    artifact = run(args.default_config, args.roster_config, args.environment_manifest, args.schema, args.output)
    print(json.dumps({
        "status": artifact["status"],
        "OUTCOME_INSPECTION_STATUS": artifact["OUTCOME_INSPECTION_STATUS"],
        "roster_payload_sha256": artifact["roster_payload_sha256"],
        "fixture_count": len(artifact["fixtures"]),
        "oracle_subset_count": len(artifact["oracle_subset"]),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
