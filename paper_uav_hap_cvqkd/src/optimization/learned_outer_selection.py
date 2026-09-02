"""Validation-only outer selection for fixed-VA learned ablations."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import math
from typing import Any, Iterable

from src.optimization.baseline_search import feasible_fixed_va_grid


FIXED_VA_LEARNED_MODES = ("ps", "gs", "ps_gs")
FORBIDDEN_TEST_TOKENS = ("test_raw_skr", "test_per_state", "test_constraints")


@dataclass(frozen=True)
class LearnedFixedVASelection:
    mode: str
    modulation_variance_snu: float
    mean_validation_raw_skr: float
    initialization_seeds: tuple[int, ...]
    checkpoint_ids: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "modulation_variance_snu": self.modulation_variance_snu,
            "mean_validation_raw_skr": self.mean_validation_raw_skr,
            "initialization_seeds": list(self.initialization_seeds),
            "checkpoint_ids": list(self.checkpoint_ids),
            "selection_split": "validation",
            "test_set_used": False,
        }


def validation_only_learned_fixed_va_selection(
    records: Iterable[dict[str, Any]],
    *,
    va_grid: Iterable[float],
    v_min: float,
    v_max: float,
    va_budget: float,
    initialization_seeds: Iterable[int],
) -> dict[str, LearnedFixedVASelection]:
    """Select PS/GS/PS+GS fixed VA using matched validation runs only.

    Every mode/VA candidate must contain exactly the same preregistered seeds
    and training-protocol hash. Incomplete or test-contaminated candidates fail
    closed rather than changing the effective compute budget.
    """

    feasible = feasible_fixed_va_grid(
        va_grid, v_min=v_min, v_max=v_max, va_budget=va_budget
    )
    expected_seeds = tuple(initialization_seeds)
    if not expected_seeds or len(set(expected_seeds)) != len(expected_seeds):
        raise ValueError("initialization_seeds must be a distinct nonempty preregistration.")
    grouped: dict[tuple[str, float], list[dict[str, Any]]] = defaultdict(list)
    protocol_hash: str | None = None
    development_seeds_identity: tuple[tuple[str, int], ...] | None = None
    validation_state_sha256: str | None = None
    for record in records:
        if any(token in record for token in FORBIDDEN_TEST_TOKENS):
            raise ValueError("Outer-selection records must not contain test results.")
        if record.get("test_set_accessed") is not False:
            raise ValueError("Every outer-selection record must attest test_set_accessed=false.")
        mode = record.get("mode")
        va = record.get("fixed_modulation_variance_snu")
        seed = record.get("initialization_seed")
        score = record.get("selected_validation_raw_skr")
        run_protocol_hash = record.get("training_protocol_sha256")
        checkpoint_id = record.get("checkpoint_id")
        record_development_seeds = record.get("development_seeds")
        record_validation_hash = record.get("validation_state_realization_sha256")
        if mode not in FIXED_VA_LEARNED_MODES or va not in feasible:
            raise ValueError("Record mode/VA is outside the preregistered outer-search grid.")
        if seed not in expected_seeds or not isinstance(score, (float, int)) or not math.isfinite(score):
            raise ValueError("Record seed/validation score is invalid or unregistered.")
        if not record.get("validation_budget_feasible", False):
            raise ValueError("Every selected learned checkpoint must be validation-budget feasible.")
        budget_evidence = record.get("validation_expected_budget")
        if not isinstance(budget_evidence, dict) or budget_evidence.get(
            "expected_budget_feasible"
        ) is not True or float(budget_evidence.get("expected_budget_upper_snu", math.inf)) > (
            va_budget + 1e-12
        ):
            raise ValueError("Every selected checkpoint needs test-blind expected-budget evidence.")
        if record.get("selected_validation_peak_feasible") is not True:
            raise ValueError("Every selected learned checkpoint must be peak-domain feasible.")
        if not isinstance(run_protocol_hash, str) or not run_protocol_hash:
            raise ValueError("training_protocol_sha256 is required for compute-budget matching.")
        if not isinstance(checkpoint_id, str) or not checkpoint_id:
            raise ValueError("checkpoint_id is required.")
        if not isinstance(record_development_seeds, dict):
            raise ValueError("development_seeds are required for matched-data selection.")
        required_development = {
            "train_channel", "train_awgn", "validation_channel", "validation_awgn"
        }
        if set(record_development_seeds) != required_development or any(
            not isinstance(value, int) or value < 0
            for value in record_development_seeds.values()
        ):
            raise ValueError("development_seeds must contain the exact train/validation streams.")
        current_seed_identity = tuple(sorted(record_development_seeds.items()))
        if development_seeds_identity is None:
            development_seeds_identity = current_seed_identity
        elif current_seed_identity != development_seeds_identity:
            raise ValueError("All outer-search runs must use identical development data seeds.")
        if not isinstance(record_validation_hash, str) or len(record_validation_hash) != 64:
            raise ValueError("validation_state_realization_sha256 is required.")
        if validation_state_sha256 is None:
            validation_state_sha256 = record_validation_hash
        elif record_validation_hash != validation_state_sha256:
            raise ValueError("All outer-search runs must use the same validation realization.")
        if protocol_hash is None:
            protocol_hash = run_protocol_hash
        elif run_protocol_hash != protocol_hash:
            raise ValueError("All outer-search runs must use the same training/update protocol.")
        grouped[(mode, float(va))].append(record)

    selections: dict[str, LearnedFixedVASelection] = {}
    for mode in FIXED_VA_LEARNED_MODES:
        candidates: list[LearnedFixedVASelection] = []
        for va in feasible:
            candidate_records = grouped.get((mode, va), [])
            seeds = tuple(sorted(record["initialization_seed"] for record in candidate_records))
            if seeds != tuple(sorted(expected_seeds)) or len(candidate_records) != len(expected_seeds):
                raise ValueError(f"Incomplete or duplicated matched seed set for {mode} at VA={va}.")
            ordered = sorted(candidate_records, key=lambda record: record["initialization_seed"])
            candidates.append(
                LearnedFixedVASelection(
                    mode=mode,
                    modulation_variance_snu=va,
                    mean_validation_raw_skr=sum(
                        float(record["selected_validation_raw_skr"]) for record in ordered
                    ) / len(ordered),
                    initialization_seeds=tuple(record["initialization_seed"] for record in ordered),
                    checkpoint_ids=tuple(record["checkpoint_id"] for record in ordered),
                )
            )
        selections[mode] = sorted(
            candidates,
            key=lambda candidate: (
                -candidate.mean_validation_raw_skr,
                candidate.modulation_variance_snu,
            ),
        )[0]
    return selections
