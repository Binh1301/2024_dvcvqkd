"""Fail-before-evaluation provenance checks for V2 certification.

The freeze manifest is deliberately separate from the numerical config: the
caller supplies the expected manifest digest, avoiding a mutable self-hash.
No function in this module evaluates a physical fixture.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


@dataclass(frozen=True)
class ProvenanceFailure(RuntimeError):
    failures: tuple[str, ...]

    def __str__(self) -> str:
        return "; ".join(self.failures)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(root: Path, *arguments: str) -> str:
    return subprocess.check_output(
        ["git", *arguments], cwd=root, text=True, stderr=subprocess.STDOUT
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
    }


def verify_freeze_manifest(
    root: Path,
    manifest_path: Path,
    expected_manifest_sha256: str,
    *,
    require_clean_worktree: bool = True,
) -> dict[str, Any]:
    """Verify every frozen binding and the live certification environment.

    Raises ``ProvenanceFailure`` before any numerical fixture may be loaded.
    """

    failures: list[str] = []
    actual_manifest_hash = sha256(manifest_path)
    if actual_manifest_hash != expected_manifest_sha256.lower():
        failures.append(
            f"freeze_manifest_sha256 expected={expected_manifest_sha256.lower()} "
            f"actual={actual_manifest_hash}"
        )
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as error:
        raise ProvenanceFailure((f"freeze_manifest_parse_error={error}",)) from error

    if manifest.get("schema_version") != "taylor-eigencluster-freeze-manifest-v2":
        failures.append("freeze_manifest_schema_version")
    if manifest.get("status") != "PROSPECTIVE_FROZEN_BEFORE_V2_OUTCOMES":
        failures.append("freeze_manifest_status")

    bindings = manifest.get("file_bindings", {})
    if not isinstance(bindings, dict) or not bindings:
        failures.append("file_bindings_missing")
    else:
        for relative, expected in sorted(bindings.items()):
            target = root / relative
            if not target.is_file():
                failures.append(f"missing_file={relative}")
                continue
            actual = sha256(target)
            if actual != str(expected).lower():
                failures.append(f"sha256_mismatch={relative}:{expected}:{actual}")

    try:
        head = _git(root, "rev-parse", "HEAD")
        source_commit = str(manifest.get("source_freeze_commit", ""))
        subprocess.check_call(
            ["git", "merge-base", "--is-ancestor", source_commit, head],
            cwd=root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        failures.append("source_freeze_commit_not_ancestor")
        head = None

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
            + " actual="
            + json.dumps(observed_environment, sort_keys=True)
        )

    if failures:
        raise ProvenanceFailure(tuple(failures))
    return {
        "status": "PROVENANCE_VERIFIED",
        "freeze_manifest_sha256": actual_manifest_hash,
        "repository_head": head,
        "source_freeze_commit": manifest["source_freeze_commit"],
        "file_binding_count": len(bindings),
        "live_environment": observed_environment,
    }

