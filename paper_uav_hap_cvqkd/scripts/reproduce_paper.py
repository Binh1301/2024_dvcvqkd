"""Validate whether the draft contains enough information for reproduction."""

from __future__ import annotations

import argparse
from pathlib import Path

from _common import REPRODUCTION_REQUIRED, ROOT, load_yaml, missing_required


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "default.yaml")
    args = parser.parse_args()
    try:
        config = load_yaml(args.config.resolve())
    except RuntimeError as error:
        print(f"Environment validation is BLOCKED: {error}")
        print("Scientific reproduction is also blocked because paper Sections V-VI contain no numerical results.")
        return 2
    missing = missing_required(config, REPRODUCTION_REQUIRED)
    expected_figures = config.get("paper_results", {}).get("expected_figures", [])
    if missing or not expected_figures:
        print("Paper reproduction is intentionally BLOCKED.")
        if missing:
            print("Unspecified numerical parameters:")
            for path in missing:
                print(f"  - {path}")
        if not expected_figures:
            print("  - Paper Section V specifies no numerical figures/results to reproduce.")
        print("Supply author-approved values; do not substitute July legacy results.")
        return 2
    print("Configuration is numerically complete, but figure mappings still require author approval.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
