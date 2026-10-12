import json
from pathlib import Path
import tempfile
import unittest
from scripts import observer_v2_recovery_entry as entry


class RecoveryEntry(unittest.TestCase):
    def test_original_entry_dummy_context_and_restore(self):
        with tempfile.TemporaryDirectory() as directory:
            result=entry.dummy_entry(Path(directory)/'normal',iterations=1000)
            self.assertEqual(result['status'],'SUCCESS')
            self.assertEqual(result['original_AP_source_moments_executed'],0)
            self.assertEqual(result['context_before'],result['context_after'])
            self.assertTrue(result['original_hooks_restored'])
            self.assertEqual(result['calls'],[(name,d) for d in (1050,1250,1450) for name in ('sectors','eigen','solve')])

    def test_disable_observer_same_worker_result_and_calls(self):
        with tempfile.TemporaryDirectory() as directory:
            a=entry.dummy_entry(Path(directory)/'enabled',iterations=1000)
            b=entry.dummy_entry(Path(directory)/'disabled',enabled=False,iterations=1000)
            self.assertEqual(a['worker_stdout'],b['worker_stdout']);self.assertEqual(a['calls'],b['calls'])
            self.assertFalse(Path(directory,'disabled_stage_snapshot.json').exists())

    def test_failures_are_distinct(self):
        with tempfile.TemporaryDirectory() as directory:
            a=entry.dummy_entry(Path(directory)/'instrument','instrumentation_failure',iterations=1000)
            b=entry.dummy_entry(Path(directory)/'numeric','numerical_failure',iterations=1000)
            self.assertEqual(a['status'],'INSTRUMENTATION_FAILURE');self.assertEqual(a['calls'],[])
            self.assertEqual(b['status'],'NUMERICAL_FAILURE');self.assertEqual(b['calls'],[])
            self.assertTrue(a['original_hooks_restored'] and b['original_hooks_restored'])

    def test_status_priority(self):
        for reason,status in (('AC_LOST_OR_CRITICAL_BATTERY','AC_SAFETY_ABORT'),
                             ('UNEXPECTED_SUSPEND_OR_SCHEDULER_GAP','WATCHDOG_ABORT'),
                             ('ABSOLUTE_DEADLINE','TIMEOUT')):
            self.assertEqual(entry.classify({'power_watch':{'abort_reason':reason},'returncode':125}),status)
        for status,code in (('SUCCESS',0),('INSTRUMENTATION_FAILURE',70),('NUMERICAL_FAILURE',71)):
            self.assertEqual(entry.classify({'returncode':code},{'status':status}),status)
        self.assertEqual(entry.classify({},started=False),'NOT_RUN')

    def test_production_requires_fresh_authority_and_containment(self):
        with self.assertRaises(PermissionError):entry.production_gate({},Path('dummy'),'{}',False)
        with self.assertRaises(PermissionError):entry.production_gate({},Path('dummy'),'{}',True)


if __name__=='__main__':unittest.main()
