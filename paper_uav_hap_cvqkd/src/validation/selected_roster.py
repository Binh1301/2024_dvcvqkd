"""Reconstruct and verify the exact post-selection transmitter roster.

This module never selects a model or numerical setting.  It rebuilds the four
validation-selected baselines and every hash-bound checkpoint on one supplied
validation realization, so convergence evidence can be tied to actual physical
ensembles instead of representative fixtures.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any
import re

import torch

from src.modulation.joint_ps_gs import Ensemble, JointTransmitter
from src.validation.physical_domain import approved_peak_photon_limit
from src.validation.publication_manifest import (
    _validate_baseline_selection_artifact,
    canonical_json_sha256,
    common_protocol_config,
    file_sha256,
    validate_manifest_against_config,
    validate_publication_manifest,
)


BASELINE_IMPLEMENTATION = {
    "uniform": "uniform",
    "binomial": "binomial",
    "fixed_mb": "mb",
    "optimized_mb": "mb",
}


def selection_roster_sha256(manifest: dict[str, Any]) -> str:
    """Hash selection identity while excluding the later convergence binding.

    The final manifest cannot know the combined-evidence file hash until that
    file exists.  This canonical subset avoids that dependency cycle while
    binding every field that determines the selected transmitter roster.
    """

    return canonical_json_sha256({
        "test_set_accessed_during_selection": manifest.get(
            "test_set_accessed_during_selection"
        ),
        "resolved_config_sha256": manifest.get("resolved_config_sha256"),
        "validation_state_sha256": manifest.get("validation_state_sha256"),
        "baseline_selection_sha256": manifest.get("baseline_selection_sha256"),
        "learned_selection_sha256": manifest.get("learned_selection_sha256"),
        "checkpoints": manifest.get("checkpoints"),
    })


def _publication_adapter(document: dict[str, Any], config: dict[str, Any] | None = None):
    """Normalize a roster-only freeze to the existing manifest validators."""

    if document.get("schema_version") == "publication-selection-manifest-v1":
        validate_publication_manifest(document)
        return document
    if document.get("schema_version") != "selected-convergence-roster-v1" or document.get(
        "status"
    ) != "selected-roster-frozen-before-convergence" or document.get(
        "test_set_accessed_during_selection"
    ) is not False:
        raise ValueError("Unsupported or test-contaminated selection roster document.")
    hashes = (
        "resolved_config_sha256", "validation_state_sha256",
        "baseline_selection_sha256", "learned_selection_sha256",
    )
    if any(not isinstance(document.get(key), str) or re.fullmatch(
        r"[0-9a-f]{64}", document[key]
    ) is None for key in hashes):
        raise ValueError("Selection roster hashes must be lowercase SHA-256 values.")
    paths = document.get("artifact_paths")
    if not isinstance(paths, dict) or set(paths) != {
        "resolved_config", "baseline_selection", "learned_selection"
    } or any(not isinstance(value, str) or not value for value in paths.values()):
        raise ValueError("Selection roster must bind config/baseline/learned artifacts.")
    training = {} if config is None else config.get("training", {})
    seeds = training.get("seeds", {})
    adapter = {
        **document,
        "schema_version": "publication-selection-manifest-v1",
        "status": "selections-and-analysis-frozen-before-test",
        "convergence_evidence_sha256": "0" * 64,
        "environment_lock_sha256": "0" * 64,
        "attempted_seed_accounting_sha256": "0" * 64,
        "git_revision": "roster-freeze",
        "artifact_paths": {
            **paths,
            "convergence_evidence": "not-yet-created.json",
            "environment_lock": "not-used-by-roster",
            "attempted_seed_accounting": "not-used-by-roster",
        },
        "test_evaluation": {
            "fading_samples": int(training.get("test_fading_samples", 1)),
            "awgn_samples_per_symbol": int(training.get("test_awgn_samples_per_symbol", 1)),
            "channel_seed": int(seeds.get("test_channel", 1)),
            "awgn_seed": int(seeds.get("test_awgn", 2)),
        },
        "analysis_plan": {
            "t_bin_edges": [0.0, 1.0], "epsilon_bin_edges": [0.0, 1.0],
            "va_heatmap_t_grid": [0.0, 1.0],
            "va_heatmap_epsilon_grid": [0.0, 1.0],
            "outage_threshold_bits": 0.0,
            "confidence_interval": "paired two-sided Student-t 95%",
        },
    }
    validate_publication_manifest(adapter)
    return adapter


@dataclass(frozen=True)
class SelectedRosterEntry:
    """One exact selected transmitter and its immutable source binding."""

    identifier: str
    kind: str
    scheme_or_mode: str
    source_artifact_sha256: str
    reconstructed_ensemble_sha256: str
    ensemble: Ensemble

    def binding(self) -> dict[str, str]:
        return {
            "id": self.identifier,
            "kind": self.kind,
            "scheme_or_mode": self.scheme_or_mode,
            "source_artifact_sha256": self.source_artifact_sha256,
            "reconstructed_ensemble_sha256": self.reconstructed_ensemble_sha256,
        }


def ensemble_sha256(ensemble: Ensemble) -> str:
    """Hash every tensor defining the deterministic physical ensemble."""

    ensemble.validate()
    digest = hashlib.sha256()
    for name, tensor in (
        ("probabilities", ensemble.probabilities),
        ("amplitudes_real", ensemble.amplitudes.real),
        ("amplitudes_imag", ensemble.amplitudes.imag),
        ("declared_va", ensemble.declared_va),
        ("relative_real", ensemble.relative_constellation.real),
        ("relative_imag", ensemble.relative_constellation.imag),
    ):
        value = tensor.detach().cpu().contiguous()
        digest.update(name.encode("ascii"))
        digest.update(str(value.dtype).encode("ascii"))
        digest.update(str(tuple(value.shape)).encode("ascii"))
        digest.update(value.numpy().tobytes())
    return digest.hexdigest()


def _artifact_path(manifest_path: Path, value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (manifest_path.parent / path).resolve()


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Artifact must contain a JSON object: {path}")
    return value


def _validate_learned_selection(
    learned: dict[str, Any], manifest: dict[str, Any], config: dict[str, Any], n_peak: float
) -> None:
    if learned.get("test_set_used") is not False or set(learned.get("selections", {})) != {
        "ps", "gs", "ps_gs"
    }:
        raise ValueError("Bound learned fixed-VA selection is incomplete or test-contaminated.")
    if learned.get("all_selected_checkpoints_peak_feasible") is not True or learned.get(
        "n_peak_photons"
    ) != n_peak:
        raise ValueError("Learned selection lacks the common peak-domain attestation.")
    selected_ids = {
        identifier
        for selection in learned["selections"].values()
        for identifier in selection.get("checkpoint_ids", [])
    }
    manifest_by_id = {entry["id"]: entry for entry in manifest["checkpoints"]}
    manifest_fixed_ids = {
        entry["id"]
        for entry in manifest["checkpoints"]
        if entry["mode"] in {"ps", "gs", "ps_gs"}
    }
    if selected_ids != manifest_fixed_ids:
        raise ValueError("Manifest fixed-VA checkpoints differ from learned selection artifact.")
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
                float(entry["selected_fixed_va_snu"]),
            ) != (mode, seed, selected_va):
                raise ValueError("Learned selection checkpoint differs from manifest binding.")


def reconstruct_selected_roster(
    manifest_path: Path,
    manifest: dict[str, Any],
    transmittance: torch.Tensor,
    epsilon: torch.Tensor,
    validation_state_realization_sha256: str,
) -> tuple[dict[str, Any], str, tuple[SelectedRosterEntry, ...]]:
    """Load hash-bound selections/checkpoints and reconstruct every ensemble."""

    manifest_path = manifest_path.resolve()
    source_document = manifest
    manifest = _publication_adapter(source_document)
    if manifest["validation_state_sha256"] != validation_state_realization_sha256:
        raise ValueError("Reconstructed validation realization differs from the frozen manifest.")
    if transmittance.ndim != 1 or epsilon.shape != transmittance.shape or not transmittance.numel():
        raise ValueError("Exact roster reconstruction needs matching nonempty state vectors.")
    paths = {
        name: _artifact_path(manifest_path, manifest["artifact_paths"][name])
        for name in ("resolved_config", "baseline_selection", "learned_selection")
    }
    try:
        import yaml
    except ImportError as error:  # pragma: no cover - publication environment requirement
        raise RuntimeError("PyYAML is required to reconstruct selected ensembles.") from error
    config = yaml.safe_load(paths["resolved_config"].read_text(encoding="utf-8"))
    if not isinstance(config, dict) or canonical_json_sha256(config) != manifest[
        "resolved_config_sha256"
    ]:
        raise ValueError("Resolved configuration differs from the frozen manifest hash.")
    baseline_hash = file_sha256(paths["baseline_selection"])
    if baseline_hash != manifest["baseline_selection_sha256"]:
        raise ValueError("Baseline-selection artifact differs from the frozen manifest hash.")
    if file_sha256(paths["learned_selection"]) != manifest["learned_selection_sha256"]:
        raise ValueError("Learned-selection artifact differs from the frozen manifest hash.")
    # Rebuild the adapter with the exact config-owned test counts/seeds so the
    # common roster/config validator can be reused without granting test access.
    manifest = _publication_adapter(source_document, config)
    validate_manifest_against_config(manifest, config)
    n_peak = approved_peak_photon_limit(config)
    baseline = _load_json(paths["baseline_selection"])
    _validate_baseline_selection_artifact(baseline, config, manifest)
    learned = _load_json(paths["learned_selection"])
    _validate_learned_selection(learned, manifest, config, n_peak)

    cvqkd = config["cvqkd"]
    roster: list[SelectedRosterEntry] = []
    for scheme in BASELINE_IMPLEMENTATION:
        selected = baseline["selections"][scheme]["selected"]
        va = float(selected["modulation_variance_snu"])
        nu_value = selected["mb_nu"]
        transmitter = JointTransmitter(
            BASELINE_IMPLEMENTATION[scheme], fixed_va=va,
            v_min=float(cvqkd["v_min_snu"]), v_max=float(cvqkd["v_max_snu"]),
            nu_mb=None if nu_value is None else float(nu_value),
            n_peak_photons=n_peak,
        )
        with torch.no_grad():
            ensemble = transmitter(transmittance, epsilon)
        roster.append(SelectedRosterEntry(
            f"baseline:{scheme}", "baseline", scheme, baseline_hash,
            ensemble_sha256(ensemble), ensemble,
        ))

    for checkpoint_entry in manifest["checkpoints"]:
        checkpoint_path = _artifact_path(manifest_path, checkpoint_entry["path"])
        checkpoint_hash = file_sha256(checkpoint_path)
        if checkpoint_hash != checkpoint_entry["sha256"]:
            raise ValueError(f"Checkpoint hash mismatch: {checkpoint_entry['id']}")
        checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
        if checkpoint.get("transmitter_spec") != "frozen_c4_v1":
            raise ValueError("Checkpoint is incompatible with the frozen C4 transmitter.")
        if checkpoint.get("mode") != checkpoint_entry["mode"] or checkpoint.get(
            "initialization_seed"
        ) != checkpoint_entry["initialization_seed"]:
            raise ValueError("Checkpoint mode/seed differs from its frozen manifest entry.")
        checkpoint_config = checkpoint.get("configuration")
        if not isinstance(checkpoint_config, dict) or common_protocol_config(
            checkpoint_config
        ) != common_protocol_config(config):
            raise ValueError("Checkpoint common protocol differs from resolved configuration.")
        fixed_va = checkpoint_config["cvqkd"].get("fixed_modulation_variance_snu")
        if fixed_va != checkpoint_entry["selected_fixed_va_snu"]:
            raise ValueError("Checkpoint fixed VA differs from its frozen manifest entry.")
        if checkpoint.get("n_peak_photons") != n_peak or checkpoint.get(
            "selected_validation_peak_feasible"
        ) is not True:
            raise ValueError("Checkpoint lacks the frozen peak-domain attestation.")
        if checkpoint.get("selected_validation_max_symbol_energy") != checkpoint_entry[
            "validation_max_symbol_energy"
        ]:
            raise ValueError("Checkpoint peak metadata differs from the frozen manifest.")
        budget_evidence = checkpoint.get("selected_validation_expected_budget")
        if not isinstance(budget_evidence, dict) or budget_evidence.get(
            "expected_budget_feasible"
        ) is not True or budget_evidence.get(
            "validation_mean_va_snu"
        ) != checkpoint_entry["validation_mean_va_snu"] or budget_evidence.get(
            "expected_budget_upper_snu"
        ) != checkpoint_entry["validation_expected_budget_upper_snu"]:
            raise ValueError("Checkpoint budget metadata differs from the frozen manifest.")
        transmitter = JointTransmitter(
            checkpoint_entry["mode"], fixed_va=checkpoint_entry["selected_fixed_va_snu"],
            v_min=float(cvqkd["v_min_snu"]), v_max=float(cvqkd["v_max_snu"]),
            reference_distribution="uniform", nu_mb=cvqkd.get("mb_nu"),
            n_peak_photons=n_peak,
        )
        transmitter.load_state_dict(checkpoint["model_state_dict"])
        transmitter.eval()
        with torch.no_grad():
            ensemble = transmitter(transmittance, epsilon)
        observed_peak = float(ensemble.amplitudes.abs().square().max())
        observed_mean_va = float(ensemble.declared_va.mean())
        if abs(observed_peak - float(checkpoint_entry["validation_max_symbol_energy"])) > (
            1e-12 * max(1.0, observed_peak)
        ):
            raise ValueError("Reconstructed checkpoint peak differs from validation metadata.")
        if abs(observed_mean_va - float(checkpoint_entry["validation_mean_va_snu"])) > (
            1e-12 * max(1.0, observed_mean_va)
        ):
            raise ValueError("Reconstructed checkpoint mean VA differs from validation metadata.")
        roster.append(SelectedRosterEntry(
            f"checkpoint:{checkpoint_entry['id']}", "checkpoint",
            checkpoint_entry["mode"], checkpoint_hash,
            ensemble_sha256(ensemble), ensemble,
        ))
    identifiers = [entry.identifier for entry in roster]
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("Selected convergence roster contains duplicate identifiers.")
    return config, baseline_hash, tuple(roster)


def expected_evidence_settings(config: dict[str, Any], evidence_type: str) -> dict[str, Any]:
    """Return the exact active setting block required in one evidence artifact."""

    numerical = config["numerical_validation"]
    holevo = config["cvqkd"]["holevo_numerics"]
    active = {
        "symmetry_tolerance": float(holevo["symmetry_tolerance"]),
        "density_trace_tolerance": float(holevo["density_trace_tolerance"]),
        "density_eigenvalue_pseudoinverse_tolerance": float(
            holevo["density_eigenvalue_pseudoinverse_tolerance"]
        ),
        "physicality_tolerance": float(holevo["physicality_tolerance"]),
    }
    if evidence_type == "mi":
        values = numerical["mi"]
        return {
            "sample_counts": [int(value) for value in values["sample_counts"]],
            "absolute_tolerance_bits": float(values["absolute_tolerance_bits"]),
            "relative_tolerance": float(values["relative_tolerance"]),
            "replication_base_seeds": [int(value) for value in values["seeds"]],
        }
    if evidence_type == "fock":
        values = numerical["fock"]
        return {
            "cutoffs": [int(value) for value in values["cutoffs"]],
            "absolute_tolerance": float(values["absolute_tolerance"]),
            "relative_tolerance": float(values["relative_tolerance"]),
            **active,
        }
    if evidence_type == "holevo_threshold":
        values = numerical["holevo_threshold_sensitivity"]
        return {
            "fock_cutoff": int(config["cvqkd"]["fock_cutoff"]),
            "density_eigenvalue_pseudoinverse_tolerances": [
                float(value) for value in values[
                    "density_eigenvalue_pseudoinverse_tolerances"
                ]
            ],
            "absolute_tolerance": float(values["absolute_tolerance"]),
            "relative_tolerance": float(values["relative_tolerance"]),
            **active,
        }
    raise ValueError(f"Unsupported exact convergence evidence type: {evidence_type!r}")


def validate_exact_evidence(
    evidence: dict[str, Any],
    *,
    evidence_type: str,
    config: dict[str, Any],
    baseline_selection_sha256: str,
    validation_state_realization_sha256: str,
    selection_roster_hash: str,
    roster: tuple[SelectedRosterEntry, ...],
) -> dict[str, dict[str, Any]]:
    """Reject any evidence not exactly equal to the independently rebuilt roster."""

    expected_config_hash = canonical_json_sha256(config)
    required = {
        "schema_version": "exact-selected-convergence-evidence-v1",
        "evidence_type": evidence_type,
        "status": "exact selected-roster validation evidence; not a publication result",
        "test_set_used": False,
        "coverage_scope": "exact_selected_roster_on_preregistered_validation_realization",
        "precision": "torch.float64 / torch.complex128 on CPU",
        "resolved_config_sha256": expected_config_hash,
        "baseline_selection_sha256": baseline_selection_sha256,
        "validation_state_realization_sha256": validation_state_realization_sha256,
        "selection_roster_sha256": selection_roster_hash,
        "settings": expected_evidence_settings(config, evidence_type),
    }
    if any(evidence.get(key) != value for key, value in required.items()):
        raise ValueError(f"{evidence_type} evidence provenance/settings differ from the freeze.")
    entries = evidence.get("entries")
    if not isinstance(entries, list):
        raise ValueError(f"{evidence_type} evidence entries must be a list.")
    actual: dict[str, dict[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("id"), str):
            raise ValueError(f"Malformed {evidence_type} roster entry.")
        if entry["id"] in actual:
            raise ValueError(f"Duplicate {evidence_type} trace entry: {entry['id']}")
        actual[entry["id"]] = entry
    expected = {entry.identifier: entry for entry in roster}
    if set(actual) != set(expected):
        raise ValueError(f"{evidence_type} evidence has missing or extra selected roster entries.")
    for identifier, expected_entry in expected.items():
        entry = actual[identifier]
        for key, value in expected_entry.binding().items():
            if entry.get(key) != value:
                raise ValueError(f"{evidence_type} binding mismatch for {identifier}: {key}")
        if not isinstance(entry.get("trace"), dict):
            raise ValueError(f"{evidence_type} trace is missing for {identifier}.")
    return actual
