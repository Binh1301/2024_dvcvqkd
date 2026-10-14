"""Scoped multistart AO; preserved numerical kernels and isolated exact sources."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "results/ao_effective_channel_no_fading_noise_reference"
CONFIG = ROOT / "configs/ao_effective_channel_no_fading_noise_reference.json"
CATALOG = ROOT / "results/exact_source_moments_catalog_20261012/all_182_MB_exact_source_moments.csv"
ATTACHMENT = Path("C:/Users/HP/.codex/attachments/3a965971-484e-48de-b337-1292308b7fc9/Pasted text.txt")
STATE = ["docs/EVIDENCE.md", "docs/DECISION_LOG.md", "docs/PROJECT_STATE.md",
         "docs/NEXT_ACTIONS.md", ".agent/SESSION_HANDOFF.md"]
NEW = ["scripts/run_ao_effective_channel_no_fading_noise_reference.py",
       "configs/ao_effective_channel_no_fading_noise_reference.json",
       "tests/test_ao_effective_channel_no_fading_noise_reference.py",
       "docs/AO_EFFECTIVE_CHANNEL_NO_FADING_NOISE_REPORT_VI.md"]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def hash_json(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                    allow_nan=False).encode()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def config_identity(value):
    # Infinite beam curvature is a physical input, not a nonfinite result.
    if isinstance(value, float) and math.isinf(value):
        return {"float_hex": value.hex()}
    if isinstance(value, dict):
        return {k:config_identity(v) for k,v in value.items()}
    if isinstance(value, (list,tuple)):
        return [config_identity(v) for v in value]
    return value


def save(path, value, *, exclusive=False):
    path = Path(path)
    if exclusive:
        with path.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write("\n")
    else:
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2,
                                       allow_nan=False) + "\n", encoding="utf-8", newline="\n")
        temporary.replace(path)


def write_csv(path, rows):
    fields = list(dict.fromkeys(k for row in rows for k in row)) or ["status"]
    with Path(path).open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows({k: json.dumps(v) if isinstance(v, (dict, list)) else v
                          for k, v in row.items()} for row in rows)


def verify_protected(manifest):
    changed = [name for name, expected in manifest["protected_hashes"].items()
               if not (ROOT / name).is_file() or digest(ROOT / name) != expected]
    if changed:
        raise ValueError("Protected files changed: " + repr(changed))
    return changed


def authenticate(candidate, authorized_hashes, config):
    """Same exact source checks, admitting only this run's verified new receipts."""
    from scripts.exact_cache_provenance import source_settings, verify_source_payload
    from scripts.run_exact_mb_test2 import ensemble_hash
    from src.cvqkd.covariance import quadrature_symmetry_diagnostics
    path = ROOT / candidate["source_path"]
    if authorized_hashes.get(candidate["source_path"]) != digest(path):
        raise ValueError("Source bytes absent from protected snapshot or new-source receipt")
    payload = read_json(path)
    verified = verify_source_payload(payload, source_settings(config))
    if (candidate["source_cache_key"] != verified["historical_cache_key"]
            or float(candidate["nu_raw"]).hex() != payload["nu_mb_raw_hex"]
            or float(candidate["V_A"]).hex() != payload["V_A_hex"]
            or candidate["ensemble_hash"] != payload["ensemble_hash"]
            or candidate["C"] != payload["C"] or candidate["w"] != payload["w"]
            or candidate["w"] < 0):
        raise ValueError("Exact candidate/source identity mismatch")
    ensemble = candidate["ensemble"]
    ensemble.validate(tolerance=1e-12)
    if ensemble_hash(ensemble) != candidate["ensemble_hash"]:
        raise ValueError("Source and transmitted ensemble differ")
    if not quadrature_symmetry_diagnostics(ensemble).standard_form_supported:
        raise ValueError("Centered C4 symmetry required")
    if not math.isclose(float(ensemble.computed_va()[0]), candidate["V_A"], abs_tol=1e-12, rel_tol=1e-12):
        raise ValueError("VA != 2 weighted mean photon number")
    return ensemble


