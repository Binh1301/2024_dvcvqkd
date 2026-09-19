"""Exact-binary64 arbitrary-precision full-support C4 source-moment worker."""

from __future__ import annotations

import json
import hashlib
import math
import os
from pathlib import Path
import sys
import time

import mpmath as mp


def _lu_solve_matrix(A, B):
    """Solve A X = B column-by-column using arbitrary precision."""
    X = mp.matrix(A.rows, B.cols)

    for j in range(B.cols):
        rhs_col = mp.matrix([B[i, j] for i in range(B.rows)])
        sol_col = mp.lu_solve(A, rhs_col)

        for i in range(A.rows):
            X[i, j] = sol_col[i]

    return X


def _right_solve_matrix(matrix, rhs):
    """Solve ``X @ matrix = rhs`` using a conjugate-transpose left solve."""

    return _lu_solve_matrix(matrix.H, rhs.H).H


def _residual(actual, expected):
    return mp.norm(actual - expected) / max(mp.mpf(1), mp.norm(expected))


def _power_diagonal(values, exponent):
    return mp.diag([value ** exponent for value in values])


def _sector_diagnostic(values):
    minimum = min(values)
    maximum = max(values)
    kappa = mp.inf if minimum <= 0 else maximum / minimum
    return {
        "eigenvalues": [mp.nstr(value, 50) for value in values],
        "lambda_min": mp.nstr(minimum, 50),
        "lambda_max": mp.nstr(maximum, 50),
        "rank": sum(value > 0 for value in values),
        "kappa": mp.nstr(kappa, 50),
        "log10_kappa": None if kappa <= 0 else mp.nstr(mp.log10(kappa), 50),
    }


def rows_converged(rows):
    if len(rows) < 2:
        return False
    final = rows[-2:]
    if not all(
        row.get("resolved") is True
        and row.get("rank") == 256
        and row.get("C_consistent") is True
        and row.get("w_consistent") is True
        for row in final
    ):
        return False
    return all(
        abs(mp.mpf(final[0][name]) - mp.mpf(final[1][name]))
        <= mp.mpf("1e-7") + mp.mpf("1e-6") * max(
            abs(mp.mpf(final[0][name])), abs(mp.mpf(final[1][name]))
        )
        for name in ("C", "w")
    )


def next_precision_digits(current_digits, row, minimum_step=128, condition_guard_digits=64):
    current_digits = int(current_digits)
    minimum_step = int(minimum_step)
    if minimum_step < 128:
        raise ValueError("minimum_step must be at least 128 decimal digits")
    if condition_guard_digits < 0:
        raise ValueError("condition_guard_digits must be nonnegative")
    if not row.get("resolved"):
        return current_digits + minimum_step
    kappa_max = max(mp.mpf(item["kappa"]) for item in row["sector_diagnostics"])
    return max(
        current_digits + minimum_step,
        int(mp.ceil(mp.log10(kappa_max))) + int(condition_guard_digits),
    )


