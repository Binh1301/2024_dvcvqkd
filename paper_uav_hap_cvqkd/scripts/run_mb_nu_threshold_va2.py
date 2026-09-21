"""Find fixed-MB nu values that beat the validated Binomial sweep."""

from __future__ import annotations

import csv
from decimal import Decimal
import json
import math
from pathlib import Path
import tempfile
import time

import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(ROOT))

from src.cvqkd.gram_moments import c4_gram_source_moments
import src.cvqkd.holevo as holevo_module
from src.cvqkd.holevo import _holevo_from_source_moments
from src.cvqkd.mutual_information import discrete_mutual_information, standard_complex_noise
from src.modulation.joint_ps_gs import reference_ensemble
from src.modulation.qam256 import square_qam256
from src.utils.random import array_sha256, torch_generator
from scripts._common import load_yaml


VA = 2.0
BETA = 0.95
MI_SEEDS = (202607, 202608, 202609, 202610, 202611)
MI_SAMPLES_PER_SYMBOL = 2048
COARSE_NUS = (0.02, 0.05, 0.075, 0.10, 0.125, 0.15, 0.20)
SCHEMES = ("uniform", "binomial", "mb")
BINOMIAL_C = "1.41414750131106445213245972871615156498"
BINOMIAL_W = "1.13331366963443032864740272931418486e-4"
MB_01_C = "1.4141975446461088728099397679159500271185396830827"
MB_01_W = "3.5382188425273695384131484143796774042381888693943e-5"


def _forbidden(*_args, **_kwargs):
    raise RuntimeError("MB threshold search reached a forbidden full-Z/AP evaluation path.")


def _load_distance_rows() -> tuple[dict, list[dict]]:
    path = ROOT / "results" / "fixed_source_distance_va2_kruse" / "fixed_source_distance_va2.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("ap_worker_invoked") or payload.get("full_z_optimization_invoked"):
        raise RuntimeError("The channel input artifact is not a fixed-source primary result.")
    return payload, payload["rows"]


def _source_summary(nu: float, ensemble, c_text: str, w_text: str, *, checkpoint: Path | None, runtime: float, rows: list[dict]) -> dict:
    scale = (ensemble.amplitudes[0] / square_qam256()).real
    alpha0 = float(scale.mean())
    accepted = rows[-2:] if len(rows) >= 2 else []
    worst_kappa = None
    pair = None
    if accepted:
        pair = [int(row["digits"]) for row in accepted]
        worst_kappa = max(
            float(sector["log10_kappa"])
            for row in accepted
            for sector in row["sector_diagnostics"]
        )
    return {
        "nu_MB": nu,
        "alpha0": alpha0,
        "C": c_text,
        "w": w_text,
        "pmf_sha256": array_sha256(ensemble.probabilities.detach().cpu().numpy()),
        "amplitude_sha256": array_sha256(ensemble.amplitudes.detach().cpu().numpy()),
        "VA": float(ensemble.computed_va()[0]),
        "accepted_precision_pair": pair,
        "worst_log10_kappa": worst_kappa,
        "AP_runtime_seconds": runtime,
        "checkpoint": None if checkpoint is None else str(checkpoint),
        "fallback_rows": rows,
    }


def _source_for_nu(config: dict, nu: float) -> tuple[object, dict]:
    ensemble = reference_ensemble(
        "mb",
        batch_size=1,
        modulation_variance=VA,
        nu_mb=nu,
        v_min=float(config["cvqkd"]["v_min_snu"]),
        v_max=float(config["cvqkd"]["v_max_snu"]),
        n_peak_photons=float(config["cvqkd"]["n_peak_photons"]),
    )
    if math.isclose(nu, 0.1, rel_tol=0.0, abs_tol=1e-15):
        checkpoint = Path(tempfile.gettempdir()) / "cvqkd_fixed_mb_va2_c4_checkpoint.json"
        payload = json.loads(checkpoint.read_text(encoding="utf-8"))
        rows = payload["rows"]
        if [row["digits"] for row in rows[-2:]] != [384, 512]:
            raise RuntimeError("The validated nu=0.1 checkpoint does not contain the accepted 384/512 pair.")
        final = rows[-1]
        if Decimal(final["C"]) != Decimal(MB_01_C) or Decimal(final["w"]) != Decimal(MB_01_W):
            raise RuntimeError("The validated nu=0.1 checkpoint does not match the approved source reference.")
        return ensemble, _source_summary(nu, ensemble, MB_01_C, MB_01_W, checkpoint=checkpoint, runtime=sum(float(row["runtime_seconds"]) for row in rows), rows=rows)

    token = f"{nu:.6f}".replace(".", "p")
    checkpoint = Path(tempfile.gettempdir()) / f"cvqkd_mb_nu_{token}_va2_c4_checkpoint.json"
    started = time.perf_counter()
    moments = c4_gram_source_moments(
        ensemble,
        density_eigenvalue_tolerance=1e-13,
        fallback_timeout_seconds=None,
        max_precision_digits=2400,
        fallback_checkpoint_path=checkpoint,
        scheme_config_hash=f"mb-nu-{nu:.6f}-va2-c4",
    )
    elapsed = time.perf_counter() - started
    diagnostics = moments.diagnostics[0]
    rows = diagnostics.get("fallback_rows", [])
    if diagnostics.get("numerical_retained_rank") != 256 or len(rows) < 2:
        raise RuntimeError(f"nu={nu} did not produce full-support convergence rows.")
    final = rows[-1]
    return ensemble, _source_summary(
        nu,
        ensemble,
        final["C"],
        final["w"],
        checkpoint=checkpoint,
        runtime=elapsed,
        rows=rows,
    )


