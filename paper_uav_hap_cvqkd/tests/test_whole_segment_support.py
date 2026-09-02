import copy
import math

import numpy as np
import torch
import unittest

from src.modulation.joint_ps_gs import JointTransmitter
from src.validation.whole_segment_support import (
    certify_segment_by_bisection,
    certify_support_from_validated_intervals,
    gram_derivative_frobenius_bound,
    transmitter_segment_bounds,
)


def test_obvious_no_crossing_certifies():
    result = certify_support_from_validated_intervals(
        [0.1, 0.8], [0.1, 0.8], retained_rank=1, threshold=0.5,
        variation_radius=0.05, numerical_radius=0.0,
    )
    assert result.certified


def test_known_crossing_fails_closed():
    result = certify_support_from_validated_intervals(
        [0.1, 0.51], [0.1, 0.51], retained_rank=1, threshold=0.5,
        variation_radius=0.02, numerical_radius=0.0,
    )
    assert not result.certified


def test_near_boundary_non_crossing_certifies_with_sufficient_margin():
    result = certify_support_from_validated_intervals(
        [0.49, 0.51], [0.49, 0.51], retained_rank=1, threshold=0.5,
        variation_radius=0.004, numerical_radius=0.001,
    )
    assert result.certified


def test_missing_numerical_enclosure_always_fails_closed():
    result = certify_support_from_validated_intervals(
        [0.1, 0.9], [0.1, 0.9], retained_rank=1, threshold=0.5,
        variation_radius=0.0, numerical_radius=None,
    )
    assert not result.certified


def test_bisection_certifies_complete_no_crossing_segment():
    result = certify_segment_by_bisection(
        lambda t: ([0.1, 0.8 + 0.02 * t], [0.1, 0.8 + 0.02 * t]),
        lambda left, right: 0.02,
        retained_rank=1, threshold=0.5, numerical_radius=0.0,
        maximum_depth=8, minimum_interval_width=2.0 ** -8,
    )
    assert result.certified
    assert not result.unresolved_intervals


def test_bisection_rejects_known_support_crossing():
    result = certify_segment_by_bisection(
        lambda t: ([0.1, 0.51 - 0.04 * t], [0.1, 0.51 - 0.04 * t]),
        lambda left, right: 0.04,
        retained_rank=1, threshold=0.5, numerical_radius=0.0,
        maximum_depth=10, minimum_interval_width=2.0 ** -10,
    )
    assert not result.certified
    assert result.unresolved_intervals


def _segment(families: tuple[str, ...]):
    torch.manual_seed(27083002)
    start = JointTransmitter("full", v_min=0.1, v_max=4.0, n_peak_photons=30.0)
    end = copy.deepcopy(start)
    generator = torch.Generator().manual_seed(27083003)
    with torch.no_grad():
        for name, parameter in end.named_parameters():
            family = "ps" if name.startswith("ps_network") else "gs" if name.startswith("gs_model") else "va"
            if family in families:
                scale = {"ps": 3e-4, "gs": 1e-4, "va": 1e-4}[family]
                parameter.add_(scale * torch.randn(parameter.shape, dtype=parameter.dtype, generator=generator))
    bounds = transmitter_segment_bounds(start, end, 0.025, 0.02)
    derivative = gram_derivative_frobenius_bound(bounds)
    assert math.isfinite(derivative) and derivative > 0.0
    assert bounds.probability_lower.min() > 0.0
    assert bounds.va_lower > 0.0
    assert bounds.energy_lower > 0.0
    endpoint_grams = []
    for fraction in np.linspace(0.0, 1.0, 17):
        trial = copy.deepcopy(start)
        with torch.no_grad():
            for (_, parameter), (_, left), (_, right) in zip(
                trial.named_parameters(), start.named_parameters(), end.named_parameters()
            ):
                parameter.copy_(left + float(fraction) * (right - left))
        ensemble = trial(
            torch.tensor([0.025], dtype=torch.float64),
            torch.tensor([0.02], dtype=torch.float64),
        )
        probability = ensemble.probabilities[0].detach().numpy()
        amplitude = ensemble.amplitudes[0].detach().numpy()
        assert np.all(probability >= bounds.probability_lower)
        assert np.all(probability <= bounds.probability_upper)
        assert np.all(np.abs(amplitude) <= bounds.amplitude_abs_upper)
        assert bounds.va_lower <= float(ensemble.declared_va[0].detach()) <= bounds.va_upper
        root = np.sqrt(probability)
        gram = root[:, None] * root[None, :] * np.exp(
            -0.5 * (np.abs(amplitude)[:, None] ** 2 + np.abs(amplitude)[None, :] ** 2)
            + amplitude.conj()[:, None] * amplitude[None, :]
        )
        if fraction in (0.0, 1.0):
            endpoint_grams.append(gram)
    observed_endpoint_change = np.linalg.norm(endpoint_grams[1] - endpoint_grams[0], ord="fro")
    assert observed_endpoint_change <= derivative
    return derivative


def test_ps_perturbation_derivative_enclosure_is_finite():
    _segment(("ps",))


def test_gs_perturbation_derivative_enclosure_is_finite():
    _segment(("gs",))


def test_va_perturbation_derivative_enclosure_is_finite():
    _segment(("va",))


def test_mixed_perturbation_derivative_enclosure_is_finite():
    _segment(("ps", "gs", "va"))


class WholeSegmentSupportTests(unittest.TestCase):
    def test_obvious_no_crossing_certifies(self):
        test_obvious_no_crossing_certifies()

    def test_known_crossing_fails_closed(self):
        test_known_crossing_fails_closed()

    def test_near_boundary_non_crossing_certifies_with_sufficient_margin(self):
        test_near_boundary_non_crossing_certifies_with_sufficient_margin()

    def test_missing_numerical_enclosure_always_fails_closed(self):
        test_missing_numerical_enclosure_always_fails_closed()

    def test_bisection_certifies_complete_no_crossing_segment(self):
        test_bisection_certifies_complete_no_crossing_segment()

    def test_bisection_rejects_known_support_crossing(self):
        test_bisection_rejects_known_support_crossing()

    def test_ps_perturbation_derivative_enclosure_is_finite(self):
        test_ps_perturbation_derivative_enclosure_is_finite()

    def test_gs_perturbation_derivative_enclosure_is_finite(self):
        test_gs_perturbation_derivative_enclosure_is_finite()

    def test_va_perturbation_derivative_enclosure_is_finite(self):
        test_va_perturbation_derivative_enclosure_is_finite()

    def test_mixed_perturbation_derivative_enclosure_is_finite(self):
        test_mixed_perturbation_derivative_enclosure_is_finite()


if __name__ == "__main__":
    unittest.main()
