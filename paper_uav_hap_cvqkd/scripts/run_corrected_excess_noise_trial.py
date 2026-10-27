"""Two fixed exact sources; isolated excess-noise trial, never a security certificate."""
from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys

import mpmath as mp
import numpy as np
from scipy.integrate import quad
from scipy.special import log_ndtr
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.recheck_manuscript_homodyne_noise import M, mi_gh, security
from scripts.run_manuscript_literal_3moments import verified_candidate
from scripts.run_theta10_D55_unconstrained_three_scheme import unconstrained_config
from scripts.run_skr_vs_link_distance_theta10urad import evaluate_candidate
from src.cvqkd.mutual_information import deterministic_mutual_information

OUT = ROOT / 'results/corrected_excess_noise_trial_20261022'
CHECKS = []
mp.mp.dps = 110
ECH, EDET, ETADET, BETA = map(M, ('.0186', '.0135', '.8', '.95'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def rows(path):
    with path.open(encoding='utf-8', newline='') as stream:
        return list(csv.DictReader(stream))


def clean(x):
    if isinstance(x, mp.mpf):
        return mp.nstr(x, 75)
    if isinstance(x, dict):
        return {k: clean(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [clean(v) for v in x]
    return x


def save(name, value):
    (OUT / name).write_text(json.dumps(clean(value), indent=2, allow_nan=False) + '\n', encoding='utf-8')


def check(name, ok, detail=None):
    CHECKS.append(dict(name=name, status='CURRENTLY_VERIFIED_PASS' if bool(ok) else 'FAILED', detail=clean(detail)))
    if not ok:
        save('failed_check.json', CHECKS[-1])
        raise AssertionError(name)


def law(ch):
    """The zero-boresight power-pointing/lognormal law; NOT a renormalization."""
    b, d, v, p0, p1 = [M(ch[k]) for k in ('B', 'chi2', 'sigma_R2', 'P0', 'P1')]
    c1 = mp.exp(v*d*(1+d)/2)
    c3, mu = 1/mp.sqrt(2*v), v*(1+2*d)/2
    x1 = -mp.log(b)+mu
    def Q(a):
        return (mp.exp(a*x1-a*mu)*mp.erfc(c3*x1)
                +mp.exp(a*a/(4*c3*c3)-a*mu)*mp.erfc(a/(2*c3)-c3*x1))/2
    def moment(q):
        return p1*b**q*d*c1/(d+q)*Q(d+q)
    def density_y(y):
        return math.exp(float(mp.log(p1*d*c1/2)-d*mp.log(b))+float(d)*y
                        +math.log(2)+float(log_ndtr(-math.sqrt(2)*float(c3)*(y-float(mp.log(b))+float(mu)))))
    mass_active = moment(M(0))
    return dict(B=b, d=d, v=v, P0=p0, P1=p1, C1=c1, Q_chi2=Q(d),
                active_mass=mass_active, retained_mass=p0+mass_active,
                truncated_m1=moment(M(1)), truncated_mhalf=moment(M('.5'))), density_y


def covariance(va, mh, t, noise, C, w, receiver):
    a, b = 1+va, 1+t*va+noise
    z = 2*mh*C-mp.sqrt(2*noise*w)
    delta, determinant = a*a+b*b-2*z*z, (a*b-z*z)**2
    discriminant = delta**2-4*determinant
    check('spectrum_discriminant_'+receiver, discriminant >= 0)
    root = mp.sqrt(discriminant)
    nu1, nu2 = mp.sqrt((delta+root)/2), mp.sqrt((delta-root)/2)
    nu3 = mp.sqrt(a*(a-z*z/b)) if receiver == 'homodyne' else a-z*z/(b+1)
    check('symplectic_physicality_'+receiver, min(nu1, nu2, nu3) >= 1)
    def g(nu):
        x = (nu-1)/2
        return ((x+1)*mp.log1p(x)-x*mp.log(x))/mp.log(2) if x else M(0)
    chi = g(nu1)+g(nu2)-g(nu3)
    matrix = np.array([[float(a),0,float(z),0],[0,float(a),0,-float(z)],
                       [float(z),0,float(b),0],[0,-float(z),0,float(b)]])
    omega = np.kron(np.eye(2), [[0.,1.],[-1.,0.]])
    spectrum = np.sort(abs(np.linalg.eigvals(1j*omega@matrix)))[::2]
    check('independent_matrix_spectrum_'+receiver,
          np.max(abs(spectrum-np.sort([float(nu1), float(nu2)]))) < 1e-11)
    uncertainty = float(np.linalg.eigvalsh(matrix+1j*omega).min())
    check('uncertainty_'+receiver, uncertainty >= -1e-12)
    check('nonnegative_Holevo_'+receiver, chi >= 0)
    return dict(a=a,b=b,Z_minus=z,Gamma_AB=matrix.tolist(),nu_1=nu1,nu_2=nu2,nu_3=nu3,
                chi_BE=chi,uncertainty_minimum_eigenvalue=uncertainty)


def measurement(candidate, t, noise, receiver, order):
    if receiver == 'homodyne':
        p, alpha = [x.detach().numpy()[0] for x in
                    (candidate['ensemble'].probabilities, candidate['ensemble'].amplitudes)]
        levels, index = np.unique(alpha.real, return_inverse=True)
        marginal = np.bincount(index, weights=p)
        return mi_gh(marginal, levels.astype(complex), float(t), float(noise), order, dimension=1)
    return float(deterministic_mutual_information(candidate['ensemble'],
                 torch.tensor([float(t)], dtype=torch.float64),
                 torch.tensor([float(noise/t)], dtype=torch.float64),
                 quadrature_order=order, implementation='product')[0])


def main():
    if OUT.exists():
        raise FileExistsError('Separate trial output already exists; preserve it')
    OUT.mkdir()
    mp.mp.dps = 110
    tracked = subprocess.check_output(['git','ls-files','-z','paper_uav_hap_cvqkd'], cwd=ROOT.parent).decode().split('\0')
    protected = {p: sha(ROOT.parent/p) for p in tracked if p and (ROOT.parent/p).is_file()}
    save('startup_manifest.json', dict(branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT).decode().strip(),
         HEAD=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip(),
         status=subprocess.check_output(['git','status','--short'],cwd=ROOT).decode(),protected=protected,
         user_request_sha256=sha(Path('C:/Users/HP/.codex/attachments/ead53cdc-d6fc-4b9b-becb-504df07dfd26/Pasted text.txt'))))
    config = unconstrained_config()
    zenith = ROOT/'results/skr_vs_zenith_angle_20261019'
    protocol = read(ROOT/'results/zenith_angle_root_cause_diagnostic_20261021/protocol.json')
    saved_ch = read(zenith/'channel_by_angle.json')['30']
    oldrows = rows(ROOT/'results/theta10_D55_alt_opt/ao_objective_evaluations.csv')
    oldref = next(r for r in oldrows if float(r['V_A'])==5.5 and float(r['nu_raw'])==.165)
    ref = next(r for r in rows(ROOT/'results/skr_vs_distance_theta10urad_D55cm_unconstrained_three_scheme/channel_by_distance.csv')
               if float(r['distance_km']) == 21.9393102292)
    # Historical raw-law moments are preserved even when they fail the requested [0,1] law.
    ref_ch = dict(B=M(ref['A0'])*M(ref['eta_atm']), chi2=M(ref['chi'])**2,
                  sigma_R2=4*M(ref['sigma_X2']), P0=ref['p_out'], P1=ref['p_in'])
    configurations = [('manuscript_8cm_233urad_30deg', saved_ch, protocol['fixed_MB']['source_path'],
                       M(saved_ch['mean_eta']), M(saved_ch['mean_sqrt_eta']), 'homodyne', M(saved_ch['L_m'])/1000),
                      ('reference_55cm_10urad', ref_ch, oldref['source_path'],
                       M(ref['mean_T_raw']), M(ref['mean_sqrt_T_raw']), 'heterodyne', M(ref['distance_km']))]
    results, audits, history, convergence = [], [], [], []
    for name, ch, source_path, m1, mh, receiver, length in configurations:
        print('Evaluating', name, flush=True)
        source = ROOT/source_path
        candidate = verified_candidate(source, config)
        payload = read(source)
        check(name+'_exact_source_available', candidate is not None and payload['support_size']==256)
        va, C, w = map(M, (candidate['V_A'], candidate['C'], candidate['w']))
        p, alpha = [x.detach().numpy()[0] for x in
                    (candidate['ensemble'].probabilities,candidate['ensemble'].amplitudes)]
        check(name+'_energy', abs(2*np.dot(p,abs(alpha)**2)-float(va))<2e-12)
        check(name+'_PMF', min(p)>0 and abs(p.sum()-1)<1e-14)
        check(name+'_fading_variance', m1 >= mh*mh)
        pdf, density = law(ch)
        integrals = {}
        for power in (0,.5,1):
            value,error = quad(lambda y: math.exp(power*y)*density(y),-math.inf,0,
                               epsabs=2e-15,epsrel=2e-13,limit=400)
            target = pdf['active_mass'] if power==0 else pdf['truncated_mhalf' if power==.5 else 'truncated_m1']
            check(name+'_PDF_quadrature_'+str(power), abs(value-float(target))<2e-13)
            integrals[str(power)] = dict(value=value,error=error,closed=target)
        matches = abs(m1-pdf['truncated_m1'])<M('2e-13') and abs(mh-pdf['truncated_mhalf'])<M('2e-13')
        normalized = abs(pdf['retained_mass']-1)<M('1e-10')
        audits.append(dict(configuration=name, **pdf, direct_integrals=integrals,
                           saved_moments_match_retained_law=bool(matches),normalized_within_1e_10=bool(normalized),
                           saved_m1_minus_truncated=m1-pdf['truncated_m1'],
                           saved_mhalf_minus_truncated=mh-pdf['truncated_mhalf'],
                           source_path=source_path,source_sha256=sha(source),C=C,w=w,
                           ensemble_hash=candidate['ensemble_hash'], source_verification='CURRENTLY_VERIFIED_PASS'))
        if receiver=='homodyne':
            sec = security(m1,mh,va,C,w)
            i1 = measurement(candidate,mh*mh,sec['eta_f_xi_f'],receiver,64)
            old = dict(I_AB=2*i1,beta_I_AB=.95*2*i1,chi_BE=sec['chi_BE'],SKR=M(.95)*M(2*i1)-sec['chi_BE'])
            # The 2D integral identity is verified directly for this exact product PMF.
            direct2 = mi_gh(p,alpha,float(mh*mh),float(sec['eta_f_xi_f']),16,dimension=2)
            check(name+'_historical_2D_replay', abs(direct2-2*i1)<2e-13)
            old.update(receiver_protocol='MIXED_2D_MI_HOMODYNE_HOLEVO',eta_det=1,epsilon_det=0)
        else:
            channel = {**ref,'theta_div_full_rad':1e-5}
            channel = {k:(float(v) if k in ('T_eff','distance_km','zeta_deg','w0_m','receiver_diameter_m') else v) for k,v in channel.items()}
            old = evaluate_candidate(candidate,channel,config)
            check(name+'_historical_SKR_replay',abs(old['SKR']-float(oldref['SKR']))<1e-12)
            old.update(receiver_protocol='heterodyne',eta_det=1,epsilon_det=0)
        history.append(dict(configuration=name,scope='ACTUAL_UNCHANGED_HISTORICAL_CODE_REPLAY_NOT_MATCHED_DETECTOR_COMPARISON',**clean(old)))
        for interpretation,mass in [('boxed_limit_at_zero',pdf['retained_mass']),('active_only_unconditioned',pdf['active_mass'])]:
            channel_noise = ECH*m1
            det_noise = EDET/ETADET*mass
            mean_noise = channel_noise+det_noise
            # Direct integration cancels eta analytically before numerical evaluation at zero.
            integral,error=quad(lambda y:(float(ECH)*math.exp(y)+float(EDET/ETADET))*density(y),
                                -math.inf,0,epsabs=2e-15,epsrel=2e-13,limit=400)
            if interpretation=='boxed_limit_at_zero':
                integral += float(EDET/ETADET*pdf['P0'])
            target = ECH*pdf['truncated_m1']+det_noise
            check(name+'_'+interpretation+'_noise_integral',abs(integral-float(target))<2e-13)
            if matches:
                check(name+'_'+interpretation+'_fixed_moment_noise_integral',abs(integral-float(mean_noise))<2e-13)
            check(name+'_'+interpretation+'_zero_detector_limit',0/ETADET*mass==0)
            fading = (m1-mh*mh)*va
            pre_noise, t = fading+mean_noise, ETADET*mh*mh
            post_noise = ETADET*pre_noise
            cv = covariance(va,mp.sqrt(ETADET)*mh,t,post_noise,C,w,receiver)
            check(name+'_'+interpretation+'_loss_applied_once',abs(cv['b']-(1+ETADET*(m1*va+mean_noise)))<M('1e-95'))
            # Independent historical total-noise -> excess conversion, with detector-output
            # excess EDET defined explicitly; no identification with electronic v_el.
            historical_total_moment = (ECH-1)*m1+(1+(1-ETADET+EDET)/ETADET)*mass
            vacuum_moment = mass/ETADET-m1
            converted_historical = historical_total_moment-vacuum_moment
            check(name+'_'+interpretation+'_matched_total_to_excess',abs(converted_historical-mean_noise)<M('1e-95'))
            orders=(16,32,64) if receiver=='homodyne' else (8,16,32,64)
            values = [measurement(candidate,t,post_noise,receiver,order) for order in orders]
            for order,value in zip(orders,values):
                convergence.append(dict(configuration=name,interpretation=interpretation,order=order,I_AB=value,
                                        delta_from_GH64=value-values[-1]))
            check(name+'_'+interpretation+'_GH32_64',abs(values[-2]-values[-1])<2e-13)
            iab = values[-1]
            check(name+'_'+interpretation+'_MI_entropy_bound',0<=iab<=-np.dot(p,np.log2(p)))
            with mp.workdps(80):
                cv80=covariance(va,mp.sqrt(ETADET)*mh,t,post_noise,C,w,receiver)
            check(name+'_'+interpretation+'_entropy_80_110',abs(cv80['chi_BE']-cv['chi_BE'])<M('1e-70'))
            kval = BETA*M(iab)-cv['chi_BE']
            # Re-evaluate the converted historical formula, not merely its printed noise.
            old_cv=covariance(va,mp.sqrt(ETADET)*mh,t,ETADET*(fading+converted_historical),C,w,receiver)
            old_i=measurement(candidate,t,ETADET*(fading+converted_historical),receiver,64)
            old_k=BETA*M(old_i)-old_cv['chi_BE']
            check(name+'_'+interpretation+'_matched_SKR',abs(kval-old_k)<M('1e-70'))
            result=dict(configuration=name,interpretation=interpretation,distance_km=length,receiver_protocol=receiver,
                        detector_security_convention='untrusted loss and excess assigned to Eve; ideal measurement after composition',
                        eta_det=ETADET,epsilon_det=EDET,epsilon_ch=ECH,beta=BETA,V_A=va,nu_raw=candidate['nu_raw'],
                        mean_eta=m1,mean_sqrt_eta=mh,eta_f=mh*mh,eta_f_after_detector=t,
                        fading_excess_output_pre_detector=fading,channel_excess_output_pre_detector=channel_noise,
                        detector_excess_output_pre_detector=det_noise,detector_excess_output_post_detector=ETADET*det_noise,
                        mean_eta_epsilon=mean_noise,eta_f_epsilon_f=pre_noise,epsilon_f=pre_noise/(mh*mh),
                        total_excess_output_post_detector=post_noise,PDF_retained_mass=pdf['retained_mass'],
                        I_AB=iab,beta_I_AB=BETA*M(iab),K_raw=kval,
                        matched_historical_converted_I_AB=old_i,matched_historical_converted_chi_BE=old_cv['chi_BE'],
                        matched_historical_converted_K_raw=old_k,delta_I_AB=iab-old_i,
                        delta_chi_BE=cv['chi_BE']-old_cv['chi_BE'],delta_K=kval-old_k,
                        original_GH_order=64 if receiver=='homodyne' else 8,
                        GH8_vs_GH64=values[0]-values[-1] if receiver=='heterodyne' else None,
                        scope='MATHEMATICAL_DIAGNOSTIC_ONLY',security_valid=False,
                        retained_law_compatible=bool(matches and normalized),**cv)
            results.append(result)
            print(name,interpretation,'I=',iab,'chi=',mp.nstr(cv['chi_BE'],18),'K=',mp.nstr(kval,18),flush=True)
    save('result.json',dict(status='DIAGNOSTIC_COMPLETE_SECURITY_UNVALIDATED',results=results,
         actual_historical_replays=history,PDF_audits=audits,
         blockers=['Frozen historical hash discrepancy retained; current hash matches experiment re-freeze.',
          'Actual historical ideal/mixed or heterodyne kernels are not matched nonideal-detector baselines.',
          'Historical LiteralChannel detector_noise is heterodyne-like and its xi_det is not established as epsilon_det.',
          'Gaussian surrogate MI, direct Z-minus sufficiency, outage security and operational fading protocol unvalidated.',
          'Reference saved raw moments are not silently replaced by [0,1]-truncated moments; see PDF audit.']))
    for name,records in [('comparison.csv',results),('quadrature_convergence.csv',convergence)]:
        flat=[{k:(float(v) if isinstance(v,mp.mpf) else v) for k,v in r.items() if not isinstance(v,(list,dict))} for r in records]
        with (OUT/name).open('w',encoding='utf-8',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(flat[0]));writer.writeheader();writer.writerows(flat)
    save('validation.json',dict(checks=CHECKS,checks_passed=len(CHECKS)))
    check('protected_files_unchanged',all(sha(ROOT.parent/p)==h for p,h in protected.items()))
    save('validation.json',dict(checks=CHECKS,checks_passed=len(CHECKS),protected_files_unchanged=len(protected)))
    save('receipt.json',dict(artifacts={p.name:sha(p) for p in OUT.iterdir() if p.is_file()},
                            producer_sha256=sha(Path(__file__)),no_source_generation=True,no_search=True,no_random_draws=True))
    print('COMPLETE',OUT,flush=True)


if __name__=='__main__':
    main()
