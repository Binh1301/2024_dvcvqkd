# Parameter-only lightweight-UAV diagnostic — 2026-10-22

User attachment b4a0546e-1cbb-4ddd-b603-d3205df15e57 authorizes this isolated
finite-catalog study. No publication lifecycle or production baseline approval.

Reuse `positive_skr_without_receiver_enlargement_20261022/numeric.py` by import,
unchanged, including its previous optical/full-Z/homodyne evaluator. Hash-bind
the imported files, source payloads, config, request and protected worktree.
Recompute the current bounded-model baseline before search; authenticate the
historical corrected-trial result separately, without mixing optical laws.

All newly evaluated points have Dr=0.08m, original HAP/UAV20/1km, tau_zen=.92,
epsilon_ch=.0186, beta=.95, AO/phase OFF, untrusted detector, epsilon_det in
{.0135,.005}, eta_det in {.8,.85,.9,.95}. No noise below .005 is evaluated.
Use full-angle divergence {233,100,75,50,35,25,20,15}urad, angular jitter
{15.61,10,7.5,5,3,1.561}urad, residual beam-centering SD {1,.5,.3,.2,.1}m,
zenith {0,15,30}deg. Residual optical centering is not UAV navigation precision.

1. Stage A: eight detector scenarios, fixed source and baseline optics.
2. Stages B/C/D: fixed-source divergence and independent pointing scans;
   targeted six coupled PAT tiers across the eight beams and three angles.
   Recompute all channel terms using the imported propagation equations.
3. Stage E: authenticate all 233 exact sources. At each detector scenario,
   rank the full catalog at the best fixed-source-K and best moment-quality
   physical contexts, plus baseline optics for the two eta=.8 noise scenarios.
   Log finite-source alternating P1/P2 updates and compare Uniform/fixed MB/MB.
   Probe exact winning sources over physical contexts, then rank the catalog
   at any newly selected physical context. No interpolation or new C,w/AP.
4. Refine closest/positive candidates and retain negative raw rates. Evaluate
   the requested pointing degradations and both allowed noise scenarios with
   the same source and other parameters. If none is positive, report failures
   and closest candidates rather than inventing three positive designs.
5. Validate mass/outage, passive support, exact source identity, covariance,
   full-Z, noise-once, direct versus Fourier MI and quadrature convergence.
   Produce Vietnamese report, complete CSVs, engineering proxies and vector
   PDF/350dpi PNG sensitivity figures, then a read-only receipt verifier.

No altitude sweep: the existing attenuation is bound to the original20/1km
scenario and there is no vertical extinction profile. No new atmosphere model
or extrapolation of fixed zenith optical depth is introduced for this task.
The historic frozen hash differs from AGENTS.md but matches the documented
2026-09-30 re-freeze; keep that promotion blocker and UNVALIDATED_SECURITY_MODEL,
NOT_READY_FOR_PUBLICATION_SCALE_RUNS and ObjectiveC USER_STOPPED unchanged.
Existing source, security, cache, historical results, config and frozen files
are protected. Only this namespace and relevant task-state ledgers may change.
