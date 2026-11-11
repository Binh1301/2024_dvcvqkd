"""Cloud-only, eleven-seed validation and full cropped-field export."""
from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import numpy as np
from scipy.ndimage import label, shift
from scipy.stats import t

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.ibrahim_stationary_cloud import (MODEL_NAME, StationaryCloudConfig, SpectralDomain,
                                         StationaryCloudSimulator, relative_intensity)

METRICS = ["mean", "variance", "second_moment", "cloud_fraction", "full_domain_variance",
           "component_count", "mean_component_area_m2", "max_component_area_m2", "third_moment", "fourth_moment"]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    path.write_bytes((json.dumps(value, indent=2, allow_nan=False, ensure_ascii=False)+"\n").encode("utf-8"))


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def uncertainty(values):
    values = np.asarray(values, float)
    se = values.std(axis=0, ddof=1)/np.sqrt(len(values))
    half = t.ppf(.975, len(values)-1)*se
    return values.mean(axis=0), se, half


def numerical_probe(c, limits):
    d = SpectralDomain(c)
    start = d.draw(np.random.default_rng(c.seed))
    moved = start.copy()
    for _ in range(c.slots):
        moved *= d.phase
    cov0, cov1 = d.empirical_covariance(start), d.empirical_covariance(moved)
    linear = d.to_real(start)
    for _ in range(c.slots):
        linear = shift(linear, (c.vy_m_s*c.dt_s/c.dy_m, c.vx_m_s*c.dt_s/c.dx_m),
                       order=1, mode="grid-wrap", prefilter=False)
    marker = np.exp(-2*np.pi**2*9*(d.fx**2+d.fy**2)).astype(complex)
    marker /= d.to_real(marker).max()
    probes = {str(k): float(np.max(abs(d.crop(d.to_real(marker*d.phase**k)))))
              for k in (0, min(400,c.slots-1), c.slots-1)}
    displacement = -float(np.angle(d.phase[0,1]))/(2*np.pi/d.nx)
    err = float(np.max(abs(cov1-cov0))/cov0[0,0])
    phase_error = float(np.max(abs(d.to_real(start*d.phase**8)-d.to_real(start*d.shift_phase(8*c.vx_m_s*c.dt_s/c.dx_m,
                                                                                                 8*c.vy_m_s*c.dt_s/c.dy_m)))))
    passed = err <= limits["spectral_relative_error_limit"] and max(probes.values()) <= limits["tagged_packet_observation_limit"]
    return {"status": "CURRENTLY_VERIFIED_PASS" if passed else "FAILED",
            "spectral_iterations": c.slots,
            "spectral_relative_variance_change": float(cov1[0,0]/cov0[0,0]-1),
            "spectral_max_covariance_error_relative_to_variance": err,
            "linear_interpolation_relative_variance_change_same_input": float(linear.var()/cov0[0,0]-1),
            "linear_comparison_scope": "same synthetic full field, no AR/noise; numerical operator comparison only; old experiment NOT rerun",
            "one_slot_x_displacement_cells": displacement,
            "one_slot_x_displacement_m": displacement*c.dx_m,
            "eight_slot_x_displacement_m": 8*displacement*c.dx_m,
            "eight_steps_vs_one_shift_max_error": phase_error,
            "seam_packet_max_absolute_in_observation_by_slot": probes,
            "packet": "periodic bandlimited Gaussian, sigma=3 cells, centre at synthetic seam, peak=1"}


def compare_saved_baseline():
    old = ROOT/"results/ibrahim_cloud_demo_20261111"
    r = json.loads((old/"run_report.json").read_text())
    rows = list(csv.DictReader((old/"coverage_timeseries.csv").open()))
    std = np.array([float(row["raw_std"]) for row in rows])
    data = np.load(old/"cloud_snapshots.npz", allow_pickle=False)
    correlations = []
    for i in (1,2):
        lag = float(data["time_s"][i]-data["time_s"][0])
        displacement = r["parameters"]["vx_m_s"]*lag/(r["parameters"]["width_m"]/r["parameters"]["nx"])
        if not np.isclose(displacement, round(displacement)):
            raise ValueError("baseline snapshot compensation requires exact integer shift")
        compensated = np.roll(data["raw_noise"][i], -round(displacement), axis=1)
        correlations.append({"lag_s": lag,
                             "eulerian_pearson": float(np.corrcoef(data["raw_noise"][0].ravel(),data["raw_noise"][i].ravel())[0,1]),
                             "motion_compensated_pearson": float(np.corrcoef(data["raw_noise"][0].ravel(),compensated.ravel())[0,1])})
    return {"scope": "read-only saved single-seed baseline; no baseline rerun or comparable baseline ensemble",
            "parameters": r["parameters"], "gamma": r["gamma_fixed_all_slots"], "coverage": r["coverage"],
            "initial_variance": float(std[0]**2), "final_variance": float(std[-1]**2),
            "variance_ratio_final_initial": float((std[-1]/std[0])**2),
            "temporal_correlation_saved_snapshots": correlations,
            "comparison_limit": "Baseline snapshot Pearson and new ensemble conditional-regression autocorrelation use different estimators/spatial laws; do not rank physical realism or overall superiority."}


