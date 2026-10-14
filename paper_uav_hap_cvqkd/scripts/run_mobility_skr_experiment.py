"""Finite MB enumeration and DP cloud-mobility demonstration; no AP or AO."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
from scripts import run_ao_effective_channel_no_fading_noise_reference as saved
from src.mobility_skr import load_candidates, channel_state, scientific_identity, ExactStateCache
from src.uav_mobility import (candidate_grid, path_intersections, moving_cloud,
    best_stationary, optimize_trajectory, scalar, usable_skr)

DEFAULT = ROOT / "results/mobility_aware_skr_20261014"
CONFIG = ROOT / "configs/mobility_aware_skr_demo.json"
SCHEMES = ("S1 Reference Fixed", "S2 Optimized Stationary", "S3 Moving SKR Only", "S4 Moving Mobility-Aware")


def verify_protected(manifest):
    saved.verify_protected(manifest)


def prepare_manifest(output):
    output.mkdir(parents=True, exist_ok=True)
    path = output / "startup_manifest.json"
    if path.exists():
        manifest = saved.read_json(path)
        verify_protected(manifest)
        return manifest
    files = [p for folder in ("src","scripts","configs","tests","results","docs",".agent")
        for p in (ROOT/folder).rglob("*") if p.is_file() and "__pycache__" not in p.parts
        and output not in p.parents and p.relative_to(ROOT).as_posix() not in saved.STATE]
    manifest = dict(captured_utc=datetime.now(timezone.utc).isoformat(),
        branch=subprocess.check_output(["git","branch","--show-current"],cwd=ROOT,text=True).strip(),
        HEAD=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),
        protected_hashes={p.relative_to(ROOT).as_posix():saved.digest(p) for p in files},
        frozen_actual_sha256=saved.digest(ROOT/"docs/FINAL_MODEL_SPEC.md"),
        lifecycle="NOT_READY_FOR_PUBLICATION_SCALE_RUNS", authorized_scope="Synthetic cached-source mobility diagnostic")
    saved.save(path, manifest, exclusive=True)
    return manifest


def validate_settings(settings):
    if settings["schema"] != "mobility-aware-skr-demo-v1":
        raise ValueError("Unsupported experiment schema")
    mission, opt = settings["mission"], settings["optimization"]
    if not isinstance(mission["slots"], int) or isinstance(mission["slots"], bool) or mission["slots"] <= 0:
        raise ValueError("Mission slots must be a positive integer")
    scalar(mission["slot_duration_s"], "slot duration", positive=True)
    scalar(mission["max_speed_m_per_s"], "speed", nonnegative=True)
    scalar(opt["reference_distance_m"], "distance normalization", positive=True)
    scalar(opt["positive_lambda_bits_per_use"], "positive penalty", positive=True)
    for value in opt["lambda_sweep_bits_per_use"]:
        scalar(value, "penalty sweep", nonnegative=True)
    for value in opt["cloud_speed_sweep_m_per_s"]:
        scalar(value, "cloud speed sweep", nonnegative=True)
    if opt["initial_position_freely_selectable"] is not True or opt["deployment_cost_included"] is not False:
        raise ValueError("This DP uses free initial position and excludes deployment costs")
    if opt["channel_use_rate_per_s"] is not None:
        scalar(opt["channel_use_rate_per_s"], "channel use rate", positive=True)
    geometry = settings["geometry"]
    positions = candidate_grid(geometry["grid_side_m"], geometry["grid_cells_per_side"])
    if positions.shape != (100,2) or geometry["grid_side_m"] != 1000. or geometry["grid_cells_per_side"] != 10:
        raise ValueError("Requested demonstration requires exactly 100 cell centers on the 1 km grid")
    reference = geometry["reference_position_index"]
    if not isinstance(reference,int) or isinstance(reference,bool) or not 0<=reference<len(positions):
        raise ValueError("Reference position must belong to the candidate grid")
    path_intersections(positions, geometry["hap_horizontal_m"], geometry["h_hap_m"],
                       geometry["h_uav_m"], settings["cloud"]["altitude_m"])
    return positions


def scheme_paths(usable, positions, reference_index, settings, penalty):
    stationary, means = best_stationary(usable)
    arguments = dict(slot_duration_s=settings["mission"]["slot_duration_s"],
        max_speed_m_per_s=settings["mission"]["max_speed_m_per_s"],
        reference_distance_m=settings["optimization"]["reference_distance_m"])
    third = optimize_trajectory(usable, positions, penalty_bits_per_use=0., **arguments)
    fourth = optimize_trajectory(usable, positions, penalty_bits_per_use=penalty, **arguments)
    if means[stationary] < means[reference_index]-1e-12 or third["average_skr"] < means[stationary]-1e-12:
        raise ValueError("Stationary/free-start DP dominance failed")
    if fourth["penalized_objective"] < means[stationary]-1e-12:
        raise ValueError("Penalized DP worse than feasible stationary solution")
    slots = usable.shape[1]
    return [np.full(slots,reference_index,dtype=int),np.full(slots,stationary,dtype=int),
            third["path"],fourth["path"]]


def scenario(settings, positions, winners, velocity=None, penalty=None):
    cloud, geometry, mission, opt = [settings[k] for k in ("cloud","geometry","mission","optimization")]
    times = np.arange(mission["slots"])*mission["slot_duration_s"]
    intersections = path_intersections(positions, geometry["hap_horizontal_m"], geometry["h_hap_m"],
                                      geometry["h_uav_m"], cloud["altitude_m"])
    blocked, centers = moving_cloud(intersections,times,cloud["initial_center_m"],
        cloud["velocity_m_per_s"] if velocity is None else velocity,cloud["radius_m"])
    raw = np.array([[winners[j][int(b)]["SKR"] for b in blocked[j]] for j in range(len(positions))])
    usable = usable_skr(raw)
    reference_index = settings["_reference_local_index"]
    penalty = opt["positive_lambda_bits_per_use"] if penalty is None else penalty
    paths = scheme_paths(usable, positions, reference_index, settings, penalty)
    summary, series = [], []
    for scheme, path in zip(SCHEMES, paths):
        coordinates = positions[path]
        legs = np.linalg.norm(np.diff(coordinates,axis=0),axis=1)
        if len(legs) and np.max(legs)>mission["max_speed_m_per_s"]*mission["slot_duration_s"]:
            raise ValueError("Scheme trajectory violates speed constraint")
        rates = usable[path,np.arange(len(times))]
        distance = float(legs.sum())
        mean = float(rates.mean())
        own_lambda = penalty if scheme==SCHEMES[3] else 0.
        summary.append(dict(scheme=scheme,average_skr_bits_per_use=mean,
            qkd_availability_percent=float(np.mean(rates>0)*100),total_flight_distance_m=distance,
            lambda_bits_per_use=own_lambda,penalized_objective_bits_per_use=mean-own_lambda*distance/opt["reference_distance_m"],
            objective_at_common_positive_lambda=mean-penalty*distance/opt["reference_distance_m"],
            initial_x_m=float(coordinates[0,0]),initial_y_m=float(coordinates[0,1]),
            final_x_m=float(coordinates[-1,0]),final_y_m=float(coordinates[-1,1]),
            max_transition_m=float(legs.max()) if len(legs) else 0.,
            maximum_allowed_transition_m=mission["max_speed_m_per_s"]*mission["slot_duration_s"]))
        cumulative = np.cumsum(rates)
        for n, j in enumerate(path):
            source = winners[int(j)][int(blocked[j,n])]
            series.append(dict(scheme=scheme,slot=n+1,slot_start_s=float(times[n]),
                slot_end_s=float(times[n]+mission["slot_duration_s"]),
                position_index=int(settings["_position_indices"][j]),x_m=float(positions[j,0]),y_m=float(positions[j,1]),
                blocked=bool(blocked[j,n]),cloud_x_m=float(centers[n,0]),cloud_y_m=float(centers[n,1]),
                raw_skr=source["SKR"],usable_skr=float(rates[n]),nu_raw=source["nu_raw"],V_A=source["V_A"],
                T_eff=source["T_eff"],ensemble_hash=source["ensemble_hash"],objective_key=source["objective_key"],
                leg_distance_m=0. if n==0 else float(legs[n-1]),cumulative_skr_contributions=float(cumulative[n]),
                cumulative_secret_bits=None if opt["channel_use_rate_per_s"] is None else
                    float(cumulative[n]*mission["slot_duration_s"]*opt["channel_use_rate_per_s"])))
    for item in summary:
        for name,baseline in (("S1",summary[0]),("S2",summary[1])):
            original=baseline["average_skr_bits_per_use"]
            item[f"improvement_vs_{name}_percent"]=(item["average_skr_bits_per_use"]-original)/original*100 if original>0 else None
    return summary,series,raw,usable,blocked,centers,intersections


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config",type=Path,default=CONFIG)
    parser.add_argument("--output",type=Path,default=DEFAULT)
    parser.add_argument("--smoke",action="store_true")
    args=parser.parse_args()
    import torch
    torch.set_num_threads(1)
    root_output=args.output.resolve()
    manifest=prepare_manifest(root_output)
    output=root_output/("smoke" if args.smoke else "full")
    output.mkdir(exist_ok=True)
    if (output/"experiment_receipt.json").exists():
        raise ValueError("Completed experiment exists; select a new output directory")
    settings=saved.read_json(args.config)
    positions=validate_settings(settings)
    candidates,config,roster=load_candidates(settings,manifest["protected_hashes"])
    indices=np.arange(100)
    if args.smoke:
        indices=np.array([0,9,44,90,99])
        positions=positions[indices]
        pairs={(.165,5.5),(.17,5.046875),(.2,1.3833230302980657)}
        candidates=[c for c in candidates if (c["nu_raw"],c["V_A"]) in pairs]
        if len(candidates)!=3:
            raise ValueError("Smoke source fixtures are absent from the authenticated catalog")
        settings["mission"]["slots"]=8
    settings["_position_indices"]=indices.tolist()
    settings["_reference_local_index"]=int(np.where(indices==settings["geometry"]["reference_position_index"])[0][0])
    identity=scientific_identity(settings,config)
    inputs=dict(settings=settings,scientific_identity=identity,source_roster_sha256=saved.digest(ROOT/settings["source_roster"]),
        candidate_hashes=[c["ensemble_hash"] for c in candidates],producer_sha256=saved.digest(Path(__file__)))
    if (output/"inputs.json").exists():
        if saved.read_json(output/"inputs.json")!=inputs:
            raise ValueError("Resume input/producer identity differs; select a new output directory")
    else:saved.save(output/"inputs.json",inputs,exclusive=True)
    cache=ExactStateCache(output/"objective_cache.jsonl",identity,manifest["protected_hashes"],config)
    began=time.perf_counter()
    states,winners,evaluations=[],[],[]
    for local_index,position in enumerate(positions):
        position_winners=[]
        for blocked in (False,True):
            state=channel_state(settings,position,blocked)
            state["position_index"]=int(indices[local_index])
            states.append(state)
            rows=[]
            for candidate in candidates:
                try:key,row=cache.evaluate(candidate,state)
                except Exception as error:
                    saved.save(output/"failure_receipt.json",dict(status="FAILED",position_index=state["position_index"],
                        blocked=blocked,nu_raw=candidate["nu_raw"],V_A=candidate["V_A"],error=str(error),
                        protected_changes=saved.verify_protected(manifest)))
                    raise
                flat=dict(row,objective_key=key,position_index=state["position_index"],blocked=blocked)
                rows.append(flat);evaluations.append(flat)
            position_winners.append(max(rows,key=lambda r:r["SKR"]))
        winners.append(position_winners)
        print("POSITION",local_index+1,"/",len(positions),"grid",int(indices[local_index]),
              "best K",[r["SKR"] for r in position_winners],"evaluations",cache.new_evaluations,"hits",cache.hits,flush=True)
        saved.save(output/"checkpoint.json",dict(status="RUNNING",completed_positions=local_index+1,
            new_evaluations=cache.new_evaluations,cache_hits=cache.hits,input_hash=saved.hash_json(inputs)))
    summary,series,raw,usable,blocked,centers,intersections=scenario(settings,positions,winners)
    if not blocked.any() or blocked.all():
        raise ValueError("Demonstration must contain both clear and blocked paths")
    saved.write_csv(output/"summary.csv",summary)
    saved.write_csv(output/"scheme_time_series.csv",series)
    saved.write_csv(output/"all_candidate_evaluations.csv",evaluations)
    saved.write_csv(output/"source_roster.csv",[{k:c[k] for k in ("nu_raw","V_A","C","w","ensemble_hash","source_cache_key","source_path")} for c in candidates])
    saved.save(output/"channel_states.json",states)
    saved.write_csv(output/"optimized_state_sources.csv",[r for group in winners for r in group])
    table=[]
    for j in range(len(positions)):
        for n in range(settings["mission"]["slots"]):
            r=winners[j][int(blocked[j,n])]
            table.append(dict(position_index=int(indices[j]),slot=n+1,blocked=bool(blocked[j,n]),
                raw_skr=float(raw[j,n]),usable_skr=float(usable[j,n]),nu_raw=r["nu_raw"],V_A=r["V_A"],objective_key=r["objective_key"]))
    saved.write_csv(output/"skr_table.csv",table)
    saved.write_csv(output/"positions.csv",[dict(position_index=int(indices[j]),x_m=float(p[0]),y_m=float(p[1]),
        intersection_x_m=float(intersections[j,0]),intersection_y_m=float(intersections[j,1])) for j,p in enumerate(positions)])
    velocity_rows,penalty_rows=[],[]
    base_velocity=np.asarray(settings["cloud"]["velocity_m_per_s"],dtype=float)
    if np.linalg.norm(base_velocity)==0:
        raise ValueError("A direction is required for the configured cloud-speed sweep")
    direction=base_velocity/np.linalg.norm(base_velocity)
    for speed in settings["optimization"]["cloud_speed_sweep_m_per_s"]:
        comparisons,_,_,_,_,_,_=scenario(settings,positions,winners,velocity=direction*speed)
        velocity_rows.extend(dict(row,cloud_speed_m_per_s=speed) for row in comparisons)
    for penalty in settings["optimization"]["lambda_sweep_bits_per_use"]:
        comparisons,_,_,_,_,_,_=scenario(settings,positions,winners,penalty=penalty)
        penalty_rows.append(dict(comparisons[3],sweep_lambda_bits_per_use=penalty))
    for a,b in zip(sorted(penalty_rows,key=lambda r:r["sweep_lambda_bits_per_use"]),sorted(penalty_rows,key=lambda r:r["sweep_lambda_bits_per_use"])[1:]):
        if b["total_flight_distance_m"]>a["total_flight_distance_m"]+1e-8:
            raise ValueError("Optimal flight distance increases with movement penalty")
    saved.write_csv(output/"cloud_velocity_sweep.csv",velocity_rows)
    saved.write_csv(output/"movement_penalty_sweep.csv",penalty_rows)
    # Channel/source statistics are time invariant conditional on binary blockage.
    if cache.new_evaluations+cache.hits!=len(positions)*2*len(candidates):
        raise ValueError("Exact finite-catalog coverage is incomplete")
    if not args.smoke:
        from scripts.plot_mobility_skr_results import plot_results
        plot_results(output,settings)
    final=dict(status="CURRENTLY_VERIFIED_PASS",scope="SYNTHETIC_MOBILITY_DIAGNOSTIC_ONLY",
        input_sha256=saved.digest(output/"inputs.json"),scientific_identity_sha256=saved.hash_json(identity),
        elapsed_seconds=time.perf_counter()-began,positions=len(positions),source_candidates=len(candidates),
        states=len(states),candidate_evaluations=len(evaluations),new_evaluations=cache.new_evaluations,cache_hits=cache.hits,
        finite_catalog_enumeration_complete=True,DP_discrete_optimum=True,continuous_optimum=False,
        numerical_failures=[],interpolation=False,AP_or_AO=False,new_source_moments=False,
        cloud_velocity_experiments=len(settings["optimization"]["cloud_speed_sweep_m_per_s"]),
        movement_penalty_experiments=len(settings["optimization"]["lambda_sweep_bits_per_use"]),
        figures_exported=0 if args.smoke else 6,cloud_geometry_blocked_fraction=float(blocked.mean()),
        summary=summary,protected_files=len(manifest["protected_hashes"]),protected_changes=saved.verify_protected(manifest),
        propulsion_energy_model=False,certified_fading_security_bound=False,
        lifecycle="NOT_READY_FOR_PUBLICATION_SCALE_RUNS",commit_or_push=False,
        output_sha256={p.name:saved.digest(p) for p in output.iterdir() if p.is_file()})
    saved.save(output/"experiment_receipt.json",final,exclusive=True)
    print("EXPERIMENT_COMPLETE",final["status"],"evaluations",len(evaluations),"elapsed",final["elapsed_seconds"],flush=True)


if __name__=="__main__":main()
