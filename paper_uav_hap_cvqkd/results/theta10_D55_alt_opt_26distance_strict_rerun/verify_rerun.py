"""Read-only post-run verification: no channel, objective or source computation."""
import csv
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def rows(name):
    with (HERE / name).open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


before = json.loads((HERE / "input_manifest_before.json").read_text())
after = json.loads((HERE / "input_manifest_after.json").read_text())
assert before == after
for name, expected in before.items():
    assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
summary = rows("mb_alt_opt_distance_summary.csv")
starts = rows("ao_multistart_summary.csv")
iterations = rows("ao_iterations.csv")
objectives = rows("ao_objective_evaluations.csv")
missing = []
for r in iterations:
    for column in ("V_A_candidate_history", "nu_candidate_history"):
        for p in json.loads(r[column]):
            if p["status"] == "EXACT_SOURCE_MISSING":
                assert "K" not in p
    warning = json.loads(r["numerical_warning"])
    missing += warning["V_A_failures"] + warning["nu_failures"]
missing_pairs = set()
for r in iterations:
    for p in json.loads(r["V_A_candidate_history"]):
        if p["status"] == "EXACT_SOURCE_MISSING":
            missing_pairs.add((float(r["nu_before"]).hex(), float(p["value"]).hex()))
    for p in json.loads(r["nu_candidate_history"]):
        if p["status"] == "EXACT_SOURCE_MISSING":
            missing_pairs.add((float(p["value"]).hex(), float(r["optimized_V_A"]).hex()))
assert len(missing) == 836 and len(missing_pairs) == 50
for r in objectives:
    assert float(r["SKR"]) == float(r["beta_I_AB"]) - float(r["chi_BE"])
    assert float(r["beta_I_AB"]) == .95 * float(r["I_AB"])
for r in summary:
    distance = float(r["L_km"])
    group = [s for s in starts if float(s["distance_km"]) == distance]
    assert all(int(s["AO_iterations"]) > 0 for s in group)
    assert float(r["K"]) == max(float(s["K"]) for s in group)
    assert float(r["final_delta_K"]) == 0
    assert r["status"] in ("STAGNATED_IN_EXACT_CATALOG", "UNRESOLVED_BOUNDARY")
    for s in group:
        history = [it for it in iterations if float(it["distance_km"]) == distance and it["start_id"] == s["start_id"]]
        assert len(history) == int(s["AO_iterations"])
assert (HERE / "skr_vs_distance_three_scheme_log10.pdf").read_bytes().startswith(b"%PDF-")
assert (HERE / "skr_vs_distance_three_scheme_log10.png").read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
print(json.dumps({"status": "CURRENTLY_VERIFIED_PASS", "protected_files": len(before),
                  "distances": len(summary), "actual_multistarts": len(starts),
                  "actual_iterations": len(iterations), "fresh_exact_objectives": len(objectives),
                  "missing_requests": len(missing), "unique_missing_source_pairs": len(missing_pairs),
                  "all_selected_final_delta_K": 0.0, "png_pdf_headers_verified": True}, indent=2))
