"""Verify saved scoped AO evidence and report in Vietnamese; no optimization."""
from __future__ import annotations
import io
import json
import math
from pathlib import Path
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts import run_ao_effective_channel_no_fading_noise_reference as d


def table(fields,rows):
    def cell(value):
        return format(value,".17g") if isinstance(value,float) else str(value)
    return ["| "+" | ".join(fields)+" |","|"+"|".join("---" for _ in fields)+"|"]+[
        "| "+" | ".join(cell(row.get(k,"—")) for k in fields)+" |" for row in rows]


def verify_artifacts(result):
    import numpy as np
    checks=[]
    for run in result["runs"]:
        current=run["initial"]
        for row in run["iterations"]:
            assert row["P1"]["fixed"]==row["nu_before"]
            assert row["P2"]["fixed"]==row["VA_after_P1"]
            assert row["K_after_P1"]>=row["K_before"]-1e-8
            assert row["K_after_P2"]>=row["K_after_P1"]-1e-8
            assert abs(row["delta_K"]-(row["K_after_P2"]-row["K_before"]))<1e-15
            assert row["nu_before"]==current["nu_raw"] and row["VA_before"]==current["V_A"]
            current=dict(nu_raw=row["nu_after_P2"],V_A=row["VA_after_P1"])
        checks.append(dict(start_id=run["start"]["start_id"],epoch=run["iterations"][0]["epoch"],
                          monotonicity=True,P2_uses_P1=True))
    for row in [result["initial"],result["best_AO_MB"],result["Uniform"]]+result["accuracy_checks"]:
        assert row["T_eff"]==.16092029098192165 and row["xi_eff"]==.0186
        assert row["N_eff"]==row["T_eff"]*.0186
        assert row["b"]==1+row["T_eff"]*(row["V_A"]+.0186)
        for name in ["mean_eta","mean_sqrt_eta","mean_eta_xi_total"]:
            assert row[name]==result["initial"][name]
        assert row["numerical_repairs"]==[]
        assert abs(row["Z_star"]-(2*math.sqrt(row["T_eff"])*row["C"]-math.sqrt(2*row["N_eff"]*row["w"])))<1e-13
        matrix=np.array(row["Gamma_AB"]);omega=np.kron(np.eye(2),[[0.,1.],[-1.,0.]])
        assert np.linalg.eigvalsh(matrix+1j*omega).min()>=-1e-13
        np.testing.assert_allclose(sorted(abs(np.linalg.eigvals(1j*omega@matrix))),
            [row["lambda_2"]]*2+[row["lambda_1"]]*2,rtol=0.,atol=1e-12)
        g=lambda n:0. if n==0 else (n+1)*math.log2(n+1)-n*math.log2(n)
        chi=g((row["lambda_1"]-1)/2)+g((row["lambda_2"]-1)/2)-g((row["lambda_3"]-1)/2)
        assert abs(chi-row["chi_BE"])<1e-12
        assert abs(row["SKR"]-(.95*row["I_AB"]-chi))<1e-12
    settings=result["config"]
    assert len(result["source_attempts"])<=settings["max_new_source_attempts"]
    assert result["used_source_wall_seconds"]<=settings["source_wall_budget_seconds"]+2
    for attempt in result["source_attempts"]:
        assert attempt["elapsed_seconds"]<=attempt["deadline_seconds"]+2
        assert attempt["scientific_context_hash"]==result["scientific_context_hash"]
    candidates=result["accuracy_checks"][:-1]
    order_winners={str(order):max(candidates,key=lambda r:next(x["SKR"] for x in r["MI_orders"] if x["order"]==order))["source_cache_key"]
                   for order in (8,16,32)}
    stable=len(set(order_winners.values()))==1 and order_winners["32"]==result["best_AO_MB"]["source_cache_key"]
    assert stable
    return checks,order_winners


