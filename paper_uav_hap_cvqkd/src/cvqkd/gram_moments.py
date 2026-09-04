"""Support-free C4 coherent-state Gram source moments."""
from __future__ import annotations
from dataclasses import dataclass
import json, math
from pathlib import Path
import subprocess, sys
from typing import Any
import torch
from src.modulation.joint_ps_gs import Ensemble
from src.modulation.qam256 import c4_orbit_indices
from .spectral_frechet import hermitian_inverse_sqrt, hermitian_sqrt

FAST_MAX_CONDITION = 1.0e6
FAST_MAX_RESIDUAL = 1.0e-12
PRECISION_LADDER = (1050, 1250, 1450)

class FullSupportGradientUnavailable(RuntimeError):
    """The arbitrary-precision fallback is evaluation-only."""

@dataclass(frozen=True)
class GramMomentResult:
    coherent_correlation: torch.Tensor
    w: torch.Tensor
    diagnostics: tuple[dict[str, Any], ...]

def _hex(value: float) -> str: return float(value).hex()

def _sectors(p: torch.Tensor, z: torch.Tensor) -> list[torch.Tensor]:
    rotations = torch.tensor([1, 1j, -1, -1j], dtype=torch.complex128)
    weight = torch.sqrt(p[:, None] * p[None, :]); blocks=[]
    for rotation in rotations:
        right=rotation*z
        blocks.append(weight*torch.exp(-.5*(z.abs().square()[:,None]+right.abs().square()[None,:])+z.conj()[:,None]*right[None,:]))
    answer=[]
    for s in range(4):
        matrix=sum(blocks[d]*rotations[(s*d)%4] for d in range(4)); answer.append(.5*(matrix+matrix.mH))
    return answer

def _fast(p: torch.Tensor, z: torch.Tensor) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    return _fast_from_sectors(p, z, _sectors(p, z))


