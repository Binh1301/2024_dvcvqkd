# Document and saved-data validation

Scope: LaTeX source and figure delivery only, following the user's explicit
2026-10-21 choice not to compile. No revised manuscript PDF exists.

| Check | Result |
| --- | --- |
| Reference PDF identity | CURRENTLY_VERIFIED_PASS: SHA-256 matches archived reference |
| Reference visual review | Pages 4, 5, 6 inspected |
| Source selection | Sealed single-file Overleaf revision selected; later unfinished GLOBECOM attempt inspected |
| Protected prefix | CURRENTLY_VERIFIED_PASS: reversing documented heading changes reproduces original scientific prefix with LF normalization |
| Title/authors/abstract/earlier science | Preserved |
| Bibliography | Preserved, all four entries |
| Section numbering | Static check: automatic III.B, IV, V; no section-counter override |
| Figure numbering | Explicit offset to retain requested numbers 2/3; absent earlier illustration disclosed |
| Equations | P1/P2/P3, raw rate, Bellman initialization/recursion, Greedy labels retained |
| Algorithm | One-column DP float included; formula uses `Nt*lambda/D_ref` |
| Table I | All requested parameters checked against manuscript mobility configuration |
| Plotted means/CI | CURRENTLY_VERIFIED_PASS: 57 exact saved points, no recomputation/resampling |
| Scientific figure assets | Two vector PDFs, embedded fonts, corresponding 350-dpi PNGs |
| Figure visual review | Both exported PNGs viewed; labels, markers, legends and panel letters legible |
| Source receipts | 743 members: 638 raw SHA-256 matches, 105 UTF-8 CRLF-only differences; no unexplained content changes |
| Labels/citations/environments | Static references defined, labels unique, environments balanced, assets present |
| Protected prior files | 5,405 snapshot hashes checked; only relevant project ledgers may change |
| ZIP | Integrity and byte-identical source/vector assets checked |
| LaTeX compilation | NOT_RUN_BY_EXPLICIT_USER_CHOICE |
| Revised PDF visual inspection | NOT_RUN |
| Overfull equations/table/float placement | NOT_RUN; static checks cannot establish typeset layout |
| Actual occupied page length | NOT_MEASURED; no estimate substituted |
| Quantum/channel/source/trajectory/cloud calls | 0 |
| Commit/push | NOT_RUN |

Machine-readable current checks and exact count are in
`validation/static_checks.json`. Input hashes, heading transformations,
and figure source mappings are stored separately. Final artifact digests are in
`validation/final_receipt.json`.

Automatic approval review rejected downloading an external compiler, citing the
preceding read-only instruction. After the rejection was disclosed, the user
selected source/figures only. No compiler was downloaded or executed, and no
rejection was bypassed.

This is a static document/data PASS. It is not a rendered-layout PASS, a security
validation, or a publication approval. The source remains a provisional internal
review manuscript with TBD/XXX authorship, synthetic clouds, offline cloud
information, finite catalogs/grids, distance rather than propulsion-energy cost,
and incompatible 2D-MI/homodyne-Holevo measurement pairing.

UNVALIDATED_SECURITY_MODEL

NOT_READY_FOR_PUBLICATION_SCALE_RUNS

The pre-existing frozen-spec SHA-256 discrepancy and Objective C USER_STOPPED
remain unchanged. No production code, source caches, physical configurations,
security functional, frozen model, training, test access, baseline selection,
or threshold approval changed.
