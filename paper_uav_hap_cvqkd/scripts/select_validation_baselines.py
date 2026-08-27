"""Select all fixed baselines on the frozen validation realization only."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch

from _common import (
    ROOT, holevo_numerical_kwargs, load_yaml, missing_required,
    require_holevo_pseudoinverse_approval,
)
from _train import _channel
from src.cvqkd.holevo import holevo_information
from src.cvqkd.mutual_information import (
    discrete_mutual_information,
    standard_complex_noise,
)
from src.cvqkd.secret_key_rate import fading_secret_key_rate
from src.modulation.joint_ps_gs import PeakPhotonConstraintViolation, reference_ensemble
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
    "cvqkd.mb_nu", "cvqkd.fock_cutoff", "training.validation_fading_samples",
    "training.validation_awgn_samples_per_symbol", "training.seeds.validation_channel",
    "training.seeds.validation_awgn", "baseline_search.va_grid_snu",
    "baseline_search.optimized_mb_nu_grid", "baseline_search.state_batch_size",
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "default.yaml")
    parser.add_argument(
        "--output", type=Path, default=ROOT / "results" / "validation_baseline_selection.json"
    )
    args = parser.parse_args()
    config = load_yaml(args.config.resolve())
    missing = missing_required(config, REQUIRED)
    if missing:
        raise ValueError("Unresolved required configuration: " + ", ".join(missing))
    cvqkd = config["cvqkd"]
    n_peak = approved_peak_photon_limit(config)
    require_preconvergence_domain_ready(config)
    require_holevo_pseudoinverse_approval(config)
    training = config["training"]
    states = _channel(
        config,
        int(training["validation_fading_samples"]),
        derive_seed(int(training["seeds"]["validation_channel"]), "validation_channel"),
    )
    t = torch.as_tensor(states.transmittance, dtype=torch.float64)
    epsilon = torch.as_tensor(states.excess_noise_snu, dtype=torch.float64)
    awgn_count = int(training["validation_awgn_samples_per_symbol"])
    state_batch_size = int(config["baseline_search"]["state_batch_size"])
    if state_batch_size <= 0:
        raise ValueError("baseline_search.state_batch_size must be positive.")

    def score(scheme: str, va: float, nu: float | None) -> float | None:
        raw_sum = 0.0
        for batch_index, start in enumerate(range(0, t.numel(), state_batch_size)):
            stop = min(start + state_batch_size, t.numel())
            batch_t = t[start:stop]
            batch_epsilon = epsilon[start:stop]
            try:
                ensemble = reference_ensemble(
                    scheme,
                    batch_size=stop - start,
                    modulation_variance=va,
                    nu_mb=nu,
                    v_min=float(cvqkd["v_min_snu"]),
                    v_max=float(cvqkd["v_max_snu"]),
                    n_peak_photons=n_peak,
                )
            except PeakPhotonConstraintViolation:
                return None
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
            )
            holevo = holevo_information(
                ensemble,
                batch_t,
                batch_epsilon,
                fock_cutoff=int(cvqkd["fock_cutoff"]),
                **holevo_numerical_kwargs(config),
            )
            raw = fading_secret_key_rate(
                mi, holevo.chi_be, float(cvqkd["beta_reconciliation"])
            ).instantaneous_raw
            raw_sum += float(raw.sum())
        return raw_sum / float(t.numel())

    selection = validation_only_baseline_search(
        split_name="validation",
        va_grid=config["baseline_search"]["va_grid_snu"],
        v_min=float(cvqkd["v_min_snu"]),
        v_max=float(cvqkd["v_max_snu"]),
        va_budget=float(cvqkd["v_a_budget_snu"]),
        reference_mb_nu=float(cvqkd["mb_nu"]),
        optimized_mb_nu_grid=config["baseline_search"]["optimized_mb_nu_grid"],
        score_validation_candidate=score,
    )
    payload = {
        "status": "validation-only selection; no test evaluation and no publication claim",
        "selection_split": "validation",
        "test_set_used": False,
        "validation_state_realization_sha256": states.realization_sha256,
        "common_random_numbers_across_candidates": True,
        "state_batch_size": state_batch_size,
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
