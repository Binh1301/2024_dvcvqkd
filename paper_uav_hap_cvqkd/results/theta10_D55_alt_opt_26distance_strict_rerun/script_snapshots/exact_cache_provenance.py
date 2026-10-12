"""Exact-cache compatibility: raw evidence plus LF-only source canonicalization.

Historical payloads are never rewritten. A historical raw digest is accepted
only if it equals current bytes or a demonstrable all-LF/all-CRLF encoding of
the current file. Whitespace, expressions and code order are not normalized.
"""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_FILES = ("src/cvqkd/gram_moments.py", "src/cvqkd/spectral_frechet.py", "scripts/full_support_c4_worker.py")
IDENTITY_FIELDS = ("schema", "ensemble_hash", "nu_mb_raw_hex", "nu_mb_repo_hex", "V_A_hex", "mb_convention", "source_implementation", "source_settings")
MB_CONVENTION = "nu_mb_repo=42.5*nu_mb_raw; raw grid is square_qam256(alpha0=sqrt(30))"


def json_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def canonical_bytes(raw):
    return raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def source_hashes(raw):
    canonical = canonical_bytes(raw)
    return {"raw_sha256": hashlib.sha256(raw).hexdigest(),
            "canonical_lf_sha256": hashlib.sha256(canonical).hexdigest(),
            "crlf_sha256": hashlib.sha256(canonical.replace(b"\n", b"\r\n")).hexdigest()}


def source_settings(config):
    from scripts._common import holevo_numerical_kwargs
    from src.cvqkd.gram_moments import PRECISION_LADDER
    n = holevo_numerical_kwargs(config)
    return {"density_eigenvalue_tolerance": n["density_eigenvalue_tolerance"],
            "physicality_tolerance": n["physicality_tolerance"], "precision_ladder": list(PRECISION_LADDER)}


def verify_source_payload(payload, settings, implementations=None):
    if any(k not in payload for k in (*IDENTITY_FIELDS, "cache_key", "support_size", "C", "w", "source_moment_route")):
        raise ValueError("SOURCE_IDENTITY_MISSING")
    if payload["schema"] != "exact-mb-source-cache-v1" or payload["source_settings"] != settings:
        raise ValueError("SOURCE_SETTINGS_INCOMPATIBLE")
    if payload["mb_convention"] != MB_CONVENTION or int(payload["support_size"]) != 256:
        raise ValueError("SOURCE_CONSTRUCTION_INCOMPATIBLE")
    if not all(math.isfinite(float(payload[k])) for k in ("C", "w")):
        raise ValueError("SOURCE_MOMENTS_NONFINITE")
    nu = float.fromhex(payload["nu_mb_raw_hex"])
    va = float.fromhex(payload["V_A_hex"])
    if nu < 0 or not math.isfinite(nu) or not math.isfinite(va) or va <= 0 or float.fromhex(payload["nu_mb_repo_hex"]) != 42.5 * nu:
        raise ValueError("SOURCE_PARAMETERS_INCOMPATIBLE")
    original = {k: payload[k] for k in IDENTITY_FIELDS}
    if payload["cache_key"] != json_hash(original):
        raise ValueError("SOURCE_HISTORICAL_KEY_CORRUPTED")
    implementations = implementations if implementations is not None else {n: (ROOT / n).read_bytes() for n in SOURCE_FILES}
    if set(payload["source_implementation"]) != set(implementations):
        raise ValueError("SOURCE_IMPLEMENTATION_IDENTITY_MISSING")
    records = {}
    for name, raw in implementations.items():
        hashes = source_hashes(raw)
        stored = payload["source_implementation"][name]
        if stored not in hashes.values():
            raise ValueError(f"SOURCE_IMPLEMENTATION_INCOMPATIBLE: {name}")
        records[name] = {"historical_raw_sha256": stored, **hashes,
                         "verification": "RAW_BYTE_MATCH" if stored == hashes["raw_sha256"] else "VERIFIED_NEWLINE_EQUIVALENT"}
    canonical = {**original, "source_implementation": {n: r["canonical_lf_sha256"] for n, r in records.items()}}
    return {"status": "VERIFIED", "policy": "LF_ONLY_WITH_PROVEN_HISTORICAL_RAW_ALIAS_V1",
            "historical_cache_key": payload["cache_key"], "canonical_source_cache_key": json_hash(canonical),
            "source_settings_sha256": json_hash(settings), "implementation": records,
            "canonical_source_identity": canonical}


def objective_identity(config, channel):
    from scripts.run_skr_vs_link_distance_theta10urad import BETA, EPSILON, GH_ORDER
    files = ("scripts/run_skr_vs_link_distance_theta10urad.py", "scripts/_common.py",
             "scripts/calculate_channel_pdf_and_moments.py", "scripts/run_uniform_beam_waist_diagnostic.py",
             "src/cvqkd/holevo.py", "src/cvqkd/mutual_information.py",
             "src/modulation/joint_ps_gs.py", "src/modulation/qam256.py")
    # Include transitive scientific code, excluding optimizer/cache plumbing.
    files = set(files) | set(SOURCE_FILES) | {str(p.relative_to(ROOT)).replace("\\", "/") for folder in ("src/channel", "src/cvqkd") for p in (ROOT / folder).rglob("*.py")}
    identity = {"schema": "theta10-exact-objective-v2", "config": config, "channel": channel,
                "security": "direct_Z_minus", "MI": "deterministic_heterodyne_product",
                "quadrature_order": GH_ORDER, "beta": BETA, "epsilon": EPSILON,
                "scientific_implementation": {n: source_hashes((ROOT / n).read_bytes())["canonical_lf_sha256"] for n in sorted(files)}}
    return {"identity": identity, "sha256": json_hash(identity)}


def objective_compatible(stored, expected):
    if not stored or "identity" not in stored or "sha256" not in stored:
        return False
    return stored["sha256"] == json_hash(stored["identity"]) == expected["sha256"] and stored["identity"] == expected["identity"]
