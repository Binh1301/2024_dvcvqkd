"""Select all fixed baselines on the frozen validation realization only."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time

import torch

from _common import (
    ROOT, holevo_numerical_kwargs, load_yaml, missing_required,
)
from _train import _channel
from src.cvqkd.holevo import shared_fixed_ensemble_holevo_chi
from src.cvqkd.mutual_information import (
    discrete_mutual_information,
    standard_complex_noise,
)
from src.cvqkd.secret_key_rate import fading_secret_key_rate
from src.modulation.joint_ps_gs import Ensemble, PeakPhotonConstraintViolation, reference_ensemble
from src.optimization.baseline_search import validation_only_baseline_search
from src.utils.random import derive_seed, torch_generator
from src.validation.physical_domain import (
    approved_peak_photon_limit, require_preconvergence_domain_ready,
)


REQUIRED = [
    "channel.h_hap_m", "channel.h_uav_m", "channel.wavelength_m",
    "channel.visibility_km", "channel.beam_waist_m", "channel.aperture_radius_m",
    "channel.cn2_m_minus_two_thirds", "channel.excess_noise_distribution.kind",
    "channel.uav_motion.sigma_x_m", "channel.uav_motion.sigma_y_m",
    "channel.uav_motion.sigma_z_m", "channel.uav_motion.sigma_theta_rad",
    "channel.uav_motion.sigma_phi_rad", "channel.uav_motion.sigma_psi_rad",
    "channel.excess_noise_distribution.minimum_snu",
    "channel.excess_noise_distribution.maximum_snu", "cvqkd.beta_reconciliation",
    "cvqkd.v_min_snu", "cvqkd.v_max_snu", "cvqkd.v_a_budget_snu",
    "cvqkd.n_peak_photons", "cvqkd.peak_domain_scope",
    "cvqkd.holevo_numerics.symmetry_tolerance",
    "cvqkd.holevo_numerics.density_trace_tolerance",
    "cvqkd.holevo_numerics.density_eigenvalue_pseudoinverse_tolerance",
    "cvqkd.holevo_numerics.physicality_tolerance",
    "cvqkd.mb_nu", "training.validation_fading_samples",
    "training.seeds.validation_channel",
    "training.seeds.validation_awgn", "baseline_search.va_grid_snu",
    "baseline_search.optimized_mb_nu_grid", "baseline_search.state_batch_size",
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "default.yaml")
    parser.add_argument(
        "--output", type=Path, default=ROOT / "results" / "validation_baseline_selection.json"
    )
    parser.add_argument("--mi-evidence", type=Path,
                        default=ROOT / "results" / "mi_convergence.json")
    parser.add_argument("--fock-evidence", type=Path,
                        default=ROOT / "results" / "fock_convergence.json")
    parser.add_argument("--threshold-evidence", type=Path,
                        default=ROOT / "results" / "holevo_threshold_sensitivity.json")
    parser.add_argument("--runtime-cap-seconds", type=float, default=None)
    args = parser.parse_args()
    config = load_yaml(args.config.resolve())
    missing = missing_required(config, REQUIRED)
    if missing:
        raise ValueError("Unresolved required configuration: " + ", ".join(missing))
    cvqkd = config["cvqkd"]
    n_peak = approved_peak_photon_limit(config)
    require_preconvergence_domain_ready(config)
    evidence_paths = {
        "mi": args.mi_evidence.resolve(), "fock": args.fock_evidence.resolve(),
        "threshold": args.threshold_evidence.resolve(),
    }
    evidence = {name: json.loads(value.read_text(encoding="utf-8"))
                for name, value in evidence_paths.items()}
    awgn_count = evidence["mi"].get("minimum_common_sample_count")
    fock_cutoff = evidence["fock"].get(
        "minimum_common_fock_cutoff_for_listed_ensembles"
    )
    if awgn_count is None or fock_cutoff is None or not evidence["threshold"].get(
        "all_listed_fixtures_pass", False
    ):
        public_candidate_count = (
            3 * len(config["baseline_search"]["va_grid_snu"])
            + len(config["baseline_search"]["optimized_mb_nu_grid"])
            * len(config["baseline_search"]["va_grid_snu"])
        )
        exact_alias_count = 2 * len(config["baseline_search"]["va_grid_snu"])
        payload = {
            "schema_version": "validation-baseline-selection-dependency-blocker-v1",
            "status": "NOT_RUN_NUMERICAL_DEPENDENCY",
            "is_baseline_selection": False,
            "selection_split": "validation",
            "test_set_used": False,
            "publication_training_performed": False,
            "mi_sample_count": awgn_count,
            "fock_cutoff": fock_cutoff,
            "pseudoinverse_threshold_approved": bool(
                evidence["threshold"].get("all_listed_fixtures_pass", False)
            ),
            "public_candidate_count": public_candidate_count,
            "unique_candidate_score_count_after_exact_aliases": (
                public_candidate_count - exact_alias_count
            ),
            "selections": {
                name: None for name in ("uniform", "binomial", "fixed_mb", "optimized_mb")
            },
            "blocker": "MI, Fock, and threshold convergence must all pass before selection.",
            "evidence_sha256": {
                name: hashlib.sha256(value.read_bytes()).hexdigest()
                for name, value in evidence_paths.items()
            },
            "alias_policy": {
                "optimized_mb_nu_0": "exactly reuses Uniform at the same V_A",
                "optimized_mb_nu_0_1": "exactly reuses fixed-MB nu=0.1 at the same V_A",
                "public_candidate_rows_retained": True,
            },
        }
        args.output.resolve().parent.mkdir(parents=True, exist_ok=True)
        args.output.resolve().write_text(
            json.dumps(payload, indent=2) + "\n", encoding="utf-8"
        )
        return 2
    training = config["training"]
    states = _channel(
        config,
        int(training["validation_fading_samples"]),
        derive_seed(int(training["seeds"]["validation_channel"]), "validation_channel"),
    )
    t = torch.as_tensor(states.transmittance, dtype=torch.float64)
    epsilon = torch.as_tensor(states.excess_noise_snu, dtype=torch.float64)
    awgn_count = int(awgn_count)
    state_batch_size = int(config["baseline_search"]["state_batch_size"])
    if state_batch_size <= 0:
        raise ValueError("baseline_search.state_batch_size must be positive.")

    started = time.perf_counter()
    deadline = None if args.runtime_cap_seconds is None else started + args.runtime_cap_seconds
    progress = {"candidate_calls_started": 0, "state_batches_completed": 0}

    class RuntimeCapReached(RuntimeError):
        pass

    def score(scheme: str, va: float, nu: float | None) -> float | None:
        progress["candidate_calls_started"] += 1
        print(f"baseline candidate={progress['candidate_calls_started']} scheme={scheme} "
              f"VA={va:g} nu={nu}", flush=True)
        raw_sum = 0.0
        try:
            full_ensemble = reference_ensemble(
                scheme, batch_size=t.numel(), modulation_variance=va, nu_mb=nu,
                v_min=float(cvqkd["v_min_snu"]), v_max=float(cvqkd["v_max_snu"]),
                n_peak_photons=n_peak,
            )
        except PeakPhotonConstraintViolation:
            return None
        # tau, C, and w depend only on this fixed source ensemble. Evaluate
        # them once, then vectorize channel-dependent Z/covariance/chi over all
        # validation states exactly.
        full_chi = shared_fixed_ensemble_holevo_chi(
            full_ensemble, t, epsilon, fock_cutoff=int(fock_cutoff),
            **holevo_numerical_kwargs(config),
        )
        for batch_index, start in enumerate(range(0, t.numel(), state_batch_size)):
            if deadline is not None and time.perf_counter() >= deadline:
                raise RuntimeCapReached("Validation baseline runtime cap reached.")
            stop = min(start + state_batch_size, t.numel())
            batch_t = t[start:stop]
            batch_epsilon = epsilon[start:stop]
            ensemble = Ensemble(
                full_ensemble.probabilities[start:stop],
                full_ensemble.amplitudes[start:stop],
                full_ensemble.declared_va[start:stop],
                full_ensemble.relative_constellation,
                exact_csi_oracle=True, c4_symmetric=True,
            )
            common_noise = standard_complex_noise(
                (stop - start, 256, awgn_count),
                generator=torch_generator(
                    derive_seed(
                        int(training["seeds"]["validation_awgn"]),
                        "baseline_common_awgn_batch",
                        batch_index,
                    )
                ),
                device=t.device,
            )
            mi = discrete_mutual_information(
                ensemble,
                batch_t,
                batch_epsilon,
                noise_samples_per_symbol=awgn_count,
                standard_noise_samples=common_noise,
                noise_sample_chunk_size=int(
                    config["numerical_validation"]["mi"]["noise_sample_chunk_size"]
                ),
                implementation="product",
            )
            raw = fading_secret_key_rate(
                mi, full_chi[start:stop], float(cvqkd["beta_reconciliation"])
            ).instantaneous_raw
            raw_sum += float(raw.sum())
            progress["state_batches_completed"] += 1
        return raw_sum / float(t.numel())

    try:
        selection = validation_only_baseline_search(
            split_name="validation",
            va_grid=config["baseline_search"]["va_grid_snu"],
            v_min=float(cvqkd["v_min_snu"]), v_max=float(cvqkd["v_max_snu"]),
            va_budget=float(cvqkd["v_a_budget_snu"]),
            reference_mb_nu=float(cvqkd["mb_nu"]),
            optimized_mb_nu_grid=config["baseline_search"]["optimized_mb_nu_grid"],
            score_validation_candidate=score,
        )
    except RuntimeCapReached as error:
        elapsed = time.perf_counter() - started
        total_candidates = 3 * len(config["baseline_search"]["va_grid_snu"]) + (
            len(config["baseline_search"]["optimized_mb_nu_grid"])
            * len(config["baseline_search"]["va_grid_snu"])
        )
        completed = progress["state_batches_completed"]
        total_batches = total_candidates * ((t.numel() + state_batch_size - 1) // state_batch_size)
        payload = {
            "schema_version": "validation-baseline-selection-resource-v2",
            "status": "FAILED_RESOURCE_LIMIT",
            "is_baseline_selection": False,
            "selection_split": "validation", "test_set_used": False,
            "publication_training_performed": False,
            "mi_sample_count": awgn_count, "fock_cutoff": fock_cutoff,
            "runtime_cap_seconds": args.runtime_cap_seconds,
            "observed_elapsed_seconds": elapsed,
            "candidate_calls_started": progress["candidate_calls_started"],
            "state_batches_completed": completed, "total_state_batches": total_batches,
            "projected_total_seconds": None if completed == 0 else elapsed * total_batches / completed,
            "projection_rule": "linear extrapolation from completed equal-shape validation state batches",
            "selections": {name: None for name in ("uniform", "binomial", "fixed_mb", "optimized_mb")},
            "blocker": str(error),
            "evidence_sha256": {name: hashlib.sha256(value.read_bytes()).hexdigest()
                                for name, value in evidence_paths.items()},
        }
        args.output.resolve().parent.mkdir(parents=True, exist_ok=True)
        args.output.resolve().write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote bounded resource evidence to {args.output.resolve()}")
        return 2
    payload = {
        "status": "validation-only selection; no test evaluation and no publication claim",
        "selection_split": "validation",
        "test_set_used": False,
        "validation_state_realization_sha256": states.realization_sha256,
        "common_random_numbers_across_candidates": True,
        "state_batch_size": state_batch_size,
        "mi_sample_count": awgn_count,
        "fock_cutoff": fock_cutoff,
        "convergence_evidence_sha256": {
            name: hashlib.sha256(value.read_bytes()).hexdigest()
            for name, value in evidence_paths.items()
        },
        "averaging_order": "sum per-state raw SKR across batches, divide once by total validation states",
        "energy_fairness": {
            "v_min_snu": cvqkd["v_min_snu"],
            "v_max_snu": cvqkd["v_max_snu"],
            "v_a_budget_snu": cvqkd["v_a_budget_snu"],
            "fixed_candidate_rule": "V_A <= min(V_max,V_A_budget)",
            "n_peak_photons": n_peak,
            "peak_candidate_rule": "max_i |alpha_i|^2 <= n_peak; infeasible candidates are ineligible",
            "same_rule_for_all_eleven_schemes": True,
        },
        "selections": {name: value.as_dict() for name, value in selection.items()},
    }
    args.output.resolve().parent.mkdir(parents=True, exist_ok=True)
    args.output.resolve().write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote validation-only baseline selections to {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
