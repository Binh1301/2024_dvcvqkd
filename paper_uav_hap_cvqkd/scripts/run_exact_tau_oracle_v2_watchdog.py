"""Hash-gated external watchdog for the frozen exact-tau V2 producer."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from _common import ROOT, load_yaml
from src.validation.certification_provenance_v2 import ProvenanceFailure, verify_freeze_manifest
from src.validation.hard_watchdog_v2 import run_with_hard_timeout


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--freeze-manifest", type=Path, required=True)
    parser.add_argument("--expected-freeze-manifest-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--watchdog-status", type=Path, required=True)
    args = parser.parse_args()
    try:
        verify_freeze_manifest(
            ROOT, args.freeze_manifest.resolve(),
            args.expected_freeze_manifest_sha256,
            require_clean_worktree=True,
        )
        settings = load_yaml(args.config.resolve())
    except (ProvenanceFailure, ValueError, OSError) as error:
        args.watchdog_status.parent.mkdir(parents=True, exist_ok=True)
        args.watchdog_status.write_text(json.dumps({
            "status": "PROVENANCE_FAILURE",
            "scientific_evaluation_started": False,
            "failure": str(error),
        }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"status": "PROVENANCE_FAILURE", "failure": str(error)}))
        return

    command = [
        sys.executable,
        str(ROOT / "scripts" / "certify_exact_tau_oracle_v2.py"),
        "--config", str(args.config.resolve()),
        "--output", str(args.output.resolve()),
        "--execute-frozen-real-fixtures",
    ]
    result = run_with_hard_timeout(
        command,
        cwd=ROOT,
        time_limit_seconds=float(settings["resources"]["maximum_exact_tau_oracle_seconds"]),
        kill_grace_seconds=float(settings["resources"]["kill_grace_seconds"]),
        fixture="four_frozen_exact_tau_oracles",
        interval="point_spectra",
        checkpoint_path=args.output.with_suffix(".checkpoint.json"),
        status_path=args.watchdog_status.resolve(),
    )
    print(json.dumps({"status": result["status"], "reason": result["reason"]}))


if __name__ == "__main__":
    main()