def evaluate_authenticated(candidate, moments, config, authorized_hashes):
    """Extend source authentication only; import the existing scientific kernels."""
    import torch
    from scripts._common import holevo_numerical_kwargs
    from src.effective_channel_no_fading_noise import effective_channel
    from src.manuscript_literal_3moments import z_star
    from src.cvqkd.holevo import _holevo_from_source_moments
    from src.cvqkd.mutual_information import deterministic_mutual_information
    ensemble = authenticate(candidate, authorized_hashes, config)
    mapping = effective_channel(moments, candidate["V_A"])
    t = torch.tensor([mapping["T_eff"]], dtype=torch.float64)
    epsilon = torch.tensor([mapping["xi_eff"]], dtype=torch.float64)
    numerical = holevo_numerical_kwargs(config)
    result = _holevo_from_source_moments(ensemble, t, epsilon,
        coherent_correlation=torch.tensor([candidate["C"]], dtype=torch.float64),
        w_raw=torch.tensor([candidate["w"]], dtype=torch.float64), tau=None,
        tau_trace=ensemble.probabilities.sum(dim=-1), require_supported_symmetry=True,
        symmetry_tolerance=numerical["symmetry_tolerance"],
        physicality_tolerance=numerical["physicality_tolerance"],
        maximize_full_interval=False, diagnostics={"backend": "effective_channel_no_fading_noise"})
    if result.diagnostics["mode"] != "zstar" or result.diagnostics["numerical_repairs"]:
        raise ValueError("Different Holevo target or numerical repair rejected")
    covariance = result.covariance
    eigenvalues = [float(x[0]) for x in (covariance.lambda1, covariance.lambda2, covariance.lambda3)]
    if min(eigenvalues) < 1:
        raise ValueError("Nonphysical symplectic eigenvalue; no clipping")
    z = float(result.z[0])
    formula = z_star(dict(eta_f=mapping["T_eff"], eta_f_xi_f=mapping["N_eff"]), candidate["C"], candidate["w"])
    if abs(z-formula) > 1e-13 or abs(float(covariance.matrix[0, 2, 2])-mapping["b"]) > 1e-12:
        raise ValueError("Covariance/mapping/Equation (20) mismatch")
    orders = []
    for order in (8, 16, 32):
        i_ab = float(deterministic_mutual_information(ensemble, t, epsilon,
                     quadrature_order=order, implementation="product")[0])
        orders.append(dict(order=order, I_AB=i_ab, SKR=.95*i_ab-float(result.chi_be[0])))
    if abs(orders[-1]["I_AB"]-orders[-2]["I_AB"]) > 1e-8:
        raise ValueError("GH16/32 refinement unresolved")
    if not 0 <= i_ab <= float((-torch.special.xlogy(ensemble.probabilities,
                       ensemble.probabilities).sum()/math.log(2))):
        raise ValueError("MI outside discrete entropy domain")
    row = dict(mapping, nu_raw=candidate["nu_raw"], V_A=candidate["V_A"],
        C=candidate["C"], w=candidate["w"], Z_star=z,
        Z_signal=2*math.sqrt(mapping["T_eff"])*candidate["C"],
        Z_penalty=math.sqrt(2*mapping["N_eff"]*candidate["w"]),
        Gamma_AB=covariance.matrix[0].tolist(), lambda_1=eigenvalues[0],
        lambda_2=eigenvalues[1], lambda_3=eigenvalues[2], I_AB=i_ab,
        beta_I_AB=.95*i_ab, chi_BE=float(result.chi_be[0]), SKR=orders[-1]["SKR"],
        source_cache_key=candidate["source_cache_key"], source_path=candidate["source_path"],
        source_payload_sha256=digest(ROOT/candidate["source_path"]),
        ensemble_hash=candidate["ensemble_hash"], source_moment_route=candidate["source_moment_route"],
        MI_integration_order=32, MI_orders=orders, numerical_repairs=[],
        objective="effective_gaussian_Zstar_diagnostic_SKR", Holevo_target="chi_BE_at_direct_Z_star",
        certified_fading_security_lower_bound=False)
    if not all(math.isfinite(row[key]) for key in ("C", "w", "I_AB", "chi_BE", "SKR")):
        raise ValueError("Nonfinite exact candidate metric")
    return row


