"""Coarse/refined full-angle divergence search for a Uniform SKR crossing."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_skr_vs_link_distance_theta10urad import (
    DISTANCES_KM,
    EPSILON,
    OUTPUT as DISTANCE_OUTPUT,
    THETA_NEW,
    channel_row,
    evaluate_candidate,
    load_distance_config,
    load_bank,
    json_hash,
    model_identity,
)


OUTPUT = ROOT / "results" / "skr_vs_distance_theta_sensitivity_D10cm"
COARSE = (10, 15, 20, 30, 40, 50, 60, 80, 100, 120, 150, 180, 200)
COARSE_DISTANCES = (25.0, 30.0, 32.0, 34.0, 35.0, 36.0, 38.0, 40.0)


def write_csv(path: Path, rows: list[dict]) -> None:
    fields = sorted({k for row in rows for k in row})
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader(); writer.writerows(rows)


def classify(rows: list[dict]) -> tuple[str, float | None, float | None, float | None]:
    by_distance = {float(row["distance_km"]): row for row in rows}
    k30 = float(by_distance[30.0]["SKR"]); k40 = float(by_distance[40.0]["SKR"])
    if k30 <= 0.0: status = "TOO_NARROW_RANGE"
    elif k40 > 0.0: status = "TOO_LONG_RANGE"
    else: status = "TARGET_CROSSING"
    positive = [d for d, row in by_distance.items() if float(row["SKR"]) > 0.0]
    nonpositive = [d for d, row in by_distance.items() if float(row["SKR"]) <= 0.0]
    last_positive = max(positive) if positive else None
    first_nonpositive = min(nonpositive) if nonpositive else None
    crossing_distance = None if last_positive is None or first_nonpositive is None else 0.5 * (last_positive + first_nonpositive)
    return status, last_positive, first_nonpositive, crossing_distance


def evaluate_theta(config: dict, uniform: list[dict], theta_urad: float) -> list[dict]:
    rows = []
    for distance in COARSE_DISTANCES:
        channel = channel_row(config, distance, theta_urad * 1e-6)
        evaluated = [evaluate_candidate(candidate, channel, config) for candidate in uniform]
        best = max(evaluated, key=lambda row: float(row["SKR"]))
        rows.append({**channel, **best, "theta_div_urad": theta_urad, "scheme": "Uniform", "search_scope": "peak_feasible_exact_bank"})
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    args = parser.parse_args()
    output = args.output_dir.resolve(); output.mkdir(parents=True, exist_ok=True)
    config = load_distance_config(); bank, skipped = load_bank(config)
    uniform = [candidate for candidate in bank if candidate["family"] == "Uniform"]
    if not uniform: raise RuntimeError("No peak-feasible Uniform bank candidates.")
    values = list(COARSE)
    coarse_rows=[]; summaries=[]
    for theta in values:
        rows=evaluate_theta(config, uniform, theta); coarse_rows.extend(rows)
        status,last,first,cross=classify(rows)
        summaries.append({"theta_div_urad":theta,"w0_mm":1000*2*1.55e-6/(math.pi*theta*1e-6),"K_Uni_30":next(r["SKR"] for r in rows if float(r["distance_km"])==30),"K_Uni_35":next(r["SKR"] for r in rows if float(r["distance_km"])==35),"K_Uni_40":next(r["SKR"] for r in rows if float(r["distance_km"])==40),"last_positive_km":last,"first_nonpositive_km":first,"crossing_midpoint_km":cross,"status":status})
    targets=[row for row in summaries if row["status"]=="TARGET_CROSSING"]
    if not targets:
        values=sorted(set(values+[5,250,300]));
        for theta in [x for x in values if x not in COARSE]:
            rows=evaluate_theta(config,uniform,theta); coarse_rows.extend(rows); status,last,first,cross=classify(rows); summaries.append({"theta_div_urad":theta,"w0_mm":1000*2*1.55e-6/(math.pi*theta*1e-6),"K_Uni_30":next(r["SKR"] for r in rows if float(r["distance_km"])==30),"K_Uni_35":next(r["SKR"] for r in rows if float(r["distance_km"])==35),"K_Uni_40":next(r["SKR"] for r in rows if float(r["distance_km"])==40),"last_positive_km":last,"first_nonpositive_km":first,"crossing_midpoint_km":cross,"status":status})
        targets=[row for row in summaries if row["status"]=="TARGET_CROSSING"]
    selected=min(targets,key=lambda row:abs(float(row["crossing_midpoint_km"])-35.0)) if targets else None
    refinement=[]
    if selected:
        center=int(selected["theta_div_urad"]); refine_values=range(max(5,center-10),center+11,5)
        for theta in refine_values:
            rows=evaluate_theta(config,uniform,theta); refinement.extend(rows); status,last,first,cross=classify(rows); summaries.append({"theta_div_urad":theta,"w0_mm":1000*2*1.55e-6/(math.pi*theta*1e-6),"K_Uni_30":next(r["SKR"] for r in rows if float(r["distance_km"])==30),"K_Uni_35":next(r["SKR"] for r in rows if float(r["distance_km"])==35),"K_Uni_40":next(r["SKR"] for r in rows if float(r["distance_km"])==40),"last_positive_km":last,"first_nonpositive_km":first,"crossing_midpoint_km":cross,"status":status,"refinement":True})
        refined_targets=[row for row in summaries if row["status"]=="TARGET_CROSSING"]
        selected=min(refined_targets,key=lambda row:abs(float(row["crossing_midpoint_km"])-35.0)) if refined_targets else selected
    write_csv(output/"theta_sensitivity_table.csv",summaries)
    write_csv(output/"theta_sensitivity_exact_rows.csv",coarse_rows+refinement)
    report={"status":"THETA_DIVERGENCE_SENSITIVITY_COMPLETE","selected_theta_div_urad":None if selected is None else selected["theta_div_urad"],"selected_w0_m":None if selected is None else 2*1.55e-6/(math.pi*float(selected["theta_div_urad"])*1e-6),"table":summaries,"coarse_range_urad":list(COARSE),"uniform_bank_count":len(uniform),"skipped_bank_count":len(skipped),"experiment_scope":"Uniform peak-feasible exact bank only; no final figure generated before selection","model_identity":model_identity(),"candidate_bank_hash":json_hash(sorted((c["family"],c["nu_raw"],c["V_A"],c["ensemble_hash"]) for c in bank))}
    (output/"theta_sensitivity_report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2)); return 0


if __name__ == "__main__": raise SystemExit(main())
