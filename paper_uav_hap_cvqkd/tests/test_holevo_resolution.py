import unittest

import torch

from src.cvqkd.holevo import _holevo_from_source_moments, _maximize_bounded_scalar
from src.modulation.joint_ps_gs import JointTransmitter


class FullZResolutionTests(unittest.TestCase):
    def _maximize(self, lower, upper, target, grid_size):
        lower_tensor = torch.tensor([lower], dtype=torch.float64)
        upper_tensor = torch.tensor([upper], dtype=torch.float64)
        return _maximize_bounded_scalar(
            lower_tensor,
            upper_tensor,
            lambda z: 1.0 - (z - target).square(),
            grid_size=grid_size,
            refinement_steps=16,
        )

    def test_resolution_grid_is_stable_for_interior_maximum(self):
        reference_value, reference_point = self._maximize(-1.0, 1.0, 0.173, 129)
        for grid_size in (17, 33, 65, 129):
            with self.subTest(grid_size=grid_size):
                value, point = self._maximize(-1.0, 1.0, 0.173, grid_size)
                self.assertAlmostEqual(float(point.item()), 0.173, delta=1e-5)
                self.assertAlmostEqual(
                    float(value.item()), float(reference_value.item()), delta=1e-10
                )
                self.assertAlmostEqual(
                    float(point.item()), float(reference_point.item()), delta=1e-5
                )

    def test_boundaries_narrow_intervals_and_near_boundary_are_retained(self):
        cases = (
            (-1.0, -0.25, -1.0, "lower"),
            (0.25, 1.0, 1.0, "upper"),
            (0.100000, 0.100100, 0.100041, "interior"),
            (0.100000, 0.100100, 0.100000 + 1e-10, "lower"),
        )
        for lower, upper, target, branch in cases:
            for grid_size in (17, 33, 65, 129):
                with self.subTest(case=branch, grid_size=grid_size):
                    _, point = self._maximize(lower, upper, target, grid_size)
                    observed = float(point.item())
                    if branch == "lower":
                        self.assertAlmostEqual(observed, lower, delta=1e-12)
                    elif branch == "upper":
                        self.assertAlmostEqual(observed, upper, delta=1e-12)
                    else:
                        self.assertGreater(observed, lower)
                        self.assertLess(observed, upper)

    def test_holevo_value_is_resolution_stable_on_admissible_fixture(self):
        ensemble = JointTransmitter("uniform", fixed_va=2.0)(
            torch.tensor([1.0], dtype=torch.float64),
            torch.tensor([0.0], dtype=torch.float64),
        )

        def evaluate(grid_size):
            return _holevo_from_source_moments(
                ensemble,
                torch.tensor([0.1], dtype=torch.float64),
                torch.tensor([0.1], dtype=torch.float64),
                coherent_correlation=torch.tensor([0.4], dtype=torch.float64),
                w_raw=torch.tensor([0.2], dtype=torch.float64),
                tau=None,
                tau_trace=torch.ones(1, dtype=torch.float64),
                require_supported_symmetry=True,
                symmetry_tolerance=1e-8,
                physicality_tolerance=1e-10,
                diagnostics={},
                z_grid_size=grid_size,
                z_refinement_steps=16,
            )

        reference = evaluate(129)
        for grid_size in (17, 33, 65, 129):
            with self.subTest(grid_size=grid_size):
                result = evaluate(grid_size)
                torch.testing.assert_close(
                    result.chi_be,
                    reference.chi_be,
                    atol=1e-9,
                    rtol=1e-8,
                )
                torch.testing.assert_close(result.z, reference.z, atol=1e-5, rtol=0.0)


if __name__ == "__main__":
    unittest.main()
