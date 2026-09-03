"""Exact-binary64 arbitrary-precision full-support C4 source-moment worker."""

from __future__ import annotations

import json
import sys

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


def _row(p, z, digits):
    with mp.workdps(digits):
        values = []
        vectors = []

        for g in _sectors(p, z):
            v, u = mp.eighe(g)

            values.append(
                [mp.re(v[i]) for i in range(64)]
            )
            vectors.append(u)

        # Flatten all four C4-sector eigenspectra.
        all_eigenvalues = [
            eigenvalue
            for sector_values in values
            for eigenvalue in sector_values
        ]

        rank = sum(
            eigenvalue > 0
            for eigenvalue in all_eigenvalues
        )

        minimum_eigenvalue = min(all_eigenvalues)

        # IMPORTANT:
        # Even unresolved rows must provide minimum_eigenvalue because
        # holevo.py consumes this diagnostic for every precision row.
        if rank != 256:
            return {
                "digits": digits,
                "rank": rank,
                "resolved": False,
                "minimum_eigenvalue": mp.nstr(
                    minimum_eigenvalue,
                    50,
                ),
            }

        a = []
        q = []
        c = mp.mpf(0)

        for s in range(4):
            previous = (s - 1) % 4

            m = (
                vectors[s].H
                * mp.diag(z)
                * vectors[previous]
            )

            sr = mp.diag(
                [mp.sqrt(x) for x in values[s]]
            )

            sp = mp.diag(
                [mp.sqrt(x) for x in values[previous]]
            )

            # First multi-RHS solve:
            # sp * X = m.T
            x = _lu_solve_matrix(
                sp,
                m.T,
            )

            b = sr * x.T

            # Second multi-RHS solve:
            # sp * X2 = (sr * b).T
            x2 = _lu_solve_matrix(
                sp,
                (sr * b).T,
            )

            aa = sr * x2.T

            a.append(aa)

            # mpmath has no mp.trace(), so compute the trace explicitly.
            cb = sr * b * sp * b.H

            c += mp.fsum(
                cb[i, i]
                for i in range(cb.rows)
            ).real

            q.append(
                sr
                * vectors[s].H
                * mp.diag(
                    [
                        1 / (2 * mp.sqrt(x))
                        for x in p
                    ]
                )
            )

        t = [
            a[s] * q[(s - 1) % 4]
            for s in range(4)
        ]

        d = [
            mp.fsum(
                mp.conj(q[s][i, k])
                * t[s][i, k]
                for s in range(4)
                for i in range(64)
            )
            for k in range(64)
        ]

        w = mp.fsum(
            4
            * p[k]
            * mp.fsum(
                abs(
                    t[s][i, k]
                    - q[s][i, k] * d[k]
                )
                ** 2
                for s in range(4)
                for i in range(64)
            )
            for k in range(64)
        )

        return {
            "digits": digits,
            "rank": 256,
            "resolved": True,
            "minimum_eigenvalue": mp.nstr(
                minimum_eigenvalue,
                50,
            ),
            "C": mp.nstr(c, 50),
            "w": mp.nstr(w, 50),
        }


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

    rows = [
        _row(p, z, int(digits))
        for digits in request[
            "precision_ladder_decimal_digits"
        ]
    ]

    final = rows[-2:]

    ok = all(
        row["resolved"]
        and row["rank"] == 256
        for row in final
    )

    if ok:
        ok = all(
            abs(
                mp.mpf(final[0][name])
                - mp.mpf(final[1][name])
            )
            <= (
                mp.mpf("1e-7")
                + mp.mpf("1e-6")
                * max(
                    abs(mp.mpf(final[0][name])),
                    abs(mp.mpf(final[1][name])),
                )
            )
            for name in ("C", "w")
        )

    result = {
        "status": (
            "FULL_SUPPORT_CONVERGED"
            if ok
            else "FAIL_CLOSED"
        ),
        "rows": rows,
    }

    if ok:
        result.update(
            {
                "C": final[-1]["C"],
                "w": final[-1]["w"],
            }
        )

    json.dump(
        result,
        sys.stdout,
        sort_keys=True,
    )


if __name__ == "__main__":
    main()