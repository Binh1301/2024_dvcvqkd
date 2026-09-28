"""Audit saved C,w source-moment records without computing new moments."""

from __future__ import annotations

import csv
from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
from typing import Any, Callable

import torch

if str(Path(__file__).resolve().parents[1]) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._common import load_yaml
from scripts.run_exact_mb_test2 import build_mb_ensemble, ensemble_hash, nu_mb_repo


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "skr_vs_link_distance"
EXCLUDE_DIRS = {
    ".git", ".venv", ".venv-cert", ".venv-inertia", ".pytest_cache",
    "__pycache__", "site-packages", "node_modules",
}
TEXT_SUFFIXES = {".json", ".jsonl", ".csv", ".yaml", ".yml", ".md", ".txt", ".log"}
BINARY_SUFFIXES = {".npz", ".npy", ".pt", ".pth", ".pkl", ".pickle"}
HEX64 = re.compile(r"^[0-9a-fA-F]{64}$")


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def scalar(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return None


def number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None


def first_number(value: Any) -> float | None:
    direct = number(value)
    if direct is not None:
        return direct
    if isinstance(value, (list, tuple)):
        for item in value:
            result = first_number(item)
            if result is not None:
                return result
    return None


def get_key(mapping: dict, names: tuple[str, ...]) -> Any:
    lowered = {str(key).lower(): value for key, value in mapping.items()}
    for name in names:
        if name.lower() in lowered:
            return lowered[name.lower()]
    return None


META_NAMES = {
    "status", "historical_status", "source_moment_status", "reference_status",
    "artifact_class", "route", "source_route", "source_moment_route",
    "cache_origin", "cache_key", "ensemble_hash", "source_ensemble_hash",
    "mi_ensemble_hash", "holevo_ensemble_hash", "nu_raw", "nu_mb_raw",
    "nu_repo", "nu_mb_repo", "va", "v_a", "v_a_actual", "m", "support_size",
    "rank", "source_settings", "source_implementation", "normalization_scale",
    "second_moment_after_normalization", "mb_convention", "production_use",
    "nu_mb_raw_hex", "nu_mb_repo_hex", "v_a_hex",
    "phase_disabled", "c_phi", "epsilon_total_definition", "T", "distance_km",
    "zeta_deg", "eta_ao", "ao_status", "cn2_phase",
}


def context_values(mapping: dict, inherited: dict[str, Any]) -> dict[str, Any]:
    result = dict(inherited)
    for key, value in mapping.items():
        if str(key).lower() in META_NAMES and scalar(value) is not None:
            result[str(key)] = value
    return result


def infer_family(path: str, context: dict[str, Any]) -> str:
    raw_nu = extract_parameter(context, True)
    if raw_nu is not None and abs(raw_nu) <= 1e-15 and "exact_mb" in path.lower():
        return "Uniform"
    text = (path + " " + " ".join(str(value) for value in context.values())).lower()
    if "binomial" in text:
        return "Binomial"
    if "uniform" in text:
        return "Uniform"
    if "maxwell" in text or re.search(r"\bmb\b|nu_raw|nu_mb", text):
        return "MB"
    if "ps_va" in text or "ps+v_a" in text:
        return "PS+V_A"
    if "full" in text or "gs" in text:
        return "Other learned/GS"
    return "UNKNOWN"


def extract_parameter(context: dict[str, Any], raw: bool) -> float | None:
    if raw:
        direct = first_number(context.get("nu_raw")) or first_number(context.get("nu_mb_raw")) or first_number(context.get("shaping_parameter_raw"))
        encoded = context.get("nu_mb_raw_hex")
    else:
        direct = first_number(context.get("nu_repo")) or first_number(context.get("nu_mb_repo")) or first_number(context.get("shaping_parameter_repo"))
        encoded = context.get("nu_mb_repo_hex")
    if direct is not None:
        return direct
    if isinstance(encoded, str):
        try:
            return float.fromhex(encoded)
        except ValueError:
            pass
    return None


def extract_va(context: dict[str, Any]) -> float | None:
    direct = first_number(context.get("VA")) or first_number(context.get("V_A")) or first_number(context.get("v_a")) or first_number(context.get("V_A_actual"))
    if direct is not None:
        return direct
    encoded = context.get("V_A_hex") or context.get("v_a_hex")
    if isinstance(encoded, str):
        try:
            return float.fromhex(encoded)
        except ValueError:
            pass
    return None


def extract_hash(context: dict[str, Any]) -> str | None:
    value = get_key(context, ("ensemble_hash", "source_ensemble_hash", "mi_ensemble_hash", "holevo_ensemble_hash"))
    return str(value) if isinstance(value, str) and value else None


def status_text(record: dict[str, Any]) -> str:
    fields = ("status", "historical_status", "source_moment_status", "reference_status", "artifact_class", "cache_origin")
    return " | ".join(str(record.get(key)) for key in fields if record.get(key) not in (None, ""))


def source_semantics(path: str, context: dict[str, Any], source_fingerprints: dict[str, str]) -> str:
    status = status_text(context).upper()
    if "SUPERSEDED_WRONG_AP_W" in status or "WRONG_AP_W" in path.upper():
        return "SOURCE_SEMANTICS_SUPERSEDED"
    implementation = context.get("source_implementation")
    if isinstance(implementation, dict):
        current = all(
            implementation.get(key) == value
            for key, value in source_fingerprints.items()
        )
        if current:
            return "SOURCE_SEMANTICS_EXACT_MATCH"
    if "exact_mb_source_cache" in path or "exact_source_cache" in path:
        return "SOURCE_SEMANTICS_EXACT_MATCH"
    if "C4" in status or "ARBITRARY_PRECISION_FALLBACK" in status or "GRAM" in status:
        return "SOURCE_SEMANTICS_UNKNOWN"
    return "SOURCE_SEMANTICS_UNKNOWN"


def normalization_status(path: str, context: dict[str, Any], semantics: str) -> str:
    if semantics == "SOURCE_SEMANTICS_SUPERSEDED":
        return "NORMALIZATION_UNKNOWN"
    if "exact_source_cache" in path and context.get("ensemble_hash"):
        return "NORMALIZATION_EXACT_MATCH"
    second = first_number(context.get("second_moment_after_normalization"))
    if second is not None and abs(second - 1.0) <= 1e-10:
        return "NORMALIZATION_EQUIVALENT_AFTER_NOTATION_CONVERSION"
    if context.get("normalization_scale") is not None:
        return "NORMALIZATION_UNKNOWN"
    return "NORMALIZATION_UNKNOWN"


def provenance_status(path: str, context: dict[str, Any], semantics: str) -> str:
    status = status_text(context).upper()
    if semantics == "SOURCE_SEMANTICS_SUPERSEDED" or "SUPERSEDED" in status:
        return "SUPERSEDED_HISTORICAL"
    if "exact_source_cache" in path and context.get("ensemble_hash"):
        return "CURRENT_HASH_BOUND_CACHE"
    if context.get("ensemble_hash"):
        return "HISTORICAL_HASH_PRESENT"
    return "HISTORICAL_UNBOUND"


@dataclass
class AuditState:
    records: list[dict[str, Any]]
    text_mentions: list[dict[str, Any]]
    binary_inventory: list[dict[str, Any]]
    parse_errors: list[dict[str, Any]]


def add_record(state: AuditState, path: Path, pointer: str, mapping: dict[str, Any], context: dict[str, Any]) -> None:
    c = first_number(get_key(mapping, ("C", "coherent_correlation")))
    w = first_number(get_key(mapping, ("w", "W")))
    if c is None or w is None:
        return
    merged = dict(context)
    merged.update(mapping)
    path_text = rel(path)
    original_hash = extract_hash(merged)
    state.records.append({
        "artifact_path": path_text,
        "record_pointer": pointer,
        "shaping_family": infer_family(path_text, merged),
        "shaping_parameter_raw": extract_parameter(merged, True),
        "shaping_parameter_repo": extract_parameter(merged, False),
        "V_A": extract_va(merged),
        "M": first_number(get_key(merged, ("M", "support_size", "rank"))),
        "C": c,
        "w": w,
        "original_ensemble_hash": original_hash,
        "status_text": status_text(merged),
        "source_route": get_key(merged, ("source_route", "source_moment_route", "route")),
        "source_settings": json.dumps(merged.get("source_settings"), sort_keys=True, default=str) if merged.get("source_settings") is not None else "",
        "normalization_scale": first_number(merged.get("normalization_scale")),
        "second_moment_after_normalization": first_number(merged.get("second_moment_after_normalization")),
        "metadata": merged,
    })


def walk_structured(state: AuditState, path: Path, value: Any, pointer: str = "$", context: dict[str, Any] | None = None) -> None:
    context = {} if context is None else context
    if isinstance(value, dict):
        local = context_values(value, context)
        add_record(state, path, pointer, value, local)
        for key, child in value.items():
            walk_structured(state, path, child, f"{pointer}.{key}", local)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            walk_structured(state, path, child, f"{pointer}[{index}]", context)


def parse_json_file(state: AuditState, path: Path) -> None:
    try:
        if path.suffix.lower() == ".jsonl":
            for index, line in enumerate(path.read_text(encoding="utf-8-sig", errors="replace").splitlines()):
                if not line.strip():
                    continue
                walk_structured(state, path, json.loads(line), f"line[{index}]")
        else:
            walk_structured(state, path, json.loads(path.read_text(encoding="utf-8-sig")))
    except Exception as error:
        state.parse_errors.append({"artifact_path": rel(path), "error": f"{type(error).__name__}: {error}"})


def parse_csv_file(state: AuditState, path: Path) -> None:
    try:
        with path.open(newline="", encoding="utf-8", errors="replace") as stream:
            reader = csv.DictReader(stream)
            fields = {str(field).lower() for field in (reader.fieldnames or [])}
            if not ({"c", "w"} <= fields):
                return
            for index, row in enumerate(reader, start=2):
                add_record(state, path, f"row[{index}]", row, row)
    except Exception as error:
        state.parse_errors.append({"artifact_path": rel(path), "error": f"{type(error).__name__}: {error}"})


def scan_binary(state: AuditState, path: Path) -> None:
    item: dict[str, Any] = {"artifact_path": rel(path), "suffix": path.suffix.lower(), "size": path.stat().st_size, "status": "NOT_PARSED"}
    try:
        if path.suffix.lower() == ".npz":
            import numpy as np
            with np.load(path, allow_pickle=False) as archive:
                item.update({"status": "INSPECTED", "keys": list(archive.keys())})
        elif path.suffix.lower() == ".npy":
            import numpy as np
            array = np.load(path, allow_pickle=False, mmap_mode="r")
            item.update({"status": "INSPECTED", "shape": list(array.shape), "dtype": str(array.dtype)})
        elif path.suffix.lower() in {".pt", ".pth"}:
            try:
                value = torch.load(path, map_location="cpu", weights_only=True)
                item.update({"status": "INSPECTED_WEIGHTS_ONLY", "top_level_keys": list(value.keys()) if isinstance(value, dict) else []})
            except Exception as error:
                item.update({"status": "WEIGHTS_ONLY_LOAD_FAILED", "error": f"{type(error).__name__}: {error}"})
        else:
            item["status"] = "NOT_PARSED_UNSAFE_PICKLE"
    except Exception as error:
        item.update({"status": "INSPECTION_FAILED", "error": f"{type(error).__name__}: {error}"})
    state.binary_inventory.append(item)


def scan_files() -> AuditState:
    state = AuditState([], [], [], [])
    output_dir = RESULTS.resolve()
    for root, dirs, files in os.walk(ROOT):
        dirs[:] = [name for name in dirs if name not in EXCLUDE_DIRS]
        root_path = Path(root)
        if output_dir == root_path or output_dir in root_path.parents:
            dirs[:] = []
            continue
        for filename in files:
            path = root_path / filename
            suffix = path.suffix.lower()
            if suffix == ".json" or suffix == ".jsonl":
                parse_json_file(state, path)
            elif suffix == ".csv":
                parse_csv_file(state, path)
            elif suffix in {".yaml", ".yml"}:
                try:
                    import yaml
                    walk_structured(state, path, yaml.safe_load(path.read_text(encoding="utf-8")))
                except Exception as error:
                    state.parse_errors.append({"artifact_path": rel(path), "error": f"{type(error).__name__}: {error}"})
            elif suffix in TEXT_SUFFIXES:
                try:
                    text = path.read_text(encoding="utf-8", errors="ignore")
                    hits = len(re.findall(r"(?i)(?:source.?moment|coherent.?correlation|\bC\b|\bw\b|wrong.?ap.?w)", text))
                    if hits:
                        state.text_mentions.append({"artifact_path": rel(path), "mention_count": hits, "sha256": sha256(path)})
                except OSError as error:
                    state.parse_errors.append({"artifact_path": rel(path), "error": f"{type(error).__name__}: {error}"})
            elif suffix in BINARY_SUFFIXES:
                scan_binary(state, path)
    return state


def current_source_fingerprints() -> dict[str, str]:
    return {
        "src/cvqkd/gram_moments.py": sha256(ROOT / "src" / "cvqkd" / "gram_moments.py"),
        "src/cvqkd/spectral_frechet.py": sha256(ROOT / "src" / "cvqkd" / "spectral_frechet.py"),
        "scripts/full_support_c4_worker.py": sha256(ROOT / "scripts" / "full_support_c4_worker.py"),
    }


def known_current_hashes() -> set[str]:
    hashes = set()
    for directory in (ROOT / "results" / "exact_mb_test2" / "exact_source_cache", ROOT / "results" / "exact_mb_asymptotic" / "exact_source_cache"):
        for path in directory.glob("*.json"):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                if payload.get("ensemble_hash"):
                    hashes.add(str(payload["ensemble_hash"]))
            except Exception:
                pass
    return hashes


def current_candidates(config: dict) -> list[dict[str, Any]]:
    vas = [0.1, 0.6, 1.1, 1.6, 2.1, 2.6, 3.1, 3.6, 4.0]
    candidates: list[dict[str, Any]] = []
    for family, raw_values in (("Uniform", [None]), ("Binomial", [None]), ("MB", [round(0.05 + 0.01 * index, 2) for index in range(16)])):
        kind = family.lower()
        for raw in raw_values:
            for va in vas:
                row = {"shaping_family": family, "nu_raw": raw, "nu_repo": None if raw is None else nu_mb_repo(raw), "V_A": va, "valid_ensemble": False, "current_ensemble_hash": None, "error": ""}
                try:
                    ensemble = build_mb_ensemble(config, raw if raw is not None else 0.0, va) if family == "MB" else __import__("src.modulation.joint_ps_gs", fromlist=["reference_ensemble"]).reference_ensemble(kind, batch_size=1, modulation_variance=va, v_min=float(config["cvqkd"]["v_min_snu"]), v_max=float(config["cvqkd"]["v_max_snu"]), n_peak_photons=float(config["cvqkd"]["n_peak_photons"]))
                    row["valid_ensemble"] = True
                    row["current_ensemble_hash"] = ensemble_hash(ensemble)
                except Exception as error:
                    row["error"] = f"{type(error).__name__}: {error}"
                candidates.append(row)
    return candidates


def classify_records(records: list[dict[str, Any]], current_hashes: set[str], fingerprints: dict[str, str]) -> None:
    for row in records:
        original = row.get("original_ensemble_hash")
        metadata = row.pop("metadata", {})
        semantics = source_semantics(row["artifact_path"], metadata, fingerprints)
        row["reconstructed_current_hash"] = original if original in current_hashes else None
        if original and original in current_hashes:
            row["hash_status"] = "CURRENT_HASH_EXACT_MATCH"
        elif original and HEX64.match(original):
            row["hash_status"] = "HASH_MISMATCH"
        else:
            row["hash_status"] = "HASH_UNAVAILABLE"
        row["normalization_status"] = normalization_status(row["artifact_path"], metadata, semantics)
        row["source_semantics_status"] = semantics
        row["provenance_status"] = provenance_status(row["artifact_path"], metadata, semantics)
        status = row["status_text"].upper()
        if semantics == "SOURCE_SEMANTICS_SUPERSEDED":
            decision, reason = "UNSAFE_SEMANTICS_MISMATCH", "Artifact is marked superseded/wrong AP w."
        elif row["hash_status"] == "CURRENT_HASH_EXACT_MATCH" and semantics == "SOURCE_SEMANTICS_EXACT_MATCH" and row["normalization_status"] == "NORMALIZATION_EXACT_MATCH":
            decision, reason = "SAFE_EXACT_REUSE", "Current hash-bound source cache and current source fingerprints."
        elif row["hash_status"] == "CURRENT_HASH_EXACT_MATCH" and semantics != "SOURCE_SEMANTICS_SUPERSEDED":
            decision, reason = "NEEDS_ONE_POINT_VALIDATION", "Hash is known but source/normalization metadata is incomplete."
        elif original and row["hash_status"] == "HASH_MISMATCH":
            decision, reason = "UNSAFE_ENSEMBLE_MISMATCH", "Stored hash is not a current known ensemble hash."
        elif row["C"] is not None and row["w"] is not None and row["normalization_status"] != "NORMALIZATION_UNKNOWN":
            decision, reason = "NEEDS_ONE_POINT_VALIDATION", "Historical C,w has partial normalization evidence but no current hash match."
        else:
            decision, reason = "INSUFFICIENT_METADATA", "No complete current ensemble/provenance proof."
        row["reuse_decision"] = decision
        row["reason"] = reason
        row["original_ensemble_hash"] = original or ""


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = sorted({key for row in rows for key in row}) or ["status"]
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def duplicate_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in records:
        key = row.get("original_ensemble_hash") or ""
        if key:
            groups.setdefault(key, []).append(row)
    output = []
    for key, rows in groups.items():
        if len(rows) < 2:
            continue
        cs = [float(row["C"]) for row in rows]
        ws = [float(row["w"]) for row in rows]
        output.append({
            "ensemble_hash": key,
            "occurrence_count": len(rows),
            "unique_C_count": len({repr(value) for value in cs}),
            "unique_w_count": len({repr(value) for value in ws}),
            "C_min": min(cs), "C_max": max(cs), "abs_delta_C": max(cs) - min(cs),
            "rel_delta_C": (max(cs) - min(cs)) / max(abs(value) for value in cs) if cs else None,
            "w_min": min(ws), "w_max": max(ws), "abs_delta_w": max(ws) - min(ws),
            "rel_delta_w": (max(ws) - min(ws)) / max(abs(value) for value in ws) if ws else None,
            "artifact_paths": " | ".join(sorted({row["artifact_path"] for row in rows})),
        })
    return output


def match_candidates(candidates: list[dict[str, Any]], records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_hash: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        if record.get("reconstructed_current_hash"):
            by_hash.setdefault(record["reconstructed_current_hash"], []).append(record)
    rows = []
    for candidate in candidates:
        matches = by_hash.get(candidate.get("current_ensemble_hash"), []) if candidate.get("valid_ensemble") else []
        ordered = sorted(matches, key=lambda item: {"SAFE_EXACT_REUSE": 0, "SAFE_AFTER_HASH_RECONSTRUCTION": 1, "NEEDS_ONE_POINT_VALIDATION": 2}.get(item.get("reuse_decision"), 9))
        best = ordered[0] if ordered else None
        row = {
            **candidate,
            "historical_match_found": bool(matches),
            "historical_artifact_path": best["artifact_path"] if best else "",
            "historical_C": best["C"] if best else None,
            "historical_w": best["w"] if best else None,
            "original_hash": best["original_ensemble_hash"] if best else "",
            "reconstructed_current_hash": best["reconstructed_current_hash"] if best else "",
            "normalization_status": best["normalization_status"] if best else "",
            "source_semantics_status": best["source_semantics_status"] if best else "",
            "provenance_status": best["provenance_status"] if best else "",
            "reuse_decision": best["reuse_decision"] if best else "NO_MATCH",
        }
        rows.append(row)
    return rows


def main() -> int:
    config = load_yaml(ROOT / "configs" / "default.yaml")
    state = scan_files()
    fingerprints = current_source_fingerprints()
    current_hashes = known_current_hashes()
    candidates = current_candidates(config)
    classify_records(state.records, current_hashes, fingerprints)
    duplicates = duplicate_rows(state.records)
    matches = match_candidates(candidates, state.records)

    RESULTS.mkdir(parents=True, exist_ok=True)
    audit_fields = [key for key in state.records[0].keys() if key != "metadata"] if state.records else []
    write_csv(RESULTS / "historical_source_moment_audit.csv", [{key: row.get(key) for key in audit_fields} for row in state.records])
    write_csv(RESULTS / "historical_source_moment_matches_current.csv", matches)
    write_csv(RESULTS / "historical_source_moment_duplicates.csv", duplicates)
    write_csv(RESULTS / "historical_source_moment_text_mentions.csv", state.text_mentions)

    counts = {}
    for row in state.records:
        counts[row["reuse_decision"]] = counts.get(row["reuse_decision"], 0) + 1
    family_counts = {}
    family_hashes: dict[str, set[str]] = {}
    for row in state.records:
        family = row["shaping_family"]
        family_counts[family] = family_counts.get(family, 0) + 1
        family_hashes.setdefault(family, set()).add(row.get("original_ensemble_hash") or row["artifact_path"] + "#" + row["record_pointer"])
    valid_candidates = [row for row in candidates if row["valid_ensemble"]]
    match_counts = {}
    for row in matches:
        match_counts[row["reuse_decision"]] = match_counts.get(row["reuse_decision"], 0) + 1
    missing = [row for row in matches if row["reuse_decision"] == "NO_MATCH"]
    missing_order = sorted(missing, key=lambda row: (0 if row["shaping_family"] == "MB" else 1, abs(float(row["V_A"]) - 2.0), -(float(row["nu_raw"]) if row["nu_raw"] is not None else -1.0)))[:10]
    detail = {
        "schema": "historical-source-moment-audit-v1",
        "status": "AUDIT_COMPLETE_NO_NEW_SOURCE_MOMENTS",
        "source_moment_generation": "NOT RUN",
        "repository_root": str(ROOT),
        "current_source_fingerprints": fingerprints,
        "inventory": {
            "total_Cw_records": len(state.records),
            "distinct_ensemble_keys": len({row.get("original_ensemble_hash") or row["artifact_path"] + "#" + row["record_pointer"] for row in state.records}),
            "family_record_counts": family_counts,
            "family_distinct_keys": {key: len(value) for key, value in family_hashes.items()},
            "duplicate_groups": len(duplicates),
            "text_artifacts_with_mentions": len(state.text_mentions),
            "binary_artifacts_inspected": len(state.binary_inventory),
            "parse_errors": len(state.parse_errors),
        },
        "current_distance_candidate_set": {
            "planned_combinations": len(candidates),
            "valid_ensemble_combinations": len(valid_candidates),
            "invalid_or_infeasible_combinations": len(candidates) - len(valid_candidates),
            "recovered_without_new_source_moment": sum(1 for row in matches if row["reuse_decision"] in {"SAFE_EXACT_REUSE", "SAFE_AFTER_HASH_RECONSTRUCTION"}),
            "recovery_fraction_of_valid_candidates": sum(1 for row in matches if row["reuse_decision"] in {"SAFE_EXACT_REUSE", "SAFE_AFTER_HASH_RECONSTRUCTION"}) / len(valid_candidates) if valid_candidates else 0.0,
            "recovery_fraction_of_planned_combinations": sum(1 for row in matches if row["reuse_decision"] in {"SAFE_EXACT_REUSE", "SAFE_AFTER_HASH_RECONSTRUCTION"}) / len(candidates) if candidates else 0.0,
            "decision_counts": match_counts,
        },
        "questions": {
            "historical_records_found": len(state.records),
            "distinct_transmitter_ensembles": len({row.get("original_ensemble_hash") or row["artifact_path"] + "#" + row["record_pointer"] for row in state.records}),
            "current_pending_candidates_with_historical_match": sum(1 for row in matches if row["historical_match_found"]),
            "duplicate_source_by_distance_or_AO": len(duplicates) > 0,
            "current_MB_nu_VA_available": [row for row in matches if row["shaping_family"] == "MB" and row["historical_match_found"]][:100],
            "current_uniform_VA_available": [row for row in matches if row["shaping_family"] == "Uniform" and row["historical_match_found"]],
            "current_binomial_parameter_VA_available": [row for row in matches if row["shaping_family"] == "Binomial" and row["historical_match_found"]],
            "next_10_current_candidates_requiring_new_source": missing_order,
        },
        "parse_errors": state.parse_errors,
        "binary_inventory": state.binary_inventory,
    }
    (RESULTS / "historical_source_moment_audit.json").write_text(json.dumps(detail, indent=2, default=str) + "\n", encoding="utf-8")

    print(json.dumps({
        "status": detail["status"],
        "total_Cw_records": detail["inventory"]["total_Cw_records"],
        "distinct_ensemble_keys": detail["inventory"]["distinct_ensemble_keys"],
        "planned_candidates": len(candidates),
        "valid_candidates": len(valid_candidates),
        "recovered": detail["current_distance_candidate_set"]["recovered_without_new_source_moment"],
        "decision_counts": match_counts,
        "duplicate_groups": len(duplicates),
        "parse_errors": len(state.parse_errors),
        "artifacts": [
            str((RESULTS / name).relative_to(ROOT)).replace("\\", "/")
            for name in (
                "historical_source_moment_audit.csv",
                "historical_source_moment_matches_current.csv",
                "historical_source_moment_duplicates.csv",
                "historical_source_moment_audit.json",
            )
        ],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
