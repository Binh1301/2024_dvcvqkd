# Energy-constrained UAV trajectory optimization for HAP CV-QKD

Paper-configuration audit: [source provenance](docs/parameter_provenance.md)
and [Vietnamese audit](docs/paper_configuration_audit_vi.md). The source-audited
rotor set is the requested 2018 preprint variant; real experiments remain blocked
by missing scientific inputs. The original 34-test development receipt is
historical; that configuration audit recorded 42 tests including eight source-config checks.
The [IEEE figure exporter](docs/paper_figures.md) adds 17 focused checks (59 total).
Its current output is one READY rotor-model illustration and nine BLOCKED figure
manifests; it does not fabricate paper-mode results.

Implements exactly four methods: Stationary UAV, SKR-Greedy, Energy-Aware Greedy,
and energy-constrained multi-label Pareto DP. Both variable-duration objectives
are evaluated: P1 estimated key bits/second and P2 estimated total key bits.

**The bundled experiment is SYNTHETIC DEMONSTRATION — NOT PAPER RESULTS.**
No physical parameters or SKRs are inferred from manuscript figures. The finite
key formula is an accumulated-block performance approximation, not a demonstrated
composable-security bound. Existing research production code and frozen specs
are not modified. See [model audit](docs/model_audit.md).

## Installation and execution

Python 3.11 or later. From this directory:

```powershell
python -m pip install -r requirements.txt
python -m pip install -e .
python -m pytest -q
python -m uav_qkd.run --config configs/demo.yaml --output results/my_demo
python -m uav_qkd.verify --output results/my_demo
```

Without installing the package, PowerShell can set `$env:PYTHONPATH='src'` before
the module commands. Dependencies were already available during implementation.
Output folders must be empty; use a new folder for a fresh reproducible run.
The demo runs all four methods and selects best prefixes separately for P1/P2.
`--skip-figures` and `--skip-sensitivities` are available for focused checks.

```powershell
python -m uav_qkd.run --config configs/paper.yaml --output results/research_run
```

The paper template intentionally fails with a list of missing scientific inputs.
Populate it only after the physical parameters, SKR/cloud data, provenance and
research-use authorization are provided. This setting does not certify a security
model or grant publication lifecycle authorization in the parent project.

## Mathematical conventions

- Power is the exact rotary-wing expression in Eq. (6), with the induced term
  rationalized to avoid subtractive cancellation. Units: W, J, m, s.
- Minimum energy uses duration times the numerical lower convex hull of P(v).
  The queried mean speeds are included in the sampled hull. Graph edge costs are
  compared on successively doubled nested speed grids, and a failed configured
  absolute-J convergence tolerance stops graph construction. Zero displacement
  costs P(0) times duration; infeasible displacement returns infinity.
- Acceleration, turning and transients are ignored. Speed mixing is along a
  straight segment. Signal reward uses each slot's destination and end time;
  it does not integrate channel variation along motion inside that slot.
- Gaussian centers move continuously, e.g. x(t)=x(0)-5t. No 40 m array jumps.
  The 50x50 cloud-display grid and waypoint graph have independent resolutions.
- `layer` blockage intersects the HAP-to-UAV 3D segment with a configured slab
  and samples CLWC on the horizontal intersection segment, including endpoints.
  `projected_path_2d` is an explicitly labeled approximation for the full horizontal
  HAP-to-UAV segment. There is no silent UAV-endpoint test. Spatial sampling may
  miss narrow above-threshold intervals; repeat with smaller spacing, and do not
  call agreement a mathematical continuous-intersection certificate.
- For u valid slots and a=sum(z*r), terminal key is
  `max(0, m0*a - 7*sqrt(m0*u*log2(2/epsilon)))`; the penalty is applied once.
  Zero valid signals gives zero key. Non-blocking never implies transmittance 1.
- Stationary accounts for hover energy; greedy methods enforce the same edge and
  budget constraints. Immediate ties use minimum energy, then waypoint index.
  Terminal ties prefer shorter duration, lower energy and lexicographic path.

A baseline can be infeasible even when movement is feasible (for example, hover
cost exceeds remaining energy). Experiments report that method as INFEASIBLE
and retain other methods' results. Invalid inputs remain errors, not infeasibility.

## Exact and approximate scope

