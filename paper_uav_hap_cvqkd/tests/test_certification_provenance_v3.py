from __future__ import annotations

import hashlib
import json

import pytest

from src.validation.certification_provenance_v3 import (
    ProvenanceFailure,
    resolve_feasibility_selection,
    verify_selection_artifact,
)


def _bundle():
    return {
        "states": [
            {"label": label, "value": index}
            for index, label in enumerate(("bad", "medium", "good"))
        ],
        "segments": [
            {"family": family, "end_parameters": {"value": index}}
            for index, family in enumerate(("ps", "gs", "va", "mixed"))
        ],
        "start_parameters": {"value": 0},
        "v_min_float64_hex": float(.1).hex(),
        "v_max_float64_hex": float(4).hex(),
    }


def test_new_namespace_selection_is_complete_and_deterministic():
    left = resolve_feasibility_selection(
        roster_sha256="a" * 64, fixture_bundle_sha256="b" * 64,
        bundle=_bundle(),
    )
    right = resolve_feasibility_selection(
        roster_sha256="a" * 64, fixture_bundle_sha256="b" * 64,
        bundle=_bundle(),
    )
    assert left == right
    assert left["namespace"] == "whole-segment-v3-feasibility"
    assert len(left["candidate_rows"]) == 12
    assert [row["family"] for row in left["selected_rows"]] == [
        "ps", "gs", "va", "mixed",
    ]


def test_selection_namespace_mismatch_fails_closed():
    with pytest.raises(ProvenanceFailure, match="selection_namespace"):
        resolve_feasibility_selection(
            roster_sha256="a" * 64, fixture_bundle_sha256="b" * 64,
            bundle=_bundle(), namespace="outcome-tuned",
        )


def test_selection_artifact_hash_mismatch_is_rejected(tmp_path):
    roster = tmp_path / "roster.json"; roster.write_text("{}")
    bundle = tmp_path / "bundle.json"; bundle.write_text(json.dumps(_bundle()))
    artifact = tmp_path / "selection.json"; artifact.write_text("{}")
    with pytest.raises(ProvenanceFailure, match="selection_artifact_sha256"):
        verify_selection_artifact(
            artifact, "0" * 64, roster_path=roster, bundle_path=bundle,
        )


def test_selection_identity_changes_when_bundle_changes():
    first = _bundle(); second = _bundle()
    second["segments"][0]["end_parameters"]["value"] = 99
    left = resolve_feasibility_selection(
        roster_sha256="a" * 64, fixture_bundle_sha256="b" * 64, bundle=first,
    )
    right = resolve_feasibility_selection(
        roster_sha256="a" * 64, fixture_bundle_sha256="b" * 64, bundle=second,
    )
    left_ps = [r for r in left["candidate_rows"] if r["family"] == "ps"]
    right_ps = [r for r in right["candidate_rows"] if r["family"] == "ps"]
    assert left_ps != right_ps

