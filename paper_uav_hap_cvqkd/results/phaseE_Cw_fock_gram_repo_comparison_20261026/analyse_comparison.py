"""Analyze saved independent jobs; no new source calculation or channel sweep."""
import csv
import importlib.util
import json
from pathlib import Path
import sys
import mpmath as mp

OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
BASE=ROOT/'results/phaseC_new_cloud_dp_greedy_stationary_20261025'


def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def save(name,value):(OUT/name).write_bytes((json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode('utf-8'))
def put(name,text):(OUT/name).write_bytes((text.strip()+'\n').encode('utf-8'))
def rows(path):
    with Path(path).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def write(name,data):
    keys=list(dict.fromkeys(k for r in data for k in r))
    with (OUT/name).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(data)
def n(value):return mp.mpf(value) if isinstance(value,(str,int)) else mp.mpf(float(value))
def dec(value):return mp.nstr(value,45)
def table(headers,data):return '\n'.join(['| '+' | '.join(headers)+' |','|'+'|'.join(['---']*len(headers))+'|']+['| '+' | '.join(map(str,r))+' |' for r in data])


def main():
    protocol=read(OUT/'protocol.json');receipts=read(OUT/'job_receipts.json')
    metadata={r['name']:r for r in read(OUT/'inputs/source_metadata.json')}
    diagnostic=[];best={}
    with mp.workdps(100):
        for receipt in receipts:
            if receipt['status']!='COMPLETED':
                diagnostic.append(dict(source=receipt['source'],method=receipt['method'],NF=receipt['NF'],digits=receipt['digits'],
                    job=receipt['job'],numerical_status=receipt['status'],reason='Worker limit; no C,w value fabricated'))
                continue
            result=read(OUT/receipt['output'])
            for r in result['rows']:
                record=dict(source=receipt['source'],job=receipt['job'],**r)
                status='INCONCLUSIVE_RETAINED_SUPPORT' if not r['full_source_rank_resolved'] else 'FULL_RETAINED_RANK_DIAGNOSTIC'
                if n(r['w_residual'])<0 or r['material_negative']:status='NUMERICAL_INSTABILITY'
                record['numerical_status']=status
                if receipt['source'] in metadata:
                    ref=metadata[receipt['source']]
                    dC=n(r['C'])-n(float(ref['C']));dw=n(r['w_residual'])-n(float(ref['w']))
                    record.update(delta_C_vs_repo=dec(dC),delta_w_vs_repo=dec(dw),
                        C_absolute_difference=dec(abs(dC)),w_absolute_difference=dec(abs(dw)),
                        C_relative_difference=dec(abs(dC)/abs(n(float(ref['C'])))),
                        w_relative_difference=dec(abs(dw)/abs(n(float(ref['w'])))),
                        reference_convention='Exact binary64 cached moments; AP job decimal strings retained')
                    if r['digits']>16 and status!='NUMERICAL_INSTABILITY':
                        key=(receipt['source'],r['method'])
                        score=(int(r['NF']) if r['NF']!='' else 0,int(r['digits']))
                        if key not in best or score>best[key][0]:best[key]=(score,record)
                diagnostic.append(record)
        write('convergence_diagnostics.csv',diagnostic)
        comparison=[];pairwise=[];assessment=[]
        for source,ref in metadata.items():
            comparison.append(dict(source=source,method='Repository',C=ref['C'],w=ref['w'],
                delta_C_vs_repo='0',delta_w_vs_repo='0',ensemble_hash=ref['ensemble_hash'],
                numerical_status='HISTORICAL_STORED_INSUFFICIENT_EVIDENCE',evidence_class=ref['classification'],
                repository_evaluator_recomputed=False))
            a,b=[best[(source,m)][1] for m in ['A_Fock','B_Gram']]
            for label,row in [('Fock',a),('Gram',b)]:
                comparison.append(dict(source=source,method=label,C=row['C'],w=row['w_residual'],
                    delta_C_vs_repo=row['delta_C_vs_repo'],delta_w_vs_repo=row['delta_w_vs_repo'],
                    C_relative_difference=row['C_relative_difference'],w_relative_difference=row['w_relative_difference'],
                    NF=row['NF'],digits=row['digits'],numerical_rank=row['numerical_rank'],
                    ensemble_hash=ref['ensemble_hash'],job=row['job'],numerical_status=row['numerical_status'],
                    full_source_rank_resolved=row['full_source_rank_resolved'],evidence_class='INDEPENDENT_DIAGNOSTIC_ONLY'))
            for metric,key in [('C','C'),('w','w_residual')]:
                delta=n(a[key])-n(b[key]);scale=abs(n(b[key]))
                pairwise.append(dict(source=source,metric=metric,A_minus_B=dec(delta),absolute_difference=dec(abs(delta)),
                    relative_difference=dec(abs(delta)/scale),A_job=a['job'],B_job=b['job'],
                    precision_note='AP job values recorded at50 significant digits; zero means indistinguishable at recorded precision'))
            local=abs(n(a['C'])-n(b['C']))<=mp.mpf('2e-11') and abs(n(a['w_residual'])-n(b['w_residual']))<=mp.mpf('2e-12')
            full=bool(a['full_source_rank_resolved'] and b['full_source_rank_resolved'])
            assessment.append(dict(source=source,observable_comparison_within_prospective_tolerances=bool(local),
                A_best_NF=a['NF'],A_digits=a['digits'],A_rank=a['numerical_rank'],B_digits=b['digits'],B_rank=b['numerical_rank'],
                full_source_support_both_resolved=full,
                mathematical_full_support_convergence_certified=False,
                conclusion='INCONCLUSIVE_FULL_SUPPORT; tested C,w observables agree' if not full else 'FULL_RANK_DIAGNOSTIC_REQUIRES_PRECISION_CONFIRMATION'))
        write('Cw_comparison.csv',comparison);write('pairwise_method_differences.csv',pairwise)
        save('convergence_assessment.json',dict(overall='INCONCLUSIVE',sources=assessment,
            PHASE_B_STRICT_READY=False,existing_source_evidence_upgraded=False,
            reason='Best completed independent references do not resolve all256 source modes; higher jobs hit declared limits'))
        downstream(best,metadata)
        reports(comparison,diagnostic,pairwise,assessment,receipts)


def downstream(best,metadata):
    sky=rows(BASE/'clear_sky_map_centered.csv');position=min(sky,key=lambda r:float(r['zenith_deg']))
    candidates=rows(BASE/f"physical_records/{position['geometry_id']}.csv")
    ref=metadata['Winner_MB'];stored=next(r for r in candidates if r['ensemble_hash']==ref['ensemble_hash'])
    path=ROOT/'results/skr_vs_zenith_eq14_v43_20261023/model.py'
    spec=importlib.util.spec_from_file_location('_approved_eq14_only',path);model=importlib.util.module_from_spec(spec);spec.loader.exec_module(model)
    A,B=[best[('Winner_MB',m)][1] for m in ['A_Fock','B_Gram']]
    ready=bool(A['full_source_rank_resolved'] and B['full_source_rank_resolved'])
    # The task makes alternate Holevo/SKR conditional on reliable independent
    # moments. Keep those fields empty when the full-support check is unresolved.
    data=[]
    with mp.workdps(110):
        eta,xi=n(float(stored['eta_f'])),n(float(stored['xi_f']))
        z0=model.correlation_eq14(eta,xi,float(ref['C']),float(ref['w']))
        inputs=[('Repository',float(ref['C']),float(ref['w']),True),
                ('Fock',A['C'],A['w_residual'],ready),('Gram',B['C'],B['w_residual'],ready)]
        for label,C,w,eligible in inputs:
            z=model.correlation_eq14(eta,xi,C,w)
            with mp.workdps(80):low=model.correlation_eq14(eta,xi,C,w)
            assert abs(z-low)<mp.mpf('2e-70')
            record=dict(result_scope='DIAGNOSTIC_ONLY',method=label,geometry_id=position['geometry_id'],
                position_index=position['position_index'],zenith_deg=position['zenith_deg'],
                eta_f=stored['eta_f'],xi_f=stored['xi_f'],C=dec(n(C)),w=dec(n(w)),
                Z_manuscript_eq14=dec(z),delta_Z_vs_repo=dec(z-z0),Z_precision80_110_difference=dec(z-low),
                I_AB=stored['I_AB'],beta_I_AB=stored['beta_I_AB'],MI_status='REUSED_SAME_PHYSICAL_ENSEMBLE_AND_CONTEXT',
                chi_BE=stored['chi_BE'] if label=='Repository' else '',K_raw=stored['K_raw'] if label=='Repository' else '',
                SKR_sign='POSITIVE_STORED_DIAGNOSTIC' if label=='Repository' else 'NOT_EVALUATED',
                SKR_status='REUSED_STORED_NOT_RECOMPUTED' if label=='Repository' else 'NOT_RUN_UNRESOLVED_INDEPENDENT_FULL_SUPPORT',
                independent_full_support_ready=ready,source_evidence_class='INSUFFICIENT_EVIDENCE')
            if label!='Repository' and eligible:
                result=model.components(float(ref['VA']),eta,xi,C,w,digits=110)
                K=float(stored['beta_I_AB'])-result['chi_BE']
                record.update(chi_BE=result['chi_BE'],K_raw=K,SKR_sign='POSITIVE' if K>0 else 'NONPOSITIVE',SKR_status='INDEPENDENT_DIAGNOSTIC_COMPONENTS')
            data.append(record)
    write('Z_SKR_sensitivity.csv',data)
    save('downstream_execution.json',dict(existing_primary_contexts_reused=1,new_channel_integrations=0,
        new_MI_computations=0,Eq14_evaluations=6,new_alternative_Holevo_SKR_evaluations=2 if ready else 0,
        alternative_evaluation_gate=ready,reason='Full256 source support unresolved; alternative Holevo/SKR not executed',
        source_guard_bypassed=False,physical_or_security_equations_changed=False))


def reports(comparison,diagnostic,pairwise,assessment,receipts):
    display=[]
    for r in comparison:
        display.append([r['source'],r['method'],mp.nstr(n(r['C']),18),mp.nstr(n(r['w']),18),
            mp.nstr(n(r['delta_C_vs_repo']),6),mp.nstr(n(r['delta_w_vs_repo']),6),r['numerical_status']])
    tab=table(['Source','Method','C','w','delta C vs repo','delta w vs repo','Numerical status'],display)
    partial=[r for r in receipts if r['status']!='COMPLETED']
    partial_table=table(['Job','Outcome','Runtime s','Assigned time cap s'],[
        [r['job'],r['status'],f"{r['elapsed_seconds']:.3f}",f"{r.get('timeout_seconds',0):.3f}"] for r in partial])
    stable='''# C,w numerical stability — INCONCLUSIVE full support

The final comparison uses the largest completed Fock cutoff/highest scheduled
precision, and the highest completed Gram precision. Selection never uses
closeness to the cached value. Differences in Cw_comparison.csv are computed
at100digits against the EXACT binary64 cached values; converting both methods
to float64 first would hide sub-ulp differences. Relative and absolute
differences are separate, and the repository cache is a reference, not an
independently certified truth.

Six small-case labels (4/16/64-QAM, Uniform/MB) pass full-rank independent
algebra checks. MB4 equals Uniform4 because all four points have the same
energy; these are six test labels, not six distinct physical constellations.
For the selected256-QAM sources, the completed C,w observables agree across
methods and tested precision/cutoffs, but some positive source modes remain
unresolved. No formal convergence certificate or evidence promotion follows.

## Conditioning, cutoff and cancellation

Winner complex128 Fock atNF64: changing the declared eigenvalue threshold
from1e-10 to1e-12,1e-14,1e-16 retains25,30,35,40 modes, respectively.
Residual w changes from about9.59060e-9 to6.70527e-10,5.70921e-10,
5.70037e-10. Raising NF alone with an unchanged spectral threshold does not
restore discarded positive modes. Gram float64 at1e-16 retains43 modes and
gives about5.70094e-10, showing a different near-roundoff numerical support.
These are explicitly regularized approximations, not replacements for the
canonical256-mode MP inverse.

At the same float64 cutoff/operator, direct-minus-residual w can be around
4e-16 absolute, already around1e-6 relative at w~5.7e-10. Stable residuals
reduce cancellation but cannot repair missing spectral support or conditioning.
No negative result is clipped. Exact direct/residual differences, any negative
w and eigenvalues, and backward residuals are retained in the CSV/job JSONs.

FockNF24 gives w around2.23e-8 for the winner: too short despite its inexpensive
density construction. Poisson tails are checked independently; no state or PMF
is renormalized. Trace near1 is necessary but not sufficient for inverse-root
accuracy. Input binary64 probabilities have tiny exact-sum deviations from1,
recorded in input_validation.json and used identically by both methods.

Arbitrary precision uses the declared10^(-digits+20) spectral floor. The winning
FockNF256/260digit job retains231/256 modes, while Gram180digits retains186/256.
Fixed MB best completed Fock hasNF128/rank128, and Gram180digits rank186/256.
Backward residuals at high precision do not bound unresolved tiny eigenvalues;
only RETAINED condition numbers are reported, not a fabricated full condition.
Both Gram260digit jobs hit180s; Fixed FockNF256 had only the remaining global
budget. Logs retain per-sector progress; no missing final C,w is filled in.

The original repository worker uses1050/1250/1450 digits and requires256positive
modes, but its final C,w allowance is1e-7+1e-6*maxabs. The absolute part is
larger than the stored w. Its cached settings/label do not substitute for the
missing original per-precision receipt or prove tiny-w relative accuracy.

## Bounded outcomes

'''+partial_table+'''

Runtime limits were enforced sequentially. A Windows venv launcher initially
hid the actual numerical-worker RSS;45 completed low/medium-cost jobs have
launcher-only memory samples and are explicitly flagged. The batch was stopped,
those results/logs preserved, and workers were relaunched via the actual base
interpreter with the existing venv dependencies. Subsequent RSS samples measure
the correct PID. No installed package, production code or historical cache was
changed. One interrupted Fock diagnostic was resumed once; this is not a retry
of either timed-out Gram260 run or the missing Uniform job.

## Safest next step

Keep current cache/evidence labels. Before another high-cost attempt, add
per-sector/per-precision numerical checkpoints and profile the selected-source
worker. A separately budgeted run above260digits must resolve all256 source
modes at two successive precisions and compare C,w, residuals and rank; it
must not rely on the repository's broad absolute tolerance alone. If numerical
or analytic bounds for omitted-mode effects are unavailable, keep full-support
accuracy INCONCLUSIVE. Do not restart the entire source catalog or Uniform job.
'''
    put('Cw_numerical_stability.md',stable)
    downstream_rows=rows(OUT/'Z_SKR_sensitivity.csv')
    ztable=table(['Method','Z Eq14','Delta Z','Raw SKR','SKR status'],[
        [r['method'],mp.nstr(n(r['Z_manuscript_eq14']),18),mp.nstr(n(r['delta_Z_vs_repo']),6),r['K_raw'] or '—',r['SKR_status']]
        for r in downstream_rows])
    text='''# PHASE E C,w COMPARISON: INCONCLUSIVE

**DIAGNOSTIC_ONLY; PHASE_B_STRICT_READY = FALSE.** Đã chạy các phương pháp
độc lập và thu được số thực tế. C,w trong các kiểm tra đã hoàn tất khớp rất sát,
nhưng chưa chứng minh hội tụ đủ256 mode của hai nguồn chính trong ngân sách.
Không có bằng chứng về mismatch định nghĩa C,w từ các phép kiểm tra đã thực hiện.

## Bảng đối chiếu

Các delta dùng chính xác giá trị binary64 trong cache làm reference; kết quả
AP được giữ dạng decimal trước khi trừ, tránh mất khác biệt dưới một ulp.

'''+tab+'''

## Trả lời các câu hỏi

1. **Repository tính gì?** Path tạo cache là weighted coherent-state Gram,
chia bốn sector C4. Nó tính cùng trace C và weighted variance của a_tau đã
chỉ định; không dùng channel/zenith. Backend Fock cũ tồn tại riêng, không phải
producer của hai cache này. Xem repository_Cw_audit.md với27 mục truy xuất
function, dòng mã, input, precision, kích thước, rank và cache/convergence.

2. **Có tương đương Sayat/Denys?** Có về đại số cho ensemble C4 này khi dùng
đủ support và precision: Eq20–22 của bản journal Sayat và định nghĩa MP/variance
của Denys đã được đối chiếu từ PDF. Điều này không chứng minh mọi cutoff hoặc
precision hữu hạn tương đương số. Không thay đổi v43, Eq14, MI hoặc Holevo.

3. **Fock và Gram độc lập có khớp?** Sáu sanity case khớp với full rank của
constellation nhỏ. Hai nguồn256-QAM cho observable C,w khớp rất sát giữa các
phép AP đã xong; xem pairwise_method_differences.csv. Các phép này chưa cùng
giải quyết đầy đủ256 mode, nên đây không phải chứng chỉ full-support.
Cả bốn giá trị C,w best-tested làm tròn về binary64 đều bằng đúng cache.
Delta A−B bằng0 trong CSV chỉ có nghĩa không phân biệt được ở50 chữ số đã lưu.

4. **w cỡ1e-10 có ổn định không?** Có ổn định thực nghiệm trong các mức AP/NF
đã kiểm tra, nhưng chưa có cận sai số toàn support. Float64 trực tiếp và
cutoff phổ tùy tiện không đủ; residual norm không tự khắc phục conditioning.

5. **Yếu tố nào gây chênh?** Fock quá ngắn (ví dụNF24), bỏ mode theo threshold,
eigendecomposition gần roundoff và cancellation đều thấy trong dữ liệu.
Không phát hiện khác biệt input ensemble/normalization. Đã ghi riêng trace,
norm, phổ, rank, backward residual, absolute và relative differences.

6. **Nguồn thắng đã được validated chưa?** Giá trị cache được hỗ trợ mạnh bởi
các cross-check observable độc lập đã hoàn tất, nhưng full-support convergence
vẫn INCONCLUSIVE. Giữ INSUFFICIENT_EVIDENCE và không tạo receipt lịch sử giả.

7. **Ảnh hưởng Eq14/SKR?** Chỉ dùng một context primary đã lưu, tại zenith nhỏ
nhất trong lưới; tính Z trực tiếp ở80/110digits. Điều kiện đánh giá lại
Holevo/SKR với hai moment reference đủ tin cậy chưa qua full-support gate,
nên không chạy alternative Holevo/SKR. MI và betaMI tái dùng vì ensemble và
channel giống hệt; SKR repository chỉ đọc cache. Không suy ra chắc chắn dấu
SKR thay thế từ sự gần nhau của Z, và không mở rộng sweep. Delta Z AP khoảng
−7.99985e-17. Nếu làm tròn các moment về binary64 như dữ liệu đang dùng,
đầu vào C,w trùng cache nên không có thay đổi đầu vào để đổi dấu SKR trong
evaluator xác định. Điều đó không chứng nhận dấu SKR của full-support reference
chưa được giải quyết; các trường alternative Holevo/SKR vẫn để trống.

'''+ztable+'''

8. **Bước tiếp theo an toàn?** Giữ cache và trạng thái evidence; lưu checkpoint
eigenspectrum theo sector/precision trước khi cấp ngân sách riêng cho một
nguồn thắng ở precision cao hơn260, có hai mức full-support liên tiếp.
Không mở rộng toàn catalog hoặc chạy lại Uniform bị thiếu.

9. **Số nguồn catalog bị sửa: ZERO.** Hai nguồn MB lịch sử chỉ được đọc làm
input/reference. Các source moment mới chỉ nằm trong namespace kiểm chứng,
không thay cache, production evaluator, manuscript hoặc historical results.

## Thực thi và giới hạn

66 job đã có receipt:63 hoàn tất,3 chạm giới hạn. Sáu sanity labels gồm4/16/64
Uniform/MB; MB4 trùng Uniform4 do năng lượng bằng nhau. Hai nguồn chính là
winner và Fixed MB; không tính thêm source catalog nào, không chạy Uniform256.
Ngân sách worker1200s, tối đa180s/job; Fixed Fock cuối chỉ còn khoảng9.17s.
Polling/termination có sai số thời gian nhỏ; tổng upper-bound đã ghi1200.122s.
Sau sửa launcher, RAM được đo ở tiến trình thực; các mẫu launcher trước đó
được ghi là không đo RAM thực. Không che limitation vận hành này. Ngoài66 job
định danh có một attempt Fock bị gián đoạn khi sửa monitor, sau đó resume một
lần; log gốc được giữ và thời gian đã được tính trong upper-bound ban đầu.
RAM thực đo được sau sửa có peak sampled khoảng146.94MiB, dưới cap1024MiB.
11 focused checks bổ sung (chỉ tối đa16 trạng thái/NF48) qua kiểm tra trong
khoảng0.034s, ngoài batch source jobs; không có thêm phép tính256-QAM.

'''+partial_table+'''

Tất cả giá trị thiếu để trống, không điền zero. Ba job không hoàn tất không
được coi là numerical pass. Không có Z search, clamp w/eigenvalue, nội suy,
source classification upgrade hoặc thay đổi điều kiện vật lý/bảo mật.
Các formula, dữ liệu đầu vào và tiến trình tái lập nằm trong ba script chính,
protocol.json, job_plan.json, job_receipts.json và inputs/.
Xem artifact_integrity_report.md và verification.json cho kiểm chứng cuối.
'''
    put('validation_report_vi.md',text)
    put('README.md','''# Phase E independent source comparison

Read [Vietnamese report](validation_report_vi.md), [derivation](mathematical_derivation.md),
[repository audit](repository_Cw_audit.md), [stability analysis](Cw_numerical_stability.md),
[six-row comparison](Cw_comparison.csv), [all diagnostics](convergence_diagnostics.csv),
[A-minus-B differences](pairwise_method_differences.csv), [one-context Eq14 check](Z_SKR_sensitivity.csv).

Independent implementations: [Fock](independent_fock_Cw.py), [Gram](independent_gram_Cw.py).
[Bounded controller](run_comparison.py) refuses a completed batch; do not rerun it
in this historical namespace. [Analysis](analyse_comparison.py) uses saved jobs only.
Raw spectra, values and limit outcomes are under jobs/. Input arrays/hashes and
primary source PDFs are under inputs/ and reference_audit.json.

Overall INCONCLUSIVE for full256-mode convergence, despite tested observable
agreement. No historical source evidence classification is promoted. Strict
Phase B remains false; no source catalog or physical/security equation is edited.
''')


if __name__=='__main__':main()
