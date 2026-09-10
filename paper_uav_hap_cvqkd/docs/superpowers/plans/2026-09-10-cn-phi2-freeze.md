# Cn_phi2 Scientific and Configuration Freeze Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the scenario-level `Cn_phi2` phase parameter explicit, dimensionally auditable, and provenance-bound without inventing an author-approved value or changing the frozen CV-QKD policy, channel, or full-Z security semantics.

**Architecture:** Keep `channel.cn_phi2_m_minus_two_thirds` as the single production input. Resolve it through the existing `LinkGeometry` and the existing two-stage phase equations, return one canonical provenance record containing the input and derived `tau_phi2`/`c_phi`, and pass only the derived `c_phi` into the already implemented post-action noise chain. Persist the provenance beside run/checkpoint metadata so a later approved value cannot be mixed with an old result. The production YAML value remains `null` until an author freezes it.

**Tech Stack:** Python 3, PyTorch float64/complex128, unittest, YAML/JSON configuration, Markdown evidence ledgers.

---

## Scope and evidence constraints

- Preserve the current phase chain exactly: `kappa = 2*pi/wavelength_m`; `tau_phi2 = 2.46*Cn_phi2*kappa**(7/6)*L**(11/6)`; `c_phi = tau_phi2 + 0.25*tau_phi2**2`; `xi_phase = c_phi*V_A`; `epsilon_total = epsilon_base + xi_phase`.
- Preserve policy input `(T, epsilon_base)`, adaptive/fixed-`V_A` behavior, the same `epsilon_total` object for MI and Holevo, and the active full Z interval.
- Treat `Cn_phi2` (`m^-2/3`) as an effective scenario-level representation of the same atmosphere, distinct from the legacy/current beam-wander compatibility field `cn2_m_minus_two_thirds`; do not derive or silently equate them.
- Do not add an independent `c_phi` configuration input and do not choose a numerical `Cn_phi2` value. `null` must continue to fail closed at production target entry points; explicit zero remains valid only where a caller explicitly supplies it for a test/development case.
- Do not run training, target/publication Monte Carlo, final-test, held-out, or certification workflows.
- Do not modify `docs/FINAL_MODEL_SPEC.md`, PS/GS/VA logic, composite-channel behavior, or numerical-domain/full-Z implementation.

## Files and responsibilities

- `src/channel/phase_noise.py`: canonical numerical validation and phase provenance record; preserve existing public functions.
- `src/channel/__init__.py`: export the provenance helper.
- `scripts/_train.py`: resolve one provenance record from canonical YAML and store it with training outputs.
- `scripts/evaluate.py`, `scripts/evaluate_baseline.py`, `scripts/smoke_validate_frozen.py`, `scripts/select_validation_baselines.py`, `scripts/run_baselines.py`, and `scripts/run_baselines_cached_source_moments.py`: use the canonical helper and expose the same provenance wherever a phase coefficient is resolved.
- `scripts/_common.py`, `scripts/_numerical_validation.py`, and `scripts/select_learned_fixed_va.py`: require the phase field at target/validation entry points so unresolved production state is reported explicitly.
- `configs/default.yaml`, `configs/channel.yaml`, and `configs/baseline_smoke.json`: document the field and preserve unresolved production/test configuration semantics without adding a physical value.
- `tests/test_phase_parameter_freeze.py`: focused unit tests for units/semantics, derivation, sensitivity, fail-closed behavior, and config-hash identity.
- `docs/PHYSICAL_PARAMETER_AUDIT.md` (or one directly linked phase-freeze section), `docs/ASSUMPTIONS.md`, `docs/EQUATIONS.md`, `docs/PAPER_TO_CODE.md`, `docs/NUMERICAL_PARAMETER_FREEZE.md`, `docs/PROJECT_STATE.md`, `docs/NEXT_ACTIONS.md`, `docs/SESSION_HANDOFF.md`, `docs/EVIDENCE.md`, and `docs/DECISION_LOG.md`: record the audit outcome and author-freeze template without altering authoritative frozen specification text.

## Implementation tasks

### Task 1: Add focused failing tests first (RED)

- [x] Add `tests/test_phase_parameter_freeze.py` with this complete test body:

