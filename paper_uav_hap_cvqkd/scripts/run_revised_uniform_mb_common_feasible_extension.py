"""Run the diagnostic-only common-feasible distance extension.

This wrapper reuses the existing common-feasible runner and candidate cache.
It changes only the tested distance list and output directory; no source
moments, candidate generation, interpolation, or optimization is added.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import run_revised_uniform_mb_common_feasible_diagnostic as base


OUTPUT = ROOT / "results" / "revised_uniform_mb_common_feasible_extended_diagnostic"
DISTANCES_KM = (
    19.0,
    20.0,
    21.0,
    21.939310229205777,
    22.0,
    23.0,
    24.0,
    25.0,
    26.0,
    27.0,
    28.0,
    29.0,
    30.0,
    30.5,
    31.0,
    31.5,
    32.0,
    32.5,
    33.0,
    34.0,
    35.0,
    36.0,
    38.0,
    40.0,
    41.0,
    42.0,
    43.0,
    44.0,
    45.0,
    46.0,
    47.0,
    48.0,
    49.0,
    50.0,
    51.0,
    52.0,
    53.0,
    54.0,
    55.0,
    56.0,
    57.0,
    58.0,
    59.0,
    60.0,
    65.0,
    70.0,
    75.0,
    80.0,
    85.0,
    90.0,
    95.0,
    100.0,
    110.0,
    120.0,
    140.0,
    160.0,
    180.0,
    200.0,
    300.0,
    400.0,
    500.0,
    600.0,
    800.0,
    810.0,
    820.0,
    830.0,
    840.0,
    850.0,
    860.0,
    870.0,
    880.0,
    890.0,
    900.0,
    910.0,
    920.0,
    930.0,
    940.0,
    950.0,
    960.0,
    970.0,
    980.0,
    990.0,
    1000.0,
)
DENSE_NEAR_CROSSING_KM = tuple(float(distance) for distance in range(800, 1001, 10))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)

    base.DISTANCES_KM = DISTANCES_KM
    base.OUTPUT = output
    original_argv = sys.argv
    try:
        sys.argv = [str(Path(__file__).resolve()), "--output-dir", str(output)]
        status = base.main()
    finally:
        sys.argv = original_argv
    if status != 0:
        return status

    report_path = output / "revised_uniform_mb_common_feasible_report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report.update(
        {
            "status": "COMMON_FEASIBLE_UNIFORM_MB_DISTANCE_EXTENSION_COMPLETE_CACHE_ONLY",
            "distance_extension": {
                "previous_largest_tested_distance_km": 30.0,
                "extended_distances_km": [
                    distance for distance in DISTANCES_KM if distance > 30.0
                ],
                "largest_tested_distance_km": max(DISTANCES_KM),
                "dense_near_crossing_grid_used": list(DENSE_NEAR_CROSSING_KM),
            },
            "extension_runner_sha256": sha256(Path(__file__).resolve()),
            "base_runner_sha256": sha256(Path(base.__file__).resolve()),
            "no_new_source_moments": True,
            "no_new_candidate_generation": True,
            "no_interpolation_or_extrapolation": True,
        }
    )
    artifact_names = (
        "diagnostic_candidate_details.csv",
        "diagnostic_distance_envelope.csv",
        "protocol_summary.csv",
        "security_term_attribution.csv",
        "availability.csv",
        "excluded_candidates.csv",
        "channel_by_distance.csv",
        "diagnostic_skr_vs_distance.png",
        "diagnostic_skr_vs_distance.pdf",
        "diagnostic_beta_iab_vs_distance.png",
        "diagnostic_beta_iab_vs_distance.pdf",
        "diagnostic_chi_be_vs_distance.png",
        "diagnostic_chi_be_vs_distance.pdf",
    )
    report["extension_artifact_sha256"] = {
        name: sha256(output / name) for name in artifact_names
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
