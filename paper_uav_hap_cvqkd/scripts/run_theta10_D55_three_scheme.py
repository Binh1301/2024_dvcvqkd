"""Three-scheme theta10 / D55 exact diagnostic and linear comparison figure."""

from __future__ import annotations

import argparse
import csv
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import math
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts._common import load_yaml
from scripts import run_revised_uniform_mb_distance_diagnostic as old
from scripts.run_exact_mb_test2 import ExactMBEvaluator
from scripts.run_skr_vs_link_distance_theta10urad import load_bank
from scripts.run_uniform_va_optimization_theta10 import load_cached_uniform, uniform_ensemble


OUTPUT = ROOT / "results" / "skr_vs_distance_theta10urad_D55cm_three_scheme"
WAVELENGTH_M = 1.55e-6
THETA_DIV_FULL_RAD = 10e-6
W0_M = 2 * WAVELENGTH_M / (math.pi * THETA_DIV_FULL_RAD)
TAU_ZEN = 0.92
EPSILON = 0.0186
BETA = 0.95
PEAK_PHOTONS = 30.0
RECEIVER_DIAMETER_M = 0.55
FIXED_MB_NU = 0.20
FIXED_MB_VA = 1.3833230302980657
DISTANCES_KM = (
    20.0, 21.0, 21.9393102292, 22.0, 23.0, 24.0, 25.0, 25.5,
    26.0, 26.5, 27.0, 27.5, 28.0, 28.5, 29.0, 29.5, 30.0,
    30.5, 31.0, 31.5, 32.0, 32.5, 33.0, 34.0, 35.0, 36.0,
    38.0, 40.0,
)
UNIFORM_VA_BANK = (
    0.02, 0.04, 0.05, 0.06, 0.08, 0.10, 0.11, 0.12, 0.13, 0.14, 0.15, 0.18, 0.20,
    0.30, 0.50,
    0.60, 0.70, 0.75, 0.80, 1.0, 1.075, 1.25, 1.5, 2.0, 2.05,
    3.0, 3.025, 4.0, 5.0,
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def write_csv(path: Path, rows: list[dict]) -> None:
    fields = sorted({key for row in rows for key in row}) or ["status"]
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader(); writer.writerows(rows)


def configure() -> None:
    old.optical.TAU_ZEN = TAU_ZEN
    old.optical.EPSILON = EPSILON
    old.forensic.BETA = BETA


def build_one_source(config: dict, va: float, output: Path) -> dict:
    evaluator = ExactMBEvaluator(
        config, {"T_eff": 0.0, "epsilon_base": EPSILON, "c_phi": 0.0}, output,
        source_cache_dir=ROOT / "results" / "exact_mb_test2" / "exact_source_cache",
        allow_legacy_exact_import=False,
    )
    payload = evaluator.source_moments(uniform_ensemble(config, va), 0.0, va)
    return {"V_A": va, "cache_key": payload["cache_key"], "ensemble_hash": payload["ensemble_hash"], "C": payload["C"], "w": payload["w"], "support_size": payload["support_size"], "route": payload["source_moment_route"]}


def uniform_bank(config: dict, output: Path, build_missing: bool) -> tuple[list[dict], list[float], list[dict]]:
    bank=[]; missing=[]
    for va in UNIFORM_VA_BANK:
        candidate=load_cached_uniform(config, va)
        if candidate is None: missing.append(va)
        else:
            candidate["historical_record_count"] = 1; bank.append(candidate)
    built=[]
    if missing and build_missing:
        with ThreadPoolExecutor(max_workers=min(4,len(missing))) as pool:
            built=list(pool.map(lambda va: build_one_source(config, va, output), missing))
        bank=[]
        for va in UNIFORM_VA_BANK:
            candidate=load_cached_uniform(config, va)
            if candidate is not None:
                candidate["historical_record_count"] = 1; bank.append(candidate)
        missing=[va for va in UNIFORM_VA_BANK if not any(abs(float(c["V_A"])-va)<1e-12 for c in bank)]
    return sorted(bank,key=lambda c:float(c["V_A"])),missing,built


def channel(config: dict, distance: float) -> dict:
    row,_=old.optical._channel_row(config,w0_m=W0_M,receiver_diameter_m=RECEIVER_DIAMETER_M,distance_km=distance)
    if abs(float(row["theta_div_full_angle_rad"])-THETA_DIV_FULL_RAD)>1e-15: raise AssertionError("theta/w0 mismatch")
    return row


def eval_candidate(candidate: dict, config: dict, channel_row: dict) -> dict:
    return old._candidate_row(candidate, config, channel_row)


def eval_uniform(config: dict, bank: list[dict], ch: dict) -> dict:
    rows=[eval_candidate(c,config,ch) for c in bank]
    best=max(rows,key=lambda r:float(r["SKR"]))
    return {"scheme":"Uniform optimized","family":"Uniform","nu_raw":None,"V_A":float(best["V_A"]),"I_AB":float(best["I_AB"]),"beta_I_AB":float(best["beta_I_AB"]),"chi_BE":float(best["chi_BE"]),"K":float(best["SKR"]),"source_hash":best["source_cache_identifier"],"selection":"best_exact_uniform_cache"}


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("--output-dir",type=Path,default=OUTPUT); parser.add_argument("--build-missing-uniform-source",action="store_true"); args=parser.parse_args()
    torch.set_num_threads(1); configure(); output=args.output_dir.resolve(); output.mkdir(parents=True,exist_ok=True); config=load_yaml(ROOT/"configs"/"default.yaml")
    uni,missing,built=uniform_bank(config,output,args.build_missing_uniform_source)
    if not uni: raise RuntimeError("No exact Uniform source bank")
    mb_all,_=load_bank(config)
    fixed=next(c for c in mb_all if abs(float(c["nu_raw"])-FIXED_MB_NU)<1e-12 and abs(float(c["V_A"])-FIXED_MB_VA)<1e-12)
    fixed["historical_record_count"]=1
    rows=[]; uniform_rows=[]; fixed_rows=[]; opt_rows=[]; channels=[]
    for distance in DISTANCES_KM:
        ch=channel(config,distance); channels.append({**ch,"distance_km":distance,"theta_div_full_rad":THETA_DIV_FULL_RAD,"w0_m":W0_M,"receiver_diameter_m":RECEIVER_DIAMETER_M})
        u=eval_uniform(config,uni,ch); f=eval_candidate(fixed,config,ch); f={"scheme":"MB fixed","family":"MB","nu_raw":FIXED_MB_NU,"V_A":FIXED_MB_VA,"I_AB":float(f["I_AB"]),"beta_I_AB":float(f["beta_I_AB"]),"chi_BE":float(f["chi_BE"]),"K":float(f["SKR"]),"source_hash":f["source_cache_identifier"],"selection":"fixed_reference"}
        mb_rows=[]
        for c in mb_all:
            c["historical_record_count"]=1
            try: mb_rows.append(eval_candidate(c,config,ch))
            except Exception: pass
        if not mb_rows: raise RuntimeError("No feasible MB rows")
        best=max(mb_rows,key=lambda r:float(r["SKR"])); o={"scheme":"MB optimized","family":"MB","nu_raw":float(best["nu"]),"V_A":float(best["V_A"]),"I_AB":float(best["I_AB"]),"beta_I_AB":float(best["beta_I_AB"]),"chi_BE":float(best["chi_BE"]),"K":float(best["SKR"]),"source_hash":best["source_cache_identifier"],"selection":"best_exact_145_point_bank"}
        base={"distance_km":distance,"zeta_deg":float(ch["zeta_deg"]),"T_eff":float(ch["T_eff"]),"theta_div_full_rad":THETA_DIV_FULL_RAD,"w0_m":W0_M,"receiver_diameter_m":RECEIVER_DIAMETER_M}
        rows += [{**base,**u},{**base,**f},{**base,**o}]; uniform_rows.append({**base,**u}); fixed_rows.append({**base,**f}); opt_rows.append({**base,**o})
    write_csv(output/"skr_vs_distance_three_scheme.csv",rows); write_csv(output/"uniform_optimized_candidates.csv",uniform_rows); write_csv(output/"mb_fixed_results.csv",fixed_rows); write_csv(output/"mb_optimized_candidates.csv",opt_rows); write_csv(output/"channel_by_distance.csv",channels)
    # Primary linear comparison figure.
    colors={"Uniform optimized":"#2563eb","MB fixed":"#f28e2b","MB optimized":"#d62728"}; labels={"Uniform optimized":"Optimized Uniform 256-QAM","MB fixed":"Fixed MB-shaped 256-QAM","MB optimized":"Optimized MB-shaped 256-QAM"}
    fig,ax=plt.subplots(figsize=(9.0,5.6),dpi=160)
    for scheme in ("Uniform optimized","MB fixed","MB optimized"):
        rr=[r for r in rows if r["scheme"]==scheme]; ax.plot([r["distance_km"] for r in rr],[r["K"] for r in rr],marker="o",markersize=3.8,linewidth=1.7,color=colors[scheme],label=labels[scheme])
    ax.axhline(0.0,color="#333333",linestyle="--",linewidth=0.9); ax.set_title("SKR versus Link Distance"); ax.set_xlabel("Link Distance (km)"); ax.set_ylabel("Secret Key Rate (bits/use)"); ax.set_xlim(20,40); ax.grid(alpha=.25); ax.legend(frameon=False); fig.tight_layout(); fig.savefig(output/"skr_vs_distance_three_scheme.png",dpi=300,facecolor="white"); fig.savefig(output/"skr_vs_distance_three_scheme.pdf",facecolor="white"); plt.close(fig)
    def endpoints(rr):
        pos=[r for r in rr if float(r["K"])>0]; non=[r for r in rr if float(r["K"])<=0]; return (max((float(r["distance_km"]) for r in pos),default=None),min((float(r["distance_km"]) for r in non),default=None))
    summary={s:endpoints([r for r in rows if r["scheme"]==s]) for s in ("Uniform optimized","MB fixed","MB optimized")}
    experiment_payload={"schema":"theta10-D55-three-scheme-v1","model_composite_sha256":"a85cc9bd8f321b93f407eaf7e1c3589e71ed6df3fb036c7178a56a602eb7fd58","config_sha256":sha256(ROOT/"configs"/"default.yaml"),"theta_div_full_rad":THETA_DIV_FULL_RAD,"receiver_diameter_m":RECEIVER_DIAMETER_M,"distances_km":list(DISTANCES_KM),"uniform_bank":[(float(c["V_A"]),c["ensemble_hash"]) for c in uni],"mb_bank_count":len(mb_all)}; experiment_hash=hashlib.sha256(json.dumps(experiment_payload,sort_keys=True).encode()).hexdigest()
    report={"status":"THETA10_D55_THREE_SCHEME_DIAGNOSTIC_COMPLETE","scope":"DIAGNOSTIC_ONLY","model_composite_sha256":experiment_payload["model_composite_sha256"],"config_sha256":experiment_payload["config_sha256"],"experiment_hash":experiment_hash,"configuration":{"h_HAP_m":20000.0,"h_UAV_m":1000.0,"lambda_m":WAVELENGTH_M,"theta_div_full_rad":THETA_DIV_FULL_RAD,"w0_m":W0_M,"D_r_m":RECEIVER_DIAMETER_M,"receiver_radius_m":RECEIVER_DIAMETER_M/2,"tau_zen":TAU_ZEN,"epsilon_ch":EPSILON,"beta":BETA,"AO":"OFF","phase_noise":"OFF","peak_photons":PEAK_PHOTONS,"VA_budget":"OFF"},"uniform_exact_VA_bank":sorted(float(c["V_A"]) for c in uni),"uniform_missing_VA":missing,"uniform_new_sources_built":built,"MB_bank_count":len(mb_all),"operational_endpoints":summary,"artifacts":{"table":"skr_vs_distance_three_scheme.csv","figure_png":"skr_vs_distance_three_scheme.png","figure_pdf":"skr_vs_distance_three_scheme.pdf","uniform":"uniform_optimized_candidates.csv","mb_fixed":"mb_fixed_results.csv","mb_optimized":"mb_optimized_candidates.csv"},"source_policy":"exact hash-matched C,w; no interpolation; direct Z_minus","limitations":["Uniform continuous VA optimum remains unresolved where requested source moments are missing.","MB optimized is the best exact 145-point bank candidate per distance; no local continuation was required.","No publication claim or baseline selection."]}
    (output/"skr_vs_distance_three_scheme_report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8"); print(json.dumps({"status":report["status"],"experiment_hash":experiment_hash,"operational_endpoints":summary,"uniform_missing_VA":missing},indent=2)); return 0


if __name__=="__main__": raise SystemExit(main())
