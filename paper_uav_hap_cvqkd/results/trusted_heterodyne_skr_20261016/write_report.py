"""Generate the Vietnamese audit from immutable numerical receipts."""
import csv,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];out=Path(__file__).parent
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
ref=read(out/'reference_decomposition.json');verified=read(out/'final_validation.json')
assert verified['status']=='CURRENTLY_VERIFIED_PASS'
old=ref['previous_ideal'];new=ref['corrected_primary'];trusted=ref['trusted_detector_diagnostic']
def fmt(x):
 if x is None:return '—'
 if isinstance(x,list):return '['+', '.join(f'{v:.13g}' for v in x)+']'
 return f'{x:.13g}' if isinstance(x,(int,float)) else str(x)
fields=[('V_A','V_A'),('nu_raw','nu_raw'),('m1=<eta>','mean_eta'),('mhalf=<sqrt eta>','mean_sqrt_eta'),('eta_f','T_eff'),('Var(sqrt eta)','fading_variance'),('m_xi=<eta xi_ch>','m_xi'),('Fading contribution','fading_excess_output'),('Channel excess contribution','channel_excess_output'),('eta_f xi_f','N_eff'),('xi_f','xi_eff'),('C','C'),('w','w'),('V','a'),('W_pre','W_pre'),('Z_star','Z_star'),('nu_1','lambda_1'),('nu_2','lambda_2'),('Conditional eigenvalues','conditional_symplectic_eigenvalues'),('I_AB','I_AB'),('beta I_AB','beta_I_AB'),('chi_BE','chi_BE'),('K_raw','K_raw'),('K_usable','K_usable')]
alias={'m_xi':'m_excess','channel_excess_output':'m_excess','fading_excess_output':'Delta_fad','W_pre':'b'}
rows=[]
for title,key in fields:
 before=old.get(alias.get(key,key))
 if key=='conditional_symplectic_eigenvalues':before=[old['lambda_3']]
 after=new[key];difference=after-before if isinstance(after,(float,int)) and isinstance(before,(float,int)) else None
 rows.append(dict(quantity=title,previous_moment_ideal=before,corrected_primary=after,difference=difference,trusted_diagnostic=trusted[key]))
with (out/'reference_full_comparison.csv').open('w',encoding='utf-8',newline='') as f:
 writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