def _json_sha256(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _write_checkpoint(path, input_hashes, precision_policy_sha256, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "c4-ap-source-moments-checkpoint-v1",
        "input_hashes": input_hashes,
        "precision_policy_sha256": precision_policy_sha256,
        "rows": rows,
    }
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _sectors(p, z):
    blocks = []

    for d in range(4):
        r = mp.j ** d

        blocks.append(
            mp.matrix(
                [
                    [
                        mp.sqrt(p[i] * p[j])
                        * mp.exp(
                            -(
                                abs(z[i]) ** 2
                                + abs(r * z[j]) ** 2
                            )
                            / 2
                            + mp.conj(z[i]) * r * z[j]
                        )
                        for j in range(64)
                    ]
                    for i in range(64)
                ]
            )
        )

    answer = []

    for s in range(4):
        x = mp.zeros(64)

        for d in range(4):
            x += blocks[d] * mp.j ** (s * d)

        answer.append((x + x.H) / 2)

    return answer


def _row(p, z, digits, diagnostic_thresholds):
    with mp.workdps(digits):
        row_started = time.perf_counter()
        sector_started = time.perf_counter()
        sector_matrices = _sectors(p, z)
        t_sector_build = time.perf_counter() - sector_started
        values = []
        vectors = []
        sector_diagnostics = []

        eig_started = time.perf_counter()
        for g in sector_matrices:
            v, u = mp.eighe(g)
            sector_values = [mp.re(v[i]) for i in range(64)]
            values.append(sector_values)
            vectors.append(u)
            sector_diagnostics.append(_sector_diagnostic(sector_values))
        t_eig = time.perf_counter() - eig_started

        all_eigenvalues = [value for sector in values for value in sector]
        rank = sum(value > 0 for value in all_eigenvalues)
        minimum_eigenvalue = min(all_eigenvalues)
        diagnostic_counts = {
            label: sum(value <= threshold for value in all_eigenvalues)
            for label, threshold in diagnostic_thresholds
        }
        base = {
            "digits": digits,
            "rank": rank,
            "resolved": rank == 256,
            "exact_resolved_rank": rank,
            "minimum_eigenvalue": mp.nstr(minimum_eigenvalue, 50),
            "eigenvalues_at_or_below_diagnostic_threshold": diagnostic_counts,
            "sector_diagnostics": sector_diagnostics,
            "runtime": {
                "t_gram": t_sector_build,
                "t_sector_build": t_sector_build,
                "t_eig": t_eig,
                "t_roots": 0.0,
                "t_solve": 0.0,
                "t_C": 0.0,
                "t_w": 0.0,
                "t_total": time.perf_counter() - row_started,
            },
        }
        if rank != 256:
            return base

        a = []
        q = []
        c_positive = mp.mpf(0)
        c_trace = mp.mpf(0)
        right_solve_residuals = []
        matrix_function_residuals = []
        t_roots = 0.0
        t_solve = 0.0
        t_c = 0.0
        for s in range(4):
            previous = (s - 1) % 4
            m = vectors[s].H * mp.diag(z) * vectors[previous]
            gs = mp.diag(values[s])
            gr = mp.diag(values[previous])
            roots_started = time.perf_counter()
            hs = _power_diagonal(values[s], mp.mpf("0.5"))
            hr = _power_diagonal(values[previous], mp.mpf("0.5"))
            gs_threequarter = _power_diagonal(values[s], mp.mpf("0.75"))
            gr_quarter = _power_diagonal(values[previous], mp.mpf("0.25"))
            t_roots += time.perf_counter() - roots_started

            # Keep the historical worker names: b=S_sr and aa=A_sr.
            solve_started = time.perf_counter()
            b = _right_solve_matrix(hr, hs * m)
            x2 = _right_solve_matrix(gr, gs * m).T
            aa = x2.T
            t_solve += time.perf_counter() - solve_started
            a.append(aa)
            right_solve_residuals.extend((
                _residual(b * hr, hs * m),
                _residual(aa * gr, gs * m),
            ))
            matrix_function_residuals.extend((
                _residual(hs * hs, gs),
                _residual(gr_quarter * gr_quarter, hr),
            ))

            c_started = time.perf_counter()
            x_positive = _right_solve_matrix(
                gr_quarter, gs_threequarter * m
            )
            c_positive += mp.fsum(
                abs(x_positive[i, j]) ** 2
                for i in range(64)
                for j in range(64)
            )
            cb = hs * b * hr * b.H
            c_trace += mp.fsum(cb[i, i] for i in range(64)).real
            t_c += time.perf_counter() - c_started
            q.append(
                hs * vectors[s].H
                * mp.diag([1 / (2 * mp.sqrt(x)) for x in p])
            )

        t = [a[s] * q[(s - 1) % 4] for s in range(4)]
        d = [
            mp.fsum(
                mp.conj(q[s][i, k]) * t[s][i, k]
                for s in range(4) for i in range(64)
            )
            for k in range(64)
        ]
        w_started = time.perf_counter()
        residual_contributions = [
            4 * mp.fsum(
                p[k] * mp.fsum(
                    abs(t[s][i, k] - q[s][i, k] * d[k]) ** 2
                    for i in range(64)
                )
                for k in range(64)
            )
            for s in range(4)
        ]
        w_residual = mp.fsum(residual_contributions)
        a_w = mp.mpf(0)
        for s in range(4):
            a_times_half = a[s] * _power_diagonal(
                values[(s - 1) % 4], mp.mpf("0.5")
            )
            a_w += mp.fsum(
                abs(a_times_half[i, j]) ** 2
                for i in range(64) for j in range(64)
            )
        b_w = mp.fsum(4 * p[k] * abs(d[k]) ** 2 for k in range(64))
        w_diff = a_w - b_w
        t_w = time.perf_counter() - w_started
        c_difference = c_positive - c_trace
        c_tolerance = mp.mpf("1e-7") + mp.mpf("1e-6") * max(abs(c_positive), abs(c_trace))
        w_tolerance = mp.mpf("1e-7") + mp.mpf("1e-6") * max(abs(w_residual), abs(w_diff))
        cancellation = (
            -mp.log10(abs(w_residual / a_w))
            if a_w > 0 and w_residual > 0 else None
        )
        base.update({
            "C": mp.nstr(c_positive, 50),
            "C_positive": mp.nstr(c_positive, 50),
            "C_trace": mp.nstr(c_trace, 50),
            "C_difference": mp.nstr(c_difference, 50),
            "w": mp.nstr(w_residual, 50),
            "w_residual": mp.nstr(w_residual, 50),
            "w_diff": mp.nstr(w_diff, 50),
            "A_w": mp.nstr(a_w, 50),
            "B_w": mp.nstr(b_w, 50),
            "cancellation_digits": None if cancellation is None else mp.nstr(cancellation, 50),
            "right_solve_residual_max": mp.nstr(max(right_solve_residuals), 50),
            "matrix_function_residual_max": mp.nstr(max(matrix_function_residuals), 50),
            "residual_contributions": [mp.nstr(value, 50) for value in residual_contributions],
            "orbit_sector_residual": [mp.nstr(value, 50) for value in residual_contributions],
            "C_consistent": abs(c_difference) <= c_tolerance,
            "w_consistent": abs(w_diff - w_residual) <= w_tolerance,
        })
        base["runtime"] = {
            "t_gram": t_sector_build,
            "t_sector_build": t_sector_build,
            "t_eig": t_eig,
            "t_roots": t_roots,
            "t_solve": t_solve,
            "t_C": t_c,
            "t_w": t_w,
            "t_total": time.perf_counter() - row_started,
        }
        return base


def main():
    request = json.load(sys.stdin)

    p = [
        mp.mpf(float.fromhex(x))
        for x in request["probabilities_float64_hex"]
    ]

    z = [
        mp.mpc(
            float.fromhex(x),
            float.fromhex(y),
        )
        for x, y in request["prototypes_float64_hex"]
    ]

    diagnostic_thresholds = [
        (value, mp.mpf(float.fromhex(value)))
        for value in request.get("diagnostic_eigenvalue_thresholds", [])
    ]
    input_hashes = request.get("input_hashes", {})
    precision_policy = {
        "initial_precision_digits": int(request.get("initial_precision_digits", 256)),
        "minimum_precision_step": int(request.get("minimum_precision_step", 128)),
        "condition_guard_digits": int(request.get("condition_guard_digits", 64)),
        "max_precision_digits": request.get("max_precision_digits"),
    }
    precision_policy_sha256 = request.get("precision_policy_sha256") or _json_sha256(
        precision_policy
    )
    checkpoint_path = request.get("checkpoint_path")
    rows = []
    if checkpoint_path and Path(checkpoint_path).exists():
        checkpoint = json.loads(Path(checkpoint_path).read_text(encoding="utf-8"))
        if (
            checkpoint.get("input_hashes") != input_hashes
            or checkpoint.get("precision_policy_sha256") != precision_policy_sha256
        ):
            raise ValueError("AP checkpoint hashes do not match the current request")
        rows = checkpoint.get("rows", [])
        if not isinstance(rows, list):
            raise ValueError("AP checkpoint rows must be a list")
        if rows and not all(
            row.get("pmf_sha256") == input_hashes.get("pmf_sha256")
            and row.get("amplitude_sha256") == input_hashes.get("amplitude_sha256")
            and row.get("scheme_config_sha256") == input_hashes.get("scheme_config_sha256")
            and row.get("precision_policy_sha256") == precision_policy_sha256
            for row in rows
        ):
            raise ValueError("AP checkpoint row hashes do not match the current request")

    policy = "adaptive"
    reason = None
    legacy_schedule = request.get("precision_ladder_decimal_digits")
    if legacy_schedule is not None:
        policy = "explicit_diagnostic_schedule"
        rows = [_row(p, z, int(digits), diagnostic_thresholds) for digits in legacy_schedule]
        ok = rows_converged(rows)
        if not ok:
            reason = "explicit precision rows did not converge"
    else:
        digits = int(request.get("initial_precision_digits", 256))
        step = int(request.get("minimum_precision_step", 128))
        maximum = request.get("max_precision_digits")
        if digits <= 0 or step < 128:
            raise ValueError("adaptive precision requires positive digits and a step >= 128")
        if maximum is not None and int(maximum) < digits:
            raise ValueError("max_precision_digits must be >= initial_precision_digits")
        maximum = None if maximum is None else int(maximum)
        ok = rows_converged(rows)
        if rows:
            digits = next_precision_digits(
                rows[-1]["digits"], rows[-1], step,
                precision_policy["condition_guard_digits"],
            )
        while not ok:
            started = time.perf_counter()
            row = _row(p, z, digits, diagnostic_thresholds)
            row["runtime_seconds"] = time.perf_counter() - started
            row.update({
                "pmf_sha256": input_hashes.get("pmf_sha256"),
                "amplitude_sha256": input_hashes.get("amplitude_sha256"),
                "scheme_config_sha256": input_hashes.get("scheme_config_sha256"),
                "precision_policy_sha256": precision_policy_sha256,
            })
            rows.append(row)
            if checkpoint_path:
                _write_checkpoint(
                    checkpoint_path, input_hashes, precision_policy_sha256, rows
                )
            if rows_converged(rows):
                ok = True
                break
            if maximum is not None and digits >= maximum:
                reason = "maximum precision reached before two-level convergence"
                break
            if row["resolved"]:
                next_digits = next_precision_digits(
                    digits, row, step, precision_policy["condition_guard_digits"]
                )
            else:
                next_digits = digits + step
            if maximum is not None and next_digits > maximum:
                reason = "maximum precision reached before two-level convergence"
                break
            digits = next_digits

    result = {
        "status": "FULL_SUPPORT_CONVERGED" if ok else "NUMERICAL_CONVERGENCE_ERROR",
        "reason": reason,
        "precision_policy": policy,
        "rows": rows,
    }

    if ok:
        result.update(
            {
                "C": rows[-1]["C"],
                "w": rows[-1]["w"],
                "C_positive": rows[-1].get("C_positive"),
                "C_trace": rows[-1].get("C_trace"),
                "C_difference": rows[-1].get("C_difference"),
                "w_residual": rows[-1].get("w_residual"),
                "w_diff": rows[-1].get("w_diff"),
                "A_w": rows[-1].get("A_w"),
                "B_w": rows[-1].get("B_w"),
                "cancellation_digits": rows[-1].get("cancellation_digits"),
                "residual_contributions": rows[-1].get("residual_contributions"),
                "orbit_sector_residual": rows[-1].get("orbit_sector_residual"),
            }
        )

    json.dump(
        result,
        sys.stdout,
        sort_keys=True,
    )


if __name__ == "__main__":
    main()
