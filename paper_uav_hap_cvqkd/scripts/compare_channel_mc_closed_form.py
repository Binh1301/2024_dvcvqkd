"""Compare channel Monte Carlo moments with deterministic quadrature moments."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from calculate_channel_pdf_and_moments import (
    analyze_product,
    derive_physical_inputs,
    primitive_monte_carlo,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "results" / "monte_carlo_closed_form_check.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tau-zen", type=float, default=0.92)
    parser.add_argument("--sample-count", type=int, default=1_000_000)
    parser.add_argument("--seed", type=int, default=202612)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    if args.sample_count <= 0:
        parser.error("--sample-count must be positive")

    physical = derive_physical_inputs(args.tau_zen)
    quadrature = analyze_product(physical["v_sc"], physical)["moments"]
    monte_carlo = primitive_monte_carlo(
        physical["v_sc"], physical, args.sample_count, args.seed
    )
    result = {
        "status": "DIAGNOSTIC_MONTE_CARLO_VS_QUADRATURE",
        "production_use": False,
        "tau_zen": args.tau_zen,
        "sample_count": args.sample_count,
        "seed": args.seed,
        "quadrature": {
            "mean_eta": quadrature["mean_eta"],
            "mean_sqrt_eta": quadrature["mean_sqrt_eta"],
            "T_eff": quadrature["mean_sqrt_eta"] ** 2,
            "mean_eta_xi_eta": quadrature["mean_eta_xi_eta"],
        },
        "monte_carlo": {
            key: monte_carlo[key]
            for key in (
                "mean_eta", "mean_eta_standard_error", "mean_sqrt_eta",
                "mean_sqrt_eta_standard_error", "mean_eta_xi_eta",
                "mean_eta_xi_eta_standard_error", "p_in", "p_out",
                "p_X_gt_1", "above_one_count", "valid_active_count",
            )
        },
    }
    mc_t_eff = monte_carlo["mean_sqrt_eta"] ** 2
    result["comparison"] = {
        "mean_eta_difference": monte_carlo["mean_eta"] - quadrature["mean_eta"],
        "mean_eta_z": (monte_carlo["mean_eta"] - quadrature["mean_eta"])
        / monte_carlo["mean_eta_standard_error"],
        "mean_sqrt_eta_difference": monte_carlo["mean_sqrt_eta"] - quadrature["mean_sqrt_eta"],
        "mean_sqrt_eta_z": (monte_carlo["mean_sqrt_eta"] - quadrature["mean_sqrt_eta"])
        / monte_carlo["mean_sqrt_eta_standard_error"],
        "T_eff_mc": mc_t_eff,
        "T_eff_difference": mc_t_eff - quadrature["mean_sqrt_eta"] ** 2,
        "T_eff_relative_percent": 100.0 * (mc_t_eff / (quadrature["mean_sqrt_eta"] ** 2) - 1.0),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
