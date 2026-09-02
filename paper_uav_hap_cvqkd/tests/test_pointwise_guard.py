"""Runtime tests for pointwise guard statuses, deduplication, and rollback."""

from __future__ import annotations

import copy
import math
import random
import unittest
from unittest.mock import patch
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]

from src.cvqkd.secret_key_rate import FadingKeyRate
from src.modulation.joint_ps_gs import Ensemble, JointTransmitter
from src.optimization.pointwise_guard import (
    PointwiseGuard,
    PointwiseGuardConfig,
    PointwiseGuardRejected,
    PointwiseStatus,
    deduplicate_ensemble_rows,
)
from src.optimization.real_point_certifier_adapter import RealPointCertifierAdapter
from src.optimization.trainer import (
    EnergyBudgetController,
    Evaluation,
    train_step,
)


EXPECTED = {
    "model": "model",
    "optimizer": "optimizer",
    "controller": "controller",
    "generator": "generator",
    "python": "python",
    "numpy": "numpy",
    "torch": "torch",
}


def _config() -> PointwiseGuardConfig:
    return PointwiseGuardConfig(
        tau_float64_hex="0x1.c25c268497682p-44",
        tau_exact_dyadic="3961408125713217/2^95",
    )


def _guard(certify, *, provenance=True) -> PointwiseGuard:
    expected = {"protocol": "p", "producer": "q"}
    actual = expected if provenance else {"protocol": "p", "producer": "wrong"}
    return PointwiseGuard(
        _config(),
        certify_point=certify,
        expected_provenance=expected,
        actual_provenance=actual,
    )


def _evidence(status="CERTIFIED_POINT", margin=0.4, uncertainty=0.05):
    tau = _config().tau_float64
    return {
        "status": status,
        "support_count": 13,
        "lower_nearest_below": tau - margin - uncertainty,
        "upper_nearest_below": tau - margin,
        "lower_nearest_above": tau + margin,
        "upper_nearest_above": tau + margin + uncertainty,
    }


class PointwiseGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.model = JointTransmitter("ps", fixed_va=1.0)
        self.t = torch.tensor([0.08, 0.08], dtype=torch.float64)
        self.epsilon = torch.tensor([0.01, 0.01], dtype=torch.float64)

    def test_safe_point_is_admissible(self) -> None:
        guard = _guard(lambda ensemble, row, config: _evidence())
        result = guard.check(self.model(self.t, self.epsilon))
        self.assertEqual(result.status, PointwiseStatus.POINTWISE_ADMISSIBLE)
        self.assertEqual(result.unique_ensembles, 1)
        self.assertEqual(result.deduplicated_hits, 1)
        self.assertEqual(result.admissible_count, 2)

    def test_guard_overlap_and_equality_reject(self) -> None:
        for margin, uncertainty in ((0.1, 0.1), (0.2, 0.4000000001)):
            with self.subTest(margin=margin):
                guard = _guard(lambda ensemble, row, config: _evidence(
                    margin=margin, uncertainty=uncertainty
                ))
                result = guard.check(self.model(self.t[:1], self.epsilon[:1]))
                self.assertEqual(result.status, PointwiseStatus.POINTWISE_GUARD_BAND_REJECT)

    def test_unresolved_certification_fails_closed(self) -> None:
        guard = _guard(lambda ensemble, row, config: _evidence(status="UNCERTIFIED_PIVOT"))
        result = guard.check(self.model(self.t[:1], self.epsilon[:1]))
        self.assertEqual(result.status, PointwiseStatus.POINTWISE_CERTIFICATION_FAILED)

    def test_provenance_mismatch_fails_closed(self) -> None:
        guard = _guard(lambda ensemble, row, config: _evidence(), provenance=False)
        result = guard.check(self.model(self.t[:1], self.epsilon[:1]))
        self.assertEqual(result.status, PointwiseStatus.PROVENANCE_FAILURE)

    def test_deduplication_is_exact_and_deterministic(self) -> None:
        ensemble = self.model(self.t, self.epsilon)
        hashes, unique_rows, mapping = deduplicate_ensemble_rows(ensemble)
        self.assertEqual(len(hashes), 2)
        self.assertEqual(unique_rows, (0,))
        self.assertEqual(mapping, (0, 0))

    def test_pointwise_rejection_prevents_evaluation_and_backward(self) -> None:
        guard = _guard(lambda ensemble, row, config: _evidence(margin=0.1, uncertainty=0.1))
        optimizer = torch.optim.Adam(self.model.parameters(), lr=1e-3)
        controller = EnergyBudgetController(va_budget=1.5, dual_learning_rate=0.1, multiplier=0.4)
        generator = torch.Generator().manual_seed(991)
        before = _snapshot(self.model, optimizer, controller, generator)
        with patch("src.optimization.trainer.evaluate_transmitter", side_effect=AssertionError("must not evaluate")):
            with self.assertRaises(PointwiseGuardRejected) as caught:
                train_step(
                    self.model, optimizer, self.t[:1], self.epsilon[:1],
                    beta_reconciliation=0.95, noise_samples_per_symbol=2,
                    density_eigenvalue_tolerance=1e-13, generator=generator,
                    energy_budget_controller=controller, pointwise_guard=guard,
                )
        self.assertEqual(caught.exception.result.status, PointwiseStatus.POINTWISE_GUARD_BAND_REJECT)
        _assert_snapshot_equal(self, before, self.model, optimizer, controller, generator)

    def test_rejected_endpoint_restores_complete_transaction_and_dual(self) -> None:
        calls = {"count": 0}

        def certify(ensemble, row, config):
            calls["count"] += 1
            return _evidence() if calls["count"] == 1 else _evidence(margin=0.1, uncertainty=0.1)

        guard = _guard(certify)
        optimizer = torch.optim.Adam(self.model.parameters(), lr=1e-3)
        controller = EnergyBudgetController(va_budget=0.5, dual_learning_rate=0.1, multiplier=0.4)
        generator = torch.Generator().manual_seed(992)
        parameter = next(self.model.parameters())
        parameter.grad = torch.ones_like(parameter)
        optimizer.step()
        optimizer.zero_grad(set_to_none=True)
        before = _snapshot(self.model, optimizer, controller, generator)

        def fake_evaluate(transmitter, transmittance, epsilon, *, generator, **kwargs):
            # Consume the explicit generator to prove that rollback restores it.
            torch.randn((3,), generator=generator)
            ensemble = transmitter(transmittance, epsilon)
            raw = ensemble.probabilities[:, 0]
            key_rate = FadingKeyRate(raw, raw.mean(), torch.clamp_min(raw, 0.0), torch.clamp_min(raw, 0.0).mean())
            return Evaluation(ensemble, raw, None, key_rate, {}, {})

        result = None
        with patch("src.optimization.trainer.evaluate_transmitter", side_effect=fake_evaluate):
            result = train_step(
                self.model, optimizer, self.t[:1], self.epsilon[:1],
                beta_reconciliation=0.95, noise_samples_per_symbol=2,
                density_eigenvalue_tolerance=1e-13, generator=generator,
                energy_budget_controller=controller, pointwise_guard=guard,
            )
        self.assertFalse(result.pointwise_guard_committed)
        self.assertEqual(result.pointwise_guard_result.status, PointwiseStatus.POINTWISE_GUARD_BAND_REJECT)
        _assert_snapshot_equal(self, before, self.model, optimizer, controller, generator)

    def test_accepted_endpoint_commits_and_dual_updates_once(self) -> None:
        guard = _guard(lambda ensemble, row, config: _evidence())
        optimizer = torch.optim.Adam(self.model.parameters(), lr=1e-3)
        controller = EnergyBudgetController(va_budget=0.5, dual_learning_rate=0.1, multiplier=0.4)
        generator = torch.Generator().manual_seed(993)

        def fake_evaluate(transmitter, transmittance, epsilon, *, generator, **kwargs):
            ensemble = transmitter(transmittance, epsilon)
            raw = ensemble.probabilities[:, 0]
            key_rate = FadingKeyRate(raw, raw.mean(), torch.clamp_min(raw, 0.0), torch.clamp_min(raw, 0.0).mean())
            return Evaluation(ensemble, raw, None, key_rate, {}, {})

        before = [parameter.detach().clone() for parameter in self.model.parameters()]
        with patch("src.optimization.trainer.evaluate_transmitter", side_effect=fake_evaluate):
            result = train_step(
                self.model, optimizer, self.t[:1], self.epsilon[:1],
                beta_reconciliation=0.95, noise_samples_per_symbol=2,
                density_eigenvalue_tolerance=1e-13, generator=generator,
                energy_budget_controller=controller, pointwise_guard=guard,
            )
        self.assertTrue(result.pointwise_guard_committed)
        self.assertEqual(result.pointwise_guard_result.status, PointwiseStatus.POINTWISE_ADMISSIBLE)
        self.assertTrue(any(not torch.equal(old, new) for old, new in zip(before, self.model.parameters())))
        self.assertGreater(result.energy_dual_after_update, result.energy_dual_before_update)

    def test_real_flint_adapter_certifies_uniform_fixture(self) -> None:
        adapter = RealPointCertifierAdapter(
            ROOT,
            worker=ROOT / "scripts" / "pointwise_certifier_worker.py",
            certification_python=ROOT / ".venv-cert" / "Scripts" / "python.exe",
            expected_provenance={"protocol": "x"},
            actual_provenance={"protocol": "x"},
            timeout_seconds=600.0,
        )
        ensemble = JointTransmitter("uniform", fixed_va=1.5, v_min=0.1, v_max=4.0)(
            self.t[:1], self.epsilon[:1]
        )
        result = adapter(ensemble, 0, _config())
        self.assertEqual(result["status"], "CERTIFIED_POINT", result)
        self.assertEqual(result["support_count"], 17)
        self.assertLess(result["upper_nearest_below"], _config().tau_float64)
        self.assertGreater(result["lower_nearest_above"], _config().tau_float64)

    def test_adapter_serialization_preserves_final_ensemble_exactly(self) -> None:
        ensemble = JointTransmitter("full", v_min=0.1, v_max=4.0)(
            self.t[:1], self.epsilon[:1]
        )
        request = RealPointCertifierAdapter._request(ensemble, 0, _config())
        probabilities = torch.tensor(
            [float.fromhex(value) for value in request["probabilities_float64_hex"]],
            dtype=torch.float64,
        )
        amplitudes = torch.tensor(
            [complex(float.fromhex(real), float.fromhex(imag))
             for real, imag in request["amplitudes_float64_hex"]],
            dtype=torch.complex128,
        )
        self.assertTrue(torch.equal(probabilities, ensemble.probabilities[0]))
        self.assertTrue(torch.equal(amplitudes, ensemble.amplitudes[0]))

    def test_real_flint_adapter_certifies_binomial_fixture(self) -> None:
        adapter = RealPointCertifierAdapter(
            ROOT,
            worker=ROOT / "scripts" / "pointwise_certifier_worker.py",
            certification_python=ROOT / ".venv-cert" / "Scripts" / "python.exe",
            expected_provenance={"protocol": "x"},
            actual_provenance={"protocol": "x"},
            timeout_seconds=600.0,
        )
        ensemble = JointTransmitter("binomial", fixed_va=1.5, v_min=0.1, v_max=4.0)(
            self.t[:1], self.epsilon[:1]
        )
        result = adapter(ensemble, 0, _config())
        self.assertEqual(result["status"], "CERTIFIED_POINT", result)
        self.assertEqual(result["support_count"], 29)

    def test_real_flint_adapter_near_coincident_fixture_fails_only_closed(self) -> None:
        orbit_masses = torch.full((64,), 1.0 / 64.0, dtype=torch.float64)
        from src.modulation.qam256 import expand_c4_orbit_masses, expand_c4_orbit_values
        prototypes = math.sqrt(4.0 / 2.0) * torch.exp(
            1j * 5e-8 * torch.arange(64, dtype=torch.float64)
        )
        ensemble = Ensemble(
            expand_c4_orbit_masses(orbit_masses).unsqueeze(0),
            expand_c4_orbit_values(prototypes).unsqueeze(0),
            torch.tensor([4.0], dtype=torch.float64), prototypes,
            exact_csi_oracle=True, c4_symmetric=True,
        )
        adapter = RealPointCertifierAdapter(
            ROOT,
            worker=ROOT / "scripts" / "pointwise_certifier_worker.py",
            certification_python=ROOT / ".venv-cert" / "Scripts" / "python.exe",
            expected_provenance={"protocol": "x"},
            actual_provenance={"protocol": "x"},
            timeout_seconds=600.0,
        )
        result = adapter(ensemble, 0, _config())
        self.assertIn(result["status"], {"CERTIFIED_POINT", "UNCERTIFIED_POINT"})