def write_report(result,prepared,status,tests,baseline):
    best=result["best_AO_MB"]
    comparison=[dict(scheme=name,**row) for name,row in [("Initial MB",result["initial"]),
        ("Best catalog MB",result["best_catalog_MB"]),("Multistart AO MB",best),
        ("Optimized Uniform",result["Uniform"])]]
    winning_run=max(result["runs"],key=lambda r:r["final"]["SKR"])
    final=winning_run["iterations"][-1]
    settings=result["config"]
    lines=["# AO multistart — Gaussian bỏ phương sai fading","",
        f"Ngày2026-10-13. **FINAL STATUS: {status}.** Chỉ L=21.9393102292km.",
        "Đã thực thi AO và các probe nguồn mới. DeltaK=0 trên catalog không được coi là hội tụ liên tục.","",
        "## A. Mô hình khoa học","",
        "Dùng effective_channel_no_fading_noise xuyên suốt, objective effective_gaussian_Zstar_diagnostic_SKR.",
        "Giữ Eq.(10), active conditioning trên(0,1], atomAoA và cả ba mômen. Adaptive optics/phase OFF; ideal heterodyne R=1,xi_det=0,chi_het=1;beta=.95,xi_ch=.0186.",
        "Full divergence10µrad,w0=.0986760647169751m,receiver diameter.55m.","",
        r"$$T_{\rm eff}=\langle\sqrt\eta\rangle^2=0.16092029098192165,\quad \xi_{\rm eff}=0.0186,\quad N_{\rm eff}=T_{\rm eff}\xi_{\rm ch}.$$",
        r"$$a=1+V_A,\quad b=1+T_{\rm eff}(V_A+0.0186),\quad Z^*=2\sqrt{T_{\rm eff}}C-\sqrt{2T_{\rm eff}(0.0186)w}.$$",
        r"$$K=0.95I_{AB}^{\rm discrete}-\chi_{BE}(Z^*).$$","",
        "Cùng centered MB-256QAM ensemble cho MI/Holevo. Signed rawK, không clipping, không Gaussian-input MI, không fading-mixture MC. Xấp xỉ này bỏ fading variance; chưa là certified fading-channel security lower bound.","",
        "## B. Regression và khởi tạo","",
        "Mandatory reference tái lập trong5e-12; các số yêu cầu làm tròn12decimals. Source-authentication adapter trùng evaluator đã bảo toàn tại reference, residuals=0.",
        "Đã đánh giá mới182 MB/29Uniform dưới objective mới, không xếp hạng bằng historical/corrected SKR.",""]
    lines+=table(["start_id","nu_raw","V_A","initial_SKR","origin"],prepared["starts"])
    lines+=["","## C. Quỹ đạo P1/P2","",
        "P1 đánh giá slice exact tại nu hiện hành; P2 dùng ngay VA sauP1. Tái dùng coarse catalog scan, boundary probes và paired midpoint refinement của bộ AO. Coarse local maxima được lưu; không giả định unimodality. Trong ngân sách này ưu tiên refinement bracket của điểm tốt nhất.",
        "Mọi accepted update không giảmK; rejected/missing steps lưu trong JSON/CSV. Zero endpoint được kiểm tra riêng vì helper historical chỉ nhậnnu>0.",""]
    histories=[row for run in result["runs"] for row in run["iterations"]]
    lines+=table(["start_id","epoch","iteration","nu_before","VA_before","VA_after_P1","K_after_P1",
        "nu_after_P2","K_after_P2","delta_K","parameter_change","convergence_status"],histories)
    starts=[run for run in result["runs"] if run["start"]["start_id"]!="best_MB_refinement"]
    endpoints={(run["final"]["nu_raw"].hex(),run["final"]["V_A"].hex()) for run in starts}
    lines+=["",f"Multistart consistency: {len(starts)} trajectories, {len(endpoints)} distinct terminal pairs; agreement is only over tested exact points.",""]
    lines+=table(["start_id","initial_SKR","final_nu","final_VA","final_SKR","status"],
        [dict(start_id=run["start"]["start_id"],initial_SKR=run["initial"]["SKR"],
              final_nu=run["final"]["nu_raw"],final_VA=run["final"]["V_A"],
              final_SKR=run["final"]["SKR"],status=run["status"]) for run in starts])
    lines+=["","## D. Best exact numerical solution","",
        f"**(nu_raw,VA,K)=({best['nu_raw']:.17g},{best['V_A']:.17g},{best['SKR']:.17g}).**",
        "Digits là output binary64 của evaluator, không phải bảo đảm total error17digits.",""]
    lines+=table(["scheme","nu_raw","V_A","I_AB","beta_I_AB","chi_BE","SKR"],comparison)
    lines+=["","Best catalog và terminal AO được báo riêng. Uniform là tốt nhất exact đã tìm trong VA search, chưa là maximum liên tục được chứng nhận.","",
        "## E. Source, covariance, MI/Holevo",""]
    lines+=table(["quantity","value"],[dict(quantity=k,value=best[k]) for k in
        ["C","w","T_eff","xi_eff","N_eff","a","b","Z_star","lambda_1","lambda_2","lambda_3","I_AB","beta_I_AB","chi_BE","SKR"]])
    lines+=["",f"Sourcekey: {best['source_cache_key']}; ensemblehash: {best['ensemble_hash']}.",
        f"Scientific context: {result['scientific_context_hash']}.","",
        "## F. Cải thiện","",
        f"DeltaK so initial={result['delta_K']:.17g} bits/use; gain={result['gain_percent']:.17g}%.",
        f"DeltaK so bestcatalog={best['SKR']-result['best_catalog_MB']['SKR']:.17g} bits/use.","",
        "## G. Uniform và shaping gain","",
        f"Uniform nu0,VA={result['Uniform']['V_A']:.17g},K={result['Uniform']['SKR']:.17g}.",
        f"MB−Uniform={result['shaping_gain_absolute']:.17g} bits/use; relative gain with |KUniform|={result['shaping_gain_percent']:.17g}%.",
        f"Uniform status={result['uniform_search']['status']}; actual range={result['uniform_search']['range']}; bracket={result['uniform_search'].get('bracket')}.","",
        "## H. Độ tin cậy, ngân sách và unresolved coverage","",
        f"Unique exact objectives={result['unique_exact_objectives']},newsource completions={result['new_sources']},source attempts={len(result['source_attempts'])}.",
        f"Default đã thông báo: source wall budget{settings['source_wall_budget_seconds']}s,per-source<={settings['per_source_deadline_seconds']}s,max{settings['max_new_source_attempts']} attempts,Uniform reserve{settings['uniform_source_reserve_seconds']}s.",
        f"Measured sourcewall={result['used_source_wall_seconds']:.6f}s;optimizationwall={result['optimization_wall_seconds']:.6f}s.",
        "Giữ nguyên full-support oracle,1050/1250/1450digits,stability rule và internal watchdog3600s. External WindowsJob deadline chỉ giới hạn tài nguyên; timeout không có C,w/K.",""]
    lines+=table(["attempt","nu_raw","V_A","group","deadline_seconds","status","elapsed_seconds","returncode","aggregate_cpu_seconds"],result["source_attempts"])
    lines+=["","Cache authentication kiểm tra bytehash,parameterhex,ensemblehash,settings/producer hashes và full support256. Không interpolation/nearest-neighbor C,w/SKR.",
        "MI GH8/16/32 cho mọi evaluated candidate. Final winner và competitors/Uniform tính lại; top10MB competitor ranking chọn cùng winner ở cả3orders.",
        f"Largest final-check |K32−K8|={result['largest_GH8_32_SKR_difference']:.17g};top2 gap={result['best_second_gap']!r}.",""]
    gh=[]
    for row in [best,result["Uniform"]]:
        for item in row["MI_orders"]:
            gh.append(dict(nu_raw=row["nu_raw"],VA=row["V_A"],**item,delta_K_from_GH32=item["SKR"]-row["SKR"]))
    lines+=table(["nu_raw","VA","order","I_AB","SKR","delta_K_from_GH32"],gh)
    lines+=["","Diagnostic stopping: deltaK1e-8,parameter1e-6;cap6iterations,3boundaryexpansions,4refinement stages. Stopping tolerance không phải total-error bound.",
        "Scientific domainnu>=0,VA>0,nopeak/energy/physical upperbounds. Catalog envelopeMBnu[.05,.8],VA[.025,8];UniformVA[.02,5] chỉ là các điểm đã có. Slice ranges và attempted expansions lưu riêng, không thành physical constraints.",
        f"Selected terminal P1 range={final['P1'].get('range')},bracket={final['P1'].get('bracket')},status={final['P1']['status']}.",
        f"Selected terminal P2 range={final['P2'].get('range')},bracket={final['P2'].get('bracket')},zero endpoint={final['P2'].get('zero_endpoint_status')},status={final['P2']['status']}.",
        "Missing points giữ trong missing_exact_source_requests.csv; full candidate/boundary/rejected histories trong AO_iteration_history.csv và trajectoryJSONs. Multistart agreement trên catalog không chứng minh coordinate-local/global continuous optimum.",
        "Source total-error bound chưa được enclosure nghiêm ngặt; AP precision stability chỉ là numerical evidence. Không nới tolerance,clip eigenvalues hoặc đổi Holevo selection để ép convergence.","",
        "## I. Preservation và validation","",
        f"{len(baseline['protected_hashes'])} prior protected files hash-verified unchanged;changes=[]. Old modes/cache182/B/C/checkpoints/MI/Holevo/Eq10/Eq20/frozen spec không sửa.",
        f"Frozenactual SHA256={baseline['frozen_sha256']};historical expected={baseline['frozen_historical_expected']};mismatch giữ như pre-existing promotion blocker.",
        f"{tests.testsRun} scoped tests CURRENTLY_VERIFIED_PASS. Independent artifact assertions: P2 dùng P1,monotonicity,moment/noise/Eq20,Gamma+iOmega/spectrum,entropy,signedK,budget,GHwinner.",
        "Sau run không còn controller/source/oldC processes. NOT_READY_FOR_PUBLICATION_SCALE_RUNS;oldObjectiveC USER_STOPPED không restart.","",
        "## J. Diễn giải và STOP","",
        "AO chỉ tối đa hóa Gaussian Zstar diagnostic objective với fading-induced variance bị bỏ theo quyết định user. K dương không tự chứng minh bảo mật cho physical fading channel.",
        f"**FINAL STATUS: {status}.** Best exact candidate giữ ở bảng; không gọi local/global convergence khi thiếu exact refinement.",
        "STOP sau result/report. Không26distance/trajectory/cloud/aperture/divergence sweeps,oldC/training/heldout/final-test/publication evaluation,commit/push.","",
        "Artifacts: [result](../results/ao_effective_channel_no_fading_noise_reference/optimization_result.json), [comparison](../results/ao_effective_channel_no_fading_noise_reference/comparison.csv), [iteration history](../results/ao_effective_channel_no_fading_noise_reference/AO_iteration_history.csv), [final validation](../results/ao_effective_channel_no_fading_noise_reference/final_validation.json).",
        "Figures SKR_vs_AO_iteration,VA_vs_AO_iteration,nu_vs_AO_iteration: vectorPDF +300dpiPNG. Sourceattempt logs/receipts/full histories/provenance cùng namespace.",""]
    report=ROOT/"docs/AO_EFFECTIVE_CHANNEL_NO_FADING_NOISE_REPORT_VI.md"
    with report.open("x",encoding="utf-8",newline="\n") as stream:stream.write("\n".join(lines))
    return report


