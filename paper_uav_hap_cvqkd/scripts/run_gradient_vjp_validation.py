"""Run the frozen gradient/VJP validation. No numerical overrides."""

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
from _numerical_validation import validation_representative_states
from src.cvqkd import gram_moments
from src.cvqkd.holevo import holevo_information
from src.cvqkd.mutual_information import discrete_mutual_information, standard_complex_noise
from src.modulation.joint_ps_gs import JointTransmitter
from src.modulation.qam256 import c4_orbit_indices


MANIFEST = ROOT / "configs/gradient_vjp_validation_execution_manifest_v1.json"
OUTPUT = ROOT / "results/gradient_vjp_validation_v1.json"


class GradientValidationFailClosed(RuntimeError):
    pass


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_protocol() -> dict[str, Any]:
    return load_yaml(ROOT / "configs/gradient_vjp_validation_protocol_v1.yaml")


def _verify_bindings(root: Path, bindings: dict[str, str]) -> None:
    for relative, expected in bindings.items():
        path = root / relative
        actual = _sha256(path) if path.is_file() else "MISSING"
        if actual != expected:
            raise ValueError(f"implementation manifest mismatch: {relative}: {actual}")


def _noise(config: dict[str, Any], state_count: int) -> torch.Tensor:
    return standard_complex_noise(
        (state_count, 256, int(config["mi_sample_count"])),
        generator=torch.Generator().manual_seed(int(config["crn_seed"])),
        device="cpu",
    )


def _require_fast(rows: list[dict[str, Any]] | tuple[dict[str, Any], ...]) -> None:
    if not rows or any(row.get("route") != "COMPLEX128_FAST" for row in rows):
        raise GradientValidationFailClosed("every gradient evaluation must use COMPLEX128_FAST")


def _precheck_fast(ensemble) -> None:
    indices = c4_orbit_indices(device=ensemble.probabilities.device)
    rows = []
    with torch.no_grad():
        for state in range(ensemble.probabilities.shape[0]):
            result, gate = gram_moments._fast(
                ensemble.probabilities[state, indices[:, 0]],
                ensemble.amplitudes[state, indices[:, 0]],
            )
            rows.append({"route": "COMPLEX128_FAST" if result is not None else "FAST_ROUTE_UNAVAILABLE", "gate": gate})
    _require_fast(rows)


def _components(model, transmittance, epsilon, noise, default):
    ensemble = model(transmittance, epsilon)
    _precheck_fast(ensemble)
    mi = discrete_mutual_information(
        ensemble,
        transmittance,
        epsilon,
        noise_samples_per_symbol=noise.shape[-1],
        standard_noise_samples=noise,
        noise_sample_chunk_size=64,
        implementation="optimized",
    )
    holevo = holevo_information(
        ensemble,
        transmittance,
        epsilon,
        backend="c4_gram",
        fock_cutoff=None,
        density_eigenvalue_tolerance=float(
            default["numerical_validation"]["production_gram_candidate_diagnostic"]
            ["candidate_density_eigenvalue_threshold"]
        ),
        density_trace_tolerance=float(default["cvqkd"]["holevo_numerics"]["density_trace_tolerance"]),
        physicality_tolerance=float(default["cvqkd"]["holevo_numerics"]["physicality_tolerance"]),
    )
    _require_fast(holevo.diagnostics["source_moment_diagnostics"])
    beta = float(default["cvqkd"]["beta_reconciliation"])
    metrics = {
        "MI": mi.mean(),
        "C": holevo.coherent_correlation.mean(),
        "w": holevo.w.mean(),
        "Z": holevo.z.mean(),
        "lambda1": holevo.covariance.lambda1.mean(),
        "lambda2": holevo.covariance.lambda2.mean(),
        "lambda3": holevo.covariance.lambda3.mean(),
        "chi_BE": holevo.chi_be.mean(),
        "raw_K": (beta * mi - holevo.chi_be).mean(),
    }
    return metrics, tuple(holevo.diagnostics["source_moment_diagnostics"])


def _stable(derivatives, analytic, steps, absolute, relative, required):
    comparisons = []
    consecutive = maximum = 0
    for index, (left, right) in enumerate(zip(derivatives, derivatives[1:])):
        allowance = absolute + relative * max(abs(left), abs(right), abs(analytic))
        passed = abs(left - right) <= allowance and max(abs(left - analytic), abs(right - analytic)) <= allowance
        consecutive = consecutive + 1 if passed else 0
        maximum = max(maximum, consecutive)
        comparisons.append({"larger_h": steps[index], "smaller_h": steps[index + 1], "adjacent_error": abs(left - right), "analytic_error": max(abs(left - analytic), abs(right - analytic)), "allowance": allowance, "passes": passed})
    return maximum >= required, comparisons


