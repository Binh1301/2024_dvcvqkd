"""Independent evidence checks and actual fading-MI probes; no source search."""
import json
import math
from pathlib import Path
import mpmath as mp
import numpy as np
from scipy.integrate import quad
from scipy.stats import ncx2
import model as m
import run as r
from extend_bright import read_csv

OUT=Path(__file__).resolve().parent
CHECKS=[]


def check(name,ok,detail=None):
    CHECKS.append(dict(name=name,status='CURRENTLY_VERIFIED_PASS' if bool(ok) else 'FAILED',detail=detail))
    if not ok:
        r.save('validation_failure.json',CHECKS[-1]);raise AssertionError(name)


def precise_entropy(a,b,z,digits):
    with mp.workdps(digits):
        a,b,z=map(m.M,(a,b,z));root=mp.sqrt((a+b)**2-4*z*z)
        nus=[(root+abs(a-b))/2,(root-abs(a-b))/2,mp.sqrt(a*(a-z*z/b))]
        def g(nu):
            x=(nu-1)/2
            return ((x+1)*mp.log1p(x)-x*mp.log(x))/mp.log(2) if x else m.M(0)
        return dict(nus=nus,chi=g(nus[0])+g(nus[1])-g(nus[2]))


def main():
    if (OUT/'validation.json').exists():raise FileExistsError('Preserve completed validation')
    r.SOURCES=m.load_catalog(r.read(m.ROOT/'configs/manuscript_mobility.json'))
    roster={c['ensemble_hash']:c for c in r.SOURCES}
    selection=r.read(OUT/'selection.json')
    files=['table_B_optical_feasibility.csv','exact_catalog_evaluations.csv','detector_all_exact_evaluations.csv',
           'bright_catalog_evaluations.csv','bright_detector_all_exact.csv','bright_distance_scan.csv',
           'improved_pointing_optical_grid.csv']
    count=0;worst_noise=0.;worst_rate=0.
    for name in files:
        records=read_csv(name);count+=len(records)
        for row in records:
            c=roster[row['ensemble_hash']]
            assert row['C']==c['C'] and row['w']==c['w'] and row['VA']==c['VA'] and row['nu_raw']==c['nu_raw']
            assert row['receiver']=='homodyne_1D' and row['detector_security']=='untrusted' and not row['security_valid']
            assert abs(row['physical_mass']-1)<1e-12 and 0<=row['eta_f']<=row['m1']<=1
            assert row['nu_1']>=1 and row['nu_2']>=1 and row['nu_3']>=1 and row['uncertainty_min_eigenvalue']>=-1e-11
            assert row['Z_lower']<=row['Z_worst']<=row['Z_upper']
            expected=row['eta_det']*((row['m1']-row['eta_f'])*row['VA']+.0186*row['m1'])+row['epsilon_det']
            worst_noise=max(worst_noise,abs(row['N_post']-expected))
            worst_rate=max(worst_rate,abs(row['K_raw']-(.95*row['I_AB']-row['chi_BE'])))
        check('all_rows_'+name,True,{'count':len(records)})
    check('detector_applied_once_all_rows',worst_noise<2e-13,worst_noise)
    check('raw_rate_subtraction_all_rows',worst_rate<2e-13,worst_rate)
    # Independent Gaussian aperture convolution identity, including narrow-beam/large-offset cases.
    for width,sigma,diameter in [(.15,1.,.75),(.15,.1,.75),(2.5,1.,.08)]:
        a=diameter/2
        at_center=ncx2.cdf((2*a/width)**2,2,0)
        check('circular_center_'+str((width,sigma,diameter)),abs(at_center-(-math.expm1(-2*a*a/(width*width))))<2e-15)
        integral,error=quad(lambda x:math.exp(-x)*ncx2.cdf((2*a/width)**2,2,8*sigma*sigma*x/(width*width)),
                            0,math.inf,epsabs=2e-13,epsrel=2e-12,points=None,limit=400)
        analytic=-math.expm1(-2*a*a/(width*width+4*sigma*sigma))
        check('Rayleigh_aperture_convolution_'+str((width,sigma,diameter)),abs(integral-analytic)<2e-12)
    base=next(x for x in read_csv('exact_catalog_evaluations.csv') if x['configuration_id']=='original' and x['family']=='MB'
              and x['VA']==5.475 and x['nu_raw']==.165)
    uniform=next(x for x in read_csv('bright_source_comparison.csv') if x['configuration_id']=='pointing_30deg' and x['source_group']=='catalog_best_Uniform')
    selected=[('original_fixed',base),('recommended_0deg',selection['recommended']),
              ('recommended_30deg',selection['recommended_reference_geometry']),('uniform_30deg',uniform)]
    convergence=[];mi_actual=[]
    for label,row in selected:
        ch=r.configure(row);mom=m.power_conserving(ch);c=roster[row['ensemble_hash']]
        fine=m.power_conserving(ch,64)
        check(label+'_width_GH32_64',max(abs(mom['m1']-fine['m1']),abs(mom['mh']-fine['mh']))<2e-10)
        refined=[m.evaluate(c,fine,row['eta_det'],row['epsilon_det'],order=order,grid=129) for order in (32,64,128)]
        errors=dict(GH32_128=refined[0]['I_AB']-refined[-1]['I_AB'],GH64_128=refined[1]['I_AB']-refined[-1]['I_AB'],
                    full_Z33_129=refined[1]['chi_BE']-row['chi_BE'],K_refined=refined[-1]['K_raw'])
        check(label+'_MI_GH64_128',abs(errors['GH64_128'])<2e-13,errors)
        check(label+'_full_Z_grid',abs(errors['full_Z33_129'])<2e-8,errors)
        entropy80=precise_entropy(refined[-1]['a'],refined[-1]['b'],refined[-1]['Z_worst'],80)
        entropy110=precise_entropy(refined[-1]['a'],refined[-1]['b'],refined[-1]['Z_worst'],110)
        check(label+'_entropy80_110',abs(entropy80['chi']-entropy110['chi'])<m.M('1e-70'))
        check(label+'_entropy_vs_float',abs(float(entropy110['chi'])-refined[-1]['chi_BE'])<2e-12)
        zero=m.evaluate(c,mom,row['eta_det'],0)
        check(label+'_detector_zero_actual_covariance',abs(row['b']-zero['b']-row['epsilon_det'])<2e-13)
        c2=math.sqrt(row['eta_det'])*mom['mh']*c['VA']/2
        nB=(row['b']-1)/2
        check(label+'_DBL_observed_moment_radius',abs(2*(nB-c2*c2/(c['VA']/2))-row['N_post'])<2e-13)
        convergence.append(dict(label=label,errors=errors,entropy110=entropy110,selected=row))
        probes=[]
        for radial,width in [(128,16),(256,32),(512,48)]:
            actual=m.pooled_mi(c,ch,row['eta_det'],row['epsilon_det'],radial,width)
            actual.update(label=label,chi_BE=row['chi_BE'],K_pooled=.95*actual['I_AB_pooled']-row['chi_BE'],
                          delta_m1=actual['quadrature_m1']-mom['m1'],delta_mh=actual['quadrature_mh']-mom['mh'])
            probes.append(actual)
            print('POOLED MI',label,radial,width,actual['I_AB_pooled'],actual['K_pooled'],flush=True)
        delta=abs(probes[-1]['I_AB_pooled']-probes[-2]['I_AB_pooled'])
        # This is a diagnostic quadrature tolerance, not a rigorous security enclosure.
        check(label+'_actual_MI_numerical_convergence',delta<2e-5,delta)
        check(label+'_actual_fading_moments_match',max(abs(probes[-1]['delta_m1']),abs(probes[-1]['delta_mh']))<2e-5)
        mi_actual.extend(probes)
    r.save('selected_convergence.json',convergence)
    r.write('actual_pooled_fading_MI.csv',mi_actual)
    r.save('validation.json',dict(status='CURRENTLY_VERIFIED_PASS_FOR_NUMERICAL_DIAGNOSTIC_ONLY',checks=CHECKS,
           saved_rows_checked=count,MI_surrogate_GH_tolerance=2e-13,actual_MI_refinement_tolerance=2e-5,
           full_Z_verification_tolerance=2e-8,security_valid=False,hardware_validated=False))
    print('VALIDATION COMPLETE',len(CHECKS),'checks;',count,'saved rows',flush=True)


if __name__=='__main__':main()
