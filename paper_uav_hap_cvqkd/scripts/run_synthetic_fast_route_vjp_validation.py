"""Run the frozen synthetic fast-route VJP validation; no overrides."""

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


MANIFEST = ROOT / "configs/synthetic_fast_route_vjp_validation_execution_manifest_v2.json"
OUTPUT = ROOT / "results/synthetic_fast_route_vjp_validation_v2.json"


class SyntheticValidationFailClosed(RuntimeError):
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
    return load_yaml(ROOT / "configs/synthetic_fast_route_vjp_validation_v1.yaml")


def _fixture() -> dict[str, Any]:
    amendment = load_yaml(ROOT / "configs/fast_route_gradient_vjp_feasibility_amendment_v1.yaml")
    spec = amendment["synthetic_fast_fixture"]
    dimension = int(spec["dimension"])
    probability = float(spec["symbol_probability"])
    prototype = complex(float(spec["prototype_real"]), float(spec["prototype_imag"]))
    sectors = [torch.eye(dimension, dtype=torch.complex128) * float(spec["sector_eigenvalue"]) for _ in range(int(spec["sector_count"]))]
    return {"identity": spec["kind"], "probabilities": torch.full((dimension,), probability, dtype=torch.float64), "prototypes": torch.full((dimension,), prototype, dtype=torch.complex128), "sectors": sectors}


def _fast_fixture_result(sectors: list[torch.Tensor] | None = None):
    fixture = _fixture()
    return gram_moments._fast_from_sectors(
        fixture["probabilities"], fixture["prototypes"], fixture["sectors"] if sectors is None else sectors
    )


def _require_fast(gate: dict[str, Any]) -> None:
    if not gate.get("all_sectors_positive") or gate.get("sector_condition_number", float("inf")) > gram_moments.FAST_MAX_CONDITION or gate.get("sector_reconstruction_residual", float("inf")) > gram_moments.FAST_MAX_RESIDUAL:
        raise SyntheticValidationFailClosed("synthetic fixture must use COMPLEX128_FAST")


def _direction() -> torch.Tensor:
    return torch.diag(torch.linspace(-0.25, 0.25, 64, dtype=torch.float64)).to(torch.complex128)


def _directional(function, matrix: torch.Tensor, direction: torch.Tensor, step: float):
    value = function(matrix)
    weight = torch.tensor([[1, 0.25j], [-0.25j, -0.5]], dtype=torch.complex128)
    weight = torch.nn.functional.pad(weight, (0, matrix.shape[0] - 2, 0, matrix.shape[0] - 2))
    scalar = torch.sum((value.conj() * weight).real)
    gradient, = torch.autograd.grad(scalar, matrix)
    analytic = float(torch.sum((gradient.conj() * direction).real))
    numerical = float((torch.sum((function(matrix.detach() + step * direction).conj() * weight).real) - torch.sum((function(matrix.detach() - step * direction).conj() * weight).real)) / (2 * step))
    return {"analytic": analytic, "numerical": numerical, "absolute_error": abs(analytic - numerical), "hermitian_gradient": bool(torch.allclose(gradient, gradient.mH, atol=1e-12, rtol=1e-11)), "finite": bool(torch.isfinite(gradient).all())}


