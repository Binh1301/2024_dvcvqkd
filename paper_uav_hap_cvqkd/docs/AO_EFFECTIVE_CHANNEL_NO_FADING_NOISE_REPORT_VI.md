# AO multistart — Gaussian bỏ phương sai fading

Ngày2026-10-13. **FINAL STATUS: AO_RESOURCE_LIMITED.** Chỉ L=21.9393102292km.
Đã thực thi AO và các probe nguồn mới. DeltaK=0 trên catalog không được coi là hội tụ liên tục.

## A. Mô hình khoa học

Dùng effective_channel_no_fading_noise xuyên suốt, objective effective_gaussian_Zstar_diagnostic_SKR.
Giữ Eq.(10), active conditioning trên(0,1], atomAoA và cả ba mômen. Adaptive optics/phase OFF; ideal heterodyne R=1,xi_det=0,chi_het=1;beta=.95,xi_ch=.0186.
Full divergence10µrad,w0=.0986760647169751m,receiver diameter.55m.

$$T_{\rm eff}=\langle\sqrt\eta\rangle^2=0.16092029098192165,\quad \xi_{\rm eff}=0.0186,\quad N_{\rm eff}=T_{\rm eff}\xi_{\rm ch}.$$
$$a=1+V_A,\quad b=1+T_{\rm eff}(V_A+0.0186),\quad Z^*=2\sqrt{T_{\rm eff}}C-\sqrt{2T_{\rm eff}(0.0186)w}.$$
$$K=0.95I_{AB}^{\rm discrete}-\chi_{BE}(Z^*).$$

Cùng centered MB-256QAM ensemble cho MI/Holevo. Signed rawK, không clipping, không Gaussian-input MI, không fading-mixture MC. Xấp xỉ này bỏ fading variance; chưa là certified fading-channel security lower bound.

## B. Regression và khởi tạo

Mandatory reference tái lập trong5e-12; các số yêu cầu làm tròn12decimals. Source-authentication adapter trùng evaluator đã bảo toàn tại reference, residuals=0.
Đã đánh giá mới182 MB/29Uniform dưới objective mới, không xếp hạng bằng historical/corrected SKR.

| start_id | nu_raw | V_A | initial_SKR | origin |
|---|---|---|---|---|
| requested_1 | 0.16500000000000001 | 5.5 | 0.058630150221137711 | USER_REQUESTED |
| requested_2 | 0.14999999999999999 | 6.5 | 0.057808829370923909 | USER_REQUESTED |
| requested_3 | 0.16 | 6 | 0.058305272498079153 | USER_REQUESTED |
| requested_4 | 0.17499999999999999 | 4.5 | 0.058551566285246714 | USER_REQUESTED |
| requested_5 | 0.20000000000000001 | 3.5 | 0.056976655719336189 | USER_REQUESTED |
| catalog_1 | 0.17000000000000001 | 5 | 0.05873317206754991 | RANKED_DIVERSE_EXACT |
| catalog_2 | 0.16 | 5 | 0.058695703202223226 | RANKED_DIVERSE_EXACT |
| catalog_3 | 0.16562500000000002 | 5.5 | 0.05862975259908576 | RANKED_DIVERSE_EXACT |

## C. Quỹ đạo P1/P2

P1 đánh giá slice exact tại nu hiện hành; P2 dùng ngay VA sauP1. Tái dùng coarse catalog scan, boundary probes và paired midpoint refinement của bộ AO. Coarse local maxima được lưu; không giả định unimodality. Trong ngân sách này ưu tiên refinement bracket của điểm tốt nhất.
Mọi accepted update không giảmK; rejected/missing steps lưu trong JSON/CSV. Zero endpoint được kiểm tra riêng vì helper historical chỉ nhậnnu>0.

