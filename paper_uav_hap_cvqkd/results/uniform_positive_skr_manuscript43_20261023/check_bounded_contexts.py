"""Higher width-quadrature order for every secondary context used in the search."""
import search as s


def main():
    checks=[]
    for path in sorted((s.OUT/'contexts').glob('*.json')):
        ctx=s.read(path)
        if ctx['law']!=s.BOUNDED:continue
        high=s.a.legacy.power_conserving(ctx['channel'],64)
        error=max(abs(high[k]-ctx['moments'][k]) for k in ['m1','mh'])
        if error>2e-11:raise ValueError('Width quadrature did not converge: '+path.stem)
        checks.append(dict(context_id=path.stem,m1_high=high['m1'],mh_high=high['mh'],maximum_residual=error,
            moments_sha256=s.key(ctx['moments']),radial_error=high['radial_quadrature_error']))
    s.save(s.OUT/'bounded_all_contexts_validation.json',dict(status='CURRENTLY_VERIFIED_PASS',
        checks=checks,contexts=len(checks),maximum_residual=max(r['maximum_residual'] for r in checks),
        threshold=2e-11,producer_sha256=s.a.sha(__file__)))
    print('ALL BOUNDED CONTEXTS',len(checks),'max residual',max(r['maximum_residual'] for r in checks))


if __name__=='__main__':main()
