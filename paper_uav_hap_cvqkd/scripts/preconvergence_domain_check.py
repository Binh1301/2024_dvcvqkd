"""Write the physical-domain precheck; never certify a Fock cutoff."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from _common import ROOT, load_yaml
from src.validation.physical_domain import preconvergence_domain_report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "default.yaml")
    parser.add_argument(
        "--output", type=Path,
        default=ROOT / "results" / "preconvergence_domain_report.json",
    )
    args = parser.parse_args()
    report = preconvergence_domain_report(load_yaml(args.config.resolve()))
    args.output.resolve().parent.mkdir(parents=True, exist_ok=True)
    args.output.resolve().write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote non-certifying physical-domain report to {args.output.resolve()}")
    return 0 if report["status"] == "READY_FOR_CONVERGENCE_EXECUTION" else 2


if __name__ == "__main__":
    raise SystemExit(main())