| start_id | epoch | iteration | nu_before | VA_before | VA_after_P1 | K_after_P1 | nu_after_P2 | K_after_P2 | delta_K | parameter_change | convergence_status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| requested_1 | 1 | 1 | 0.16500000000000001 | 5.5 | 5 | 0.058720900119700159 | 0.17000000000000001 | 0.05873317206754991 | 0.00010302184641219903 | 0.5 | BEST_EXACT_CANDIDATE |
| requested_1 | 1 | 2 | 0.17000000000000001 | 5 | 5 | 0.05873317206754991 | 0.17000000000000001 | 0.05873317206754991 | 0 | 0 | BEST_EXACT_CANDIDATE |
| requested_2 | 1 | 1 | 0.14999999999999999 | 6.5 | 5 | 0.05861226709405698 | 0.17000000000000001 | 0.05873317206754991 | 0.00092434269662600155 | 1.5 | BEST_EXACT_CANDIDATE |
| requested_2 | 1 | 2 | 0.17000000000000001 | 5 | 5 | 0.05873317206754991 | 0.17000000000000001 | 0.05873317206754991 | 0 | 0 | BEST_EXACT_CANDIDATE |
| requested_3 | 1 | 1 | 0.16 | 6 | 5 | 0.058695703202223226 | 0.17000000000000001 | 0.05873317206754991 | 0.00042789956947075769 | 1 | BEST_EXACT_CANDIDATE |
| requested_3 | 1 | 2 | 0.17000000000000001 | 5 | 5 | 0.05873317206754991 | 0.17000000000000001 | 0.05873317206754991 | 0 | 0 | BEST_EXACT_CANDIDATE |
| requested_4 | 1 | 1 | 0.17499999999999999 | 4.5 | 5 | 0.05873082341419078 | 0.17000000000000001 | 0.05873317206754991 | 0.0001816057823031958 | 0.5 | BEST_EXACT_CANDIDATE |
| requested_4 | 1 | 2 | 0.17000000000000001 | 5 | 5 | 0.05873317206754991 | 0.17000000000000001 | 0.05873317206754991 | 0 | 0 | BEST_EXACT_CANDIDATE |
| requested_5 | 1 | 1 | 0.20000000000000001 | 3.5 | 5 | 0.058518608772232472 | 0.17000000000000001 | 0.05873317206754991 | 0.0017565163482137214 | 1.5 | BEST_EXACT_CANDIDATE |
| requested_5 | 1 | 2 | 0.17000000000000001 | 5 | 5 | 0.05873317206754991 | 0.17000000000000001 | 0.05873317206754991 | 0 | 0 | BEST_EXACT_CANDIDATE |
| catalog_1 | 1 | 1 | 0.17000000000000001 | 5 | 5 | 0.05873317206754991 | 0.17000000000000001 | 0.05873317206754991 | 0 | 0 | BEST_EXACT_CANDIDATE |
| catalog_2 | 1 | 1 | 0.16 | 5 | 5 | 0.058695703202223226 | 0.17000000000000001 | 0.05873317206754991 | 3.7468865326684142e-05 | 0.010000000000000009 | BEST_EXACT_CANDIDATE |
| catalog_2 | 1 | 2 | 0.17000000000000001 | 5 | 5 | 0.05873317206754991 | 0.17000000000000001 | 0.05873317206754991 | 0 | 0 | BEST_EXACT_CANDIDATE |
| catalog_3 | 1 | 1 | 0.16562500000000002 | 5.5 | 5.5 | 0.05862975259908576 | 0.16500000000000001 | 0.058630150221137711 | 3.976220519508189e-07 | 0.00062500000000001443 | BEST_EXACT_CANDIDATE |
| catalog_3 | 1 | 2 | 0.16500000000000001 | 5.5 | 5 | 0.058720900119700159 | 0.17000000000000001 | 0.05873317206754991 | 0.00010302184641219903 | 0.5 | BEST_EXACT_CANDIDATE |
| catalog_3 | 1 | 3 | 0.17000000000000001 | 5 | 5 | 0.05873317206754991 | 0.17000000000000001 | 0.05873317206754991 | 0 | 0 | BEST_EXACT_CANDIDATE |
| best_MB_refinement | 2 | 1 | 0.17000000000000001 | 5 | 5 | 0.05873317206754991 | 0.17000000000000001 | 0.05873317206754991 | 0 | 0 | BEST_EXACT_CANDIDATE |

Multistart consistency: 8 trajectories, 1 distinct terminal pairs; agreement is only over tested exact points.

| start_id | initial_SKR | final_nu | final_VA | final_SKR | status |
|---|---|---|---|---|---|
| requested_1 | 0.058630150221137711 | 0.17000000000000001 | 5 | 0.05873317206754991 | BEST_EXACT_CANDIDATE |
| requested_2 | 0.057808829370923909 | 0.17000000000000001 | 5 | 0.05873317206754991 | BEST_EXACT_CANDIDATE |
| requested_3 | 0.058305272498079153 | 0.17000000000000001 | 5 | 0.05873317206754991 | BEST_EXACT_CANDIDATE |
| requested_4 | 0.058551566285246714 | 0.17000000000000001 | 5 | 0.05873317206754991 | BEST_EXACT_CANDIDATE |
| requested_5 | 0.056976655719336189 | 0.17000000000000001 | 5 | 0.05873317206754991 | BEST_EXACT_CANDIDATE |
| catalog_1 | 0.05873317206754991 | 0.17000000000000001 | 5 | 0.05873317206754991 | BEST_EXACT_CANDIDATE |
| catalog_2 | 0.058695703202223226 | 0.17000000000000001 | 5 | 0.05873317206754991 | BEST_EXACT_CANDIDATE |
| catalog_3 | 0.05862975259908576 | 0.17000000000000001 | 5 | 0.05873317206754991 | BEST_EXACT_CANDIDATE |

