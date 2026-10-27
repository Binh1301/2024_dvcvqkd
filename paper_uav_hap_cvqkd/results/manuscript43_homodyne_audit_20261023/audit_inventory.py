"""Repository traceability, cache impact and source/channel notation checks."""
import ast
import math
import re
from collections import defaultdict
import numpy as np
from scipy.integrate import quad
from scipy.stats import rice
import audit_model as a
import run_audit as r


def main():
    if (a.OUT/'inventory_receipt.json').exists():raise FileExistsError('Preserve completed inventory')
    paths={
        'scripts/hap_uav_channel_pdf.py':'mixed channel PDF and Rician pointing',
        'scripts/calculate_channel_pdf_and_moments.py':'geometry/HV/closed moments',
        'src/manuscript_literal_3moments.py':'historical37 literal mode, not v43',
        'src/manuscript_corrected_3moments.py':'explicit historical conditional-active law; not raw v43 PDF',
        'src/manuscript_corrected_evaluator.py':'trusted/ideal configuration gate; not new untrusted mode',
        'src/manuscript_corrected_mi.py':'historical complex fading measurement',
        'src/cvqkd/mutual_information.py':'frozen production complex heterodyne MI',
        'scripts/recheck_manuscript_homodyne_noise.py':'shared GH dimension1 helper; historical script uses mixed primary pairing',
        'src/modulation/qam256.py':'C4 square QAM and canonical MB PMF',
        'src/modulation/normalization.py':'VA=2*nbar physical amplitudes',
        'src/cvqkd/gram_moments.py':'exact source correlation implementation',
        'scripts/exact_cache_provenance.py':'authenticated source/cache identities',
        'src/manuscript_mobility.py':'233-source authenticated catalog and historical mixed evaluator',
        'src/cvqkd/covariance.py':'frozen production heterodyne conditional spectrum',
        'src/cvqkd/holevo.py':'production correlation interval/Holevo',
        'src/cvqkd/protocol.py':'frozen ideal heterodyne assumptions',
        'src/optimization/trainer.py':'production learning caller; NOT_RUN',
        'scripts/run_theta10_D55_alt_opt.py':'historical finite exact-source parameter optimizer; NOT_RUN',
        'scripts/optimize_uniform_manuscript_2d.py':'historical 2D MI optimizer; not homodyne reuse',
        'results/untrusted_positive_skr_feasibility_20261022/model.py':'preserved strict real homodyne/Gaussian component and passive surrogate',
        'results/uav_skwap_aware_positive_skr_20261022/parameter_adapter.py':'preserved pooled fading likelihood and aperture adapter',
        'configs/default.yaml':'production protocol/defaults preserved',
        'configs/channel.yaml':'unresolved production channel inputs preserved',
        'configs/manuscript_corrected_3moments.json':'historical alternative convention preserved',
        'configs/manuscript_mobility.json':'authenticated source roster preserved',
        'tests/test_mutual_information.py':'historical production MI tests',
        'tests/test_holevo.py':'historical production security tests',
        'tests/test_manuscript_corrected_mi.py':'historical complex fading test',
    }
    inventory=[]
    for path,role in paths.items():
        f=a.ROOT/path
        if not f.exists():
            inventory.append(dict(path=path,role=role,status='MISSING_NOT_ASSUMED',modified=False));continue
        symbols=[]
        if f.suffix=='.py':
            tree=ast.parse(f.read_text(encoding='utf-8-sig'))
            symbols=[f'{n.name}:{n.lineno}' for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))]
        inventory.append(dict(path=path,role=role,status='LOCATED',symbols=';'.join(symbols),sha256=a.sha(f),modified=False))
    r.write('repository_inventory.csv',inventory)
    start=a.read(a.OUT/'startup_manifest.json');sources={c['source_path']:c for c in r.catalog()}
    cache=[];folders=defaultdict(list)
    for path,digest in start['protected'].items():
        if not path.startswith('paper_uav_hap_cvqkd/results/'):continue
        relative=path[len('paper_uav_hap_cvqkd/'):];parts=relative.split('/');folders[parts[1]].append(relative)
        kind=None
        if relative in sources:kind='AUTHENTICATED_SOURCE_CW_REUSABLE_IDENTICAL_ENSEMBLE'
        elif any(x in path.lower() for x in ['/exact_source_cache/','/source_cache/','/source_checkpoints/']):kind='SOURCE_CACHE_PRESERVED_NOT_REVALIDATED_IN_THIS_AUDIT'
        elif 'cache' in path.lower() and path.endswith('.json'):kind='CHANNEL_OR_OBJECTIVE_CACHE_REQUIRES_NEW_CONTEXT_FOR_VARIANT_C'
        if kind:
            cache.append(dict(path=relative,sha256=digest,classification=kind,modified=False,
                ensemble_hash=sources[relative]['ensemble_hash'] if relative in sources else '',
                underlying_source_convention_changed=False,old_objective_interchangeable=False))
    r.write('cache_impact.csv',cache)
    recent={'corrected_excess_noise_trial_20261022','untrusted_positive_skr_feasibility_20261022',
        'minimal_physical_positive_skr_20261022','positive_skr_without_receiver_enlargement_20261022',
        'lightweight_uav_positive_skr_20261022','uav_skwap_aware_positive_skr_20261022'}
    result_folders=[]
    for name,files in sorted(folders.items()):
        note='NOT_REEVALUATED_PROTOCOL_AND_CHANNEL_DEPENDENT; DO_NOT_TRANSFER_TO_NEW_VARIANT'
        if name in recent:note='SELECTED_MATCHED_REGRESSIONS_OR_INPUTS_AUDITED; REST_NOT_REEVALUATED'
        if name in ['skr_vs_zenith_angle_20261019','zenith_angle_root_cause_diagnostic_20261021','manuscript_mobility_p1_p2_p3_20261019']:
            note='HISTORICAL_MIXED_2D_MI_HOMODYNE_HOLEVO; NOT_A_CONSISTENT_NEW_HOMODYNE_RATE'
        result_folders.append(dict(result_directory='results/'+name,entry_kind='directory' if (a.ROOT/'results'/name).is_dir() else 'file',
            protected_file_count=len(files),assessment=note,
            historical_bytes_changed=False,all_points_reoptimized_or_revalidated=False))
    r.write('affected_results.csv',result_folders)
    notation=[]
    for c in [next(c for c in r.catalog() if c['nu_raw']==.165 and c['VA']==5.475),
              next(c for c in r.catalog() if c['nu_raw']==.25 and c['VA']==1.6249995399703647)]:
        p,alpha=a.validate_source(c);indices=np.indices((16,16)).reshape(2,-1).T
        energy=np.sum(indices**2,axis=1);uncentered=np.exp(-c['nu_raw']*energy);uncentered/=uncentered.sum()
        center_energy=np.sum((indices-7.5)**2,axis=1)
        expected=np.exp(-c['nu_raw']*center_energy);expected/=expected.sum()
        assert np.max(abs(expected-p))<2e-14
        spacing=float(np.diff(np.unique(alpha.real)).mean())
        notation.append(dict(source_hash=c['ensemble_hash'],nu_raw=c['nu_raw'],nu_repo=42.5*c['nu_raw'],
            spacing=spacing,nu_physical_energy=c['nu_raw']/spacing**2,centered_PMF_residual=float(np.max(abs(expected-p))),
            uncentered_weighted_alpha_real=float((uncentered@alpha).real),uncentered_weighted_alpha_imag=float((uncentered@alpha).imag),
            old_cache_reusable_for_uncentered_PMF=False))
    r.write('MB_notation_checks.csv',notation)
    gamma,nu=.165,.25
    grid=np.indices((16,16));raw_energy=grid[0]**2+grid[1]**2
    mismatch=float(np.exp(-gamma*raw_energy).sum()/np.exp(-nu*raw_energy).sum())
    r.save('notation_findings.json',dict(raw_index_gamma=gamma,raw_index_denominator_nu=nu,literal_probability_sum=mismatch,
        fixture_only_not_assumed_manuscript_values=True,gamma_nu_relationship='UNDEFINED_IN_MANUSCRIPT',
        centered_probability_rule_required_for_existing_sources=True,source_cache_changes=False))
    ch=r.raw_channel((20.,1.,30.,233.,15.61,1.,.8,.0135,.92,.08));v=float(ch['v'])
    turbulence=[]
    for q in [0.,1.,2.]:
        value,error=quad(lambda s:math.exp(q*s-(s+v/2)**2/(2*v))/math.sqrt(2*math.pi*v),
            -math.inf,math.inf,epsabs=2e-12,epsrel=2e-12)
        target=math.exp(.5*v*(q*q-q));assert abs(value-target)<2e-10
        turbulence.append(dict(power=q,direct=value,closed=target,error=error,log_irradiance_variance=v,log_amplitude_variance=v/4,
            model='Eq5_LN_minus_v_over2_v',raw_Rytov_used_as_log_irradiance_variance='WEAK_TURBULENCE_APPROXIMATION'))
    r.write('turbulence_variance_checks.csv',turbulence)
    rician=[]
    with mp_context():
        for rho in [0.,.1,.5]:
            c=a.raw_coefficients(ch,rho);B,d,sigma,lc,c3,mu=[float(c[k]) for k in ['B','d','sigma','logC1','C3','mu']]
            for q in [.5,1.]:
                exact=float(ch['P1'])*B**q*math.exp(.5*v*(q*q-q))*d/(d+q)*math.exp(-rho*rho*q/(2*sigma*sigma*(d+q)))
                cf=float(ch['P1'])*B**q*d/(d+q)*math.exp(lc+(d+q)**2/(4*c3*c3)-(d+q)*mu)
                direct,error=quad(lambda rr:math.exp(-2*q*rr*rr/ch['w_eq_m']**2)*rice.pdf(rr,rho/sigma,scale=sigma),
                    0.,math.inf,epsabs=2e-12,epsrel=2e-12)
                direct*=float(ch['P1'])*B**q*math.exp(.5*v*(q*q-q))
                assert abs(direct-exact)<2e-10
                rician.append(dict(rho_m=rho,power=q,full_support_exact_product_moment=exact,
                    full_support_Eq10_moment=cf,direct_Rice_integral=direct,relative_Eq10_difference=cf/exact-1,
                    scope='UNTRUNCATED_PRODUCT_DIAGNOSTIC_NOT_BOUNDED_MOMENT_REPLACEMENT'))
    r.write('Rician_product_checks.csv',rician)
    r.save('inventory_receipt.json',dict(status='CURRENTLY_VERIFIED_PASS',located_files=sum(x['status']=='LOCATED' for x in inventory),
        missing_paths=[x['path'] for x in inventory if x['status']!='LOCATED'],cache_rows=len(cache),
        result_entries=len(result_folders),result_directories=sum(x['entry_kind']=='directory' for x in result_folders),
        result_root_files=sum(x['entry_kind']=='file' for x in result_folders),
        authenticated_catalog_source_paths=len(sources),MB_notation_fixtures=len(notation),
        nonzero_rho_Eq10_exact_product_discrepancy_detected=any(abs(x['relative_Eq10_difference'])>1e-8 for x in rician),
        whole_model_or_all_historical_results_validated=False))
    print('INVENTORY/NOTATION COMPLETE',len(inventory),len(cache),len(result_folders),flush=True)


def mp_context():
    return a.mp.workdps(90)


if __name__=='__main__':main()
