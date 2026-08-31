"""Serialize the exact float64 endpoint parameters for rigorous certification.

This producer runs only in the locked PyTorch environment.  The resulting
hexadecimal float payload is consumed by the isolated python-flint environment,
which therefore does not import or modify the production training stack.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

import numpy as np
import torch

from _common import ROOT, load_yaml
from src.modulation.joint_ps_gs import JointTransmitter
from src.modulation.probabilistic_shaping import channel_features


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def float_hex(value: float) -> str:
    return float(value).hex()


def tensor_payload(tensor: torch.Tensor) -> dict[str, Any]:
    flat = tensor.detach().cpu().reshape(-1).tolist()
    return {"shape": list(tensor.shape), "float64_hex": [float_hex(value) for value in flat]}


def parameter_payload(model: JointTransmitter) -> dict[str, Any]:
    return {name: tensor_payload(value) for name, value in model.named_parameters()}


def endpoint_model(start: JointTransmitter, family: str, seed: int,
                   scales: dict[str, float]) -> JointTransmitter:
    end = copy.deepcopy(start)
    generator = torch.Generator().manual_seed(seed)
    selected = ("ps", "gs", "va") if family == "mixed" else (family,)
    with torch.no_grad():
        for name, parameter in end.named_parameters():
            owner = "ps" if name.startswith("ps_network") else "gs" if name.startswith("gs_model") else "va"
            if owner in selected:
                parameter.add_(float(scales[owner]) * torch.randn(
                    parameter.shape, dtype=parameter.dtype, generator=generator
                ))
    return end


def gram(ensemble) -> np.ndarray:
    probability = ensemble.probabilities[0].detach().cpu().numpy()
    amplitude = ensemble.amplitudes[0].detach().cpu().numpy()
    root = np.sqrt(probability)
    return root[:, None] * root[None, :] * np.exp(
        -0.5 * (np.abs(amplitude)[:, None] ** 2 + np.abs(amplitude)[None, :] ** 2)
        + amplitude.conj()[:, None] * amplitude[None, :]
    )


def run(config_path: Path, default_path: Path, roster_path: Path,
        environment_path: Path, output_path: Path) -> dict[str, Any]:
    settings = load_yaml(config_path)
    default = load_yaml(default_path)
    roster = json.loads(roster_path.read_text(encoding="utf-8"))
    if roster["status"] != "FROZEN_OUTCOME_UNINSPECTED":
        raise ValueError("Independent confirmation roster is not frozen.")
    if settings["threshold_approval_permitted"] or settings["final_test_access_permitted"]:
        raise ValueError("Fixture freezing cannot approve thresholds or access final test.")

    legacy = load_yaml(ROOT / "configs" / "whole_segment_support_enclosure.yaml")
    segment_seed = int(legacy["segment_seed"])
    scales = {key: float(value) for key, value in legacy["parameter_family_scales"].items()}
    torch.manual_seed(segment_seed)
    start = JointTransmitter(
        "full",
        v_min=float(default["cvqkd"]["v_min_snu"]),
        v_max=float(default["cvqkd"]["v_max_snu"]),
        n_peak_photons=float(default["cvqkd"]["n_peak_photons"]),
    )
    endpoints = {
        family: endpoint_model(start, family, segment_seed + index + 1, scales)
        for index, family in enumerate(("ps", "gs", "va", "mixed"))
    }
    states = []
    for row in roster["representative_states"]:
        transmittance = float(row["transmittance"])
        epsilon = float(row["epsilon_snu"])
        features = channel_features(
            torch.tensor([transmittance], dtype=torch.float64),
            torch.tensor([epsilon], dtype=torch.float64),
        )[0]
        states.append({
            "label": row["label"],
            "transmittance_float64_hex": float_hex(transmittance),
            "epsilon_snu_float64_hex": float_hex(epsilon),
            "channel_features_float64_hex": [float_hex(value) for value in features.tolist()],
        })

    segment_rows = []
    for family, end in endpoints.items():
        diagnostics = {}
        for state in states:
            t = float.fromhex(state["transmittance_float64_hex"])
            epsilon = float.fromhex(state["epsilon_snu_float64_hex"])
            start_gram = gram(start(
                torch.tensor([t], dtype=torch.float64),
                torch.tensor([epsilon], dtype=torch.float64),
            ))
            end_gram = gram(end(
                torch.tensor([t], dtype=torch.float64),
                torch.tensor([epsilon], dtype=torch.float64),
            ))
            diagnostics[state["label"]] = {
                "observed_endpoint_frobenius_change_float64": float_hex(
                    float(np.linalg.norm(end_gram - start_gram, ord="fro"))
                )
            }
        segment_rows.append({
            "family": family,
            "endpoint_seed": segment_seed + ("ps", "gs", "va", "mixed").index(family) + 1,
            "end_parameters": parameter_payload(end),
            "endpoint_diagnostics": diagnostics,
        })

    artifact = {
        "schema_version": "rigorous-segment-fixture-bundle-v1",
        "status": "FROZEN_FLOAT64_PARAMETER_PATH_INPUTS",
        "path_definition": "theta(t)=theta_start+t*(theta_end-theta_start), t in [0,1]",
        "float_encoding": "exact Python float.hex representation of IEEE-754 binary64 values",
        "candidate_threshold_float64_hex": settings["candidate_threshold_float64_hex"],
        "segment_seed": segment_seed,
        "parameter_family_scales": scales,
        "v_min_float64_hex": float_hex(float(default["cvqkd"]["v_min_snu"])),
        "v_max_float64_hex": float_hex(float(default["cvqkd"]["v_max_snu"])),
        "states": states,
        "start_parameters": parameter_payload(start),
        "segments": segment_rows,
        "lifecycle_guards": {
            "threshold_approved": False,
            "publication_training_performed": False,
            "final_test_accessed": False,
            "optimized_mb_grid_performed": False,
            "baseline_selection_performed": False,
        },
        "provenance": {
            "repository_commit": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            "producer_sha256": sha256(Path(__file__).resolve()),
            "config_sha256": sha256(config_path),
            "default_config_sha256": sha256(default_path),
            "roster_sha256": sha256(roster_path),
            "environment_manifest_sha256": sha256(environment_path),
            "final_model_spec_sha256": sha256(ROOT / "docs" / "FINAL_MODEL_SPEC.md"),
        },
    }
    output_path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return artifact


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "rigorous_whole_segment_support.yaml")
    parser.add_argument("--default", type=Path, default=ROOT / "configs" / "default.yaml")
    parser.add_argument("--roster", type=Path, default=ROOT / "results" / "independent_confirmation_roster.json")
    parser.add_argument("--environment", type=Path, default=ROOT / "results" / "current_environment_manifest.json")
    parser.add_argument("--output", type=Path, default=ROOT / "results" / "rigorous_segment_fixture_bundle.json")
    args = parser.parse_args()
    artifact = run(args.config, args.default, args.roster, args.environment, args.output)
    print(json.dumps({"status": artifact["status"], "segments": len(artifact["segments"])}, sort_keys=True))


if __name__ == "__main__":
    main()
