# Batch3 exact MB refinement

Status: STOPPED_FAILED_SAFETY_PROVENANCE_OR_BUDGET

Original scientific implementation,1050/1250/1450 policy,GH8/direct-Zminus and ALT_OPT unchanged. No interpolation.
Numerical ranking: ORDERING_REPRODUCED_BUT_ERROR_UNBOUNDED; no total objective error bound or continuous/global claim.

## Probe outcomes

| Probe | nu_raw | VA | C | w | Status | Wall seconds | Job CPU seconds |
|---|---|---|---|---|---|---|---|
| 1 | 0.165 | 5.4625 | NOT_AVAILABLE | NOT_AVAILABLE | PROCESS_FAILURE | 1952.7190000000119 | 1926.453125 |

Successful=0; timeout=0.
Wall=7969.641421s/10800s; measured Job+controller CPU=1937.3125s.
Wall compliance=True; error=AssertionError(('Dummy deadline did not terminate', {'returncode': 3221225540, 'deadline_exceeded': False, 'elapsed_seconds': 2.5310000000026776, 'supervision': 'ABSOLUTE_DEADLINE_AND_WINDOWS_JOB', 'user_cpu_seconds': 4.546875, 'kernel_cpu_seconds': 0.109375, 'aggregate_cpu_seconds': 4.65625, 'accounted_processes': 5, 'cpu_measurement': 'WINDOWS_JOB_BASIC_ACCOUNTING', 'sleep_prevention': {'active_verified': True, 'released_verified': True, 'power_before': {'ac': 1, 'battery_flag': 8, 'battery_percent': 49, 'system_status': 0, 'life_seconds': 4294967295, 'full_life_seconds': 4294967295}, 'requested_flags': 2147483649, 'previous_state': 2147483649, 'owner_thread': 26504, 'restored_state': 2147483649}, 'power_watch': {'abort_reason': None, 'poll_gaps': [], 'last_power': {'ac': 1, 'battery_flag': 8, 'battery_percent': 49, 'system_status': 0, 'life_seconds': 4294967295, 'full_life_seconds': 4294967295}}, 'approved_wall_limit_seconds': 4.0, 'operational_shutdown_margin_seconds': 1.0, 'measured_wall_seconds_including_cleanup': 2.5310000000026776, 'wall_limit_respected': True, 'no_watchdog_thread_remaining': True, 'dummy_log': 'CHILD_PID=23252\n'})).
Total includes execution and between-probe processing; preparation/tests before session are excluded.
Sleep prevention active across campaign, restored in finally; no permanent power-plan change.
See individual supervision receipts for real deadlines, power watches and worker cleanup.


Protected files unchanged=908.
Earlier selection snapshots and all previous numerical artifacts preserved.
Frozen-spec discrepancy/NOT_READY_FOR_PUBLICATION_SCALE_RUNS remain; no training/test/baseline/threshold approval.
