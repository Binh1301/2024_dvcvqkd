# Stage-1 validation report

Scope: saved historical 218-source catalog and parameter-domain audit only.
Stage 2/3 are NOT_RUN pending approval of a numerical exploratory domain.

| Item | Result |
| --- | --- |
| Original experiment | 233 urad full divergence, Dr=0.08 m, HAP/UAV=20/1 km |
| Roster | 36 Uniform + 182 MB; exactly 218 unique common ensembles |
| All saved candidate values | 31*218=6758, including every negative raw rate |
| Independent finite-catalog argmax | 62/62 match; no discrepancy |
| Source identity | Exact binary64 ensemble hashes reconstructed from saved NPZ |
| Source PMF and geometry | 256 positive probabilities, 256 distinct states, MB law and VA energy checked |
| Raw/repository nu | nu_repo=42.5*nu_raw, verified by payload hex and actual PMFs |
| C,w | Historical payloads authenticated; no fresh AP recomputation |
| Channel association | Each saved angle, geometry, moments and modulation-dependent N matched |
| Rate/noise reconstruction | Maximum residuals recorded in validation/audit_checks.json |
| GH convergence | Saved GH16/32/64 values checked; no quadrature rerun |
| Covariance | Saved uncertainty/spectrum gates and V,W reconstruction checked |
| Catalog boundary | MB8 at24--60 deg, Uniform12 at42--60 deg; no physical cap inferred |
| Receipt provenance | 106 members: 93 raw SHA256 matches, 13 CRLF-only matches, no content mismatch |
| Historical peaks | Uniform52deg, fixedMB48deg, optimizedMB48deg reproduced from saved values |
| Figure data | Only evaluated historical points; no surrogate/interpolated optimum |
| New sources, C,w calls, rate evaluations | 0 |
| Continuous optimum or optimality gap | NOT_CERTIFIED |
| Protected files | Startup hashes checked; only relevant ledgers may change |
| Commit/push | NOT_RUN |

`validation/audit_checks.json` records producer checks. The independent verifier
uses a complete 31-by-218 numeric array and NumPy argmax, rather than the
producer's sorted per-family records. It also checks plotted values, vector-PDF
content, embedded fonts, PNG resolution, links, input hashes and protected files.
Exact independent count is in `validation/independent_checks.json`.

The producer checks are arithmetic/provenance checks on stored results. They do
not independently recompute MI, source moments, entropy or turbulence integrals,
and they are not interval-error or security certificates. A finite-catalog
maximum of saved numerical values is distinct from a proof over a continuous
physical source domain. Multistart/local refinement would not establish that
proof either without justified whole-domain bounds.

The proposal in `proposed_pilot.json` is NOT_APPROVED and NOT_EXECUTED. No
physical energy constraint was introduced. No zero-gain series or untested
refinement optimum is fabricated; new-value and gain fields are N/A.

The pre-existing frozen-model SHA256 discrepancy is retained, without modifying
the specification. The manuscript's alternate VA/nbar relation is recorded;
the audited historical source normalization remains VA=2*nbar. No production
evaluator, source cache, detector convention, security functional, optical
configuration, training, test access, baseline/threshold approval or Objective C
USER_STOPPED state changes.

UNVALIDATED_SECURITY_MODEL

NOT_READY_FOR_PUBLICATION_SCALE_RUNS
