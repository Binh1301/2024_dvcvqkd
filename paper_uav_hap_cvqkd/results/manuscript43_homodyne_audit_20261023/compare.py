"""Focused, source-authenticated Gaussian reevaluation after component tests pass."""
import math
import mpmath as mp
import numpy as np
import audit_model as a
import run_audit as r


def independent_entropy(row, digits):
    with mp.workdps(digits):
        aa,bb,z=[mp.mpf(str(row[k])) for k in ['a','b','Z_worst']]
        if abs(row['Z_worst'])==row['Z_physical_cap']:
            z=mp.sqrt(min((aa-1)*(bb+1),(aa+1)*(bb-1)))
            n1,n2=1+abs(aa-bb),mp.mpf(1)
        else:
            delta=aa*aa+bb*bb-2*z*z
            root=mp.sqrt(delta*delta-4*(aa*bb-z*z)**2)
            n1,n2=mp.sqrt((delta+root)/2),mp.sqrt((delta-root)/2)
        n3=mp.sqrt(aa*(aa-z*z/bb))
        if min(n1,n2,n3)<1:raise ValueError('High-precision covariance is nonphysical')
        def g(nu):
            x=(nu-1)/2
            return ((x+1)*mp.log1p(x)-x*mp.log(x))/mp.log(2) if x else mp.mpf(0)
        return float(g(n1)+g(n2)-g(n3))


