"""Prepare saved MB results, compute only missing Uniform states, export IEEE package."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import numpy as np
from scripts import run_ao_effective_channel_no_fading_noise_reference as saved
from scripts.run_theta10_D55_unconstrained_three_scheme import unconstrained_config, candidate_from_payload
from scripts.exact_cache_provenance import source_settings, verify_source_payload
from scripts.run_mobility_skr_experiment import SCHEMES, scenario, validate_settings
from src.mobility_skr import ExactStateCache
from src.mobility_results_package import (ORIGINAL,load_existing,read_csv,cumulative_normalized,
    tradeoff_metrics,boundary_audit,fading_omissions,reconstructed_winners,verify_series)

OUT=ROOT/"results/mobility_numerical_results_package_20261014"


def prepare():
    data=load_existing();plot=OUT/"plot_data";plot.mkdir(exist_ok=True)
    manifest=saved.read_json(OUT/"startup_manifest.json");saved.verify_protected(manifest)
    for name,rows in (("figure_1_positions",data["positions"]),("figure_2_skr_time",data["series"]),
        ("figure_3_cumulative_normalized",cumulative_normalized(data["series"],data["settings"]["mission"]["slots"])),
        ("figure_4_skr_flight",data["penalty"]),("figure_5_cloud_velocity",data["velocity"]),
        ("figure_6_source_parameters",data["series"]),("performance_summary",data["summary"])):
        saved.write_csv(plot/(name+".csv"),rows)
    snapshots=[r for r in data["series"] if r["scheme"]==SCHEMES[0] and int(r["slot"]) in (1,10,17,21,30)]
    saved.write_csv(plot/"figure_1_cloud_snapshots.csv",snapshots)
    boundary,explanation=boundary_audit(data)
    saved.write_csv(OUT/"stationary_boundary_audit.csv",boundary)
    saved.save(OUT/"stationary_boundary_audit.json",explanation)
    saved.write_csv(OUT/"fading_omission_audit.csv",fading_omissions(data))
    saved.save(OUT/"tradeoff_metrics.json",tradeoff_metrics(data["summary"]))
    reference_path=ROOT/"results/manuscript_corrected_3moments/ideal_heterodyne_reference_20261013/reference_result.json"
    prior=saved.read_json(reference_path)
    # Inspect stored numerical/security precision evidence, never launch a new mixture MC run.
    def fields(value,names):
        matches=[]
        if isinstance(value,dict):
            for k,v in value.items():
                if k in names:matches.append(dict(field=k,value=v))
                if isinstance(v,(dict,list)):matches.extend(fields(v,names))
        elif isinstance(value,list):
            for v in value:matches.extend(fields(v,names))
        return matches
    precision=fields(prior,{"status","sampling_precision_pass","MI_valid","stderr","sampling_stderr_tolerance",
        "rigorous_global_error_enclosure","security_bound_status","total_error_certified"})
    source_roster=read_csv(ROOT/data["settings"]["source_roster"])
    baseline=saved.read_json(ROOT/"results/manuscript_corrected_3moments/implementation_validation/baseline_manifest.json")
    absent=[r["source_path"] for r in source_roster if r["family"]=="MB" and r["source_path"] not in baseline["protected_hashes"]]
    security=dict(status="PRELIMINARY_EFFECTIVE_GAUSSIAN_IGNORING_FADING_VARIANCE",
        fading_aware_numerical_modules_exist=True,complete_validated_fading_aware_evaluator_available=False,
        full_comparison_rerun=False,mixture_MC_rerun=False,
        reasons=["Stored mixture MI sampling precision not met; this is not a validated full-fading rate table",
            "Numerical interval Holevo lacks rigorous continuous error enclosure and operational fading-protocol justification",
            "Original corrected evaluator source snapshot does not authorize every later MB source; no guard bypass performed"],
        corrected_source_paths_outside_original_snapshot=absent,
        stored_precision_evidence=precision,reference_result_sha256=saved.digest(reference_path),
        raw_physical_PDF_three_moments_unchanged=True,
        omission="N_adopted=T_eff*xi_ch, rather than (mean_eta-T_eff)*VA+mean_eta*xi_ch",
        additional_output_noise_difference="(mean_eta-T_eff)*(VA+xi_ch)",
        symplectic_covariance_and_Z_noise_terms_consistent_in_each_existing_mode=True,
        full_security_lower_bound_claim=False,publication_lifecycle="NOT_READY_FOR_PUBLICATION_SCALE_RUNS")
    saved.save(OUT/"scientific_validation_audit.json",security)
    audit=dict(status="CURRENTLY_VERIFIED_PASS",scope="existing-data audit and preliminary plotting only",
        reproduced_summary=data["summary"],series_validation=data["validation"],
        old_MB_evaluations_repeated=0,missing_Uniform_candidates=sum(r["family"]=="Uniform" for r in source_roster),
        missing_Uniform_state_evaluations=100*2*sum(r["family"]=="Uniform" for r in source_roster),
        protected_changes=saved.verify_protected(manifest),input_config_sha256=saved.digest(ROOT/"configs/mobility_aware_skr_demo.json"),
        package_scientific_status=security["status"],LaTeX_compiler="BLOCKED_BY_ENVIRONMENT: no pdflatex/latexmk/tectonic found")
    saved.save(OUT/"audit.json",audit)
    from scripts.plot_mobility_numerical_package import render_package
    render_package(OUT,data["settings"])
    saved.save(OUT/"preparation_receipt.json",dict(status="CURRENTLY_VERIFIED_PASS",figures=6,
        sizes=["single","double"],MB_rerun=False,
        output_sha256={p.relative_to(OUT).as_posix():saved.digest(p) for folder in (plot,OUT/"figures") for p in folder.iterdir()}))
    print("PREPARE_COMPLETE existing summary verified; 6 figures exported; Uniform6000 missing; full fading remains preliminary",flush=True)


def uniform_candidates(data,manifest):
    config=unconstrained_config();candidates=[]
    roster=read_csv(ROOT/data["settings"]["source_roster"])
    for row in roster:
        if row["family"]!="Uniform":continue
        path=ROOT/row["source_path"]
        if saved.digest(path)!=row["source_payload_sha256"]:raise ValueError("Uniform source payload changed")
        payload=saved.read_json(path)
        payload["_provenance"]=verify_source_payload(payload,source_settings(config));payload["_path"]=row["source_path"]
        candidate=candidate_from_payload(config,{payload["ensemble_hash"]:payload},"Uniform",0.,float(row["V_A"]))
        saved.authenticate(candidate,manifest["protected_hashes"],config)
        if candidate["ensemble_hash"]!=row["ensemble_hash"]:raise ValueError("Uniform ensemble differs from cached source")
        candidates.append(candidate)
    if len(candidates)!=30:raise ValueError("Validated 30-source Uniform bank absent")
    return candidates,config


def uniform(smoke=False):
    import torch
    torch.set_num_threads(1)
    if not (OUT/"preparation_receipt.json").exists():raise ValueError("Audit and original figure preparation required")
    manifest=saved.read_json(OUT/"startup_manifest.json");saved.verify_protected(manifest)
    data=load_existing();candidates,config=uniform_candidates(data,manifest)
    directory=OUT/("uniform_smoke" if smoke else "uniform");directory.mkdir(exist_ok=True)
    if (directory/"receipt.json").exists():raise ValueError("Completed Uniform benchmark exists; preserve outputs")
    if not smoke:
        if saved.read_json(OUT/"uniform_smoke/receipt.json")["status"]!="CURRENTLY_VERIFIED_PASS":raise ValueError("Uniform smoke required")
        tests=saved.read_json(OUT/"test_receipt.json")
        if tests["status"]!="CURRENTLY_VERIFIED_PASS":raise ValueError("Current original and package tests required")
    states=data["states"]
    if smoke:
        candidates=[c for c in candidates if c["V_A"] in (.5,1.,1.25)]
        states=[s for s in states if s["position_index"] in (0,9,44,90,99)]
    identity=dict(data["inputs"]["scientific_identity"],source_family="Uniform",adapter_sha256=saved.digest(Path(__file__)))
    cache=ExactStateCache(directory/"objective_cache.jsonl",identity,manifest["protected_hashes"],config)
    rows,winners=[],[]
    for state in states:
        local=[]
        for candidate in candidates:
            key,result=cache.evaluate(candidate,state)
            row=dict(result,objective_key=key,position_index=state["position_index"],blocked=state["blocked"])
            local.append(row);rows.append(row)
        winners.append(max(local,key=lambda r:r["SKR"]))
        if state["blocked"]:
            print("UNIFORM_POSITION",state["position_index"],"/99","rows",len(rows),flush=True)
    saved.write_csv(directory/"all_candidate_evaluations.csv",rows)
    saved.write_csv(directory/"optimized_state_sources.csv",winners)
    if not smoke:
        table=reconstructed_winners(winners)
        summary,series,*_=scenario(data["settings"],validate_settings(data["settings"]),table)
        verify_series(data["settings"],series,summary)
        saved.write_csv(directory/"summary.csv",summary);saved.write_csv(directory/"scheme_time_series.csv",series)
        saved.write_csv(directory/"source_roster.csv",[{k:c[k] for k in ("nu_raw","V_A","C","w","ensemble_hash","source_cache_key","source_path")} for c in candidates])
    for r in rows:
        if abs(r["SKR"]-(.95*r["I_AB"]-r["chi_BE"]))>1e-14 or r["nu_raw"]!=0. or r["numerical_repairs"]:
            raise ValueError("Uniform consistency failed")
    receipt=dict(status="CURRENTLY_VERIFIED_PASS",states=len(states),sources=len(candidates),
        candidate_evaluations=len(rows),new_evaluations=cache.new_evaluations,cache_hits=cache.hits,
        new_Cw=False,MB_evaluations_repeated=0,interpolation=False,
        scientific_status="PRELIMINARY_EFFECTIVE_GAUSSIAN_IGNORING_FADING_VARIANCE",
        protected_changes=saved.verify_protected(manifest),adapter_sha256=saved.digest(Path(__file__)),
        source_snapshot_sha256=saved.digest(OUT/"startup_manifest.json"),
        output_sha256={p.name:saved.digest(p) for p in directory.iterdir() if p.is_file()})
    saved.save(directory/"receipt.json",receipt,exclusive=True)
    print("UNIFORM_COMPLETE",receipt["status"],len(rows),flush=True)


def finish():
    from scripts.write_mobility_numerical_results import finish_package
    finish_package(OUT,load_existing())


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase",choices=("prepare","uniform-smoke","uniform","finish"))
    args=parser.parse_args()
    if args.phase=="prepare":prepare()
    elif args.phase=="uniform-smoke":uniform(True)
    elif args.phase=="uniform":uniform()
    else:finish()
