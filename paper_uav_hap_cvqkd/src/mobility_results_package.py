"""Saved-data validation and derived IEEE plotting quantities; no new physics."""
from __future__ import annotations

import csv
from pathlib import Path
import math
import numpy as np

from scripts import run_ao_effective_channel_no_fading_noise_reference as saved
from scripts.run_mobility_skr_experiment import SCHEMES, scenario, validate_settings

ROOT=Path(__file__).resolve().parents[1]
ORIGINAL=ROOT/"results/mobility_aware_skr_20261014"


def read_csv(path):
    with Path(path).open(encoding="utf-8",newline="") as stream:return list(csv.DictReader(stream))


def reconstructed_winners(rows):
    winners=[[None,None] for _ in range(100)]
    for row in rows:
        j=int(row["position_index"]);blocked=row["blocked"] in (True,"True")
        result={k:float(row[k]) for k in ("nu_raw","V_A","C","w","SKR","T_eff")}
        result.update({k:row[k] for k in ("ensemble_hash","objective_key")})
        if winners[j][int(blocked)] is not None:raise ValueError("Duplicate position/state winner")
        winners[j][int(blocked)]=result
    if any(row is None for pair in winners for row in pair):raise ValueError("Missing position/state winner")
    return winners


def verify_series(settings, series, summary):
    positions=validate_settings(settings)
    slots=settings["mission"]["slots"];dt=settings["mission"]["slot_duration_s"]
    speed=settings["mission"]["max_speed_m_per_s"]
    for scheme,record in zip(SCHEMES,summary):
        group=sorted((r for r in series if r["scheme"]==scheme),key=lambda r:int(r["slot"]))
        if len(group)!=slots or [int(r["slot"]) for r in group]!=list(range(1,slots+1)):
            raise ValueError("Missing/duplicate mission slots")
        index=np.array([int(r["position_index"]) for r in group])
        if ((index<0)|(index>=100)).any():raise ValueError("Trajectory leaves the grid")
        coordinates=np.array([[float(r["x_m"]),float(r["y_m"])] for r in group])
        if not np.array_equal(positions[index],coordinates):raise ValueError("Coordinates/grid index mismatch")
        legs=np.linalg.norm(np.diff(coordinates,axis=0),axis=1)
        if (legs>speed*dt).any():raise ValueError("Speed constraint violated")
        rates=np.array([float(r["usable_skr"]) for r in group])
        raw=np.array([float(r["raw_skr"]) for r in group])
        if not np.isfinite(rates).all() or not np.array_equal(rates,np.maximum(raw,0.)):
            raise ValueError("Usable/signed rate inconsistency")
        if abs(float(record["average_skr_bits_per_use"])-rates.mean())>1e-12:
            raise ValueError("Summary/per-slot mean differs")
        if abs(float(record["total_flight_distance_m"])-legs.sum())>1e-10:
            raise ValueError("Summary/trajectory flight distance differs")
        availability=float(np.mean(rates>0)*100)
        if abs(float(record["qkd_availability_percent"])-availability)>1e-12:
            raise ValueError("Positive-rate slot availability differs")
        penalty=float(record["lambda_bits_per_use"])
        objective=float(rates.mean())-penalty*float(legs.sum())/settings["optimization"]["reference_distance_m"]
        if abs(float(record["penalized_objective_bits_per_use"])-objective)>1e-12:
            raise ValueError("Penalized objective/noise units differ")
        for n,row in enumerate(group):
            if float(row["slot_start_s"])!=n*dt or float(row["slot_end_s"])!=(n+1)*dt:
                raise ValueError("Slot timing differs")
            expected=0. if n==0 else float(legs[n-1])
            if abs(float(row["leg_distance_m"])-expected)>1e-12:raise ValueError("Per-slot leg distance differs")
    values=[float(r["average_skr_bits_per_use"]) for r in summary]
    if values[1]<values[0]-1e-12 or values[2]<values[1]-1e-12:
        raise ValueError("S2/S1 or S3/S2 dominance failed")
    if float(summary[3]["penalized_objective_bits_per_use"])<values[1]-1e-12:
        raise ValueError("S4 objective below feasible stationary solution")
    return dict(status="CURRENTLY_VERIFIED_PASS",schemes=4,slots_per_scheme=slots,
        grid_membership=True,speed_constraints=True,signed_and_usable_rates=True,
        flight_distances=True,summary_means=True,availability_definition="fraction of slots with usable S>0")


def load_existing():
    full=ORIGINAL/"full"
    receipt=saved.read_json(full/"experiment_receipt.json")
    for name,want in receipt["output_sha256"].items():
        if saved.digest(full/name)!=want:raise ValueError(f"Original output hash differs: {name}")
    validation=saved.read_json(ORIGINAL/"final_validation.json")
    if validation["status"]!="CURRENTLY_VERIFIED_PASS":raise ValueError("Original validation is not current")
    inputs=saved.read_json(full/"inputs.json")
    for name,want in inputs["scientific_identity"]["scientific_implementation"].items():
        if saved.digest(ROOT/name)!=want:raise ValueError(f"Original scientific producer differs: {name}")
    settings=inputs["settings"]
    summary=read_csv(full/"summary.csv");series=read_csv(full/"scheme_time_series.csv")
    series_check=verify_series(settings,series,summary)
    winners=reconstructed_winners(read_csv(full/"optimized_state_sources.csv"))
    reconstructed,*_=scenario(settings,validate_settings(settings),winners)
    for old,new in zip(summary,reconstructed):
        for field in ("average_skr_bits_per_use","total_flight_distance_m","penalized_objective_bits_per_use"):
            if abs(float(old[field])-new[field])>1e-12:raise ValueError("Recomputed DP summary differs")
    return dict(settings=settings,inputs=inputs,summary=summary,series=series,winners=winners,
        states=saved.read_json(full/"channel_states.json"),positions=read_csv(full/"positions.csv"),
        velocity=read_csv(full/"cloud_velocity_sweep.csv"),penalty=read_csv(full/"movement_penalty_sweep.csv"),
        validation=series_check)