def _row(name: str, values: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    tolerance = config["finite_difference"]
    scale = max(abs(values["analytic"]), abs(values["numerical"]))
    allowance = float(tolerance["absolute_tolerance"]) + float(tolerance["relative_tolerance"]) * scale
    return {"name": name, **values, "allowance": allowance, "passes": values["finite"] and values["hermitian_gradient"] and values["absolute_error"] <= allowance}


def _scalar_directional(function, matrix: torch.Tensor, direction: torch.Tensor, step: float):
    scalar = function(matrix)
    gradient, = torch.autograd.grad(scalar, matrix)
    analytic = float(torch.sum((gradient.conj() * direction).real))
    numerical = float((function(matrix.detach() + step * direction) - function(matrix.detach() - step * direction)) / (2 * step))
    return {"analytic": analytic, "numerical": numerical, "absolute_error": abs(analytic - numerical), "hermitian_gradient": bool(torch.allclose(gradient, gradient.mH, atol=1e-12, rtol=1e-11)), "finite": bool(torch.isfinite(gradient).all())}


def _status(rows: list[dict[str, Any]]) -> str:
    return "SYNTHETIC_FAST_ROUTE_VJP_VALIDATION_PASS" if rows and all(row["passes"] for row in rows) else "SYNTHETIC_FAST_ROUTE_VJP_VALIDATION_FAIL_CLOSED"


def _parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(description=__doc__)


def run() -> dict[str, Any]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    _verify_bindings(ROOT, manifest["required_sha256"])
    config = _config()
    fixture = _fixture()
    result, gate = _fast_fixture_result()
    if result is None:
        raise SyntheticValidationFailClosed("synthetic C/w fast kernel unavailable")
    _require_fast(gate)
    step = float(config["finite_difference"]["step"])
    direction = _direction()
    matrix = fixture["sectors"][0].clone().requires_grad_()
    rows = [
        _row("inverse_sqrt", _directional(hermitian_inverse_sqrt, matrix, direction, step), config),
        _row("square_root", _directional(hermitian_sqrt, matrix, direction, step), config),
    ]
    fixed_sectors = [item.clone() for item in fixture["sectors"][1:]]
    def source(metric, variable):
        result, _ = _fast_fixture_result([variable] + fixed_sectors)
        if result is None:
            raise SyntheticValidationFailClosed("synthetic route changed during directional preflight")
        return result[metric]
    rows.extend([
        _row("C", _scalar_directional(lambda variable: source("C", variable), matrix, direction, step), config),
        _row("w", _scalar_directional(lambda variable: source("w", variable), matrix, direction, step), config),
    ])
    ensemble = reference_ensemble("uniform", batch_size=1, modulation_variance=1.0)
    def downstream_raw_key(variable):
        downstream_c = source("C", variable)
        downstream_w = source("w", variable)
        downstream = _holevo_from_source_moments(ensemble, torch.tensor([0.02]), torch.tensor([0.01]), coherent_correlation=downstream_c.reshape(1), w_raw=downstream_w.reshape(1), tau=None, tau_trace=torch.ones(1), require_supported_symmetry=True, symmetry_tolerance=1e-8, physicality_tolerance=1e-10, diagnostics={})
        return 0.95 * torch.tensor(0.03, dtype=torch.float64) - downstream.chi_be.mean()
    rows.append(_row("downstream_raw_K", _scalar_directional(downstream_raw_key, matrix, direction, step), config))
    return {"schema_version": "synthetic-fast-route-vjp-validation-v2", "status": _status(rows), "fixture": {"identity": fixture["identity"], "dimension": 64, "sector_count": 4}, "gate": gate, "rows": rows, "runtime": {"validation_execution_attempted": True}, "lifecycle_guards": config["lifecycle_guards"], "provenance": {"execution_manifest_sha256": _sha256(MANIFEST), "amendment_sha256": _sha256(ROOT / "configs/fast_route_gradient_vjp_feasibility_amendment_v1.yaml"), "frozen_model_sha256": _sha256(ROOT / "docs/FINAL_MODEL_SPEC.md")}}


def main() -> int:
    _parser().parse_args()
    try:
        payload = run()
    except Exception as error:
        payload = {"schema_version": "synthetic-fast-route-vjp-validation-v2", "status": "SYNTHETIC_FAST_ROUTE_VJP_VALIDATION_FAIL_CLOSED", "fixture": {}, "gate": {}, "rows": [], "failure_reason": f"{type(error).__name__}: {error}", "runtime": {"validation_execution_attempted": True}, "lifecycle_guards": _config()["lifecycle_guards"], "provenance": {"execution_manifest_sha256": _sha256(MANIFEST)}}
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(payload["status"])
    return 0 if payload["status"] == "SYNTHETIC_FAST_ROUTE_VJP_VALIDATION_PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
