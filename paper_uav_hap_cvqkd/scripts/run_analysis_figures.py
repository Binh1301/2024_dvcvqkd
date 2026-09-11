"""Bounded analysis-grade surrogate search and exact security-anchor figures.

The only differentiable source-moment path used here is explicitly marked
``TRAINING_SURROGATE_ONLY``.  Exact corrected AP values and the existing full-Z
Holevo chain remain the authority for every reported security anchor.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import html
import json
import math
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Iterable

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import recompute_corrected_bd_security as existing_case  # noqa: E402
from scripts.validate_corrected_ap_custom_backward import (  # noqa: E402
    _target_base,
    _target_direction,
    _target_directional_inputs,
)
from src.cvqkd.holevo import (  # noqa: E402
    _evaluate_holevo_for_correlations,
    _holevo_from_source_moments,
)
from src.cvqkd.mutual_information import (  # noqa: E402
    discrete_mutual_information,
    standard_complex_noise,
)
from src.cvqkd.training_surrogate import (  # noqa: E402
    c4_training_surrogate,
)
from src.modulation.joint_ps_gs import (  # noqa: E402
    Ensemble,
    JointTransmitter,
    PeakPhotonConstraintViolation,
)
from src.modulation.normalization import physical_amplitudes  # noqa: E402
from src.modulation.qam256 import (  # noqa: E402
    c4_orbit_indices,
    expand_c4_orbit_masses,
    expand_c4_orbit_values,
)


ARTIFACT_DATE = "20260911"
SURROGATE_REGULARIZATION = 1.0e-10
SURROGATE_CANDIDATES = (1.0e-8, 1.0e-10, 1.0e-12)
SMOKE_STEPS = 20
ANALYSIS_STEPS = 50
TRAINING_NOISE_SAMPLES = 32
GRID_NOISE_SAMPLES = 64
ANCHOR_NOISE_SAMPLES = 512
GRID_T_BINS = 4
GRID_EPSILON_BINS = 4
ANCHOR_COUNT = 7
MB_NU = 0.1
V_MIN = 0.1
V_MAX = 4.0
VA_BUDGET = 1.5
N_PEAK_PHOTONS = 30.0
BETA = 0.95
PHASE_COEFFICIENT = 0.0
EPSILON_TOTAL_DEFINITION = "epsilon_total = epsilon_base + 0 * V_A"
ANALYSIS_Z_GRID_SIZE = 9
ANALYSIS_Z_REFINEMENT_STEPS = 2
SECURITY_Z_GRID_SIZE = 33
SECURITY_Z_REFINEMENT_STEPS = 12
AP_DIGITS = (800, 900)
AP_MAX_WORKERS = 3
AP_TIMEOUT_SECONDS = 1800
CORRECTED_C = float(existing_case.C_CORRECTED)
CORRECTED_W = float(existing_case.W_CORRECTED)
CORRECTED_C_TEXT = existing_case.C_CORRECTED_TEXT
CORRECTED_W_TEXT = existing_case.W_CORRECTED_TEXT
CORRECTED_WORKER = ROOT / "scripts" / "full_support_c4_worker.py"
TANGENT_ARTIFACT = ROOT / "results" / "c4_remaining_forward_tangents_20260911.json"
ORBIT_INDICES = c4_orbit_indices(device="cpu")[:, 0]

METHODS = (
    ("uniform", "Uniform 256-QAM", "#1f77b4"),
    ("mb", "MB baseline (nu=0.1)", "#ff7f0e"),
    ("ps", "Adaptive PS", "#2ca02c"),
    ("va", "Adaptive V_A", "#d62728"),
    ("ps_va", "Adaptive PS+V_A", "#9467bd"),
    ("full", "Full PS+GS+V_A", "#111111"),
)
METHOD_LABEL = {key: label for key, label, _ in METHODS}
METHOD_COLOR = {key: color for key, _, color in METHODS}


class AnalysisBlocked(RuntimeError):
    """A declared stop condition prevented defensible analysis figures."""


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _git_metadata() -> dict[str, Any]:
    def run(*args: str) -> str | None:
        try:
            return subprocess.check_output(
                ["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
            ).strip()
        except (OSError, subprocess.CalledProcessError):
            return None

    status = run("status", "--porcelain")
    return {
        "commit": run("rev-parse", "HEAD"),
        "branch": run("branch", "--show-current"),
        "dirty": None if status is None else bool(status),
    }


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def _float(value: Any) -> float:
    return float(value.detach()) if isinstance(value, torch.Tensor) else float(value)


def _relative(observed: float, reference: float) -> float:
    return abs(float(observed) - float(reference)) / max(abs(float(reference)), 1.0e-40)


def _array_hash(values: Iterable[float]) -> str:
    array = np.ascontiguousarray(np.asarray(tuple(values), dtype=np.float64))
    return hashlib.sha256(array.tobytes()).hexdigest()


def _pair_hash(values: Iterable[Iterable[float]]) -> str:
    array = np.ascontiguousarray(np.asarray(tuple(values), dtype=np.float64))
    return hashlib.sha256(array.tobytes()).hexdigest()


def _orbit_inputs(ensemble: Ensemble, row: int) -> tuple[torch.Tensor, torch.Tensor]:
    indices = ORBIT_INDICES.to(device=ensemble.probabilities.device)
    return (
        ensemble.probabilities[row, indices],
        ensemble.amplitudes[row, indices],
    )


def _surrogate_batch(
    ensemble: Ensemble,
    *,
    regularization: float = SURROGATE_REGULARIZATION,
) -> tuple[torch.Tensor, torch.Tensor, tuple[dict[str, Any], ...]]:
    """Evaluate the isolated search surrogate state-by-state."""

    correlations: list[torch.Tensor] = []
    penalties: list[torch.Tensor] = []
    diagnostics: list[dict[str, Any]] = []
    for row in range(ensemble.probabilities.shape[0]):
        probabilities, prototypes = _orbit_inputs(ensemble, row)
        result = c4_training_surrogate(
            probabilities,
            prototypes,
            regularization=regularization,
        )
        correlations.append(result.coherent_correlation)
        penalties.append(result.w)
        diagnostics.append(dict(result.diagnostics))
    return torch.stack(correlations), torch.stack(penalties), tuple(diagnostics)


def _holevo_from_moments(
    ensemble: Ensemble,
    transmittance: torch.Tensor,
    epsilon_base: torch.Tensor,
    correlations: torch.Tensor,
    w_raw: torch.Tensor,
    *,
    analysis_grid: bool,
) -> Any:
    return _holevo_from_source_moments(
        ensemble,
        transmittance,
        epsilon_base,
        coherent_correlation=correlations,
        w_raw=w_raw,
        tau=None,
        tau_trace=ensemble.probabilities.sum(dim=-1),
        require_supported_symmetry=True,
        symmetry_tolerance=1.0e-8,
        physicality_tolerance=1.0e-10,
        diagnostics={
            "backend": (
                "training_surrogate_regularized_c4"
                if analysis_grid
                else "corrected_ap_anchor_source_moments"
            ),
            "artifact_class": (
                "TRAINING_SURROGATE" if analysis_grid else "EXACT_AP_SECURITY_ANCHOR"
            ),
            "phase_disabled": True,
            "c_phi": PHASE_COEFFICIENT,
        },
        z_grid_size=(ANALYSIS_Z_GRID_SIZE if analysis_grid else SECURITY_Z_GRID_SIZE),
        z_refinement_steps=(
            ANALYSIS_Z_REFINEMENT_STEPS if analysis_grid else SECURITY_Z_REFINEMENT_STEPS
        ),
    )


def _evaluate_surrogate(
    transmitter: JointTransmitter,
    transmittance: torch.Tensor,
    epsilon_base: torch.Tensor,
    standard_noise: torch.Tensor,
    *,
    analysis_grid: bool = True,
    search_proxy: bool = True,
) -> dict[str, Any]:
    ensemble = transmitter(transmittance, epsilon_base)
    correlations, w_raw, source_diagnostics = _surrogate_batch(ensemble)
    mi = discrete_mutual_information(
        ensemble,
        transmittance,
        epsilon_base,
        noise_samples_per_symbol=standard_noise.shape[-1],
        standard_noise_samples=standard_noise,
        noise_sample_chunk_size=standard_noise.shape[-1],
    )
    if search_proxy:
        # This is only a smooth optimization objective.  It uses a bounded
        # representative correlation near the source-moment interval rather
        # than claiming to solve the full-Z maximization.  Exact anchors below
        # always call _holevo_from_source_moments with the existing 33/12
        # full-Z solver.
        va = ensemble.computed_va()
        a = va + 1.0
        b = 1.0 + transmittance * va + transmittance * epsilon_base
        physical_radicand = a * b - 1.0 - torch.abs(a - b)
        z_phys = torch.sqrt(torch.clamp_min(physical_radicand, 0.0))
        width = torch.sqrt(torch.clamp_min(2.0 * transmittance * epsilon_base * w_raw, 0.0) + 1.0e-18)
        representative = 2.0 * torch.sqrt(transmittance) * correlations + width
        bounded = 0.98 * z_phys * torch.tanh(
            representative / (0.98 * z_phys + 1.0e-12)
        )
        chi, _, _ = _evaluate_holevo_for_correlations(
            ensemble,
            transmittance,
            epsilon_base,
            bounded,
            require_supported_symmetry=True,
            symmetry_tolerance=1.0e-8,
            physicality_tolerance=1.0e-10,
            return_covariance=False,
        )
        holevo = None
        source_marker = "smooth_bounded_training_security_proxy"
    else:
        holevo = _holevo_from_moments(
            ensemble,
            transmittance,
            epsilon_base,
            correlations,
            w_raw,
            analysis_grid=analysis_grid,
        )
        chi = holevo.chi_be
        source_marker = "full_Z_with_surrogate_source_moments"
    raw = BETA * mi - chi
    if not bool(torch.isfinite(raw).all()):
        raise FloatingPointError("surrogate security estimate returned NaN or Inf")
    return {
        "ensemble": ensemble,
        "C": correlations,
        "w": w_raw,
        "I_AB": mi,
        "chi_BE": chi,
        "raw_K": raw,
        "holevo": holevo,
        "source_marker": source_marker,
        "source_diagnostics": source_diagnostics,
    }


def _target_nearby_ensembles() -> dict[str, tuple[torch.Tensor, torch.Tensor]]:
    nearby: dict[str, tuple[torch.Tensor, torch.Tensor]] = {}
    for name, family, theta in (
        ("mild_ps", "ps", 0.10),
        ("mild_gs_real", "gs_real", 0.03),
        ("mild_va", "va", 0.10),
    ):
        p, z = _target_direction(family, torch.tensor(theta, dtype=torch.float64))
        nearby[name] = (p.detach(), z.detach())

    base_p, _, raw_coordinates = _target_base()
    x = torch.arange(1, 65, dtype=torch.float64)
    direction = torch.sin(0.37 * x)
    direction = (direction - direction.mean()) / direction.abs().max()
    orbit_masses = torch.softmax(0.05 * direction, dim=0)
    coordinates = raw_coordinates.clone()
    coordinates[0, 0] += 0.03
    prototypes = torch.view_as_complex(coordinates.contiguous())
    relative_prototypes = prototypes / torch.sqrt(prototypes.abs().square().mean())
    full_p = expand_c4_orbit_masses(orbit_masses.unsqueeze(0))[0]
    full_relative = expand_c4_orbit_values(relative_prototypes)
    full_alpha = physical_amplitudes(
        full_p.unsqueeze(0),
        full_relative.unsqueeze(0),
        torch.tensor([1.10], dtype=torch.float64),
    )[0]
    del base_p
    nearby["combined"] = (
        (orbit_masses / 4.0).detach(),
        full_alpha[ORBIT_INDICES].detach(),
    )
    return nearby


def _exact_worker_request(
    probabilities: torch.Tensor,
    prototypes: torch.Tensor,
) -> dict[str, Any]:
    return {
        "probabilities_float64_hex": [float(value).hex() for value in probabilities.tolist()],
        "prototypes_float64_hex": [
            [float(complex(value).real).hex(), float(complex(value).imag).hex()]
            for value in prototypes.tolist()
        ],
        "precision_ladder_decimal_digits": list(AP_DIGITS),
    }


def _run_exact_ap_job(
    name: str,
    probabilities: torch.Tensor,
    prototypes: torch.Tensor,
) -> dict[str, Any]:
    started = time.perf_counter()
    request = _exact_worker_request(probabilities, prototypes)
    try:
        completed = subprocess.run(
            [sys.executable, str(CORRECTED_WORKER)],
            cwd=ROOT,
            input=json.dumps(request, sort_keys=True),
            text=True,
            capture_output=True,
            timeout=AP_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {
            "name": name,
            "status": "FAIL_CLOSED",
            "reason": "corrected AP worker timeout",
            "runtime_seconds": time.perf_counter() - started,
        }
    if completed.returncode != 0:
        return {
            "name": name,
            "status": "FAIL_CLOSED",
            "reason": completed.stderr[-2000:] or f"worker exit {completed.returncode}",
            "runtime_seconds": time.perf_counter() - started,
        }
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        return {
            "name": name,
            "status": "FAIL_CLOSED",
            "reason": f"worker JSON failure: {error}",
            "runtime_seconds": time.perf_counter() - started,
        }
    if payload.get("status") != "FULL_SUPPORT_CONVERGED":
        return {
            "name": name,
            "status": "FAIL_CLOSED",
            "reason": payload.get("status", "unknown worker status"),
            "rows": payload.get("rows", []),
            "runtime_seconds": time.perf_counter() - started,
        }
    return {
        "name": name,
        "status": "FULL_SUPPORT_CONVERGED",
        "C": payload["C"],
        "w": payload["w"],
        "rows": payload["rows"],
        "minimum_eigenvalue": payload["rows"][-1]["minimum_eigenvalue"],
        "runtime_seconds": time.perf_counter() - started,
        "probabilities_orbit": [float(value) for value in probabilities.tolist()],
        "prototypes": [
            [float(complex(value).real), float(complex(value).imag)]
            for value in prototypes.tolist()
        ],
    }


def _run_exact_jobs(
    jobs: dict[str, tuple[torch.Tensor, torch.Tensor]],
) -> dict[str, dict[str, Any]]:
    if not jobs:
        return {}
    results: dict[str, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=min(AP_MAX_WORKERS, len(jobs))) as executor:
        futures = {
            executor.submit(_run_exact_ap_job, name, p, z): name
            for name, (p, z) in jobs.items()
        }
        for future in as_completed(futures):
            name = futures[future]
            result = future.result()
            results[name] = result
            print(
                f"exact AP {name}: {result['status']} "
                f"({result.get('runtime_seconds', 0.0):.1f}s)",
                flush=True,
            )
    return {name: results[name] for name in jobs}


def _build_ensemble_from_orbits(
    probabilities: torch.Tensor,
    prototypes: torch.Tensor,
) -> Ensemble:
    full_probabilities = expand_c4_orbit_masses((4.0 * probabilities).unsqueeze(0))[0]
    full_amplitudes = expand_c4_orbit_values(prototypes)
    declared_va = 2.0 * torch.sum(full_probabilities * full_amplitudes.abs().square())
    return Ensemble(
        probabilities=full_probabilities.unsqueeze(0),
        amplitudes=full_amplitudes.unsqueeze(0),
        declared_va=declared_va.reshape(1),
        raw_constellation=full_amplitudes,
        exact_csi_oracle=True,
        c4_symmetric=True,
    )


def _nearby_calibration() -> dict[str, Any]:
    nearby = _target_nearby_ensembles()
    cache_path = ROOT / "results" / f"training_surrogate_nearby_calibration_{ARTIFACT_DATE}.json"
    exact: dict[str, dict[str, Any]] = {}
    reused: list[str] = []
    # Reuse rows only when the cached exact worker output also passed the local
    # full-Z domain gate.  This rejects the stale pre-convention-fix combined
    # row while allowing a later run to reuse the corrected cache.
    if cache_path.exists():
        cached = json.loads(cache_path.read_text(encoding="utf-8"))
        for row in cached.get("rows", []):
            name = row.get("ensemble")
            if (
                name in nearby
                and row.get("full_Z_domain_check") == "PASS"
                and row.get("exact", {}).get("worker_rows")
            ):
                exact[name] = {
                    "name": name,
                    "status": "FULL_SUPPORT_CONVERGED",
                    "C": row["exact"]["C"],
                    "w": row["exact"]["w"],
                    "minimum_eigenvalue": row["exact"]["minimum_eigenvalue"],
                    "rows": row["exact"]["worker_rows"],
                }
                reused.append(name)
    jobs = {name: values for name, values in nearby.items() if name not in exact}
    exact.update(_run_exact_jobs(jobs))
    rows: list[dict[str, Any]] = []
    for name, (probabilities, prototypes) in nearby.items():
        result = exact[name]
        if result["status"] != "FULL_SUPPORT_CONVERGED":
            rows.append({"ensemble": name, "passes": False, "exact": result})
            continue
        surrogate = c4_training_surrogate(
            probabilities,
            prototypes,
            regularization=SURROGATE_REGULARIZATION,
        )
        c_exact = float(result["C"])
        w_exact = float(result["w"])
        c_surrogate = _float(surrogate.coherent_correlation)
        w_surrogate = _float(surrogate.w)
        local_domain = "PASS"
        try:
            ensemble = _build_ensemble_from_orbits(probabilities, prototypes)
            _holevo_from_source_moments(
                ensemble,
                torch.tensor([0.03], dtype=torch.float64),
                torch.tensor([0.02], dtype=torch.float64),
                coherent_correlation=torch.tensor([c_exact], dtype=torch.float64),
                w_raw=torch.tensor([w_exact], dtype=torch.float64),
                tau=None,
                tau_trace=ensemble.probabilities.sum(dim=-1),
                require_supported_symmetry=True,
                symmetry_tolerance=1.0e-8,
                physicality_tolerance=1.0e-10,
                diagnostics={"artifact_class": "EXACT_AP_SECURITY_ANCHOR"},
                z_grid_size=SECURITY_Z_GRID_SIZE,
                z_refinement_steps=SECURITY_Z_REFINEMENT_STEPS,
            )
        except Exception as error:  # local gate is deliberately fail-closed
            local_domain = f"FAIL:{type(error).__name__}"
        c_error = _relative(c_surrogate, c_exact)
        w_error = _relative(w_surrogate, w_exact)
        rows.append(
            {
                "ensemble": name,
                "artifact_class": "TRAINING_SURROGATE",
                "exact": {
                    "C": result["C"],
                    "w": result["w"],
                    "minimum_eigenvalue": result["minimum_eigenvalue"],
                    "worker_rows": result["rows"],
                },
                "surrogate": {
                    "C": c_surrogate,
                    "w": w_surrogate,
                    **surrogate.diagnostics,
                },
                "relative_error": {"C": c_error, "w": w_error},
                "full_Z_domain_check": local_domain,
                "passes": (
                    c_error <= 0.02
                    and w_error <= 0.10
                    and local_domain == "PASS"
                ),
            }
        )
    return {
        "status": "NEARBY_SURROGATE_PASS" if all(row["passes"] for row in rows) else "NEARBY_SURROGATE_FAIL",
        "artifact_class": "TRAINING_SURROGATE",
        "acceptance": {
            "C_relative_error_max": 0.02,
            "w_relative_error_max": 0.10,
            "full_Z_domain": "one deterministic active state at T=0.03, epsilon_base=0.02",
        },
        "rows": rows,
        "provenance": {
            "corrected_worker": str(CORRECTED_WORKER.relative_to(ROOT)),
            "corrected_worker_sha256": _hash_file(CORRECTED_WORKER),
            "precision_ladder_decimal_digits": list(AP_DIGITS),
            "phase_disabled": True,
            "reused_exact_rows": reused,
            "reused_artifact": (str(cache_path.relative_to(ROOT)) if reused else None),
            "reused_artifact_sha256": (_hash_file(cache_path) if reused else None),
        },
    }


def _calibrate_surrogate() -> dict[str, Any]:
    if not TANGENT_ARTIFACT.exists():
        raise AnalysisBlocked("SURROGATE_OPTIMIZATION_BLOCKED: tangent artifact is missing")
    tangent_artifact = json.loads(TANGENT_ARTIFACT.read_text(encoding="utf-8"))
    references: dict[str, tuple[float, float, float]] = {}
    ps = tangent_artifact["ps_reference"]["precision_800"]
    references["ps"] = (float(ps["dC"]), float(ps["dw"]), float(ps["dJ"]))
    for family in ("gs_real", "gs_imag", "va"):
        row = tangent_artifact["directions"][family]["central"]
        references[family] = (float(row["dC"]), float(row["dw"]), float(row["dJ"]))

    acceptance = {
        "derivative_sign_required": True,
        "directional_relative_error_max": 0.10,
        "reference_C_relative_error_max": 0.01,
        "reference_w_relative_error_max": 0.05,
        "selection_rule": (
            "choose the stability-first 1e-10 shift after comparing the bounded set; "
            "do not use surrogate values for security"
        ),
    }
    candidate_records: list[dict[str, Any]] = []
    for regularization in SURROGATE_CANDIDATES:
        rows: list[dict[str, Any]] = []
        finite = True
        try:
            for family in ("ps", "gs_real", "gs_imag", "va"):
                p, z, dp, dz = _target_directional_inputs(family)
                p_tensor = torch.tensor(p, dtype=torch.float64)
                z_tensor = torch.tensor(z, dtype=torch.complex128)
                dp_tensor = torch.tensor(dp, dtype=torch.float64)
                dz_tensor = torch.tensor(dz, dtype=torch.complex128)
                theta = torch.zeros((), dtype=torch.float64, requires_grad=True)
                result = c4_training_surrogate(
                    p_tensor + theta * dp_tensor,
                    z_tensor + theta * dz_tensor,
                    regularization=regularization,
                )
                d_c = torch.autograd.grad(
                    result.coherent_correlation, theta, retain_graph=True
                )[0]
                d_w = torch.autograd.grad(result.w, theta)[0]
                d_j = 1.7 * d_c - 0.8 * d_w
                values = (_float(d_c), _float(d_w), _float(d_j))
                reference = references[family]
                errors = {
                    "dC": _relative(values[0], reference[0]),
                    "dw": _relative(values[1], reference[1]),
                    "dJ": _relative(values[2], reference[2]),
                }
                sign_pass = all(
                    math.copysign(1.0, values[index])
                    == math.copysign(1.0, reference[index])
                    for index in range(3)
                )
                rows.append(
                    {
                        "direction": family,
                        "exact": {"dC": reference[0], "dw": reference[1], "dJ": reference[2]},
                        "surrogate": {"dC": values[0], "dw": values[1], "dJ": values[2]},
                        "relative_error": errors,
                        "sign_pass": sign_pass,
                        "passes": sign_pass and max(errors.values()) <= acceptance["directional_relative_error_max"],
                    }
                )
        except Exception as error:
            finite = False
            rows.append({"direction": "all", "error": f"{type(error).__name__}: {error}", "passes": False})

        p, z, _, _ = _target_directional_inputs("ps")
        reference_result = c4_training_surrogate(
            torch.tensor(p, dtype=torch.float64),
            torch.tensor(z, dtype=torch.complex128),
            regularization=regularization,
        )
        reference_c = _float(reference_result.coherent_correlation)
        reference_w = _float(reference_result.w)
        c_error = _relative(reference_c, CORRECTED_C)
        w_error = _relative(reference_w, CORRECTED_W)
        passes = (
            finite
            and len(rows) == 4
            and all(row.get("passes", False) for row in rows)
            and c_error <= acceptance["reference_C_relative_error_max"]
            and w_error <= acceptance["reference_w_relative_error_max"]
        )
        candidate_records.append(
            {
                "regularization": regularization,
                "reference": {
                    "C": reference_c,
                    "w": reference_w,
                    "C_relative_error": c_error,
                    "w_relative_error": w_error,
                    **reference_result.diagnostics,
                },
                "directions": rows,
                "passes": passes,
            }
        )

    selected = next(
        (row for row in candidate_records if row["regularization"] == SURROGATE_REGULARIZATION and row["passes"]),
        None,
    )
    if selected is None:
        return {
            "status": "SURROGATE_OPTIMIZATION_BLOCKED",
            "artifact_class": "TRAINING_SURROGATE",
            "acceptance": acceptance,
            "candidates": candidate_records,
            "tangent_artifact": str(TANGENT_ARTIFACT.relative_to(ROOT)),
            "tangent_artifact_sha256": _hash_file(TANGENT_ARTIFACT),
        }
    return {
        "status": "TRAINING_SURROGATE_CALIBRATED",
        "artifact_class": "TRAINING_SURROGATE",
        "selected_regularization": SURROGATE_REGULARIZATION,
        "acceptance": acceptance,
        "candidates": candidate_records,
        "selected": selected,
        "tangent_artifact": str(TANGENT_ARTIFACT.relative_to(ROOT)),
        "tangent_artifact_sha256": _hash_file(TANGENT_ARTIFACT),
        "corrected_reference": {
            "C": CORRECTED_C_TEXT,
            "w": CORRECTED_W_TEXT,
        },
    }


def _analysis_grid() -> dict[str, Any]:
    transmittance, epsilon_base, metadata = existing_case._sample_case("D")
    active = transmittance > 0.0
    active_t = np.asarray(transmittance[active], dtype=np.float64)
    active_e = np.asarray(epsilon_base[active], dtype=np.float64)
    if active_t.size < GRID_T_BINS or active_e.size < GRID_EPSILON_BINS:
        raise AnalysisBlocked("analysis channel grid has too few active states")
    t_order = np.argsort(active_t, kind="mergesort")
    e_order = np.argsort(active_e, kind="mergesort")
    t_groups = np.array_split(t_order, GRID_T_BINS)
    e_groups = np.array_split(e_order, GRID_EPSILON_BINS)
    active_count = int(active_t.size)
    total_count = int(transmittance.size)
    active_mass = active_count / total_count
    points: list[dict[str, Any]] = []
    index = 0
    for t_bin, t_group in enumerate(t_groups):
        t_value = float(np.median(active_t[t_group]))
        t_weight = len(t_group) / total_count
        for e_bin, e_group in enumerate(e_groups):
            e_value = float(np.median(active_e[e_group]))
            weight = t_weight * len(e_group) / active_count
            points.append(
                {
                    "index": index,
                    "active": True,
                    "weight": float(weight),
                    "T": t_value,
                    "epsilon_base": e_value,
                    "epsilon_total": e_value,
                    "T_bin": t_bin,
                    "epsilon_bin": e_bin,
                }
            )
            index += 1
    outage_mass = float(np.mean(~active))
    outage_epsilon = float(np.median(epsilon_base))
    points.append(
        {
            "index": index,
            "active": False,
            "weight": outage_mass,
            "T": 0.0,
            "epsilon_base": outage_epsilon,
            "epsilon_total": outage_epsilon,
            "outage_rule": "T=0 -> no policy, MI, Holevo; raw K=0",
        }
    )
    if abs(sum(point["weight"] for point in points) - 1.0) > 1.0e-12:
        raise FloatingPointError("analysis grid weights do not sum to one")
    active_points = [point for point in points if point["active"]]
    anchor_quantiles = np.linspace(0.02, 0.98, ANCHOR_COUNT)
    anchor_t = np.quantile(active_t, anchor_quantiles)
    anchor_points = [
        {
            "index": index,
            "weight": active_mass / ANCHOR_COUNT,
            "T": float(value),
            "epsilon_base": float(np.median(active_e)),
            "epsilon_total": float(np.median(active_e)),
            "quantile": float(quantile),
            "active": True,
        }
        for index, (quantile, value) in enumerate(zip(anchor_quantiles, anchor_t))
    ]
    source = {
        "case": "D",
        "sample_count": total_count,
        "channel_seed": existing_case.CHANNEL_SEED,
        "epsilon_base_seed": existing_case.EPSILON_SEED,
        "transmittance_sha256": metadata["transmittance_sha256"],
        "epsilon_base_sha256": metadata["epsilon_base_sha256"],
        "realization_sha256": metadata["realization_sha256"],
        "channel_config": metadata["channel_config"],
        "channel_metadata": metadata["channel"],
    }
    payload = {
        "source": source,
        "weighting": "equal probability bins in T crossed with equal probability bins in independent epsilon_base",
        "active_count": active_count,
        "active_mass": active_mass,
        "outage_count": total_count - active_count,
        "outage_mass": outage_mass,
        "points": points,
        "anchor_points": anchor_points,
        "phase_disabled": True,
        "c_phi": PHASE_COEFFICIENT,
        "epsilon_total_definition": EPSILON_TOTAL_DEFINITION,
    }
    payload["grid_sha256"] = _canonical_hash(payload)
    return payload


def _initialize_transmitter(mode: str, seed: int) -> JointTransmitter:
    torch.manual_seed(seed)
    if mode in {"uniform", "mb"}:
        transmitter = JointTransmitter(
            "uniform" if mode == "uniform" else "optimized_mb",
            fixed_va=1.0,
            nu_mb=MB_NU,
            n_peak_photons=N_PEAK_PHOTONS,
        )
    else:
        transmitter = JointTransmitter(
            mode,
            fixed_va=1.0 if mode not in {"va", "ps_va", "full"} else None,
            v_min=V_MIN if mode in {"va", "ps_va", "full"} else None,
            v_max=V_MAX if mode in {"va", "ps_va", "full"} else None,
            n_peak_photons=N_PEAK_PHOTONS,
        )
    if transmitter.va_network is not None:
        with torch.no_grad():
            for layer in transmitter.va_network.network:
                if isinstance(layer, torch.nn.Linear):
                    layer.weight.zero_()
                    layer.bias.zero_()
            target_unit = math.log(1.0 / V_MIN) / math.log(V_MAX / V_MIN)
            transmitter.va_network.network[-1].bias.fill_(
                math.log(target_unit / (1.0 - target_unit))
            )
    return transmitter


def _unique_state_count(amplitudes: torch.Tensor, row: int) -> int:
    return len(
        {
            (complex(value).real.hex(), complex(value).imag.hex())
            for value in amplitudes[row].detach().cpu().tolist()
        }
    )


def _training_metrics(
    transmitter: JointTransmitter,
    evaluation: dict[str, Any],
    gradient_norm: float | None,
    dual: float,
    violation: float,
    objective: float,
    step: int,
) -> dict[str, Any]:
    ensemble = evaluation["ensemble"]
    probabilities = ensemble.probabilities.detach()
    va = ensemble.declared_va.detach()
    metrics: dict[str, Any] = {
        "step": step,
        "objective_weighted_raw_K_estimate": objective,
        "mean_raw_K_estimate": float(evaluation["raw_K"].detach().mean()),
        "mean_C_surrogate": float(evaluation["C"].detach().mean()),
        "mean_w_surrogate": float(evaluation["w"].detach().mean()),
        "gradient_norm_pre_clip": gradient_norm,
        "energy_dual": dual,
        "energy_violation_mean_V_A_minus_budget": violation,
        "mean_V_A": float(va.mean()),
        "min_V_A": float(va.min()),
        "max_V_A": float(va.max()),
        "min_probability": float(probabilities.min()),
        "maximum_probability_sum_error": float((probabilities.sum(dim=-1) - 1.0).abs().max()),
        "maximum_symbol_energy": float(ensemble.amplitudes.detach().abs().square().max()),
        "unique_state_count_min": min(
            _unique_state_count(ensemble.amplitudes, row)
            for row in range(ensemble.amplitudes.shape[0])
        ),
        "finite": bool(
            torch.isfinite(ensemble.probabilities).all()
            and torch.isfinite(ensemble.amplitudes.real).all()
            and torch.isfinite(ensemble.amplitudes.imag).all()
            and torch.isfinite(ensemble.declared_va).all()
        ),
    }
    if transmitter.gs_model is not None:
        metrics["GS_relative_prototype_rms"] = float(
            transmitter.gs_model.relative_prototypes().detach().abs().square().mean()
        )
    else:
        metrics["GS_relative_prototype_rms"] = None
    return metrics


def _candidate_payload(
    transmitter: JointTransmitter,
    grid_points: list[dict[str, Any]],
    evaluation: dict[str, Any],
) -> dict[str, Any]:
    ensemble = evaluation["ensemble"]
    rows: list[dict[str, Any]] = []
    for row, point in enumerate(grid_points):
        rows.append(
            {
                "grid_index": point["index"],
                "T": point["T"],
                "epsilon_base": point["epsilon_base"],
                "weight": point["weight"],
                "V_A": float(ensemble.declared_va[row].detach()),
                "C_surrogate": float(evaluation["C"][row].detach()),
                "w_surrogate": float(evaluation["w"][row].detach()),
                "I_AB": float(evaluation["I_AB"][row].detach()),
                "chi_BE_search_proxy": float(evaluation["chi_BE"][row].detach()),
                "raw_K_search_proxy": float(evaluation["raw_K"][row].detach()),
                "probabilities": [float(value) for value in ensemble.probabilities[row].detach().tolist()],
                "amplitudes": [
                    [float(complex(value).real), float(complex(value).imag)]
                    for value in ensemble.amplitudes[row].detach().tolist()
                ],
            }
        )
    return {
        "artifact_class": "ANALYSIS_ESTIMATE",
        "mode": transmitter.mode,
        "rows": rows,
        "n_peak_photons": N_PEAK_PHOTONS,
        "phase_disabled": True,
        "c_phi": PHASE_COEFFICIENT,
        "epsilon_total_definition": EPSILON_TOTAL_DEFINITION,
        "source_moment_marker": "TRAINING_SURROGATE_ONLY",
        "security_objective_marker": "OPTIMIZATION/ANALYSIS ESTIMATE; not full-Z security",
    }


def _run_method(
    mode: str,
    grid: dict[str, Any],
    standard_noise: torch.Tensor,
    *,
    seed: int,
) -> tuple[JointTransmitter, dict[str, Any], dict[str, Any]]:
    transmitter = _initialize_transmitter(mode, seed)
    points = [point for point in grid["points"] if point["active"]]
    transmittance = torch.tensor([point["T"] for point in points], dtype=torch.float64)
    epsilon = torch.tensor([point["epsilon_base"] for point in points], dtype=torch.float64)
    weights = torch.tensor([point["weight"] for point in points], dtype=torch.float64)
    initial = _evaluate_surrogate(transmitter, transmittance, epsilon, standard_noise)
    if mode in {"uniform", "mb"}:
        final = _evaluate_surrogate(transmitter, transmittance, epsilon, standard_noise)
        history = {
            "artifact_class": "TRAINING_SURROGATE",
            "mode": mode,
            "status": "FIXED_BASELINE_NOT_OPTIMIZED",
            "steps": 0,
            "smoke": {"status": "NOT_APPLICABLE_FIXED_BASELINE"},
            "records": [],
        }
        return transmitter, final, history

    learning_rate = {
        "ps": 3.0e-4,
        "va": 1.0e-4,
        "ps_va": 3.0e-4,
        "full": 1.0e-4,
    }[mode]
    optimizer = torch.optim.Adam(transmitter.parameters(), lr=learning_rate)
    dual = 0.0
    records: list[dict[str, Any]] = []
    initial_objective = float(torch.sum(weights * initial["raw_K"].detach()))
    smoke_status = "NOT_REACHED"
    for step in range(1, ANALYSIS_STEPS + 1):
        optimizer.zero_grad(set_to_none=True)
        evaluation = _evaluate_surrogate(transmitter, transmittance, epsilon, standard_noise)
        objective = torch.sum(weights * evaluation["raw_K"])
        violation_tensor = evaluation["ensemble"].declared_va.mean() - VA_BUDGET
        loss = -objective + dual * violation_tensor
        if not bool(torch.isfinite(loss)):
            raise AnalysisBlocked(f"SMOKE_OPTIMIZATION_BLOCKED:{mode}:nonfinite loss")
        loss.backward()
        parameters = [parameter for parameter in transmitter.parameters() if parameter.grad is not None]
        if not parameters or any(not bool(torch.isfinite(parameter.grad).all()) for parameter in parameters):
            raise AnalysisBlocked(f"SMOKE_OPTIMIZATION_BLOCKED:{mode}:nonfinite gradient")
        gradient_norm = float(torch.sqrt(sum(torch.sum(parameter.grad.detach().square()) for parameter in parameters)))
        torch.nn.utils.clip_grad_norm_(parameters, 1.0)
        optimizer.step()
        try:
            transmitter(transmittance, epsilon)
        except PeakPhotonConstraintViolation as error:
            raise AnalysisBlocked(f"SMOKE_OPTIMIZATION_BLOCKED:{mode}:peak-domain violation") from error
        violation = float(violation_tensor.detach())
        dual = max(0.0, dual + 1.0e-2 * violation)
        records.append(
            _training_metrics(
                transmitter,
                evaluation,
                gradient_norm,
                dual,
                violation,
                float(objective.detach()),
                step,
            )
        )
        if step == SMOKE_STEPS:
            first_window = [record["objective_weighted_raw_K_estimate"] for record in records[:5]]
            last_window = [record["objective_weighted_raw_K_estimate"] for record in records[-5:]]
            smoke_ok = (
                all(record["finite"] for record in records)
                and min(record["min_V_A"] for record in records) >= V_MIN - 1.0e-10
                and max(record["max_V_A"] for record in records) <= V_MAX + 1.0e-10
                and min(record["min_probability"] for record in records) > 0.0
                and min(record["unique_state_count_min"] for record in records) == 256
                and np.mean(last_window) > np.mean(first_window) - 1.0e-8
            )
            smoke_status = "PASS" if smoke_ok else "FAIL"
            if not smoke_ok:
                raise AnalysisBlocked(f"SMOKE_OPTIMIZATION_BLOCKED:{mode}:stability gate")
            checkpoint = ROOT / "results" / f"analysis_checkpoint_{mode}_{ARTIFACT_DATE}_step_{step}.pt"
            torch.save(
                {"artifact_class": "TRAINING_SURROGATE", "mode": mode, "step": step, "state_dict": transmitter.state_dict()},
                checkpoint,
            )
    final = _evaluate_surrogate(transmitter, transmittance, epsilon, standard_noise)
    final_objective = float(torch.sum(weights * final["raw_K"].detach()))
    history = {
        "artifact_class": "TRAINING_SURROGATE",
        "mode": mode,
        "status": "ANALYSIS_OPTIMIZED",
        "steps": ANALYSIS_STEPS,
        "smoke": {"status": smoke_status, "steps": SMOKE_STEPS},
        "initial_objective_weighted_raw_K_estimate": initial_objective,
        "final_objective_weighted_raw_K_estimate": final_objective,
        "objective_change": final_objective - initial_objective,
        "records": records,
        "checkpoint": str(
            (ROOT / "results" / f"analysis_checkpoint_{mode}_{ARTIFACT_DATE}_step_{ANALYSIS_STEPS}.pt").relative_to(ROOT)
        ),
    }
    final_checkpoint = ROOT / "results" / f"analysis_checkpoint_{mode}_{ARTIFACT_DATE}_step_{ANALYSIS_STEPS}.pt"
    torch.save(
        {"artifact_class": "TRAINING_SURROGATE", "mode": mode, "step": ANALYSIS_STEPS, "state_dict": transmitter.state_dict()},
        final_checkpoint,
    )
    return transmitter, final, history


def _security_rows(
    transmitter: JointTransmitter,
    transmittance: torch.Tensor,
    epsilon: torch.Tensor,
    standard_noise: torch.Tensor,
    correlations: torch.Tensor,
    w_raw: torch.Tensor,
    *,
    surrogate: bool,
) -> dict[str, Any]:
    ensemble = transmitter(transmittance, epsilon)
    mi = discrete_mutual_information(
        ensemble,
        transmittance,
        epsilon,
        noise_samples_per_symbol=standard_noise.shape[-1],
        standard_noise_samples=standard_noise,
        noise_sample_chunk_size=standard_noise.shape[-1],
    )
    holevo = _holevo_from_moments(
        ensemble,
        transmittance,
        epsilon,
        correlations,
        w_raw,
        analysis_grid=False,
    )
    raw = BETA * mi - holevo.chi_be
    locations = list(holevo.diagnostics["maximizing_location"])
    return {
        "artifact_class": "ANALYSIS_ESTIMATE" if surrogate else "EXACT_AP_SECURITY_ANCHOR",
        "surrogate_source_moments": surrogate,
        "rows": [
            {
                "T": float(transmittance[row]),
                "epsilon_base": float(epsilon[row]),
                "C": float(correlations[row]),
                "w": float(w_raw[row]),
                "I_AB": float(mi[row]),
                "chi_BE": float(holevo.chi_be[row]),
                "raw_K": float(raw[row]),
                "Z_L": float(holevo.diagnostics["Z_L"][row]),
                "Z_U": float(holevo.diagnostics["Z_U"][row]),
                "Z_star": float(holevo.z[row]),
                "maximizing_location": locations[row],
                "security_domain_valid": bool(holevo.diagnostics["security_domain_valid"][row]),
            }
            for row in range(transmittance.shape[0])
        ],
        "solver": {
            "z_grid_size": SECURITY_Z_GRID_SIZE,
            "z_refinement_steps": SECURITY_Z_REFINEMENT_STEPS,
            "method": "fixed_grid_all_cells_golden_section",
        },
    }


def _search_estimate_rows(
    evaluation: dict[str, Any],
    transmittance: torch.Tensor,
    epsilon: torch.Tensor,
) -> dict[str, Any]:
    """Serialize the smooth search proxy without calling it exact security."""

    return {
        "artifact_class": "ANALYSIS_ESTIMATE",
        "surrogate_source_moments": True,
        "security_objective": "smooth_bounded_training_security_proxy",
        "rows": [
            {
                "T": float(transmittance[row]),
                "epsilon_base": float(epsilon[row]),
                "C": float(evaluation["C"][row].detach()),
                "w": float(evaluation["w"][row].detach()),
                "I_AB": float(evaluation["I_AB"][row].detach()),
                "chi_BE": float(evaluation["chi_BE"][row].detach()),
                "raw_K": float(evaluation["raw_K"][row].detach()),
            }
            for row in range(transmittance.shape[0])
        ],
    }


def _serialize_candidate_ensembles(
    candidate_ensembles: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    return {
        "artifact_class": "ANALYSIS_ESTIMATE",
        "methods": candidate_ensembles,
        "phase_disabled": True,
        "c_phi": PHASE_COEFFICIENT,
        "epsilon_total_definition": EPSILON_TOTAL_DEFINITION,
    }


def _fmt(value: float, digits: int = 4) -> str:
    if not math.isfinite(float(value)):
        return "nan"
    value = float(value)
    if value == 0.0:
        return "0"
    if abs(value) >= 1.0e4 or abs(value) < 1.0e-3:
        return f"{value:.{max(2, digits - 1)}e}"
    return f"{value:.{digits}f}"


def _svg_text(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _svg_document(content: str, width: int, height: int, title: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">\n'
        f'<title>{_svg_text(title)}</title>\n'
        '<style>text{font-family:Arial,Helvetica,sans-serif;fill:#222} '
        '.small{font-size:12px}.axis{font-size:13px}.title{font-size:18px;font-weight:600} '
        '.tick{font-size:11px}.grid{stroke:#dddddd;stroke-width:1} '
        '.axisline{stroke:#333333;stroke-width:1.2}.legend{font-size:12px}</style>\n'
        f'{content}</svg>\n'
    )


def _write_svg(path: Path, content: str, width: int, height: int, title: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_svg_document(content, width, height, title), encoding="utf-8")
    return str(path.relative_to(ROOT))


def _line_figure(
    path: Path,
    title: str,
    subtitle: str,
    xlabel: str,
    ylabel: str,
    series: list[dict[str, Any]],
    *,
    x_min: float = 0.0,
    x_max: float | None = None,
    y_min: float | None = None,
    y_max: float | None = None,
) -> str:
    width, height = 920, 600
    left, top, plot_width, plot_height = 90, 75, 750, 410
    all_x = [float(value) for row in series for value in row.get("x", [])]
    all_y = [float(value) for row in series for value in row.get("y", [])]
    x_max = max(all_x) * 1.05 if x_max is None else x_max
    x_max = max(x_max, x_min + 1.0e-9)
    if y_min is None:
        y_min = min(all_y + [0.0])
    if y_max is None:
        y_max = max(all_y + [0.0])
    span = max(y_max - y_min, 1.0e-6)
    y_min -= 0.08 * span
    y_max += 0.08 * span

    def sx(value: float) -> float:
        return left + (float(value) - x_min) / (x_max - x_min) * plot_width

    def sy(value: float) -> float:
        return top + plot_height - (float(value) - y_min) / (y_max - y_min) * plot_height

    body = [
        f'<text class="title" x="{left}" y="30">{_svg_text(title)}</text>',
        f'<text class="small" x="{left}" y="51">{_svg_text(subtitle)}</text>',
    ]
    for fraction in np.linspace(0.0, 1.0, 6):
        y = top + plot_height * (1.0 - fraction)
        value = y_min + fraction * (y_max - y_min)
        body.append(f'<line class="grid" x1="{left}" y1="{y:.2f}" x2="{left + plot_width}" y2="{y:.2f}"/>')
        body.append(f'<text class="tick" text-anchor="end" x="{left - 8}" y="{y + 4:.2f}">{_svg_text(_fmt(value, 3))}</text>')
    for fraction in np.linspace(0.0, 1.0, 6):
        x = left + plot_width * fraction
        value = x_min + fraction * (x_max - x_min)
        body.append(f'<line class="grid" x1="{x:.2f}" y1="{top}" x2="{x:.2f}" y2="{top + plot_height}"/>')
        body.append(f'<text class="tick" text-anchor="middle" x="{x:.2f}" y="{top + plot_height + 22}">{_svg_text(_fmt(value, 3))}</text>')
    body.extend(
        (
            f'<line class="axisline" x1="{left}" y1="{top + plot_height}" x2="{left + plot_width}" y2="{top + plot_height}"/>',
            f'<line class="axisline" x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_height}"/>',
            f'<text class="axis" text-anchor="middle" x="{left + plot_width / 2}" y="{height - 45}">{_svg_text(xlabel)}</text>',
            f'<text class="axis" text-anchor="middle" transform="translate(22 {top + plot_height / 2}) rotate(-90)">{_svg_text(ylabel)}</text>',
        )
    )
    legend_y = top + plot_height + 52
    legend_x = left
    for index, row in enumerate(series):
        color = row.get("color", "#333333")
        dash = ' stroke-dasharray="7 5"' if row.get("dash") else ""
        x_values = row.get("x", [])
        y_values = row.get("y", [])
        if len(x_values) >= 2:
            points = " ".join(f"{sx(x):.2f},{sy(y):.2f}" for x, y in zip(x_values, y_values))
            body.append(f'<polyline fill="none" stroke="{color}" stroke-width="2"{dash} points="{points}"/>')
        for x, y in zip(x_values, y_values):
            radius = 4 if row.get("marker", True) else 0
            if radius:
                body.append(f'<circle cx="{sx(x):.2f}" cy="{sy(y):.2f}" r="{radius}" fill="white" stroke="{color}" stroke-width="2"/>')
        lx = legend_x + (index % 3) * 245
        ly = legend_y + (index // 3) * 20
        body.append(f'<line x1="{lx}" y1="{ly - 4}" x2="{lx + 24}" y2="{ly - 4}" stroke="{color}" stroke-width="2"{dash}/>')
        body.append(f'<text class="legend" x="{lx + 30}" y="{ly}">{_svg_text(row["label"])}</text>')
    return _write_svg(path, "\n".join(body), width, height, title)


def _bar_figure(path: Path, title: str, subtitle: str, values: list[dict[str, Any]]) -> str:
    width, height = 960, 600
    left, top, plot_width, plot_height = 90, 75, 800, 390
    ymin = min([0.0] + [float(row["value"]) for row in values])
    ymax = max([0.0] + [float(row["value"]) for row in values])
    span = max(ymax - ymin, 1.0e-6)
    ymin -= 0.12 * span
    ymax += 0.12 * span
    baseline = top + plot_height - (0.0 - ymin) / (ymax - ymin) * plot_height
    bar_width = plot_width / max(1, len(values)) * 0.65

    def sy(value: float) -> float:
        return top + plot_height - (float(value) - ymin) / (ymax - ymin) * plot_height

    body = [
        f'<text class="title" x="{left}" y="30">{_svg_text(title)}</text>',
        f'<text class="small" x="{left}" y="51">{_svg_text(subtitle)}</text>',
    ]
    for fraction in np.linspace(0.0, 1.0, 6):
        y = top + plot_height * (1.0 - fraction)
        value = ymin + fraction * (ymax - ymin)
        body.append(f'<line class="grid" x1="{left}" y1="{y:.2f}" x2="{left + plot_width}" y2="{y:.2f}"/>')
        body.append(f'<text class="tick" text-anchor="end" x="{left - 8}" y="{y + 4:.2f}">{_svg_text(_fmt(value, 3))}</text>')
    body.append(f'<line class="axisline" x1="{left}" y1="{baseline:.2f}" x2="{left + plot_width}" y2="{baseline:.2f}"/>')
    for index, row in enumerate(values):
        center = left + (index + 0.5) * plot_width / len(values)
        value = float(row["value"])
        y = sy(value)
        y0 = baseline
        rect_y = min(y, y0)
        rect_h = max(abs(y - y0), 1.0)
        body.append(f'<rect x="{center - bar_width / 2:.2f}" y="{rect_y:.2f}" width="{bar_width:.2f}" height="{rect_h:.2f}" fill="{row["color"]}" opacity="0.82"/>')
        body.append(f'<text class="tick" text-anchor="middle" x="{center:.2f}" y="{top + plot_height + 24}">{_svg_text(row["label"])}</text>')
        body.append(f'<text class="tick" text-anchor="middle" x="{center:.2f}" y="{rect_y - 6 if value >= 0 else rect_y + rect_h + 14:.2f}">{_svg_text(_fmt(value, 4))}</text>')
    body.extend(
        (
            f'<line class="axisline" x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_height}"/>',
            f'<text class="axis" text-anchor="middle" x="{left + plot_width / 2}" y="{height - 38}">method</text>',
            f'<text class="axis" text-anchor="middle" transform="translate(22 {top + plot_height / 2}) rotate(-90)">weighted raw K (bits/use)</text>',
        )
    )
    return _write_svg(path, "\n".join(body), width, height, title)


def _table_figure(path: Path, title: str, subtitle: str, rows: list[dict[str, Any]]) -> str:
    width = 1120
    row_height = 25
    height = 115 + row_height * max(1, len(rows))
    left, top = 35, 78
    columns = [
        (0, "method / anchor"),
        (190, "T"),
        (275, "C rel.err"),
        (390, "w rel.err"),
        (505, "K exact"),
        (620, "K surrogate"),
        (770, "rank"),
    ]
    body = [
        f'<text class="title" x="{left}" y="30">{_svg_text(title)}</text>',
        f'<text class="small" x="{left}" y="51">{_svg_text(subtitle)}</text>',
        '<rect x="25" y="60" width="1070" height="28" fill="#eeeeee"/>',
    ]
    for offset, label in columns:
        body.append(f'<text class="legend" x="{left + offset}" y="79">{_svg_text(label)}</text>')
    for index, row in enumerate(rows):
        y = top + 28 + index * row_height
        if index % 2:
            body.append(f'<rect x="25" y="{y - 17}" width="1070" height="{row_height}" fill="#fafafa"/>')
        values = [
            row["label"],
            _fmt(row["T"], 4),
            _fmt(row["C_relative_error"], 3),
            _fmt(row["w_relative_error"], 3),
            _fmt(row["K_exact"], 4),
            _fmt(row["K_surrogate"], 4),
            "PASS" if row["rank_consistent"] else "REVERSAL",
        ]
        for (offset, _), value in zip(columns, values):
            body.append(f'<text class="small" x="{left + offset}" y="{y}">{_svg_text(value)}</text>')
    return _write_svg(path, "\n".join(body), width, height, title)


def _scatter_figure(path: Path, panels: list[dict[str, Any]]) -> str:
    width, height = 1120, 530
    panel_width, panel_height = 330, 385
    left, top = 30, 85
    body = [
        '<text class="title" x="30" y="30">Full constellation snapshots</text>',
        '<text class="small" x="30" y="53">Analysis-grade policy output; marker area is proportional to learned symbol probability; no monotonic geometry assumed</text>',
    ]
    for panel_index, panel in enumerate(panels):
        px = left + panel_index * (panel_width + 25)
        py = top
        plot_left, plot_top = px + 42, py + 20
        plot_w, plot_h = panel_width - 62, panel_height - 55
        amplitudes = np.asarray(panel["amplitudes"], dtype=np.float64)
        probabilities = np.asarray(panel["probabilities"], dtype=np.float64)
        x_values, y_values = amplitudes[:, 0], amplitudes[:, 1]
        x_span = max(float(np.ptp(x_values)), 1.0e-6)
        y_span = max(float(np.ptp(y_values)), 1.0e-6)
        xmin, xmax = float(x_values.min()) - 0.08 * x_span, float(x_values.max()) + 0.08 * x_span
        ymin, ymax = float(y_values.min()) - 0.08 * y_span, float(y_values.max()) + 0.08 * y_span

        def sx(value: float) -> float:
            return plot_left + (value - xmin) / (xmax - xmin) * plot_w

        def sy(value: float) -> float:
            return plot_top + plot_h - (value - ymin) / (ymax - ymin) * plot_h

        body.append(f'<text class="legend" x="{px + 8}" y="{py + 5}">{_svg_text(panel["label"])}</text>')
        body.append(f'<rect x="{plot_left}" y="{plot_top}" width="{plot_w}" height="{plot_h}" fill="white" stroke="#333"/>')
        body.append(f'<line class="grid" x1="{sx(0):.2f}" y1="{plot_top}" x2="{sx(0):.2f}" y2="{plot_top + plot_h}"/>')
        body.append(f'<line class="grid" x1="{plot_left}" y1="{sy(0):.2f}" x2="{plot_left + plot_w}" y2="{sy(0):.2f}"/>')
        maximum = float(probabilities.max())
        for (x_value, y_value), probability in zip(amplitudes, probabilities):
            radius = 1.5 + 5.5 * math.sqrt(float(probability) / maximum)
            body.append(f'<circle cx="{sx(x_value):.2f}" cy="{sy(y_value):.2f}" r="{radius:.2f}" fill="#222" fill-opacity="0.55"/>')
        body.append(f'<text class="tick" text-anchor="middle" x="{plot_left + plot_w / 2}" y="{plot_top + plot_h + 22}">Re(alpha)</text>')
        body.append(f'<text class="tick" text-anchor="middle" transform="translate({px + 15} {plot_top + plot_h / 2}) rotate(-90)">Im(alpha)</text>')
        body.append(f'<text class="tick" x="{plot_left}" y="{plot_top + plot_h + 40}">T={_fmt(panel["T"], 4)}, V_A={_fmt(panel["V_A"], 3)}</text>')
    return _write_svg(path, "\n".join(body), width, height, "Full constellation snapshots")


def _render_figures(
    grid: dict[str, Any],
    candidates: dict[str, dict[str, Any]],
    grid_security_exact: dict[str, dict[str, Any]],
    grid_security_surrogate: dict[str, dict[str, Any]],
    anchor_security: dict[str, dict[str, Any]],
    summaries: dict[str, Any],
    error_rows: list[dict[str, Any]],
) -> dict[str, str]:
    figure_dir = ROOT / "figures" / "analysis"
    outage = {"x": [0.0], "y": [0.0], "label": "AoA outage: K=0", "color": "#777777", "marker": True}
    figure1_series = []
    for mode in ("uniform", "mb"):
        rows = grid_security_exact[mode]["rows"]
        figure1_series.append(
            {
                "x": [0.0] + [row["T"] for row in rows],
                "y": [0.0] + [row["raw_K"] for row in rows],
                "label": METHOD_LABEL[mode] + " exact grid",
                "color": METHOD_COLOR[mode],
                "marker": True,
            }
        )
    full_rows = anchor_security["full"]["exact"]["rows"]
    figure1_series.append(
        {
            "x": [0.0] + [row["T"] for row in full_rows],
            "y": [0.0] + [row["raw_K"] for row in full_rows],
            "label": "Full exact AP anchors / guide",
            "color": METHOD_COLOR["full"],
            "dash": True,
            "marker": True,
        }
    )
    figure1_series.append(outage)
    paths = {
        "figure_1": _line_figure(
            figure_dir / "figure_1_statewise_k_vs_t.svg",
            "Statewise raw secret-key rate versus T",
            "PHASE_DISABLED_ANALYSIS_SCENARIO; exact AP/full-Z anchors are markers, connecting lines are guides",
            "power transmittance T",
            "raw K (bits/use)",
            figure1_series,
            x_max=max(row["T"] for row in full_rows) * 1.08,
        )
    }

    for mode in ("va", "ps_va", "full"):
        rows = candidates[mode]["rows"]
        paths.setdefault("figure_2_series", [])
        paths["figure_2_series"].append(
            {
                "x": [row["T"] for row in rows],
                "y": [row["V_A"] for row in rows],
                "label": METHOD_LABEL[mode],
                "color": METHOD_COLOR[mode],
                "marker": True,
            }
        )
    va_series = paths.pop("figure_2_series")
    va_series.extend(
        [
            {"x": [0.0, max(row["T"] for row in candidates["full"]["rows"])], "y": [V_MIN, V_MIN], "label": "V_min", "color": "#777777", "dash": True, "marker": False},
            {"x": [0.0, max(row["T"] for row in candidates["full"]["rows"])], "y": [V_MAX, V_MAX], "label": "V_max", "color": "#aaaaaa", "dash": True, "marker": False},
        ]
    )
    paths["figure_2"] = _line_figure(
        figure_dir / "figure_2_learned_va_vs_t.svg",
        "Learned modulation variance versus T",
        "Policy diagnostic only; bounds are enforced by the transmitter parameterization",
        "power transmittance T",
        "V_A (SNU)",
        va_series,
        y_min=V_MIN,
        y_max=V_MAX,
    )

    ps_series = []
    for mode in ("ps", "ps_va", "full"):
        rows = candidates[mode]["rows"]
        entropy = [
            -sum(probability * math.log(probability, 2) for probability in row["probabilities"] if probability > 0.0)
            for row in rows
        ]
        ps_series.append(
            {
                "x": [row["T"] for row in rows],
                "y": entropy,
                "label": METHOD_LABEL[mode],
                "color": METHOD_COLOR[mode],
                "marker": True,
            }
        )
    paths["figure_3"] = _line_figure(
        figure_dir / "figure_3_ps_entropy_vs_t.svg",
        "Probabilistic-shaping adaptation versus T",
        "H(p) is computed from the learned 256-symbol PMF; policy diagnostic only",
        "power transmittance T",
        "PMF entropy H(p) (bits)",
        ps_series,
        y_min=0.0,
        y_max=8.1,
    )

    full_rows = candidates["full"]["rows"]
    choices = [
        min(full_rows, key=lambda row: row["T"]),
        min(full_rows, key=lambda row: abs(row["T"] - np.median([item["T"] for item in full_rows]))),
        max(full_rows, key=lambda row: row["T"]),
    ]
    paths["figure_4"] = _scatter_figure(
        figure_dir / "figure_4_full_constellation_snapshots.svg",
        [
            {
                "label": label,
                "T": row["T"],
                "V_A": row["V_A"],
                "probabilities": row["probabilities"],
                "amplitudes": row["amplitudes"],
            }
            for label, row in zip(("poor active channel", "median channel", "good active channel"), choices)
        ],
    )

    bar_values = [
        {"label": mode, "value": summaries["surrogate_weighted"][mode], "color": METHOD_COLOR[mode]}
        for mode, _, _ in METHODS
    ]
    paths["figure_5"] = _bar_figure(
        figure_dir / "figure_5_weighted_method_summary.svg",
        "Weighted method comparison",
        "OPTIMIZATION/ANALYSIS ESTIMATE from the representative grid; exact-bin values are separate artifact data",
        bar_values,
    )
    paths["figure_6"] = _table_figure(
        figure_dir / "figure_6_exact_vs_surrogate_table.svg",
        "Exact AP versus training-surrogate anchor comparison",
        "C and w are source-moment comparisons; K uses the same existing full-Z chain; rank reversals are explicit",
        error_rows,
    )
    return {key: value for key, value in paths.items() if isinstance(value, str)}


def _method_ensemble_at(
    transmitter: JointTransmitter,
    points: list[dict[str, Any]],
) -> tuple[torch.Tensor, torch.Tensor, Ensemble]:
    transmittance = torch.tensor([point["T"] for point in points], dtype=torch.float64)
    epsilon = torch.tensor([point["epsilon_base"] for point in points], dtype=torch.float64)
    return transmittance, epsilon, transmitter(transmittance, epsilon)


def _source_tensors_from_exact(
    exact: dict[str, Any], count: int,
) -> tuple[torch.Tensor, torch.Tensor]:
    return (
        torch.tensor([float(exact["C"])] * count, dtype=torch.float64),
        torch.tensor([float(exact["w"])] * count, dtype=torch.float64),
    )


def _anchor_source_for_full(
    exact_results: dict[str, dict[str, Any]],
) -> tuple[torch.Tensor, torch.Tensor]:
    return (
        torch.tensor([float(exact_results[f"full_{index}"]["C"]) for index in range(ANCHOR_COUNT)], dtype=torch.float64),
        torch.tensor([float(exact_results[f"full_{index}"]["w"]) for index in range(ANCHOR_COUNT)], dtype=torch.float64),
    )


def _build_security_artifacts(
    transmitters: dict[str, JointTransmitter],
    grid: dict[str, Any],
    anchors: list[dict[str, Any]],
    exact_results: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    active_grid = [point for point in grid["points"] if point["active"]]
    t_grid = torch.tensor([point["T"] for point in active_grid], dtype=torch.float64)
    e_grid = torch.tensor([point["epsilon_base"] for point in active_grid], dtype=torch.float64)
    t_anchor = torch.tensor([point["T"] for point in anchors], dtype=torch.float64)
    e_anchor = torch.tensor([point["epsilon_base"] for point in anchors], dtype=torch.float64)
    grid_noise = standard_complex_noise(
        (len(active_grid), 256, GRID_NOISE_SAMPLES),
        generator=torch.Generator(device="cpu").manual_seed(existing_case.AWGN_SEED),
        device=torch.device("cpu"),
    )
    anchor_noise = standard_complex_noise(
        (len(anchors), 256, ANCHOR_NOISE_SAMPLES),
        generator=torch.Generator(device="cpu").manual_seed(existing_case.AWGN_SEED + 1),
        device=torch.device("cpu"),
    )

    grid_exact: dict[str, Any] = {}
    grid_surrogate: dict[str, Any] = {}
    anchor_security: dict[str, Any] = {}
    for mode in ("uniform", "mb", "ps", "va", "ps_va", "full"):
        transmitter = transmitters[mode]
        with torch.no_grad():
            surrogate_eval = _evaluate_surrogate(
                transmitter,
                t_grid,
                e_grid,
                grid_noise,
                analysis_grid=True,
                search_proxy=True,
            )
            grid_surrogate[mode] = _search_estimate_rows(surrogate_eval, t_grid, e_grid)
        if mode == "uniform":
            c_grid, w_grid = _source_tensors_from_exact(
                {"C": CORRECTED_C_TEXT, "w": CORRECTED_W_TEXT}, len(active_grid)
            )
        elif mode == "mb":
            c_grid, w_grid = _source_tensors_from_exact(exact_results["mb"], len(active_grid))
        else:
            c_grid, w_grid = surrogate_eval["C"], surrogate_eval["w"]
        if mode in {"uniform", "mb"}:
            grid_exact[mode] = _security_rows(
                transmitter,
                t_grid,
                e_grid,
                grid_noise,
                c_grid,
                w_grid,
                surrogate=False,
            )

        if mode in {"uniform", "mb", "full"}:
            with torch.no_grad():
                anchor_ensemble = transmitter(t_anchor, e_anchor)
                if mode == "uniform":
                    c_exact, w_exact = _source_tensors_from_exact(
                        {"C": CORRECTED_C_TEXT, "w": CORRECTED_W_TEXT}, ANCHOR_COUNT
                    )
                elif mode == "mb":
                    c_exact, w_exact = _source_tensors_from_exact(exact_results["mb"], ANCHOR_COUNT)
                else:
                    c_exact, w_exact = _anchor_source_for_full(exact_results)
                exact_rows = _security_rows(
                    transmitter,
                    t_anchor,
                    e_anchor,
                    anchor_noise,
                    c_exact,
                    w_exact,
                    surrogate=False,
                )
                surrogate_c, surrogate_w, _ = _surrogate_batch(anchor_ensemble)
                surrogate_rows = _security_rows(
                    transmitter,
                    t_anchor,
                    e_anchor,
                    anchor_noise,
                    surrogate_c,
                    surrogate_w,
                    surrogate=True,
                )
                anchor_security[mode] = {
                    "exact": exact_rows,
                    "surrogate": surrogate_rows,
                }

    error_rows: list[dict[str, Any]] = []
    exact_k_by_anchor: dict[str, list[float]] = {}
    surrogate_k_by_anchor: dict[str, list[float]] = {}
    for mode in ("uniform", "mb", "full"):
        exact_rows = anchor_security[mode]["exact"]["rows"]
        surrogate_rows = anchor_security[mode]["surrogate"]["rows"]
        exact_k_by_anchor[mode] = [row["raw_K"] for row in exact_rows]
        surrogate_k_by_anchor[mode] = [row["raw_K"] for row in surrogate_rows]
    for index, anchor in enumerate(anchors):
        exact_order = sorted((mode for mode in ("uniform", "mb", "full")), key=lambda mode: exact_k_by_anchor[mode][index], reverse=True)
        surrogate_order = sorted((mode for mode in ("uniform", "mb", "full")), key=lambda mode: surrogate_k_by_anchor[mode][index], reverse=True)
        for mode in ("uniform", "mb", "full"):
            exact_c = anchor_security[mode]["exact"]["rows"][index]["C"]
            exact_w = anchor_security[mode]["exact"]["rows"][index]["w"]
            surrogate_c = anchor_security[mode]["surrogate"]["rows"][index]["C"]
            surrogate_w = anchor_security[mode]["surrogate"]["rows"][index]["w"]
            error_rows.append(
                {
                    "label": f"{METHOD_LABEL[mode]} / a{index + 1}",
                    "method": mode,
                    "anchor_index": index,
                    "T": anchor["T"],
                    "C_relative_error": _relative(surrogate_c, exact_c),
                    "w_relative_error": _relative(surrogate_w, exact_w),
                    "K_exact": exact_k_by_anchor[mode][index],
                    "K_surrogate": surrogate_k_by_anchor[mode][index],
                    "rank_consistent": exact_order == surrogate_order,
                    "exact_order": exact_order,
                    "surrogate_order": surrogate_order,
                }
            )
    return grid_exact, grid_surrogate, anchor_security, error_rows


def _weighted_summary(
    grid: dict[str, Any],
    grid_surrogate: dict[str, Any],
    anchor_security: dict[str, Any],
) -> dict[str, Any]:
    active_weights = np.asarray([point["weight"] for point in grid["points"] if point["active"]], dtype=np.float64)
    surrogate_weighted = {
        mode: float(np.sum(active_weights * np.asarray([row["raw_K"] for row in grid_surrogate[mode]["rows"]], dtype=np.float64)))
        for mode, _, _ in METHODS
    }
    exact_bin: dict[str, float] = {}
    anchor_weight = float(grid["active_mass"] / ANCHOR_COUNT)
    for mode in ("uniform", "mb", "full"):
        exact_bin[mode] = anchor_weight * float(
            np.sum([row["raw_K"] for row in anchor_security[mode]["exact"]["rows"]])
        )
    return {
        "artifact_class": "ANALYSIS_ESTIMATE",
        "surrogate_weighted": surrogate_weighted,
        "exact_bin_weighted": exact_bin,
        "exact_bin_definition": "seven equally weighted active T quantile representatives plus explicit outage mass; only Uniform, MB, and Full have exact anchors",
        "outage_mass": grid["outage_mass"],
    }


def _write_workflow_status(
    status: str,
    *,
    reason: str,
    calibration: dict[str, Any] | None = None,
    nearby: dict[str, Any] | None = None,
) -> Path:
    payload = {
        "status": status,
        "artifact_class": "ANALYSIS_ESTIMATE",
        "reason": reason,
        "calibration_status": None if calibration is None else calibration.get("status"),
        "nearby_status": None if nearby is None else nearby.get("status"),
        "publication_status": "NOT_PUBLICATION_CERTIFIED",
        "publication_scale_training": False,
        "final_test_accessed": False,
    }
    path = ROOT / "results" / f"analysis_figures_artifact_{ARTIFACT_DATE}.json"
    _write_json(path, payload)
    return path


def main() -> int:
    started = time.perf_counter()
    calibration = _calibrate_surrogate()
    calibration_path = ROOT / "results" / f"training_surrogate_calibration_{ARTIFACT_DATE}.json"
    _write_json(calibration_path, calibration)
    print(f"surrogate calibration: {calibration['status']}", flush=True)
    if calibration["status"] != "TRAINING_SURROGATE_CALIBRATED":
        _write_workflow_status(
            "ANALYSIS_FIGURES_BLOCKED",
            reason="SURROGATE_OPTIMIZATION_BLOCKED",
            calibration=calibration,
        )
        return 2

    nearby = _nearby_calibration()
    nearby_path = ROOT / "results" / f"training_surrogate_nearby_calibration_{ARTIFACT_DATE}.json"
    _write_json(nearby_path, nearby)
    print(f"nearby calibration: {nearby['status']}", flush=True)
    if nearby["status"] != "NEARBY_SURROGATE_PASS":
        _write_workflow_status(
            "ANALYSIS_FIGURES_BLOCKED",
            reason="LOCAL_SURROGATE_CALIBRATION_FAILED",
            calibration=calibration,
            nearby=nearby,
        )
        return 2

    grid = _analysis_grid()
    grid_path = ROOT / "results" / f"analysis_channel_grid_{ARTIFACT_DATE}.json"
    _write_json(grid_path, {"artifact_class": "ANALYSIS_ESTIMATE", **grid})
    active_points = [point for point in grid["points"] if point["active"]]
    anchor_points = grid["anchor_points"]
    training_noise = standard_complex_noise(
        (len(active_points), 256, TRAINING_NOISE_SAMPLES),
        generator=torch.Generator(device="cpu").manual_seed(existing_case.AWGN_SEED + 2),
        device=torch.device("cpu"),
    )

    transmitters: dict[str, JointTransmitter] = {}
    candidates: dict[str, dict[str, Any]] = {}
    training: dict[str, Any] = {}
    for method_index, (mode, _, _) in enumerate(METHODS):
        print(f"optimization {mode}: start", flush=True)
        transmitter, final, history = _run_method(
            mode,
            grid,
            training_noise,
            seed=20260920 + method_index,
        )
        transmitters[mode] = transmitter
        candidates[mode] = _candidate_payload(transmitter, active_points, final)
        training[mode] = history
        print(f"optimization {mode}: {history['status']}", flush=True)

    candidate_path = ROOT / "results" / f"analysis_candidate_ensembles_{ARTIFACT_DATE}.json"
    _write_json(candidate_path, _serialize_candidate_ensembles(candidates))
    checkpoint_path = ROOT / "results" / f"analysis_training_checkpoints_{ARTIFACT_DATE}.json"
    _write_json(
        checkpoint_path,
        {
            "artifact_class": "TRAINING_SURROGATE",
            "methods": training,
            "smoke_steps": SMOKE_STEPS,
            "analysis_steps": ANALYSIS_STEPS,
            "phase_disabled": True,
            "c_phi": PHASE_COEFFICIENT,
            "epsilon_total_definition": EPSILON_TOTAL_DEFINITION,
        },
    )

    # Exact AP source moments are requested only for a small nearby set and the
    # seven main full-method anchor ensembles. Uniform is already validated;
    # MB requires one reusable exact source-moment evaluation.
    mb_ensemble = transmitters["mb"](torch.tensor([0.03]), torch.tensor([0.02]))
    mb_p, mb_z = _orbit_inputs(mb_ensemble, 0)
    full_anchor_ensemble = transmitters["full"](
        torch.tensor([point["T"] for point in anchor_points]),
        torch.tensor([point["epsilon_base"] for point in anchor_points]),
    )
    exact_jobs: dict[str, tuple[torch.Tensor, torch.Tensor]] = {"mb": (mb_p.detach(), mb_z.detach())}
    for index in range(ANCHOR_COUNT):
        exact_jobs[f"full_{index}"] = _orbit_inputs(full_anchor_ensemble, index)
    exact_results = _run_exact_jobs(exact_jobs)
    exact_anchor_path = ROOT / "results" / f"analysis_exact_ap_security_anchors_{ARTIFACT_DATE}.json"
    exact_anchor_payload = {
        "artifact_class": "EXACT_AP_SECURITY_ANCHOR",
        "status": "EXACT_AP_SOURCE_ROWS_COMPLETE" if all(
            value["status"] == "FULL_SUPPORT_CONVERGED" for value in exact_results.values()
        ) else "EXACT_AP_SOURCE_ROWS_INCOMPLETE",
        "precision_ladder_decimal_digits": list(AP_DIGITS),
        "corrected_worker": str(CORRECTED_WORKER.relative_to(ROOT)),
        "corrected_worker_sha256": _hash_file(CORRECTED_WORKER),
        "uniform_reference": {
            "C": CORRECTED_C_TEXT,
            "w": CORRECTED_W_TEXT,
            "support": "256/256",
            "minimum_eigenvalue": existing_case.__dict__.get("MINIMUM_EIGENVALUE", "3.9730108272405810054e-618"),
        },
        "results": exact_results,
        "phase_disabled": True,
        "c_phi": PHASE_COEFFICIENT,
        "epsilon_total_definition": EPSILON_TOTAL_DEFINITION,
    }
    _write_json(exact_anchor_path, exact_anchor_payload)
    if any(value["status"] != "FULL_SUPPORT_CONVERGED" for value in exact_results.values()):
        _write_workflow_status(
            "ANALYSIS_FIGURES_BLOCKED",
            reason="EXACT_AP_ANCHOR_SOURCE_ROWS_INCOMPLETE",
            calibration=calibration,
            nearby=nearby,
        )
        return 2

    grid_exact, grid_surrogate, anchor_security, error_rows = _build_security_artifacts(
        transmitters,
        grid,
        anchor_points,
        exact_results,
    )
    summaries = _weighted_summary(grid, grid_surrogate, anchor_security)
    figure_data = {
        "artifact_class": "ANALYSIS_ESTIMATE",
        "phase_disabled": True,
        "c_phi": PHASE_COEFFICIENT,
        "epsilon_total_definition": EPSILON_TOTAL_DEFINITION,
        "grid": grid,
        "candidates": candidates,
        "grid_security_exact": grid_exact,
        "grid_security_surrogate": grid_surrogate,
        "anchor_security": anchor_security,
        "summary": summaries,
        "exact_vs_surrogate": error_rows,
        "plot_backend": {
            "name": "stdlib_svg",
            "vector_format": "SVG",
            "png_supported": False,
            "pdf_supported": False,
            "reason": "No matplotlib or other raster/PDF plotting backend is installed in the active environment.",
        },
    }
    figure_data_path = ROOT / "results" / f"analysis_figure_data_{ARTIFACT_DATE}.json"
    _write_json(figure_data_path, figure_data)
    figures = _render_figures(
        grid,
        candidates,
        grid_exact,
        grid_surrogate,
        anchor_security,
        summaries,
        error_rows,
    )
    final_payload = {
        "status": "ANALYSIS_FIGURES_READY",
        "artifact_class": "ANALYSIS_ESTIMATE",
        "publication_status": "NOT_PUBLICATION_CERTIFIED",
        "phase_disabled": True,
        "c_phi": PHASE_COEFFICIENT,
        "epsilon_total_definition": EPSILON_TOTAL_DEFINITION,
        "security_oracle": {
            "corrected_worker": str(CORRECTED_WORKER.relative_to(ROOT)),
            "corrected_worker_sha256": _hash_file(CORRECTED_WORKER),
            "full_Z_grid_size": SECURITY_Z_GRID_SIZE,
            "full_Z_refinement_steps": SECURITY_Z_REFINEMENT_STEPS,
            "outage_rule": "T=0 -> no policy, MI, Holevo; raw K=0",
            "old_w_used": False,
        },
        "training_surrogate": {
            "module": "src/cvqkd/training_surrogate.py",
            "regularization": SURROGATE_REGULARIZATION,
            "calibration_artifact": str(calibration_path.relative_to(ROOT)),
            "nearby_artifact": str(nearby_path.relative_to(ROOT)),
        },
        "artifacts": {
            "channel_grid": str(grid_path.relative_to(ROOT)),
            "training_checkpoints": str(checkpoint_path.relative_to(ROOT)),
            "candidate_ensembles": str(candidate_path.relative_to(ROOT)),
            "exact_ap_security_anchors": str(exact_anchor_path.relative_to(ROOT)),
            "figure_data": str(figure_data_path.relative_to(ROOT)),
            "figures": figures,
        },
        "summary": summaries,
        "exact_vs_surrogate": {
            "rows": error_rows,
            "all_rank_consistent": all(row["rank_consistent"] for row in error_rows),
        },
        "provenance": {
            "repository": _git_metadata(),
            "runner_sha256": _hash_file(Path(__file__)),
            "final_model_spec_sha256": _hash_file(ROOT / "docs" / "FINAL_MODEL_SPEC.md"),
            "tangent_artifact_sha256": _hash_file(TANGENT_ARTIFACT),
            "grid_sha256": grid["grid_sha256"],
        },
        "publication_scale_training": False,
        "final_test_accessed": False,
        "runtime_seconds": time.perf_counter() - started,
    }
    final_path = ROOT / "results" / f"analysis_figures_artifact_{ARTIFACT_DATE}.json"
    _write_json(final_path, final_payload)
    print(f"ANALYSIS_FIGURES_READY: {final_path}", flush=True)
    print(f"figures: {final_payload['artifacts']['figures']}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