## D. Best exact numerical solution

**(nu_raw,VA,K)=(0.17000000000000001,5,0.05873317206754991).**
Digits là output binary64 của evaluator, không phải bảo đảm total error17digits.

| scheme | nu_raw | V_A | I_AB | beta_I_AB | chi_BE | SKR |
|---|---|---|---|---|---|---|
| Initial MB | 0.16500000000000001 | 5.5 | 0.52794061038495599 | 0.50154357986570819 | 0.44291342964457048 | 0.058630150221137711 |
| Best catalog MB | 0.17000000000000001 | 5 | 0.48717715519741578 | 0.46281829743754499 | 0.40408512536999508 | 0.05873317206754991 |
| Multistart AO MB | 0.17000000000000001 | 5 | 0.48717715519741578 | 0.46281829743754499 | 0.40408512536999508 | 0.05873317206754991 |
| Optimized Uniform | 0 | 1 | 0.11148258590641102 | 0.10590845661109047 | 0.10132225508887815 | 0.0045862015222123131 |

Best catalog và terminal AO được báo riêng. Uniform là tốt nhất exact đã tìm trong VA search, chưa là maximum liên tục được chứng nhận.

## E. Source, covariance, MI/Holevo

| quantity | value |
|---|---|
| C | 2.9580396096665234 |
| w | 5.891447295112126e-07 |
| T_eff | 0.16092029098192165 |
| xi_eff | 0.018599999999999998 |
| N_eff | 0.0029931174122637422 |
| a | 6 |
| b | 1.807594572321872 |
| Z_star | 2.3731681859935847 |
| lambda_1 | 5.1958326937601198 |
| lambda_2 | 1.0034272660819916 |
| lambda_3 | 3.9940382794106566 |
| I_AB | 0.48717715519741578 |
| beta_I_AB | 0.46281829743754499 |
| chi_BE | 0.40408512536999508 |
| SKR | 0.05873317206754991 |

Sourcekey: 05e00c51ba3999da4292776e9114536dc964997d61b4fc48719360c40eef635b; ensemblehash: 65a38efb871f9d600cd823a022c66593fbf22785998b8af5699a5c210e9525fa.
Scientific context: 77abb3f0ff944accb850da5f6e8ad68b4fec69dd702bd11b5b897681e6c7193c.

## F. Cải thiện

DeltaK so initial=0.00010302184641219903 bits/use; gain=0.17571479183257652%.
DeltaK so bestcatalog=0 bits/use.

## G. Uniform và shaping gain

Uniform nu0,VA=1,K=0.0045862015222123131.
MB−Uniform=0.054146970545337597 bits/use; relative gain with |KUniform|=1180.649613478344%.
Uniform status=BRACKETED_EXACT_CATALOG_SOURCE_MISSING; actual range=[0.02, 5.0]; bracket=[0.8, 1.075].

## H. Độ tin cậy, ngân sách và unresolved coverage

Unique exact objectives=211,newsource completions=0,source attempts=3.
Default đã thông báo: source wall budget1800s,per-source<=720s,max3 attempts,Uniform reserve600s.
Measured sourcewall=1800.016000s;optimizationwall=1807.765000s.
Giữ nguyên full-support oracle,1050/1250/1450digits,stability rule và internal watchdog3600s. External WindowsJob deadline chỉ giới hạn tài nguyên; timeout không có C,w/K.

| attempt | nu_raw | V_A | group | deadline_seconds | status | elapsed_seconds | returncode | aggregate_cpu_seconds |
|---|---|---|---|---|---|---|---|---|
| 1 | 0.17000000000000001 | 4.75 | MB | 720 | TIMEOUT | 720 | 124 | 694.390625 |
| 2 | 0.17000000000000001 | 5.25 | MB | 480 | TIMEOUT | 480 | 124 | 457.59375 |
| 3 | 0 | 0.90000000000000002 | Uniform | 600 | TIMEOUT | 600.01600000000326 | 124 | 573.65625 |