class Objective:
    def __init__(self):
        from scripts.run_theta10_D55_unconstrained_three_scheme import unconstrained_config
        from scripts.exact_cache_provenance import source_settings, verify_source_payload
        self.settings = read_json(CONFIG)
        self.config = unconstrained_config()
        self.baseline = read_json(OUT/"startup_manifest.json")
        self.hashes = dict(self.baseline["protected_hashes"])
        self.payloads, self.rows, self.points, self.requests, self.attempts = {}, {}, set(), [], []
        self.allow_new = False
        self.used_source_seconds = 0.
        self.group = "MB"
        self.moments = read_json(OUT/"reference_regression.json")["record"]
        paths = {ROOT/r["source_path"] for r in csv.DictReader(CATALOG.open(encoding="utf-8"))}
        paths.update((ROOT/"results/exact_mb_test2/exact_source_cache").glob("*.json"))
        paths.update((OUT/"exact_source_cache").glob("*.json"))
        for path in sorted(paths):
            payload = read_json(path)
            payload["_provenance"] = verify_source_payload(payload, source_settings(self.config))
            payload["_path"] = path.relative_to(ROOT).as_posix()
            self.payloads[payload["ensemble_hash"]] = payload
            self.points.add((float.fromhex(payload["nu_mb_raw_hex"]), float.fromhex(payload["V_A_hex"])))
        identity = dict(mode=self.settings["scientific_model"], objective=self.settings["objective"],
            config=self.settings, physical_moments=self.moments, source_settings=source_settings(self.config),
            numerical_config=config_identity(self.config), regression_sha256=digest(OUT/"reference_regression.json"),
            implementations={n:digest(ROOT/n) for n in NEW[:3] if (ROOT/n).is_file()},
            inherited_scientific_implementations=read_json(OUT/"reference_regression.json")["identity"]["implementations"])
        self.context_hash = hash_json(identity)
        self.identity = identity

    def catalog_values(self, variable, fixed):
        return sorted({v if variable == "V_A" else n for n, v in self.points
                       if (n if variable == "V_A" else v).hex() == float(fixed).hex()})

    def checkpoint(self):
        save(OUT/"checkpoint.json", dict(status="RUNNING", scientific_context_hash=self.context_hash,
            exact_objective_rows=len(self.rows), source_attempts=self.attempts,
            used_source_seconds=self.used_source_seconds, requests=self.requests))
        save(OUT/"objective_evaluations.json", list(self.rows.values()))

    def generate(self, nu, va):
        from scripts.run_theta10_D55_alt_opt_closure_continuation import supervised_probe
        settings = self.settings
        remaining = settings["source_wall_budget_seconds"]-self.used_source_seconds
        if self.group != "Uniform":
            remaining -= settings["uniform_source_reserve_seconds"]
        if remaining < 15 or len(self.attempts) >= settings["max_new_source_attempts"]:
            return False
        deadline = min(settings["per_source_deadline_seconds"], remaining)
        number = len(self.attempts)+1
        record = dict(attempt=number, nu_raw=nu, V_A=va, group=self.group,
            scientific_context_hash=self.context_hash, deadline_seconds=deadline,
            status="RUNNING", started_utc=datetime.now(timezone.utc).isoformat())
        self.attempts.append(record)
        self.checkpoint()
        print(f"SOURCE {number} {self.group} nu={nu:.17g} VA={va:.17g}; deadline={deadline:.1f}s", flush=True)
        with (OUT/f"source_attempt_{number}.log").open("w", encoding="utf-8") as log:
            receipt = supervised_probe([sys.executable, "-B", str(Path(__file__).resolve()),
                        "--source-worker", str(nu), str(va)], deadline, log)
        self.used_source_seconds += receipt["elapsed_seconds"]
        record.update(receipt)
        result_path = OUT/f"source_result_{float(nu).hex()}_{float(va).hex()}.json"
        if receipt["returncode"] == 0 and not receipt["deadline_exceeded"] and result_path.is_file():
            result = read_json(result_path)
            payload = read_json(ROOT/result["source_path"])
            from scripts.exact_cache_provenance import source_settings, verify_source_payload
            payload["_provenance"] = verify_source_payload(payload, source_settings(self.config))
            payload["_path"] = result["source_path"]
            if digest(ROOT/result["source_path"]) != result["source_sha256"]:
                raise ValueError("Fresh source receipt bytes mismatch")
            self.hashes[result["source_path"]] = result["source_sha256"]
            self.payloads[payload["ensemble_hash"]] = payload
            self.points.add((nu, va))
            record.update(status="COMPLETED_EXACT", **result)
        else:
            record.update(status="TIMEOUT" if receipt["deadline_exceeded"] else "SOURCE_FAILURE",
                result_available=False)
        self.checkpoint()
        print("SOURCE completed:", record["status"], "wall", receipt["elapsed_seconds"], flush=True)
        return record["status"] == "COMPLETED_EXACT"

    def __call__(self, nu, va):
        from scripts.run_theta10_D55_alt_opt import ExactSourceUnavailable, ExactCandidateFailure
        from scripts.run_theta10_D55_unconstrained_three_scheme import candidate_from_payload
        nu, va = float(nu), float(va)
        if not math.isfinite(nu) or not math.isfinite(va) or nu < 0 or va <= 0:
            raise ValueError("nu>=0, VA>0 required")
        key = (nu.hex(), va.hex())
        if key in self.rows:
            return self.rows[key]
        candidate = candidate_from_payload(self.config, self.payloads, "Uniform" if nu == 0 else "MB", nu, va)
        failed_before = any(x["nu_raw"] == nu and x["V_A"] == va for x in self.attempts)
        if candidate is None and self.allow_new and not failed_before:
            if self.generate(nu, va):
                candidate = candidate_from_payload(self.config, self.payloads, "Uniform" if nu == 0 else "MB", nu, va)
        if candidate is None:
            self.requests.append(dict(nu_raw=nu, V_A=va, group=self.group, status="EXACT_SOURCE_MISSING",
                scientific_context_hash=self.context_hash, reason="Source unavailable within controlled budget"))
            self.checkpoint()
            raise ExactSourceUnavailable(f"Missing exact source {nu:.17g}, {va:.17g}; no interpolation")
        try:
            row = evaluate_authenticated(candidate, self.moments, self.config, self.hashes)
        except Exception as error:
            self.requests.append(dict(nu_raw=nu, V_A=va, status="NUMERICAL_FAILURE", error=str(error)))
            self.checkpoint()
            raise ExactCandidateFailure(str(error)) from error
        row.update(scientific_context_hash=self.context_hash, distance_km=self.settings["distance_km"],
                   source_origin="NEW_EXACT" if OUT in (ROOT/candidate["source_path"]).parents else "PROTECTED_EXISTING")
        self.rows[key] = row
        self.points.add((nu, va))
        self.checkpoint()
        return row


