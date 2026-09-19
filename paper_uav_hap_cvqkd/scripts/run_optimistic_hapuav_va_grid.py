"""Coarse VA grid for the isolated optimistic HAP-UAV scenario."""

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
import sys
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts._common import load_yaml
from scripts.run_mb_nu_threshold_va2 import _source_summary
from src.cvqkd.gram_moments import c4_gram_source_moments
import src.cvqkd.holevo as holevo_module
from src.cvqkd.holevo import _holevo_from_source_moments
from src.cvqkd.mutual_information import discrete_mutual_information, standard_complex_noise
from src.modulation.joint_ps_gs import reference_ensemble
from src.utils.random import torch_generator

VA_GRID = (0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0)
BETA = 0.95
NU_MB = 0.20
MI_SEEDS = (202607, 202608, 202609, 202610, 202611)
MI_SAMPLES_PER_SYMBOL = 2048
SCHEMES = ("uniform", "binomial", "mb")
SOURCE_REFS = {
    "uniform": (
        "1.4019995788968011700681192152159252514555640211395",
        "0.026543338228713932540445642845440478987301227896247",
        "cvqkd_uniform_va2_c4_checkpoint.json",
    ),
    "binomial": (
        "1.41414750131106445213245972871615156498",
        "1.13331366963443032864740272931418486e-4",
        "cvqkd_binomial_va2_c4_checkpoint.json",
    ),
    "mb": (
        "1.4142135560377151402791686003423073594184222417457",
        "1.626550090520852218494768463193198898946e-8",
        "cvqkd_mb_nu_0p200000_va2_c4_checkpoint.json",
    ),
}


def _forbidden(*_args, **_kwargs):
    raise RuntimeError("Optimistic VA grid reached a forbidden full-Z/AP path.")


def _load_channel_rows() -> list[dict]:
    path = ROOT / "results" / "optimistic_hapuav_va2" / "optimistic_hapuav_va2.json"
    return json.loads(path.read_text(encoding="utf-8"))["channel_rows"]


def _source(config: dict, scheme: str, va: float):
    nu = NU_MB if scheme == "mb" else None
    ensemble = reference_ensemble(
        scheme,
        batch_size=1,
        modulation_variance=va,
        nu_mb=nu,
        v_min=float(config["cvqkd"]["v_min_snu"]),
        v_max=float(config["cvqkd"]["v_max_snu"]),
        n_peak_photons=float(config["cvqkd"]["n_peak_photons"]),
    )
    token = f"{scheme}_va_{va:.6f}".replace(".", "p")
    checkpoint = Path(tempfile.gettempdir()) / f"cvqkd_optimistic_{token}_c4_checkpoint.json"
    if math.isclose(va, 2.0, rel_tol=0.0, abs_tol=1e-15):
        checkpoint = Path(tempfile.gettempdir()) / SOURCE_REFS[scheme][2]
        payload = json.loads(checkpoint.read_text(encoding="utf-8"))
        rows = payload["rows"]
        final = rows[-1]
        if Decimal(final["C"]) != Decimal(SOURCE_REFS[scheme][0]) or Decimal(final["w"]) != Decimal(SOURCE_REFS[scheme][1]):
            raise RuntimeError(f"Validated VA=2 source mismatch for {scheme}.")
        return ensemble, _source_summary(
            va,
            ensemble,
            final["C"],
            final["w"],
            checkpoint=checkpoint,
            runtime=sum(float(row["runtime_seconds"]) for row in rows),
            rows=rows,
        )
    started = time.perf_counter()
    moments = c4_gram_source_moments(
        ensemble,
        density_eigenvalue_tolerance=1e-13,
        fallback_timeout_seconds=None,
        max_precision_digits=2400,
        fallback_checkpoint_path=checkpoint,
        scheme_config_hash=f"optimistic-{scheme}-va-{va:.6f}-nu-{NU_MB}-c4",
    )
    elapsed = time.perf_counter() - started
    diagnostics = moments.diagnostics[0]
    rows = diagnostics.get("fallback_rows", [])
    if diagnostics.get("numerical_retained_rank") != 256 or len(rows) < 2:
        raise RuntimeError(f"Source convergence failed for {scheme}, VA={va}.")
    final = rows[-1]
    return ensemble, _source_summary(
        va,
        ensemble,
        final["C"],
        final["w"],
        checkpoint=checkpoint,
        runtime=elapsed,
        rows=rows,
    )


