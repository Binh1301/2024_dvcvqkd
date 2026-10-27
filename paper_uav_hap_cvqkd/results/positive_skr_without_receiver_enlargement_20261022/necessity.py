"""One-at-a-time reversions distinguish necessary changes from added margin."""
import search as s
from validate import precise_entropy


def main():
    if (s.OUT/'necessity.json').exists():raise FileExistsError('Preserve completed necessity checks')
    selection=s.read(s.OUT/'selection.json');s.initialize();rows=[];extra=[]
    for selected in selection['recommendations'][1:]:
        c=s.source(selected);par=s.parameters(selected)
        for axis,(name,original) in enumerate(zip(s.FIELDS,s.BASE)):
            if par[axis]==original:continue
            p=list(par);p[axis]=original
            coarse=s.evaluate(c,p,'necessary_change_reversion',256,32);r=coarse;delta=None
            if r['K_raw']>0 or abs(r['K_raw'])<5e-5:
                r=s.evaluate(c,p,'necessary_change_reversion',512,48);delta=abs(r['I_AB']-coarse['I_AB'])
                assert delta<2e-6
                if r['K_raw']>0:assert r['K_raw']>2*.95*delta
            rows.append({**r,'configuration':selected['configuration'],'reverted_parameter':name,
                'nominal_value':par[axis],'baseline_value':original,'required_for_positive_sign_on_this_branch':r['K_raw']<=0,
                'observed_MI_change':delta,'scope':'FIXED_SOURCE_ALL_OTHER_PARAMETERS_FIXED_NOT_GLOBAL_NECESSITY'})
            if axis==2 and r['K_raw']>0:
                ch,mo=s.n.optical(*p[:6],p[8]);fine=s.n.previous.evaluate(c,mo,eta_det=p[6],epsilon_det=p[7],grid=129)
                entropy=precise_entropy(r['a'],r['b'],r['Z_worst'],110)
                assert abs(fine['chi_BE']-r['chi_BE'])<2e-8 and abs(float(entropy['chi'])-r['chi_BE'])<2e-12
                extra.append({**r,'configuration':'C_original_geometry_tiny_margin','observed_MI_change':delta,
                    'full_Z33_129_difference':fine['chi_BE']-r['chi_BE'],'classification':'NEAR_ZERO_DIAGNOSTIC_ONLY_NOT_ROBUST_NOT_RECOMMENDED'})
    s.write('necessary_changes.csv',rows);s.write('additional_positive_original_geometry.csv',extra)
    s.save('necessity.json',dict(status='CURRENTLY_VERIFIED_PASS',reversions=len(rows),additional_positive_original_geometry=extra,
        note='C geometry shortening and its efficiency upgrade are alternatives for sign; neither is individually necessary with all other C changes retained'))
    s.write('all_evaluations.csv',s.ROWS)
    print('NECESSITY PASS',[(r['configuration'],r['zenith_deg'],r['eta_det'],r['K_raw']) for r in extra],len(s.ROWS),flush=True)


if __name__=='__main__':main()
