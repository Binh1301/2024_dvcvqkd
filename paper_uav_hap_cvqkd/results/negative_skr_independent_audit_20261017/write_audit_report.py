"""Report the independent audit; no production imports or recalculation."""
import csv,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];out=Path(__file__).parent
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
a=read(out/'independent_audit.json');probe=read(out/'production_probe.json');inputs=read(out/'audit_inputs.json');extra=read(out/'supplemental_independent_checks.json');selfchecks=read(out/'independent_self_checks.json')
assert all(x['status']=='CURRENTLY_VERIFIED_PASS' for x in (a,extra,selfchecks))
r=next(x for x in a['results'] if x['source_id']==0 and x['case']=='reference_fading' and x['detector']=='primary_detector')
t=next(x for x in a['results'] if x['source_id']==0 and x['case']=='reference_fading' and x['detector']=='trusted_detector')
fmt=lambda x: '['+', '.join(f'{v:.17g}' for v in x)+']' if isinstance(x,list) else '—' if x is None else f'{x:.17g}' if isinstance(x,(int,float)) else str(x)
quantities=[('m1','m1'),('mhalf','mhalf'),('eta_f','eta_f'),('Var(sqrt eta)','fading_variance'),('xi_ch','xi_ch'),('m_xi','m_xi'),('Fading excess output','fading_excess_output'),('Channel excess output','m_xi'),('eta_f xi_f','N_eff'),('xi_f','xi_f'),('C','C'),('w','w'),('V','V'),('W_pre','W_pre'),('Z','Z'),('nu_1','lambda_1'),('nu_2','lambda_2'),('Conditional eigenvalues','conditional_eigenvalues'),('S(AB) terms','S_AB_terms'),('S(AB)','S_AB'),('Conditional entropy terms','conditional_entropy_terms'),('Conditional entropy','conditional_entropy'),('chi_BE','chi_BE'),('I_AB','I_AB'),('beta I_AB','beta_I_AB'),('K_raw','K_raw'),('S(B1) upper','Bob_entropy_upper'),('chi_upper=2S(B1) upper','chi_upper'),('Bound margin','chi_bound_margin'),('Complex noise variance','sigma2_complex'),('Variance/real quadrature','variance_per_real_quadrature'),('Gaussian capacity upper','Gaussian_input_capacity_upper')]
reference='| Quantity | Ideal | Trusted(.7,.0135) |\n|---|---:|---:|\n'
for title,k in quantities:reference+='| '+title+' | '+fmt(r[k])+' | '+fmt(t[k])+' |\n'
with (out/'reference_entropy_decomposition.csv').open('w',encoding='utf-8',newline='') as f:
 writer=csv.DictWriter(f,fieldnames=('quantity','ideal','trusted'));writer.writeheader();writer.writerows(dict(quantity=title,ideal=fmt(r[k]),trusted=fmt(t[k])) for title,k in quantities)
