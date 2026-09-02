"""Prospective two-phase provenance for V3 whole-segment certification.

This module deliberately contains no Gram, Taylor, inertia, or transmitter
imports.  Selection resolution and every provenance failure therefore happen
before a scientific fixture can be evaluated.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
from typing import Any, Iterable


PRESELECTION_SCHEMA = "taylor-eigencluster-preselection-manifest-v3"
PRESELECTION_STATUS = "PROSPECTIVE_FROZEN_BEFORE_V3_SELECTION_RESOLUTION_AND_OUTCOMES"
FREEZE_SCHEMA = "taylor-eigencluster-freeze-manifest-v3"
FREEZE_STATUS = "PROSPECTIVE_FROZEN_BEFORE_V3_FEASIBILITY_OUTCOMES"
SELECTION_SCHEMA = "taylor-eigencluster-selection-v3"
SELECTION_NAMESPACE = "whole-segment-v3-feasibility"
FAMILIES = ("ps", "gs", "va", "mixed")
STATES = ("bad", "medium", "good")


@dataclass(frozen=True)
class ProvenanceFailure(RuntimeError):
    failures: tuple[str, ...]

    def __str__(self) -> str:
        return "; ".join(self.failures)


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def object_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _git(root: Path, *arguments: str) -> str:
    return subprocess.check_output(
        ["git", *arguments], cwd=root, text=True, stderr=subprocess.STDOUT,
    ).strip()


def live_environment() -> dict[str, Any]:
    import flint
    import numpy
    import yaml
    from flint import ctx

    return {
        "python": ".".join(map(str, sys.version_info[:3])),
        "python_flint": str(flint.__version__),
        "flint": str(flint.__FLINT_VERSION__),
        "numpy": str(numpy.__version__),
        "pyyaml": str(yaml.__version__),
        "flint_threads": int(ctx.threads),
        "os_name": os.name,
        "platform_system": platform.system(),
        "platform_release": platform.release(),
        "platform_version": platform.version(),
        "machine": platform.machine(),
        "windows_job_objects": bool(
            os.name == "nt"
            and hasattr(__import__("ctypes").windll.kernel32, "CreateJobObjectW")
            and hasattr(__import__("ctypes").windll.kernel32, "AssignProcessToJobObject")
            and hasattr(__import__("ctypes").windll.kernel32, "TerminateJobObject")
        ),
    }


def _load_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as error:
        raise ProvenanceFailure((f"{label}_parse_error={error}",)) from error
    if not isinstance(value, dict):
        raise ProvenanceFailure((f"{label}_must_be_object",))
    return value


def _verify_bindings(root: Path, bindings: Any) -> list[str]:
    failures: list[str] = []
    if not isinstance(bindings, dict) or not bindings:
        return ["file_bindings_missing"]
    for relative, expected in sorted(bindings.items()):
        target = root / str(relative)
        if not target.is_file():
            failures.append(f"missing_file={relative}")
            continue
        actual = sha256(target)
        if actual != str(expected).lower():
            failures.append(f"sha256_mismatch={relative}:{expected}:{actual}")
    return failures


def verify_manifest(
    root: Path,
    manifest_path: Path,
    expected_manifest_sha256: str,
    *,
    schema_version: str,
    status: str,
    require_clean_worktree: bool = True,
) -> dict[str, Any]:
    """Verify one externally hash-anchored freeze manifest and environment."""

    root = Path(root).resolve()
    manifest_path = Path(manifest_path).resolve()
    failures: list[str] = []
    actual_manifest_hash = sha256(manifest_path)
    if actual_manifest_hash != expected_manifest_sha256.lower():
        failures.append(
            "freeze_manifest_sha256 "
            f"expected={expected_manifest_sha256.lower()} actual={actual_manifest_hash}"
        )
    manifest = _load_object(manifest_path, "freeze_manifest")
    if manifest.get("schema_version") != schema_version:
        failures.append("freeze_manifest_schema_version")
    if manifest.get("status") != status:
        failures.append("freeze_manifest_status")
    failures.extend(_verify_bindings(root, manifest.get("file_bindings")))

    source_commit = str(manifest.get("source_freeze_commit", ""))
    head: str | None = None
    try:
        head = _git(root, "rev-parse", "HEAD")
        subprocess.check_call(
            ["git", "merge-base", "--is-ancestor", source_commit, head], cwd=root,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    except Exception:
        failures.append("source_freeze_commit_not_ancestor")

    if require_clean_worktree:
        try:
            dirty = _git(root, "status", "--porcelain")
        except Exception as error:
            failures.append(f"git_status_error={error}")
        else:
            if dirty:
                failures.append("worktree_not_clean")

    try:
        observed_environment = live_environment()
    except Exception as error:
        failures.append(f"live_environment_error={error}")
        observed_environment = None
    expected_environment = manifest.get("live_environment")
    if observed_environment is not None and observed_environment != expected_environment:
        failures.append(
            "live_environment_mismatch expected="
            + json.dumps(expected_environment, sort_keys=True)
            + " actual=" + json.dumps(observed_environment, sort_keys=True)
        )

    if failures:
        raise ProvenanceFailure(tuple(failures))
    return {
        "status": "PROVENANCE_VERIFIED",
        "freeze_manifest_sha256": actual_manifest_hash,
        "repository_head": head,
        "source_freeze_commit": source_commit,
        "file_binding_count": len(manifest["file_bindings"]),
        "live_environment": observed_environment,
        "manifest": manifest,
    }


def verify_preselection_manifest(
    root: Path, manifest_path: Path, expected_manifest_sha256: str, *,
    require_clean_worktree: bool = True,
) -> dict[str, Any]:
    return verify_manifest(
        root, manifest_path, expected_manifest_sha256,
        schema_version=PRESELECTION_SCHEMA, status=PRESELECTION_STATUS,
        require_clean_worktree=require_clean_worktree,
    )


def verify_freeze_manifest(
    root: Path, manifest_path: Path, expected_manifest_sha256: str, *,
    require_clean_worktree: bool = True,
) -> dict[str, Any]:
    return verify_manifest(
        root, manifest_path, expected_manifest_sha256,
        schema_version=FREEZE_SCHEMA, status=FREEZE_STATUS,
        require_clean_worktree=require_clean_worktree,
    )


def _unique_by(rows: Iterable[dict[str, Any]], key: str, expected: tuple[str, ...]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        label = row.get(key)
        if label not in expected or label in result:
            raise ProvenanceFailure((f"invalid_or_duplicate_{key}={label}",))
        result[str(label)] = row
    if set(result) != set(expected):
        raise ProvenanceFailure((f"incomplete_{key}_universe",))
    return result


def segment_identity_payload(
    bundle: dict[str, Any], state_label: str, family: str,
) -> dict[str, Any]:
    """Canonical scientific identity used only for outcome-blind ranking."""

    states = _unique_by(bundle.get("states", []), "label", STATES)
    segments = _unique_by(bundle.get("segments", []), "family", FAMILIES)
    return {
        "state": states[state_label],
        "family": family,
        "start_parameters": bundle.get("start_parameters"),
        "end_parameters": segments[family].get("end_parameters"),
        "v_min_float64_hex": bundle.get("v_min_float64_hex"),
        "v_max_float64_hex": bundle.get("v_max_float64_hex"),
    }


def resolve_feasibility_selection(
    *, roster_sha256: str, fixture_bundle_sha256: str,
    bundle: dict[str, Any], namespace: str = SELECTION_NAMESPACE,
) -> dict[str, Any]:
    """Score all 12 rows and choose one state independently per family."""

    if namespace != SELECTION_NAMESPACE:
        raise ProvenanceFailure((f"selection_namespace={namespace}",))
    candidates: list[dict[str, str]] = []
    selected: list[dict[str, str]] = []
    for family in FAMILIES:
        family_rows = []
        for state in STATES:
            identity_sha = object_sha256(segment_identity_payload(bundle, state, family))
            score_input = "\0".join((
                namespace, roster_sha256.lower(), fixture_bundle_sha256.lower(),
                family, state, identity_sha,
            )).encode("ascii")
            score = hashlib.sha256(score_input).hexdigest()
            row = {
                "state_label": state,
                "family": family,
                "segment_identity_sha256": identity_sha,
                "ranking_sha256": score,
            }
            candidates.append(row)
            family_rows.append(row)
        selected.append(min(family_rows, key=lambda row: (
            row["ranking_sha256"], row["state_label"],
        )))
    return {
        "namespace": namespace,
        "score_serialization": (
            "UTF8(namespace\\0roster_sha256\\0fixture_bundle_sha256\\0family"
            "\\0state_label\\0canonical_segment_identity_sha256)"
        ),
        "candidate_rows": candidates,
        "selected_rows": selected,
        "selection_payload_sha256": object_sha256({
            "namespace": namespace,
            "candidate_rows": candidates,
            "selected_rows": selected,
        }),
    }


def verify_selection_artifact(
    path: Path,
    expected_sha256: str,
    *,
    roster_path: Path,
    bundle_path: Path,
    expected_preselection_manifest_sha256: str | None = None,
    expected_config_sha256: str | None = None,
) -> dict[str, Any]:
    """Recompute the complete 12-row selection and reject any copied IDs."""

    actual = sha256(path)
    failures: list[str] = []
    if actual != expected_sha256.lower():
        failures.append(
            f"selection_artifact_sha256 expected={expected_sha256.lower()} actual={actual}"
        )
    artifact = _load_object(path, "selection_artifact")
    if artifact.get("schema_version") != SELECTION_SCHEMA:
        failures.append("selection_schema_version")
    if artifact.get("status") != "DETERMINISTIC_SELECTION_RESOLVED_BEFORE_V3_OUTCOMES":
        failures.append("selection_status")
    roster_hash = sha256(roster_path)
    bundle_hash = sha256(bundle_path)
    if artifact.get("confirmation_roster_sha256") != roster_hash:
        failures.append("selection_roster_sha256_mismatch")
    if artifact.get("fixture_bundle_sha256") != bundle_hash:
        failures.append("selection_bundle_sha256_mismatch")
    if (expected_preselection_manifest_sha256 is not None and
            artifact.get("preselection_manifest_sha256") != expected_preselection_manifest_sha256):
        failures.append("selection_preselection_manifest_sha256_mismatch")
    if (expected_config_sha256 is not None and
            artifact.get("config_sha256") != expected_config_sha256):
        failures.append("selection_config_sha256_mismatch")
    bundle = _load_object(bundle_path, "fixture_bundle")
    try:
        computed = resolve_feasibility_selection(
            roster_sha256=roster_hash, fixture_bundle_sha256=bundle_hash,
            bundle=bundle,
            namespace=str(artifact.get("selection", {}).get("namespace", "")),
        )
    except ProvenanceFailure as error:
        failures.extend(error.failures)
        computed = None
    if computed is None or artifact.get("selection") != computed:
        failures.append("mechanical_feasibility_selection_mismatch")
    if failures:
        raise ProvenanceFailure(tuple(failures))
    return {
        "status": "SELECTION_VERIFIED",
        "sha256": actual,
        "selection": computed,
        "artifact": artifact,
    }


__all__ = [
    "FAMILIES", "FREEZE_SCHEMA", "FREEZE_STATUS", "PRESELECTION_SCHEMA",
    "PRESELECTION_STATUS", "ProvenanceFailure", "SELECTION_NAMESPACE",
    "SELECTION_SCHEMA", "STATES", "canonical_json_bytes", "live_environment",
    "object_sha256", "resolve_feasibility_selection", "segment_identity_payload",
    "sha256", "verify_freeze_manifest", "verify_manifest",
    "verify_preselection_manifest", "verify_selection_artifact",
]
