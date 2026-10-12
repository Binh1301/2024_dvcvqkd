import ast
from pathlib import Path
import unittest
from scripts import diagnose_theta10_D55_source_bottlenecks as diagnostic


class SavedSourceDiagnostic(unittest.TestCase):
    def test_dummy_dump_reproduces_collector_gap(self):
        result=diagnostic.dummy_profile_check()
        self.assertTrue(result['before_dump_recorded'])
        self.assertFalse(result['after_dump_recorded'])
        self.assertFalse(result['real_AP_invoked'])

    def test_conditional_refinement_and_original_caps(self):
        self.assertEqual(diagnostic.halving_analysis(.0125)['conditional_halving_steps'],14)
        self.assertEqual(diagnostic.halving_analysis(.0025)['conditional_halving_steps'],12)
        self.assertEqual(diagnostic.original_settings()['MAX_REFINEMENT_STAGES'],4)
        self.assertEqual(diagnostic.original_settings()['K_TOLERANCE'],1e-8)

    def test_exact_keys_and_no_scientific_imports(self):
        self.assertEqual(diagnostic.pair(.16531250000000003,5.5)[0],'0x1.528f5c28f5c2ap-3')
        tree=ast.parse(Path(diagnostic.__file__).read_text(encoding='utf-8'))
        scientific_imports=[n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)
                            and n.module and n.module.startswith(('src.','scripts.run_'))]
        self.assertEqual(scientific_imports,[])


if __name__=='__main__':
    unittest.main()