def prepare():
    from scripts.run_effective_channel_no_fading_noise import evaluate_reference
    from scripts.run_theta10_D55_unconstrained_three_scheme import candidate_from_payload
    from src.effective_channel_no_fading_noise import evaluate_candidate
    import torch
    torch.set_num_threads(1)
    OUT.mkdir(exist_ok=True)
    if (OUT/"catalog_preparation.json").exists() or (OUT/"execution_started.json").exists():
        raise ValueError("Preparation/execution already complete; never overwrite a prior experiment")
    (OUT/"exact_source_cache").mkdir(exist_ok=True)
    paths = [p for folder in ("src", "scripts", "configs", "tests", "results", "docs", ".agent")
             for p in (ROOT/folder).rglob("*") if p.is_file() and "__pycache__" not in p.parts
             and OUT not in p.parents and p.relative_to(ROOT).as_posix() not in STATE+NEW]
    manifest = dict(captured_utc=datetime.now(timezone.utc).isoformat(), attachment_sha256=digest(ATTACHMENT),
        authority="Explicit current user request RUN MULTISTART ALTERNATING OPTIMIZATION",
        branch=subprocess.check_output(["git","branch","--show-current"],cwd=ROOT,text=True).strip(),
        head=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),
        git_status=subprocess.check_output(["git","status","--short"],cwd=ROOT,text=True),
        git_diff=subprocess.check_output(["git","diff"],cwd=ROOT).decode("utf-8"),
        frozen_sha256=digest(ROOT/"docs/FINAL_MODEL_SPEC.md"),
        frozen_historical_expected="561fecc97cdf9967034ffd6865c1605804b624b98f47a091e47f17e520a2a7b1",
        protected_hashes={p.relative_to(ROOT).as_posix():digest(p) for p in sorted(paths)},
        state_before={n:(ROOT/n).read_text(encoding="utf-8") for n in STATE}, config=read_json(CONFIG))
    if (OUT/"startup_manifest.json").exists():
        manifest=read_json(OUT/"startup_manifest.json")
        verify_protected(manifest)
        save(OUT/"preparation_recovery.json",dict(reason="Encode infinite beam curvature losslessly in config identity",
             driver_sha256=digest(Path(__file__)),same_protected_inputs=True),exclusive=True)
    else:
        save(OUT/"startup_manifest.json", manifest, exclusive=True)
    reference = read_json(OUT/"reference_regression.json") if (OUT/"reference_regression.json").exists() else evaluate_reference(read_json(ROOT/"configs/effective_channel_no_fading_noise.json"))
    expected = dict(T_eff=.16092029098192165,a=6.5,b=1.8880547178128329,
        Z_star=2.576345544379474,I_AB=.527940610385,chi_BE=.442913429645,SKR=.058630150221)
    residuals = {k: reference["record"][k]-v for k,v in expected.items()}
    if any(abs(v) > 5e-12 for v in residuals.values()):
        save(OUT/"regression_failed.json", residuals)
        raise ValueError("Mandatory scientific regression failed")
    reference["mandatory_regression"] = dict(status="CURRENTLY_VERIFIED_PASS", tolerance=5e-12,
        justification="Rounded user references (12 decimals); preserved source and deterministic GH32 evaluator", residuals=residuals)
    if not (OUT/"reference_regression.json").exists():
        save(OUT/"reference_regression.json", reference, exclusive=True)
    objective = Objective()
    save(OUT/"objective_identity.json", dict(identity=objective.identity, sha256=objective.context_hash), exclusive=True)
    catalog_keys = {(float(r["nu_raw"]).hex(),float(r["VA"]).hex())
                    for r in csv.DictReader(CATALOG.open(encoding="utf-8"))}
    failures = []
    for nu, va in sorted(objective.points):
        try:
            objective(nu, va)
        except Exception as error:
            failures.append(dict(nu_raw=nu, V_A=va, error=str(error)))
    rows = list(objective.rows.values())
    mb = sorted([r for r in rows if (r["nu_raw"].hex(),r["V_A"].hex()) in catalog_keys], key=lambda r:r["SKR"], reverse=True)
    uniform = sorted([r for r in rows if r["nu_raw"]==0],key=lambda r:r["SKR"], reverse=True)
    if len(mb) != 182:
        raise ValueError(f"182-pair catalog incomplete: {len(mb)} compatible evaluated rows; {failures}")
    starts = [dict(start_id=f"requested_{i+1}",nu_raw=n,V_A=v,origin="USER_REQUESTED")
              for i,(n,v) in enumerate(objective.settings["starts"])]
    for row in mb:
        if len(starts) >= len(objective.settings["starts"])+objective.settings["additional_diverse_starts"]:
            break
        if any(row["nu_raw"]==s["nu_raw"] and row["V_A"]==s["V_A"] for s in starts):
            continue
        if len(starts)>5 and any(abs(row["nu_raw"]-s["nu_raw"])<.01 and abs(row["V_A"]-s["V_A"])<.5 for s in starts[5:]):
            continue
        starts.append(dict(start_id=f"catalog_{len(starts)-4}",nu_raw=row["nu_raw"],V_A=row["V_A"],origin="RANKED_DIVERSE_EXACT"))
    for start in starts:
        start["initial_SKR"] = objective(start["nu_raw"],start["V_A"])["SKR"]
    original_candidate = candidate_from_payload(objective.config,objective.payloads,"MB",.165,5.5)
    old = evaluate_candidate(original_candidate,objective.moments,objective.config)
    adapter = objective(.165,5.5)
    agreement = {k:adapter[k]-old[k] for k in expected}
    if any(v!=0 for v in agreement.values()):
        raise ValueError("AO authentication adapter changed the scientific evaluator")
    summary = dict(status="CURRENTLY_VERIFIED_PASS", catalog_rows=len(mb),uniform_rows=len(uniform),
        other_existing_rows=len(rows)-len(mb)-len(uniform),failures=failures,
        best_catalog_MB=mb[0],best_existing_Uniform=uniform[0],starts=starts,
        source_adapter_reference_residuals=agreement,protected_changes=verify_protected(manifest),
        scientific_context_hash=objective.context_hash)
    save(OUT/"catalog_preparation.json", summary, exclusive=True)
    write_csv(OUT/"catalog_MB_ranking.csv",mb)
    write_csv(OUT/"catalog_Uniform_ranking.csv",uniform)
    write_csv(OUT/"start_points.csv",starts)
    print("REFERENCE_REGRESSION_PASS; catalog",len(mb),"Uniform",len(uniform),flush=True)
    print("BEST_CATALOG",mb[0]["nu_raw"],mb[0]["V_A"],mb[0]["SKR"],flush=True)
    print("STARTS",json.dumps(starts),flush=True)


