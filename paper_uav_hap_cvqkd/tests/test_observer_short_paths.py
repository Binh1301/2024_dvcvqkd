import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import run_path_fixed_probe_A as run


class ShortProductionPaths(unittest.TestCase):
    def test_real_generator_all_paths_and_long_scientific_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / 'out';out.mkdir()
            stage = Path(directory) / 's';stage.mkdir()
            with patch.object(run, 'OUT', out), patch.object(run.pilot, 'OUT', out), patch.dict(run.os.environ):
                manifest = run.prepare_paths(stage)
            mapped = manifest['prefixes'][str(run.prefix(stage, 'a').resolve())]
            self.assertGreater(len(mapped['scientific_run_identity']), 256)
            self.assertEqual(mapped['source_cache_key'], run.KEY)
            self.assertEqual(Path(manifest['production_prefix']).name, 'a')
            self.assertTrue((out / 'production_path_preflight.csv').is_file())
            self.assertFalse(list(stage.rglob('*.tmp')))
            self.assertFalse(list((out / 'exact_source_cache').iterdir()))

    def test_atomic_operations_leave_no_dummy_and_never_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / 'sub' / 'a.json'
            self.assertEqual(run.path_operations(path, (root,))['creation_flush_read_atomic_replace_rename_hash_delete'], 'PASS')
            path.write_text('original')
            with self.assertRaises(FileExistsError):
                run.path_operations(path, (root,))
            self.assertEqual(path.read_text(), 'original')

    def test_reject_unsafe_names_paths_and_length(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(ValueError):run.prefix(root, '../outside')
            with self.assertRaises(ValueError):run.path_operations(root / ('x' * 240), (root,))
            with self.assertRaises(ValueError):run.path_operations(root.parent / 'outside.json', (root,))

    def test_no_legacy_controller_and_no_scientific_reimplementation(self):
        code = Path(run.__file__).read_text()
        self.assertNotIn('run_theta10_D55_overnight_ao', code)
        self.assertIn('pilot.process_success()', code)
        self.assertIn('evaluator.source_moments(ensemble, *pilot.PAIR)', code)
        self.assertEqual(run.pilot.PAIR[1].hex(), '0x1.5f9999999999ap+2')


if __name__ == '__main__':unittest.main()
