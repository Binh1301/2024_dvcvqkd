"""Write Phase D reports and isolated IEEE LaTeX from saved numerical records."""
from pathlib import Path
import csv
import json
import shutil
import re
import numpy as np

OUT=Path(__file__).resolve().parent
BASE=OUT.parent/'phaseC_new_cloud_dp_greedy_stationary_20261025'
METRICS=['average_usable_skr','objective_U','zero_rate_unavailability','total_distance_m']


def read(name):return json.loads((OUT/name).read_text(encoding='utf-8'))
def rows(name,base=OUT):
    with (base/name).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def put(name,text):(OUT/name).write_text(text.strip()+'\n',encoding='utf-8')
def f(x):return f'{float(x):.9g}'
def table(headers,data):return '\n'.join(['| '+' | '.join(headers)+' |','|'+'|'.join(['---']*len(headers))+'|']+['| '+' | '.join(map(str,r))+' |' for r in data])


def main():
    model=read('cloud_mathematical_checks.json');audit=read('winning_source_audit.json')
    paired=rows('paired_algorithm_statistics.csv');index=rows('indexing_summary.csv')
    cov=rows('cloud_validation_metrics.csv');threshold=rows('binary_threshold_validation.csv')
    binary=rows('binary_spatial_correlations.csv');sens=rows('source_sensitivity_evaluations.csv')
    p_lookup={(r['p'],r['baseline'],r['metric']):r for r in paired}
    cloud_text=r'''# Cloud mathematical validation — DIAGNOSTIC_ONLY

The simulation adopts G_n=mu_n+epsilon_n, with independent slot innovations
epsilon_n~N(0,Gamma) and iid per-cell/per-slot mu_jn~Uniform(-1,1).
Gamma_ij=9(0.9)^|i-j| is the conditional covariance, in deterministic row-major
label order. No physical cloud centre, wind velocity or temporal AR is modeled.

## Conditional and unconditional covariance

E[G|mu]=mu and Cov(G|mu)=Gamma. The law of total covariance gives
Cov(G)=E[Cov(G|mu)]+Cov(E[G|mu])=Gamma+I/3, because independent Uniform means
have variance1/3. Hence Var(G_j)=28/3; off-diagonal covariance stays9*.9^lag.
The unconditional G is a Gaussian/Uniform mixture, not a multivariate Gaussian.
Its off-diagonal correlation is (27/28)*.9^lag. Residual epsilon=G-mu is used
to test Gamma, with no re-scaling of the covariance.

The original100 independent Phase C missions are reused, 30 slots each.
For each matrix entry, use the mean known-zero-mean cross product within each
mission, then its between-mission standard error. The <=6SE gate is a finite
diagnostic, not a formally calibrated simultaneous covariance certificate.
The previous512-mission audit remains preserved; it is not rerun.
'''
    cloud_text+=f'\nMinimum eigenvalue: {model["eigenvalue_min"]:.12g}; Cholesky max error: {model["cholesky_max_error"]:.4g}.\n'
    for name in ['conditional','unconditional']:
        a=[r for r in cov if r['test']==name]
        cloud_text+=f'\n{name}: maximum standardized entry error {max(float(r["standardized_error"]) for r in a):.6g}SE; diagonal target {9 if name=="conditional" else 28/3:.12g}.\n'
    cloud_text+='''
## Temporal independence and uncertainty

Code inspection confirms separate PCG64 streams for innovations and means,
both sampled as entire slot-by-cell arrays; there is no prior-field argument
or persistent shared mean. Nonzero-lag covariance is theoretically zero under
these independent-slot assumptions. Known-marginal normalized cross moments
are measured at lags1,2,5,10 for G, epsilon, mu and binary C.
Pointwise95% and Bonferroni95% intervals across these16 temporal comparisons
are both saved. The G lag1 estimate is about-0.01129: its pointwise95%CI
slightly excludes0, while its Bonferroni interval includes0. Do not hide this
pointwise fluctuation or describe it as evidence of a temporal mechanism.
All16 family-adjusted intervals include0. Independence is a property of the
specified generator, not something a correlation test can prove in general.

## Binary thresholds

By symmetry G and-G have the same marginal law, which is continuous, so
P(G>0)=1/2. For calibrated p, integrate the Uniform-mixture survival probability.
An independent80-digit antiderivative of Phi checks the stored thresholds:
P(G>t)=3/2[H((1-t)/3)-H((-1-t)/3)], H(x)=x Phi(x)+phi(x).
No exact per-slot blocked count is imposed. Pointwise sampling intervals use
independent mission means, not300000 supposedly independent cells/slots.
These thresholds and independently resampled means are explicit simulation
conventions; no attribution to Gong/Sanchez Net for these details is made.

'''
    cloud_text+=table(['p','Threshold','Calibration error','Empirical p [mission95%CI]'],[
        [r['p'],f(r['threshold']),f(r['calibration_error']),f"{f(r['mean'])} [{f(r['ci95_low'])},{f(r['ci95_high'])}]"] for r in threshold])
    cloud_text+='''

## Binary spatial correlations

For pair latent residual correlation rho, the joint threshold exceedance
minus p^2 equals the integral from0 to rho of the bivariate normal density,
averaged over the two independent Uniform means. Divide this integral by
p(1-p) to obtain the binary correlation. This Plackett-identity integral is
computed with20/40-point Gauss-Legendre mean quadrature and independent
adaptive integration over rho; agreement is below1e-10. This is a validation
derivation for the supplied cloud law, not a replacement law.
Binary correlations need not equal residual or unconditional G correlations.
At zero threshold, the Gaussian arcsine formula alone is inappropriate after
marginalizing the independent Uniform means. Known-marginal covariance and
pooled Pearson estimates are both saved and explicitly distinguished.

'''
    cloud_text+=table(['Cells (zero-based)','Distance m','Residual rho','Mixture G rho','Predicted binary rho','Empirical binary [95%CI]'],[
        [f"{r['i']},{r['j']}",f(r['distance_m']),f(r['residual_Gaussian_correlation']),f(r['unconditional_G_correlation']),f(r['predicted_binary_correlation']),
         f"{f(r['binary_normalized_covariance'])} [{f(r['binary_ci95_low'])},{f(r['binary_ci95_high'])}]"] for r in binary if r['p']=='0.5'])
    put('cloud_mathematical_validation.md',cloud_text)

    source_text=f'''# Winning-source evidence audit — INSUFFICIENT_EVIDENCE

Exact ensemble: `{audit['ensemble_hash']}`.
Payload: `{audit['source_path']}`.
Payload SHA256: `{audit['source_sha256']}`.
Historical cache key: `{audit['payload_cache_key']}`.
Canonical source identity: `{audit['canonical_source_identity']}`.

VA={audit['VA']!r}, VA_hex={audit['VA_hex']}; nu_raw=0.30,
nu_repo=42.5*nu_raw=12.75; C={audit['C']!r}, w={audit['w']!r}.
The physical ensemble was reconstructed with the existing builder; no moments
were generated. PMF, C4 symmetry, p/alpha hashes and256-state normalization
passed the unchanged validators. VA=2*nbar error={audit['normalization_error']:.4g};
measured quadrature X=2Re(alpha) variance error={audit['homodyne_quadrature_variance_error']:.4g}.

## What is verified and what is missing

The payload declares ARBITRARY_PRECISION_FALLBACK, support_size256 and a
1050/1250/1450 decimal-digit ladder, density tolerance1e-12 and physicality
tolerance1e-10. These are settings/claims, not saved convergence observations.
The hash-bound implementation matches the historical implementation under the
existing LF/CRLF provenance policy; no alias policy is changed in this task.

The persistence path in scripts/run_exact_mb_test2.py (the source cache writer)
extracts C,w,route,support from moments.diagnostics[0], then serializes those
summary fields. It does not persist the worker's complete precision-row
diagnostics. The worker can emit digits, rank/resolved, minimum_eigenvalue,
C and w; the winning payload contains none of those per-precision rows.
No bound residual/error estimate for this exact source is saved in the payload.

This task scanned {audit['scanned_artifacts']} eligible JSON/JSONL/log/text artifacts;
{audit['evidence_matches']} contain the winning ensemble hash or cache key.
The complete matched-path/hash list is winning_source_evidence_matches.csv.
It excludes startup/manifests, held-out/final-test material and this new namespace;
{audit['oversize_artifacts_not_scanned']} files larger than8MB were not read.
Existing Phase B inventory, receipt investigation and Git-evidence scan are
corroboration; copies, cache/ensemble identities and successful later SKR values
do not reconstruct discarded numerical iterations.

No usable identity-bound convergence receipt was recovered from inspected
source/precision artifacts. This is a bounded audit, not a claim that evidence
cannot exist anywhere. Missing receipt does not imply C,w are incorrect.
Classification remains INSUFFICIENT_EVIDENCE. No source job was executed.

## Minimum remaining action

Recover original worker output bound to this exact ensemble/input hashes,
implementation and settings, including the1250/1450 rows, resolved rank,
minimum eigenvalues and C,w differences. If unavailable, independently
authorize the single-source plan in source_recomputation_plan.md. Identity
checks and arbitrary sensitivity perturbations cannot replace that evidence.
'''
    put('winning_source_evidence_audit.md',source_text)
    put('source_recomputation_plan.md',f'''# Separate proposed single-source recovery — NOT_RUN

Requires explicit authorization; no source computation is authorized by Phase D.
Target ensemble `{audit['ensemble_hash']}`, VA_hex `{audit['VA_hex']}`,
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
''')

    sensitivity_rows=[]
    for scenario in dict.fromkeys(r['scenario'] for r in sens):
        a=[r for r in sens if r['scenario']==scenario and r['status']=='CURRENTLY_VERIFIED_PASS']
        sensitivity_rows.append([scenario,len(a),f(min(float(r['delta_K']) for r in a)),f(max(float(r['delta_K']) for r in a)),
            sorted(set(r['source_rank'] for r in a)),sum(float(r['K_raw'])>0 for r in a)])
    put('source_sensitivity_report.md',r'''# Source-moment sensitivity — DIAGNOSTIC_ONLY

These are user-authorized artificial input perturbations, NOT new or approximate
source-moment calculations and NOT certified solver-error bounds.
The primary evaluator correctly rejects perturbed C,w because its source
identity checks would fail (168 expected rejections,14 stored-value passes).
The original guard probe and producer remain in source_sensitivity_provenance_guard_probe/.
No guard is bypassed in the primary evaluator. This separate diagnostic calls
the EXISTING Eq14/Eq13 mathematical component helper at80/110 digits, keeping
cached MI, VA, eta_f and xi_f fixed. It recomputes Z directly; no free-Z search.
It does not claim the perturbed pairs are realizable source moments for the
unchanged physical ensemble. Historical payloads/catalogs remain unchanged.

13 scenarios at14 saved primary contexts:182 component-level rate evaluations,
expanded to1300 position/scenario rows. There are ZERO new channel integrations,
ZERO C,w calculations, no new ensembles and no mission-policy reruns here.

Ranking changes are assessed ONLY by replacing the winning source's rate,
holding the other211 stored candidates fixed. Correlated errors of other
sources are not covered. The tested box is finite and not a convergence proof.

'''+table(['Scenario','Valid contexts','Min delta K','Max delta K','Ranks','Positive contexts'],sensitivity_rows)+r'''

All tested perturbations retain positive SKR at100/100 primary positions and
rank1 against unchanged competitors. Absolute C shifts up to1e-6 produce
about1.814e-6 bits/use rate shifts. Setting w to0 or twice its stored value
changes K by approximately+8.75e-6 or-3.62e-6 bits/use. These finite stress
observations do not bound the unknown numerical error of historical C,w,
and do not justify upgrading INSUFFICIENT_EVIDENCE.
''')

    tests=read('algorithm_tests.json');tie=read('transpose_tie_check.json')
    put('algorithm_correctness_tests.md',f'''# Focused algorithm correctness — {tests['status']}

Reused4 Phase C test methods, called as a unittest suite without executing its
stochastic-audit main. All4 passed. They check covariance/threshold validation,
determinism, greedy future-prefix independence, stay/diagonal moves and DP
against256 full-graph trajectories at3 penalties.

Added3 exhaustive checks on a4-node5-slot NONCOMPLETE predecessor graph,
maximal110m step. Enumerate only feasible sequences, test lambda0/ref/.001.
DP U agrees with maximum exhaustive U to<1e-15. The exact recurrence in
src/uav_mobility.py initializes reward S[:,0]/Nt, adds S[:,n]/Nt and subtracts
lambda*d/Dref, then validates backtracking objective and every speed bound.
Free initial position, no deployment/return charge, stay allowed.
Stationary is the offline maximum mission-average fixed position, distance0.
Greedy reads only current S[:,n], uses the same reward/penalty scaling and
deterministic first-index ties. Its prefix remains unchanged if future S is edited.

All{tests['saved_DP_inequalities']} saved Phase C DP-vs-baseline inequalities
pass; minimum margin={tests['minimum_margin']}. New indexing compares also
check per-instance dominance, immutable common S/C hashes and feasible paths.
The saved NEW paths include four new mappings,100 missions and3p values;
their raw outcomes and backtracking are in indexing_realizations.npz.

## Transpose symmetry and tie ordering

Column labels transpose the centered grid. K and distances are exactly
transpose-invariant. DP's objective and Stationary's rate are bit-exact equal
for all300 coupled row/column mission views. Greedy can choose different tied
physical indices, so its original fixed-index tie convention is not equivariant.
A separate{tie['Greedy_verification_calls']}-call Greedy-only test reorders the
transposed problem into the corresponding label order: maximum absolute U
difference={tie['maximum_abs_U_difference']}. This isolates the observed
Greedy row/column differences as tie-order effects, not a different cloud law.
The original algorithms and baseline outcomes are untouched.
''')

    paired_table=table(['p','Baseline','Metric','Delta mean [paired t95%CI]','Paired bootstrap95%CI','Gain %'],[
        [r['p'],r['baseline'],r['metric'],f"{f(r['mean'])} [{f(r['ci95_low'])},{f(r['ci95_high'])}]",
         f"[{f(r['bootstrap_ci95_low'])},{f(r['bootstrap_ci95_high'])}]",f(r['relative_improvement_percent']) if r['relative_improvement_percent'] else 'N/A baseline=0'] for r in paired])
    index_table=table(['Indexing','p','DP vs Greedy delta U [paired95%CI]','Relative U gain %'],[
        [r['indexing'],r['p'],f"{f(r['mean'])} [{f(r['ci95_low'])},{f(r['ci95_high'])}]",f(r['relative_improvement_percent'])]
        for r in rows('indexing_paired_statistics.csv') if r['baseline']=='Greedy' and r['metric']=='objective_U'])
    summary=rows('summary_comparison.csv',BASE)
    main_table=[]
    for metric in METRICS[:4]:
        row=[metric]
        for a in ['Stationary','Greedy','DP']:
            r=next(r for r in summary if r['geometry']=='centered' and r['case_id']=='new_zero' and r['algorithm']==a and r['metric']==metric)
            row.append(f"{f(r['mean'])} [{f(r['ci95_low'])},{f(r['ci95_high'])}]")
        main_table.append(row)
    report='''# PHASE D RESULT: COMPLETE

**DIAGNOSTIC_ONLY; PHASE_B_STRICT_READY = FALSE.** Hoàn tất các kiểm tra và
phân tích được yêu cầu, không đồng nghĩa có chứng chỉ hội tụ nguồn hoặc bảo mật.
Thực thi ngày 26/10/2026; giữ tên namespace 20261025 đúng yêu cầu.

## Baseline được bảo toàn

Tái dựng đủ 912 dòng summary từ 11.400 bản ghi theo mission của Phase C:
sai khác lớn nhất của mean/SD/SE/CI và các bảng B, primary–secondary đều bằng 0.
Không chạy lại các mission hoặc bản đồ physical layer của thí nghiệm gốc.
Primary: HAP (500,500) m, zenith 0.213–1.918°, 100/100 vị trí clear-sky dương.
Secondary: HAP (11419.65511459133,450) m, zenith 28.856–30.921°, 0/100 dương.
Giữ 100 mission, 30 slot × 20 s, 15 m/s, bước Euclidean tối đa 300 m,
Dref=1000 m và lambda_ref=9.468026677248516e-6 bits/use.
Nguồn, bản đồ SKR và normalization giữ nguyên.

## A. Cloud model validation

Covariance có điều kiện bằng Gamma, vô điều kiện bằng Gamma+I/3;
đường chéo tương ứng bằng 9 và 28/3. Ma trận đối xứng, xác định dương;
Cholesky reconstruction PASS. Max standardized entry errors lần lượt
3.4073 và 3.5825 SE theo cụm mission trên 100 mission đã lưu, dưới ngưỡng
chẩn đoán 6 SE. Đây không phải chứng nhận đồng thời mọi phần tử covariance.

Đã đo temporal lag 1, 2, 5, 10 cho G, epsilon, mu và binary. Không có AR
hoặc mean chung cố định trong generator. G lag 1=-0.0112914 có CI 95% riêng
[-0.0223837,-0.0001990], hơi tách khỏi 0. Khoảng Bonferroni 95% cho nhóm
16 kiểm tra chứa 0; điều này đúng với cả 16 kiểm tra. Giữ nguyên quan sát
hữu hạn mẫu, không ép correlation thực nghiệm bằng 0.

Threshold được xác minh độc lập bằng nguyên hàm ở 80 chữ số; sai khác
calibration nhỏ hơn 1e-12. Zero threshold có xác suất biên lý thuyết 0.5.
Binary spatial correlation được kiểm tra bằng tích phân Plackett cho mixture:
ở p=0.5, lag 1 có residual-Gaussian rho=0.9, mixture-G rho=0.867857,
binary rho≈0.668078; lag 10 tương ứng là 0.348678, 0.336226, 0.218207.
Cặp index 9→10 khi sang hàng vẫn có lag 1 dù cách nhau khoảng 905.5 m.
Xem cloud_mathematical_validation.md và CSV để có CI/sai số đầy đủ.

## B. Algorithm robustness

Baseline zero threshold (p=0.5), mean [CI 95% theo mission]:

'''+table(['Metric','Stationary','Greedy','DP'],main_table)+'''

Phân tích paired dùng 100 mission; không coi 30 slot/mission là 30 mẫu độc lập.
CI Student-t paired là kiểm tra chính; 10.000 bootstrap paired dùng để đối chiếu.
Đây là CI riêng cho từng đại lượng, chưa điều chỉnh đồng thời mọi metric.
Tỷ số các mean dùng đúng chiều tăng U/K hoặc giảm distance/unavailability;
baseline bằng 0 thì báo delta tuyệt đối. Bootstrap tỷ số loại các replicate
có mẫu số bằng 0 và báo số replicate hợp lệ, không tạo tỷ số vô hạn.

Tại p=0.4, delta mean K của DP−Greedy bằng 3.96435e-7; CI paired t 95%
[-6.51912e-7,1.44478e-6],bootstrap[-4.95137e-7,1.52006e-6]:
**lợi ích 0.0499% chưa phân biệt với 0**, không gọi là mức tăng rate đáng kể.
Delta U=6.69501e-6, CI [5.50954e-6,7.88048e-6]; mức giảm quãng đường
665.247 m, CI [599.594,730.900] m: hai lợi ích này rõ trong mẫu đã thử.

Tại p=0.8, U tăng 13.5131%, K tăng 13.4500%, unavailability giảm 68.9796%,
distance tăng 12.0013%. Cả CI paired t và bootstrap cho delta U, delta K,
unavailability và distance đều tách khỏi 0. Đây là đánh đổi tăng di chuyển
để né outage. DP biết mây tương lai offline, Greedy chỉ biết slot hiện tại:
không tách được lợi ích thông tin oracle khỏi phần còn lại của khác biệt.

DP zero mode quan sát 0 slot zero-rate/3000 và 0/100 mission có outage.
Cận trên một phía 95% cho xác suất một mission có ít nhất một outage là
2.9513%. Không dùng giả định 3000 slot độc lập để tạo cận hẹp giả.
Không quan sát outage không có nghĩa xác suất thực bằng 0.

'''+paired_table+'''

## C. Indexing sensitivity

Năm mapping: Row, Column, Serpentine, Random_A (seed 20261026), Random_B
(seed 20261027). Mỗi mapping dùng 100 mission và p=0.4,0.5,0.8, giữ nguyên
vị trí, Kstar, lambda, tốc độ và objective. Trường latent theo label của
Phase C được permutation chính xác sang ô vật lý; Gamma vẫn bằng
9*.9**abs(label_i-label_j). Đây là coupling của cùng 100 base draw,
không phải các dataset độc lập mới.

Row/Column là hai biểu diễn đối xứng qua transpose; K và distance bất biến
chính xác. DP và Stationary có objective bằng nhau bit-exact ở 300 instance
ghép. Greedy phá hòa bằng physical index đầu tiên nên không equivariant.
300 kiểm tra riêng với thứ tự phá hòa được transpose cho sai khác U bằng 0.
Không diễn giải chênh lệch Greedy này thành khác biệt vật lý của cloud law.

'''+index_table+'''

Với random mapping, tương quan mạnh có thể nối các ô vật lý xa/gần tùy ý:
performance và độ lớn lợi ích DP thay đổi. Tại p=0.8, U gain của DP so với
Greedy là 13.51% Row, 13.60% Serpentine, 5.59% Random_A, 7.00% Random_B.
DP vẫn trội U trong các instance đã thử, và CI delta U paired dương ở cả
năm mapping, nhưng độ lớn gain không bất biến với cách đánh index.
Hai permutation ngẫu nhiên không đủ để khái quát mọi mapping hoặc xác định
một mô hình mây vật lý; đây là hạn chế của covariance theo index.

## D. Winning exact-source evidence

Nguồn nu_raw=0.30, VA=1.358333319784304, C=1.067911050328646,
w=5.700303183579203e-10, ensemble b083ac84…eb214.
Identity/hash/settings/PMF/normalization PASS; nu_repo=12.75.
Không phục hồi được receipt gắn với nguồn này theo từng precision.
Cache writer lưu summary C,w/route/support và bỏ các precision diagnostics.
Giữ INSUFFICIENT_EVIDENCE; hash hoặc phép tính SKR đúng không chứng minh hội tụ.

Sensitivity riêng: 13 scenario × 14 context đã lưu = 182 component-rate call.
Giữ MI/effective channel đã lưu, tính Eq14/Eq13 bằng helper nguyên bản ở
80/110 chữ số. Primary evaluator vẫn từ chối C,w không khớp payload;
không tắt provenance guard. Các stress C±1e-10/1e-8/1e-6, w±1%/10%/100%
đều giữ rank 1 và SKR dương ở 100/100 vị trí, với giả thiết chỉ perturb
winner và giữ nguyên 211 nguồn khác. Đây là các đầu vào stress nhân tạo,
không phải sai số solver đã được chứng nhận hoặc chứng minh hội tụ nguồn.
Kế hoạch phục hồi một nguồn được chuẩn bị riêng, chưa chạy.

## E. Manuscript readiness

Đã chuẩn bị bốn subsection IEEE-style bằng LaTeX, không sửa frozen manuscript.
Phần cloud/mobility mô tả các convention đã duyệt; phần results chứa CI,
giới hạn indexing, hình học và giả định thông tin oracle. Phần limitations
nêu rõ mây tổng hợp, không cloud motion, distance chưa phải propulsion energy,
bằng chứng hội tụ nguồn và homodyne/security validation còn thiếu.
Không thêm citation hoặc định lý bảo mật chưa được xác minh.

Canonical PDF cùng SHA f970cd6d… có bốn trang theo PdfReader, gồm trang 4
là references. Metadata “ba trang” trong prose Phase C là sai sót đếm trang;
Phase D ghi đính chính, không sửa PDF hoặc artifact lịch sử. Công thức và
physical results không bị ảnh hưởng. LaTeX đã kiểm tra cấu trúc/nhãn, nhưng
chưa compile IEEEtran vì không có TeX engine trong PATH. Draft sẵn sàng
review nội dung; mathematical/security validation và publication readiness
vẫn chưa đạt.

## F. Execution and preservation

New C,w calculations=ZERO; source job=ZERO; channel integration mới=ZERO.
182 component-only SKR call thành công, gồm 14 lần kiểm tra lại giá trị gốc.
Probe trước đó có 14 stored-value primary call thành công và 168 lần guard
từ chối đúng dự kiến; giữ riêng, không gọi chúng là physicality failures.
Tổng cộng 196 downstream rate evaluation thành công, 168 attempt bị guard từ chối.

Monte Carlo mới: 1200 cấu hình mapping/p/mission × ba thuật toán = 3600 call;
tái dùng 900 baseline algorithm record, không sinh independent cloud draw mới.
Thêm 300 Greedy-only transpose/tie check, chín lời gọi thuật toán trong ba
toy graph mới, và các fixture trong bốn unittest method được ghi nhận riêng.
Bootstrap seed 20261026, 10.000 replicate; mapping seed 20261026/27;
base field seed 20261015, mission ID 0…99.

Bốn unittest method, ba restricted-graph brute-force case, 7600 bất đẳng thức
DP đã lưu, 2400 bất đẳng thức DP mới và 300 transpose Greedy check đều PASS.
Không vi phạm vận tốc; không có perturbation thất bại trong component stage.
Đối chiếu hash 9886 file lịch sử, không có thay đổi. Bằng chứng hội tụ nguồn
chưa phục hồi được là dependency khoa học còn thiếu, không phải failed test.
Xem artifact_integrity_report.md và verification.json cho kiểm chứng cuối.

Mã reproduce_phaseD.py mặc định verify chỉ đọc. Analysis guard ngăn tự động
ghi đè run đã hoàn tất. Reports/figures đọc CSV/NPY/NPZ đã tính;
xem figure_index.md. Giữ PHASE_B_STRICT_READY=FALSE,
UNVALIDATED_SECURITY_MODEL và NOT_READY_FOR_PUBLICATION_SCALE_RUNS.
Không training, test/heldout/publication, sửa frozen/production/cache,
source job hoặc tự động nâng lifecycle.
'''
    # Keep prose readable without changing machine-readable values or math.
    put('phaseD_validation_report_vi.md',report)
    write_tex(p_lookup)
    labels=[]
    for path in OUT.glob('manuscript_*.tex'):
        text=path.read_text(encoding='utf-8')
        assert text.count('{')==text.count('}'),path
        labels+=re.findall(r'\\label\{([^}]+)\}',text)
        assert '\\cite{' not in text
    assert len(labels)==len(set(labels))
    engine=next((shutil.which(x) for x in ['pdflatex','latexmk','tectonic'] if shutil.which(x)),None)
    (OUT/'manuscript_validation.json').write_text(json.dumps(dict(status='DRAFT_STRUCTURE_PASS',
        balanced_braces=True,unique_labels=labels,compiler_available=engine,
        IEEEtran_compilation='NOT_RUN' if engine is None else 'NOT_RUN_DRAFT_FRAGMENTS_ONLY',
        frozen_manuscript_edited=False,security_validation_ready=False),indent=2),encoding='utf-8')