def _status(rows: list[dict[str, Any]]) -> str:
    return "GRADIENT_VJP_VALIDATION_PASS" if rows and all(row["passes"] for row in rows) else "GRADIENT_VJP_VALIDATION_FAIL_CLOSED"


def _parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(description=__doc__)


def run() -> dict[str, Any]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    _verify_bindings(ROOT, manifest["required_sha256"])
    protocol = _load_protocol()
    default = load_yaml(ROOT / "configs/default.yaml")
    _, labels, transmittance, epsilon = validation_representative_states(default)
    if labels != protocol["representative_states"]:
        raise ValueError("representative-state binding mismatch")
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(int(protocol["fixture_initialization_seed"]))
        model = JointTransmitter(
            "full",
            v_min=float(default["cvqkd"]["v_min_snu"]),
            v_max=float(default["cvqkd"]["v_max_snu"]),
            n_peak_photons=float(default["cvqkd"]["n_peak_photons"]),
        )
    noise = _noise(protocol, len(labels))
    named = dict(model.named_parameters())
    parameters = list(named.values())
    center, center_routes = _components(model, transmittance, epsilon, noise, default)
    gradients = {}
    metric_names = list(protocol["required_metrics"])
    for index, metric in enumerate(metric_names):
        values = torch.autograd.grad(center[metric], parameters, retain_graph=index < len(metric_names) - 1, allow_unused=False)
        gradients[metric] = {name: value.detach().clone() for name, value in zip(named, values)}

    steps = [float(value) for value in protocol["central_difference_steps"]]
    tolerance = protocol["derivative_tolerance"]
    rows = []
    for family, coordinates in protocol["parameter_coordinates"].items():
        for parameter_name, raw_index in coordinates:
            coordinate = tuple(int(value) for value in raw_index)
            parameter = named[parameter_name]
            original = parameter[coordinate].detach().clone()
            derivatives = {metric: [] for metric in metric_names}
            h_rows = []
            try:
                for h in steps:
                    endpoints = {}
                    for label, sign in (("plus", 1.0), ("minus", -1.0)):
                        with torch.no_grad():
                            parameter[coordinate] = original + sign * h
                            metrics, routes = _components(model, transmittance, epsilon, noise, default)
                        endpoints[label] = {"metrics": {key: float(value) for key, value in metrics.items()}, "routes": list(routes)}
                    for metric in metric_names:
                        derivatives[metric].append((endpoints["plus"]["metrics"][metric] - endpoints["minus"]["metrics"][metric]) / (2 * h))
                    h_rows.append({"h": h, **endpoints})
            finally:
                with torch.no_grad():
                    parameter[coordinate] = original
            checks = {}
            passes = True
            for metric in metric_names:
                analytic = float(gradients[metric][parameter_name][coordinate])
                stable, comparisons = _stable(
                    derivatives[metric], analytic, steps,
                    float(tolerance["absolute"]), float(tolerance["relative"]),
                    int(tolerance["required_adjacent_stable_pairs"]),
                )
                checks[metric] = {"analytic_directional_derivative": analytic, "finite_difference_derivatives": derivatives[metric], "adjacent_checks": comparisons, "passes": stable}
                passes = passes and stable
            rows.append({"states": labels, "family": family, "parameter": parameter_name, "coordinate": list(coordinate), "center_routes": list(center_routes), "h_rows": h_rows, "checks": checks, "passes": passes})
    return {"schema_version": "gradient-vjp-validation-v1", "status": _status(rows), "rows": rows, "lifecycle_guards": protocol["lifecycle_guards"], "provenance": {"execution_manifest_sha256": _sha256(MANIFEST), "protocol_sha256": _sha256(ROOT / "configs/gradient_vjp_validation_protocol_v1.yaml"), "amendment_sha256": _sha256(ROOT / "configs/gradient_vjp_spectral_frechet_amendment_v1.yaml"), "frozen_model_sha256": _sha256(ROOT / "docs/FINAL_MODEL_SPEC.md")}}


def main() -> int:
    _parser().parse_args()
    try:
        payload = run()
    except Exception as error:
        payload = {"schema_version": "gradient-vjp-validation-v1", "status": "GRADIENT_VJP_VALIDATION_FAIL_CLOSED", "rows": [], "failure_reason": f"{type(error).__name__}: {error}", "lifecycle_guards": _load_protocol()["lifecycle_guards"], "provenance": {"execution_manifest_sha256": _sha256(MANIFEST)}}
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(payload["status"])
    return 0 if payload["status"] == "GRADIENT_VJP_VALIDATION_PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
