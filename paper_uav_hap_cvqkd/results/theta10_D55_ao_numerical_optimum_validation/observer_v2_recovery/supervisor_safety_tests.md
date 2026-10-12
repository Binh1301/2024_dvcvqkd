# Native supervisor dummy safety tests

READY_FOR_CONTROLLED_AP_PILOT. Full results in dummy_worker_integration_results.csv and dummy/*_supervision.json.
Same original Windows Job supervisor/Sleep/AC watchdog, not a reimplemented safety mock.
Live idle child + worker tests normal exit, observer failure, numerical failure, wall deadline,
AC status injection and synthetic watchdog clock gap>5s. No real AC disconnection or suspension.
Watchdog clock injection is thread-selective so controller clock/deadline remains real.
Native Job membership verified by IsProcessInJob; marker/PID inventory confirms complete tree
cleanup, owning-thread Sleep request acquired/restored and no watchdog thread left.

Return/status map: success0; observer70; numerical71; deadline124; unsafeAC/gap125 with explicit
recorded reason. NOT_RUN starts no process. Measurement scope Job aggregateCPU versus worker
processCPU/thread collector overhead is explicit. Forced termination leaves valid prior snapshot
with OPEN interval, never invents final callback or full-run coverage. Automatic Sleep lease does
not prevent manual suspend/shutdown; actual OS suspension can prevent watchdog scheduling and
strict deadlines. Any gap/overrun must fail closed in the future pilot. No permanent power plan change.
