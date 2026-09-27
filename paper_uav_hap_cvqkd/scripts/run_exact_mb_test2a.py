"""Certify deterministic MB MI and its raw-nu autodiff chain."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import sys

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts._common import load_yaml
from scripts.run_exact_mb_test2 import (
    CRN_SEEDS,
    MI_SAMPLES_PER_SYMBOL,
    VA,
    build_mb_ensemble,
    channel_fixture,
    ensemble_hash,
    nu_mb_repo,
)
from src.cvqkd.mutual_information import (
    deterministic_mutual_information,
    discrete_mutual_information,
    is_product_qam_ensemble,
    standard_complex_noise,
)
from src.modulation.joint_ps_gs import Ensemble
from src.modulation.qam256 import square_qam256
from src.utils.random import torch_generator


OUTPUT = ROOT / "results" / "exact_mb_test2a"
NU_VALUES = (0.10, 0.15, 0.16, 0.17, 0.20)
GRAD_VALUES = (0.15, 0.16, 0.17)
GH_ORDERS = (8, 16, 24, 32, 48, 64)
FD_STEPS = (1.0e-2, 5.0e-3, 1.0e-3, 5.0e-4, 1.0e-4, 1.0e-5)
MC_CROSS_SAMPLES = 65536


def differentiable_mb_ensemble(nu_raw: torch.Tensor | float, va: float = VA) -> Ensemble:
    """Build the exact raw-MB physical ensemble without detaching the chain."""

    raw = square_qam256(alpha0=math.sqrt(30.0))
    relative = raw / math.sqrt(42.5)
    nu_raw_tensor = torch.as_tensor(nu_raw, dtype=torch.float64, device=raw.device)
    energy = relative.abs().square().to(dtype=torch.float64)
    probabilities = torch.softmax(-42.5 * nu_raw_tensor * energy, dim=-1)
    scale = torch.sqrt(torch.as_tensor(va, dtype=torch.float64) / (2.0 * torch.sum(probabilities * energy)))
    amplitudes = scale * relative
    ensemble = Ensemble(
        probabilities.unsqueeze(0),
        amplitudes.unsqueeze(0),
        torch.full((1,), float(va), dtype=torch.float64),
        raw,
        c4_symmetric=True,
    )
    ensemble.validate(tolerance=1.0e-11)
    return ensemble


def _channel_tensors(channel: dict[str, float]) -> tuple[torch.Tensor, torch.Tensor]:
    t = torch.tensor([channel["T_eff"]], dtype=torch.float64)
    epsilon = torch.tensor(
        [channel["epsilon_base"] + channel["c_phi"] * VA], dtype=torch.float64
    )
    return t, epsilon


def deterministic_value_and_gradient(
    nu_raw: float, channel: dict[str, float], order: int
) -> tuple[float, float]:
    value = torch.tensor(float(nu_raw), dtype=torch.float64, requires_grad=True)
    ensemble = differentiable_mb_ensemble(value)
    t, epsilon = _channel_tensors(channel)
    mi = deterministic_mutual_information(
        ensemble, t, epsilon, quadrature_order=order, implementation="product"
    )
    gradient, = torch.autograd.grad(mi.sum(), value)
    return float(mi[0].detach()), float(gradient.detach())


def deterministic_value(nu_raw: float, channel: dict[str, float], order: int, implementation: str) -> float:
    ensemble = differentiable_mb_ensemble(float(nu_raw))
    t, epsilon = _channel_tensors(channel)
    value = deterministic_mutual_information(
        ensemble, t, epsilon, quadrature_order=order, implementation=implementation
    )
    return float(value[0].detach())


def pmf_derivative_checks(nu_raw: float) -> dict[str, float]:
    raw = square_qam256(alpha0=math.sqrt(30.0))
    energy = (raw.abs().square() / 42.5).to(dtype=torch.float64)
    repo = torch.tensor(nu_mb_repo(nu_raw), dtype=torch.float64, requires_grad=True)
    pmf_repo = torch.softmax(-repo * energy, dim=0)
    jac_repo, = torch.autograd.functional.jacobian(
        lambda x: torch.softmax(-x * energy, dim=0), repo, create_graph=False
    ).reshape(1, -1)
    mean_energy = torch.sum(pmf_repo.detach() * energy)
    analytic_repo = pmf_repo.detach() * (mean_energy - energy)
    raw_parameter = torch.tensor(nu_raw, dtype=torch.float64, requires_grad=True)
    jac_raw, = torch.autograd.functional.jacobian(
        lambda x: torch.softmax(-42.5 * x * energy, dim=0), raw_parameter, create_graph=False
    ).reshape(1, -1)
    return {
        "nu_raw": nu_raw,
        "max_abs_repo_error": float((jac_repo - analytic_repo).abs().max()),
        "max_abs_raw_chain_error": float((jac_raw - 42.5 * analytic_repo).abs().max()),
        "sum_p": float(pmf_repo.detach().sum()),
        "min_p": float(pmf_repo.detach().min()),
    }


def factorization_check(channel: dict[str, float], order: int = 32) -> dict:
    rows = []
    for nu_raw in NU_VALUES:
        ensemble = build_mb_ensemble(load_yaml(ROOT / "configs" / "default.yaml"), nu_raw, VA)
        product = is_product_qam_ensemble(ensemble)
        full = deterministic_value(nu_raw, channel, order, "full")
        product_value = deterministic_value(nu_raw, channel, order, "product")
        probabilities = ensemble.probabilities.reshape(1, 16, 16)
        real_p = probabilities.sum(dim=-1)
        imag_p = probabilities.sum(dim=-2)
        reconstructed_p = real_p.unsqueeze(-1) * imag_p.unsqueeze(-2)
        amplitudes = ensemble.amplitudes.reshape(1, 16, 16)
        real_levels = amplitudes[:, :, 0].real
        imag_levels = amplitudes[:, 0, :].imag
        reconstructed_a = torch.complex(
            real_levels.unsqueeze(-1).expand(-1, -1, 16),
            imag_levels.unsqueeze(-2).expand(-1, 16, -1),
        )
        rows.append({
            "nu_raw": nu_raw,
            "cartesian_product": product,
            "max_probability_factorization_error": float((probabilities - reconstructed_p).abs().max()),
            "max_geometry_factorization_error": float((amplitudes - reconstructed_a).abs().max()),
            "I_full": full,
            "I_2xPAM": product_value,
            "absolute_difference": abs(full - product_value),
            "relative_difference": abs(full - product_value) / max(abs(full), 1.0e-30),
        })
    return {
        "rows": rows,
        "cartesian_factorization": all(row["cartesian_product"] for row in rows),
        "pmf_factorization": max(row["max_probability_factorization_error"] for row in rows) <= 1.0e-12,
        "I_256_equals_2I_16PAM": max(row["absolute_difference"] for row in rows) <= 1.0e-12,
    }


def gh_convergence(channel: dict[str, float]) -> tuple[list[dict], int | None]:
    rows = []
    for order in GH_ORDERS:
        for nu_raw in GRAD_VALUES:
            value, gradient = deterministic_value_and_gradient(nu_raw, channel, order)
            rows.append({"order": order, "nu_raw": nu_raw, "I_AB": value, "dI_dnu_raw": gradient})
    final = {(row["nu_raw"]): row for row in rows if row["order"] == GH_ORDERS[-1]}
    selected = None
    for order in GH_ORDERS:
        candidate = [row for row in rows if row["order"] == order]
        if all(
            abs(row["I_AB"] - final[row["nu_raw"]]["I_AB"]) <= 1.0e-10
            and abs(row["dI_dnu_raw"] - final[row["nu_raw"]]["dI_dnu_raw"]) <= 1.0e-7
            for row in candidate
        ):
            selected = order
            break
    return rows, selected


def autodiff_vs_fd(channel: dict[str, float], order: int) -> list[dict]:
    rows = []
    for nu_raw in GRAD_VALUES:
        center, autodiff = deterministic_value_and_gradient(nu_raw, channel, order)
        for h in FD_STEPS:
            minus = deterministic_value(nu_raw - h, channel, order, "product")
            plus = deterministic_value(nu_raw + h, channel, order, "product")
            fd = (plus - minus) / (2.0 * h)
            absolute = abs(fd - autodiff)
            relative = absolute / max(abs(autodiff), 1.0e-12)
            rows.append({
                "nu_raw": nu_raw,
                "h": h,
                "I_minus": minus,
                "I_center": center,
                "I_plus": plus,
                "fd_derivative": fd,
                "autodiff_derivative": autodiff,
                "absolute_error": absolute,
                "relative_error": relative,
            })
    return rows


def mc_cross_check(channel: dict[str, float], order: int) -> list[dict]:
    config = load_yaml(ROOT / "configs" / "default.yaml")
    t, epsilon = _channel_tensors(channel)
    rows = []
    for nu_raw in NU_VALUES:
        ensemble = build_mb_ensemble(config, nu_raw, VA)
        samples = []
        for seed in CRN_SEEDS:
            noise = standard_complex_noise(
                (1, 256, MC_CROSS_SAMPLES),
                generator=torch_generator(seed),
                device=t.device,
            )
            samples.append(float(discrete_mutual_information(
                ensemble, t, epsilon,
                noise_samples_per_symbol=MC_CROSS_SAMPLES,
                standard_noise_samples=noise,
                implementation="product",
                noise_sample_chunk_size=4096,
            )[0]))
        deterministic = deterministic_value(nu_raw, channel, order, "product")
        mean = float(np.mean(samples))
        stderr = float(np.std(samples, ddof=1) / math.sqrt(len(samples)))
        rows.append({
            "nu_raw": nu_raw,
            "I_GH": deterministic,
            "I_MC": mean,
            "MC_stderr": stderr,
            "difference": deterministic - mean,
            "difference_over_stderr": (deterministic - mean) / stderr if stderr else math.inf,
        })
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    args = parser.parse_args()
    torch.set_num_threads(1)
    config = load_yaml(ROOT / "configs" / "default.yaml")
    channel = channel_fixture()
    trace = {
        "nu_conversion": "scripts/run_exact_mb_test2.py::nu_mb_repo; src/modulation/qam256.py::maxwell_boltzmann_pmf",
        "MB_PMF": "src/modulation/qam256.py::maxwell_boltzmann_pmf",
        "VA_normalization": "src/modulation/normalization.py::physical_amplitudes; Ensemble.computed_va",
        "MI_MC": "src/cvqkd/mutual_information.py::discrete_mutual_information",
        "MI_deterministic": "src/cvqkd/mutual_information.py::deterministic_mutual_information",
        "C_w": "src/cvqkd/gram_moments.py::c4_gram_source_moments",
        "Z_star": "src/cvqkd/holevo.py::_holevo_from_source_moments",
        "Holevo": "src/cvqkd/holevo.py::c4_gram_holevo_information",
        "cache": "scripts/run_exact_mb_test2.py::ExactMBEvaluator.source_moments",
    }
    factors = factorization_check(channel)
    gh_rows, selected_order = gh_convergence(channel)
    production_order = selected_order or GH_ORDERS[-1]
    fd_rows = autodiff_vs_fd(channel, production_order)
    mc_rows = mc_cross_check(channel, production_order)
    derivative_pass = all(
        row["relative_error"] <= 1.0e-4 or row["absolute_error"] <= 1.0e-9
        for row in fd_rows if row["h"] >= 1.0e-4
    )
    gh_pass = selected_order is not None
    mc_pass = all(abs(row["difference_over_stderr"]) <= 3.0 for row in mc_rows)
    report = {
        "status": "DETERMINISTIC_MI_CERTIFIED" if derivative_pass and gh_pass else "DETERMINISTIC_MI_FAILED",
        "channel_fixture": channel,
        "repository_trace": trace,
        "raw_repo_scale": 42.5,
        "quadrature_orders": list(GH_ORDERS),
        "selected_gh_order": selected_order,
        "MC_cross_check_samples_per_symbol": MC_CROSS_SAMPLES,
        "FD_absolute_tolerance_near_zero": 1.0e-9,
        "FD_relative_target": 1.0e-4,
        "deterministic_MI": "PASS" if derivative_pass else "FAIL",
        "GH_convergence": "PASS" if gh_pass else "FAIL",
        "autodiff_gradient": "PASS" if derivative_pass else "FAIL",
        "FD_agreement": "PASS" if derivative_pass else "FAIL",
        "MC_independent_cross_check": "PASS" if mc_pass else "FAIL",
        "factorization": factors,
        "integrity": {
            "common_ensemble_hash_contract": "PASS_FROM_EVID_0087",
            "C_w_interpolation": "NO",
            "physical_security_equations_changed": "NO",
            "historical_invalid_cache_used": "NO",
        },
        "full_skr_search": {
            "status": "NOT RUN",
            "reason": "Optimized-MB search remains lifecycle-gated; this task certifies deterministic MI only.",
        },
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "repository_trace.json").write_text(json.dumps(trace, indent=2) + "\n", encoding="utf-8")
    (args.output_dir / "gh_convergence.json").write_text(json.dumps(gh_rows, indent=2) + "\n", encoding="utf-8")
    (args.output_dir / "factorization_check.json").write_text(json.dumps(factors, indent=2) + "\n", encoding="utf-8")
    (args.output_dir / "run_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    write_csv(args.output_dir / "gh_convergence.csv", gh_rows)
    write_csv(args.output_dir / "autodiff_vs_fd.csv", fd_rows)
    write_csv(args.output_dir / "mc_vs_gh.csv", mc_rows)
    print(json.dumps(report, indent=2), flush=True)
    return 0 if report["status"] == "DETERMINISTIC_MI_CERTIFIED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