max_prod=max(abs(v) for c in a['production_comparisons'] for v in c['residuals'].values())
max_mi=max(abs(x['I_AB']-x['full_2D_GH'][-1]['I_AB']) for x in a['results'] if x['full_2D_GH'])
matres=max(x['details']['AFG_max_difference'] or 0 for x in extra['checks'] if x['name'].startswith('matrix'))
share=r['fading_excess_output']/r['N_eff'];drop_chi=r['chi_BE']-t['chi_BE'];drop_beta=r['beta_I_AB']-t['beta_I_AB'];gain=t['K_raw']-r['K_raw']
text=r'''# Independent Physical Audit of Negative SKR

Ngày2026-10-17. Phạm vi **AUDIT_ONLY**, task d36a98d1. Không sửa production evaluator/config/source, không chạy P1–P3, không commit/push.

**Kết luận:** không phát hiện contradiction entropy vật lý hoặc lỗi MI/Holevo số học tại các điểm đã audit. Hai Holevo reference đều thấp hơn chặn2S(B1). Giả thiết mean eta bậc1e-4 không đúng với cấu hình đang chạy: mean eta hiện tại khoảng.238, W_pre khoảng2.205. Rate âm được giải thích định lượng trong Gaussian surrogate hiện hành; đây chưa là security proof cho protocol DM fading.

**UNVALIDATED_SECURITY_MODEL** và **NOT_READY_FOR_PUBLICATION_SCALE_RUNS** giữ nguyên.

## A. Actual implementation và provenance

### Call graph thực sự chạy

Runner lịch sử scripts/run_trusted_heterodyne_skr.py:45–55 gọi evaluate_candidate cho reference từ đúng config. Probe mới scripts/probe_negative_skr_production.py chạy32 đánh giá có giới hạn, không lấy SKR từ journal. Sys.setprofile ghi lại call graph và entropy returns thật:

1. scripts/probe_negative_skr_production.main -> src/trusted_heterodyne_skr.evaluate_candidate:262 -> evaluate_batch:212.
2. evaluate_batch -> authenticate: scripts/run_ao_effective_channel_no_fading_noise_reference.py:83. Chỉ tải C,w/source metadata đã xác thực, dựng đúng transmitted ensemble.
3. effective_channel:26 tạo m_xi/N/W_pre; receiver:71 tách trusted eta_B,nu_B.
4. trusted_holevo:119 -> symplectic_spectrum:94 và spectral_entropy:111. Production tính S(AB) trừ S(E|Y) qua finite AB purification; khi eta_B<1, đồng thời tạo AFG AppendixA và kiểm tra spectrum. Điều này khác với việc chỉ dùng ideal nu3 cho nonideal receiver.
5. deterministic_mutual_information trong src/cvqkd/mutual_information.py được gọi với implementation=product, GH8/16/32. Không gọi pooled_fading_mixture_MI hoặc Gaussian-input MI. Không gọi _holevo_from_source_moments của mode cũ ở đường này.

[actual_call_graph.json](../results/negative_skr_independent_audit_20261017/actual_call_graph.json) ghi file/function/line/count, kernel arguments và hai entropy production thực sự trả về. Tại ideal, MI kernel nhận T=.16092029098192165, epsilon≈2.4420588998314914. Tại trusted, MI kernel nhận gain²=.11264420368734515 và epsilon adapter≈2.681751659122871. Epsilon adapter bao gồm detector cho riêng likelihood MI, không phải xi_f để dùng lại cho W_pre/Z.

Những số đang audit thuộc mode channel_only_fading_trusted_heterodyne_v1; global production default không được đổi thành mode này. Audit xác nhận evaluator của chính reference được trích dẫn, không suy luận từ việc hàm tồn tại.

### Cache và inputs

Tất cả4 producer hashes trong receipt của task trước và các receipt/report liên quan khớp checkout hiện tại. Hai source payload/C,w, source roster và saved fading moments được đọc từ cache có provenance. Cả hai ensemble hashes còn được tính lại độc lập từ chính p/alpha/VA binary64, không dùng production hash helper. Probe đọc0 cached SKR để tạo32 kết quả mới; hai reference so với artifact trước có residual0 trên I,chi,K,W,Z.

'''
for s in inputs['sources']:
 text+=f"- Source nu_raw={s['nu_raw']}, VA={s['V_A']}: C={s['C']:.17g}, w={s['w']:.17g}; ensemble SHA256 {s['ensemble_hash']}; payload SHA256 {s['source_payload_sha256']}; path {s['source_path']}.\n"
