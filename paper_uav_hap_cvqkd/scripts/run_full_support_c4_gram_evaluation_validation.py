"""Execute the frozen full-support C4 evaluation validation; no overrides."""
from __future__ import annotations
import copy, hashlib, json
from pathlib import Path
import torch
from _common import ROOT, load_yaml
from _numerical_validation import ensemble_sha256, representative_ensembles
from src.cvqkd.holevo import holevo_information
from src.cvqkd.mutual_information import discrete_mutual_information, standard_complex_noise
from src.utils.random import torch_generator

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def main():
    manifest=json.loads((ROOT/"configs/full_support_c4_gram_backend_implementation_manifest_v1.json").read_text())
    for relative, digest in manifest["required_sha256"].items():
        if sha(ROOT/relative)!=digest: raise ValueError(f"implementation manifest mismatch: {relative}")
    config=load_yaml(ROOT/"configs/full_support_c4_gram_evaluation_validation_v1.yaml"); roster=load_yaml(ROOT/"configs/threshold_validation_v1.yaml")
    states=roster["oracle"]["representative_states"]; t=torch.tensor([x["transmittance"] for x in states],dtype=torch.float64); e=torch.tensor([x["epsilon_snu"] for x in states],dtype=torch.float64)
    default=copy.deepcopy(load_yaml(ROOT/"configs/default.yaml")); default["numerical_validation"]["fixture_initialization_seed"]=roster["oracle"]["fixture_initialization_seed"]
    ensembles=representative_ensembles(default,t,e); beta=float(default["cvqkd"]["beta_reconciliation"]); rows=[]
    for name, expected in roster["fixture_roster"].items():
        ensemble=ensembles[name]
        if ensemble_sha256(ensemble)!=expected: raise ValueError(f"fixture hash mismatch: {name}")
        noise=standard_complex_noise((3,256,2048),generator=torch_generator(int(roster["oracle"]["mi_seed"]),"cpu"),device="cpu")
        with torch.no_grad():
            mi=discrete_mutual_information(ensemble,t,e,noise_samples_per_symbol=2048,standard_noise_samples=noise,noise_sample_chunk_size=64)
            result=holevo_information(ensemble,t,e,backend="c4_gram",fock_cutoff=None,density_eigenvalue_tolerance=float.fromhex(roster["candidate_threshold_float64_hex"]),density_trace_tolerance=1e-10)
        source=result.diagnostics["source_moment_diagnostics"]
        rows.append({"fixture":name,"ensemble_sha256":expected,"route":[x["route"] for x in source],"source":list(source),"C":result.coherent_correlation.tolist(),"w":result.w.tolist(),"Z":result.z.tolist(),"lambda1":result.covariance.lambda1.tolist(),"lambda2":result.covariance.lambda2.tolist(),"lambda3":result.covariance.lambda3.tolist(),"chi_BE":result.chi_be.tolist(),"raw_K":(beta*mi-result.chi_be).tolist()})
    passed=all(all(x["support_size"]==256 for x in row["source"]) for row in rows)
    out={"schema_version":"full-support-c4-gram-evaluation-validation-v1","status":"FULL_SUPPORT_BACKEND_VALIDATION_PASS" if passed else "FULL_SUPPORT_BACKEND_VALIDATION_FAIL_CLOSED","fixture_count":len(rows),"rows":rows,"lifecycle_guards":config["lifecycle_guards"],"provenance":{"config_sha256":sha(ROOT/"configs/full_support_c4_gram_evaluation_validation_v1.yaml"),"protocol_sha256":sha(ROOT/"configs/full_support_c4_gram_backend_protocol_v1.yaml"),"frozen_model_sha256":sha(ROOT/"docs/FINAL_MODEL_SPEC.md")}}
    (ROOT/"results/full_support_c4_gram_evaluation_validation_v1.json").write_text(json.dumps(out,indent=2)+"\n"); print(out["status"])
if __name__=="__main__": main()
