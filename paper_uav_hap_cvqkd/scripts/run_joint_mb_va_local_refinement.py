"""Exact local joint MB/V_A refinement around the best coarse region."""

from __future__ import annotations

import csv
import json
from pathlib import Path
import sys

import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts._common import load_yaml
from scripts.run_exact_mb_test2 import ExactMBEvaluator, channel_fixture
from scripts.run_joint_mb_va_optimization import evaluate


OUTPUT = ROOT / "results" / "joint_mb_va"
POINTS = tuple(
    [(0.20, value) for value in (1.90, 1.95, 2.00, 2.05, 2.10)]
    + [(value, 2.00) for value in (0.18, 0.19, 0.20, 0.21, 0.22, 0.23, 0.24)]
    + [(0.22, value) for value in (1.90, 1.925, 1.95, 1.975, 2.05)]
    + [(value, 1.95) for value in (0.21, 0.23)]
    + [(0.23, value) for value in (1.90, 1.925, 1.975)]
    + [(0.24, 1.95)]
    + [(0.25, value) for value in (1.925, 1.95, 1.975)]
    + [(0.24, 1.925), (0.24, 1.975)]
)


def main() -> int:
    torch.set_num_threads(1)
    config = load_yaml(ROOT / "configs" / "default.yaml")
    channel = channel_fixture()
    evaluator = ExactMBEvaluator(
        config, channel, OUTPUT, source_cache_dir=ROOT / "results" / "exact_mb_test2" / "exact_source_cache"
    )
    evaluator.prepare_sources(list(POINTS), workers=4)
    rows = [evaluate(config, channel, evaluator, nu, va) for nu, va in POINTS]
    rows.sort(key=lambda row: row["SKR"], reverse=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with (OUTPUT / "local_refinement.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted({key for row in rows for key in row}), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    (OUTPUT / "local_refinement.json").write_text(
        json.dumps({"status": "LOCAL_EXACT_REFINEMENT_COMPLETE", "rows": rows}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": "LOCAL_EXACT_REFINEMENT_COMPLETE", "best": rows[0], "rows": rows}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
