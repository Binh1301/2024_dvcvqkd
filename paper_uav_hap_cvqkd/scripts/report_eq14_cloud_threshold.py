"""Plot and report saved diagnostic cloud thresholds, without numerical reruns."""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams.update({'font.family':'DejaVu Serif','font.size':10,'pdf.fonttype':42,
 'ps.fonttype':42,'savefig.dpi':400,'axes.spines.top':False,'axes.spines.right':False})
MODES=['fixed_clear_optimum','catalog_reselected_212']
LABELS=['Fixed clear-sky optimum','Reselected: finite 212-source catalog']
COLORS=['#276b92','#bd4a35']


def rows(path):
    with path.open(encoding='utf-8') as f:return list(csv.DictReader(f))


def report(out):
    execution=json.loads((out/'execution_summary.json').read_text())
    validation=json.loads((out/'adapter_validation.json').read_text())
    summaries=[json.loads(p.read_text()) for p in out.glob('*_summary.json') if p.name!='execution_summary.json']
    byname={r['geometry']:r for r in summaries};data=rows(out/'critical_thresholds.csv')
    mapped=rows(out/'critical_threshold_map.csv')
    corner=byname['domain_corner'];grid_corner=max((r for r in summaries if r['geometry'].startswith('grid_')),key=lambda r:r['zenith_deg'])
    plots=[]
    def save(fig,name):
        fig.savefig(out/(name+'.png'),dpi=400,facecolor='white');fig.savefig(out/(name+'.pdf'),facecolor='white');plt.close(fig);plots.append(name)
    fig,axs=plt.subplots(3,2,figsize=(12,10),layout='constrained')
    for i,(name,label) in enumerate([('vertical','Vertical, L=19 km'),(grid_corner['geometry'],'Farthest grid cell'),('extended_22km','Extended range, L=22 km')]):
        records=rows(out/(name+'_evaluations.csv'));summary=byname[name]
        critical=[]
        for mode,title,color,style in zip(MODES,LABELS,COLORS,['-','--']):
            selected=sorted((r for r in records if r['mode']==mode),key=lambda r:float(r['A_db']))
            x=[float(r['A_db']) for r in selected];y=[float(r['K_raw']) for r in selected]
            for j in [0,1]:axs[i,j].plot(x,y,label=title,color=color,ls=style,lw=1.3)
            value=summary['searches'][mode]['diagnostic_crossing_midpoint_db']
            if value is not None:
                critical.append(value)
                axs[i,1].axvline(value,color=color,ls=':',alpha=.85)
        for j in [0,1]:
            axs[i,j].axhline(0,color='black',lw=.7);axs[i,j].grid(alpha=.2)
            axs[i,j].set(xlabel='Additional cloud attenuation (dB)',ylabel='Raw SKR (bits/use)',title=label+(' - full scan' if j==0 else ' - near crossing'))
        axs[i,0].set_xlim(0,100)
        if critical:
            axs[i,1].set_xlim(0,max(critical)*1.6)
            near=[float(r['K_raw']) for r in records if float(r['A_db'])<=max(critical)*1.6]
            low=min(near);high=max(near);axs[i,1].set_ylim(min(low-.1*(high-low),-.7*high),high+.1*(high-low))
            axs[i,1].text(.97,.04,'Crossing: '+', '.join(f'{c:.4f} dB' for c in critical),transform=axs[i,1].transAxes,ha='right',fontsize=8)
        else:
            axs[i,1].set_xlim(0,1);axs[i,1].text(.5,.92,'K_raw(0) <= 0: no positive margin',transform=axs[i,1].transAxes,ha='center',fontsize=9)
        if i==0:axs[i,0].legend(fontsize=8)
    fig.suptitle('1. Eq.(14) cloud-loss diagnostic - uncertified C,w; no security/outage certification',fontsize=13)
    save(fig,'figure_1_raw_skr_vs_cloud_attenuation')

    fig,axs=plt.subplots(1,2,figsize=(12,4.8),layout='constrained')
    for mode,title,color,style in zip(MODES,LABELS,COLORS,['-','--']):
        selected=[r for r in data if r['mode']==mode and r['A_crit_db']!='' and not r['geometry'].startswith('extended_')]
        x=[float(r['zenith_deg']) for r in selected];y=[float(r['A_crit_db']) for r in selected]
        for ax in axs:ax.plot(x,y,label=title,color=color,ls=style,marker='.',ms=3)
        extended=[r for r in data if r['mode']==mode and r['A_crit_db']!='' and r['geometry'].startswith('extended_')]
        axs[1].scatter([float(r['zenith_deg']) for r in extended],[float(r['A_crit_db']) for r in extended],marker='^',color=color,s=40)
        no_margin=[r for r in data if r['mode']==mode and r['zero_additional_margin']=='True']
        axs[1].scatter([float(r['zenith_deg']) for r in no_margin],[0]*len(no_margin),marker='x',color=color,s=40)
    axs[0].set(xlim=(0,4.35),xlabel='Zenith angle (deg)',ylabel='Diagnostic crossing (dB)',title='Centered 2 km square: 251 exact radial groups')
    axs[1].set(xlabel='Zenith angle (deg)',ylabel='Additional attenuation margin (dB)',title='Extended distances shown separately as markers')
    axs[1].text(.98,.95,'x at 0: already nonpositive at clear sky\nThese markers are NOT roots at A=0',transform=axs[1].transAxes,ha='right',va='top',fontsize=8)
    for ax in axs:ax.grid(alpha=.2);ax.legend(fontsize=8)
    fig.suptitle('2. Conditional numerical crossings - finite catalog; no continuous global optimization',fontsize=12)
    save(fig,'figure_2_threshold_vs_zenith')

    arrays=[]
    for mode in MODES:
        z=np.zeros((50,50));clear=np.zeros((50,50))
        for r in mapped:
            if r['mode']==mode:
                assert r['A_crit_db']!=''
                z[int(r['iy']),int(r['ix'])]=float(r['A_crit_db']);clear[int(r['iy']),int(r['ix'])]=float(r['clear_raw_skr'])
        arrays.append(z)
    fig,axs=plt.subplots(1,2,figsize=(11,5),layout='constrained')
    for ax,z,label in zip(axs,arrays,LABELS):
        image=ax.imshow(z,origin='lower',extent=[0,2,0,2],vmin=min(a.min() for a in arrays),vmax=max(a.max() for a in arrays),cmap='viridis',interpolation='nearest',rasterized=True)
        ax.plot(1,1,'+',color='white',ms=12,mew=2)
        ax.set(xlabel='UAV x (km)',ylabel='UAV y (km)',title=label)
    fig.colorbar(image,ax=axs,label='Conditional crossing (dB)',shrink=.88)
    fig.suptitle('3. 50 x 50 cell centers, no spatial interpolation; HAP above (1, 1) km\nCrossing bracket width <= 0.001 dB; uncertified C,w; Eq.(14) diagnostic only',fontsize=12)
    save(fig,'figure_3_critical_attenuation_map')
    np.savez_compressed(out/'threshold_maps.npz',fixed_db=arrays[0],catalog_reselected_db=arrays[1],
        x_m=(np.arange(50)+.5)*40,y_m=(np.arange(50)+.5)*40,
        scope=np.array('DIAGNOSTIC_ONLY_UNCERTIFIED_CW_NOT_CONTINUOUS_GLOBAL_OPTIMUM'))
    table=[]
    for name in ['vertical',grid_corner['geometry'],'domain_corner','extended_19.5km','extended_20km','extended_21km','extended_22km']:
        r=byname[name]
        for mode in MODES:
            s=r['searches'][mode];br=s['diagnostic_crossing_interval_db']
            table.append(f"| {name} | {r['zenith_deg']:.6f} | {r['distance_km']:.6f} | {s['clear_raw_skr']:.10g} | "+(f"[{br[0]:.6f}, {br[1]:.6f}]" if br else 'Không có positive margin')+f" | {'Fixed' if mode==MODES[0] else 'Catalog 212'} |")
    increments=[]
    for r in summaries:
        records=rows(out/(r['geometry']+'_evaluations.csv'))
        for mode in MODES:
            points=sorted((float(p['A_db']),float(p['K_raw'])) for p in records if p['mode']==mode)
            inc=max(b[1]-a[1] for a,b in zip(points,points[1:]))
            increments.append(dict(geometry=r['geometry'],mode=mode,max_upward_raw_increment=inc,
                 sampled_nonincreasing_with_1e_10_allowance=inc<=1e-10,
                 sampled_positive_reentry=r['searches'][mode]['sampled_positive_reentry']))
    with (out/'monotonicity_diagnostics.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(increments[0]));w.writeheader();w.writerows(increments)
    maxinc=max(r['max_upward_raw_increment'] for r in increments)
    reentries=sum(r['sampled_positive_reentry'] for r in increments)
    text=f'''# Ngưỡng suy hao mây: chẩn đoán Eq.(14)

Ngày 2026-11-12. **DIAGNOSTIC_ONLY_UNCERTIFIED_CW**. Người dùng đã chọn nhánh Eq14,
chấp nhận C,w chưa được chứng nhận, HAP=(1000,1000,20000)m và UAV z=1000m,
miền 2km x2km, 50x50 tâm ô (20,60,...,1980)m. Không sửa kênh/QKD cũ.

## Bảng kết quả chính

Fixed là giữ nghiệm MB tốt nhất dưới clear sky **tại từng geometry**, không phải
đường Fixed-MB nu=.25 của hình lịch sử. Catalog 212 là chọn lại tham số trong
đúng tập nguồn lịch sử được dùng ở nhánh gần nhất; không là tối ưu liên tục VA,nu.

| Hình học | Zenith (độ) | L (km) | Kraw clear (bit/use) | Bracket crossing (dB) | Chế độ |
|---|---:|---:|---:|---|---|
{chr(10).join(table)}

Ngưỡng báo cáo bằng midpoint của bracket rộng <=.001dB. Đây là độ phân giải
root của evaluator cố định; không là sai số vật lý hay chứng nhận nguồn C,w.
Các bậc và vùng màu đồng nhất trong hình2/3 phản ánh độ phân giải bracket,
không chứng minh các dải ngưỡng vật lý rời rạc. Không làm mịn bằng nội suy.
Kraw(0)<=0 được ghi không có margin dương; không gọi A=0 là nghiệm nếu Kraw(0)<0.
Góc0 đúng nghĩa thẳng đứng nằm giữa các tâm ô lưới chẵn, vì vậy được tính riêng.
Góc biên miền liên tục và góc ô xa nhất cũng được tính riêng, không nhầm hai giá trị.

## Mô hình và phép áp suy hao

Giữ nguyên Eq10 retained[0,1], AoA atom, turbulence, pointing, tau_zen.92,
D_r=.30m, lambda1550nm, full divergence35urad, jitter1.561urad, sigma_position.10m,
xi_ch=.0186, xi_det=.005, beta=.95, homodyne hiệu dụng1D, AO và phase OFF.
DM256 square16x16; VA=2*nbar, nu_repo=42.5*nu_raw. Catalog VA[.05,10],nu_raw[0,.4].
Không thay bằng GM-CV-QKD hoặc dùng công thức SKR giả định.

s=10^(-A/10); m1'=s*m1,mh'=sqrt(s)*mh,M0'=M0,P0'=P0.
t'=mh'^2; N'=(m1'-mh'^2)*VA+xi_ch*m1'+xi_det*M0.
Detector noise không bị nhân s. Giữ thiếu khối lượng của baseline, không
renormalize, không nhập lại phần đuôi clear đã loại bỏ. Không scale SKR cũ.
Tại mỗi A, tính lại MI discrete GH64/128, Eq13/14 và Holevo80/110 chữ số.
Kraw=beta*I_AB-chi_BE, giữ cả số âm. Mô hình pooled moment-matched này khác
với average K(T) của một mô hình oracle iid; không trộn hai nhánh.

## Tái sử dụng hàm cũ và giới hạn tối ưu

Import CLI cũ bị Windows Application Control chặn torch_python.dll (WinError4551).
Adapter mới thực thi nguyên các định nghĩa hàm số học đã lưu, với namespace NumPy/
SciPy/mpmath rõ ràng, không nạp DLL bị chặn, giả lập Torch, hoặc thay chính sách OS.
`adapter_validation.json` ghi hash module và tên hàm nguyên bản được dùng.
Mảng PMF/alpha được nạp từ archive đã có và khớp hash từng source; không tạo nguồn.
195 nguồn có mảng trong archive. Khôi phục thêm14bộ biên độ chỉ khi byte PMF và
biên độ khớp đúng digest nguồn cũ; không đổi tham số, không nội suy hoặc tính C,w.
Hiện có {validation['archive_sources']} bộ mảng khớp hash và {validation['unarchived_sources']}
nguồn chưa có mảng. Các nguồn thiếu chỉ được loại khi upper bound không thể thắng.
Nếu không loại được nhưng upper bound vẫn âm, chỉ biết interval raw-SKR ở vùng
âm; không dùng lower endpoint như một maximum chính xác. Nếu bound còn có thể
dương, runner dừng, không đưa ra root đầy đủ. CSV ghi catalog_maximum_resolved
và catalog_K_upper để kiểm tra riêng từng điểm.

Upper bound cổ điển I_discrete<=0.5log2(1+t*VA/(1+N)) chỉ dùng screening;
giá trị SKR báo cáo luôn dùng MI discrete nguyên bản. Eq14/Holevo vectorized để
tính bound được so với110digits cho cả212nguồn tại9checkpoints.
Nghiệm chọn được so với exhaustive{validation['archive_sources']}nguồn tại9điểm,
cộng replay{validation['archive_sources']}nguồnA0 cũ.
Sai số replayA0 tối đa {validation['saved_A0_replay_max_error']:.6g}bit/use.
Chọn catalog có tolerance1e-10bit/use và đệm bound1e-11 từ kiểm tra số học;
không gọi đây là enclosure số học interval có chứng minh hay tối ưu toàn miền.

**Experiment B liên tục VA,nu chưa hoàn tất**: không có source coverage liên tục
và Torch constructor/optimizer bị chặn. Không nội suy C,w, không tự tạo AP nguồn,
không thay kết quả finite catalog thành global optimum. Hình/CSV nhãn catalog
để so sánh kết quả phần chọn lại nguồn có thể tái lập của implementation hiện có.

## Hình học và tính toán

Tính {execution['grid_unique_radii']} nhóm bán kính chính xác đại diện2500tâmô;
do kênhđẳnghướng, các ô cùng r^2 có geometry giống nhau, không phải interpolation.
Tính thêm vertical, góc miền liên tục và L=19.5,20,21,22km tách riêng.
Tổng {execution['geometry_groups']} geometry. {execution['full_raw_sweep_groups']}nhóm
có raw sweep đủ201mứcA0..100dB/bước.5, bao gồm mọi hình học đại diện và các
checkpoint full đã hoàn tất được giữ nguyên. {execution['root_and_bound_groups']}nhóm
còn lại tính raw0..0.5dB và bisection quanh root; sau đó kiểm tra upper bound của
toàn bộ212nguồn ở200nútA=.5..100dB. Chỉ khi mọi upper bound < -1e-10 mới bỏ
phép tính MI tại những nút đã chắc chắn không cho SKR dương; nếu không, quay về
raw sweep đầy đủ. Đây là kiểm tra dấu bằng bound, không phải201giá trị raw đã tính.
CSV/summary của từng nhóm ghi scan_scope và full_range_bound_checks riêng.
Không điền giá trị raw giả tại các nút chỉ có bound. Tất cả root bracket được
đánh giá bằng MI/Holevo nguyên bản. Hình1 dùng raw sweep đầy đủ của hình học đại diện.
Số selected evaluation rows chính: {execution['main_canonical_selected_evaluations']},
thời gian lượt hoàn tất v4 {execution['seconds']:.3f}s (không gồm adapter validation,
render hoặc chi phí trước đó của {execution['reused_complete_groups']}full-sweep
checkpoints được tái sử dụng từ v3). Không diễn giải đây là chi phí chạy từ đầu.
Mỗi nhóm lưu toàn bộ evaluations và summary có moments nguồn, source identity.
Số rows không gồm các evaluation bị loại trong screening/validation, probe và
lần chạy lỗi trước đó. Hai lần chạy trước giữ riêng: lần1 không loại được nguồn
thiếu, lần2 lỗi serialize NumPy boolean ở export; không đổi vật lý hoặc tolerance.
Input/provenance và design receipt khóa lựa chọn người dùng và thông số trước run.

## Monotonicity và outage

Upward step raw lớn nhất trong tất cả các điểm đã đánh giá: {maxinc:.9g} bit/use;
số đường có positive re-entry quan sát được: {reentries}.
`monotonicity_diagnostics.csv` ghi cả kiểm tra strict từ scanner và kiểm tra
allowance1e-10bit/use. Nếu raw tăng ở vùng âm, không được gọi raw là monotonic.
Một crossing không tự chứng minh không có crossing giữa các nút chưa đánh giá.
Quy tắc chính xác theo evaluator vẫn là b=1[Kraw<=0]. Bản đồ crossing này chỉ
là margin chẩn đoán theo geometry, không được tích hợp thành outage chính thức.
Ngưỡng thay theo vị trí; không chọn một số toàn cục tùy ý. Nếu cần conservative
margin cho miền, lấy minimum có điều kiện từ bản đồ và nêu giả định tương ứng,
không coi đó là hằng số khí tượng hoặc ngưỡng bảo mật phổ quát.

## Tệp và xác minh

critical_thresholds.csv; critical_threshold_map.csv (5000 mode-position rows);
threshold_maps.npz; geometry_jobs.json; mỗi geometry_evaluations.csv và_summary.json;
adapter_validation.json; execution_summary.json; design_receipt/protected_inputs;
unit_tests.log, verification.json, artifact_hashes.json và3PNG400dpi/PDF.
Lệnh từ project root (run mới từ đầu không cần checkpoint trước):

```powershell
.\\.venv\\Scripts\\python.exe -X utf8 -B scripts/run_eq14_cloud_threshold.py --output results/cloud_threshold_eq14_new --workers 6
.\\.venv\\Scripts\\python.exe -X utf8 -B scripts/report_eq14_cloud_threshold.py results/cloud_threshold_eq14_new
```

Runner cần namespace mới, giữ checkpoint theo geometry; không ghi kết quả cũ.
Không chạy full repo tests, sourceCw generation, finite-size, security/publication
evaluation, final-test/heldout, training hoặc ObjectiveC. Frozen model, các cache
và gói mây cũ giữ nguyên. Cw vẫn INSUFFICIENT_EVIDENCE, E2INCONCLUSIVE,
strictPhaseBfalse, UNVALIDATED_SECURITY_MODEL, NOT_READY_FOR_PUBLICATION_SCALE_RUNS.
Đây là bản đồ ngưỡng theo tọa độ UAV. Khi tích hợp tương lai phải lấy A_cloud
tại giao điểm qc của tia với lớp mây; không tự lấy A_cloud tại xy của UAV.
'''
    (out/'report_vi.md').write_bytes(text.encode())
    (out/'README.md').write_bytes(b'# Eq14 cloud attenuation diagnostic\n\nRead report_vi.md and execution_summary.json.\nFixed and reselected finite 212-source catalog only; continuous global reoptimization NOT_RUN.\nUncertified Cw; never an operational/security outage threshold.\n\nData: critical_thresholds.csv, critical_threshold_map.csv, threshold_maps.npz, geometry-level CSV/JSON and artifact_hashes.json.\n')
    (out/'render_receipt.json').write_bytes((json.dumps(dict(plotter_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),figures=plots,PNG_dpi=400,saved_data_only=True),indent=2)+'\n').encode())


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',type=Path);report(p.parse_args().output.resolve())