def main() -> int:
    started = time.perf_counter()
    config = load_yaml(ROOT / "configs" / "default.yaml")
    channel_rows = _load_channel_rows()
    noises = {
        seed: standard_complex_noise(
            (1, 256, MI_SAMPLES_PER_SYMBOL),
            generator=torch_generator(seed),
            device=torch.device("cpu"),
        )
        for seed in MI_SEEDS
    }
    holevo_module._maximize_bounded_scalar = _forbidden
    holevo_module.c4_gram_source_moments = _forbidden
    source_table = []
    rows = []
    for va in VA_GRID:
        source_by_scheme = {}
        for scheme in SCHEMES:
            ensemble, source = _source(config, scheme, va)
            source_table.append({
                "scheme": scheme,
                "VA": va,
                **{key: value for key, value in source.items() if key != "fallback_rows"},
            })
            source_by_scheme[scheme] = (ensemble, source)
        for channel in channel_rows:
            L_km = float(channel["L_km"])
            transmittance = float(channel["T"])
            epsilon_base = float(channel["epsilon_base"])
            c_phi = float(channel["c_phi"])
            epsilon_value = epsilon_base + c_phi * va
            for scheme in SCHEMES:
                ensemble, source = source_by_scheme[scheme]
                t = torch.tensor([transmittance], dtype=torch.float64)
                epsilon = torch.tensor([epsilon_value], dtype=torch.float64)
                c = torch.tensor([float(source["C"])], dtype=torch.float64)
                w = torch.tensor([float(source["w"])], dtype=torch.float64)
                mi_values = []
                for seed in MI_SEEDS:
                    mi_values.append(float(discrete_mutual_information(
                        ensemble, t, epsilon,
                        noise_samples_per_symbol=MI_SAMPLES_PER_SYMBOL,
                        standard_noise_samples=noises[seed],
                    )[0]))
                mi = sum(mi_values) / len(mi_values)
                holevo = _holevo_from_source_moments(
                    ensemble, t, epsilon,
                    coherent_correlation=c,
                    w_raw=w,
                    tau=None,
                    tau_trace=ensemble.probabilities.sum(dim=-1),
                    require_supported_symmetry=True,
                    symmetry_tolerance=1e-8,
                    physicality_tolerance=1e-10,
                    maximize_full_interval=False,
                    diagnostics={
                        "backend": "optimistic_hapuav_va_grid",
                        "source_moment_recomputed_per_distance": False,
                        "phase_noise_already_in_epsilon": True,
                    },
                )
                chi = float(holevo.chi_be[0])
                rows.append({
                    "VA": va,
                    "L_km": L_km,
                    "scheme": scheme,
                    "I_AB": mi,
                    "Z_star": float(holevo.z[0]),
                    "chi_BE": chi,
                    "beta_I_AB": BETA * mi,
                    "K_raw": BETA * mi - chi,
                    "physicality_pass": min(float(holevo.covariance.lambda1[0]), float(holevo.covariance.lambda2[0]), float(holevo.covariance.lambda3[0])) >= 1.0 - 1e-10,
                    "holevo_mode": holevo.diagnostics["mode"],
                })
    out = ROOT / "results" / "optimistic_hapuav_va_grid"
    out.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0])
    with (out / "optimistic_hapuav_va_grid.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    summary = []
    for va in VA_GRID:
        selected = [row for row in rows if row["VA"] == va]
        summary.append({
            "VA": va,
            "min_K_raw": min(row["K_raw"] for row in selected),
            "max_K_raw": max(row["K_raw"] for row in selected),
            "positive_points": sum(row["K_raw"] > 0.0 for row in selected),
            "all_positive": all(row["K_raw"] > 0.0 for row in selected),
        })
    payload = {
        "artifact": "OPTIMISTIC_HAPUAV_VA_GRID",
        "VA_grid": list(VA_GRID),
        "source_moments": source_table,
        "summary": summary,
        "rows": rows,
        "runtime_seconds": time.perf_counter() - started,
    }
    (out / "optimistic_hapuav_va_grid.json").write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"runtime_seconds": time.perf_counter() - started, "summary": summary, "output_dir": str(out)}, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
