import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_runner():
    sys.path.insert(0, str(ROOT / "scripts"))
    script = ROOT / "scripts" / "run_baselines_cached_source_moments.py"
    spec = importlib.util.spec_from_file_location("cached_baselines_workflow", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BaselineDevelopmentWorkflowTests(unittest.TestCase):
    def test_default_phase_is_derived_and_not_free(self):
        runner = load_runner()
        config = runner.load_yaml(ROOT / "configs" / "default.yaml")
        record = runner._phase_provenance(config)
        self.assertEqual(record["parameterization"], "rytov_equivalent_hufnagel_valley")
        self.assertNotIn("cn_phi2_m_minus_two_thirds", config["channel"])

    def test_preflight_covers_same_three_schemes_at_all_va_points(self):
        runner = load_runner()
        config = runner.load_yaml(ROOT / "configs" / "default.yaml")
        rows, ensembles = runner.build_support_preflight(config)
        self.assertEqual(len(rows), 45)
        self.assertEqual(len(ensembles), 45)
        for va in config["baseline_search"]["va_grid_snu"]:
            self.assertEqual(
                {row["scheme"] for row in rows if row["target_VA"] == va},
                {"uniform", "binomial", "mb"},
            )

    def test_fixed_mb_is_not_optimized(self):
        runner = load_runner()
        config = runner.load_yaml(ROOT / "configs" / "default.yaml")
        self.assertEqual(config["cvqkd"]["mb_nu"], 0.1)
        self.assertEqual(runner.SCHEMES, ("uniform", "binomial", "mb"))


if __name__ == "__main__":
    unittest.main()
