"""Prepared nine-angle pilot. This readiness task never invokes --pilot."""
import argparse
import json

import model
from support import OUT, ROOT, PREVIOUS, prior_run, read, save, sha, with_ensemble, write_csv
from provenance import ACCEPTED

SCHEMES = ["Optimized Uniform 256-QAM", "Fixed MB-shaped 256-QAM", "Optimized MB-shaped 256-QAM"]


def plan():
    protocol = read(OUT / "protocol.json")
    summary = read(OUT / "source_verification_summary.json")
    return dict(angles_deg=protocol["pilot_angles_deg"], proposed_sources=81,
        verified_available=summary["verified_available"], planned_channel_contexts=9,
        planned_candidate_evaluations=729, primary_Z_per_candidate=1,
        correlation_policy="manuscript_eq14_direct", source_jobs_in_pilot=0,
        fixed_MB=protocol["fixed_MB"], pool_policy="IDENTICAL_81_SOURCE_POOL_AT_ALL_NINE_ANGLES",
        scheme_candidate_rules=dict(Uniform="All Uniform sources", Fixed_MB="Exact fixed ensemble only",
                                    Optimized_MB="All81 sources, including Uniform and Fixed MB"),
        negative_K_policy="RETAIN_RAW_VALUES", pilot_executed=False, full_sweep_executed=False)


def require_ready():
    gate = read(OUT / "readiness.json")
    if gate["decision"] != "PASS" or gate["phase_B_ready"] is not True:
        raise model.ModelBlocked("Pilot prerequisites remain blocked: "+";".join(gate["blockers"]))
    for name, digest in gate["dependency_sha256"].items():
        if sha(ROOT / name) != digest:
            raise model.ModelBlocked("Readiness dependency changed: "+name)
    protocol = read(OUT / "protocol.json")
    model.validate_protocol(protocol)
    return protocol


def check_pool_identity(records, protocol):
    spec = read(ROOT / protocol["experiment_spec_path"])
    fields = ["family", "VA_hex", "nu_raw_hex", "ensemble_hash"]
    identity = lambda rows: {tuple(row[k] for k in fields) for row in rows}
    if len(records) != 81 or identity(records) != identity(spec["source_identities"]):
        raise model.ModelBlocked("Pilot source identities differ from the versioned81-source specification")


def load_sources(protocol):
    records = prior_run.old.rows(OUT / "pilot_source_verification.csv")
    if len(records) != 81 or any(r["classification"] not in ACCEPTED for r in records):
        raise model.ModelBlocked("Full proposed81-source pool is not verified; no silent subset substitution")
    check_pool_identity(records, protocol)
    sources = []
    for row in records:
        row.update(VA=float.fromhex(row["VA_hex"]), nu_raw=float.fromhex(row["nu_raw_hex"]),
                   C=float(row["C"]), w=float(row["w"]))
        source = with_ensemble(row)
        model.prior_model.helpers().validate_source(source)
        sources.append(source)
    return sources


def candidate_records(angle, context, sources, protocol):
    records = []
    for source in sources:
        record = dict(zenith_deg=angle, family=source["family"], VA=source["VA"],
            VA_hex=source["VA_hex"], nu_raw=source["nu_raw"], nu_raw_hex=source["nu_raw_hex"],
            source_hash=source["ensemble_hash"], C=source["C"], w=source["w"],
            source_classification=source["classification"], source_path=source["source_path"],
            source_payload_sha256=source["source_sha256"], protocol_sha256=sha(OUT / "protocol.json"),
            experiment_spec_sha256=protocol["experiment_spec_sha256"], correlation_policy=model.POLICY)
        try:
            record.update(**model.evaluate(source, context, protocol), status="CURRENTLY_VERIFIED_PASS", reason="")
        except ValueError as error:
            record.update(status="FAILED_NUMERICAL_DOMAIN", reason=str(error), K_raw=None,
                          I_AB=None, beta_I_AB=None, chi_BE=None, Z_manuscript_eq14=None)
        records.append(record)
    return records


