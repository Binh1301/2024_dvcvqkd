"""Experimental full-support C4 forward tangent diagnostic.

EXPERIMENTAL_DIAGNOSTIC_ONLY: this module is deliberately outside the
production/autograd path.  It evaluates one physical forward tangent for the
exact four-sector source moments without clipping, jitter, or support
truncation.  It does not implement a reverse pass or training integration.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Sequence

import mpmath as mp


EXPERIMENTAL_DIAGNOSTIC_ONLY = True


class FullSupportUnresolved(RuntimeError):
    """Raised when the requested AP precision does not resolve every mode."""

    def __init__(self, digits: int, rank: int, minimum_eigenvalue: mp.mpf) -> None:
        self.digits = digits
        self.rank = rank
        self.minimum_eigenvalue = minimum_eigenvalue
        super().__init__(
            f"full support unresolved at {digits} digits: "
            f"rank={rank}, lambda_min={mp.nstr(minimum_eigenvalue, 30)}"
        )


@dataclass(frozen=True)
class C4TangentResult:
    """Forward values and one directional differential of C4 source moments."""

    C: mp.mpf
    w: mp.mpf
    dC: mp.mpf
    dw: mp.mpf
    diagnostics: dict[str, Any]


def _as_real(value: Any) -> mp.mpf:
    if isinstance(value, mp.mpf):
        return value
    try:
        return mp.mpf(value)
    except (TypeError, ValueError):
        return mp.mpf(float(value))


def _as_complex(value: Any) -> mp.mpc:
    if isinstance(value, mp.mpc):
        return value
    if isinstance(value, complex):
        return mp.mpc(value.real, value.imag)
    try:
        return mp.mpc(value, 0)
    except (TypeError, ValueError):
        return mp.mpc(float(value), 0)


def _matrix_max_abs(matrix: mp.matrix) -> mp.mpf:
    if matrix.rows == 0 or matrix.cols == 0:
        return mp.mpf(0)
    return max(abs(matrix[i, j]) for i in range(matrix.rows) for j in range(matrix.cols))


def _max_abs(value: Any) -> mp.mpf:
    if isinstance(value, mp.matrix):
        return _matrix_max_abs(value)
    if isinstance(value, (list, tuple)):
        return max((_max_abs(item) for item in value), default=mp.mpf(0))
    return abs(value)


def _scale(value: Any) -> dict[str, str]:
    magnitude = _max_abs(value)
    if not magnitude:
        return {"max_abs": "0", "log10_max_abs": "-inf"}
    return {
        "max_abs": mp.nstr(magnitude, 30),
        "log10_max_abs": mp.nstr(mp.log10(magnitude), 30),
    }


def _scales(objects: dict[str, Any]) -> dict[str, dict[str, str]]:
    return {name: _scale(value) for name, value in objects.items()}


def _right_solve(
    eigenvectors: mp.matrix,
    eigenvalues: Sequence[mp.mpf],
    rhs: mp.matrix,
    *,
    square_root: bool,
) -> mp.matrix:
    """Solve X A = rhs using the retained full-support spectral factorization.

    With A=U diag(lambda) U^H (or A=S=U diag(sqrt(lambda)) U^H), this is the
    exact right-side linear solve X=rhs U diag(lambda)^(-1) U^H.  Only scalar
    divisions are performed; dense R=G^(-1/2) and J=G^(-1) matrices are never
    materialized.
    """

    transformed = rhs * eigenvectors
    for j, value in enumerate(eigenvalues):
        denominator = mp.sqrt(value) if square_root else value
        for i in range(transformed.rows):
            transformed[i, j] /= denominator
    return transformed * eigenvectors.H


def _raw_blocks(
    probabilities: Sequence[mp.mpf],
    amplitudes: Sequence[mp.mpc],
    d_probabilities: Sequence[mp.mpf],
    d_amplitudes: Sequence[mp.mpc],
) -> tuple[list[mp.matrix], list[mp.matrix]]:
    blocks: list[mp.matrix] = []
    d_blocks: list[mp.matrix] = []
    for d in range(4):
        rotation = mp.j**d
        block = mp.matrix(len(probabilities))
        d_block = mp.matrix(len(probabilities))
        for i, (pi, zi, dpi, dzi) in enumerate(
            zip(probabilities, amplitudes, d_probabilities, d_amplitudes)
        ):
            for j, (pj, zj, dpj, dzj) in enumerate(
                zip(probabilities, amplitudes, d_probabilities, d_amplitudes)
            ):
                exponent = (
                    -(abs(zi) ** 2 + abs(rotation * zj) ** 2) / 2
                    + mp.conj(zi) * rotation * zj
                )
                value = mp.sqrt(pi * pj) * mp.exp(exponent)
                d_exponent = (
                    -(
                        mp.conj(zi) * dzi
                        + zi * mp.conj(dzi)
                        + mp.conj(zj) * dzj
                        + zj * mp.conj(dzj)
                    )
                    / 2
                    + mp.conj(dzi) * rotation * zj
                    + mp.conj(zi) * rotation * dzj
                )
                d_value = value * (
                    dpi / (2 * pi)
                    + dpj / (2 * pj)
                    + d_exponent
                )
                block[i, j] = value
                d_block[i, j] = d_value
        blocks.append(block)
        d_blocks.append(d_block)
    return blocks, d_blocks


def _sectors(
    blocks: Sequence[mp.matrix],
    d_blocks: Sequence[mp.matrix],
) -> tuple[list[mp.matrix], list[mp.matrix]]:
    sectors: list[mp.matrix] = []
    d_sectors: list[mp.matrix] = []
    for s in range(4):
        x = mp.zeros(blocks[0].rows)
        d_x = mp.zeros(blocks[0].rows)
        for d in range(4):
            coefficient = mp.j ** (s * d)
            x += coefficient * blocks[d]
            d_x += coefficient * d_blocks[d]
        sectors.append((x + x.H) / 2)
        d_sectors.append((d_x + d_x.H) / 2)
    return sectors, d_sectors


def _sqrt_tangent(
    eigenvectors: mp.matrix,
    square_root: mp.matrix,
    d_sector: mp.matrix,
) -> mp.matrix:
    transformed = eigenvectors.H * d_sector * eigenvectors
    kernel = mp.zeros(transformed.rows)
    for i in range(transformed.rows):
        for j in range(transformed.cols):
            kernel[i, j] = transformed[i, j] / (square_root[i, i] + square_root[j, j])
    return eigenvectors * kernel * eigenvectors.H


def _difference(left: Any, right: Any) -> dict[str, str]:
    if isinstance(left, mp.matrix):
        magnitude = _matrix_max_abs(left - right)
    elif isinstance(left, (list, tuple)):
        magnitude = max(
            (_difference_magnitude(a, b) for a, b in zip(left, right)),
            default=mp.mpf(0),
        )
    else:
        magnitude = abs(left - right)
    scale = max(_max_abs(left), _max_abs(right), mp.mpf("1e-40"))
    return {
        "max_abs": mp.nstr(magnitude, 30),
        "relative": mp.nstr(magnitude / scale, 30),
    }


def _difference_magnitude(left: Any, right: Any) -> mp.mpf:
    if isinstance(left, mp.matrix):
        return _matrix_max_abs(left - right)
    if isinstance(left, (list, tuple)):
        return max(
            (_difference_magnitude(a, b) for a, b in zip(left, right)),
            default=mp.mpf(0),
        )
    return abs(left - right)


def _residual(lhs: mp.matrix, rhs: mp.matrix, solved: mp.matrix) -> dict[str, str]:
    return _difference(solved * lhs, rhs)


def _propagate(
    probabilities: Sequence[mp.mpf],
    d_probabilities: Sequence[mp.mpf],
    square_roots: Sequence[mp.matrix],
    d_square_roots: Sequence[mp.matrix],
    B: Sequence[mp.matrix],
    dB: Sequence[mp.matrix],
    A: Sequence[mp.matrix],
    dA: Sequence[mp.matrix],
) -> dict[str, Any]:
    n = len(probabilities)
    P = mp.diag([1 / (2 * mp.sqrt(value)) for value in probabilities])
    dP = mp.diag(
        [-value / (4 * probability ** (mp.mpf(3) / 2)) for value, probability in zip(d_probabilities, probabilities)]
    )
    Q = [square_roots[s] * P for s in range(4)]
    dQ = [
        d_square_roots[s] * P + square_roots[s] * dP
        for s in range(4)
    ]
    T = [A[s] * Q[(s - 1) % 4] for s in range(4)]
    dT = [
        dA[s] * Q[(s - 1) % 4] + A[s] * dQ[(s - 1) % 4]
        for s in range(4)
    ]
    u = [
        mp.fsum(
            mp.conj(Q[s][i, k]) * T[s][i, k]
            for s in range(4)
            for i in range(n)
        )
        for k in range(n)
    ]
    du = [
        mp.fsum(
            mp.conj(dQ[s][i, k]) * T[s][i, k]
            + mp.conj(Q[s][i, k]) * dT[s][i, k]
            for s in range(4)
            for i in range(n)
        )
        for k in range(n)
    ]
    E = [mp.matrix(n) for _ in range(4)]
    dE = [mp.matrix(n) for _ in range(4)]
    for s in range(4):
        for i in range(n):
            for k in range(n):
                E[s][i, k] = T[s][i, k] - Q[s][i, k] * u[k]
                dE[s][i, k] = (
                    dT[s][i, k]
                    - dQ[s][i, k] * u[k]
                    - Q[s][i, k] * du[k]
                )

    C = mp.mpf(0)
    dC = mp.mpf(0)
    for s in range(4):
        previous = (s - 1) % 4
        C_term = square_roots[s] * B[s] * square_roots[previous] * B[s].H
        dC_term = (
            d_square_roots[s] * B[s] * square_roots[previous] * B[s].H
            + square_roots[s] * dB[s] * square_roots[previous] * B[s].H
            + square_roots[s] * B[s] * d_square_roots[previous] * B[s].H
            + square_roots[s] * B[s] * square_roots[previous] * dB[s].H
        )
        C += mp.fsum(C_term[i, i] for i in range(n)).real
        dC += mp.fsum(dC_term[i, i] for i in range(n)).real

    w = mp.mpf(0)
    dw = mp.mpf(0)
    for k, probability in enumerate(probabilities):
        for s in range(4):
            norm_square = mp.fsum(abs(E[s][i, k]) ** 2 for i in range(n))
            cross = mp.fsum(mp.conj(E[s][i, k]) * dE[s][i, k] for i in range(n)).real
            w += 4 * probability * norm_square
            dw += 4 * d_probabilities[k] * norm_square + 8 * probability * cross
    return {
        "C": C,
        "w": w,
        "dC": dC,
        "dw": dw,
        "P": P,
        "dP": dP,
        "Q": Q,
        "dQ": dQ,
        "T": T,
        "dT": dT,
        "u": u,
        "du": du,
        "E": E,
        "dE": dE,
    }


def _explicit_products(
    values: Sequence[Sequence[mp.mpf]],
    vectors: Sequence[mp.matrix],
    square_roots: Sequence[mp.matrix],
    sectors: Sequence[mp.matrix],
    d_sectors: Sequence[mp.matrix],
    d_square_roots: Sequence[mp.matrix],
    diagonal_z: mp.matrix,
    d_diagonal_z: mp.matrix,
) -> dict[str, Any]:
    inverse_square = [
        vectors[s] * mp.diag([1 / mp.sqrt(value) for value in values[s]]) * vectors[s].H
        for s in range(4)
    ]
    inverse = [
        vectors[s] * mp.diag([1 / value for value in values[s]]) * vectors[s].H
        for s in range(4)
    ]
    d_inverse_square = [
        -inverse_square[s] * d_square_roots[s] * inverse_square[s]
        for s in range(4)
    ]
    d_inverse = [
        -inverse[s] * d_sectors[s] * inverse[s]
        for s in range(4)
    ]
    B = [
        square_roots[s] * diagonal_z * inverse_square[(s - 1) % 4]
        for s in range(4)
    ]
    dB = [
        d_square_roots[s] * diagonal_z * inverse_square[(s - 1) % 4]
        + square_roots[s] * d_diagonal_z * inverse_square[(s - 1) % 4]
        + square_roots[s] * diagonal_z * d_inverse_square[(s - 1) % 4]
        for s in range(4)
    ]
    A = [
        sectors[s] * diagonal_z * inverse[(s - 1) % 4]
        for s in range(4)
    ]
    dA = [
        d_sectors[s] * diagonal_z * inverse[(s - 1) % 4]
        + sectors[s] * d_diagonal_z * inverse[(s - 1) % 4]
        + sectors[s] * diagonal_z * d_inverse[(s - 1) % 4]
        for s in range(4)
    ]
    return {
        "R": inverse_square,
        "J": inverse,
        "dR": d_inverse_square,
        "dJ": d_inverse,
        "B": B,
        "dB": dB,
        "A": A,
        "dA": dA,
    }


def forward_tangent(
    probabilities: Iterable[Any],
    amplitudes: Iterable[Any],
    d_probabilities: Iterable[Any],
    d_amplitudes: Iterable[Any],
    *,
    digits: int = 80,
    instrument_explicit: bool = False,
) -> C4TangentResult:
    """Return C, w and their exact forward tangent for one physical path.

    The input probabilities/amplitudes are the 64 prototype representatives
    used by the repository's C4 worker.  ``d_amplitudes`` is a complex
    directional derivative with the physical convention d(conj(z))=conj(dz).
    The call fails closed if arbitrary precision does not resolve all 4*n
    positive Gram modes.
    """

    if digits < 20:
        raise ValueError("digits must be at least 20")
    raw_p = list(probabilities)
    raw_z = list(amplitudes)
    raw_dp = list(d_probabilities)
    raw_dz = list(d_amplitudes)
    n = len(raw_p)
    if not n or len(raw_z) != n or len(raw_dp) != n or len(raw_dz) != n:
        raise ValueError("probabilities, amplitudes, and tangents must have equal nonzero length")

    with mp.workdps(digits):
        p = [_as_real(value) for value in raw_p]
        z = [_as_complex(value) for value in raw_z]
        dp = [_as_real(value) for value in raw_dp]
        dz = [_as_complex(value) for value in raw_dz]
        if any(value <= 0 for value in p):
            raise ValueError("full-support probabilities must be strictly positive")

        blocks, d_blocks = _raw_blocks(p, z, dp, dz)
        sectors, d_sectors = _sectors(blocks, d_blocks)
        values: list[list[mp.mpf]] = []
        vectors: list[mp.matrix] = []
        square_roots: list[mp.matrix] = []
        root_diagonals: list[mp.matrix] = []
        all_values: list[mp.mpf] = []
        for sector in sectors:
            eigenvalues, eigenvectors = mp.eighe(sector)
            row = [mp.re(eigenvalues[i]) for i in range(n)]
            values.append(row)
            vectors.append(eigenvectors)
            root_diagonal = mp.diag([mp.sqrt(value) for value in row])
            root_diagonals.append(root_diagonal)
            square_roots.append(eigenvectors * root_diagonal * eigenvectors.H)
            all_values.extend(row)
        minimum = min(all_values)
        rank = sum(value > 0 for value in all_values)
        if rank != 4 * n:
            raise FullSupportUnresolved(digits, rank, minimum)

        d_square_roots = [
            _sqrt_tangent(vectors[s], root_diagonals[s], d_sectors[s])
            for s in range(4)
        ]
        diagonal_z = mp.diag(z)
        d_diagonal_z = mp.diag(dz)
        G = sectors
        dG = d_sectors
        B_rhs = [square_roots[s] * diagonal_z for s in range(4)]
        A_rhs = [G[s] * diagonal_z for s in range(4)]
        B = [
            _right_solve(
                vectors[(s - 1) % 4],
                values[(s - 1) % 4],
                B_rhs[s],
                square_root=True,
            )
            for s in range(4)
        ]
        A = [
            _right_solve(
                vectors[(s - 1) % 4],
                values[(s - 1) % 4],
                A_rhs[s],
                square_root=False,
            )
            for s in range(4)
        ]
        dB_rhs = [
            d_square_roots[s] * diagonal_z
            + square_roots[s] * d_diagonal_z
            - B[s] * d_square_roots[(s - 1) % 4]
            for s in range(4)
        ]
        dA_rhs = [
            dG[s] * diagonal_z
            + G[s] * d_diagonal_z
            - A[s] * dG[(s - 1) % 4]
            for s in range(4)
        ]
        dB = [
            _right_solve(
                vectors[(s - 1) % 4],
                values[(s - 1) % 4],
                dB_rhs[s],
                square_root=True,
            )
            for s in range(4)
        ]
        dA = [
            _right_solve(
                vectors[(s - 1) % 4],
                values[(s - 1) % 4],
                dA_rhs[s],
                square_root=False,
            )
            for s in range(4)
        ]
        constrained = _propagate(
            p,
            dp,
            square_roots,
            d_square_roots,
            B,
            dB,
            A,
            dA,
        )

        solve_residuals = {
            "B": [
                _residual(square_roots[(s - 1) % 4], B_rhs[s], B[s])
                for s in range(4)
            ],
            "A": [
                _residual(G[(s - 1) % 4], A_rhs[s], A[s])
                for s in range(4)
            ],
            "dB": [
                _residual(square_roots[(s - 1) % 4], dB_rhs[s], dB[s])
                for s in range(4)
            ],
            "dA": [
                _residual(G[(s - 1) % 4], dA_rhs[s], dA[s])
                for s in range(4)
            ],
            "sylvester": [
                _difference(
                    square_roots[s] * d_square_roots[s]
                    + d_square_roots[s] * square_roots[s],
                    dG[s],
                )
                for s in range(4)
            ],
        }
        diagnostics: dict[str, Any] = {
            "marker": "EXPERIMENTAL_DIAGNOSTIC_ONLY",
            "representation": "C4_constrained_solve_forward_tangent",
            "reverse": "not_implemented",
            "digits": digits,
            "prototype_count": n,
            "support": {
                "rank": rank,
                "expected_rank": 4 * n,
                "minimum_eigenvalue": mp.nstr(minimum, 50),
                "maximum_eigenvalue": mp.nstr(max(all_values), 50),
            },
            "solve_residuals": solve_residuals,
            "magnitude": {
                "constrained": _scales(
                    {
                        "H": blocks,
                        "dH": d_blocks,
                        "G": G,
                        "dG": dG,
                        "S": square_roots,
                        "dS": d_square_roots,
                        "D": diagonal_z,
                        "dD": d_diagonal_z,
                        "P": constrained["P"],
                        "dP": constrained["dP"],
                        "B_rhs": B_rhs,
                        "A_rhs": A_rhs,
                        "dB_rhs": dB_rhs,
                        "dA_rhs": dA_rhs,
                        "B": B,
                        "dB": dB,
                        "A": A,
                        "dA": dA,
                        "Q": constrained["Q"],
                        "dQ": constrained["dQ"],
                        "T": constrained["T"],
                        "dT": constrained["dT"],
                        "u": constrained["u"],
                        "du": constrained["du"],
                        "E": constrained["E"],
                        "dE": constrained["dE"],
                    }
                )
            },
            "constrained_values": {
                "C": mp.nstr(constrained["C"], 50),
                "w": mp.nstr(constrained["w"], 50),
                "dC": mp.nstr(constrained["dC"], 50),
                "dw": mp.nstr(constrained["dw"], 50),
            },
        }

        if instrument_explicit:
            explicit_products = _explicit_products(
                values,
                vectors,
                square_roots,
                G,
                dG,
                d_square_roots,
                diagonal_z,
                d_diagonal_z,
            )
            explicit = _propagate(
                p,
                dp,
                square_roots,
                d_square_roots,
                explicit_products["B"],
                explicit_products["dB"],
                explicit_products["A"],
                explicit_products["dA"],
            )
            diagnostics["magnitude"]["explicit"] = _scales(
                {
                    **explicit_products,
                    "Q": explicit["Q"],
                    "dQ": explicit["dQ"],
                    "T": explicit["T"],
                    "dT": explicit["dT"],
                    "u": explicit["u"],
                    "du": explicit["du"],
                    "E": explicit["E"],
                    "dE": explicit["dE"],
                }
            )
            diagnostics["explicit_values"] = {
                "C": mp.nstr(explicit["C"], 50),
                "w": mp.nstr(explicit["w"], 50),
                "dC": mp.nstr(explicit["dC"], 50),
                "dw": mp.nstr(explicit["dw"], 50),
            }
            diagnostics["constrained_vs_explicit"] = {
                "B": _difference(B, explicit_products["B"]),
                "dB": _difference(dB, explicit_products["dB"]),
                "A": _difference(A, explicit_products["A"]),
                "dA": _difference(dA, explicit_products["dA"]),
                "C": _difference(constrained["C"], explicit["C"]),
                "w": _difference(constrained["w"], explicit["w"]),
                "dC": _difference(constrained["dC"], explicit["dC"]),
                "dw": _difference(constrained["dw"], explicit["dw"]),
            }

        return C4TangentResult(
            C=constrained["C"],
            w=constrained["w"],
            dC=constrained["dC"],
            dw=constrained["dw"],
            diagnostics=diagnostics,
        )
