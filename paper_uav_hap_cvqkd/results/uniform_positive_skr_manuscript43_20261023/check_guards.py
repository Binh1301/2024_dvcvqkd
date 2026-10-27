"""Small behavioral checks at the isolated model's scientific boundaries."""
import math
import search as s


def main():
    sources=s.bank();c=next(x for x in sources if x['VA']==.6)
    mom=dict(M0=1.,m1=.2,mh=math.sqrt(.2),normalized_within_tolerance=True)
    value=s.model(c,mom,128,129)
    expected=(mom['m1']-mom['mh']**2)*c['VA']+.0186*.2+.005
    assert abs(value['N_effective']-expected)<1e-15
    assert value['T_Holevo']==value['eta_f']==mom['mh']**2
    assert value['sigma2_MI']==1+expected and 'eta_det' not in value
    assert abs(value['K_raw']-(.95*value['I_AB']-value['chi_BE']))<1e-15
    try:s.model(c,{**mom,'M0':.9,'normalized_within_tolerance':False})
    except ValueError as e:assert str(e)=='FAILED_PDF_NORMALIZATION'
    else:raise AssertionError('Failed PDF must never reach information evaluation')
    assert all(x['p'].shape==(256,) and (x['p']==1/256).all() for x in sources)
    s.save(s.OUT/'guard_checks.json',dict(status='CURRENTLY_VERIFIED_PASS',
        checks=['Uniform256 equal probabilities','v43 noise/no eta_det','one quantum effective plane',
                'homodyne variance','unclipped raw rate identity','PDF failure prevents rate evaluation'],
        source_hash=c['ensemble_hash'],producer_sha256=s.a.sha(__file__)))
    print('CURRENTLY_VERIFIED_PASS: 6 guard checks')


if __name__=='__main__':main()