text+=r'''
Không chạy worker C,w/AP mới. Source cache authenticity không được gọi là một lần independent full-support source-moment certification mới.

### Physical inputs và tài liệu thực tế

HAP20000m, UAV1000m, reference44 ở(450,450)m, L=21939.3102292m; D_r=.55m; beam waist=.0986760647169751m; eta_atm=.9082089654181673. Raw A0=.9977339699934346, w_eq=1.312921595852572m, sigma_s=1.0570182137187947m, sigma_R²=.0539620777961657; phase/AO OFF; xi_ch=.0186, beta=.95.

[Hosseinidehaj v1](https://arxiv.org/pdf/2002.03476.pdf), Eq4–7/AppendixA, được kiểm tra từ primary web text. Local2002.03476v1(1).pdf không tìm thấy trong workspace/Downloads. Bản thảo thực có là C:/Users/admin/Downloads/2026__Binh_s_work (38).pdf, SHA2560c60153cb6dcd4f8a3a2e8ecfe0cb245b473463f051837fb46028916eb6be0a0; requested(38)(3).pdf không tìm thấy. Trang3 được render và xem trực quan; các khác biệt homodyne/total-noise vẫn ghi rõ, không coi hai phiên bản là giống nhau. [Denys–Brown–Leverrier2021](https://quantum-journal.org/papers/q-2021-09-13-540/pdf/) Eq11–14 và footnotes11–12 được đối chiếu riêng.

Luật physical hiện hành là active-conditioned0<eta<=1, giữ atom AoA0. Không áp dụng normalization mới. Script audit tự viết PDF trong log eta từ raw parameters và tích phân bằng SciPy, không import physical density/moments helper. Kết quả independent m1=.23790886783673015, mhalf=.40114871429673277; residual so saved moments0 và1.11e-16. Raw active retained mass=.9841173294426485, raw total mass=.9841200272202844; atom P0=.00016985667656141038. Physical conditioned mass1. Các số này xác nhận coherence với luật đang dùng, không chứng minh mô hình đã được hiệu chuẩn ngoài thực địa.

## B. Reference numerical decomposition

Cùng nguồn nu_raw=.17, VA=5.046875 SNU. Bảng dùng ít nhất16 chữ số có nghĩa khi phù hợp. high_precision_decomposition.json lưu arithmetic70 decimal digits; độ chính xác số học không đồng nghĩa70 chữ số chính xác của tham số vật lý.

'''+reference+r'''
### Các số hạng tạo W_pre và Z

'''
text+=f"W_pre = 1 + m1*VA + m_xi = 1 + {r['source_modulation_output']:.17g} + {r['m_xi']:.17g} = {r['W_pre']:.17g}.\n\n"
text+=f"Tương đương W_pre = 1 + eta_f*VA + N_eff = 1 + {r['signal_output']:.17g} + {r['N_eff']:.17g}.\n\n"
text+=f"N_eff = fading {r['fading_excess_output']:.17g} + channel {r['m_xi']:.17g}; fading chiếm{100*share:.12g}% N_eff. Z_signal={r['Z_signal']:.17g}, Z_penalty={r['Z_penalty']:.17g}, Z={r['Z']:.17g}. Source-side2C={r['source_side_Z']:.17g} không bị dùng nhầm làm Z sau kênh.\n\n"
text+=r'''
Không có chi_line/chi_tot/trusted detector trong W_pre hoặc cănZ. Shot noise1 xuất hiện một lần. Fading variance được cộng một lần trong N_eff; regrouping W=1+m1VA+m_xi đã bao gồm nó, không cộng lại fading vào biểu thức này.

### Kiểm tra MI độc lập

Tích phân256-state complex Gaussian likelihood thực hiện trực tiếp ở GH16/32/48. Một implementation khác dùng adaptive quadrature một chiều sau khi tự kiểm tra Cartesian/PMF factorization. Cả hai không gọi production MI. Log-likelihood dùng natural log và chia ln2 đúng một lần.

'''
text+=f"Max difference adaptive/direct2D={max_mi:.17g} bits/use; max production-independent difference trên tất cả đại lượng so sánh={max_prod:.17g}.\n\n"
for i,sa in enumerate(a['source_audits']):
 text+=f"Source{i}: sum p={sa['probability_sum']:.17g}, VA_reconstructed={sa['energy']:.17g}, H(X)={sa['H_X']:.17g}<=8, max PMF reconstruction error={sa['PMF_reconstruction_residual']:.17g}.\n\n"
