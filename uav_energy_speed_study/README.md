# Independent UAV energy–speed study

This standalone experiment evaluates rotary-wing propulsion only. All source,
results, figures, temporary files, and Matplotlib caches stay in this directory.
It imports no HAP–UAV, channel, FSO, SKR, or CV-QKD project modules and changes no
environment, dependency, Git setting, or previous result.

## Run

With an existing Python containing NumPy, SciPy, and Matplotlib:

```powershell
python -B main.py
```

The actual execution used the already installed project environment, read-only:

```powershell
# From uav_energy_speed_study/
..\paper_uav_hap_cvqkd\.venv\Scripts\python.exe -B main.py
python -B verify_isolation.py verify
```

Python 3.12.10, NumPy 2.5.2, SciPy 1.18.1, Matplotlib 3.10.7.
`main.py` regenerates outputs within this experiment. It sets bytecode suppression,
the Matplotlib cache, and temporary-directory environment variables before importing
scientific packages. No installation or environment activation is required.
`verify_isolation.py record` created a one-time, non-overwritable baseline before
the numerical run; `verify` compares all other repository files, including ignored
files, `.git`, and the existing `.venv`, by SHA-256, size, and modification time.

## Model and parameters

The physical expression is Eq. (6) in the authors' preprint of Y. Zeng, J. Xu,
and R. Zhang, “Energy Minimization for Wireless Communication With Rotary-Wing
UAV,” *IEEE Transactions on Wireless Communications*, 18(4), 2329–2345, 2019.
[Published paper](https://doi.org/10.1109/TWC.2019.2902559),
[authors' preprint](https://arxiv.org/pdf/1804.02238).

\[
P(V)=P_0\left(1+\frac{3V^2}{U_{\rm tip}^2}\right)
+P_i\left(\sqrt{1+\frac{V^4}{4v_0^4}}-\frac{V^2}{2v_0^2}\right)^{1/2}
+\frac12d_0\rho sAV^3.
\]

| Parameter | Fixed value |
|---|---:|
| \(P_0\) | 79.85628 W |
| \(P_i\) | 88.62794 W |
| \(U_{\rm tip}\) | 120 m/s |
| \(v_0\) | 4.02854 m/s |
| \(d_0\) | 0.6 |
| \(\rho\) | 1.225 kg/m³ |
| \(s\) | 0.05 |
| \(A\) | 0.503 m² |
| \(V_{\max}\) | 30 m/s |

These are the user's prescribed parameters, not a claim that they reproduce the
paper's entire numerical setup. The supplied approximate value of \(v_0\) is used
as exactly 4.02854 for reproducibility; no additional digits are invented. The
power evaluator uses the original nested-square-root expression and physical
parameters, not a fitted curve or rounded polynomial coefficients.

Assumptions: horizontal flight at constant altitude, no wind, nonnegative forward
speed, instantaneous switching, and no acceleration/deceleration energy. Hovering
consumes \(P(0)=168.48422\) W. No aerodynamic, flight-controller, battery,
communication-power, or quantum-channel simulation is included.

## Computed results

| Quantity | Numerical result |
|---|---:|
| Maximum-endurance speed \(V_{\rm me}\) | 10.2116900078601 m/s |
| Minimum instantaneous propulsion power | 125.990759652381 W |
| Maximum-range speed \(V_{\rm mr}\) | 18.2944789470261 m/s |
| Power at \(V_{\rm mr}\) | 161.509932408258 W |
| Minimum energy per unit distance | 8.82834285009861 J/m |
| Minimum constant-speed energy over 1000 m | 8828.34285009861 J |
| Duration over 1000 m at \(V_{\rm mr}\) | 54.6612998870107 s |
| Energy over 1000 m at \(V_{\rm me}\) | 12337.8950551186 J |
| Duration over 1000 m at \(V_{\rm me}\) | 97.9269836070505 s |
| Constant-speed energy, 1000 m in 100 s | 12601.6917553118 J |
| Globally optimal energy, 1000 m in 100 s | 12601.6917553118 J |
| Savings in the 1000 m / 100 s scenario | 0 J (0%) |
| Hover/cruise transition speed \(V_*\) | 6.30168764529971 m/s |
| Universal energy lower bound for 100 s | 12599.0759652381 J |

For 1000 m in 100 s, the optimal profile is \(V(t)=10\) m/s throughout.
The stored two-level representation is \(V_1=V_2=10\) m/s and \(\alpha=0.5\).
The fraction is nonunique when both speeds coincide; it does not imply a physical
speed change at 50 s. Figures 5 and 6 explicitly show the two coincident solutions.

For fixed distance and free duration, \(E=DP(V)/V\), so the optimum is
\(V_{\rm mr}\), not \(V_{\rm me}\). For fixed distance **and** duration, the mean
speed is constrained and a different optimization problem applies.

## Fixed-time sensitivity

The duration is 100 s in every row. Distance is fixed **within** a scenario and
changes **between** scenarios as \(D=100\overline V\).
Energy differences are \(E_{\rm const}-E_{\rm opt}\), so positive values denote savings.

| Mean speed (m/s) | Distance (m) | Constant energy (J) | Optimal energy (J) | \(V_1,V_2\) (m/s) | \(\alpha\) | Savings (J) | Savings (%) | Hover (s) |
|---:|---:|---:|---:|---|---:|---:|---:|---:|
| 2 | 200 | 16334.142328 | 15809.875188 | 0, 6.301688 | 0.682624701100 | 524.267140 | 3.209640 | 68.262470 |
| 5 | 500 | 14359.456175 | 14252.054971 | 0, 6.301688 | 0.206561752751 | 107.401204 | 0.747948 | 20.656175 |
| 10 | 1000 | 12601.691755 | 12601.691755 | 10, 10 | 0.5 | 0 | 0 | 0 |
| 15 | 1500 | 13853.478736 | 13853.478736 | 15, 15 | 0.5 | 0 | 0 | 0 |
| 20 | 2000 | 17828.937861 | 17828.937861 | 20, 20 | 0.5 | 0 | 0 | 0 |
| 25 | 2500 | 24894.708767 | 24894.708767 | 25, 25 | 0.5 | 0 | 0 | 0 |
| 30 | 3000 | 35627.964702 | 35627.964702 | 30, 30 | 0.5 | 0 | 0 | 0 |

## Why the solution is globally optimal

Let \(H=P(0)\), \(x=V^2/(2v_0^2)\), \(r=\sqrt{1+x^2}\), and
\(q=\exp[-\operatorname{asinh}(x)/2]\). This last expression is algebraically
identical to the induced-power factor in the original model; it is used only for
stable analytic derivatives, independently checked against finite differences of
the original power evaluator. Its second derivative is

\[
q''(V)=\frac{q}{2v_0^2r^3}(xr+x^2-1).
\]

For \(V\ge V_c=v_0\sqrt{2/\sqrt3}\), \(q''\ge0\), hence \(P''>0\).
Below \(V_c\), the sign needed to show \(q'''\ge0\) follows from

\[
q'''(V)=\frac{3qV}{4v_0^4r^5}
\left[(1-x^2)r+3x-x^3\right]\ge0,
\qquad 0\le x\le1/\sqrt3.
\]

The positive cubic drag term makes \(P''\) strictly increasing on that interval.
Since \(P''(0)<0\) and \(P''(V_c)>0\), there is exactly one inflection point,
numerically 4.06297847589801 m/s. Consequently, \(P'\) first decreases from zero,
then strictly increases. Its positive value at 30 m/s establishes a unique
interior minimum at \(V_{\rm me}\), below both endpoint powers.

For range, define \(g(V)=VP'(V)-P(V)\). Then \(g'=VP''\): it first decreases
from \(-H\), then strictly increases to a positive value at 30 m/s. Thus it has
one root, \(V_{\rm mr}\), giving the global minimum of \(P(V)/V\).
The zero-speed limit of that ratio is positive infinity. The tangent from the
origin has slope \(P(V_{\rm mr})/V_{\rm mr}=P'(V_{\rm mr})\).

For the convex envelope, solve the **different** tangency equation

\[
V_*P'(V_*)-P(V_*)+H=0,
\qquad V_*=6.30168764529971\ \mathrm{m/s}.
\]

The same derivative argument shows that \([P(V)-H]/V\) has a unique global
minimum at \(V_*\). Therefore the line from \((0,H)\) to
\((V_*,P(V_*))\) lies below the entire power curve. It joins the convex part of
the curve with matching derivative. The lower convex envelope is exactly

\[
P_{\rm ce}(v)=
\begin{cases}
H+\dfrac{v}{V_*}[P(V_*)-H],&0\le v\le V_*,\\
P(v),&V_*\le v\le30.
\end{cases}
\]

It is the largest convex minorant: between the two contact points any convex
minorant is bounded above by their chord, while elsewhere it is bounded above
by \(P\) itself. For any feasible measurable speed profile,

\[
\frac1T\int_0^T P(V(t))\,dt
\ge\frac1T\int_0^T P_{\rm ce}(V(t))\,dt
\ge P_{\rm ce}(D/T).
\]

Jensen's inequality is applied here to the proven convex **envelope**, not to
the nonconvex original power function. The bound is attainable:

- For \(0<\overline V<V_*\): hover at 0 m/s for fraction
  \(\alpha=1-\overline V/V_*\), and fly at \(V_*\) for the remaining fraction.
  Hovering energy is fully counted. Reversing the order gives the same energy.
- For \(V_*\le\overline V\le30\): constant speed is globally optimal.
- At \(\overline V=0\): hover throughout; there is no strict improvement.

This proves global optimality for arbitrary switching under this simplified
model, beyond the two-level search. The grid results independently reproduce it.
The universal bound \(TP(V_{\rm me})\) is lower than or equal to the constrained
minimum and is attained only when the prescribed average speed equals
\(V_{\rm me}\). In particular it is not attainable for exactly 1000 m in 100 s.

## Numerical checks and convergence

The run performs 65 explicit checks, raising an error on failure. Evidence and
tolerances are saved in `results/validation.json`; convergence values are saved
in `results/convergence.csv`. The checks cover hover power, extrema and endpoints,
derivatives, tangencies, speed bounds, distance, duration, explicit constant-speed
candidates, \(\alpha=0,1\), comparison against the envelope, the universal bound,
and 5000 independently sampled eight-level profiles (seed 20261028).

Two-speed search uses feasible \((\alpha,V_1)\) grids of 121, 241, 481, and 961
points on each axis, with \(V_2\) determined by the exact mean constraint.
Infeasible cells are excluded. Endpoints \(\alpha=0,1\) are handled separately.
Constant-speed candidates are always included. The final grid candidate is
refined with bounded SLSQP searches, a bounded hover/cruise scalar search, and
local derivative root refinement where applicable. Degenerate equal-energy
solutions use the canonical constant-speed representation.

A monotone-chain lower hull is constructed independently on speed grids of
301, 601, 1201, 2401, and 4801 points. A final 30001-point hull is used for
the envelope figure and saved curve. A sampled polygon is a numerical
approximation to the continuous envelope, not itself a proof between nodes;
the analytic shape argument above establishes the continuous bound.

| Verification | Observed result |
|---|---:|
| \(P'(V_{\rm me})\) | −7.99e−15 W/(m/s) |
| \(V_{\rm mr}P'(V_{\rm mr})-P(V_{\rm mr})\) | −4.26e−13 W |
| Hover-tangent residual | 2.02e−12 W |
| First derivative vs independent finite difference, maximum error | 5.93e−10 W/(m/s) |
| Second derivative vs independent finite difference, maximum error | 9.63e−7 W/(m/s)² |
| Largest fine optimization-grid energy gap | 0.000961290 J |
| Largest 4801-point hull scenario error | 0.000156771 J |
| Largest 30001-point hull / continuous-envelope power error | 6.77e−8 W |
| Refined energy vs envelope, required tolerance | 1e−6 J |
| Distance residual, required tolerance | 1e−8 m |
| Duration residual, required tolerance | 1e−12 s |

All ten figures are 2304 × 1536 PNGs, saved at 320 dpi (PNG metadata reports
319.9892 dpi because resolution is encoded in integer pixels per metre).
Figures 2–4 use a labelled logarithmic vertical axis and a plotting cutoff of
0.1 m/s; no finite value is assigned to fixed-distance flight at zero speed.
The CSV floats retain Python's round-trip precision. Numerical precision does
not imply equivalent accuracy of the physical parameters or real aircraft model.

## Complete output inventory

```text
uav_energy_speed_study/
    main.py
    verify_isolation.py
    README.md
    figures/
        fig01_power_vs_velocity.png
        fig02_energy_vs_velocity.png
        fig03_duration_vs_velocity.png
        fig04_energy_per_meter.png
        fig05_velocity_profiles.png
        fig06_cumulative_energy.png
        fig07_energy_landscape.png
        fig08_energy_comparison.png
        fig09_energy_savings.png
        fig10_convex_envelope.png
    results/
        summary.csv
        fixed_distance.csv
        fixed_time_variable_speed.csv
        sensitivity.csv
        convergence.csv
        power_convex_envelope.csv
        profiles.csv
        validation.json
        outside_baseline.json
        isolation_check.json
        artifact_manifest.json
    .cache/
        matplotlib/fontlist-v390.json
        visual_review.png
        tmp/  (empty)
```

`summary.csv` contains the scalar outcomes; `fixed_distance.csv` contains the
1000-m speed sweep including both exact extrema; `fixed_time_variable_speed.csv`
contains the constant and optimized 1000-m / 100-s strategies; `sensitivity.csv`
contains all seven fixed-time scenarios. The other CSVs preserve convergence,
the envelope, and time-resolved selected profiles. The artifact manifest records
SHA-256 hashes and PNG geometry/resolution. The preview contact sheet is only
for visual review; the ten individual PNGs are the delivery figures.

The source is standalone and reproducible. The pre-run baseline records branch
`feat/27-10`, commit `eff607ceb3cf7b0906353d4abb43eeac5ff371b5`, with no pre-existing
tracked modifications. The final `isolation_check.json` records the actual
comparison result rather than inferring isolation from Git status alone.

Dynamic feasibility, finite switching time, acceleration energy, wind, and
hardware calibration were not evaluated. Consequently the hover/cruise optimum
is a propulsion-model baseline, not a validated real-world flight command.
