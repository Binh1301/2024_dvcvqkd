import unittest

import torch

from src.cvqkd.mutual_information import discrete_mutual_information
from src.modulation.joint_ps_gs import Ensemble, reference_ensemble
from src.modulation.normalization import physical_amplitudes
from src.modulation.qam256 import square_qam256


class MutualInformationTests(unittest.TestCase):
    def test_optimized_distance_path_matches_literal_reference(self):
        for kind, nu in (("uniform", None), ("binomial", None), ("mb", 0.23)):
            ensemble = reference_ensemble(
                kind, batch_size=2, modulation_variance=1.3, nu_mb=nu
            )
            generator = torch.Generator().manual_seed(918273)
            noise = torch.complex(
                torch.randn((2, 256, 11), dtype=torch.float64, generator=generator),
                torch.randn((2, 256, 11), dtype=torch.float64, generator=generator),
            ) / (2.0 ** 0.5)
            arguments = dict(
                ensemble=ensemble,
                transmittance=torch.tensor([0.019, 0.029], dtype=torch.float64),
                epsilon=torch.tensor([0.04, 0.001], dtype=torch.float64),
                noise_samples_per_symbol=11,
                standard_noise_samples=noise,
                noise_sample_chunk_size=4,
            )
            reference = discrete_mutual_information(**arguments, implementation="reference")
            optimized = discrete_mutual_information(**arguments, implementation="optimized")
            torch.testing.assert_close(optimized, reference, rtol=1e-12, atol=1e-12)

    def test_product_qam_path_matches_both_generic_paths(self):
        for kind, nu, va in (
            ("uniform", None, 0.1), ("uniform", None, 1.5),
            ("binomial", None, 1.3), ("mb", 0.01, 0.7),
            ("mb", 0.1, 1.5), ("mb", 0.3, 0.4),
        ):
            ensemble = reference_ensemble(kind, batch_size=3, modulation_variance=va, nu_mb=nu)
            generator = torch.Generator().manual_seed(190827)
            noise = torch.complex(
                torch.randn((3, 256, 13), dtype=torch.float64, generator=generator),
                torch.randn((3, 256, 13), dtype=torch.float64, generator=generator),
            ) / (2.0 ** 0.5)
            arguments = dict(
                ensemble=ensemble,
                transmittance=torch.tensor([0.019, 0.024, 0.029], dtype=torch.float64),
                epsilon=torch.tensor([0.04, 0.02, 0.001], dtype=torch.float64),
                noise_samples_per_symbol=13, standard_noise_samples=noise,
                noise_sample_chunk_size=5,
            )
            values = {
                implementation: discrete_mutual_information(
                    **arguments, implementation=implementation
                )
                for implementation in ("reference", "optimized", "product")
            }
            torch.testing.assert_close(values["product"], values["reference"],
                                       rtol=1e-12, atol=1e-12)
            torch.testing.assert_close(values["product"], values["optimized"],
                                       rtol=1e-12, atol=1e-12)

    def test_product_path_rejects_deformed_constellation(self):
        ensemble = reference_ensemble("uniform", batch_size=1, modulation_variance=1.0)
        amplitudes = ensemble.amplitudes.clone()
        amplitudes[0, 17] += 0.01 + 0.02j
        malformed = Ensemble(
            ensemble.probabilities, amplitudes, ensemble.declared_va,
            ensemble.relative_constellation,
        )
        # Avoid Ensemble.validate's energy mismatch masking the factorization
        # guard by declaring the actually computed variance.
        malformed = Ensemble(
            malformed.probabilities, malformed.amplitudes,
            malformed.computed_va(), malformed.relative_constellation,
        )
        with self.assertRaisesRegex(ValueError, "Cartesian product"):
            discrete_mutual_information(
                malformed, torch.tensor([0.02]), torch.tensor([0.01]),
                noise_samples_per_symbol=1,
                standard_noise_samples=torch.zeros((1, 256, 1), dtype=torch.complex128),
                implementation="product",
            )

    def test_noise_axis_chunking_preserves_estimator_and_gradients(self):
        ensemble = reference_ensemble("uniform", batch_size=1, modulation_variance=2.0)
        generator = torch.Generator().manual_seed(260827)
        noise = torch.complex(
            torch.randn((1, 256, 7), dtype=torch.float64, generator=generator),
            torch.randn((1, 256, 7), dtype=torch.float64, generator=generator),
        ) / (2.0 ** 0.5)
        values = []
        for chunk_size in (None, 1, 3, 16):
            probabilities = ensemble.probabilities.clone().requires_grad_(True)
            candidate = Ensemble(
                probabilities, ensemble.amplitudes, ensemble.declared_va,
                ensemble.relative_constellation,
            )
            value = discrete_mutual_information(
                candidate, torch.tensor([0.2]), torch.tensor([0.01]),
                noise_samples_per_symbol=7, standard_noise_samples=noise,
                noise_sample_chunk_size=chunk_size,
            )
            gradient, = torch.autograd.grad(value.sum(), probabilities)
            values.append((value.detach(), gradient.detach()))
        for value, gradient in values[1:]:
            torch.testing.assert_close(value, values[0][0], rtol=1e-12, atol=1e-12)
            torch.testing.assert_close(gradient, values[0][1], rtol=1e-11, atol=1e-11)

    def test_zero_transmittance_limit(self):
        ensemble = reference_ensemble("uniform", batch_size=1, modulation_variance=2.0)
        noise = torch.zeros((1, 256, 2), dtype=torch.complex128)
        value = discrete_mutual_information(
            ensemble,
            torch.tensor([0.0]),
            torch.tensor([0.0]),
            noise_samples_per_symbol=2,
            standard_noise_samples=noise,
        )
        self.assertLess(abs(float(value)), 1e-12)

    def test_high_snr_uniform_limit(self):
        ensemble = reference_ensemble("uniform", batch_size=1, modulation_variance=1e6)
        generator = torch.Generator().manual_seed(77)
        value = discrete_mutual_information(
            ensemble,
            torch.tensor([1.0]),
            torch.tensor([0.0]),
            noise_samples_per_symbol=4,
            generator=generator,
        )
        self.assertLess(abs(float(value) - 8.0), 1e-8)

    def test_zero_probability_symbols_are_numerically_safe(self):
        probabilities = torch.zeros((1, 256), dtype=torch.float64)
        probabilities[:, :128] = 1.0 / 128.0
        raw = square_qam256()
        variance = torch.tensor([2.0], dtype=torch.float64)
        ensemble = Ensemble(
            probabilities,
            physical_amplitudes(probabilities, raw, variance),
            variance,
            raw,
        )
        value = discrete_mutual_information(
            ensemble,
            torch.tensor([0.0]),
            torch.tensor([0.0]),
            noise_samples_per_symbol=1,
            standard_noise_samples=torch.zeros((1, 256, 1), dtype=torch.complex128),
        )
        self.assertTrue(bool(torch.isfinite(value).all()))
        self.assertLess(abs(float(value)), 1e-12)

    def test_differentiable_exact_zero_probability_is_rejected(self):
        probabilities = torch.zeros((1, 256), dtype=torch.float64)
        probabilities[:, :128] = 1.0 / 128.0
        probabilities.requires_grad_(True)
        raw = square_qam256()
        variance = torch.tensor([2.0], dtype=torch.float64)
        ensemble = Ensemble(
            probabilities,
            physical_amplitudes(probabilities, raw, variance),
            variance,
            raw,
        )
        with self.assertRaisesRegex(ValueError, "strictly positive"):
            discrete_mutual_information(
                ensemble,
                torch.tensor([0.1]),
                torch.tensor([0.0]),
                noise_samples_per_symbol=1,
                standard_noise_samples=torch.zeros((1, 256, 1), dtype=torch.complex128),
            )


if __name__ == "__main__":
    unittest.main()
