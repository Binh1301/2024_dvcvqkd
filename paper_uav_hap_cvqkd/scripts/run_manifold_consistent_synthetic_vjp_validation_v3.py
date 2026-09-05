"""Run the frozen manifold-consistent synthetic VJP validation; no overrides."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from _common import load_yaml
from src.cvqkd import gram_moments
from src.cvqkd.holevo import _holevo_from_source_moments
from src.cvqkd.spectral_frechet import hermitian_inverse_sqrt, hermitian_sqrt
from src.modulation.joint_ps_gs import reference_ensemble

MANIFEST = ROOT / "configs/manifold_consistent_synthetic_vjp_validation_execution_manifest_v3.json"
OUTPUT = ROOT / "results/manifold_consistent_synthetic_vjp_validation_v3.json"

class ManifoldValidationFailClosed(RuntimeError):
    pass


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _verify_bindings(root: Path, bindings: dict[str, str]) -> None:
    for relative, expected in bindings.items():
        path = root / relative
        actual = _sha256(path) if path.is_file() else "MISSING"
        if actual != expected:
            raise ValueError(f"manifest mismatch: {relative}: {actual}")


def _config() -> dict[str, Any]:
    return load_yaml(ROOT / "configs/manifold_consistent_cw_vjp_validation_amendment_v1.yaml")


def _fixture_a() -> dict[str, Any]:
    return {"identity": "S_s=0.00390625_I_64", "sectors": [torch.eye(64, dtype=torch.complex128) / 256 for _ in range(4)]}


def _fixture_b() -> dict[str, Any]:
    source = load_yaml(ROOT / _config()["fixture_b"]["finite_difference_source"])
    p = torch.full((64,), 1 / 256, dtype=torch.float64)
    z = torch.arange(1, 65, dtype=torch.float64).to(torch.complex128)
    return {"probabilities": p, "prototypes": z, "direction": z.clone(), "step": float(source["finite_difference"]["step"])}


def _fixture_b_point(fixture: dict[str, Any], sign: float) -> dict[str, Any]:
    z = fixture["prototypes"] + sign * fixture["step"] * fixture["direction"]
    sectors = gram_moments._sectors(fixture["probabilities"], z)
    result, gate = gram_moments._fast(fixture["probabilities"], z)
    return {"z": z, "sectors": sectors, "result": result, "gate": gate}


def _require_fast(result: dict[str, Any] | None, gate: dict[str, Any]) -> None:
    if result is not None and gate.get("all_sectors_positive") and gate.get("sector_condition_number", float("inf")) <= gram_moments.FAST_MAX_CONDITION and gate.get("sector_reconstruction_residual", float("inf")) <= gram_moments.FAST_MAX_RESIDUAL and gate.get("residual_identity_relative_error", float("inf")) <= gram_moments.FAST_MAX_RESIDUAL:
        return
    details = ", ".join(f"{key}={gate.get(key)!r}" for key in ("all_sectors_positive", "minimum_eigenvalue", "sector_condition_number", "sector_reconstruction_residual", "residual_identity_relative_error"))
    raise ManifoldValidationFailClosed(f"COMPLEX128_FAST gate failed: {details}")


def _scalar_directional(
    function,
    variable: torch.Tensor,
    direction: torch.Tensor,
    h: float,
    *,
    require_hermitian_gradient: bool = False,
) -> dict[str, Any]:
    scalar = function(variable)
    gradient, = torch.autograd.grad(scalar, variable)

    analytic = float(
        torch.sum((gradient.conj() * direction).real)
    )

    numerical = float(
        (
            function(variable.detach() + h * direction)
            - function(variable.detach() - h * direction)
        )
        / (2 * h)
    )

    hermitian_gradient = False
    if require_hermitian_gradient:
        hermitian_gradient = bool(
            torch.allclose(
                gradient,
                gradient.mH,
                atol=1e-12,
                rtol=1e-11,
            )
        )

    return {
        "analytic": analytic,
        "numerical": numerical,
        "absolute_error": abs(analytic - numerical),
        "finite": bool(torch.isfinite(gradient).all()),
        "hermitian_gradient": hermitian_gradient,
    }

def _spectral_rows(h: float) -> list[dict[str, Any]]:
    matrix = (
        torch.eye(64, dtype=torch.complex128) / 256
    ).requires_grad_()

    direction = torch.diag(
        torch.linspace(-0.25, 0.25, 64, dtype=torch.float64)
    ).to(torch.complex128)

    weight = torch.tensor(
        [
            [1.0, 0.25j],
            [-0.25j, -0.5],
        ],
        dtype=torch.complex128,
    )

    weight = torch.nn.functional.pad(
        weight,
        (0, 62, 0, 62),
    )

    rows = []

    for name, function in (
        ("inverse_sqrt", hermitian_inverse_sqrt),
        ("square_root", hermitian_sqrt),
    ):
        def scalar(value, fn=function):
            return torch.sum(
                (fn(value).conj() * weight).real
            )

        values = _scalar_directional(
            scalar,
            matrix,
            direction,
            h,
            require_hermitian_gradient=True,
        )

        values["name"] = name
        rows.append(values)

    return rows


def _manifold_rows(fixture: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    center = _fixture_b_point(fixture, 0.0)
    plus = _fixture_b_point(fixture, 1.0)
    minus = _fixture_b_point(fixture, -1.0)
    for point in (center, plus, minus):
        _require_fast(point["result"], point["gate"])
    z = center["z"].detach().clone().requires_grad_()
    def source(metric, value):
        result, gate = gram_moments._fast(fixture["probabilities"], value)
        _require_fast(result, gate)
        return result[metric]
    c_row = _scalar_directional(lambda value: source("C", value), z, fixture["direction"], fixture["step"])
    c_row["name"] = "C_manifold"
    w_row = _scalar_directional(lambda value: source("w", value), z, fixture["direction"], fixture["step"])
    w_row["name"] = "w_manifold"
    ensemble = reference_ensemble("uniform", batch_size=1, modulation_variance=1.0)
    def raw_key(value):
        downstream = _holevo_from_source_moments(ensemble, torch.tensor([0.02]), torch.tensor([0.01]), coherent_correlation=source("C", value).reshape(1), w_raw=source("w", value).reshape(1), tau=None, tau_trace=torch.ones(1), require_supported_symmetry=True, symmetry_tolerance=1e-8, physicality_tolerance=1e-10, diagnostics={})
        return 0.95 * torch.tensor(0.03, dtype=torch.float64) - downstream.chi_be.mean()
    downstream_row = _scalar_directional(raw_key, z, fixture["direction"], fixture["step"])
    downstream_row["name"] = "downstream_raw_K_manifold"
    return [c_row, w_row, downstream_row], {"center": center["gate"], "plus": plus["gate"], "minus": minus["gate"]}


def _row_pass(
    row: dict[str, Any],
    tolerance: dict[str, Any],
) -> bool:
    allowance = (
        float(tolerance["absolute_tolerance"])
        + float(tolerance["relative_tolerance"])
        * max(
            abs(row["analytic"]),
            abs(row["numerical"]),
        )
    )

    row["allowance"] = allowance

    if row["name"] in ("inverse_sqrt", "square_root"):
        hermitian_ok = row["hermitian_gradient"]
    else:
        hermitian_ok = True

    row["passes"] = (
        row["finite"]
        and hermitian_ok
        and row["absolute_error"] <= allowance
    )

    return row["passes"]


def _parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(description=__doc__)


def run() -> dict[str, Any]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8-sig"))
    _verify_bindings(ROOT, manifest["required_sha256"])
    config = _config()
    fixture_b = _fixture_b()
    source = load_yaml(ROOT / config["fixture_b"]["finite_difference_source"])
    manifold_rows, gates = _manifold_rows(fixture_b)
    rows = _spectral_rows(fixture_b["step"]) + manifold_rows
    for row in rows:
        _row_pass(row, source["finite_difference"])
    status = "MANIFOLD_CONSISTENT_SYNTHETIC_VJP_VALIDATION_PASS" if all(row["passes"] for row in rows) else "MANIFOLD_CONSISTENT_SYNTHETIC_VJP_VALIDATION_FAIL_CLOSED"
    return {"schema_version": "manifold-consistent-synthetic-vjp-validation-v1", "status": status, "fixture_a": _fixture_a()["identity"], "fixture_b": {"fixture_sha256": config["fixture_b"]["fixture_sha256"], "direction_rule": config["fixture_b"]["direction_rule"]}, "finite_difference": source["finite_difference"], "gates": gates, "rows": rows, "runtime": {"validation_execution_attempted": True}, "lifecycle_guards": config["lifecycle_guards"], "provenance": {"execution_manifest_sha256": _sha256(MANIFEST), "amendment_sha256": _sha256(ROOT / "configs/manifold_consistent_cw_vjp_validation_amendment_v1.yaml"), "frozen_model_sha256": _sha256(ROOT / "docs/FINAL_MODEL_SPEC.md")}}


def main() -> int:
    _parser().parse_args()
    try:
        payload = run()
    except Exception as error:
        payload = {"schema_version": "manifold-consistent-synthetic-vjp-validation-v1", "status": "MANIFOLD_CONSISTENT_SYNTHETIC_VJP_VALIDATION_FAIL_CLOSED", "fixture_a": "", "fixture_b": {}, "finite_difference": {}, "gates": {}, "rows": [], "runtime": {"validation_execution_attempted": True}, "failure_reason": f"{type(error).__name__}: {error}", "lifecycle_guards": _config()["lifecycle_guards"], "provenance": {"execution_manifest_sha256": _sha256(MANIFEST)}}
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(payload["status"])
    return 0 if payload["status"] == "MANIFOLD_CONSISTENT_SYNTHETIC_VJP_VALIDATION_PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
