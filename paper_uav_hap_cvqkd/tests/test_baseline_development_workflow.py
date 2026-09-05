import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def load_runner():
    import importlib.util
    import sys

    sys.path.insert(0, str(ROOT / "scripts"))
    script = ROOT / "scripts" / "run_baselines_cached_source_moments.py"
    spec = importlib.util.spec_from_file_location("cached_baselines_workflow", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BaselineDevelopmentWorkflowTests(unittest.TestCase):
    def test_json_config_loads_and_cli_override_is_explicit(self):
        runner = load_runner()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            config = json.loads((ROOT / "configs" / "baseline_smoke.json").read_text(encoding="utf-8"))
            path.write_text(json.dumps(config), encoding="utf-8")
            settings = runner.load_experiment_config(path, {"va": 0.5})
        self.assertEqual(settings["h_hap_m"], 20000)
        self.assertEqual(settings["va"], 0.5)
        self.assertEqual(settings["fading_samples"], 2)

    def test_missing_git_metadata_is_recorded_without_blocking(self):
        runner = load_runner()
        with patch.object(runner.subprocess, "run", side_effect=FileNotFoundError):
            metadata = runner.collect_run_metadata(Path("configs/baseline_smoke.json"), {})
        self.assertIsNone(metadata["git_commit"])
        self.assertIsNone(metadata["git_dirty"])
        self.assertEqual(metadata["config_path"], "configs/baseline_smoke.json")

    def test_dirty_git_metadata_is_recorded_without_blocking(self):
        runner = load_runner()
        completed = [runner.subprocess.CompletedProcess([], 0, stdout="abc123\n", stderr="")]
        completed.append(runner.subprocess.CompletedProcess([], 0, stdout=" M src/x.py\n", stderr=""))
        with patch.object(runner.subprocess, "run", side_effect=completed):
            metadata = runner.collect_run_metadata(Path("configs/baseline_smoke.json"), {})
        self.assertEqual(metadata["git_commit"], "abc123")
        self.assertTrue(metadata["git_dirty"])

    def test_resume_requires_matching_normalized_config(self):
        runner = load_runner()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "uniform.json"
            runner._write_json(path, {"run_config": {"va": 1.0}})
            self.assertTrue(runner.checkpoint_matches(path, {"va": 1.0}))
            self.assertFalse(runner.checkpoint_matches(path, {"va": 1.1}))


if __name__ == "__main__":
    unittest.main()
