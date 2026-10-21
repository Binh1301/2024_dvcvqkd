"""Bounded diagnosis of saved zenith results; never search or build sources.

Run with the project Python, -B. Historical producers are read-only dependencies.
The only fresh rate calls are fixed-source controls and four accuracy probes.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
import platform
import sys

import mpmath as mp
import numpy as np
import scipy
from scipy.integrate import quad
from scipy.special import log_ndtr

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
OLD = ROOT / 'results/skr_vs_zenith_angle_20261019'
sys.path.insert(0, str(ROOT))
from scripts.exact_cache_provenance import verify_source_payload
from scripts.optimize_uniform_manuscript_2d import uniform_mi_2d
from scripts.recheck_manuscript_homodyne_noise import M, security

CHECKS = []
CALLS = []


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def read(path):
    with path.open(encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def write(name, rows):
    with (OUT / name).open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def check(name, ok, detail=None):
    CHECKS.append(dict(check=name, status='CURRENTLY_VERIFIED_PASS' if ok else 'FAILED', detail=detail))
    if not ok:
        save('validation/failed_check.json', CHECKS[-1])
        raise AssertionError((name, detail))


def ensemble_digest(p, a, va):
    value = dict(schema='exact-common-ensemble-v1',
        probabilities=dict(dtype='torch.float64', shape=[1, 256], data=[float(x).hex() for x in p]),
        amplitudes=dict(dtype='torch.complex128', shape=[1, 256],
                        data=[[float(x.real).hex(), float(x.imag).hex()] for x in a]),
        declared_va=dict(dtype='torch.float64', shape=[1], data=[float(va).hex()]))
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def product_moment(B, d, v, p1, q):
    """Historical zero-boresight law on [0,1], no conditioning/renormalization."""
    a = d + q
    mu = v * (1 + 2*d) / 2
    x1 = -mp.log(B) + mu
    c3 = 1/mp.sqrt(2*v)
    full = p1 * B**q * d/a * mp.exp(v*(q*q-q)/2)
    # Relative upper-tail moment, evaluated directly to avoid 1 - CDF cancellation.
    tail = (mp.erfc(c3*x1-a/(2*c3))
            - mp.exp(a*x1-a*a/(4*c3*c3))*mp.erfc(c3*x1))/2
    return full*(1-tail), tail


def independent_entropy(m1, mh, va, cs, ws, digits):
    """Independent two-mode closed spectrum, using stable sum/difference roots."""
    with mp.workdps(digits):
        t = mh*mh
        noise = (m1-t)*va + M('.0186')*m1
        v, b = 1+va, 1+t*va+noise
        z = 2*mh*cs-mp.sqrt(2*noise*ws)
        root = mp.sqrt((v+b)**2-4*z*z)
        nus = [(root+abs(v-b))/2, (root-abs(v-b))/2, mp.sqrt(v*(v-z*z/b))]
        if min(nus) < 1:
            raise ValueError('Nonphysical independent covariance')
        def g(nu):
            x = (nu-1)/2
            return ((x+1)*mp.log1p(x)-x*mp.log(x))/mp.log(2) if x else M(0)
        ent = list(map(g, nus))
        return ent[0]+ent[1]-ent[2]


def main():
    if (OUT/'diagnostic_results.json').exists():
        raise FileExistsError('Completed diagnostic is immutable')
    mp.mp.dps = 110
    protocol = load(OLD/'protocol.json')
    check('historical_configuration', protocol['catalogs']=={'Uniform':36,'MB':182}
          and protocol['xi_ch']==.0186 and protocol['beta']==.95
          and protocol['R']==1 and protocol['xi_det']==0
          and protocol['optical']['full_divergence_rad']==233e-6
          and not protocol['PDF_renormalized'])
    inputs = dict(load(OLD/'input_manifest.json'))
    receipt = load(OLD/'validation_receipt.json')
    for name, h in receipt['artifact_sha256'].items():
        check('historical_receipt:'+name, sha(ROOT/name)==h)
        inputs[name] = h
    for name, h in inputs.items():
        check('historical_input:'+name, sha(ROOT/name)==h)
    inputs[(OLD/'validation_receipt.json').relative_to(ROOT).as_posix()] = sha(OLD/'validation_receipt.json')
    for name in ['docs/FINAL_MODEL_SPEC.md','docs/security_model_consistency_audit.md']:
        inputs[name] = sha(ROOT/name)

    curves = read(OLD/'skr_vs_zenith_angle.csv')
    detailed = read(OLD/'skr_vs_zenith_angle_detailed.csv')
    candidates = read(OLD/'all_candidate_evaluations.csv')
    channels = load(OLD/'channel_by_angle.json')
    models = load(OLD/'selected_high_precision_models.json')
    roster = read(OLD/'source_roster.csv')
    arrays = np.load(OLD/'verified_ensembles.npz', allow_pickle=False)
    check('complete_saved_grid', [int(x['zenith_deg']) for x in curves]==list(range(0,61,2))
          and len(detailed)==93 and len(candidates)==6758 and len(models)==93)
    check('source_counts', len(roster)==218 and sum(x['family']=='MB' for x in roster)==182)
    by_source = {}
    source_records = []
    settings = None
    for row in roster:
        eh = row['ensemble_hash']
        path = ROOT/row['source_path']
        payload = load(path)
        settings = settings or payload['source_settings']
        verified = verify_source_payload(payload, settings)
        p, a = arrays[eh+'_p'], arrays[eh+'_alpha']
        va, nu = float(row['VA']), float(row['nu_raw'])
        check('source_identity:'+eh, sha(path)==row['source_sha256']
              and payload['ensemble_hash']==eh==ensemble_digest(p,a,va)
              and float.fromhex(payload['V_A_hex'])==va
              and float.fromhex(payload['nu_mb_raw_hex'])==nu
              and float(payload['C'])==float(row['C']) and float(payload['w'])==float(row['w'])
              and payload['support_size']==len(p)==256)
        x, ix = np.unique(a.real, return_inverse=True)
        y, iy = np.unique(a.imag, return_inverse=True)
        px, py = np.bincount(ix, weights=p), np.bincount(iy, weights=p)
        raw = np.arange(16)-7.5
        target = np.exp(-nu*raw**2); target /= target.sum()
        scale = math.sqrt(va/(4*np.dot(target, raw**2)))
        check('source_PMF_energy:'+eh, np.all(p>0) and abs(p.sum()-1)<1e-14
              and abs(2*np.dot(p,abs(a)**2)-va)<2e-12
              and np.max(abs(p-px[ix]*py[iy]))<1e-14
              and max(np.max(abs(px-target)),np.max(abs(py-target)))<2e-14
              and max(np.max(abs(x-scale*raw)),np.max(abs(y-scale*raw)))<2e-13)
        inputs[row['source_path']] = sha(path)
        by_source[eh] = row
        source_records.append(dict(ensemble_hash=eh, family=row['family'], nu_raw=nu, VA=va,
            source_sha256=sha(path), identity_policy=verified['policy'], source_path=row['source_path']))
    write('validation/authenticated_sources.csv',source_records)
    save('input_manifest.json',inputs)

    fixed = next(r for r in roster if r['family']=='MB' and float(r['VA'])==5.475 and float(r['nu_raw'])==.165)
    p,a = arrays[fixed['ensemble_hash']+'_p'], arrays[fixed['ensemble_hash']+'_alpha']
    VA,CS,WS = [M(fixed[k]) for k in ('VA','C','w')]
    BETA = M('.95')
    save('protocol.json',dict(historical_protocol=protocol, reference_angle_deg=30,
         fixed_MB=fixed, controlled_checks=dict(
            A='Fix normalized pointing/scintillation/outage at 30deg; vary B=A0*eta_atm; exact [0,1] truncation.',
            B='Reuse saved fixed MB at all 31 angles; no source switching.',
            C='Nonfading T equals saved mean power transmittance at each angle, physical xi unchanged.',
            attribution='Two-coordinate symmetric finite-difference (Shapley) decomposition of K(Tf,Rf), selected intervals only.',
            D='Reuse all saved convergence; four fixed-source probes, independent 80/110 digit Holevo.'),
         new_source_optimization=False,new_source_moments=False,production_edits=False,
         security_status='UNVALIDATED_SECURITY_MODEL',lifecycle='NOT_READY_FOR_PUBLICATION_SCALE_RUNS',
         frozen_hash_conflict_preserved=True))

    # Reconstruct primitives independently, from the literal historical constants.
    wl,h0,h1 = M('1.55e-6'),M(1000),M(20000)
    wave = 2*mp.pi/wl
    def cn2(h):
        return M('.00594')*(M(21)/27)**2*(M('1e-5')*h)**10*mp.exp(-h/1000) + M('2.7e-16')*mp.exp(-h/1500)+M('1e-14')*mp.exp(-h/100)
    knots = list(map(M,[1000,2000,5000,10000,20000]))
    jry = mp.quad(lambda h:cn2(h)*(h-h0)**(M(5)/6),knots)
    jmu = mp.quad(lambda h:cn2(h)*((h-h0)/(h1-h0))**(M(5)/3),knots)
    physics, moment_rows, noises, factor_rows, geometry_checks, integral_rows = [],[],[],[],[],[]
    channel_numbers = {}
    tail_max = M(0)
    for deg in range(0,61,2):
        ch = {k:M(v) for k,v in channels[str(deg)].items()}
        sec = 1/mp.cos(M(deg)*mp.pi/180)
        length = (h1-h0)*sec
        w0 = 2*wl/(mp.pi*M('233e-6'))
        wL = mp.sqrt(w0*w0+(length*wl/(mp.pi*w0))**2)
        sc = M('2.25')*wave**(M(7)/6)*sec**(M(11)/6)*jry
        gd = M('4.35')*(2*length/(wave*wL*wL))**(M(5)/6)*wave**(M(7)/6)*(h1-h0)**(M(5)/6)*sec**(M(11)/6)*jmu
        weff = wL*mp.sqrt(1+gd)
        ap = mp.sqrt(mp.pi)*M('.08')/(2*mp.sqrt(2)*weff)
        a0 = mp.erf(ap)**2
        weq = weff*mp.sqrt(mp.sqrt(mp.pi)*mp.erf(ap)/(2*ap*mp.exp(-ap*ap)))
        sigs = mp.sqrt(1+(length*M('15.61e-6'))**2)
        atm = M('.92')**sec
        p0 = mp.exp(-M('.00625')**2/(2*M('.0015')**2))
        d = weq**2/(4*sigs**2)
        independent = dict(L_m=length,zeta_rad=M(deg)*mp.pi/180,w0_m=w0,wL_m=wL,G_d=gd,
            w_eff_m=weff,w_eq_m=weq,sigma_s_m=sigs,sigma_R2=sc,eta_atm=atm,A0=a0,
            P0=p0,P1=1-p0,chi2=d,mu2_integral=jmu,rytov_integral=jry)
        for key, value in independent.items():
            residual = value-ch[key]
            check(f'primitive:{deg}:{key}', abs(residual)<M('1e-60')*max(1,abs(value)),float(residual))
            geometry_checks.append(dict(zenith_deg=deg,quantity=key,saved=float(ch[key]),
                independent=float(value),residual=float(residual),origin='RECONSTRUCTED_FROM_HISTORICAL_CONSTANTS'))
        m1,mh = ch['mean_eta'],ch['mean_sqrt_eta']
        t,var = mh*mh,m1-mh*mh
        rf = var/t
        for q,key in [(M(0),'pdf_mass'),(M('.5'),'mean_sqrt_eta'),(M(1),'mean_eta')]:
            value,tail = product_moment(ch['B'],d,sc,ch['P1'],q)
            if q==0:value += ch['P0']
            tail_max = max(tail_max,tail)
            check(f'factorized_moment:{deg}:{q}', abs(value-ch[key])<M('1e-60'),float(value-ch[key]))
        check('bounds:'+str(deg), 0<t<=m1<=ch['P1']<=1 and abs(ch['pdf_mass']-1)<M('1e-25'))
        fp = (d+M('.5'))**2/(d*(d+1))
        fs = mp.exp(sc/4)
        fo = 1/ch['P1']
        check('Rf_product:'+str(deg),abs(1+rf-fp*fs*fo)<M('1e-59'))
        record = dict(zenith_deg=deg,distance_km=float(length/1000),
            **{k:float(ch[k]) for k in ch},sigma_s_squared_m2=float(sigs*sigs),
            sigma_h_squared_m2=1.,angular_jitter_variance_m2=float((length*M('15.61e-6'))**2),
            relative_displacement=float(sigs/weq),lognormal_log_variance=float(sc),
            scintillation_index=float(mp.expm1(sc)),origin='SAVED_CHANNEL_PLUS_ALGEBRA')
        physics.append(record)
        moment_rows.append(dict(zenith_deg=deg,distance_km=float(length/1000),mean_T=float(m1),
            mean_sqrt_T=float(mh),T_eff=float(t),variance_sqrt_T=float(var),R_f=float(rf),
            pdf_mass=float(ch['pdf_mass']),outage_atom=float(ch['P0']),origin='SAVED_MOMENTS_PLUS_ALGEBRA'))
        channel_numbers[deg] = dict(m1=m1,mh=mh,t=t,rf=rf,ch=ch)
        nf,nphysical = var*VA,M('.0186')*m1
        noises.append(dict(zenith_deg=deg,nu_raw=float(fixed['nu_raw']),VA=float(VA),xi_ch=.0186,
            xi_fading=float(rf*VA),xi_physical=float(m1/t*M('.0186')),
            xi_f=float((nf+nphysical)/t),N_fading=float(nf),N_physical=float(nphysical),
            N_total=float(nf+nphysical),fading_fraction_output=float(nf/(nf+nphysical)),
            origin='ALGEBRA_OF_SAVED_MOMENTS_FIXED_MB'))
        factor_rows.append(dict(zenith_deg=deg,pointing_factor=float(fp),scintillation_factor=float(fs),
            outage_factor=float(fo),pointing_R=float(fp-1),scintillation_R=float(fs-1),outage_R=float(fo-1),
            log_pointing=float(mp.log(fp)),log_scintillation=float(mp.log(fs)),log_outage=float(mp.log(fo)),
            log_total=float(mp.log1p(rf)),R_f=float(rf)))
        # Only five bounded independent PDF-integral controls, not a new sweep.
        if deg in (0,24,30,48,60):
            df,b,c1,c3,mu,p1 = [float(ch[k]) for k in ('chi2','B','C1','C3','mu','P1')]
            for q,key in [(0,'pdf_mass'),(.5,'mean_sqrt_eta'),(1,'mean_eta')]:
                def integrand(y):
                    return math.exp(math.log(p1*df*c1)-df*math.log(b)+(df+q)*y
                                     +float(log_ndtr(-math.sqrt(2)*c3*(y-math.log(b)+mu))))
                v,err = quad(integrand,-math.inf,0,epsabs=2e-15,epsrel=2e-13,limit=400)
                if q==0:v += float(ch['P0'])
                delta = v-float(ch[key])
                check(f'PDF_quadrature:{deg}:{key}',abs(delta)<2e-13,delta)
                integral_rows.append(dict(zenith_deg=deg,quantity=key,stored=float(ch[key]),
                    independent_quad=v,residual=delta,quad_error_estimate=err))
    write('channel_parameters.csv',physics)
    write('channel_moments.csv',moment_rows)
    write('noise_decomposition.csv',noises)
    write('fading_factor_decomposition.csv',factor_rows)
    write('validation/geometry_reconstruction.csv',geometry_checks)
    write('validation/independent_pdf_integrals.csv',integral_rows)

    decomp = []
    worst_arithmetic,worst_gh = 0.,0.
    for row in detailed:
        deg = int(row['zenith_deg'])
        ch = channel_numbers[deg]
        i,b,h,k = [float(row[x]) for x in ('I_AB_2D','beta_I_AB','chi_BE','K_raw')]
        residual = .95*i-h-k
        worst_arithmetic = max(worst_arithmetic,abs(residual))
        check(f'K_reconstruction:{deg}:{row["scheme"]}',abs(residual)<1e-17,residual)
        check(f'selected_source:{deg}:{row["scheme"]}', row['ensemble_hash'] in by_source
              and all(row[f]==by_source[row['ensemble_hash']][f] for f in ('VA','nu_raw','C','w')))
        raw = dict(row)
        raw.update(mean_T=float(ch['m1']),mean_sqrt_T=float(ch['mh']),R_f=float(ch['rf']),
            K_reconstruction_residual=residual,
            subtraction_condition_number=(abs(b)+abs(h))/abs(k) if k else '',
            origin='SAVED_SELECTED_RESULTS_PLUS_ALGEBRA')
        decomp.append(raw)
        worst_gh = max(worst_gh,float(row['GH_max_difference']))
    write('skr_decomposition.csv',decomp)
    check('all_6758_saved_candidates',len(candidates)==31*218)
    for row in candidates:
        deg = int(row['zenith_deg'])
        eh = row['ensemble_hash']
        s = by_source[eh]
        ch = channel_numbers[deg]
        noise = (ch['m1']-ch['t'])*M(row['VA'])+M('.0186')*ch['m1']
        check(f'candidate:{deg}:{eh}',
            all(row[f]==s[f] for f in ('VA','nu_raw','C','w','source_sha256'))
            and abs(.95*float(row['I_AB_2D'])-float(row['chi_BE'])-float(row['K_raw']))<1e-17
            and abs(float(noise)-float(row['N']))<1e-18
            and abs(float(ch['t'])-float(row['eta_f']))<1e-18
            and max(abs(float(row['MI_GH'+str(o)])-float(row['MI_GH64'])) for o in (16,32,64))<2e-13
            and min(float(row[f]) for f in ('nu_1','nu_2','nu_3'))>=1
            and float(row['uncertainty_min_eigenvalue'])>0)
    fixed_rows = [r for r in detailed if r['scheme']=='Fixed MB']
    fixed_rows.sort(key=lambda r:int(r['zenith_deg']))
    adjacent = []
    for aa,bb in zip(fixed_rows,fixed_rows[1:]):
        da,db = int(aa['zenith_deg']),int(bb['zenith_deg'])
        di = float(bb['beta_I_AB'])-float(aa['beta_I_AB'])
        dh = float(bb['chi_BE'])-float(aa['chi_BE'])
        dk = float(bb['K_raw'])-float(aa['K_raw'])
        check(f'adjacent_difference:{da}:{db}',abs(dk-(di-dh))<1e-17)
        adjacent.append(dict(from_deg=da,to_deg=db,delta_beta_I_AB=di,delta_chi_BE=dh,delta_K=dk,
            gain_from_Holevo_reduction=-dh,loss_from_MI_reduction=-di,
            dominant='HOLEVO_REDUCTION' if dk>0 else 'MI_REDUCTION'))
    write('adjacent_skr_differences.csv',adjacent)
    optimization = []
    for row in curves:
        deg = int(row['zenith_deg'])
        group = [r for r in candidates if int(r['zenith_deg'])==deg]
        uniform = max((r for r in group if r['family']=='Uniform'),key=lambda r:float(r['K_raw']))
        mb = max((r for r in group if r['family']=='MB'),key=lambda r:float(r['K_raw']))
        fr = next(r for r in group if r['ensemble_hash']==fixed['ensemble_hash'])
        check('saved_argmax:'+str(deg),float(row['Uniform_K_raw'])==float(uniform['K_raw'])
              and float(row['Optimized_MB_K_raw'])==float(mb['K_raw'])
              and float(row['Fixed_MB_K_raw'])==float(fr['K_raw']))
        optimization.append(dict(zenith_deg=deg,distance_km=float(row['distance_km']),
            Uniform_K_raw=float(uniform['K_raw']),Uniform_nu_raw=0.,Uniform_VA=float(uniform['VA']),
            Fixed_MB_K_raw=float(fr['K_raw']),Fixed_MB_nu_raw=.165,Fixed_MB_VA=5.475,
            Optimized_MB_K_raw=float(mb['K_raw']),Optimized_MB_nu_raw=float(mb['nu_raw']),
            Optimized_MB_VA=float(mb['VA']),optimization_gain=float(mb['K_raw'])-float(fr['K_raw']),
            origin='SAVED_CURVES_MAXIMA_VERIFIED_NO_NEW_SEARCH'))
    write('diagnostic_summary.csv',optimization)
    write('source_optimization_effect.csv',optimization)

    def fixed_rate(m1,mh,label,angle,orders=(32,64)):
        model = security(m1,mh,VA,CS,WS)
        # sqrt(m1)**2 can round one arithmetic ulp above m1 in the exact nonfading fixture.
        boundary_roundoff = 4*mp.eps*max(m1,mh*mh)
        check(f'controlled_physical:{label}:{angle}', model['physical'] and 0<mh*mh<=1
              and m1<=1 and mh*mh-m1<=boundary_roundoff,
              dict(squared_sqrt_residual=mp.nstr(mh*mh-m1,15),arithmetic_roundoff=mp.nstr(boundary_roundoff,15)))
        mi = [uniform_mi_2d(p,a,float(model['eta_f']),float(model['eta_f_xi_f']),o) for o in orders]
        gh = max(abs(v-mi[-1]) for v in mi)
        check(f'controlled_GH:{label}:{angle}',gh<2e-13,gh)
        kval = BETA*M(mi[-1])-model['chi_BE']
        record = dict(check=label,zenith_deg=angle,mean_T=float(m1),T_eff=float(mh*mh),
            R_f=float(m1/(mh*mh)-1),I_AB_2D=mi[-1],beta_I_AB=float(BETA*M(mi[-1])),
            chi_BE=float(model['chi_BE']),K_raw=float(kval),xi_f=float(model['xi_f']),
            N=float(model['eta_f_xi_f']),GH_delta=gh,origin='NEW_FIXED_SOURCE_NUMERICAL_CONTROL')
        CALLS.append(record)
        return float(kval)

    controls = []
    ref = channel_numbers[30]['ch']
    for deg,ch in channel_numbers.items():
        # Freeze distribution shape, retain exact absolute [0,1] law at new B.
        mean,_ = product_moment(ch['ch']['B'],ref['chi2'],ref['sigma_R2'],ref['P1'],M(1))
        half,_ = product_moment(ch['ch']['B'],ref['chi2'],ref['sigma_R2'],ref['P1'],M('.5'))
        fixed_rate(mean,half,'A_frozen_normalized_fading_at_30deg',deg)
        controls.append(CALLS[-1])
        fixed_rate(ch['m1'],mp.sqrt(ch['m1']),'C_deterministic_matched_mean_T',deg)
        controls.append(CALLS[-1])
    write('controlled_diagnostics.csv',controls)

    precision = []
    for deg in (0,24,48,60):
        ch = channel_numbers[deg]
        row = next(r for r in fixed_rows if int(r['zenith_deg'])==deg)
        fresh = fixed_rate(ch['m1'],ch['mh'],'D_fixed_source_accuracy_probe',deg,(16,32,64))
        hp = next(r['model'] for r in models if r['scheme']=='Fixed MB' and r['zenith_deg']==deg)
        entropy80 = independent_entropy(ch['m1'],ch['mh'],VA,CS,WS,80)
        entropy110 = independent_entropy(ch['m1'],ch['mh'],VA,CS,WS,110)
        delta = entropy110-M(hp['chi_BE'])
        check('entropy_precision:'+str(deg),abs(entropy80-entropy110)<M('1e-72') and abs(delta)<M('1e-60'))
        check('fixed_K_replay:'+str(deg),abs(fresh-float(row['K_raw']))<2e-13)
        precision.append(dict(zenith_deg=deg,saved_K=float(row['K_raw']),fresh_K=fresh,
            K_delta=fresh-float(row['K_raw']),entropy80_vs110=mp.nstr(entropy80-entropy110,12),
            independent_vs_saved_entropy=mp.nstr(delta,12),GH_delta=CALLS[-1]['GH_delta']))
    write('validation/precision_probes.csv',precision)
    attribution = []
    for da,db in [(24,48),(46,48),(48,50),(48,56),(56,60),(48,60)]:
        ca,cb = channel_numbers[da],channel_numbers[db]
        ka = float(next(r['K_raw'] for r in fixed_rows if int(r['zenith_deg'])==da))
        kb = float(next(r['K_raw'] for r in fixed_rows if int(r['zenith_deg'])==db))
        kba = fixed_rate(cb['t']*(1+ca['rf']),mp.sqrt(cb['t']),f'attribution_T{db}_R{da}',db)
        kab = fixed_rate(ca['t']*(1+cb['rf']),mp.sqrt(ca['t']),f'attribution_T{da}_R{db}',da)
        dt = ((kba-ka)+(kb-kab))/2
        dr = ((kab-ka)+(kb-kba))/2
        check(f'attribution_sum:{da}:{db}',abs(dt+dr-(kb-ka))<1e-17)
        attribution.append(dict(from_deg=da,to_deg=db,delta_K=kb-ka,
            contribution_Teff_at_fixed_Rf=dt,contribution_Rf_at_fixed_Teff=dr,
            K_Tb_Ra=kba,K_Ta_Rb=kab,
            convention='SYMMETRIC_TWO_ORDER_COORDINATE_DECOMPOSITION_NOT_PHYSICAL_INTERVENTION'))
    write('coordinate_attribution.csv',attribution)
    write('validation/new_fixed_source_calls.csv',CALLS)

    representative = []
    for deg in (0,20,24,30,40,48,52,60):
        m = next(r for r in moment_rows if r['zenith_deg']==deg)
        n = next(r for r in noises if r['zenith_deg']==deg)
        s = next(r for r in decomp if r['scheme']=='Fixed MB' and int(r['zenith_deg'])==deg)
        representative.append(dict(zenith_deg=deg,distance_km=m['distance_km'],mean_T=m['mean_T'],
            T_eff=m['T_eff'],xi_fading=n['xi_fading'],xi_f=n['xi_f'],beta_I_AB=s['beta_I_AB'],
            chi_BE=s['chi_BE'],K_raw=s['K_raw']))
    write('representative_angles.csv',representative)
    peaks = []
    for scheme,key in [('Optimized Uniform','Uniform_K_raw'),('Fixed MB','Fixed_MB_K_raw'),('Optimized MB','Optimized_MB_K_raw')]:
        best = max(optimization,key=lambda r:r[key])
        peaks.append(dict(scheme=scheme,zenith_deg=best['zenith_deg'],K_raw=best[key],
            positive_angles=[r['zenith_deg'] for r in optimization if r[key]>0]))
    old_gh = max(abs(float(r['difference_from_GH64'])) for r in read(OLD/'MI_convergence.csv'))
    old_direct = max(abs(float(r['residual'])) for r in read(OLD/'direct_mixture_controls.csv'))
    old_quad = max(abs(float(r['residual'])) for r in read(OLD/'channel_closed_vs_quadrature.csv'))
    save('diagnostic_results.json',dict(status='CURRENTLY_VERIFIED_PASS',scope='NUMERICAL_ROOT_CAUSE_ONLY',
        peaks=peaks,Rf_min_angle=min(moment_rows,key=lambda r:r['R_f'])['zenith_deg'],
        fixed_xi_min_angle=min(noises,key=lambda r:r['xi_f'])['zenith_deg'],
        K_reconstruction_max_residual=worst_arithmetic,selected_GH_max_delta=worst_gh,
        saved_selected_MI_convergence_max=old_gh,saved_direct_mixture_max_delta=old_direct,
        saved_moment_quadrature_max_delta=old_quad,
        max_relative_upper_tail_moment=mp.nstr(tail_max,15),
        new_rate_calls=len(CALLS),new_source_search_calls=0,new_Cw_calls=0,
        environment=dict(python=sys.version,platform=platform.platform(),numpy=np.__version__,
            scipy=scipy.__version__,mpmath=mp.__version__),
        security_status='UNVALIDATED_SECURITY_MODEL',lifecycle='NOT_READY_FOR_PUBLICATION_SCALE_RUNS'))
    save('validation/numerical_checks.json',dict(status='CURRENTLY_VERIFIED_PASS',count=len(CHECKS),checks=CHECKS))
    print('Numerical diagnostic complete:',len(CHECKS),'checks;',len(CALLS),'bounded fixed-source calls;',peaks)


if __name__=='__main__':
    main()
