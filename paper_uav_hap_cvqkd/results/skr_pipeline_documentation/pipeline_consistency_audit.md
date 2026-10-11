# Audit consistency của tài liệu SKR

Scope:documentation-only; fixed completed151-source/26-distance snapshot. Các findings không tự sửa model, source, manuscript hay running batch. Numeric ordering remains NUMERICALLY_UNCERTIFIED; lifecycle NOT_READY_FOR_PUBLICATION_SCALE_RUNS.

## 1. Findings và bằng chứng

| ID |Finding|Evidence / implemented consequence|Disposition|
|---|---|---|---|
|A01|Retained[0,1] versus result-producing untruncated moments|configs/default.yaml active_treatment; analyze_product:571 uses truncated/F1; closed_form_channel_moments:461 omits those factors|Documented discrepancy; no substitution/rerun; reference tail/error NOT RECORDED|
|A02|Scalar effective noise does not preserve full fading second moment|evaluate_candidate:155 passes eps.0186; covariance.py:95 uses1+tVA+t eps; mu1/muTeps not consumed|epsilon_match algebraic comparison shown but NOT IMPLEMENTED; no corrected K invented|
|A03|Outage integrated into moments versus statewise rate|muHalf contains p_in, t contains p_in²; MI/Holevo scalar evaluates t>0 once|No extra p_in multiplier/no claimed equivalence to E[K(T)] or secure post-selection|
|A04|Actual peak guard disabled|unconstrained_config:99 sets peak/budget/bounds None; reference observed peak51.05066856827034|Do not apply generic default30 limit or call point peak30-feasible|
|A05|Raw alpha0=sqrt30 misread as peak30|qam256.py:95-98 raw levels ±7.5; max raw energy112.5; mean42.5|Explain parameterization; physical peak only after normalization|
|A06|MI method differs across callers|theta10 evaluator:157 GH8product; ExactMBEvaluator.__call__:293 MC|Document active GH8; MC roster/history not convergence evidence for this point|
|A07|Default GH order32 differs from actual8|mutual_information.py:371 default; caller GH_ORDER8|Record caller override in each version; no assumption default32 generated data|
|A08|Direct-Z versus full-interval Holevo|checkpoint targetdirect_Z_minus; caller maximize_full_intervalFalse; general docs/full branch describe maximizer|Do not call modezstar an argmax or direct value a proved full-interval upper bound|
|A09|Source AP exactness is numerical|worker last2 full-support/convergence under1e-7+1e-6 relative; output50digits then float64|No exact symbolic/error-free or17-digit-certified claim|
|A10|Compact reference payload lacks per-rung diagnostics|source records route/support/settings/final C,w only|Fallback_rows/minimum/residual/repair logs NOT RECORDED for this record|
|A11|Old source validation was superseded for wrong AP w|full_support_c4_gram_evaluation_validation_v1.json statusSUPERSEDED_WRONG_AP_W; current worker aa=x2.T|Reject historical PASS as present evidence; corrected CaseA remains bounded different fixture|
|A12|Historical corrected CaseA not identity-compatible D55 certificate|ap_worker_corrected_case_A_20260911.json uses800/900digits, different ensemble/worker hashes|LAST_KNOWN_PASS only for recorded CaseA scope; not D55 convergence|
|A13|No total K error bound resolving near ties|catalog verification total_K_error_bound_certifiedFalse; second gap3.6726688357191506e-10|Preserve NUMERICALLY_UNCERTIFIED; no continuous plateau or certified pair ordering|
|A14|Performance-near threshold versus absolute analysis tolerances|export classify relative<=1e-5; earlier near script absolute thresholds1e-6…1e-10|Define CSVdelta_K absolute, fraction/percent separately; criterion not an AO stopping replacement|
|A15|AO stagnation versus numerical closure|stopping_status:447 includes missing/open/history; radius check at refinement-loop entry only|Do not call unchanged pair/consecutive identical K converged;4-stage cap not epsilon certificate|
|A16|Finite catalog versus unbounded continuous problem|151sparsepairs; positive nu/VA wrapper; no boundary/global theorem|BEST_CURRENT_EXACT_TESTED_CANDIDATE_ONLY; Uniform endpoint separately sampled|
|A17|Original AO versus expanded catalog differs at22km|original strict three_scheme_alt_opt.csv:VA5.5,K.07661685601911128;151:VA5.475,K.07661740491526092|Explicit gain5.488961496435962e-7;25otherdistances agree;later26/26 equality is another version|
|A18|Manuscript catalog147 versus fixed documentation151|joint_optimization_final.tex numerical-results paragraph|Tag historical DM scope; manuscript preserved|
|A19|Requested rounded fixed-MB VA differs binary64 source|runner FIXED_MB_VA_REQUESTED1.3833230303; actual1.3833230302980657|Document actual exact hash-bound value, not interpolated moments|
|A20|Frozen specification hash differs historical required value|actualdf83ea63af3b475ecca03a44d22d3240ab24d695ff0ebef31f0cd6747db78c15 vs historical561fecc97cdf9967034ffd6865c1605804b624b98f47a091e47f17e520a2a7b1|Known blocker remains; no lifecycle promotion or restoration|
|A21|Generic physical config null fields and obsolete open tabs|defaulttau_zen null/phase mapping unresolved; baseline_smoke legacy; exact_tau_oracle separate protocol|Use saved D55 overrides/context, not open-tab parameters|
|A22|Separate w0=.10m redesign versus theta10 waist|FINAL_MODEL_SPEC first re-freeze versus saved D55w0.0986760647169751|Separate experiment identities; no mixed attribution|
|A23|Running catalog changes during documentation|full_51_grid_exact_completion controller already authorized/running per repository records|Exclude live completion entirely; use timestamp/hash-fixed151snapshot; no live-count claim|
|A24|Plots may omit negative rates visually|log10renderer positive_runs:68 filters K<=0; underlying CSV raw|Report display omission versus clipping; no rerender or CSV alteration|
|A25|Grid51coverage differs from151total sources|initial grid20cached/31missing,131offgrid sources; two-level spec30+25-4|Do not claim complete51-grid from151catalog or read partial completion|
|A26|Scientific working-tree identity differs from commit-only story|several historical producers untracked before task; renderer/state already edited|Snapshot records HEAD and dirty state; code facts bound by actual bytes/context rather than claimed commit-only state|
|A27|External manuscript source unavailable|PAPER_CODE_ALIGNMENT references C:/Users/admin/Downloads/2026__Binh_s_work__Copy_ (1).pdf; path absent|Original external equation-number audit not newly verified; cite available repo equation/code/generated LaTeX only|
|A28|Physical factor independence/weak-lognormal scope not experimentally validated here|moment product assumes independence; scintillation code weak-turbulence finite-aperture model|AV for outside-model physical validity; no measured/model-validity certificate|
|A29|Security interpretation limited|SECURITY_SCOPE_FREEZE unresolved attack/fading approvals and no finite-key protocol; scalar-channel result path|No unconditional/finite-size/composable/operational fading-security claim|
|A30|Numerical repairs not all persisted in point CSV|covariance/Holevo include tiny-repair diagnostics; point evaluator exports aggregate metrics|Document code repairs without claiming none occurred at reference|
|A31|Printed decimal digits differ from numerical guarantees|reference operands printed17digits; binary64 subtraction differs from Decimal strings in final digits|Verify binary64 stored arithmetic; no rounding of ranking inputs; no17-digit error guarantee|

