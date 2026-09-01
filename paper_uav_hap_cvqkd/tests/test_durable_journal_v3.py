from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

from src.validation.durable_journal_v3 import (
    DurableJournal,
    JournalError,
    replay_journal,
)


IDENTITY = {"config_sha256": "a" * 64, "producer_sha256": "b" * 64}


def _path_domain(status="PATH_DOMAIN_CERTIFIED"):
    return {
        "status": status,
        "certified_leaf_count": 2 if status == "PATH_DOMAIN_CERTIFIED" else 0,
        "unresolved_leaf_count": 0 if status == "PATH_DOMAIN_CERTIFIED" else 1,
        "certified_leaves": [],
        "unresolved_leaves": [],
    }


def _start(journal):
    journal.append("RUN_STARTED", {"state_label": "medium", "family": "ps"})
    journal.append("PATH_DOMAIN_COMMITTED", {"path_domain": _path_domain()})
    journal.append("WORK_QUEUE_INITIALIZED", {"pending": [["0/1", "1/1", 0]]})


def test_fsynced_hash_chained_roundtrip(tmp_path):
    with DurableJournal(
        tmp_path, attempt_id="attempt-1", segment_id="medium/ps", identity=IDENTITY
    ) as journal:
        _start(journal)
        journal.append("NODE_STARTED", {"node_id": "root"})
        journal.append("NODE_COMMITTED", {
            "node_id": "root", "node": {"status": "CERTIFIED"}, "action": "ACCEPT",
        })
        journal.append("SEGMENT_COMPLETED", {"status": "CERTIFIED_FIXED_INERTIA"})

    replay = replay_journal(
        tmp_path, expected_identity=IDENTITY, expected_attempt_id="attempt-1",
        expected_segment_id="medium/ps",
    )
    assert replay.completed is True
    assert replay.next_sequence == 6
    assert replay.path_domain["status"] == "PATH_DOMAIN_CERTIFIED"
    assert len(replay.completed_nodes) == 1
    assert replay.head_sha256 == replay.records[-1]["record_sha256"]
    assert replay.chunks[0].torn_tail_size_bytes == 0


def test_path_domain_must_be_durable_before_node_work(tmp_path):
    with DurableJournal(
        tmp_path, attempt_id="attempt-1", segment_id="medium/ps", identity=IDENTITY
    ) as journal:
        journal.append("RUN_STARTED", {})
        with pytest.raises(JournalError, match="NODE_STARTED"):
            journal.append("NODE_STARTED", {"node_id": "illegal"})
    assert replay_journal(tmp_path).next_sequence == 1


def test_torn_tail_is_preserved_and_recovery_uses_new_chunk(tmp_path):
    with DurableJournal(
        tmp_path, attempt_id="attempt-1", segment_id="medium/ps", identity=IDENTITY
    ) as journal:
        _start(journal)
        journal.append("NODE_STARTED", {"node_id": "root"})
    first = tmp_path / "events-000000.jsonl"
    with first.open("ab", buffering=0) as stream:
        stream.write(b'{"uncommitted":')
        os.fsync(stream.fileno())

    with DurableJournal(
        tmp_path, attempt_id="attempt-1", segment_id="medium/ps",
        identity=IDENTITY, resume=True,
    ) as journal:
        journal.append("NODE_STARTED", {"node_id": "root"})
        journal.append("NODE_COMMITTED", {
            "node_id": "root", "node": {"status": "UNCERTIFIED"},
            "action": "UNRESOLVED",
        })
        journal.append("SEGMENT_COMPLETED", {"status": "UNCERTIFIED"})

    assert (tmp_path / "events-000001.jsonl").is_file()
    assert first.read_bytes().endswith(b'{"uncommitted":')
    replay = replay_journal(tmp_path)
    assert replay.completed is True
    assert replay.chunks[0].torn_tail_size_bytes > 0
    recovery = replay.records[4]
    assert recovery["event_type"] == "RECOVERY_STARTED"
    assert recovery["payload"]["abandoned_node_id"] == "root"
    assert len(replay.completed_nodes) == 1


def test_complete_tampered_record_fails_closed(tmp_path):
    with DurableJournal(
        tmp_path, attempt_id="attempt-1", segment_id="medium/ps", identity=IDENTITY
    ) as journal:
        journal.append("RUN_STARTED", {})
    path = tmp_path / "events-000000.jsonl"
    payload = json.loads(path.read_text())
    payload["payload"]["tampered"] = True
    path.write_text(json.dumps(payload, sort_keys=True) + "\n")
    with pytest.raises(JournalError, match="hash mismatch"):
        replay_journal(tmp_path)


def test_identity_mismatch_and_completed_resume_fail_closed(tmp_path):
    with DurableJournal(
        tmp_path, attempt_id="attempt-1", segment_id="medium/ps", identity=IDENTITY
    ) as journal:
        journal.append("RUN_STARTED", {})
        journal.append("PATH_DOMAIN_COMMITTED", {"path_domain": _path_domain("PATH_DOMAIN_UNCERTIFIED")})
        journal.append("SEGMENT_COMPLETED", {"status": "UNCERTIFIED_PATH_DOMAIN"})
    with pytest.raises(JournalError, match="identity mismatch"):
        replay_journal(tmp_path, expected_identity={"config_sha256": "c" * 64})
    with pytest.raises(JournalError, match="completed"):
        DurableJournal(
            tmp_path, attempt_id="attempt-1", segment_id="medium/ps",
            identity=IDENTITY, resume=True,
        )


def test_newline_terminated_invalid_json_is_not_ignored_as_torn_tail(tmp_path):
    with DurableJournal(
        tmp_path, attempt_id="attempt-1", segment_id="medium/ps", identity=IDENTITY
    ) as journal:
        journal.append("RUN_STARTED", {})
    with (tmp_path / "events-000000.jsonl").open("ab") as stream:
        stream.write(b"not-json\n")
    with pytest.raises(JournalError, match="Invalid complete JSON"):
        replay_journal(tmp_path)


def test_acknowledged_records_survive_abrupt_worker_exit(tmp_path):
    code = (
        "import os;from pathlib import Path;"
        "from src.validation.durable_journal_v3 import DurableJournal;"
        f"j=DurableJournal(Path({str(tmp_path)!r}),attempt_id='attempt-1',"
        f"segment_id='medium/ps',identity={IDENTITY!r});"
        "j.append('RUN_STARTED',{});"
        f"j.append('PATH_DOMAIN_COMMITTED',{{'path_domain':{_path_domain()!r}}});"
        "os._exit(17)"
    )
    completed = subprocess.run([sys.executable, "-c", code], check=False)
    assert completed.returncode == 17
    replay = replay_journal(tmp_path, expected_identity=IDENTITY)
    assert replay.next_sequence == 2
    assert replay.path_domain["status"] == "PATH_DOMAIN_CERTIFIED"
