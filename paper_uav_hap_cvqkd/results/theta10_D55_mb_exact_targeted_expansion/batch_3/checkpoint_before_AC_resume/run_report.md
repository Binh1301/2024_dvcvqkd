# Batch3 exact MB refinement

Status: STOPPED_FAILED_SAFETY_PROVENANCE_OR_BUDGET

Original scientific implementation,1050/1250/1450 policy,GH8/direct-Zminus and ALT_OPT unchanged. No interpolation.
Numerical ranking: ORDERING_REPRODUCED_BUT_ERROR_UNBOUNDED; no total objective error bound or continuous/global claim.

## Probe outcomes

| Probe | nu_raw | VA | C | w | Status | Wall seconds | Job CPU seconds |
|---|---|---|---|---|---|---|---|
| 1 | 0.165 | 5.4625 | NOT_AVAILABLE | NOT_AVAILABLE | PROCESS_FAILURE | 1952.7190000000119 | 1926.453125 |

Successful=0; timeout=0.
Wall=2162.932808999991s/10800s; measured Job+controller CPU=1937.28125s.
Wall compliance=True; error=RuntimeError('Unsafe power/deadline or cleanup').
Total includes execution and between-probe processing; preparation/tests before session are excluded.
Sleep prevention active across campaign, restored in finally; no permanent power-plan change.
See individual supervision receipts for real deadlines, power watches and worker cleanup.


Protected files unchanged=885.
Earlier selection snapshots and all previous numerical artifacts preserved.
Frozen-spec discrepancy/NOT_READY_FOR_PUBLICATION_SCALE_RUNS remain; no training/test/baseline/threshold approval.
