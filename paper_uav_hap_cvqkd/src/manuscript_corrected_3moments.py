"""Isolated three-moment correction; protected raw Eqs. (10), (20) reused.

The physical law explicitly conditions the active Eq. (10) distribution on
(0, 1], retaining its AoA atom. Nonideal trusted-detector security remains
unresolved. Numerical Holevo maximization is a diagnostic, not a certified
global error enclosure or a finite-size security claim.
"""
from __future__ import annotations

import math
import warnings

import numpy as np
from scipy.integrate import IntegrationWarning, quad
from scipy.optimize import minimize_scalar

from src.manuscript_literal_3moments import (
    LiteralChannel, ManuscriptModelError, _log_erfc, detector_noise, entropy,
    finite, z_star as literal_z_star,
)

MODEL = 'manuscript_corrected_3moments'
PHYSICAL_LAW = 'active_conditioned_on_0_eta_le_1_preserve_outage'


class CorrectedModelError(ManuscriptModelError):
    """Invalid or unsupported corrected-model input; evaluation fails closed."""


def _agree(first, second, name, tolerance):
    if not math.isclose(first, second, abs_tol=tolerance, rel_tol=tolerance):
        raise CorrectedModelError(f'{name} mismatch: {first!r} versus {second!r}')


class PhysicalFadingDistribution:
    """Separate physical wrapper; the supplied LiteralChannel is unchanged."""

    def __init__(self, raw: LiteralChannel, tolerance=1e-10):
        if not isinstance(raw, LiteralChannel):
            raise CorrectedModelError('raw must be a LiteralChannel')
        if raw.rho != 0:
            raise CorrectedModelError('UNSUPPORTED_NONZERO_BORESIGHT: corrected mode validates rho=0 only')
        self.raw = raw
        self.tolerance = finite(tolerance, 'normalization tolerance', positive=True)
        self.coefficients = raw.coefficients()
        d = self.coefficients['chi2']
        q0 = math.exp(raw.log_Q(d))
        finite(q0, 'Q(d)', positive=True)
        retained = raw.active_moment(0)
        finite(retained, 'retained active probability', positive=True)
        if retained > 1:
            raise CorrectedModelError('Retained active probability exceeds one; no clipping')
        _agree(retained, self.coefficients['C1'] * q0, 'Factive=C1 Q(d)', self.tolerance)
        self.active_normalization = retained
        mass_quad, mass_error = self._integrate_raw(0)
        _agree(retained, mass_quad, 'Independent retained active mass', self.tolerance)
        whole_quad, whole_error = self._integrate_raw(0, upper=math.inf)
        tail_quad, tail_error = self._integrate_raw(0, lower=0, upper=math.inf)
        _agree(whole_quad, 1., 'Full-support raw active mass', self.tolerance)
        _agree(retained + tail_quad, whole_quad, 'Retained plus tail probability', self.tolerance)
        physical_mass = raw.P0 + raw.P1 * mass_quad / retained
        _agree(physical_mass, 1., 'Physical probability normalization', self.tolerance)
        self._diagnostics = dict(
            scientific_model=MODEL, physical_fading_law=PHYSICAL_LAW,
            raw_probability_mass=raw.P0 + raw.P1 * retained,
            physical_probability_mass=physical_mass,
            discarded_raw_mass=raw.P1 * (1 - retained),
            active_normalization=retained, active_retained_mass=retained,
            active_tail_probability=tail_quad, discarded_raw_mass_quadrature=raw.P1 * tail_quad,
            raw_full_support_probability_mass=raw.P0 + raw.P1 * whole_quad,
            independent_active_retained_mass=mass_quad,
            independent_normalized_active_mass=mass_quad / retained,
            quadrature_error_retained=mass_error, quadrature_error_tail=tail_error,
            quadrature_error_full_support=whole_error,
            normalization_status='CURRENTLY_VERIFIED_PASS', normalization_tolerance=self.tolerance,
            normalization_identity='F_active(1)=C1*Q(chi2)',
            raw_equation_10_changed=False, conditioning_is_modeling_choice=True,
            outage_atom=raw.P0, active_probability=raw.P1, validated_boresight_rho=0.,
        )

    def log_active_density_in_log_eta(self, y):
        """RAW active log-density times Jacobian, excluding P1.

        Positive y is exposed only for independent raw-tail diagnostics.
        Physical law callers must restrict their integrations to y<=0.
        """
        y = finite(y, 'log eta')
        if y <= 0 and self.raw.P1 > 0:
            return self.raw.log_continuous_density_in_log_eta(y) - math.log(self.raw.P1)
        c = self.coefficients
        return (math.log(c['chi2']) + c['log_C1'] - math.log(2.)
                - c['chi2'] * math.log(c['B']) + c['chi2'] * y
                + _log_erfc(c['C3'] * (y - math.log(c['B']) + c['mu'])))

    def log_physical_active_density_in_log_eta(self, y):
        y = finite(y, 'physical log eta')
        if y > 0:
            raise CorrectedModelError('Physical density domain is 0<eta<=1')
        return self.log_active_density_in_log_eta(y) - math.log(self.active_normalization)

    def active_density(self, eta):
        """Normalized physical active density, not the mixed law's atom."""
        eta = finite(eta, 'eta', positive=True)
        if eta > 1:
            raise CorrectedModelError('Physical density domain is 0<eta<=1')
        return math.exp(self.log_physical_active_density_in_log_eta(math.log(eta))) / eta

    def _integrate_raw(self, power, *, lower=-math.inf, upper=0., factor=None):
        def integrand(y):
            density = math.exp(self.log_active_density_in_log_eta(y) + power * y)
            return density if factor is None else density * factor(y)
        with warnings.catch_warnings():
            warnings.simplefilter('error', IntegrationWarning)
            try:
                value, error = quad(integrand, lower, upper, epsabs=self.tolerance / 10,
                                    epsrel=self.tolerance / 10, limit=400)
            except (IntegrationWarning, OverflowError) as exc:
                raise CorrectedModelError(f'Independent fading quadrature failed: {exc}') from exc
        value = finite(value, 'fading quadrature', nonnegative=True)
        error = finite(error, 'fading quadrature error', nonnegative=True)
        if error > self.tolerance * max(1., abs(value)):
            raise CorrectedModelError(f'Fading quadrature error exceeds tolerance: {error!r}')
        return value, error

    def diagnostics(self):
        return dict(self._diagnostics)

    def moments(self, *, R=.7, xi_det=.0135, xi_ch=.0186):
        xi_ch = finite(xi_ch, 'channel excess noise', nonnegative=True)
        chi_het = detector_noise(R, xi_det)
        d, B = self.coefficients['chi2'], self.coefficients['B']
        log_q0 = self.raw.log_Q(d)
        m1 = self.raw.P1 * math.exp(math.log(B) + math.log(d / (d + 1.))
                                  + self.raw.log_Q(d + 1.) - log_q0)
        mh = self.raw.P1 * math.exp(.5 * math.log(B) + math.log(d / (d + .5))
                                  + self.raw.log_Q(d + .5) - log_q0)
        mn = 1 + chi_het + (xi_ch - 1) * m1
        m1_quad, m1_error = self._integrate_raw(1.)
        mh_quad, mh_error = self._integrate_raw(.5)
        mn_active_quad, mn_error = self._integrate_raw(
            0., factor=lambda y: 1 + chi_het + math.exp(y) * (xi_ch - 1))
        scale = self.raw.P1 / self.active_normalization
        m1_quad *= scale
        mh_quad *= scale
        mn_quad = self.raw.P0 * (1 + chi_het) + scale * mn_active_quad
        for first, second, name in ((m1, m1_quad, 'mean_eta'), (mh, mh_quad, 'mean_sqrt_eta'),
                                    (mn, mn_quad, 'mean_eta_xi_total')):
            _agree(first, second, name, self.tolerance)
        if not 0 <= mh * mh <= m1 <= 1:
            raise CorrectedModelError('Moment ordering 0<=mh^2<=m1<=1 failed; no clipping')
        raw = self.raw.moments(R=R, xi_det=xi_det, xi_ch=xi_ch)
        return dict(
            **self.diagnostics(), mean_eta=m1, mean_sqrt_eta=mh, mean_eta_xi_total=mn,
            mean_eta_xi=mn, chi_het=chi_het, R=float(R), xi_det=float(xi_det), xi_ch=xi_ch,
            detector_efficiency=float(R), detector_excess_noise=float(xi_det),
            channel_excess_noise=xi_ch, independent_mean_eta=m1_quad,
            independent_mean_sqrt_eta=mh_quad, independent_mean_eta_xi_total=mn_quad,
            moment_quadrature_errors=dict(mean_eta=scale * m1_error, mean_sqrt_eta=scale * mh_error,
                                          mean_eta_xi_total=scale * mn_error),
            raw_mean_eta=raw['mean_eta'], raw_mean_sqrt_eta=raw['mean_sqrt_eta'],
            raw_mean_eta_xi_total=raw['mean_eta_xi'],
            third_moment_raw_to_physical_difference=mn - raw['mean_eta_xi'],
            third_moment_identity_residual=mn - (1 + chi_het + (xi_ch - 1) * m1),
            outage_eta_xi_total_limit=1 + chi_het, moments_status='CURRENTLY_VERIFIED_PASS',
        )