## 2. What evidence is actually available

The completed checkpoint contains26context identities, each with151records; the recorded source/ensemble/channel keys identify the source exactly. Current canonical-LF producer hashes can be checked without importing any evaluator. Source payloads carry support256, final C,w, settings and route; they are evidence of accepted producer output, not full raw AP diagnostics.

all_exact_skr_points/catalog_verification.json and near_optimal_skr_analysis/analysis_verification.json record historical cache-only coverage/ranking verification. Their software/test claims remain historical until scoped document checks independently reread the required inputs. test runs from those artifacts were **not repeated**. Current checks below are parsing/hash/arithmetic/document checks only.

Historical convergence performed:

- AP worker acceptance logic resolves support and compares last precision rows; individual reference comparison values are not available in compact payload.
- Corrected CaseA800/900-digit artifact records stable values at its own fixture and historical producer, not a blanket/current D55 certificate.
- TEST2A GH8/16/24/32/48/64 values exist for other source/channel; no transfer of its apparent stability to D55.
- Monte Carlo convergence roster exists for another caller; it cannot certify GH8 or direct-Z D55 total error.
- Legacy full-support validation with wrong-w status is superseded and excluded.

Unavailable bounds: reference-specific finite-domain tail correction effect; channel integration error after all transforms; source absolute-error enclosure; GH8error at all151×26points; propagation through near-pure symplectic entropy; combined error small enough to distinguish second-best gap. No continuous-domain global-optimum or operational fading-protocol certificate.

