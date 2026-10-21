# Reproduce the Uniform manuscript-style numerical comparison

Run commands from `paper_uav_hap_cvqkd/` with `.venv/Scripts/python.exe`.
Package versions are recorded in `environment.json`.

Validate the completed saved result without rerunning numerical calculations:

```powershell
& .venv/Scripts/python.exe -X utf8 -B results/uniform_manuscript_2d_optimization_20261019/verify_results.py
```

The original producer refuses to overwrite a completed `summary.json`.
For a numerical replay in a **new** result directory, use the following
Python code. It reuses authenticated exact sources, recomputes the channel
and GH16/32/64 MI/Holevo/SKR, and writes its own figures and report.
It does not update project-state documents or the original output directory.

```python
from pathlib import Path
import shutil
from scripts import optimize_uniform_manuscript_2d as run

original = run.OUT
replay = run.ROOT / "results" / "uniform_manuscript_2d_replay"
replay.mkdir(exist_ok=False)
for name in ("request.txt", "source_uniform_exact.py",
             "source_uniform_diagonal.py", "diagonal_solve_worker.py"):
    shutil.copy2(original / name, replay / name)
run.OUT = replay
run.REPORT = replay / "report_vi.md"
run.main()
```

Once the original task is complete, all its accepted exact sources are
available for replay. Cache-origin/count fields can differ because those
sources are already available, while the evaluated numerical values match.

If a genuinely new source is requested later, the isolated source worker
uses mpmath with gmpy2 `2.3.2` from the temporary path recorded in
`environment.json`. The repository's `.venv` was not modified. Recreate
that temporary dependency, if absent, with the same `pip --target` setup
before requesting a new source. Full-support precision remains
1050/1250/1450 decimal digits; no finite Fock cutoff is introduced.

`compiled_matrix_worker.py` and `compiled_trial_*` record an unused,
stopped performance experiment. They do not contribute to any candidate.
The accepted source route is the repository C4 Gram method with the
separately tested diagonal-system solve. `source_parity_control.json`
records its full-source agreement with the historical Uniform cache.
