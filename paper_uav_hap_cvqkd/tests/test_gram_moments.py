import unittest

import torch

from src.cvqkd.gram_moments import c4_gram_source_moments
from src.cvqkd.holevo import holevo_information
from src.modulation.joint_ps_gs import reference_ensemble


class GramMomentTests(unittest.TestCase):
    def test_well_conditioned_c4_gram_matches_dense_fock_source_moments(self):
        t = torch.tensor([0.024], dtype=torch.float64)
        epsilon = torch.tensor([0.02], dtype=torch.float64)
        for kind, nu, va in (
            ("uniform", None, 0.1), ("binomial", None, 1.5), ("mb", 0.3, 0.7)
        ):
            ensemble = reference_ensemble(
                kind, batch_size=1, modulation_variance=va, nu_mb=nu
            )
            gram = c4_gram_source_moments(
                ensemble, density_eigenvalue_tolerance=1e-12
            )
            dense = holevo_information(
                ensemble, t, epsilon, fock_cutoff=72,
                density_trace_tolerance=1e-10,
                density_eigenvalue_tolerance=1e-12,
            )
            torch.testing.assert_close(
                gram.coherent_correlation, dense.coherent_correlation,
                rtol=1e-11, atol=1e-12,
            )
            torch.testing.assert_close(gram.w, dense.w, rtol=1e-10, atol=1e-12)


if __name__ == "__main__":
    unittest.main()
