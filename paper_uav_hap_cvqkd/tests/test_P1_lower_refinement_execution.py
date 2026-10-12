"""Only target/path bindings change; source API and runtime safety are reused."""
import unittest
from unittest.mock import patch
from scripts import run_theta10_D55_P1_lower_refinement as run


class LowerExecutionTests(unittest.TestCase):
    def test_no_automatic_AP(self):
        with patch.object(run.OUT.__class__,'mkdir') as mkdir:
            with self.assertRaisesRegex(SystemExit,'AP NOT_RUN'):
                run.main()
            mkdir.assert_not_called()

    def test_original_source_and_controller_binding(self):
        original_path = run.upper.__file__
        with patch.object(run.upper,'source_child',return_value=0) as source:
            self.assertEqual(run.source_child(),0)
            source.assert_called_once_with()
        with run.binding():
            self.assertEqual((run.upper.NU,run.upper.VA,run.upper.KEY),(run.NU,run.VA,run.KEY))
            self.assertEqual(run.upper.prep.merge_source,run.CONTEXT.merge_source)
            self.assertEqual(run.upper.CACHE,run.CACHE)
            self.assertEqual(run.upper.__file__,str(run.Path(run.__file__).resolve()))
            self.assertEqual((run.upper.TOTAL,run.upper.SUPERVISOR_MAX,run.upper.RESERVE),(7200.,5400.,1800.))
        self.assertEqual(run.upper.__file__,original_path)
        self.assertEqual(run.VA.hex(),'0x1.5fccccccccccdp+2')
        self.assertLessEqual(len(str(run.CACHE/(run.KEY+'.json.tmp'))),247)


if __name__ == '__main__':
    unittest.main()