def main():
    if (a.OUT/'comparison_receipt.json').exists():raise FileExistsError('Preserve completed comparison')
    assert a.read(a.OUT/'validation.json')['status']=='CURRENTLY_VERIFIED_PASS'
    regressions=a.read(a.OUT/'historical_regressions.json')['records']
    pdf=a.read(a.OUT/'channel_pdf_audit.json')['contexts']
    bylabel={v['context']:v for v in pdf}
    corrected=[];oldnew=[];checks=[];raw_results=[]
    for ref in regressions:
        if ref['label']=='original_manuscript_trial8':continue
        old=ref['fresh'];c=r.source(old)
        mo=dict(M0=old['physical_mass'],m1=old['m1'],mh=old['mh'],P0=old['P0'],law=old['treatment'])
        eta,epsilon=old['eta_det'],old['epsilon_det']
        fine=a.evaluate_physical(c,mo,eta,epsilon,order=128,grid=129)
        coarse=a.evaluate_physical(c,mo,eta,epsilon,order=64,grid=33)
        separate,error=a.independent_mi(c['p'],c['alpha'],fine['T_quantum'],fine['sigma2_output'])
        entropy80=independent_entropy(fine,80);entropy110=independent_entropy(fine,110)
        assert abs(coarse['I_AB']-fine['I_AB'])<2e-10
        assert abs(coarse['chi_BE']-fine['chi_BE'])<2e-8
        assert abs(separate-fine['I_AB'])<2e-10 and error<2e-10
        assert max(abs(entropy80-fine['chi_BE']),abs(entropy110-fine['chi_BE']))<2e-11
        assert abs(coarse['I_AB']-old['I_AB_surrogate'])<2e-12
        assert abs(coarse['chi_BE']-old['chi_BE'])<2e-12
        fine.update(scenario=ref['label'],eta_det=eta,epsilon_det=epsilon,
            D_r=old['D_r'],zenith_deg=old['zenith_deg'],divergence_urad=old['divergence_urad'],
            jitter_urad=old['jitter_urad'],sigma_h_m=old['sigma_h_m'],
            status='PHYSICAL_GAUSSIAN_COMPONENT_CHECKS_PASS_SECURITY_UNVALIDATED')
        corrected.append(fine)
        checks.append(dict(scenario=ref['label'],MI_GH64=coarse['I_AB'],MI_GH128=fine['I_AB'],
            MI_adaptive=separate,adaptive_error=error,chi_Z33=coarse['chi_BE'],chi_Z129=fine['chi_BE'],
            chi_entropy80=entropy80,chi_entropy110=entropy110,
            historical_Gaussian_MI_residual=coarse['I_AB']-old['I_AB_surrogate'],
            historical_Holevo_residual=coarse['chi_BE']-old['chi_BE'],
            covariance_b_residual=coarse['b']-old['b']))
        oldnew.append(dict(scenario=ref['label'],channel_law=mo['law'],source_hash=c['ensemble_hash'],VA=c['VA'],nu_raw=c['nu_raw'],
            eta_det=eta,epsilon_det=epsilon,Dr=old['D_r'],Legacy_MI=old['I_AB'],Corrected_MI=fine['I_AB'],
            Legacy_Holevo=old['chi_BE'],Corrected_Holevo=fine['chi_BE'],Legacy_SKR=old['K_raw'],Corrected_SKR=fine['K_raw'],
            delta_MI=fine['I_AB']-old['I_AB'],delta_Holevo=fine['chi_BE']-old['chi_BE'],delta_SKR=fine['K_raw']-old['K_raw'],
            change='exact_fading_likelihood_to_requested_Gaussian_effective_MI; physical_noise_and_homodyne_Holevo_unchanged',
            remains_positive=fine['K_raw']>0,security_valid=False,historical_files_overwritten=False))
        raw=bylabel[ref['label']]
        try:
            value=a.evaluate_physical(c,raw,eta,epsilon,order=128,grid=129)
            raw_results.append(dict(**value,scenario=ref['label'],status='RAW_V43_PDF_WITHIN_DECLARED_TOLERANCE',
                M0=raw['M0'],channel_comparison='Different_law_from_passive_historical_result_not_a_detector_only_correction'))
        except ValueError as error:
            raw_results.append(dict(scenario=ref['label'],channel_law=raw['law'],source_hash=c['ensemble_hash'],
                M0=raw['M0'],I_AB=None,chi_BE=None,K_raw=None,status='BLOCKED_BY_SCIENTIFIC_MODEL',failure=str(error)))
        print('GAUSSIAN',ref['label'],'old',old['K_raw'],'new',fine['K_raw'],flush=True)
    baseline=next(c for c in r.catalog() if c['family']=='MB' and c['nu_raw']==.165 and c['VA']==5.475)
    recent=next(c for c in r.catalog() if c['family']=='MB' and c['nu_raw']==.25 and c['VA']==1.6249995399703647)
    conventions=[];noise_checks=[]
    for context,c in [('baseline8',baseline),('recent8',recent)]:
        raw=bylabel[context]
        for eta in [.8,.85,.9,.95]:
            for epsilon in [.0135,.005]:
                common=dict(scenario=context,eta_det=eta,epsilon_det=epsilon,
                    source_hash=c['ensemble_hash'],channel_law=raw['law'],VA=c['VA'],nu_raw=c['nu_raw'])
                physical=a.evaluate_physical(c,raw,eta,epsilon,order=128,grid=129)
                for plane in ['output','classically_rescaled_output']:
                    conventions.append({**common,**physical,'model':'C_physical_'+plane,
                        'xi_det_definition':'epsilon_det_output_separate_from_efficiency',
                        'noise_variance':physical['sigma2_output'] if plane=='output' else physical['sigma2_rescaled'],
                        'effective_MI_signal_gain2':physical['T_quantum'] if plane=='output' else physical['eta_f'],
                        'status':'COMPONENTS_VALIDATED_SAME_QUANTUM_COVARIANCE'})
                for definition in ['A_epsilon_over_eta','B_chi_hom']:
                    literal=a.evaluate_literal(c,raw,eta,epsilon,definition)
                    conventions.append({**common,**literal,'noise_variance':literal['sigma2_literal'],
                        'effective_MI_signal_gain2':literal['eta_f']})
                    for outage in ['limit','active_only']:
                        projected=a.evaluate_literal(c,raw,eta,epsilon,definition,real_projection=True,outage=outage)
                        conventions.append({**common,**projected,'noise_variance':projected['sigma2_literal'],
                            'effective_MI_signal_gain2':projected['eta_f']})
                        if definition=='B_chi_hom' and outage=='limit':
                            difference=projected['I_AB']-physical['I_AB']
                            assert abs(difference)<2e-10
                            noise_checks.append(dict(**common,convention='B_chi_hom_classical_MI_matches_C_but_quantum_channel_different',
                                MI_difference=difference,quantum_T_literal=raw['mh']**2,quantum_T_physical=physical['T_quantum'],
                                b_literal=1+raw['mh']**2*c['VA']+projected['N_literal'],b_physical=physical['b'],
                                Holevo_difference=projected['chi_BE']-physical['chi_BE']))
                conventions.append({**common,'model':'B_independent_xi_det_unresolved','xi_det_definition':'independent_explicit',
                    'xi_det':None,'I_AB':None,'chi_BE':None,'K_raw':None,'status':'BLOCKED_MISSING_DEFINITION_OR_VALUE'})
    # Same original lognormal law/source, not the later passive collector baseline.
    raw=bylabel['baseline8'];value=a.evaluate_physical(baseline,raw,.8,.0135,order=128,grid=129)
    original=next(v for v in regressions if v['label']=='original_manuscript_trial8')['fresh']
    oldnew.append(dict(scenario='original_manuscript_trial8',channel_law=raw['law'],source_hash=baseline['ensemble_hash'],
        VA=baseline['VA'],nu_raw=baseline['nu_raw'],eta_det=.8,epsilon_det=.0135,Dr=.08,
        Legacy_MI=original['I_AB'],Corrected_MI=value['I_AB'],Legacy_Holevo=original['chi_BE'],Corrected_Holevo=value['chi_BE'],
        Legacy_SKR=original['K_raw'],Corrected_SKR=value['K_raw'],delta_MI=value['I_AB']-original['I_AB'],
        delta_Holevo=value['chi_BE']-original['chi_BE'],delta_SKR=value['K_raw']-original['K_raw'],
        change='matched_physical_noise_convention; full_Z_instead_of_fixed_lower_endpoint',remains_positive=value['K_raw']>0,
        security_valid=False,historical_files_overwritten=False))
    r.write('old_vs_new.csv',oldnew);r.write('corrected_same_channel.csv',corrected)
    r.write('detector_convention_comparison.csv',conventions);r.write('classical_quantum_plane_checks.csv',noise_checks)
    r.write('focused_independent_checks.csv',checks);r.save('raw_manuscript43_results.json',raw_results)
    r.save('comparison_receipt.json',dict(status='CURRENTLY_VERIFIED_PASS',same_channel_scenarios=len(oldnew),
        detector_convention_rows=len(conventions),focused_checks=len(checks),raw_PDF_blocked=sum(v['K_raw'] is None for v in raw_results),
        original_trial_corrected_K=value['K_raw'],source_cache_modified=False,old_results_modified=False,new_optimization=False,
        recommended_Gaussian_component='C_physical_output_gaussian_effective',recommended_secure_default=False,
        security_valid=False,whole_manuscript_model_validated=False))
    print('FOCUSED COMPARISONS COMPLETE',len(oldnew),len(conventions),flush=True)


if __name__=='__main__':main()
