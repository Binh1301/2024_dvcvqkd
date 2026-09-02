"""Select fixed VA for PS, GS, and PS+GS from validation-only run records."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from _common import ROOT, load_yaml, missing_required, require_holevo_pseudoinverse_approval
from src.optimization.learned_outer_selection import (
    validation_only_learned_fixed_va_selection,
)
from src.validation.physical_domain import (
    approved_peak_photon_limit, require_preconvergence_domain_ready,
)


REQUIRED = [
    "cvqkd.v_min_snu", "cvqkd.v_max_snu", "cvqkd.v_a_budget_snu",
    "cvqkd.n_peak_photons", "cvqkd.peak_domain_scope",
    "baseline_search.va_grid_snu", "training.independent_training_initialization_seeds",
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "default.yaml")
    parser.add_argument("--records", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    config = load_yaml(args.config.resolve())
    missing = missing_required(config, REQUIRED)
    if missing:
        raise ValueError("Unresolved required configuration: " + ", ".join(missing))
    records = [json.loads(path.read_text(encoding="utf-8")) for path in args.records]
    cvqkd = config["cvqkd"]
    n_peak = approved_peak_photon_limit(config)
    require_preconvergence_domain_ready(config)
    require_holevo_pseudoinverse_approval(config)
    selections = validation_only_learned_fixed_va_selection(
        records,
        va_grid=config["baseline_search"]["va_grid_snu"],
        v_min=float(cvqkd["v_min_snu"]),
        v_max=float(cvqkd["v_max_snu"]),
        va_budget=float(cvqkd["v_a_budget_snu"]),
        initialization_seeds=config["training"]["independent_training_initialization_seeds"],
    )
    payload = {
        "status": "validation-only learned fixed-VA selection; no test access",
        "test_set_used": False,
        "n_peak_photons": n_peak,
        "all_selected_checkpoints_peak_feasible": True,
        "selections": {name: value.as_dict() for name, value in selections.items()},
    }
    args.output.resolve().parent.mkdir(parents=True, exist_ok=True)
    args.output.resolve().write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
