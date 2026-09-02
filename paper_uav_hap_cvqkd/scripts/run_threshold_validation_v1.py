"""Run only the frozen finite candidate-threshold validation."""
from __future__ import annotations
import argparse, copy, hashlib, json, time
from pathlib import Path
import torch
from _common import ROOT, load_yaml
from _numerical_validation import ensemble_sha256, representative_ensembles
from freeze_independent_confirmation_roster import stress_ensemble
from oracle_independent_confirmation_gram import run as run_oracle
from certify_production_gram import _observable_comparison, _result_metrics, _source_diagnostics
from src.cvqkd.holevo import holevo_information

def sha(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()
def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("--execute-frozen-validation",action="store_true"); args=parser.parse_args()
    if not args.execute_frozen_validation: parser.error("requires --execute-frozen-validation")
    config_path=ROOT/"configs/threshold_validation_v1.yaml"; config=load_yaml(config_path); oracle_config={**config["oracle"],"fixture_roster":config["fixture_roster"]}
    temp=ROOT/"results/threshold_validation_oracles_v1.json"
    oracle_path=ROOT/"configs/threshold_validation_oracles_v1.generated.yaml"; oracle_path.write_text(json.dumps(oracle_config),encoding="utf-8")
    try:
        oracle=run_oracle(oracle_path, ROOT/"configs/default.yaml", ROOT/"results/independent_confirmation_roster.json", ROOT/"configs/independent_confirmation_roster.yaml", ROOT/"results/current_environment_manifest.json", ROOT/"schemas/independent_confirmation_gram_oracles.schema.json", temp, None)
    finally: oracle_path.unlink(missing_ok=True)
    roster=json.loads((ROOT/"results/independent_confirmation_roster.json").read_text()); states=config["oracle"]["representative_states"]
    t=torch.tensor([x["transmittance"] for x in states],dtype=torch.float64); e=torch.tensor([x["epsilon_snu"] for x in states],dtype=torch.float64)
    default=load_yaml(ROOT/"configs/default.yaml"); fixture_config=copy.deepcopy(default); fixture_config["numerical_validation"]["fixture_initialization_seed"]=config["oracle"]["fixture_initialization_seed"]
    ensembles=representative_ensembles(fixture_config,t,e); ensembles.pop("near_coincident_pseudoinverse_stress",None)
    for phase in (5e-8,1e-7,2e-7): ensembles[f"near_coincident_phase_step_{phase:g}"]=stress_ensemble(phase,batch_size=3,v_max=4.,n_peak=30.)
    rows=[]
    for hp in oracle["oracle_fixture_rows"]:
        name=hp["fixture"]; ensemble=ensembles[name]
        if ensemble_sha256(ensemble)!=config["fixture_roster"][name]: raise ValueError(f"fixture hash mismatch: {name}")
        result=holevo_information(ensemble,t,e,backend="c4_gram",fock_cutoff=None,require_supported_symmetry=True,symmetry_tolerance=1e-8,density_trace_tolerance=1e-10,physicality_tolerance=1e-10,density_eigenvalue_tolerance=float.fromhex(config["candidate_threshold_float64_hex"]))
        final=hp["precision_rows"][-1]; mi=torch.tensor(hp["mi_bits"],dtype=torch.float64); beta=float(default["cvqkd"]["beta_reconciliation"])
        reference={"C":torch.full((3,),float(final["C"])),"w":torch.full((3,),float(final["w"]))}
        reference.update({k:torch.tensor([float(s[k]) for s in final["states"]]) for k in ("Z","lambda1","lambda2","lambda3","chi_BE","raw_K")})
        candidate=_result_metrics(result,mi,beta); comparison=_observable_comparison(candidate,reference)
        rows.append({"fixture":name,"ensemble_sha256":ensemble_sha256(ensemble),"oracle_full_support_rank":final["resolved_mathematical_rank"],"production_support_by_state":[x["support_size"] for x in _source_diagnostics(result)],"comparison":comparison,"oracle_converged":hp["successive_full_support_converged"]})
    passed=all(x["oracle_full_support_rank"]==256 and x["oracle_converged"] and x["comparison"]["passes_all_frozen_observable_tolerances"] for x in rows)
    payload={"schema_version":"threshold-validation-v1","status":"THRESHOLD_VALIDATION_PASS_PENDING_AUTHOR_APPROVAL" if passed else "THRESHOLD_VALIDATION_FAIL_CLOSED","fixture_count":len(rows),"rows":rows,"aggregate":{"all_pass":passed},"lifecycle_guards":config["lifecycle_guards"],"provenance":{"config_sha256":sha(config_path),"oracle_artifact_sha256":sha(temp),"runner_sha256":sha(Path(__file__)),"frozen_model_sha256":sha(ROOT/"docs/FINAL_MODEL_SPEC.md")}}
    out=ROOT/"results/threshold_validation_v1.json"; out.write_text(json.dumps(payload,indent=2)+"\n"); print(payload["status"]); return 0 if passed else 2
if __name__=="__main__": raise SystemExit(main())