def source_worker(nu, va):
    import torch
    from scripts.run_exact_mb_test2 import ExactMBEvaluator
    from scripts.run_theta10_D55_unconstrained_three_scheme import unconstrained_config,make_ensemble
    from src.cvqkd.gram_moments import c4_gram_source_moments
    torch.set_num_threads(1)
    config = unconstrained_config()
    ensemble = make_ensemble(config,"Uniform" if nu==0 else "MB",nu,va)
    diagnostics = []
    def observed_source(*args, **kwargs):
        result = c4_gram_source_moments(*args, **kwargs)
        diagnostics.extend(result.diagnostics)
        return result
    evaluator = ExactMBEvaluator(config,{"T_eff":0.,"epsilon_base":.0186,"c_phi":0.},OUT,
        source_cache_dir=OUT/"exact_source_cache",allow_legacy_exact_import=False,
        source_evaluator=observed_source,crn_seeds=(),mi_samples=1)
    source = evaluator.source_moments(ensemble,nu,va)
    path = OUT/"exact_source_cache"/(source["cache_key"]+".json")
    save(OUT/f"source_result_{nu.hex()}_{va.hex()}.json",dict(source_path=path.relative_to(ROOT).as_posix(),
        source_sha256=digest(path),cache_key=source["cache_key"],C=source["C"],w=source["w"],diagnostics=diagnostics),exclusive=True)