def write_tex(paired):
    put('manuscript_cloud_model.tex',r'''
% DIAGNOSTIC_ONLY draft fragment; author integration required.
\subsection{Spatially Correlated Cloud Blockage Model}
Let $j\in\{1,\ldots,J\}$ index the $J=100$ UAV locations and
$n\in\{1,\ldots,N_t\}$ index equal-duration time slots. We adopt
\begin{align}
 \boldsymbol G_n\mid\boldsymbol\mu_n&\sim\mathcal N(\boldsymbol\mu_n,\boldsymbol\Gamma),
 &\mu_{j,n}&\overset{\mathrm{iid}}\sim\mathcal U(-1,1),\label{eq:phaseD_cloud}\\
 \Gamma_{ij}&=9(0.9)^{|i-j|}.\label{eq:phaseD_gamma}
\end{align}
The means and Gaussian innovations are independently resampled in every
slot; no temporal AR(1) or physical cloud motion is modeled. Row-major
indexing is used. Thus equally spaced horizontal and vertical neighbors
have index separations one and ten, respectively: this model is not
distance-isotropic. Conditional covariance is $\boldsymbol\Gamma$, whereas
the law of total covariance gives
$\operatorname{Cov}(\boldsymbol G_n)=\boldsymbol\Gamma+\boldsymbol I/3$.
As an explicit simulation convention, blockage is
$c_{j,n}=\mathbb I\{G_{j,n}>0\}$, yielding marginal probability $1/2$.
For a prescribed probability $p$, the separate calibrated extension uses
\begin{equation}
 c_{j,n}=\mathbb I\{G_{j,n}>t_p\},\qquad
 \frac12\int_{-1}^{1}\left[1-\Phi\!\left(\frac{t_p-u}{3}\right)\right]du=p.
 \label{eq:phaseD_threshold}
\end{equation}
Here $\Phi$ is the standard normal CDF. These threshold and mean-resampling
conventions are not attributed verbatim to prior references. Complete cloud
blockage gives $S_{j,n}=(1-c_{j,n})K_j^\star$.
''')
    put('manuscript_mobility_optimization.tex',r'''
% DIAGNOSTIC_ONLY draft fragment; existing physical-layer equations unchanged.
\subsection{Mobility-Aware SKR Optimization}
For each physical location $\boldsymbol q_j$, the approved v43 evaluator
is evaluated at its actual zenith angle, using the same finite historical
catalog $\mathcal C$ of 212 compatible source ensembles:
\begin{equation}
 K_j^\star=\left[\max_{(\nu_{\rm raw},V_A)\in\mathcal C}
 K_j(\nu_{\rm raw},V_A)\right]^+ .\label{eq:phaseD_catalog}
\end{equation}
The previously computed $C,w$ and the direct manuscript Eq.~(14),
discrete-input homodyne MI, and manuscript Holevo expressions are preserved.
No interpolation or new source-moment calculation is performed.
For a trajectory $j_1,\ldots,j_{N_t}$, define
\begin{equation}
 U=\frac1{N_t}\sum_{n=1}^{N_t}S_{j_n,n}
 -\frac{\lambda}{D_{\rm ref}}\sum_{n=2}^{N_t}d_{j_{n-1},j_n},\quad
 d_{ij}=\|\boldsymbol q_i-\boldsymbol q_j\|_2 .\label{eq:phaseD_objective}
\end{equation}
Feasible transitions satisfy $d_{ij}\le v_{\max}\Delta t$; staying is
allowed, the initial position is free, and no terminal-return cost is used.
The offline Stationary benchmark selects the location maximizing
$N_t^{-1}\sum_n S_{j,n}$. Greedy starts at $\arg\max_j S_{j,1}$ and
subsequently maximizes $S_{j,n}/N_t-\lambda d_{j_{n-1},j}/D_{\rm ref}$
over feasible current locations, without future blockage information.
With full offline knowledge, DP initializes $F_1(j)=S_{j,1}/N_t$ and uses
\begin{equation}
 F_n(j)=\frac{S_{j,n}}{N_t}+\max_{i:d_{ij}\le v_{\max}\Delta t}
 \left[F_{n-1}(i)-\frac{\lambda d_{ij}}{D_{\rm ref}}\right].
 \label{eq:phaseD_dp}
\end{equation}
Backpointers recover a feasible maximizer. All methods share the same
$S$, grid and constraints; DP maximizes this finite-instance objective,
which does not require it to maximize every individual performance metric.
''')
    put('manuscript_numerical_results.tex',r'''
% DIAGNOSTIC_ONLY; paired intervals are pointwise exploratory intervals.
\subsection{Numerical Results and Discussion}
The centered primary geometry places the HAP at $(500,500)$ m and 20 km
altitude, above a 1 km square containing a 10-by-10 UAV grid at 1 km altitude.
The zenith angles range from $0.213^\circ$ to $1.918^\circ$; all 100 locations
have positive diagnostic clear-sky rates, ranging from $7.86230\times10^{-4}$
to $7.95966\times10^{-4}$ bits/use. The catalog winner is
$(\nu_{\rm raw},V_A)=(0.30,1.358333319784304)$ throughout the grid.
The historical off-center geometry has no positive clear-sky location.
We reuse 100 paired 30-slot missions, with $\Delta t=20$ s,
$v_{\max}=15$ m/s, $D_{\rm ref}=1000$ m and
$\lambda=9.468026677248516\times10^{-6}$ bits/use.

At calibrated $p=0.4$, the DP-minus-Greedy mean-rate difference is
$3.96435\times10^{-7}$ bits/use, with paired 95\% Student-$t$ interval
$[-6.51912\times10^{-7},1.44478\times10^{-6}]$.
A 10000-replicate paired mission bootstrap also includes zero. Therefore
the $0.0499\%$ rate difference is not statistically resolved in this sample.
The objective increase is $6.69501\times10^{-6}$ bits/use
(95\% interval $[5.50954,7.88048]\times10^{-6}$), and mean travel distance
decreases by $665.247$ m (95\% interval $[599.594,730.900]$ m).
At $p=0.8$, DP increases mean objective and rate by $13.513\%$ and $13.450\%$,
reduces unavailability from $16.333\%$ to $5.067\%$, and increases distance
by $12.001\%$. The corresponding paired intervals exclude zero.
These gains include the value of future blockage information available
to the offline DP oracle, which is unavailable to Greedy.

No DP zero-rate slot was observed at $p=0.5$ across 3000 slots in 100 missions.
This does not establish zero risk: the one-sided 95\% upper bound for the
probability of a mission containing any outage is $2.9513\%$ under independent
missions. We do not treat the optimized slots as independent Bernoulli trials.

Indexing robustness uses the same latent draws and physical rate map for
row-major, column-major, serpentine and two fixed random permutations,
with 100 paired missions at each of $p=0.4,0.5,0.8$.
Row/column cloud laws are transpose-equivalent on this centered grid;
their DP and Stationary objectives agree exactly. Greedy differences
disappear under transpose-equivariant tie ordering. Other assignments
change physical correlation patterns: at $p=0.8$, DP's objective advantage
over Greedy is $13.51\%$ for row-major, $13.60\%$ for serpentine, and $5.59\%$
and $7.00\%$ for the random assignments. Thus finite-instance objective
dominance persists, while gain magnitude is sensitive to arbitrary indexing.
''')
    put('manuscript_limitations.tex',r'''
% Diagnostic conclusions require separate source/security validation.
\subsection{Limitations}
The cloud field is synthetic and correlated by cell index, with no
distance-isotropy or temporal cloud motion. Threshold calibration and
independently resampled means are simulation conventions. Only two random
index assignments are tested; they do not characterize every permutation.
DP is an offline oracle with future blockage knowledge, and Stationary
is also selected offline; the comparison does not establish online gains.
Travel distance is a mobility surrogate rather than a calibrated propulsion
energy model. Mission-level intervals are pointwise and quantify synthetic
cloud variation, not physical-channel or source-moment uncertainty.
The winning historical source remains \texttt{INSUFFICIENT\_EVIDENCE} for
numerical convergence. Identity/normalization checks and arbitrary moment
perturbations do not certify its error; the finite catalog is not a continuous
global optimum. No new exact source calculation is performed. The security
model, homodyne-related consistency, fading protocol and operational key
aggregation require separate validation. Consequently these are
\texttt{DIAGNOSTIC\_ONLY} rate-function calculations, not independently
certified secure key rates or publication-ready security conclusions.
''')


if __name__=='__main__':main()
