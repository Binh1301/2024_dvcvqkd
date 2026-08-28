"""Independent arbitrary-precision Gram oracle for the near-coincident fixture.

The oracle uses coherent-state overlaps directly and has no Fock cutoff.  C4
block-circulant structure reduces the weighted 256-state Gram eigensystem to
four exact 64-state Hermitian sectors.  It is diagnostic only and never reads
the held-out test set or changes the active security implementation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time

import mpmath as mp

from _common import ROOT, load_yaml


# Frozen before arbitrary-precision outcomes were inspected.
PREREGISTERED_DECIMAL_DIGITS = (50, 80, 120, 160)
# Added prospectively after the 160-digit result resolved only 44/256 modes and
# the frozen sector extrapolation estimated 974--986 digits for full support.
ADAPTIVE_FULL_SUPPORT_CONFIRMATION_DIGITS = (1050, 1250, 1450)
ORBIT_COUNT = 64
C4_ORDER = 4
PHASE_INCREMENT = "1e-7"


def _text(value: mp.mpf | mp.mpc, digits: int) -> str:
    return mp.nstr(value, n=digits, strip_zeros=False)


def coherent_state_overlap(alpha_i: mp.mpc, alpha_j: mp.mpc) -> mp.mpc:
    """Exact normalized coherent-state overlap ``<alpha_i|alpha_j>``."""

    return mp.exp(
        -(abs(alpha_i) ** 2 + abs(alpha_j) ** 2) / 2
        + mp.conj(alpha_i) * alpha_j
    )


def _build_sector_grams() -> tuple[list[mp.matrix], list[mp.mpc]]:
    radius = mp.sqrt(2)
    phase_step = mp.mpf(PHASE_INCREMENT)
    prototypes = [radius * mp.expj(phase_step * k) for k in range(ORBIT_COUNT)]
    imaginary_unit = mp.j
    blocks: list[mp.matrix] = []
    for difference in range(C4_ORDER):
        rotation = imaginary_unit ** difference
        block = mp.matrix(ORBIT_COUNT)
        for k in range(ORBIT_COUNT):
            for ell in range(ORBIT_COUNT):
                # sqrt(p_i p_j)=1/256 for the uniform 256-state fixture.
                block[k, ell] = coherent_state_overlap(
                    prototypes[k], rotation * prototypes[ell]
                ) / 256
        blocks.append(block)
    sectors: list[mp.matrix] = []
    for sector in range(C4_ORDER):
        matrix = mp.matrix(ORBIT_COUNT)
        for k in range(ORBIT_COUNT):
            for ell in range(ORBIT_COUNT):
                value = mp.fsum(
                    blocks[difference][k, ell] * imaginary_unit ** (sector * difference)
                    for difference in range(C4_ORDER)
                )
                matrix[k, ell] = value
        # Remove only arithmetic anti-Hermitian residue; the exact sector is Hermitian.
        sectors.append((matrix + matrix.H) / 2)
    return sectors, prototypes


def _security_chain(
    correlation: mp.mpf,
    penalty: mp.mpf,
    transmittance: mp.mpf,
    epsilon: mp.mpf,
    mutual_information: mp.mpf,
    beta: mp.mpf,
) -> dict[str, mp.mpf]:
    va = mp.mpf(4)
    z = 2 * mp.sqrt(transmittance) * correlation - mp.sqrt(
        2 * transmittance * epsilon * penalty
    )
    a = va + 1
    b = 1 + transmittance * va + transmittance * epsilon
    delta = a * a + b * b - 2 * z * z
    determinant = (a * b - z * z) ** 2
    root = mp.sqrt(delta * delta - 4 * determinant)
    lambda1 = mp.sqrt((delta + root) / 2)
    lambda2 = mp.sqrt((delta - root) / 2)
    lambda3 = a - z * z / (b + 1)

    def entropy(occupation: mp.mpf) -> mp.mpf:
        if occupation == 0:
            return mp.mpf(0)
        return (
            (occupation + 1) * mp.log(occupation + 1, 2)
            - occupation * mp.log(occupation, 2)
        )

    chi = (
        entropy((lambda1 - 1) / 2)
        + entropy((lambda2 - 1) / 2)
        - entropy((lambda3 - 1) / 2)
    )
    return {
        "Z": z, "lambda1": lambda1, "lambda2": lambda2, "lambda3": lambda3,
        "chi_BE": chi, "raw_K": beta * mutual_information - chi,
    }


def _successive_oracles_converge(
    previous: dict[str, object],
    current: dict[str, object],
    config: dict[str, object],
) -> tuple[bool, dict[str, object]]:
    """Apply the frozen Fock/security tolerances to two full-support rows."""

    fock = config["numerical_validation"]["fock"]
    moment_absolute = mp.mpf(str(fock["moment_absolute_tolerance"]))
    moment_relative = mp.mpf(str(fock["moment_relative_tolerance"]))
    information_absolute = mp.mpf(str(fock["information_absolute_tolerance_bits"]))
    information_relative = mp.mpf(str(fock["information_relative_tolerance"]))

    def comparison(
        left: str, right: str, *, information: bool = False
    ) -> dict[str, object]:
        left_value = mp.mpf(left)
        right_value = mp.mpf(right)
        absolute = information_absolute if information else moment_absolute
        relative = information_relative if information else moment_relative
        difference = abs(left_value - right_value)
        allowance = absolute + relative * max(abs(left_value), abs(right_value))
        return {"difference": difference, "allowance": allowance,
                "passes": difference <= allowance}

    comparisons: dict[str, object] = {
        "C": comparison(previous["C"], current["C"]),
        "w": comparison(previous["w"], current["w"]),
        "states": [],
    }
    for left, right in zip(previous["states"], current["states"]):
        comparisons["states"].append({
            name: comparison(
                left[name], right[name], information=name in {"chi_BE", "raw_K"}
            )
            for name in ("Z", "lambda1", "lambda2", "lambda3", "chi_BE", "raw_K")
        })
    passes = bool(comparisons["C"]["passes"] and comparisons["w"]["passes"])
    passes = passes and all(
        metric["passes"]
        for state in comparisons["states"]
        for metric in state.values()
    )
    return passes, comparisons


def _moments_at_threshold(
    eigenvalues: list[list[mp.mpf]],
    eigenvectors: list[mp.matrix],
    prototypes: list[mp.mpc],
    threshold: mp.mpf,
    states: list[tuple[mp.mpf, mp.mpf, mp.mpf]],
    beta: mp.mpf,
) -> dict[str, object]:
    supports = [
        [index for index, value in enumerate(sector) if value > threshold]
        for sector in eigenvalues
    ]
    a_tau_blocks: list[mp.matrix] = []
    correlation = mp.mpf(0)
    for sector in range(C4_ORDER):
        previous = (sector - 1) % C4_ORDER
        rows = supports[sector]
        columns = supports[previous]
        block = mp.matrix(len(rows), len(columns))
        for row_position, row_index in enumerate(rows):
            for column_position, column_index in enumerate(columns):
                matrix_element = mp.fsum(
                    mp.conj(eigenvectors[sector][k, row_index])
                    * prototypes[k]
                    * eigenvectors[previous][k, column_index]
                    for k in range(ORBIT_COUNT)
                )
                row_value = eigenvalues[sector][row_index]
                column_value = eigenvalues[previous][column_index]
                a_support = mp.sqrt(row_value) * matrix_element / mp.sqrt(column_value)
                correlation += (
                    mp.sqrt(row_value) * mp.sqrt(column_value) * abs(a_support) ** 2
                )
                block[row_position, column_position] = (
                    mp.sqrt(row_value) * a_support / mp.sqrt(column_value)
                )
        a_tau_blocks.append(block)

    coefficient_matrices: list[mp.matrix] = []
    maximum_projection_norm_excess = mp.mpf(0)
    for sector in range(C4_ORDER):
        coefficients = mp.matrix(len(supports[sector]), ORBIT_COUNT)
        for position, index in enumerate(supports[sector]):
            scale = 8 * mp.sqrt(eigenvalues[sector][index])
            for orbit in range(ORBIT_COUNT):
                coefficients[position, orbit] = (
                    scale * mp.conj(eigenvectors[sector][orbit, index])
                )
        coefficient_matrices.append(coefficients)
    transformed = [
        a_tau_blocks[sector] * coefficient_matrices[(sector - 1) % C4_ORDER]
        for sector in range(C4_ORDER)
    ]
    inner_by_orbit = [
        mp.fsum(
            mp.fsum(
                mp.conj(coefficient_matrices[sector][index, orbit])
                * transformed[sector][index, orbit]
                for index in range(len(supports[sector]))
            )
            for sector in range(C4_ORDER)
        )
        for orbit in range(ORBIT_COUNT)
    ]
    for orbit in range(ORBIT_COUNT):
        projection_norm = mp.fsum(
            mp.fsum(
                abs(coefficient_matrices[sector][index, orbit]) ** 2
                for index in range(len(supports[sector]))
            )
            for sector in range(C4_ORDER)
        )
        maximum_projection_norm_excess = max(
            maximum_projection_norm_excess, projection_norm - 1
        )
    first_term = mp.fsum(
        eigenvalues[(sector - 1) % C4_ORDER][column_index]
        * abs(a_tau_blocks[sector][row_position, column_position]) ** 2
        for sector in range(C4_ORDER)
        for row_position, _ in enumerate(supports[sector])
        for column_position, column_index in enumerate(
            supports[(sector - 1) % C4_ORDER]
        )
    )
    penalty = first_term - mp.fsum(abs(value) ** 2 for value in inner_by_orbit) / 64

    # The original symbolwise contraction is retained only as a bounded oracle
    # regression for small supports. It is never used for the 256-mode run.
    scalar_reference_penalty = None
    if sum(len(value) for value in supports) <= 16:
        scalar_reference_penalty = mp.mpf(0)
        for orbit in range(ORBIT_COUNT):
            for rotation in range(C4_ORDER):
                coefficients = [
                    coefficient_matrices[sector][:, orbit]
                    * ((-mp.j) ** (sector * rotation))
                    for sector in range(C4_ORDER)
                ]
                transformed_symbol = [
                    a_tau_blocks[sector] * coefficients[(sector - 1) % C4_ORDER]
                    for sector in range(C4_ORDER)
                ]
                inner = mp.fsum(
                    mp.fsum(
                        mp.conj(coefficients[sector][index])
                        * transformed_symbol[sector][index]
                        for index in range(len(coefficients[sector]))
                    )
                    for sector in range(C4_ORDER)
                )
                first = mp.fsum(
                    mp.fsum(abs(value) ** 2 for value in transformed_symbol[sector])
                    for sector in range(C4_ORDER)
                )
                scalar_reference_penalty += first - abs(inner) ** 2
        scalar_reference_penalty /= 256
    return {
        "threshold": threshold,
        "sector_support_sizes": [len(value) for value in supports],
        "support_size": sum(len(value) for value in supports),
        "C": correlation,
        "w": penalty,
        "scalar_reference_w": scalar_reference_penalty,
        "block_minus_scalar_w": (
            None if scalar_reference_penalty is None else penalty - scalar_reference_penalty
        ),
        "maximum_projection_norm_excess": maximum_projection_norm_excess,
        "states": [
            _security_chain(correlation, penalty, t, epsilon, mi, beta)
            for t, epsilon, mi in states
        ],
    }


def _run_precision(
    digits: int,
    *,
    thresholds: tuple[str, ...],
    states_as_text: list[tuple[str, str, str]],
    beta_as_text: str,
) -> dict[str, object]:
    started = time.perf_counter()
    with mp.workdps(digits):
        sectors, prototypes = _build_sector_grams()
        eigenvalues: list[list[mp.mpf]] = []
        eigenvectors: list[mp.matrix] = []
        maximum_hermitian_residual = mp.mpf(0)
        for sector_index, sector in enumerate(sectors):
            print(f"digits={digits} sector={sector_index + 1}/4 eighe", flush=True)
            maximum_hermitian_residual = max(
                maximum_hermitian_residual,
                max(abs(sector[k, ell] - mp.conj(sector[ell, k]))
                    for k in range(ORBIT_COUNT) for ell in range(ORBIT_COUNT)),
            )
            values, vectors = mp.eighe(sector)
            eigenvalues.append([mp.re(values[index]) for index in range(ORBIT_COUNT)])
            eigenvectors.append(vectors)
        all_values = sorted(value for sector in eigenvalues for value in sector)
        resolution_floor = mp.power(10, -(digits - 10))
        resolved_positive = [value for value in all_values if value > resolution_floor]
        full_support_resolved = len(resolved_positive) == 256
        states = [(mp.mpf(t), mp.mpf(e), mp.mpf(mi)) for t, e, mi in states_as_text]
        beta = mp.mpf(beta_as_text)
        threshold_rows = [
            _moments_at_threshold(
                eigenvalues, eigenvectors, prototypes, mp.mpf(threshold), states, beta
            )
            for threshold in thresholds
        ]
        resolved_candidate = _moments_at_threshold(
            eigenvalues, eigenvectors, prototypes, resolution_floor, states, beta
        )

        def format_moments(row: dict[str, object]) -> dict[str, object]:
            return {
                **{key: value for key, value in row.items()
                   if key not in {
                       "threshold", "C", "w", "scalar_reference_w",
                       "block_minus_scalar_w", "maximum_projection_norm_excess", "states"
                   }},
                "threshold": _text(row["threshold"], digits),
                "C": _text(row["C"], digits),
                "w": _text(row["w"], digits),
                "scalar_reference_w": (
                    None if row["scalar_reference_w"] is None
                    else _text(row["scalar_reference_w"], digits)
                ),
                "block_minus_scalar_w": (
                    None if row["block_minus_scalar_w"] is None
                    else _text(row["block_minus_scalar_w"], digits)
                ),
                "maximum_projection_norm_excess": _text(
                    row["maximum_projection_norm_excess"], digits
                ),
                "states": [
                    {name: _text(value, digits) for name, value in state.items()}
                    for state in row["states"]
                ],
            }

        # Extrapolate only a compute requirement, never an unresolved eigenvalue.
        sector_required_digit_estimates = []
        for sector in eigenvalues:
            descending = sorted((value for value in sector if value > resolution_floor),
                                reverse=True)
            if len(descending) < 2:
                sector_required_digit_estimates.append(None)
                continue
            log_values = [-mp.log10(value) for value in descending]
            recent_gaps = [
                log_values[index] - log_values[index - 1]
                for index in range(max(1, len(log_values) - 3), len(log_values))
            ]
            gap = sorted(recent_gaps)[len(recent_gaps) // 2]
            estimate = log_values[-1] + gap * (ORBIT_COUNT - len(descending)) + 20
            sector_required_digit_estimates.append(int(mp.ceil(estimate)))
        active_index = next(
            index for index, threshold in enumerate(thresholds)
            if mp.mpf(threshold) == mp.mpf("1e-12")
        )
        return {
            "decimal_digits": digits,
            "runtime_seconds": time.perf_counter() - started,
            "maximum_hermitian_residual": _text(maximum_hermitian_residual, digits),
            "analytic_physical_rank_distinct_coherent_states": 256,
            "resolution_floor": _text(resolution_floor, digits),
            "resolved_positive_eigenvalue_count": len(resolved_positive),
            "expected_physical_eigenvalue_count": 256,
            "full_support_resolved": full_support_resolved,
            "minimum_positive_margin_over_resolution_floor": (
                None if not resolved_positive else _text(
                    resolved_positive[0] / resolution_floor, digits
                )
            ),
            "negative_eigenvalue_count_at_precision": sum(value < 0 for value in all_values),
            "minimum_eigenvalue": _text(all_values[0], digits),
            "maximum_eigenvalue": _text(all_values[-1], digits),
            "minimum_resolved_positive_eigenvalue": (
                None if not resolved_positive else _text(resolved_positive[0], digits)
            ),
            "resolved_spectral_condition_number": (
                None if not resolved_positive else _text(
                    all_values[-1] / resolved_positive[0], digits
                )
            ),
            "estimated_decimal_digits_for_full_rank_resolution_by_sector": (
                sector_required_digit_estimates
            ),
            "sector_eigenvalues": [
                [_text(value, digits) for value in sector] for sector in eigenvalues
            ],
            "active_threshold_1e_minus_12_reproduction": format_moments(
                threshold_rows[active_index]
            ),
            "threshold_sensitivity_diagnostic_only": [
                format_moments(row) for row in threshold_rows
            ],
            "resolved_full_support_candidate": {
                "status": (
                    "FULL_MATHEMATICAL_SUPPORT_RESOLVED"
                    if full_support_resolved else "PARTIAL_SUPPORT_ONLY"
                ),
                **format_moments(resolved_candidate),
            },
            "full_mathematical_support_oracle": (
                {"status": "FULL_MATHEMATICAL_SUPPORT_RESOLVED",
                 **format_moments(resolved_candidate)} if full_support_resolved else {
                    "status": "UNRESOLVED_AT_THIS_PRECISION",
                    "C": None, "w": None, "states": None,
                }
            ),
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "default.yaml")
    parser.add_argument("--mi-evidence", type=Path, default=ROOT / "results" / "mi_convergence.json")
    parser.add_argument("--dense-diagnostic", type=Path, default=ROOT / "results" / "near_coincident_fock_diagnostic.json")
    parser.add_argument("--output", type=Path, default=ROOT / "results" / "near_coincident_gram_oracle.json")
    parser.add_argument("--digits", type=int, nargs="*", default=list(PREREGISTERED_DECIMAL_DIGITS))
    parser.add_argument(
        "--reuse-existing-precision-rows", action="store_true",
        help="Refresh provenance/summary without recomputing existing frozen rows.",
    )
    parser.add_argument(
        "--append-to-existing", action="store_true",
        help="Checkpoint newly requested adaptive precision beside existing frozen rows.",
    )
    args = parser.parse_args()
    digits = tuple(args.digits)
    allowed_digits = PREREGISTERED_DECIMAL_DIGITS + ADAPTIVE_FULL_SUPPORT_CONFIRMATION_DIGITS
    if any(value not in allowed_digits for value in digits):
        raise ValueError("Digits must come from the frozen ladder or adaptive 1050 confirmation.")
    config = load_yaml(args.config.resolve())
    mi_evidence = json.loads(args.mi_evidence.resolve().read_text(encoding="utf-8"))
    dense = json.loads(args.dense_diagnostic.resolve().read_text(encoding="utf-8"))
    if dense.get("fixture") != "near_coincident_pseudoinverse_stress":
        raise ValueError("Dense diagnostic is not the required fixture.")
    t_values = mi_evidence["states"]["transmittance"]
    epsilon_values = mi_evidence["states"]["epsilon_snu"]
    replications = mi_evidence["traces"]["near_coincident_pseudoinverse_stress"]["replications"]
    selected_mi_sample_count = int(mi_evidence["minimum_common_sample_count"])
    reference_mi = [
        sum(float(next(
            row for row in replication["rows"]
            if int(row["sample_count"]) == selected_mi_sample_count
        )["mi_bits"][state]) for replication in replications)
        / len(replications)
        for state in range(3)
    ]
    states_as_text = [
        (repr(t), repr(epsilon), repr(mi))
        for t, epsilon, mi in zip(t_values, epsilon_values, reference_mi)
    ]
    thresholds = tuple(
        repr(float(value)) for value in config["numerical_validation"][
            "holevo_threshold_sensitivity"
        ]["density_eigenvalue_pseudoinverse_tolerances"]
    )
    payload = {
        "schema_version": "near-coincident-gram-oracle-v1",
        "status": "HIGH_PRECISION_DIAGNOSTIC_ONLY",
        "test_set_used": False,
        "publication_training_performed": False,
        "fixture": "near_coincident_pseudoinverse_stress",
        "overlap_formula": "exp(-(|alpha_i|^2+|alpha_j|^2)/2 + conj(alpha_i)*alpha_j)",
        "minus_cross_term_rejected": True,
        "fock_cutoff_used": False,
        "preregistered_decimal_digits": list(PREREGISTERED_DECIMAL_DIGITS),
        "adaptive_full_support_confirmation_digits": list(
            ADAPTIVE_FULL_SUPPORT_CONFIRMATION_DIGITS
        ),
        "executed_decimal_digits": list(digits),
        "thresholds": list(thresholds),
        "states": {"transmittance": t_values, "epsilon_snu": epsilon_values,
                   "mutual_information_bits": reference_mi},
        "mutual_information_sample_count_for_raw_K": selected_mi_sample_count,
        "precision_rows": [],
        "provenance": {
            "config_sha256": hashlib.sha256(args.config.resolve().read_bytes()).hexdigest(),
            "mi_evidence_sha256": hashlib.sha256(args.mi_evidence.resolve().read_bytes()).hexdigest(),
            "dense_diagnostic_sha256": hashlib.sha256(args.dense_diagnostic.resolve().read_bytes()).hexdigest(),
            "oracle_script_sha256": hashlib.sha256(Path(__file__).resolve().read_bytes()).hexdigest(),
            "backend": f"mpmath {mp.__version__}",
        },
    }
    args.output.resolve().parent.mkdir(parents=True, exist_ok=True)
    if args.append_to_existing:
        existing = json.loads(args.output.resolve().read_text(encoding="utf-8"))
        payload["precision_rows"] = list(existing["precision_rows"])
        existing_digits = {int(row["decimal_digits"]) for row in payload["precision_rows"]}
        if any(value in existing_digits for value in digits):
            raise ValueError("Adaptive append cannot overwrite an existing precision row.")
        payload["executed_decimal_digits"] = [
            value for value in allowed_digits if value in existing_digits or value in digits
        ]
    if args.reuse_existing_precision_rows:
        existing = json.loads(args.output.resolve().read_text(encoding="utf-8"))
        rows_by_digits = {
            int(row["decimal_digits"]): row for row in existing["precision_rows"]
        }
        if set(rows_by_digits) != set(digits):
            raise ValueError("Existing precision rows do not match requested frozen digits.")
        payload["precision_rows"] = [rows_by_digits[value] for value in digits]
    else:
        for value in digits:
            payload["precision_rows"].append(_run_precision(
                value, thresholds=thresholds, states_as_text=states_as_text,
                beta_as_text=repr(float(config["cvqkd"]["beta_reconciliation"])),
            ))
            args.output.resolve().write_text(
                json.dumps(payload, indent=2) + "\n", encoding="utf-8"
            )
            print(f"checkpointed digits={value}", flush=True)
    full_support_rows = [
        row for row in payload["precision_rows"] if bool(row["full_support_resolved"])
    ]
    for row in full_support_rows:
        row["full_mathematical_support_oracle"]["status"] = (
            "FULL_MATHEMATICAL_SUPPORT_RESOLVED"
        )
    payload["full_mathematical_support_oracle_obtained"] = bool(full_support_rows)
    payload["full_support_precision_digits"] = [
        row["decimal_digits"] for row in full_support_rows
    ]
    payload["successive_full_support_confirmation"] = len(full_support_rows) >= 2
    if len(full_support_rows) >= 2:
        previous = full_support_rows[-2]["full_mathematical_support_oracle"]
        current = full_support_rows[-1]["full_mathematical_support_oracle"]
        payload["selected_full_support_oracle_digits"] = full_support_rows[-2][
            "decimal_digits"
        ]
        payload["confirmation_full_support_oracle_digits"] = full_support_rows[-1][
            "decimal_digits"
        ]
        payload["selected_full_support_oracle"] = previous
        with mp.workdps(max(row["decimal_digits"] for row in full_support_rows) + 20):
            payload["successive_full_support_absolute_differences"] = {
                "C": _text(abs(mp.mpf(previous["C"]) - mp.mpf(current["C"])), 40),
                "w": _text(abs(mp.mpf(previous["w"]) - mp.mpf(current["w"])), 40),
                "states": [
                    {
                        name: _text(abs(mp.mpf(left[name]) - mp.mpf(right[name])), 40)
                        for name in ("Z", "lambda1", "lambda2", "lambda3", "chi_BE", "raw_K")
                    }
                    for left, right in zip(previous["states"], current["states"])
                ],
            }
            converges, comparisons = _successive_oracles_converge(
                previous, current, config
            )
            payload["successive_full_support_converges_under_frozen_tolerances"] = (
                converges
            )
            payload["successive_full_support_tolerance_comparisons"] = {
                "C": {
                    key: (_text(value, 40) if key != "passes" else value)
                    for key, value in comparisons["C"].items()
                },
                "w": {
                    key: (_text(value, 40) if key != "passes" else value)
                    for key, value in comparisons["w"].items()
                },
                "states": [
                    {
                        name: {
                            key: (_text(value, 40) if key != "passes" else value)
                            for key, value in metric.items()
                        }
                        for name, metric in state.items()
                    }
                    for state in comparisons["states"]
                ],
            }
    payload["resolved_support_counts_by_digits"] = {
        str(row["decimal_digits"]): row["resolved_positive_eigenvalue_count"]
        for row in payload["precision_rows"]
    }
    estimates = [
        estimate
        for row in payload["precision_rows"]
        for estimate in row["estimated_decimal_digits_for_full_rank_resolution_by_sector"]
        if estimate is not None
    ]
    payload["estimated_decimal_digits_required_for_full_support_resolution"] = max(estimates)
    payload["conclusion"] = (
        "No full-mathematical-support high-precision oracle was obtained; "
        "active-threshold and partial-support values are diagnostic only."
        if not payload["full_mathematical_support_oracle_obtained"]
        else "All 256 physical modes were resolved and successively confirmed at 1250 and 1450 digits."
    )
    args.output.resolve().write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