def search_coordinate(objective, variable, fixed, current):
    from scripts.run_theta10_D55_alt_opt import adaptive_maximize_1d, ExactSourceUnavailable, ExactCandidateFailure
    values = objective.catalog_values(variable,fixed)
    current_value = current["V_A"] if variable=="V_A" else current["nu_raw"]
    values.append(current_value)
    search = adaptive_maximize_1d(variable=variable,fixed=fixed,values=values,objective=objective,
               k_tolerance=objective.settings["SKR_tolerance"],parameter_tolerance=objective.settings["parameter_tolerance"])
    # The legacy helper excludes zero; explicitly check the allowed Uniform endpoint.
    if variable=="nu_raw":
        try:
            zero = objective(0.,fixed)
            search["history"].append(dict(value=0.,status="EXACT_EVALUATED",K=zero["SKR"],nu_raw=0.,V_A=fixed))
            if search.get("best") is None or zero["SKR"]>search["best"]["SKR"]:
                search["best"] = zero
                search["status"] = "ZERO_ENDPOINT_SELECTED_LOCAL_CLOSURE_UNRESOLVED"
            search["zero_endpoint_status"] = "EXACT_CHECKED"
        except (ExactSourceUnavailable,ExactCandidateFailure) as error:
            search["zero_endpoint_status"] = "UNRESOLVED"
            search["source_missing"].append(dict(value=0.,error=str(error)))
    # Record every coarse local maximum; no unimodality assumption.
    successful = sorted([x for x in search["history"] if x["status"]=="EXACT_EVALUATED"],key=lambda x:x["value"])
    search["coarse_local_maxima"] = [x for i,x in enumerate(successful)
        if (i==0 or x["K"]>=successful[i-1]["K"]) and (i==len(successful)-1 or x["K"]>=successful[i+1]["K"])]
    return search