def cumulative_normalized(series,slots):
    if not isinstance(slots,int) or slots<=0:raise ValueError("Positive slot count required")
    result=[]
    for scheme in SCHEMES:
        group=sorted((r for r in series if r["scheme"]==scheme),key=lambda r:int(r["slot"]))
        if len(group)!=slots:raise ValueError("Cumulative slot coverage differs")
        value=0.
        result.append(dict(scheme=scheme,slot=0,time_s=0.,cumulative_normalized_skr=0.,initial_boundary=True))
        for row in group:
            value+=float(row["usable_skr"])
            result.append(dict(scheme=scheme,slot=int(row["slot"]),time_s=float(row["slot_end_s"]),
                cumulative_normalized_skr=value/slots,initial_boundary=False))
    return result


def tradeoff_metrics(summary):
    s1,s2,s3,s4=[float(r["average_skr_bits_per_use"]) for r in summary]
    d3,d4=[float(summary[i]["total_flight_distance_m"]) for i in (2,3)]
    return dict(S4_SKR_retained_vs_S3_percent=100*s4/s3 if s3>0 else None,
        S4_flight_distance_reduction_vs_S3_percent=100*(1-d4/d3) if d3>0 else None,
        S4_gain_vs_S1_percent=100*(s4-s1)/s1 if s1>0 else None,
        S4_gain_vs_S2_percent=100*(s4-s2)/s2 if s2>0 else None,
        S4_absolute_gain_vs_S1=s4-s1,S4_absolute_gain_vs_S2=s4-s2)


def projected_cloud_footprint(settings,center):
    g=settings["geometry"];h=settings["cloud"]["altitude_m"]
    fraction=(h-g["h_uav_m"])/(g["h_hap_m"]-g["h_uav_m"])
    if not 0<fraction<1:raise ValueError("Cloud altitude outside the link")
    # The circle shown at UAV coordinates is the inverse-ray occlusion set, not a cloud at h_U.
    return (np.asarray(center)-fraction*np.asarray(g["hap_horizontal_m"]))/ (1-fraction),settings["cloud"]["radius_m"]/(1-fraction)


def boundary_audit(data):
    winners=data["winners"];settings=data["settings"]
    positions=validate_settings(settings);by_position={j:[] for j in range(100)}
    table=read_csv(ORIGINAL/"full/skr_table.csv")
    for r in table:by_position[int(r["position_index"])].append(r)
    rows=[]
    for j,position in enumerate(positions):
        blocked=sum(r["blocked"]=="True" for r in by_position[j]);nt=len(by_position[j])
        clear=max(0.,winners[j][0]["SKR"]);cloudy=max(0.,winners[j][1]["SKR"])
        rows.append(dict(position_index=j,x_m=float(position[0]),y_m=float(position[1]),
            clear_skr=clear,blocked_skr=cloudy,blocked_slots=blocked,blocked_fraction=blocked/nt,
            predicted_stationary_mean=((nt-blocked)*clear+blocked*cloudy)/nt,
            on_grid_boundary=bool(np.any((position==50)|(position==950)))))
    best=max(rows,key=lambda r:r["predicted_stationary_mean"])
    no_cloud=max(rows,key=lambda r:r["clear_skr"])
    return rows,dict(stationary_best=best,no_cloud_counterfactual_best=no_cloud,
        interpretation="finite-grid balance of geometry-dependent clear rate and cloud exposure; boundary is not an implementation error; no continuous-area optimum claimed")


def fading_omissions(data):
    rows=[]
    for state in data["states"]:
        j=state["position_index"];blocked=state["blocked"];winner=data["winners"][j][int(blocked)]
        m=state["moments"];t=m["mean_sqrt_eta"]**2;va=winner["V_A"]
        fading=(m["mean_eta"]-t)*va
        physical_channel=m["mean_eta"]*.0186
        adopted=t*.0186
        full=fading+physical_channel
        rows.append(dict(position_index=j,blocked=blocked,nu_raw=winner["nu_raw"],V_A=va,
            mean_eta=m["mean_eta"],mean_sqrt_eta=m["mean_sqrt_eta"],mean_eta_xi_total=m["mean_eta_xi_total"],
            T_eff=t,N_adopted=adopted,N_fading_omitted=fading,
            channel_output_noise_difference=(m["mean_eta"]-t)*.0186,N_full_moment_matched=full,
            xi_full_moment_matched=full/t,b_adopted=1+t*(va+.0186),b_full=1+m["mean_eta"]*(va+.0186),
            b_difference=full-adopted,Z_adopted=2*math.sqrt(t)*winner["C"]-math.sqrt(2*winner["w"]*adopted),
            Z_full_noise_algebra=2*math.sqrt(t)*winner["C"]-math.sqrt(2*winner["w"]*full),
            scope="algebraic omission audit only; no new full-fading MI/Holevo/security result"))
    return rows
