"""Capture the isolated environment for shifted-inertia certification v1."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import platform
import subprocess

import flint
import numpy
import yaml

from _common import ROOT


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    output = ROOT / "results" / "shifted_inertia_environment_v1.json"
    lock = ROOT / "requirements-certification-inertia.lock"
    artifact = {
        "schema_version": "shifted-inertia-environment-v1",
        "status": "CAPTURED_CERTIFICATION_ONLY_ENVIRONMENT",
        "python": {"version": platform.python_version(), "implementation": platform.python_implementation()},
        "platform": {"system": platform.system(), "release": platform.release(), "machine": platform.machine()},
        "validated_arithmetic": {
            "library": "python-flint",
            "python_flint_version": flint.__version__,
            "flint_version": flint.__FLINT_VERSION__,
            "threads": int(flint.ctx.threads),
            "proof_types": ["arb", "acb"],
        },
        "diagnostic_only": {
            "library": "numpy",
            "version": numpy.__version__,
            "role": "complex128 comparison only; never a proof decision",
        },
        "configuration_parser": {"library": "PyYAML", "version": yaml.__version__},
        "wheel_sha256": {
            "python_flint": "8f1059536b7393e48b1444894c3b54ce1b961e4aa4a356e19217b26690f20db0",
            "pyyaml": "5fcd34e47f6e0b794d17de1b4ff496c00986e1c83f7ab2fb8fcfe9616ff7477b",
            "numpy": "28ac63476ec7651484215ee7fa15a1f78b57c14621f01e392afe17b9a1390ce4",
        },
        "lifecycle_guards": {
            "threshold_approved": False,
            "publication_training_performed": False,
            "final_test_accessed": False,
            "optimized_mb_grid_performed": False,
            "baseline_selection_performed": False,
        },
        "provenance": {
            "repository_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "producer_sha256": sha256(Path(__file__).resolve()),
            "dependency_lock_sha256": sha256(lock),
            "final_model_spec_sha256": sha256(ROOT / "docs" / "FINAL_MODEL_SPEC.md"),
        },
    }
    output.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": artifact["status"], "output": str(output)}, sort_keys=True))


if __name__ == "__main__":
    main()