```python
import copy
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from _train import _phase_coefficient, _phase_provenance
from src.channel.phase_noise import (
    phase_noise_coefficient,
    phase_parameter_provenance,
)
from src.validation.publication_manifest import canonical_json_sha256


def config(cn_phi2=2.0e-16, wavelength_m=1.55e-6, h_hap_m=20000.0, h_uav_m=1000.0):
    return {
        "channel": {
            "h_hap_m": h_hap_m,
            "h_uav_m": h_uav_m,
            "zenith_angle_rad": 0.0,
            "wavelength_m": wavelength_m,
            "cn2_m_minus_two_thirds": 1.0e-16,
            "cn_phi2_m_minus_two_thirds": cn_phi2,
        }
    }


class PhaseParameterFreezeTests(unittest.TestCase):
    def test_provenance_contains_si_inputs_and_derived_values(self):
        record = phase_parameter_provenance(2.0e-16, 1.55e-6, 19000.0)
        self.assertEqual(record["parameterization"], "scenario_level_effective_Cn_phi2")
        self.assertEqual(record["cn_phi2_m_minus_two_thirds"], 2.0e-16)
        self.assertEqual(record["wavelength_m"], 1.55e-6)
        self.assertEqual(record["link_distance_m"], 19000.0)
        self.assertEqual(record["units"]["cn_phi2_m_minus_two_thirds"], "m^(-2/3)")
        self.assertEqual(record["units"]["wavelength_m"], "m")
        self.assertEqual(record["units"]["link_distance_m"], "m")
        self.assertEqual(record["units"]["tau_phi2"], "dimensionless")
        self.assertEqual(record["units"]["c_phi"], "dimensionless")
        self.assertTrue(record["c_phi_is_derived"])
        self.assertEqual(
            record["cn_phi2_relation_to_cn2_profile"],
            "independent; not derived from altitude-dependent C_n^2(h)",
        )

    def test_c_phi_is_derived_from_tau_and_has_no_independent_input(self):
        record = phase_parameter_provenance(2.0e-16, 1.55e-6, 19000.0)
        self.assertEqual(record["c_phi"], phase_noise_coefficient(record["tau_phi2"]))
        self.assertNotIn("c_phi_configured", record)

    def test_cn_phi2_changes_tau_and_c_phi(self):
        low = phase_parameter_provenance(1.0e-16, 1.55e-6, 19000.0)
        high = phase_parameter_provenance(2.0e-16, 1.55e-6, 19000.0)
        self.assertNotEqual(low["tau_phi2"], high["tau_phi2"])
        self.assertNotEqual(low["c_phi"], high["c_phi"])

    def test_wavelength_and_link_distance_change_phase_provenance(self):
        reference = phase_parameter_provenance(2.0e-16, 1.55e-6, 19000.0)
        different_wavelength = phase_parameter_provenance(2.0e-16, 1.50e-6, 19000.0)
        different_link = phase_parameter_provenance(2.0e-16, 1.55e-6, 20000.0)
        self.assertNotEqual(reference["tau_phi2"], different_wavelength["tau_phi2"])
        self.assertNotEqual(reference["tau_phi2"], different_link["tau_phi2"])

    def test_legacy_cn2_does_not_enter_phase_provenance(self):
        first = config()
        second = copy.deepcopy(first)
        second["channel"]["cn2_m_minus_two_thirds"] = 1.0e-15
        self.assertEqual(_phase_provenance(first), _phase_provenance(second))

    def test_configured_phase_provenance_is_resolved_from_link_geometry(self):
        record = _phase_provenance(config())
        self.assertEqual(record["link_distance_m"], 19000.0)
        self.assertEqual(_phase_coefficient(config()), record["c_phi"])
        self.assertEqual(record["c_phi"], phase_parameter_provenance(
            2.0e-16, 1.55e-6, 19000.0
        )["c_phi"])

    def test_missing_phase_value_fails_closed(self):
        unresolved = config(None)
        with self.assertRaisesRegex(ValueError, "author-approved"):
            _phase_provenance(unresolved)

    def test_explicit_zero_is_valid_for_test_only_callers(self):
        record = phase_parameter_provenance(0.0, 1.55e-6, 19000.0)
        self.assertEqual(record["tau_phi2"], 0.0)
        self.assertEqual(record["c_phi"], 0.0)

    def test_resolved_config_hash_changes_with_phase_inputs_and_link(self):
        base = config()
        changed_cn = copy.deepcopy(base)
        changed_cn["channel"]["cn_phi2_m_minus_two_thirds"] = 3.0e-16
        changed_wavelength = copy.deepcopy(base)
        changed_wavelength["channel"]["wavelength_m"] = 1.50e-6
        changed_link = copy.deepcopy(base)
        changed_link["channel"]["h_hap_m"] = 21000.0
        self.assertNotEqual(canonical_json_sha256(base), canonical_json_sha256(changed_cn))
        self.assertNotEqual(
            canonical_json_sha256(base), canonical_json_sha256(changed_wavelength)
        )
        self.assertNotEqual(canonical_json_sha256(base), canonical_json_sha256(changed_link))


if __name__ == "__main__":
    unittest.main()
```

