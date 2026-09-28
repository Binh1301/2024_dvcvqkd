"""Summarize MB exact-compatible pairs from the existing audit only."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "results" / "skr_vs_link_distance" / "historical_source_moment_audit.csv"
MATCHES = ROOT / "results" / "skr_vs_link_distance" / "historical_source_moment_matches_current.csv"
OUTPUT = ROOT / "results" / "skr_vs_link_distance"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def key(nu: str, va: str) -> tuple[float, float]:
    return round(float(nu), 14), round(float(va), 14)


def write_csv(path: Path, records: list[dict]) -> None:
    fields = sorted({field for record in records for field in record})
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)


def main() -> int:
    audit = [
        row for row in rows(AUDIT)
        if row.get("shaping_family") == "MB"
        and row.get("source_semantics_status") == "SOURCE_SEMANTICS_EXACT_MATCH"
        and row.get("shaping_parameter_raw") not in (None, "")
        and row.get("V_A") not in (None, "")
    ]
    match_rows = rows(MATCHES)
    candidate_keys = {
        key(row["nu_raw"], row["V_A"])
        for row in match_rows
        if row.get("shaping_family") == "MB"
        and row.get("valid_ensemble") == "True"
        and row.get("nu_raw") not in (None, "")
    }
    safe_keys = {
        key(row["nu_raw"], row["V_A"])
        for row in match_rows
        if row.get("shaping_family") == "MB"
        and row.get("reuse_decision") == "SAFE_EXACT_REUSE"
        and row.get("nu_raw") not in (None, "")
    }
    grouped: dict[tuple[float, float], list[dict[str, str]]] = defaultdict(list)
    for row in audit:
        grouped[key(row["shaping_parameter_raw"], row["V_A"])].append(row)

    pair_rows = []
    for (nu, va), records in sorted(grouped.items()):
        c_values = [float(row["C"]) for row in records]
        w_values = [float(row["w"]) for row in records]
        pair_rows.append({
            "nu_raw": nu,
            "nu_repo": 42.5 * nu,
            "V_A": va,
            "historical_record_count": len(records),
            "C": c_values[0],
            "w": w_values[0],
            "unique_C_count": len(set(c_values)),
            "unique_w_count": len(set(w_values)),
            "max_abs_delta_C": max(c_values) - min(c_values),
            "max_abs_delta_w": max(w_values) - min(w_values),
            "current_distance_candidate": key(str(nu), str(va)) in candidate_keys,
            "safe_current_distance_match": key(str(nu), str(va)) in safe_keys,
            "source_path_examples": " | ".join(sorted({row["artifact_path"] for row in records})[:5]),
        })

    nu_rows = []
    by_nu: dict[float, list[dict]] = defaultdict(list)
    for row in pair_rows:
        by_nu[float(row["nu_raw"])].append(row)
    for nu, records in sorted(by_nu.items()):
        nu_rows.append({
            "nu_raw": nu,
            "nu_repo": 42.5 * nu,
            "unique_pair_count": len(records),
            "V_A_values": "; ".join(f"{float(row['V_A']):.14g}" for row in records),
            "safe_current_match_count": sum(bool(row["safe_current_distance_match"]) for row in records),
        })

    OUTPUT.mkdir(parents=True, exist_ok=True)
    write_csv(OUTPUT / "historical_mb_exact_pairs.csv", pair_rows)
    write_csv(OUTPUT / "historical_mb_exact_nu_summary.csv", nu_rows)
    summary = {
        "status": "DERIVED_FROM_EXISTING_AUDIT_ONLY",
        "new_source_moments_computed": False,
        "record_count": len(audit),
        "unique_pair_count": len(pair_rows),
        "unique_nu_count": len(nu_rows),
        "safe_current_distance_match_pair_count": sum(bool(row["safe_current_distance_match"]) for row in pair_rows),
        "outputs": [
            "results/skr_vs_link_distance/historical_mb_exact_pairs.csv",
            "results/skr_vs_link_distance/historical_mb_exact_nu_summary.csv",
        ],
    }
    (OUTPUT / "historical_mb_exact_pairs_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    for row in pair_rows:
        print(f"nu_raw={row['nu_raw']:.14g}, V_A={row['V_A']:.14g}, count={row['historical_record_count']}, C={row['C']:.17g}, w={row['w']:.17g}, current_candidate={row['current_distance_candidate']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
