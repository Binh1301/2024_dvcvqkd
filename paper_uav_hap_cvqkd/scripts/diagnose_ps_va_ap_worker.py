"""Diagnostic-only localization of the corrected AP C4 worker.

This script freezes one saved transmitter checkpoint and one existing anchor,
replays ``full_support_c4_worker.py`` unchanged when requested, instruments a
faithful copy of its forward stages, and builds an independent 256-state
weighted coherent-state Gram.  It is not imported by production code.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
from typing import Any

import mpmath as mp
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import run_analysis_figures as runner  # noqa: E402
from src.modulation.probabilistic_shaping import channel_features  # noqa: E402


WORKER = ROOT / "scripts" / "full_support_c4_worker.py"
FIGURE_DATA = ROOT / "results" / "analysis_figure_data_20260911.json"
PS_CHECKPOINT = ROOT / "results" / "repaired_full_z_checkpoint_ps_va_20260911_step_50.pt"
FULL_CHECKPOINT = ROOT / "results" / "repaired_full_z_checkpoint_full_20260911_step_50.pt"
DEFAULT_OUTPUT = ROOT / "results" / "ps_va_ap_worker_localization_20260912.json"
MEDIAN_ANCHOR_INDEX = 3
INITIALIZER_SEED = 20260924
ROTATIONS = (1.0 + 0.0j, 0.0 + 1.0j, -1.0 + 0.0j, 0.0 - 1.0j)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _hex(value: float) -> str:
    return float(value).hex()


def _complex_hex(value: complex) -> list[str]:
    return [_hex(complex(value).real), _hex(complex(value).imag)]


def _mp_float(value: str) -> mp.mpf:
    # Match the unchanged worker: float.fromhex is converted before its
    # workdps context, and mpmath retains the exact binary64 value.
    return mp.mpf(float.fromhex(value))


def _mp_complex(value: list[str]) -> mp.mpc:
    return mp.mpc(float.fromhex(value[0]), float.fromhex(value[1]))


def _mp_exact_float(value: str) -> mp.mpf:
    number = float.fromhex(value)
    numerator, denominator = number.as_integer_ratio()
    return mp.mpf(numerator) / denominator


def _mp_exact_complex(value: list[str]) -> mp.mpc:
    return mp.mpc(_mp_exact_float(value[0]), _mp_exact_float(value[1]))


def _matrix_max_abs(matrix: mp.matrix) -> mp.mpf:
    return max(
        (abs(matrix[i, j]) for i in range(matrix.rows) for j in range(matrix.cols)),
        default=mp.mpf(0),
    )


def _matrix_fro(matrix: mp.matrix) -> mp.mpf:
    return mp.sqrt(
        mp.fsum(abs(matrix[i, j]) ** 2 for i in range(matrix.rows) for j in range(matrix.cols))
    )


def _relative_residual(left: mp.matrix, right: mp.matrix) -> str:
    scale = max(_matrix_fro(right), mp.mpf("1e-10000"))
    return mp.nstr(_matrix_fro(left - right) / scale, 30)


def _trace(matrix: mp.matrix) -> mp.mpf:
    return mp.fsum(matrix[i, i] for i in range(matrix.rows)).real


def _trace_square(matrix: mp.matrix) -> mp.mpf:
    return mp.fsum(
        matrix[i, j] * matrix[j, i]
        for i in range(matrix.rows)
        for j in range(matrix.cols)
    ).real


def _scalar_relative_residual(left: mp.mpf, right: mp.mpf) -> str:
    return mp.nstr(abs(left - right) / max(abs(right), mp.mpf("1e-10000")), 30)


def _eigendecomposition_residual(
    matrix: mp.matrix, values: mp.matrix, vectors: mp.matrix
) -> str:
    diagonal = mp.diag([mp.re(values[i]) for i in range(values.rows)])
    residual = matrix * vectors - vectors * diagonal
    return mp.nstr(
        _matrix_fro(residual) / max(_matrix_fro(matrix), mp.mpf("1e-10000")),
        30,
    )


def _format(value: Any, digits: int = 50) -> str:
    if isinstance(value, (mp.mpf, mp.mpc)):
        return mp.nstr(value, digits)
    return str(value)


def _load_transmitter(mode: str, checkpoint: Path) -> tuple[Any, dict[str, Any]]:
    transmitter = runner._initialize_transmitter(mode, INITIALIZER_SEED)
    state = torch.load(checkpoint, map_location="cpu", weights_only=False)
    transmitter.load_state_dict(state["state_dict"])
    transmitter.eval()
    with torch.no_grad():
        figure_data = json.loads(FIGURE_DATA.read_text(encoding="utf-8"))
        point = figure_data["grid"]["anchor_points"][MEDIAN_ANCHOR_INDEX]
        transmittance = torch.tensor([float(point["T"])], dtype=torch.float64)
        epsilon = torch.tensor([float(point["epsilon_base"])], dtype=torch.float64)
        ensemble = transmitter(transmittance, epsilon)
        probabilities, prototypes = runner._orbit_inputs(ensemble, 0)
        logits = transmitter.ps_network.network(channel_features(transmittance, epsilon))[0]

    p = [float(value) for value in probabilities.tolist()]
    z = [complex(value) for value in prototypes.tolist()]
    q = [4.0 * value for value in p]
    indices = runner.c4_orbit_indices(device="cpu").tolist()
    full_z = [z[orbit] * ROTATIONS[rotation] for orbit in range(64) for rotation in range(4)]
    public_p = ensemble.probabilities[0].detach().cpu().tolist()
    public_z = ensemble.amplitudes[0].detach().cpu().tolist()
    expanded_p = [None] * 256
    expanded_z = [None] * 256
    for orbit, row in enumerate(indices):
        for rotation, label in enumerate(row):
            expanded_p[label] = p[orbit]
            expanded_z[label] = z[orbit] * ROTATIONS[rotation]

    if any(_hex(a) != _hex(b) for a, b in zip(public_p, expanded_p)):
        raise RuntimeError(f"{mode}: public probability expansion is not bitwise C4-consistent")
    if any(
        _complex_hex(a) != _complex_hex(b)
        for a, b in zip(public_z, expanded_z)
    ):
        raise RuntimeError(f"{mode}: public amplitude expansion is not bitwise C4-consistent")

    relative = transmitter.base_relative_constellation.detach().cpu()[runner.ORBIT_INDICES]
    relative_values = [complex(value) for value in relative.tolist()]
    q_sum = sum(q)
    relative_energy = sum(qi * abs(xi) ** 2 for qi, xi in zip(q, relative_values))
    va = float(ensemble.declared_va[0])
    scale = (va / (2.0 * relative_energy)) ** 0.5
    full_distances = [
        abs(full_z[i] - full_z[j])
        for i in range(256)
        for j in range(i)
    ]
    all_hex = {
        "probabilities_float64_hex": [_hex(value) for value in p],
        "prototypes_float64_hex": [_complex_hex(value) for value in z],
        "q_float64_hex": [_hex(value) for value in q],
        "logits_float64_hex": [_hex(float(value)) for value in logits.detach().cpu().tolist()],
        "full_probabilities_float64_hex": [_hex(value) for value in expanded_p],
        "full_amplitudes_float64_hex": [_complex_hex(value) for value in expanded_z],
    }
    request = {
        "probabilities_float64_hex": all_hex["probabilities_float64_hex"],
        "prototypes_float64_hex": all_hex["prototypes_float64_hex"],
        "precision_ladder_decimal_digits": [],
    }
    return transmitter, {
        "mode": mode,
        "state_label": "median",
        "anchor_index": MEDIAN_ANCHOR_INDEX,
        "T": point["T"],
        "T_float64_hex": _hex(float(point["T"])),
        "epsilon_base": point["epsilon_base"],
        "epsilon_base_float64_hex": _hex(float(point["epsilon_base"])),
        "V_A": va,
        "V_A_float64_hex": _hex(va),
        "checkpoint": str(checkpoint.relative_to(ROOT)),
        "checkpoint_sha256": _sha256(checkpoint),
        "serialized": all_hex,
        "request": request,
        "constellation_hash": _canonical_hash({"prototypes": all_hex["prototypes_float64_hex"]}),
        "full_constellation_hash": _canonical_hash({"amplitudes": all_hex["full_amplitudes_float64_hex"]}),
        "direct_input_hash": _canonical_hash(all_hex),
        "q_sum": q_sum,
        "p_sum": sum(p),
        "q_min": min(q),
        "q_max": max(q),
        "p_min": min(p),
        "p_max": max(p),
        "logit_min": float(logits.min()),
        "logit_max": float(logits.max()),
        "logit_range": float(logits.max() - logits.min()),
        "relative_energy": relative_energy,
        "physical_energy": sum(value * abs(alpha) ** 2 for value, alpha in zip(expanded_p, expanded_z)),
        "normalization_scale": scale,
        "minimum_pair_distance": min(full_distances),
        "unique_amplitudes": len({_complex_hex(value)[0] + ":" + _complex_hex(value)[1] for value in expanded_z}),
        "c4_probability_max_error": max(
            abs(expanded_p[row] - expanded_p[indices[orbit][0]])
            for orbit in range(64)
            for row in indices[orbit]
        ),
        "c4_amplitude_max_error": max(
            abs(expanded_z[indices[orbit][rotation]] - z[orbit] * ROTATIONS[rotation])
            for orbit in range(64)
            for rotation in range(4)
        ),
    }


def _worker_replay(request: dict[str, Any], digits: list[int], timeout: float) -> dict[str, Any]:
    payload = dict(request)
    payload["precision_ladder_decimal_digits"] = digits
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            [sys.executable, str(WORKER)],
            cwd=ROOT,
            input=json.dumps(payload, sort_keys=True),
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {"status": "TIMEOUT", "digits": digits, "runtime_seconds": time.perf_counter() - started}
    row: dict[str, Any] = {
        "status": "RETURNED" if completed.returncode == 0 else "EXIT_NONZERO",
        "digits": digits,
        "returncode": completed.returncode,
        "runtime_seconds": time.perf_counter() - started,
        "stderr_tail": completed.stderr[-2000:],
    }
    try:
        row["worker_payload"] = json.loads(completed.stdout)
    except json.JSONDecodeError:
        row["stdout_tail"] = completed.stdout[-2000:]
    return row


def _independent_full(p_hex: list[str], z_hex: list[list[str]], digits: int, do_eigh: bool) -> dict[str, Any]:
    """Build the full weighted Gram directly, then Fourier-block it."""
    with mp.workdps(digits):
        p = [_mp_exact_float(value) for value in p_hex]
        z = [_mp_exact_complex(value) for value in z_hex]
        alpha = [z[orbit] * (mp.j ** rotation) for orbit in range(64) for rotation in range(4)]
        weights = [p[orbit] for orbit in range(64) for _ in range(4)]
        full = mp.matrix(256)
        for i in range(256):
            for j in range(256):
                full[i, j] = mp.sqrt(weights[i] * weights[j]) * mp.exp(
                    -(abs(alpha[i]) ** 2 + abs(alpha[j]) ** 2) / 2 + mp.conj(alpha[i]) * alpha[j]
                )
        trace = _trace(full)
        hermitian = max(abs(full[i, j] - mp.conj(full[j, i])) for i in range(256) for j in range(256))
        transformed = [[mp.matrix(64) for _ in range(4)] for _ in range(4)]
        for sector in range(4):
            for other_sector in range(4):
                for orbit in range(64):
                    for other in range(64):
                        transformed[sector][other_sector][orbit, other] = mp.fsum(
                            mp.conj(mp.j ** (sector * r))
                            * full[4 * orbit + r, 4 * other + u]
                            * (mp.j ** (other_sector * u))
                            / 4
                            for r in range(4)
                            for u in range(4)
                        )
        off_diagonal = max(
            _matrix_max_abs(transformed[sector][other_sector])
            for sector in range(4)
            for other_sector in range(4)
            if sector != other_sector
        )
        independent_sector = []
        for sector in range(4):
            raw = mp.zeros(64)
            for orbit in range(64):
                for other in range(64):
                    raw[orbit, other] = mp.fsum(
                        mp.sqrt(p[orbit] * p[other])
                        * mp.exp(
                            -(
                                abs(z[orbit]) ** 2
                                + abs((mp.j ** difference) * z[other]) ** 2
                            )
                            / 2
                            + mp.conj(z[orbit]) * (mp.j ** difference) * z[other]
                        )
                        * (mp.j ** (sector * difference))
                        for difference in range(4)
                    )
            independent_sector.append((raw + raw.H) / 2)
        from scripts import full_support_c4_worker as worker

        production_sector = worker._sectors(
            [_mp_float(value) for value in p_hex],
            [_mp_complex(value) for value in z_hex],
        )
        sector_differences = [
            _relative_residual(transformed[sector][sector], independent_sector[sector])
            for sector in range(4)
        ]
        production_sector_differences = [
            _relative_residual(transformed[sector][sector], production_sector[sector])
            for sector in range(4)
        ]
        fourier = mp.matrix(
            [
                [mp.j ** (row * column) / 2 for column in range(4)]
                for row in range(4)
            ]
        )
        fourier_unitarity = fourier.H * fourier - mp.eye(4)
        trace_full = _trace(full)
        trace_blocks = mp.fsum(_trace(matrix) for matrix in independent_sector)
        frobenius_squared_full = _matrix_fro(full) ** 2
        frobenius_squared_blocks = mp.fsum(
            _matrix_fro(matrix) ** 2 for matrix in independent_sector
        )
        trace_square_full = _trace_square(full)
        trace_square_blocks = mp.fsum(
            _trace_square(matrix) for matrix in independent_sector
        )
        independent_spectra = []
        independent_values = []
        for matrix in independent_sector:
            eigenvalues, _vectors = mp.eighe(matrix)
            values = [mp.re(eigenvalues[i]) for i in range(64)]
            independent_values.extend(values)
            independent_spectra.append([_format(value, 50) for value in values])
        result: dict[str, Any] = {
            "digits": digits,
            "status": "GLOBAL_SPECTRUM_NOT_RUN",
            "construction": "direct_256_state_weighted_Gram_with_exact_binary64_ratios",
            "trace": _format(trace_full),
            "trace_residual": _format(abs(trace_full - 1)),
            "hermiticity_max_residual": _format(hermitian),
            "fourier_unitarity_residual": _format(_matrix_max_abs(fourier_unitarity)),
            "fourier_off_diagonal_max_residual": _format(off_diagonal),
            "fourier_sector_relative_residuals": sector_differences,
            "production_sector_relative_residuals": production_sector_differences,
            "invariants": {
                "trace_blocks": _format(trace_blocks),
                "trace_invariant_relative_error": _scalar_relative_residual(
                    trace_full, trace_blocks
                ),
                "frobenius_squared_full": _format(frobenius_squared_full),
                "frobenius_squared_blocks": _format(frobenius_squared_blocks),
                "frobenius_invariant_relative_error": _scalar_relative_residual(
                    frobenius_squared_full, frobenius_squared_blocks
                ),
                "trace_square_full": _format(trace_square_full),
                "trace_square_blocks": _format(trace_square_blocks),
                "trace_square_relative_error": _scalar_relative_residual(
                    trace_square_full, trace_square_blocks
                ),
            },
            "independent_sector_spectra": independent_spectra,
            "full_matrix_frobenius_norm": _format(_matrix_fro(full)),
            "global_spectrum": None,
            "global_spectrum_status": "NOT_RUN",
        }
        if do_eigh:
            started = time.perf_counter()
            values, vectors = mp.eighe(full)
            global_values = sorted(
                [mp.re(values[i]) for i in range(256)]
            )
            sector_union = sorted(independent_values)
            resolution_threshold = mp.power(10, -(digits - 20))
            resolved_global = [
                value for value in global_values if value > resolution_threshold
            ]
            resolved_union = [
                value for value in sector_union if value > resolution_threshold
            ]
            paired_absolute_errors = [
                abs(left - right)
                for left, right in zip(global_values, sector_union)
            ]
            log_errors = [
                abs(mp.log10(left) - mp.log10(right))
                for left, right in zip(global_values, sector_union)
                if left > resolution_threshold and right > resolution_threshold
            ]
            result["global_spectrum"] = [_format(value, 50) for value in global_values]
            result["global_spectrum_status"] = "COMPLETED"
            result["status"] = "GLOBAL_SPECTRUM_COMPLETED"
            result["global_eigh_runtime_seconds"] = time.perf_counter() - started
            result["global_spectrum_summary"] = {
                "resolution_threshold": _format(resolution_threshold),
                "resolved_global_modes": len(resolved_global),
                "resolved_sector_union_modes": len(resolved_union),
                "minimum_resolved_global_eigenvalue": (
                    _format(min(resolved_global))
                    if resolved_global
                    else None
                ),
                "maximum_global_eigenvalue": _format(max(global_values)),
                "global_eigenvalue_trace": _format(mp.fsum(global_values)),
                "global_eigenvalue_trace_error": _format(
                    abs(mp.fsum(global_values) - trace_full)
                ),
                "sector_union_max_absolute_error": _format(
                    max(paired_absolute_errors)
                ),
                "sector_union_max_log10_error": (
                    _format(max(log_errors)) if log_errors else None
                ),
                "eigendecomposition_relative_residual": _eigendecomposition_residual(
                    full, values, vectors
                ),
            }
        return result


def _trace_row(p_hex: list[str], z_hex: list[list[str]], digits: int) -> dict[str, Any]:
    """Instrument the unchanged worker equations without changing that file."""
    from scripts import full_support_c4_worker as worker

    with mp.workdps(digits):
        p = [_mp_float(value) for value in p_hex]
        z = [_mp_complex(value) for value in z_hex]
        started = time.perf_counter()
        sectors = worker._sectors(p, z)
        sector_rows: list[dict[str, Any]] = []
        values: list[list[mp.mpf]] = []
        vectors: list[mp.matrix] = []
        for sector, matrix in enumerate(sectors):
            row: dict[str, Any] = {
                "sector": sector,
                "G_s": {
                    "status": "CONSTRUCTED",
                    "shape": [matrix.rows, matrix.cols],
                    "hermiticity_max_residual": _format(
                        max(abs(matrix[i, j] - mp.conj(matrix[j, i])) for i in range(64) for j in range(64))
                    ),
                    "trace": _format(_trace(matrix)),
                },
                "eigensolver": {"status": "RUNNING"},
            }
            try:
                eigenvalues, eigenvectors = mp.eighe(matrix)
            except Exception as error:  # pragma: no cover - diagnostic boundary
                row["eigensolver"] = {"status": "ERROR", "error": repr(error)}
                sector_rows.append(row)
                return {
                    "digits": digits,
                    "status": "EIGENSOLVER_ERROR",
                    "stage_failed": "eigensolver",
                    "sector_rows": sector_rows,
                    "runtime_seconds": time.perf_counter() - started,
                }
            local = [mp.re(eigenvalues[i]) for i in range(64)]
            values.append(local)
            vectors.append(eigenvectors)
            diagonal = mp.diag(local)
            reconstruction = eigenvectors * diagonal * eigenvectors.H
            orthogonality = eigenvectors.H * eigenvectors
            row["eigensolver"] = {
                "status": "COMPLETED",
                "minimum_eigenvalue": _format(min(local)),
                "maximum_eigenvalue": _format(max(local)),
                "positive_count": sum(value > 0 for value in local),
                "nonpositive_count": sum(value <= 0 for value in local),
                "reconstruction_relative_residual": _relative_residual(reconstruction, matrix),
                "orthogonality_relative_residual": _relative_residual(orthogonality, mp.eye(64)),
            }
            sector_rows.append(row)

        all_values = [value for local in values for value in local]
        rank = sum(value > 0 for value in all_values)
        result: dict[str, Any] = {
            "digits": digits,
            "status": "FULL_SUPPORT" if rank == 256 else "FAIL_CLOSED",
            "stage_failed": None if rank == 256 else "support_gate",
            "rank": rank,
            "sector_positive_counts": [row["eigensolver"]["positive_count"] for row in sector_rows],
            "minimum_eigenvalue": _format(min(all_values)),
            "maximum_eigenvalue": _format(max(all_values)),
            "trace_residual": _format(abs(mp.fsum(_trace(matrix) for matrix in sectors) - 1)),
            "sector_rows": sector_rows,
            "stages": {
                "G_s_construction": "PASS",
                "Hermiticity": "PASS",
                "trace_normalization": "PASS" if abs(mp.fsum(_trace(matrix) for matrix in sectors) - 1) < mp.mpf("1e-40") else "DIAGNOSTIC_NONZERO",
                "eigensolver": "PASS",
                "support_gate": "PASS" if rank == 256 else "FAIL_CLOSED",
                "sqrt_inverse_sqrt": "NOT_RUN",
                "A_s_B_s": "NOT_RUN",
                "Q_s": "NOT_RUN",
                "T_s": "NOT_RUN",
                "partial_C_w": "NOT_RUN",
            },
            "runtime_seconds": time.perf_counter() - started,
        }
        if rank != 256:
            return result

        square = []
        inverse_square = []
        sqrt_rows = []
        for sector, (local, vectors_for_sector, matrix) in enumerate(zip(values, vectors, sectors)):
            sr = mp.diag([mp.sqrt(value) for value in local])
            sp = mp.diag([mp.sqrt(value) for value in values[(sector - 1) % 4]])
            square_matrix = vectors_for_sector * sr * vectors_for_sector.H
            inverse_matrix = vectors_for_sector * mp.diag([1 / mp.sqrt(value) for value in local]) * vectors_for_sector.H
            square.append(square_matrix)
            inverse_square.append(inverse_matrix)
            sqrt_rows.append({
                "sector": sector,
                "status": "COMPLETED",
                "sqrt_residual": _relative_residual(square_matrix * square_matrix, matrix),
                "inverse_sqrt_residual": _relative_residual(inverse_matrix * matrix * inverse_matrix, mp.eye(64)),
            })

        result["sqrt_inverse_sqrt"] = sqrt_rows
        diagonal_z = mp.diag(z)
        a_matrices = []
        q_matrices = []
        c_parts = []
        solve_rows = []
        diagonal_weight = mp.diag([1 / (2 * mp.sqrt(value)) for value in p])
        c = mp.mpf(0)
        for sector in range(4):
            previous = (sector - 1) % 4
            m = vectors[sector].H * diagonal_z * vectors[previous]
            sr = mp.diag([mp.sqrt(value) for value in values[sector]])
            sp = mp.diag([mp.sqrt(value) for value in values[previous]])
            x = worker._lu_solve_matrix(sp, m.T)
            b = sr * x.T
            x2 = worker._lu_solve_matrix(sp, (sr * b).T)
            aa = x2.T
            cb = sr * b * sp * b.H
            c_part = mp.fsum(cb[i, i] for i in range(64)).real
            c += c_part
            a_matrices.append(aa)
            q_matrices.append(sr * vectors[sector].H * diagonal_weight)
            solve_rows.append({
                "sector": sector,
                "status": "COMPLETED",
                "B_s_max_abs": _format(_matrix_max_abs(b)),
                "A_s_max_abs": _format(_matrix_max_abs(aa)),
                "B_s_right_solve_relative_residual": _relative_residual(b * sp, sr * m),
                "A_s_right_solve_relative_residual": _relative_residual(aa * (sp * sp), (sr * sr) * m),
                "partial_C": _format(c_part),
            })
        t = [a_matrices[s] * q_matrices[(s - 1) % 4] for s in range(4)]
        d = [
            mp.fsum(
                mp.conj(q_matrices[s][i, k]) * t[s][i, k]
                for s in range(4)
                for i in range(64)
            )
            for k in range(64)
        ]
        w_parts = [
            4 * mp.fsum(
                p[k]
                * mp.fsum(abs(t[s][i, k] - q_matrices[s][i, k] * d[k]) ** 2 for s in range(4) for i in range(64))
                for k in range(64)
            )
            for _ in range(1)
        ]
        w = w_parts[0]
        result["stages"].update({
            "support_gate": "PASS",
            "sqrt_inverse_sqrt": "PASS",
            "A_s_B_s": "PASS",
            "Q_s": "PASS",
            "T_s": "PASS",
            "partial_C_w": "PASS",
        })
        result["A_s_B_s"] = solve_rows
        result["Q_s"] = [{"sector": s, "status": "COMPLETED", "max_abs": _format(_matrix_max_abs(q_matrices[s]))} for s in range(4)]
        result["T_s"] = [{"sector": s, "status": "COMPLETED", "max_abs": _format(_matrix_max_abs(t[s]))} for s in range(4)]
        result["partial_C_w"] = {"C": _format(c), "w": _format(w), "C_parts": [row["partial_C"] for row in solve_rows]}
        result["runtime_seconds"] = time.perf_counter() - started
        return result


def _run_case(mode: str, checkpoint: Path, digits: list[int], independent_digits: int | None, full_eigh: bool) -> dict[str, Any]:
    _transmitter, frozen = _load_transmitter(mode, checkpoint)
    request = frozen["request"]
    rows = [_trace_row(request["probabilities_float64_hex"], request["prototypes_float64_hex"], value) for value in digits]
    independent = None if independent_digits is None else _independent_full(
        request["probabilities_float64_hex"], request["prototypes_float64_hex"], independent_digits, full_eigh
    )
    return {"frozen_input": frozen, "instrumented_worker_rows": rows, "independent_full_gram": independent}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--digits", nargs="+", type=int, default=[300, 400, 600])
    parser.add_argument("--independent-digits", type=int, default=100)
    parser.add_argument("--full-eigh", action="store_true")
    parser.add_argument("--mode", choices=("ps_va", "full", "both"), default="both")
    parser.add_argument("--skip-independent", action="store_true")
    parser.add_argument("--run-worker", action="store_true")
    parser.add_argument("--worker-digits", nargs="+", type=int, default=[800, 900])
    parser.add_argument("--worker-timeout", type=float, default=7200.0)
    args = parser.parse_args()
    if args.run_worker and len(args.worker_digits) < 2:
        parser.error("--worker-digits must contain at least two rows for the unchanged worker")

    artifact: dict[str, Any] = {
        "artifact_class": "EXACT_AP_WORKER_LOCALIZATION_DIAGNOSTIC",
        "status": "DIAGNOSTIC_ONLY",
        "scope": "one median PS+V_A failure state plus Full median positive control",
        "model_and_security_changes": False,
        "classification": "PENDING_UNTIL_DIAGNOSTIC_COMPLETE",
        "cases": {},
        "provenance": {
            "worker": str(WORKER.relative_to(ROOT)),
            "worker_sha256": _sha256(WORKER),
            "analysis_runner": str((ROOT / "scripts" / "run_analysis_figures.py").relative_to(ROOT)),
            "analysis_runner_sha256": _sha256(ROOT / "scripts" / "run_analysis_figures.py"),
            "checkpoint_ps_sha256": _sha256(PS_CHECKPOINT),
            "checkpoint_full_sha256": _sha256(FULL_CHECKPOINT),
            "final_model_spec_sha256": _sha256(ROOT / "docs" / "FINAL_MODEL_SPEC.md"),
            "precision_rows": args.digits,
            "independent_precision_digits": args.independent_digits,
        },
    }
    cases = (("ps_va", PS_CHECKPOINT), ("full", FULL_CHECKPOINT)) if args.mode == "both" else (
        (args.mode, PS_CHECKPOINT if args.mode == "ps_va" else FULL_CHECKPOINT),
    )
    independent_digits = None if args.skip_independent else args.independent_digits
    for mode, checkpoint in cases:
        artifact["cases"][mode] = _run_case(mode, checkpoint, args.digits, independent_digits, args.full_eigh)
        if args.run_worker:
            frozen = artifact["cases"][mode]["frozen_input"]
            artifact["cases"][mode]["unchanged_worker_replay"] = _worker_replay(
                frozen["request"], args.worker_digits, args.worker_timeout
            )
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(artifact, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(artifact, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": artifact["status"], "output": str(args.output), "cases": list(artifact["cases"])}, indent=2))


if __name__ == "__main__":
    main()