def corrected_channel_moments(raw, *, R=.7, xi_det=.0135, xi_ch=.0186, tolerance=1e-10):
    return PhysicalFadingDistribution(raw, tolerance).moments(R=R, xi_det=xi_det, xi_ch=xi_ch)


def deterministic_moments(T0, *, R=.7, xi_det=.0135, xi_ch=.0186):
    """Analytic delta-law limit, separate from the protected Eq. (10) PDF.

    The tag establishes an exact law rather than inferring determinism from
    nearly equal floating-point fading moments. Squaring a rounded sqrt(T0)
    need not return T0; the exact delta identity is used and audited below.
    """
    T0 = finite(T0, 'deterministic transmissivity', nonnegative=True)
    if T0 > 1:
        raise CorrectedModelError('Deterministic transmissivity must be in [0,1]')
    xi_ch = finite(xi_ch, 'channel excess noise', nonnegative=True)
    chi_het = detector_noise(R, xi_det)
    mn = 1 + chi_het + (xi_ch - 1) * T0
    return dict(moment_law='deterministic_delta', deterministic_transmissivity=T0,
                scientific_model=MODEL, physical_fading_law='analytic_delta_at_T0',
                mean_eta=T0, mean_sqrt_eta=math.sqrt(T0), mean_eta_xi_total=mn,
                mean_eta_xi=mn, chi_het=chi_het, R=float(R), xi_det=float(xi_det), xi_ch=xi_ch,
                detector_efficiency=float(R), detector_excess_noise=float(xi_det),
                channel_excess_noise=xi_ch, physical_probability_mass=1.,
                normalization_status='ANALYTICALLY_NORMALIZED_DELTA_LAW',
                outage_eta_xi_total_limit=1 + chi_het,
                moments_status='ANALYTIC_DETERMINISTIC_LIMIT')


