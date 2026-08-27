"""Fail-closed publication-selection manifest validation.

The held-out evaluator accepts no free numerical or analysis choices.  Every
choice must be recorded before test access in one immutable JSON manifest.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import re
from typing import Any

from src.validation.physical_domain import approved_peak_photon_limit


MANIFEST_VERSION = "publication-selection-manifest-v1"
LEARNED_MODES = ("ps", "gs", "va", "ps_gs", "ps_va", "gs_va", "full")
FIXED_VA_LEARNED_MODES = ("ps", "gs", "ps_gs")
ARTIFACT_KEYS = (
    "resolved_config", "baseline_selection", "learned_selection",
    "convergence_evidence", "environment_lock", "attempted_seed_accounting",
)
_SHA256 = re.compile(r"[0-9a-f]{64}")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_sha256(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _require_mapping(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object.")
    return value


def validate_publication_manifest(manifest: dict[str, Any]) -> None:
    """Validate all gates that must be frozen before held-out test access."""

    if manifest.get("schema_version") != MANIFEST_VERSION:
        raise ValueError(f"schema_version must be {MANIFEST_VERSION!r}.")
    if manifest.get("status") != "selections-and-analysis-frozen-before-test":
        raise ValueError("Manifest status does not authorize held-out evaluation.")
    if manifest.get("test_set_accessed_during_selection") is not False:
        raise ValueError("Manifest must attest that selection never accessed the test set.")
    for key in (
        "resolved_config_sha256", "validation_state_sha256",
        "baseline_selection_sha256", "learned_selection_sha256",
        "convergence_evidence_sha256", "environment_lock_sha256",
        "attempted_seed_accounting_sha256", "git_revision",
    ):
        value = manifest.get(key)
        valid = (
            isinstance(value, str) and len(value) >= 7
            if key == "git_revision"
            else isinstance(value, str) and _SHA256.fullmatch(value) is not None
        )
        if not valid:
            raise ValueError(f"Manifest field {key!r} must be a nonempty hash/revision.")
    artifact_paths = _require_mapping(manifest.get("artifact_paths"), "artifact_paths")
    if set(artifact_paths) != set(ARTIFACT_KEYS) or any(
        not isinstance(value, str) or not value for value in artifact_paths.values()
    ):
        raise ValueError("artifact_paths must bind every frozen selection/provenance artifact.")

    evaluation = _require_mapping(manifest.get("test_evaluation"), "test_evaluation")
    required_positive = ("fading_samples", "awgn_samples_per_symbol")
    for key in required_positive:
        if not isinstance(evaluation.get(key), int) or evaluation[key] <= 0:
            raise ValueError(f"test_evaluation.{key} must be a positive integer.")
    seeds = (evaluation.get("channel_seed"), evaluation.get("awgn_seed"))
    if any(not isinstance(seed, int) or seed < 0 for seed in seeds) or seeds[0] == seeds[1]:
        raise ValueError("Held-out channel/AWGN seeds must be distinct nonnegative integers.")

    analysis = _require_mapping(manifest.get("analysis_plan"), "analysis_plan")
    for key in ("t_bin_edges", "epsilon_bin_edges", "va_heatmap_t_grid",
                "va_heatmap_epsilon_grid"):
        values = analysis.get(key)
        if not isinstance(values, list) or len(values) < 2 or any(
            not isinstance(value, (float, int)) or not math.isfinite(value)
            for value in values
        ) or any(right <= left for left, right in zip(values, values[1:])):
            raise ValueError(f"analysis_plan.{key} must be a finite increasing grid.")
    if analysis["t_bin_edges"][0] < 0.0 or analysis["t_bin_edges"][-1] > 1.0:
        raise ValueError("Transmittance bin edges must lie in [0,1].")
    if analysis["epsilon_bin_edges"][0] < 0.0:
        raise ValueError("Excess-noise bin edges must be nonnegative.")
    if not isinstance(analysis.get("outage_threshold_bits"), (int, float)) or not math.isfinite(
        analysis["outage_threshold_bits"]
    ):
        raise ValueError("analysis_plan.outage_threshold_bits must be finite.")
    if analysis.get("confidence_interval") != "paired two-sided Student-t 95%":
        raise ValueError("The frozen confidence-interval rule is missing or changed.")

    checkpoints = manifest.get("checkpoints")
    if not isinstance(checkpoints, list) or not checkpoints:
        raise ValueError("Manifest must list every selected checkpoint.")
    identifiers: set[str] = set()
    for index, item in enumerate(checkpoints):
        entry = _require_mapping(item, f"checkpoints[{index}]")
        for key in ("id", "mode", "path", "sha256", "initialization_seed",
                    "selected_fixed_va_snu", "validation_peak_feasible",
                    "validation_max_symbol_energy", "validation_budget_feasible",
                    "validation_mean_va_snu", "validation_expected_budget_upper_snu"):
            if key not in entry:
                raise ValueError(f"checkpoints[{index}].{key} is required.")
        if entry["id"] in identifiers:
            raise ValueError("Checkpoint identifiers must be unique.")
        identifiers.add(entry["id"])
        if entry["mode"] not in LEARNED_MODES:
            raise ValueError("Checkpoint mode is not a frozen learned ablation.")
        if not isinstance(entry["initialization_seed"], int) or entry["initialization_seed"] < 0:
            raise ValueError("Checkpoint initialization_seed must be nonnegative.")
        if not isinstance(entry["sha256"], str) or _SHA256.fullmatch(entry["sha256"]) is None:
            raise ValueError("Checkpoint sha256 must contain exactly 64 lowercase hex digits.")
        selected_va = entry["selected_fixed_va_snu"]
        if entry["validation_peak_feasible"] is not True:
            raise ValueError("Selected checkpoints must be validation-peak feasible.")
        maximum_energy = entry["validation_max_symbol_energy"]
        if not isinstance(maximum_energy, (int, float)) or not math.isfinite(maximum_energy):
            raise ValueError("Selected checkpoints require finite validation peak energy.")
        if entry["validation_budget_feasible"] is not True:
            raise ValueError("Selected checkpoints must satisfy the test-blind expected budget rule.")
        budget_upper = entry["validation_expected_budget_upper_snu"]
        budget_mean = entry["validation_mean_va_snu"]
        if any(not isinstance(value, (int, float)) or not math.isfinite(value)
               for value in (budget_mean, budget_upper)):
            raise ValueError("Selected checkpoints require a finite validation budget upper bound.")
        if entry["mode"] in FIXED_VA_LEARNED_MODES:
            if not isinstance(selected_va, (int, float)) or not math.isfinite(selected_va):
                raise ValueError("Fixed-VA learned checkpoints require selected_fixed_va_snu.")
        elif selected_va is not None:
            raise ValueError("Adaptive-VA checkpoints must set selected_fixed_va_snu to null.")


def common_protocol_config(config: dict[str, Any]) -> dict[str, Any]:
    """Remove the per-mode fixed-VA choice from an otherwise common config."""

    normalized = json.loads(json.dumps(config))
    if not isinstance(normalized.get("cvqkd"), dict):
        raise ValueError("Configuration is missing cvqkd settings.")
    normalized["cvqkd"]["fixed_modulation_variance_snu"] = None
    return normalized


def validate_manifest_against_config(manifest: dict[str, Any], config: dict[str, Any]) -> None:
    """Require the exact learned mode/seed roster declared by resolved config."""

    validate_publication_manifest(manifest)
    approved_peak_photon_limit(config)
    if config.get("cvqkd", {}).get("holevo_numerics", {}).get(
        "density_eigenvalue_pseudoinverse_author_approved"
    ) is not True:
        raise ValueError("Resolved config lacks author approval of the Holevo pseudoinverse threshold.")
    seeds = config.get("training", {}).get("independent_training_initialization_seeds")
    if not isinstance(seeds, list) or not seeds or len(set(seeds)) != len(seeds):
        raise ValueError("Resolved config must preregister distinct training seeds.")
    expected = {(mode, seed) for mode in LEARNED_MODES for seed in seeds}
    actual = {(entry["mode"], entry["initialization_seed"]) for entry in manifest["checkpoints"]}
    if len(actual) != len(manifest["checkpoints"]) or actual != expected:
        raise ValueError("Manifest checkpoint roster is incomplete, duplicated, or substituted.")
    cvqkd = config.get("cvqkd", {})
    v_min, v_max, budget = (
        float(cvqkd["v_min_snu"]), float(cvqkd["v_max_snu"]),
        float(cvqkd["v_a_budget_snu"]),
    )
    for entry in manifest["checkpoints"]:
        selected_va = entry["selected_fixed_va_snu"]
        if selected_va is not None and not v_min <= float(selected_va) <= min(v_max, budget):
            raise ValueError("Manifest fixed-VA checkpoint violates the common energy domain.")
        if float(entry["validation_max_symbol_energy"]) > approved_peak_photon_limit(config) * (
            1.0 + 1e-12
        ):
            raise ValueError("Manifest checkpoint violates the common peak-photon domain.")
        if float(entry["validation_expected_budget_upper_snu"]) > budget + 1e-12:
            raise ValueError("Manifest checkpoint violates the expected V_A budget rule.")
        margin = (
            0.0 if entry["mode"] in FIXED_VA_LEARNED_MODES
            else float(config["training"]["validation_energy_budget_margin_snu"])
        )
        if abs(
            float(entry["validation_expected_budget_upper_snu"])
            - float(entry["validation_mean_va_snu"]) - margin
        ) > 1e-12:
            raise ValueError("Manifest checkpoint expected-budget margin differs from config.")
    frozen_test = manifest["test_evaluation"]
    training = config.get("training", {})
    expected_test = {
        "fading_samples": training.get("test_fading_samples"),
        "awgn_samples_per_symbol": training.get("test_awgn_samples_per_symbol"),
        "channel_seed": training.get("seeds", {}).get("test_channel"),
        "awgn_seed": training.get("seeds", {}).get("test_awgn"),
    }
    if frozen_test != expected_test:
        raise ValueError("Manifest test seeds/counts differ from the resolved numerical freeze.")


def _resolve_artifact(manifest_path: Path, value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (manifest_path.parent / path).resolve()


def _validate_baseline_selection_artifact(
    baseline: dict[str, Any], config: dict[str, Any], manifest: dict[str, Any]
) -> None:
    if baseline.get("test_set_used") is not False or baseline.get("selection_split") != "validation":
        raise ValueError("Baseline selection is not validation-only.")
    if baseline.get("validation_state_realization_sha256") != manifest["validation_state_sha256"]:
        raise ValueError("Baseline selection used a different validation realization.")
    if baseline.get("common_random_numbers_across_candidates") is not True:
        raise ValueError("Baseline candidates must use common validation randomness.")
    selections = baseline.get("selections", {})
    if set(selections) != {"uniform", "binomial", "fixed_mb", "optimized_mb"}:
        raise ValueError("Bound baseline-selection artifact is incomplete.")
    cvqkd, search = config["cvqkd"], config["baseline_search"]
    va_grid = tuple(float(value) for value in search["va_grid_snu"])
    nu_grid = tuple(float(value) for value in search["optimized_mb_nu_grid"])
    reference_nu = float(cvqkd["mb_nu"])
    v_min, v_max, budget = (
        float(cvqkd["v_min_snu"]), float(cvqkd["v_max_snu"]),
        float(cvqkd["v_a_budget_snu"]),
    )
    if not va_grid or any(va < v_min or va > min(v_max, budget) for va in va_grid):
        raise ValueError("Frozen baseline VA grid violates the common energy domain.")
    fairness = baseline.get("energy_fairness", {})
    if any(float(fairness.get(key, float("nan"))) != expected for key, expected in (
        ("v_min_snu", v_min), ("v_max_snu", v_max), ("v_a_budget_snu", budget)
    )):
        raise ValueError("Baseline artifact energy domain differs from resolved config.")
    if float(fairness.get("n_peak_photons", float("nan"))) != approved_peak_photon_limit(config):
        raise ValueError("Baseline artifact peak domain differs from resolved config.")
    if fairness.get("same_rule_for_all_eleven_schemes") is not True:
        raise ValueError("Baseline artifact does not attest the common eleven-scheme peak rule.")
    definitions = {
        "uniform": (None,), "binomial": (None,),
        "fixed_mb": (reference_nu,), "optimized_mb": nu_grid,
    }
    for name, nus in definitions.items():
        selection = selections[name]
        if selection.get("split_used_for_selection") != "validation" or selection.get(
            "test_set_used"
        ) is not False:
            raise ValueError(f"Baseline {name} is not validation-only.")
        candidates = selection.get("candidates")
        if not isinstance(candidates, list):
            raise ValueError(f"Baseline {name} candidates are missing.")
        expected = {(va, nu) for nu in nus for va in va_grid}
        actual: set[tuple[float, float | None]] = set()
        for candidate in candidates:
            va = float(candidate.get("modulation_variance_snu"))
            nu_value = candidate.get("mb_nu")
            nu = None if nu_value is None else float(nu_value)
            score = candidate.get("validation_raw_skr")
            admissible = candidate.get("physical_domain_admissible")
            valid_score = (
                admissible is True and isinstance(score, (int, float)) and math.isfinite(score)
            ) or (
                admissible is False and score is None
                and isinstance(candidate.get("ineligibility_reason"), str)
            )
            if candidate.get("scheme") != name or not valid_score:
                raise ValueError(f"Baseline {name} contains an invalid candidate.")
            actual.add((va, nu))
        if actual != expected or len(candidates) != len(expected):
            raise ValueError(f"Baseline {name} candidate grid differs from the freeze.")
        eligible = [row for row in candidates if row["physical_domain_admissible"] is True]
        if not eligible:
            raise ValueError(f"Baseline {name} has no common-domain-admissible candidate.")
        recomputed = min(
            eligible,
            key=lambda row: (-float(row["validation_raw_skr"]),
                             float(row["modulation_variance_snu"]),
                             -1.0 if row["mb_nu"] is None else float(row["mb_nu"])),
        )
        if selection.get("selected") != recomputed:
            raise ValueError(f"Baseline {name} selected value violates the frozen tie-break.")


def verify_bound_artifacts(manifest_path: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    """Verify every selection/provenance artifact before held-out construction."""

    validate_publication_manifest(manifest)
    paths = {
        name: _resolve_artifact(manifest_path, manifest["artifact_paths"][name])
        for name in ARTIFACT_KEYS
    }
    try:
        import yaml
    except ImportError as error:
        raise RuntimeError("PyYAML is required to verify the resolved configuration.") from error
    config = yaml.safe_load(paths["resolved_config"].read_text(encoding="utf-8"))
    expected_hashes = {
        "resolved_config": canonical_json_sha256(config),
        **{name: file_sha256(path) for name, path in paths.items() if name != "resolved_config"},
    }
    for name, actual in expected_hashes.items():
        key = f"{name}_sha256"
        if manifest[key] != actual:
            raise ValueError(f"Frozen manifest hash mismatch: {name}.")
    baseline = json.loads(paths["baseline_selection"].read_text(encoding="utf-8"))
    _validate_baseline_selection_artifact(baseline, config, manifest)
    learned = json.loads(paths["learned_selection"].read_text(encoding="utf-8"))
    if learned.get("test_set_used") is not False or set(learned.get("selections", {})) != {
        "ps", "gs", "ps_gs"
    }:
        raise ValueError("Bound learned fixed-VA selection is incomplete or test-contaminated.")
    if learned.get("all_selected_checkpoints_peak_feasible") is not True or learned.get(
        "n_peak_photons"
    ) != approved_peak_photon_limit(config):
        raise ValueError("Learned selection lacks the frozen common peak-domain attestation.")
    selected_ids = {
        identifier
        for selection in learned["selections"].values()
        for identifier in selection.get("checkpoint_ids", [])
    }
    manifest_fixed_ids = {
        entry["id"] for entry in manifest["checkpoints"] if entry["mode"] in {"ps", "gs", "ps_gs"}
    }
    if selected_ids != manifest_fixed_ids:
        raise ValueError("Manifest fixed-VA checkpoints differ from learned selection artifact.")
    manifest_by_id = {entry["id"]: entry for entry in manifest["checkpoints"]}
    frozen_va_grid = {float(value) for value in config["baseline_search"]["va_grid_snu"]}
    for mode, selection in learned["selections"].items():
        selected_va = float(selection.get("modulation_variance_snu"))
        seeds = selection.get("initialization_seeds")
        identifiers = selection.get("checkpoint_ids")
        if selection.get("mode") != mode or selected_va not in frozen_va_grid:
            raise ValueError("Learned selection mode/VA differs from the frozen outer grid.")
        if not isinstance(seeds, list) or not isinstance(identifiers, list) or len(seeds) != len(
            identifiers
        ):
            raise ValueError("Learned selection seed/checkpoint pairing is malformed.")
        for seed, identifier in zip(seeds, identifiers):
            entry = manifest_by_id.get(identifier)
            if entry is None or (
                entry["mode"], entry["initialization_seed"],
                float(entry["selected_fixed_va_snu"])
            ) != (mode, seed, selected_va):
                raise ValueError(
                    "Learned selection checkpoint mode/seed/VA differs from manifest binding."
                )
    validate_manifest_against_config(manifest, config)
    convergence = json.loads(paths["convergence_evidence"].read_text(encoding="utf-8"))
    required_convergence = {
        "schema_version": "combined-convergence-evidence-v2",
        "status": "exact-selected-roster-convergence-gates-passed",
        "test_set_used": False,
        "coverage_scope": "exact_selected_roster_on_preregistered_validation_realization",
        "coverage_complete_over_enumerated_selected_ensembles": True,
        "mi_replications_stable": True,
        "all_mi_cases_converged": True,
        "all_fock_cases_converged": True,
        "all_holevo_threshold_sensitivity_cases_passed": True,
        "resolved_config_sha256": manifest["resolved_config_sha256"],
        "validation_state_realization_sha256": manifest["validation_state_sha256"],
    }
    if any(convergence.get(key) != value for key, value in required_convergence.items()):
        raise ValueError("Combined convergence evidence has not passed every frozen gate.")
    # Local import avoids a module-import cycle; selected_roster depends on this
    # manifest validator for its own reconstruction checks.
    from src.validation.selected_roster import selection_roster_sha256
    if convergence.get("selection_roster_sha256") != selection_roster_sha256(manifest):
        raise ValueError("Combined convergence evidence is bound to a different roster.")
    if convergence.get("certified_baseline_selection_sha256") != manifest[
        "baseline_selection_sha256"
    ]:
        raise ValueError("Convergence evidence is not bound to the selected baselines.")
    if set(convergence.get("certified_checkpoint_sha256", [])) != {
        entry["sha256"] for entry in manifest["checkpoints"]
    }:
        raise ValueError("Convergence evidence is not bound to every selected checkpoint.")
    certified = convergence.get("certified_roster")
    if not isinstance(certified, list):
        raise ValueError("Combined convergence evidence lacks the exact certified roster.")
    identifiers = [entry.get("id") for entry in certified if isinstance(entry, dict)]
    expected_ids = {f"baseline:{name}" for name in ("uniform", "binomial", "fixed_mb", "optimized_mb")} | {
        f"checkpoint:{entry['id']}" for entry in manifest["checkpoints"]
    }
    if len(identifiers) != len(certified) or len(set(identifiers)) != len(identifiers) or set(
        identifiers
    ) != expected_ids:
        raise ValueError("Combined convergence certified roster is missing, extra, or duplicated.")
    manifest_checkpoint_hashes = {
        f"checkpoint:{entry['id']}": entry["sha256"] for entry in manifest["checkpoints"]
    }
    for entry in certified:
        identifier = entry["id"]
        expected_source = (
            manifest["baseline_selection_sha256"]
            if identifier.startswith("baseline:") else manifest_checkpoint_hashes[identifier]
        )
        if entry.get("source_artifact_sha256") != expected_source or not isinstance(
            entry.get("reconstructed_ensemble_sha256"), str
        ) or _SHA256.fullmatch(entry["reconstructed_ensemble_sha256"]) is None:
            raise ValueError("Combined convergence roster source/ensemble binding is invalid.")
    if convergence.get("n_peak_photons") != approved_peak_photon_limit(config):
        raise ValueError("Convergence evidence peak domain differs from resolved config.")
    selected_mi = convergence.get("selected_mi_samples_per_symbol")
    selected_fock = convergence.get("selected_fock_cutoff")
    if not isinstance(selected_mi, int) or selected_mi <= 0:
        raise ValueError("Combined convergence evidence lacks a valid MI count.")
    if selected_fock != config["cvqkd"].get("fock_cutoff"):
        raise ValueError("Resolved Fock cutoff differs from combined convergence evidence.")
    if any(config["training"].get(key, 0) < selected_mi for key in (
        "validation_awgn_samples_per_symbol", "test_awgn_samples_per_symbol"
    )):
        raise ValueError("Resolved MI counts are below combined convergence evidence.")
    accounting = json.loads(paths["attempted_seed_accounting"].read_text(encoding="utf-8"))
    if accounting.get("test_set_used") is not False or not isinstance(
        accounting.get("records"), list
    ):
        raise ValueError("Attempted-seed accounting is missing or test-contaminated.")
    seeds = tuple(config["training"]["independent_training_initialization_seeds"])
    va_grid = tuple(float(value) for value in config["baseline_search"]["va_grid_snu"])
    expected_attempts = {
        (mode, seed, va)
        for mode in ("ps", "gs", "ps_gs") for seed in seeds for va in va_grid
    } | {
        (mode, seed, None)
        for mode in ("va", "ps_va", "gs_va", "full") for seed in seeds
    }
    actual_attempts: set[tuple[str, int, float | None]] = set()
    completed_checkpoint_ids: set[str] = set()
    for record in accounting["records"]:
        if not isinstance(record, dict) or record.get("outcome") not in {"completed", "failed"}:
            raise ValueError("Every attempted run needs a completed/failed outcome.")
        va = record.get("fixed_modulation_variance_snu")
        key = (record.get("mode"), record.get("initialization_seed"),
               None if va is None else float(va))
        if key in actual_attempts:
            raise ValueError("Attempted-seed accounting contains duplicate runs.")
        actual_attempts.add(key)
        if record["outcome"] == "completed":
            identifier = record.get("checkpoint_id")
            if not isinstance(identifier, str) or not identifier:
                raise ValueError("Completed attempted runs require checkpoint_id.")
            completed_checkpoint_ids.add(identifier)
    if actual_attempts != expected_attempts:
        raise ValueError("Attempted-seed accounting omits or substitutes preregistered runs.")
    manifest_ids = {entry["id"] for entry in manifest["checkpoints"]}
    if not manifest_ids.issubset(completed_checkpoint_ids):
        raise ValueError("Selected checkpoints are not all accounted as completed attempts.")
    return config


def load_publication_manifest(path: Path) -> dict[str, Any]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    validate_publication_manifest(manifest)
    return manifest


def selected_checkpoint(manifest: dict[str, Any], identifier: str) -> dict[str, Any]:
    validate_publication_manifest(manifest)
    matches = [entry for entry in manifest["checkpoints"] if entry["id"] == identifier]
    if len(matches) != 1:
        raise ValueError(f"Checkpoint id {identifier!r} is not uniquely frozen in the manifest.")
    return matches[0]
