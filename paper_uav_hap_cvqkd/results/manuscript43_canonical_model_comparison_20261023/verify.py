"""Read-only verification of saved evidence; no evaluator imports or reruns."""
import csv
import hashlib
import json
import math
from pathlib import Path
import re

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
REPO = ROOT.parent


def read(name):
    return json.loads((OUT / name).read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def csv_rows(name):
    with (OUT / name).open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def close(left, right, tolerance=2e-12):
    return math.isfinite(float(left)) and math.isfinite(float(right)) and abs(float(left)-float(right)) <= tolerance


def main():
    startup = read("startup_manifest.json")
    for rel, expected in startup["protected"].items():
        require((REPO/rel).is_file(), f"Protected path missing: {rel}")
        require(sha(REPO/rel)==expected, f"Protected bytes changed: {rel}")
    for current, snapshot in [
        ("docs/EVIDENCE.md","EVIDENCE.md"),("docs/DECISION_LOG.md","DECISION_LOG.md"),
        ("docs/PROJECT_STATE.md","PROJECT_STATE.md"),("docs/NEXT_ACTIONS.md","NEXT_ACTIONS.md")]:
        old=(OUT/"startup_ledgers"/snapshot).read_text(encoding="utf-8-sig").replace("\r\n","\n")
        new=(ROOT/current).read_text(encoding="utf-8-sig").replace("\r\n","\n")
        # The current audit can prepend status; all prior blocks remain verbatim.
        old_blocks=old.split("\n",2)[-1]
        require(old_blocks in new, f"Historical ledger blocks changed: {current}")

    manifest=read("canonical_model_manifest.json")
    require(manifest["reference_identity"]=="BLOCKED_REFERENCE_NOT_LOCATED", "Unverified reference promoted")
    require(manifest["canonical_binding"]=="BLOCKED" and not manifest["canonical_evaluator_adopted"],
            "Canonical evaluator falsely adopted")
    require(not manifest["corrections_adopted"] and not manifest["production_modified"],"Production correction applied")
    require(not manifest["optimization_executed"] and not manifest["old_results_and_Cw_modified"],"Scope violation")
    require(manifest["security_status"]=="UNVALIDATED_SECURITY_MODEL","Security status promoted")
    require(manifest["lifecycle"]=="NOT_READY_FOR_PUBLICATION_SCALE_RUNS","Lifecycle promoted")
    require(sha(OUT/manifest["available_reference"])==startup["available_reference_sha256"],"Available PDF changed")
    require(sha(ROOT/"docs/FINAL_MODEL_SPEC.md")==startup["frozen_sha256"],"Frozen bytes changed")

    for receipt, producer, protocol in [
        ("numerical_receipt.json","audit_fixed.py","protocol.json"),
        ("refined_precision_receipt.json","refine_precision.py","additional_precision_protocol.json"),
        ("package_receipt.json","package_audit.py",None)]:
        value=read(receipt)
        require(value["status"]=="CURRENTLY_VERIFIED_PASS",f"Failed receipt: {receipt}")
        require(value["producer_sha256"]==sha(OUT/producer),f"Producer changed: {producer}")
        if protocol:
            require(value["protocol_sha256"]==sha(OUT/protocol),f"Protocol changed: {protocol}")

    source=read("fixed_source.json")
    require(sha(ROOT/source["source_path"])==source["source_sha256"],"Source payload changed")
    require(source["family"]=="Uniform" and source["VA"]==3 and source["nu_raw"]==0,"Source changed")
    alias=read("channel_alias_identity.json")
    require(alias["same_module_object"] and alias["same_function_object"] and
            alias["three_requested_labels_are_two_channel_laws"],"B/C alias proof absent")
    require(alias["historical_function"]==alias["Uniform_search_function"],"B/C paths differ")

    protocol=read("protocol.json")
    require(protocol["mass_tolerance"]==1e-10 and protocol["MI_tolerance"]==2e-10,"Tolerance changed")
    require(not protocol["canonical_eta_det_parameter"] and not protocol["optimization"],"Canonical scope changed")
    rows=read("three_model_comparison.json")
    require(len(rows)==9 and len(csv_rows("three_model_comparison.csv"))==9,"Comparison rows missing")
    contexts=read("fixed_contexts.json")
    require(set(contexts)==set(protocol["scenarios"]),"Scenario coverage changed")
    for scenario, context in contexts.items():
        subset={r["channel_model"]:r for r in rows if r["scenario"]==scenario}
        require(len(subset)==3 and context["geometry"]==protocol["scenarios"][scenario],"Geometry mismatch")
        b,c=subset["B_historical_random_width"],subset["C_Uniform_search_bounded"]
        for key in ["pdf_mass","P0","continuous_mass","E_eta","E_sqrt_eta","eta_f","E_eta_xi","xi_f",
                    "I_AB","beta_I_AB","chi_BE","raw_SKR"]:
            require(b[key]==c[key],f"B/C differ: {scenario}/{key}")
        for row in subset.values():
            require(row["source_hash"]==source["ensemble_hash"] and row["source_sha256"]==source["source_sha256"],
                    "Source identity mismatch")
            require(not row["security_valid"] and not row["requested_PDF_identity_verified"],"False validation promotion")
            require(close(row["eta_f"],row["E_sqrt_eta"]**2),"T != mh^2")
            require(close(row["E_eta_xi"],.0186*row["E_eta"]+.005*row["pdf_mass"]),"Noise moment mismatch")
            require(close(row["N_effective"],3*(row["E_eta"]-row["eta_f"])+row["E_eta_xi"]),"Shared N mismatch")
            require(close(row["xi_f"],row["N_effective"]/row["eta_f"]),"xi_f mismatch")
            if row["raw_SKR"] is None:
                require(abs(row["pdf_mass"]-1)>1e-10,"Unexpected blocked row")
                require(all(row[k] is None for k in ["I_AB","beta_I_AB","chi_BE"]),"Failed PDF has information")
            else:
                require(abs(row["pdf_mass"]-1)<=1e-10,"Failed PDF evaluated")
                require(close(row["raw_SKR"],.95*row["I_AB"]-row["chi_BE"]),"Raw K mismatch")
        for power, entry in context["raw_moments"]["direct"].items():
            require(abs(entry["residual"])<2e-10,f"Raw closed/direct mismatch: {scenario}/{power}")
        require(max(abs(context["bounded_moments"][k]-context["bounded_high"][k])
                    for k in ["m1","mh"])<2e-11,"Bounded quadrature mismatch")
    critical=next(r for r in rows if r["scenario"]=="critical_uniform_positive" and r["channel_model"]=="A_Eq10")
    require(critical["raw_SKR"] is None and close(critical["pdf_mass"],.9013297245653482),"Critical gate lost")
    positive=next(r for r in rows if r["scenario"]=="critical_uniform_positive" and r["channel_model"].startswith("B_"))
    require(close(positive["raw_SKR"],.10788256029424448),"Saved positive not reproduced")
    selected=read("fixed_validation.json")
    checks=[v for row in selected for v in row["checks"]]
    require(len(selected)==7 and len(checks)==84 and all(v["status"]=="CURRENTLY_VERIFIED_PASS" for v in checks),
            "Selected checks failed/missing")
    require(read("numerical_receipt.json")["independent_checks"]==len(checks),"Check count mismatch")

    refined=read("pooled_MI_refined.json")
    require(refined["status"]=="CURRENTLY_VERIFIED_PASS" and abs(refined["convergence_delta"])<2e-10,"Pooled refinement failed")
    require(refined["same_physical_law_as_historical_pooled"] and refined["no_eta_det_parameter"],"Pooled law changed")
    require(read("pooled_MI_precision.json")["status"]=="BLOCKED_BY_NUMERICAL_PRECISION","Original precision failure hidden")
    require(close(refined["compared_to_Gaussian"]["delta_K"],.95*refined["compared_to_Gaussian"]["delta_I_AB"]),
            "Isolated MI attribution mismatch")
    for entry in refined["records"]:
        require(entry["conditional_mass_residual"]<2e-10,"Mixture conditional mass failed")
        require(close(entry["quadrature_m1"],positive["E_eta"],2e-10),"Mixture m1 mismatch")
        require(close(entry["quadrature_mh"],positive["E_sqrt_eta"],2e-10),"Mixture mh mismatch")
    for row in csv_rows("rician_comparison.csv"):
        require(close(float(row["Eq10_full_moment"])/float(row["Rician_product_full_moment"]),
                      float(row["predicted_relative_ratio"]),2e-10),"Rician moment-ratio identity failed")
    require(read("source_notation_checks.json")["checks"]==4,"Source notation checks missing")
    literal=read("literal_internal_consistency.json")
    require(literal["literal_rate_status"]=="BLOCKED_LITERAL_LIKELIHOOD" and literal["literal_Vmod"]==.75,
            "Literal source inconsistency hidden")
    for row in csv_rows("component_classification.csv"):
        require(row["classification"] in ["EXACT_MATCH","EQUIVALENT","DIFFERENT","BLOCKED"],"Invalid classification")
        require(sha(ROOT/row["path"])==row["sha256"],"Inventory source hash drift")
    require(len(csv_rows("equation_comparison.csv"))==22,"Equation map incomplete")
    require(len(csv_rows("parameter_provenance.csv"))==54,"Parameter table incomplete")

    # Check local links in all human-facing deliverables; remote links are bibliography.
    docs=["report_vi.md","mathematical_differences_vi.md","correction_proposal_v1.md"]
    for name in docs:
        body=(OUT/name).read_text(encoding="utf-8")
        require("\ufffd" not in body and body.count("???")==0,f"Text encoding failed: {name}")
        for link in re.findall(r"\]\(([^)]+)\)",body):
            if not link.startswith(("https://","http://","#")):
                require((OUT/link).is_file(),f"Broken report link: {link}")
    if (OUT/"artifact_manifest.json").exists():
        sealed=read("artifact_manifest.json")
        for rel,expected in sealed["files"].items():
            require(sha(OUT/rel)==expected,f"Artifact changed after sealing: {rel}")
        seal=read("final_seal.json")
        require(sha(OUT/"artifact_manifest.json")==seal["artifact_manifest_sha256"],"Artifact manifest seal changed")
        require(sha(OUT/"verification.json")==seal["verification_sha256"],"Verification seal changed")
        for rel,expected in seal["ledgers"].items():
            require(sha(ROOT/rel)==expected,f"Ledger changed since final seal: {rel}")
    return dict(status="CURRENTLY_VERIFIED_PASS",
                scope="SAVED_FIXED_AUDIT_EVIDENCE_ONLY_NOT_CANONICAL_OR_SECURITY_APPROVAL",
                protected_old_files=len(startup["protected"]),selected_independent_check_records=len(checks),
                source_notation_checks=4,comparison_rows=9,component_rows=35,equation_rows=22,parameters=54,
                pooled_refinement="CURRENTLY_VERIFIED_PASS",requested_v43_2_identity="BLOCKED_REFERENCE_NOT_LOCATED",
                canonical_binding="BLOCKED",production_changed=False,old_cache_changed=False,
                lifecycle="NOT_READY_FOR_PUBLICATION_SCALE_RUNS",security_status="UNVALIDATED_SECURITY_MODEL",
                source_hash=source["ensemble_hash"],frozen_sha256=startup["frozen_sha256"])


if __name__=="__main__":
    print(json.dumps(main(),indent=2))
