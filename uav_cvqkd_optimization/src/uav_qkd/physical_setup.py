"""Nominal Gaussian-beam sanity only; no channel/SKR backend or model changes."""
import math
from .hap_uav_channel import _finite, _existing_helper, PARENT


def beam_sanity(config, distances_m=(19000., 21940.)):
    wavelength = _finite(config.get('wavelength_m'), 'wavelength_m', minimum=0)
    theta = _finite(config.get('beam_full_divergence_rad'), 'full divergence rad', minimum=0)
    diameter = _finite(config.get('receiver_aperture_diameter_m'), 'aperture diameter m', minimum=0)
    if min(wavelength, theta, diameter) <= 0:
        raise ValueError('Wavelength, full divergence and aperture diameter must be positive')
    curvature = config['wavefront_curvature_radius_m']
    curvature = math.inf if curvature == 'infinity' else _finite(curvature, 'wavefront curvature m', minimum=0)
    helper, path, digest = _existing_helper('pointing_error.py', PARENT)
    w0 = 2*wavelength/(math.pi*theta)
    receivers = []
    for length in distances_m:
        length = _finite(length, 'slant distance m', minimum=0)
        radius, rayleigh = helper.gaussian_beam_radius(w0, wavelength, length, curvature)
        nu = math.sqrt(math.pi)*diameter/(2*math.sqrt(2)*radius)
        receivers.append(dict(distance_m=length, beam_radius_m=radius, beam_diameter_m=2*radius,
                              ideal_centered_circular_capture=-math.expm1(-2*(diameter/2)**2/radius**2),
                              diffraction_only_manuscript_erf_approx=math.erf(nu)**2))
    if not receivers:
        raise ValueError('Provide at least one positive receiver distance')
    return dict(transmitter_waist_radius_m=w0, transmitter_waist_diameter_m=2*w0,
                full_angle_divergence_rad=theta, wavelength_m=wavelength, aperture_diameter_m=diameter,
                rayleigh_range_m=rayleigh, receivers=receivers, turbulence_broadening_applied=False,
                coupling_scope='Nominal diffraction-only centered capture; no G_d, jitter, AoA or atmospheric loss. Not a full channel transmission or SKR.',
                convention='Source manuscript PDF p2: w0=2*lambda/(pi*full_angle), F0 curvature; radius is intensity 1/e^2 radius',
                producer_sha256={path:digest})
