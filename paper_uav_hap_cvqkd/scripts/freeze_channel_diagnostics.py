"""Generate the preregistered frozen-channel diagnostic artifact; no training."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from _common import ROOT, load_yaml

from src.channel.diagnostics import frozen_channel_diagnostics
from src.channel.geometry import LinkGeometry
from src.channel.turbulence import UavMotion


def _required(mapping: dict, key: str):
    if key not in mapping or mapping[key] is None:
        raise ValueError(f"Missing required resolved channel field: {key}")
    return mapping[key]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "default.yaml")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "results" / "frozen_channel_diagnostics.json",
    )
    args = parser.parse_args()
    config = load_yaml(args.config)
    channel = config.get("channel")
    if not isinstance(channel, dict):
        raise ValueError("config.channel must be a mapping.")
    motion_config = _required(channel, "uav_motion")
    epsilon_config = _required(channel, "excess_noise_distribution")
    diagnostics_config = _required(channel, "diagnostics")
    if diagnostics_config.get("classification") != "SOFTWARE_PREREGISTERED":
        raise ValueError("Channel diagnostic seed/count must be SOFTWARE_PREREGISTERED.")
    if epsilon_config.get("kind") != "independent_uniform":
        raise ValueError("The approved channel freeze requires independent_uniform epsilon.")
    if epsilon_config.get("dependence_on_transmittance") != "independent":
        raise ValueError("The approved freeze forbids an invented T-epsilon coupling.")
    geometry = LinkGeometry(
            float(_required(channel, "h_hap_m")),
            float(_required(channel, "h_uav_m")),
            float(_required(channel, "zenith_angle_rad")),
        )
    expected_length = float(_required(channel, "expected_derived_link_length_m"))
    if not abs(geometry.link_length_m - expected_length) <= 1.0e-9:
        raise ValueError(
            "Derived geometry link length disagrees with the author-approved 19 km record."
        )
    payload = frozen_channel_diagnostics(
        geometry=geometry,
        wavelength_m=float(_required(channel, "wavelength_m")),
        visibility_km=float(_required(channel, "visibility_km")),
        beam_waist_m=float(_required(channel, "beam_waist_m")),
        aperture_radius_m=float(_required(channel, "aperture_radius_m")),
        cn2_m_minus_two_thirds=float(_required(channel, "cn2_m_minus_two_thirds")),
        motion=UavMotion(
            sigma_x_m=float(_required(motion_config, "sigma_x_m")),
            sigma_y_m=float(_required(motion_config, "sigma_y_m")),
            sigma_z_m=float(_required(motion_config, "sigma_z_m")),
            sigma_theta_rad=float(_required(motion_config, "sigma_theta_rad")),
            sigma_phi_rad=float(_required(motion_config, "sigma_phi_rad")),
            sigma_psi_rad=float(_required(motion_config, "sigma_psi_rad")),
        ),
        epsilon_minimum_snu=float(_required(epsilon_config, "minimum_snu")),
        epsilon_maximum_snu=float(_required(epsilon_config, "maximum_snu")),
        sample_count=int(_required(diagnostics_config, "sample_count")),
        seed=int(_required(diagnostics_config, "seed")),
        quantile_probabilities=_required(diagnostics_config, "quantile_probabilities"),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": payload["status"],
        "output": str(args.output.resolve()),
        "sample_count": payload["monte_carlo_diagnostic"]["sample_count"],
        "joint_realization_sha256": payload["monte_carlo_diagnostic"]["joint_realization_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
