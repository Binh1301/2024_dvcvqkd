# Figures 4–7 từ kết quả numerical diagnostic Phase6A

Đã tạo Fig.4,5,7 ở mức trình bày IEEE, từ dữ liệu đã niêm phong; **không nâng chúng thành paper-ready scientific evidence**. Fig.6 chưa có thí nghiệm energy sweep phù hợp nên không có ảnh thay thế.

Source chính: [Phase6A RSS retry](../results/phase6a_baseline_20261109_rss_retry_20261110/), [báo cáo thí nghiệm](phase6a_baseline_numerical_experiment_vi.md). Renderer: [phase6a_figures.py](../src/uav_qkd/phase6a_figures.py). Output: [results/paper_figures/phase6a](../results/paper_figures/phase6a/).

## Sai khác trong yêu cầu và dữ liệu có thẩm quyền

- Pasted context ghiΔt1s vàK1000slots. Config,scenario.npz,timestamp CSV/JSON gốc đều dùng **Δt10s,K100slots,T1000s**. Không resample hoặc đổi thời gian để phù hợp mô tả sai.
- Không có saved endpoint999s. Snapshot dùng0,300,1000s. Snapshot0 là đánh giá lại LOS từ **hệ số mây đã lưu**, không phải thêm slot0 vào finite-size accounting.
- P1/P2 có các selected results riêng. Kiểm tra cho thấy cả bốn phương pháp có cùng path_indices choP1vàP2 trong dataset này; cả hai chọnK100. Fig.4/5/7 **dùngP2**; không ghép curveP1 với terminalP2.
- Null Python allocation peak trong RSS retry không phải0. Không vẽ runtime/memory hoặc dùng số allocation thiếu. Lỗi sampling child đã được báo cáo ở Phase6A; các hình hiện tại không phụ thuộc telemetry đó.

## Figure 4 — UAV trajectories under dynamic cloud blockage

Files: [PDF](../results/paper_figures/phase6a/fig4_dynamic_cloud_trajectories.pdf), [SVG](../results/paper_figures/phase6a/fig4_dynamic_cloud_trajectories.svg), [PNG600dpi](../results/paper_figures/phase6a/fig4_dynamic_cloud_trajectories.png), [provenance](../results/paper_figures/phase6a/fig4_dynamic_cloud_trajectories.json).

Ba panel0/300/1000s, vùng UAV cố định[0,2000]²m. Trục vẽkm, chuyển đúng từm. Paths là các endpoint đã lưu đến snapshot, không phải đường mới tối ưu; marker hiện tại giữ nguyên tọa độ, dùng nested hollow markers khi trùng. Initial UAV và HAP projection trùng(1000,1000)m. Tại300s, các current positions vẫn trùng; đó là dữ liệu thực, không dịch marker để tạo khác biệt giả.

Nền xám là **blocked HAP→UAV LOS tại các tọa độ UAV**, không phải CLWC ngay trên đầu/endpoint UAV. Dùng400Gaussian coefficients từcloud_realization.npz, seed20261108, drift(-5,0)m/s, threshold15mg/m³ đã frozen, clipping15, slab2000..4000m, vertically uniform trongslab. Reuse `CloudField`, `BlockageModel.projected_segment` và `phase6a_experiment.los_samples` với spacing20m theo segment3D.

Lưới hình50×50cell-centers,40m/cell, tách khỏi movement graph11×11spacing200m. Đây là phép lấy mẫu **chỉ để hiển thị**, không sinh realization hoặc chạy optimizer. Mặt nạ tại121graph nodes ở300/1000s khớp chính xác savedz (242comparisons). Lưu các mặt nạ và tọa độ trong [fig4_los_maps.npz](../results/paper_figures/phase6a/fig4_los_maps.npz).

Quan trọng khi đọc: đường lịch sử đi qua một vùng xám ởsnapshot1000s **không đồng nghĩa** UAV đã bịblock khi đi qua đó ở thời điểm trước. LOS được xét theo cảpositionvàtime. Đường nối endpoint không chứng nhận clearLOS liên tục giữa các slot.

## Figure 5 — Accumulated finite-size key-yield proxy

Files: [PDF](../results/paper_figures/phase6a/fig5_accumulated_key_vs_time.pdf), [SVG](../results/paper_figures/phase6a/fig5_accumulated_key_vs_time.svg), [PNG600dpi](../results/paper_figures/phase6a/fig5_accumulated_key_vs_time.png), [provenance](../results/paper_figures/phase6a/fig5_accumulated_key_vs_time.json).

Vẽ trực tiếp các saved prefix `key_bits`, thêm initial accumulated value0 tại0s. Kiểm từngprefix bằng `finite_key` hiện có với m0=800000 vàepsilon3e-8; cloud erasure dùng đúng một lần trongn,S. Không lấy average terminalrate nhân thời gian hoặc thay bằngasymptotic contribution. Nguồn plot từng điểm: [fig5_plotted_data.csv](../results/paper_figures/phase6a/fig5_plotted_data.csv).