def _snapshot(model, optimizer, controller, generator):
    return {
        "model": copy.deepcopy(model.state_dict()),
        "optimizer": copy.deepcopy(optimizer.state_dict()),
        "controller": controller.multiplier,
        "generator": generator.get_state().clone(),
        "python": random.getstate(),
        "numpy": np.random.get_state(),
        "torch": torch.get_rng_state().clone(),
    }


def _assert_snapshot_equal(testcase, before, model, optimizer, controller, generator):
    for key, value in before["model"].items():
        testcase.assertTrue(torch.equal(value, model.state_dict()[key]), key)
    _assert_nested_equal(testcase, before["optimizer"], optimizer.state_dict())
    testcase.assertEqual(before["controller"], controller.multiplier)
    testcase.assertTrue(torch.equal(before["generator"], generator.get_state()))
    testcase.assertEqual(before["python"], random.getstate())
    np.testing.assert_array_equal(before["numpy"][1], np.random.get_state()[1])
    testcase.assertEqual(before["numpy"][0], np.random.get_state()[0])
    testcase.assertTrue(torch.equal(before["torch"], torch.get_rng_state()))


def _assert_nested_equal(testcase, left, right):
    if isinstance(left, torch.Tensor):
        testcase.assertTrue(torch.equal(left, right))
    elif isinstance(left, dict):
        testcase.assertEqual(set(left), set(right))
        for key in left:
            _assert_nested_equal(testcase, left[key], right[key])
    elif isinstance(left, (list, tuple)):
        testcase.assertEqual(len(left), len(right))
        for left_value, right_value in zip(left, right):
            _assert_nested_equal(testcase, left_value, right_value)
    else:
        testcase.assertEqual(left, right)


if __name__ == "__main__":
    unittest.main()