text+=r'''
Complex likelihood có hệ số1/(pi sigma_c²); tích phân radial độc lập và second moment xác nhận normalization1, E|N|²=sigma_c², Var(ReN)=Var(ImN)=sigma_c²/2. Gain=sqrt(eta_B eta_f), sigma_c²=1+nu_B+eta_B N_eff/2. Vacuum measurement và electronic noise đều chỉ xuất hiện một lần.

Gaussian-input capacity upper là log2(1+SNR) cho một complex use, SNR=eta_B eta_f*(VA/2)/sigma_c². Không có hệ số1/2 bên ngoài log vì cả hai quadrature đều dùng. Hai MI reference nằm dưới capacity với margin tương ứng khoảng4.47e-10 và1.42e-10 bits/use. Với sourceVA=.025, chênh lệch capacity cỡ1e-16 là integration rounding và nhỏ hơn tolerance đã khai báo; không clip MI theo capacity.

## C. Independent physics checks

### Chặn entropy bắt buộc

Cho rho_B1E trước detector và rho_FG trusted độc lập với BE. Thêm ancilla không đổi I(B1FG:E)=I(B1:E). Local measurement/channel và data processing cho chi(Y:E)=I(Y:E)<=I(B1:E). Araki–Lieb cho I(B1:E)<=2S(B1). Với mean displacement0 và covariance W_pre I2, thermal state tối đa entropy tại variance này, nên S(B1)<=g((W_pre-1)/2). Đây là bound cho mọi one-mode state có covariance đó, không cần Bob thực sự Gaussian.

Do đó0<=chi(Y:E)<=2g((W_pre-1)/2), với điều kiện trusted independence/local processing đúng. Audit dùng W_pre trước detector, không dùng V_B2 hoặc variance của dữ liệu heterodyne để tính bound.

| Detector tại reference | Holevo independent | chi_upper | Margin | Kết quả |
|---|---:|---:|---:|---|
'''
for label,x in [('Ideal',r),('Trusted',t)]:text+=f"|{label}|{x['chi_BE']:.17g}|{x['chi_upper']:.17g}|{x['chi_bound_margin']:.17g}|PASS|\n"
text+=r'''
Các hypothesis được đáp ứng ở mô hình covariance đã khai báo: SNU vacuum1; B1 là mode lượng tử trước detector; F,G ban đầu nằm trong Bob, độc lập Eve; beam splitter và heterodyne là local operations. Sự độc lập trusted là giả định protocol, không phải kết luận từ detector measurements trong task này.

### Spectrum, uncertainty và arithmetic

Independent script tính closed symplectic formula từ Delta/D bằng mpmath70dps, đồng thời diagonalize trực tiếp iOmegaGamma; không import symplectic helper production. Γ+iOmega được kiểm tra riêng. Ideal conditional là V-Z²/(W+1), không phải sqrt(V(V-Z²/W)) homodyne. Entropy được in từng mode trước khi cộng/trừ; không nhầm source-side correlation, dấu trừ conditional hoặc log base.

Reference S(AB) chỉ khoảng3.67 và conditional khoảng2.52/2.91, hiệu khoảng1.15/.76; đây không phải cancellation của hai entropy lớn gây ra số âm giả. Kết quả70dps và binary64 đồng ý ở mức1e-14. Ở T0/source nhỏ, residual chi khoảng-1.4e-70 được lưu nguyên; analytic value là0. Audit không clip Holevo để qua bound. Vacuum symplectic factor1 có residual70dps được lưu riêng, chỉ entropy-limit của mode vacuum được dùng.

### Tổng kiểm tra và FAIL

-201 independent checks PASS: PMF/energy, PDF moments, W/Z identities, physicality, entropy bound và so production cho32 cases; vacuum/no-modulation limits.
-5 self-checks PASS: g known values, vacuum spectrum, normalized complex likelihood, bound sensitivity và kiểm tra AST không import production numerical helpers.
-7 supplemental checks PASS: ensemble/payload hashes, ΓAB/conditional AFG matrix ordering, trusted->ideal limit.
-40 physical entropy-bound evaluations PASS:32 source/channel/detector cases,4 exact-vacuum cases và4 joint detector limits. Không có FAIL–HOLEVO_PHYSICAL_ENTROPY_BOUND ở cấu hình hợp lệ đã chạy.

Các FAIL/exception vẫn được báo: lần chạy diagnostic đầu thất bại khi xuất vacuum row do duplicate xi_ch keyword; script/log nằm trong attempts/initial_independent/. Chỉ sửa script audit rồi chạy lại, production không sửa. Sensitivity self-check cố tình ghép m1=.00026407446657 với Holevo reference1.1466: W=1.0013376626085486, upper=.016037567950527874, nên bị expected rejection. Đây là kiểm tra phát hiện input mismatch, không phải FAIL của cấu hình thực. Không nâng tolerance hoặc đổi bound.

### Weak-transmission scaling, cùng source và detector

Mỗi bảng dùng fixed non-fading channel, cùng C,w/VA và xi_ch=.0186. CSV giữ đầy đủ precision; bảng này làm tròn để đọc. T0 analytic MI/chi=0, residual70dps nếu có vẫn lưu trong CSV.

'''
for sid in (0,1):
 for detector in ('primary_detector','trusted_detector'):
  text+=f"Source{sid}, {detector}:\n\n|T|W|Z|I_AB|chi_BE|2S(B1) upper|K_raw|\n|---:|---:|---:|---:|---:|---:|---:|\n"
  for x in a['results']:
   if x['source_id']==sid and x['detector']==detector and x['case'].startswith('fixed_channel_'):
    text+='| '+' | '.join(f'{x[k]:.10g}' for k in ('eta_f','W_pre','Z','I_AB','chi_BE','chi_upper','K_raw'))+' |\n'
  text+='\n'
