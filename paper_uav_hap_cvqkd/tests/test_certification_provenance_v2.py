from __future__ import annotations

import hashlib
import json

import pytest

from src.validation.certification_provenance_v2 import ProvenanceFailure, sha256


def test_sha256_reads_exact_bytes(tmp_path):
    target = tmp_path / "payload.bin"
    target.write_bytes(b"v2\x00payload")
    assert sha256(target) == hashlib.sha256(b"v2\x00payload").hexdigest()


def test_provenance_failure_is_explicit():
    failure = ProvenanceFailure(("hash mismatch", "environment mismatch"))
    assert str(failure) == "hash mismatch; environment mismatch"


def test_manifest_hash_mismatch_fails_before_environment(monkeypatch, tmp_path):
    from src.validation import certification_provenance_v2 as module

    manifest = tmp_path / "freeze.json"
    manifest.write_text(json.dumps({
        "schema_version": "taylor-eigencluster-freeze-manifest-v2",
        "status": "PROSPECTIVE_FROZEN_BEFORE_V2_OUTCOMES",
        "source_freeze_commit": "not-a-commit",
        "file_bindings": {"missing": "0" * 64},
        "live_environment": {},
    }), encoding="utf-8")
    monkeypatch.setattr(module, "live_environment", lambda: {})
    with pytest.raises(ProvenanceFailure) as caught:
        module.verify_freeze_manifest(
            tmp_path, manifest, "f" * 64, require_clean_worktree=False
        )
    assert "freeze_manifest_sha256" in str(caught.value)
    assert "missing_file=missing" in str(caught.value)

