"""Read-only scientific checks and self-contained LaTeX package regressions."""
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
import zipfile
from scripts import finalize_theta10_D55_ao_manuscript as manuscript


class ManuscriptFinalizationTests(unittest.TestCase):
    def test_structure_numbering_and_all_inputs(self):
        result = manuscript.latex_check(manuscript.OUT)
        self.assertEqual(len(result['inputs']), 7)
        self.assertEqual(len(result['figures']), 5)
        self.assertEqual([result['preview_equation_numbers'][k] for k in ('eq:p1', 'eq:p2', 'eq:ao-stopping')], [5, 6, 7])
        self.assertEqual(result['algorithm_count'], 1)

    def test_zip_self_contained_and_byte_identical(self):
        expected = manuscript.saved.read(manuscript.OUT / 'package_manifest.json')
        with tempfile.TemporaryDirectory() as temporary:
            with zipfile.ZipFile(manuscript.OUT / 'objective_A_overleaf.zip') as z:
                self.assertIsNone(z.testzip())
                self.assertEqual(set(z.namelist()), set(expected) | {'package_manifest.json'})
                self.assertTrue(all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in z.namelist()))
                for n, digest in expected.items():
                    self.assertEqual(hashlib.sha256(z.read(n)).hexdigest(), digest)
                z.extractall(temporary)
            manuscript.latex_check(Path(temporary))

    def test_saved_numbers_without_optimizer_or_evaluator(self):
        m = manuscript.saved
        with patch.object(m.ao, 'evaluate_candidate', m.audit.forbidden), \
             patch.object(m.sweep, 'run_single_distance_ao', m.audit.forbidden), \
             patch.object(m.ao, 'adaptive_maximize_1d', m.audit.forbidden), \
             patch.object(m.ao.ExactMBEvaluator, 'source_moments', m.audit.forbidden):
            data, configs, numbers = manuscript.verify_materials()
        self.assertEqual(len(configs), 16)
        self.assertEqual(numbers['distinct_missing_pairs'], 55)
        ref = next(r for r in data['best'] if r['L_km'] == m.REF)
        self.assertEqual((ref['best_nu_raw'], ref['best_V_A'], ref['best_SKR']), (.165, 5.5, .07798099387393764))
        self.assertFalse(numbers['Uniform_boundary_fully_optimized'])

    def test_static_checker_rejects_undefined_reference(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            shutil.copytree(manuscript.OUT / 'figures', target / 'figures')
            for p in manuscript.OUT.glob('*.tex'):
                shutil.copy2(p, target / p.name)
            source = target / 'joint_optimization_final.tex'
            source.write_text(source.read_text(encoding='utf-8') + '\n\\ref{nonexistent-label}\n', encoding='utf-8')
            with self.assertRaisesRegex(AssertionError, 'Undefined labels'):
                manuscript.latex_check(target)

    def test_protected_hashes_compile_scope_and_outputs(self):
        protected = manuscript.saved.read(manuscript.OUT / 'protected_input_manifest.json')
        self.assertEqual(len(protected), 1733)
        self.assertTrue(all(manuscript.sha(manuscript.ROOT / name) == digest for name, digest in protected.items()))
        validation = manuscript.saved.read(manuscript.OUT / 'manuscript_validation.json')
        self.assertTrue(all(manuscript.sha(manuscript.OUT / name) == digest for name, digest in validation['output_hashes'].items()))
        self.assertFalse(validation['full_paper_master_available'])
        self.assertEqual(validation['new_AP_or_AO_or_objective_evaluations'], 0)
        if validation['compile_status'] == 'NOT_VERIFIED':
            self.assertFalse((manuscript.OUT / 'manuscript.pdf').exists())
            self.assertFalse((manuscript.OUT / 'overleaf_main.pdf').exists())


if __name__ == '__main__':
    unittest.main()