def effective_fading_channel(moments, VA, *, tolerance=1e-10):
    VA = finite(VA, 'VA', positive=True)
    tolerance = finite(tolerance, 'consistency tolerance', positive=True)
    m1 = finite(moments['mean_eta'], 'mean_eta', nonnegative=True)
    mh = finite(moments['mean_sqrt_eta'], 'mean_sqrt_eta', nonnegative=True)
    mn = finite(moments['mean_eta_xi_total'], 'mean_eta_xi_total', nonnegative=True)
    chi_het = finite(moments['chi_het'], 'chi_het', nonnegative=True)
    xi_ch = finite(moments['xi_ch'], 'channel excess noise', nonnegative=True)
    amplitude_squared = mh * mh
    deterministic = moments.get('moment_law') == 'deterministic_delta'
    if deterministic:
        transmission = finite(moments['deterministic_transmissivity'],
                              'deterministic transmissivity', nonnegative=True)
        if transmission > 1 or m1 != transmission or mh != math.sqrt(transmission):
            raise CorrectedModelError('Tagged deterministic moments do not match the exact delta law')
        method = 'analytic_deterministic_delta_identity'
    else:
        transmission = amplitude_squared
        method = 'squared_amplitude_moment'
    if not 0 <= transmission <= m1 <= 1:
        raise CorrectedModelError('Moment ordering 0<=T_eff<=m1<=1 failed; no clipping')
    _agree(mn, 1 + chi_het + (xi_ch - 1) * m1, 'Third-moment identity', tolerance)
    variance = 0. if deterministic else m1 - transmission
    fading_noise = variance * VA
    physical_noise = m1 * xi_ch
    # Regrouping avoids cancellation in the exactly noiseless deterministic limit.
    physical_noise_from_third = mn - (1 + chi_het - m1)
    noise = fading_noise + physical_noise
    noise_from_third = fading_noise + physical_noise_from_third
    finite(noise, 'effective output excess noise', nonnegative=True)
    finite(noise_from_third, 'three-moment effective output excess noise', nonnegative=True)
    _agree(noise, noise_from_third, 'Dual effective excess noise', tolerance)
    b = 1 + m1 * (VA + xi_ch)
    b_from_third = math.fsum(((VA + 1) * m1, mn, -chi_het))
    finite(b, 'Bob pre-detection variance', positive=True)
    _agree(b, b_from_third, 'Dual Bob covariance', tolerance)
    return dict(
        **moments, VA=VA, T_eff=transmission, variance_sqrt_eta=variance,
        effective_transmittance_evaluation_method=method,
        deterministic_channel_handling=deterministic,
        amplitude_square_rounding_residual=amplitude_squared - transmission,
        fading_noise_output=fading_noise, mean_channel_excess_noise_output=physical_noise,
        recovered_channel_excess_noise_output=physical_noise_from_third,
        effective_excess_noise_output=noise, output_excess_noise=noise,
        output_excess_noise_from_third=noise_from_third,
        xi_eff=noise / transmission if transmission > 0 else None,
        b=b, b_from_third=b_from_third, noise_consistency_residual=noise - noise_from_third,
        covariance_consistency_residual=b - b_from_third, consistency_tolerance=tolerance,
        effective_channel_status='CURRENTLY_VERIFIED_PASS' if transmission > 0 else 'ZERO_EFFECTIVE_TRANSMISSION',
    )


