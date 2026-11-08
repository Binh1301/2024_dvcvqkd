# Independent review: IEEE 2019 rotor reference

What this change does: Adds separately named IEEE 2019 and arXiv 2018 aircraft
profiles and derives the power coefficients from raw physical parameters. It
reuses the historical total-power evaluator and exports a separate reference
figure without running a mission or changing the default aircraft.

Review scope: new reference loader, speed minimization, figure exporter, both
profiles, focused tests, plan, existing propulsion evaluator and configuration
loader. Expected use is one researcher invoking the CLI with a YAML profile.

## Must fix

1. **A modified aircraft can still receive the verified IEEE label**
   (`src/uav_qkd/rotor_power_figure.py`, `_source_verification` and
   `export_figure`).
   - **What this is:** The exporter accepts a profile path and labels the result
     READY when the profile name is `ieee_2019` and the local PDF hash matches.
   - **Problem:** Changing `aircraft.weight_N` to 100 or changing
     `induced_velocity_policy` to `table_value` does not invalidate that status.
     The caption still attributes the calculation to IEEE Table I and says the
     derived induced velocity was used. An in-memory mutation reproduced
     `CURRENTLY_VERIFIED_PASS` after both changes.
   - **Fix:** Bind the verified status to the verified aircraft values, source
     identity/hash and induced-velocity policy, or reject a profile that differs
     from the verified IEEE reference. Add a regression test for a changed
     weight and policy.
   - **If we skip it:** A routine edit or supplied profile can produce a
     scientific figure with incorrect source attribution.

## Checks completed

- Independently calculated P0=79.85628000000001 W,
  Pi=88.62793774108202 W, hover=168.48421774108203 W and
  derived v0=4.028542624594636 m/s.
- Obtained ME=10.211691198388639 m/s and MR=18.294480351062063 m/s.
  Both objective values passed a separate 100001-point sweep over 0-30 m/s.
- Checked the component sum against the reused evaluator at relative tolerance
  2e-15, finite nonnegative total power, and decreasing induced power across
  the same sweep.
- Verified every legacy `PropulsionParams` field matches `configs/paper.yaml`
  to absolute tolerance 1e-10; the table convention v0=7.2 is preserved.
- Read the existing tests, including high-speed numerical stability,
  stationarity, output dimensions and overwrite protection. Existing default
  paper inputs remain explicitly incomplete and research authorization false.

Verdict: fix 1 first.

Not checked: full test-suite rerun, final figure visual layout (being adjusted
by the implementer), or independent re-reading of the source PDF. No source,
mission, trajectory, cloud or QKD experiment was run by this reviewer.
