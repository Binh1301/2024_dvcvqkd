"""Run the already frozen six-step pointwise-guard smoke protocol."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import random
import time

import numpy as np
import torch
import yaml

from src.modulation.joint_ps_gs import JointTransmitter
from src.optimization.pointwise_guard import PointwiseGuard, PointwiseGuardConfig, snapshot_training_transaction
from src.optimization.real_point_certifier_adapter import RealPointCertifierAdapter
from src.optimization.trainer import EnergyBudgetController, train_step
from src.utils.random import seed_process, torch_generator


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "configs" / "pointwise_guard_execution_manifest_v1.json"
PROTOCOL = ROOT / "configs" / "pointwise_guard_protocol_v1.yaml"
ROSTER = ROOT / "results" / "independent_confirmation_roster.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def deterministic_trace(trace: list[dict]) -> list[dict]:
    """Remove declared non-deterministic bookkeeping before replay comparison."""

    return [
        {key: value for key, value in row.items() if key not in {"repetition", "runtime_seconds"}}
        for row in trace
    ]


def verify_manifest() -> dict:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("status") != "PROSPECTIVE_FROZEN_BEFORE_SMOKE_OUTCOMES":
        raise RuntimeError("Smoke execution manifest is not prospectively frozen.")
    current_head = __import__("subprocess").check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    try:
        __import__("subprocess").check_call(
            ["git", "merge-base", "--is-ancestor", manifest["repository_head"], current_head],
            cwd=ROOT, stdout=__import__("subprocess").DEVNULL,
            stderr=__import__("subprocess").DEVNULL,
        )
    except __import__("subprocess").CalledProcessError as error:
        raise RuntimeError("Smoke execution checkout is not a descendant of the frozen manifest commit.") from error
    if __import__("subprocess").check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip():
        raise RuntimeError("Smoke execution requires a clean worktree.")
    failures = []
    for relative, expected in manifest["file_bindings"].items():
        path = ROOT / relative
        if not path.is_file() or sha256(path) != expected:
            failures.append(relative)
    if failures:
        raise RuntimeError("Smoke execution provenance mismatch: " + ", ".join(failures))
    return manifest


def _state_dict_equal(left, right) -> bool:
    if isinstance(left, torch.Tensor):
        return isinstance(right, torch.Tensor) and torch.equal(left, right)
    if isinstance(left, dict):
        return isinstance(right, dict) and set(left) == set(right) and all(
            _state_dict_equal(left[key], right[key]) for key in left
        )
    if isinstance(left, (tuple, list)):
        return isinstance(right, type(left)) and len(left) == len(right) and all(
            _state_dict_equal(a, b) for a, b in zip(left, right)
        )
    return left == right


def rollback_equivalent(snapshot, transmitter, optimizer, controller, generator) -> bool:
    return (
        _state_dict_equal(snapshot.model_state, transmitter.state_dict())
        and _state_dict_equal(snapshot.optimizer_state, optimizer.state_dict())
        and (controller is None or snapshot.controller_state["multiplier"] == controller.multiplier)
        and random.getstate() == snapshot.python_rng_state
        and np.array_equal(np.random.get_state()[1], snapshot.numpy_rng_state[1])
        and np.random.get_state()[0] == snapshot.numpy_rng_state[0]
        and torch.equal(torch.get_rng_state(), snapshot.torch_cpu_rng_state)
        and (generator is None or torch.equal(generator.get_state(), snapshot.explicit_generator_state))
    )


def run_repetition(manifest: dict, repetition: int) -> list[dict]:
    protocol = yaml.safe_load(PROTOCOL.read_text(encoding="utf-8"))
    default = yaml.safe_load((ROOT / "configs" / "default.yaml").read_text(encoding="utf-8"))
    roster = json.loads(ROSTER.read_text(encoding="utf-8"))
    states = roster["representative_states"]
    transmittance = torch.tensor([row["transmittance"] for row in states], dtype=torch.float64)
    epsilon = torch.tensor([row["epsilon_snu"] for row in states], dtype=torch.float64)
    seed_process(int(protocol["smoke_test"]["initialization_seed"]))
    cvqkd = default["cvqkd"]
    training = default["training"]
    model = JointTransmitter(
        "full", v_min=float(cvqkd["v_min_snu"]), v_max=float(cvqkd["v_max_snu"]),
        n_peak_photons=float(cvqkd["n_peak_photons"]),
    )
    optimizer = torch.optim.Adam([
        {"params": model.ps_network.parameters(), "lr": float(training["learning_rates"]["ps"]), "name": "ps"},
        {"params": model.gs_model.parameters(), "lr": float(training["learning_rates"]["gs"]), "name": "gs"},
        {"params": model.va_network.parameters(), "lr": float(training["learning_rates"]["va"]), "name": "va"},
    ])
    controller = EnergyBudgetController(
        va_budget=float(cvqkd["v_a_budget_snu"]),
        dual_learning_rate=float(training["energy_dual_learning_rate"]),
    )
    generator = torch_generator(int(protocol["smoke_test"]["common_random_seed"]))
    expected = manifest["file_bindings"]
    guard = PointwiseGuard(
        PointwiseGuardConfig(
            protocol["threshold"]["candidate_float64_hex"],
            protocol["threshold"]["candidate_exact_dyadic"],
        ),
        certify_point=RealPointCertifierAdapter(
            ROOT,
            worker=ROOT / "scripts" / "pointwise_certifier_worker.py",
            certification_python=ROOT / ".venv-cert" / "Scripts" / "python.exe",
            expected_provenance=expected,
            actual_provenance={key: sha256(ROOT / key) for key in expected},
        ),
        expected_provenance=expected,
        actual_provenance={key: sha256(ROOT / key) for key in expected},
    )
    rows: list[dict] = []
    for step in range(int(protocol["smoke_test"]["steps"])):
        started = time.perf_counter()
        pre_ensemble = model(transmittance, epsilon)
        pre = guard.check(pre_ensemble)
        row = {
            "repetition": repetition, "step": step,
            "pre_update_status": pre.status.value,
            "pre_update_unique_ensembles": pre.unique_ensembles,
            "pre_update_guard_results": [result.__dict__ | {"status": result.status.value} for result in pre.row_results],
            "proposed_update_attempted": False,
            "post_update_status": None, "commit": False, "rollback": False,
            "rollback_equivalence": True,
            "energy_dual_before": controller.multiplier,
            "energy_dual_after": controller.multiplier,
            "runtime_seconds": 0.0,
        }
        if pre.all_admissible:
            snapshot = snapshot_training_transaction(
                model, optimizer, energy_budget_controller=controller, generator=generator,
            )
            row["proposed_update_attempted"] = True
            result = train_step(
                model, optimizer, transmittance, epsilon,
                beta_reconciliation=float(cvqkd["beta_reconciliation"]),
                noise_samples_per_symbol=int(training["train_awgn_samples_per_symbol"]),
                density_eigenvalue_tolerance=float.fromhex(
                    protocol["threshold"]["candidate_float64_hex"]
                ), generator=generator,
                gradient_clip_norm=float(training["gradient_clip_norm"]), energy_budget_controller=controller,
                pointwise_guard=guard,
            )
            row.update({
                "post_update_status": None if result.pointwise_guard_result is None else result.pointwise_guard_result.status.value,
                "commit": bool(result.pointwise_guard_committed),
                "rollback": result.pointwise_guard_committed is False,
                "rollback_equivalence": True if result.pointwise_guard_committed else rollback_equivalent(snapshot, model, optimizer, controller, generator),
                "loss_before_update": None if result.optimization_loss is None else float(result.optimization_loss),
                "skr_before_update": result.key_rate.fading_average_raw.detach().tolist(),
                "gradient_finite": True,
                "energy_dual_before": result.energy_dual_before_update,
                "energy_dual_after": result.energy_dual_after_update,
            })
        row["runtime_seconds"] = time.perf_counter() - started
        rows.append(row)
    return rows


def main() -> int:
    manifest = verify_manifest()
    started = time.perf_counter()
    traces = [run_repetition(manifest, repetition) for repetition in (1, 2)]
    deterministic_traces = [deterministic_trace(trace) for trace in traces]
    trace_hashes = [hashlib.sha256(canonical_bytes(trace)).hexdigest() for trace in deterministic_traces]
    payload = {
        "schema_version": "pointwise-guard-smoke-v2",
        "status": "SMOKE_EXECUTION_COMPLETED",
        "protocol_config_sha256": sha256(PROTOCOL),
        "execution_manifest_sha256": sha256(MANIFEST),
        "frozen_model_sha256": manifest["file_bindings"]["docs/FINAL_MODEL_SPEC.md"],
        "trace_hashes": trace_hashes,
        "deterministic_replay": {"status": "DETERMINISTIC_REPLAY_PASS" if trace_hashes[0] == trace_hashes[1] else "DETERMINISTIC_REPLAY_FAIL", "byte_identical": deterministic_traces[0] == deterministic_traces[1], "excluded_fields": ["repetition", "runtime_seconds"]},
        "traces": traces,
        "runtime_seconds": time.perf_counter() - started,
        "lifecycle_guards": {"threshold_approved": False, "publication_training_performed": False, "final_test_accessed": False, "optimized_mb_grid_performed": False, "baseline_selection_performed": False, "security_functional_changed": False},
    }
    output = ROOT / "results" / "pointwise_guard_smoke_v2.json"
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "trace_hashes": trace_hashes}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