def corrected_z_star(effective, C, w):
    """Protected Eq. (20), with corrected T_eff and output-excess product."""
    C = finite(C, 'C', nonnegative=True)
    w = finite(w, 'w', nonnegative=True)
    transmission = finite(effective['T_eff'], 'T_eff', nonnegative=True)
    noise = finite(effective['output_excess_noise'], 'output excess noise', nonnegative=True)
    noise_three = finite(effective['output_excess_noise_from_third'], 'three-moment output excess noise', nonnegative=True)
    # Reuse the literal Eq. (20) algebra without changing its protected inputs or function.
    z = literal_z_star(dict(eta_f=transmission, eta_f_xi_f=noise), C, w)
    z_three = 2 * effective['mean_sqrt_eta'] * C - math.sqrt(2 * noise_three * w)
    _agree(z, z_three, 'Dual corrected Eq. (20)', effective.get('consistency_tolerance', 1e-10))
    return z


def corrected_covariance(effective, VA, Z, *, tolerance=1e-10):
    VA = finite(VA, 'VA', positive=True)
    Z = finite(Z, 'correlation Z')
    tolerance = finite(tolerance, 'physicality tolerance', positive=True)
    a, b = VA + 1., finite(effective['b'], 'Bob pre-detection variance', positive=True)
    if 'VA' in effective and VA != effective['VA']:
        raise CorrectedModelError('Covariance VA differs from the effective-channel VA')
    expected_b = 1 + effective['T_eff'] * VA + effective['output_excess_noise']
    _agree(b, expected_b, 'Covariance/effective input identity', tolerance)
    matrix = np.array([[a, 0., Z, 0.], [0., a, 0., -Z], [Z, 0., b, 0.], [0., -Z, 0., b]])
    minimum_eigenvalue = float(np.linalg.eigvalsh(matrix).min())
    if not np.isfinite(matrix).all() or minimum_eigenvalue <= 0:
        raise CorrectedModelError('Covariance is not positive definite')
    delta = a * a + b * b - 2 * Z * Z
    determinant = (a * b - Z * Z) ** 2
    # Exact factorization avoids subtractive cancellation; no discriminant clipping.
    spectrum_radicand = (a + b) ** 2 - 4 * Z * Z
    discriminant = (a - b) ** 2 * spectrum_radicand
    for name, value in (('Delta', delta), ('D', determinant), ('discriminant', discriminant),
                        ('symplectic spectrum radicand', spectrum_radicand)):
        finite(value, name)
    if spectrum_radicand < 0 or discriminant < 0:
        raise CorrectedModelError('Negative symplectic discriminant; no clipping')
    spectrum_root = math.sqrt(spectrum_radicand)
    lambda_1 = (spectrum_root + abs(a - b)) / 2
    lambda_2 = (spectrum_root - abs(a - b)) / 2
    lambda_3 = a - Z * Z / (b + 1)
    for index, value in enumerate((lambda_1, lambda_2, lambda_3), start=1):
        finite(value, f'lambda_{index}')
    if min(lambda_1, lambda_2, lambda_3) < 1:
        raise CorrectedModelError('Symplectic eigenvalue below one; no clipping')
    return dict(a=a, b=b, Z=Z, Gamma_AB=matrix.tolist(), Delta=delta, D=determinant,
                discriminant=discriminant, direct_discriminant_diagnostic=delta * delta - 4 * determinant,
                lambda_1=lambda_1, lambda_2=lambda_2, lambda_3=lambda_3,
                conditional_symplectic_eigenvalues=[lambda_3], minimum_covariance_eigenvalue=minimum_eigenvalue,
                covariance_physicality_status='CURRENTLY_VERIFIED_PASS', numerical_repairs=[],
                conditional_measurement='ideal_heterodyne_only')


