from __future__ import annotations

import pytest

from scripts.certify_taylor_eigencluster_segments_v3 import (
    _gate,
    _journal_summary,
    _remaining_total_budget,
)
from src.validation.durable_journal_v3 import DurableJournal, JournalError


IDENTITY = {"config_sha256": "a" * 64}


def _settings():
    return {
        "resources": {
            "maximum_feasibility_seconds": 1800,
            "maximum_timeout_overshoot_seconds": 2,
        },
        "feasibility_gate": {
            "exact_selected_segment_count": 4,
            "minimum_certified_fixed_inertia_segments": 1,
            "maximum_median_terminal_unresolved_far_count": 37,
            "maximum_median_terminal_final_reduced_dimension": 61,
            "require_all_paired_coefficient_to_entrywise_radius_ratios_strictly_below": 1.0,
        },
    }


def _row(index, *, status="UNCERTIFIED"):
    return {
        "state_label": ("bad", "medium", "good", "bad")[index],
        "family": ("ps", "gs", "va", "mixed")[index],
        "status": status,
        "attempted_node_count": 1,
        "completed_node_count": 1,
        "successful_schur_elimination_count": 1,
        "path_domain_persisted": True,
        "path_domain_status": "PATH_DOMAIN_CERTIFIED",
        "journal_status": "JOURNAL_VALID",
        "watchdog": {"return_bound_satisfied": True},
        "metrics": {
            "paired_radius_ratios": [.5],
            "unresolved_far_distribution": [20],
            "final_reduced_dimension_distribution": [28],
            "true_near_size_distribution": [8],
        },
    }


def test_frozen_gate_requires_structural_improvement_and_one_certificate():
    rows = [_row(index) for index in range(4)]
    rows[0]["status"] = "CERTIFIED_FIXED_INERTIA"
    result = _gate(
        _settings(), rows,
        preflight={"status": "SYNTHETIC_PREFLIGHT_PASS"},
        total_elapsed_seconds=100,
    )
    assert result["passed"] is True
    assert all(result["checks"].values())


def test_resource_limit_or_no_schur_fails_gate():
    rows = [_row(index) for index in range(4)]
    rows[0]["status"] = "CERTIFIED_FIXED_INERTIA"
    rows[1]["status"] = "RESOURCE_LIMIT"
    rows[2]["successful_schur_elimination_count"] = 0
    result = _gate(
        _settings(), rows,
        preflight={"status": "SYNTHETIC_PREFLIGHT_PASS"},
        total_elapsed_seconds=100,
    )
    assert result["passed"] is False
    assert not result["checks"]["zero_provenance_resource_journal_or_watchdog_defects"]
    assert not result["checks"]["successful_schur_for_every_spectral_segment"]


def test_journal_summary_counts_started_and_committed_independently(tmp_path):
    with DurableJournal(
        tmp_path, attempt_id="a", segment_id="bad/ps", identity=IDENTITY,
    ) as journal:
        journal.append("RUN_STARTED", {})
        journal.append("PATH_DOMAIN_COMMITTED", {"path_domain": {
            "status": "PATH_DOMAIN_CERTIFIED",
        }})
        journal.append("WORK_QUEUE_INITIALIZED", {"pending": []})
        journal.append("NODE_STARTED", {"node_id": "node-0"})
    summary, nodes = _journal_summary(
        tmp_path, identity=IDENTITY, attempt_id="a", segment_id="bad/ps",
    )
    assert summary["attempted_node_count"] == 1
    assert summary["completed_node_count"] == 0
    assert summary["outstanding_node_id"] == "node-0"
    assert nodes == []


def test_missing_journal_is_not_valid(tmp_path):
    with pytest.raises(JournalError, match="no durable records"):
        _journal_summary(
            tmp_path, identity=IDENTITY, attempt_id="a", segment_id="bad/ps",
        )


def test_total_budget_is_hard_and_never_negative():
    assert _remaining_total_budget(100, 10, now=109) == 1
    assert _remaining_total_budget(100, 10, now=111) == 0
