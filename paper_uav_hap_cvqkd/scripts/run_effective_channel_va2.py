"""Preliminary effective-channel SKR comparison at V_A=2 SNU."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import time
from typing import Any

import numpy as np
import torch

from _common import ROOT, holevo_numerical_kwargs, load_yaml
from _train import _channel, _phase_provenance
from src.cvqkd.gram_moments import (
    DIAGNOSTIC_EIGENVALUE_THRESHOLDS,
    c4_gram_fast_preflight,
    c4_gram_source_moments,
)
from src.cvqkd.holevo import _holevo_from_source_moments
from src.cvqkd.mutual_information import discrete_mutual_information, standard_complex_noise
from src.cvqkd.secret_key_rate import fading_secret_key_rate
from src.modulation.joint_ps_gs import Ensemble, reference_ensemble
from src.utils.random import array_sha256, torch_generator
from scripts.calculate_channel_pdf_and_moments import analyze_product, derive_physical_inputs


VA = 2.0
MB_NU = 0.1
MI_SEEDS = (202607, 202608, 202609, 202610, 202611)
MI_SAMPLES_PER_SYMBOL = 2048
JOINT_SAMPLE_COUNT = 10_000
JOINT_SAMPLE_SEED = 42
SCHEMES = ("uniform", "binomial", "mb")


def _sha256(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def _json_value(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        return str(value)
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().tolist()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_value(item) for item in value]
    return value


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(_json_value(payload), indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def phase_augmented_eta_xi(
    mean_eta: float,
    mean_epsilon_base: float,
    c_phi: float,
    modulation_variance: float = VA,
) -> float:
    """Return E[eta * (epsilon_base + c_phi V_A)] under independence."""

    return float(mean_eta) * (
        float(mean_epsilon_base) + float(c_phi) * float(modulation_variance)
    )


def effective_channel_parameters(
    mean_eta: float,
    mean_sqrt_eta: float,
    mean_eta_xi: float,
    modulation_variance: float = VA,
) -> dict[str, float]:
    """Construct the covariance-matched deterministic effective channel."""

    mean_eta = float(mean_eta)
    mean_sqrt_eta = float(mean_sqrt_eta)
    mean_eta_xi = float(mean_eta_xi)
    modulation_variance = float(modulation_variance)
    if not all(math.isfinite(value) for value in (
        mean_eta, mean_sqrt_eta, mean_eta_xi, modulation_variance
    )):
        raise ValueError("Effective-channel inputs must be finite.")
    if mean_eta < 0.0 or mean_sqrt_eta <= 0.0 or mean_eta_xi < 0.0:
        raise ValueError("Effective-channel moments have invalid signs.")
    if modulation_variance <= 0.0:
        raise ValueError("modulation_variance must be positive.")
    t_eff = mean_sqrt_eta**2
    epsilon_eff = (mean_eta * modulation_variance + mean_eta_xi) / t_eff - modulation_variance
    if epsilon_eff < 0.0 or not math.isfinite(epsilon_eff):
        raise ValueError("The effective input-referred excess noise is invalid.")
    sigma_c2 = 1.0 + t_eff * epsilon_eff / 2.0
    return {
        "T_eff": t_eff,
        "epsilon_eff": epsilon_eff,
        "sigma_c2": sigma_c2,
        "snr": (t_eff * modulation_variance / 2.0) / sigma_c2,
        "fading_induced_noise": (mean_eta / t_eff - 1.0) * modulation_variance,
        "effective_physical_noise": mean_eta_xi / t_eff,
    }


def _ensemble(config: dict[str, Any], scheme: str) -> Ensemble:
    return reference_ensemble(
        scheme,
        batch_size=1,
        modulation_variance=VA,
        nu_mb=MB_NU if scheme == "mb" else None,
        v_min=float(config["cvqkd"]["v_min_snu"]),
        v_max=float(config["cvqkd"]["v_max_snu"]),
        n_peak_photons=float(config["cvqkd"]["n_peak_photons"]),
    )


def _array_hash(tensor: torch.Tensor) -> str:
    return array_sha256(tensor.detach().cpu().numpy())


def _source_record(scheme: str, ensemble: Ensemble, gate: dict[str, Any]) -> dict[str, Any]:
    diagnostics = {
        "scheme": scheme,
        "VA": VA,
        "pmf_sha256": _array_hash(ensemble.probabilities),
        "amplitude_sha256": _array_hash(ensemble.amplitudes),
        "computed_VA": float(ensemble.computed_va()[0]),
        "normalization_error": abs(float(ensemble.computed_va()[0]) - VA),
        "gate": gate,
        "rank": None,
        "C": None,
        "w": None,
        "precision_history": [],
        "route": None,
        "runtime_seconds": None,
    }
    return diagnostics


def _resolve_source_moments(
    config: dict[str, Any],
    scheme: str,
    ensemble: Ensemble,
    gate: dict[str, Any],
) -> dict[str, Any]:
    record = _source_record(scheme, ensemble, gate)
    started = time.perf_counter()
    moments = c4_gram_source_moments(
        ensemble,
        density_eigenvalue_tolerance=float(
            config["cvqkd"]["holevo_numerics"][
                "density_eigenvalue_pseudoinverse_tolerance"
            ]
        ),
        physicality_tolerance=float(
            config["cvqkd"]["holevo_numerics"]["physicality_tolerance"]
        ),
        fallback_timeout_seconds=None,
    )
    elapsed = time.perf_counter() - started
    source_diagnostics = moments.diagnostics[0]
    fallback_rows = source_diagnostics.get("fallback_rows", [])
    record.update({
        "rank": source_diagnostics.get("numerical_retained_rank", 256),
        "C": float(moments.coherent_correlation[0]),
        "w": float(moments.w[0]),
        "precision_history": fallback_rows,
        "route": source_diagnostics.get("route"),
        "runtime_seconds": elapsed,
        "diagnostics": source_diagnostics,
    })
    if record["rank"] != 256:
        raise RuntimeError(f"{scheme} source rank is not 256.")
    return record


def _evaluate_scheme(
    config: dict[str, Any],
    scheme: str,
    ensemble: Ensemble,
    source: dict[str, Any],
    t_eff: float,
    epsilon_eff: float,
    numerical: dict[str, float],
) -> dict[str, Any]:
    transmittance = torch.tensor([t_eff], dtype=torch.float64)
    epsilon = torch.tensor([epsilon_eff], dtype=torch.float64)
    c = torch.tensor([source["C"]], dtype=torch.float64)
    w = torch.tensor([source["w"]], dtype=torch.float64)

    mi_values: list[float] = []
    for seed in MI_SEEDS:
        noise = standard_complex_noise(
            (1, 256, MI_SAMPLES_PER_SYMBOL),
            generator=torch_generator(seed),
            device=transmittance.device,
        )
        mi = discrete_mutual_information(
            ensemble,
            transmittance,
            epsilon,
            noise_samples_per_symbol=MI_SAMPLES_PER_SYMBOL,
            standard_noise_samples=noise,
        )
        mi_values.append(float(mi[0]))

    mi_mean = float(np.mean(mi_values))
    mi_stderr = float(np.std(mi_values, ddof=1) / math.sqrt(len(mi_values)))
    holevo = _holevo_from_source_moments(
        ensemble,
        transmittance,
        epsilon,
        coherent_correlation=c,
        w_raw=w,
        tau=None,
        tau_trace=ensemble.probabilities.sum(dim=-1),
        require_supported_symmetry=True,
        symmetry_tolerance=numerical["symmetry_tolerance"],
        physicality_tolerance=numerical["physicality_tolerance"],
        diagnostics={
            "backend": "effective_channel_va2",
            "source_moment_route": source["route"],
            "phase_noise_already_in_epsilon_eff": True,
        },
    )
    chi = float(holevo.chi_be[0])
    beta = float(config["cvqkd"]["beta_reconciliation"])
    raw_k = beta * mi_mean - chi
    return {
        "scheme": scheme,
        "VA": VA,
        "nu_MB": MB_NU if scheme == "mb" else None,
        "PMF_normalization": float(ensemble.probabilities.sum()),
        "physical_energy": float(ensemble.computed_va()[0]),
        "rank": int(source["rank"]),
        "C": source["C"],
        "w": source["w"],
        "T_eff": t_eff,
        "epsilon_eff": epsilon_eff,
        "beta_rec": beta,
        "I_AB": mi_mean,
        "I_AB_stderr": mi_stderr,
        "I_AB_replications": mi_values,
        "chi_BE_ub": chi,
        "raw_K": raw_k,
        "Z_L": float(holevo.diagnostics["Z_L"][0]),
        "Z_U": float(holevo.diagnostics["Z_U"][0]),
        "Z_star": float(holevo.z[0]),
        "maximizing_location": holevo.diagnostics["maximizing_location"][0],
        "source_moment_route": source["route"],
    }


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "scheme", "VA", "T_eff", "epsilon_eff", "beta_rec",
        "I_AB", "I_AB_stderr", "chi_BE_ub", "raw_K",
        "Z_L", "Z_U", "Z_star", "maximizing_location",
    ]
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows({field: row[field] for field in fields} for row in rows)


def _plot(path: Path, rows: list[dict[str, Any]]) -> None:
    import matplotlib.pyplot as plt

    labels = ["Uniform", "Binomial", "Fixed MB"]
    values = [next(row["raw_K"] for row in rows if row["scheme"] == key)
              for key in SCHEMES]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar(labels, values, color=("#4C78A8", "#F58518", "#54A24B"))
    ax.axhline(0.0, color="black", linewidth=0.8)
    ax.set_title("Preliminary Effective-Channel SKR at VA = 2 SNU")
    ax.set_ylabel("Raw SKR (bits/use)")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "default.yaml")
    parser.add_argument(
        "--output-dir", type=Path,
        default=ROOT / "results" / "effective_channel_va2",
    )
    parser.add_argument(
        "--joint-sample-count", type=int, default=JOINT_SAMPLE_COUNT
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config_path = args.config.resolve()
    config = load_yaml(config_path)
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()

    physical = derive_physical_inputs()
    analysis = analyze_product(physical["v_sc"], physical)
    phase = _phase_provenance(config)
    moments = analysis["moments"]
    mean_eta = float(moments["mean_eta"])
    mean_sqrt_eta = float(moments["mean_sqrt_eta"])
    mean_epsilon_base = (
        float(physical["epsilon_min_snu"]) + float(physical["epsilon_max_snu"])
    ) / 2.0
    mean_eta_xi_factorized = phase_augmented_eta_xi(
        mean_eta, mean_epsilon_base, phase["c_phi"], VA
    )
    effective = effective_channel_parameters(
        mean_eta, mean_sqrt_eta, mean_eta_xi_factorized, VA
    )

    states = _channel(config, args.joint_sample_count, JOINT_SAMPLE_SEED)
    eta_sample = np.asarray(states.transmittance, dtype=np.float64)
    epsilon_sample = np.asarray(states.epsilon_base_snu, dtype=np.float64)
    xi_sample = epsilon_sample + VA * float(phase["c_phi"])
    direct_eta_xi = float(np.mean(eta_sample * xi_sample))
    direct_eta_xi_stderr = float(
        np.std(eta_sample * xi_sample, ddof=1) / math.sqrt(eta_sample.size)
    )
    crosscheck_error = abs(direct_eta_xi - mean_eta_xi_factorized)
    if crosscheck_error > max(5.0 * direct_eta_xi_stderr, 1.0e-7 * abs(mean_eta_xi_factorized)):
        raise RuntimeError(
            "Direct and factorized <eta*xi_eta> disagree beyond the declared diagnostic uncertainty."
        )

    channel_payload = {
        "label": "Preliminary Effective-Channel SKR at VA = 2 SNU",
        "phase_provenance": phase,
        "analytical_moments": {
            "mean_eta": mean_eta,
            "mean_sqrt_eta": mean_sqrt_eta,
            "mean_eta_xi_eta_factorized": mean_eta_xi_factorized,
            "mean_epsilon_base": mean_epsilon_base,
        },
        "direct_joint_sample": {
            "sample_count": int(args.joint_sample_count),
            "seed": JOINT_SAMPLE_SEED,
            "mean_eta": float(np.mean(eta_sample)),
            "mean_sqrt_eta": float(np.mean(np.sqrt(eta_sample))),
            "mean_eta_xi_eta": direct_eta_xi,
            "mean_eta_xi_eta_standard_error": direct_eta_xi_stderr,
        },
        "crosscheck": {
            "absolute_difference": crosscheck_error,
            "accepted": True,
        },
    }
    _write_json(output_dir / "channel_moments.json", channel_payload)
    _write_json(output_dir / "effective_channel.json", {
        "label": "Preliminary Effective-Channel SKR at VA = 2 SNU",
        "VA": VA,
        "mean_eta": mean_eta,
        "mean_sqrt_eta": mean_sqrt_eta,
        "mean_eta_xi_eta": mean_eta_xi_factorized,
        **effective,
        "phase_noise_already_in_epsilon_eff": True,
    })

    ensembles = {scheme: _ensemble(config, scheme) for scheme in SCHEMES}
    source_records: dict[str, dict[str, Any]] = {}
    for scheme, ensemble in ensembles.items():
        source_records[scheme] = _source_record(
            scheme, ensemble, c4_gram_fast_preflight(ensemble)[0]
        )
    prior_sources: dict[str, Any] = {}
    source_path = output_dir / "source_moments_va2.json"
    if source_path.is_file():
        try:
            prior_sources = json.loads(source_path.read_text(encoding="utf-8")).get(
                "sources", {}
            )
        except (OSError, json.JSONDecodeError):
            prior_sources = {}

    for scheme, ensemble in ensembles.items():
        gate = c4_gram_fast_preflight(ensemble)[0]
        record = source_records[scheme]
        prior = prior_sources.get(scheme)
        if (
            isinstance(prior, dict)
            and prior.get("rank") == 256
            and prior.get("C") is not None
            and prior.get("w") is not None
            and prior.get("pmf_sha256") == record["pmf_sha256"]
            and prior.get("amplitude_sha256") == record["amplitude_sha256"]
        ):
            source_records[scheme] = {
                key: value
                for key, value in prior.items()
                if key not in {"status", "error", "blocker"}
            }
            continue
        _write_json(output_dir / "source_moments_va2.json", {
            "VA": VA,
            "sources": {**source_records, scheme: record},
        })
        source_records[scheme] = _resolve_source_moments(
            config, scheme, ensemble, gate
        )
        _write_json(output_dir / "source_moments_va2.json", {
            "VA": VA,
            "sources": source_records,
        })

    numerical = holevo_numerical_kwargs(config)
    rows = [
        _evaluate_scheme(
            config, scheme, ensembles[scheme], source_records[scheme],
            effective["T_eff"], effective["epsilon_eff"], numerical,
        )
        for scheme in SCHEMES
    ]
    payload = {
        "label": "Preliminary Effective-Channel SKR at VA = 2 SNU",
        "config_sha256": _sha256(config_path),
        "final_model_spec_sha256": _sha256(ROOT / "docs" / "FINAL_MODEL_SPEC.md"),
        "source_pdf_sha256": _sha256(Path(r"C:\Users\admin\Downloads\2026__Binh_s_work__Copy___Copy_ (5).pdf")),
        "VA": VA,
        "T_eff": effective["T_eff"],
        "epsilon_eff": effective["epsilon_eff"],
        "beta_rec": float(config["cvqkd"]["beta_reconciliation"]),
        "phase_noise_already_in_epsilon_eff": True,
        "source_moments": source_records,
        "results": rows,
        "runtime_seconds": time.perf_counter() - started,
    }
    _write_json(output_dir / "effective_channel_skr_va2.json", payload)
    _write_csv(output_dir / "effective_channel_skr_va2.csv", rows)
    _plot(output_dir / "effective_channel_skr_va2.png", rows)

    print("Scheme       VA    T_eff        eps_eff       I_AB       chi_BE_ub   K_raw")
    for row in rows:
        print(
            f"{row['scheme']:<11} {row['VA']:.1f} "
            f"{row['T_eff']:.9e} {row['epsilon_eff']:.9f} "
            f"{row['I_AB']:.9e} {row['chi_BE_ub']:.9e} {row['raw_K']:.9e}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