text+=r'''
Pure-loss fixed T=.25 có W=1+.25VA, no fading. Exact coherent vacuum với VA0,C0,w0 cho MI0; khi channel excess bằng0, Bob vacuum/chi0. Khi channel noise dương, vacuum input có thể cho Bob thermal noise/chi>0 nhưng MI vẫn0, không được giả định chi0 ở noisy channel có T>0. Với VA->0, kiểm tra MI ở.01,.0001,1e-8,0 bằng scaling coherent amplitudes; đó là MI-only limit, không nội suy C,w hoặc tuyên bố thêm exact source vào catalog. Không vi phạm entropy bound trong các case này.

## D. Ideal so với trusted heterodyne

Audit tự khai triển A,F,G covariance blocks và C_AFG,B2 theo AppendixA, không gọi production trusted_holevo hoặc purification. Quadrature order là(q_A,p_A,q_F,p_F,q_G,p_G); Omega=direct sum[[0,1],[-1,0]]. Beam splitter phases được đối chiếu bằng toàn conditional covariance, không chỉ eigenvalues.

'''
text+=f"Max conditional AFG element difference với production={matres:.17g}. Trusted entropy tăng từ{r['conditional_entropy']:.17g} lên{t['conditional_entropy']:.17g}, trong khi S(AB)={r['S_AB']:.17g} giữ nguyên. Holevo giảm{drop_chi:.17g}; beta*MI giảm{drop_beta:.17g}; raw K tăng{gain:.17g}, vẫn âm.\n\n"
text+=r'''
Điều này phù hợp với trusted receiver: một phần thông tin không còn truy cập được bởi Eve, song Bob cũng mất tín hiệu/thêm noise. Không thay ideal nu3 vào nonideal spectrum. Giới hạn eta_B=1-delta,nu_B=delta² với delta từ1e-2 tới1e-8 hội tụ về ideal, bound vẫn PASS; bảng trusted_ideal_limit.csv giữ số. Không có thay đổi detector operating point cho thí nghiệm chính.

## E. Root cause

**Không tìm thấy lỗi arithmetic/noise-accounting hoặc physical entropy contradiction tại reference.** Các biểu thức đang chạy đúng ở src/trusted_heterodyne_skr.py:57 (W=1+m1VA+m_xi),:220 (Z),:81 (complex receiver noise),:171 (S_AB-S_E_cond). Independent MI và Appendix entropy tái lập giá trị âm.

Nguyên nhân định lượng là current m1 và fading spread lớn, tạo output excess chủ yếu từ fading. W_pre lớn hơn1 khoảng1.205, không phải khoảng1e-3. Conditional entropy bị trừ đúng nhưng còn để lại chi lớn hơn beta*MI. Không cần một Holevo vượt2S(B1) để làm K âm.

Nếu dùng m1 bậc1e-4, W_pre và entropy bound sẽ thấp hơn nhiều; ghép những moments đó với Holevo1.1466 là sai input/model identity. Đó là nguồn của nghi vấn không tương thích trong task, không phải phép tính của cấu hình thật. Không suy đoán nguồn gốc các con số minh họa nếu chưa có cùng config/hash.

## F. Security validity

Ba trạng thái phải tách riêng:

| Nội dung | Trạng thái | Phạm vi |
|---|---|---|
| DPI + Araki–Lieb + maximum entropy tại covariance |MATHEMATICALLY_VALIDATED|Dưới các giả thiết B1 quantum/local/trusted independence đã nêu |
| Moment/W/Z algebra, Appendix Gaussian receiver |MATHEMATICALLY_VALIDATED|Declared source-independent phase-tracked fading/constant xi_ch và covariance Gaussian model |
| Reference/boundary numerical MI, spectra/entropy |NUMERICALLY_VALIDATED|Các2 sources/32 cases/giới hạn đã liệt kê |
| Full DM fading key-rate security |SECURITY_PROOF_VALIDATED=False|UNVALIDATED_SECURITY_MODEL |

### Denys constraints: suy ra riêng cho fading

Với input source độc lập fading, phase tracked và E[b|alpha_k]=mhalf*alpha_k, đặt nbar=VA/2. Từ các first/second-moment constraints của Denys, suy ra c1=mhalf*C, c2=mhalf*nbar, nB=m1*nbar+m_xi/2. Do đó nB-c2²/nbar=((m1-mhalf²)VA+m_xi)/2=N_eff/2. Thay vào general Eq13 cho Zlower=2c1-2sqrt(w(nB-c2²/nbar))=2mhalf*C-sqrt(2wN_eff). Đây là derivation từ general constraint, không phải khẳng định Eq14 của Denys viết trực tiếp cho atmospheric fading.

Quan hệ algebra này phù hợp với mô hình và exact C,w đã xác thực. Covariance tại Zlower đã kiểm physicality. Tuy nhiên nguồn thống kê đó được simulator cung cấp, chưa là parameter estimation thực nghiệm. Denys footnotes11–12 còn yêu cầu maximum Holevo trên physical correlation interval khi không có bảo đảm lower endpoint là worst case. Audit này không chứng nhận full-interval optimum hoặc thay security target hiện hành.

Hosseinidehaj covariance/detector analysis được xây dựng trong Gaussian-modulation protocol. MI tính bằng AWGN moment surrogate không phải true pooled-fading mixture MI của nguồn discrete; chưa có lower-bound/error theorem được kiểm chứng cho việc thay thế cụ thể này. Trusted Gaussian conditional entropy khớp toán/số không tự cấp một proof mới cho DM fading. Operational CSI/binning/leakage, attacks, finite-size và composable claims vẫn mở. Passing the entropy upper bound là necessary consistency check, không phải sufficient security certificate hay tightness guarantee.

## G. Recommendation

Không đề xuất sửa công thức production để làm K dương: audit không xác nhận lỗi cần patch ở reference. Thay đổi tối thiểu hữu ích trong một task implementation sau là thêm regression guard chi<=2g((Wpre-1)/2) và Gaussian-capacity check vào diagnostic validation, cùng input/config identity trên mọi bảng; không clip chi/MI khi guard fail.

Ưu tiên khoa học tiếp theo là xác nhận measurement constraints và estimator cho actual fading-mixture MI, kiểm tra worst-case physical Z interval/trusted DM bound trong đúng security scope. Đây là đề xuất, không chạy thêm optimizer/source/22.700 điểm/P1–P3 trong task audit này. Mọi physical redesign hoặc detector tuning phải là nghiên cứu riêng, không sửa đầu vào để cứu dấu SKR.

### Artifacts và bảo toàn

[Independent results](../results/negative_skr_independent_audit_20261017/independent_audit.json), [16-digit reference table](../results/negative_skr_independent_audit_20261017/reference_entropy_decomposition.csv), [all finite cases](../results/negative_skr_independent_audit_20261017/independent_results.csv), [checks](../results/negative_skr_independent_audit_20261017/checks.csv), [high precision](../results/negative_skr_independent_audit_20261017/high_precision_decomposition.json), [source/ordering/limit checks](../results/negative_skr_independent_audit_20261017/supplemental_independent_checks.json).

Chỉ thêm2 scripts chẩn đoán riêng và report/state/evidence artifacts. Không sửa source/evaluator/Cw/config/normalization/security functional/frozen specs hoặc kết quả lịch sử. Không training/test dataset access, publication evaluation, baseline/threshold certification, ObjectiveC restart, external PDF edit, commit/push. Frozen actual hashdf83ea63...78c15 vẫn khác historical hash trong AGENTS, đã giữ nguyên. NOT_READY và ObjectiveC USER_STOPPED không đổi. Audit complete; STOP.
'''
(ROOT/'docs/NEGATIVE_SKR_INDEPENDENT_AUDIT_VI.md').write_text(text,encoding='utf-8')
(out/'NEGATIVE_SKR_INDEPENDENT_AUDIT_VI.md').write_text(text.replace('../results/negative_skr_independent_audit_20261017/',''),encoding='utf-8')
summary=dict(status='CURRENTLY_VERIFIED_PASS',security_status='UNVALIDATED_SECURITY_MODEL',independent_checks=201,self_checks=5,supplemental_checks=7,total_checks=213,physical_entropy_bound_cases=40,physical_entropy_bound_failures=0,max_production_independent_difference=max_prod,max_direct2D_adaptive_MI_difference=max_mi,max_conditional_matrix_difference=matres,reference_ideal={k:r[k] for k in ('m1','W_pre','S_AB','conditional_entropy','chi_BE','chi_upper','I_AB','K_raw')},reference_trusted={k:t[k] for k in ('S_AB','conditional_entropy','chi_BE','chi_upper','I_AB','K_raw')},fading_fraction_of_output_excess=share,production_code_edited=False,source_moments_computed=0,P1_P3_run=False,source_provenance_verified=True,recommendation='No production formula change justified by this reference audit; preserve UNVALIDATED_SECURITY_MODEL')
(out/'audit_summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
print(json.dumps(summary,indent=2))
