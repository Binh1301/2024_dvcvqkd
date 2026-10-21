"""Small checks for immutable stage evidence and resume identity."""
import importlib
import json
from pathlib import Path
import tempfile
import unittest
import sys
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))


class RunnerEvidenceTests(unittest.TestCase):
    def runner(self):
        try:
            return importlib.import_module('scripts.run_manuscript_mobility')
        except ModuleNotFoundError:
            self.fail('Approved runner is not implemented yet')

    def test_resume_rejects_changed_inputs_without_overwriting(self):
        r=self.runner()
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)
            r.bind_inputs(out,{'physical_model':'same','source_hash':'one'})
            original=(out/'input_manifest.json').read_bytes()
            r.bind_inputs(out,{'physical_model':'same','source_hash':'one'})
            with self.assertRaises(ValueError):
                r.bind_inputs(out,{'physical_model':'same','source_hash':'two'})
            self.assertEqual(original,(out/'input_manifest.json').read_bytes())

    def test_completed_stage_detects_changed_artifact(self):
        r=self.runner()
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder);(out/'validation').mkdir()
            (out/'table.csv').write_text('raw_K\n-0.25\n',encoding='utf-8')
            r.stage_receipt(out,'test','identity',{'rows':1},['table.csv'])
            self.assertEqual(r.require_stage(out,'test','identity')['status'],'CURRENTLY_VERIFIED_PASS')
            with self.assertRaises(FileExistsError):
                r.stage_receipt(out,'test','identity',{},['table.csv'])
            (out/'table.csv').write_text('raw_K\n0\n',encoding='utf-8')
            with self.assertRaises(ValueError):r.require_stage(out,'test','identity')

    def test_json_and_csv_reject_nonfinite_but_preserve_negative_raw(self):
        r=self.runner()
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)
            r.write_csv(out/'raw.csv',[{'raw_K':-.25,'percentage':None}])
            self.assertIn('-0.25',(out/'raw.csv').read_text())
            with self.assertRaises(ValueError):r.save_json(out/'bad.json',{'K':float('nan')})

    def test_coverage_rejects_empty_missing_and_duplicate_rows(self):
        r=self.runner()
        expected={(0,'A'),(1,'A')}
        good=[{'id':0,'strategy':'A'},{'id':1,'strategy':'A'}]
        r.require_key_coverage(good,('id','strategy'),expected,'fixture')
        for bad in ([],good[:1],good+[good[0]],[good[0],good[0]]):
            with self.subTest(rows=bad),self.assertRaises(ValueError):
                r.require_key_coverage(bad,('id','strategy'),expected,'fixture')

    def test_producer_snapshot_uses_loaded_bytes(self):
        r=self.runner()
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder);(out/'table.csv').write_text('K\n1\n')
            # A changed on-disk producer must not replace the code actually loaded.
            with patch.object(r,'__file__',str(out/'different.py')):
                receipt=r.stage_receipt(out,'fixture','identity',{},['table.csv'])
            snapshot=out/'validation/producers'/(receipt['producer_sha256']+'.py')
            self.assertEqual(snapshot.read_bytes(),r.PRODUCER_BYTES)


if __name__=='__main__':unittest.main()
