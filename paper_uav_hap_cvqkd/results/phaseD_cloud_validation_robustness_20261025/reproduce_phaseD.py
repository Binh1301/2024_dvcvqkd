"""Bounded Phase D diagnostics. Never generate source moments or channel contexts."""
import argparse
import csv
import hashlib
import importlib.util
import inspect
import itertools
import json
from pathlib import Path
import subprocess
import sys
import time
import unittest

import numpy as np
from scipy.integrate import quad
from scipy.special import ndtr
from scipy.stats import t as student_t, kstest

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
BASE = ROOT / 'results/phaseC_new_cloud_dp_greedy_stationary_20261025'
sys.path.insert(0, str(BASE))
import new_cloud_model as cloud
import compare_algorithms as alg

PASS = 'CURRENTLY_VERIFIED_PASS'
METRICS = ['average_usable_skr', 'objective_U', 'zero_rate_unavailability',
           'total_distance_m', 'position_changes']
PROBS = [.4, .5, .8]
SEED = 20261026


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def rows(path):
    with Path(path).open(encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def save(name, value):
    (OUT/name).write_text(json.dumps(value, indent=2, ensure_ascii=False,
                                   allow_nan=False)+'\n', encoding='utf-8')


def write(name, data):
    assert data, name
    fields = list(dict.fromkeys(k for row in data for k in row))
    with (OUT/name).open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(data)


def stats(values):
    v = np.asarray(values, dtype=float)
    mean = float(v.mean())
    sd = float(v.std(ddof=1))
    se = sd/np.sqrt(len(v))
    half = float(student_t.ppf(.975, len(v)-1)*se)
    return dict(mean=mean, sd=sd, se=float(se), ci95_low=mean-half,
                ci95_high=mean+half, missions=len(v))


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def baseline():
    """Reconstruct all 912 saved summary rows and the displayed tables."""
    data = rows(BASE/'simulation_results.csv')
    lookup = {}
    for r in data:
        key = (r['geometry'], r['case_id'], int(r['mission_id']), r['algorithm'])
        assert key not in lookup
        lookup[key] = r
    differences = []
    for r in rows(BASE/'summary_comparison.csv'):
        v = [float(lookup[(r['geometry'], r['case_id'], m, r['algorithm'])][r['metric']]) for m in range(100)]
        actual = stats(v)
        delta = max(abs(actual[k]-float(r[k])) for k in ['mean', 'sd', 'se', 'ci95_low', 'ci95_high'])
        assert delta <= 2e-12, (r, delta)
        differences.append(dict(geometry=r['geometry'], case_id=r['case_id'], algorithm=r['algorithm'],
                                metric=r['metric'], max_abs_difference=delta, status=PASS))
    table_delta = []
    for r in rows(BASE/'table_B_probability_sweep.csv'):
        for metric in METRICS[:4]:
            v = [float(lookup[('centered', f"new_calibrated_p{float(r['p']):.1f}", m, r['algorithm'])][metric]) for m in range(100)]
            s = stats(v)
            for k in ['mean', 'sd', 'ci95_low', 'ci95_high']:
                table_delta.append(abs(s[k]-float(r[f'{metric}_{k}'])))
    for r in rows(BASE/'primary_secondary_model_comparison.csv'):
        for metric in METRICS[:4]:
            actual = np.mean([float(lookup[(r['geometry'], r['case_id'], m, r['algorithm'])][metric]) for m in range(100)])
            table_delta.append(abs(actual-float(r[metric])))
    assert max(table_delta) <= 2e-12
    write('baseline_summary_reproduction.csv', differences)
    save('baseline_reproduction.json', dict(status=PASS, summary_rows=len(differences),
        max_summary_difference=max(r['max_abs_difference'] for r in differences),
        max_table_difference=max(table_delta), mission_rows=len(data), original_runs_repeated=False))
    return lookup


def binary_prediction(rho, threshold, probability, order):
    """Plackett integral averaged over two independent Uniform means."""
    nodes, weights = np.polynomial.legendre.leggauss(order)
    z = (threshold-nodes)/3
    x, y = z[:, None], z[None, :]
    weight = weights[:, None]*weights[None, :]/4
    def density(r):
        return float(np.sum(weight*np.exp(-(x*x-2*r*x*y+y*y)/(2*(1-r*r))) /
                            (2*np.pi*np.sqrt(1-r*r))))
    excess, error = quad(density, 0, rho, epsabs=2e-13, epsrel=2e-13)
    return excess/(probability*(1-probability)), error/(probability*(1-probability))


def mathematical_validation(archive):
    G, mu, residual = [archive[k] for k in ['G_new', 'mu_new', 'epsilon_new']]
    assert G.shape == (100, 100, 30)
    np.testing.assert_array_equal(G, mu+residual)
    gamma, factor = cloud.covariance()
    eigen_min = float(np.linalg.eigvalsh(gamma).min())
    assert eigen_min > 0
    chol_error = float(np.max(abs(factor@factor.T-gamma)))
    assert chol_error < 2e-13
    output = []
    estimates = {}
    for kind, a, target in [('conditional', residual, gamma),
                            ('unconditional', G, gamma+np.eye(100)/3)]:
        # Population means are exactly zero; use unbiased known-mean cross moments.
        per_mission = np.einsum('mit,mjt->mij', a, a)/30
        estimate = per_mission.mean(axis=0)
        se = per_mission.std(axis=0, ddof=1)/10
        z = abs(estimate-target)/se
        assert float(z.max()) < 6
        estimates[kind] = estimate
        np.save(OUT/f'covariance_{kind}.npy', estimate)
        for i in range(100):
            for j in range(i, 100):
                output.append(dict(test=kind, i=i, j=j, target=target[i,j], estimate=estimate[i,j],
                    mission_cluster_se=se[i,j], standardized_error=z[i,j],
                    status=PASS, diagnostic_gate='abs(error)<=6 mission-cluster SE'))
    for kind, a, scale, mean in [('G', G, 9+1/3, 0), ('residual', residual, 9, 0),
                                ('mu', mu, 1/3, 0), ('binary', (G>0).astype(float), .25, .5)]:
        for lag in [1, 2, 5, 10]:
            v = ((a[:, :, :-lag]-mean)*(a[:, :, lag:]-mean)).mean(axis=(1,2))/scale
            s = stats(v)
            assert abs(s['mean']) <= 6*s['se']+1e-12
            family_half=float(student_t.ppf(1-.05/(2*16),99)*s['se'])
            output.append(dict(test='temporal_'+kind, lag=lag, target=0, estimate=s['mean'],
                mission_cluster_se=s['se'], ci95_low=s['ci95_low'], ci95_high=s['ci95_high'],
                bonferroni16_ci95_low=s['mean']-family_half,bonferroni16_ci95_high=s['mean']+family_half,
                standardized_error=abs(s['mean'])/s['se'], status=PASS,
                estimator='known-marginal normalized cross moment'))
    D = float(kstest(mu.ravel(), 'uniform', args=(-1,2)).statistic)
    bound = float(np.sqrt(np.log(2/1e-6)/(2*mu.size)))
    assert D < bound
    threshold_rows = []
    import mpmath as mp
    with mp.workdps(80):
        for p in [.1,.2,.3,.4,.5,.6,.7,.8]:
            threshold = cloud.calibrated_threshold(p)
            tm = mp.mpf(threshold)
            H = lambda x: x*mp.erfc(-x/mp.sqrt(2))/2+mp.exp(-x*x/2)/mp.sqrt(2*mp.pi)
            independent = float(mp.mpf('1.5')*(H((1-tm)/3)-H((-1-tm)/3)))
            assert abs(independent-p) < 1e-12
            s = stats((G>threshold).mean(axis=(1,2)))
            threshold_rows.append(dict(p=p, threshold=threshold, independent_prediction_80dps=independent,
                calibration_error=independent-p, sampling_error=s['mean']-p, **s,
                target_in_pointwise_CI=s['ci95_low']<=p<=s['ci95_high'], status=PASS))
    assert abs(cloud.blockage_probability(0)-.5) < 1e-14
    pairs = [(0,1),(0,2),(0,10),(9,10),(0,11),(0,99)]
    binary_rows = []
    for p in PROBS:
        threshold = cloud.calibrated_threshold(p)
        C = G>threshold
        for i,j in pairs:
            rho = .9**abs(i-j)
            prediction, error = binary_prediction(rho, threshold, p, 40)
            low, _ = binary_prediction(rho, threshold, p, 20)
            assert abs(prediction-low) < 1e-10
            s = stats(((C[:,i,:]-p)*(C[:,j,:]-p)).mean(axis=1)/(p*(1-p)))
            latent = stats((G[:,i,:]*G[:,j,:]).mean(axis=1)/(9+1/3))
            assert abs(s['mean']-prediction) <= 6*s['se']+1e-12
            binary_rows.append(dict(p=p, i=i, j=j, index_lag=abs(i-j), distance_m=float(np.linalg.norm(archive['positions'][i]-archive['positions'][j])),
                residual_Gaussian_correlation=rho, unconditional_G_correlation=9*rho/(9+1/3),
                empirical_G_correlation=latent['mean'], G_ci95_low=latent['ci95_low'], G_ci95_high=latent['ci95_high'],
                predicted_binary_correlation=prediction, quadrature20_40_delta=abs(prediction-low),
                pooled_binary_Pearson=float(np.corrcoef(C[:,i,:].ravel(),C[:,j,:].ravel())[0,1]),
                binary_normalized_covariance=s['mean'], binary_ci95_low=s['ci95_low'], binary_ci95_high=s['ci95_high'],
                binary_cluster_se=s['se'], status=PASS))
    write('cloud_validation_metrics.csv', output)
    write('binary_threshold_validation.csv', threshold_rows)
    write('binary_spatial_correlations.csv', binary_rows)
    code = inspect.getsource(cloud.latent)
    assert 'previous' not in code and 'rho' not in inspect.signature(cloud.latent).parameters
    save('cloud_mathematical_checks.json', dict(status=PASS, conditional_variance=9,
        unconditional_variance=9+1/3, eigenvalue_min=eigen_min, cholesky_max_error=chol_error,
        Uniform_KS_D=D, DKW_alpha_1e_minus6_bound=bound, temporal_lags=[1,2,5,10],
        missions_reused=100, new_cloud_draws=0, covariance_diagnostic_gate_SE=6,
        threshold_calibration_method='independent 80-digit normal-CDF antiderivative',
        binary_prediction_method='Plackett integral, Uniform mean Gauss-Legendre20/40 comparison',
        statistical_tests_scope='finite-sample diagnostics, no familywise covariance certification'))


def paired_statistics(lookup):
    rng = np.random.default_rng(SEED)
    indices = rng.integers(0,100,size=(10000,100))
    output = []
    for p in PROBS:
        case = f'new_calibrated_p{p:.1f}'
        for baseline_name in ['Greedy','Stationary']:
            for metric in METRICS:
                dp = np.array([float(lookup[('centered',case,m,'DP')][metric]) for m in range(100)])
                b = np.array([float(lookup[('centered',case,m,baseline_name)][metric]) for m in range(100)])
                delta = dp-b
                s = stats(delta)
                boot = delta[indices].mean(axis=1)
                lo, hi = np.quantile(boot,[.025,.975])
                direction = -1 if metric in ['zero_rate_unavailability','total_distance_m','position_changes'] else 1
                if b.mean()!=0:
                    relative = 100*direction*delta.mean()/abs(b.mean())
                    denominators = abs(b[indices].mean(axis=1))
                    valid = denominators>0
                    relative_boot = 100*direction*boot[valid]/denominators[valid]
                    rlo,rhi = np.quantile(relative_boot,[.025,.975])
                else:
                    relative=rlo=rhi=''
                    valid=np.zeros(10000,dtype=bool)
                output.append(dict(p=p,baseline=baseline_name,metric=metric,DP_mean=float(dp.mean()),baseline_mean=float(b.mean()),
                    **s,bootstrap_ci95_low=float(lo),bootstrap_ci95_high=float(hi),
                    relative_improvement_percent=relative,relative_bootstrap_ci95_low=rlo,relative_bootstrap_ci95_high=rhi,
                    relative_bootstrap_valid_replicates=int(valid.sum()),
                    distinguishable_from_zero_t_CI=s['ci95_low']>0 or s['ci95_high']<0,
                    distinguishable_from_zero_bootstrap_CI=lo>0 or hi<0,
                    method='paired Student-t primary; paired percentile bootstrap10000 secondary',seed=SEED,
                    multiplicity='pointwise exploratory; no simultaneous inference'))
    write('paired_algorithm_statistics.csv',output)
    outage=[]
    for p in PROBS:
        case=f'new_calibrated_p{p:.1f}'
        for a in alg.ALGORITHMS:
            v=np.array([float(lookup[('centered',case,m,a)]['zero_rate_unavailability']) for m in range(100)])
            count=int(np.rint((v*30).sum())); any_count=int((v>0).sum())
            outage.append(dict(p=p,algorithm=a,zero_rate_slots=count,total_slots=3000,
                missions_with_any_outage=any_count,total_missions=100,
                any_outage_probability_upper95_if_zero=float(1-.05**.01) if any_count==0 else '',
                interpretation='one-sided exact mission-level bound; slots not independent after policy selection'))
    write('zero_outage_bounds.csv',outage)


def index_maps():
    grid=np.arange(100).reshape(10,10)
    snake=grid.copy();snake[1::2]=snake[1::2,::-1]
    return dict(Row=grid.ravel(),Column=grid.T.ravel(),Serpentine=snake.ravel(),
        Random_A=np.random.default_rng(SEED).permutation(100),
        Random_B=np.random.default_rng(SEED+1).permutation(100))


def indexing(archive,lookup):
    maps=index_maps();positions=archive['positions'];K=archive['K_star_centered']
    config=read(BASE/'experiment_config.json')
    mission=dict(config['mission'],reference_distance_m=config['reference_distance_m'])
    penalty=config['lambda_ref_bits_per_use'];gamma,_=cloud.covariance()
    records=[];arrays={};executions=0;symmetry=[]
    for name,labels in maps.items():
        assert sorted(labels.tolist())==list(range(100))
        target=9*.9**abs(labels[:,None]-labels[None,:])
        np.testing.assert_array_equal(target,gamma[np.ix_(labels,labels)])
        arrays['labels_'+name]=labels
        for p in PROBS:
            case=f'new_calibrated_p{p:.1f}'
            c0=archive['C_calibrated'][list(archive['probabilities']).index(p)]
            masks=c0[:,labels,:]
            arrays[f'C_{name}_p{p}']=masks
            path_array=[]
            for m,C in enumerate(masks):
                S=(~C)*K[:,None]
                if name=='Row':
                    result=[lookup[('centered',case,m,a)] for a in alg.ALGORITHMS]
                else:
                    result,paths=alg.compare(S,C,positions,penalty,mission)
                    path_array.append(np.array([paths[a] for a in alg.ALGORITHMS]))
                    executions+=1
                for r in result:
                    record=dict(result_scope='DIAGNOSTIC_ONLY',indexing=name,p=p,mission_id=m,algorithm=r['algorithm'],
                        C_sha256=alg.digest(C),S_sha256=alg.digest(S),record_reused=name=='Row')
                    record.update({k:float(r[k]) for k in METRICS+['availability','runtime_s']})
                    assert record['C_sha256']==r['C_sha256'] and record['S_sha256']==r['S_sha256']
                    records.append(record)
            if path_array:arrays[f'paths_{name}_p{p}']=np.asarray(path_array,dtype=np.int16)
        print('Indexing complete:',name,flush=True)
    write('indexing_robustness_results.csv',records)
    grouped={}
    for r in records:grouped.setdefault((r['indexing'],r['p'],r['algorithm']),[]).append(r)
    summary=[];paired=[]
    for (name,p,a),group in grouped.items():
        for metric in METRICS:
            summary.append(dict(indexing=name,p=p,algorithm=a,metric=metric,**stats([r[metric] for r in group])))
    for name in maps:
        for p in PROBS:
            for b in ['Greedy','Stationary']:
                for metric in METRICS[:4]:
                    dp=np.array([r[metric] for r in grouped[(name,p,'DP')]])
                    baseline_values=np.array([r[metric] for r in grouped[(name,p,b)]])
                    s=stats(dp-baseline_values)
                    assert metric!='objective_U' or np.min(dp-baseline_values)>=-1e-12
                    paired.append(dict(indexing=name,p=p,baseline=b,metric=metric,**s,
                        relative_improvement_percent=(100*s['mean']*(-1 if metric in METRICS[2:4] else 1)/abs(baseline_values.mean())) if baseline_values.mean()!=0 else ''))
    by={(r['indexing'],r['p'],r['mission_id'],r['algorithm']):r for r in records}
    for p in PROBS:
        for a in alg.ALGORITHMS:
            delta=np.array([by[('Column',p,m,a)]['objective_U']-by[('Row',p,m,a)]['objective_U'] for m in range(100)])
            symmetry.append(dict(p=p,algorithm=a,maximum_abs_U_difference=float(abs(delta).max()),**stats(delta),
                explanation='Transpose preserves grid, K and constraints; physical-index argmax tie breaking need not be equivariant for Greedy'))
            if a!='Greedy':assert abs(delta).max()<1e-12
    write('indexing_summary.csv',summary);write('indexing_paired_statistics.csv',paired)
    write('indexing_transpose_symmetry.csv',symmetry)
    np.savez_compressed(OUT/'indexing_realizations.npz',**arrays)
    save('indexing_execution.json',dict(status=PASS,assignments=list(maps),probabilities=PROBS,
        independent_base_missions=100,new_independent_cloud_draws=0,new_mission_configuration_executions=executions,
        new_algorithm_calls=executions*3,reused_baseline_algorithm_records=900,
        maximum_transpose_K_difference=float(abs(K-K[maps['Column']]).max()),
        coupling='Exactly same Phase C latent label field permuted onto physical cells; law9*.9**abs(label_i-label_j) unchanged',
        mapping_seeds=[SEED,SEED+1],strict_Phase_B_ready=False))


def algorithm_tests(lookup):
    module=load_module('_phaseC_tests_read_only',BASE/'test_models.py')
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(module.ModelTests))
    assert result.wasSuccessful()
    # Noncomplete predecessor graph: exhaustive enumeration must exclude infeasible legs.
    positions=np.array([[0.,0.],[100.,0.],[200.,0.],[100.,100.]])
    distance=alg.transition_distances(positions);feasible=distance<=110
    S=np.random.default_rng(584).uniform(0,.001,(4,5));C=np.zeros_like(S,dtype=bool)
    checks=[]
    for penalty in [0.,9.468026677248516e-6,.001]:
        records,paths=alg.compare(S,C,positions,penalty,dict(slot_duration_s=20,max_speed_m_per_s=5.5,reference_distance_m=1000))
        values=[S[np.array(path),np.arange(5)].mean()-penalty*sum(distance[path[n-1],path[n]] for n in range(1,5))/1000
            for path in itertools.product(range(4),repeat=5) if all(feasible[path[n-1],path[n]] for n in range(1,5))]
        error=abs(max(values)-records[2]['objective_U']);assert error<1e-15
        checks.append(dict(penalty=penalty,feasible_paths=len(values),bruteforce_error=error))
    margins=[]
    for key,dp in lookup.items():
        if key[-1]!='DP':continue
        for b in ['Greedy','Stationary']:
            margin=float(dp['objective_U'])-float(lookup[key[:-1]+(b,)]['objective_U'])
            assert margin>=-1e-12
            margins.append(margin)
    save('algorithm_tests.json',dict(status=PASS,existing_unit_methods=result.testsRun,
        new_restricted_graph_bruteforce_cases=checks,saved_DP_inequalities=len(margins),
        minimum_margin=min(margins),failures=0,initial_position='free; no initial movement charge',
        tie_breaking='first physical array index; deterministic',maximum_step_m=300))