def admissible_correlation_interval(effective, VA, C, w):
    """DBL Eqs. (11)--(13), intersected with the standard-form uncertainty region.

    For the fixed C4 source and phase-compensated independent fading channel,
    nbar=VA/2, c1=mh*C, c2=mh*nbar, nB=(m1*VA+m1*xi_ch)/2.
    Thus nB-c2**2/nbar=N_out/2. No statewise-average shortcut is used.
    """
    VA = finite(VA, 'VA', positive=True)
    C, w = finite(C, 'C', nonnegative=True), finite(w, 'w', nonnegative=True)
    z_star = corrected_z_star(effective, C, w)
    center = 2 * effective['mean_sqrt_eta'] * C
    radius = math.sqrt(2 * w * effective['output_excess_noise'])
    theoretical_lower, theoretical_upper = center - radius, center + radius
    a, b = VA + 1., effective['b']
    cap_squared = min((a - 1.) * (b + 1.), (a + 1.) * (b - 1.))
    finite(cap_squared, 'physical correlation cap squared')
    if cap_squared < 0:
        raise CorrectedModelError('Negative physical correlation cap')
    cap = math.sqrt(cap_squared)
    lower, upper = max(theoretical_lower, -cap), min(theoretical_upper, cap)
    if lower > upper:
        raise CorrectedModelError('EMPTY_CORRELATION_INTERVAL: DBL bound and physical covariance do not intersect')
    _agree(z_star, theoretical_lower, 'Eq. (20)/DBL lower endpoint', effective.get('consistency_tolerance', 1e-10))
    nbar = VA / 2
    return dict(lower=lower, upper=upper, theoretical_lower=theoretical_lower,
                theoretical_upper=theoretical_upper, Z_star=z_star, Z_lower=lower, Z_upper=upper,
                Z_physical_cap=cap, c1=effective['mean_sqrt_eta'] * C,
                c2=effective['mean_sqrt_eta'] * nbar,
                n_B=(effective['mean_eta'] * VA + effective['mean_eta'] * effective['xi_ch']) / 2,
                average_photon_number=nbar, correlation_bound_status='THEORETICALLY_IDENTIFIED_NUMERICALLY_EVALUATED',
                status='VALID', theorem_reference='Denys-Brown-Leverrier arXiv:2103.13945v3 Eqs.(11)-(13)',
                assumptions=['fixed validated centered C4 ensemble', 'phase-compensated independent fading',
                             'unconditioned pooled outcomes including outage', 'asymptotic observed moment interpretation'])


def _ideal_holevo(covariance):
    value = (entropy((covariance['lambda_1'] - 1) / 2)
             + entropy((covariance['lambda_2'] - 1) / 2)
             - entropy((covariance['lambda_3'] - 1) / 2))
    return finite(value, 'ideal heterodyne Holevo', nonnegative=True)


