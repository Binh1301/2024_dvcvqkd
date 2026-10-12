"""ONE lower P1 source; reuse the validated source/controller/Job path verbatim."""
import time
ORIGIN = time.monotonic()
import datetime
ORIGIN_UTC = datetime.datetime.now(datetime.timezone.utc)
import argparse
from contextlib import ExitStack
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import prepare_theta10_D55_P1_lower_refinement as prep

upper, saved, prior = prep.upper, prep.saved, prep.prior
NU, VA, KEY = prep.NU, prep.VA, prep.KEY
OUT = prep.OUT / 'minimal_run'
CACHE = prep.OUT / 'exact_source_cache'
DIRS = (*prep.DIRS, CACHE)
CONTEXT = SimpleNamespace(OUT=prep.OUT, INPUT=prep.INPUT, reconcile=prep.reconcile,
    storage=prep.storage, provenance=prep.provenance, merge_source=upper.prep.merge_source)


def binding():
    # Only target, I/O paths and the fresh clock change. No evaluator/API patch.
    return patch.multiple(upper, prep=CONTEXT, NU=NU, VA=VA, KEY=KEY, OUT=OUT,
        CACHE=CACHE, DIRS=DIRS, __file__=str(Path(__file__).resolve()),
        ORIGIN=ORIGIN, ORIGIN_UTC=ORIGIN_UTC)


def main(*, approved_ap=False):
    with binding():
        return upper.main(approved_ap=approved_ap)


def source_child():
    with binding():
        return upper.source_child()  # Original source_moments and internal3600s.


def save(name, data):
    (OUT / name).write_text(prep.storage.checked_json(data), encoding='utf-8')


def csv(name, rows):
    with patch.object(saved, 'OUT', OUT):
        saved.write_csv(name, rows)


def verify():
    protected = saved.read(OUT / 'protected_input_manifest.json')
    assert all(saved.sweep.sha256(ROOT/n) == h for n,h in protected.items())
    return len(protected)