Set `dp.mode: exact` for uncapped nondominated labels. Dominance compares only
identical (k,j,u) with energy <= and reward >=. Strict binary64 comparisons are
used: no epsilon dominance, reward binning or energy rounding. Identical labels
keep the first deterministically generated predecessor. Backtracking uses object
references so pruning does not invalidate predecessor chains.

`dp.mode: approximate` requires `dp.label_cap`; per-state beam retention ranks
accumulated asymptotic contribution descending then energy ascending. Discarded
labels are counted, and every result is labeled approximate. Approximate runs
never automatically launch an uncapped exact run, including pruning sweeps.
To measure gaps, run a separate feasible small exact-mode configuration; the
demo does so automatically because its main mode is exact. The exact DP test
suite independently enumerates every trajectory and stopping time on tiny graphs.

The positive minimum edge cost gives floor(Emax/c_min). The actual search stops
at its intersection with the configured prediction horizon. Thus exact-on-graph
means the supplied candidate graph, sampled energy costs, availability sequence
and finite horizon within binary64 numerical precision. It is not continuous
trajectory global optimality, true energy-envelope certification, or secure key
certification. The demo uses a deliberately restricted 9-waypoint graph inside
the full 2 km square. Full-area fine lattices can be expensive, and exact Pareto
fronts can grow exponentially; no cap is silently applied in exact mode.

## Fairness and lambda selection

The DP uses the full predicted cloud sequence. Greedy actions use current-slot
information. All methods retrospectively select their best feasible stopping
prefix, so even a greedy result is not a causal online stopping guarantee.
Runtime includes this terminal evaluation and instrumentation, not common
graph/cloud/lookup precomputation. RSS is sampled at 10 ms and is not an exact
continuous peak; tracemalloc measures per-call Python allocation peak, excluding
some native-library allocations. Both measurements are saved separately.

In demo mode, the configured lambda sweep is evaluated on a different synthetic
cloud-center realization with `calibration_seed`; choose maximum calibration P2,
breaking ties by smaller lambda. The resulting lambda is held fixed in every
evaluation/sensitivity. Real mode uses a prior lambda and requires its provenance;
it never tunes using the evaluation realization. Equal DP/greedy outcomes are
reported as equal, not altered to manufacture an algorithmic gain.

## Outputs and configuration

`results.json` contains all eight method/objective results, full trajectories,
cumulative series, graph diagnostics and memory/runtime measurements.
`summary.csv`, `trajectories.csv`, `lambda_calibration.csv`,
`approximation_gaps.csv`, `sensitivities.csv`, `scenario.npz` and `skr_input.csv`
retain computed data and synthetic/research labels. `output_manifest.json`
seals generated outputs. `verify` checks those hashes and replays all selected
path metrics from the configured physical/input models.

`figures/` contains 16 PNG/PDF pairs: CLWC time maps, blockage maps, three
trajectory comparisons, energy, asymptotic key, valid signals, finite penalty,
total key, average SKR, runtime/memory and four sensitivity figures. All synthetic
figures include their status. Scientific results require independently verified
inputs; styling does not make the demo a publication result.

All simulation numbers are explicit in YAML. Supported graph kinds are `points`,
`lattice`, and `restricted_lattice`; q0 is included. `terminal_m` can restrict the
terminal to a graph waypoint. `max_horizon` is a prediction bound, not a fixed K.
See [data format contracts](data/README.md), [plan](docs/implementation_plan.md),
and the saved validation report for the current test evidence and limitations.

## IEEE 2019 rotor reference and new Figure 02

Separate profiles now live in `configs/rotor/ieee_2019.yaml` and
`configs/rotor/arxiv_2018_v1.yaml`. The existing paper/demo defaults remain
unchanged. The IEEE profile derives P0, Pi and v0 from raw journal parameters;
the legacy profile retains its original table-v0 convention.

```powershell
python -m uav_qkd.rotor_power_figure --profile configs/rotor/ieee_2019.yaml --output figures/ieee_2019_reproduction --column single
```

Use a new empty output path. This exports vector PDF, 600dpi PNG, computed
components CSV, caption and source/profile-bound metadata. The new rotor
Figure02 is separate from the earlier blocked cloud-map Figure02. No mission
or QKD result is produced. The current full suite has 70 tests, including11 new
reference-aircraft cases; see the [Vietnamese report](docs/ieee_2019_rotor_report_vi.md)
for source locations, exact derived values, ME/MR speeds and remaining limitations.