def run(settings_path, output):
    start_time = time.perf_counter()
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    c = StationaryCloudConfig(**settings["simulation"])
    seeds, snapshots, lags = settings["ensemble_seeds"], settings["snapshot_slots"], settings["temporal_lags"]
    if len(seeds)<10 or len(set(seeds)) != len(seeds) or seeds[0] != c.seed:
        raise ValueError("at least ten distinct seeds; first must equal main seed")
    if any(type(k) is not int or not 0<=k<c.slots for k in snapshots+lags):
        raise ValueError("snapshot/lag slots outside configured horizon")
    output.mkdir(parents=True, exist_ok=False)
    protected_paths = subprocess.check_output(["git","ls-files","src","configs","tests/test_ibrahim_cloud.py",
                     "scripts/visualize_ibrahim_cloud.py","docs/IBRAHIM_CLOUD_README.md",
                     "docs/FINAL_MODEL_SPEC.md","docs/SECURITY_SCOPE_FREEZE.md"],cwd=ROOT,text=True).splitlines()
    protected_paths += [p.relative_to(ROOT).as_posix() for p in (ROOT/"results/ibrahim_cloud_demo_20261111").rglob("*") if p.is_file()]
    protected = {p:sha(ROOT/p) for p in sorted(set(protected_paths))}
    write_json(output/"protected_inputs.json",protected)
    paper = Path(r"C:\Users\HP\Downloads\Anticipating_Optical_Availability_in_Hybrid_RF_FSO_Links_Using_RF_Beacons_and_Deep_Learning.pdf")
    producers = ["src/ibrahim_stationary_cloud.py","scripts/run_ibrahim_stationary_cloud.py",
                 "scripts/plot_ibrahim_stationary_cloud.py","tests/test_ibrahim_stationary_cloud.py"]
    write_json(output/"design_receipt.json",{
        "settings":settings, "config_sha256":sha(settings_path), "producer_hashes":{p:sha(ROOT/p) for p in producers},
        "git_branch":subprocess.check_output(["git","branch","--show-current"],cwd=ROOT,text=True).strip(),
        "git_head":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),
        "worktree_at_launch":subprocess.check_output(["git","status","--short"],cwd=ROOT,text=True),
        "startup_state":"clean before this task; branch feat/cloud-11-11; HEAD 0c039f394511ce43c0038e76694c4f15e446b1eb",
        "reference_pdf": {"path":str(paper),"sha256":sha(paper),"algorithm_pdf_page":10} if paper.is_file() else None,
        "environment":{"python":sys.version,"numpy":np.__version__,"scipy":__import__("scipy").__version__},
        "scope":"CLOUD_GENERATION_ONLY; no optical blockage, attenuation, QKD, SKR or UAV optimization"})
    d = SpectralDomain(c)
    boundary = d.boundary_receipt()
    write_json(output/"boundary_validation.json",boundary)
    numerical = numerical_probe(c, settings["validation"])
    write_json(output/"numerical_validation.json",numerical)
    metrics = np.empty((len(seeds),c.slots,len(METRICS)))
    temporal = np.empty((len(seeds),len(lags)))
    eulerian = np.empty_like(temporal)
    covariance_initial, covariance_final, gammas = [], [], []
    main_x = np.empty((c.slots,c.ny,c.nx))
    component_rows = []
    anchor_x = d.x0-round(c.vx_m_s*c.horizon_s/c.dx_m)
    anchor_y = d.y0-round(c.vy_m_s*c.horizon_s/c.dy_m)
    for si,seed in enumerate(seeds):
        sim = StationaryCloudSimulator(replace(c,seed=seed))
        gammas.append(sim.gamma)
        initial_full = d.to_real(sim.coefficients)
        material_initial = initial_full[anchor_y:anchor_y+c.ny,anchor_x:anchor_x+c.nx].copy()
        material_energy = np.mean(material_initial**2)
        covariance_initial.append(d.empirical_covariance(sim.coefficients))
        if si==0:
            initial_fine,initial_coarse = sim.initial_fine,sim.initial_coarse
        for k in range(c.slots):
            x = sim.initial if k==0 else sim.step()
            presence = x>sim.gamma
            components,count = label(presence,structure=np.ones((3,3),dtype=int))
            sizes = np.bincount(components.ravel())[1:]*c.dx_m*c.dy_m
            power = abs(sim.coefficients)**2
            full_var = (power[:,0].sum()+2*power[:,1:].sum())/(d.nx*d.ny)**2
            metrics[si,k] = [x.mean(),x.var(),np.mean(x*x),presence.mean(),full_var,count,
                             float(sizes.mean()) if count else 0.,float(sizes.max()) if count else 0.,
                             np.mean(x**3),np.mean(x**4)]
            if k in lags:
                compensated = d.to_real(sim.coefficients*np.conjugate(d.phase)**k)
                material = compensated[anchor_y:anchor_y+c.ny,anchor_x:anchor_x+c.nx]
                temporal[si,lags.index(k)] = np.mean(material_initial*material)/material_energy
                eulerian[si,lags.index(k)] = np.mean(sim.initial*x)
            if si==0:
                main_x[k] = x
                component_rows.append({"slot":k,"time_s":k*c.dt_s,"components_8_connected":count,
                                       "mean_area_m2":float(sizes.mean()) if count else 0.,
                                       "median_area_m2":float(np.median(sizes)) if count else 0.,
                                       "maximum_area_m2":float(sizes.max()) if count else 0.})
        covariance_final.append(d.empirical_covariance(sim.coefficients))
        print(f"seed {seed}: {si+1}/{len(seeds)} complete; fraction final={metrics[si,-1,3]:.4f}",flush=True)
    covariance_initial,covariance_final = np.array(covariance_initial),np.array(covariance_final)
    metadata = {"model_name":MODEL_NAME,"parameters":asdict(c),"rho":c.rho,"innovation_scale":c.innovation_scale,
                "gamma_fixed":gammas[0],"mask_semantics":"cloud presence diagnostic only; NOT optical blockage",
                "X_semantics":"dimensionless Gaussian latent; target ensemble mean=0, variance=1",
                "intensity_semantics":"relative nonnegative intensity; NOT physical CLWC",
                "normalization":"fixed linear DC projection and deterministic marginal variance factors; no sample-std or per-frame normalization",
                "domain":boundary}
    np.savez_compressed(output/"cloud_fields.npz", X=main_x,intensity=relative_intensity(main_x,c),
                        diagnostic_mask=(main_x>gammas[0]).astype(np.uint8),time_s=np.arange(c.slots)*c.dt_s,
                        x_m=(np.arange(c.nx)+.5)*c.dx_m,y_m=(np.arange(c.ny)+.5)*c.dy_m,
                        initial_fine=initial_fine,initial_coarse=initial_coarse,
                        metadata_json=np.array(json.dumps(metadata)))
    np.savez_compressed(output/"ensemble_validation.npz",seeds=seeds,metrics=metrics,metric_names=METRICS,
                        temporal=temporal,eulerian=eulerian,temporal_lags=lags,gamma=gammas,
                        covariance_initial=covariance_initial,covariance_final=covariance_final,
                        covariance_target=d.covariance(),fine_covariance_target=d.covariance("fine"),
                        coarse_covariance_target=d.covariance("coarse"))
    write_json(output/"metadata.json",metadata)
    write_csv(output/"connected_components_main.csv",component_rows)
    mean,se,half = uncertainty(metrics)
    rows=[]
    for k in range(c.slots):
        row={"slot":k,"time_s":k*c.dt_s}
        for mi,name in enumerate(METRICS):
            row.update({name+"_main":metrics[0,k,mi],name+"_ensemble_mean":mean[k,mi],
                        name+"_ensemble_se":se[k,mi],name+"_ci95_halfwidth":half[k,mi]})
        rows.append(row)
    write_csv(output/"time_statistics.csv",rows)
    tm,ts,th = uncertainty(temporal)
    temporal_rows=[{"lag_slots":lag,"lag_s":lag*c.dt_s,"rho_to_lag":c.rho**lag,
                    "motion_compensated_mean":tm[i],"independent_seed_se":ts[i],"ci95_halfwidth":th[i],
                    "estimator":"seed-wise sum(X0_material*Xlag_material)/sum(X0_material^2); then independent-seed mean"}
                   for i,lag in enumerate(lags)]
    write_csv(output/"temporal_correlation.csv",temporal_rows)
    multiplier=settings["validation"]["ensemble_standard_error_multiplier"]
    checks=[]
    def check(name,values,target):
        avg,error,_ = uncertainty(values)
        delta=abs(float(avg)-float(target))
        checks.append({"name":name,"estimate":float(avg),"target":float(target),"independent_seed_se":float(error),
                       "criterion":f"absolute error <= {multiplier}*SE + 1e-10",
                       "passed":bool(delta<=multiplier*error+1e-10)})
    expected_var=d.expected_crop_variance()
    for k in snapshots:
        for mi,target in ((0,0.),(1,expected_var),(2,1.),(4,1.),(8,0.),(9,3.)):
            check(f"{METRICS[mi]}_slot_{k}",metrics[:,k,mi],target)
    for mi in (0,1,2,4):
        check(f"paired_final_minus_initial_{METRICS[mi]}",metrics[:,-1,mi]-metrics[:,0,mi],0.)
    for i,lag in enumerate(lags):
        check(f"motion_compensated_rho_lag_{lag}",temporal[:,i],c.rho**lag)
    for axis in (0,1):
        for lag in (0,1,5,10,20):
            yy,xx=(0,lag) if axis==0 else (lag,0)
            check(f"initial_spatial_covariance_axis_{axis}_lag_{lag}",covariance_initial[:,yy,xx],d.covariance()[yy,xx])
    baseline=compare_saved_baseline()
    new_main = {"gamma":gammas[0],"initial_fraction":float(metrics[0,0,3]),"final_fraction":float(metrics[0,-1,3]),
                "time_mean_fraction":float(metrics[0,:,3].mean()),"minimum_fraction":float(metrics[0,:,3].min()),
                "maximum_fraction":float(metrics[0,:,3].max()),"initial_variance":float(metrics[0,0,1]),
                "final_variance":float(metrics[0,-1,1]),"initial_mean":float(metrics[0,0,0]),"final_mean":float(metrics[0,-1,0])}
    ensemble_summary={}
    for name,mi in (("final_fraction",3),("time_mean_fraction",3),("initial_variance",1),("final_variance",1)):
        values = (metrics[:,:,mi].mean(axis=1) if name=="time_mean_fraction" else
                  metrics[:,0 if name.startswith("initial") else -1,mi])
        avg,error,ci=uncertainty(values)
        ensemble_summary[name]={"mean":float(avg),"se":float(error),"ci95_halfwidth":float(ci)}
    changed=[p for p,v in protected.items() if sha(ROOT/p)!=v]
    passed = all(ch["passed"] for ch in checks) and not changed and numerical["status"]==boundary["status"]=="CURRENTLY_VERIFIED_PASS"
    report={"status":"CURRENTLY_VERIFIED_PASS" if passed else "FAILED","scope":"CLOUD_GENERATION_ONLY",
            "model_name":MODEL_NAME,"main_seed":c.seed,"independent_seeds":seeds,"slots":c.slots,
            "rho":c.rho,"innovation_scale":c.innovation_scale,"main":new_main,"ensemble":ensemble_summary,
            "expected_crop_population_variance":expected_var,"checks":checks,"failed_checks":[v for v in checks if not v["passed"]],
            "uncertainty":"approximate Student-t 95% intervals across independent seeds; cells/slots are not treated as independent; four-SE checks were set before runs and are descriptive, not simultaneous confidence certification",
            "baseline":baseline,"numerical":numerical,"boundary":boundary,
            "protected_files":{"count":len(protected),"changed":changed},"elapsed_wall_s":time.perf_counter()-start_time,
            "model_claim":"Gaussian stationary law follows from A C A*=C and independent Z~N(0,C); ensemble checks test numerical implementation, not meteorological realism",
            "frozen_spec_sha256":sha(ROOT/"docs/FINAL_MODEL_SPEC.md"),"frozen_historical_mismatch_preserved":True,
            "lifecycle":"NOT_READY_FOR_PUBLICATION_SCALE_RUNS","security":"UNVALIDATED_SECURITY_MODEL",
            "not_run":["full repository suite","physical CLWC calibration","optical blockage/attenuation","QKD/SKR/finite-size/UAV integration","training/final-test/heldout/publication evaluation"]}
    write_json(output/"validation.json",report)
    print(json.dumps({"status":report["status"],"main":new_main,"ensemble":ensemble_summary,
                      "failed_checks":report["failed_checks"],"elapsed_wall_s":report["elapsed_wall_s"]},indent=2),flush=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config",type=Path,default=ROOT/"configs/ibrahim_stationary_cloud.json")
    parser.add_argument("--output",type=Path,default=ROOT/"results/ibrahim_stationary_cloud_20261111")
    args=parser.parse_args()
    run(args.config,args.output)
