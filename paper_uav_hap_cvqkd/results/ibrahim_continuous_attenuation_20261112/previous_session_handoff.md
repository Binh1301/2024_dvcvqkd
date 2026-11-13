# Session Handoff

2026-11-11 EVID-0235/DEC-0218. New exponential-GRF stochastic cloud task COMPLETE.
Read docs/STOCHASTIC_CLOUD_GRF_README.md and results/stochastic_cloud_grf_20261111/
report_vi.md, validation.json, artifact_verification.json. New independent
module/config/runner/plotter/tests only; prior Ibrahim models/results unchanged.

Ks=exp(-distance/ell200m),tau300s,rho=exp(-1/300),wind(-5,0)m/s,1000slots0..999.
Internal5x40m/3200x150 embedding16x6km; output40m/50x50/2km. MinEigen.01249935,
negative/clipped0,exact internal-grid wind permutation and -40m/8slots; frozen
fullvariancechange0/covariancechange3.33e-16 before evolving runs. Guard/backtrace
and covariance-support checks exclude observation re-entry and periodic folding
for all exported point/time pairs. No arbitrary off-lattice-wind interpolation:
change refinement or fail. All parameters illustrative, no weather calibration.

CURRENTLY_VERIFIED_PASS:11independentseeds,12new+21Ibrahim regressiontests=33,
152four-SEchecks,56sealed artifacts,941oldprotectedfiles unchanged. Eight400dpi
PNG/PDFs(E/F/Gvector),1000frameGIF and fullNPZ/CSV/histogram/track data delivered.
Fixed ensembletheta.5244005127080407 expected30%; maininitial33.32%,final27.56%,
timeavg28.88036%. Ensemble timeavg30.01817%+/-2.055pp approximate95%CI.
5pointwise95%CIs exclude targets,max3.10073SE; not simultaneous certification.
158195track segments have ROI/time and association ambiguity recorded; not
physical cloud lifetimes. Intensity is uncalibrated proxy, not CLWC/blockage.
Read-only verification from project root:
.venv/Scripts/python.exe -X utf8 -B results/stochastic_cloud_grf_20261111/verify.py

Starting branch feat/cloud-11-11,HEAD0c039f394511ce43c0038e76694c4f15e446b1eb.
Starting worktree was DIRTY with prior EVID0234/DEC0217 registries and untracked
stationary-Ibrahim source/artifacts; preserved, startup diff/handoff archived.
No existing scientific/security/frozen/channel/SKR/finite-size/UAV/cache/
manuscript change, QKD baseline/threshold approval or publication setting change.
No physical/optical integration,training/final-test/heldout/publication evaluation.
Full repository suite NOT_RUN. Peleg publisher HTML and Carpentieri author
preprint checked; published ETHPDF403 documented; simplified AR(1) is proposed.
Frozen-hash mismatch df83ea63...b78c15 vs561fecc9...a2a7b1,E2INCONCLUSIVE,
strictPhaseBfalse,INSUFFICIENT_EVIDENCE,UNVALIDATED_SECURITY_MODEL,
NOT_READY_FOR_PUBLICATION_SCALE_RUNS,ObjectiveC USER_STOPPED remain unchanged.
Deliver and stop; no automatic integration or extra experiment.
