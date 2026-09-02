"""Boundedly profile the exact validation-baseline scoring path.

This diagnostic never ranks a candidate. If the Fock gate is blocked it uses
the nonselectable reference cutoff solely to measure resource requirements.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

import torch

from _common import ROOT, holevo_numerical_kwargs, load_yaml
from _train import _channel
from src.cvqkd.holevo import shared_fixed_ensemble_holevo_chi
from src.cvqkd.mutual_information import discrete_mutual_information, standard_complex_noise
from src.modulation.joint_ps_gs import reference_ensemble
from src.utils.random import derive_seed, torch_generator


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "default.yaml")
    parser.add_argument("--mi-evidence", type=Path,
                        default=ROOT / "results" / "mi_convergence.json")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "results" / "baseline_runtime_profile.json")
    args = parser.parse_args()
    config = load_yaml(args.config.resolve())
    mi_count = int(json.loads(args.mi_evidence.read_text())["minimum_common_sample_count"])
    training = config["training"]
    states = _channel(
        config, int(training["validation_fading_samples"]),
        derive_seed(int(training["seeds"]["validation_channel"]), "validation_channel"),
    )
    batch_size = int(config["baseline_search"]["state_batch_size"])
    t = torch.as_tensor(states.transmittance[:batch_size], dtype=torch.float64)
    epsilon = torch.as_tensor(states.excess_noise_snu[:batch_size], dtype=torch.float64)
    ensemble = reference_ensemble(
        "uniform", batch_size=batch_size, modulation_variance=0.1,
        v_min=float(config["cvqkd"]["v_min_snu"]),
        v_max=float(config["cvqkd"]["v_max_snu"]),
        n_peak_photons=float(config["cvqkd"]["n_peak_photons"]),
    )
    started = time.perf_counter()
    noise = standard_complex_noise(
        (batch_size, 256, mi_count),
        generator=torch_generator(derive_seed(
            int(training["seeds"]["validation_awgn"]),
            "baseline_common_awgn_batch", 0,
        )), device=t.device,
    )
    noise_seconds = time.perf_counter() - started
    started = time.perf_counter()
    discrete_mutual_information(
        ensemble, t, epsilon, noise_samples_per_symbol=mi_count,
        standard_noise_samples=noise,
        noise_sample_chunk_size=int(
            config["numerical_validation"]["mi"]["noise_sample_chunk_size"]
        ),
        implementation="product",
    )
    mi_seconds = time.perf_counter() - started
    started = time.perf_counter()
    shared_fixed_ensemble_holevo_chi(
        ensemble, t, epsilon, backend="c4_gram", fock_cutoff=None,
        **holevo_numerical_kwargs(config)
    )
    holevo_seconds = time.perf_counter() - started
    total = noise_seconds + mi_seconds + holevo_seconds
    public_candidate_count = 3 * len(config["baseline_search"]["va_grid_snu"]) + (
        len(config["baseline_search"]["optimized_mb_nu_grid"])
        * len(config["baseline_search"]["va_grid_snu"])
    )
    unique_candidate_count = public_candidate_count - 2 * len(
        config["baseline_search"]["va_grid_snu"]
    )
    batches_per_candidate = (
        int(training["validation_fading_samples"]) + batch_size - 1
    ) // batch_size
    projected_seconds = (
        unique_candidate_count * holevo_seconds
        + unique_candidate_count * batches_per_candidate
        * (noise_seconds + mi_seconds)
    )
    payload = {
        "schema_version": "baseline-runtime-profile-v2",
        "status": "validation-only runtime profile; no candidate selected",
        "test_set_used": False,
        "publication_training_performed": False,
        "fixture": "uniform_va_0.1_first_validation_state_batch",
        "state_batch_size": batch_size, "mi_sample_count": mi_count,
        "holevo_backend": "c4_gram_candidate_diagnostic",
        "density_eigenvalue_threshold": float(config["cvqkd"]["holevo_numerics"][
            "density_eigenvalue_pseudoinverse_tolerance"
        ]),
        "mi_implementation": "exact_product_qam_float64_same_256_source_crn",
        "holevo_implementation": "complete_batch_c4_gram_no_fock_fallback",
        "timings_seconds": {"noise_generation": noise_seconds,
                            "mutual_information": mi_seconds,
                            "holevo": holevo_seconds, "total": total},
        "dominant_fraction_mi": mi_seconds / total,
        "public_candidate_count": public_candidate_count,
        "unique_candidate_score_count": unique_candidate_count,
        "exact_alias_score_count": public_candidate_count - unique_candidate_count,
        "validation_batches_per_unique_candidate": batches_per_candidate,
        "projected_full_search_seconds": projected_seconds,
        "projection_rule": (
            "unique_candidates*one shared Holevo evaluation + "
            "unique_candidates*batches*(noise+exact product MI); linear diagnostic"
        ),
        "logical_distance_evaluations": batch_size * 256 * mi_count * 256,
        "precision": "torch.float64 / torch.complex128",
        "limitation": (
            "Resource projection only. Expanded Fock convergence is blocked, "
            "so this profile cannot authorize baseline selection."
        ),
    }
    args.output.resolve().write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
