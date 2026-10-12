"""Inspect every actually missing pair using stored142-catalog objectives only."""
import json
from pathlib import Path
import sys

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
sys.path.insert(0,str(ROOT))
from scripts import prepare_theta10_D55_mb_batch2 as prep


def main():
    io,ao,source=prep.io,prep.ao,prep.source
    config=source.unconstrained_config()
    checkpoints=json.loads((prep.BASE/'objective_checkpoint.json').read_text())
    missing=io.read_csv(prep.BASE/'remaining_missing_exact_pairs.csv')
    selected=io.read_csv(OUT/'selected_probes.csv')
    chosen={prep.pair(r['nu_raw'],r['V_A']) for r in selected}
    evaluator=ao.ExactMBEvaluator(config,{'T_eff':0.,'epsilon_base':.0186,'c_phi':0.},prep.BASE,
        source_cache_dir=prep.BASE/'exact_source_cache',allow_legacy_exact_import=False)
    old_attempts=json.loads((prep.previous.prior.CONT/'source_generation_ledger.json').read_text())['attempts']
    evidence=[]
    for r in missing:
        nu,va=float(r['nu_raw']),float(r['V_A'])
        identity=evaluator._source_identity(source.make_ensemble(config,'MB',nu,va),nu,va)
        history=[a for a in old_attempts if prep.pair(a['nu_raw'],a['V_A'])==prep.pair(nu,va)]
        rows=[]
        for distance in json.loads(r['distances']):
            if distance not in (20.,21.9393102292,22.,23.):
                continue
            stored=checkpoints[str(distance)]['rows']
            for variable,fixed in (('V_A',nu),('nu_raw',va)):
                fixed_key='nu_raw' if variable=='V_A' else 'V_A'
                value=va if variable=='V_A' else nu
                exact=[x for x in stored if float(x[fixed_key]).hex()==fixed.hex()]
                lower=max((x for x in exact if float(x[variable])<value),key=lambda x:float(x[variable]),default=None)
                upper=min((x for x in exact if float(x[variable])>value),key=lambda x:float(x[variable]),default=None)
                if exact:
                    rows.append({'L_km':distance,'coordinate':variable,'fixed':fixed,
                        'lower_value':lower[variable] if lower else None,'lower_K':lower['SKR'] if lower else None,
                        'upper_value':upper[variable] if upper else None,'upper_K':upper['SKR'] if upper else None,
                        'slice_best_K':max(float(x['SKR']) for x in exact),
                        'catalog142_best_K':max(float(x['SKR']) for x in stored)})
        evidence.append({**r,'nu_hex':nu.hex(),'VA_hex':va.hex(),'cache_key':source.json_hash(identity),
            'selected_provisionally':prep.pair(nu,va) in chosen,'local_exact_evidence':json.dumps(rows),
            'prior_attempts':json.dumps([{k:a.get(k) for k in ('status','wall_seconds','timeout_seconds')} for a in history]),
            'missing_objective':'UNKNOWN_NOT_INTERPOLATED'})
    assert len(evidence)==52 and len({r['cache_key'] for r in evidence})==52
    io.write_csv(OUT/'all_missing_candidate_evidence.csv',evidence)
    report=json.loads((OUT/'run_report.json').read_text())
    report.update(missing_candidates_inspected=52,selection_policy='Priority1 fixed; priorities2/3 provisional, reassess after valid new exact results/actual missing coordinate requests. Never predict missing K.',
        artifact_auditor_sha256=io.digest(__file__))
    io.save_json(OUT/'run_report.json',report)
    md=(OUT/'run_report.md').read_text()
    (OUT/'run_report.md').write_text(md+'\nAll52 missing pairs inspected; actual binary64 identities, local stored evidence and prior timeouts saved in all_missing_candidate_evidence.csv.\nPriorities2/3 remain provisional: reassess with newly measured results before committing next probe. No missing K is predicted and no dense restart is planned.\n',encoding='utf-8')
    print(json.dumps({'missing_candidates_inspected':52,'new_scientific_evaluations':0,'AP_started':False,'priority2_3_provisional':True}))


if __name__=='__main__':
    main()
