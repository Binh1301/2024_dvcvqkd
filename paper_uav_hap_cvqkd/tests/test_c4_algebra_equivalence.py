import unittest

import torch

from src.cvqkd import gram_moments as gm


DTYPE = torch.float64
CDTYPE = torch.complex128
ROTATIONS = torch.tensor([1.0, 1.0j, -1.0, -1.0j], dtype=CDTYPE)


def _fixture():
    prototypes = torch.tensor([1.0 + 0.0j, 2.0 + 0.3j], dtype=CDTYPE)
    orbit_masses = torch.tensor([0.35, 0.65], dtype=DTYPE)
    amplitudes = torch.stack(
        [prototype * ROTATIONS for prototype in prototypes]
    ).reshape(-1)
    probabilities = torch.repeat_interleave(orbit_masses / 4.0, 4)
    return probabilities, amplitudes


def _gram(probabilities, amplitudes):
    weight = torch.sqrt(probabilities[:, None] * probabilities[None, :])
    return weight * torch.exp(
        -0.5 * (
            amplitudes.abs().square()[:, None]
            + amplitudes.abs().square()[None, :]
        )
        + amplitudes.conj()[:, None] * amplitudes[None, :]
    )


def _fourier_unitary(orbit_count):
    f4 = torch.tensor(
        [[(1.0j) ** (row * column) for column in range(4)] for row in range(4)],
        dtype=CDTYPE,
    ) / 2.0
    return torch.kron(torch.eye(orbit_count, dtype=CDTYPE), f4)


def _block(matrix, sector_row, sector_column, orbit_count):
    rows = torch.tensor(
        [4 * orbit + sector_row for orbit in range(orbit_count)]
    )
    columns = torch.tensor(
        [4 * orbit + sector_column for orbit in range(orbit_count)]
    )
    return matrix[rows][:, columns]


def _fock_vectors(amplitudes, cutoff):
    number = torch.arange(cutoff, dtype=DTYPE)
    factorial = torch.exp(-0.5 * torch.lgamma(number + 1.0))
    return (
        torch.exp(-0.5 * amplitudes.abs().square()).unsqueeze(-1)
        * amplitudes.unsqueeze(-1) ** number.to(torch.int64)
        * factorial
    ).T


def _annihilation(cutoff):
    operator = torch.zeros((cutoff, cutoff), dtype=CDTYPE)
    indices = torch.arange(1, cutoff)
    operator[indices - 1, indices] = torch.sqrt(indices.to(DTYPE)).to(CDTYPE)
    return operator


def _positive_power(matrix, exponent):
    values, vectors = torch.linalg.eigh(matrix)
    return vectors @ torch.diag(values.pow(exponent)).to(CDTYPE) @ vectors.mH


