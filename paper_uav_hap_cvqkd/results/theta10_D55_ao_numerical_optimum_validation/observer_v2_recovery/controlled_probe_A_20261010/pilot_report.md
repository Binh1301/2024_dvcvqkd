# Controlled observer-v2 Probe A pilot

CONTROLLED_PILOT_STOPPED_INSTRUMENTATION_FAILURE

Source status=INSTRUMENTATION_FAILURE; exactly1attempt, no retries/B/P2.
Totalwall=19.687000000005355s/5400, sourceceiling=4485.880392s<=4500, finalreserve900s.
Recordedcontroller+JobCPU=8.375s; excludes interactive implementation and independent checks outside controller.

Source result: {'status': 'INSTRUMENTATION_FAILURE', 'error': 'FloatingPointError(\'full-support fallback failed closed: Traceback (most recent call last):\\n  File "C:\\\\Users\\\\HP\\\\Documents\\\\GitHub\\\\2024_dvcvqkd\\\\paper_uav_hap_cvqkd\\\\scripts\\\\observer_v2_recovery_entry.py", line 210, in <module>\\n    if __name__==\\\'__main__\\\':raise SystemExit(main())\\n                                             ^^^^^^\\n  File "C:\\\\Users\\\\HP\\\\Documents\\\\GitHub\\\\2024_dvcvqkd\\\\paper_uav_hap_cvqkd\\\\scripts\\\\observer_v2_recovery_entry.py", line 197, in main\\n    atomic_json(str(args.prefix)+\\\'_worker_result.json\\\',{\\\'status\\\':status,\\\'error\\\':error,\\\'dummy_only\\\':False})\\n  File "C:\\\\Users\\\\HP\\\\Documents\\\\GitHub\\\\2024_dvcvqkd\\\\paper_uav_hap_cvqkd\\\\scripts\\\\overnight_source_observer.py", line 18, in atomic_json\\n    temporary.write_text(json.dumps(data,indent=2)+\\\'\\\\n\\\',encoding=\\\'utf-8\\\')\\n  File "C:\\\\Users\\\\HP\\\\AppData\\\\Local\\\\Python\\\\pythoncore-3.12-64\\\\Lib\\\\pathlib.py", line 1047, in write_text\\n    with self.open(mode=\\\'w\\\', encoding=encoding, errors=errors, newline=newline) as f:\\n         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\\n  File "C:\\\\Users\\\\HP\\\\AppData\\\\Local\\\\Python\\\\pythoncore-3.12-64\\\\Lib\\\\pathlib.py", line 1013, in open\\n    return io.open(self, mode, buffering, encoding, errors, newline)\\n           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\\nFileNotFoundError: [Errno 2] No such file or directory: \\\'C:\\\\\\\\Users\\\\\\\\HP\\\\\\\\Documents\\\\\\\\GitHub\\\\\\\\2024_dvcvqkd\\\\\\\\paper_uav_hap_cvqkd\\\\\\\\results\\\\\\\\theta10_D55_ao_numerical_optimum_validation\\\\\\\\observer_v2_recovery\\\\\\\\controlled_probe_A_20261010\\\\\\\\probe_results\\\\\\\\db17b04f09fb7555f681236d204ce658a95c1f413a3ab1b48cc2fefae322ae59_worker_result.json.tmp\\\'\\n\')', 'worker_result': None, 'ended_utc': '2026-10-10T01:02:52.504588+00:00', 'parent_wall_seconds': 0.23399999999674037, 'parent_process_CPU_seconds': 0.015625}

No completed new26distance/AO result; previous147catalog maxima remain baseline, not fresh convergence evidence.

Profiling={'coverage': 'NO_AP_OBSERVATIONS', 'bottleneck': 'BOTTLENECK_NOT_LOCALIZED'}
Cleanup no worker=True; Sleep restored=True; deadline respected=True.
Source refinement coverage and objective error/boundaries remain distinct. No numerical/global optimum claimed; unchanged inner4/outer6/epsilon1e-8/param1e-6.
If successfulA is the only new point, a bracket side may narrow but old pairedP1 stage still lacks partner unless actual search says otherwise. No nextsource launched.
Ponytail: original source/provenance/evaluator/AO/Job/Sleep reused; observer-v2 only, never overnight-v1 controller.
Error=None. Allpreviousscientificartifacts preserved.