- [x] Run the focused test before adding the helper:

```powershell
.venv\Scripts\python.exe -m unittest tests.test_phase_parameter_freeze -v
```

The expected RED result is an import failure because `phase_parameter_provenance` and `_phase_provenance` do not yet exist. Do not treat that expected failure as a finished verification result.

### Task 2: Implement one canonical phase provenance record

- [x] Add `phase_parameter_provenance(Cn_phi2, wavelength_m, link_distance_m)` to `src/channel/phase_noise.py`. Validate the three SI inputs with the existing validators, compute `tau_phi2` through `phase_distortion_variance`, compute `c_phi` through `phase_noise_coefficient`, and return exactly these fields:

```python
{
    "parameterization": "scenario_level_effective_Cn_phi2",
    "cn_phi2_m_minus_two_thirds": cn_phi2,
    "wavelength_m": wavelength,
    "link_distance_m": link_distance,
    "tau_phi2": tau_phi2,
    "c_phi": c_phi,
    "units": {
        "cn_phi2_m_minus_two_thirds": "m^(-2/3)",
        "wavelength_m": "m",
        "link_distance_m": "m",
        "tau_phi2": "dimensionless",
        "c_phi": "dimensionless",
    },
    "cn_phi2_scope": "fixed_within_scenario",
    "cn_phi2_relation_to_cn2_profile": (
        "independent; not derived from altitude-dependent C_n^2(h)"
    ),
    "c_phi_is_derived": True,
}
```

- [x] Refactor `phase_coefficient_from_parameters` to return the record's `c_phi`, preserving its existing signature and numerical behavior. Export the new helper from `src/channel/__init__.py`.
- [x] Run the focused test again and require GREEN:

```powershell
.venv\Scripts\python.exe -m unittest tests.test_phase_parameter_freeze -v
```

### Task 3: Resolve provenance once at active entry points

- [x] Add `_phase_provenance(config)` to `scripts/_train.py`. It must read only `channel.cn_phi2_m_minus_two_thirds`, raise the existing author-approval error on `None`, construct `LinkGeometry` from the configured HAP/UAV heights and zenith angle, and call `phase_parameter_provenance` with the configured wavelength and resolved link length. Make `_phase_coefficient(config)` return `_phase_provenance(config)["c_phi"]` so existing callers remain compatible.
- [x] In `_train.py`, resolve `phase_provenance` once and pass `phase_provenance["c_phi"]` to train/evaluation calls. Store the full record next to the legacy scalar `phase_coefficient` in checkpoint and report payloads.
- [x] Update `evaluate.py`, `evaluate_baseline.py`, `smoke_validate_frozen.py`, and `select_validation_baselines.py` to resolve through `_phase_provenance` and include the same record in emitted evaluation/selection metadata wherever those scripts currently emit the scalar coefficient.
- [x] Update `run_baselines.py` and `run_baselines_cached_source_moments.py` to use `phase_parameter_provenance` for their explicit CLI/JSON phase input, retain their existing scalar coefficient field, and add the full record to `parameters`, `settings`, or `run_config` output as appropriate. Do not turn the development JSON's missing value into a default.
- [x] Add `channel.cn_phi2_m_minus_two_thirds` to the shared target/validation required lists in `_common.py`, `_numerical_validation.py`, and `select_learned_fixed_va.py` where those lists currently omit the field. This makes unresolved production configuration fail closed before any target or validation computation.
- [x] Keep `configs/default.yaml` and `configs/channel.yaml` at `null`, add only comments identifying the SI units, scenario-level scope, independence from `cn2_m_minus_two_thirds`, and the fact that `c_phi` is derived. Add an explicit `"cn_phi2": null` field to `configs/baseline_smoke.json` only if its loader's existing fail-closed semantics require the key to distinguish absent from unresolved; keep the existing explicit CLI override test intact.

