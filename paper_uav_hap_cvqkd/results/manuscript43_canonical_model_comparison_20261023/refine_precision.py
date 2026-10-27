"""Independent equivalent quadrature for pooled homodyne MI and tiny Eq10 tails."""
import math
import numpy as np
from scipy.special import roots_hermitenorm
from scipy.stats import ncx2
import audit_fixed as f


def pooled(c,ch,radial_order,width_order,output_order):
    x,wx=np.polynomial.legendre.leggauss(radial_order)
    x=20*(x+1);wx=20*wx*np.exp(-x)
    z,wz=roots_hermitenorm(width_order);wz/=math.sqrt(2*math.pi)
    widths=ch['w_eff_m']*np.exp(-(-float(ch['v'])/2+math.sqrt(float(ch['v']))*z)/2)
    t=ch['eta_atm']*ncx2.cdf((ch['D_r']/widths[:,None])**2,2,
        8*ch['sigma_s_m']**2*x[None,:]/widths[:,None]**2)
    weights=(float(ch['P1'])*np.outer(wz,wx)).ravel()
    weights=np.r_[weights,float(ch['P0'])];t=np.r_[t.ravel(),0.]
    if abs(weights.sum()-1)>2e-12:raise ValueError('Pooled quadrature missing mass')
    levels,px=f.a.marginal(c['p'],c['alpha'])
    means=levels[:,None]*np.sqrt(t)[None,:]
    variance=1+.0186*t+.005
    extent=float(np.max(abs(means))+12*math.sqrt(variance.max()))
    y,wy=np.polynomial.legendre.leggauss(output_order);y*=extent;wy*=extent
    densities=np.empty((output_order,len(px)));scale=weights/np.sqrt(2*math.pi*variance)
    for start in range(0,output_order,16):
        delta=y[start:start+16,None,None]-means[None,:,:]
        densities[start:start+16]=np.sum(np.exp(-delta**2/(2*variance[None,None,:]))*scale,axis=-1)
    mixture=densities@px
    terms=densities*np.log(densities/mixture[:,None])
    information=float(wy@(terms@px)/math.log(2))
    masses=wy@densities
    return dict(I_AB=information,conditional_mass_residual=float(max(abs(masses-1))),
        quadrature_m1=float(weights@t),quadrature_mh=float(weights@np.sqrt(t)),
        total_weight=float(weights.sum()),radial_order=radial_order,width_order=width_order,output_order=output_order,
        eta_max=float(t.max()),eta_atm=ch['eta_atm'])


def stable_tail(ch,rho=0.):
    mp=f.mp
    with mp.workdps(100):
        B,d,v,sigma=map(lambda k:mp.mpf(str(ch[k])),['B','d','v','sigma_s_m'])
        lam=mp.mpf(str(rho))**2/sigma**2
        vv=v+lam/d**2;mean=-v/2-lam/(2*d);root=mp.sqrt(vv)
        z=(-mp.log(B)-mean)/root
        survival=lambda x:mp.erfc(x/mp.sqrt(2))/2
        tail=mp.mpf(str(ch['P1']))*(survival(z)
            -mp.exp(-d*mp.log(B)-d*mean+d*d*vv/2)*survival(z+d*root))
        if tail<0:raise ValueError('Stable tail became negative')
        return mp.nstr(tail,60)


def main():
    if (f.OUT/'refined_precision_receipt.json').exists():raise FileExistsError('Preserve completed precision check')
    context=f.read(f.OUT/'fixed_contexts.json')['critical_uniform_positive'];ch=context['channel'];m=context['bounded_moments']
    c=next(c for c in f.r.catalog() if c['family']=='Uniform' and c['VA']==3.)
    protocol=f.read(f.OUT/'additional_precision_protocol.json')
    results=[pooled(c,ch,*level) for level in protocol['quadrature_levels']]
    for result in results:
        if max(abs(result['quadrature_m1']-m['m1']),abs(result['quadrature_mh']-m['mh']),
            result['conditional_mass_residual'])>2e-10:raise ValueError('Independent pooled quadrature failed moments/masses')
    delta=results[-1]['I_AB']-results[-2]['I_AB']
    if abs(delta)>2e-10:raise ValueError('Independent pooled MI not converged')
    reference=context['evaluations']['C_Uniform_search_bounded']
    value=dict(**results[-1],chi_BE=reference['chi_BE'],raw_SKR=.95*results[-1]['I_AB']-reference['chi_BE'],
        delta_I_AB=results[-1]['I_AB']-reference['I_AB'],
        delta_K=.95*(results[-1]['I_AB']-reference['I_AB']),source_hash=c['ensemble_hash'])
    f.save('pooled_MI_refined.json',dict(status='CURRENTLY_VERIFIED_PASS',records=results,convergence_delta=delta,
        compared_to_Gaussian=value,no_eta_det_parameter=True,same_physical_law_as_historical_pooled=True))
    rows=[]
    for label,ch0,rhos in [('critical',ch,[0.,.03,.1]),('baseline',f.optical([.08,233.,15.61,1.,30.]),[0.,.5])]:
        for rho in rhos:
            raw=f.a.raw_pdf_moments(ch0,rho)
            rows.append(dict(scenario=label,rho_m=rho,stable_tail=stable_tail(ch0,rho),
                one_minus_M0=raw['raw_upper_tail_mass'],direct_tail_integral=raw['upper_tail_quadrature'],
                absolute_tolerance=1e-10,relative_precision_not_implied_by_absolute_tolerance=True))
    f.save('tail_precision.json',rows);f.write('tail_precision.csv',rows)
    f.save('refined_precision_receipt.json',dict(status='CURRENTLY_VERIFIED_PASS',
        protocol_sha256=f.a.sha(f.OUT/'additional_precision_protocol.json'),producer_sha256=f.a.sha(__file__),
        MI_quadrature_converged=True,source_unchanged=True,channel_law_changed=False))
    print('REFINED MI',value,'convergence delta',delta,flush=True)


if __name__=='__main__':main()