Cache authentication kiểm tra bytehash,parameterhex,ensemblehash,settings/producer hashes và full support256. Không interpolation/nearest-neighbor C,w/SKR.
MI GH8/16/32 cho mọi evaluated candidate. Final winner và competitors/Uniform tính lại; top10MB competitor ranking chọn cùng winner ở cả3orders.
Largest final-check |K32−K8|=2.7706774374802734e-10;top2 gap=2.3486533591299263e-06.

| nu_raw | VA | order | I_AB | SKR | delta_K_from_GH32 |
|---|---|---|---|---|---|
| 0.17000000000000001 | 5 | 8 | 0.48717715517004745 | 0.058733172041549986 | -2.5999924435637922e-11 |
| 0.17000000000000001 | 5 | 16 | 0.48717715519741667 | 0.058733172067550743 | 8.3266726846886741e-16 |
| 0.17000000000000001 | 5 | 32 | 0.48717715519741578 | 0.05873317206754991 | 0 |
| 0 | 1 | 8 | 0.11148258561476077 | 0.0045862012451445694 | -2.7706774374802734e-10 |
| 0 | 1 | 16 | 0.11148258590641102 | 0.0045862015222123131 | 0 |
| 0 | 1 | 32 | 0.11148258590641102 | 0.0045862015222123131 | 0 |

Diagnostic stopping: deltaK1e-8,parameter1e-6;cap6iterations,3boundaryexpansions,4refinement stages. Stopping tolerance không phải total-error bound.
Scientific domainnu>=0,VA>0,nopeak/energy/physical upperbounds. Catalog envelopeMBnu[.05,.8],VA[.025,8];UniformVA[.02,5] chỉ là các điểm đã có. Slice ranges và attempted expansions lưu riêng, không thành physical constraints.
Selected terminal P1 range=[2.0, 6.5],bracket=[4.5, 5.5],status=BRACKETED_EXACT_CATALOG_SOURCE_MISSING.
Selected terminal P2 range=[0.1, 0.8],bracket=[0.165, 0.175],zero endpoint=EXACT_CHECKED,status=BRACKETED_EXACT_CATALOG_SOURCE_MISSING.
Missing points giữ trong missing_exact_source_requests.csv; full candidate/boundary/rejected histories trong AO_iteration_history.csv và trajectoryJSONs. Multistart agreement trên catalog không chứng minh coordinate-local/global continuous optimum.
Source total-error bound chưa được enclosure nghiêm ngặt; AP precision stability chỉ là numerical evidence. Không nới tolerance,clip eigenvalues hoặc đổi Holevo selection để ép convergence.

## I. Preservation và validation

3228 prior protected files hash-verified unchanged;changes=[]. Old modes/cache182/B/C/checkpoints/MI/Holevo/Eq10/Eq20/frozen spec không sửa.
Frozenactual SHA256=df83ea63af3b475ecca03a44d22d3240ab24d695ff0ebef31f0cd6747db78c15;historical expected=561fecc97cdf9967034ffd6865c1605804b624b98f47a091e47f17e520a2a7b1;mismatch giữ như pre-existing promotion blocker.
7 scoped tests CURRENTLY_VERIFIED_PASS. Independent artifact assertions: P2 dùng P1,monotonicity,moment/noise/Eq20,Gamma+iOmega/spectrum,entropy,signedK,budget,GHwinner.
Sau run không còn controller/source/oldC processes. NOT_READY_FOR_PUBLICATION_SCALE_RUNS;oldObjectiveC USER_STOPPED không restart.

## J. Diễn giải và STOP

AO chỉ tối đa hóa Gaussian Zstar diagnostic objective với fading-induced variance bị bỏ theo quyết định user. K dương không tự chứng minh bảo mật cho physical fading channel.
**FINAL STATUS: AO_RESOURCE_LIMITED.** Best exact candidate giữ ở bảng; không gọi local/global convergence khi thiếu exact refinement.
STOP sau result/report. Không26distance/trajectory/cloud/aperture/divergence sweeps,oldC/training/heldout/final-test/publication evaluation,commit/push.

Artifacts: [result](../results/ao_effective_channel_no_fading_noise_reference/optimization_result.json), [comparison](../results/ao_effective_channel_no_fading_noise_reference/comparison.csv), [iteration history](../results/ao_effective_channel_no_fading_noise_reference/AO_iteration_history.csv), [final validation](../results/ao_effective_channel_no_fading_noise_reference/final_validation.json).
Figures SKR_vs_AO_iteration,VA_vs_AO_iteration,nu_vs_AO_iteration: vectorPDF +300dpiPNG. Sourceattempt logs/receipts/full histories/provenance cùng namespace.
