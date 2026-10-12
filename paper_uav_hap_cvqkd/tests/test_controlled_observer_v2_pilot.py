import json
from pathlib import Path
import tempfile
import unittest
from scripts import run_controlled_observer_v2_probe_A as pilot


class ControlledPilot(unittest.TestCase):
    def test_exact_one_pair_and_new_entry(self):
        self.assertEqual(pilot.PAIR,(.165,5.49375))
        self.assertEqual(pilot.PAIR[1].hex(),'0x1.5f9999999999ap+2')
        self.assertEqual(Path(pilot.entry.__file__).name,'observer_v2_recovery_entry.py')
        self.assertNotIn('run_theta10_D55_overnight_ao',Path(pilot.__file__).read_text())

    def test_monitor_failure_and_heartbeat_loss(self):
        clock=[0.]
        with tempfile.TemporaryDirectory() as directory:
            prefix=Path(directory)/'source';health=pilot.ObserverHealth(prefix,lambda:clock[0],grace=30)
            health.check();clock[0]=31
            with self.assertRaisesRegex(RuntimeError,'HEARTBEAT_LOST'):health.check()
            Path(str(prefix)+'_worker_result.json').write_text(json.dumps({'status':'INSTRUMENTATION_FAILURE'}))
            with self.assertRaisesRegex(RuntimeError,'OBSERVER_INSTRUMENTATION'):health.check()

    def test_progress_and_finish_no_spurious_timeout(self):
        clock=[0.]
        with tempfile.TemporaryDirectory() as directory:
            prefix=Path(directory)/'source';health=pilot.ObserverHealth(prefix,lambda:clock[0],grace=30)
            path=Path(str(prefix)+'_stage_snapshot.json')
            path.write_text(json.dumps({'snapshot_count':1,'finished':False,'observer_error':None}))
            clock[0]=20;health.check();clock[0]=49;health.check()
            path.write_text(json.dumps({'snapshot_count':2,'finished':True,'observer_error':None}))
            clock[0]=120;health.check()


if __name__=='__main__':unittest.main()
