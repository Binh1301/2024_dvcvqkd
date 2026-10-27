"""Classify the exact pilot sources using saved numerical evidence only."""
from collections import Counter
import re

import mpmath as mp

from support import OUT, ROOT, input_digests, pilot_rows, prior_model, prior_run, read, save, sha, write_csv

ACCEPTED = {"VERIFIED_EXACT", "VERIFIED_BY_ALTERNATIVE_EVIDENCE"}


def nested_dicts(value, pointer=""):
    if isinstance(value, dict):
        yield pointer, value
        for key, child in value.items():
            yield from nested_dicts(child, pointer+"/"+key)
    elif isinstance(value, list):
        for i, child in enumerate(value):
            yield from nested_dicts(child, pointer+"/"+str(i))


def alternative_ladder(source, node):
    """Input digests bind both arrays; metadata/nearby VA alone never suffices."""
    if "pmf_sha256" not in node or "amplitude_sha256" not in node:
        return None
    digests = input_digests(source)
    if any(node.get(k) != digest for k, digest in digests.items()):
        return None
    diag = node.get("diagnostics", {})
    if not isinstance(diag, dict):
        return None
    levels = diag.get("fallback_rows", [])
    if (diag.get("fallback_precisions") != [1050, 1250, 1450]
            or [x.get("digits") for x in levels] != [1050, 1250, 1450]
            or diag.get("support_size") != 256 or diag.get("tau_diagnostic") != 1e-12):
        return None
    with mp.workdps(110):
        if any(x.get("rank") != 256 or x.get("resolved") is not True
               or not mp.isfinite(mp.mpf(x["minimum_eigenvalue"]))
               or mp.mpf(x["minimum_eigenvalue"]) <= 0 for x in levels):
            return None
        deltas = {}
        for key in ["C", "w"]:
            values = [mp.mpf(x[key]) for x in levels]
            if not all(mp.isfinite(x) and x >= 0 for x in values):
                return None
            tolerance = mp.mpf("1e-7")+mp.mpf("1e-6")*abs(values[-1])
            residual = max(abs(x-values[-1]) for x in values)
            payload_delta = abs(mp.mpf(source[key])-values[-1])
            if residual > tolerance or payload_delta > tolerance:
                return None
            deltas[key] = dict(ladder_max_delta=str(residual), payload_delta=str(payload_delta),
                               absolute_plus_relative_tolerance=str(tolerance))
    return dict(method="EXACT_PMF_AND_AMPLITUDE_DIGESTS_PLUS_SAVED_FULL_SUPPORT_LADDER",
        input_digests=digests, precision_ladder=[1050, 1250, 1450], comparisons=deltas,
        limitations="Bound to identical source arrays, not the primary payload file hash; saved diagnostics were validated, no C,w recomputation and no security certification.")


