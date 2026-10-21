"""Requested finite-catalog manuscript-style comparison; no security certification.

Replay in a fresh output directory, after creating a matching startup manifest.
Historical scientific modules, caches and results are read-only dependencies.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
import platform
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator, LogLocator
import mpmath as mp
import numpy as np
import scipy
from scipy.integrate import quad
from scipy.special import log_ndtr
import torch

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
sys.path.insert(0, str(ROOT))
from scripts.exact_cache_provenance import source_settings, verify_source_payload
from scripts.optimize_uniform_manuscript_2d import uniform_mi_2d
from scripts.recheck_manuscript_homodyne_noise import M, channel, converted, mi_gh, security
from scripts.run_exact_mb_test2 import ensemble_hash
from scripts.run_theta10_D55_unconstrained_three_scheme import make_ensemble, unconstrained_config

MB_DIR = ROOT/'results/manuscript_homodyne_noise_recheck_20261019'
UNI_DIR = ROOT/'results/uniform_manuscript_2d_optimization_20261019'
MB_CATALOG = ROOT/'results/exact_source_moments_catalog_20261012/all_182_MB_exact_source_moments.csv'
SCHEMES = ('Optimized Uniform', 'Fixed MB', 'Optimized MB')
CHECKS = []


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, value):
    (OUT/name).write_text(json.dumps(value, indent=2, allow_nan=False)+'\n', encoding='utf-8')


def read_csv(path):
    with path.open(encoding='utf-8', newline='') as stream:
        return list(csv.DictReader(stream))


def write_csv(name, rows):
    if not rows:
        (OUT/name).write_text('', encoding='utf-8')
        return
    with (OUT/name).open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def check(name, ok, detail=None):
    record = dict(check=name, status='CURRENTLY_VERIFIED_PASS' if ok else 'FAILED', detail=detail)
    CHECKS.append(record)
    if not ok:
        save('failed_check.json', record)
        raise AssertionError(record)


def channel_at_angle(degrees):
    """Same primitive equations as the immutable recheck, with zeta variable.

    All angle-dependent quantities are recomputed, including both HV integrals.
    The retained [0,1] law includes its separate AoA outage atom; no renormalizing.
    HV/G_d use the previously disclosed repository closure absent from the PDF.
    """
    if not 0 <= degrees <= 60:
        raise ValueError('Zenith angle outside the requested domain')
    wl, theta, h0, h1 = map(M, ('1.55e-6', '233e-6', '1000', '20000'))
    zeta = M(degrees)*mp.pi/180
    sec = 1/mp.cos(zeta)
    dh, k = h1-h0, 2*mp.pi/wl
    length = dh*sec
    w0 = 2*wl/(mp.pi*theta)
    wL = w0*mp.sqrt(1+(length*wl/(mp.pi*w0**2))**2)

    def cn2(h):
        return (M('.00594')*(M(21)/27)**2*(M('1e-5')*h)**10*mp.exp(-h/1000)
                + M('2.7e-16')*mp.exp(-h/1500)+M('1e-14')*mp.exp(-h/100))

    knots = [h0, M(2000), M(5000), M(10000), h1]
    jry = mp.quad(lambda h: cn2(h)*(h-h0)**(M(5)/6), knots)
    jmu = mp.quad(lambda h: cn2(h)*((h-h0)/dh)**(M(5)/3), knots)
    sigma_R2 = M('2.25')*k**(M(7)/6)*sec**(M(11)/6)*jry
    beam_lambda = 2*length/(k*wL**2)
    gd = M('4.35')*beam_lambda**(M(5)/6)*k**(M(7)/6)*dh**(M(5)/6)*sec**(M(11)/6)*jmu
    weff = wL*mp.sqrt(1+gd)
    ap = mp.sqrt(mp.pi)*M('.08')/(2*mp.sqrt(2)*weff)
    A0 = mp.erf(ap)**2
    weq = mp.sqrt(weff**2*mp.sqrt(mp.pi)*mp.erf(ap)/(2*ap*mp.exp(-ap**2)))
    sigma_s = mp.sqrt(1+(length*M('15.61e-6'))**2)
    eta_atm = M('.92')**sec
    P0 = mp.exp(-M('6.25e-3')**2/(2*M('1.5e-3')**2))
    P1, rho = 1-P0, M(0)
    d = (weq/(2*sigma_s))**2
    C1 = mp.exp(rho**2/sigma_s**2+sigma_R2*d*(1+d)/2)
    C3 = (32*rho**2*sigma_s**2/weq**4+2*sigma_R2)**(-M('.5'))
    mu = 6*rho**2/weq**2+sigma_R2*(1+2*d)/2
    B = A0*eta_atm
    x1 = -mp.log(B)+mu

    def Q(a):
        return (mp.exp(a*x1-a*mu)*mp.erfc(C3*x1)
                + mp.exp(a*a/(4*C3*C3)-a*mu)*mp.erfc(a/(2*C3)-C3*x1))/2

    def moment(q):
        return P1*B**q*d*C1/(d+q)*Q(d+q)

    return dict(L_m=length, zeta_rad=zeta, w0_m=w0, wL_m=wL, G_d=gd,
                w_eff_m=weff, w_eq_m=weq, sigma_s_m=sigma_s, sigma_R2=sigma_R2,
                eta_atm=eta_atm, A0=A0, P0=P0, P1=P1, rho=rho, chi=mp.sqrt(d),
                chi2=d, C1=C1, C3=C3, mu=mu, B=B, x1=x1,
                Q_chi2=Q(d), Q_chi2_plus_half=Q(d+M('.5')), Q_chi2_plus_one=Q(d+1),
                mean_eta=moment(1), mean_sqrt_eta=moment(M('.5')),
                pdf_mass=P0+moment(0), mu2_integral=jmu, rytov_integral=jry)


def load_roster():
    config = unconstrained_config()
    settings = source_settings(config)
    roster, candidates, arrays = [], [], {}
    inputs = [MB_CATALOG, UNI_DIR/'all_candidates.csv', UNI_DIR/'summary.json', MB_DIR/'result.json']
    for directory in (MB_DIR, UNI_DIR):
        receipt = json.loads((directory/'validation_receipt.json').read_text(encoding='utf-8'))
        for name, value in receipt['artifact_sha256'].items():
            check('prior_receipt:'+name, sha(ROOT/name) == value)
        inputs.append(directory/'validation_receipt.json')
    sources = [('Uniform', r) for r in read_csv(UNI_DIR/'all_candidates.csv')]
    sources += [('MB', r) for r in read_csv(MB_CATALOG)]
    for family, row in sources:
        path = ROOT/row['source_path']
        payload = json.loads(path.read_text(encoding='utf-8'))
        verification = verify_source_payload(payload, settings)
        va, nu = float(row['VA']), 0. if family == 'Uniform' else float(row['nu_raw'])
        identity = (family, nu.hex(), va.hex())
        if any(c['identity'] == identity for c in candidates):
            raise ValueError('Duplicate source parameters')
        ensemble = make_ensemble(config, family, nu, va)
        eh = ensemble_hash(ensemble)
        p, a = ensemble.probabilities[0].numpy(), ensemble.amplitudes[0].numpy()
        check('source_identity:'+eh, payload['ensemble_hash'] == eh
              and float.fromhex(payload['V_A_hex']) == va
              and float.fromhex(payload['nu_mb_raw_hex']) == nu
              and float(payload['C']) == float(row['C']) and float(payload['w']) == float(row['w'])
              and int(payload['support_size']) == 256 and payload['C'] > 0 and payload['w'] >= 0)
        if 'source_sha256' in row:
            check('source_full_file_sha:'+eh, sha(path) == row['source_sha256'])
        x, ix = np.unique(a.real, return_inverse=True)
        y, iy = np.unique(a.imag, return_inverse=True)
        px, py = np.bincount(ix, weights=p), np.bincount(iy, weights=p)
        raw = np.arange(16)-7.5
        target = np.exp(-nu*raw**2); target /= target.sum()
        scale = math.sqrt(va/(4*np.dot(target, raw**2)))
        check('source_PMF_energy_geometry:'+eh, len(p) == 256 and np.all(p > 0)
              and abs(p.sum()-1) < 1e-14 and abs(2*np.dot(p, abs(a)**2)-va) < 2e-12
              and np.max(abs(p-px[ix]*py[iy])) < 1e-14
              and max(np.max(abs(px-target)), np.max(abs(py-target))) < 2e-14
              and max(np.max(abs(x-scale*raw)), np.max(abs(y-scale*raw))) < 2e-13)
        item = dict(family=family, nu_raw=nu, VA=va, nu_raw_hex=nu.hex(), VA_hex=va.hex(),
                    C=payload['C'], w=payload['w'], ensemble_hash=eh,
                    source_path=path.relative_to(ROOT).as_posix(), source_sha256=sha(path),
                    cache_key=payload['cache_key'], canonical_cache_key=verification['canonical_source_cache_key'],
                    source_moment_route=payload['source_moment_route'], support_size=256)
        roster.append(item)
        candidates.append(dict(**item, identity=identity, p=p, alpha=a))
        arrays[eh+'_p'], arrays[eh+'_alpha'] = p, a
    check('catalog_sizes', sum(c['family'] == 'Uniform' for c in candidates) == 36
          and sum(c['family'] == 'MB' for c in candidates) == 182)
    fixed = next(c for c in candidates if c['family'] == 'MB' and c['nu_raw'] == .165 and c['VA'] == 5.475)
    check('fixed_MB_exact_Cw', fixed['C'] == 3.1986564642787387 and fixed['w'] == 9.973886145561931e-7)
    write_csv('source_roster.csv', roster)
    np.savez(OUT/'verified_ensembles.npz', **arrays)
    deps = {p for folder in ('src/channel', 'src/cvqkd', 'src/modulation') for p in (ROOT/folder).glob('*.py')}
    deps.update(ROOT/p for p in ('scripts/recheck_manuscript_homodyne_noise.py', 'scripts/optimize_uniform_manuscript_2d.py',
                'scripts/exact_cache_provenance.py', 'scripts/run_exact_mb_test2.py',
                'scripts/run_theta10_D55_unconstrained_three_scheme.py', 'scripts/_common.py',
                'scripts/full_support_c4_worker.py', 'configs/default.yaml', 'configs/channel.yaml'))
    deps.update(inputs)
    save('input_manifest.json', {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(deps)})
    return candidates, fixed


def evaluate(ch, candidate, degrees):
    m = security(ch['mean_eta'], ch['mean_sqrt_eta'], M(candidate['VA']), M(candidate['C']), M(candidate['w']))
    if not m['physical']:
        raise ValueError(('Unphysical covariance', degrees, candidate['identity']))
    vals = [uniform_mi_2d(candidate['p'], candidate['alpha'], float(m['eta_f']),
                           float(m['eta_f_xi_f']), order) for order in (16, 32, 64)]
    gh_delta = max(abs(v-vals[-1]) for v in vals)
    V, W, Z = [float(m[k]) for k in ('V', 'W', 'Z')]
    gamma = np.array([[V,0,Z,0],[0,V,0,-Z],[Z,0,W,0],[0,-Z,0,W]])
    omega = np.kron(np.eye(2), np.array([[0.,1.],[-1.,0.]]))
    eig = np.sort(abs(np.linalg.eigvals(1j*omega@gamma)))[::2]
    spectrum_delta = float(max(abs(eig-np.sort([float(m['nu_1']), float(m['nu_2'])]))))
    uncertainty_min = float(np.linalg.eigvalsh(gamma+1j*omega).min())
    raw = M('.95')*M(vals[-1])-m['chi_BE']
    check(f'evaluation:{degrees}:{candidate["ensemble_hash"]}', gh_delta < 2e-13
          and 0 <= vals[-1] <= -float(np.dot(candidate['p'], np.log2(candidate['p'])))
          and uncertainty_min > 0 and spectrum_delta < 2e-11
          and abs(m['eta_f_xi_f']-((ch['mean_eta']-ch['mean_sqrt_eta']**2)*M(candidate['VA'])
                                  +M('.0186')*ch['mean_eta'])) < M('1e-65'))
    row = dict(zenith_deg=degrees, distance_km=float(ch['L_m']/1000), family=candidate['family'],
               nu_raw=candidate['nu_raw'], VA=candidate['VA'], C=candidate['C'], w=candidate['w'],
               I_AB_2D=vals[-1], beta_I_AB=float(M('.95')*M(vals[-1])), chi_BE=float(m['chi_BE']), K_raw=float(raw),
               eta_f=float(m['eta_f']), xi_f=float(m['xi_f']), N=float(m['eta_f_xi_f']),
               V=V, W=W, Z=Z, nu_1=float(m['nu_1']), nu_2=float(m['nu_2']), nu_3=float(m['nu_3']),
               MI_GH16=vals[0], MI_GH32=vals[1], MI_GH64=vals[2], GH_max_difference=gh_delta,
               uncertainty_min_eigenvalue=uncertainty_min, matrix_spectrum_max_difference=spectrum_delta,
               ensemble_hash=candidate['ensemble_hash'], source_sha256=candidate['source_sha256'])
    return row, m


def quadrature_control(ch, degrees):
    rows = []
    for q, key in ((0, 'pdf_mass'), (.5, 'mean_sqrt_eta'), (1, 'mean_eta')):
        d,b,c1,c3,mu,p1 = [float(ch[k]) for k in ('chi2','B','C1','C3','mu','P1')]

        def integrand(y):
            return math.exp(math.log(p1*d*c1/2)-d*math.log(b)+(d+q)*y+math.log(2)
                            +float(log_ndtr(-math.sqrt(2)*c3*(y-math.log(b)+mu))))

        value, error = quad(integrand, -math.inf, 0, epsabs=2e-15, epsrel=2e-13, limit=400)
        if q == 0:
            value += float(ch['P0'])
        delta = value-float(ch[key])
        check(f'closed_form_vs_direct_integral:{degrees}:{key}', abs(delta) < 2e-13, delta)
        rows.append(dict(zenith_deg=degrees, quantity=key, closed_form=float(ch[key]),
                         direct_integral=value, residual=delta, error_estimate=error))
    return rows


def plot(rows):
    x = np.array([r['zenith_deg'] for r in rows])
    series = [('Uniform_K_raw','tab:blue','Optimized Uniform 256-QAM'),
              ('Fixed_MB_K_raw','tab:orange','Fixed MB-shaped 256-QAM'),
              ('Optimized_MB_K_raw','tab:red','Optimized MB-shaped 256-QAM')]
    metadata = []
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':12,'pdf.fonttype':42,
                         'axes.titlesize':18,'axes.labelsize':15})
    for logarithmic in (True, False):
        fig, ax = plt.subplots(figsize=(10, 6.6), facecolor='white')
        for key, color, label in series:
            y = np.array([r[key] for r in rows])
            if logarithmic and not np.any(y > 0):
                label += ' (no positive values)'
            shown = np.where(y > 0, y, np.nan) if logarithmic else y
            ax.plot(x, shown, '-o', color=color, lw=1.8, ms=4, label=label)
            metadata.append(dict(scale='log' if logarithmic else 'linear', scheme=key,
                                 evaluated=len(y), positive=int(sum(y > 0)), nonpositive=int(sum(y <= 0)),
                                 displayed=int(sum(np.isfinite(shown)))))
        if logarithmic:
            ax.set_yscale('log')
            ax.yaxis.set_minor_locator(LogLocator(base=10, subs=np.arange(2,10)*.1))
        else:
            ax.axhline(0, color='.25', linewidth=.9)
            ax.yaxis.set_minor_locator(AutoMinorLocator())
            ax.ticklabel_format(axis='y', style='sci', scilimits=(0,0))
        ax.set(title='SKR versus Zenith Angle', xlabel='Zenith Angle (deg)',
               ylabel='Secret Key Rate (bits/use)', xlim=(0,60))
        ax.set_xticks(np.arange(0,61,10)); ax.xaxis.set_minor_locator(AutoMinorLocator(2))
        ax.grid(True, which='major', color='.80', linewidth=.7)
        ax.grid(True, which='minor', color='.91', linewidth=.45)
        ax.legend(loc='upper right', fontsize=10, framealpha=.96)
        fig.tight_layout()
        name = 'skr_vs_zenith_angle'+('' if logarithmic else '_linear')
        fig.savefig(OUT/(name+'.png'), dpi=350)
        fig.savefig(OUT/(name+'.pdf'))
        plt.close(fig)
    save('plot_metadata.json', metadata)


def main():
    if (OUT/'summary.json').exists():
        raise FileExistsError('Completed sweep is immutable')
    torch.set_num_threads(1)
    mp.mp.dps = 80
    startup = json.loads((OUT/'startup_manifest.json').read_text(encoding='utf-8'))
    check('manuscript_identity', sha(Path(startup['manuscript_path'])) == startup['manuscript_sha256']
          == '84e1ba495d7f57ea1147426eac9a38fbadf59bae5edc6d7f17b9e1b4c9f192cc')
    candidates, fixed = load_roster()
    old_MB = json.loads((MB_DIR/'result.json').read_text(encoding='utf-8'))
    old_Uni = json.loads((UNI_DIR/'summary.json').read_text(encoding='utf-8'))
    ref_ch = channel_at_angle(30)
    original_ch = channel()
    check('all_channel_fields_match_immutable_30deg_recheck', all(abs(ref_ch[k]-original_ch[k])
          < M('1e-60')*max(1, abs(original_ch[k])) for k in ref_ch))
    for k in ('mean_eta', 'mean_sqrt_eta'):
        check('stored_reference:'+k, abs(ref_ch[k]-M(old_MB['high_precision_model'][k])) < M('1e-60'))
    for deg, distance in ((0,19), (30,21.9393102292), (60,38)):
        check(f'geometry:{deg}', abs(19/math.cos(math.radians(deg))-distance) < 1e-10)
    reference = []
    for c, expected in ((fixed, old_MB['model']['K']),
                        (next(c for c in candidates if c['family'] == 'Uniform' and c['VA'] == .0475), old_Uni['best']['K_raw'])):
        row, _ = evaluate(ref_ch, c, 30)
        check('reference_K:'+c['family'], abs(row['K_raw']-expected) < 2e-13, row['K_raw']-expected)
        reference.append(dict(**row, stored_reference_K=expected, residual=row['K_raw']-expected))
    save('reference_gate.json', dict(status='CURRENTLY_VERIFIED_PASS', references=reference,
                                   channel=converted(ref_ch, precise=True), checks=CHECKS.copy()))
    print('REFERENCE_GATE PASS', [(r['family'],r['K_raw']) for r in reference], flush=True)
    save('protocol.json', dict(scope='MANUSCRIPT_STYLE_2D_MI_HOMODYNE_HOLEVO_NUMERICAL_COMPARISON',
          request_sha256=sha(OUT/'request.txt'), initial_angles=list(range(0,61,2)), refinement_step_deg=.25,
          catalogs={'Uniform':36,'MB':182}, candidate_selection='maximum raw K; deterministic roster-order tie break',
          MI='normalized 2D Gaussian; 2sqrt(eta_f)*alpha; component variance 1+N; no 1/2',
          Holevo='unchanged imported homodyne security() including sqrt(V*(V-Z^2/W))',
          xi_ch=.0186, beta=.95, R=1, xi_det=0, normalization='VA=2*nbar', integration_domain=[0,1],
          PDF_renormalized=False, source_interpolation=False, SKR_interpolation=False, source_moments_recomputed=False,
          quadrature_orders=[16,32,64], GH_absolute_tolerance=2e-13, entropy_decimal_digits=80,
          optical=dict(wavelength_m=1.55e-6,full_divergence_rad=233e-6,receiver_diameter_m=.08,
             h_HAP_m=20000,h_UAV_m=1000,jitter_rad=15.61e-6,sigma_h_m=1,boresight_m=0,
             sigma_AoA_rad=1.5e-3,FOV_half_angle_rad=6.25e-3,tau_zen=.92,wind_m_s=21,Cn2_ground=1e-14),
          security_status='UNVALIDATED_SECURITY_MODEL', lifecycle='NOT_READY_FOR_PUBLICATION_SCALE_RUNS',
          global_optimality_certified=False, frozen_hash_conflict_preserved=True))
    save('environment.json', dict(python=sys.version,platform=platform.platform(),numpy=np.__version__,
          scipy=scipy.__version__,mpmath=mp.__version__,matplotlib=matplotlib.__version__,torch=torch.__version__,
          torch_threads=torch.get_num_threads(),producer_sha256=sha(Path(__file__))))
    results, details, channels, all_candidates, convergences = {}, [], {}, [], []
    high_models, direct_controls, integral_controls = [], [], []

    def sweep_angle(deg, stage):
        if deg in results:
            return
        ch = channel_at_angle(deg)
        check(f'channel_domain:{deg}', abs(ch['pdf_mass']-1) < M('1e-25')
              and 0 < ch['mean_sqrt_eta']**2 <= ch['mean_eta'] <= ch['P1'] <= 1)
        channels[str(deg)] = converted(ch, precise=True)
        evaluated, models = [], {}
        for c in candidates:
            r,m = evaluate(ch,c,deg)
            evaluated.append(r);models[c['ensemble_hash']] = m
        all_candidates.extend(evaluated)
        uniform = max((r for r in evaluated if r['family'] == 'Uniform'), key=lambda r:r['K_raw'])
        mb_fixed = next(r for r in evaluated if r['ensemble_hash'] == fixed['ensemble_hash'])
        mb_opt = max((r for r in evaluated if r['family'] == 'MB'), key=lambda r:r['K_raw'])
        for scheme, r in zip(SCHEMES, (uniform,mb_fixed,mb_opt)):
            details.append(dict(scheme=scheme, grid_stage=stage, **r))
            model = models[r['ensemble_hash']]
            high_models.append(dict(scheme=scheme,zenith_deg=deg,ensemble_hash=r['ensemble_hash'],
                                   model=converted(model, precise=True)))
            for order in (16,32,64):
                convergences.append(dict(scheme=scheme,zenith_deg=deg,GH_order=order,
                    I_AB_2D=r['MI_GH'+str(order)],difference_from_GH64=r['MI_GH'+str(order)]-r['I_AB_2D']))
        gap = mb_opt['K_raw']-mb_fixed['K_raw']
        check(f'optimized_MB_contains_fixed:{deg}', gap >= 0)
        results[deg] = dict(zenith_deg=deg,distance_km=float(ch['L_m']/1000),grid_stage=stage,
            Uniform_optimal_VA=uniform['VA'],Uniform_K_raw=uniform['K_raw'],Fixed_MB_K_raw=mb_fixed['K_raw'],
            MB_optimal_nu_raw=mb_opt['nu_raw'],MB_optimal_VA=mb_opt['VA'],Optimized_MB_K_raw=mb_opt['K_raw'],
            MB_improvement_absolute=gap,MB_improvement_percent=100*gap/mb_fixed['K_raw'] if mb_fixed['K_raw'] > 0 else None)
        if deg in (0,30,60):
            integral_controls.extend(quadrature_control(ch,deg))
            for r in (uniform,mb_fixed,mb_opt):
                c = next(c for c in candidates if c['ensemble_hash'] == r['ensemble_hash'])
                direct = mi_gh(c['p'],c['alpha'],r['eta_f'],r['N'],16,dimension=2)
                delta = direct-r['MI_GH16']
                check(f'full_256_mixture_vs_product_tensor:{deg}:{r["ensemble_hash"]}',abs(delta) < 2e-13,delta)
                direct_controls.append(dict(zenith_deg=deg,ensemble_hash=r['ensemble_hash'],GH_order=16,
                                           direct_full_mixture=direct,product_tensor=r['MI_GH16'],residual=delta))
            with mp.workdps(110):
                higher = channel_at_angle(deg)
                c = fixed
                higher_m = security(higher['mean_eta'],higher['mean_sqrt_eta'],M(c['VA']),M(c['C']),M(c['w']))
                check(f'80_to_110_digit_channel_entropy:{deg}',
                      abs(higher_m['chi_BE']-models[c['ensemble_hash']]['chi_BE']) < M('1e-65'))
        write_csv('all_candidate_evaluations.csv',all_candidates)
        write_csv('skr_vs_zenith_angle.csv',[results[k] for k in sorted(results)])
        save('checkpoint.json',dict(status='RUNNING',completed_angles=sorted(results),last_stage=stage,
                                   candidate_evaluations=len(all_candidates)))
        print('ANGLE',deg,'K',uniform['K_raw'],mb_fixed['K_raw'],mb_opt['K_raw'],
              'SOURCES',uniform['VA'],mb_opt['nu_raw'],mb_opt['VA'],flush=True)

    for deg in range(0,61,2):
        sweep_angle(deg,'initial_2deg')
    refinement_angles = set()
    for key in ('Uniform_K_raw','Fixed_MB_K_raw','Optimized_MB_K_raw'):
        for left,right in zip(range(0,60,2),range(2,61,2)):
            if results[left][key] > 0 and results[right][key] <= 0:
                refinement_angles.update(left+.25*j for j in range(1,8))
    for deg in sorted(refinement_angles):
        sweep_angle(deg,'transition_0p25deg')
    rows = [results[k] for k in sorted(results)]
    operations = []
    for scheme,key in zip(SCHEMES,('Uniform_K_raw','Fixed_MB_K_raw','Optimized_MB_K_raw')):
        positive = [r for r in rows if r[key] > 0]
        nonpositive = [r for r in rows if r[key] <= 0]
        brackets = [(l,r) for l,r in zip(rows,rows[1:]) if l[key] > 0 and r[key] <= 0]
        last = brackets[-1] if brackets else None
        if not positive:
            status = 'NO_POSITIVE_SKR_FOUND_IN_TESTED_INTERVAL'
        elif rows[-1][key] > 0:
            status = 'POSITIVE_THROUGH_SWEEP_BOUNDARY_NOT_TRUE_MAXIMUM'
        else:
            status = 'DIRECTLY_EVALUATED_POSITIVE_TO_NONPOSITIVE_BRACKET'
        operations.append(dict(scheme=scheme,status=status,
            maximum_tested_positive_deg=positive[-1]['zenith_deg'] if positive else None,
            first_tested_nonpositive_deg=nonpositive[0]['zenith_deg'] if nonpositive else None,
            operational_lower_deg=last[0]['zenith_deg'] if last else None,
            operational_upper_deg=last[1]['zenith_deg'] if last else None,
            distance_lower_km=last[0]['distance_km'] if last else None,
            distance_upper_km=last[1]['distance_km'] if last else None,
            K_lower=last[0][key] if last else None,K_upper=last[1][key] if last else None,
            positive_count=len(positive),nonpositive_count=len(nonpositive),
            all_positive_to_nonpositive_brackets=json.dumps([[l['zenith_deg'],r['zenith_deg']] for l,r in brackets])))
        for l,r in brackets:
            check('operational_bracket:'+scheme,r['zenith_deg']-l['zenith_deg'] <= .25)
    changes = []
    for scheme,fields in (('Optimized Uniform',('Uniform_optimal_VA',)),
                          ('Optimized MB',('MB_optimal_nu_raw','MB_optimal_VA'))):
        for left,right in zip(rows,rows[1:]):
            if any(left[k] != right[k] for k in fields):
                changes.append(dict(scheme=scheme,previous_tested_deg=left['zenith_deg'],
                    first_tested_new_parameters_deg=right['zenith_deg'],
                    previous_parameters=json.dumps({k:left[k] for k in fields}),
                    new_parameters=json.dumps({k:right[k] for k in fields})))
    check('reference_Uniform_reranked_over_expanded_catalog',results[30]['Uniform_optimal_VA'] == .0475)
    check('channel_recomputed_and_angle_dependent',len(channels) == len(rows)
          and len({c['eta_atm'] for c in channels.values()}) == len(rows)
          and len({c['sigma_R2'] for c in channels.values()}) == len(rows))
    write_csv('skr_vs_zenith_angle_detailed.csv',sorted(details,key=lambda r:(r['zenith_deg'],SCHEMES.index(r['scheme']))))
    write_csv('initial_31_points.csv',[r for r in rows if r['grid_stage'] == 'initial_2deg'])
    write_csv('operational_zenith_angles.csv',operations)
    write_csv('source_parameter_changes.csv',changes)
    write_csv('MI_convergence.csv',convergences)
    write_csv('direct_mixture_controls.csv',direct_controls)
    write_csv('channel_closed_vs_quadrature.csv',integral_controls)
    save('channel_by_angle.json',channels)
    save('selected_high_precision_models.json',high_models)
    save('checks.json',CHECKS)
    plot(rows)
    summary = dict(status='CURRENTLY_VERIFIED_PASS',scope='BEST_CURRENT_EXACT_TESTED_CANDIDATE_ONLY',
        security_status='UNVALIDATED_SECURITY_MODEL',lifecycle='NOT_READY_FOR_PUBLICATION_SCALE_RUNS',
        initial_angles=31,refined_angles=len(refinement_angles),total_angles=len(rows),
        candidate_count=len(candidates),candidate_evaluations=len(all_candidates),checks=len(CHECKS),
        GH_maximum_difference=max(r['GH_max_difference'] for r in all_candidates),
        spectrum_maximum_difference=max(r['matrix_spectrum_max_difference'] for r in all_candidates),
        minimum_uncertainty_eigenvalue=min(r['uncertainty_min_eigenvalue'] for r in all_candidates),
        at_0=results[0],at_30=results[30],at_60=results[60],operations=operations,source_changes=changes,
        Uniform_positive_angles=[r['zenith_deg'] for r in rows if r['Uniform_K_raw'] > 0],
        MB_improvement_max_absolute=max(rows,key=lambda r:r['MB_improvement_absolute']),
        MB_improvement_max_percent_where_fixed_positive=max((r for r in rows if r['Fixed_MB_K_raw'] > 0),
                                                           key=lambda r:r['MB_improvement_percent']),
        frozen_hash_conflict_preserved=True,source_moments_recomputed=False,
        continuous_global_optimum_certified=False,producer_sha256=sha(Path(__file__)))
    save('summary.json',summary)
    save('checkpoint.json',dict(status='COMPLETE',completed_angles=sorted(results),
                               candidate_evaluations=len(all_candidates),next_action='DELIVER_THEN_STOP'))
    print('COMPLETE',summary['total_angles'],'angles',summary['candidate_evaluations'],'evaluations',flush=True)


if __name__ == '__main__':
    main()
