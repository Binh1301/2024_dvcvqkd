import inspect
import unittest

import torch

from src.cvqkd.spectral_frechet import hermitian_inverse_sqrt, hermitian_sqrt


class SpectralFrechetVjpTests(unittest.TestCase):
    def test_repeated_spectrum_backward_is_finite_hermitian(self):
        matrix = torch.eye(3, dtype=torch.complex128, requires_grad=True)
        weight = torch.tensor(
            [[1, 1j, 0], [-1j, 2, 0.5], [0, 0.5, -1]],
            dtype=torch.complex128,
        )
        output = hermitian_inverse_sqrt(matrix)
        loss = torch.sum((output.conj() * weight).real)
        gradient, = torch.autograd.grad(loss, matrix)
        self.assertTrue(torch.isfinite(gradient).all())
        torch.testing.assert_close(gradient, gradient.mH, atol=1e-12, rtol=1e-11)

    def test_inverse_sqrt_vjp_matches_central_difference_at_complex_hpd(self):
        matrix = torch.tensor([[3, 1j], [-1j, 4]], dtype=torch.complex128, requires_grad=True)
        direction = torch.tensor([[1, 0.5j], [-0.5j, -1]], dtype=torch.complex128)
        weight = torch.tensor([[0.5, 0.2j], [-0.2j, -0.7]], dtype=torch.complex128)
        scalar = lambda value: torch.sum((hermitian_inverse_sqrt(value).conj() * weight).real)
        analytic, = torch.autograd.grad(scalar(matrix), matrix)
        h = 1e-6
        numerical = float((scalar(matrix.detach() + h * direction) - scalar(matrix.detach() - h * direction)) / (2 * h))
        directional = float(torch.sum((analytic.conj() * direction).real))
        self.assertAlmostEqual(directional, numerical, delta=1e-10)

    def test_square_root_vjp_is_cluster_safe(self):
        matrix = torch.diag(torch.tensor([2.0, 2.0, 5.0], dtype=torch.float64)).to(torch.complex128).requires_grad_()
        output = hermitian_sqrt(matrix)
        output.real.sum().backward()
        self.assertTrue(torch.isfinite(matrix.grad).all())

    def test_custom_boundary_does_not_expose_native_eigh_backward(self):
        matrix = torch.eye(2, dtype=torch.complex128, requires_grad=True)
        output = hermitian_inverse_sqrt(matrix)
        self.assertIn("HermitianInverseSqrtBackward", type(output.grad_fn).__name__)
        source = inspect.getsource(hermitian_inverse_sqrt)
        self.assertNotIn("torch.linalg.eigh", source)

    def test_nonpositive_input_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "positive definite"):
            hermitian_inverse_sqrt(torch.diag(torch.tensor([1.0, 0.0], dtype=torch.float64)).to(torch.complex128))


if __name__ == "__main__":
    unittest.main()
