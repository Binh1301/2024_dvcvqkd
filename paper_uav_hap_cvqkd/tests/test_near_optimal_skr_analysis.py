"""Pure arithmetic and current stored-catalog checks; never call a numerical evaluator."""
import ast
from pathlib import Path
import unittest
from scripts import analyze_theta10_D55_near_optimal_skr as analysis


class NearOptimalAnalysisTests(unittest.TestCase):
    def test_full_catalog_and_reference(self):
        entries, protected, audit, _ = analysis.load_verified()
        self.assertEqual(sum(len(e['rows']) for e in entries), 3926)
        rows = analysis.reference_rows(next(e['rows'] for e in entries if e['L_km'] == analysis.REF))
        self.assertEqual((rows[0]['nu_raw'], rows[0]['V_A'], rows[0]['SKR']), (.165, 5.5, .07798099387393764))
        self.assertEqual((rows[1]['nu_raw'], rows[1]['V_A']), (.165, 5.496875))
        self.assertEqual(rows[1]['delta_K'], 3.6726688357191506e-10)
        self.assertEqual([sum(0 <= r['delta_K'] <= t for r in rows) for t in analysis.THRESHOLDS], [9, 5, 2, 2, 1])
        self.assertEqual(len([r for r in rows if r['V_A'] == 5.5]), 20)
        close = analysis.neighbors(rows)
        self.assertEqual(len(close), 24)
        self.assertTrue(all(analysis.pair(r) != analysis.pair(rows[0]) for r in close))
        self.assertEqual({r['group']: (r['nu_raw'], r['V_A']) for r in close if r['neighbor_rank'] == 1 and 'nearest10' not in r['group']},
                         {'V_A_below': (.165, 5.496875), 'V_A_above': (.165, 5.50625),
                          'nu_raw_below': (.1625, 5.5), 'nu_raw_above': (.16562500000000002, 5.5)})
        self.assertTrue(audit)
        self.assertTrue(all(analysis.digest(analysis.ROOT / n) == sha for n, sha in protected.items()))

    def test_duplicate_pair_rejected_and_adjacent_binary64_preserved(self):
        row = dict(nu_raw=.165, V_A=5.5, SKR=1.)
        with self.assertRaises(ValueError):
            analysis.ranked([row, dict(row)])
        other = dict(row, nu_raw=float.fromhex('0x1.51eb851eb8520p-3'))
        self.assertNotEqual(analysis.pair(row), analysis.pair(other))
        self.assertEqual(len(analysis.ranked([row, other])), 2)

    def test_no_scientific_imports_or_worker_execution(self):
        tree = ast.parse(Path(analysis.__file__).read_text(encoding='utf-8'))
        modules = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
        modules += [a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names]
        self.assertEqual(set(modules), {'csv', 'hashlib', 'json', 'math', 'pathlib', 'sys', 'time', 'scripts.exact_cache_provenance'})
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                self.assertNotIn(node.func.attr, ('source_moments', 'evaluate_candidate', 'adaptive_maximize_1d', 'Popen', 'system'))

    def test_no_overwrite(self):
        from unittest.mock import patch
        with patch.object(analysis, 'OUT', analysis.INPUT), patch.object(analysis, 'load_verified') as load:
            with self.assertRaises(SystemExit):
                analysis.main()
            load.assert_not_called()


if __name__ == '__main__':
    unittest.main()
