"""Independent artifact checks; no source oracle, MI, Holevo or Monte Carlo run."""
import json
import math
from pathlib import Path
import re
import sys
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from scripts import run_ao_effective_channel_no_fading_noise_reference as saved
from scripts.run_mobility_skr_experiment import SCHEMES
from src.mobility_skr import objective_key
from src.mobility_results_package import load_existing,read_csv,verify_series,cumulative_normalized,tradeoff_metrics

OUT=ROOT/"results/mobility_numerical_results_package_20261014"


def main():
    manifest=saved.read_json(OUT/"startup_manifest.json");package=saved.read_json(OUT/"package_receipt.json")
    for name,want in package["output_sha256"].items():
        if saved.digest(OUT/name)!=want:raise ValueError(f"Package output differs: {name}")
    for name,want in package["producers"].items():
        if saved.digest(ROOT/name)!=want:raise ValueError(f"Package producer differs: {name}")
    data=load_existing();settings=data["settings"]
    test=saved.read_json(OUT/"test_receipt.json")
    if test["status"]!="CURRENTLY_VERIFIED_PASS" or test["test_count"]!=25:raise ValueError("Test prerequisite missing")
    for name,want in test["producer_sha256"].items():
        if saved.digest(ROOT/name)!=want:raise ValueError("Test source differs")
    if saved.digest(OUT/"test_output.txt")!=test["output_sha256"]:raise ValueError("Test log differs")
    plotted=saved.read_json(OUT/"tradeoff_metrics.json")
    for k,v in tradeoff_metrics(data["summary"]).items():
        if plotted[k]!=v:raise ValueError("Tradeoff metric differs")
    expected=cumulative_normalized(data["series"],30);actual=read_csv(OUT/"plot_data/figure_3_cumulative_normalized.csv")
    if len(actual)!=124:raise ValueError("Normalized cumulative coverage differs")
    for a,b in zip(actual,expected):
        if a["scheme"]!=b["scheme"] or float(a["cumulative_normalized_skr"])!=b["cumulative_normalized_skr"]:
            raise ValueError("Cumulative plotting data differ")
    for oldfile,newfile in (("scheme_time_series.csv","figure_2_skr_time.csv"),
        ("movement_penalty_sweep.csv","figure_4_skr_flight.csv"),("cloud_velocity_sweep.csv","figure_5_cloud_velocity.csv")):
        if read_csv(ROOT/"results/mobility_aware_skr_20261014/full"/oldfile)!=read_csv(OUT/"plot_data"/newfile):
            raise ValueError("Plot values changed from original source")
    if read_csv(OUT/"plot_data/figure_6_source_parameters.csv")!=data["series"]:
        raise ValueError("Source parameters changed in plotting")
    directory=OUT/"uniform";receipt=saved.read_json(directory/"receipt.json")
    for name,want in receipt["output_sha256"].items():
        if saved.digest(directory/name)!=want:raise ValueError("Uniform output differs")
    rows=read_csv(directory/"all_candidate_evaluations.csv");selected=read_csv(directory/"optimized_state_sources.csv")
    roster=read_csv(directory/"source_roster.csv");sources={r["ensemble_hash"]:r for r in roster}
    if (len(rows),len(selected),len(sources))!=(6000,200,30):raise ValueError("Uniform catalog/state coverage differs")
    for source in sources.values():
        if float(source["nu_raw"])!=0.:raise ValueError("Non-Uniform source in Uniform bank")
        if saved.digest(ROOT/source["source_path"])!=manifest["protected_hashes"][source["source_path"]]:
            raise ValueError("Uniform source bytes differ")
    journal={}
    for line in (directory/"objective_cache.jsonl").read_text(encoding="utf-8").splitlines():
        r=json.loads(line)
        if r["row_sha256"]!=saved.hash_json(r["row"]) or r["key"] in journal:raise ValueError("Uniform journal corrupt")
        journal[r["key"]]=r["row"]
    if len(journal)!=6000:raise ValueError("Uniform journal coverage differs")
    state_map={(s["position_index"],s["blocked"]):s for s in data["states"]}
    identity=dict(data["inputs"]["scientific_identity"],source_family="Uniform",adapter_sha256=receipt["adapter_sha256"])
    maxima={};counts={};ghmax={};max_spectrum=0.;max_entropy=0.;min_uncertainty=math.inf
    omega=np.array([[0,1,0,0],[-1,0,0,0],[0,0,0,1],[0,0,-1,0]])
    def g(lam):
        n=(lam-1)/2
        return 0. if n==0 else (n+1)*math.log2(n+1)-n*math.log2(n)
    for row in rows:
        pair=(int(row["position_index"]),row["blocked"]=="True");state=state_map[pair]
        source=sources[row["ensemble_hash"]];stored=journal[row["objective_key"]]
        candidate={k:float(source[k]) for k in ("nu_raw","V_A","C","w")}
        candidate.update(ensemble_hash=source["ensemble_hash"],source_cache_key=source["source_cache_key"])
        key=objective_key(identity,state,candidate,saved.digest(ROOT/source["source_path"]))
        if key!=row["objective_key"]:raise ValueError("Uniform cache key differs")
        for k in ("C","w","V_A","nu_raw","source_cache_key","source_path"):
            if row[k]!=source[k]:raise ValueError("Uniform C,w/parameters differ across states")
        for k in ("SKR","I_AB","chi_BE","T_eff","xi_eff","N_eff","a","b","Z_star","lambda_1","lambda_2","lambda_3"):
            if float(row[k])!=stored[k] or not math.isfinite(float(row[k])):raise ValueError("Uniform numerical record differs")
        t=stored["T_eff"];va=stored["V_A"];a=stored["a"];b=stored["b"];z=stored["Z_star"]
        if t!=state["moments"]["mean_sqrt_eta"]**2 or stored["xi_eff"]!=.0186 or stored["N_eff"]!=t*.0186:
            raise ValueError("Uniform channel/noise mismatch")
        if abs(a-(1+va))>1e-13 or abs(b-(1+t*(va+.0186)))>1e-13 or abs(stored["SKR"]-(.95*stored["I_AB"]-stored["chi_BE"]))>1e-14:
            raise ValueError("Uniform algebra identity failed")
        covariance=np.array([[a,0,z,0],[0,a,0,-z],[z,0,b,0],[0,-z,0,b]])
        lambdas=[stored[k] for k in ("lambda_1","lambda_2","lambda_3")]
        if min(lambdas)<1 or stored["numerical_repairs"]:raise ValueError("Uniform covariance nonphysical/repaired")
        spectrum=np.sort(np.abs(np.linalg.eigvals(1j*omega@covariance)))
        expected_spectrum=np.array(sorted([lambdas[0]]*2+[lambdas[1]]*2))
        max_spectrum=max(max_spectrum,float(np.abs(spectrum-expected_spectrum).max()))
        min_uncertainty=min(min_uncertainty,float(np.linalg.eigvalsh(covariance+1j*omega).min()))
        max_entropy=max(max_entropy,abs(stored["chi_BE"]-(g(lambdas[0])+g(lambdas[1])-g(lambdas[2]))))
        counts[pair]=counts.get(pair,0)+1
        if pair not in maxima or stored["SKR"]>float(maxima[pair]["SKR"]):maxima[pair]=row
        for stage in stored["MI_orders"]:
            orderkey=(*pair,stage["order"])
            if orderkey not in ghmax or stage["SKR"]>ghmax[orderkey][0]:ghmax[orderkey]=(stage["SKR"],stored["ensemble_hash"])
    if max_spectrum>1e-12 or max_entropy>1e-12 or min_uncertainty< -1e-12:
        raise ValueError("Independent Uniform spectrum/entropy failed")
    if len(counts)!=200 or any(v!=30 for v in counts.values()):raise ValueError("Uniform source enumeration incomplete")
    for row in selected:
        pair=(int(row["position_index"]),row["blocked"]=="True")
        if row["objective_key"]!=maxima[pair]["objective_key"]:raise ValueError("Uniform source maximum not selected")
    verify_series(settings,read_csv(directory/"scheme_time_series.csv"),read_csv(directory/"summary.csv"))
    fig_checks=[]
    for png in sorted((OUT/"figures").glob("*.png")):
        with Image.open(png) as image:
            if min(image.info["dpi"])<299.9:raise ValueError("PNG below 300dpi")
            expected_width=3.5 if png.stem.endswith("single") else 7.16
            if abs(image.width/300-expected_width)>.01:raise ValueError("IEEE figure width differs")
            size=image.size
        pdf=png.with_suffix(".pdf");raw=pdf.read_bytes()
        if not raw.startswith(b"%PDF") or b"/Subtype /Image" in raw:raise ValueError("PDF not vector")
        fig_checks.append(dict(png=png.name,pdf=pdf.name,pixels=size))
    if len(fig_checks)!=14:raise ValueError("Seven single/double figures missing")
    tex=(OUT/"numerical_results_section.tex").read_text(encoding="utf-8")
    if any(ord(c)<32 and c not in '\n\r' for c in tex):raise ValueError("LaTeX control character escaping failed")
    if tex.count(r"\includegraphics[width=\textwidth]")!=1 or tex.count(r"\includegraphics[width=\columnwidth]")!=6:
        raise ValueError("LaTeX figure widths malformed")
    for target in re.findall(r"\\(?:input|includegraphics)(?:\[[^]]*\])?\{([^}]+)\}",tex):
        p=OUT/target
        if not p.exists() and not p.with_suffix('.tex').exists():raise ValueError(f"LaTeX referenced file missing: {target}")
    labels=re.findall(r"\\label\{([^}]+)\}",tex)
    if len(labels)!=len(set(labels)):raise ValueError("Duplicate LaTeX labels")
    if tex.count('{')!=tex.count('}'):raise ValueError("LaTeX braces unbalanced")
    if tex.count('$')%2 or r"$\$" in tex or r"S4($\lambda=0.001$ bits/use)" not in tex:
        raise ValueError("LaTeX caption math escaping failed")
    stage=saved.read_json(OUT/"scientific_validation_audit.json")
    if stage["complete_validated_fading_aware_evaluator_available"] or package["actual_fading_security_claim"]:
        raise ValueError("Unsupported full fading security promotion")
    record=dict(status="CURRENTLY_VERIFIED_PASS",checked_utc=datetime.now(timezone.utc).isoformat(),
        validation_scope="Saved-data and export checks only; no scientific evaluator rerun",original_MB_repeated=0,
        new_Uniform_records_verified=6000,Uniform_P1_maxima_verified=200,
        Uniform_GH16_32_stable_states=sum(ghmax[(j,b,16)][1]==ghmax[(j,b,32)][1] for j,b in counts),
        Uniform_maximum_spectrum_residual=max_spectrum,Uniform_maximum_entropy_residual=max_entropy,
        Uniform_minimum_uncertainty_eigenvalue=min_uncertainty,original15tests_preserved=True,current_tests=25,
        cumulative_endpoint_equals_mean=True,figures=fig_checks,LaTeX_lexical_structure="CURRENTLY_VERIFIED_PASS",
        LaTeX_compile="BLOCKED_BY_ENVIRONMENT",all_comparisons_share_config=True,
        scientific_status="PRELIMINARY_EFFECTIVE_GAUSSIAN_IGNORING_FADING_VARIANCE",
        protected_files=len(manifest["protected_hashes"]),protected_changes=saved.verify_protected(manifest),
        verifier_sha256=saved.digest(Path(__file__)),package_receipt_sha256=saved.digest(OUT/"package_receipt.json"))
    saved.save(OUT/"final_validation.json",record,exclusive=True)
    print("FINAL_PACKAGE_VALIDATION",record["status"],"Uniform6000, 14figure exports, originalMBunchanged; TeXcompile unavailable",flush=True)


if __name__=="__main__":main()
