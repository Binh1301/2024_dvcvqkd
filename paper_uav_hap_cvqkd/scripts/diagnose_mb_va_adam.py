"""Verify Adam + central finite differences without changing QKD physics."""

from __future__ import annotations

import copy
import csv
import json
import math
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "results" / "diagnostic_mb_va_adam"
TRACE_FIELDS = (
    "iteration", "u_mb", "u_va", "nu_mb", "V_A", "K", "I_AB", "chi_BE",
    "dK_dnu", "dK_dVA", "grad_u_mb", "grad_u_va", "adam_step_mb", "adam_step_va",
)


def _logit(value: float) -> float:
    if not 0.0 < value < 1.0:
        raise ValueError("logit input must lie in (0,1).")
    return math.log(value / (1.0 - value))


class MBVAParameters(torch.nn.Module):
    def __init__(self, nu: float = 0.10, va: float = 2.0):
        super().__init__()
        self.u_mb = torch.nn.Parameter(torch.tensor(_logit(nu / 0.30), dtype=torch.float64))
        self.u_va = torch.nn.Parameter(torch.tensor(_logit((va - 0.1) / 3.9), dtype=torch.float64))

    def forward(self) -> tuple[torch.Tensor, torch.Tensor]:
        return 0.30 * torch.sigmoid(self.u_mb), 0.1 + 3.9 * torch.sigmoid(self.u_va)

    def assign_loss_gradients(self, dK_dnu: float, dK_dva: float) -> tuple[float, float]:
        if not all(math.isfinite(value) for value in (dK_dnu, dK_dva)):
            raise FloatingPointError("Finite-difference gradient is nonfinite.")
        with torch.no_grad():
            s_mb = torch.sigmoid(self.u_mb)
            s_va = torch.sigmoid(self.u_va)
            # torch Adam minimizes, so gradients are for loss=-K.
            grad_mb = -dK_dnu * 0.30 * s_mb * (1.0 - s_mb)
            grad_va = -dK_dva * 3.9 * s_va * (1.0 - s_va)
            self.u_mb.grad = grad_mb.clone()
            self.u_va.grad = grad_va.clone()
        return float(grad_mb), float(grad_va)


def synthetic_objective(nu: float, va: float) -> dict[str, float]:
    value = -(nu - 0.17) ** 2 - 0.5 * (va - 2.2) ** 2
    return {"K": value, "I_AB": 0.0, "chi_BE": -value}


def central_difference(evaluate, nu: float, va: float, coordinate: str, h: float) -> float:
    if h <= 0.0 or not math.isfinite(h):
        raise ValueError("Finite-difference h must be finite and positive.")
    if coordinate == "nu":
        plus, minus = evaluate(nu + h, va), evaluate(nu - h, va)
    elif coordinate == "VA":
        plus, minus = evaluate(nu, va + h), evaluate(nu, va - h)
    else:
        raise ValueError("coordinate must be 'nu' or 'VA'.")
    return (float(plus["K"]) - float(minus["K"])) / (2.0 * h)


def adam_step(model, optimizer, evaluate, h_nu: float, h_va: float) -> dict[str, float]:
    with torch.no_grad():
        nu, va = (float(value) for value in model())
        old_u_mb, old_u_va = float(model.u_mb), float(model.u_va)
    dK_dnu = central_difference(evaluate, nu, va, "nu", h_nu)
    dK_dva = central_difference(evaluate, nu, va, "VA", h_va)
    model_before = copy.deepcopy(model.state_dict())
    optimizer_before = copy.deepcopy(optimizer.state_dict())
    optimizer.zero_grad(set_to_none=True)
    grad_u_mb, grad_u_va = model.assign_loss_gradients(dK_dnu, dK_dva)
    try:
        optimizer.step()
        with torch.no_grad():
            new_nu, new_va = (float(value) for value in model())
            new_u_mb, new_u_va = float(model.u_mb), float(model.u_va)
        result = evaluate(new_nu, new_va)
    except Exception:
        model.load_state_dict(model_before)
        optimizer.load_state_dict(optimizer_before)
        raise
    return {
        "u_mb": new_u_mb, "u_va": new_u_va, "nu_mb": new_nu, "V_A": new_va,
        "K": float(result["K"]), "I_AB": float(result["I_AB"]),
        "chi_BE": float(result["chi_BE"]), "dK_dnu": dK_dnu, "dK_dVA": dK_dva,
        "grad_u_mb": grad_u_mb, "grad_u_va": grad_u_va,
        "adam_step_mb": new_u_mb - old_u_mb, "adam_step_va": new_u_va - old_u_va,
    }


