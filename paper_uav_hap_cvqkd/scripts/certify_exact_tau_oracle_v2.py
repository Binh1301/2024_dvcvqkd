"""Independent exact-candidate-threshold oracle for the four frozen fixtures.

The arbitrary-precision mpmath eigensystem is used only to propose narrow
dyadic eigenvalue brackets.  Every support count and every accepted bracket is
proved independently with Arb/acb shifted Hermitian inertia.  No complex128
eigensystem or support count participates in this producer.

Real-fixture execution requires the explicit command-line flag
``--execute-frozen-real-fixtures``.  This makes synthetic regression runs safe
before the parent V2 protocol has prospectively bound this producer's hash.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import subprocess
import time
from typing import Any, Sequence

from flint import acb, arb, ctx
import mpmath as mp
import torch

from _common import ROOT, load_yaml
from _numerical_validation import ensemble_sha256, representative_ensembles
from freeze_independent_confirmation_roster import stress_ensemble
from oracle_independent_confirmation_gram import build_sectors as build_mp_sectors
from src.modulation.qam256 import c4_orbit_indices
from src.validation.rigorous_flint_support import exact_arb_from_float_hex
from src.validation.rigorous_shifted_inertia import (
    shift_hermitian,
    verified_block_ldl_inertia,
)


I = acb(0, 1)
EXPECTED_ROSTER_SHA256 = "a9362ee752be5e9eeb5c0152574d0909a95bf7927e48be727ad9a9534600c1de"
EXACT_CANDIDATE_TAU_HEX = "0x1.c25c268497682p-44"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exact_dyadic_from_float_hex(value: str) -> tuple[int, int]:
    """Return ``(numerator, denominator_power_two)`` for finite binary64."""

    binary = float.fromhex(value)
    if not math.isfinite(binary):
        raise ValueError("Exact-threshold inputs must be finite binary64 values.")
    numerator, denominator = binary.as_integer_ratio()
    if denominator & (denominator - 1):
        raise ValueError("binary64 denominator is not a power of two.")
    return numerator, denominator.bit_length() - 1


def mp_from_binary64(value: float) -> mp.mpf:
    """Lift a binary64 value to its exact dyadic value in mpmath."""

    numerator, denominator = float(value).as_integer_ratio()
    return mp.mpf(numerator) / denominator


def mpc_from_binary64(value: complex) -> mp.mpc:
    return mp.mpc(mp_from_binary64(float(value.real)), mp_from_binary64(float(value.imag)))


def _arb_from_dyadic(numerator: int, denominator_power_two: int) -> arb:
    return arb((int(numerator), -int(denominator_power_two)))


def _dyadic_payload(numerator: int, denominator_power_two: int, digits: int = 50) -> dict[str, Any]:
    with mp.workdps(digits + 10):
        value = mp.mpf(numerator) / mp.power(2, denominator_power_two)
        decimal = mp.nstr(value, digits, strip_zeros=False)
    return {
        "numerator": str(int(numerator)),
        "denominator_power_two": int(denominator_power_two),
        "rational": f"{int(numerator)}/2^{int(denominator_power_two)}",
        "decimal": decimal,
    }


def exact_tau_payload() -> dict[str, Any]:
    numerator, exponent = exact_dyadic_from_float_hex(EXACT_CANDIDATE_TAU_HEX)
    return {"binary64_hex": EXACT_CANDIDATE_TAU_HEX, **_dyadic_payload(numerator, exponent, 40)}


def arb_sectors_from_binary64(
    probabilities: Sequence[float], prototypes: Sequence[complex]
) -> list[list[list[acb]]]:
    """Construct exact-binary64 C4 sectors using inclusion arithmetic only."""

    if len(probabilities) != 64 or len(prototypes) != 64:
        raise ValueError("A C4 oracle fixture must contain 64 orbit representatives.")
    p = [exact_arb_from_float_hex(float(value).hex()) for value in probabilities]
    z = [
        acb(
            exact_arb_from_float_hex(float(value.real).hex()),
            exact_arb_from_float_hex(float(value.imag).hex()),
        )
        for value in prototypes
    ]
    rotations = [acb(1), I, acb(-1), -I]
    sectors = []
    for sector in range(4):
        raw = [[acb(0) for _ in range(64)] for _ in range(64)]
        for row in range(64):
            for column in range(64):
                root_probability = (p[row] * p[column]).sqrt()
                value = acb(0)
                for difference in range(4):
                    left = z[row]
                    right = rotations[difference] * z[column]
                    left_energy = left.real * left.real + left.imag * left.imag
                    right_energy = right.real * right.real + right.imag * right.imag
                    overlap = (
                        acb(-(left_energy + right_energy) / 2)
                        + left.conjugate() * right
                    ).exp()
                    value += root_probability * overlap * (I ** (sector * difference))
                raw[row][column] = value
        sectors.append(
            [
                [
                    (raw[row][column] + raw[column][row].conjugate()) / 2
                    for column in range(64)
                ]
                for row in range(64)
            ]
        )
    return sectors


def _compact_inertia(result: dict[str, Any], sector: int) -> dict[str, Any]:
    pivots = result.get("pivot_rows", [])
    return {
        "sector": int(sector),
        "status": result["status"],
        "n_positive": int(result["n_positive"]),
        "n_negative": int(result["n_negative"]),
        "n_zero_or_unresolved": int(result["n_zero_or_unresolved"]),
        "precision_bits": int(result["precision_bits"]),
        "minimum_certified_signed_margin": result.get("minimum_certified_signed_margin"),
        "one_by_one_pivot_count": sum(row["block_size"] == 1 for row in pivots),
        "two_by_two_pivot_count": sum(row["block_size"] == 2 for row in pivots),
        "pivot_rows": pivots,
        "runtime_seconds": float(result["runtime_seconds"]),
        "failure_reason": result.get("failure_reason"),
    }


def certify_inertia_at_dyadic_threshold(
    sectors: Sequence[Sequence[Sequence[acb]]],
    threshold_numerator: int,
    threshold_denominator_power_two: int,
    *,
    precision_bits: Sequence[int],
    maximum_seconds_per_point: float,
) -> dict[str, Any]:
    """Certify aggregate inertia at one exact dyadic threshold, fail closed."""

    attempts = []
    threshold = _arb_from_dyadic(threshold_numerator, threshold_denominator_power_two)
    for bits in precision_bits:
        ctx.prec = int(bits)
        sector_rows = []
        for sector_index, sector in enumerate(sectors):
            result = verified_block_ldl_inertia(
                shift_hermitian(sector, threshold),
                precision_bits=int(bits),
                maximum_seconds=float(maximum_seconds_per_point),
            )
            sector_rows.append(_compact_inertia(result, sector_index))
            if result["status"] != "CERTIFIED_INERTIA":
                break
        missing_dimension = sum(len(sector) for sector in sectors[len(sector_rows) :])
        certified = len(sector_rows) == len(sectors) and all(
            row["status"] == "CERTIFIED_INERTIA" for row in sector_rows
        )
        attempt = {
            "precision_bits": int(bits),
            "status": "CERTIFIED_INERTIA" if certified else "UNCERTIFIED",
            "n_positive": sum(row["n_positive"] for row in sector_rows),
            "n_negative": sum(row["n_negative"] for row in sector_rows),
            "n_zero_or_unresolved": (
                sum(row["n_zero_or_unresolved"] for row in sector_rows)
                + missing_dimension
            ),
            "sector_rows": sector_rows,
        }
        attempts.append(attempt)
        if certified:
            return {**attempt, "threshold": _dyadic_payload(
                threshold_numerator, threshold_denominator_power_two
            ), "attempts": attempts}
    last = attempts[-1]
    return {**last, "threshold": _dyadic_payload(
        threshold_numerator, threshold_denominator_power_two
    ), "attempts": attempts}


def _dyadic_floor(value: mp.mpf, denominator_power_two: int) -> int:
    return int(mp.floor(value * mp.power(2, denominator_power_two)))


def prove_eigenvalue_bracket(
    sectors: Sequence[Sequence[Sequence[acb]]],
    approximate_eigenvalue: mp.mpf,
    *,
    expected_below_at_left: int,
    expected_below_at_right: int,
    bracket_denominator_power_two: int,
    maximum_expansions: int,
    precision_bits: Sequence[int],
    maximum_seconds_per_point: float,
) -> dict[str, Any]:
    """Prove a one-eigenvalue dyadic bracket using only inertia counts."""

    center_floor = _dyadic_floor(approximate_eigenvalue, bracket_denominator_power_two)
    attempts = []
    for expansion_index in range(maximum_expansions + 1):
        expansion = (1 << expansion_index) - 1
        left_numerator = center_floor - expansion
        right_numerator = center_floor + 1 + expansion
        left = certify_inertia_at_dyadic_threshold(
            sectors,
            left_numerator,
            bracket_denominator_power_two,
            precision_bits=precision_bits,
            maximum_seconds_per_point=maximum_seconds_per_point,
        )
        right = certify_inertia_at_dyadic_threshold(
            sectors,
            right_numerator,
            bracket_denominator_power_two,
            precision_bits=precision_bits,
            maximum_seconds_per_point=maximum_seconds_per_point,
        )
        accepted = (
            left["status"] == "CERTIFIED_INERTIA"
            and right["status"] == "CERTIFIED_INERTIA"
            and left["n_negative"] == expected_below_at_left
            and right["n_negative"] == expected_below_at_right
            and right["n_negative"] - left["n_negative"] == 1
            and left["n_zero_or_unresolved"] == 0
            and right["n_zero_or_unresolved"] == 0
        )
        attempts.append({
            "expansion_index": expansion_index,
            "left": left,
            "right": right,
            "accepted": accepted,
        })
        if accepted:
            return {
                "status": "CERTIFIED_SINGLE_EIGENVALUE_BRACKET",
                "lower": _dyadic_payload(left_numerator, bracket_denominator_power_two),
                "upper": _dyadic_payload(right_numerator, bracket_denominator_power_two),
                "certified_eigenvalue_count_in_open_bracket": 1,
                "below_count_at_lower": int(left["n_negative"]),
                "below_count_at_upper": int(right["n_negative"]),
                "attempts": attempts,
            }
    return {"status": "UNCERTIFIED_EIGENVALUE_BRACKET", "attempts": attempts}


def certified_distance_from_tau(
    bracket: dict[str, Any], *, tau_numerator: int, tau_denominator_power_two: int,
    side: str,
) -> dict[str, Any]:
    """Return a positive exact dyadic interval for distance from tau."""

    if bracket["status"] != "CERTIFIED_SINGLE_EIGENVALUE_BRACKET":
        return {"status": "UNCERTIFIED_DISTANCE"}
    common_power = max(
        tau_denominator_power_two,
        int(bracket["lower"]["denominator_power_two"]),
        int(bracket["upper"]["denominator_power_two"]),
    )
    tau = tau_numerator << (common_power - tau_denominator_power_two)
    lower = int(bracket["lower"]["numerator"]) << (
        common_power - int(bracket["lower"]["denominator_power_two"])
    )
    upper = int(bracket["upper"]["numerator"]) << (
        common_power - int(bracket["upper"]["denominator_power_two"])
    )
    if side == "BELOW":
        distance_lower, distance_upper = tau - upper, tau - lower
    elif side == "ABOVE":
        distance_lower, distance_upper = lower - tau, upper - tau
    else:
        raise ValueError("Distance side must be BELOW or ABOVE.")
    if distance_lower <= 0:
        return {"status": "UNCERTIFIED_DISTANCE", "reason": "BRACKET_NOT_STRICTLY_ON_SIDE"}
    return {
        "status": "CERTIFIED_POSITIVE_DISTANCE_INTERVAL",
        "lower": _dyadic_payload(distance_lower, common_power),
        "upper": _dyadic_payload(distance_upper, common_power),
    }


def high_precision_spectrum(
    probabilities: Sequence[float], prototypes: Sequence[complex], decimal_digits: int
) -> dict[str, Any]:
    """Compute an independent mpmath spectrum from exact binary64 inputs."""

    started = time.perf_counter()
    with mp.workdps(int(decimal_digits)):
        mp_probabilities = [mp_from_binary64(value) for value in probabilities]
        mp_prototypes = [mpc_from_binary64(value) for value in prototypes]
        sectors = build_mp_sectors(mp_probabilities, mp_prototypes)
        sector_values = []
        for sector in sectors:
            values = mp.eigvalsh(sector)
            sector_values.append([mp.re(values[index]) for index in range(len(values))])
        flattened = sorted(value for values in sector_values for value in values)
        floor = mp.power(10, -(int(decimal_digits) - 10))
        return {
            "decimal_digits": int(decimal_digits),
            "arithmetic": "mpmath arbitrary precision; exact binary64 dyadic fixture inputs",
            "spectrum_is_rigorous_interval_proof": False,
            "resolution_floor": mp.nstr(floor, decimal_digits, strip_zeros=False),
            "resolved_positive_count_above_floor": sum(value > floor for value in flattened),
            "sector_eigenvalues": [
                [mp.nstr(value, decimal_digits, strip_zeros=False) for value in values]
                for values in sector_values
            ],
            "trace_residual": mp.nstr(abs(mp.fsum(flattened) - 1), 50),
            "runtime_seconds": time.perf_counter() - started,
            "_flattened": flattened,
        }


def certify_fixture(
    name: str,
    probabilities: Sequence[float],
    prototypes: Sequence[complex],
    *,
    decimal_digits: int,
    precision_bits: Sequence[int],
    bracket_denominator_power_two: int,
    maximum_bracket_expansions: int,
    maximum_seconds_per_point: float,
) -> dict[str, Any]:
    """Run the independent spectrum plus validated exact-tau proof chain."""

    started = time.perf_counter()
    spectrum = high_precision_spectrum(probabilities, prototypes, decimal_digits)
    flattened = spectrum.pop("_flattened")
    tau_numerator, tau_power = exact_dyadic_from_float_hex(EXACT_CANDIDATE_TAU_HEX)
    with mp.workdps(int(decimal_digits)):
        exact_tau_mp = mp.mpf(tau_numerator) / mp.power(2, tau_power)
        approximate_below = sum(value < exact_tau_mp for value in flattened)
        approximate_above = sum(value > exact_tau_mp for value in flattened)
        approximate_equal = len(flattened) - approximate_below - approximate_above

    ctx.prec = max(int(value) for value in precision_bits)
    sectors = arb_sectors_from_binary64(probabilities, prototypes)
    at_tau = certify_inertia_at_dyadic_threshold(
        sectors,
        tau_numerator,
        tau_power,
        precision_bits=precision_bits,
        maximum_seconds_per_point=maximum_seconds_per_point,
    )
    if at_tau["status"] != "CERTIFIED_INERTIA" or at_tau["n_zero_or_unresolved"] != 0:
        return {
            "fixture": name,
            "status": "UNCERTIFIED_EXACT_TAU_SUPPORT",
            "exact_candidate_tau": exact_tau_payload(),
            "arbitrary_precision_spectrum": spectrum,
            "arbitrary_precision_diagnostic_counts": {
                "above_tau": approximate_above,
                "below_tau": approximate_below,
                "equal_or_unordered_at_tau": approximate_equal,
            },
            "validated_inertia_at_tau": at_tau,
            "runtime_seconds": time.perf_counter() - started,
        }

    below_count = int(at_tau["n_negative"])
    above_count = int(at_tau["n_positive"])
    if below_count == 0 or above_count == 0:
        raise ValueError("Exact tau does not lie strictly inside the fixture spectrum.")
    below_bracket = prove_eigenvalue_bracket(
        sectors,
        flattened[below_count - 1],
        expected_below_at_left=below_count - 1,
        expected_below_at_right=below_count,
        bracket_denominator_power_two=bracket_denominator_power_two,
        maximum_expansions=maximum_bracket_expansions,
        precision_bits=precision_bits,
        maximum_seconds_per_point=maximum_seconds_per_point,
    )
    above_bracket = prove_eigenvalue_bracket(
        sectors,
        flattened[below_count],
        expected_below_at_left=below_count,
        expected_below_at_right=below_count + 1,
        bracket_denominator_power_two=bracket_denominator_power_two,
        maximum_expansions=maximum_bracket_expansions,
        precision_bits=precision_bits,
        maximum_seconds_per_point=maximum_seconds_per_point,
    )
    below_distance = certified_distance_from_tau(
        below_bracket,
        tau_numerator=tau_numerator,
        tau_denominator_power_two=tau_power,
        side="BELOW",
    )
    above_distance = certified_distance_from_tau(
        above_bracket,
        tau_numerator=tau_numerator,
        tau_denominator_power_two=tau_power,
        side="ABOVE",
    )
    complete = (
        below_bracket["status"] == "CERTIFIED_SINGLE_EIGENVALUE_BRACKET"
        and above_bracket["status"] == "CERTIFIED_SINGLE_EIGENVALUE_BRACKET"
        and below_distance["status"] == "CERTIFIED_POSITIVE_DISTANCE_INTERVAL"
        and above_distance["status"] == "CERTIFIED_POSITIVE_DISTANCE_INTERVAL"
        and approximate_below == below_count
        and approximate_above == above_count
        and approximate_equal == 0
    )
    return {
        "fixture": name,
        "status": "CERTIFIED_EXACT_TAU_SUPPORT_AND_NEAREST_GAPS" if complete else "UNCERTIFIED_EXACT_TAU_GAPS",
        "exact_candidate_tau": exact_tau_payload(),
        "arbitrary_precision_spectrum": spectrum,
        "arbitrary_precision_diagnostic_counts": {
            "above_tau": approximate_above,
            "below_tau": approximate_below,
            "equal_or_unordered_at_tau": approximate_equal,
        },
        "validated_inertia_at_tau": at_tau,
        "number_rigorously_above_tau": above_count,
        "number_rigorously_below_tau": below_count,
        "number_unresolved_against_tau": int(at_tau["n_zero_or_unresolved"]),
        "closest_eigenvalue_below_tau": {
            "bracket": below_bracket,
            "certified_distance_from_tau": below_distance,
        },
        "closest_eigenvalue_above_tau": {
            "bracket": above_bracket,
            "certified_distance_from_tau": above_distance,
        },
        "complex128_reference_used": False,
        "runtime_seconds": time.perf_counter() - started,
    }


def _component_settings(settings: dict[str, Any]) -> dict[str, Any]:
    return settings.get("exact_tau_oracle", settings)


def verify_frozen_inputs(config_path: Path, settings: dict[str, Any]) -> dict[str, str]:
    component = _component_settings(settings)
    if component["candidate_threshold_float64_hex"] != EXACT_CANDIDATE_TAU_HEX:
        raise ValueError("V2 exact-tau producer accepts only the frozen candidate binary64 value.")
    if component.get("threshold_approval_permitted", False):
        raise ValueError("Exact-tau oracle cannot approve a threshold.")
    if component.get("final_test_access_permitted", False):
        raise ValueError("Exact-tau oracle cannot access final-test data.")
    observed = {}
    for relative, expected in component["required_input_sha256"].items():
        path = ROOT / relative
        digest = sha256(path)
        observed[relative] = digest
        if digest != expected:
            raise ValueError(f"PROVENANCE_FAILURE: {relative} SHA-256 mismatch")
    producer_expected = component["producer_sha256"]
    producer_observed = sha256(Path(__file__).resolve())
    if producer_observed != producer_expected:
        raise ValueError("PROVENANCE_FAILURE: exact-tau producer SHA-256 mismatch")
    roster_path = ROOT / component["confirmation_roster"]
    if sha256(roster_path) != EXPECTED_ROSTER_SHA256:
        raise ValueError("PROVENANCE_FAILURE: confirmation roster is not the frozen roster")
    observed[str(config_path.relative_to(ROOT))] = sha256(config_path)
    observed[str(Path(__file__).resolve().relative_to(ROOT))] = producer_observed
    return observed


def _reconstruct_oracle_fixtures(component: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    roster_path = ROOT / component["confirmation_roster"]
    roster = json.loads(roster_path.read_text(encoding="utf-8"))
    default = load_yaml(ROOT / component["default_config"])
    roster_design = load_yaml(ROOT / component["confirmation_roster_config"])
    states = roster["representative_states"]
    transmittance = torch.tensor([row["transmittance"] for row in states], dtype=torch.float64)
    epsilon = torch.tensor([row["epsilon_snu"] for row in states], dtype=torch.float64)
    fixture_config = copy.deepcopy(default)
    fixture_config["numerical_validation"]["fixture_initialization_seed"] = int(
        roster_design["fixture_initialization_seed"]
    )
    ensembles = representative_ensembles(fixture_config, transmittance, epsilon)
    ensembles.pop("near_coincident_pseudoinverse_stress", None)
    for phase in roster_design["near_coincident_phase_steps_rad"]:
        ensembles[f"near_coincident_phase_step_{float(phase):g}"] = stress_ensemble(
            float(phase),
            batch_size=3,
            v_max=float(default["cvqkd"]["v_max_snu"]),
            n_peak=float(default["cvqkd"]["n_peak_photons"]),
        )
    roster_hashes = {row["name"]: row["ensemble_sha256"] for row in roster["fixtures"]}
    if roster["oracle_subset"] != component["oracle_fixtures"]:
        raise ValueError("PROVENANCE_FAILURE: configured oracle subset differs from frozen roster")
    for name in roster["oracle_subset"]:
        if ensemble_sha256(ensembles[name]) != roster_hashes[name]:
            raise ValueError(f"PROVENANCE_FAILURE: reconstructed fixture hash mismatch: {name}")
    return roster, ensembles


def run(config_path: Path, output_path: Path) -> dict[str, Any]:
    settings = load_yaml(config_path)
    component = _component_settings(settings)
    observed_hashes = verify_frozen_inputs(config_path, settings)
    roster, ensembles = _reconstruct_oracle_fixtures(component)
    indices = c4_orbit_indices()[:, 0]
    roster_rows = {row["name"]: row for row in roster["fixtures"]}
    started = time.perf_counter()
    rows = []
    for name in component["oracle_fixtures"]:
        ensemble = ensembles[name]
        probabilities = [float(value) for value in ensemble.probabilities[0, indices].tolist()]
        prototypes = [complex(value) for value in ensemble.amplitudes[0, indices].tolist()]
        fixture_class = roster_rows[name]["configuration_class"]
        digits = int(component["decimal_digits_by_class"][fixture_class])
        row = certify_fixture(
            name,
            probabilities,
            prototypes,
            decimal_digits=digits,
            precision_bits=[int(value) for value in component["arb_precision_bits"]],
            bracket_denominator_power_two=int(component["bracket_denominator_power_two"]),
            maximum_bracket_expansions=int(component["maximum_bracket_expansions"]),
            maximum_seconds_per_point=float(component["maximum_seconds_per_inertia_point"]),
        )
        row["ensemble_sha256"] = roster_rows[name]["ensemble_sha256"]
        rows.append(row)
    all_pass = all(row["status"] == "CERTIFIED_EXACT_TAU_SUPPORT_AND_NEAREST_GAPS" for row in rows)
    artifact = {
        "schema_version": "exact-tau-oracle-v2",
        "status": "EXACT_TAU_ORACLE_CERTIFIED" if all_pass else "EXACT_TAU_ORACLE_FAIL_CLOSED",
        "candidate_threshold_status": "PROPOSED_UNAPPROVED",
        "exact_candidate_tau": exact_tau_payload(),
        "fixture_rows": rows,
        "aggregate": {
            "fixture_count": len(rows),
            "certified_fixture_count": sum(
                row["status"] == "CERTIFIED_EXACT_TAU_SUPPORT_AND_NEAREST_GAPS" for row in rows
            ),
            "unresolved_fixture_count": sum(
                row["status"] != "CERTIFIED_EXACT_TAU_SUPPORT_AND_NEAREST_GAPS" for row in rows
            ),
            "complex128_reference_used": False,
            "runtime_seconds": time.perf_counter() - started,
        },
        "lifecycle_guards": {
            "threshold_approved": False,
            "publication_training_performed": False,
            "final_test_accessed": False,
            "optimized_mb_grid_performed": False,
            "baseline_selection_performed": False,
            "security_functional_changed": False,
        },
        "provenance": {
            "repository_commit": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            "worktree_dirty": bool(subprocess.check_output(
                ["git", "status", "--porcelain"], cwd=ROOT, text=True
            ).strip()),
            "config_sha256": sha256(config_path),
            "producer_sha256": sha256(Path(__file__).resolve()),
            "observed_required_sha256": observed_hashes,
            "confirmation_roster_sha256": sha256(ROOT / component["confirmation_roster"]),
            "final_model_spec_sha256": sha256(ROOT / "docs" / "FINAL_MODEL_SPEC.md"),
        },
    }
    output_path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return artifact


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "results" / "exact_tau_oracle_v2.json",
    )
    parser.add_argument("--execute-frozen-real-fixtures", action="store_true")
    args = parser.parse_args()
    if not args.execute_frozen_real_fixtures:
        raise SystemExit(
            "Refusing real-fixture execution without --execute-frozen-real-fixtures; "
            "freeze and commit the parent V2 protocol first."
        )
    artifact = run(args.config.resolve(), args.output.resolve())
    print(json.dumps({"status": artifact["status"], "aggregate": artifact["aggregate"]}, indent=2))


if __name__ == "__main__":
    main()