| Method | First positive proxy (s) | Terminal key (bits) | Average at1000s(bits/s) |
|---|---:|---:|---:|
| Stationary | 880 | 25160.230296656 | 25.160230297 |
| SKR-Greedy | 840 | 33623.045287247 | 33.623045287 |
| Energy-Aware Greedy | 850 | 33276.467693714 | 33.276467694 |
| Pareto DP (forecast oracle) | 650 | 77040.107779909 | 77.040107780 |

Các đoạn đầu bằng0 và onset khác nhau là kết quả proxy có overhead finite-size; đường không tuyến tính. Terminal và từngobjective được kiểm theo actual missionduration, với average=key/duration. Không có discrepancy vượt tolerance1e-12relative/1e-8absolute.

## Figure 6 — PENDING matched energy-budget experiments

Không tạoPDF/SVG/PNG choFig.6. [BLOCKED manifest](../results/paper_figures/phase6a/fig6_energy_budget_sensitivity.json) cóoutputs={} và danh sách file đã kiểm.

Đã tìm toàn bộ`results/**/sensitivities.csv` và kiểm các`results.json` có method runs. BaCSV sensitivity88rows/file thuộcdemo_verified,final_demo,synthetic_demo: energy500/1000/1500J, scenario/rate/model khác; một file cũ thiếudata_status. approximate_smoke cũng chỉ làdemo1500J. HaiPhase6Aattempt cùngbudget185332.63951519027J; lần đầufullDPfailed, lần saucomplete. Không coi haiattempt cùngbudget làhai điểm sweep hoặc dùngdemo để lấp curve.

Đã có `plot_fig6`, `load_energy_sweep`, schema [energy_sweep_schema.json](../results/paper_figures/phase6a/energy_sweep_schema.json). Input descriptor cho tương lai:

```json
{
  "schema_version": 1,
  "runs": [
    {"directory": "relative/path/to/first/real/sealed/budget/run"},
    {"directory": "relative/path/to/second/real/sealed/budget/run"}
  ]
}
```

Các chuỗi trên chỉ minh họa **cấu trúc path**, không phải các thí nghiệm đã chạy. Mỗi directory phải cóPhase6A-format config/results/scenario/cloud coefficients/trajectoryCSVs/input/output manifests với bốn method vàP1/P2 đầy đủ. Renderer kiểmseals, quantities, khácEmax, cùngnon-budget config vàarrays (graph,costs,rates,z,dt,m0,epsilon,q0,cloud), khớpPhase6A reference. Không nhậnCSV demo hoặc tự phát sinh rates/paths thiếu. `fig6_plotted_data.csv` sẽ ghibudget,method,objective,K_slots,duration_s,objective_value vàsource; panel(a)dùngP1bits/s, panel(b)dùngP2bits.

Thí nghiệm cần xin phép tiếp theo: **cùng scenario hiện tại**, sweepEmaxđề nghị90,110,130,150,165,175,185.332639515kJ; giữhorizon1000s,dt10s,graph,lookup,cloudcoefficients/threshold,rotor,finite-size,λprior vàforecast policy. Chạy đủbốnmethod/P1/P2; lưu cảzero-yield/infeasible/failure, không retunecloud hoặcλ khi nhìn kết quả.

Đây chỉ làbudget candidates để thu thập dữ liệu, **chưa được phê duyệt và chưa cóoutcomes**. Cơ sở chọn miền: hover1000s cần168.484217741kJ; maxallowededge×100=178.289389735kJ, nên185.333kJ lànonbinding. Cácbudget thấp hơn tạoenergy-limitedprefix opportunities, nhưng không giả định tất cả sẽ cho positive key haymethod nào thắng. Minimumpositive valid-signal requirement và cloud avoidance có thể làm cácbudget thấp chozero. Không chạy sweep trong tasknày.

## Figure 7 — Energy–key scatter at one budget

Files: [PDF](../results/paper_figures/phase6a/fig7_energy_key_tradeoff.pdf), [SVG](../results/paper_figures/phase6a/fig7_energy_key_tradeoff.svg), [PNG600dpi](../results/paper_figures/phase6a/fig7_energy_key_tradeoff.png), [provenance](../results/paper_figures/phase6a/fig7_energy_key_tradeoff.json).

Bốn điểmP2, energy=recordedJ/1000, key=recordedbits. Không nối thành frontier hoặc tuyên bố DP dominance theo cảhai axes. Percent labels làsampled clear-LOS slotfraction. Nguồn [fig7_plotted_data.csv](../results/paper_figures/phase6a/fig7_plotted_data.csv).

