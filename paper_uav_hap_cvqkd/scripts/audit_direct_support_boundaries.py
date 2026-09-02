"""Reproduce the prospectively defined direct-coordinate support sweep."""

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
    ensemble_sha256, representative_ensembles, unique_ensemble_roster,
    validation_representative_states,
)
from audit_support_threshold_protocol import _sector_eigenvalues
from src.modulation.joint_ps_gs import Ensemble, enforce_peak_photon_constraint
from src.modulation.normalization import physical_amplitudes
from src.modulation.qam256 import (
    c4_orbit_indices, c4_orbit_masses, expand_c4_orbit_masses,
    expand_c4_orbit_values,
)


THRESHOLD = 1e-13
MULTIPLIERS = (1, 3, 10, 30, 100, 300, 1000)
LEARNING_RATES = {"ps": 3e-4, "gs": 1e-4, "va": 1e-4}
PS_COORDINATES = (0, 17, 42)
GS_COORDINATES = ((0, "real"), (17, "imag"), (42, "real"))
SIGNS = (-1, 1)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _single_state(ensemble: Ensemble, state_index: int) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    probability = ensemble.probabilities[state_index]
    va = ensemble.declared_va[state_index]
    raw = ensemble.raw_constellation
    if raw.ndim == 2:
        raw = raw[state_index]
    return probability, raw, va


def _build_perturbed(
    ensemble: Ensemble, state_index: int, family: str, coordinate: Any, delta: float,
    *, v_min: float, v_max: float, n_peak: float,
) -> Ensemble:
    probability, raw, va = _single_state(ensemble, state_index)
    if family == "ps":
        q = c4_orbit_masses(probability)
        eta = torch.log(q)
        eta[int(coordinate)] += delta
        probability = expand_c4_orbit_masses(torch.softmax(eta, dim=-1))
    elif family == "gs":
        prototypes = raw[c4_orbit_indices(device=raw.device)[:, 0]].clone()
        real_view = torch.view_as_real(prototypes)
        orbit, component = coordinate
        real_view[int(orbit), 0 if component == "real" else 1] += delta
        prototypes = torch.view_as_complex(real_view)
        gauge = torch.sqrt(torch.mean(prototypes.abs().square()))
        prototypes = prototypes / gauge
        raw = expand_c4_orbit_values(prototypes)
    elif family == "va":
        va = va * math.exp(delta)
        if not v_min <= float(va) <= v_max:
            raise ValueError("Direct log-VA proposal leaves the frozen VA box.")
    else:
        raise ValueError(f"Unknown family {family}.")
    amplitudes = physical_amplitudes(probability, raw, va)
    result = Ensemble(
        probability.unsqueeze(0), amplitudes, va.reshape(1), raw,
        exact_csi_oracle=True, c4_symmetric=True,
    )
    result.validate()
    enforce_peak_photon_constraint(result, n_peak)
    return result


def _support(ensemble: Ensemble) -> dict[str, Any]:
    sectors = _sector_eigenvalues(ensemble)[0]
    masks = [[value > THRESHOLD for value in values] for values in sectors]
    flat = [value for values in sectors for value in values]
    nearest = min(flat, key=lambda value: abs(value - THRESHOLD))
    return {
        "mask": masks,
        "rank": sum(sum(mask) for mask in masks),
        "sector_ranks": [sum(mask) for mask in masks],
        "nearest_eigenvalue": nearest,
        "distance_to_threshold": abs(nearest - THRESHOLD),
    }