def postprocess_child():
    verify()
    prior.torch.set_num_threads(1)
    config = saved.source.unconstrained_config()
    payload = saved.read(CACHE / (KEY + '.json'))
    prep.provenance.verify_source_payload(payload, prep.provenance.source_settings(config))
    assert payload['cache_key'] == KEY and payload['support_size'] == 256
    previous = {e['L_km']:e for e in saved.read(prep.INPUT/'objective_checkpoint.json')}
    old = {float(r['L_km']):r for r in saved.rows(prep.INPUT/'optimized_skr_26_distances.csv')}
    runs, searches, checkpoints, selected, comparisons, objectives, coords = [], [], [], [], [], [], []
    metadata, warm, reference_rows = {}, None, []
    original_search = saved.ao.adaptive_maximize_1d

    def record(**kwargs):
        result = original_search(**kwargs)
        searches.append({**result, **metadata})
        return result

    with ExitStack() as guards:
        for obj,name in ((saved.ao.ExactMBEvaluator,'source_moments'),(prior.gram_moments,'_fallback'),(saved.sweep,'make_channel')):
            guards.enter_context(patch.object(obj,name,prior.preparation.forbidden))
        guards.enter_context(patch.object(saved.sweep,'adaptive_maximize_1d',record))
        for L in saved.sweep.DISTANCES_KM:
            entry = previous[L]
            objective = saved.ao.ExactObjective(config,entry['identity']['identity']['channel'],OUT,
                allow_new_source=False,source_cache_dirs=DIRS)
            assert objective.restore_objective_rows(entry['rows'],entry['identity']) == 150
            for row in entry['rows']:
                objective.register_catalog(row['nu_raw'],row['V_A'])
            new = objective(NU,VA)  # Original deterministic MI/direct-Z-minus SKR.
            assert len(objective.rows) == len(objective.catalog) == 151
            objectives.append(new)
            rank = sorted(objective.rows.values(),key=lambda r:r['SKR'],reverse=True)
            starts = [(f'nu_{n:g}',n,None) for n in saved.sweep.BASE_STARTS]
            if warm is not None:
                starts.append(('warm_previous_distance',*warm))
            local = []
            for start_id,nu,va in starts:
                metadata.update(L_km=L,start_id=start_id,role='ITERATION')
                run = saved.sweep.run_single_distance_ao(distance_km=L,start_id=start_id,
                    start_nu=nu,start_va=va,objective=objective,max_iterations=6)
                assert not run['warnings'] and run['final'] is not None
                local.append({'L_km':L,**run})
            chosen = max(local,key=lambda r:r['final']['SKR'])
            best = chosen['final']
            warm = (best['nu_raw'],best['V_A'])
            metadata.update(L_km=L,start_id=chosen['start_id'],role='SELECTED_FINAL')
            checks = [record(variable=v,fixed=f,values=objective.catalog_values(v,f),objective=objective)
                for v,f in (('V_A',warm[0]),('nu_raw',warm[1]))]
            coords.extend({**saved.audit.diagnostic({**s,'L_km':L},list(objective.rows.values())),
                'candidate_history':s['history']} for s in checks)
            match = saved.pair(*warm) == saved.pair(rank[0]['nu_raw'],rank[0]['V_A']) and best['SKR'] == rank[0]['SKR']
            selected.append({'L_km':L,'nu_raw':warm[0],'V_A':warm[1],'I_AB':best['I_AB'],
                'beta_I_AB':best['beta_I_AB'],'chi_BE':best['chi_BE'],'best_SKR':best['SKR'],
                'AO_status':chosen['status'],'selected_start':chosen['start_id'],'catalog_maximum':rank[0]['SKR'],
                'AO_matches_catalog':match,'catalog_size':151,
                'coordinate_complete':all(saved.ao.coordinate_search_complete(s) for s in checks),
                'source_cache_key':best['source_cache_key'],'scope':'GENUINE_ORIGINAL_AO_FINITE_CATALOG_ONLY'})
            comparisons.append({'L_km':L,'old_nu_raw':old[L]['nu_raw'],'old_V_A':old[L]['V_A'],
                'old_K':old[L]['best_SKR'],'new_nu_raw':warm[0],'new_V_A':warm[1],'new_K':best['SKR'],
                'delta_K':best['SKR']-float(old[L]['best_SKR']),'new_probe_K':new['SKR'],
                'AO_matches_catalog':match,'total_K_discrimination_accuracy':'NOT_ESTABLISHED'})
            runs.extend(local)
            checkpoints.append({'L_km':L,'identity':objective.objective_identity,'rows':list(objective.rows.values())})
            if L == saved.REF:
                reference_rows = sorted((r for r in objective.rows.values() if r['nu_raw'] == NU
                    and r['V_A'] in (5.49375,VA,5.5,5.50625)),key=lambda r:r['V_A'])
                assert len(reference_rows) == 4
            csv('new_exact_skr_26_distances.csv',objectives)
            csv('optimized_skr_26_distances.csv',selected)
            csv('old_vs_new_skr.csv',comparisons)
            save('objective_checkpoint.json',checkpoints)
            print(f'L={L}; K={best["SKR"]!r}; pair={warm}; catalog_match={match}',flush=True)
    save('cache_only_runs.json',runs)
    save('cache_only_searches.json',searches)
    csv('reference_P1_comparison.csv',reference_rows)
    csv('coordinate_search_status.csv',coords)
    csv('reference_P1_refinement.csv',[r for r in coords if r['L_km'] == saved.REF and r['coordinate'] == 'V_A'])
    csv('ao_iteration_history.csv',[{'L_km':r['L_km'],'start_id':r['start_id'],**it} for r in runs for it in r['iterations']])
    csv('ao_multistart_recheck.csv',[{'L_km':r['L_km'],'start_id':r['start_id'],'nu_raw':r['final']['nu_raw'],
        'V_A':r['final']['V_A'],'K':r['final']['SKR'],'status':r['status'],'iterations':len(r['iterations'])} for r in runs])
    aligned,_ = saved.audit.align_searches(runs,searches)
    save('postprocess_report.json',{'status':'COMPLETED_ORIGINAL_26DISTANCE_AO_FINITE_CATALOG_ONLY',
        'baseline_MB_sources':150,'available_MB_sources':151,'new_AP_sources':1,'fresh_SKR_evaluations':len(objectives),
        'distances':len(selected),'starts':len(runs),'iterations':sum(len(r['iterations']) for r in runs),
        'catalog_matches':sum(r['AO_matches_catalog'] for r in selected),'coordinate_searches':len(aligned),
        'coordinate_closures':sum(saved.ao.coordinate_search_complete(s) for s in aligned),
        'improved_distances':[r['L_km'] for r in comparisons if r['delta_K'] > 0],
        'reference':next(r for r in selected if r['L_km'] == saved.REF),
        'reference_new_probe':next(r for r in objectives if r['L_km'] == saved.REF),
        'reference_coordinates':[r for r in coords if r['L_km'] == saved.REF],
        'at_22_km':next(r for r in selected if r['L_km'] == 22.),'protected_count':verify(),
        'continuous_or_global_optimum_certified':False,'extra_AP_attempts':0})
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--approved-ap',action='store_true')
    parser.add_argument('--child',choices=('source','postprocess'))
    args = parser.parse_args()
    raise SystemExit({'source':source_child,'postprocess':postprocess_child}[args.child]()
        if args.child else main(approved_ap=args.approved_ap))
