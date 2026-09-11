"""Validate the isolated AP custom source-moment VJP against corrected AP."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Iterable

import mpmath as mp
import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import full_support_c4_worker as ap_worker
from src.cvqkd.ap_custom_backward import source_moments_vjp
from src.modulation.geometric_shaping import GlobalGeometricShaping
from src.modulation.joint_ps_gs import reference_ensemble
from src.modulation.normalization import physical_amplitudes
from src.modulation.qam256 import (
    c4_orbit_indices,
    expand_c4_orbit_masses,
    expand_c4_orbit_values,
    square_qam256,
)


CORRECTED_C = "0.85985110654649868138037962728289179096834048571987"
CORRECTED_W = "0.018327610474963502048823295065766568532781601388489"
ENSEMBLE_HASH = "c0e576b1ad55ddd6b5167b3011a5ace9104e2b8d81821b8c0d43b0844a581ab3"
CORRECTED_AP_ARTIFACT_SHA256 = "f81dfd9c713a796b3314268a1e1897ec35ff63e390810df015d4cdd943f69d44"
OLD_CUSTOM_ARTIFACT_SHA256 = "dc11c998f755d328906558b949444e4bf45a088657938f7b4b1c1a13daaf58d4"
TARGET_DIGITS = 800
CHEAP_DIGITS = 80
CHEAP_H_VALUES = tuple(mp.mpf(value) for value in ("1e-3", "3e-4", "1e-4", "3e-5", "1e-5"))
COMBINED_A = mp.mpf("1.7")
COMBINED_B = mp.mpf("-0.8")
ORBIT_INDICES = c4_orbit_indices(device="cpu")[:, 0]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _mp(value: Any) -> mp.mpf:
    return value if isinstance(value, mp.mpf) else mp.mpf(float(value))


def _mp_complex(value: Any) -> mp.mpc:
    if isinstance(value, mp.mpc):
        return value
    if isinstance(value, complex):
        return mp.mpc(value.real, value.imag)
    return mp.mpc(float(value), 0.0)


def _worker_row(p: Iterable[Any], z: Iterable[Any], digits: int) -> dict[str, Any]:
    values = list(p)
    amplitudes = list(z)
    if len(values) == 64:
        row = ap_worker._row([_mp(value) for value in values], [_mp_complex(value) for value in amplitudes], digits)
    else:
        row = _generic_ap_row(values, amplitudes, digits)
    expected_rank = len(values) * 4
    if not row["resolved"] or row["rank"] != expected_rank:
        raise RuntimeError(
            f"corrected AP support unresolved at {digits} digits: "
            f"rank={row['rank']} lambda_min={row['minimum_eigenvalue']}"
        )
    return row


def _generic_ap_row(p: Iterable[Any], z: Iterable[Any], digits: int) -> dict[str, Any]:
    """Independent small-fixture AP oracle; the repository worker is fixed at n=64."""

    probabilities = [_mp(value) for value in p]
    amplitudes = [_mp_complex(value) for value in z]
    n = len(probabilities)
    with mp.workdps(digits):
        blocks = []
        for d in range(4):
            rotation = mp.j ** d
            blocks.append(
                mp.matrix(
                    [
                        [
                            mp.sqrt(probabilities[i] * probabilities[j])
                            * mp.exp(
                                -(
                                    abs(amplitudes[i]) ** 2
                                    + abs(rotation * amplitudes[j]) ** 2
                                )
                                / 2
                                + mp.conj(amplitudes[i]) * rotation * amplitudes[j]
                            )
                            for j in range(n)
                        ]
                        for i in range(n)
                    ]
                )
            )
        sectors = []
        for sector in range(4):
            matrix = mp.zeros(n)
            for d, block in enumerate(blocks):
                matrix += block * mp.j ** (sector * d)
            sectors.append((matrix + matrix.H) / 2)
        eigensystems = [mp.eighe(matrix) for matrix in sectors]
        eigenvalues = [[mp.re(values[i]) for i in range(n)] for values, _ in eigensystems]
        minimum = min(value for values in eigenvalues for value in values)
        if any(value <= 0 for values in eigenvalues for value in values):
            return {
                "digits": digits,
                "rank": sum(value > 0 for values in eigenvalues for value in values),
                "resolved": False,
                "minimum_eigenvalue": mp.nstr(minimum, 50),
            }
        vectors = [vectors for _, vectors in eigensystems]
        square = [vectors[s] * mp.diag([mp.sqrt(value) for value in eigenvalues[s]]) * vectors[s].H for s in range(4)]
        inverse_square = [vectors[s] * mp.diag([1 / mp.sqrt(value) for value in eigenvalues[s]]) * vectors[s].H for s in range(4)]
        inverse = [vectors[s] * mp.diag([1 / value for value in eigenvalues[s]]) * vectors[s].H for s in range(4)]
        diagonal_z = mp.diag(amplitudes)
        diagonal_weight = mp.diag([1 / (2 * mp.sqrt(value)) for value in probabilities])
        c = mp.mpf(0)
        a_matrices = []
        q_matrices = []
        for sector in range(4):
            previous = (sector - 1) % 4
            b = square[sector] * diagonal_z * inverse_square[previous]
            cb = square[sector] * b * square[previous] * b.H
            c += mp.fsum(cb[i, i] for i in range(n)).real
            a_matrices.append(sectors[sector] * diagonal_z * inverse[previous])
            q_matrices.append(square[sector] * diagonal_weight)
        t_matrices = [a_matrices[s] * q_matrices[(s - 1) % 4] for s in range(4)]
        inner = [
            mp.fsum(
                mp.conj(q_matrices[s][i, column]) * t_matrices[s][i, column]
                for s in range(4)
                for i in range(n)
            )
            for column in range(n)
        ]
        w = mp.fsum(
            4
            * probabilities[column]
            * mp.fsum(
                abs(t_matrices[s][i, column] - q_matrices[s][i, column] * inner[column]) ** 2
                for s in range(4)
                for i in range(n)
            )
            for column in range(n)
        )
        return {
            "digits": digits,
            "rank": n * 4,
            "resolved": True,
            "minimum_eigenvalue": mp.nstr(minimum, 50),
            "C": mp.nstr(c, 50),
            "w": mp.nstr(w, 50),
        }


def _custom_forward(p: Iterable[Any], z: Iterable[Any], digits: int) -> tuple[mp.mpf, mp.mpf, mp.mpf]:
    result = source_moments_vjp(
        list(p),
        list(z),
        digits=digits,
        upstream_c=0,
        upstream_w=0,
    )
    return result.c, result.w, result.minimum_eigenvalue


def _custom_directional(
    p: Iterable[Any],
    z: Iterable[Any],
    dp: Iterable[Any],
    dz: Iterable[Any],
    *,
    digits: int,
    upstream_c: mp.mpf,
    upstream_w: mp.mpf,
) -> tuple[mp.mpf, mp.mpf, mp.mpf]:
    result = source_moments_vjp(
        list(p),
        list(z),
        digits=digits,
        upstream_c=upstream_c,
        upstream_w=upstream_w,
    )
    directional = mp.fsum(
        result.grad_p[index] * _mp(dp[index])
        + mp.re(mp.conj(result.grad_z[index]) * _mp_complex(dz[index]))
        for index in range(len(result.grad_p))
    )
    return directional, result.c, result.w


def _production_forward(p: list[float], z: list[complex]) -> tuple[float, float, dict[str, Any]]:
    """Float64 equivalent of the production C4 equations for n<64 fixtures."""

    p_tensor = torch.tensor(p, dtype=torch.float64)
    z_tensor = torch.tensor(z, dtype=torch.complex128)
    rotations = torch.tensor([1, 1j, -1, -1j], dtype=torch.complex128)
    weight = torch.sqrt(p_tensor[:, None] * p_tensor[None, :])
    blocks = []
    for rotation in rotations:
        right = rotation * z_tensor
        blocks.append(weight * torch.exp(-0.5 * (z_tensor.abs().square()[:, None] + right.abs().square()[None, :]) + z_tensor.conj()[:, None] * right[None, :]))
    sectors = []
    for sector in range(4):
        matrix = sum(blocks[d] * rotations[(sector * d) % 4] for d in range(4))
        sectors.append(0.5 * (matrix + matrix.mH))
    eigensystems = [torch.linalg.eigh(matrix) for matrix in sectors]
    square = [vectors @ torch.diag(torch.sqrt(values)).to(torch.complex128) @ vectors.mH for values, vectors in eigensystems]
    inverse = [vectors @ torch.diag(1 / values).to(torch.complex128) @ vectors.mH for values, vectors in eigensystems]
    inverse_square = [vectors @ torch.diag(1 / torch.sqrt(values)).to(torch.complex128) @ vectors.mH for values, vectors in eigensystems]
    diagonal_z = torch.diag(z_tensor)
    diagonal_weight = torch.diag(1 / (2 * torch.sqrt(p_tensor))).to(torch.complex128)
    c = torch.zeros((), dtype=torch.float64)
    a_matrices = []
    q_matrices = []
    for sector in range(4):
        previous = (sector - 1) % 4
        b = square[sector] @ diagonal_z @ inverse_square[previous]
        c = c + torch.trace(square[sector] @ b @ square[previous] @ b.mH).real
        a_matrices.append(sectors[sector] @ diagonal_z @ inverse[previous])
        q_matrices.append(square[sector] @ diagonal_weight)
    transformed = [a_matrices[s] @ q_matrices[(s - 1) % 4] for s in range(4)]
    inner = sum(torch.sum(q_matrices[s].conj() * transformed[s], dim=0) for s in range(4))
    w = sum(
        torch.sum(4 * p_tensor * torch.sum((transformed[s] - q_matrices[s] * inner[None, :]).abs().square(), dim=0)).real
        for s in range(4)
    )
    return float(c), float(w), {"minimum_eigenvalue": min(float(values.min()) for values, _ in eigensystems)}


def _relative_error(observed: mp.mpf, reference: mp.mpf) -> mp.mpf:
    return abs(observed - reference) / max(abs(reference), mp.mpf("1e-40"))


def _fixture_inputs() -> dict[str, tuple[list[float], list[complex], list[float], list[complex]]]:
    x = np.arange(1, 5, dtype=np.float64)
    uniform = np.full(4, 1.0 / 4.0, dtype=np.float64)
    mild = 1.0 + 0.01 * np.sin(x)
    mild /= mild.sum()
    dp = np.sin(0.37 * x)
    dp -= dp.mean()
    dp /= np.max(np.abs(dp))
    z_real = 2.0 * np.array([0.35 + 0.10j, 0.75 - 0.20j, 1.10 + 0.45j, 1.45 - 0.55j])
    z_perturbed_real = z_real + 0.1 * np.sin(x)
    z_perturbed_imag = z_real + 0.1j * np.sin(x)
    dz = 0.01 * (np.cos(0.19 * x) + 1j * np.sin(0.23 * x))
    return {
        "uniform": (uniform.tolist(), z_real.tolist(), dp.tolist(), dz.tolist()),
        "nonuniform_positive": (mild.tolist(), z_real.tolist(), dp.tolist(), dz.tolist()),
        "perturbed_real": (mild.tolist(), z_perturbed_real.tolist(), dp.tolist(), dz.tolist()),
        "perturbed_imaginary": (mild.tolist(), z_perturbed_imag.tolist(), dp.tolist(), dz.tolist()),
    }


def _fixture_record(name: str, digits: int = CHEAP_DIGITS) -> dict[str, Any]:
    p, z, dp, dz = _fixture_inputs()[name]
    n = len(p)
    ap = _worker_row(p, z, digits)
    custom_c, custom_w, custom_minimum = _custom_forward(p, z, digits)
    production_c, production_w, gate = _production_forward(p, z)
    custom_dj, _, _ = _custom_directional(
        p,
        z,
        dp,
        dz,
        digits=digits,
        upstream_c=COMBINED_A,
        upstream_w=COMBINED_B,
    )
    custom_dc, _, _ = _custom_directional(
        p,
        z,
        dp,
        dz,
        digits=digits,
        upstream_c=mp.mpf(1),
        upstream_w=mp.mpf(0),
    )
    custom_dw, _, _ = _custom_directional(
        p,
        z,
        dp,
        dz,
        digits=digits,
        upstream_c=mp.mpf(0),
        upstream_w=mp.mpf(1),
    )
    h_rows = []
    for h in CHEAP_H_VALUES:
        plus = _worker_row([p[i] + float(h) * dp[i] for i in range(n)], [z[i] + complex(h) * dz[i] for i in range(n)], digits)
        minus = _worker_row([p[i] - float(h) * dp[i] for i in range(n)], [z[i] - complex(h) * dz[i] for i in range(n)], digits)
        ap_dj = (
            COMBINED_A * (mp.mpf(plus["C"]) - mp.mpf(minus["C"]))
            + COMBINED_B * (mp.mpf(plus["w"]) - mp.mpf(minus["w"]))
        ) / (2 * h)
        h_rows.append(
            {
                "h": mp.nstr(h, 20),
                "AP_dC": mp.nstr((mp.mpf(plus["C"]) - mp.mpf(minus["C"])) / (2 * h), 40),
                "AP_dw": mp.nstr((mp.mpf(plus["w"]) - mp.mpf(minus["w"])) / (2 * h), 40),
                "AP_dJ": mp.nstr(ap_dj, 40),
            }
        )
    selected = mp.mpf(h_rows[-1]["AP_dJ"])
    selected_dc = mp.mpf(h_rows[-1]["AP_dC"])
    selected_dw = mp.mpf(h_rows[-1]["AP_dw"])
    adjacent_errors = [
        abs(mp.mpf(h_rows[index]["AP_dJ"]) - mp.mpf(h_rows[index + 1]["AP_dJ"]))
        for index in range(len(h_rows) - 1)
    ]
    selected_error = abs(custom_dj - selected)
    allowance = mp.mpf("1e-6") * max(abs(custom_dj), abs(selected), mp.mpf(1))
    plateau = any(error <= allowance for error in adjacent_errors[-2:])
    return {
        "fixture": name,
        "digits": digits,
        "support": {
            "rank": ap["rank"],
            "minimum_eigenvalue": ap["minimum_eigenvalue"],
            "custom_minimum_eigenvalue": mp.nstr(custom_minimum, 50),
        },
        "forward": {
            "production_C": production_c,
            "ap_C": ap["C"],
            "custom_C": mp.nstr(custom_c, 50),
            "production_w": production_w,
            "ap_w": ap["w"],
            "custom_w": mp.nstr(custom_w, 50),
            "production_C_abs_error": float(abs(mp.mpf(production_c) - mp.mpf(ap["C"]))),
            "production_w_abs_error": float(abs(mp.mpf(production_w) - mp.mpf(ap["w"]))),
            "custom_C_abs_error": mp.nstr(abs(custom_c - mp.mpf(ap["C"])), 30),
            "custom_w_abs_error": mp.nstr(abs(custom_w - mp.mpf(ap["w"])), 30),
        },
        "direction": {
            "h_sweep": h_rows,
            "selected_h": h_rows[-1]["h"],
            "AP_dJ": mp.nstr(selected, 40),
            "custom_dJ": mp.nstr(custom_dj, 40),
            "absolute_error": mp.nstr(selected_error, 30),
            "relative_error": mp.nstr(_relative_error(custom_dj, selected), 30),
            "adjacent_errors": [mp.nstr(error, 30) for error in adjacent_errors],
            "passes": plateau and selected_error <= allowance,
        },
        "component_direction": {
            "selected_AP_dC": mp.nstr(selected_dc, 40),
            "custom_dC": mp.nstr(custom_dc, 40),
            "dC_absolute_error": mp.nstr(abs(custom_dc - selected_dc), 30),
            "dC_relative_error": mp.nstr(_relative_error(custom_dc, selected_dc), 30),
            "selected_AP_dw": mp.nstr(selected_dw, 40),
            "custom_dw": mp.nstr(custom_dw, 40),
            "dw_absolute_error": mp.nstr(abs(custom_dw - selected_dw), 30),
            "dw_relative_error": mp.nstr(_relative_error(custom_dw, selected_dw), 30),
            "passes": (
                abs(custom_dc - selected_dc) <= mp.mpf("1e-6") * max(abs(custom_dc), abs(selected_dc), mp.mpf(1))
                and abs(custom_dw - selected_dw) <= mp.mpf("1e-6") * max(abs(custom_dw), abs(selected_dw), mp.mpf(1))
            ),
        },
        "production_gate": gate,
    }


def _complex_convention_record(digits: int = CHEAP_DIGITS) -> dict[str, Any]:
    p, z, _, dz = _fixture_inputs()["uniform"]
    checks = {}
    for name, perturbation in (
        ("real_alpha", [complex(value.real, 0.0) for value in dz]),
        ("imaginary_alpha", [complex(0.0, value.imag) for value in dz]),
    ):
        dp = [0.0] * len(p)
        custom, _, _ = _custom_directional(
            p,
            z,
            dp,
            perturbation,
            digits=digits,
            upstream_c=COMBINED_A,
            upstream_w=COMBINED_B,
        )
        h = mp.mpf("1e-5")
        plus = _worker_row([p[index] for index in range(len(p))], [z[index] + complex(h) * perturbation[index] for index in range(len(p))], digits)
        minus = _worker_row([p[index] for index in range(len(p))], [z[index] - complex(h) * perturbation[index] for index in range(len(p))], digits)
        reference = (
            COMBINED_A * (mp.mpf(plus["C"]) - mp.mpf(minus["C"]))
            + COMBINED_B * (mp.mpf(plus["w"]) - mp.mpf(minus["w"]))
        ) / (2 * h)
        error = abs(custom - reference)
        allowance = mp.mpf("1e-6") * max(abs(custom), abs(reference), mp.mpf(1))
        checks[name] = {
            "AP_dJ": mp.nstr(reference, 40),
            "custom_dJ": mp.nstr(custom, 40),
            "absolute_error": mp.nstr(error, 30),
            "relative_error": mp.nstr(_relative_error(custom, reference), 30),
            "passes": error <= allowance,
        }
    return {"digits": digits, "checks": checks, "passes": all(row["passes"] for row in checks.values())}


def _target_base() -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    ensemble = reference_ensemble("uniform", batch_size=1, modulation_variance=1.0)
    ensemble.validate()
    if ensemble_row_sha256(ensemble, 0) != ENSEMBLE_HASH:
        raise AssertionError("target ensemble hash mismatch")
    base_p = ensemble.probabilities[0]
    base_relative = ensemble.raw_constellation
    base_gs = GlobalGeometricShaping(square_qam256())
    raw_coordinates = base_gs.raw_coordinates.detach().clone()
    return base_p, base_relative, raw_coordinates


def ensemble_row_sha256(ensemble, row: int) -> str:
    """Local import-free copy of the existing provenance hash entry point."""

    digest = hashlib.sha256()
    for name, tensor in (
        ("probabilities", ensemble.probabilities[row]),
        ("amplitudes", ensemble.amplitudes[row]),
        ("declared_va", ensemble.declared_va[row]),
    ):
        digest.update(name.encode("ascii"))
        digest.update(str(tensor.dtype).encode("ascii"))
        digest.update(repr(tuple(tensor.shape)).encode("ascii"))
        digest.update(tensor.detach().to(device="cpu").contiguous().numpy().tobytes())
    return digest.hexdigest()


def _target_direction(family: str, theta: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    base_p, base_relative, raw_coordinates = _target_base()
    if family == "ps":
        x = torch.arange(1, 65, dtype=torch.float64)
        direction = torch.sin(0.37 * x)
        direction = direction - direction.mean()
        direction = direction / direction.abs().max()
        orbit_masses = torch.softmax(theta * direction, dim=0)
        probabilities = expand_c4_orbit_masses(orbit_masses).unsqueeze(0)
        relative = base_relative.unsqueeze(0)
        variance = torch.ones(1, dtype=torch.float64)
    elif family in {"gs_real", "gs_imag"}:
        coordinates = raw_coordinates.clone()
        coordinates[0, 0 if family == "gs_real" else 1] += theta
        prototypes = torch.view_as_complex(coordinates.contiguous())
        relative_prototypes = prototypes / torch.sqrt(prototypes.abs().square().mean())
        relative = expand_c4_orbit_values(relative_prototypes).unsqueeze(0)
        probabilities = base_p.unsqueeze(0)
        variance = torch.ones(1, dtype=torch.float64)
    elif family == "va":
        probabilities = base_p.unsqueeze(0)
        relative = base_relative.unsqueeze(0)
        variance = (1.0 + theta).reshape(1)
    else:
        raise ValueError(f"unsupported target family: {family}")
    amplitudes = physical_amplitudes(probabilities, relative, variance)
    return probabilities[0, ORBIT_INDICES], amplitudes[0, ORBIT_INDICES]


def _target_directional_inputs(family: str) -> tuple[list[float], list[complex], list[float], list[complex]]:
    theta = torch.zeros((), dtype=torch.float64, requires_grad=True)

    def vector(value: torch.Tensor) -> torch.Tensor:
        p, z = _target_direction(family, value)
        return torch.cat((p, z.real, z.imag))

    center, tangent = torch.autograd.functional.jvp(
        vector,
        (theta,),
        (torch.ones_like(theta),),
        create_graph=False,
        strict=True,
    )
    p = center[:64]
    z = center[64:128] + 1j * center[128:]
    dp = tangent[:64]
    dz = tangent[64:128] + 1j * tangent[128:]
    return p.tolist(), z.tolist(), dp.tolist(), dz.tolist()


def _target_structure_record(family: str) -> dict[str, Any]:
    p, z, dp, dz = _target_directional_inputs(family)
    p_tensor = torch.tensor(p, dtype=torch.float64)
    z_tensor = torch.tensor(z, dtype=torch.complex128)
    full_p = expand_c4_orbit_masses((4.0 * p_tensor).unsqueeze(0))[0]
    full_z = expand_c4_orbit_values(z_tensor).reshape(-1)
    direction_payload = json.dumps(
        {
            "p": p,
            "z": [[complex(value).real, complex(value).imag] for value in z],
            "dp": dp,
            "dz": [[complex(value).real, complex(value).imag] for value in dz],
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "family": family,
        "prototype_count": len(p),
        "positive_probabilities": bool(torch.all(full_p > 0)),
        "probability_sum": float(full_p.sum()),
        "unique_state_count": len({(complex(value).real.hex(), complex(value).imag.hex()) for value in full_z.tolist()}),
        "directional_probability_sum": float(sum(dp)),
        "directional_z_norm": float(torch.linalg.vector_norm(torch.tensor([complex(value) for value in dz])).item()),
        "direction_sha256": hashlib.sha256(direction_payload).hexdigest(),
    }


def _target_validation(family: str, digits: int, h_values: tuple[mp.mpf, ...]) -> dict[str, Any]:
    structure = _target_structure_record(family)
    if not structure["positive_probabilities"] or structure["probability_sum"] != 1.0 or structure["unique_state_count"] != 256:
        raise RuntimeError(f"target physical mapping failed structure checks: {structure}")
    p, z, dp, dz = _target_directional_inputs(family)
    print(f"{family}: starting custom VJP at {digits} digits", flush=True)
    started_custom = time.perf_counter()
    custom_j, custom_c, custom_w = _custom_directional(
        p,
        z,
        dp,
        dz,
        digits=digits,
        upstream_c=COMBINED_A,
        upstream_w=COMBINED_B,
    )
    custom_runtime = time.perf_counter() - started_custom
    h_rows = []
    for h in h_values:
        print(f"{family}: AP finite difference h={h}", flush=True)
        plus_p = [p[index] + float(h) * dp[index] for index in range(64)]
        minus_p = [p[index] - float(h) * dp[index] for index in range(64)]
        plus_z = [z[index] + complex(h) * dz[index] for index in range(64)]
        minus_z = [z[index] - complex(h) * dz[index] for index in range(64)]
        if min(plus_p) <= 0 or min(minus_p) <= 0:
            raise RuntimeError(f"target probability support failed at h={h}")
        started = time.perf_counter()
        plus = _worker_row(plus_p, plus_z, digits)
        plus_runtime = time.perf_counter() - started
        started = time.perf_counter()
        minus = _worker_row(minus_p, minus_z, digits)
        minus_runtime = time.perf_counter() - started
        ap_dc = (mp.mpf(plus["C"]) - mp.mpf(minus["C"])) / (2 * h)
        ap_dw = (mp.mpf(plus["w"]) - mp.mpf(minus["w"])) / (2 * h)
        ap_dj = COMBINED_A * ap_dc + COMBINED_B * ap_dw
        h_rows.append(
            {
                "h": mp.nstr(h, 20),
                "AP_dC": mp.nstr(ap_dc, 50),
                "AP_dw": mp.nstr(ap_dw, 50),
                "AP_dJ": mp.nstr(ap_dj, 50),
                "plus_rank": plus["rank"],
                "minus_rank": minus["rank"],
                "plus_minimum_eigenvalue": plus["minimum_eigenvalue"],
                "minus_minimum_eigenvalue": minus["minimum_eigenvalue"],
                "plus_runtime_seconds": plus_runtime,
                "minus_runtime_seconds": minus_runtime,
            }
        )
    selected = mp.mpf(h_rows[-1]["AP_dJ"])
    allowance = mp.mpf("1e-6") * max(abs(selected), abs(custom_j), mp.mpf(1))
    adjacent = [
        abs(mp.mpf(h_rows[index]["AP_dJ"]) - mp.mpf(h_rows[index + 1]["AP_dJ"]))
        for index in range(len(h_rows) - 1)
    ]
    return {
        "family": family,
        "digits": digits,
        "structure": structure,
        "custom_forward": {"C": mp.nstr(custom_c, 50), "w": mp.nstr(custom_w, 50)},
        "custom_directional_combined": mp.nstr(custom_j, 50),
        "custom_vjp_runtime_seconds": custom_runtime,
        "h_rows": h_rows,
        "selected_h": h_rows[-1]["h"],
        "selected_AP_dJ": mp.nstr(selected, 50),
        "combined_absolute_error": mp.nstr(abs(custom_j - selected), 40),
        "combined_relative_error": mp.nstr(_relative_error(custom_j, selected), 40),
        "adjacent_combined_errors": [mp.nstr(value, 40) for value in adjacent],
        "passes": bool(abs(custom_j - selected) <= allowance and any(value <= allowance for value in adjacent[-2:])),
    }


def _git_metadata() -> dict[str, Any]:
    def run(*args: str) -> str | None:
        try:
            return subprocess.check_output(["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
        except (OSError, subprocess.CalledProcessError):
            return None

    return {"commit": run("rev-parse", "HEAD"), "branch": run("branch", "--show-current"), "dirty": bool(run("status", "--porcelain"))}


def build_cheap_artifact() -> dict[str, Any]:
    started = time.perf_counter()
    fixtures = [_fixture_record(name) for name in _fixture_inputs()]
    complex_convention = _complex_convention_record()
    target_structures = [_target_structure_record(family) for family in ("ps", "gs_real", "gs_imag", "va")]
    fixtures_pass = all(row["direction"]["passes"] and row["component_direction"]["passes"] for row in fixtures)
    return {
        "status": "CHEAP_FIXTURE_VALIDATION_PASS" if fixtures_pass and complex_convention["passes"] else "AP_CUSTOM_BACKWARD_NOT_VALIDATED",
        "scope": "corrected AP custom backward cheap fixture validation only",
        "corrected_source_moments": {"C": CORRECTED_C, "w": CORRECTED_W},
        "fixtures": fixtures,
        "complex_gradient_convention": complex_convention,
        "target_structure_preflight": target_structures,
        "runtime_seconds": time.perf_counter() - started,
        "provenance": {
            "repository": _git_metadata(),
            "corrected_worker_sha256": _sha256(ROOT / "scripts" / "full_support_c4_worker.py"),
            "custom_backward_sha256": _sha256(ROOT / "src" / "cvqkd" / "ap_custom_backward.py"),
            "corrected_ap_artifact_sha256": CORRECTED_AP_ARTIFACT_SHA256,
            "superseded_custom_artifact_sha256": OLD_CUSTOM_ARTIFACT_SHA256,
            "exact_ensemble_sha256": ENSEMBLE_HASH,
        },
        "lifecycle_guards": {"training_ran": False, "optimizer_step": False, "final_test_accessed": False},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("cheap", "target"), default="cheap")
    parser.add_argument("--output", type=Path, default=ROOT / "results" / "ap_custom_backward_corrected_directional_validation_20260911.json")
    parser.add_argument("--digits", type=int, default=TARGET_DIGITS)
    parser.add_argument("--family", choices=("ps", "gs_real", "gs_imag", "va"), default="ps")
    parser.add_argument("--h-values", nargs="+", default=["1e-4"])
    args = parser.parse_args()
    if args.phase == "cheap":
        artifact = build_cheap_artifact()
    else:
        started = time.perf_counter()
        artifact = build_cheap_artifact()
        provenance = {
            "repository": _git_metadata(),
            "corrected_worker_sha256": _sha256(ROOT / "scripts" / "full_support_c4_worker.py"),
            "custom_backward_sha256": _sha256(ROOT / "src" / "cvqkd" / "ap_custom_backward.py"),
            "corrected_ap_artifact_sha256": CORRECTED_AP_ARTIFACT_SHA256,
            "exact_ensemble_sha256": ENSEMBLE_HASH,
            "frozen_model_sha256": _sha256(ROOT / "docs" / "FINAL_MODEL_SPEC.md"),
        }
        try:
            direction = _target_validation(args.family, args.digits, tuple(mp.mpf(value) for value in args.h_values))
            artifact["status"] = "TARGET_DIRECTIONAL_VALIDATION_PASS" if direction["passes"] else "AP_CUSTOM_BACKWARD_NOT_VALIDATED"
            artifact["scope"] = "cheap fixtures plus one bounded corrected full-support Case A target direction"
            artifact["direction"] = direction
            artifact["target_runtime_seconds"] = time.perf_counter() - started
            artifact["provenance"].update(provenance)
        except Exception as error:
            artifact["status"] = "AP_CUSTOM_BACKWARD_NOT_VALIDATED"
            artifact["scope"] = "cheap fixtures plus bounded corrected full-support Case A target direction stopped fail-closed"
            artifact["failure_reason"] = f"{type(error).__name__}: {error}"
            artifact["target_runtime_seconds"] = time.perf_counter() - started
            artifact["provenance"].update(provenance)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(artifact, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    print(artifact["status"])
    print(f"Wrote {args.output}")
    return 0 if artifact["status"] == "CHEAP_FIXTURE_VALIDATION_PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
