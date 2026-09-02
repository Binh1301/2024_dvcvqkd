"""Durable append-only JSONL evidence journal for V3 segment workers.

Each acknowledged event is newline terminated, hash chained, and fsynced.
Recovery never truncates a torn final record: it starts a new numbered chunk
whose first event identifies the preceding chunk and any uncommitted tail.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any, Iterable


SCHEMA_VERSION = "taylor-eigencluster-journal-event-v3"
_CHUNK_PATTERN = re.compile(r"^events-(\d{6})\.jsonl$")
_REQUIRED_KEYS = {
    "schema_version", "attempt_id", "segment_id", "identity", "sequence",
    "event_type", "previous_record_sha256", "payload", "record_sha256",
}
_EVENT_TYPES = {
    "RUN_STARTED",
    "PATH_DOMAIN_COMMITTED",
    "WORK_QUEUE_INITIALIZED",
    "NODE_STARTED",
    "SCHUR_ELIMINATION_COMMITTED",
    "NODE_COMMITTED",
    "RECOVERY_STARTED",
    "SEGMENT_COMPLETED",
}


class JournalError(RuntimeError):
    """Raised when append-only evidence is invalid or internally inconsistent."""


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _record_hash(record: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in record.items() if key != "record_sha256"}
    return _sha256(_canonical(unsigned))


def _chunk_paths(directory: Path) -> list[Path]:
    rows = []
    if not directory.is_dir():
        return rows
    for path in directory.iterdir():
        match = _CHUNK_PATTERN.match(path.name)
        if match:
            rows.append((int(match.group(1)), path))
    rows.sort()
    if rows and [index for index, _ in rows] != list(range(rows[-1][0] + 1)):
        raise JournalError("Journal chunk sequence contains a gap.")
    return [path for _, path in rows]


@dataclass(frozen=True)
class ChunkEvidence:
    path: str
    sha256: str
    size_bytes: int
    complete_record_count: int
    torn_tail_size_bytes: int
    torn_tail_sha256: str | None


@dataclass(frozen=True)
class JournalReplay:
    records: tuple[dict[str, Any], ...]
    chunks: tuple[ChunkEvidence, ...]
    head_sha256: str | None
    next_sequence: int
    outstanding_node_id: str | None
    path_domain: dict[str, Any] | None
    completed_nodes: tuple[dict[str, Any], ...]
    completed: bool


def _validate_state_machine(records: Iterable[dict[str, Any]]) -> tuple[
    str | None, dict[str, Any] | None, tuple[dict[str, Any], ...], bool
]:
    started = False
    path_domain: dict[str, Any] | None = None
    queue_initialized = False
    outstanding: str | None = None
    completed_nodes: list[dict[str, Any]] = []
    completed = False
    for record in records:
        event = record["event_type"]
        payload = record["payload"]
        if completed:
            raise JournalError("Events may not follow SEGMENT_COMPLETED.")
        if event == "RUN_STARTED":
            if started:
                raise JournalError("RUN_STARTED must occur exactly once and first.")
            started = True
        elif not started:
            raise JournalError("RUN_STARTED must be the first journal event.")
        elif event == "PATH_DOMAIN_COMMITTED":
            if path_domain is not None or queue_initialized or outstanding:
                raise JournalError("PATH_DOMAIN_COMMITTED is out of order.")
            candidate = payload.get("path_domain")
            if not isinstance(candidate, dict) or candidate.get("status") not in {
                "PATH_DOMAIN_CERTIFIED", "PATH_DOMAIN_UNCERTIFIED"
            }:
                raise JournalError("Complete path-domain payload/status is required.")
            path_domain = candidate
        elif event == "WORK_QUEUE_INITIALIZED":
            if path_domain is None or path_domain.get("status") != "PATH_DOMAIN_CERTIFIED":
                raise JournalError("Work queue requires a certified path-domain event.")
            if queue_initialized or outstanding:
                raise JournalError("WORK_QUEUE_INITIALIZED is duplicated/out of order.")
            if not isinstance(payload.get("pending"), list):
                raise JournalError("WORK_QUEUE_INITIALIZED requires pending intervals.")
            queue_initialized = True
        elif event == "NODE_STARTED":
            node_id = payload.get("node_id")
            if not queue_initialized or outstanding is not None:
                raise JournalError("NODE_STARTED is out of order.")
            if not isinstance(node_id, str) or not node_id:
                raise JournalError("NODE_STARTED requires node_id.")
            outstanding = node_id
        elif event == "NODE_COMMITTED":
            node_id = payload.get("node_id")
            if outstanding is None or node_id != outstanding:
                raise JournalError("NODE_COMMITTED does not match NODE_STARTED.")
            if not isinstance(payload.get("node"), dict):
                raise JournalError("NODE_COMMITTED requires the complete node payload.")
            if payload.get("action") not in {"ACCEPT", "SPLIT", "UNRESOLVED"}:
                raise JournalError("NODE_COMMITTED action is invalid.")
            completed_nodes.append(payload)
            outstanding = None
        elif event == "SCHUR_ELIMINATION_COMMITTED":
            if outstanding is None or payload.get("node_id") != outstanding:
                raise JournalError(
                    "SCHUR_ELIMINATION_COMMITTED requires the active node."
                )
            if payload.get("expected_sign") not in {"POSITIVE", "NEGATIVE"}:
                raise JournalError("Schur event requires a certified sign.")
            if not isinstance(payload.get("original_labels"), list):
                raise JournalError("Schur event requires eliminated original labels.")
        elif event == "RECOVERY_STARTED":
            abandoned = payload.get("abandoned_node_id")
            if outstanding is None:
                if abandoned is not None:
                    raise JournalError("Recovery names a node that was not outstanding.")
            elif abandoned != outstanding:
                raise JournalError("Recovery must identify the interrupted node.")
            else:
                outstanding = None
        elif event == "SEGMENT_COMPLETED":
            if path_domain is None or outstanding is not None:
                raise JournalError("SEGMENT_COMPLETED requires path-domain and no active node.")
            completed = True
    return outstanding, path_domain, tuple(completed_nodes), completed


def replay_journal(
    directory: Path,
    *,
    expected_identity: dict[str, Any] | None = None,
    expected_attempt_id: str | None = None,
    expected_segment_id: str | None = None,
) -> JournalReplay:
    """Read and validate every committed record in an append-only journal."""

    directory = Path(directory)
    paths = _chunk_paths(directory)
    records: list[dict[str, Any]] = []
    chunks: list[ChunkEvidence] = []
    previous_record_hash: str | None = None
    attempt_id: str | None = expected_attempt_id
    segment_id: str | None = expected_segment_id
    identity: dict[str, Any] | None = expected_identity

    for chunk_index, path in enumerate(paths):
        raw = path.read_bytes()
        complete_part = raw
        torn_tail = b""
        if raw and not raw.endswith(b"\n"):
            boundary = raw.rfind(b"\n")
            complete_part = raw[:boundary + 1] if boundary >= 0 else b""
            torn_tail = raw[boundary + 1:]
        lines = complete_part.splitlines()
        chunk_records: list[dict[str, Any]] = []
        for line_number, line in enumerate(lines, start=1):
            try:
                record = json.loads(line)
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise JournalError(
                    f"Invalid complete JSON record {path.name}:{line_number}: {error}"
                ) from error
            if not isinstance(record, dict) or set(record) != _REQUIRED_KEYS:
                raise JournalError(f"Invalid record fields at {path.name}:{line_number}.")
            if record["schema_version"] != SCHEMA_VERSION:
                raise JournalError("Unsupported journal schema version.")
            if record["event_type"] not in _EVENT_TYPES:
                raise JournalError("Unknown journal event type.")
            if not isinstance(record["payload"], dict) or not isinstance(
                record["identity"], dict
            ):
                raise JournalError("Journal payload/identity must be objects.")
            if record["record_sha256"] != _record_hash(record):
                raise JournalError("Journal record hash mismatch.")
            if record["previous_record_sha256"] != previous_record_hash:
                raise JournalError("Journal hash chain mismatch.")
            if record["sequence"] != len(records):
                raise JournalError("Journal record sequence is noncontiguous.")
            if attempt_id is None:
                attempt_id = record["attempt_id"]
            if segment_id is None:
                segment_id = record["segment_id"]
            if identity is None:
                identity = record["identity"]
            if record["attempt_id"] != attempt_id or record["segment_id"] != segment_id:
                raise JournalError("Journal attempt/segment identity mismatch.")
            if record["identity"] != identity:
                raise JournalError("Frozen journal identity mismatch.")
            previous_record_hash = record["record_sha256"]
            records.append(record)
            chunk_records.append(record)

        tail_sha = _sha256(torn_tail) if torn_tail else None
        chunks.append(ChunkEvidence(
            path=str(path), sha256=_sha256(raw), size_bytes=len(raw),
            complete_record_count=len(chunk_records),
            torn_tail_size_bytes=len(torn_tail), torn_tail_sha256=tail_sha,
        ))
        if chunk_index > 0:
            if not chunk_records or chunk_records[0]["event_type"] != "RECOVERY_STARTED":
                raise JournalError("Every continuation chunk must start with RECOVERY_STARTED.")
            prior = chunks[chunk_index - 1]
            recovery = chunk_records[0]["payload"]
            expected = {
                "previous_chunk_sha256": prior.sha256,
                "previous_torn_tail_size_bytes": prior.torn_tail_size_bytes,
                "previous_torn_tail_sha256": prior.torn_tail_sha256,
            }
            for key, value in expected.items():
                if recovery.get(key) != value:
                    raise JournalError("Recovery chunk does not bind its predecessor.")

    outstanding, path_domain, completed_nodes, completed = _validate_state_machine(records)
    return JournalReplay(
        records=tuple(records), chunks=tuple(chunks),
        head_sha256=previous_record_hash, next_sequence=len(records),
        outstanding_node_id=outstanding, path_domain=path_domain,
        completed_nodes=completed_nodes, completed=completed,
    )


class DurableJournal:
    """Single-writer fsync-backed append handle for one JSONL chunk."""

    def __init__(
        self, directory: Path, *, attempt_id: str, segment_id: str,
        identity: dict[str, Any], resume: bool = False,
    ) -> None:
        if not attempt_id or not segment_id or not isinstance(identity, dict) or not identity:
            raise ValueError("attempt_id, segment_id, and nonempty identity are required")
        self.directory = Path(directory).resolve()
        self.directory.mkdir(parents=True, exist_ok=True)
        existing = replay_journal(
            self.directory, expected_identity=identity,
            expected_attempt_id=attempt_id, expected_segment_id=segment_id,
        )
        if existing.records and not resume:
            raise JournalError("Existing journal requires explicit resume=True.")
        if existing.completed:
            raise JournalError("A completed journal may not be resumed.")
        self.attempt_id = attempt_id
        self.segment_id = segment_id
        self.identity = dict(identity)
        self.sequence = existing.next_sequence
        self.previous_record_sha256 = existing.head_sha256
        self._records = list(existing.records)
        self._closed = False

        chunk_index = len(existing.chunks)
        self.path = self.directory / f"events-{chunk_index:06d}.jsonl"
        binary_flag = getattr(os, "O_BINARY", 0)
        self._fd = os.open(
            self.path, os.O_CREAT | os.O_EXCL | os.O_APPEND | os.O_WRONLY | binary_flag,
            0o600,
        )
        if existing.chunks:
            prior = existing.chunks[-1]
            self.append("RECOVERY_STARTED", {
                "previous_chunk_sha256": prior.sha256,
                "previous_torn_tail_size_bytes": prior.torn_tail_size_bytes,
                "previous_torn_tail_sha256": prior.torn_tail_sha256,
                "abandoned_node_id": existing.outstanding_node_id,
            })

    def append(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        if self._closed:
            raise JournalError("Cannot append to a closed journal.")
        if event_type not in _EVENT_TYPES or not isinstance(payload, dict):
            raise ValueError("Known event_type and object payload are required.")
        record = {
            "schema_version": SCHEMA_VERSION,
            "attempt_id": self.attempt_id,
            "segment_id": self.segment_id,
            "identity": self.identity,
            "sequence": self.sequence,
            "event_type": event_type,
            "previous_record_sha256": self.previous_record_sha256,
            "payload": payload,
        }
        record["record_sha256"] = _record_hash(record)
        # Reject a bad transition before it becomes durable evidence.
        _validate_state_machine([*self._records, record])
        encoded = _canonical(record) + b"\n"
        view = memoryview(encoded)
        while view:
            written = os.write(self._fd, view)
            if written <= 0:
                raise OSError("Journal append made no progress.")
            view = view[written:]
        os.fsync(self._fd)
        self.sequence += 1
        self.previous_record_sha256 = record["record_sha256"]
        self._records.append(record)
        return record

    def close(self) -> None:
        if not self._closed:
            os.close(self._fd)
            self._closed = True

    def __enter__(self) -> "DurableJournal":
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        self.close()
