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
    sectors=_sectors(p,z); pairs=[torch.linalg.eigh(x) for x in sectors]
    values=[x[0] for x in pairs]; vectors=[x[1] for x in pairs]
    minimum=min(float(x.min()) for x in values); maximum=max(float(x.max()) for x in values)
    reconstruction=max(float((g-u@torch.diag(v).to(torch.complex128)@u.mH).norm()/g.norm()) for g,v,u in zip(sectors,values,vectors))
    gate = {
    "all_sectors_positive": minimum > 0,
    "minimum_eigenvalue": minimum,
    "sector_condition_number": (
        math.inf if minimum <= 0 else maximum / minimum
    ),
    "sector_reconstruction_residual": reconstruction,}
    if not gate["all_sectors_positive"] or gate["sector_condition_number"]>FAST_MAX_CONDITION or reconstruction>FAST_MAX_RESIDUAL: return None,gate
    square=[torch.diag(torch.sqrt(v).to(torch.complex128)) for v in values]; b=[]; a=[]; q=[]; c=torch.zeros((),dtype=torch.float64)
    for s in range(4):
        previous=(s-1)%4; m=vectors[s].mH@(z[:,None]*vectors[previous])
        # Factorized right-side Hermitian solves; no elementwise eigenvalue ratios.
        bs=square[s]@torch.linalg.solve(square[previous],m.mH).mH
        aa=square[s]@torch.linalg.solve(square[previous],(square[s]@bs).mH).mH
        b.append(bs); a.append(aa); c+=torch.trace(square[s]@bs@square[previous]@bs.mH).real
        q.append(square[s]@vectors[s].mH/(2*torch.sqrt(p))[None,:])
    t=[a[s]@q[(s-1)%4] for s in range(4)]
    d=sum(torch.sum(q[s].conj()*t[s],dim=0) for s in range(4))
    first=sum(torch.sum(values[(s-1)%4][None,:]*a[s].abs().square()).real for s in range(4))
    subtraction=first-torch.sum(4*p*d.abs().square()).real
    residual=sum(torch.sum(4*p*torch.sum((t[s]-q[s]*d[None,:]).abs().square(),dim=0)).real for s in range(4))
    gate["residual_identity_relative_error"]=abs(float(subtraction-residual))/max(1.,abs(float(subtraction)))
    if gate["residual_identity_relative_error"]>FAST_MAX_RESIDUAL or not bool(torch.isfinite(c)) or not bool(torch.isfinite(residual)): return None,gate
    return {"C":c,"w":residual},gate

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
