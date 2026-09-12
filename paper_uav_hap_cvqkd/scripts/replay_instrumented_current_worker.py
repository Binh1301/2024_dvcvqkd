"""Run the current AP worker unchanged while collecting diagnostic hooks."""

from __future__ import annotations

import contextlib
import io
import argparse
import json
from pathlib import Path
import sys
import time

import mpmath as mp

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import full_support_c4_worker as worker


def _matrix_max_abs(matrix: mp.matrix) -> mp.mpf:
    return max(
        (abs(matrix[i, j]) for i in range(matrix.rows) for j in range(matrix.cols)),
        default=mp.mpf(0),
    )


def _matrix_fro(matrix: mp.matrix) -> mp.mpf:
    return mp.sqrt(
        mp.fsum(
            abs(matrix[i, j]) ** 2
            for i in range(matrix.rows)
            for j in range(matrix.cols)
        )
    )


def _relative_residual(left: mp.matrix, right: mp.matrix) -> mp.mpf:
    return _matrix_fro(left - right) / max(_matrix_fro(right), mp.mpf("1e-10000"))


def _trace(matrix: mp.matrix) -> mp.mpf:
    return mp.fsum(matrix[i, i] for i in range(matrix.rows)).real


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-artifact", type=Path)
    parser.add_argument("--mode", choices=("ps_va", "full"), default="ps_va")
    parser.add_argument("--digits", nargs="+", type=int, default=[800, 900])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.input_artifact is None:
        request = json.loads(sys.stdin.read())
    else:
        artifact = json.loads(args.input_artifact.read_text(encoding="utf-8"))
        request = artifact["cases"][args.mode]["frozen_input"]["request"]
    request["precision_ladder_decimal_digits"] = args.digits
    request_text = json.dumps(request, sort_keys=True)
    capture: dict[str, object] = {"rows": [], "solve_calls": []}
    current: dict[str, object] | None = None
    original_sectors = worker._sectors
    original_eighe = worker.mp.eighe
    original_solve = worker._lu_solve_matrix

    def sectors_hook(p, z):
        nonlocal current
        sectors = original_sectors(p, z)
        current = {
            "digits": int(mp.mp.dps),
            "sector_rows": [
                {
                    "sector": index,
                    "G_s": {
                        "status": "CONSTRUCTED",
                        "hermiticity_max_residual": str(
                            mp.nstr(
                                max(
                                    abs(matrix[i, j] - mp.conj(matrix[j, i]))
                                    for i in range(matrix.rows)
                                    for j in range(matrix.cols)
                                ),
                                30,
                            )
                        ),
                        "trace": str(mp.nstr(_trace(matrix), 50)),
                    },
                    "eigensolver": {"status": "PENDING"},
                }
                for index, matrix in enumerate(sectors)
            ],
        }
        capture["rows"].append(current)
        return sectors

    def eighe_hook(matrix, *args, **kwargs):
        values, vectors = original_eighe(matrix, *args, **kwargs)
        if current is not None:
            sector = next(
                row for row in current["sector_rows"]
                if row["eigensolver"]["status"] == "PENDING"
            )
            local = [mp.re(values[i]) for i in range(values.rows)]
            diagonal = mp.diag(local)
            reconstruction = vectors * diagonal * vectors.H
            orthogonality = vectors.H * vectors
            sector["eigensolver"] = {
                "status": "COMPLETED",
                "minimum_eigenvalue": mp.nstr(min(local), 50),
                "maximum_eigenvalue": mp.nstr(max(local), 50),
                "positive_count": sum(value > 0 for value in local),
                "nonpositive_count": sum(value <= 0 for value in local),
                "reconstruction_relative_residual": mp.nstr(
                    _relative_residual(reconstruction, matrix),
                    30,
                ),
                "orthogonality_relative_residual": mp.nstr(
                    _relative_residual(orthogonality, mp.eye(64)),
                    30,
                ),
            }
            if all(value > 0 for value in local):
                square_root = vectors * mp.diag([mp.sqrt(value) for value in local]) * vectors.H
                inverse_square_root = vectors * mp.diag([1 / mp.sqrt(value) for value in local]) * vectors.H
                sector["sqrt_inverse_sqrt"] = {
                    "sqrt_residual": mp.nstr(
                        _relative_residual(square_root * square_root, matrix),
                        30,
                    ),
                    "inverse_sqrt_residual": mp.nstr(
                        _relative_residual(
                            inverse_square_root * matrix * inverse_square_root,
                            mp.eye(64),
                        ),
                        30,
                    ),
                }
        return values, vectors

    def solve_hook(A, B):
        started = time.perf_counter()
        solved = original_solve(A, B)
        residual = A * solved - B
        call = {
            "digits": int(mp.mp.dps),
            "runtime_seconds": time.perf_counter() - started,
            "relative_residual": mp.nstr(
                _matrix_max_abs(residual) / max(_matrix_max_abs(B), mp.mpf("1e-10000")),
                30,
            ),
        }
        capture["solve_calls"].append(call)
        if current is not None:
            current.setdefault("solve_calls", []).append(call)
        return solved

    worker._sectors = sectors_hook
    worker.mp.eighe = eighe_hook
    worker._lu_solve_matrix = solve_hook
    output = io.StringIO()
    started = time.perf_counter()
    try:
        if len(args.digits) == 1:
            # The production CLI requires two rows for its convergence check.
            # For the frozen diagnostic-only first rung, call the same _row
            # implementation directly and leave the production worker intact.
            p = [
                mp.mpf(float.fromhex(value))
                for value in request["probabilities_float64_hex"]
            ]
            z = [
                mp.mpc(float.fromhex(real), float.fromhex(imaginary))
                for real, imaginary in request["prototypes_float64_hex"]
            ]
            payload = {
                "status": "DIAGNOSTIC_ONLY",
                "rows": [worker._row(p, z, int(args.digits[0]))],
            }
        else:
            sys.stdin = io.StringIO(request_text)
            with contextlib.redirect_stdout(output):
                worker.main()
            payload = json.loads(output.getvalue())
    finally:
        worker._sectors = original_sectors
        worker.mp.eighe = original_eighe
        worker._lu_solve_matrix = original_solve
    payload["instrumentation"] = capture
    payload["instrumentation_runtime_seconds"] = time.perf_counter() - started
    rendered = json.dumps(payload, indent=2)
    if args.output is None:
        print(rendered)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
        print(json.dumps({"status": payload["status"], "output": str(args.output)}))


if __name__ == "__main__":
    main()
