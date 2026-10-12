"""Bounded operational checks;no native dummy or scientific AP is launched."""
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from scripts import run_theta10_D55_full_51_grid as run


class FullGridExecutionTests(unittest.TestCase):
    def test_queue_exact_binary64_and_group_order(self):
        q=run.QUEUE_B+run.QUEUE_A
        self.assertEqual(len(q),31);self.assertEqual(len(set(q)),31)
        self.assertEqual(q[0],(.16,4.5));self.assertEqual(q[-1],(.25,8.))
        spec=run.grid.grid_specification();self.assertTrue(set(q)<={(r['nu_raw'],r['V_A']) for r in spec})
        missing=run.grid.audit.read(run.grid.OUT/'grid_verification.json')['missing_pairs']
        self.assertEqual(missing,31)
        self.assertEqual(run.INTERNAL,3600.);self.assertEqual(run.TOTAL,129600.)
        self.assertEqual(run.RESERVE,1800.);self.assertEqual(len(run.QUEUE_B),12)

    def test_deadline_reserve_and_no_internal_timeout_override(self):
        self.assertFalse(run.enough_time(0,run.SOURCE_OUTER+run.POST_OUTER+run.RESERVE-.001))
        self.assertTrue(run.enough_time(0,run.SOURCE_OUTER+run.POST_OUTER+run.RESERVE))
        self.assertEqual(run.source_child.__globals__['original'].source_child,run.original.source_child)

    def test_safety_fail_closed(self):
        r=dict(actual_job_cleanup=[dict(verified=True,handle_closed=True,active_processes_remaining=0)],
               wall_limit_respected=True,no_watchdog_thread_remaining=True,
               sleep_prevention=dict(active_verified=True,released_verified=True),
               power_watch=dict(abort_reason=None),supervision='ABSOLUTE_DEADLINE_AND_WINDOWS_JOB',
               cpu_measurement='WINDOWS_JOB_BASIC_ACCOUNTING')
        self.assertTrue(run.safety_ok(r))
        r['actual_job_cleanup'][0]['active_processes_remaining']=1;self.assertFalse(run.safety_ok(r))
        r['actual_job_cleanup'][0]['active_processes_remaining']=0
        r['power_watch']['abort_reason']='AC_LOST_OR_CRITICAL_BATTERY';self.assertFalse(run.safety_ok(r))

    def test_atomic_checkpoint_and_csv(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);run.atomic_json(p/'checkpoint.json',dict(status='PENDING',nu_raw_hex=.165.hex()))
            self.assertEqual(run.read(p/'checkpoint.json')['status'],'PENDING')
            self.assertFalse((p/'checkpoint.json.tmp').exists())
            run.atomic_csv(p/'rows.csv',[dict(status='TIMEOUT',attempt_number=1)])
            self.assertIn('TIMEOUT',(p/'rows.csv').read_text())

    def test_no_unapproved_ap_or_retry(self):
        with patch.object(run,'preflight') as preflight:
            with self.assertRaises(SystemExit):run.run()
            preflight.assert_not_called()
        self.assertTrue({'TIMEOUT','FAILED','SAFETY_ABORT','INTERRUPTED'}<=run.TERMINAL)


if __name__=='__main__':unittest.main()
