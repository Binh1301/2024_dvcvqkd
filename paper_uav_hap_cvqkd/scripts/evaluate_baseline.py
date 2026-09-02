"""Manifest-gated held-out evaluation for the four selected fixed baselines."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch

from _common import holevo_numerical_kwargs, require_holevo_pseudoinverse_approval
from _train import _channel, _state_payload
from src.modulation.joint_ps_gs import JointTransmitter
from src.modulation.qam256 import c4_orbit_masses
from src.optimization.trainer import evaluate_transmitter
from src.optimization.constraints import heldout_budget_comparison_status
from src.utils.random import derive_seed, torch_generator
from src.validation.publication_manifest import (
    file_sha256,
    load_publication_manifest,
    verify_bound_artifacts,
)
from src.validation.physical_domain import approved_peak_photon_limit


BASELINE_IMPLEMENTATION = {
    "uniform": "uniform", "binomial": "binomial",
    "fixed_mb": "mb", "optimized_mb": "mb",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selection-manifest", type=Path, required=True)
    parser.add_argument("--scheme-id", choices=tuple(BASELINE_IMPLEMENTATION), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest_path = args.selection_manifest.resolve()
    manifest = load_publication_manifest(manifest_path)
    config = verify_bound_artifacts(manifest_path, manifest)
    require_holevo_pseudoinverse_approval(config)
    baseline_path = Path(manifest["artifact_paths"]["baseline_selection"])
    if not baseline_path.is_absolute():
        baseline_path = (manifest_path.parent / baseline_path).resolve()
    selection_artifact = json.loads(baseline_path.read_text(encoding="utf-8"))
    selected = selection_artifact["selections"][args.scheme_id]["selected"]
    va = float(selected["modulation_variance_snu"])
    nu = selected["mb_nu"]
    cvqkd = config["cvqkd"]
    n_peak = approved_peak_photon_limit(config)
    if not float(cvqkd["v_min_snu"]) <= va <= min(
        float(cvqkd["v_max_snu"]), float(cvqkd["v_a_budget_snu"])
    ):
        raise ValueError("Frozen baseline selection violates the common energy domain.")
    if args.scheme_id == "fixed_mb" and float(nu) != float(cvqkd["mb_nu"]):
        raise ValueError("Fixed-MB selection differs from preregistered reference nu.")
    transmitter = JointTransmitter(
        BASELINE_IMPLEMENTATION[args.scheme_id], fixed_va=va,
        v_min=float(cvqkd["v_min_snu"]), v_max=float(cvqkd["v_max_snu"]),
        nu_mb=None if nu is None else float(nu),
        n_peak_photons=n_peak,
    )
    frozen = manifest["test_evaluation"]
    channel_seed = derive_seed(frozen["channel_seed"], "held_out_test_channel")
    awgn_seed = derive_seed(frozen["awgn_seed"], "held_out_test_awgn")
    states = _channel(config, int(frozen["fading_samples"]), channel_seed)
    t = torch.as_tensor(states.transmittance, dtype=torch.float64)
    epsilon = torch.as_tensor(states.excess_noise_snu, dtype=torch.float64)
    with torch.no_grad():
        evaluation = evaluate_transmitter(
            transmitter, t, epsilon,
            beta_reconciliation=float(cvqkd["beta_reconciliation"]),
            noise_samples_per_symbol=int(frozen["awgn_samples_per_symbol"]),
            generator=torch_generator(awgn_seed), require_supported_symmetry=True,
            **holevo_numerical_kwargs(config),
        )
    budget_status = heldout_budget_comparison_status(
        float(evaluation.ensemble.declared_va.mean()), float(cvqkd["v_a_budget_snu"])
    )
    payload = {
        "status": "manifest-gated held-out baseline evaluation; not yet a claim",
        "scheme": args.scheme_id, "selected_va_snu": va, "selected_mb_nu": nu,
        "selection_manifest_sha256": file_sha256(manifest_path),
        "baseline_selection_sha256": file_sha256(baseline_path),
        "n_peak_photons": n_peak,
        "peak_photon_constraint_satisfied": True,
        "publication_eligible": bool(budget_status["comparison_valid"]),
        "heldout_budget_validity": budget_status,
        "test_state_realization_sha256": states.realization_sha256,
        "mean_raw_skr": float(evaluation.key_rate.fading_average_raw),
        "per_state": _state_payload(evaluation, t, epsilon),
        "policy": {
            "orbit_masses": c4_orbit_masses(evaluation.ensemble.probabilities).tolist(),
            "probabilities": evaluation.ensemble.probabilities.tolist(),
        },
        "constraints": evaluation.constraints,
        "holevo_diagnostics": evaluation.holevo.diagnostics,
    }
    args.output.resolve().parent.mkdir(parents=True, exist_ok=True)
    args.output.resolve().write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
