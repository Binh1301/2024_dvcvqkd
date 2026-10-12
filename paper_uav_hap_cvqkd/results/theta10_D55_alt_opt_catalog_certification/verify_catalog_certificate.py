"""Independent read-only check of finite-set outputs, accounting and cap edge."""
import csv
import hashlib
import json
from pathlib import Path
import sys

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
sys.path.insert(0, str(ROOT))
from scripts import run_theta10_D55_alt_opt as ao


def read(name):
    with (OUT / name).open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def pair(row):
    return float(row["nu_raw"]).hex(), float(row["V_A"]).hex()


required = ("catalog_definition.csv", "catalog_coverage_by_distance.csv", "catalog_maximum_certificate.csv",
    "alt_opt_vs_catalog_maximum.csv", "catalog_top_two_candidates.csv", "refinement_limit_audit.md",
    "refinement_counterfactual.csv", "all_multistart_iterations.csv", "selected_run_iterations.csv",
    "remaining_source_dependency_review.csv", "final_recommendation.md", "final_report.json")
assert all((OUT / name).is_file() for name in required)
report = json.loads((OUT / "final_report.json").read_text())
manifest = json.loads((OUT / "input_manifest_after.json").read_text())
assert manifest == json.loads((OUT / "input_manifest_before.json").read_text())
for name, digest in manifest.items():
    assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
assert hashlib.sha256((ROOT / "scripts/certify_theta10_D55_exact_catalog.py").read_bytes()).hexdigest() == report["producer_sha256"]
definitions = read("catalog_definition.csv")
reference = {pair(r) for r in definitions if r["in_C_reference"] == "True"}
available = {pair(r) for r in definitions}
assert len(reference) == 136 and len(available) == 168 and reference <= available
evaluations = read("catalog_exact_objectives.csv")
for c in read("catalog_maximum_certificate.csv"):
    rows = [r for r in evaluations if float(r["L_km"]) == float(c["L_km"])]
    assert len(rows) == len({pair(r) for r in rows}) == 168
    assert {pair(r) for r in rows} == available
    ranked = sorted((r for r in rows if pair(r) in reference), key=lambda r: float(r["SKR"]), reverse=True)
    assert float(ranked[0]["SKR"]) == float(c["best_K"])
    assert float(ranked[1]["SKR"]) == float(c["second_K"])
    assert pair(ranked[0]) != pair(ranked[1])
    assert float(ranked[0]["SKR"])-float(ranked[1]["SKR"]) == float(c["reference_gap"])
    assert max(float(r["SKR"]) for r in rows) == float(c["best_K"])
    assert c["reference_status"] == "CERTIFIED_REFERENCE_CATALOG_MAXIMUM"
    assert c["available_all_status"] == "CERTIFIED_AVAILABLE_EXACT_SET_MAXIMUM"
starts = read("all_multistart_iterations.csv")
assert len(starts) == 129 and sum(int(r["AO_iterations"]) for r in starts) == 279
assert sum(int(r["AO_iterations"]) for r in starts if r["selected"] == "True") == 57
assert len(read("selected_run_iterations.csv")) == 57
counterfactual = read("refinement_counterfactual.csv")
assert len(counterfactual) == 650
assert {int(r["hypothetical_limit"]) for r in counterfactual} == {4, 8, 12, 16, 20}
assert all(r["stop_status"] == "UNKNOWN_SOURCE" and r["closed_with_existing_data"] == "False" for r in counterfactual)
assert (ao.K_TOLERANCE, ao.PARAMETER_TOLERANCE, ao.MAX_AO_ITERATIONS, ao.MAX_REFINEMENT_STAGES) == (1e-8, 1e-6, 6, 4)

# Synthetic unit fixture only, NOT a physical/security/source evaluation.
# Verify the documented loop-entry condition: last-stage radius attainment
# does not itself receive the completion verdict in the unchanged routine.
def toy(nu, va):
    return {"nu_raw": nu, "V_A": va, "SKR": -(va-1)**2}

result = ao.adaptive_maximize_1d(variable="V_A", fixed=.1,
    values=[1-1.5e-5, 1., 1+1.5e-5], objective=toy)
assert result["refinement_stages"] == 4
assert max(1-result["bracket"][0], result["bracket"][1]-1) <= ao.PARAMETER_TOLERANCE
assert result["refinement_status"] == "REFINEMENT_LIMIT_REACHED"
assert not ao.coordinate_search_complete(result)
print("CURRENTLY_VERIFIED_PASS: 12 outputs; 661 protected hashes; 26 exhaustive maxima; 129/279/57 accounting; 650 offline records; unchanged cap-edge fixture")