def run_start(objective,start,epoch):
    from scripts.run_theta10_D55_alt_opt import coordinate_search_complete
    current = objective(start["nu_raw"],start["V_A"])
    initial = current
    history=[]
    terminal="BEST_EXACT_CANDIDATE"
    for iteration in range(1,objective.settings["max_ao_iterations"]+1):
        before = current
        p1=search_coordinate(objective,"V_A",before["nu_raw"],before)
        after_p1=p1.get("best") or before
        rejected=[]
        if after_p1["SKR"] < before["SKR"]:
            rejected.append(dict(stage="P1",candidate=after_p1,reason="DECREASE_REJECTED"))
            after_p1=before
        p2=search_coordinate(objective,"nu_raw",after_p1["V_A"],after_p1)
        after_p2=p2.get("best") or after_p1
        if after_p2["SKR"] < after_p1["SKR"]:
            rejected.append(dict(stage="P2",candidate=after_p2,reason="DECREASE_REJECTED"))
            after_p2=after_p1
        delta=after_p2["SKR"]-before["SKR"]
        displacement=max(abs(after_p2["nu_raw"]-before["nu_raw"]),abs(after_p2["V_A"]-before["V_A"]))
        closed=all(coordinate_search_complete(s) for s in (p1,p2))
        if delta<=objective.settings["SKR_tolerance"] and displacement<=objective.settings["parameter_tolerance"]:
            terminal="CONVERGED_COORDINATE_LOCAL" if closed and p2.get("zero_endpoint_status")=="EXACT_CHECKED" else "BEST_EXACT_CANDIDATE"
        row=dict(start_id=start["start_id"],epoch=epoch,iteration=iteration,
            nu_before=before["nu_raw"],VA_before=before["V_A"],K_before=before["SKR"],
            VA_after_P1=after_p1["V_A"],K_after_P1=after_p1["SKR"],
            nu_after_P2=after_p2["nu_raw"],K_after_P2=after_p2["SKR"],delta_K=delta,
            parameter_change=displacement,exact_source_cache_key=after_p2["source_cache_key"],
            MI_integration_order=after_p2["MI_integration_order"],convergence_status=terminal,
            rejected_steps=rejected,P1=p1,P2=p2)
        history.append(row)
        save(OUT/f"trajectory_{start['start_id']}_epoch{epoch}.json",dict(start=start,initial=initial,iterations=history,final=after_p2,status=terminal))
        current=after_p2
        print(f"AO {start['start_id']} epoch={epoch} r={iteration}: P1 VA={after_p1['V_A']:.17g} K={after_p1['SKR']:.14g}; P2 nu={after_p2['nu_raw']:.17g} K={after_p2['SKR']:.14g}; delta={delta:.3g}",flush=True)
        if delta<=objective.settings["SKR_tolerance"] and displacement<=objective.settings["parameter_tolerance"]:
            break
    return dict(start=start,initial=initial,iterations=history,final=current,status=terminal)


def figures(runs):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from scripts.run_theta10_D55_alt_opt import save_figure
    for field,initial_field,filename,label in [("K_after_P2","SKR","SKR_vs_AO_iteration","Diagnostic SKR (bits/use)"),
        ("VA_after_P1","V_A","VA_vs_AO_iteration",r"$V_A$ (SNU)"),
        ("nu_after_P2","nu_raw","nu_vs_AO_iteration",r"$\nu_{\rm raw}$")]:
        fig,ax=plt.subplots(figsize=(7,4.5))
        for run in runs:
            values=[run["initial"][initial_field]]+[r[field] for r in run["iterations"]]
            ax.plot(range(len(values)),values,marker="o",label=run["start"]["start_id"])
        ax.set_xlabel("AO iteration"); ax.set_ylabel(label); ax.grid(alpha=.25)
        ax.legend(frameon=False,fontsize=8)
        save_figure(OUT/filename,fig)


