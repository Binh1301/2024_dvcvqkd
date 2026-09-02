"""Reproduce fixed-reference peak certification without training or test data."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from _common import ROOT, load_yaml
from src.validation.physical_domain import amplitude_domain_certification


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "default.yaml")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "results" / "amplitude_domain_certification.json",
    )
    args = parser.parse_args()
    config_path = args.config.resolve()
    report = amplitude_domain_certification(load_yaml(config_path))
    report["provenance"] = {
        "config_path": str(config_path.relative_to(ROOT)),
        "config_sha256": hashlib.sha256(config_path.read_bytes()).hexdigest(),
        "generator": "scripts/certify_amplitude_domain.py",
    }
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote amplitude-domain certification to {output}")
    return 0 if report["status"].startswith("PASS_") else 2


if __name__ == "__main__":
    raise SystemExit(main())
