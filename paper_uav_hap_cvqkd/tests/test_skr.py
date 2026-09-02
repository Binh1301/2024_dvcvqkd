import unittest

import torch

from src.cvqkd.secret_key_rate import fading_secret_key_rate


class SecretKeyRateTests(unittest.TestCase):
    def test_average_is_after_instantaneous_skr(self):
        mutual_information = torch.tensor([0.0, 1.0], dtype=torch.float64)
        holevo = torch.tensor([0.2, 0.1], dtype=torch.float64)
        result = fading_secret_key_rate(mutual_information, holevo, 0.95)
        expected = torch.tensor([-0.2, 0.85], dtype=torch.float64)
        self.assertTrue(torch.allclose(result.instantaneous_raw, expected, atol=1e-15, rtol=0.0))
        self.assertAlmostEqual(float(result.fading_average_raw), 0.325)
        self.assertAlmostEqual(float(result.fading_average_positive_part), 0.425)
        self.assertNotEqual(
            float(result.fading_average_raw), float(result.fading_average_positive_part)
        )

    def test_invalid_beta_rejected(self):
        with self.assertRaises(ValueError):
            fading_secret_key_rate(torch.ones(1), torch.zeros(1), 1.1)


if __name__ == "__main__":
    unittest.main()
