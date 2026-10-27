"""Explicitly authorized historical-payload diagnostic; strict evaluator untouched."""
import time
import mpmath as mp
from inventory import PRIOR,STRICT,canonical,read,sha

components=canonical.components
correlation_eq14=canonical.correlation_eq14


def evaluate(source,context,protocol):
    if source.get('compatibility_status')!='CURRENTLY_VERIFIED_PASS':
        raise ValueError('Compatible historical source identity required')
    if source.get('classification') not in STRICT|{'INSUFFICIENT_EVIDENCE'}:
        raise ValueError('Invalid source cannot enter diagnostic analysis')
    if (context.get('numerical_experiment_accepted') is not True
        or context.get('numerical_status')!='CURRENTLY_VERIFIED_PASS'
        or context.get('channel_law')!=canonical.prior_model.LAW
        or context.get('protocol_sha256')!=sha(PRIOR/'protocol.json')
        or context.get('renormalized') is not False or context.get('clipped') is not False):
        raise ValueError('Validated approved channel context required')
    p,alpha=canonical.prior_model.helpers().validate_source(source)
    if abs(float(p @ (2*alpha.real)**2)-source['VA'])>protocol['numerical']['source_tolerance']:
        raise ValueError('VA=Vmod=2*nbar quadrature mismatch')
    moments=context['moments']
    t=moments['mh']**2
    if not 0<t<=moments['m1']<=1:raise ValueError('Invalid effective moments')
    noise=((moments['m1']-t)*source['VA']+protocol['xi_ch']*moments['m1']+protocol['xi_det']*moments['M0'])
    began=time.perf_counter()
    h=components(source['VA'],t,noise/t,source['C'],source['w'],digits=110)
    low=components(source['VA'],t,noise/t,source['C'],source['w'],digits=80)
    with mp.workdps(120):
        if any(abs(mp.mpf(h['decimal'][k])-mp.mpf(low['decimal'][k]))>mp.mpf('2e-11') for k in ['Z_manuscript_eq14','chi_BE']):
            raise ValueError('Eq14/Holevo precision agreement unresolved')
    holevo_seconds=time.perf_counter()-began
    began=time.perf_counter()
    mi64,mi=[canonical.prior_model.helpers().homodyne_mi(p,alpha,t,1+noise,order=order) for order in [64,128]]
    if abs(mi-mi64)>protocol['numerical']['MI_tolerance']:
        raise ValueError('MI GH64/128 agreement unresolved; higher-order validation required')
    return {**h,'eta_f':t,'xi_f':noise/t,'N_effective':noise,'I_AB':mi,
        'beta_I_AB':protocol['beta']*mi,'chi_BE':h['chi_BE'],'K_raw':protocol['beta']*mi-h['chi_BE'],
        'MI_GH64_128_difference':abs(mi-mi64),'MI_seconds':time.perf_counter()-began,'Holevo_seconds':holevo_seconds,
        'probability_deficit':context['probability_deficit'],'security_valid':False}