### Task 4: Bind provenance to existing configuration identity

- [x] Do not create a second hash scheme. Preserve the existing resolved-config SHA-256 used by manifests/checkpoint matching; the focused hash tests must demonstrate that changing `Cn_phi2`, wavelength, or geometry changes that identity.
- [x] Ensure every newly emitted phase provenance record contains the resolved numerical link length and all phase inputs, so an artifact can be audited without reconstructing geometry from prose.
- [x] Do not require a new provenance field in unrelated historical/synthetic artifact fixtures unless the active validator already consumes the modified payload; preserve compatibility for non-target development fixtures.

### Task 5: Record the author-freeze template and decision

- [x] Add a clearly marked current phase-parameter freeze section to `docs/PHYSICAL_PARAMETER_AUDIT.md` (or a directly linked new phase-freeze document) containing: field name, symbol, units, scope, relation to altitude-dependent `C_n^2(h)`, link-length derivation, formula chain, candidate evidence classification, approved-value field, approver/date/source fields, and the explicit current decision `BLOCKED — no author-approved value; production remains null`.
- [x] Update `docs/ASSUMPTIONS.md`, `docs/EQUATIONS.md`, `docs/PAPER_TO_CODE.md`, and `docs/NUMERICAL_PARAMETER_FREEZE.md` to state that the API/provenance implementation is present while the production parameter remains unresolved; do not edit the frozen final model specification.
- [x] Append a new evidence entry to `docs/EVIDENCE.md` after verification, listing the repository search result, candidate classifications, focused test result, and the fact that no experiment/certification workflow was run.
- [x] Append a decision-log entry to `docs/DECISION_LOG.md` recording: retain `null`; do not promote test fixtures or `cn2`; derive `c_phi`; persist provenance; leave lifecycle state not ready.
- [x] Update `docs/PROJECT_STATE.md`, `docs/NEXT_ACTIONS.md`, and `docs/SESSION_HANDOFF.md` with the same blocked author decision and the next action: obtain and freeze the author-approved scenario-level `Cn_phi2` value, then rebind target numerical evidence. Preserve all existing lifecycle gates and the current final-model-spec hash.

### Task 6: Verification and handoff

- [x] Run focused tests only, including the new tests and existing phase/pipeline/full-Z/baseline tests:

```powershell
.venv\Scripts\python.exe -m unittest tests.test_phase_parameter_freeze -v
.venv\Scripts\python.exe -m unittest tests.test_phase_noise -v
.venv\Scripts\python.exe -m unittest tests.test_pipeline_consistency -v
.venv\Scripts\python.exe -m unittest tests.test_holevo_interval -v
.venv\Scripts\python.exe -m unittest tests.test_baseline_development_workflow -v
```

- [x] Run syntax-only verification on changed Python files with `py_compile` (no training or evaluation), then run `git diff --check`.
- [x] Re-read the complete diff and verify that `docs/FINAL_MODEL_SPEC.md` is unchanged, the active full-Z interval is unchanged, no physical phase value was invented, and no target/publication/final-test workflow was invoked.
- [x] Report exact verification outcomes using the repository vocabulary (`CURRENTLY_VERIFIED_PASS`, `FAILED`, `NOT_RUN`, or `BLOCKED_BY_ENVIRONMENT`), list every changed file, and state the one remaining author decision plus the one recommended next task without executing it.

## Plan self-review

- The plan has a RED test before the production helper and a GREEN test after implementation.
- Existing public phase APIs and post-action security flow are preserved; the new record is a small dictionary, not a new abstraction layer.
- The test suite distinguishes effective phase `Cn_phi2` from legacy beam-wander `cn2`, checks dimensional labels and all three sensitivity inputs, and verifies missing/zero semantics.
- The plan has no numerical placeholder that could be mistaken for approval: production stays `null`, while nonzero test values are explicitly fixture inputs.
- No step authorizes lifecycle-gated experiments or changes to frozen specification text.
