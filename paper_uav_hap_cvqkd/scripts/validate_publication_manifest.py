"""Validate the frozen pre-test manifest and every referenced artifact hash."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.validation.publication_manifest import (
    file_sha256,
    load_publication_manifest,
    verify_bound_artifacts,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    manifest_path = args.manifest.resolve()
    manifest = load_publication_manifest(manifest_path)
    verify_bound_artifacts(manifest_path, manifest)
    mismatches = []
    for entry in manifest["checkpoints"]:
        checkpoint = Path(entry["path"])
        if not checkpoint.is_absolute():
            checkpoint = (manifest_path.parent / checkpoint).resolve()
        if file_sha256(checkpoint) != entry["sha256"]:
            mismatches.append(f"checkpoint:{entry['id']}")
    if mismatches:
        raise ValueError("Frozen manifest hash mismatch: " + ", ".join(mismatches))
    print(json.dumps({"manifest_valid": True, "manifest_sha256": file_sha256(manifest_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