def select(records, protocol):
    output = []
    for scheme in SCHEMES:
        candidates = [r for r in records if
            (scheme == SCHEMES[0] and r["family"] == "Uniform")
            or (scheme == SCHEMES[1] and r["source_hash"] == protocol["fixed_MB"]["ensemble_hash"])
            or scheme == SCHEMES[2]]
        valid = [r for r in candidates if r["status"] == "CURRENTLY_VERIFIED_PASS"]
        if valid:
            best = max(valid, key=lambda r: r["K_raw"])
            output.append(dict(best, scheme=scheme, search_scope="BEST_TESTED_IN_FIXED_PILOT_POOL"))
        else:
            output.append(dict(zenith_deg=records[0]["zenith_deg"], scheme=scheme,
                status="NO_VALID_CANDIDATE", reason="All scheme candidates failed numerical/domain checks",
                K_raw=None, I_AB=None, beta_I_AB=None, chi_BE=None, Z_manuscript_eq14=None))
    return output


def pilot():
    # The readiness guard precedes even directory creation and channel evaluation.
    protocol = require_ready()
    sources = load_sources(protocol)
    identity = dict(protocol_sha256=sha(OUT / "protocol.json"),
        pool_sha256=sha(OUT / "pilot_source_verification.csv"),
        evidence_sha256=sha(OUT / "source_verification_evidence.json"),
        producer_sha256={n: sha(OUT / n) for n in ["model.py", "run.py", "provenance.py", "support.py"]})
    target = OUT / "pilot"
    target.mkdir(exist_ok=True)
    all_candidates, selections = [], []
    for angle in protocol["pilot_angles_deg"]:
        checkpoint = target / f"angle_{angle:02d}.json"
        if checkpoint.exists():
            data = read(checkpoint)
            if data["identity"] != identity or data["zenith_deg"] != angle:
                raise ValueError("Incompatible checkpoint; preserve it for review")
            records = data["candidates"]
        else:
            import time
            began = time.perf_counter()
            context = model.channel_context(angle, protocol)
            moment_seconds = time.perf_counter()-began
            began = time.perf_counter()
            records = candidate_records(angle, context, sources, protocol)
            data = dict(identity=identity, zenith_deg=angle, channel_context=context,
                        moment_seconds=moment_seconds, evaluation_seconds=time.perf_counter()-began,
                        candidates=records)
            temporary = checkpoint.with_suffix(".json.tmp")
            save(temporary, data); temporary.replace(checkpoint)
        if len(records) != 81 or len({r["source_hash"] for r in records}) != 81:
            raise ValueError("Checkpoint does not contain the common81-source pool")
        all_candidates.extend(records)
        selections.extend(select(records, protocol))
    write_csv(target / "candidate_results.csv", all_candidates)
    write_csv(target / "pilot_skr_vs_zenith.csv", selections)
    return dict(status="PILOT_COMPLETED_WITH_EXPLICIT_CANDIDATE_STATUSES", angles=9,
                candidates=len(all_candidates), selected_rows=len(selections), full_sweep=False)


def verify():
    manifest = read(OUT / "artifact_manifest.json")
    for name, digest in manifest["files"].items():
        if sha(OUT / name) != digest: raise ValueError("Readiness artifact changed: "+name)
    for name, digest in read(OUT / "startup_manifest.json")["protected"].items():
        if sha(ROOT.parent / name) != digest: raise ValueError("Historical file changed: "+name)
    gate = read(OUT / "readiness.json")
    if (OUT / "pilot").exists() or gate["pilot_executed"] or gate["full_sweep_executed"]:
        raise ValueError("Readiness task must not execute a pilot or sweep")
    return dict(status="CURRENTLY_VERIFIED_PASS", artifacts=len(manifest["files"]),
        protected_historical_files=len(read(OUT / "startup_manifest.json")["protected"]),
        phase_B_ready=gate["phase_B_ready"], pilot_executed=False, full_sweep_executed=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--plan", action="store_true")
    group.add_argument("--verify-only", action="store_true")
    group.add_argument("--pilot", action="store_true")
    args = parser.parse_args()
    try:
        result = plan() if args.plan else verify() if args.verify_only else pilot()
    except model.ModelBlocked as error:
        print(json.dumps(dict(status="BLOCKED_PHASE_DEPENDENCY", reason=str(error)))); return 2
    print(json.dumps(result, indent=2)); return 0


if __name__ == "__main__":
    raise SystemExit(main())
