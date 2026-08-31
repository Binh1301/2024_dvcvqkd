"""Full-support arbitrary-precision Gram oracles for the frozen confirmation subset."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import time
from typing import Any

import mpmath as mp
import torch

from _common import ROOT, load_yaml
from _numerical_validation import ensemble_sha256, representative_ensembles
from freeze_independent_confirmation_roster import stress_ensemble
from src.cvqkd.mutual_information import discrete_mutual_information, standard_complex_noise
from src.utils.random import torch_generator


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text(value: mp.mpf | mp.mpc, digits: int) -> str:
    return mp.nstr(value, n=digits, strip_zeros=False)


def overlap(alpha_i: mp.mpc, alpha_j: mp.mpc) -> mp.mpc:
    return mp.exp(-(abs(alpha_i) ** 2 + abs(alpha_j) ** 2) / 2 + mp.conj(alpha_i) * alpha_j)


def security_chain(correlation: mp.mpf, penalty: mp.mpf, va: mp.mpf,
                   transmittance: mp.mpf, epsilon: mp.mpf,
                   mutual_information: mp.mpf, beta: mp.mpf) -> dict[str, mp.mpf]:
    z = 2 * mp.sqrt(transmittance) * correlation - mp.sqrt(2 * transmittance * epsilon * penalty)
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
        return (occupation + 1) * mp.log(occupation + 1, 2) - occupation * mp.log(occupation, 2)
    chi = entropy((lambda1 - 1) / 2) + entropy((lambda2 - 1) / 2) - entropy((lambda3 - 1) / 2)
    return {
        "Z": z, "lambda1": lambda1, "lambda2": lambda2, "lambda3": lambda3,
        "chi_BE": chi, "raw_K": beta * mutual_information - chi,
    }


def build_sectors(probabilities: list[mp.mpf], prototypes: list[mp.mpc]) -> list[mp.matrix]:
    blocks: list[mp.matrix] = []
    for difference in range(4):
        rotation = mp.j ** difference
        block = mp.matrix(64)
        for row in range(64):
            for column in range(64):
                block[row, column] = mp.sqrt(probabilities[row] * probabilities[column]) * overlap(
                    prototypes[row], rotation * prototypes[column]
                )
        blocks.append(block)
    sectors: list[mp.matrix] = []
    for sector in range(4):
        matrix = mp.matrix(64)
        for row in range(64):
            for column in range(64):
                matrix[row, column] = mp.fsum(
                    blocks[difference][row, column] * mp.j ** (sector * difference)
                    for difference in range(4)
                )
        sectors.append((matrix + matrix.H) / 2)
    return sectors


def full_support_moments(eigenvalues: list[list[mp.mpf]], eigenvectors: list[mp.matrix],
                         prototypes: list[mp.mpc], symbol_probabilities: list[mp.mpf],
                         floor: mp.mpf) -> dict[str, Any]:
    supports = [[index for index, value in enumerate(values) if value > floor] for values in eigenvalues]
    a_tau_blocks: list[mp.matrix] = []
    correlation = mp.mpf(0)
    for sector in range(4):
        previous = (sector - 1) % 4
        rows, columns = supports[sector], supports[previous]
        block = mp.matrix(len(rows), len(columns))
        for row_position, row_index in enumerate(rows):
            for column_position, column_index in enumerate(columns):
                matrix_element = mp.fsum(
                    mp.conj(eigenvectors[sector][orbit, row_index])
                    * prototypes[orbit]
                    * eigenvectors[previous][orbit, column_index]
                    for orbit in range(64)
                )
                row_value = eigenvalues[sector][row_index]
                column_value = eigenvalues[previous][column_index]
                a_support = mp.sqrt(row_value) * matrix_element / mp.sqrt(column_value)
                correlation += mp.sqrt(row_value * column_value) * abs(a_support) ** 2
                block[row_position, column_position] = mp.sqrt(row_value) * a_support / mp.sqrt(column_value)
        a_tau_blocks.append(block)
    coefficients: list[mp.matrix] = []
    for sector in range(4):
        matrix = mp.matrix(len(supports[sector]), 64)
        for position, eigen_index in enumerate(supports[sector]):
            for orbit in range(64):
                matrix[position, orbit] = (
                    mp.sqrt(eigenvalues[sector][eigen_index])
                    * mp.conj(eigenvectors[sector][orbit, eigen_index])
                    / (2 * mp.sqrt(symbol_probabilities[orbit]))
                )
        coefficients.append(matrix)
    transformed = [a_tau_blocks[sector] * coefficients[(sector - 1) % 4] for sector in range(4)]
    inner = [
        mp.fsum(
            mp.fsum(mp.conj(coefficients[sector][index, orbit]) * transformed[sector][index, orbit]
                    for index in range(len(supports[sector])))
            for sector in range(4)
        )
        for orbit in range(64)
    ]
    first = mp.fsum(
        eigenvalues[(sector - 1) % 4][column_index]
        * abs(a_tau_blocks[sector][row_position, column_position]) ** 2
        for sector in range(4)
        for row_position, _ in enumerate(supports[sector])
        for column_position, column_index in enumerate(supports[(sector - 1) % 4])
    )
    penalty = first - mp.fsum(
        4 * symbol_probabilities[orbit] * abs(inner[orbit]) ** 2 for orbit in range(64)
    )
    return {
        "sector_support_sizes": [len(values) for values in supports],
        "support_size": sum(len(values) for values in supports),
        "C": correlation,
        "w": penalty,
    }


def precision_row(name: str, digits: int, symbol_probability_text: list[str],
                  prototype_text: list[tuple[str, str]], va_text: str,
                  state_text: list[tuple[str, str, str]], beta_text: str,
                  resolution_guard_digits: int) -> dict[str, Any]:
    started = time.perf_counter()
    with mp.workdps(digits):
        probabilities = [mp.mpf(value) for value in symbol_probability_text]
        prototypes = [mp.mpc(real, imag) for real, imag in prototype_text]
        sectors = build_sectors(probabilities, prototypes)
        eigenvalues: list[list[mp.mpf]] = []
        eigenvectors: list[mp.matrix] = []
        for index, sector in enumerate(sectors):
            print(f"fixture={name} digits={digits} sector={index + 1}/4", flush=True)
            values, vectors = mp.eighe(sector)
            eigenvalues.append([mp.re(values[position]) for position in range(64)])
            eigenvectors.append(vectors)
        all_values = sorted(value for sector in eigenvalues for value in sector)
        floor = mp.power(10, -(digits - resolution_guard_digits))
        positive = [value for value in all_values if value > floor]
        moments = full_support_moments(eigenvalues, eigenvectors, prototypes, probabilities, floor)
        va = mp.mpf(va_text)
        beta = mp.mpf(beta_text)
        states = [security_chain(moments["C"], moments["w"], va, mp.mpf(t), mp.mpf(e), mp.mpf(mi), beta)
                  for t, e, mi in state_text]
        return {
            "decimal_digits": digits,
            "runtime_seconds": time.perf_counter() - started,
            "resolution_floor": text(floor, digits),
            "resolved_mathematical_rank": len(positive),
            "full_support_resolved": len(positive) == 256,
            "minimum_eigenvalue": text(all_values[0], digits),
            "smallest_positive_eigenvalue": None if not positive else text(positive[0], digits),
            "largest_eigenvalue": text(all_values[-1], digits),
            "condition_number": None if not positive else text(all_values[-1] / positive[0], digits),
            "trace_residual": text(abs(mp.fsum(all_values) - 1), digits),
            "sector_support_sizes": moments["sector_support_sizes"],
            "C": text(moments["C"], digits),
            "w": text(moments["w"], digits),
            "states": [{key: text(value, digits) for key, value in state.items()} for state in states],
        }


def run(config_path: Path, default_path: Path, roster_path: Path, roster_config_path: Path,
        environment_path: Path, schema_path: Path, output_path: Path,
        reuse_initial_path: Path | None) -> dict[str, Any]:
    settings = load_yaml(config_path)
    default = load_yaml(default_path)
    roster_design = load_yaml(roster_config_path)
    roster = json.loads(roster_path.read_text(encoding="utf-8"))
    reusable: dict[tuple[str, int], dict[str, Any]] = {}
    if reuse_initial_path is not None:
        initial = json.loads(reuse_initial_path.read_text(encoding="utf-8"))
        if initial["confirmation_roster_sha256"] != sha256(roster_path):
            raise ValueError("Reusable oracle artifact has a different roster hash.")
        for fixture in initial["oracle_fixture_rows"]:
            for row in fixture["precision_rows"]:
                reusable[(fixture["fixture"], int(row["decimal_digits"]))] = row
    if settings["threshold_approval_permitted"] or settings["final_test_access_permitted"]:
        raise ValueError("Oracle expansion must not approve thresholds or access final-test data.")
    state_rows = roster["representative_states"]
    t = torch.tensor([row["transmittance"] for row in state_rows], dtype=torch.float64)
    epsilon = torch.tensor([row["epsilon_snu"] for row in state_rows], dtype=torch.float64)
    fixture_config = copy.deepcopy(default)
    fixture_config["numerical_validation"]["fixture_initialization_seed"] = int(roster_design["fixture_initialization_seed"])
    ensembles = representative_ensembles(fixture_config, t, epsilon)
    ensembles.pop("near_coincident_pseudoinverse_stress", None)
    for phase in roster_design["near_coincident_phase_steps_rad"]:
        ensembles[f"near_coincident_phase_step_{float(phase):g}"] = stress_ensemble(
            float(phase), batch_size=3, v_max=float(default["cvqkd"]["v_max_snu"]),
            n_peak=float(default["cvqkd"]["n_peak_photons"]),
        )
    roster_hashes = {row["name"]: row["ensemble_sha256"] for row in roster["fixtures"]}
    oracle_names = roster["oracle_subset"]
    for name in oracle_names:
        if ensemble_sha256(ensembles[name]) != roster_hashes[name]:
            raise ValueError(f"Reconstructed oracle fixture hash mismatch: {name}")

    beta = float(default["cvqkd"]["beta_reconciliation"])
    output_rows = []
    for name in oracle_names:
        ensemble = ensembles[name]
        noise = standard_complex_noise(
            (3, 256, int(settings["mi_sample_count"])),
            generator=torch_generator(int(settings["mi_seed"]), "cpu"), device="cpu",
        )
        mi = discrete_mutual_information(
            ensemble, t, epsilon,
            noise_samples_per_symbol=int(settings["mi_sample_count"]),
            standard_noise_samples=noise, noise_sample_chunk_size=64,
        ).detach()
        from src.modulation.qam256 import c4_orbit_indices
        indices = c4_orbit_indices()
        probabilities = ensemble.probabilities[0, indices[:, 0]].detach().tolist()
        prototypes = ensemble.amplitudes[0, indices[:, 0]].detach().tolist()
        fixture_class = next(row["configuration_class"] for row in roster["fixtures"] if row["name"] == name)
        digits_sequence = settings["precision_sequences"][
            "analytic_near_coincident" if fixture_class == "analytic_near_coincident" else "regular"
        ]
        rows = []
        for digits in digits_sequence:
            key = (name, int(digits))
            rows.append(reusable[key] if key in reusable else precision_row(
                name, int(digits), [repr(float(value)) for value in probabilities],
                [(repr(complex(value).real), repr(complex(value).imag)) for value in prototypes],
                repr(float(ensemble.declared_va[0])),
                [(repr(float(t[index])), repr(float(epsilon[index])), repr(float(mi[index]))) for index in range(3)],
                repr(beta), int(settings["resolution_guard_digits"]),
            ))
        full_rows = [row for row in rows if row["full_support_resolved"]]
        converged = False
        convergence = None
        if len(full_rows) >= 2:
            left, right = full_rows[-2], full_rows[-1]
            with mp.workdps(max(int(left["decimal_digits"]), int(right["decimal_digits"])) + 50):
                differences = {
                    "C": abs(mp.mpf(left["C"]) - mp.mpf(right["C"])),
                    "w": abs(mp.mpf(left["w"]) - mp.mpf(right["w"])),
                }
                for state_index in range(3):
                    for metric in ("Z", "lambda1", "lambda2", "lambda3", "chi_BE", "raw_K"):
                        differences[f"state_{state_index}_{metric}"] = abs(
                            mp.mpf(left["states"][state_index][metric]) - mp.mpf(right["states"][state_index][metric])
                        )
                maximum = max(differences.values())
                converged = maximum < mp.mpf("1e-10")
                convergence = {
                    "maximum_successive_full_support_difference": mp.nstr(maximum, 30),
                    "passes_1e_minus_10": converged,
                    "comparison_decimal_digits": mp.mp.dps,
                }
        output_rows.append({
            "fixture": name,
            "fixture_class": fixture_class,
            "ensemble_sha256": roster_hashes[name],
            "mi_sample_count": int(settings["mi_sample_count"]),
            "mi_seed": int(settings["mi_seed"]),
            "mi_bits": [float(value) for value in mi],
            "precision_rows": rows,
            "full_support_precision_count": len(full_rows),
            "successive_full_support_converged": converged,
            "convergence": convergence,
        })
    all_pass = all(
        row["full_support_precision_count"] >= int(settings["full_support_confirmation_required"])
        and row["successive_full_support_converged"] for row in output_rows
    )
    artifact = {
        "schema_version": "independent-confirmation-gram-oracles-v1",
        "status": "MULTI_FIXTURE_FULL_SUPPORT_ORACLE_PASS" if all_pass else "MULTI_FIXTURE_FULL_SUPPORT_ORACLE_INCOMPLETE",
        "confirmation_roster_sha256": sha256(roster_path),
        "confirmation_roster_payload_sha256": roster["roster_payload_sha256"],
        "oracle_fixture_rows": output_rows,
        "aggregate": {
            "fixture_count": len(output_rows),
            "fixtures_with_two_full_support_precisions": sum(row["full_support_precision_count"] >= 2 for row in output_rows),
            "fixtures_successively_converged": sum(row["successive_full_support_converged"] for row in output_rows),
            "all_oracle_requirements_pass": all_pass,
        },
        "lifecycle_guards": {
            "threshold_approved": False, "publication_training_performed": False,
            "final_test_accessed": False, "optimized_mb_grid_performed": False,
            "baseline_selection_performed": False,
        },
        "provenance": {
            "repository_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "producer_sha256": sha256(Path(__file__).resolve()),
            "config_sha256": sha256(config_path),
            "default_config_sha256": sha256(default_path),
            "roster_sha256": sha256(roster_path),
            "roster_config_sha256": sha256(roster_config_path),
            "environment_manifest_sha256": sha256(environment_path),
            "schema_sha256": sha256(schema_path),
            "final_model_spec_sha256": sha256(ROOT / "docs" / "FINAL_MODEL_SPEC.md"),
            "reused_initial_artifact_sha256": (
                None if reuse_initial_path is None else sha256(reuse_initial_path)
            ),
        },
    }
    output_path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return artifact


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "independent_confirmation_oracle.yaml")
    parser.add_argument("--default-config", type=Path, default=ROOT / "configs" / "default.yaml")
    parser.add_argument("--roster", type=Path, default=ROOT / "results" / "independent_confirmation_roster.json")
    parser.add_argument("--roster-config", type=Path, default=ROOT / "configs" / "independent_confirmation_roster.yaml")
    parser.add_argument("--environment", type=Path, default=ROOT / "results" / "current_environment_manifest.json")
    parser.add_argument("--schema", type=Path, default=ROOT / "schemas" / "independent_confirmation_gram_oracles.schema.json")
    parser.add_argument("--output", type=Path, default=ROOT / "results" / "independent_confirmation_gram_oracles.json")
    parser.add_argument("--reuse-initial", type=Path, default=ROOT / "results" / "independent_confirmation_gram_oracles_initial.json")
    args = parser.parse_args()
    artifact = run(
        args.config, args.default_config, args.roster, args.roster_config,
        args.environment, args.schema, args.output,
        args.reuse_initial if args.reuse_initial.exists() else None,
    )
    print(json.dumps({"status": artifact["status"], **artifact["aggregate"]}, sort_keys=True))


if __name__ == "__main__":
    main()
