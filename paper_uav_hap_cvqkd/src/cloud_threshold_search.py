"""Numerical preparation only; no assumed SKR model or automatic QKD execution."""
import math
import numpy as np


def attenuate_realizations(clear, attenuation_db):
    a=float(attenuation_db)
    values=np.asarray(clear,dtype=float)
    if not math.isfinite(a) or a<0 or not np.isfinite(values).all() or np.any((values<0)|(values>1)):
        raise ValueError('Require A>=0 and physical clear power samples in [0,1]')
    s=10**(-a/10)
    result=values*s
    if s==0 or np.any((values>0)&(result==0)):
        raise ValueError('Float underflow; keep logarithmic losses instead of clipping')
    return result


def attenuate_moments(m1,mh,mass,attenuation_db):
    """Push forward an unchanged clear law; preserve its mass and zero atom.

    Do not reconstruct an untruncated PDF on [0,1] after the transformation.
    Detector noise is NOT attenuated: a selected evaluator must rebuild noise.
    """
    a=float(attenuation_db)
    if (not all(math.isfinite(x) for x in [m1,mh,mass,a]) or not 0<mass<=1
        or mh<0 or not 0<=mh*mh<=m1<=mass or a<0):
        raise ValueError('Invalid finite fading moments or attenuation')
    s=10**(-a/10)
    if s==0 or (m1>0 and s*m1==0) or (mh>0 and math.sqrt(s)*mh==0):raise ValueError('Moment underflow')
    return dict(m1=s*m1,mh=math.sqrt(s)*mh,M0=mass,power_factor=s)


def search_raw_threshold(evaluate_raw, *, upper_db=100., step_db=.5, width_db=.005):
    """Coarse raw sweep + bisection; callback is the selected existing evaluator.

    Tests may inject analytic fixtures. They are not physical SKR formulas.
    No root claim if already nonpositive, no extrapolation if not bracketed.
    Monotonicity is sampled only; this routine never certifies an outage rule.
    """
    if not all(math.isfinite(v) and v>0 for v in [upper_db,step_db,width_db]) or width_db>=.01:
        raise ValueError('Positive bounds/step and width below .01 dB required')
    cache={}
    def value(a):
        a=float(a)
        if a not in cache:
            k=float(evaluate_raw(a))
            if not math.isfinite(k):raise ValueError(f'Nonfinite raw SKR at {a} dB')
            cache[a]=k
        return cache[a]
    grid=np.unique(np.r_[np.arange(0,upper_db,step_db),upper_db])
    rates=[value(a) for a in grid]
    monotonic=all(b<=a for a,b in zip(rates,rates[1:]))
    crossings=[]
    for low,high,kl,kh in zip(grid,grid[1:],rates,rates[1:]):
        if kl>0 and kh<=0:
            while high-low>width_db:
                mid=float((low+high)/2);km=value(mid)
                if km>0:low,kl=mid,km
                else:high,kh=mid,km
            crossings.append(dict(lower_db=float(low),upper_db=float(high),
                 K_lower=kl,K_upper=kh,width_db=float(high-low)))
    # Include refinement samples when checking for observed upward steps.
    all_rows=sorted(cache.items())
    monotonic=monotonic and all(b[1]<=a[1] for a,b in zip(all_rows,all_rows[1:]))
    status=('NO_POSITIVE_CLEAR_MARGIN' if rates[0]<=0 else
            'SAMPLED_NONMONOTONIC' if not monotonic else
            'BRACKETED' if crossings else 'RIGHT_CENSORED')
    return dict(status=status,clear_raw_skr=rates[0],search_upper_db=upper_db,
        sampled_nonincreasing=monotonic,positive_to_nonpositive_crossings=crossings,
        critical_interval_db=([crossings[0]['lower_db'],crossings[0]['upper_db']]
            if status=='BRACKETED' and len(crossings)==1 else None),
        threshold_outage_rule_certified=False,
        samples=[dict(A_db=a,K_raw=k) for a,k in all_rows])
