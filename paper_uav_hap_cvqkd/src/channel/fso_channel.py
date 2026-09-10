"""Composite instantaneous HAP-to-UAV FSO channel.

The active path samples atmospheric loss, scintillation, generalized
pointing, and an optional hard AoA gate.  The historical constant-``C_n^2``
beam-wander equation is intentionally not part of this path.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import math

import numpy as np

from src.utils.random import array_sha256

from .aoa import aoa_outage_probability, aoa_variance_rad2, sample_aoa_gate
from .atmospheric_loss import atmospheric_transmittance
from .geometry import LinkGeometry
from .pointing_error import (
    PointingParameters,
    pointing_parameters,
    pointing_power_transmittance,
)
from .scintillation import (
    normalized_lognormal_samples,
    resolve_scintillation_variance,
    rytov_variance_from_profile,
    scintillation_provenance,
)
from .turbulence import (
    UavMotion,
    pointing_displacement_variance_m2,
    uav_translational_variance_m2,
)


class TransmittanceDomainError(ValueError):
    """Raised when a raw active transmittance cannot be admitted physically."""


@dataclass(frozen=True)
class ChannelSamples:
    transmittance: np.ndarray
    radial_displacement_m: np.ndarray
    atmospheric_transmittance: float
    pointing: PointingParameters
    sigma_axis_m: float
    exact_csi_oracle: bool
    metadata: dict[str, Any]
    raw_transmittance: np.ndarray | None = None
    scintillation_factor: np.ndarray | None = None
    aoa_gate: np.ndarray | None = None

    @property
    def mean_transmittance(self) -> float:
        return float(np.mean(self.transmittance))


def compose_raw_transmittance(
    *,
    eta_atm: float,
    scintillation: np.ndarray,
    pointing: np.ndarray,
    aoa_gate: np.ndarray,
) -> np.ndarray:
    """Compose ``T_raw=eta_atm*H_sc*H_p*B_AoA`` without clipping."""

    eta_atm = float(eta_atm)
    if not math.isfinite(eta_atm) or not 0.0 < eta_atm <= 1.0:
        raise ValueError("eta_atm must be finite and lie in (0,1].")
    scintillation = np.asarray(scintillation, dtype=np.float64)
    pointing = np.asarray(pointing, dtype=np.float64)
    aoa_gate = np.asarray(aoa_gate)
    if scintillation.ndim != 1 or pointing.shape != scintillation.shape or aoa_gate.shape != scintillation.shape:
        raise ValueError("Composite channel factors must be equally shaped 1-D arrays.")
    if not np.all(np.isfinite(scintillation)) or np.any(scintillation <= 0.0):
        raise ValueError("H_sc must be finite and strictly positive.")
    if not np.all(np.isfinite(pointing)) or np.any(pointing <= 0.0):
        raise ValueError("H_p must be finite and strictly positive.")
    if not np.all(np.isin(aoa_gate, (0, 1))):
        raise ValueError("B_AoA must contain only zero/one gates.")
    return (eta_atm * scintillation * pointing * aoa_gate).astype(np.float64, copy=False)


def physicalize_raw_transmittance(
    raw_transmittance: np.ndarray,
    *,
    aoa_gate: np.ndarray | None = None,
) -> np.ndarray:
    """Admit a raw realization only if it is already in the physical domain.

    This helper deliberately raises on an active value above one.  Sampling
    code performs rejection/resampling to implement the normalized active law;
    this function never clips and never inserts a floor.
    """

    raw = np.asarray(raw_transmittance, dtype=np.float64)
    if raw.ndim != 1 or not np.all(np.isfinite(raw)) or np.any(raw < 0.0):
        raise TransmittanceDomainError("T_raw must be a finite nonnegative 1-D array.")
    active = np.ones(raw.shape, dtype=bool)
    if aoa_gate is not None:
        gate = np.asarray(aoa_gate)
        if gate.shape != raw.shape or not np.all(np.isin(gate, (0, 1))):
            raise ValueError("aoa_gate must be a zero/one array matching T_raw.")
        active = gate.astype(bool)
        if np.any((~active) & (raw != 0.0)):
            raise TransmittanceDomainError("AoA-outage states must have T_raw=0.")
    if np.any(raw[active] > 1.0):
        raise TransmittanceDomainError(
            "Active T_raw>1 requires truncated-renormalized sampling; pointwise clipping is forbidden."
        )
    return raw.copy()


def _finite_nonnegative(value: float, name: str) -> float:
    value = float(value)
    if not math.isfinite(value) or value < 0.0:
        raise ValueError(f"{name} must be finite and nonnegative.")
    return value


def _resolve_scintillation(
    *,
    geometry: LinkGeometry,
    wavelength_m: float,
    scintillation_log_variance: float | None,
    v_sc_override: float | None,
    aperture_averaging_model: str | None,
    profile_heights_m: np.ndarray | None,
    profile_cn2: np.ndarray | None,
    sigma_R0_squared: float | None,
) -> tuple[float, float | None, str, str]:
    if profile_heights_m is not None or profile_cn2 is not None:
        if profile_heights_m is None or profile_cn2 is None:
            raise ValueError("Both turbulence profile heights and C_n^2 values are required.")
        sigma_R0 = rytov_variance_from_profile(
            profile_heights_m,
            profile_cn2,
            wavelength_m=wavelength_m,
            link_length_m=geometry.link_length_m,
            h_uav_m=geometry.h_uav_m,
            zenith_angle_rad=geometry.zenith_angle_rad,
        )
        profile_model = "external_altitude_profile"
    elif sigma_R0_squared is not None:
        sigma_R0 = _finite_nonnegative(sigma_R0_squared, "sigma_R0_squared")
        profile_model = "externally_resolved_sigma_R0"
    else:
        sigma_R0 = None
        profile_model = "profile_unresolved"

    if scintillation_log_variance is not None:
        v_sc = _finite_nonnegative(scintillation_log_variance, "scintillation_log_variance")
        status = "explicit_v_sc_input"
    elif v_sc_override is not None:
        v_sc = _finite_nonnegative(v_sc_override, "v_sc_override")
        status = "explicit_v_sc_override"
    else:
        if sigma_R0 is None:
            raise ValueError(
                "Scintillation requires an altitude-profile sigma_R0^2 or an explicit v_sc override."
            )
        v_sc, status = resolve_scintillation_variance(
            sigma_R0_squared=sigma_R0,
            aperture_averaging_model=aperture_averaging_model,
            v_sc_override=v_sc_override,
        )
    if v_sc_override is not None:
        v_sc = _finite_nonnegative(v_sc_override, "v_sc_override")
        status = "explicit_v_sc_override"
    return float(v_sc), sigma_R0, status, profile_model


def sample_fso_channel(
    *,
    geometry: LinkGeometry,
    wavelength_m: float,
    visibility_km: float,
    beam_waist_m: float,
    aperture_radius_m: float,
    cn2_m_minus_two_thirds: float | None,
    sample_count: int,
    rng: np.random.Generator,
    uav_motion: UavMotion | None = None,
    scintillation_log_variance: float | None = 0.0,
    v_sc_override: float | None = None,
    aperture_averaging_model: str | None = "disabled",
    turbulence_profile_heights_m: np.ndarray | None = None,
    turbulence_profile_cn2_m_minus_two_thirds: np.ndarray | None = None,
    sigma_R0_squared: float | None = None,
    boresight_x_m: float = 0.0,
    boresight_y_m: float = 0.0,
    sigma_hap_ang_rad: float = 0.0,
    hap_angular_jitter_convention: str = "per_axis",
    aoa_model: str = "disabled",
    sigma_turb_AoA2: float | None = None,
    turbulence_aoa_provenance: str | None = None,
    theta_fov_rad: float | None = None,
) -> ChannelSamples:
    """Draw physical composite channel states.

    The default zero-scintillation/disabled-AoA values are explicit software
    fixture choices.  Production configuration resolution is stricter and
    requires its unresolved physical mappings to be settled first.
    """

    geometry.validate()
    if not isinstance(sample_count, int) or sample_count <= 0:
        raise ValueError("sample_count must be a positive integer.")
    if not isinstance(rng, np.random.Generator):
        raise TypeError("rng must be an explicit numpy.random.Generator.")
    if cn2_m_minus_two_thirds is not None:
        _finite_nonnegative(cn2_m_minus_two_thirds, "cn2_m_minus_two_thirds")
    motion = UavMotion() if uav_motion is None else uav_motion
    motion.validate()
    boresight_x_m = float(boresight_x_m)
    boresight_y_m = float(boresight_y_m)
    if not math.isfinite(boresight_x_m) or not math.isfinite(boresight_y_m):
        raise ValueError("Boresight offsets must be finite.")
    v_sc, sigma_R0, scintillation_status, profile_model = _resolve_scintillation(
        geometry=geometry,
        wavelength_m=wavelength_m,
        scintillation_log_variance=scintillation_log_variance,
        v_sc_override=v_sc_override,
        aperture_averaging_model=aperture_averaging_model,
        profile_heights_m=turbulence_profile_heights_m,
        profile_cn2=turbulence_profile_cn2_m_minus_two_thirds,
        sigma_R0_squared=sigma_R0_squared,
    )
    eta_atm = atmospheric_transmittance(geometry.link_length_m, visibility_km, wavelength_m)
    pointing = pointing_parameters(
        aperture_radius_m, beam_waist_m, wavelength_m, geometry.link_length_m
    )
    sigma2_uav = uav_translational_variance_m2(motion)
    sigma2_hap = pointing_displacement_variance_m2(
        motion=UavMotion(
            sigma_x_m=0.0,
            sigma_y_m=0.0,
            sigma_z_m=0.0,
            sigma_theta_rad=0.0,
            sigma_phi_rad=0.0,
            sigma_psi_rad=0.0,
        ),
        link_length_m=geometry.link_length_m,
        sigma_hap_ang_rad=sigma_hap_ang_rad,
        hap_angular_convention=hap_angular_jitter_convention,
    )
    sigma2_axis = sigma2_uav + sigma2_hap
    sigma_axis_m = math.sqrt(sigma2_axis)

    if aoa_model == "disabled":
        if sigma_turb_AoA2 not in (None, 0.0):
            raise ValueError("Disabled AoA requires sigma_turb_AoA2=0 or null.")
        aoa_sigma2 = aoa_variance_rad2(motion, model="disabled")
        aoa_gate_default = True
        theta_fov = None
    else:
        if theta_fov_rad is None:
            raise ValueError("theta_fov_rad is required when AoA gating is enabled.")
        theta_fov = float(theta_fov_rad)
        aoa_sigma2 = aoa_variance_rad2(
            motion,
            sigma_turb_AoA2=sigma_turb_AoA2,
            model=aoa_model,
            provenance=turbulence_aoa_provenance,
        )
        aoa_gate_default = False

    if aoa_gate_default:
        gate = np.ones(sample_count, dtype=np.int8)
    else:
        # Draw the outage atom once.  Physical-domain rejection applies only
        # to active optical states; it must not renormalize the AoA mass.
        gate = sample_aoa_gate(
            sample_count=sample_count,
            rng=rng,
            sigma_o2=aoa_sigma2,
            theta_fov_rad=theta_fov,
        )
    active_indices = np.flatnonzero(gate == 1)
    active_count = int(active_indices.size)

    def draw_active(batch_size: int) -> dict[str, np.ndarray]:
        radial_x = rng.normal(boresight_x_m, sigma_axis_m, size=batch_size)
        radial_y = rng.normal(boresight_y_m, sigma_axis_m, size=batch_size)
        radial = np.hypot(radial_x, radial_y).astype(np.float64, copy=False)
        h_sc = normalized_lognormal_samples(v_sc, rng, batch_size)
        h_p = np.asarray(pointing_power_transmittance(radial, pointing), dtype=np.float64)
        if np.any(~np.isfinite(h_p)) or np.any(h_p <= 0.0) or np.any(h_p > pointing.t0_power):
            raise FloatingPointError("Generalized pointing loss left its physical support.")
        raw = compose_raw_transmittance(
            eta_atm=eta_atm,
            scintillation=h_sc,
            pointing=h_p,
            aoa_gate=np.ones(batch_size, dtype=np.int8),
        )
        return {
            "radial": radial,
            "h_sc": h_sc,
            "h_p": h_p,
            "raw": raw,
        }

    accepted: dict[str, list[np.ndarray]] = {"radial": [], "h_sc": [], "raw": []}
    accepted_count = 0
    candidate_count = 0
    candidate_raw_sum = 0.0
    candidate_hp_sum = 0.0
    above_one_count = 0
    while accepted_count < active_count:
        batch_size = max(64, 2 * (active_count - accepted_count))
        batch = draw_active(batch_size)
        candidate_count += batch_size
        candidate_raw_sum += float(np.sum(batch["raw"]))
        candidate_hp_sum += float(np.sum(batch["h_p"]))
        above = batch["raw"] > 1.0
        above_one_count += int(np.count_nonzero(above))
        keep = ~above
        take = min(active_count - accepted_count, int(np.count_nonzero(keep)))
        if take:
            indices = np.flatnonzero(keep)[:take]
            for key in accepted:
                accepted[key].append(batch[key][indices])
            accepted_count += take
        if candidate_count > max(100_000, 100_000 * sample_count):
            raise FloatingPointError(
                "Unable to resolve the active T_raw<=1 distribution by rejection sampling."
            )

    radial = np.zeros(sample_count, dtype=np.float64)
    h_sc = np.ones(sample_count, dtype=np.float64)
    raw = np.zeros(sample_count, dtype=np.float64)
    if active_count:
        radial[active_indices] = np.concatenate(accepted["radial"])[:active_count]
        h_sc[active_indices] = np.concatenate(accepted["h_sc"])[:active_count]
        raw[active_indices] = np.concatenate(accepted["raw"])[:active_count]
    transmittance = physicalize_raw_transmittance(raw, aoa_gate=gate)
    p_out = float(np.mean(gate == 0))
    p_in = float(1.0 - p_out)
    p_out_analytic = (
        0.0
        if aoa_gate_default
        else aoa_outage_probability(theta_fov, aoa_sigma2)
    )
    candidate_active_raw_mean = (
        0.0 if candidate_count == 0 else candidate_raw_sum / candidate_count
    )
    raw_mean = float(p_in * candidate_active_raw_mean)
    physical_mean = float(np.mean(transmittance))
    delta = (
        None if physical_mean == 0.0
        else float(abs(raw_mean - physical_mean) / physical_mean)
    )
    candidate_hp_mean = (
        0.0 if candidate_count == 0 else candidate_hp_sum / candidate_count
    )
    raw_identity_mean = float(p_in * eta_atm * candidate_hp_mean)
    profile_hashes = None
    if turbulence_profile_heights_m is not None:
        profile_hashes = {
            "heights_sha256": array_sha256(
                np.asarray(turbulence_profile_heights_m, dtype=np.float64)
            ),
            "cn2_sha256": array_sha256(
                np.asarray(
                    turbulence_profile_cn2_m_minus_two_thirds, dtype=np.float64
                )
            ),
        }
    profile_record = scintillation_provenance(
        sigma_R0_squared=sigma_R0,
        v_sc=v_sc,
        resolution_status=scintillation_status,
        profile_model=profile_model,
    )
    provenance = {
        "geometry": {
            "h_hap_m": float(geometry.h_hap_m),
            "h_uav_m": float(geometry.h_uav_m),
            "zenith_angle_rad": float(geometry.zenith_angle_rad),
            "link_length_m": float(geometry.link_length_m),
        },
        "wavelength_m": float(wavelength_m),
        "visibility_km": float(visibility_km),
        "atmospheric_model": "Kruse extinction with Beer-Lambert eta_atm",
        "turbulence_source": "one shared C_n^2(h) scenario; scalar cn2 retained only as legacy input",
        "legacy_scalar_cn2_m_minus_two_thirds": (
            None
            if cn2_m_minus_two_thirds is None
            else float(cn2_m_minus_two_thirds)
        ),
        "turbulence_profile": {
            "model": profile_model,
            "array_hashes": profile_hashes,
        },
        "scintillation_model": profile_record,
        "aperture_averaging_model": aperture_averaging_model,
        "aperture_averaging_status": scintillation_status,
        "beam_waist_m": float(beam_waist_m),
        "aperture_radius_m": float(aperture_radius_m),
        "pointing_model": "generalized_gaussian_beam",
        "pointing_parameters": {
            "beam_radius_receiver_m": float(pointing.beam_radius_receiver_m),
            "rayleigh_range_m": float(pointing.rayleigh_range_m),
            "t0_power": float(pointing.t0_power),
            "gamma": float(pointing.gamma),
            "scale_radius_m": float(pointing.scale_radius_m),
        },
        "boresight_m": [boresight_x_m, boresight_y_m],
        "uav_motion": {
            name: float(value) for name, value in motion.__dict__.items()
        },
        "sigma_hap_ang_rad": float(sigma_hap_ang_rad),
        "sigma_uav_trans_m2": float(sigma2_uav),
        "sigma_hap_disp_m2": float(sigma2_hap),
        "sigma_axis_m2": float(sigma2_axis),
        "jitter_convention": {
            "uav_transverse": "(sigma_x^2+sigma_y^2)/2 per axis",
            "sigma_z": "excluded from pointing",
            "hap_angular": hap_angular_jitter_convention,
        },
        "aoa_model": aoa_model,
        "sigma_turb_AoA2_rad2": (
            None if sigma_turb_AoA2 is None else float(sigma_turb_AoA2)
        ),
        "turbulence_aoa_provenance": turbulence_aoa_provenance,
        "aoa_sigma_o2_rad2": float(aoa_sigma2),
        "theta_fov_rad": theta_fov,
        "physical_domain_rule": "truncated_renormalized_active_law",
    }
    metadata = {
        "link_length_m": float(geometry.link_length_m),
        "zenith_angle_rad": float(geometry.zenith_angle_rad),
        "sigma2_uav_m2": float(sigma2_uav),
        "sigma2_hap_m2": float(sigma2_hap),
        "sigma2_turbulence_m2": 0.0,
        "sigma2_axis_m2": float(sigma2_axis),
        "rayleigh_scale_convention": "legacy name; sigma_axis is each Rician Cartesian component",
        "displacement_law": "Rician",
        "pointing_model": "generalized_gaussian_beam",
        "sigma_z_included": False,
        "beam_wander_status": "LEGACY_NOT_USED",
        "csi_assumption": "exact instantaneous physical T and epsilon_base oracle; no estimator model",
        "physical_domain_rule": "truncated_renormalized_active_law",
        "raw_transmittance_array_semantics": (
            "pre-admission product for the retained realization; active rows are "
            "conditioned on T_raw<=1"
        ),
        "raw_mean_scope": "unconditioned proposal before active-domain rejection",
        "physical_support_upper": float(
            eta_atm * pointing.t0_power if v_sc == 0.0 else 1.0
        ),
        "p_out": p_out,
        "p_in": p_in,
        "p_out_analytic": float(p_out_analytic),
        "p_above_one": float(
            0.0
            if candidate_count == 0
            else p_in * above_one_count / candidate_count
        ),
        "p_above_one_active": float(
            0.0 if candidate_count == 0 else above_one_count / candidate_count
        ),
        "raw_mean_T": raw_mean,
        "physical_mean_T": physical_mean,
        "delta_T": delta,
        "raw_identity_mean_T": raw_identity_mean,
        "raw_candidate_count": candidate_count,
        "raw_candidate_count_including_outages": candidate_count + (sample_count - active_count),
        "unit_transmittance_atom_created": False,
        "provenance": provenance,
    }
    return ChannelSamples(
        transmittance=np.asarray(transmittance, dtype=np.float64),
        radial_displacement_m=np.asarray(radial, dtype=np.float64),
        atmospheric_transmittance=float(eta_atm),
        pointing=pointing,
        sigma_axis_m=float(sigma_axis_m),
        exact_csi_oracle=True,
        metadata=metadata,
        raw_transmittance=np.asarray(raw, dtype=np.float64),
        scintillation_factor=np.asarray(h_sc, dtype=np.float64),
        aoa_gate=np.asarray(gate, dtype=np.int8),
    )


__all__ = [
    "ChannelSamples",
    "TransmittanceDomainError",
    "compose_raw_transmittance",
    "physicalize_raw_transmittance",
    "sample_fso_channel",
]
