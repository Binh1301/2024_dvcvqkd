"""Profile the exact 256-state MI estimator without reading held-out data."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import platform
import time

import torch

from _common import ROOT, load_yaml
from _numerical_validation import validation_representative_states
from src.cvqkd.mutual_information import discrete_mutual_information, standard_complex_noise
from src.modulation.joint_ps_gs import reference_ensemble
from src.utils.random import torch_generator


def _synchronize() -> None:
    if torch.cuda.is_available():
        torch.cuda.synchronize()


def _elapsed(callable_):
    _synchronize()
    started = time.perf_counter()
    value = callable_()
    _synchronize()
    return value, time.perf_counter() - started


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "default.yaml")
    parser.add_argument("--samples", type=int, default=256)
    parser.add_argument("--output", type=Path, default=ROOT / "results" / "mi_runtime_profile.json")
    args = parser.parse_args()
    if args.samples <= 0:
        raise ValueError("--samples must be positive.")
    config = load_yaml(args.config.resolve())
    _, labels, transmittance, epsilon = validation_representative_states(config)
    batch_size = transmittance.numel()
    symbol_count = 256
    timings: dict[str, float] = {}

    ensemble, timings["constellation_construction"] = _elapsed(
        lambda: reference_ensemble(
            "uniform", batch_size=batch_size, modulation_variance=0.1,
            v_min=float(config["cvqkd"]["v_min_snu"]),
            v_max=float(config["cvqkd"]["v_max_snu"]),
            n_peak_photons=float(config["cvqkd"]["n_peak_photons"]),
        )
    )
    generator = torch_generator(202607, torch.device("cpu"))
    noise, timings["gaussian_noise_generation"] = _elapsed(
        lambda: standard_complex_noise(
            (batch_size, symbol_count, args.samples),
            generator=generator, device=torch.device("cpu"),
        )
    )

    def prepare():
        t = transmittance.to(device=ensemble.probabilities.device, dtype=torch.float64)
        e = epsilon.to(device=ensemble.probabilities.device, dtype=torch.float64)
        sigma2 = 1.0 + t * e / 2.0
        means = torch.sqrt(t).unsqueeze(-1) * ensemble.amplitudes
        logp = torch.log(ensemble.probabilities)
        return t, e, sigma2, means, logp

    (_, _, sigma2, means, logp), timings["host_device_and_dtype_preparation"] = _elapsed(prepare)
    received = (
        means.unsqueeze(-1)
        + torch.sqrt(sigma2)[:, None, None] * noise
    )
    candidate_chunk = 64
    candidate = means[:, :candidate_chunk]
    distance_reference, timings["distance_matrix_reference_broadcast"] = _elapsed(
        lambda: (received[:, :, :, None] - candidate[:, None, None, :]).abs().square()
    )

    def optimized_distance():
        observations = received.reshape(batch_size, -1)
        observations_xy = torch.stack((observations.real, observations.imag), dim=-1)
        candidates_xy = torch.stack((candidate.real, candidate.imag), dim=-1)
        dot = observations_xy @ candidates_xy.transpose(-2, -1)
        value = (
            observations.abs().square().unsqueeze(-1)
            + candidate.abs().square().unsqueeze(-2) - 2.0 * dot
        )
        return torch.clamp_min(value, 0.0).reshape_as(distance_reference)

    distance_optimized, timings["distance_matrix_optimized_gemm"] = _elapsed(optimized_distance)
    logits, timings["mixture_likelihood_logits"] = _elapsed(
        lambda: logp[:, None, None, :candidate_chunk]
        - distance_optimized / sigma2[:, None, None, None]
    )
    _, timings["logsumexp"] = _elapsed(lambda: torch.logsumexp(logits, dim=-1))

    reference, timings["complete_reference_estimator"] = _elapsed(
        lambda: discrete_mutual_information(
            ensemble, transmittance, epsilon,
            noise_samples_per_symbol=args.samples,
            standard_noise_samples=noise,
            noise_sample_chunk_size=64,
            implementation="reference",
        )
    )
    optimized, timings["complete_optimized_estimator"] = _elapsed(
        lambda: discrete_mutual_information(
            ensemble, transmittance, epsilon,
            noise_samples_per_symbol=args.samples,
            standard_noise_samples=noise,
            noise_sample_chunk_size=64,
            implementation="optimized",
        )
    )
    absolute_difference = (reference - optimized).abs()
    payload = {
        "schema_version": "mi-runtime-profile-v1",
        "status": "validation-only runtime profile; not convergence certification",
        "test_set_used": False,
        "estimator": "exact discrete 256-state continuous-output Monte Carlo mixture",
        "precision": "torch.float64 / torch.complex128",
        "profile_fixture": "uniform_low_va_0.1_on_validation_bad_medium_good",
        "state_labels": labels,
        "noise_samples_per_symbol": args.samples,
        "candidate_chunk_size": candidate_chunk,
        "noise_sample_chunk_size": 64,
        "tensor_shapes": {
            "probabilities": list(ensemble.probabilities.shape),
            "amplitudes": list(ensemble.amplitudes.shape),
            "standard_complex_noise": list(noise.shape),
            "received": list(received.shape),
            "distance_chunk": list(distance_reference.shape),
            "full_logical_distance_tensor": [batch_size, symbol_count, args.samples, symbol_count],
        },
        "logical_pairwise_distances": batch_size * symbol_count * args.samples * symbol_count,
        "timings_seconds": timings,
        "dominant_complexity": "O(B * M_source * N_MC * M_mixture), M_source=M_mixture=256",
        "optimized_over_reference_speedup": timings["complete_reference_estimator"] / timings["complete_optimized_estimator"],
        "numerical_equivalence": {
            "maximum_absolute_difference_bits": float(absolute_difference.max()),
            "strict_atol_bits": 1e-12,
            "strict_rtol": 1e-12,
            "passes": bool(torch.allclose(reference, optimized, atol=1e-12, rtol=1e-12)),
            "maximum_distance_chunk_difference": float((distance_reference - distance_optimized).abs().max()),
        },
        "repeated_work_audit": {
            "reused_within_replication": ["explicit maximum-length CRN tensor", "prefix segment arithmetic means"],
            "recomputed_by_fixture": ["channel-scaled constellation means", "mixture pairwise distances", "log mixture likelihood"],
            "cannot_be_reused_across_replications": ["independent preregistered CRN tensor"],
            "state_independent_cached_inputs": ["ensemble probabilities", "ensemble amplitudes", "candidate log probabilities"],
        },
        "environment": {
            "python": platform.python_version(),
            "torch": torch.__version__,
            "cuda_available": torch.cuda.is_available(),
            "torch_threads": torch.get_num_threads(),
            "platform": platform.platform(),
        },
    }
    args.output.resolve().parent.mkdir(parents=True, exist_ok=True)
    args.output.resolve().write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload["numerical_equivalence"], indent=2))
    print(f"Wrote {args.output.resolve()}")
    return 0 if payload["numerical_equivalence"]["passes"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
