from __future__ import annotations

import hashlib
import json

import pytest

from src.validation.certification_provenance_v2 import ProvenanceFailure


def _write_gate(path, *, status="EXACT_TAU_ORACLE_CERTIFIED", unresolved=0):
    path.write_text(json.dumps({
        "status": status,
        "aggregate": {
            "fixture_count": 4,
            "certified_fixture_count": 4,
            "unresolved_fixture_count": unresolved,
            "complex128_reference_used": False,
        },
    }), encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_exact_tau_gate_accepts_only_complete_validated_artifact(tmp_path):
    from scripts.certify_taylor_eigencluster_segments_v2 import _verify_exact_tau_gate

    path = tmp_path / "gate.json"
    digest = _write_gate(path)
    row = _verify_exact_tau_gate(path, digest)
    assert row["certified_fixture_count"] == 4


def test_exact_tau_gate_rejects_hash_mismatch_before_segment_work(tmp_path):
    from scripts.certify_taylor_eigencluster_segments_v2 import _verify_exact_tau_gate

    path = tmp_path / "gate.json"
    _write_gate(path)
    with pytest.raises(ProvenanceFailure, match="exact_tau_artifact_sha256"):
        _verify_exact_tau_gate(path, "0" * 64)


def test_exact_tau_gate_rejects_partial_oracle(tmp_path):
    from scripts.certify_taylor_eigencluster_segments_v2 import _verify_exact_tau_gate

    path = tmp_path / "gate.json"
    digest = _write_gate(path, status="EXACT_TAU_ORACLE_FAIL_CLOSED", unresolved=1)
    with pytest.raises(ProvenanceFailure, match="not_certified"):
        _verify_exact_tau_gate(path, digest)
