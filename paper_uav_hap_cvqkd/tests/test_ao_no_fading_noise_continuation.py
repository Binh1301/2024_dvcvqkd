"""Transport/checkpoint tests; no arbitrary-precision source calculation."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock,patch

from scripts import continue_ao_effective_channel_no_fading_noise as c


class ContinuationTests(unittest.TestCase):
    def test_extended_timeout_preserves_exact_request(self):
        original=Mock(return_value="completed")
        request=json.dumps(dict(probabilities_float64_hex=["0x1.0p-8"],
              precision_ladder_decimal_digits=[1050,1250,1450]))
        c.extended_ap_run(original,["python",str(c.ROOT/"scripts/full_support_c4_worker.py")],(),
            dict(input=request,capture_output=True,text=True,timeout=3600),Path("journal"),7200)
        command=original.call_args.args[0];kw=original.call_args.kwargs
        self.assertIn("--ap-worker",command)
        self.assertEqual(kw["timeout"],7200)
        self.assertEqual(kw["input"],request)

    def test_unrelated_subprocess_not_modified(self):
        original=Mock()
        c.extended_ap_run(original,["python","unrelated.py"],(),dict(timeout=123),Path("journal"),7200)
        self.assertEqual(original.call_args.args[0],["python","unrelated.py"])
        self.assertEqual(original.call_args.kwargs["timeout"],123)

    def test_completed_precision_checkpoint_reused_and_corruption_rejected(self):
        request=dict(precision_ladder_decimal_digits=[1050,1250,1450],input_hex="fixture")
        row=dict(digits=1050,rank=256,resolved=True,C="3.0",w="0.000001",minimum_eigenvalue="1e-200")
        original=Mock(return_value=row)
        with tempfile.TemporaryDirectory() as folder:
            journal=Path(folder)
            first=c.checkpointed_precision_row(original,[],[],1050,request,journal)
            second=c.checkpointed_precision_row(original,[],[],1050,request,journal)
            self.assertEqual(first,second);self.assertEqual(original.call_count,1)
            payload=c.d.read_json(journal/"1050.json");payload["row"]["C"]="4.0"
            c.save(journal/"1050.json",payload)
            with self.assertRaises(ValueError):
                c.checkpointed_precision_row(original,[],[],1050,request,journal)

    def test_different_exact_input_rejects_partial_checkpoint(self):
        row=dict(digits=1250,rank=256,resolved=True,C="3.0",w="0.0",minimum_eigenvalue="1e-200")
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)
            c.checkpointed_precision_row(Mock(return_value=row),[],[],1250,dict(hex="input1"),path)
            with self.assertRaises(ValueError):
                c.checkpointed_precision_row(Mock(),[],[],1250,dict(hex="input2"),path)

    def test_nonfinite_gate_metadata_encoded_without_changing_moments(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/"row.json"
            c.save(p,dict(C=3.,w=1e-6,gate_condition=float("inf")))
            value=c.d.read_json(p)
            self.assertEqual(value["C"],3.)
            self.assertEqual(value["w"],1e-6)
            self.assertEqual(value["gate_condition"],dict(float_hex="inf"))

    def test_sparse_slice_uses_nearby_existing_coordinates(self):
        objective=object.__new__(c.ContinuationObjective)
        objective.points={(.17,5.),(.165,4.5),(.175,5.5),(.10,2.),(.8,8.)}
        objective.current=dict(nu_raw=.17,V_A=5.)
        self.assertEqual(objective.catalog_values("nu_raw",5.),[.165,.17,.175])
        self.assertEqual(objective.catalog_values("V_A",.17),[4.5,5.,5.5])


if __name__=="__main__":
    unittest.main()