def source_audit_and_sensitivity():
    pool=ROOT/'results/skr_vs_zenith_eq14_v43_phaseB_61angle_diagnostic_20261024/source_pool.csv'
    winner=next(r for r in rows(pool) if r['ensemble_hash'].startswith('b083ac84'))
    payload_path=ROOT/winner['source_path'];payload=read(payload_path)
    assert sha(payload_path)==winner['source_sha256']
    # Imports source builders and the evaluator, never calls a source solver.
    physical=load_module('_phaseC_physical_helpers_no_run',BASE/'physical_map.py')
    old=physical.old;protocol=read(ROOT/'results/skr_vs_zenith_eq14_v43_phaseB_readiness_20261024/protocol.json')
    old.canonical.validate_protocol(protocol)
    source=dict(winner,VA=float.fromhex(winner['VA_hex']),nu_raw=float.fromhex(winner['nu_raw_hex']),
                C=float(winner['C']),w=float(winner['w']),classification=winner['classification'])
    source=old.historical.with_ensemble(source)
    proof=old.historical.verify_source_payload(payload,json.loads(winner['source_settings_json']))
    p,alpha=old.canonical.prior_model.helpers().validate_source(source)
    assert old.historical.input_digests(source)==json.loads(winner['input_digests_json'])
    identity=dict(ensemble_hash=source['ensemble_hash'],source_path=winner['source_path'],source_sha256=sha(payload_path),
        canonical_source_identity=winner['canonical_source_identity'],payload_cache_key=payload['cache_key'],
        VA=source['VA'],VA_hex=source['VA'].hex(),nu_raw=source['nu_raw'],nu_repo=42.5*source['nu_raw'],
        C=source['C'],w=source['w'],normalization_error=abs(float(p@abs(alpha)**2)*2-source['VA']),
        homodyne_quadrature_variance_error=abs(float(p@(2*alpha.real)**2)-source['VA']),
        source_settings=payload['source_settings'],source_implementation=payload['source_implementation'],
        classification_before=winner['classification'],classification_after=winner['classification'],
        convergence_receipts=winner['convergence_receipts'],payload_keys=list(payload),provenance_proof=proof)
    matches=[];scanned=0;skipped=0
    needles=[source['ensemble_hash'],payload['cache_key']]
    for path in sorted((ROOT/'results').rglob('*')):
        if not path.is_file() or path.suffix.lower() not in {'.json','.jsonl','.log','.txt'}:continue
        rel=path.relative_to(ROOT).as_posix()
        if OUT in path.parents or any(x in rel.lower() for x in ['heldout','held_out','held-out','finaltest','final_test','final-test','startup','manifest','physical_records','contexts/']):continue
        if path.stat().st_size>8_000_000:skipped+=1;continue
        scanned+=1
        text=path.read_text(encoding='utf-8',errors='replace')
        if any(needle in text for needle in needles):
            matches.append(dict(path=rel,sha256=sha(path),contains_ensemble_hash=needles[0] in text,
                contains_cache_key=needles[1] in text,kind='source_payload' if 'exact_source_cache' in rel else 'historical_artifact_requires_identity_bound_per_precision_rows'))
    write('winning_source_evidence_matches.csv',matches)
    identity.update(scanned_artifacts=scanned,oversize_artifacts_not_scanned=skipped,
        evidence_matches=len(matches),new_Cw_computations=0,solver_called=False,
        limitation='Identity and conventions verified; no source-bound per-precision C,w/eigenvalue/residual receipt recovered. No numerical convergence upgrade.')
    save('winning_source_audit.json',identity)
    variants=[('stored',source['C'],source['w'])]
    for delta in [1e-10,1e-8,1e-6]:
        for sign in [-1,1]:variants.append((f'C_delta_{sign*delta:+g}',source['C']+sign*delta,source['w']))
    for fraction in [.01,.1,1.]:
        for sign in [-1,1]:variants.append((f'w_relative_{sign*fraction:+g}',source['C'],source['w']*(1+sign*fraction)))
    component_sensitivity(old,source,protocol,variants)


