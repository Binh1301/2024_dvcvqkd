"""Finite-block reference and existing accumulated key-yield proxy adapters."""
import math
import numpy as np
from .config import load_config
from .finite_size import finite_key
from .hap_uav_channel import _finite


def delta_per_signal(n,epsilon):
    n=_finite(n,'valid block signals',minimum=0)
    if n<=0:raise ValueError('Delta per signal requires n>0; zero-signal key is handled by finite_key')
    # One mathematical block reuses the evaluator; this never assigns mission m0.
    return finite_key(0.,1,n,epsilon)['penalty_per_signal']


def load_finite_reference(path):
    c=load_config(path)
    total=_finite(c['N_block'],'N_block',minimum=1)
    if int(total)!=total:raise ValueError('N_block must be an integer')
    fraction=_finite(c['key_fraction'],'key_fraction')
    if not 0<fraction<=1:raise ValueError('key_fraction must lie in (0,1]')
    eps=[_finite(c[k],k) for k in ('epsilon_PE','epsilon_EC','epsilon_PA')]
    if not all(0<x<1 for x in eps):raise ValueError('Reference failure probabilities must lie in (0,1)')
    epsilon=math.fsum(eps)
    if epsilon>=1:raise ValueError('Total reference epsilon must be below1')
    n=total*fraction
    c['derived']=dict(epsilon_reference=epsilon,n_block_reference=n,
                       delta_reference_bits_per_signal=delta_per_signal(n,epsilon))
    return c


def valid_signals_per_clear_slot(f_s,dt,eta_valid):
    rate=_finite(f_s,'f_s signal rate',minimum=0)
    duration=_finite(dt,'slot duration',minimum=0)
    fraction=_finite(eta_valid,'eta_valid')
    if rate<=0 or duration<=0 or not 0<=fraction<=1:
        raise ValueError('Require f_s>0, dt>0, and explicit eta_valid in [0,1]')
    value=rate*duration*fraction
    if not math.isfinite(value):raise ValueError('Valid-signal count exceeds the numerical range')
    return value


def finite_size_aware_key_yield_proxy(slot_rates,available_slots,m0,epsilon,dt):
    rates=np.asarray(slot_rates,float);z=np.asarray(available_slots)
    if rates.ndim!=1 or rates.shape!=z.shape or len(rates)==0 or not np.isfinite(rates).all() or not np.isin(z,[0,1]).all():
        raise ValueError('Proxy needs finite slot rates and matching binary retained-slot flags')
    duration=_finite(dt,'slot duration')
    if duration<=0:raise ValueError('Slot duration must be positive')
    result=finite_key(float(np.sum(z*rates)),int(np.sum(z)),m0,epsilon)
    return dict(result,K=len(rates),mission_time_s=len(rates)*duration,
                average_skr_bits_s=result['key_bits']/(len(rates)*duration),
                objective_name='finite_size_aware_key_yield_proxy')