def investigate():
    from scripts.exact_cache_provenance import source_settings, verify_source_payload
    from scripts.run_exact_mb_test2 import ensemble_hash
    from scripts.run_theta10_D55_unconstrained_three_scheme import make_ensemble, unconstrained_config
    config = unconstrained_config()
    settings = source_settings(config)
    precision_paths = [ROOT/p for p in read(OUT / "historical_precision_matches.json")["matching_files"]]
    precision_paths += list((OUT / "new_exact_source/source_receipts").glob("*.json"))
    precision = []
    excluded = []
    for path in sorted(set(precision_paths)):
        if "dummy" in path.parts or "staging_archive" in path.parts:
            excluded.append(dict(path=path.relative_to(ROOT).as_posix(), reason="SYNTHETIC_WORKER_TEST_NOT_SOURCE_EVIDENCE"))
            continue
        try:
            data = read(path)
        except ValueError:
            excluded.append(dict(path=path.relative_to(ROOT).as_posix(), reason="JSONL_OR_NON_SINGLE_RECEIPT"))
            continue
        if isinstance(data, dict) and any(x in str(data.get("status", "")).upper() for x in ["QUARANTIN", "SUPERSEDED", "DEPRECATED"]):
            excluded.append(dict(path=path.relative_to(ROOT).as_posix(), reason="HISTORICAL_QUARANTINE_OR_SUPERSESSION"))
            continue
        precision.append((path, data))
    roster = pilot_rows()
    hashes = {r["ensemble_hash"] for r in roster if r.get("ensemble_hash")}
    pattern = re.compile(r"(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])")
    alternatives = {}
    for candidate, data in precision:
        for pointer, node in nested_dicts(data):
            if "pmf_sha256" in node and "amplitude_sha256" in node:
                alternatives.setdefault((node["pmf_sha256"], node["amplitude_sha256"]), []).append((candidate, pointer, node))
    supporting = {h: [] for h in hashes}
    files = read(OUT / "historical_identity_matches.json")["matching_files"]
    inspected = {}
    for name in files:
        path = ROOT / name
        raw = path.read_bytes()
        inspected[path.relative_to(ROOT).as_posix()] = __import__("hashlib").sha256(raw).hexdigest()
        for h in set(pattern.findall(raw.decode("utf-8-sig", errors="replace"))) & hashes:
            supporting[h].append(path.relative_to(ROOT).as_posix())
    records, evidence = [], []
    for row in roster:
        record = {k: row.get(k) for k in ["family", "VA", "VA_hex", "nu_raw", "nu_raw_hex",
                  "ensemble_hash", "source_path", "source_sha256", "C", "w"]}
        record.update(classification="INSUFFICIENT_EVIDENCE", identity_status="NOT_RUN", reason="EXACT_SOURCE_NOT_AVAILABLE")
        detail = dict(source=record.copy(), direct_receipts=[], alternative_evidence=[],
            supporting_records=supporting.get(row.get("ensemble_hash"), []),
            metadata_only_does_not_establish_convergence=True)
        if row.get("source_path"):
            try:
                path = ROOT / row["source_path"]
                if sha(path) != row["source_sha256"]:
                    raise ValueError("Source payload file hash changed")
                payload = read(path)
                detail["implementation_and_settings"] = verify_source_payload(payload, settings)
                ensemble = make_ensemble(config, row["family"], row["nu_raw"], row["VA"])
                if ensemble_hash(ensemble) != row["ensemble_hash"]:
                    raise ValueError("Reconstructed ensemble identity mismatch")
                if (payload["V_A_hex"] != row["VA_hex"] or payload["nu_mb_raw_hex"] != row["nu_raw_hex"]
                        or payload["ensemble_hash"] != row["ensemble_hash"]):
                    raise ValueError("Source parameter identity mismatch")
                source = {**row, "p": ensemble.probabilities[0].numpy(), "alpha": ensemble.amplitudes[0].numpy()}
                p, alpha = prior_model.helpers().validate_source(source)
                if abs(float(p @ (2*alpha.real)**2)-row["VA"]) > 2e-12:
                    raise ValueError("Homodyne variance convention mismatch")
                record.update(identity_status="CURRENTLY_VERIFIED_PASS", nbar=float(p @ abs(alpha)**2),
                    X_variance=float(p @ (2*alpha.real)**2), reason="FULL_NUMERICAL_CONVERGENCE_EVIDENCE_NOT_LOCATED")
                for candidate, data in precision:
                    if not isinstance(data, dict): continue
                    receipt = dict(path=candidate.relative_to(ROOT).as_posix(), sha256=sha(candidate))
                    try:
                        if prior_run.check_receipt(payload, row["source_sha256"], data) == "CURRENTLY_VERIFIED_PASS":
                            detail["direct_receipts"].append(receipt)
                    except (ValueError, KeyError, TypeError):
                        detail.setdefault("malformed_receipts", []).append(receipt)
                digests = input_digests(source)
                for candidate, pointer, node in alternatives.get((digests["pmf_sha256"], digests["amplitude_sha256"]), []):
                    receipt = dict(path=candidate.relative_to(ROOT).as_posix(), sha256=sha(candidate))
                    try:
                        proof = alternative_ladder(source, node)
                    except (ValueError, KeyError, TypeError):
                        detail.setdefault("malformed_receipts", []).append(dict(**receipt, pointer=pointer))
                        continue
                    if proof:
                        detail["alternative_evidence"].append(dict(**receipt, pointer=pointer, **proof))
                if detail["direct_receipts"]:
                    record.update(classification="VERIFIED_EXACT", reason="PAYLOAD_BOUND_FULL_SUPPORT_PRECISION_RECEIPT")
                elif detail["alternative_evidence"]:
                    record.update(classification="VERIFIED_BY_ALTERNATIVE_EVIDENCE", reason="EXACT_ARRAY_DIGESTS_AND_FULL_PRECISION_LADDER")
            except (ValueError, OSError, KeyError, TypeError) as error:
                record.update(classification="INVALID", identity_status="FAILED", reason=str(error))
        record["supporting_record_count"] = len(detail["supporting_records"])
        record["receipt_paths"] = ";".join(x["path"] for x in detail["direct_receipts"]+detail["alternative_evidence"])
        detail["source"] = record
        records.append(record); evidence.append(detail)
    counts = Counter(r["classification"] for r in records)
    summary = dict(status="CURRENTLY_VERIFIED_PASS", proposed_sources=81,
        counts={k: counts[k] for k in ["VERIFIED_EXACT", "VERIFIED_BY_ALTERNATIVE_EVIDENCE", "INSUFFICIENT_EVIDENCE", "INVALID"]},
        verified_available=sum(counts[k] for k in ACCEPTED),
        full_pool_ready=all(r["classification"] in ACCEPTED for r in records),
        Cw_recomputations_in_provenance_audit=0,
        policy="No missing receipt is automatically INVALID. Guarded producer code, cache labels and repeated C,w records alone are supporting metadata, not a recovered precision history.",
        scientific_tolerance="1e-7 + 1e-6*abs(reference) for C,w, from the existing full-support worker/preregistration; no interpolation",
        historical_identity_files_inspected=len(inspected),
        precision_files_used=len(precision), excluded_precision_files=excluded)
    write_csv(OUT / "pilot_source_verification.csv", records)
    save(OUT / "source_verification_evidence.json", dict(summary=summary, sources=evidence,
        searched_precision_artifacts={p.relative_to(ROOT).as_posix(): sha(p) for p, _ in precision},
        inspected_historical_files=inspected))
    save(OUT / "source_verification_summary.json", summary)
    return summary


if __name__ == "__main__":
    print(__import__("json").dumps(investigate(), indent=2))
