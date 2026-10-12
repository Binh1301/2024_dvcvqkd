"""Finalize reporting from saved artifacts only; never run AP/channel/SKR/AO."""
from collections import Counter
import json
from pathlib import Path
import sys

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
sys.path.insert(0,str(ROOT))
from scripts import run_theta10_D55_alt_opt_convergence_validation as io


def main():
    report=json.loads((OUT/'run_report.json').read_text())
    verified=json.loads((OUT/'completed_run_verification.json').read_text())
    assert verified['status']=='CURRENTLY_VERIFIED_PASS' and verified['workers_remaining']==0
    sources=io.read_csv(OUT/'new_exact_mb_sources.csv')
    rows=io.read_csv(OUT/'old_vs_new_mb_skr.csv')
    ao=io.read_csv(OUT/'alt_opt_recheck.csv')
    searches=json.loads((OUT/'cache_only_searches.json').read_text())
    missing={}
    served=Counter()
    targets={(float(r['nu_raw']).hex(),float(r['V_A']).hex()) for r in sources}
    for search in searches:
        for event in search['history']:
            value=event.get('value')
            if value is None:
                continue
            nu,va=(float(search['fixed']),float(value)) if search['variable']=='V_A' else (float(value),float(search['fixed']))
            pair=(nu.hex(),va.hex())
            if event['status']=='EXACT_SOURCE_MISSING':
                item=missing.setdefault(pair,{'nu_raw':nu,'V_A':va,'requests':0,'distances':set()})
                item['requests']+=1
                item['distances'].add(search['L_km'])
            elif event['status']=='EXACT_EVALUATED' and pair in targets:
                served[pair]+=1
    missing_rows=[{**r,'distances':json.dumps(sorted(r['distances']))} for r in missing.values()]
    io.write_csv(OUT/'remaining_missing_exact_pairs.csv',sorted(missing_rows,key=lambda r:(r['nu_raw'],r['V_A'])))
    stats={'coordinate_invocations':len(searches),'coordinate_status_counts':dict(Counter(s['status'] for s in searches)),
        'selected_AO_status_counts':dict(Counter(r['status'] for r in ao)),
        'unique_missing_exact_pairs':len(missing),'newly_closed_coordinate_searches':0,
        'new_sources_used_in_original_searches':[{'nu_raw':float(r['nu_raw']),'V_A':float(r['V_A']),
            'exact_search_evaluations':served[(float(r['nu_raw']).hex(),float(r['V_A']).hex())]} for r in sources],
        'comparison_scope':'Finite142-MB catalog only; no continuous/global optimality certificate',
        'objective_error_bound':'NOT_ESTABLISHED',
        'CPU_scope':'Aggregate Windows Job source/SKR/AO CPU plus coordinator CPU; excludes preparation and independent regression checks',
        'coordinator_sha256':io.digest(ROOT/'scripts/run_theta10_D55_mb_sleep_safe_expansion.py'),
        'artifact_reporter_sha256':io.digest(__file__)}
    assert stats['coordinate_status_counts'].get('NUMERICALLY_CLOSED_LOCAL_BRACKET',0)==0
    io.save_json(OUT/'final_scope_audit.json',stats)
    report.update(final_verification=verified,coordinate_audit=stats)
    io.save_json(OUT/'run_report.json',report)
    base=(OUT/'run_report.md').read_text()
    # Preserve the automatically generated runtime report before appending tables.
    original=OUT/'coordinator_run_report.md'
    if not original.exists():
        original.write_text(base,encoding='utf-8')
    lines=[original.read_text(),'', '## Verified source moments and runtime','',
        '| Probe | nu_raw | V_A | C | w | Wall seconds | Job CPU seconds |',
        '|---|---|---|---|---|---|---|']
    lines += ['| '+' | '.join(r[k] for k in ('batch','nu_raw','V_A','C','w','wall_seconds','cpu_seconds'))+' |' for r in sources]
    lines += ['', '## Maximum of the expanded exact MB catalog at all26 distances','',
        'All values copied directly from old_vs_new_mb_skr.csv. This is not a continuous/global optimum.', '',
        '| Link km | nu_raw | V_A | K bits/use | deltaK vs139 |', '|---|---|---|---|---|']
    lines += ['| '+' | '.join(r[k] for k in ('L_km','new_nu','new_V_A','new_K','delta_K'))+' |' for r in rows]
    lines += ['', '## Validation and remaining scope','',
        f"Independent verifier: {json.dumps(verified)}.",
        f"Original129 starts and52 final coordinate checks yield {len(searches)} total coordinate calls: {stats['coordinate_status_counts']}.",
        f"Selected statuses: {stats['selected_AO_status_counts']}; unique missing exact pairs={len(missing)}. Newly fully closed coordinate searches=0.",
        'The three requested exact point values are now available in searches, but refinement still requests unavailable neighbors.',
        'At22km (.165,5.45) improves finite numerical K by2.8628002113340045e-07; no total objective error bound establishes meaningful physical gain.',
        stats['CPU_scope']+'.',
        'Old frozen-spec hash discrepancy remains recorded; no model change or publication/training/test/threshold authorization.',
        'Full inputs, receipts, cache-only search histories and remaining_missing_exact_pairs.csv preserve reproducibility.']
    (OUT/'run_report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps(stats,indent=2))


if __name__=='__main__':
    main()
