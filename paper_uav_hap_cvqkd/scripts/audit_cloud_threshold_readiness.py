"""Read-only scientific preflight; writes a new audit, never launches SKR/search."""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import math
import subprocess

ROOT=Path(__file__).resolve().parents[1]


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def run(out):
    if out.exists():raise FileExistsError('Use a fresh audit namespace')
    before=subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True)
    out.mkdir(parents=True)
    paths=['docs/FINAL_MODEL_SPEC.md','docs/SECURITY_SCOPE_FREEZE.md',
      'results/skr_vs_zenith_eq14_v43_phaseB_readiness_20261024/readiness.json',
      'results/phaseE2_winning_source_spectral_validation_20261026/source_convergence_status.json',
      'results/skr_vs_zenith_eq14_v43_phaseB_readiness_20261024/protocol.json',
      'results/skr_vs_zenith_eq14_v43_phaseB_61angle_diagnostic_20261024/protocol.json',
      'results/skr_vs_zenith_eq14_v43_phaseB_61angle_diagnostic_20261024/best_scheme_by_angle.csv',
      'results/skr_vs_zenith_eq14_v43_phaseB_exact_reuse_20261024/diagnostic_model.py',
      'src/channel/fso_channel.py','src/cvqkd/secret_key_rate.py',
      'src/optimization/baseline_search.py','configs/manuscript_mobility.json']
    inputs={p:sha(ROOT/p) for p in paths}
    read=lambda p:json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
    readiness=read(paths[2]);e2=read(paths[3]);protocol=read(paths[4]);task=read(paths[5])
    assert sha(ROOT/task['physical_protocol_path'])==task['physical_protocol_sha256']
    source=e2['source_identity'];sourcepath=ROOT/source['source_path']
    assert sha(sourcepath)==source['source_sha256']
    inputs[source['source_path']]=sha(sourcepath)
    expected='561fecc97cdf9967034ffd6865c1605804b624b98f47a091e47f17e520a2a7b1'
    blockers=[]
    if inputs[paths[0]]!=expected:blockers.append('FROZEN_SPEC_HASH_DISCREPANCY_UNRESOLVED')
    if not readiness['phase_B_ready']:blockers.append('STRICT_PHASE_B_NOT_READY')
    if e2['conclusion']!='CURRENTLY_VERIFIED_PASS' or not e2['full_support_certified']:
        blockers.append('WINNER_CW_CONVERGENCE_INCONCLUSIVE')
    blockers+=['SECURITY_BRANCH_REQUIRES_EXPLICIT_SELECTION',
               'UAV_GRID_AND_HAP_HORIZONTAL_PLACEMENT_NOT_BOUND_TO_2KM_REGION',
               'CONTINUOUS_REOPTIMIZATION_HAS_NO_COMPLETE_CERTIFIED_SOURCE_COVERAGE']
    result=dict(status='BLOCKED_BY_SCIENTIFIC_PREREQUISITES',
        requested_task_complete=False,numerical_thresholds_available=False,
        blockers=blockers,actual_frozen_sha256=inputs[paths[0]],historical_expected_sha256=expected,
        phase_B_ready=readiness['phase_B_ready'],source_status_counts=readiness['source_status_counts'],
        winning_source_evidence=source['source_evidence_class'],E2_conclusion=e2['conclusion'],
        rigorous_Cw_error_bound=e2['rigorous_Cw_error_bound'],
        selected_physical_branch=None,publication_training=False,
        new_channel_evaluations=0,new_MI_evaluations=0,new_Holevo_evaluations=0,
        new_source_Cw_computations=0,new_optimizer_calls=0,
        critical_attenuation_fixed_db=None,critical_attenuation_reoptimized_db=None,
        threshold_outage_rule_certified=False,
        historical_eq14_parameters={k:protocol[k] for k in ['physical','beta','xi_ch','xi_det','measurement','source_domain']})
    def save(name,v):(out/name).write_bytes((json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode())
    save('readiness.json',result);save('input_hashes.json',inputs)
    save('startup.json',dict(branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip(),
         HEAD=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),git_status=before))
    (out/'startup_git_diff.patch').write_bytes(subprocess.check_output(['git','diff'],cwd=ROOT))
    # Preserve all pre-existing cloud data including the uncommitted attenuation task.
    prior=ROOT/'results/ibrahim_continuous_attenuation_20261112'
    protected=json.loads((prior/'protected_inputs.json').read_text())
    for f in prior.rglob('*'):
        if f.is_file():protected[f.relative_to(ROOT).as_posix()]=sha(f)
    for name,digest in protected.items():assert sha(ROOT/name)==digest,name
    save('protected_inputs.json',protected)
    geometries=[]
    mobility=read('configs/manuscript_mobility.json')['geometry']
    n=mobility['grid_cells_per_side'];side=mobility['grid_side_m']
    for iy in range(n):
        for ix in range(n):
            x,y=(ix+.5)*side/n,(iy+.5)*side/n
            r=math.hypot(x-mobility['hap_horizontal_m'][0],y-mobility['hap_horizontal_m'][1])
            geometries.append(dict(scenario='EXISTING_MANUSCRIPT_GRID',ix=ix,iy=iy,x_m=x,y_m=y,
                horizontal_m=r,link_km=math.hypot(19000,r)/1000,zenith_deg=math.degrees(math.atan2(r,19000)),
                geometry_only=True,threshold_db='',status='NOT_RUN'))
    # Analytic domain bounds; no invented UAV placement or grid.
    center_radius=math.sqrt(2)*1000
    geometry_bounds=dict(scope='CONDITIONAL_GEOMETRY_ONLY_NOT_APPROVED_QKD_LAYOUT',
        vertical_separation_km=19,proposed_2km_centered_continuous_square_max_link_km=math.hypot(19000,center_radius)/1000,
        proposed_2km_centered_continuous_square_max_zenith_deg=math.degrees(math.atan2(center_radius,19000)),
        distance_22km_zenith_deg=math.degrees(math.acos(19/22)),
        distance_22km_horizontal_km=math.sqrt(22**2-19**2),
        actual_manuscript_side_m=side,actual_manuscript_grid=n,
        actual_manuscript_HAP_xy_m=mobility['hap_horizontal_m'],
        actual_manuscript_max_zenith_deg=max(r['zenith_deg'] for r in geometries))
    save('geometry_bounds.json',geometry_bounds)
    with (out/'existing_geometry.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(geometries[0]));w.writeheader();w.writerows(geometries)
    with (ROOT/paths[6]).open(encoding='utf-8',newline='') as f:stored=list(csv.DictReader(f))
    selected=[r for r in stored if float(r['zenith_deg'])==0]
    with (out/'saved_clear_sky_reference.csv').open('w',encoding='utf-8',newline='') as f:
        names=['scheme','zenith_deg','VA','nu_raw','K_raw','source_evidence_class','origin','A_crit_db']
        w=csv.DictWriter(f,fieldnames=names);w.writeheader()
        for row in selected:w.writerow({**{k:row[k] for k in names[:6]},'origin':'SAVED_EQ14_A0_ONLY_NOT_NEW_EVALUATION','A_crit_db':''})
    report=f'''# Kiểm tra điều kiện xác định ngưỡng suy hao mây

Ngày 2026-11-12. **Chưa hoàn thành phép tính ngưỡng được yêu cầu.**
Trạng thái: BLOCKED_BY_SCIENTIFIC_PREREQUISITES. Acrit_fixed và Acrit_reoptimized
đều chưa xác định (null), không phải 0 dB. Không có sweep SKR hoặc hình ngưỡng mới.

## Nguồn chân lý và các nhánh không được trộn

`src/cvqkd/secret_key_rate.py::fading_secret_key_rate` giữ cả raw=beta*MI-Holevo
và positive-part riêng. Root phải dùng instantaneous_raw/fading_average_raw theo
đúng nhánh đã chọn, không dùng instantaneous_positive_part.
`src/channel/fso_channel.py` ghép khí quyển, scintillation, pointing và AoA;
không thay các yếu tố này bằng một mean T đơn lẻ trong mô hình oracle-iid.
`src/optimization/baseline_search.py` là tìm kiếm trên validation có constraints,
không phải giấy phép đổi sang một miền VA/nu khác.

Đặc tả FINAL_MODEL_SPEC có nhánh direct-Z-minus, ideal heterodyne, D_r=0.55m,
xi_total=.0186, nu_raw>=0, VA>0 không có cận vật lý trên cố định.
Trong khi đó gói hình Eq14 gần nhất dùng homodyne hiệu dụng, D_r=0.30m,
xi_ch=.0186, xi_det=.005, beta=.95, VA=[.05,10],nu_raw=[0,.4], AO/phase OFF.
Code đánh giá lịch sử:
`results/skr_vs_zenith_eq14_v43_phaseB_exact_reuse_20261024/diagnostic_model.py::evaluate`.
Nó gọi MI GH64/128 và components Eq14/Holevo ở 80/110 chữ số,
với nguồn DM 256 điểm, không được thay bằng công thức Gaussian-modulation.
Nguồn MB có nu_repo=42.5*nu_raw, VA=2*nbar.
Các nhánh trên cho các bài toán khác nhau; không tự chọn khẩu độ hoặc Holevo
theo ý nghĩa mơ hồ của từ current.

## Bằng chứng chặn hiện tại

Hash FINAL_MODEL_SPEC thực tế `{inputs[paths[0]]}` khác hash lịch sử AGENTS
`{expected}`. Giữ nguyên tệp, không tự phục hồi hoặc phê duyệt hash mới.
readiness Phase B: phase_B_ready=false, số nguồn theo lớp {readiness['source_status_counts']}.
E2: {e2['conclusion']}; source tốt nhất còn INSUFFICIENT_EVIDENCE,
full_support_certified=false; chưa có rigorous_Cw_error_bound.
Hash nguồn tốt nhất và liên kết protocol đã kiểm tra trực tiếp, không chỉ chép
nhãn PROJECT_STATE. Đây là thiếu bằng chứng, không khẳng định C,w chắc chắn sai.
Một nghiệm root chính xác đến .005 dB không thay thế hội tụ C,w/MI/Holevo.
Không chạy tối ưu liên tục rồi nội suy C,w ở các VA,nu chưa có nguồn chính xác.
Max trên 212 nguồn lịch sử cũng không được gọi là tối ưu liên tục toàn miền.

## Đặt suy hao đúng một lần

Với mỗi realization T_clear, dùng T_eff=s*T_clear, s=10^(-A/10), giữ AoA atom0.
Đối với nhánh moments cố định: m1'=s*m1, mh'=sqrt(s)*mh, M0'=M0, P0'=P0.
Không tái chuẩn hóa PDF và không tái tích phân một PDF clear trên miền [0,1]
để vô tình lấy thêm phần đuôi đã loại khỏi baseline.
Đặc biệt nhánh Eq14 có noise N=(m1-mh^2)*VA+xi_ch*m1+xi_det*M0.
Sau suy hao, N'=s*((m1-mh^2)*VA+xi_ch*m1)+xi_det*M0;
detector noise không bị suy hao cùng tín hiệu. Không đơn giản nhân toàn N với s.
Sau đó phải gọi lại chính MI/Holevo của nhánh đã chọn, không scale SKR đã lưu.
Nếu trạng thái oracle tức thời được chọn, phải tính từng realization trước average;
không thay average(K(T)) bằng K(average(T)).

## Hình học đã kiểm tra

Miền UAV cấu hình manuscript hiện có là {side:g}m, {n}x{n} tâm ô,
HAP xy={mobility['hap_horizontal_m']}, không phải miền 2km x2km của trường mây.
`existing_geometry.csv` ghi toàn bộ 100 vị trí cũ, không gán threshold.
Với **giả thiết bổ sung** HAP ở tâm miền 2km liên tục, khoảng đứng 19km:
zenith lớn nhất {geometry_bounds['proposed_2km_centered_continuous_square_max_zenith_deg']:.9f} độ,
Lmax {geometry_bounds['proposed_2km_centered_continuous_square_max_link_km']:.9f}km.
Đây chỉ là biên hình học có điều kiện, chưa là layout QKD được chọn.
L=22km tương ứng góc {geometry_bounds['distance_22km_zenith_deg']:.9f} độ và bán kính
ngang {geometry_bounds['distance_22km_horizontal_km']:.9f}km: là extended-range,
không phải do miền bay 2km tự sinh ra. Không đồng nhất xy_UAV với xy trên lớp mây.

## Công cụ đã chuẩn bị và giới hạn

`src/cloud_threshold_search.py` cung cấp pushforward realization/moments và
coarse raw sweep0..100dB/bước.5, bisection bracket rộng<=.005dB qua callback.
Chưa nối một evaluator khoa học vì nhánh chưa được quyết định. Test callback
giải tích chỉ là fixture kiểm thử root, không là công thức SKR thay thế.
Hàm xử lý K(0)<=0 như không có positive margin, không giả vờ root=0;
không có crossing thì right-censored, không ngoại suy. Có nhiều crossing hoặc
upward steps thì không trả một threshold duy nhất. Sweep chỉ chứng minh
monotonicity tại các điểm đã đánh giá, không bảo đảm liên tục hay toàn miền.
Nhánh tối ưu còn cần tolerance/budget, convergence và sai số từng evaluation;
bracket theo dấu không đáng tin nếu sai số số học làm dấu K không chắc chắn.

Định nghĩa outage bằng dấu Kraw<=0 vẫn đúng theo evaluator được chọn.
Chưa xác minh quy tắc A>=Acrit hay một ngưỡng toàn cục. Nếu chọn average-SKR
thì threshold của average khác outage tức thời; AoA đã gây K=0 dù A=0.
Không cài quy tắc outage mới vào mô hình mây/QKD hiện có.

## Việc cần quyết định trước bước tính số

Chọn rõ nhánh Eq14 diagnostic hoặc frozen ideal-heterodyne; cố định khẩu độ,
receiver/noise/security convention và miền VA/nu theo nhánh đó. Gắn HAP xy và
lưới UAV thực với miền 2km. Xác nhận chỉ chạy chẩn đoán dùng nguồn chưa được
chứng nhận, hoặc hoàn tất điều kiện hội tụ trước ngưỡng có thể dùng chính thức.
Không có một boolean override nào trong công cụ để bỏ qua thiếu bằng chứng.
Reoptimization phải dùng procedure và nguồn hợp lệ, không đổi thành catalog
envelope hoặc surrogate. Không tự chạy AP cao, training, final-test, held-out,
publication hoặc ObjectiveC đã USER_STOPPED.

Các tệp số có sẵn ở A=0 được trích riêng `saved_clear_sky_reference.csv` và
đánh dấu nguồn lịch sử; không phải sweep suy hao hoặc Experiment A/B mới.
Figure1,Figure2,Figure3,threshold-map và so sánh fixed/reoptimized: **NOT_RUN**.
'''
    (out/'report_vi.md').write_bytes(report.encode())
    (out/'README.md').write_bytes(b'# Cloud threshold scientific preflight\n\nIncomplete requested study: read report_vi.md and readiness.json. No physical thresholds or new SKR figures.\n\nRun from project root: .venv/Scripts/python.exe -X utf8 -B scripts/audit_cloud_threshold_readiness.py --output results/cloud_threshold_audit_new\n\nUnit tests: .venv/Scripts/python.exe -X utf8 -B -m unittest tests.test_cloud_threshold_search -v\n')
    assert all(sha(ROOT/p)==h for p,h in inputs.items())
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    run(p.parse_args().output.resolve())