def run(config: dict[str, Any], *, config_path: Path, support_artifact_path: Path,
        output_path: Path) -> dict[str, Any]:
    support_artifact = json.loads(support_artifact_path.read_text(encoding="utf-8"))
    disagreement_names = [row["fixture"] for row in support_artifact["support_disagreements"]]
    if len(disagreement_names) != 12:
        raise ValueError("Expected exactly 12 hash-bound support disagreements.")
    validation, labels, transmittance, epsilon = validation_representative_states(config)
    complete = representative_ensembles(config, transmittance, epsilon)
    ensembles, _ = unique_ensemble_roster(complete)
    fixture_names = disagreement_names + ["near_coincident_pseudoinverse_stress"]
    cvqkd = config["cvqkd"]
    v_min, v_max = float(cvqkd["v_min_snu"]), float(cvqkd["v_max_snu"])
    n_peak = float(cvqkd["n_peak_photons"])
    probes = []
    fixture_aggregates = []
    started = time.perf_counter()
    for fixture in fixture_names:
        ensemble = ensembles[fixture]
        crossing = {"ps": 0, "gs": 0, "va": 0}
        totals = {"ps": 0, "gs": 0, "va": 0}
        invalid = {"ps": 0, "gs": 0, "va": 0}
        for state_index, state_label in enumerate(labels):
            probability, raw, va = _single_state(ensemble, state_index)
            base = Ensemble(
                probability.unsqueeze(0), ensemble.amplitudes[state_index].unsqueeze(0),
                va.reshape(1), raw, exact_csi_oracle=True, c4_symmetric=True,
            )
            base_support = _support(base)
            for family, coordinates in (
                ("ps", PS_COORDINATES), ("gs", GS_COORDINATES), ("va", (None,)),
            ):
                for coordinate in coordinates:
                    for multiplier in MULTIPLIERS:
                        for sign in SIGNS:
                            delta = sign * LEARNING_RATES[family] * multiplier
                            totals[family] += 1
                            try:
                                proposed = _build_perturbed(
                                    ensemble, state_index, family, coordinate, delta,
                                    v_min=v_min, v_max=v_max, n_peak=n_peak,
                                )
                                after = _support(proposed)
                                changed = after["mask"] != base_support["mask"]
                                crossing[family] += int(changed)
                                status = "support_transition" if changed else "support_stable"
                                error = None
                            except (ValueError, FloatingPointError, RuntimeError) as caught:
                                after = None
                                changed = False
                                invalid[family] += 1
                                status = "invalid_fail_closed"
                                error = f"{type(caught).__name__}: {caught}"
                            probes.append({
                                "fixture": fixture,
                                "ensemble_sha256": ensemble_sha256(ensemble),
                                "state": state_label,
                                "state_index": state_index,
                                "family": family,
                                "coordinate": coordinate,
                                "multiplier": multiplier,
                                "sign": sign,
                                "delta": delta,
                                "status": status,
                                "support_changed": changed,
                                "rank_before": base_support["rank"],
                                "rank_after": after["rank"] if after else None,
                                "sector_ranks_before": base_support["sector_ranks"],
                                "sector_ranks_after": after["sector_ranks"] if after else None,
                                "nearest_eigenvalue_before": base_support["nearest_eigenvalue"],
                                "nearest_eigenvalue_after": after["nearest_eigenvalue"] if after else None,
                                "error": error,
                            })
        fixture_aggregates.append({
            "fixture": fixture,
            "is_support_disagreement_fixture": fixture in disagreement_names,
            "probe_count_by_family": totals,
            "support_transition_count_by_family": crossing,
            "invalid_count_by_family": invalid,
        })
    disagreement_probes = [row for row in probes if row["fixture"] in disagreement_names]
    disagreement_counts = {
        family: sum(
            row["support_changed"] for row in disagreement_probes if row["family"] == family
        ) for family in LEARNING_RATES
    }
    disagreement_totals = {
        family: sum(row["family"] == family for row in disagreement_probes)
        for family in LEARNING_RATES
    }
    disagreement_invalid = {
        family: sum(
            row["status"] == "invalid_fail_closed"
            for row in disagreement_probes if row["family"] == family
        ) for family in LEARNING_RATES
    }
    disagreement_admissible = {
        family: disagreement_totals[family] - disagreement_invalid[family]
        for family in LEARNING_RATES
    }
    dependencies = {
        "config": config_path,
        "support_threshold_artifact": support_artifact_path,
        "final_model_spec": ROOT / "docs" / "FINAL_MODEL_SPEC.md",
        "joint_transmitter": ROOT / "src" / "modulation" / "joint_ps_gs.py",
        "normalization": ROOT / "src" / "modulation" / "normalization.py",
        "audit_script": Path(__file__).resolve(),
    }
    hashes = {
        name: {"path": str(path.relative_to(ROOT)), "sha256": _sha256(path)}
        for name, path in dependencies.items()
    }
    if hashes["final_model_spec"]["sha256"] != (
        "561fecc97cdf9967034ffd6865c1605804b624b98f47a091e47f17e520a2a7b1"
    ):
        raise ValueError("FINAL_MODEL_SPEC.md hash changed.")
    return {
        "schema_version": "direct-support-boundary-sweep-v1",
        "status": "PROPOSED_DIAGNOSTIC_ONLY_NOT_FROZEN",
        "preregistered_design": {
            "threshold": THRESHOLD,
            "support_disagreement_fixture_count": 12,
            "supplemental_stress_fixture": "near_coincident_pseudoinverse_stress",
            "state_labels": labels,
            "families": ["ps", "gs", "va"],
            "multipliers": list(MULTIPLIERS),
            "signs": list(SIGNS),
            "learning_rates": LEARNING_RATES,
            "ps_path": "eta=log(q); eta[j]+=delta; q'=softmax(eta), j in {0,17,42}",
            "gs_path": (
                "perturb prototype coordinates (0,real),(17,imag),(42,real), then enforce "
                "unweighted unit-RMS GS gauge before physical normalization"
            ),
            "va_path": "VA'=VA*exp(delta), fail closed outside frozen [Vmin,Vmax]",
            "support_rule": "record a crossing if any C4 sector support mask changes",
            "interpretation": "controlled direct-coordinate diagnostic, not optimization",
        },
        "lifecycle_guards": {
            "publication_training_performed": False,
            "test_set_accessed": False,
            "optimized_mb_grid_performed": False,
            "baseline_selection_performed": False,
            "active_config_changed": False,
            "physical_or_security_functional_changed": False,
        },
        "validation_state_realization_sha256": validation.realization_sha256,
        "fixture_aggregates": fixture_aggregates,
        "disagreement_fixture_summary": {
            "total_probes_by_family": disagreement_totals,
            "inadmissible_probes_by_family": disagreement_invalid,
            "admissible_probes_by_family": disagreement_admissible,
            "support_transition_count_by_family": disagreement_counts,
            "support_transition_fraction_of_admissible_by_family": {
                family: disagreement_counts[family] / disagreement_admissible[family]
                for family in LEARNING_RATES
            },
        },
        "probe_rows": probes,
        "runtime_seconds": time.perf_counter() - started,
        "provenance": {"input_and_source_hashes": hashes, "output_path": str(output_path.relative_to(ROOT))},
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "default.yaml")
    parser.add_argument(
        "--support-artifact", type=Path,
        default=ROOT / "results" / "support_threshold_protocol_audit.json",
    )
    parser.add_argument(
        "--output", type=Path,
        default=ROOT / "results" / "direct_support_boundary_sweep.json",
    )
    args = parser.parse_args()
    result = run(
        load_yaml(args.config), config_path=args.config.resolve(),
        support_artifact_path=args.support_artifact.resolve(), output_path=args.output.resolve(),
    )
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "summary": result["disagreement_fixture_summary"],
        "runtime_seconds": result["runtime_seconds"],
        "output": str(args.output),
    }, indent=2))


if __name__ == "__main__":
    main()
