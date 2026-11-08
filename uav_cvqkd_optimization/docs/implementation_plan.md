# Energy-constrained UAV CV-QKD implementation plan

Goal: implement exactly Stationary, SKR-Greedy, Energy-Aware Greedy and Pareto DP,
with both variable-duration objectives in the supplied implementation task.
Architecture: an independent Python package. Physics and lookup inputs are
separate from graph search, terminal evaluation, experiments and plotting.
Stack: Python >=3.11, NumPy, SciPy, Matplotlib, PyYAML, pytest, psutil.
Spec: supplied Pasted text.txt (attachment af5e45d9) and manuscript Copy (17),
especially equations (6)-(10), (15)-(33), (35)-(39).

## Decisions and limits

- Work only in this new sibling folder on existing feature branch feat/11-6.
  No production CV-QKD model edits, commits, pushes or publication evaluation.
- Native implementation, one independent review at the end. The user's explicit
  development order authorizes incremental implementation and synthetic tests.
- Real mode requires declared physical inputs, external SKR data with units,
  provenance and research-use authorization. Do not automatically import the
  diagnostic receiver30 map or promote its security/source status.
- Gaussian superposition is analytic, with continuous advection. Cloud display
  sampling (50x50) is independent of waypoints. LOS samples a configured altitude
  slab; resolution convergence is a diagnostic, not an intersection certificate.
- Lower convex hull is numerical on nested speed grids; edge means are inserted
  into the grid so feasible constant speed is an explicit candidate. Compare
  coarse/fine edge costs prospectively and fail when tolerance is not met.
- Exact DP dominance uses strict binary64 comparisons, identical duplicates keep
  first insertion; no epsilon-dominance that could delete an optimum. Energy
  feasibility uses strict <=. Report exact only for the graph and sampled-energy
  problem within the configured horizon, not continuous physical/global security.
- Missing engine, signal, epsilon, layer and energy inputs remain null in paper
  config. Demo values are arbitrary synthetic fixtures, never paper parameters.

## Tasks

1. Physics and inputs: propulsion.py, cloud_model.py, blockage.py, skr_lookup.py,
   finite_size.py; test stable power, convexity/convergence, advection, slab
   geometry, lookup formats/units/domain and accumulated penalty.
2. Graph and evaluation: waypoint_graph.py, evaluation.py, baselines.py;
   test connected/disconnected graphs, edge feasibility, tie breaks and prefixes.
3. DP: dp_solver.py; test both objectives vs independent exhaustive enumeration,
   dominance on/off, different stopping times, zero/all blockage, approximate gap.
4. Integration: config.py, experiments.py, visualization.py, run.py, YAML configs,
   README and provenance/validation artifacts. Generate synthetic PNG/PDF figures,
   tables, lambda/calibration and energy/threshold/resolution/label sweeps.

Each task: write tests; observe failure; implement; execute scoped tests. Final:
full suite, end-to-end demo, fail-closed paper run, external review, diff check.

## Review focus

Invalid/nonfinite config and queries; unavailable external inputs; geometry
sampling misses; floating point energy/dominance errors; accidental synthetic
or diagnostic promotion to paper/security results. Tests pin each input boundary.

## Progress

Tasks 1-4 complete. Final suite: 34 passed, recorded in
results/tests_20261107.xml. Final demo: results/final_demo_20261107/.
Source/input/output and trajectory replay: CURRENTLY_VERIFIED_PASS.
Independent review findings all resolved with regression tests; see
review_resolution.md. No production/frozen-model or lifecycle changes.
