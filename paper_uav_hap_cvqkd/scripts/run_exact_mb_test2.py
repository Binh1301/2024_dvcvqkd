"""Minimal exact common-ensemble validation for physical MB TEST2 only."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import csv
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Callable

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts._common import holevo_numerical_kwargs, load_yaml
from scripts.calculate_channel_pdf_and_moments import analyze_product, derive_physical_inputs
from scripts.diagnose_mb_va_adam import MBVAParameters
from src.channel.phase_noise import phase_distortion_variance, phase_noise_coefficient
from src.cvqkd.gram_moments import (
    PRECISION_LADDER,
    GramMomentResult,
    c4_gram_source_moments,
)
from src.cvqkd.holevo import _holevo_from_source_moments
from src.cvqkd.mutual_information import discrete_mutual_information, standard_complex_noise
from src.cvqkd.secret_key_rate import fading_secret_key_rate
from src.modulation.joint_ps_gs import Ensemble, reference_ensemble
from src.modulation.qam256 import square_qam256
from src.utils.random import torch_generator


RAW_TO_REPO_MB_SCALE = 42.5
MB_CONVENTION = "nu_mb_repo=42.5*nu_mb_raw; raw grid is square_qam256(alpha0=sqrt(30))"
COARSE_NUS = (0.10, 0.13, 0.14, 0.15, 0.16, 0.17, 0.20)
CRN_SEEDS = (202607, 202608, 202609, 202610, 202611)
MI_SAMPLES_PER_SYMBOL = 2048
VA = 2.0
FD_ATOL = 1.0e-7
FD_RTOL = 0.05
OBJECTIVE_FLOOR = 1.0e-10
OUTPUT = ROOT / "results" / "exact_mb_test2"
LEGACY_EXACT_DIR = ROOT / "results" / "mb_sweep_fixed_zeta30_VA2_sources"
KNOWN_EXACT_SOURCE = {
    0.10: (1.4141975446461088, 3.53821884252737e-5),
    0.15: (1.4142132377824910, 7.81868459723089e-7),
    0.20: (1.4142135560377151, 1.62655009052085e-8),
}


def nu_mb_repo(nu_mb_raw: float) -> float:
    value = float(nu_mb_raw)
    if not math.isfinite(value) or value < 0.0:
        raise ValueError("nu_mb_raw must be finite and nonnegative.")
    return RAW_TO_REPO_MB_SCALE * value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json_hash(payload: dict) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _tensor_hex(value: torch.Tensor) -> dict:
    flat = value.detach().cpu().reshape(-1)
    if value.is_complex():
        data = [[float(item.real).hex(), float(item.imag).hex()] for item in flat.tolist()]
    else:
        data = [float(item).hex() for item in flat.tolist()]
    return {"dtype": str(value.dtype), "shape": list(value.shape), "data": data}


def ensemble_hash(ensemble: Ensemble) -> str:
    """Hash the exact binary64 common ensemble used by MI and Holevo."""

    return _json_hash({
        "schema": "exact-common-ensemble-v1",
        "probabilities": _tensor_hex(ensemble.probabilities),
        "amplitudes": _tensor_hex(ensemble.amplitudes),
        "declared_va": _tensor_hex(ensemble.declared_va),
    })


def build_mb_ensemble(config: dict, nu_mb_raw: float, va: float) -> Ensemble:
    repo_value = nu_mb_repo(nu_mb_raw)
    ensemble = reference_ensemble(
        "mb",
        batch_size=1,
        modulation_variance=float(va),
        nu_mb=repo_value,
        v_min=float(config["cvqkd"]["v_min_snu"]),
        v_max=float(config["cvqkd"]["v_max_snu"]),
        n_peak_photons=float(config["cvqkd"]["n_peak_photons"]),
    )
    raw = square_qam256(alpha0=math.sqrt(30.0))
    expected = torch.exp(-float(nu_mb_raw) * raw.abs().square())
    expected = expected / expected.sum()
    if not torch.allclose(ensemble.probabilities[0], expected, atol=1e-14, rtol=1e-14):
        raise AssertionError("raw/canonical MB conversion mismatch")
    ensemble.validate(tolerance=1e-12)
    return ensemble


def channel_fixture(tau_zen: float = 0.92, eta_ao: float = 0.95) -> dict[str, float]:
    physical = derive_physical_inputs(float(tau_zen))
    channel_moments = analyze_product(physical["v_sc"], physical)["moments"]
    tau_raw = phase_distortion_variance(
        9.4e-18, physical["wavelength_m"], physical["link_length_m"]
    )
    tau_ao = (1.0 - float(eta_ao)) * tau_raw
    return {
        "tau_zen": float(tau_zen),
        "eta_AO": float(eta_ao),
        "zeta_deg": 30.0,
        "link_length_m": float(physical["link_length_m"]),
        "T_eff": float(channel_moments["mean_sqrt_eta"]) ** 2,
        "epsilon_base": float(physical["epsilon_ch_snu"]),
        "c_phi": phase_noise_coefficient(tau_ao),
        "cn2_phase": 9.4e-18,
    }


class ExactMBEvaluator:
    def __init__(
        self,
        config: dict,
        channel: dict[str, float],
        output: Path,
        *,
        crn_seeds: tuple[int, ...] = CRN_SEEDS,
        mi_samples: int = MI_SAMPLES_PER_SYMBOL,
        source_evaluator: Callable[..., GramMomentResult] = c4_gram_source_moments,
        allow_legacy_exact_import: bool = True,
        source_cache_dir: Path | None = None,
    ) -> None:
        self.config = config
        self.channel = channel
        self.output = Path(output)
        self.cache_dir = Path(source_cache_dir) if source_cache_dir is not None else self.output / "exact_source_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.numerical = holevo_numerical_kwargs(config)
        self.crn_seeds = tuple(int(seed) for seed in crn_seeds)
        self.mi_samples = int(mi_samples)
        self.source_evaluator = source_evaluator
        self.allow_legacy_exact_import = bool(allow_legacy_exact_import)
        self.noises = tuple(
            standard_complex_noise(
                (1, 256, self.mi_samples),
                generator=torch_generator(seed),
                device=torch.device("cpu"),
            )
            for seed in self.crn_seeds
        )
        self.sources: dict[str, dict] = {}
        self.evaluations: dict[tuple[str, str], dict] = {}
        source_paths = (
            ROOT / "src" / "cvqkd" / "gram_moments.py",
            ROOT / "src" / "cvqkd" / "spectral_frechet.py",
            ROOT / "scripts" / "full_support_c4_worker.py",
        )
        self.source_implementation = {
            str(path.relative_to(ROOT)).replace("\\", "/"): _sha256(path)
            for path in source_paths
        }
        self.source_settings = {
            "density_eigenvalue_tolerance": self.numerical["density_eigenvalue_tolerance"],
            "physicality_tolerance": self.numerical["physicality_tolerance"],
            "precision_ladder": list(PRECISION_LADDER),
        }

    def _source_identity(self, ensemble: Ensemble, nu_raw: float, va: float) -> dict:
        return {
            "schema": "exact-mb-source-cache-v1",
            "ensemble_hash": ensemble_hash(ensemble),
            "nu_mb_raw_hex": float(nu_raw).hex(),
            "nu_mb_repo_hex": nu_mb_repo(nu_raw).hex(),
            "V_A_hex": float(va).hex(),
            "mb_convention": MB_CONVENTION,
            "source_implementation": self.source_implementation,
            "source_settings": self.source_settings,
        }

    @staticmethod
    def _legacy_byte_hash(value: torch.Tensor) -> str:
        return hashlib.sha256(value.detach().cpu().contiguous().numpy().tobytes()).hexdigest()

    def _legacy_exact_source(
        self, ensemble: Ensemble, nu_raw: float, identity: dict
    ) -> dict | None:
        if not self.allow_legacy_exact_import or self.source_evaluator is not c4_gram_source_moments:
            return None
        if float(f"{nu_raw:.2f}") != float(nu_raw):
            return None
        path = LEGACY_EXACT_DIR / f"source_nu_{nu_raw:.2f}.json"
        if not path.is_file():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        expected = {
            "pmf_sha256": self._legacy_byte_hash(ensemble.probabilities),
            "amplitude_sha256": self._legacy_byte_hash(ensemble.amplitudes),
        }
        if payload.get("input_hashes") != expected or payload.get("rank") != 256:
            return None
        return {
            **identity,
            "cache_key": _json_hash(identity),
            "C": float(payload["C"]),
            "w": float(payload["w"]),
            "source_moment_route": str(payload["route"]),
            "support_size": 256,
            "cache_origin": "LEGACY_EXACT_ENSEMBLE_HASH_IMPORT",
            "legacy_artifact": str(path.relative_to(ROOT)).replace("\\", "/"),
            "legacy_artifact_sha256": _sha256(path),
        }

    def source_moments(self, ensemble: Ensemble, nu_raw: float, va: float) -> dict:
        identity = self._source_identity(ensemble, nu_raw, va)
        key = _json_hash(identity)
        if key in self.sources:
            return self.sources[key]
        path = self.cache_dir / f"{key}.json"
        if path.is_file():
            payload = json.loads(path.read_text(encoding="utf-8"))
            if payload.get("cache_key") != key or any(
                payload.get(name) != value for name, value in identity.items()
            ):
                raise ValueError(f"Exact source cache identity mismatch: {path}")
            payload["cache_hit"] = True
            self.sources[key] = payload
            return payload

        payload = self._legacy_exact_source(ensemble, nu_raw, identity)
        cache_hit = payload is not None
        if payload is None:
            before = ensemble_hash(ensemble)
            moments = self.source_evaluator(
                ensemble,
                density_eigenvalue_tolerance=self.numerical["density_eigenvalue_tolerance"],
                physicality_tolerance=self.numerical["physicality_tolerance"],
            )
            after = ensemble_hash(ensemble)
            if before != after or before != identity["ensemble_hash"]:
                raise AssertionError("source-moment evaluator mutated or changed the ensemble")
            diagnostic = moments.diagnostics[0]
            payload = {
                **identity,
                "cache_key": key,
                "C": float(moments.coherent_correlation[0]),
                "w": float(moments.w[0]),
                "source_moment_route": str(diagnostic.get("route")),
                "support_size": int(diagnostic.get("support_size", 256)),
                "cache_origin": "FRESH_EXACT_EVALUATION",
            }
        if payload["support_size"] != 256:
            raise FloatingPointError("Exact source moments do not retain all 256 modes")
        stored = {name: value for name, value in payload.items() if name != "cache_hit"}
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(stored, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(path)
        payload["cache_hit"] = cache_hit
        self.sources[key] = payload
        return payload

    def prepare_sources(self, points: list[tuple[float, float]], workers: int) -> None:
        unique = list(dict.fromkeys((float(nu), float(va)) for nu, va in points))

        def prepare(point: tuple[float, float]) -> None:
            nu_raw, va = point
            ensemble = build_mb_ensemble(self.config, nu_raw, va)
            print(f"source start nu_raw={nu_raw:.12g} VA={va:.12g}", flush=True)
            source = self.source_moments(ensemble, nu_raw, va)
            print(
                f"source ready nu_raw={nu_raw:.12g} route={source['source_moment_route']} "
                f"cache_hit={source['cache_hit']}",
                flush=True,
            )

        with ThreadPoolExecutor(max_workers=workers) as pool:
            list(pool.map(prepare, unique))

    def __call__(self, nu_raw: float, va: float = VA) -> dict:
        key = (float(nu_raw).hex(), float(va).hex())
        if key in self.evaluations:
            return self.evaluations[key]
        ensemble = build_mb_ensemble(self.config, nu_raw, va)
        common_hash = ensemble_hash(ensemble)
        t = torch.tensor([self.channel["T_eff"]], dtype=torch.float64)
        epsilon_total = self.channel["epsilon_base"] + self.channel["c_phi"] * float(va)
        epsilon = torch.tensor([epsilon_total], dtype=torch.float64)
        mi_values = [
            float(discrete_mutual_information(
                ensemble,
                t,
                epsilon,
                noise_samples_per_symbol=self.mi_samples,
                standard_noise_samples=noise,
            )[0])
            for noise in self.noises
        ]
        mi_hash = ensemble_hash(ensemble)
        source = self.source_moments(ensemble, nu_raw, va)
        source_hash = ensemble_hash(ensemble)
        if source["ensemble_hash"] != common_hash:
            raise AssertionError("source cache does not match the MI ensemble")
        holevo = _holevo_from_source_moments(
            ensemble,
            t,
            epsilon,
            coherent_correlation=torch.tensor([source["C"]], dtype=torch.float64),
            w_raw=torch.tensor([source["w"]], dtype=torch.float64),
            tau=None,
            tau_trace=ensemble.probabilities.sum(dim=-1),
            require_supported_symmetry=True,
            symmetry_tolerance=self.numerical["symmetry_tolerance"],
            physicality_tolerance=self.numerical["physicality_tolerance"],
            diagnostics={
                "backend": "exact_common_ensemble_mb_test2",
                "ensemble_hash": common_hash,
                "source_cache_key": source["cache_key"],
            },
        )
        holevo_hash = ensemble_hash(ensemble)
        if len({common_hash, mi_hash, source_hash, holevo_hash}) != 1:
            raise AssertionError("MI/source/Holevo ensemble hashes differ")
        mi = float(np.mean(mi_values))
        rate = fading_secret_key_rate(
            torch.tensor([mi], dtype=torch.float64),
            holevo.chi_be,
            float(self.config["cvqkd"]["beta_reconciliation"]),
        )
        row = {
            "nu_raw": float(nu_raw),
            "nu_repo": nu_mb_repo(nu_raw),
            "V_A": float(va),
            "sum_p": float(ensemble.probabilities.sum()),
            "VA_actual": float(ensemble.computed_va()[0]),
            "ensemble_hash": common_hash,
            "mi_ensemble_hash": mi_hash,
            "source_ensemble_hash": source_hash,
            "holevo_ensemble_hash": holevo_hash,
            "C": float(source["C"]),
            "w": float(source["w"]),
            "I_AB": mi,
            "I_AB_replicates": mi_values,
            "chi_BE": float(holevo.chi_be[0]),
            "SKR": float(rate.fading_average_raw),
            "K": float(rate.fading_average_raw),
            "SKR_replicates": [
                float(self.config["cvqkd"]["beta_reconciliation"]) * value
                - float(holevo.chi_be[0])
                for value in mi_values
            ],
            "Z_star": float(holevo.z[0]),
            "epsilon_total": epsilon_total,
            "source_moment_route": source["source_moment_route"],
            "source_cache_key": source["cache_key"],
            "cache_hit": bool(source["cache_hit"]),
            "cache_origin": source["cache_origin"],
        }
        self.evaluations[key] = row
        return row


def finite_difference(evaluate: ExactMBEvaluator, center: float, h: float) -> dict:
    plus = evaluate(center + h, VA)
    minus = evaluate(center - h, VA)
    derivatives = (
        np.asarray(plus["SKR_replicates"]) - np.asarray(minus["SKR_replicates"])
    ) / (2.0 * h)
    gradient = (plus["SKR"] - minus["SKR"]) / (2.0 * h)
    stderr = float(np.std(derivatives, ddof=1) / math.sqrt(len(derivatives)))
    resolved = abs(gradient) > 2.0 * stderr + OBJECTIVE_FLOOR / h
    return {
        "center_nu_raw": center,
        "h": h,
        "minus_nu_raw": center - h,
        "plus_nu_raw": center + h,
        "minus_SKR": minus["SKR"],
        "plus_SKR": plus["SKR"],
        "dK_dnu": gradient,
        "paired_stderr": stderr,
        "resolved": resolved,
    }


def _write_csv(path: Path, rows: list[dict], fields: tuple[str, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def coarse_landscape(evaluator: ExactMBEvaluator, workers: int) -> tuple[list[dict], dict]:
    evaluator.prepare_sources([(nu, VA) for nu in COARSE_NUS], workers)
    rows = [evaluator(nu, VA) for nu in COARSE_NUS]
    best = max(rows, key=lambda row: row["SKR"])
    fields = (
        "nu_raw", "nu_repo", "V_A", "sum_p", "VA_actual", "ensemble_hash",
        "C", "w", "I_AB", "chi_BE", "SKR", "Z_star", "source_moment_route",
        "cache_hit", "cache_origin",
    )
    _write_csv(evaluator.output / "coarse_landscape.csv", rows, fields)
    _write_json(evaluator.output / "coarse_landscape.json", rows)
    return rows, best


def fd_readiness(evaluator: ExactMBEvaluator, center: float, workers: int) -> dict:
    steps = (0.01, 0.005)
    evaluator.prepare_sources(
        [(center - h, VA) for h in steps] + [(center + h, VA) for h in steps], workers
    )
    rows = [finite_difference(evaluator, center, h) for h in steps]
    left, right = rows
    stable = (
        math.copysign(1.0, left["dK_dnu"]) == math.copysign(1.0, right["dK_dnu"])
        and abs(left["dK_dnu"] - right["dK_dnu"])
        <= FD_ATOL + FD_RTOL * max(abs(left["dK_dnu"]), abs(right["dK_dnu"]))
    )
    report = {
        "status": "PASS" if stable and all(row["resolved"] for row in rows) else "FAIL",
        "center_nu_raw": center,
        "chosen_h": 0.01 if stable and all(row["resolved"] for row in rows) else None,
        "stable": stable,
        "rows": rows,
        "absolute_tolerance": FD_ATOL,
        "relative_tolerance": FD_RTOL,
    }
    _write_csv(
        evaluator.output / "finite_difference.csv",
        rows,
        ("center_nu_raw", "h", "minus_nu_raw", "plus_nu_raw", "minus_SKR", "plus_SKR", "dK_dnu", "paired_stderr", "resolved"),
    )
    _write_json(evaluator.output / "finite_difference.json", report)
    return report


def test2_one_step(
    evaluator: ExactMBEvaluator,
    h: float,
    workers: int,
    learning_rate: float,
) -> dict:
    starts = (0.10, 0.15, 0.20)
    evaluator.prepare_sources(
        [(start - h, VA) for start in starts] + [(start + h, VA) for start in starts], workers
    )
    proposals = []
    for start in starts:
        initial = evaluator(start, VA)
        fd = finite_difference(evaluator, start, h)
        if not fd["resolved"]:
            return {"status": "FAIL", "reason": f"unresolved derivative at nu={start}", "runs": proposals}
        model = MBVAParameters(start, VA)
        model.u_va.requires_grad_(False)
        optimizer = torch.optim.Adam([model.u_mb], lr=learning_rate)
        optimizer.zero_grad(set_to_none=True)
        grad_u_mb, _ = model.assign_loss_gradients(fd["dK_dnu"], 0.0)
        model.u_va.grad = None
        optimizer.step()
        with torch.no_grad():
            new_nu = float(model()[0])
        proposals.append({
            "start_nu_raw": start,
            "initial": initial,
            "fd": fd,
            "grad_u_mb": grad_u_mb,
            "new_nu_raw": new_nu,
        })

    evaluator.prepare_sources([(row["new_nu_raw"], VA) for row in proposals], workers)
    rows = []
    for proposal in proposals:
        final = evaluator(proposal["new_nu_raw"], VA)
        rows.append({
            "start_nu_raw": proposal["start_nu_raw"],
            "new_nu_raw": proposal["new_nu_raw"],
            "h": h,
            "dK_dnu": proposal["fd"]["dK_dnu"],
            "grad_u_mb": proposal["grad_u_mb"],
            "initial_SKR": proposal["initial"]["SKR"],
            "new_SKR": final["SKR"],
            "improved": final["SKR"] > proposal["initial"]["SKR"],
            "ensemble_hash": final["ensemble_hash"],
            "source_moment_route": final["source_moment_route"],
            "cache_hit": final["cache_hit"],
        })
    passed = all(row["improved"] for row in rows)
    report = {
        "status": "PASS" if passed else "FAIL",
        "scope": "ONE_EXACT_ADAM_STEP_PER_START; NOT_CONTINUOUS_OPTIMUM",
        "learning_rate": learning_rate,
        "h": h,
        "runs": rows,
    }
    _write_csv(
        evaluator.output / "test2_adam_one_step.csv",
        rows,
        ("start_nu_raw", "new_nu_raw", "h", "dK_dnu", "grad_u_mb", "initial_SKR", "new_SKR", "improved", "ensemble_hash", "source_moment_route", "cache_hit"),
    )
    _write_json(evaluator.output / "test2_adam_one_step.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("coarse", "fd", "test2"), default="coarse")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    parser.add_argument("--source-workers", type=int, default=3)
    parser.add_argument("--learning-rate", type=float, default=0.10)
    args = parser.parse_args()
    if args.source_workers < 1 or not math.isfinite(args.learning_rate) or args.learning_rate <= 0.0:
        parser.error("source-workers and learning-rate must be positive")
    torch.set_num_threads(1)
    config = load_yaml(ROOT / "configs" / "default.yaml")
    channel = channel_fixture()
    evaluator = ExactMBEvaluator(config, channel, args.output_dir)
    rows, best = coarse_landscape(evaluator, args.source_workers)
    known_checks = {}
    for row in rows:
        if row["nu_raw"] in KNOWN_EXACT_SOURCE:
            expected_c, expected_w = KNOWN_EXACT_SOURCE[row["nu_raw"]]
            known_checks[str(row["nu_raw"])] = {
                "C_abs_diff": abs(row["C"] - expected_c),
                "w_abs_diff": abs(row["w"] - expected_w),
                "status": "PASS" if math.isclose(row["C"], expected_c, rel_tol=1e-12, abs_tol=1e-14)
                and math.isclose(row["w"], expected_w, rel_tol=1e-10, abs_tol=1e-14) else "FAIL",
            }
    known_checks["0.173421"] = {
        "status": "NOT RUN",
        "reason": "Prior terminal audit had no hash-bound cache artifact; unsafe import refused.",
    }
    report = {
        "status": "COARSE_COMPLETE",
        "channel_fixture": channel,
        "mb_convention": MB_CONVENTION,
        "crn_seeds": list(CRN_SEEDS),
        "mi_samples_per_symbol": MI_SAMPLES_PER_SYMBOL,
        "common_ensemble_hashes_identical": all(
            row["ensemble_hash"] == row["mi_ensemble_hash"] == row["source_ensemble_hash"] == row["holevo_ensemble_hash"]
            for row in rows
        ),
        "C_w_interpolation": False,
        "coarse_best": {"nu_raw": best["nu_raw"], "SKR": best["SKR"]},
        "known_exact_source_checks": known_checks,
        "finite_difference": "NOT RUN",
        "test2_adam": "NOT RUN",
        "test3": "NOT RUN",
    }
    if args.stage in {"fd", "test2"}:
        fd = fd_readiness(evaluator, best["nu_raw"], args.source_workers)
        report["finite_difference"] = fd
        report["status"] = "FD_PASS" if fd["status"] == "PASS" else "FD_FAILED"
        if args.stage == "test2" and fd["status"] == "PASS":
            report["test2_adam"] = test2_one_step(
                evaluator, float(fd["chosen_h"]), args.source_workers, args.learning_rate
            )
            report["status"] = f"TEST2_{report['test2_adam']['status']}"
        elif args.stage == "test2":
            report["test2_adam"] = {"status": "NOT RUN", "reason": "FD readiness failed"}
            report["status"] = "TEST2_NOT_RUN_FD"
    _write_json(evaluator.output / "run_report.json", report)
    print(json.dumps(report, indent=2, sort_keys=True), flush=True)
    test2 = report["test2_adam"]
    return 1 if isinstance(test2, dict) and test2.get("status") == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
