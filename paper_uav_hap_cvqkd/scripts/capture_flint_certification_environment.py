"""Capture the isolated python-flint certification environment."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

import flint
import yaml

from _common import ROOT


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    output = ROOT / "results" / "certification_flint_environment.json"
    lock = ROOT / "requirements-certification-flint.lock"
    spec = ROOT / "docs" / "FINAL_MODEL_SPEC.md"
    artifact = {
        "schema_version": "certification-flint-environment-v1",
        "status": "CAPTURED_ISOLATED_VALIDATED_ARITHMETIC_ENVIRONMENT",
        "python": {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "executable_role": "project_local_ignored_certification_venv",
        },
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        },
        "validated_arithmetic": {
            "library": "python-flint",
            "python_flint_version": flint.__version__,
            "flint_version": flint.__FLINT_VERSION__,
            "real_ball_type": "arb",
            "complex_ball_type": "acb",
            "threads": int(flint.ctx.threads),
            "default_precision_bits": int(flint.ctx.prec),
            "wheel_filename": "python_flint-0.9.0-cp310-abi3-win_amd64.whl",
            "wheel_sha256": "8f1059536b7393e48b1444894c3b54ce1b961e4aa4a356e19217b26690f20db0",
            "configuration_parser": "PyYAML",
            "pyyaml_version": yaml.__version__,
            "pyyaml_wheel_sha256": "5fcd34e47f6e0b794d17de1b4ff496c00986e1c83f7ab2fb8fcfe9616ff7477b",
        },
        "lifecycle_guards": {
            "threshold_approved": False,
            "publication_training_performed": False,
            "final_test_accessed": False,
            "optimized_mb_grid_performed": False,
            "baseline_selection_performed": False,
        },
        "provenance": {
            "repository_commit": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            "worktree_dirty": bool(subprocess.check_output(
                ["git", "status", "--porcelain"], cwd=ROOT, text=True
            ).strip()),
            "producer_sha256": sha256(Path(__file__).resolve()),
            "dependency_lock_sha256": sha256(lock),
            "final_model_spec_sha256": sha256(spec),
            "python_hash_seed": os.environ.get("PYTHONHASHSEED"),
        },
    }
    output.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": artifact["status"], "output": str(output)}, sort_keys=True))


if __name__ == "__main__":
    main()
