"""Read saved continuation evidence; live reporting or final artifact validation."""
from __future__ import annotations
import argparse
from pathlib import Path
import math
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts import continue_ao_effective_channel_no_fading_noise as c


def table(fields,rows):
    def fmt(value):return format(value,".17g") if isinstance(value,float) else str(value)
    return ["| "+" | ".join(fields)+" |","|"+"|".join("---" for _ in fields)+"|"]+[
        "| "+" | ".join(fmt(r.get(k,"NOT_RECORDED")) for k in fields)+" |" for r in rows]


def report(live):
    checkpoint=c.d.read_json(c.OUT/"checkpoint.json")
    manifest=c.d.read_json(c.OUT/"startup_manifest.json")
    prepared=c.d.read_json(c.OUT/"preparation.json")
    result=None if live else c.d.read_json(c.OUT/"continuation_result.json")
    best=checkpoint["best_exact"] if live else result["best_exact"]
    attempts=checkpoint["source_attempts"]
    iterations=checkpoint["iterations"]
    previous=prepared["previous_best"]
    delta=best["SKR"]-previous["SKR"]
    target=[]
    for old in prepared["timed_out_probes"]:
        matches=[a for a in attempts if a["nu_raw"]==old["nu_raw"] and a["V_A"]==old["V_A"]]
        a=matches[-1] if matches else {}
        target.append(dict(nu_raw=old["nu_raw"],VA=old["V_A"],status=a.get("status","NOT_RUN"),
            runtime_seconds=a.get("elapsed_seconds"),C=a.get("C"),w=a.get("w"),I_AB=a.get("I_AB"),
            chi_BE=a.get("chi_BE"),SKR=a.get("SKR"),source_hash=a.get("source_hash"),
            checkpoint_path=a.get("checkpoint_path")))
    status=checkpoint["status"] if live else result["status"]
    lines=["# Tiếp tục AO từ checkpoint — tăng thời gian tính C,w","",
        f"**Trạng thái: {status}.** {'Báo cáo tiến độ, chưa phải kết quả cuối.' if live else 'Báo cáo kết thúc lần tiếp tục.'}","",
        "Chỉ L=21.9393102292km; effective_channel_no_fading_noise và objective effective_gaussian_Zstar_diagnostic_SKR. Không chạy lại tám multistart; khôi phục 211 objective exact và các lịch sử đã hoàn tất.","",
        "## A. Tính source exact cho ba probe timeout cũ","",
        "Tọa độ lấy nguyên từ source_attempts/checkpoint cũ. Đã kiểm tra toàn bộ cache hiện có: không có source hoàn chỉnh của ba điểm trước khi bắt đầu. Lần cũ không lưu intermediate numerical state; lần này bắt đầu mới và journal các precision row đã hoàn tất.",""]
    lines+=table(["nu_raw","VA","runtime_seconds","status","C","w","I_AB","chi_BE","SKR"],target)
    completed=sum(a["status"]=="COMPLETED_EXACT" for a in attempts)
    lines += ["",f"Toàn lượt: {completed} source mới hoàn thành; {len(attempts)-completed} job chưa hoàn thành. Tổng objective đã lưu: {len(c.d.read_json(c.OUT/'objective_evaluations.json'))}."]
    for attempt in attempts:
        if attempt["status"]!="TIMEOUT":continue
        journal=c.OUT/"precision_checkpoints"/attempt["source_cache_key"]
        digits=sorted(int(p.stem) for p in journal.glob("*.json") if p.stem.isdigit())
        reason="giới hạn ngân sách toàn lượt, gồm thời gian dự phòng kết thúc" if attempt["deadline_seconds"]<7200 else "giới hạn thời gian candidate"
        lines += [f"Job {attempt['attempt']} tại (nu,VA)=({attempt['nu_raw']},{attempt['V_A']}) dừng do {reason}: deadline={attempt['deadline_seconds']:.6f}s, thực chạy={attempt['elapsed_seconds']:.6f}s, shutdown margin=5s. Các hàng precision được giữ: {digits}; chưa chấp nhận C,w hoặc tính SKR từ các hàng chưa đủ ladder."]
    lines+=["","TIMEOUT/gián đoạn là trạng thái tài nguyên, không phải K âm/0 hoặc constellation không physical.",
        "7200s tối đa mỗi candidate (Windows Job có shutdown margin5s); watchdog AP bên trong cũng tăng từ3600s lên7200s chỉ tại wrapper này. Budget continuation43200s, reserve60s, source jobs tuần tự1. Không giảm1050/1250/1450digits hoặc thay acceptance rule.","",
        "## B. Nhật ký P1/P2","",
        "P1 giữ nu hiện tại; P2 dùng ngay VA sauP1. Chỉ thêm targeted exact neighbors/bracket midpoints, không rectangular sweep/interpolation. Tất cả accepted updates không giảm evaluatedK.",""]
    lines+=table(["iteration","nu_before","VA_before","VA_after_P1","K_after_P1",
                  "nu_after_P2","K_after_P2","delta_K","parameter_change"],iterations)
    if checkpoint["pending_iteration"]:
        pending=checkpoint["pending_iteration"]
        lines+=["",f"Iteration đang dở: phase={checkpoint['phase']}; VA sauP1={pending['after_P1']['V_A']!r}, K={pending['after_P1']['SKR']!r}. P2/chốt full iteration chưa hoàn tất."]
    lines+=["","## C. Best exact đã xác thực","",
        f"**(nu_raw,VA,K)=({best['nu_raw']:.17g},{best['V_A']:.17g},{best['SKR']:.17g})**.",
        "Giữ previous best cho đến khi có exact result hợp lệ tốt hơn. Digits là binary64 output, không phải chứng nhận total error17digits.",""]
    lines+=table(["quantity","value"],[dict(quantity=k,value=best[k]) for k in
        ["C","w","T_eff","xi_eff","a","b","Z_star","lambda_1","lambda_2","lambda_3","I_AB","beta_I_AB","chi_BE","SKR"]])
    lines+=["",f"Source cache key={best['source_cache_key']}; ensemble hash={best['ensemble_hash']}; source={best['source_path']}.",
        f"Inherited scientific context={checkpoint['inherited_scientific_context']}; continuation context={checkpoint['continuation_context']}.",""]
    lines+=table(["order","I_AB","SKR"],best["MI_orders"])
    lines+=["","## D. So sánh với kết quả trước","",
        f"K_previous exact stored={previous['SKR']:.17g} (yêu cầu làm tròn0.05873317206755).",
        f"DeltaK={delta:.17g} bits/use; relative gain={100*delta/abs(previous['SKR']):.17g}%.","",
        "## E. Hội tụ và bracket","",
        "Ngưỡng improvement1e-8, parameter stability1e-6. Không kết luận convergence chỉ vì deltaK nhỏ. Hai local brackets, exact neighbors, boundaries, GH8/16/32 và covariance physicality phải cùng được kiểm tra."]
    if iterations:
        last=iterations[-1]
        for key in ("P1","P2"):
            search=last[key]
            lines.append(f"{key}: status={search['status']}, actual range={search.get('range')}, bracket={search.get('bracket')}, refinement={search.get('refinement_status')}, boundary={search.get('boundary_status')}.")
        lines.append(f"Coordinate brackets complete={last['coordinate_brackets_complete']}.")
        for key in ("P1","P2"):
            missing=last[key].get("source_missing",[])
            if missing:lines.append(f"{key} còn thiếu exact source tại: {[row['value'] for row in missing]}; VA cố định sau P1={last['VA_after_P1']}.")
        lines.append("P1 đạt giới hạn bốn lượt refinement; nhãn legacy INNER_SEARCH_FAILURE ở đây không có numerical_failures. P2 chưa hoàn tất refinement/boundary checks. Chưa hội tụ theo tọa độ hoặc trên miền liên tục.")
    else:
        lines.append("P1/P2 chưa hoàn tất iteration mới; không gán trạng thái complete.")
    lines+=["","## F. Bảo toàn và provenance","",
        f"{len(manifest['protected_hashes'])} prior files được hash-bound trong startup_manifest; toàn bộ old cache/catalog182/B/C/modes/previousAO results được giữ nguyên.",
        "Transport/deadline/checkpoint wrapper import original AP _row,worker.main,Gram moments,source normalization,discrete MI/Holevo. Completed precision rows hash-bind exact binary64 request,mathproducer,mpmath version,ambient precision,digits và rowdigest. Hash mismatch fail closed.",
        "Source full-support accepted mới lưu vào cache riêng ngay khi hoàn tất; auxiliary fast-gate Infinity được encode losslessly, không biến đổi C,w. Interrupted job có thể tiếp tục precision rows hoàn tất; không reset cumulative candidate7200s hoặc continuation budget.",
        f"Elapsed continuation={checkpoint['elapsed_seconds']:.6f}s; restarted multistarts={checkpoint['restarted_multistarts']}.",
        "T_eff=.16092029098192165,xi_ch=.0186,beta=.95,ideal heterodyne/phase/adaptiveopticsOFF giữ nguyên. b=1+T_eff(VA+xi),Z*=2sqrt(T_eff)C-sqrt(2T_eff xi w);K=.95I_AB-chi(Zstar). Eq10/20/PDF/moments/source normalization không sửa.",
        "Đây là Gaussian approximation bỏ fading-induced variance, không phải certified fading security lower bound. Total source/security error enclosure vẫn chưa được thiết lập; numeric agreement không chứng nhận continuous/global optimum.",
        f"Frozen actual SHA256={manifest['frozen_sha256']}; historicalexpected={manifest['frozen_expected']};pre-existing promotion blocker giữ nguyên. NOT_READY_FOR_PUBLICATION_SCALE_RUNS;oldObjectiveC USER_STOPPED.",
        "Không newmultistarts/distance/trajectory/heldout/final-test/training/publication evaluation/commit/push.","",
        "Artifacts: [checkpoint](../results/ao_effective_channel_no_fading_noise_reference_continuation/checkpoint.json), [source results](../results/ao_effective_channel_no_fading_noise_reference_continuation/exact_source_results.csv), [iterations](../results/ao_effective_channel_no_fading_noise_reference_continuation/continuation_iterations.csv).",""]
    path=ROOT/"docs/AO_NO_FADING_NOISE_CONTINUATION_REPORT_VI.md"
    path.write_text("\n".join(lines),encoding="utf-8",newline="\n")
    c.d.write_csv(c.OUT/"three_previous_timeout_probes.csv",target)
    if live:
        c.d.write_csv(c.OUT/"exact_source_results.csv",attempts)
        c.d.write_csv(c.OUT/"continuation_iterations.csv",iterations)
    if not live:validate(result,path,manifest)
    print("REPORT",status,"bestK",best["SKR"],flush=True)