def component_sensitivity(old,source,protocol,variants=None):
    if variants is None:
        variants=[('stored',source['C'],source['w'])]
        for delta in [1e-10,1e-8,1e-6]:
            for sign in [-1,1]:variants.append((f'C_delta_{sign*delta:+g}',source['C']+sign*delta,source['w']))
        for fraction in [.01,.1,1.]:
            for sign in [-1,1]:variants.append((f'w_relative_{sign*fraction:+g}',source['C'],source['w']*(1+sign*fraction)))
    positions=rows(BASE/'clear_sky_map_centered.csv');contexts={r['geometry_id'] for r in positions}
    evaluations=[];start=time.perf_counter()
    for geometry_id in sorted(contexts):
        context=read(BASE/f'physical_records/{geometry_id}_context.json')
        candidates=rows(BASE/f'physical_records/{geometry_id}.csv')
        competitors=[r for r in candidates if r['ensemble_hash']!=source['ensemble_hash']]
        best_other=max(competitors,key=lambda r:float(r['K_raw']));other_K=float(best_other['K_raw'])
        stored=next(r for r in candidates if r['ensemble_hash']==source['ensemble_hash'])
        baseline_K=float(stored['K_raw'])
        for scenario,C,w in variants:
            record=dict(result_scope='DIAGNOSTIC_ONLY',geometry_id=geometry_id,zenith_deg=context['zenith_deg'],
                scenario=scenario,C_input=C,w_input=w,delta_C=C-source['C'],relative_w_delta=w/source['w']-1,
                stored_K_raw=baseline_K,best_unchanged_competitor_K=other_K,
                competitor_ensemble_hash=best_other['ensemble_hash'],assumption='Only winning source perturbed; arbitrary stress sizes, not certified solver errors')
            try:
                # Provenance-checked evaluate rejects modified source moments. Only its unchanged
                # mathematical component helper is used here, with cached MI/effective channel.
                result=old.canonical.components(source['VA'],float(stored['eta_f']),float(stored['xi_f']),C,w,digits=110)
                check=old.canonical.components(source['VA'],float(stored['eta_f']),float(stored['xi_f']),C,w,digits=80)
                assert abs(result['chi_BE']-check['chi_BE'])<2e-11
                K=float(stored['beta_I_AB'])-result['chi_BE'];rank=1+sum(float(r['K_raw'])>K for r in competitors)
                record.update(K_raw=K,delta_K=K-baseline_K,positive=K>0,source_rank=rank,
                    selected_map_K=max(K,other_K,0),Z=result['Z_manuscript_eq14'],status=PASS)
                if scenario=='stored':assert abs(K-baseline_K)<2e-12
            except ValueError as error:
                record.update(status='FAILED_PHYSICALITY_OR_NUMERICAL',error=str(error))
            evaluations.append(record)
    write('source_sensitivity_evaluations.csv',evaluations)
    expanded=[]
    for position in positions:
        for r in evaluations:
            if r['geometry_id']==position['geometry_id']:
                expanded.append(dict(position_index=position['position_index'],x_m=position['x_m'],y_m=position['y_m'],**r))
    write('source_sensitivity_positions.csv',expanded)
    save('source_sensitivity_execution.json',dict(status=PASS,variants=len(variants),unique_contexts=len(contexts),
        new_channel_contexts=0,new_channel_dependent_SKR_evaluations=len(evaluations),
        new_Cw_computations=0,elapsed_seconds=time.perf_counter()-start,
        invalid_perturbation_evaluations=sum(r['status']!=PASS for r in evaluations),
        classification_unchanged=True,perturbed_values_written_to_catalog=False,
        method='Existing components at80/110 digits; cached MI and effective channel; primary provenance guard untouched',
        primary_evaluator_modified=False,source_realizability_of_perturbations_not_claimed=True))


