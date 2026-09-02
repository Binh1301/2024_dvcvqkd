"""Isolated FLINT worker for one serialized realized physical ensemble."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import flint
import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.validation.realized_point_certifier import certify_final_ensemble_point


def _decode_complex(values):
    return [complex(float.fromhex(row[0]), float.fromhex(row[1])) for row in values]


def main() -> int:
    request = json.load(sys.stdin)
    if sys.version_info[:3] != (3, 12, 10):
        raise RuntimeError(f"worker requires CPython 3.12.10, got {sys.version_info[:3]}")
    if flint.__version__ != "0.9.0" or flint.__FLINT_VERSION__ != "3.6.0":
        raise RuntimeError("worker FLINT version does not match the frozen environment")
    if yaml.__version__ != "6.0.3":
        raise RuntimeError("worker PyYAML version does not match the frozen environment")
    result = certify_final_ensemble_point(
        [float.fromhex(value) for value in request["probabilities_float64_hex"]],
        _decode_complex(request["amplitudes_float64_hex"]),
        tau_float64_hex=request["tau_float64_hex"],
        precision_bits=tuple(int(value) for value in request.get("precision_bits", (160, 256, 384, 512))),
        bracket_denominator_power_two=int(request.get("bracket_denominator_power_two", 48)),
        maximum_bracket_expansions=int(request.get("maximum_bracket_expansions", 8)),
        maximum_seconds_per_inertia=float(request.get("maximum_seconds_per_inertia", 120.0)),
        protocol_version=str(request.get("protocol_version", "pointwise-guard-v1")),
    )
    json.dump(result, sys.stdout, sort_keys=True, separators=(",", ":"))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
