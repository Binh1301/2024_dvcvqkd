"""Capture the locked CPU numerical environment without changing it."""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.metadata
import io
import json
import platform
from pathlib import Path
import subprocess
import sys

from _common import ROOT


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def run(output: Path) -> dict[str, object]:
    import mpmath
    import numpy
    import scipy
    import torch
    import yaml

    distributions = sorted(
        {
            distribution.metadata["Name"].lower(): distribution.version
            for distribution in importlib.metadata.distributions()
            if distribution.metadata.get("Name")
        }.items()
    )
    package_manifest = [{"name": name, "version": version} for name, version in distributions]
    numpy_config = io.StringIO()
    with contextlib.redirect_stdout(numpy_config):
        numpy.show_config()
    repository_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    payload: dict[str, object] = {
        "schema_version": "locked-cpu-environment-manifest-v1",
        "status": "CAPTURED_FROM_LOCKED_ENVIRONMENT",
        "python": {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "executable_role": "project_local_ignored_venv",
        },
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        },
        "numerical_packages": {
            "torch": torch.__version__,
            "numpy": numpy.__version__,
            "scipy": scipy.__version__,
            "mpmath": mpmath.__version__,
            "pyyaml": yaml.__version__,
        },
        "backend": {
            "device": "cpu",
            "default_real_dtype": "torch.float64",
            "default_complex_dtype": "torch.complex128",
            "torch_mkl_available": bool(torch.backends.mkl.is_available()),
            "torch_openmp_available": bool(torch.backends.openmp.is_available()),
            "torch_build_config": torch.__config__.show(),
            "numpy_build_config": numpy_config.getvalue(),
        },
        "package_manifest": package_manifest,
        "package_manifest_sha256": canonical_sha256(package_manifest),
        "provenance": {
            "repository_commit": repository_commit,
            "requirements_lock_sha256": sha256(ROOT / "requirements-publication.lock"),
            "producer_sha256": sha256(Path(__file__).resolve()),
            "final_model_spec_sha256": sha256(ROOT / "docs" / "FINAL_MODEL_SPEC.md"),
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output", type=Path, default=ROOT / "results" / "current_environment_manifest.json"
    )
    args = parser.parse_args()
    payload = run(args.output)
    print(json.dumps({
        "status": payload["status"],
        "package_manifest_sha256": payload["package_manifest_sha256"],
        "output": str(args.output),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