def run_synthetic(iterations: int = 80, learning_rate: float = 0.10) -> tuple[list[dict], dict]:
    model = MBVAParameters(0.10, 2.0)
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    with torch.no_grad():
        initial_nu, initial_va = (float(value) for value in model())
    initial = synthetic_objective(initial_nu, initial_va)
    rows = []
    for iteration in range(1, iterations + 1):
        row = adam_step(model, optimizer, synthetic_objective, 1.0e-3, 1.0e-3)
        row["iteration"] = iteration
        rows.append(row)
        print(" ".join(f"{name}={row[name]:.12g}" for name in TRACE_FIELDS), flush=True)
    final = rows[-1]
    passed = (
        final["K"] > initial["K"]
        and abs(final["nu_mb"] - 0.17) <= 5.0e-3
        and abs(final["V_A"] - 2.2) <= 2.0e-2
    )
    stability = {
        str(h): central_difference(synthetic_objective, 0.15, 2.0, "nu", h)
        for h in (1.0e-2, 5.0e-3, 1.0e-3, 5.0e-4)
    }
    return rows, {
        "status": "PASS" if passed else "FAIL",
        "initial": {"nu_mb": initial_nu, "V_A": initial_va, **initial},
        "final": final,
        "known_maximum": {"nu_mb": 0.17, "V_A": 2.2, "K": 0.0},
        "finite_difference_stability": stability,
    }


def physical_source_coverage() -> dict:
    csv_path = ROOT / "results" / "mb_sweep_fixed_zeta30_VA2.csv"
    available = []
    if csv_path.is_file():
        with csv_path.open(newline="", encoding="utf-8") as stream:
            available = sorted(float(row["nu_mb"]) for row in csv.DictReader(stream) if row["status"] == "PASS")
    dense = [round(0.01 + 0.005 * index, 6) for index in range(59)]
    required_fd = sorted({
        round(center + sign * step, 6)
        for center in (0.05, 0.10, 0.15, 0.20)
        for step in (1.0e-2, 5.0e-3, 1.0e-3, 5.0e-4)
        for sign in (-1.0, 1.0)
    })
    missing_dense = [value for value in dense if value not in available]
    missing_fd = [value for value in required_fd if value not in available]
    return {
        "status": "PASS" if not missing_dense and not missing_fd else "NOT_RUN_SOURCE_MOMENTS_UNAVAILABLE",
        "available_exact_nu": available,
        "required_dense_count": len(dense),
        "missing_dense_count": len(missing_dense),
        "missing_dense_nu": missing_dense,
        "missing_fd_nu": missing_fd,
        "reason": (
            None if not missing_dense and not missing_fd else
            "Exact C,w are missing for physical finite-difference/grid points; interpolation is forbidden."
        ),
    }


def _write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=TRACE_FIELDS)
        writer.writeheader()
        writer.writerows({key: row[key] for key in TRACE_FIELDS} for row in rows)


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    rows, test1 = run_synthetic()
    _write_csv(OUTPUT / "synthetic_adam_trace.csv", rows)
    test2 = physical_source_coverage()
    test3 = {"status": "NOT RUN", "reason": "TEST 2 did not pass."}
    overall = (
        "OPTIMIZER IMPLEMENTATION APPEARS FUNCTIONAL ON SYNTHETIC OBJECTIVE; "
        "PHYSICAL OPTIMIZER NOT VERIFIED"
        if test1["status"] == "PASS" else
        "OPTIMIZER IMPLEMENTATION REQUIRES DEBUGGING"
    )
    report = {
        "test_1_synthetic_adam": test1,
        "test_2_nu_only_physical": test2,
        "test_3_joint_mb_va": test3,
        "rollbacks": [],
        "overall_conclusion": overall,
    }
    (OUTPUT / "diagnostic_report.json").write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2), flush=True)
    return 0 if test1["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
