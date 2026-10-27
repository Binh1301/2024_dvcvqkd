# Separate proposed single-source recovery — NOT_RUN

Requires explicit authorization; no source computation is authorized by Phase D.
Target ensemble `b083ac8400f7e1068ec045f9882bd256cbbfdec50b64d66d8b7f2d84c05eb214`, VA_hex `0x1.5bbbbb818a6b0p+0`,
nu_raw_hex `0x1.3333333333333p-2`, nu_repo12.75, PMF/amplitude hashes as in
the Phase B source inventory. Reconstruct and authenticate the ensemble first.
Use the existing full-support C4 Python method and recorded implementation,
with the historical1050/1250/1450 ladder. Start no more than one job, one
3600s wall-clock cap, no automatic retry and no GMP/AppControl bypass.
Write progress/each precision row atomically into a NEW recovery namespace,
including input/code/settings hashes, digits, rank/resolved, minimum spectrum,
C,w decimal strings, elapsed time and completion/timeout outcome.
Never overwrite the historical payload or invent unfinished precision rows.
Apply the frozen source convergence rule only in its documented scope;
report both absolute/relative C,w differences and downstream observable
effects. An old absolute tolerance larger than stored w is not a relative
accuracy certificate for w. Any new tighter certification criterion requires
separate prospective approval. A pass does not resolve the entire Phase B
pool or homodyne/security-model requirements. Review before any promotion.