class C4AlgebraEquivalenceTests(unittest.TestCase):
    def test_dense_fock_gram_and_c4_algebra_are_equivalent(self):
        probabilities, amplitudes = _fixture()
        gram = _gram(probabilities, amplitudes)
        diagonal_amplitudes = torch.diag(amplitudes)
        unitary = _fourier_unitary(2)
        gram_hat = unitary.mH @ gram @ unitary
        amplitudes_hat = unitary.mH @ diagonal_amplitudes @ unitary

        identity = torch.eye(8, dtype=CDTYPE)
        torch.testing.assert_close(unitary.mH @ unitary, identity, atol=1e-14, rtol=0.0)

        for sector in range(4):
            for other in range(4):
                if sector != other:
                    self.assertLess(
                        float(_block(gram_hat, sector, other, 2).abs().max()),
                        1e-13,
                    )
        expected_d_blocks = {(0, 3), (1, 0), (2, 1), (3, 2)}
        for sector in range(4):
            for other in range(4):
                block = _block(amplitudes_hat, sector, other, 2)
                if (sector, other) in expected_d_blocks:
                    self.assertGreater(float(block.abs().max()), 1e-6)
                else:
                    self.assertLess(float(block.abs().max()), 1e-13)

        global_spectrum = torch.linalg.eigvalsh(gram).sort().values
        sector_spectra = torch.cat(
            [torch.linalg.eigvalsh(_block(gram_hat, sector, sector, 2)) for sector in range(4)]
        ).sort().values
        torch.testing.assert_close(global_spectrum, sector_spectra, atol=1e-13, rtol=0.0)

        values, vectors = torch.linalg.eigh(gram)
        half = vectors @ torch.diag(torch.sqrt(values)).to(CDTYPE) @ vectors.mH
        half_inverse = vectors @ torch.diag(torch.rsqrt(values)).to(CDTYPE) @ vectors.mH
        dense_s = half @ diagonal_amplitudes @ half_inverse
        dense_a = gram @ diagonal_amplitudes @ torch.linalg.inv(gram)
        torch.testing.assert_close(dense_s @ half, half @ diagonal_amplitudes, atol=1e-12, rtol=1e-12)

        s_hat = unitary.mH @ dense_s @ unitary
        a_hat = unitary.mH @ dense_a @ unitary
        for sector in range(4):
            previous = (sector - 1) % 4
            g_s = _block(gram_hat, sector, sector, 2)
            g_r = _block(gram_hat, previous, previous, 2)
            d_sr = _block(amplitudes_hat, sector, previous, 2)
            h_s_values, h_s_vectors = torch.linalg.eigh(g_s)
            h_r_values, h_r_vectors = torch.linalg.eigh(g_r)
            h_s = h_s_vectors @ torch.diag(torch.sqrt(h_s_values)).to(CDTYPE) @ h_s_vectors.mH
            h_r = h_r_vectors @ torch.diag(torch.sqrt(h_r_values)).to(CDTYPE) @ h_r_vectors.mH
            b_current = h_s @ d_sr @ torch.linalg.inv(h_r)
            aa_current = g_s @ d_sr @ torch.linalg.inv(g_r)
            torch.testing.assert_close(
                _block(s_hat, sector, previous, 2), b_current, atol=1e-12, rtol=1e-11
            )
            torch.testing.assert_close(
                _block(a_hat, sector, previous, 2), aa_current, atol=1e-12, rtol=1e-11
            )
            torch.testing.assert_close(
                aa_current @ h_r, h_s @ b_current, atol=1e-12, rtol=1e-11
            )
            self.assertGreater(float((aa_current - b_current).abs().max()), 1e-6)

        synthesis = _fock_vectors(amplitudes, 48) * torch.sqrt(probabilities).unsqueeze(0)
        fock_gram = synthesis.mH @ synthesis
        fock_values, fock_vectors = torch.linalg.eigh(fock_gram)
        fock_half = fock_vectors @ torch.diag(torch.sqrt(fock_values)).to(CDTYPE) @ fock_vectors.mH
        fock_half_inverse = fock_vectors @ torch.diag(torch.rsqrt(fock_values)).to(CDTYPE) @ fock_vectors.mH
        q_basis = synthesis @ fock_half_inverse
        annihilation = _annihilation(48)
        tau_half = q_basis @ fock_half @ q_basis.mH
        tau_half_inverse = q_basis @ fock_half_inverse @ q_basis.mH
        a_tau = tau_half @ annihilation @ tau_half_inverse
        torch.testing.assert_close(
            a_tau @ synthesis, synthesis @ dense_s, atol=2e-12, rtol=2e-11
        )
        direct_a = q_basis.mH @ a_tau @ q_basis
        torch.testing.assert_close(direct_a, dense_a, atol=2e-12, rtol=2e-11)

        direct_c = torch.trace(
            tau_half @ annihilation @ tau_half @ annihilation.mH
        ).real
        positive_c = torch.zeros((), dtype=DTYPE)
        for sector in range(4):
            previous = (sector - 1) % 4
            g_s = _block(gram_hat, sector, sector, 2)
            g_r = _block(gram_hat, previous, previous, 2)
            d_sr = _block(amplitudes_hat, sector, previous, 2)
            x_sr = _positive_power(g_s, 0.75) @ d_sr @ torch.linalg.inv(
                _positive_power(g_r, 0.25)
            )
            positive_c = positive_c + torch.linalg.matrix_norm(x_sr).square()
        trace_c = torch.trace(fock_half @ dense_s @ fock_half @ dense_s.mH).real
        torch.testing.assert_close(positive_c, trace_c, atol=1e-11, rtol=1e-10)
        torch.testing.assert_close(trace_c, direct_c, atol=2e-11, rtol=2e-10)

        gram_s = fock_gram @ dense_s
        mu = torch.diagonal(gram_s) / probabilities
        residual_vectors = dense_s - torch.diag(mu)
        gram_w = torch.trace(residual_vectors.mH @ fock_gram @ residual_vectors).real
        fock_t1 = torch.einsum("ni,nm,mj->ij", _fock_vectors(amplitudes, 48).conj(), a_tau.mH @ a_tau, _fock_vectors(amplitudes, 48)).diagonal().real
        fock_inner = torch.einsum("ni,nm,mi->i", _fock_vectors(amplitudes, 48).conj(), a_tau, _fock_vectors(amplitudes, 48))
        fock_w = torch.sum(probabilities * (fock_t1 - fock_inner.abs().square()))
        torch.testing.assert_close(gram_w, fock_w, atol=2e-10, rtol=2e-9)

        p64 = torch.full((64,), 1.0 / 64.0, dtype=DTYPE)
        z64 = torch.arange(1, 65, dtype=DTYPE).to(CDTYPE)
        fast, gate = gm._fast(p64, z64)
        self.assertIsNotNone(fast, gate)
        self.assertGreater(float(fast["C"]), 0.0)
        self.assertGreaterEqual(float(fast["w"]), 0.0)


if __name__ == "__main__":
    unittest.main()
