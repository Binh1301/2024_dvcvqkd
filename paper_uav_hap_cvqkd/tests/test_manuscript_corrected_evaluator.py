"""Integration boundaries: no unsupported SKR or unauthenticated source reuse."""
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from src.manuscript_literal_3moments import LiteralChannel
from src.manuscript_corrected_3moments import PhysicalFadingDistribution
from src.manuscript_corrected_evaluator import evaluate_candidate, validate_cached_candidate

ROOT = Path(__file__).resolve().parents[1]


class CorrectedEvaluatorTests(unittest.TestCase):
    metrics = {}

    @classmethod
    def setUpClass(cls):
        from scripts.run_manuscript_literal_3moments import verified_candidate
        from scripts.run_theta10_D55_unconstrained_three_scheme import unconstrained_config
        saved = json.loads((ROOT/'results/manuscript_literal_3moments/implementation_validation_4/validation.json').read_text())
        reference = saved['metrics']['reference_new_mode_D_F']
        path = ROOT/'results/exact_mb_test2/exact_source_cache'/f"{reference['source_cache_key']}.json"
        cls.candidate = verified_candidate(path, unconstrained_config())
        cls.settings = json.loads((ROOT/'configs/manuscript_corrected_3moments.json').read_text())

    def test_nonideal_security_blocks_mi_and_skr(self):
        # Synthetic physical channel; this is not a corrected reference-point run.
        fading = PhysicalFadingDistribution(LiteralChannel(.85,.91,1.4,1.,.12,0.,.02,.98))
        with patch('src.manuscript_corrected_evaluator.discrete_fading_mutual_information',
                   side_effect=AssertionError('MI must not launch after security blocker')):
            result = evaluate_candidate(self.candidate, fading, self.settings, distance_km=21.)
        record = result['record']
        self.assertEqual(record['status'], 'BLOCKED_BY_SCIENTIFIC_MODEL')
        for key in ['I_AB','chi_BE','K_raw','K_operational','Z_worst','lambda_1','lambda_2']:
            self.assertIsNone(record[key])
            self.assertIn(key,record['unavailable_fields'])
        self.assertEqual(record['detector_security_convention'],'trusted')
        self.assertEqual(record['a'],6.5)
        self.assertNotEqual(record['scientific_model'],'manuscript_literal_3moments')
        self.assertEqual(len(record['scientific_context_hash']),64)
        self.metrics['synthetic_nonideal_integration'] = result

    def test_tampered_cache_rejected(self):
        with self.assertRaises(ValueError):
            validate_cached_candidate({**self.candidate,'C':self.candidate['C']+.01})

    def test_direct_api_rejects_wrong_protocol(self):
        fading = PhysicalFadingDistribution(LiteralChannel(.85,.91,1.4,1.,.12,0.,.02,.98))
        with self.assertRaisesRegex(ValueError,'phase_noise'):
            evaluate_candidate(self.candidate, fading, {**self.settings,'phase_noise':'ON'}, distance_km=21.)


if __name__=='__main__':
    unittest.main()
