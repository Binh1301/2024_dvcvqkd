"""Vietnamese audit and manuscript corrections from saved evidence only."""
import ast
import csv
import difflib
import hashlib
import json
from pathlib import Path

OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
def read(name):return json.loads((OUT/name).read_text(encoding='utf-8'))
def rows(name):
    with (OUT/name).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def fmt(x):
    if x is None or x=='':return '—'
    if isinstance(x,(bool,str)):return str(x)
    return f'{x:.12g}'
def table(headers,data):
    return '| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+''.join('| '+' | '.join(fmt(x) for x in row)+' |\n' for row in data)+'\n'
def write(name,data):
    fields=list(dict.fromkeys(k for row in data for k in row))
    with (OUT/name).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(data)


def main():
    if (OUT/'final_receipt.json').exists():raise FileExistsError('Preserve sealed audit')
    validation=read('validation.json');comparison=read('comparison_receipt.json')
    oldnew=rows('old_vs_new.csv');conv=rows('detector_convention_comparison.csv');source=rows('source_normalization.csv')
    raw=read('channel_pdf_audit.json')['contexts'];raw_results=read('raw_manuscript43_results.json')
    plane=rows('classical_quantum_plane_checks.csv');notation=read('notation_findings.json');rician=rows('Rician_product_checks.csv')
    source0=next(x for x in source if x['family']=='MB' and float(x['VA'])==5.475 and float(x['nu_raw'])==.165)
    parameters=[]
    for record in read('historical_regressions.json')['records']:
        if record['label']=='original_manuscript_trial8':continue
        value=record['saved']
        parameters.append(dict(scenario=record['label'],**{k:value[k] for k in [
            'D_r','h_hap_km','h_uav_km','zenith_deg','L_km','divergence_urad','jitter_urad',
            'sigma_h_m','eta_det','epsilon_det','VA','nu_raw','tau_zen','treatment','ensemble_hash']}))
    write('scenario_parameters.csv',parameters)
    paramtable=table(['Scenario','Dr(m)','HAP/UAV(km)','ζ(°)','L(km)','Full div(µrad)','Jitter(µrad)','Center SD(m)','ηdet','εdet','VA','νraw'],
        [[x['scenario'],x['D_r'],str(x['h_hap_km'])+'/'+str(x['h_uav_km']),
          *[x[k] for k in ['zenith_deg','L_km','divergence_urad','jitter_urad','sigma_h_m','eta_det','epsilon_det','VA','nu_raw']]]
          for x in parameters])
    noise=[]
    for context in raw:
        for efficiency in [.8,.85,.9,.95]:
            for electronic in [.0135,.005]:
                for definition,xd in [('A_epsilon_over_eta',electronic/efficiency),
                                      ('B_chi_hom',(1-efficiency+electronic)/efficiency)]:
                    for extension in ['limit','active_only']:
                        closed_mass=context['M0']-(context['P0'] if extension=='active_only' else 0.)
                        direct_mass=context['direct']['0.0']['value']+(context['P0'] if extension=='limit' else 0.)
                        closed=.0186*context['m1']+xd*closed_mass
                        direct=.0186*context['direct']['1.0']['value']+xd*direct_mass
                        residual=direct-closed
                        assert abs(residual)<2e-10
                        noise.append(dict(scenario=context['context'],eta_det=efficiency,epsilon_det=electronic,
                            xi_det_definition=definition,xi_det=xd,outage_extension=extension,
                            closed_noise_moment=closed,direct_noise_moment=direct,residual=residual,
                            method='LINEAR_COMBINATION_OF_INDEPENDENT_ZEROTH_AND_FIRST_PDF_QUADRATURES',
                            raw_PDF_normalization_status=context['normalization_status']))
    write('noise_moment_checks.csv',noise)
    extra=[]
    for rel in ['src/channel/fso_channel.py','src/channel/geometry.py','src/channel/turbulence.py',
        'src/channel/scintillation.py','src/channel/pointing_error.py','src/channel/aoa.py',
        'src/channel/atmospheric_loss.py','src/cvqkd/secret_key_rate.py','src/modulation/joint_ps_gs.py']:
        path=ROOT/rel;assert path.exists()
        tree=ast.parse(path.read_text(encoding='utf-8-sig'))
        extra.append(dict(path=rel,role='Production channel/source/rate caller; frozen behavior preserved',status='LOCATED',
            symbols=';'.join(f'{n.name}:{n.lineno}' for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))),
            sha256=sha(path),modified=False))
    mapping=rows('repository_inventory.csv')+extra;write('repository_map.csv',mapping)
    write('production_call_sites.csv',extra)
    variants=dict(A_historical=dict(implementation='preserved original modules; fresh matching regressions',historical_files_modified=False),
        B_literal_v43=dict(xi_det_definition='REQUIRED_EXPLICIT_A_B_OR_INDEPENDENT',printed_complex_mean_density='FAILED',SKR=None),
        B_real_projection_diagnostic=dict(change='Re(alpha) explicitly applied; original noise/covariance convention retained',physically_interchangeable_with_C=False),
        C_physical_homodyne_untrusted=dict(implementation='audit_model.evaluate_physical',measurement='homodyne_1D',
            T_quantum='eta_det*mean_sqrt_eta**2',N_post='eta_det*((m1-mh**2)*VA+.0186*m1)+epsilon_det',
            Gaussian_component_numerically_validated=True,raw_PDF_normalization_guard=True,secure_default=False),
        production_default_changed=False,recommended_secure_default=None,source_cache_namespace_changed=False)
    (OUT/'variants.json').write_text(json.dumps(variants,indent=2)+'\n',encoding='utf-8')
    selected_conv=[x for x in conv if x['scenario']=='baseline8' and float(x['eta_det'])==.8 and float(x['epsilon_det'])==.0135]
    convtable=table(['Biến thể','ηdet','εdet','ξdet / định nghĩa','Outage extension','Gain² MI','Variance MI','MI','Holevo','K / trạng thái'],
        [[x['model'],x['eta_det'],x['epsilon_det'],
          (x.get('xi_det_definition') or '')+(' = '+x['xi_det'] if x.get('xi_det') else ''),
          x.get('outage_extension') or 'physical output',
          x.get('effective_MI_signal_gain2'),x.get('noise_variance'),
          x.get('I_AB'),x.get('chi_BE'),x.get('K_raw') or x['status']] for x in selected_conv])
    oldtable=table(['Scenario / cùng law lịch sử','MI cũ','MI Gaussian','Holevo cũ','Holevo mới','K cũ','K mới'],
        [[x[k] for k in ['scenario','Legacy_MI','Corrected_MI','Legacy_Holevo','Corrected_Holevo','Legacy_SKR','Corrected_SKR']] for x in oldnew])
    pdftable=table(['Scenario','M0','Khối lượng η>1','Eη','E√η','Chuẩn hóa ≤1e-10','K theo PDF gốc'],
        [[x['context'],x['M0'],x['raw_upper_tail_mass'],x['m1'],x['mh'],x['normalization_status'],
          next(v.get('K_raw') for v in raw_results if v['scenario']==x['context'])] for x in raw])
    sources=table(['Nguồn','VA cache','n̄','E[X]','E[X²]','Var(X)','n̄/2 theo PDF'],
        [[x['family']+' ν='+x['nu_raw'],*[x[k] for k in ['VA','nbar','mean_X','second_X','variance_X','manuscript_nbar_over2']]]
         for x in source if x['ensemble_hash']==source0['ensemble_hash'] or (x['family']=='MB' and float(x['nu_raw'])==.25 and float(x['VA'])==1.6249995399703647)
         or (x['family']=='Uniform' and abs(float(x['VA'])-1)<1e-12)])
    symbolmap=table(['Tệp / nhóm','Vai trò','Hàm : dòng'],[[x['path'],x['role'],x.get('symbols','')] for x in mapping])
    old_A=next(x for x in oldnew if x['scenario']=='receiver28p1');old_C=next(x for x in oldnew if x['scenario']=='receiver30')
    baseline_plane=plane[0]
    body=rf'''# Audit HAP–UAV DM-CV-QKD theo manuscript43 — 2026-10-23

**Đã hoàn tất audit và patch cô lập; chưa có mô hình secure-SKR được phê chuẩn làm default.** Có {validation['unit_tests']} unit tests đạt, 10 regression lịch sử khớp và 233 nguồn exact được kiểm tra. Ba trong chín context của PDF gốc không đạt mass tolerance đã đặt trước. Không sửa PDF, nguồn exact, cache, production evaluator hoặc đặc tả frozen.

Phạm vi dùng **homodyne một quadrature thực, reverse reconciliation, detector untrusted**. Các kết quả mới không có finite-key/composable-security claim. audit_model.py, protocol.json, variants.json và isolated_code_patch.diff là patch riêng trong thư mục này; branch cũ được giữ nguyên. Code mới từ chối nguồn/cache không đúng identity, PDF mất chuẩn hóa, covariance không vật lý và variance sai miền.

Ứng viên 28,1 cm trước đây có K={old_A['Legacy_SKR']} từ **actual pooled fading MI**. Khi giữ đúng channel moments, nguồn và Holevo đó nhưng dùng **Gaussian effective MI** theo yêu cầu hiện tại, K={old_A['Corrected_SKR']}, tức âm. 30 cm vẫn có K={old_C['Corrected_SKR']} trong **random-width surrogate lịch sử**; không được chuyển con số này sang PDF log-normal của bản43. Không thực hiện tối ưu mới để khôi phục dấu dương.

## 1. Tệp, phương trình và phạm vi sửa

Nguồn PDF: inputs/manuscript_v43.pdf, SHA256 {read('pdf_capture.json')['manuscript_sha256']}, bốn trang. Trang2 chứa Eqs.(1)–(8); trang3 chứa Eqs.(9)–(21); trang4 là tài liệu tham khảo. Các PNG trang2–4 đã được kiểm tra trực quan. PDF gốc ở Downloads và bản sao đầu vào không bị chỉnh sửa.

Bảng tham số dùng để tái đánh giá các điểm cố định nằm dưới đây và trong scenario_parameters.csv. Cùng λ=1550nm, β=.95, ξch=.0186, τzen=.92. Baseline giữ full divergence233µrad và jitter15.61µrad. Grid detector riêng cho hai geometry8cm là ηdet={{.8,.85,.9,.95}}, εdet={{.0135,.005}}; bảng này ghi detector của từng điểm lịch sử, không thay thế grid đó.

{paramtable}

| Vấn đề | Bản43 | Repo thực tế | Kết luận / patch |
| --- | --- | --- | --- |
| Modulation | Sau(3): Vmod=n̄/2 | Normalization VA=2n̄ | Bản thảo lệch hệ số4 so với X=2Reα; giữ nguồn/caches |
| MB | γ ở tử, ν ở Z; norm của chỉ sốk | PMF centered; νrepo=42,5νraw | Thiếu định nghĩa/notation; giữ PMF hiện có |
| MI | Gaussian1D dùng αphức trong modulus | Production frozen heterodyne; diagnostic có cả2D/1D | Dùng Reα trong patch; không ghép MI2D với Holevo homodyne |
| Detector | ξ=ξch+ξdet/η | Nhiều biến ξdet/εdet/R ở các namespace | Giữ ηdet/εdet riêng; explicit A/B/independent |
| Noise | σ²=1+ηfξf | Recent untrusted helper đã có Npost đúng | C giữ đúng signal/loss/noise; B giữ literal để audit |
| Holevo | ν3 homodyne; T=ηf | Production heterodyne; recent helper homodyne/full-Z | C dùng Ttotal=ηdetηf cùng Npost trong Z,Γ,χ |
| PDF | Eq.(10), moments trên[0,1] | Raw literal, conditional-active và random-width riêng | Không thay law cho nhau; fail closed trên mass lỗi |

repository_map.csv ghi đường dẫn, hàm:dòng và hash của {len(mapping)} tệp. production_call_sites.csv bổ sung chín caller/channel/source file vào inventory gốc28 tệp. Đây không phải tuyên bố đã chạy toàn bộ pipeline cũ.

## 2. Nguồn, Vmod và MB

Đặt \(X_k=2\operatorname{{Re}}\alpha_k\), \(P_k=2\operatorname{{Im}}\alpha_k\), vacuum variance1. Với ensemble centered/C4:

\[
\operatorname{{Var}}X=\operatorname{{Var}}P=2\sum_kp_k|\alpha_k|^2=2\bar n=V_A.
\]

Vì vậy sửa Vmod=n̄/2 thành Vmod=2n̄ nếu giữ quadrature này. Không sửa VA, amplitude hoặc C,w của cache để khớp phương trình sai. source_normalization.csv kiểm tra đủ233 nguồn:

{sources}

Raw centered indices là \(u_i=i-7.5\). Nguồn hiện có dùng \(p_{{ij}}\propto\exp[-\nu_{{raw}}(u_i^2+u_j^2)]\); canonical constellation có mean energy42,5 nên \(\nu_{{repo}}=42.5\nu_{{raw}}\). Với physical energy \(|\alpha|^2=\Delta^2(u_i^2+u_j^2)\), \(\nu_{{phys}}=\nu_{{raw}}/\Delta^2\). Đây là đổi biến của cùng PMF.

Nếu γ vàν khác nhau, tử/mẫu(2) không bảo đảm tổng1. Fixture γ=.165/ν=.25 cho tổng {notation['literal_probability_sum']:.12g}; đây là counterexample, không phải giá trị được suy đoán cho manuscript. Khi γ=ν, weighting bằng i²+j² chưa centered vẫn cho meanα≠0; MB_notation_checks.csv ghi cụ thể. Cache cũ không dùng được dưới PMF thay đổi đó.

## 3. Detector và bốn mặt phẳng tham chiếu

Đặt \(m_1=\langle\eta\rangle\), \(m_h=\langle\sqrt\eta\rangle\), \(T_f=m_h^2\), \(N_f=(m_1-T_f)V_A\), \(N_c=m_1\xi_{{ch}}\).

| Mặt phẳng | Mean homodyne | Variance noise Gaussian hiệu dụng | Vai trò |
| --- | --- | --- | --- |
| Alice | Xk=2Reαk | Vacuum1 | Classical displacement variance VA=2n̄ |
| Channel output trước detector | √Tf Xk | 1+Nf+Nc | Detectorloss chưa tác động |
| Physical detector output YB | √(ηdet Tf) Xk | 1+ηdet(Nf+Nc)+εdet | Plane quantumΓ trongC |
| Classical Y′=YB/√ηdet | √Tf Xk | 1/ηdet+Nf+Nc+εdet/ηdet | MI invariant; Γ lượng tử giữ nguyên |

Với \(Y_B=\sqrt{{\eta_{{det}}}}Y_{{ch}}+\sqrt{{1-\eta_{{det}}}}V_0+E_{{el}}\), vacuum cộng thành \(\eta_{{det}}+(1-\eta_{{det}})=1\). Không thêm loss vacuum lần nữa vào output excess. C dùng

\[
T_{{total}}=\eta_{{det}}T_f,\quad
N_{{post}}=\eta_{{det}}[(m_1-T_f)V_A+m_1\xi_{{ch}}]+\epsilon_{{det}},\quad
\sigma^2_{{N,B}}=1+N_{{post}}.
\]

ConventionA là \(\xi_{{det}}=\epsilon_{{det}}/\eta_{{det}}\): v42 vàv43 trùng đại số ởη>0 nếu chuyển tham số đúng. ConventionB là \(\chi_{{hom}}=(1-\eta_{{det}}+\epsilon_{{det}})/\eta_{{det}}\), có cả loss vacuum trong noise budget quy về trước detector; không phải electronic excess đơn thuần.

**Nếu M0=1, literal σ² với conventionB đúng bằng variance của classically rescaled measurement, nên MI có thể trùngC.** Nhưng dùng Wrescaled như quantum variance với vacuum/CCR cũ và áp lạiZ không phải phép đổi biến cổ điển hợp lệ cho Holevo. Baselineη=.8/ε=.0135: MI lệch {float(baseline_plane['MI_difference']):.4g}, nhưng Holevo lệch {float(baseline_plane['Holevo_difference']):.12g}. classical_quantum_plane_checks.csv kiểm tra đủ16 detector/context pairs. Manuscript chưa chọn A/B/independent; independent chưa có giá trị nên BLOCKED.

Tham khảo receiver/noise framework trong [Laudenbach et al.](https://arxiv.org/pdf/1703.09278). Các plane equations ở đây được suy ra trực tiếp từ loss/vacuum, không dùng Gaussian-modulation SKR thay DM source bound.

## 4. MI homodyne và conditional variance

Patch tính discrete-input MI với real mean \(2\sqrt{{T_{{total}}}}\operatorname{{Re}}\alpha_k\). Tổng256 labels bằng marginal16 levels vì cùng Reα cho cùng density. Không nhân MI lên2; entropy measured quadrature≤4bit/use. \(\frac12\log_2(1+T_{{total}}V_A/\sigma_N^2)\) chỉ là Gaussian reference bound.

Với complex mean như bản in vày∈R, conditional mass là \(\exp[-2\eta_f(\operatorname{{Im}}\alpha_k)^2/\sigma_\xi^2]\), khác1. B-as-printed có MI/Holevo/SKR unavailable. B_real_projection_diagnostic sửa mean thành Reα và giữ noise/covariance literal để so sánh; không phải nguyên density in trong PDF.

Fading thực cho \(\operatorname{{Var}}(Y_B\mid X=x)=1+\eta_{{det}}m_1\xi_{{ch}}+\epsilon_{{det}}+\eta_{{det}}(m_1-T_f)x^2\), phụ thuộc symbol. C thay x² bằngVA để tạo **moment-matched Gaussian approximation**, không phải exact fading likelihood. Unconditional Bob variance là \(b=\sigma_N^2+T_{{total}}V_A=1+\eta_{{det}}m_1(V_A+\xi_{{ch}})+\epsilon_{{det}}\), khác conditional noise. Đổi actual pooled MI thành Gaussian MI có thể đổi SKR dù noise/Holevo không đổi.

Unit tests kiểm tra conditional normalization, finite/nonnegative MI trong tolerance, T→0, entropy≤4, X/P symmetry,256/16 equality, adaptive quadrature, invertible scaling, source tampering, noise planes, covariance và low-T stability. Các số nằm trong conditional_pdf_normalization.csv, MI_independent_checks.csv, unit_tests.json và focused_independent_checks.csv. Raw negativeK giữ nguyên.

## 5. PDF, outage và ba moments

Giữ Eq.(10), closed forms(18)–(19). channel_moment_checks.csv đối chiếu closed form với direct integration đổi biếnη=exp(y) trên[0,1]; atomP0 cộng riêng ởpower0. Residuals đạt tolerance đã đặt trước.

{pdftable}

M0=P0+P1 C1 Q(χ²). Zero-limit extension \(g(0)=\lim_{{\eta\to0}}\eta\xi(\eta)=\xi_{{det}}\) cho Eq.(20) là \(\xi_{{ch}}m_1+\xi_{{det}}M_0\). Active-only cho \(\xi_{{ch}}m_1+\xi_{{det}}(M_0-P_0)\). Chênh lệch ξdetP0; không phải conditioning lại PMF. C giữ electronics trên mọi transmitted use; gating/postselection là protocol khác.

noise_moment_checks.csv đối chiếu đủ288 tổ hợp context/detector/ξdet/outage. Direct noise integral được lấy bằng linearity từ các quadrature độc lập của moment0 và1 đã lưu; atom0 cộng riêng theo extension. Đây là kiểm tra moment nhiễu, không phê chuẩn các PDF mất mass và không chạy lại MI/Holevo.

40/55cm mất mass do lognormal gain unbounded trong khi tích phân chỉ tới1. 30cm hơi vượt1e-10 nên vẫn bị chặn; không nới tolerance vì gần ngưỡng. 28,1cm mất3,34e-12, được chấp nhận trong tolerance nhưng residual/tail vẫn lưu. Không renormalize, chuyển tail sang outage, clipping hoặc thêm atomη=1. Raw-PDF C cho40/55/30cm có K unavailable, không phải0.

**Rician:** Eq.(10) khớp product lognormal×pointing ởρ=0. Vớiρ≠0, untruncated moments từ Eq.(8) cho counterexample:ρ=.5m/power1 tại fixture baseline có lệch {100*float(rician[-1]['relative_Eq10_difference']):.6g}%. Rician_product_checks.csv ghi analytic Laplace/directRice checks. Đây là whole-support supplementary check, không thay truncated moments ở trên. Manuscript cần nêu approximation/domain hoặc derivation choρ≠0.

Eq.(5) dùng lnIa∼N(−v/2,v). Code dùng rawRytov làmv dưới weak-turbulence approximation. turbulence_variance_checks.csv xác nhận mass1,E[Ia]=1,E[Ia²]=exp(v). Log-amplitude variance=v/4. Không đổi atmospheric model hoặc lẫn rawRytov/aperture-averaged variance. Gd/Cn² còn chỗ thiếu citation[] trong PDF.

## 6. Holevo và scope bảo mật

C dùng cùng \(T_{{total}}\), \(N_{{post}}=T_{{total}}\xi_{{total}}\) trong \(Z_\pm=2\sqrt{{T_{{total}}}}C\pm\sqrt{{2N_{{post}}w}}\), \(a=1+V_A\), \(b=1+T_{{total}}V_A+N_{{post}}\). Intersect physical correlation interval rồi numerical-maxχ. Conditional eigenvalue là homodyne \(\nu_3=\sqrt{{a(a-Z^2/b)}}\).

[Denys–Brown–Leverrier](https://arxiv.org/html/2103.13945v3) nêu công thức homodyne trên và áp dụng bound cho homodyne. Production protocol frozen của repo vẫn là idealheterodyne; đó là khác biệt protocol, không phải giới hạn “DBL chỉ heterodyne”. Exact C,w hiện có được dùng nguyên.

Full-Z33/129, independent symplectic matrix/uncertainty và entropy80/110digits đã kiểm tra. Không clip eigenvalues dưới1. Exact uncertainty-boundary identity của helper không phải numerical repair. Numerical max chưa là rigorous global enclosure. [Hosseinidehaj–Walk–Ralph](https://arxiv.org/abs/2002.03476) là reference effective fading/finite-sizeGaussian; không tự chuyển proof sang256-QAM ở đây. Parameter estimation, operational fading protocol và finite/composable proof vẫn chưa xác lập.

## 7. Detector-convention comparison

Ví dụ geometry gốc,ηdet=.8,εdet=.0135,fixedMB(.165,VA5.475). CSV đầy đủ144 rows cho hai geometry×tám detector pairs×các variant/extension:

{convtable}

## 8. Old versus new — cùng historical channel law

{oldtable}

baseline8/recent8/15–55cm dùng đúng passive random-width moments lịch sử; chỉ thay actual fading likelihood MI bằng Gaussian effective MI. C new MI khớp I_AB_surrogate đã tồn tại; Holevo cùng convention khớp helper cũ. **Không phát hiện double-count εdet trong recent untrusted helper.** Đổi dấu28,1cm là đổi approximation; không chứng minh source cache sai hoặc phủ nhận legacy value trong chính model cũ.

original_manuscript_trial8 giữ đúng rawlognormal law: K mới={comparison['original_trial_corrected_K']:.17g}, khớp số cũ ở độ chính xác số học. 30/40/55cm còn dương trong passive-surrogate table, nhưng chuyển sang rawPDF bị chặn tại các context mất mass. raw_manuscript43_results.json ghi riêng các giá trị/blocked fields. Không quy chênh lệch hai laws thành hiệu ứng detector riêng.

**Không chuyển tiếp kết luận “minimum28,1cm positive” sang Gaussian model.** Không re-ranking/optimization catalog mới; chỉ re-evaluate source cũ. affected_results.csv liệt kê252 result entries (thư mục và tệp ở root, có entry_kind riêng): chỉ scenario ghi rõ được tính lại; phần khác NOT_REEVALUATED. Old2DMI/homodyneHolevo zenith/mobility outputs giữ nguyên, không dùng làm consistent new homodyne SKR.

cache_impact.csv liệt kê287 cache entries:233 authenticated source payloads còn dùng được với đúng ensemble/VA; cache khác chỉ được bảo toàn, không coi là tái thẩm định. Objective/SKR cache phải có contextID mới khi dùngC. Không đổi namespace hoặc bytes source cache.

## 9. Thay đổi, verification và blocker

Chỉ thêm patch riêng cùng năm task ledgers. Không sửa src/, frozen spec, production configs, exact caches hoặc artifacts cũ. repository_map.csv và isolated_code_patch.diff chỉ rõ code/traceability; verify.py kiểm tra saved artifacts bằng hash, không gọi evaluator.

Lần tích hợp đầu tiên, harness dùng passive-collector geometry để đọc hệ số PDF cũ, gây KeyErrorB sau17 tests đạt. attempt_1/ giữ nguyên producer/failure. Caller đã sửa sang đúng preserved lognormal/Rician factory, thêm guard/test;18 tests sau đó đạt. Không đổi tolerance hoặc scientific source.

Không designate secure default do PDF mass failures,ξdet manuscript chưa định nghĩa,caveatρ≠0,Gaussian-MI approximation và operational/security scope chưa hoàn tất. C chỉ là **numerically validated physical homodyne/untrusted Gaussian component** khi input guards đạt. Giữ UNVALIDATED_SECURITY_MODEL,NOT_READY_FOR_PUBLICATION_SCALE_RUNS,historical frozen-hash discrepancy,ObjectiveC USER_STOPPED.

Không newAP, optimization sweep, training, final-test/heldout/publication, production baseline/threshold approval hoặc commit/push. Đề xuất sửa PDF nằm riêng ở manuscript_corrections_vi.md; PDF không bị chỉnh sửa.

## Appendix: bản đồ repo đã kiểm tra

{symbolmap}
'''
    (OUT/'report_vi.md').write_text(body,encoding='utf-8')
    corrections=r'''# Đề xuất sửa manuscript43 — không chỉnh sửa PDF

| ID | Equation / nội dung | Loại phát hiện | Đề xuất |
| --- | --- | --- | --- |
| M01 | Sau(3),Vmod=n̄/2 | Confirmed mathematical error dưới X=2Reα | Sửa Vmod=2n̄; giữ exact source/caches |
| M02 | (12),complexα trong Gaussian1D | Confirmed mathematical error | Real mean2√T Reα;y∈R;không nhân MI lên2 |
| M03 | (2),γ ở tử/ν ởZ | Missing definition/notation; lỗi normalization nếu khác nhau | Dùng cùng shaping symbol ở numerator/denominator |
| M04 | (2),norm indexk không centered | Missing convention; khác source hiện có | Ghi centered raw energy hoặc physical-energy mapping rõ |
| M05 | ξdet sau(17),(20) | Missing reference-plane definition | Phân biệt εdet/ηdet,χhom và independentξdet |
| M06 | σξ² sau(12) | Missing measurement-plane definition | Physical output dùng1+ηdet[(m1−mh²)VA+m1ξch]+εdet và signalTtotal=ηdetmh² |
| M07 | W,Z ở(13),(14) | Security-model ambiguity với untrusted detector | Cùng physical quantumTtotal,Npost cho Z,Γ,χ;rescale measurement không rescale quantumΓ tùy ý |
| M08 | (10),(18)–(20),support[0,1] | Confirmed normalization failure tại context đã lưu | BáoM0,tail,atom0;quyết định model trước fullprotocol;không silent renormalization |
| M09 | (8)→(10) khiρ≠0 | Confirmed exact-product inconsistency bằng moment counterexample | Ghi approximation/domain hoặc bổ sung derivation choρ≠0 |
| M10 | (5),σR² | Missing approximation/variance convention | v=Var(logIa)≈rawRytov khi weak;Var(log amplitude)=v/4 |
| M11 | Gaussian effective MI | Missing approximation statement | Constant noise là moment matching;fading conditional noise phụ thuộcX² |
| M12 | (14),lowerZ vs worstχ | Security/numerical scope | Physical interval và full-Zmax nếu dùng;finite-grid không là global proof |
| M13 | Homodyne claim vs production2D path | Numerical protocol-pairing issue khi dùng sai caller | Dùng homodyne1D;old2DMI+homodyneHolevo không là consistentnew rate |
| M14 | [] choGd,Cn²;OptimizationTBD | Notation/writing và missing provenance | Bổ sung nguồn/derivation;không mô tảTBD như đã triển khai |

Với y thực nhưng mean phứcμ=2√ηfα:

\[
\int_{\mathbb R}\frac{e^{-|y-\mu|^2/(2\sigma^2)}}{\sqrt{2\pi\sigma^2}}\,dy
=e^{-(\operatorname{Im}\mu)^2/(2\sigma^2)}.
\]

Với centeredC4, \(E[X^2]=2E|\alpha|^2=2\bar n\). Vì vậy lỗi Vmod là hệ số4; không đổi C,w để khớp cách viết đó.

ConventionB (\(\xi_{\rm det}=\chi_{\rm hom}\)) có thể tái tạo MI của measurementrescaled. Nó không cho phép dùng quantumΓrescaled standard form với CCR/vacuum cũ. Physical detectorloss là quantumloss; electronics làεdet; đều untrusted trongC.

Exact untruncated product moments từ Eq.(8) và lognormal Eq.(5):

\[
P_1 B^q e^{v(q^2-q)/2}\frac{d}{d+q}
\exp\left[-\frac{\rho^2q}{2\sigma_s^2(d+q)}\right],\quad d=\chi^2.
\]

Whole-support moment của Eq.(10):

\[
P_1B^q\frac{d}{d+q}
\exp\left[\log C_1+\frac{(d+q)^2}{4C_3^2}-(d+q)\mu\right].
\]

Chúng trùng khiρ=0, không trùng tổng quát. Rician_product_checks.csv là bằng chứng định lượng; không thay truncated moments trong audit.

Tài liệu: [Denys–Brown–Leverrier](https://arxiv.org/html/2103.13945v3) cho DM correlation/homodyne; [Laudenbach et al.](https://arxiv.org/pdf/1703.09278) cho receiver/noise framework. Các reference không tự phê chuẩn protocol/security scope của repo. Số liệu và trạng thái code/cache nằm trong report_vi.md cùng CSV/receipts.
'''
    (OUT/'manuscript_corrections_vi.md').write_text(corrections,encoding='utf-8')
    files=sorted(OUT.glob('*.py'))+[OUT/'protocol.json',OUT/'variants.json']
    patch=''.join(''.join(difflib.unified_diff([],p.read_text(encoding='utf-8-sig').splitlines(keepends=True),
        fromfile='/dev/null',tofile='results/'+OUT.name+'/'+p.name)) for p in files)
    (OUT/'isolated_code_patch.diff').write_text(patch,encoding='utf-8')
    print('REPORT/CORRECTIONS/MAP/PATCH COMPLETE',len(mapping),flush=True)


if __name__=='__main__':main()