def transpose_tie_check():
    archive=np.load(BASE/'cloud_realizations.npz');q=index_maps()['Column']
    K=archive['K_star_centered'];positions=archive['positions'];distance=alg.transition_distances(positions[q])
    assert np.array_equal(K,K[q])
    config=read(BASE/'experiment_config.json');penalty=config['lambda_ref_bits_per_use']
    lookup={(float(r['p']),int(r['mission_id']),r['algorithm']):r for r in rows(OUT/'indexing_robustness_results.csv') if r['indexing']=='Row'}
    output=[]
    for p in PROBS:
        masks=archive['C_calibrated'][list(archive['probabilities']).index(p)]
        for m,C in enumerate(masks):
            column_S=(~C[q])*K[:,None]
            ordered=column_S[q]
            path=alg.greedy(ordered,distance,distance<=300,penalty,1000)
            U=ordered[path,np.arange(30)].mean()-penalty*distance[path[:-1],path[1:]].sum()/1000
            delta=U-float(lookup[(p,m,'Greedy')]['objective_U'])
            assert abs(delta)<1e-15
            output.append(dict(p=p,mission_id=m,Greedy_U_difference_after_transpose_equivariant_tie_order=delta,status=PASS))
    write('transpose_tie_break_verification.csv',output)
    save('transpose_tie_check.json',dict(status=PASS,Greedy_verification_calls=300,
        maximum_abs_U_difference=max(abs(r['Greedy_U_difference_after_transpose_equivariant_tie_order']) for r in output),
        original_Greedy_unchanged=True,interpretation='Row/column cloud laws equivalent by transpose; observed Greedy differences arise from physical-index tie ordering'))