def execute():
    import torch
    from scripts.run_theta10_D55_unconstrained_three_scheme import candidate_from_payload
    torch.set_num_threads(1)
    baseline=read_json(OUT/"startup_manifest.json")
    verify_protected(baseline)
    prepared=read_json(OUT/"catalog_preparation.json")
    objective=Objective()
    if objective.context_hash!=prepared["scientific_context_hash"]:
        raise ValueError("Objective changed since reference/catalog preparation")
    old_rows=read_json(OUT/"objective_evaluations.json")
    for r in old_rows:
        if r["scientific_context_hash"]!=objective.context_hash:
            raise ValueError("Objective cache scientific context mismatch")
        objective.rows[(r["nu_raw"].hex(),r["V_A"].hex())]=r
    save(OUT/"execution_started.json",dict(started_utc=datetime.now(timezone.utc).isoformat(),
        scientific_context_hash=objective.context_hash,config=objective.settings),exclusive=True)
    started=time.monotonic()
    # All starts execute catalog-assisted P1/P2 before prioritizing expensive new sources.
    runs=[run_start(objective,s,1) for s in prepared["starts"]]
    winner=max(runs,key=lambda r:r["final"]["SKR"])
    objective.allow_new=True
    refined=run_start(objective,dict(start_id="best_MB_refinement",nu_raw=winner["final"]["nu_raw"],
        V_A=winner["final"]["V_A"],origin="BEST_MULTISTART_TERMINAL"),2)
    runs.append(refined)
    objective.group="Uniform"
    uniform_initial=prepared["best_existing_Uniform"]
    uniform=search_coordinate(objective,"V_A",0.,uniform_initial)
    uniform_best=uniform.get("best") or uniform_initial
    objective.allow_new=False
    # Recheck every start against successful overlay discoveries; retained first histories.
    if any(a["status"]=="COMPLETED_EXACT" for a in objective.attempts):
        runs += [run_start(objective,s,3) for s in prepared["starts"]]
    ao_best=max((r["final"] for r in runs),key=lambda r:r["SKR"])
    competitors=sorted([r for r in objective.rows.values() if r["nu_raw"]>0],key=lambda r:r["SKR"],reverse=True)[:10]
    accuracy=[]
    for row in competitors+[uniform_best]:
        candidate=candidate_from_payload(objective.config,objective.payloads,"Uniform" if row["nu_raw"]==0 else "MB",row["nu_raw"],row["V_A"])
        fresh=evaluate_authenticated(candidate,objective.moments,objective.config,objective.hashes)
        fresh.update(scientific_context_hash=objective.context_hash)
        accuracy.append(fresh)
    best_checked=max(accuracy[:-1],key=lambda r:r["SKR"])
    rank_stable=best_checked["nu_raw"]==ao_best["nu_raw"] and best_checked["V_A"]==ao_best["V_A"]
    best_neighbors=[r for r in accuracy[:-1] if (r["nu_raw"],r["V_A"])!=(ao_best["nu_raw"],ao_best["V_A"])]
    gh_changes=[abs(r["MI_orders"][2]["SKR"]-r["MI_orders"][0]["SKR"]) for r in accuracy]
    numerical_failures=[r for r in objective.requests if r["status"]=="NUMERICAL_FAILURE"]
    status="AO_RESOURCE_LIMITED" if any(a["status"]=="TIMEOUT" for a in objective.attempts) else "AO_BEST_EXACT_CANDIDATE"
    if not rank_stable or numerical_failures:
        status="AO_NUMERICAL_UNRESOLVED"
    all_iterations=[r for run in runs for r in run["iterations"]]
    initial=objective(.165,5.5)
    comparison=[dict(scheme=name,**row) for name,row in [("Initial MB",initial),
        ("Best catalog MB",prepared["best_catalog_MB"]),("Multistart AO MB",ao_best),("Optimized Uniform",uniform_best)]]
    result=dict(status=status,scientific_model=objective.settings["scientific_model"],objective=objective.settings["objective"],
        scientific_context_hash=objective.context_hash,config=objective.settings,initial=initial,
        best_catalog_MB=prepared["best_catalog_MB"],best_AO_MB=ao_best,Uniform=uniform_best,
        uniform_search=uniform,runs=runs,source_attempts=objective.attempts,
        unique_exact_objectives=len(objective.rows),new_sources=sum(a["status"]=="COMPLETED_EXACT" for a in objective.attempts),
        missing_source_requests=objective.requests,used_source_wall_seconds=objective.used_source_seconds,
        optimization_wall_seconds=time.monotonic()-started,
        delta_K=ao_best["SKR"]-initial["SKR"],gain_percent=100*(ao_best["SKR"]-initial["SKR"])/abs(initial["SKR"]),
        shaping_gain_absolute=ao_best["SKR"]-uniform_best["SKR"],
        shaping_gain_percent=100*(ao_best["SKR"]-uniform_best["SKR"])/abs(uniform_best["SKR"]),
        accuracy_checks=accuracy,winner_stable_under_GH_refinement=rank_stable,
        largest_GH8_32_SKR_difference=max(gh_changes),
        best_second_gap=None if not best_neighbors else ao_best["SKR"]-best_neighbors[0]["SKR"],
        source_total_error_bound="NOT_ESTABLISHED; AP last-two-row stability is not a rigorous error enclosure",
        continuous_global_optimum=False,certified_fading_security_lower_bound=False,
        protected_changes=verify_protected(baseline),protected_files=len(baseline["protected_hashes"]))
    save(OUT/"optimization_result.json",result,exclusive=True)
    save(OUT/"checkpoint.json",dict(status=status,scientific_context_hash=objective.context_hash,
        best_exact=ao_best,source_attempts=objective.attempts,used_source_wall_seconds=objective.used_source_seconds))
    write_csv(OUT/"comparison.csv",comparison)
    write_csv(OUT/"AO_iteration_history.csv",all_iterations)
    write_csv(OUT/"source_attempts.csv",objective.attempts)
    write_csv(OUT/"missing_exact_source_requests.csv",objective.requests)
    figures(runs)
    print("FINAL",status,"best",ao_best["nu_raw"],ao_best["V_A"],ao_best["SKR"],flush=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare",action="store_true")
    parser.add_argument("--source-worker",nargs=2,type=float)
    args=parser.parse_args()
    if args.source_worker:
        source_worker(*args.source_worker)
    elif args.prepare:
        prepare()
    else:
        execute()