## 3. Authorization and file preservation

Writes are confined to results/skr_pipeline_documentation/. The user expressly required this scope, so docs/PROJECT_STATE.md,EVIDENCE.md,DECISION_LOG.md,NEXT_ACTIONS.md and .agent/SESSION_HANDOFF.md are read for context and not updated by this task. Any state staleness is recorded here without editing live project/batch records.

No source,security functional,frozen model,config,active cache,checkpoint/ledger,controller,Windows Sleep/AC/Job settings,existing manuscript,baseline selection or threshold approval is changed. Training/test access and scientific evaluation are NOT_RUN. Read-only file listing and stdlib parsing/hashing do not import scientific modules or create their bytecode.

Input and output manifests plus lightweight verification receipts record the document checks. Static LaTeX checks are not a compiler pass; if an installed TeX engine is unavailable, compilation is BLOCKED_BY_ENVIRONMENT and no PDF-build claim is made. Mermaid syntax inspection is not a rendered-browser pass.

## 4. Fifteen requested questions mapped to sections

|Question|Where answered|
|---|---|
|Physical channel calculation|Vietnamese sections3–5;English geometry/atmosphere/pointing/PDF|
|Fading to effective parameters|Vietnamese5–6, with untruncated/retained discrepancy|
|QAM/MB symbols and probabilities|Vietnamese7;English QAM/MB|
|V_A normalization|M4;normalization.py:22|
|Exact C,w operations|Vietnamese8;English source-moment sector/solve equations;pseudocode2|
|C,w expense|High-precision4×64eigensystems/inverse/columnwise solves;no quadrature|
|Numerical I_AB|Vietnamese9;GH8product formulaI4|
|Numerical chi_BE|Vietnamese10;H1–H4/guards|
|Reverse reconciliation|Vietnamese10–11;Bob-basedchi_BE/betaMI|
|Assembly K|K1;reference numerical walkthrough and arithmetic verification|
|Distance dependencies|Vietnamese11/table;26distance grid|
|nu/VA dependencies|Vietnamese7–8/11table|
|Original AO search|Vietnamese13;exact1D,initialization,warmstarts,stopping,pseudocode3|
|Near-optimal threshold|Vietnamese14;relativefraction/percent;finite-catalog scope|
|Supported numerical accuracy|Vietnamese16;this audit;per-record missing evidence/uncertified gaps|

## 5. Kết quả kiểm tra tài liệu hiện tại

Lightweight stdlib checks đã đọc lại239tệp snapshot, không có input drift; xác minh26objective contexts,151source identities,3926saved metric equations và3926exported SKRs. Kiểm tra51traceability rows xác nhận paths/line ranges vàclassification. Original strict AO so151 có25matches và một khác biệt22km. Những phép kiểm tra này là parsing/hashing/arithmetic trên dữ liệu lưu, không tạo ensemble, source moments, MI hoặc SKR mới.

Trạng thái: **CURRENTLY_VERIFIED_PASS_DOCUMENTATION_ONLY**, receipt ở documentation_verification.json. LaTeX braces/environments/math-delimiters/text-underscore vàsource-reference checks PASS tĩnh. **BLOCKED_BY_ENVIRONMENT** cho compilation: không có pdflatex/xelatex/lualatex/tectonic trên PATH. Mermaid được đọc syntax/dependencies thủ công; render **NOT_RUN**. git diff --check PASS. Scientific regression/convergence/evaluation NOT_RUN.

All seven requested deliverables and independent snapshot/comparison/verification receipts are present. STOP after documentation.