def verify():
    startup=read(OUT/'startup_manifest.json')
    failures=[n for n,h in startup['protected'].items() if sha(ROOT.parent/n)!=h]
    assert not failures, failures
    result=dict(status=PASS,protected_historical_files=len(startup['protected']),historical_changes=0,
                new_Cw_computations=0,PHASE_B_STRICT_READY=False,result_scope='DIAGNOSTIC_ONLY')
    if (OUT/'indexing_execution.json').exists():
        records=rows(OUT/'indexing_robustness_results.csv')
        lookup={(r['indexing'],float(r['p']),int(r['mission_id']),r['algorithm']):r for r in records}
        assert len(lookup)==len(records)==4500
        base=np.load(BASE/'cloud_realizations.npz');archive=np.load(OUT/'indexing_realizations.npz')
        positions=base['positions'];distance=alg.transition_distances(positions);K=base['K_star_centered']
        penalty=read(BASE/'experiment_config.json')['lambda_ref_bits_per_use']
        checked=0;dominance=0
        for name,labels in index_maps().items():
            np.testing.assert_array_equal(archive['labels_'+name],labels)
            for p in PROBS:
                expected=base['C_calibrated'][list(base['probabilities']).index(p)][:,labels,:]
                np.testing.assert_array_equal(expected,archive[f'C_{name}_p{p}'])
                for m,C in enumerate(expected):
                    S=(~C)*K[:,None]
                    for a in alg.ALGORITHMS:
                        r=lookup[(name,p,m,a)]
                        assert r['C_sha256']==alg.digest(C) and r['S_sha256']==alg.digest(S)
                        values=[float(r[k]) for k in METRICS]
                        assert np.isfinite(values).all()
                        if name!='Row':
                            path=archive[f'paths_{name}_p{p}'][m,alg.ALGORITHMS.index(a)]
                            legs=distance[path[:-1],path[1:]]
                            assert (legs<=300).all()
                            rates=S[path,np.arange(30)]
                            assert abs(rates.mean()-float(r['average_usable_skr']))<1e-15
                            assert abs(legs.sum()-float(r['total_distance_m']))<1e-9
                            assert abs((rates<=0).mean()-float(r['zero_rate_unavailability']))<1e-15
                            assert abs(rates.mean()-penalty*legs.sum()/1000-float(r['objective_U']))<1e-15
                            checked+=1
                    for b in ['Greedy','Stationary']:
                        assert float(lookup[(name,p,m,'DP')]['objective_U'])>=float(lookup[(name,p,m,b)]['objective_U'])-1e-12
                        dominance+=1
        result.update(indexing_paths_verified=checked,indexing_DP_inequalities_including_reused=dominance)
    if (OUT/'artifact_manifest.json').exists():
        manifest=read(OUT/'artifact_manifest.json')
        for n,h in manifest.items():assert sha(OUT/n)==h,n
        result['sealed_artifacts']=len(manifest)
    return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--phase',choices=['analysis','sensitivity','reports','figures','verify'],default='verify')
    args=parser.parse_args()
    if args.phase=='analysis':
        if (OUT/'analysis_execution.json').exists():raise FileExistsError('Completed diagnostic analysis is immutable; use verify')
        verify();begin=time.perf_counter()
        lookup=baseline()
        with np.load(BASE/'cloud_realizations.npz') as data:archive={k:data[k] for k in data.files}
        mathematical_validation(archive);paired_statistics(lookup);algorithm_tests(lookup)
        indexing(archive,lookup);transpose_tie_check();source_audit_and_sensitivity()
        save('analysis_execution.json',dict(status=PASS,result_scope='DIAGNOSTIC_ONLY',
            elapsed_seconds=time.perf_counter()-begin,seed=SEED,bootstrap_replicates=10000,
            new_Cw_computations=0,new_channel_contexts=0,PHASE_B_STRICT_READY=False,
            producer_sha256=sha(Path(__file__)),new_independent_cloud_draws=0,
            existing_PhaseC_runs_repeated=False))
        save('preservation_check.json',verify())
    elif args.phase=='sensitivity':
        physical=load_module('_phaseC_helpers_components_only',BASE/'physical_map.py')
        audit=read(OUT/'winning_source_audit.json')
        source={k:audit[k] for k in ['VA','C','w','ensemble_hash']}
        protocol=read(ROOT/'results/skr_vs_zenith_eq14_v43_phaseB_readiness_20261024/protocol.json')
        component_sensitivity(physical.old,source,protocol)
        transpose_tie_check()
    elif args.phase=='reports':
        load_module('_phaseD_reports',OUT/'write_reports.py').main()
    elif args.phase=='figures':
        load_module('_phaseD_figures',OUT/'plot_phaseD.py').main()
    else:print(json.dumps(verify(),indent=2))


if __name__=='__main__':main()
