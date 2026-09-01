"""Pointwise spectral admissibility and transactional rollback primitives.

The production security functional is deliberately not implemented here.  A
validated point-certifier is injected by the caller; raw ``torch.linalg.eigh``
values are never accepted as certification evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import copy
import hashlib
import random
from typing import Any, Callable, Mapping, Sequence

import numpy as np
import torch

from src.modulation.joint_ps_gs import Ensemble


class PointwiseStatus(str, Enum):
    POINTWISE_ADMISSIBLE = "POINTWISE_ADMISSIBLE"
    POINTWISE_GUARD_BAND_REJECT = "POINTWISE_GUARD_BAND_REJECT"
    POINTWISE_CERTIFICATION_FAILED = "POINTWISE_CERTIFICATION_FAILED"
    PROVENANCE_FAILURE = "PROVENANCE_FAILURE"


STATUS_ORDER = (
    PointwiseStatus.PROVENANCE_FAILURE,
    PointwiseStatus.POINTWISE_CERTIFICATION_FAILED,
    PointwiseStatus.POINTWISE_GUARD_BAND_REJECT,
    PointwiseStatus.POINTWISE_ADMISSIBLE,
)


@dataclass(frozen=True)
class PointwiseGuardConfig:
    """Threshold-parametric guard settings from protocol v1."""

    tau_float64_hex: str
    tau_exact_dyadic: str
    safety_factor: int = 2

    def validate(self) -> None:
        try:
            value = float.fromhex(self.tau_float64_hex)
        except (TypeError, ValueError) as error:
            raise ValueError("tau_float64_hex must be a valid hexadecimal float.") from error
        if not np.isfinite(value) or value <= 0.0:
            raise ValueError("tau_float64_hex must be finite and positive.")
        if not isinstance(self.tau_exact_dyadic, str) or not self.tau_exact_dyadic:
            raise ValueError("tau_exact_dyadic must be a nonempty exact representation.")
        if self.safety_factor != 2:
            raise ValueError("pointwise-guard-v1 freezes safety_factor=2.")

    @property
    def tau_float64(self) -> float:
        self.validate()
        return float.fromhex(self.tau_float64_hex)


@dataclass(frozen=True)
class PointwiseGuardResult:
    status: PointwiseStatus
    ensemble_sha256: str
    support_count: int | None
    certified_margin: float | None
    uncertainty_upper: float | None
    threshold_float64_hex: str
    threshold_exact_dyadic: str
    reason: str
    provenance_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class PointwiseBatchResult:
    status: PointwiseStatus
    row_results: tuple[PointwiseGuardResult, ...]
    unique_results: tuple[PointwiseGuardResult, ...]
    row_to_unique: tuple[int, ...]
    total_checks: int
    unique_ensembles: int
    deduplicated_hits: int
    admissible_count: int
    guard_reject_count: int
    certification_failure_count: int
    provenance_failure_count: int

    @property
    def all_admissible(self) -> bool:
        return self.status is PointwiseStatus.POINTWISE_ADMISSIBLE


class PointwiseGuardRejected(RuntimeError):
    """Raised when a current training batch is not admissible for backward."""

    def __init__(self, result: PointwiseBatchResult) -> None:
        self.result = result
        super().__init__(f"Pointwise guard rejected current state: {result.status.value}")


def _tensor_bytes(value: torch.Tensor) -> bytes:
    tensor = value.detach().to(device="cpu").contiguous()
    return tensor.numpy().tobytes()


def ensemble_row_sha256(ensemble: Ensemble, row: int) -> str:
    """Hash the final physical row, including probabilities, amplitudes, and V_A."""

    ensemble.validate()
    if not isinstance(row, int) or row < 0 or row >= ensemble.probabilities.shape[0]:
        raise IndexError("ensemble row is outside the batch.")
    digest = hashlib.sha256()
    for name, tensor in (
        ("probabilities", ensemble.probabilities[row]),
        ("amplitudes", ensemble.amplitudes[row]),
        ("declared_va", ensemble.declared_va[row]),
    ):
        digest.update(name.encode("ascii"))
        digest.update(str(tensor.dtype).encode("ascii"))
        digest.update(repr(tuple(tensor.shape)).encode("ascii"))
        digest.update(_tensor_bytes(tensor))
    return digest.hexdigest()


def deduplicate_ensemble_rows(ensemble: Ensemble) -> tuple[tuple[str, ...], tuple[int, ...], tuple[int, ...]]:
    """Return row hashes, unique row indices, and deterministic row mapping."""

    hashes = tuple(ensemble_row_sha256(ensemble, row) for row in range(ensemble.probabilities.shape[0]))
    first_by_hash: dict[str, int] = {}
    unique_rows: list[int] = []
    row_to_unique: list[int] = []
    for row_hash in hashes:
        if row_hash not in first_by_hash:
            first_by_hash[row_hash] = len(unique_rows)
            unique_rows.append(hashes.index(row_hash))
        row_to_unique.append(first_by_hash[row_hash])
    return hashes, tuple(unique_rows), tuple(row_to_unique)


def validate_provenance_bindings(
    expected: Mapping[str, str], actual: Mapping[str, str]
) -> tuple[bool, tuple[str, ...]]:
    """Compare caller-supplied bindings without regenerating or weakening them."""

    if set(expected) != set(actual):
        return False, ("provenance binding key set mismatch",)
    mismatches = tuple(sorted(key for key in expected if expected[key] != actual[key]))
    return not mismatches, mismatches


def _result_status(results: Sequence[PointwiseGuardResult]) -> PointwiseStatus:
    for status in STATUS_ORDER:
        if any(result.status is status for result in results):
            return status
    raise ValueError("At least one pointwise result is required.")


class PointwiseGuard:
    """Validated pointwise guard with an injected certification backend."""

    def __init__(
        self,
        config: PointwiseGuardConfig,
        *,
        certify_point: Callable[[Ensemble, int, PointwiseGuardConfig], Mapping[str, Any]],
        expected_provenance: Mapping[str, str],
        actual_provenance: Mapping[str, str],
    ) -> None:
        config.validate()
        if not callable(certify_point):
            raise TypeError("certify_point must be callable.")
        valid, mismatches = validate_provenance_bindings(expected_provenance, actual_provenance)
        self.config = config
        self.certify_point = certify_point
        self.provenance_valid = valid
        self.provenance_ids = tuple(sorted(actual_provenance))
        self.provenance_reason = "" if valid else "; ".join(mismatches)

    def _check_unique(self, ensemble: Ensemble, row: int, row_hash: str) -> PointwiseGuardResult:
        if not self.provenance_valid:
            return PointwiseGuardResult(
                PointwiseStatus.PROVENANCE_FAILURE, row_hash, None, None, None,
                self.config.tau_float64_hex, self.config.tau_exact_dyadic,
                self.provenance_reason, self.provenance_ids,
            )
        try:
            evidence = dict(self.certify_point(ensemble, row, self.config))
        except Exception as error:
            return PointwiseGuardResult(
                PointwiseStatus.POINTWISE_CERTIFICATION_FAILED, row_hash, None, None, None,
                self.config.tau_float64_hex, self.config.tau_exact_dyadic,
                f"point certifier exception: {type(error).__name__}: {error}", self.provenance_ids,
            )
        if evidence.get("status") != "CERTIFIED_POINT":
            return PointwiseGuardResult(
                PointwiseStatus.POINTWISE_CERTIFICATION_FAILED, row_hash, None, None, None,
                self.config.tau_float64_hex, self.config.tau_exact_dyadic,
                str(evidence.get("reason", "point certification did not complete")), self.provenance_ids,
            )
        try:
            support_count = int(evidence["support_count"])
            lower_below = float(evidence["lower_nearest_below"])
            upper_below = float(evidence["upper_nearest_below"])
            lower_above = float(evidence["lower_nearest_above"])
            upper_above = float(evidence["upper_nearest_above"])
            threshold = self.config.tau_float64
            certified_margin = min(threshold - upper_below, lower_above - threshold)
            uncertainty_upper = max((upper_below - lower_below) / 2.0,
                                     (upper_above - lower_above) / 2.0)
        except (KeyError, TypeError, ValueError, OverflowError) as error:
            return PointwiseGuardResult(
                PointwiseStatus.POINTWISE_CERTIFICATION_FAILED, row_hash, None, None, None,
                self.config.tau_float64_hex, self.config.tau_exact_dyadic,
                f"malformed validated point evidence: {error}", self.provenance_ids,
            )
        values = (lower_below, upper_below, lower_above, upper_above,
                  certified_margin, uncertainty_upper)
        if (support_count <= 0 or not all(np.isfinite(value) for value in values)
                or lower_below > upper_below or lower_above > upper_above
                or upper_below >= threshold or lower_above <= threshold
                or certified_margin <= 0.0 or uncertainty_upper < 0.0):
            return PointwiseGuardResult(
                PointwiseStatus.POINTWISE_CERTIFICATION_FAILED, row_hash, support_count,
                certified_margin, uncertainty_upper, self.config.tau_float64_hex,
                self.config.tau_exact_dyadic, "invalid or non-separating certified brackets",
                self.provenance_ids,
            )
        if not certified_margin > self.config.safety_factor * uncertainty_upper:
            return PointwiseGuardResult(
                PointwiseStatus.POINTWISE_GUARD_BAND_REJECT, row_hash, support_count,
                certified_margin, uncertainty_upper, self.config.tau_float64_hex,
                self.config.tau_exact_dyadic, "certified margin does not exceed guard band",
                self.provenance_ids,
            )
        return PointwiseGuardResult(
            PointwiseStatus.POINTWISE_ADMISSIBLE, row_hash, support_count,
            certified_margin, uncertainty_upper, self.config.tau_float64_hex,
            self.config.tau_exact_dyadic, "validated point is outside the guard band",
            self.provenance_ids,
        )

    def check(self, ensemble: Ensemble) -> PointwiseBatchResult:
        ensemble.validate()
        hashes, unique_rows, row_to_unique = deduplicate_ensemble_rows(ensemble)
        unique_results = tuple(
            self._check_unique(ensemble, row, hashes[row]) for row in unique_rows
        )
        row_results = tuple(unique_results[index] for index in row_to_unique)
        counts = {status: sum(result.status is status for result in row_results)
                  for status in PointwiseStatus}
        return PointwiseBatchResult(
            status=_result_status(row_results),
            row_results=row_results,
            unique_results=unique_results,
            row_to_unique=row_to_unique,
            total_checks=len(row_results),
            unique_ensembles=len(unique_results),
            deduplicated_hits=len(row_results) - len(unique_results),
            admissible_count=counts[PointwiseStatus.POINTWISE_ADMISSIBLE],
            guard_reject_count=counts[PointwiseStatus.POINTWISE_GUARD_BAND_REJECT],
            certification_failure_count=counts[PointwiseStatus.POINTWISE_CERTIFICATION_FAILED],
            provenance_failure_count=counts[PointwiseStatus.PROVENANCE_FAILURE],
        )


@dataclass
class TrainingTransactionSnapshot:
    model_state: dict[str, Any]
    optimizer_state: dict[str, Any]
    controller_state: dict[str, float] | None
    gradients: dict[str, torch.Tensor | None]
    module_training_flags: dict[str, bool]
    python_rng_state: object
    numpy_rng_state: tuple[Any, ...]
    torch_cpu_rng_state: torch.Tensor
    torch_cuda_rng_state: list[torch.Tensor] | None
    explicit_generator_state: torch.Tensor | None
    counters: Any
    scheduler_state: dict[str, Any] | None
    scaler_state: dict[str, Any] | None


def snapshot_training_transaction(
    transmitter: torch.nn.Module,
    optimizer: torch.optim.Optimizer,
    *,
    energy_budget_controller: Any | None = None,
    generator: torch.Generator | None = None,
    counters: Any = None,
    scheduler: Any | None = None,
    scaler: Any | None = None,
) -> TrainingTransactionSnapshot:
    """Deeply snapshot every mutable state present in the current trainer."""

    gradients = {
        name: None if parameter.grad is None else parameter.grad.detach().clone()
        for name, parameter in transmitter.named_parameters()
    }
    return TrainingTransactionSnapshot(
        model_state=copy.deepcopy(transmitter.state_dict()),
        optimizer_state=copy.deepcopy(optimizer.state_dict()),
        controller_state=(None if energy_budget_controller is None
                          else copy.deepcopy(energy_budget_controller.state_dict())),
        gradients=gradients,
        module_training_flags={name: module.training for name, module in transmitter.named_modules()},
        python_rng_state=random.getstate(),
        numpy_rng_state=np.random.get_state(),
        torch_cpu_rng_state=torch.get_rng_state().clone(),
        torch_cuda_rng_state=(None if not torch.cuda.is_available()
                              else [state.clone() for state in torch.cuda.get_rng_state_all()]),
        explicit_generator_state=(None if generator is None else generator.get_state().clone()),
        counters=copy.deepcopy(counters),
        scheduler_state=(None if scheduler is None else copy.deepcopy(scheduler.state_dict())),
        scaler_state=(None if scaler is None else copy.deepcopy(scaler.state_dict())),
    )


def restore_training_transaction(
    snapshot: TrainingTransactionSnapshot,
    transmitter: torch.nn.Module,
    optimizer: torch.optim.Optimizer,
    *,
    energy_budget_controller: Any | None = None,
    generator: torch.Generator | None = None,
    counters_target: Any = None,
    scheduler: Any | None = None,
    scaler: Any | None = None,
) -> Any:
    """Restore a snapshot and return its detached counter copy."""

    transmitter.load_state_dict(snapshot.model_state)
    optimizer.load_state_dict(snapshot.optimizer_state)
    if energy_budget_controller is not None and snapshot.controller_state is not None:
        if hasattr(energy_budget_controller, "multiplier"):
            energy_budget_controller.multiplier = snapshot.controller_state["multiplier"]
    for name, parameter in transmitter.named_parameters():
        gradient = snapshot.gradients[name]
        parameter.grad = None if gradient is None else gradient.detach().clone()
    for name, module in transmitter.named_modules():
        module.training = snapshot.module_training_flags[name]
    random.setstate(snapshot.python_rng_state)
    np.random.set_state(snapshot.numpy_rng_state)
    torch.set_rng_state(snapshot.torch_cpu_rng_state)
    if snapshot.torch_cuda_rng_state is not None and torch.cuda.is_available():
        torch.cuda.set_rng_state_all(snapshot.torch_cuda_rng_state)
    if generator is not None and snapshot.explicit_generator_state is not None:
        generator.set_state(snapshot.explicit_generator_state)
    if scheduler is not None and snapshot.scheduler_state is not None:
        scheduler.load_state_dict(snapshot.scheduler_state)
    if scaler is not None and snapshot.scaler_state is not None:
        scaler.load_state_dict(snapshot.scaler_state)
    if counters_target is not None:
        if isinstance(counters_target, dict) and isinstance(snapshot.counters, dict):
            counters_target.clear()
            counters_target.update(copy.deepcopy(snapshot.counters))
        else:
            raise TypeError("counters_target must be a dict when counters were snapshotted.")
    return copy.deepcopy(snapshot.counters)