def _mi(ensemble, transmittance: float, epsilon: float, noises: dict[int, torch.Tensor]) -> tuple[float, float]:
    values = []
    t = torch.tensor([transmittance], dtype=torch.float64)
    epsilon = torch.tensor([epsilon], dtype=torch.float64)
    for seed in MI_SEEDS:
        values.append(float(discrete_mutual_information(
            ensemble,
            t,
            epsilon,
            noise_samples_per_symbol=MI_SAMPLES_PER_SYMBOL,
            standard_noise_samples=noises[seed],
        )[0]))
    mean = sum(values) / len(values)
    stderr = (sum((value - mean) ** 2 for value in values) / (len(values) - 1)) ** 0.5
    return mean, stderr / len(values) ** 0.5


def _evaluate_nu(nu: float, ensemble, source: dict, distance_rows: list[dict], noises: dict[int, torch.Tensor], binomial_rows: dict[float, dict]) -> list[dict]:
    c = torch.tensor([float(source["C"])], dtype=torch.float64)
    w = torch.tensor([float(source["w"])], dtype=torch.float64)
    output = []
    for channel_row in sorted(distance_rows, key=lambda row: (row["L_km"], row["scheme"])):
        if channel_row["scheme"] != "uniform":
            continue
        L_km = float(channel_row["L_km"])
        transmittance = float(channel_row["T"])
        epsilon_value = float(channel_row["epsilon"])
        t = torch.tensor([transmittance], dtype=torch.float64)
        epsilon = torch.tensor([epsilon_value], dtype=torch.float64)
        mi, mi_stderr = _mi(ensemble, transmittance, epsilon_value, noises)
        holevo = _holevo_from_source_moments(
            ensemble,
            t,
            epsilon,
            coherent_correlation=c,
            w_raw=w,
            tau=None,
            tau_trace=ensemble.probabilities.sum(dim=-1),
            require_supported_symmetry=True,
            symmetry_tolerance=1e-8,
            physicality_tolerance=1e-10,
            maximize_full_interval=False,
            diagnostics={
                "backend": "mb_nu_threshold_va2",
                "source_moment_recomputed_per_distance": False,
                "phase_noise_already_in_epsilon": True,
            },
        )
        chi = float(holevo.chi_be[0])
        k_raw = BETA * mi - chi
        k_bin = float(binomial_rows[L_km]["K_raw"])
        output.append({
            "nu_MB": nu,
            "L_km": L_km,
            "I_AB_MB": mi,
            "I_AB_MB_stderr": mi_stderr,
            "Z_star_MB": float(holevo.z[0]),
            "chi_MB": chi,
            "K_MB": k_raw,
            "K_bin": k_bin,
            "DeltaK": k_raw - k_bin,
            "holevo_mode": holevo.diagnostics["mode"],
            "physicality_pass": min(float(holevo.covariance.lambda1[0]), float(holevo.covariance.lambda2[0]), float(holevo.covariance.lambda3[0])) >= 1.0 - 1e-10,
        })
    if len(output) != 11:
        raise RuntimeError(f"nu={nu} produced {len(output)} distance rows, expected 11.")
    return output


def _performance(nu: float, rows: list[dict]) -> dict:
    deltas = [row["DeltaK"] for row in rows]
    return {
        "nu_MB": nu,
        "min_DeltaK": min(deltas),
        "max_DeltaK": max(deltas),
        "mean_DeltaK": sum(deltas) / len(deltas),
        "count_MB_better": sum(delta > 0.0 for delta in deltas),
        "any_distance_pass": any(delta > 0.0 for delta in deltas),
        "all_distance_pass": all(delta > 0.0 for delta in deltas),
    }


