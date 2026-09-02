import copy
import json
from pathlib import Path
import tempfile
import unittest

import torch
import yaml

from src.modulation.joint_ps_gs import JointTransmitter
from src.validation.publication_manifest import canonical_json_sha256, file_sha256
from src.validation.selected_roster import (
    reconstruct_selected_roster,
    selection_roster_sha256,
    validate_exact_evidence,
)


class SelectedRosterConvergenceTests(unittest.TestCase):
    def _fixture(self, root: Path):
        state_hash = "a" * 64
        modes = ("ps", "gs", "va", "ps_gs", "ps_va", "gs_va", "full")
        config = {
            "cvqkd": {
                "fixed_modulation_variance_snu": None,
                "v_min_snu": 0.5, "v_max_snu": 2.0, "v_a_budget_snu": 2.0,
                "n_peak_photons": 100.0, "n_peak_author_approved": True,
                "peak_domain_scope": "complete_preregistered_realizations",
                "mb_nu": 0.1, "fock_cutoff": 8,
                "holevo_numerics": {
                    "symmetry_tolerance": 1e-8, "density_trace_tolerance": 1e-8,
                    "density_eigenvalue_pseudoinverse_tolerance": 1e-12,
                    "density_eigenvalue_pseudoinverse_author_approved": True,
                    "physicality_tolerance": 1e-10,
                },
            },
            "training": {
                "independent_training_initialization_seeds": [7],
                "validation_energy_budget_margin_snu": 0.1,
                "validation_awgn_samples_per_symbol": 2,
                "test_awgn_samples_per_symbol": 2,
                "test_fading_samples": 2,
                "seeds": {"test_channel": 9, "test_awgn": 10},
            },
            "baseline_search": {"va_grid_snu": [0.5], "optimized_mb_nu_grid": [0.0, 0.1]},
            "numerical_validation": {
                "mi": {"sample_counts": [1, 2], "absolute_tolerance_bits": 1.0,
                       "relative_tolerance": 0.0, "seeds": [101, 102]},
                "fock": {"cutoffs": [6, 8], "absolute_tolerance": 1.0,
                         "relative_tolerance": 0.0, "density_trace_tolerance": 1e-8},
                "holevo_threshold_sensitivity": {
                    "density_eigenvalue_pseudoinverse_tolerances": [1e-14, 1e-12],
                    "absolute_tolerance": 1.0, "relative_tolerance": 0.0,
                },
            },
        }
        config_path = root / "resolved.yaml"
        config_path.write_text(yaml.safe_dump(config, sort_keys=True), encoding="utf-8")
        selections = {}
        definitions = {
            "uniform": [None], "binomial": [None], "fixed_mb": [0.1],
            "optimized_mb": [0.0, 0.1],
        }
        for scheme, nus in definitions.items():
            candidates = [{
                "scheme": scheme, "modulation_variance_snu": 0.5, "mb_nu": nu,
                "validation_raw_skr": 0.0, "physical_domain_admissible": True,
                "ineligibility_reason": None,
            } for nu in nus]
            selections[scheme] = {
                "scheme": scheme, "selected": candidates[0], "candidates": candidates,
                "split_used_for_selection": "validation", "test_set_used": False,
            }
        baseline = {
            "selection_split": "validation", "test_set_used": False,
            "validation_state_realization_sha256": state_hash,
            "common_random_numbers_across_candidates": True,
            "energy_fairness": {
                "v_min_snu": 0.5, "v_max_snu": 2.0, "v_a_budget_snu": 2.0,
                "n_peak_photons": 100.0, "same_rule_for_all_eleven_schemes": True,
            },
            "selections": selections,
        }
        baseline_path = root / "baselines.json"
        baseline_path.write_text(json.dumps(baseline), encoding="utf-8")
        checkpoint_entries = []
        fixed_ids = {}
        validation_t = torch.tensor([0.02, 0.1], dtype=torch.float64)
        validation_epsilon = torch.tensor([0.002, 0.001], dtype=torch.float64)
        for mode in modes:
            fixed_va = 0.5 if mode in {"ps", "gs", "ps_gs"} else None
            checkpoint_config = copy.deepcopy(config)
            checkpoint_config["cvqkd"]["fixed_modulation_variance_snu"] = fixed_va
            transmitter = JointTransmitter(
                mode, fixed_va=fixed_va, v_min=0.5, v_max=2.0,
                n_peak_photons=100.0,
            )
            with torch.no_grad():
                reconstructed = transmitter(validation_t, validation_epsilon)
            validation_mean_va = float(reconstructed.declared_va.mean())
            validation_peak = float(reconstructed.amplitudes.abs().square().max())
            identifier = f"{mode}-7"
            checkpoint_path = root / f"{identifier}.pt"
            expected_upper = validation_mean_va + (0.0 if fixed_va is not None else 0.1)
            torch.save({
                "transmitter_spec": "frozen_c4_v1", "mode": mode,
                "initialization_seed": 7, "configuration": checkpoint_config,
                "n_peak_photons": 100.0, "selected_validation_peak_feasible": True,
                "selected_validation_max_symbol_energy": validation_peak,
                "model_state_dict": transmitter.state_dict(),
                "selected_validation_expected_budget": {
                    "validation_mean_va_snu": validation_mean_va,
                    "expected_budget_upper_snu": expected_upper,
                    "expected_budget_feasible": True,
                },
            }, checkpoint_path)
            checkpoint_entries.append({
                "id": identifier, "mode": mode, "path": checkpoint_path.name,
                "sha256": file_sha256(checkpoint_path), "initialization_seed": 7,
                "selected_fixed_va_snu": fixed_va, "validation_peak_feasible": True,
                "validation_max_symbol_energy": validation_peak,
                "validation_budget_feasible": True,
                "validation_mean_va_snu": validation_mean_va,
                "validation_expected_budget_upper_snu": expected_upper,
            })
            if fixed_va is not None:
                fixed_ids[mode] = identifier
        learned = {
            "test_set_used": False, "all_selected_checkpoints_peak_feasible": True,
            "n_peak_photons": 100.0,
            "selections": {
                mode: {"mode": mode, "modulation_variance_snu": 0.5,
                       "initialization_seeds": [7], "checkpoint_ids": [fixed_ids[mode]]}
                for mode in ("ps", "gs", "ps_gs")
            },
        }
        learned_path = root / "learned.json"
        learned_path.write_text(json.dumps(learned), encoding="utf-8")
        manifest = {
            "schema_version": "publication-selection-manifest-v1",
            "status": "selections-and-analysis-frozen-before-test",
            "test_set_accessed_during_selection": False,
            "resolved_config_sha256": canonical_json_sha256(config),
            "validation_state_sha256": state_hash,
            "baseline_selection_sha256": file_sha256(baseline_path),
            "learned_selection_sha256": file_sha256(learned_path),
            "convergence_evidence_sha256": "b" * 64,
            "environment_lock_sha256": "c" * 64,
            "attempted_seed_accounting_sha256": "d" * 64,
            "git_revision": "1234567",
            "artifact_paths": {
                "resolved_config": config_path.name,
                "baseline_selection": baseline_path.name,
                "learned_selection": learned_path.name,
                "convergence_evidence": "future.json",
                "environment_lock": "environment.lock",
                "attempted_seed_accounting": "attempted.json",
            },
            "test_evaluation": {"fading_samples": 2, "awgn_samples_per_symbol": 2,
                                "channel_seed": 9, "awgn_seed": 10},
            "analysis_plan": {
                "t_bin_edges": [0.0, 1.0], "epsilon_bin_edges": [0.0, 0.1],
                "va_heatmap_t_grid": [0.1, 0.9],
                "va_heatmap_epsilon_grid": [0.0, 0.1],
                "outage_threshold_bits": 0.0,
                "confidence_interval": "paired two-sided Student-t 95%",
            },
            "checkpoints": checkpoint_entries,
        }
        manifest_path = root / "manifest.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        return config, manifest, manifest_path, state_hash

    def test_reconstructs_all_eleven_hash_bound_synthetic_ensembles(self):
        with tempfile.TemporaryDirectory() as directory:
            config, manifest, manifest_path, state_hash = self._fixture(Path(directory))
            t = torch.tensor([0.02, 0.1], dtype=torch.float64)
            epsilon = torch.tensor([0.002, 0.001], dtype=torch.float64)
            resolved, baseline_hash, roster = reconstruct_selected_roster(
                manifest_path, manifest, t, epsilon, state_hash
            )
            self.assertEqual(resolved, config)
            self.assertEqual(len(roster), 11)
            self.assertEqual(len({entry.identifier for entry in roster}), 11)
            self.assertTrue(all(len(entry.reconstructed_ensemble_sha256) == 64 for entry in roster))
            _, second_hash, second = reconstruct_selected_roster(
                manifest_path, manifest, t, epsilon, state_hash
            )
            self.assertEqual(baseline_hash, second_hash)
            self.assertEqual([entry.binding() for entry in roster],
                             [entry.binding() for entry in second])
            roster_document = {
                "schema_version": "selected-convergence-roster-v1",
                "status": "selected-roster-frozen-before-convergence",
                "test_set_accessed_during_selection": False,
                **{key: manifest[key] for key in (
                    "resolved_config_sha256", "validation_state_sha256",
                    "baseline_selection_sha256", "learned_selection_sha256",
                    "checkpoints",
                )},
                "artifact_paths": {
                    key: manifest["artifact_paths"][key] for key in (
                        "resolved_config", "baseline_selection", "learned_selection"
                    )
                },
            }
            _, _, roster_only = reconstruct_selected_roster(
                manifest_path, roster_document, t, epsilon, state_hash
            )
            self.assertEqual(selection_roster_sha256(manifest),
                             selection_roster_sha256(roster_document))
            self.assertEqual([entry.binding() for entry in roster],
                             [entry.binding() for entry in roster_only])

    def test_evidence_rejects_duplicate_missing_and_binding_mismatch(self):
        with tempfile.TemporaryDirectory() as directory:
            config, manifest, manifest_path, state_hash = self._fixture(Path(directory))
            t = torch.tensor([0.02, 0.1], dtype=torch.float64)
            epsilon = torch.tensor([0.002, 0.001], dtype=torch.float64)
            config, baseline_hash, roster = reconstruct_selected_roster(
                manifest_path, manifest, t, epsilon, state_hash
            )
            entries = [{**entry.binding(), "trace": {}} for entry in roster]
            evidence = {
                "schema_version": "exact-selected-convergence-evidence-v1",
                "evidence_type": "mi", "test_set_used": False,
                "status": "exact selected-roster validation evidence; not a publication result",
                "coverage_scope": "exact_selected_roster_on_preregistered_validation_realization",
                "precision": "torch.float64 / torch.complex128 on CPU",
                "selection_roster_sha256": selection_roster_sha256(manifest),
                "resolved_config_sha256": canonical_json_sha256(config),
                "baseline_selection_sha256": baseline_hash,
                "validation_state_realization_sha256": state_hash,
                "settings": {
                    "sample_counts": [1, 2], "absolute_tolerance_bits": 1.0,
                    "relative_tolerance": 0.0, "replication_base_seeds": [101, 102],
                },
                "entries": entries,
            }
            validate_exact_evidence(
                evidence, evidence_type="mi", config=config,
                baseline_selection_sha256=baseline_hash,
                validation_state_realization_sha256=state_hash,
                selection_roster_hash=selection_roster_sha256(manifest), roster=roster,
            )
            for bad_entries, message in (
                (entries[:-1], "missing or extra"),
                (entries + [entries[0]], "Duplicate"),
                ([{**entries[0], "reconstructed_ensemble_sha256": "0" * 64}] + entries[1:],
                 "binding mismatch"),
            ):
                with self.assertRaisesRegex(ValueError, message):
                    validate_exact_evidence(
                        {**evidence, "entries": bad_entries}, evidence_type="mi", config=config,
                        baseline_selection_sha256=baseline_hash,
                        validation_state_realization_sha256=state_hash,
                        selection_roster_hash=selection_roster_sha256(manifest), roster=roster,
                    )
            with self.assertRaisesRegex(ValueError, "provenance/settings"):
                validate_exact_evidence(
                    {**evidence, "settings": {**evidence["settings"],
                                               "relative_tolerance": 0.25}},
                    evidence_type="mi", config=config,
                    baseline_selection_sha256=baseline_hash,
                    validation_state_realization_sha256=state_hash,
                    selection_roster_hash=selection_roster_sha256(manifest), roster=roster,
                )


if __name__ == "__main__":
    unittest.main()
