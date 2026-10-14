"""Literal reproduction of manuscript (37), Eqs. (9)--(20).

Not an independently certified security model. Kept outside src/channel and
src/cvqkd so the historical transitive objective cache identity is unchanged.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math

import numpy as np
from scipy.special import log_ndtr, logsumexp

MODEL = 'manuscript_literal_3moments'
MANUSCRIPT_VERSION = '2026__Binh_s_work (37).pdf'
MANUSCRIPT_SHA256 = '9e7e1af3c218aa8136cf9c00e41309e84c083bab5f8be9735bf14b73e3a8ca95'
LABEL = 'manuscript-literal covariance/Holevo + existing discrete-QAM MI'


class ManuscriptModelError(ValueError):
    """Literal model or numerical domain failed; no equations are repaired."""


def finite(value, name, *, positive=False, nonnegative=False):
    value = float(value)
    if not math.isfinite(value) or (positive and value <= 0) or (nonnegative and value < 0):
        raise ManuscriptModelError(f'Invalid {name}: {value!r}')
    return value


def detector_noise(R=.7, xi_det=.0135):
    R = finite(R, 'R', positive=True)
    if R > 1:
        raise ManuscriptModelError('Detector efficiency R must not exceed 1')
    xi_det = finite(xi_det, 'xi_det', nonnegative=True)
    return (1 + (1 - R) + 2 * xi_det) / R


def total_input_noise(eta, *, R=.7, xi_det=.0135, xi_ch=.0186):
    """Positive-eta definition only; outage is treated by Eq. (14)."""
    eta = finite(eta, 'eta', positive=True)
    if eta > 1:
        raise ManuscriptModelError('eta must be in (0,1]')
    return 1 / eta - 1 + finite(xi_ch, 'xi_ch', nonnegative=True) + detector_noise(R, xi_det) / eta


def _log_erfc(value):
    return math.log(2.) + float(log_ndtr(-math.sqrt(2.) * value))


def _exp(value):
    try:
        return finite(math.exp(value), 'closed-form exponential', nonnegative=True)
    except OverflowError as error:
        raise ManuscriptModelError('Closed-form exponential overflow; no parameter repair') from error


@dataclass(frozen=True)
class LiteralChannel:
    eta_atm: float
    A0: float
    w_eq: float
    sigma_s: float
    sigma_R2: float
    rho: float
    P0: float
    P1: float

    def __post_init__(self):
        for name in ('eta_atm', 'A0', 'w_eq', 'sigma_s'):
            finite(getattr(self, name), name, positive=True)
        for name in ('sigma_R2', 'rho', 'P0', 'P1'):
            finite(getattr(self, name), name, nonnegative=True)
        if self.eta_atm > 1 or self.A0 > 1 or self.P0 > 1 or self.P1 > 1:
            raise ManuscriptModelError('Transmittances/probabilities must not exceed 1')
        if not math.isclose(self.P0 + self.P1, 1., abs_tol=1e-14, rel_tol=0):
            raise ManuscriptModelError('Eq. (9) requires P1=1-P0; no renormalization')
        if self.sigma_R2 == 0 and self.rho == 0:
            raise ManuscriptModelError('C3 is singular; degenerate PDF not specified by this closed form')

    @classmethod
    def from_physical(cls, physical):
        """Eq. (6) uses effective beam width; Eq. (5) uses raw Rytov variance.

        Existing geometry/HV/G_d helpers supply the physical inputs. G_d's
        omitted citation/definition in the PDF remains an implementation gap.
        Historical A0 (unbroadened nu) and aperture-averaged v_sc are NOT used.
        """
        pointing = physical['pointing']
        w_eff = float(pointing['omega_L_m']) * math.sqrt(1 + float(pointing['G_d']))
        nu_ap = math.sqrt(math.pi) * float(physical['receiver_diameter_m']) / (2 * math.sqrt(2) * w_eff)
        a0 = math.erf(nu_ap) ** 2
        w_eq = math.sqrt(w_eff ** 2 * math.sqrt(math.pi) * math.erf(nu_ap)
                         / (2 * nu_ap * math.exp(-nu_ap ** 2)))
        p0 = math.exp(-float(physical['theta_fov_rad']) ** 2 / (2 * float(physical['sigma_o2_rad2'])))
        return cls(float(physical['eta_atm']), a0, w_eq, float(physical['sigma_m']),
                   float(physical['sigma_R0_squared']), float(physical['rho_m']), p0, 1 - p0)

    def coefficients(self):
        B = self.A0 * self.eta_atm
        chi2 = (self.w_eq / (2 * self.sigma_s)) ** 2
        log_C1 = self.rho ** 2 / self.sigma_s ** 2 + .5 * self.sigma_R2 * chi2 * (1 + chi2)
        C3 = (32 * self.rho ** 2 * self.sigma_s ** 2 / self.w_eq ** 4 + 2 * self.sigma_R2) ** (-.5)
        mu = 6 * self.rho ** 2 / self.w_eq ** 2 + .5 * self.sigma_R2 * (1 + 2 * chi2)
        x1 = -math.log(B) + mu
        for name, value in (('B', B), ('chi2', chi2), ('C3', C3)):
            finite(value, name, positive=True)
        finite(mu, 'mu', nonnegative=True)
        return dict(B=B, chi2=chi2, C1=_exp(log_C1), log_C1=log_C1, C3=C3, mu=mu, x1=x1)

    def log_Q(self, a):
        a = finite(a, 'Q exponent', positive=True)
        c = self.coefficients()
        log_q1 = a * c['x1'] - a * c['mu'] + _log_erfc(c['C3'] * c['x1'])
        log_q2 = a * a / (4 * c['C3'] ** 2) - a * c['mu'] + _log_erfc(a / (2 * c['C3']) - c['C3'] * c['x1'])
        return float(logsumexp([log_q1, log_q2])) - math.log(2.)

    def active_moment(self, q):
        """Eq. (12)/(13) (q=1/.5), Eq. (14) active mass (q=0).

        Integral of eta**q times the continuous active law on [0,1]; no
        normalization by retained mass and no historical raw moments.
        """
        q = finite(q, 'moment power', nonnegative=True)
        c = self.coefficients()
        value = _exp(q * math.log(c['B']) + math.log(c['chi2']) + c['log_C1']
                         - math.log(c['chi2'] + q) + self.log_Q(c['chi2'] + q))
        return finite(value, 'active moment', nonnegative=True)

    def log_continuous_density_in_log_eta(self, y):
        """Eq. (10) continuous density times d eta / d log eta.

        This excludes P0 delta_0, which is kept separately. y <= 0 only.
        """
        y = finite(y, 'log eta')
        if y > 0:
            raise ManuscriptModelError('Integration interval is [0,1]')
        if self.P1 == 0:
            return -math.inf
        c = self.coefficients()
        return (math.log(self.P1) + math.log(c['chi2']) + c['log_C1'] - math.log(2.)
                - c['chi2'] * math.log(c['B']) + c['chi2'] * y
                + _log_erfc(c['C3'] * (y - math.log(c['B']) + c['mu'])))

    def moments(self, *, R=.7, xi_det=.0135, xi_ch=.0186, normalization_tolerance=1e-10):
        xi_ch = finite(xi_ch, 'xi_ch', nonnegative=True)
        tolerance = finite(normalization_tolerance, 'normalization_tolerance', positive=True)
        chi_het = detector_noise(R, xi_det)
        mean_eta = self.P1 * self.active_moment(1.)
        mean_sqrt_eta = self.P1 * self.active_moment(.5)
        pdf_mass = self.P0 + self.P1 * self.active_moment(0.)
        mean_eta_xi = mean_eta * (xi_ch - 1) + (1 + chi_het) * pdf_mass
        return dict(mean_eta=mean_eta, mean_sqrt_eta=mean_sqrt_eta, mean_eta_xi=mean_eta_xi,
                    pdf_mass=pdf_mass, normalization_discrepancy=pdf_mass - 1,
                    normalization_status='WITHIN_TOLERANCE' if abs(pdf_mass - 1) <= tolerance else 'DISCREPANCY',
                    normalization_tolerance=tolerance, normalized=False, outage_atom=self.P0,
                    chi_het=chi_het, R=R, xi_det=xi_det, xi_ch=xi_ch,
                    channel_parameters=asdict(self), coefficients=self.coefficients())


def effective_channel(moments, VA):
    VA = finite(VA, 'VA', positive=True)
    m1 = finite(moments['mean_eta'], 'mean_eta', nonnegative=True)
    mh = finite(moments['mean_sqrt_eta'], 'mean_sqrt_eta', nonnegative=True)
    mn = finite(moments['mean_eta_xi'], 'mean_eta_xi', nonnegative=True)
    if mh > 1:
        raise ManuscriptModelError('eta_f outside [0,1]; literal PDF is not a valid effective channel')
    variance = m1 - mh ** 2
    if variance < 0:
        raise ManuscriptModelError('Negative variance_sqrt_eta; no clipping/renormalization')
    noise = finite(variance * VA + mn, 'eta_f_xi_f', nonnegative=True)
    return dict(eta_f=mh, variance_sqrt_eta=variance, eta_f_xi_f=noise,
                xi_f=finite(noise / mh, 'xi_f', nonnegative=True) if mh > 0 else None,
                status='VALID' if mh > 0 else 'ZERO_EFFECTIVE_TRANSMISSION')


def z_star(effective, C, w):
    C, w = finite(C, 'C', nonnegative=True), finite(w, 'w', nonnegative=True)
    eta = finite(effective['eta_f'], 'eta_f', nonnegative=True)
    noise = finite(effective['eta_f_xi_f'], 'eta_f_xi_f', nonnegative=True)
    return finite(2 * math.sqrt(eta) * C - math.sqrt(2 * noise * w), 'Z_star')


def covariance(moments, VA, C, w, *, tolerance=1e-10):
    VA = finite(VA, 'VA', positive=True)
    tolerance = finite(tolerance, 'physicality tolerance', positive=True)
    effective = effective_channel(moments, VA)
    a, b = VA + 1, 1 + effective['eta_f'] * VA + effective['eta_f_xi_f']
    z = z_star(effective, C, w)
    matrix = np.array([[a, 0, z, 0], [0, a, 0, -z], [z, 0, b, 0], [0, -z, 0, b]])
    if not np.isfinite(matrix).all() or np.linalg.eigvalsh(matrix).min() <= 0:
        raise ManuscriptModelError('Covariance is not positive definite')
    delta = a * a + b * b - 2 * z * z
    determinant = (a * b - z * z) ** 2
    discriminant = delta * delta - 4 * determinant
    if discriminant < 0:
        raise ManuscriptModelError('Negative symplectic discriminant; no clipping')
    root = math.sqrt(discriminant)
    squared = ((delta + root) / 2, (delta - root) / 2)
    if min(squared) < 0:
        raise ManuscriptModelError('Negative squared symplectic eigenvalue')
    lambdas = math.sqrt(squared[0]), math.sqrt(squared[1]), a - z * z / (b + 1)
    if not all(math.isfinite(v) for v in lambdas):
        raise ManuscriptModelError('Nonfinite symplectic eigenvalues')
    if min(lambdas) < 1:
        qualifier = 'material' if min(lambdas) < 1 - tolerance else 'within-tolerance numerical'
        raise ManuscriptModelError(f'{qualifier} eigenvalue below 1; entropy undefined, no clipping')
    return dict(**effective, a=a, b=b, Z_star=z, Delta=delta, D=determinant,
                lambda_1=lambdas[0], lambda_2=lambdas[1], lambda_3=lambdas[2],
                Gamma_AB=matrix.tolist(), numerical_repairs=[])


def entropy(x):
    x = finite(x, 'bosonic occupation', nonnegative=True)
    if x == 0:
        return 0.
    return (math.log1p(x) + x * (math.log1p(x) - math.log(x))) / math.log(2.)


def holevo(cov):
    return (entropy((cov['lambda_1'] - 1) / 2) + entropy((cov['lambda_2'] - 1) / 2)
            - entropy((cov['lambda_3'] - 1) / 2))


def evaluate_candidate(candidate, moments, *, distance_km, physical_config_hash, numerical_config_hash):
    """New mode only; same discrete ensemble and GH8 algorithm, no AP path.

    MI input mapping T=eta_f, epsilon=xi_f is explicitly selected too. Its
    likelihood remains the existing one, not a manuscript DM-MI theorem.
    """
    import torch
    import json
    from pathlib import Path
    from scripts.exact_cache_provenance import source_settings, verify_source_payload
    from scripts.run_exact_mb_test2 import ensemble_hash
    from scripts.run_theta10_D55_unconstrained_three_scheme import unconstrained_config
    from src.cvqkd.covariance import quadrature_symmetry_diagnostics
    from src.cvqkd.mutual_information import deterministic_mutual_information
    ensemble = candidate['ensemble']
    source_path = Path(candidate['source_path'])
    if not source_path.is_absolute():
        source_path = Path(__file__).resolve().parents[1] / source_path
    payload = json.loads(source_path.read_text(encoding='utf-8'))
    verified = verify_source_payload(payload, source_settings(unconstrained_config()))
    if (candidate['source_cache_key'] not in (verified['historical_cache_key'], verified['canonical_source_cache_key'])
            or candidate['ensemble_hash'] != payload['ensemble_hash']
            or float(candidate['V_A']).hex() != payload['V_A_hex']
            or float(candidate['nu_raw']).hex() != payload['nu_mb_raw_hex']
            or candidate['C'] != payload['C'] or candidate['w'] != payload['w']):
        raise ManuscriptModelError('Candidate C,w/source identity mismatch; no approximate reuse')
    ensemble.validate(tolerance=1e-12)
    if candidate['ensemble_hash'] != ensemble_hash(ensemble):
        raise ManuscriptModelError('Candidate/ensemble identity mismatch')
    if not math.isclose(float(ensemble.computed_va()[0]), candidate['V_A'], abs_tol=1e-12, rel_tol=1e-12):
        raise ManuscriptModelError('Candidate VA normalization mismatch')
    if not quadrature_symmetry_diagnostics(ensemble).standard_form_supported:
        raise ManuscriptModelError('Asymmetric ensemble incompatible with scalar covariance')
    base = dict(scientific_model=MODEL, manuscript_version=MANUSCRIPT_VERSION,
                manuscript_sha256=MANUSCRIPT_SHA256, pipeline_label=LABEL,
                nu_raw=candidate['nu_raw'], VA=candidate['V_A'], distance_km=distance_km,
                C=candidate['C'], w=candidate['w'], source_cache_key=candidate['source_cache_key'],
                ensemble_hash=candidate['ensemble_hash'], physical_config_hash=physical_config_hash,
                numerical_config_hash=numerical_config_hash, beta_rec=.95, quadrature_order=8,
                equation_11_to_20_mapping='T=eta_f; xi=xi_f (selected implementation convention)',
                MI_mapping='existing discrete GH8/product likelihood with T=eta_f, epsilon=xi_f', **moments)
    effective = effective_channel(moments, candidate['V_A'])
    if effective['eta_f'] == 0:
        record = dict(base, **effective, I_AB=None, chi_BE=None, SKR=None,
                      failure='Undefined xi_f at zero eta_f; no divide-by-zero or fabricated SKR')
        for key in ('a', 'b', 'Z_star', 'lambda_1', 'lambda_2', 'lambda_3'):
            record[key] = None
        return record
    cov = covariance(moments, candidate['V_A'], candidate['C'], candidate['w'])
    mi = float(deterministic_mutual_information(ensemble,
               torch.tensor([cov['eta_f']], dtype=torch.float64), torch.tensor([cov['xi_f']], dtype=torch.float64),
               quadrature_order=8, implementation='product')[0])
    chi = finite(holevo(cov), 'chi_BE', nonnegative=True)
    skr = finite(.95 * mi - chi, 'SKR')
    return {**base, **cov, 'I_AB': mi, 'chi_BE': chi, 'SKR': skr,
            'status': 'PASS_WITH_NORMALIZATION_DISCREPANCY' if moments['normalization_status'] == 'DISCREPANCY' else 'PASS'}
