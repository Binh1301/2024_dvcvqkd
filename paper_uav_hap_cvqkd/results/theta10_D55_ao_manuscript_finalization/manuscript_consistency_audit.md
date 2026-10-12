# Manuscript consistency audit

CURRENTLY_VERIFIED_PASS: saved-data/provenance and focused static LaTeX checks.

Repository discovery found only the standalone article master in ao_final_scientific_results; no full-paper master, IEEEtran template, original numbered-equation source or bibliography was available (including hidden-file search outside .git/.venv). We therefore integrate into a NEW standalone article wrapper, not an unseen full paper. No previous manuscript file is edited. Known labels eq:p1, eq:p2, alg:ao and the joint-section/figure labels are preserved. A new eq:ao-stopping label is added. Preview numbering is P1(5), P2(6), stopping(7), using a documented wrapper-only counter offset2; this is not proof of original-paper numbering. Remove the offset when inserting into the actual full master and resolve any colliding labels there.

1. P1 fixes nu^(r-1); P2 fixes new VA^(r). Approximate signs reflect finite numerical search.
2. Algorithm1 preserves original initialization, four raw starts, prior-distance warm start, ordered tie handling, last complete update, unresolved latch and original failure/threshold status logic. Missing moments do NOT independently trigger immediate outer termination when a valid best point exists.
3. Rmax6 is a conservative safeguard: caps4/6/8/10 give identical terminals; no cap termination occurs.
4. Epsilon1e-8 measures objective stagnation, not absolute error;1e-9 gives no gains;1e-6 reduces283 cycles to279 with identical terminals.
5. All16 settings and416 distance records checked against original147-source values. Scope: per-setting129 starts, 20 stagnation/109 unresolved, same55 missing sources. No successful coordinate search among9856 calls (9024 within cycles +832 postchecks).
6. No continuous/global-optimality, universal-start agreement, error-bound or expanded-security claim is made. Manuscript statements about non-certification are intentional, not optimizer failures hidden as convergence.
7. Raw convention explicitly nu_MB=nu_raw; nu_repo=42.5*nu_raw. Ref(.165,5.5),K.07798099387393764;22km(.165,5.475),K.07661740491526092 confirmed. Individual baseline catalog matches59/129, unanimous distances0/26.
8. The intended domain retains nu>=0; original AO searches nu>0. Compatible independently stored Uniform samples exist at26 distances under the same model, but the VA continuum on nu=0 is not fully optimized and Uniform is excluded from positive-MB AO. Existing positive-only plot stops Uniform25km, both MB40km; raw negative tail is not changed.
9. Compact main table groups four caps per epsilon; each cell is per configuration, not a pooled statistic. Detailed16 rows and rounded26-distance parameters are in appendices; copied CSVs are byte-identical. All five figure PDFs are byte-identical to validated originals, with no new rendering.
10. Input graph, braces, environments, labels/references, bibliography dependencies, one algorithm and preview5/6/7 numbering checked. No bibliography commands/dependencies were introduced. Undefined macros/package availability and overfull/layout issues require a real TeX compiler.
11. Compile status is recorded separately; static checks are NOT a build pass. The downloadable package is ready for an external build, not a claim that Overleaf has compiled it.
12. Original scientific source/configs/frozen files/AO defaults/cache/results protected by hashes. No AP, channel, source, MI/Holevo, SKR evaluation, AO rerun, interpolation, observer/profiling or final-test access.

The frozen specification historical-hash discrepancy remains PREEXISTING_UNCHANGED; publication-scale lifecycle remains NOT_READY_FOR_PUBLICATION_SCALE_RUNS. This task writes existing conditional direct-Z-minus results only and does not certify another protocol or the broader frozen training model.