table='| Đại lượng | Moment ideal trước | Corrected ideal | Chênh lệch | Trusted diagnostic |\n|---|---:|---:|---:|---:|\n'
for r in rows:table+='| '+' | '.join([r['quantity']]+[fmt(r[k]) for k in ('previous_moment_ideal','corrected_primary','difference','trusted_diagnostic')])+' |\n'
audit=read(out/'noise_audit_complete.json')
functions='| Hàm | Quy ước nhiễu / phát hiện |\n|---|---|\n'
for r in audit['root_cause']+audit['additional_functions']:functions+='| '+r['function']+' | '+r.get('noise',r.get('issue',''))+' |\n'
text=r'''# Báo cáo mômen kênh và trusted heterodyne

Ngày 2026-10-16. Hoàn tất implementation và numerical diagnostics của task bb825b02.
**UNVALIDATED_SECURITY_MODEL**. **NOT_READY_FOR_PUBLICATION_SCALE_RUNS**.

## A. Root cause và baseline

Nhánh mới nhất src/fading_effective_skr.py đã dùng đúng channel-only excess noise và ideal heterodyne. Không phát hiện total-noise contamination trong nhánh này. SKR âm trước task không phải bằng chứng có lỗi noise accounting.

Mode lịch sử src/manuscript_literal_3moments.py có lỗi diễn giải: LiteralChannel.moments trả mômen total input-referred noise, effective_channel dùng nguyên nó làm excess noise và eta_f=mean_sqrt_eta thay vì bình phương. Mode literal được giữ nguyên để bảo toàn ý nghĩa kết quả lịch sử. Nhánh effective_channel_no_fading_noise cố ý bỏ fading variance theo mode riêng, không phải corrected fading evaluator.

Khoảng trống chính của nhánh moment-corrected là từ chối nonideal trusted detector. Nó chưa từng chứng nhận việc dùng ideal three-entropy formula cho detector không lý tưởng. Task này thêm evaluator có version riêng, không đổi default hoặc ghi đè cache cũ.

Baseline trước sửa:40 tests PASS, snapshot4042 tệp. JSON chẩn đoán đã bị xóa từ trước vẫn giữ trạng thái đó. startup_manifest.json, baseline_receipt.json và noise_audit.json có trước implementation; bản đồ đầy đủ ở noise_audit_complete.json.

'''+functions+r'''
## B. Mathematical audit

Nguồn: [Hosseinidehaj–Walk–Ralph, arXiv:2002.03476v1](https://arxiv.org/pdf/2002.03476.pdf), Eq4–7/AppendixA; [Denys–Brown–Leverrier, Quantum5,540(2021)](https://quantum-journal.org/papers/q-2021-09-13-540/pdf/).

Đã kiểm tra primary web text Hosseinidehaj v1. Tệp local 2002.03476v1(1).pdf không tìm thấy trong Downloads/workspace; raw download và screenshot không khả dụng. Bản thảo thực tế là 2026__Binh_s_work (38).pdf, SHA256 0c60153cb6dcd4f8a3a2e8ecfe0cb245b473463f051837fb46028916eb6be0a0. Biến thể (38)(3).pdf không tìm thấy, không giả định hai bản tương đương. Trang3 đã xem trực quan: Eq12 likelihood vô hướng, Eq13 conditional homodyne, Eq18/21 dùng total/homodyne noise. Các công thức receiver này không được dùng làm heterodyne default.

\[
m_1=E[\eta],\quad m_{1/2}=E[\sqrt\eta],\quad m_\xi=E[\eta\xi_{ch}(\eta)],\quad \eta_f=m_{1/2}^2.
\]
\[
N_{fad}=(m_1-\eta_f)V_A,\quad N_{ch}=m_\xi,\quad N_{eff}=N_{fad}+N_{ch},\quad \xi_f=N_{eff}/\eta_f.
\]

m_xi là channel excess, không chứa loss vacuum/detector. Với xi_ch constant, dùng m1*xi_ch trực tiếp; không lấy hiệu hai total-noise số lớn. API nhận mômen channel-only độc lập khi xi_ch phụ thuộc eta, từ chối constant xi_ch mâu thuẫn. Khi eta_f=0, xi_f để trống và không gọi MI/Holevo.

\[
W_{pre}=1+\eta_fV_A+N_{eff}=1+m_1V_A+m_\xi,\qquad
Z_*=2m_{1/2}C-\sqrt{2wN_{eff}}.
\]

Hai dạng W_pre được kiểm tra. Vacuum1 chỉ xuất hiện một lần; không đưa chi_line/chi_tot/detector vào W_pre hoặc Z. Không fading khôi phục Z=2sqrt(T)C-sqrt(2T xi_ch w); pure loss T0 trả W_pre1/Z0. C,w và normalization nguồn giữ nguyên. Áp dụng cận Denys vào covariance fading hiệu dụng là giả định ghép mô hình; không gọi đây là công thức fading nguyên văn trong Denys Eq14. Giữ direct Z-minus target, không chứng nhận full-Z interval optimum.

### Receiver và MI

Repo định nghĩa xi_det là output-referred quadrature noise mỗi detected arm; nó khớp nu_B của AppendixA. Tách rõ:

\[
\chi_{het}=(2-\eta_B+2\nu_B)/\eta_B,\quad
\chi_{line}=1/\eta_f-1+\xi_f,\quad
\chi_{tot}=\chi_{line}+\chi_{het}/\eta_f.
\]
\[
Y=\sqrt{\eta_B\eta_f}\alpha+\mathcal{CN}(0,1+\nu_B+\eta_BN_{eff}/2),\quad
V_{B2}=\eta_BW_{pre}+1-\eta_B+2\nu_B.
\]

Đây là effective_gaussian_MI, tích phân discrete-input256-state hai quadrature GH8/16/32, không phải Gaussian-modulation MI. Adapter chuyển đúng gain/noise sang kernel hiện có. Product-QAM factorization có guard. pooled_fading_mixture_MI là estimator khác, không được chạy hay thay thế ở đây.

Ở SNR dưới sqrt(machine epsilon), entropy-difference MI bị cancellation. Dùng expm1/log1p với node +/- của cùng tích phân GH để tránh trừ entropy gần nhau. Không clip MI âm thành0, không thay likelihood. Full-complex/product agreement và low-SNR slope đều PASS.

### Trusted Holevo

Gamma_AB trước detector giữ V=VA+1, W=W_pre và Z từ exact source. Kiểm tra positive covariance, gamma+iOmega và symplectic doublets. Với eta_B<1, auxiliary EPR có upsilon=1+2nu_B/(1-eta_B); beam splitter tạo A,B2,F,G; conditional covariance là gamma_AFG-C(gamma_B2+I)^(-1)C^T. Chi=S(AB)-S(AFG|B2).

Purification độc lập của standard-form AB tạo hai mode Eve; spectrum conditional Eve phải khớp AFG sau khi thêm vacuum eigenvalue. Ở eta_B1/nu_B0 khôi phục a-Z²/(b+1), không chia0/0. Với eta_B1/electronic noise dương, dùng finite purification. Khi eps_machine*upsilon²>1e-10, tránh diagonalize thermal representation ill-conditioned và ghi trạng thái dùng purification tương đương. Không nới tolerance sau kết quả. Vacuum-limit entropy trong allowance1e-10 giữ raw eigenvalues dưới1 ở entropy_roundoff_modes; không clip Z/covariance.

### Physical PDF và normalization

Giữ HAP20000m/UAV1000m, reference44, L_ref21.9393102292km, D_r=.55m, beam_waist=.0986760647169751m và xi_ch=.0186 theo repo. Không hard-code fixture nhỏ của task thay kênh thật.

Luật hiện hành active-conditioned trên0<eta<=1, giữ atom AoA0. Raw Eq10 mass trên[0,1] tại reference=.9841200272202841, active retained mass=.9841173294426483, P0=.00016985667656141038. Conditioning đã có trước task, không phải renormalization mới. Closed forms dùng đúng luật này và khớp quadrature độc lập. Không khẳng định raw Eq19–20 không-normalize bằng moment conditioned. physical_law_audit.json lưu raw mass/tail/normalizer và quadrature errors. Atom0 đóng góp0 vào eta*xi_ch.

## C. Implementation

- src/trusted_heterodyne_skr.py: effective_channel -> receiver -> trusted_holevo; evaluate_batch/authenticate dùng một exact source cho MI và correlation.
- tests/test_trusted_heterodyne_skr.py:14 tests A–K, có Appendix block algebra độc lập, MC và source mutation rejection.
- scripts/run_trusted_heterodyne_skr.py: validate/full/verify, journal/model key version mới, hash-bound inputs/producers và immutable completed stages.
- configs/trusted_heterodyne_skr.json: tham chiếu config thật; primary receiver lấy từ binary config, alternate diagnostic lấy R/xi_det từ corrected config lịch sử.
- docs/TRUSTED_HETERODYNE_SKR_REPORT_VI.md: báo cáo này.

Nguồn đi qua load_sources/authenticate; giữ ensemble hash, nu_raw, C,w và VA=2nbar. Không AP/new source/interpolation. Sau gates mới tính P1 rồi gọi nguyên mission_results/DP. Mọi output mới tách riêng results/trusted_heterodyne_skr_20261016/. Scientific kernels/legacy source và kết quả cũ giữ nguyên.

Dùng .venv-binary-cloud/Scripts/python.exe -X utf8 -B scripts/run_trusted_heterodyne_skr.py --stage validate|full|verify. Namespace hiện tại đã hoàn tất, không chạy lại validate/full vào đó. Resume chỉ cho journal chưa hoàn tất với cùng input/producer identity; startup/test receipts là prerequisite.

## D. Validation

| Nhóm | Kết quả | Bằng chứng |
|---|---|---|
| Baseline trước sửa |40 PASS |baseline_receipt.json |
| A No fading |PASS |eta_f=T, fading0, xi_f=xi_ch |
| B Pure loss |PASS |W_pre1+T VA, T0 vacuum |
| C Moments |PASS |constant/eta-dependent m_xi, rejects invalid inputs |
| D Bob identity |PASS |hai dạng W_pre và unit-test fixture riêng |
| E Detector independence |PASS |kênh/Wpre/Z/Cw không đổi |
| F Ideal heterodyne |PASS |Schur complement và old/new regression |
| G Nonideal trusted |PASS |AppendixA block covariance/purification/receiver limits |
| H Không duplicate noise |PASS |chi_line/chi_tot riêng, normalized complex likelihood |
| I MC moments |PASS |5x65536 physical samples,16 independent blocks,15 checks5SE+1e-10 |
| J Source preservation |PASS |197MB/30Uniform; hashes/VA/Cw; mutation rejection |
| K Physical/numerical |PASS |T0, strong loss, entropy, physicality, low-SNR slope |
| Scoped regression |71 PASS |scoped_tests.log/test_receipt.json |
| Boundary sweep độc lập |166 PASS |VA tới1e-12,100 random physical CMs và vacuum/receiver limits |
| Small set |60 PASS |3 nguồn/họ x5 vị trí x2 detector |
| Full primary/P1–P3 |PASS |final_validation.json |

Boundary sweep max Appendix/purification residual2.4868995751603507e-14. Lỗi ban đầu và cách sửa được giữ ở trusted_tests_initial.log và initial_receiver_probe_failure.json. Không thay tolerance. MC_channel_moments.csv lưu số và SE; analytic moments vẫn là primary.

## E. Numerical decomposition tại reference thật

Cùng nu_raw=.17, VA5.046875 SNU. Primary eta_B1/nu_B0. Diagnostic eta_B.7/nu_B.0135 từ config lịch sử, không đổi primary detector.

'''+table+r'''
\[
N_{eff}=\underbrace{0.3885517238141117}_{(m_1-\eta_f)V_A}
+\underbrace{0.0044251049417631805}_{m_\xi}=0.39297682875587486.
\]

Noise input-referred được in riêng:

| Detector | chi_het | chi_line | chi_tot | V_B2 | Complex noise variance |
|---|---:|---:|---:|---:|---:|
'''
for label,row in [('Primary ideal',new),('Trusted diagnostic',trusted)]:text+='| '+label+' | '+' | '.join(fmt(row[k]) for k in ('chi_het','chi_line','chi_tot','V_B2','sigma2_complex'))+' |\n'
text+='\nLegacy no-fading-variance rawK='+fmt(ref['legacy_no_fading_variance']['SKR'])+'; previous moment ideal và corrected ideal đều khoảng-0.746140527195. Trusted diagnostic vẫn âm. Không điều chỉnh physics/source/noise để ép dương.\n\n'
text+='reference_full_comparison.csv và reference_decomposition.json giữ full precision, spectra và conditional matrices; bảng Markdown làm tròn. Chênh lệch để trống khi đại lượng là một spectrum hoặc field trước không tồn tại.\n\n'
text+=r'''## F. Optimization sau numerical gates

Full primary giữ detector hiện hành, catalog197MB/30Uniform,100 vị trí và cùng cloud/seeds. Tính mới22700 row, không nhập K cũ; source C,w đã xác thực được dùng lại. Không chạy catalog nonideal vì điều đó đổi cấu hình chính.

'''
text+=f"Xác minh độc lập200 P1 maxima,1600 matched missions,7600 Bellman profiles. Max ideal old/new difference={verified['maximum_ideal_regression_difference']:.15g}. Bảo toàn{verified['protected_files']} old files, changed={verified['protected_changes']}.\n\n"
text+='| Source | Maximum raw K trên catalog/lưới | Usable K |\n|---|---:|---:|\n'
for family,value in verified['maximum_raw'].items():text+=f'| {family} | {value:.15g} |0 |\n'
text+=r'''
Tất cả usable rates0; S1–S4 mean SKR/availability/returned distance0. Lambda0 có nhiều feasible paths hòa objective; đứng yên là tie-breaking. Không có mobility gain, unique trajectory hoặc physical energy gain được xác lập. Relative gain so reference0 không xác định. Không suy rộng thành bất khả thi với mọi nguồn/protocol hoặc optimum liên tục.

Cloud NPZ SHA25614aa45add1f1a8828a1dfb9d870c883a150fe8fe820b787dd4050a132b391f35 giữ nguyên. P1 signed catalog argmax, P2 stationary mean, P3 reward S/Nt và lambda*d/Dref, speed/free-initial conventions không đổi. Availability không là objective. Summary/statistics/time-series/trajectory/lambda files mới tách riêng. Không tổng bit khóa khi thiếu channel-use rate.

## G. Security assumptions và trạng thái cuối

Hosseinidehaj trực tiếp hỗ trợ Gaussian-modulation fading covariance và trusted Gaussian detector entropy của protocol trong bài đó. C,w và correlation constraint có nguồn gốc Denys. Kết hợp chúng với Gaussian-surrogate MI cho MB256-state qua fading chưa có theorem/error enclosure được kiểm chứng. Mọi row mới giữ **UNVALIDATED_SECURITY_MODEL**, dù numerical identities PASS.

Không chứng nhận composable/finite-size security, attack class mới, operational yield, tight lower bound cho actual pooled-fading MI, calibrated detector measurements, full-Z worst case hoặc continuous optimum. Trusted modes/noise giả định nằm trong Bob và không truy cập được bởi Eve. Cloud synthetic và DP biết toàn horizon; relocation/reacquisition/source-switch overhead chưa mô hình hóa.

Frozen actual hash df83ea63af3b475ecca03a44d22d3240ab24d695ff0ebef31f0cd6747db78c15 vẫn khác historical hash trong AGENTS, không sửa/restore. NOT_READY_FOR_PUBLICATION_SCALE_RUNS và ObjectiveC USER_STOPPED giữ nguyên. Không đổi frozen specs, source cache/Cw/normalization, production default/security functional, physical law, shared kernels hoặc cloud/DP. Không training/test dataset access, publication evaluation, production baseline/threshold approval, Downloads edit, commit/push.

Implementation/numerical validation hoàn tất; security validation chưa được thiết lập. Deliver và STOP.
'''
(out/'TRUSTED_HETERODYNE_REPORT_VI.md').write_text(text,encoding='utf-8')
(ROOT/'docs/TRUSTED_HETERODYNE_SKR_REPORT_VI.md').write_text(text,encoding='utf-8')
print('REPORT_WRITTEN',len(text))
