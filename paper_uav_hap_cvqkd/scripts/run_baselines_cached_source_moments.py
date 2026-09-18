"""Paired short diagnostic for Uniform, Binomial, and fixed-MB 256-QAM."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import subprocess
import time
from typing import Any, Callable

import numpy as np
import torch

from _common import ROOT, holevo_numerical_kwargs, load_yaml
from _train import _channel, _phase_provenance
from src.channel.phase_noise import total_excess_noise
from src.cvqkd.gram_moments import (
    DIAGNOSTIC_EIGENVALUE_THRESHOLDS,
    GramMomentResult,
    c4_gram_fast_preflight,
    c4_gram_source_moments,
)
from src.cvqkd.holevo import _holevo_from_source_moments
from src.cvqkd.mutual_information import discrete_mutual_information, standard_complex_noise
from src.cvqkd.protocol import validate_channel_state
from src.cvqkd.secret_key_rate import fading_secret_key_rate
from src.modulation.joint_ps_gs import Ensemble, reference_ensemble
from src.optimization.constraints import ensemble_state_diagnostics
from src.utils.random import array_sha256, torch_generator


SCHEMES = ("uniform", "binomial", "mb")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "default.yaml")
    parser.add_argument(
        "--output-dir", type=Path,
        default=ROOT / "results" / "fixed_benchmark_diagnostic",
    )
    parser.add_argument("--fading-samples", type=int, default=16)
    parser.add_argument("--awgn-samples", type=int, default=64)
    parser.add_argument("--channel-seed", type=int, default=202613)
    parser.add_argument("--awgn-seed", type=int, default=202615)
    parser.add_argument("--run-ap-witness", action="store_true")
    parser.add_argument(
        "--source-pdf", type=Path,
        default=Path(r"C:\Users\admin\Downloads\2026__Binh_s_work__Copy___Copy_ (5).pdf"),
    )
    return parser.parse_args()


def _sha256(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def _repeat_ensemble(source: Ensemble, batch_size: int) -> Ensemble:
    if source.probabilities.shape[0] != 1:
        raise ValueError("Cached fixed-baseline source must have batch_size=1.")
    return Ensemble(
        probabilities=source.probabilities.expand(batch_size, -1),
        amplitudes=source.amplitudes.expand(batch_size, -1),
        declared_va=source.declared_va.expand(batch_size),
        raw_constellation=source.raw_constellation,
        exact_csi_oracle=source.exact_csi_oracle,
        c4_symmetric=source.c4_symmetric,
    )


def evaluate_fixed_ensemble(
    source_ensemble: Ensemble,
    transmittance: torch.Tensor,
    epsilon_base: torch.Tensor,
    *,
    phase_coefficient: float,
    density_eigenvalue_tolerance: float,
    beta_reconciliation: float,
    awgn_samples: int,
    standard_noise_samples: torch.Tensor | None = None,
    awgn_generator: torch.Generator | None = None,
    source_moment_evaluator: Callable[..., GramMomentResult] = c4_gram_source_moments,
    symmetry_tolerance: float = 1e-8,
    density_trace_tolerance: float = 1e-10,
    physicality_tolerance: float = 1e-10,
) -> dict[str, Any]:
    """Evaluate one fixed source on active states; callers own outage reinsertion."""

    source_ensemble.validate()
    transmittance, epsilon_base = validate_channel_state(
        transmittance, epsilon_base, allow_zero_transmittance=False
    )
    batch = _repeat_ensemble(source_ensemble, transmittance.numel())
    epsilon_total = total_excess_noise(
        epsilon_base, batch.declared_va, phase_coefficient
    )

    source_start = time.perf_counter()
    moments = source_moment_evaluator(
        source_ensemble,
        density_eigenvalue_tolerance=density_eigenvalue_tolerance,
        physicality_tolerance=physicality_tolerance,
    )
    source_elapsed = time.perf_counter() - source_start
    if moments.coherent_correlation.shape != (1,) or moments.w.shape != (1,):
        raise ValueError("Source evaluator must return exactly one C and w value.")
    if standard_noise_samples is None and awgn_generator is None:
        raise ValueError("Provide common standard_noise_samples or an explicit generator.")

    mi = discrete_mutual_information(
        batch, transmittance, epsilon_total,
        noise_samples_per_symbol=awgn_samples,
        generator=awgn_generator,
        standard_noise_samples=standard_noise_samples,
    )
    holevo = _holevo_from_source_moments(
        batch, transmittance, epsilon_total,
        coherent_correlation=moments.coherent_correlation.expand_as(transmittance),
        w_raw=moments.w.expand_as(transmittance),
        tau=None,
        tau_trace=batch.probabilities.sum(dim=-1),
        require_supported_symmetry=True,
        symmetry_tolerance=symmetry_tolerance,
        physicality_tolerance=physicality_tolerance,
        diagnostics={
            "backend": "c4_gram_full_support_cached_source",
            "density_trace_tolerance": density_trace_tolerance,
            "source_moment_diagnostics": moments.diagnostics,
            "density_eigenvalue_threshold_role": "diagnostic_only",
        },
    )
    rate = fading_secret_key_rate(mi, holevo.chi_be, beta_reconciliation)
    diagnostics = ensemble_state_diagnostics(batch)
    return {
        "source_moments": {
            "C": float(moments.coherent_correlation.item()),
            "w": float(moments.w.item()),
            "route": moments.diagnostics[0].get("route"),
            "elapsed_seconds": source_elapsed,
            "diagnostics": moments.diagnostics[0],
        },
        "epsilon_total": epsilon_total,
        "i_ab": mi,
        "chi_be": holevo.chi_be,
        "raw_k": rate.instantaneous_raw,
        "holevo_diagnostics": holevo.diagnostics,
        "realized_va_error": float(
            (diagnostics["modulation_variance"] - batch.declared_va).abs().max()
        ),
        "pmf_normalization_error": float(
            (batch.probabilities.sum(dim=-1) - 1.0).abs().max()
        ),
    }


def _source_ensemble(config: dict[str, Any], scheme: str, va: float) -> Ensemble:
    cvqkd = config["cvqkd"]
    return reference_ensemble(
        scheme, batch_size=1, modulation_variance=va,
        nu_mb=float(cvqkd["mb_nu"]) if scheme == "mb" else None,
        v_min=float(cvqkd["v_min_snu"]), v_max=float(cvqkd["v_max_snu"]),
        n_peak_photons=float(cvqkd["n_peak_photons"]),
    )


def build_support_preflight(
    config: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[tuple[str, float], Ensemble]]:
    grid = [float(value) for value in config["baseline_search"]["va_grid_snu"]]
    ensembles: dict[tuple[str, float], Ensemble] = {}
    rows: list[dict[str, Any]] = []
    for va in grid:
        for scheme in SCHEMES:
            source = _source_ensemble(config, scheme, va)
            gate = c4_gram_fast_preflight(source)[0]
            ensembles[(scheme, va)] = source
            rows.append({"scheme": scheme, "target_VA": va, **gate})
    return rows, ensembles


def _provenance(config_path: Path, source_pdf: Path) -> dict[str, Any]:
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT,
        capture_output=True, text=True, check=False,
    ).stdout.strip()
    dirty = bool(subprocess.run(
        ["git", "status", "--porcelain"], cwd=ROOT,
        capture_output=True, text=True, check=False,
    ).stdout.strip())
    model = ROOT / "docs" / "FINAL_MODEL_SPEC.md"
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": commit or None,
        "git_dirty": dirty,
        "config": str(config_path.resolve()),
        "config_sha256": _sha256(config_path.resolve()),
        "final_model_spec_sha256": _sha256(model),
        "source_pdf": str(source_pdf),
        "source_pdf_sha256": _sha256(source_pdf),
        "producer_sha256": _sha256(Path(__file__).resolve()),
        "phase_source_sha256": _sha256(ROOT / "src" / "channel" / "phase_noise.py"),
        "qam_source_sha256": _sha256(ROOT / "src" / "modulation" / "qam256.py"),
        "gram_source_sha256": _sha256(ROOT / "src" / "cvqkd" / "gram_moments.py"),
        "ap_worker_sha256": _sha256(ROOT / "scripts" / "full_support_c4_worker.py"),
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")


def _plot(rows: list[dict[str, Any]], path: Path) -> None:
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8, 5))
    for scheme in SCHEMES:
        selected = [row for row in rows if row["scheme"] == scheme]
        ax.plot(
            [row["target_VA"] for row in selected],
            [row["mean_K_outage_inclusive"] for row in selected],
            marker="o", label="Fixed MB (nu=0.1)" if scheme == "mb" else scheme.title(),
        )
    ax.set_xlabel("Target modulation variance $V_A$ (SNU)")
    ax.set_ylabel("Outage-inclusive mean raw SKR (bits/use)")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def main() -> int:
    args = parse_args()
    config_path = args.config.resolve()
    config = load_yaml(config_path)
    cvqkd = config["cvqkd"]
    grid = [float(value) for value in config["baseline_search"]["va_grid_snu"]]
    if cvqkd.get("fixed_modulation_variance_snu") is not None:
        raise ValueError("This paired diagnostic requires the shared declared V_A grid.")
    if grid != [round(0.1 * index, 1) for index in range(1, 16)]:
        raise ValueError("Expected the existing shared V_A grid 0.1 through 1.5 SNU.")
    if float(cvqkd["mb_nu"]) != 0.1:
        raise ValueError("This task is fixed MB with nu=0.1 only.")

    started = time.perf_counter()
    phase = _phase_provenance(config)
    preflight, ensembles = build_support_preflight(config)
    failed = [row for row in preflight if not row["fast_path_passed"]]
    output = args.output_dir.resolve() / "paired_fixed_benchmark_results.json"
    prior_sha256 = _sha256(output)
    prior = json.loads(output.read_text(encoding="utf-8")) if output.is_file() else {}
    prior_provenance = prior.get("provenance", {})
    reusable_witness = (
        prior.get("ap_witness")
        if prior_provenance.get("config_sha256") == _sha256(config_path)
        and prior_provenance.get("source_pdf_sha256") == _sha256(args.source_pdf)
        else None
    )
    payload: dict[str, Any] = {
        "schema_version": "paired-fixed-benchmark-diagnostic-v1",
        "status": "SUPPORT_PREFLIGHT_PASS" if not failed else "READY_FOR_IMPLEMENTATION: NO",
        "classification": "EXPLORATORY_NON_PUBLICATION_DIAGNOSTIC",
        "blocker": None if not failed else "NUMERICAL_SUPPORT_AMBIGUITY",
        "provenance": _provenance(config_path, args.source_pdf),
        "run_config": {
            "schemes": list(SCHEMES), "va_grid_snu": grid, "mb_nu": 0.1,
            "fading_samples": args.fading_samples,
            "awgn_samples_per_symbol": args.awgn_samples,
            "channel_seed": args.channel_seed, "awgn_seed": args.awgn_seed,
            "diagnostic_eigenvalue_thresholds": list(DIAGNOSTIC_EIGENVALUE_THRESHOLDS),
            "pseudoinverse_threshold_approved": False,
            "source_support_definition": "strict_positive_full_mathematical_support_256",
        },
        "phase_provenance": phase,
        "support_preflight": preflight,
        "ap_witness": None,
        "ap_witness_reused_from_artifact_sha256": None,
        "results": [],
    }

    if failed:
        if args.run_ap_witness:
            witness = failed[0]
            key = (str(witness["scheme"]), float(witness["target_VA"]))
            witness_started = time.perf_counter()
            try:
                moments = c4_gram_source_moments(
                    ensembles[key],
                    density_eigenvalue_tolerance=float(
                        cvqkd["holevo_numerics"]["density_eigenvalue_pseudoinverse_tolerance"]
                    ),
                    physicality_tolerance=float(
                        cvqkd["holevo_numerics"]["physicality_tolerance"]
                    ),
                )
                payload["ap_witness"] = {
                    "scheme": key[0], "target_VA": key[1],
                    "status": "FULL_SUPPORT_CONVERGED",
                    "C": float(moments.coherent_correlation.item()),
                    "w": float(moments.w.item()),
                    "diagnostics": moments.diagnostics[0],
                    "runtime_seconds": time.perf_counter() - witness_started,
                }
            except Exception as error:
                payload["ap_witness"] = {
                    "scheme": key[0], "target_VA": key[1],
                    "status": "FAIL_CLOSED", "error": repr(error),
                    "runtime_seconds": time.perf_counter() - witness_started,
                }
        elif reusable_witness is not None:
            payload["ap_witness"] = reusable_witness
            payload["ap_witness_reused_from_artifact_sha256"] = prior_sha256
        payload["runtime_seconds"] = time.perf_counter() - started
        _write_json(output, payload)
        print(f"Blocked by {len(failed)}/45 complex128 source ensembles; wrote {output}")
        return 2

    channel = _channel(config, args.fading_samples, args.channel_seed)
    transmittance = torch.as_tensor(channel.transmittance, dtype=torch.float64)
    epsilon_base = torch.as_tensor(channel.epsilon_base_snu, dtype=torch.float64)
    active_mask = transmittance > 0.0
    active_t = transmittance[active_mask]
    active_epsilon = epsilon_base[active_mask]
    if not bool(torch.any(active_mask)):
        raise RuntimeError("Diagnostic channel realization contains no active states.")
    shared_noise = standard_complex_noise(
        (active_t.numel(), 256, args.awgn_samples),
        generator=torch_generator(args.awgn_seed), device=active_t.device,
    )
    numerical = holevo_numerical_kwargs(config)
    rows: list[dict[str, Any]] = []
    for va in grid:
        for scheme in SCHEMES:
            row_started = time.perf_counter()
            evaluation = evaluate_fixed_ensemble(
                ensembles[(scheme, va)], active_t, active_epsilon,
                phase_coefficient=float(phase["c_phi"]),
                density_eigenvalue_tolerance=numerical["density_eigenvalue_tolerance"],
                beta_reconciliation=float(cvqkd["beta_reconciliation"]),
                awgn_samples=args.awgn_samples,
                standard_noise_samples=shared_noise,
                symmetry_tolerance=numerical["symmetry_tolerance"],
                density_trace_tolerance=numerical["density_trace_tolerance"],
                physicality_tolerance=numerical["physicality_tolerance"],
            )
            full_k = torch.zeros_like(transmittance)
            full_k[active_mask] = evaluation["raw_k"]
            n_total = int(transmittance.numel())
            n_active = int(active_mask.sum())
            rows.append({
                "scheme": scheme,
                "nu_MB": 0.1 if scheme == "mb" else None,
                "target_VA": va,
                "N_total": n_total,
                "N_active": n_active,
                "outage_rate": 1.0 - n_active / n_total,
                "mean_T": float(transmittance.mean()),
                "mean_sqrt_T": float(torch.sqrt(transmittance).mean()),
                "mean_epsilon_total_active": float(evaluation["epsilon_total"].mean()),
                "mean_IAB_active": float(evaluation["i_ab"].mean()),
                "mean_Holevo_active": float(evaluation["chi_be"].mean()),
                "mean_K_active": float(evaluation["raw_k"].mean()),
                "mean_K_outage_inclusive": float(full_k.mean()),
                "std_error_K": float(full_k.std(unbiased=True) / math.sqrt(n_total)),
                "negative_K_fraction_active": float((evaluation["raw_k"] < 0.0).double().mean()),
                "security_failure_count": 0,
                "physicality_failure_count": 0,
                "pmf_normalization_error": evaluation["pmf_normalization_error"],
                "realized_VA_error": evaluation["realized_va_error"],
                "source_moments": evaluation["source_moments"],
                "holevo_diagnostics": evaluation["holevo_diagnostics"],
                "threshold_effect_deltas": {
                    "C": 0.0, "w": 0.0, "Z_L": 0.0, "Z_U": 0.0,
                    "chi_BE_ub": 0.0, "K": 0.0,
                    "reason": "production C4 thresholds are diagnostic metadata only",
                },
                "runtime_seconds": time.perf_counter() - row_started,
            })

    payload.update({
        "status": "CURRENTLY_VERIFIED_PASS",
        "blocker": None,
        "channel": {
            "metadata": channel.metadata,
            "realization_sha256": channel.realization_sha256,
            "transmittance_sha256": array_sha256(channel.transmittance),
            "epsilon_base_sha256": array_sha256(channel.epsilon_base_snu),
            "active_mask": active_mask.tolist(),
        },
        "common_random_numbers": {
            "standard_noise_sha256": array_sha256(shared_noise.numpy()),
            "same_tensor_reused_for_all_scheme_va_rows": True,
        },
        "results": rows,
        "runtime_seconds": time.perf_counter() - started,
    })
    _write_json(output, payload)
    _plot(rows, args.output_dir.resolve() / "skr_vs_va.png")
    print("scheme    VA    outage-inclusive raw SKR")
    for row in rows:
        print(f"{row['scheme']:<8} {row['target_VA']:>3.1f} {row['mean_K_outage_inclusive']:> .9e}")
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