def _write_plot(path: Path, rows: list[dict]) -> None:
    import matplotlib.pyplot as plt

    styles = {
        19.0: ("0.30", "--", "s"),
        24.0: ("0.55", "-.", "^") ,
    }
    fig, ax = plt.subplots(figsize=(6.2, 4.0))
    for L_km in (19.0, 24.0):
        selected = [row for row in rows if row["L_km"] == L_km]
        color, linestyle, marker = styles[L_km]
        ax.plot(
            [row["nu_MB"] for row in selected],
            [row["DeltaK"] for row in selected],
            color=color,
            linestyle=linestyle,
            marker=marker,
            markersize=4,
            linewidth=1.3,
            markerfacecolor="white",
            label=f"L = {L_km:g} km",
        )
    ax.axhline(0.0, color="0.35", linestyle=":", linewidth=0.8)
    ax.set_xlabel(r"MB shaping parameter, $\nu_{\rm MB}$")
    ax.set_ylabel(r"$\Delta K = K_{\rm MB}-K_{\rm Binomial}$ (bits/use)")
    ax.grid(True, alpha=0.25)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)


def main() -> int:
    started = time.perf_counter()
    config = load_yaml(ROOT / "configs" / "default.yaml")
    channel_payload, distance_rows = _load_distance_rows()
    if len(distance_rows) != 33 or sorted({row["scheme"] for row in distance_rows}) != ["binomial", "mb", "uniform"]:
        raise RuntimeError("The Kruse distance artifact does not contain the expected 33 rows.")
    binomial_rows = {
        float(row["L_km"]): row
        for row in distance_rows
        if row["scheme"] == "binomial"
    }
    if len(binomial_rows) != 11:
        raise RuntimeError("The Kruse Binomial comparator does not contain 11 distances.")

    source_rows = []
    performance_rows = []
    all_performance_rows = []
    representative_rows = []
    evaluation_rows = []
    noises = {
        seed: standard_noise_samples
        for seed, standard_noise_samples in (
            (seed, standard_complex_noise(
                (1, 256, MI_SAMPLES_PER_SYMBOL),
                generator=torch_generator(seed),
                device=torch.device("cpu"),
            ))
            for seed in MI_SEEDS
        )
    }
    output_dir = ROOT / "results" / "mb_nu_threshold_va2"
    output_dir.mkdir(parents=True, exist_ok=True)
    # The existing validated nu=0.1 source checkpoint is reused; all other
    # nu values get distinct AP checkpoints and cache keys.
    for nu in COARSE_NUS:
        ensemble, source = _source_for_nu(config, nu)
        holevo_module._maximize_bounded_scalar = _forbidden
        holevo_module.c4_gram_source_moments = _forbidden
        source_rows.append({key: value for key, value in source.items() if key != "fallback_rows"})
        evaluation = _evaluate_nu(nu, ensemble, source, distance_rows, noises, binomial_rows)
        evaluation_rows.extend(evaluation)
        performance_rows.append(_performance(nu, evaluation))
        representative_rows.extend(row for row in evaluation if row["L_km"] in (19.0, 24.0))

    # Install the final guard only after all source rows are complete, so any
    # accidental optimization/source path during channel evaluation fails.
    for row in evaluation_rows:
        if row["holevo_mode"] != "zstar" or not row["physicality_pass"]:
            raise RuntimeError("A non-primary or nonphysical MB evaluation was produced.")
    for row in performance_rows:
        all_performance_rows.append(row)

    fields = list(evaluation_rows[0])
    with (output_dir / "mb_nu_performance_rows.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(evaluation_rows)
    _write_plot(output_dir / "DeltaK_vs_nu_MB.png", evaluation_rows)
    payload = {
        "artifact": "MB_NU_THRESHOLD_VA2_COARSE",
        "nu_values": list(COARSE_NUS),
        "VA": VA,
        "beta_rec": BETA,
        "distance_artifact": "results/fixed_source_distance_va2_kruse/fixed_source_distance_va2.json",
        "source_moment_recomputed_per_distance": False,
        "full_z_optimization_invoked": False,
        "source_moments": source_rows,
        "performance": performance_rows,
        "representative_rows": representative_rows,
        "evaluation_rows": evaluation_rows,
        "runtime_seconds": time.perf_counter() - started,
        "AP_runtime_seconds": sum(
            float(row["AP_runtime_seconds"])
            for row in source_rows
            if row["checkpoint"] is not None and row["nu_MB"] != 0.1
        ),
    }
    (output_dir / "mb_nu_threshold_va2.json").write_text(
        json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "runtime_seconds": time.perf_counter() - started,
        "AP_runtime_seconds": payload["AP_runtime_seconds"],
        "nu_values": list(COARSE_NUS),
        "performance": performance_rows,
        "output_dir": str(output_dir),
    }, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