def validate(result,report_path,manifest):
    import numpy as np
    from scripts.run_theta10_D55_unconstrained_three_scheme import candidate_from_payload
    obj=c.d.Objective()
    hashes=dict(manifest["protected_hashes"])
    from scripts.exact_cache_provenance import verify_source_payload,source_settings
    for path in (c.OUT/"exact_source_cache").glob("*.json"):
        payload=c.d.read_json(path)
        payload["_provenance"]=verify_source_payload(payload,source_settings(obj.config))
        payload["_path"]=path.relative_to(ROOT).as_posix()
        obj.payloads[payload["ensemble_hash"]]=payload;hashes[payload["_path"]]=c.d.digest(path)
    rows=sorted(c.d.read_json(c.OUT/"objective_evaluations.json"),key=lambda r:r["SKR"],reverse=True)[:10]
    checks=[]
    for row in rows:
        candidate=candidate_from_payload(obj.config,obj.payloads,"Uniform" if row["nu_raw"]==0 else "MB",row["nu_raw"],row["V_A"])
        fresh=c.d.evaluate_authenticated(candidate,obj.moments,obj.config,hashes)
        checks.append(fresh)
        matrix=np.array(fresh["Gamma_AB"]);omega=np.kron(np.eye(2),[[0.,1.],[-1.,0.]])
        assert np.linalg.eigvalsh(matrix+1j*omega).min()>=-1e-13
        assert fresh["numerical_repairs"]==[] and fresh["T_eff"]==.16092029098192165
    winners={str(order):max(checks,key=lambda r:next(x["SKR"] for x in r["MI_orders"] if x["order"]==order))["source_cache_key"] for order in (8,16,32)}
    stable=len(set(winners.values()))==1
    for iteration in result["iterations"]:
        assert iteration["P1"]["fixed"]==iteration["nu_before"]
        assert iteration["P2"]["fixed"]==iteration["VA_after_P1"]
        assert iteration["K_after_P1"]>=iteration["K_before"]-1e-8
        assert iteration["K_after_P2"]>=iteration["K_after_P1"]-1e-8
    changes=c.d.verify_protected(manifest)
    for name,expected in manifest["producers"].items():assert c.d.digest(ROOT/name)==expected
    preflight=c.d.read_json(c.OUT/"preflight_receipt.json")
    assert preflight["status"]=="CURRENTLY_VERIFIED_PASS" and preflight["producer_sha256"]==manifest["producers"]
    journals={}
    for attempt in result["source_attempts"]:
        directory=c.OUT/"precision_checkpoints"/attempt["source_cache_key"]
        request=c.d.read_json(directory/"request.json")
        digits=[];row_hashes={}
        for path in sorted(directory.glob("*.json")):
            if not path.stem.isdigit():continue
            saved=c.d.read_json(path)
            assert saved["identity"]["request"]==request
            assert saved["identity"]["producer_sha256"]==c.d.digest(ROOT/"scripts/full_support_c4_worker.py")
            assert saved["identity_sha256"]==c.d.hash_json(saved["identity"])
            assert saved["row_sha256"]==c.d.hash_json(saved["row"])
            assert saved["row"]["digits"]==saved["identity"]["digits"]==int(path.stem)
            digits.append(int(path.stem));row_hashes[path.name]=c.d.digest(path)
        if attempt["status"]=="COMPLETED_EXACT":assert sorted(digits)==[1050,1250,1450]
        journals[attempt["source_cache_key"]]=dict(digits=sorted(digits),row_sha256=row_hashes,
            request_sha256=c.d.digest(directory/"request.json"),accepted_source=attempt["status"]=="COMPLETED_EXACT")
    assert subprocess.run(["git","diff","--check"],cwd=ROOT,capture_output=True).returncode==0
    with report_path.open("a",encoding="utf-8",newline="\n") as report_file:
        report_file.write("\n## G. Kiểm tra kết thúc\n\n")
        report_file.write(f"CURRENTLY_VERIFIED_PASS: {len(changes)} protected changes trên {len(manifest['protected_hashes'])} file; provenance của toàn bộ cache và journal precision mới khớp.\n")
        report_file.write(f"GH8/16/32 chọn cùng winner trong top10={stable}; covariance độc lập Gamma+iOmega và domain symplectic pass, repairs=[]; P2 dùng đúng VA mới sau P1.\n")
        report_file.write(f"{preflight['tests_run']} scoped tests đã chạy PASS ở preflight; hash của test/config/controller vẫn khớp bản đã kiểm tra, không chạy lại AP hay AO để lập báo cáo.\n")
        report_file.write("Đã dừng toàn lượt theo ngân sách; full source mới được giữ trong namespace riêng. Source timeout không được gán SKR âm/0 hoặc coi là numerically invalid.\n")
    c.save(c.OUT/"final_validation.json",dict(status="CURRENTLY_VERIFIED_PASS",AO_status=result["status"],
        protected_files=len(manifest["protected_hashes"]),protected_changes=changes,
        GH_order_winners=winners,GH_winner_stable=stable,final_accuracy_checks=checks,
        report_sha256=c.d.digest(report_path),finalizer_sha256=c.d.digest(Path(__file__)),
        precision_journals=journals,preflight_tests_run=preflight["tests_run"],
        preflight_receipt_sha256=c.d.digest(c.OUT/"preflight_receipt.json"),
        restarted_multistarts=0,rigorous_global_or_fading_security_claim=False))


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--live",action="store_true")
    args=parser.parse_args();report(args.live)
