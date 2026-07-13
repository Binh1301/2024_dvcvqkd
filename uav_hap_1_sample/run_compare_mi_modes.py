"""Compare legacy Gaussian and discrete-input MI with common random numbers."""

from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path

import torch

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from uav_hap_1_sample.config import (
        QAM_ALPHA0_BINOMIAL,
        QAM_ALPHA0_MB,
        QAM_ALPHA0_UNIFORM,
        QAM_BETA,
        QAM_EPS,
        QAM_ETA,
        QAM_NCUT_BINOMIAL,
        QAM_NCUT_MB,
        QAM_NCUT_UNIFORM,
        QAM_NU_TILDE,
        QAM_V_EL,
    )
    from uav_hap_1_sample.protocol.qam_protocol import (
        build_state_binomial,
        build_state_mb,
        build_state_uniform,
        compute_metrics,
    )
else:
    from .config import (
        QAM_ALPHA0_BINOMIAL,
        QAM_ALPHA0_MB,
        QAM_ALPHA0_UNIFORM,
        QAM_BETA,
        QAM_EPS,
        QAM_ETA,
        QAM_NCUT_BINOMIAL,
        QAM_NCUT_MB,
        QAM_NCUT_UNIFORM,
        QAM_NU_TILDE,
        QAM_V_EL,
    )
    from .protocol.qam_protocol import (
        build_state_binomial,
        build_state_mb,
        build_state_uniform,
        compute_metrics,
    )


FIELDNAMES = (
    "distribution",
    "T",
    "I_legacy",
    "I_discrete",
    "absolute_difference",
    "relative_difference",
    "H_X",
    "chi_BE",
    "K_legacy",
    "K_discrete",
)


def _states(distribution: str):
    states = {
        "uniform": build_state_uniform(QAM_ALPHA0_UNIFORM, QAM_NCUT_UNIFORM),
        "binomial": build_state_binomial(QAM_ALPHA0_BINOMIAL, QAM_NCUT_BINOMIAL),
        "mb": build_state_mb(QAM_ALPHA0_MB, QAM_NCUT_MB, QAM_NU_TILDE),
    }
    return states if distribution == "all" else {distribution: states[distribution]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--distribution", choices=("all", "uniform", "binomial", "mb"), default="all")
    parser.add_argument("--noise-samples", type=int, default=128)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parent / "output" / "mi_mode_comparison.csv",
    )
    args = parser.parse_args()

    transmittance_grid = (1e-4, 1e-3, 1e-2, 5e-2, 0.1, 0.2, 0.5, 1.0)
    rows: list[dict[str, float | str]] = []
    for label, state in _states(args.distribution).items():
        for transmittance in transmittance_grid:
            legacy = compute_metrics(
                state,
                transmittance,
                QAM_EPS,
                QAM_BETA,
                QAM_ETA,
                QAM_V_EL,
                mi_mode="legacy_gaussian",
            )
            # Resetting the generator reuses the same standardized AWGN for
            # every distribution and T value in this comparison.
            generator = torch.Generator().manual_seed(args.seed)
            discrete = compute_metrics(
                state,
                transmittance,
                QAM_EPS,
                QAM_BETA,
                QAM_ETA,
                QAM_V_EL,
                mi_mode="discrete",
                noise_samples_per_symbol=args.noise_samples,
                generator=generator,
            )
            difference = discrete.i_ab - legacy.i_ab
            rows.append(
                {
                    "distribution": label,
                    "T": transmittance,
                    "I_legacy": legacy.i_ab,
                    "I_discrete": discrete.i_ab,
                    "absolute_difference": abs(difference),
                    "relative_difference": abs(difference) / max(abs(legacy.i_ab), 1e-300),
                    "H_X": discrete.h_x,
                    "chi_BE": discrete.chi_be,
                    "K_legacy": legacy.skr_raw,
                    "K_discrete": discrete.skr_raw,
                }
            )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    print("distribution        T     I_legacy   I_discrete       |diff|       H(X)   K_discrete")
    for row in rows:
        print(
            f"{row['distribution']:<12} {row['T']:8.4g} "
            f"{row['I_legacy']:12.6f} {row['I_discrete']:12.6f} "
            f"{row['absolute_difference']:12.6f} {row['H_X']:10.6f} "
            f"{row['K_discrete']:12.6f}"
        )
    print(f"Saved {len(rows)} rows to {args.output}")


if __name__ == "__main__":
    main()