def main():
    baseline=d.read_json(d.OUT/"startup_manifest.json")
    result=d.read_json(d.OUT/"optimization_result.json")
    prepared=d.read_json(d.OUT/"catalog_preparation.json")
    identity=d.read_json(d.OUT/"objective_identity.json")
    assert d.hash_json(identity["identity"])==identity["sha256"]==result["scientific_context_hash"]
    for name,expected in identity["identity"]["implementations"].items():
        assert d.digest(ROOT/name)==expected,name
    changes=d.verify_protected(baseline)
    log=io.StringIO()
    tests=unittest.TextTestRunner(stream=log,verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromName("tests.test_ao_effective_channel_no_fading_noise_reference"))
    if not tests.wasSuccessful():raise ValueError(log.getvalue())
    (d.OUT/"final_tests.txt").write_text(log.getvalue(),encoding="utf-8",newline="\n")
    checks,winners=verify_artifacts(result)
    query="Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^python' -and ($_.CommandLine -match 'run_ao_effective_channel_no_fading_noise_reference.py|full_support_c4_worker.py|run_theta10_D55_objective_c.py') } | Select-Object ProcessId,ParentProcessId,CommandLine | ConvertTo-Json -Compress"
    raw=subprocess.check_output(["powershell","-NoProfile","-Command",query],text=True,
                                creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0)).strip()
    remaining=[] if not raw else json.loads(raw)
    if remaining:raise ValueError("AO/source/oldC processes remain: "+str(remaining))
    resource_limited=bool(result["missing_source_requests"]) and (
        len(result["source_attempts"])>=result["config"]["max_new_source_attempts"] or
        any(a["deadline_exceeded"] or a["returncode"]==124 for a in result["source_attempts"]))
    status="AO_RESOURCE_LIMITED" if resource_limited else result["status"]
    report=write_report(result,prepared,status,tests,baseline)
    outputs={p.relative_to(ROOT).as_posix():d.digest(p) for p in d.OUT.rglob("*") if p.is_file()}
    receipt=dict(status="CURRENTLY_VERIFIED_PASS",final_AO_status=status,tests_run=tests.testsRun,
        failures=len(tests.failures),errors=len(tests.errors),artifact_checks=checks,
        protected_files=len(baseline["protected_hashes"]),protected_changes=changes,
        source_budget_verified=True,GH_winner_stable=True,GH_winners=winners,
        processes_remaining=remaining,producer_sha256={n:d.digest(ROOT/n) for n in d.NEW[:3]},
        finalizer_sha256=d.digest(Path(__file__)),report_sha256=d.digest(report),output_sha256=outputs,
        global_or_fading_security_certification=False)
    d.save(d.OUT/"final_validation.json",receipt,exclusive=True)
    print("FINAL_VALIDATION",status,"tests",tests.testsRun,"protected",len(baseline["protected_hashes"]),flush=True)


if __name__=="__main__":
    main()