| Method | Propulsion energy(kJ) | Clear slots | Modeled blocked-slot duration(s) | Key/propulsion energy(bits/J) |
|---|---:|---:|---:|---:|
| Stationary |168.484217741|77/100|230|0.149332861|
| SKR-Greedy |169.660838380|81/100|190|0.198177998|
| Energy-Aware Greedy |169.170579781|81/100|190|0.196703633|
| Pareto DP |170.641355580|100/100|0|0.451473838|

Denominator của metric phụ là **propulsion energy của selected trajectory**, không gồmcommunication/computation/battery losses không có trongmodel. Duration ở đây làblocked slotcount×10s theo mô hình rời rạc, không phải chứng nhận LOS liên tục theo thời gian.

## Diễn giải khoa học

DP giữ100clear slots, so với77/81/81 của baselines, và được cấp quyền nhìn trước toàncloud horizon. Cảba thuật toán di chuyển đều rờiq0 lần đầu ở380s khi sampledLOS tạiq0 đãblock; vì vậy không diễn giải hình như bằng chứng DP khởi hành sớm hơn baselines trước khi mây tới. DP chọn chuỗi đường dựa trên forecast, nhưng chưa cóablation tách tác động quyền thông tin. Mean rawclear-use rates lần lượt.004955338,.004952076,.004946728,.004952883bits/use; DP không cóclear-channel rate tốt hơnStationary. Dữ liệu hỗ trợ kết luận phần lớn chênh lệch key đi cùng nhiềuvalid signals/ítcloud erasure hơn và đáp ứngphi tuyến củafinite-size proxy; không gán toàngain cho thuật toán trong equal-information setting.

So vớiStationary, DP thêm51879.877483253proxybits và2157.137838622Jpropulsion (energy+1.2803%,key+206.1979%) trong **scenario duy nhất này**. Đó là trade-off: DP dùng nhiềuenergy hơn, không dominate vềenergy. Không chứng nhận real-time feasibility từruntime này.

P1vàP2 cùng chọn1000s vì savedprefix scan của từngmethod đạtmaxcủa cảaveragevàtotal tạiendpoint đó. Proxy dương muộn và khả năng tiếp tục thu valid signals khiến kết quả này hợp lý trongdataset; không chứng minh haiobjectives tương đương tổng quát hoặc luôncùng stoppingtime. Budget đangnonbinding; cầnFig.6 mới khảo sát ảnh hưởngbudgetchặt.

Các hình là **numerical diagnostic, presentation-quality**, không composable-security proof, không continuous-space/global MB optimum certificate, không practical deployment guarantee. Paper/source/security readiness vàcatalog cũ giữ nguyên.

## Tái tạo, LaTeX và kiểm chứng

Chạy từpackage root, yêu cầuoutput mới hoặc trống:

```powershell
$env:PYTHONPATH='src'
python -X utf8 -B -m uav_qkd.phase6a_figures --output results/paper_figures/NEW_EXPORT
# Chỉ sau khi có dữ liệu sweep thật:
python -X utf8 -B -m uav_qkd.phase6a_figures --output results/paper_figures/NEW_SWEEP_EXPORT --energy-sweep PATH_TO_SWEEP_JSON
```

LaTeX: [figures_ieee.tex](../results/paper_figures/phase6a/figures_ieee.tex), caption text [captions.tex](../results/paper_figures/phase6a/captions.tex) vàper-figure.caption.txt. Dùng`graphicx`; setgraphicspath tớioutputdirectory hoặc copyPDF vào manuscriptassets. Fig.4 dùngfigure*/textwidth7.16in; Fig.5/7 dùngfigure/columnwidth3.5in. Không tự sửa manuscript. SVGtext editable; heatmap binaryrasterized cònaxes/paths/text ởvector. PNG600dpi; không cóoversizedfiguretitle.

Source loader kiểm22files sealcoverage,7inputhashes,32exact executed producers (archive phù hợp choPhase6Aproducer đã sửa riêngtelemetry), CSV/JSON/NPZ và800prefix quantities. Mỗi hình cósource filehashes,renderdependencyhashes,softwareversions,units,objective,caption,PNGdpi,figsize,outputhashes; BLOCKEDfigure không cóimage.

Visual QA đã kiểmPNGs: sửaFig.4text collision cótestbounding-boxRED→GREEN; chuyểnP2label vàolegendFig.5, giảmtickdensityFig.7, giữtọa độendpointkhi markers trùng. [Independent review](phase6a_figures_independent_review.md) PASS. Fullsuite: **215passed in72.14s,0failed,0errors,0skipped**, gồm206tests có sẵn và9case mới; lệnh `python -X utf8 -m pytest -q --junitxml=docs/phase6a_figures_validation/tests.xml`. **1327file có trước không thay đổi**,23output files được hash-seal; [verification receipt](phase6a_figures_validation/verification.json). Không optimizer,SKRregeneration,paper-mode hoặc sensitivity simulation nào được gọi; không commit/push.
