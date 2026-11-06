"""Prepare geometry only; SKR evaluation remains blocked by project gates."""
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
PRIOR = ROOT / 'results/skr_vs_zenith_eq14_v43_phaseB_exact_reuse_20261024'
READINESS = ROOT / 'results/skr_vs_zenith_eq14_v43_phaseB_readiness_20261024'


def geometry(x, y, hap_x=1000., hap_y=1000.):
    if not all(math.isfinite(v) for v in (x, y, hap_x, hap_y)):
        raise ValueError('Coordinates must be finite')
    radius = math.hypot(x-hap_x, y-hap_y)
    return math.hypot(19000., radius), math.degrees(math.atan2(radius, 19000.))


def lookup_skr(x, y):
    if not (math.isfinite(x) and math.isfinite(y) and 0 <= x <= 2000 and 0 <= y <= 2000):
        raise ValueError('Position outside [0,2000] x [0,2000] m')
    raise RuntimeError('NOT_RUN: no validated SKR map; interpolation is unavailable')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads((READINESS / 'protocol.json').read_text(encoding='utf-8'))
    readiness = json.loads((READINESS / 'readiness.json').read_text(encoding='utf-8'))
    with (PRIOR / 'diagnostic_selected_schemes.csv').open(encoding='utf-8', newline='') as f:
        rows = list(csv.DictReader(f))
    selected = [r for r in rows if r['scheme'] == 'Optimized MB-shaped 256-QAM'
                and r['zenith_deg'] in ('0', '30')]
    if len(selected) != 2 or readiness['phase_B_ready'] is not False:
        raise ValueError('Unexpected benchmark or gate state; reassess before proceeding')
    p = protocol['physical']
    expected = (p['h_hap_km'], p['h_uav_km'], p['Dr_m'], p['wavelength_m'],
                p['divergence_full_urad'], p['jitter_urad'], p['sigma_h_m'],
                protocol['xi_ch'], protocol['xi_det'], protocol['beta'])
    if expected != (20., 1., .3, 1.55e-6, 35., 1.561, .1, .0186, .005, .95):
        raise ValueError('Receiver-30 protocol mismatch')
    x = np.arange(51, dtype=float)*40.
    X, Y = np.meshgrid(x, x, indexing='xy')
    radial = np.hypot(X-1000., Y-1000.)
    L = np.hypot(19000., radial)
    angle = np.degrees(np.arctan2(radial, 19000.))
    missing = np.full_like(X, np.nan)
    with (OUT/'geometry_only.csv').open('x', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['x_m', 'y_m', 'distance_m', 'zenith_deg', 'transmittance',
                         'received_power', 'nu_opt', 'VA_opt', 'IAB_opt', 'chiBE_opt',
                         'K_raw_opt_bits_per_use', 'K_potential_bits_per_use', 'numerical_status'])
        for i in range(51):
            for j in range(51):
                writer.writerow([X[i,j], Y[i,j], L[i,j], angle[i,j], *(['']*8), 'NOT_RUN'])
    target = OUT/'geometry_only.npz'
    with target.open('xb') as f:
        np.savez_compressed(f, x_m=X, y_m=Y, distance_m=L, zenith_deg=angle,
                            transmittance=missing, received_power=missing, nu_opt=missing,
                            VA_opt=missing, IAB_opt=missing, chiBE_opt=missing,
                            K_raw_opt_bits_per_use=missing, K_potential_bits_per_use=missing,
                            numerical_status=np.full(X.shape, 'NOT_RUN'))
    w0 = 2*p['wavelength_m']/(math.pi*p['divergence_full_urad']*1e-6)
    wL = w0*math.sqrt(1+(19000*p['wavelength_m']/(math.pi*w0*w0))**2)
    benchmarks = [{k: r[k] for k in ('zenith_deg', 'nu_raw', 'VA', 'I_AB', 'beta_I_AB',
                                      'chi_BE', 'K_raw', 'source_evidence_class', 'result_scope')}
                  for r in selected]
    receipt = dict(status='GEOMETRY_ONLY_SKR_NOT_RUN', map_ready=False, phase_B_ready=False,
        grid_shape=[51,51], grid_spacing_m=40., hap_xy_m=[1000.,1000.],
        center_distance_m=L[25,25], center_zenith_deg=angle[25,25],
        max_distance_m=float(L.max()), max_zenith_deg=float(angle.max()),
        w0_m=w0, wL_at_19km_m=wL, physical_configuration=expected,
        historical_benchmarks=benchmarks, benchmark_re_evaluated=False,
        reason=['Phase B not ready and winning source C,w convergence inconclusive',
                'Raw PDF center deficit exceeds strict tolerance',
                'Current scientific optimization/lifecycle authorization unresolved'],
        source_hashes={str(path.relative_to(ROOT)).replace('\\','/'):sha(path) for path in
                       [PRIOR/'diagnostic_selected_schemes.csv',READINESS/'protocol.json',READINESS/'readiness.json',
                        ROOT/'docs/FINAL_MODEL_SPEC.md',ROOT/'results/phaseE2_winning_source_spectral_validation_20261026/source_convergence_status.json']},
        outputs={name:sha(OUT/name) for name in ['geometry_only.csv','geometry_only.npz']},
        SKR_evaluations=0, source_builds=0, rate_maps_generated=False)
    with (OUT/'geometry_receipt.json').open('x', encoding='utf-8') as f:
        json.dump(receipt, f, indent=2, allow_nan=False)
        f.write('\n')
    print(json.dumps({k:receipt[k] for k in ['status','grid_shape','center_distance_m',
                      'max_zenith_deg','w0_m','wL_at_19km_m','SKR_evaluations']}, indent=2))


if __name__ == '__main__':
    main()
