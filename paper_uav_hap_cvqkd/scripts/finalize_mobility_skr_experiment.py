"""Independent saved-data validation and Vietnamese mobility report; no SKR run."""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path
import sys
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from scripts import run_ao_effective_channel_no_fading_noise_reference as saved
from scripts.run_mobility_skr_experiment import DEFAULT, SCHEMES, scenario, validate_settings
from src.mobility_skr import objective_key


def csv_rows(path):
    with path.open(encoding="utf-8",newline="") as stream:return list(csv.DictReader(stream))


def main():
    output=DEFAULT/"full"
    manifest=saved.read_json(DEFAULT/"startup_manifest.json")
    receipt=saved.read_json(output/"experiment_receipt.json")
    if receipt["status"]!="CURRENTLY_VERIFIED_PASS":raise ValueError("Full diagnostic is incomplete")
    if (DEFAULT/"final_validation.json").exists():raise ValueError("Final validation already exists")
    for name,want in receipt["output_sha256"].items():
        if saved.digest(output/name)!=want:raise ValueError(f"Output hash mismatch: {name}")
    inputs=saved.read_json(output/"inputs.json");settings=inputs["settings"]
    if saved.digest(ROOT/"scripts/run_mobility_skr_experiment.py")!=inputs["producer_sha256"]:
        raise ValueError("Runner changed since execution")
    for name,want in inputs["scientific_identity"]["scientific_implementation"].items():
        if saved.digest(ROOT/name)!=want:raise ValueError(f"Scientific producer changed: {name}")
    test=saved.read_json(DEFAULT/"test_receipt.json")
    if test["status"]!="CURRENTLY_VERIFIED_PASS" or test["test_count"]!=15:
        raise ValueError("Scoped test prerequisite is absent")
    if saved.digest(DEFAULT/"test_output_retry.txt")!=test["output_sha256"] or saved.digest(ROOT/"tests/test_mobility_skr.py")!=test["test_producer_sha256"]:
        raise ValueError("Scoped test evidence has changed")
    smoke=saved.read_json(DEFAULT/"smoke/experiment_receipt.json")
    if smoke["status"]!="CURRENTLY_VERIFIED_PASS" or smoke["candidate_evaluations"]!=30:
        raise ValueError("Smoke prerequisite is absent")
    all_rows=csv_rows(output/"all_candidate_evaluations.csv")
    winners=csv_rows(output/"optimized_state_sources.csv")
    roster=csv_rows(output/"source_roster.csv")
    sources={r["ensemble_hash"]:r for r in roster}
    states=saved.read_json(output/"channel_states.json")
    if (len(all_rows),len(winners),len(sources),len(states))!=(39400,200,197,200):
        raise ValueError("Requested finite-catalog/state coverage is incomplete")
    original=csv_rows(ROOT/"results/exact_source_moments_catalog_20261012/all_182_MB_exact_source_moments.csv")
    original_sources={r["cache_key"] for r in original}
    if len(original_sources)!=182 or not original_sources<={r["source_cache_key"] for r in sources.values()}:
        raise ValueError("Original 182 MB sources are not all preserved in the expanded catalog")
    journal={}
    with (output/"objective_cache.jsonl").open(encoding="utf-8") as stream:
        for line in stream:
            record=json.loads(line)
            if record["row_sha256"]!=saved.hash_json(record["row"]) or record["key"] in journal:
                raise ValueError("Objective journal row/hash corruption")
            journal[record["key"]]=record["row"]
    state_map={(s["position_index"],s["blocked"]):s for s in states}
    maximum={};counts={};gh_maximum={};max_entropy_residual=0.;max_spectrum_residual=0.;minimum_uncertainty=math.inf
    omega=np.array([[0,1,0,0],[-1,0,0,0],[0,0,0,1],[0,0,-1,0]])
    def g(lam):
        n=(lam-1)/2
        return 0. if n==0 else (n+1)*math.log2(n+1)-n*math.log2(n)
    for row in all_rows:
        pair=(int(row["position_index"]),row["blocked"]=="True")
        source=sources[row["ensemble_hash"]];state=state_map[pair]
        record=journal[row["objective_key"]]
        if any(row[k]!=source[k] for k in ("nu_raw","V_A","C","w","source_cache_key","source_path")):
            raise ValueError("Source moments/parameters changed across channel states")
        candidate={k:float(source[k]) for k in ("nu_raw","V_A","C","w")}
        candidate.update(ensemble_hash=source["ensemble_hash"],source_cache_key=source["source_cache_key"])
        payload_hash=saved.digest(ROOT/source["source_path"])
        expected=objective_key(inputs["scientific_identity"],state,candidate,payload_hash)
        if expected!=row["objective_key"]:raise ValueError("Complete physical/source cache key differs")
        for name in ("nu_raw","V_A","C","w","I_AB","chi_BE","SKR","T_eff","xi_eff","N_eff","a","b","Z_star","lambda_1","lambda_2","lambda_3"):
            if float(row[name])!=record[name]:raise ValueError(f"CSV/journal {name} mismatch")
        t,va,a,b,z=[float(row[k]) for k in ("T_eff","V_A","a","b","Z_star")]
        if abs(float(row["SKR"])-(.95*float(row["I_AB"])-float(row["chi_BE"])))>1e-14:
            raise ValueError("Signed SKR identity failed")
        if t!=state["moments"]["mean_sqrt_eta"]**2 or float(row["xi_eff"])!=.0186:
            raise ValueError("Gaussian transmission/noise identity failed")
        if abs(a-(1+va))>1e-13 or abs(b-(1+t*(va+.0186)))>1e-13:
            raise ValueError("Gaussian covariance identity failed")
        lambdas=[float(row[k]) for k in ("lambda_1","lambda_2","lambda_3")]
        if min(lambdas)<1:raise ValueError("Nonphysical symplectic spectrum")
        covariance=np.array([[a,0,z,0],[0,a,0,-z],[z,0,b,0],[0,-z,0,b]])
        spectrum=np.sort(np.abs(np.linalg.eigvals(1j*omega@covariance)))
        expected_spectrum=np.array(sorted([lambdas[0]]*2+[lambdas[1]]*2))
        max_spectrum_residual=max(max_spectrum_residual,float(np.max(np.abs(spectrum-expected_spectrum))),abs(lambdas[2]-(a-z*z/(b+1))))
        minimum_uncertainty=min(minimum_uncertainty,float(np.linalg.eigvalsh(covariance+1j*omega).min()))
        max_entropy_residual=max(max_entropy_residual,abs(float(row["chi_BE"])-(g(lambdas[0])+g(lambdas[1])-g(lambdas[2]))))
        counts[pair]=counts.get(pair,0)+1
        if pair not in maximum or float(row["SKR"])>float(maximum[pair]["SKR"]):maximum[pair]=row
        for refinement in record["MI_orders"]:
            order_pair=(*pair,refinement["order"])
            if order_pair not in gh_maximum or refinement["SKR"]>gh_maximum[order_pair][0]:
                gh_maximum[order_pair]=(refinement["SKR"],row["ensemble_hash"])
    if any(v!=197 for v in counts.values()) or len(journal)!=39400:
        raise ValueError("Cache/state candidate counts differ")
    if max_spectrum_residual>1e-12 or max_entropy_residual>1e-12 or minimum_uncertainty < -1e-12:
        raise ValueError("Independent covariance/entropy check failed")
    winning_table=[[None,None] for _ in range(100)]
    for row in winners:
        pair=(int(row["position_index"]),row["blocked"]=="True")
        if row["objective_key"]!=maximum[pair]["objective_key"]:
            raise ValueError("P1 selected row is not the finite-catalog maximum")
        winning_table[pair[0]][int(pair[1])]=dict(journal[row["objective_key"]],objective_key=row["objective_key"])
    for state in states:
        m=state["moments"]
        if not (0<=m["mean_sqrt_eta"]**2<=m["mean_eta"]<=1) or abs(m["physical_probability_mass"]-1)>1e-10:
            raise ValueError("Cloud physical-law normalization/moments failed")
        if abs(m["mean_eta_xi_total"]-(2+(.0186-1)*m["mean_eta"]))>1e-12:
            raise ValueError("Detector noise was not kept consistent")
    comparisons,series,*_=scenario(settings,validate_settings(settings),winning_table)
    csv_summary=csv_rows(output/"summary.csv")
    for original,independent in zip(csv_summary,comparisons):
        for key in ("average_skr_bits_per_use","total_flight_distance_m","penalized_objective_bits_per_use","qkd_availability_percent"):
            if abs(float(original[key])-independent[key])>1e-12:raise ValueError("Independent P2/DP summary differs")
    fig_checks=[]
    for png in sorted(output.glob("figure_*.png")):
        with Image.open(png) as image:
            if min(image.info["dpi"])<299.9:raise ValueError("Figure below 300 dpi")
            size=image.size
        pdf=png.with_suffix(".pdf");data=pdf.read_bytes()
        if not data.startswith(b"%PDF") or b"/Subtype /Image" in data:
            raise ValueError("Missing or non-vector PDF")
        fig_checks.append(dict(png=png.name,pdf=pdf.name,size=size,PNG_sha256=saved.digest(png),PDF_sha256=saved.digest(pdf)))
    if len(fig_checks)!=6:raise ValueError("Six figures were not exported")
    gh_checks=[dict(position_index=j,blocked=b,
        winners={str(order):gh_maximum[(j,b,order)][1] for order in (8,16,32)},
        GH16_32_stable=gh_maximum[(j,b,16)][1]==gh_maximum[(j,b,32)][1]) for j,b in sorted(state_map)]
    if not all(r["GH16_32_stable"] for r in gh_checks):
        raise ValueError("Finite-catalog winner changes under GH16/32 refinement")
    validation=dict(status="CURRENTLY_VERIFIED_PASS",checked_utc=datetime.now(timezone.utc).isoformat(),
        validation_scope="Saved-data check only; no source, MI or Holevo rerun",candidate_evaluations=39400,
        unique_source_candidates=197,original_182_sources_preserved=True,physical_states=200,
        finite_catalog_maxima_verified=200,independent_P2_DP_summaries_match=True,GH_winner_checks=gh_checks,
        maximum_entropy_residual=max_entropy_residual,maximum_symplectic_spectrum_residual=max_spectrum_residual,
        minimum_uncertainty_eigenvalue=minimum_uncertainty,figures=fig_checks,
        current_test_count=15,smoke_evaluations=30,protected_files=len(manifest["protected_hashes"]),
        protected_changes=saved.verify_protected(manifest),input_sha256=saved.digest(output/"inputs.json"),
        experiment_receipt_sha256=saved.digest(output/"experiment_receipt.json"),
        verifier_sha256=saved.digest(Path(__file__)),plotter_sha256=saved.digest(ROOT/"scripts/plot_mobility_skr_results.py"))
    saved.save(DEFAULT/"final_validation.json",validation,exclusive=True)
    lines=["# Tối ưu vị trí UAV và nguồn MB dưới mây chuyển động", "", "Ngày 2026-10-14. CURRENTLY_VERIFIED_PASS cho mô phỏng minh họa; không phải chứng nhận bảo mật hoặc kết quả final-test.","",
        "Đã hoàn tất: 100 vị trí, 30 slot × 20 s, 197 nguồn MB (giữ đủ 182 nguồn gốc), 200 trạng thái sạch/có mây, 39.400 phép đánh giá. Không tính C,w mới; không AP/AO hoặc nội suy. 15 tests và smoke 30 phép đánh giá đã đạt trước lượt đầy đủ.","",
        "| Phương án | SKR trung bình (bits/use) | Khả dụng (%) | Quãng bay (m) | Tăng so S1 (%) | Tăng so S2 (%) | Mục tiêu riêng (bits/use) |", "|---|---:|---:|---:|---:|---:|---:|"]
    for r in comparisons:
        lines.append(f"| {r['scheme']} | {r['average_skr_bits_per_use']:.10g} | {r['qkd_availability_percent']:.6g} | {r['total_flight_distance_m']:.9g} | {r['improvement_vs_S1_percent']:.6g} | {r['improvement_vs_S2_percent']:.6g} | {r['penalized_objective_bits_per_use']:.10g} |")
    stationary=next(r for r in series if r["scheme"]==SCHEMES[1])
    lines.extend(["",f"S2 chọn vị trí cố định ({stationary['x_m']:g}, {stationary['y_m']:g}) m. S4 dùng lambda={settings['optimization']['positive_lambda_bits_per_use']:g} bits/use, D_ref={settings['optimization']['reference_distance_m']:g} m. Mục tiêu có phạt và SKR trung bình là hai đại lượng riêng; cột mục tiêu riêng của S1–S3 có lambda=0. CSV còn lưu objective_at_common_positive_lambda để so sánh cùng mục tiêu.","",
        "Hình học minh họa: h_H=20 km, h_U=1 km, UAV tham chiếu (450,450) m, HAP (11419.65511459133,450) m. Tọa độ này giữ đúng L_ref=21.9393102292 km; azimuth +x là giả định minh họa vì repo không có tọa độ HAP thực tế. Mây giả lập ở 5 km, bán kính 420 m, suy hao 10 dB, tâm đầu (2093.7168662297537,450) m, vận tốc (3,0) m/s. Các tham số này không phải đo đạc thời tiết.","",
        "Tái sử dụng derive_physical_inputs, LiteralChannel.from_physical, PhysicalFadingDistribution.moments, authenticate/evaluate_authenticated, canonical MB và normalization, deterministic_mutual_information, _holevo_from_source_moments và covariance hiện có. Tệp audit.json lưu đường dẫn/hash; code_equation chi tiết có trong báo cáo SKR trước. Ba mômen/PDF Eq. (10)/C,w/ensemble và Eq. (20) giữ nguyên producer.","",
        "T_cloud=10^(-A_c b/10) nhân đúng một lần vào eta_atm của luật thô. Sau đó áp dụng conditioning active trên 0<T<=1 và giữ atom AoA. Đây không phải nhân trực tiếp cả ba mômen đã chuẩn hóa; thay đổi tail/normalizer được tính lại. Mômen thứ ba vẫn bằng 2+(xi_ch−1)mean_eta, không nhân phần shot/detector noise với suy hao mây.","",
        "Mô hình SKR là effective_channel_no_fading_noise: T_eff=mean_sqrt_eta², xi_eff=0.0186, N_eff=T_eff xi_ch, a=VA+1, b=1+T_eff(VA+xi_ch), Z*=2sqrt(T_eff)C−sqrt(2T_eff xi_ch w). Ideal heterodyne R=1, xi_det=0, chi_het=1, beta=0.95; phase/adaptive optics OFF. MI discrete 256-QAM mới GH8/16/32 và Holevo direct Z_star dùng cùng ensemble/noise. Đây là xấp xỉ Gaussian bỏ phương sai fading, chưa là security lower bound của kênh fading.","",
        "P1 vét cạn nguồn MB ở mỗi vị trí/trạng thái; giữ signed K trong all_candidate_evaluations.csv và dùng S=max(0,K) cho bảng tiện ích. P2 tối đa trung bình theo vị trí cố định. P3 dùng DP với d<=15×20=300 m mỗi bước, vị trí đầu tự chọn, không tính chi phí triển khai. Mục tiêu là mean(S)−lambda D_fly/D_ref, không phải mô hình năng lượng và không báo joule/bits/J. Cùng catalog và quy tắc đổi nguồn mỗi slot cho cả bốn phương án. Khả dụng ở bảng là tỷ lệ slot có S>0, không phải xác suất không-outage AoA hoặc bằng chứng cấp khóa vận hành. P1 và DP tách được vì nguồn không có ràng buộc ngân sách liên-slot hoặc chi phí đổi tham số trong mô hình này.","",
        "Đã chạy năm vận tốc mây 0.5,1.5,3,4.5,6 m/s và tám lambda 0,0.0005,0.001,0.002,0.005,0.01,0.02,0.05 bits/use. Bảng hai trạng thái tại mỗi vị trí được tái sử dụng chính xác vì mọi thống kê khác độc lập thời gian/vận tốc trong mô hình binary này. Quỹ đạo mây là dữ liệu minh họa biết trước; không triển khai dự báo hoặc học máy.","",
        "Không có channel-use rate giả định: cumulative_skr_contributions=sum(S_n), hiển thị bits/use-slot. Không gọi số này là tổng bit khóa thực tế. Nếu cấu hình channel_use_rate_per_s, xuất thêm cumulative_secret_bits=rate×Delta_t×sum(S_n), vẫn chỉ là ước lượng theo functional đang dùng.","",
        f"Kiểm tra độc lập toàn bộ dữ liệu: 200 cực đại P1; cache keys/hash và cùng C,w; PDF normalization/moment ordering; a,b,Z,K; uncertainty matrix và spectrum. Max residual spectrum={max_spectrum_residual:.6g}, entropy={max_entropy_residual:.6g}. DP khớp vét cạn 3 vị trí/4 slot trong test; nghiệm toàn bộ khớp tái dựng DP. S2≥S1, S3≥S2; objective S4≥stationary cùng lambda. {validation['protected_files']} file cũ không đổi hash.","",
        "Giới hạn: cực đại chỉ trong 100 điểm và 197 nguồn được tính số, không phải tối ưu liên tục/toàn cục của hệ vật lý. C,w và GH có kiểm tra số nhưng chưa có enclosure tổng sai số chặt. Cloud là đĩa phẳng suy hao nhị phân, CSI/lịch mây biết trước, thống kê turbulence/pointing cố định tại từng vị trí; không fluid dynamics. Đánh giá rate tại vị trí slot, bỏ diễn biến link giữa các cell, trễ reacquisition, overhead đổi nguồn và chi phí triển khai. Không đánh giá năng lượng đẩy thực tế.","",
        "Khác đoạn Overleaf tham khảo: triển khai phạt quãng đường theo yêu cầu đính kèm, không P_hov/e_mov/E_ref. Không sửa tệp TeX/PDF bên ngoài. PDF được hash-bound nhưng chưa trích xuất full text vì thiếu PDF parser; các công thức triển khai lấy từ task đính kèm và đoạn TeX người dùng cung cấp.","",
        "15 tests bao phủ A_c=0, hình học/biên/altitude mây, source/catalog/ref SKR, P2, DP-vét cạn, tốc độ, dominance, signed-negative handling, journal reuse/corruption và cache context. Lượt đầu bắt lỗi serialize UavMotion và assertion thừa rằng toàn lưới sạch ở slot đầu; sửa serializer và kiểm tra đúng reference ray đi vào/ra, không đổi physics để ép kết quả. Lưu log lỗi ban đầu và receipt lượt đạt.","",
        "Chạy từ paper_uav_hap_cvqkd bằng PowerShell:","", "```powershell", "& .venv/Scripts/python.exe -m unittest tests.test_mobility_skr -v",
        "& .venv/Scripts/python.exe scripts/run_mobility_skr_experiment.py --smoke --output results/mobility_demo_rerun",
        "& .venv/Scripts/python.exe scripts/run_mobility_skr_experiment.py --output results/mobility_demo_rerun", "```","",
        "Runner dùng cache journal cùng identity nếu cần tiếp tục lượt chưa xong; từ chối ghi đè lượt đã có experiment_receipt.json. Chỉnh tham số trong configs/mobility_aware_skr_demo.json và dùng output mới để giữ provenance.","",
        "Tệp mới: src/uav_mobility.py, src/mobility_skr.py, scripts/run_mobility_skr_experiment.py, scripts/plot_mobility_skr_results.py, scripts/finalize_mobility_skr_experiment.py, tests/test_mobility_skr.py, configs/mobility_aware_skr_demo.json. Scientific kernels/security functional/frozen specification và mọi cache/result cũ không đổi.","",
        "Artifacts: [summary.csv](../results/mobility_aware_skr_20261014/full/summary.csv), [time series](../results/mobility_aware_skr_20261014/full/scheme_time_series.csv), [bảng SKR](../results/mobility_aware_skr_20261014/full/skr_table.csv), [final validation](../results/mobility_aware_skr_20261014/final_validation.json).", ""])
    for check in fig_checks:
        lines.append(f"- [{check['png']}](../results/mobility_aware_skr_20261014/full/{check['png']}) / [PDF](../results/mobility_aware_skr_20261014/full/{check['pdf']})")
    lines.extend(["", "Lifecycle NOT_READY_FOR_PUBLICATION_SCALE_RUNS và frozen-hash mismatch cũ vẫn giữ. Không training, held-out/final-test/publication evaluation, AP/AO, source generation, commit hoặc push. STOP sau báo cáo minh họa này.", ""])
    report=ROOT/"docs/MOBILITY_AWARE_SKR_REPORT_VI.md"
    with report.open("x",encoding="utf-8",newline="\n") as stream:stream.write("\n".join(lines))
    print("FINAL_VALIDATION",validation["status"],"REPORT",str(report),flush=True)


if __name__=="__main__":main()
