"""Shared script bootstrap and resolved-configuration validation."""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Any
import math

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as error:
        raise RuntimeError("PyYAML is required; install requirements.txt in an isolated environment.") from error
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Configuration root must be a mapping.")
    return data


def missing_required(config: dict[str, Any], dotted_paths: list[str]) -> list[str]:
    missing: list[str] = []
    for dotted in dotted_paths:
        value: Any = config
        for key in dotted.split("."):
            if not isinstance(value, dict) or key not in value:
                value = None
                break
            value = value[key]
        if value is None:
            missing.append(dotted)
    return missing


def holevo_numerical_kwargs(config: dict[str, Any]) -> dict[str, float]:
    """Resolve every active Holevo numerical threshold from configuration."""

    values = config.get("cvqkd", {}).get("holevo_numerics")
    if not isinstance(values, dict):
        raise ValueError("cvqkd.holevo_numerics must explicitly resolve all thresholds.")
    mapping = {
        "symmetry_tolerance": "symmetry_tolerance",
        "density_trace_tolerance": "density_trace_tolerance",
        "density_eigenvalue_tolerance": "density_eigenvalue_pseudoinverse_tolerance",
        "physicality_tolerance": "physicality_tolerance",
    }
    result: dict[str, float] = {}
    for argument, key in mapping.items():
        value = values.get(key)
        if not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0.0:
            raise ValueError(f"cvqkd.holevo_numerics.{key} must be finite and positive.")
        result[argument] = float(value)
    return result


def require_holevo_pseudoinverse_approval(config: dict[str, Any]) -> None:
    values = config.get("cvqkd", {}).get("holevo_numerics", {})
    if values.get("density_eigenvalue_pseudoinverse_author_approved") is not True:
        raise ValueError(
            "cvqkd.holevo_numerics.density_eigenvalue_pseudoinverse_author_approved "
            "must be explicitly true after sensitivity review."
        )


REPRODUCTION_REQUIRED = [
    "channel.h_hap_m",
    "channel.h_uav_m",
    "channel.wavelength_m",
    "channel.visibility_km",
    "channel.beam_waist_m",
    "channel.aperture_radius_m",
    "channel.cn2_m_minus_two_thirds",
    "channel.uav_motion.sigma_x_m",
    "channel.uav_motion.sigma_y_m",
    "channel.uav_motion.sigma_z_m",
    "channel.uav_motion.sigma_theta_rad",
    "channel.uav_motion.sigma_phi_rad",
    "channel.uav_motion.sigma_psi_rad",
    "channel.excess_noise_distribution.kind",
    "channel.excess_noise_distribution.minimum_snu",
    "channel.excess_noise_distribution.maximum_snu",
    "cvqkd.beta_reconciliation",
    "cvqkd.fixed_modulation_variance_snu",
    "cvqkd.v_min_snu",
    "cvqkd.v_max_snu",
    "cvqkd.v_a_budget_snu",
    "cvqkd.n_peak_photons",
    "cvqkd.peak_domain_scope",
    "cvqkd.mb_nu",
    "cvqkd.fock_cutoff",
    "cvqkd.holevo_numerics.symmetry_tolerance",
    "cvqkd.holevo_numerics.density_trace_tolerance",
    "cvqkd.holevo_numerics.density_eigenvalue_pseudoinverse_tolerance",
    "cvqkd.holevo_numerics.physicality_tolerance",
    "training.epochs",
    "training.optimizer",
    "training.learning_rates.ps",
    "training.learning_rates.gs",
    "training.learning_rates.va",
    "training.energy_dual_learning_rate",
    "training.batch_size",
    "training.validation_patience_epochs",
    "training.validation_min_delta_bits",
    "training.validation_energy_budget_margin_snu",
    "training.gradient_clip_norm",
    "training.independent_training_initialization_seeds",
    "training.train_fading_samples",
    "training.validation_fading_samples",
    "training.test_fading_samples",
    "training.train_awgn_samples_per_symbol",
    "training.validation_awgn_samples_per_symbol",
    "training.test_awgn_samples_per_symbol",
    "baseline_search.va_grid_snu",
    "baseline_search.optimized_mb_nu_grid",
    "baseline_search.state_batch_size",
    "numerical_validation.mi.sample_counts",
    "numerical_validation.mi.absolute_tolerance_bits",
    "numerical_validation.mi.relative_tolerance",
    "numerical_validation.fock.cutoffs",
    "numerical_validation.fock.absolute_tolerance",
    "numerical_validation.fock.relative_tolerance",
    "numerical_validation.holevo_threshold_sensitivity.density_eigenvalue_pseudoinverse_tolerances",
    "numerical_validation.holevo_threshold_sensitivity.absolute_tolerance",
    "numerical_validation.holevo_threshold_sensitivity.relative_tolerance",
]
