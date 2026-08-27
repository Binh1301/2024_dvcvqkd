"""Noncertifying Poisson-tail prescreen for the 30-photon peak boundary."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from scipy.stats import poisson

from _common import ROOT, load_yaml


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "default.yaml")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "results" / "fock_poisson_prescreen.json")
    args = parser.parse_args()
    config = load_yaml(args.config.resolve())
    mean = float(config["cvqkd"]["n_peak_photons"])
    candidates = (48, 56, 64, 72, 80, 96, 112, 128)
    rows = [{
        "fock_cutoff": cutoff,
        "tail_definition": "P(N_photon >= fock_cutoff | Poisson(mean=30))",
        "tail_probability": float(poisson.sf(cutoff - 1, mean)),
        "retained_probability": float(poisson.cdf(cutoff - 1, mean)),
    } for cutoff in candidates]
    payload = {
        "schema_version": "fock-poisson-prescreen-v1",
        "status": "NONCERTIFYING_PRESCREEN_ONLY",
        "is_fock_cutoff_certification": False,
        "test_set_used": False,
        "mean_photon_number": mean,
        "hard_peak_domain_photons": mean,
        "rows": rows,
        "explicit_limitation": (
            "Poisson tails prioritize staged cutoffs only; they do not certify "
            "C, w, Z, symplectic eigenvalues, chi_BE, or raw K."
        ),
    }
    args.output.resolve().parent.mkdir(parents=True, exist_ok=True)
    args.output.resolve().write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
