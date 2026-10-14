"""Gaussian diagnostic with fixed channel excess noise, not a fading bound.

Kept outside src/channel and src/cvqkd to preserve historical cache identities.
The physical fading moments remain intact; only the Gaussian mapping changes.
"""
from __future__ import annotations

import math

import torch

from scripts._common import holevo_numerical_kwargs
from src.cvqkd.holevo import _holevo_from_source_moments
from src.cvqkd.mutual_information import deterministic_mutual_information
from src.manuscript_corrected_evaluator import validate_cached_candidate
from src.manuscript_literal_3moments import finite, z_star

MODEL = "effective_channel_no_fading_noise"
INTERPRETATION = "effective Gaussian approximation ignoring fading-induced variance"


def effective_channel(moments, VA):
    """Use mh² and xi_ch, retaining every physical moment as metadata."""
    VA = finite(VA, "VA", positive=True)
    for name, expected in dict(R=1., xi_det=0., chi_het=1., xi_ch=.0186).items():
        if moments.get(name) != expected:
            raise ValueError(f"This diagnostic requires ideal heterodyne and xi_ch=.0186: {name}")
    m1 = finite(moments["mean_eta"], "mean_eta", nonnegative=True)
    mh = finite(moments["mean_sqrt_eta"], "mean_sqrt_eta", nonnegative=True)
    mn = finite(moments["mean_eta_xi_total"], "mean_eta_xi_total", nonnegative=True)
    if not math.isclose(moments["physical_probability_mass"], 1., abs_tol=1e-10, rel_tol=0.):
        raise ValueError("Physical fading law must already be normalized")
    if not math.isclose(mn, 2+(.0186-1)*m1, abs_tol=1e-10, rel_tol=0.):
        raise ValueError("Input physical three-moment identity failed")
    t = mh*mh
    if not 0 < t <= m1 <= 1:
        raise ValueError("Invalid physical channel moments; no clipping")
    noise = t*.0186
    return dict(moments, scientific_model=MODEL, interpretation=INTERPRETATION,
        VA=VA, T_eff=t, xi_eff=.0186, N_eff=noise,
        output_excess_noise=noise, a=VA+1, b=1+t*(VA+.0186),
        sigma2_complex=1+noise/2,
        fading_noise_included=False, omitted_fading_noise_output=(m1-t)*VA,
        matches_full_fading_covariance=False,
        physical_Bob_variance_diagnostic=1+m1*(VA+.0186),
        validated_fading_security_lower_bound="NOT_ESTABLISHED")


def evaluate_candidate(candidate, moments, config):
    ensemble = validate_cached_candidate(candidate)
    effective = effective_channel(moments, candidate["V_A"])
    t = torch.tensor([effective["T_eff"]], dtype=torch.float64)
    epsilon = torch.tensor([effective["xi_eff"]], dtype=torch.float64)
    numerical = holevo_numerical_kwargs(config)
    z_formula = z_star(dict(eta_f=effective["T_eff"], eta_f_xi_f=effective["N_eff"]),
                       candidate["C"], candidate["w"])
    security = _holevo_from_source_moments(
        ensemble, t, epsilon,
        coherent_correlation=torch.tensor([candidate["C"]], dtype=torch.float64),
        w_raw=torch.tensor([candidate["w"]], dtype=torch.float64), tau=None,
        tau_trace=ensemble.probabilities.sum(dim=-1), require_supported_symmetry=True,
        symmetry_tolerance=numerical["symmetry_tolerance"],
        physicality_tolerance=numerical["physicality_tolerance"],
        maximize_full_interval=False, diagnostics={"backend": MODEL})
    if security.diagnostics["numerical_repairs"] or security.diagnostics["mode"] != "zstar":
        raise ValueError("Diagnostic rejected numerical repairs or a different Holevo target")
    covariance = security.covariance
    lambdas = [float(value[0]) for value in (covariance.lambda1, covariance.lambda2, covariance.lambda3)]
    if min(lambdas) < 1:
        raise ValueError("Nonphysical covariance; no clipping")
    actual_z = float(security.z[0])
    matrix = covariance.matrix[0].tolist()
    if not math.isclose(actual_z, z_formula, abs_tol=1e-13, rel_tol=0.):
        raise ValueError("Equation (20) implementations disagree")
    if not math.isclose(matrix[2][2], effective["b"], abs_tol=1e-13, rel_tol=0.):
        raise ValueError("MI/noise/Bob covariance mismatch")
    mi_rows = [dict(order=order, I_AB=float(deterministic_mutual_information(
        ensemble, t, epsilon, quadrature_order=order, implementation="product")[0]))
        for order in (8, 16, 32)]
    difference = abs(mi_rows[-1]["I_AB"]-mi_rows[-2]["I_AB"])
    if difference > 1e-8:
        raise ValueError("Gaussian discrete-MI quadrature refinement did not pass")
    i_ab, chi = mi_rows[-1]["I_AB"], float(security.chi_be[0])
    p = ensemble.probabilities
    entropy = float((-torch.special.xlogy(p, p).sum()/math.log(2.)))
    if not 0 <= i_ab <= entropy:
        raise ValueError("Discrete mutual information outside entropy domain")
    signal = 2*math.sqrt(effective["T_eff"])*candidate["C"]
    penalty = math.sqrt(2*effective["N_eff"]*candidate["w"])
    return dict(effective, Z_star=actual_z, Z_signal=signal, Z_penalty=penalty,
        Gamma_AB=matrix, lambda_1=lambdas[0], lambda_2=lambdas[1], lambda_3=lambdas[2],
        I_AB=i_ab, chi_BE=chi, beta_rec=.95, beta_I_AB=.95*i_ab, SKR=.95*i_ab-chi,
        MI_method="discrete_256_QAM_effective_Gaussian_GH_product",
        MI_computed_fresh=True, MI_orders=mi_rows,
        MI_last_refinement_difference=difference, MI_refinement_tolerance=1e-8,
        symbol_entropy_bits=entropy, numerical_repairs=[],
        Holevo_target="chi_BE_at_direct_Z_star", full_interval_security_claim=False,
        scientific_validation_status="DIAGNOSTIC_GAUSSIAN_APPROXIMATION_ONLY")