def holevo_interval_maximizer(effective, VA, C, w, *, detector_security_convention='ideal',
                              R=1., xi_det=0., grid_size=257, tolerance=1e-8):
    """Numerical interval search, checked by a separately offset denser grid.

    All local grid maxima receive bounded refinement. This does not assume
    monotonicity or assert a rigorous continuous supremum/error enclosure.
    """
    detector_noise(R, xi_det)
    tolerance = finite(tolerance, 'Holevo maximization tolerance', positive=True)
    if detector_security_convention not in ('ideal', 'trusted', 'untrusted'):
        raise CorrectedModelError('Unknown detector security convention')
    interval = admissible_correlation_interval(effective, VA, C, w)
    if detector_security_convention != 'ideal' or R != 1 or xi_det != 0:
        return dict(interval, status='SCIENTIFICALLY_UNRESOLVED', chi_BE=None, Z_worst=None,
                    lambda_1=None, lambda_2=None, conditional_symplectic_eigenvalues=None,
                    detector_security_convention=detector_security_convention,
                    failure='No independently verified nonideal trusted/untrusted detector Holevo model in this mode',
                    numerical_convergence_status='NOT_RUN')
    if not isinstance(grid_size, int) or grid_size < 17:
        raise CorrectedModelError('Holevo diagnostic grid_size must be an integer >=17')
    lower, upper = interval['lower'], interval['upper']
    invalid = []

    def evaluate(z):
        try:
            cov = corrected_covariance(effective, VA, float(z))
            return _ideal_holevo(cov), cov
        except ManuscriptModelError as exc:
            invalid.append(dict(Z=float(z), failure=str(exc)))
            return None

    grid = np.linspace(lower, upper, grid_size) if lower != upper else np.array([lower])
    rows = [evaluate(z) for z in grid]
    valid = [(float(z), result[0], result[1]) for z, result in zip(grid, rows) if result is not None]
    if not valid:
        raise CorrectedModelError('No numerically physical point in the admissible interval')
    refinements = []
    if lower != upper:
        def objective(z):
            result = evaluate(z)
            return -result[0] if result is not None else math.inf
        for index in range(1, len(grid) - 1):
            left, mid, right = rows[index - 1:index + 2]
            if mid is None or left is None or right is None or mid[0] < max(left[0], right[0]):
                continue
            result = minimize_scalar(objective, bounds=(float(grid[index - 1]), float(grid[index + 1])),
                                     method='bounded', options=dict(xatol=tolerance / 10, maxiter=500))
            refined = evaluate(result.x)
            refinements.append(dict(success=bool(result.success), evaluations=int(result.nfev),
                                    Z=float(result.x), message=str(result.message)))
            if refined is not None:
                valid.append((float(result.x), refined[0], refined[1]))
        # Include an independent search of the full bounded interval, without assuming unimodality.
        result = minimize_scalar(objective,
                                 bounds=(lower, upper), method='bounded',
                                 options=dict(xatol=tolerance / 10, maxiter=500))
        refined = evaluate(result.x)
        refinements.append(dict(success=bool(result.success), evaluations=int(result.nfev),
                                Z=float(result.x), message=str(result.message)))
        if refined is not None:
            valid.append((float(result.x), refined[0], refined[1]))
    best = max(valid, key=lambda row: row[1])
    dense_grid = np.linspace(lower, upper, 2 * grid_size + 1)
    dense_results = [evaluate(z) for z in dense_grid]
    dense_valid = [(float(z), result[0]) for z, result in zip(dense_grid, dense_results) if result is not None]
    dense_best = max(dense_valid, key=lambda row: row[1])
    discrepancy = max(0., dense_best[1] - best[1])
    endpoints = [evaluate(lower), evaluate(upper)]
    numerical_pass = (discrepancy <= tolerance and not invalid
                      and all(row['success'] for row in refinements))
    cov = best[2]
    return dict(interval, status='NUMERICALLY_VERIFIED' if numerical_pass else 'NUMERICAL_CONVERGENCE_FAILED',
                chi_BE=best[1] if numerical_pass else None, Z_worst=best[0],
                diagnostic_best_chi=best[1],
                lambda_1=cov['lambda_1'], lambda_2=cov['lambda_2'],
                conditional_symplectic_eigenvalues=[cov['lambda_3']],
                covariance_physicality_status=cov['covariance_physicality_status'],
                detector_security_convention='ideal', grid_size=grid_size, dense_grid_size=len(dense_grid),
                dense_grid_best_Z=dense_best[0], dense_grid_best_chi=dense_best[1],
                grid_verification_shortfall=discrepancy, tolerance=tolerance, refinements=refinements,
                endpoint_chi=[row[0] if row is not None else None for row in endpoints],
                invalid_covariance_evaluations=invalid, numerical_repairs=[],
                numerical_convergence_status='CURRENTLY_VERIFIED_PASS' if numerical_pass else 'FAILED',
                rigorous_global_error_enclosure=False, monotonicity_assumed=False)
