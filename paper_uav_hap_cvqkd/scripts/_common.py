"""Shared script bootstrap and resolved-configuration validation."""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

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


REPRODUCTION_REQUIRED = [
    "channel.h_hap_m",
    "channel.h_uav_m",
    "channel.wavelength_m",
    "channel.visibility_km",
    "channel.beam_waist_m",
    "channel.aperture_radius_m",
    "channel.cn2_m_minus_two_thirds",
    "channel.excess_noise_snu",
    "cvqkd.beta_reconciliation",
    "cvqkd.fixed_modulation_variance_snu",
    "cvqkd.v_min_snu",
    "cvqkd.v_max_snu",
    "cvqkd.fock_cutoff",
    "training.epochs",
    "training.learning_rate",
    "training.train_fading_samples",
    "training.validation_fading_samples",
    "training.test_fading_samples",
    "training.train_awgn_samples_per_symbol",
    "training.validation_awgn_samples_per_symbol",
    "training.test_awgn_samples_per_symbol",
]

