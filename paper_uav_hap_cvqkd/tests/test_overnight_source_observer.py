import json
from pathlib import Path
import pstats
import tempfile
import time
import unittest
from scripts.overnight_source_observer import OwnerProfiler,StageObserver


class Observability(unittest.TestCase):
    def test_owner_snapshots_continue_and_are_cumulative(self):
        def late_work():return sum(range(1000))
        with tempfile.TemporaryDirectory() as directory:
            prefix=Path(directory)/'profile'
            with OwnerProfiler(prefix) as profile:
                sum(range(1000));profile.snapshot();late_work();profile.snapshot();late_work()
            self.assertEqual(next(v[1] for k,v in pstats.Stats(str(prefix)+'.prof').stats.items() if k[2]=='late_work'),2)
            snapshots=json.loads(Path(str(prefix)+'_snapshots.json').read_text())
            self.assertEqual(len(snapshots),3)
            self.assertTrue(snapshots[-1]['final'])
            self.assertTrue(all(b['wall_seconds']>=a['wall_seconds'] for a,b in zip(snapshots,snapshots[1:])))
            self.assertAlmostEqual(sum(r['delta_profile_self_seconds'] for r in snapshots),snapshots[-1]['cumulative_profile_self_seconds'])

    def test_lightweight_heartbeat_and_nested_accounting(self):
        with tempfile.TemporaryDirectory() as directory:
            prefix=Path(directory)/'stages'
            with StageObserver(prefix,interval=.01) as observer:
                with observer.stage('outer'):
                    with observer.stage('inner'):time.sleep(.06)
            data=json.loads(Path(str(prefix)+'_stage_snapshot.json').read_text())
            self.assertGreaterEqual(data['snapshot_count'],3)
            self.assertTrue(data['finished']);self.assertEqual(data['open_stages'],[])
            self.assertTrue(all(r['completed_normally'] for r in data['completed_stages']))
            inner,outer=data['completed_stages']
            self.assertAlmostEqual(inner['wall_seconds_inclusive']+outer['wall_seconds_exclusive'],outer['wall_seconds_inclusive'])
            self.assertFalse(observer.thread.is_alive())

    def test_exception_preserved_no_numeric_reexecution(self):
        calls=[]
        def fail(value):calls.append(value);raise ValueError('dummy failure')
        with tempfile.TemporaryDirectory() as directory:
            prefix=Path(directory)/'failure'
            with self.assertRaisesRegex(ValueError,'dummy failure'):
                with StageObserver(prefix) as observer:observer.wrap(fail,'failure')(5)
            self.assertEqual(calls,[5])
            data=json.loads(Path(str(prefix)+'_stage_snapshot.json').read_text())
            self.assertFalse(data['completed_stages'][0]['completed_normally'])
            self.assertFalse(observer.thread.is_alive())


if __name__=='__main__':unittest.main()