def _fast_from_sectors(
    p: torch.Tensor, z: torch.Tensor, sectors: list[torch.Tensor]
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    if len(sectors) != 4 or any(matrix.shape != (64, 64) for matrix in sectors):
        raise ValueError("C4 fast path requires four 64-by-64 sectors")
    # Gate-only eigensystems are detached. Differentiable work below uses
    # whole-matrix Fréchet functions and solves, never eigenvectors.
    with torch.no_grad():
        pairs = [torch.linalg.eigh(matrix.detach()) for matrix in sectors]
        values = [pair[0] for pair in pairs]
        vectors = [pair[1] for pair in pairs]
        minimum = min(float(value.min()) for value in values)
        maximum = max(float(value.max()) for value in values)
        reconstruction = max(
            float(
                (matrix.detach() - vector @ torch.diag(value).to(torch.complex128) @ vector.mH).norm()
                / matrix.detach().norm()
            )
            for matrix, value, vector in zip(sectors, values, vectors)
        )
    gate = {
    "all_sectors_positive": minimum > 0,
    "minimum_eigenvalue": minimum,
    "sector_condition_number": (
        math.inf if minimum <= 0 else maximum / minimum
    ),
    "sector_reconstruction_residual": reconstruction,}
    if not gate["all_sectors_positive"] or gate["sector_condition_number"] > FAST_MAX_CONDITION or reconstruction > FAST_MAX_RESIDUAL:
        return None, gate

    square = [hermitian_sqrt(matrix) for matrix in sectors]
    inverse_square = [hermitian_inverse_sqrt(matrix) for matrix in sectors]
    diagonal_z = torch.diag(z)
    diagonal_weight = torch.diag(1.0 / (2.0 * torch.sqrt(p))).to(torch.complex128)
    b_blocks = []
    a_blocks = []
    coefficients = []
    correlation = torch.zeros((), dtype=torch.float64, device=z.device)
    for sector in range(4):
        previous = (sector - 1) % 4
        b = square[sector] @ diagonal_z @ inverse_square[previous]
        left = sectors[sector] @ diagonal_z
        a = torch.linalg.solve(sectors[previous], left.mH).mH
        b_blocks.append(b)
        a_blocks.append(a)
        correlation = correlation + torch.trace(
            square[sector] @ b @ square[previous] @ b.mH
        ).real
        coefficients.append(square[sector] @ diagonal_weight)

    transformed = [
        a_blocks[sector] @ coefficients[(sector - 1) % 4]
        for sector in range(4)
    ]
    inner = sum(
        torch.sum(coefficients[sector].conj() * transformed[sector], dim=0)
        for sector in range(4)
    )
    first = sum(
        torch.sum((a_blocks[sector] @ square[(sector - 1) % 4]).abs().square()).real
        for sector in range(4)
    )
    subtraction = first - torch.sum(4.0 * p * inner.abs().square()).real
    residual = sum(
        torch.sum(
            4.0 * p
            * torch.sum(
                (transformed[sector] - coefficients[sector] * inner[None, :]).abs().square(),
                dim=0,
            )
        ).real
        for sector in range(4)
    )
    gate["residual_identity_relative_error"] = abs(float((subtraction - residual).detach())) / max(
        1.0, abs(float(subtraction.detach()))
    )
    gate["spectral_backward"] = "CUSTOM_LOEWNER_FRECHET"
    if gate["residual_identity_relative_error"] > FAST_MAX_RESIDUAL or not bool(
        torch.isfinite(correlation)
    ) or not bool(torch.isfinite(residual)):
        return None, gate
    return {"C": correlation, "w": residual}, gate

def _fallback(p: torch.Tensor,z: torch.Tensor) -> dict[str,Any]:
    worker=Path(__file__).parents[2]/"scripts"/"full_support_c4_worker.py"
    request={"probabilities_float64_hex":[_hex(x) for x in p.detach().tolist()],"prototypes_float64_hex":[[_hex(complex(x).real),_hex(complex(x).imag)] for x in z.detach().tolist()],"precision_ladder_decimal_digits":list(PRECISION_LADDER)}
    try: done=subprocess.run([sys.executable,str(worker)],input=json.dumps(request,sort_keys=True),text=True,capture_output=True,timeout=3600,check=False)
    except subprocess.TimeoutExpired: return {"status":"FAIL_CLOSED","reason":"fallback timeout"}
    if done.returncode: return {"status":"FAIL_CLOSED","reason":done.stderr[-2000:] or f"worker exit {done.returncode}"}
    try: return json.loads(done.stdout)
    except json.JSONDecodeError as error: return {"status":"FAIL_CLOSED","reason":f"worker JSON failure: {error}"}

def c4_gram_source_moments(
    ensemble: Ensemble,
    *,
    density_eigenvalue_tolerance: float,
    physicality_tolerance: float = 1e-10,
) -> GramMomentResult:
    """Full mathematical support; threshold is diagnostic metadata only."""

    ensemble.validate()

    if (
        not ensemble.c4_symmetric
        or ensemble.probabilities.dtype != torch.float64
        or ensemble.amplitudes.dtype != torch.complex128
    ):
        raise ValueError(
            "Support-free C4 Gram requires a float64/complex128 C4 ensemble."
        )

    if (
        not math.isfinite(density_eigenvalue_tolerance)
        or density_eigenvalue_tolerance <= 0
    ):
        raise ValueError(
            "diagnostic threshold must be finite and positive."
        )

    indices = c4_orbit_indices(
        device=ensemble.probabilities.device
    )

    cs = []
    ws = []
    diagnostics = []

    for row in range(ensemble.probabilities.shape[0]):
        p = ensemble.probabilities[row, indices[:, 0]]
        z = ensemble.amplitudes[row, indices[:, 0]]

        fast, gate = _fast(p, z)

        if fast is None:
            if p.requires_grad or z.requires_grad:
                raise FullSupportGradientUnavailable(
                    "FULL_SUPPORT_FALLBACK_EVALUATION_ONLY"
                )

            fallback = _fallback(p, z)

            if fallback.get("status") != "FULL_SUPPORT_CONVERGED":
                raise FloatingPointError(
                    "full-support fallback failed closed: "
                    f"{fallback.get('reason', 'unresolved')}"
                )

            c = torch.tensor(
                float(fallback["C"]),
                dtype=torch.float64,
            )

            w = torch.tensor(
                float(fallback["w"]),
                dtype=torch.float64,
            )

            route = "ARBITRARY_PRECISION_FALLBACK"
            rows = fallback["rows"]

            # The worker reports this for every precision row.
            minimum_eigenvalue = min(
                float(item["minimum_eigenvalue"])
                for item in rows
            )

        else:
            c = fast["C"]
            w = fast["w"]
            route = "COMPLEX128_FAST"
            rows = []

            # _fast() already computes this from all C4 sectors.
            minimum_eigenvalue = float(
                gate["minimum_eigenvalue"]
            )

        if (
            not bool(torch.isfinite(c))
            or not bool(torch.isfinite(w))
            or bool(w < -physicality_tolerance)
        ):
            raise FloatingPointError(
                "support-free C4 moments nonfinite or nonphysical"
            )

        cs.append(c)
        ws.append(w)

        diagnostics.append(
            {
                "route": route,
                "fast_path_gate": gate,
                "fallback_precisions": (
                    list(PRECISION_LADDER)
                    if rows
                    else []
                ),
                "fallback_rows": rows,

                # REQUIRED BY holevo.py
                "minimum_eigenvalue": minimum_eigenvalue,

                "support_size": 256,
                "numerical_retained_rank": 256,
                "tau_diagnostic": density_eigenvalue_tolerance,
                "exact_input_provenance": "float.hex binary64",
            }
        )

    return GramMomentResult(
        torch.stack(cs),
        torch.stack(ws),
        tuple(diagnostics),
    )
