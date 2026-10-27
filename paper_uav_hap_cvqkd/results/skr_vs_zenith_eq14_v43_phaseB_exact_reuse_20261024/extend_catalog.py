"""Reuse pilot results and add other historical sources in the approved domain."""
from collections import Counter
import json
import time

from inventory import OUT,ROOT,PRIOR,STRICT,LABEL,canonical,read,rows,save,write,sha,with_ensemble
import diagnostic_model
import run

NUMERIC={'VA','nu_raw','nu_repo','C','w','eta_f','xi_f','N_effective','I_AB','beta_I_AB','chi_BE','K_raw',
    'Z_manuscript_eq14','V','W','Delta','D','nu_1','nu_2','nu_3','MI_GH64_128_difference',
    'MI_seconds','Holevo_seconds','probability_deficit','M0','E_sqrt_eta','E_eta','P0'}


def numeric_records(records):
    return [{k:(float(v) if v!='' else None) if k in NUMERIC else v for k,v in r.items()} for r in records]


def extend():
    if (OUT/'diagnostic_summary.json').exists():raise FileExistsError('Preserve completed diagnostic')
    if (OUT/'additional_candidate_results.csv').exists():raise FileExistsError('Preserve saved additional results; finish postprocessing without recalculation')
    initial=rows(OUT/('pilot_candidate_diagnostic_results.csv' if (OUT/'pilot_candidate_diagnostic_results.csv').exists() else 'diagnostic_results.csv'));assert len(initial)==720
    for name in ['diagnostic_results.csv','diagnostic_selected_schemes.csv','strict_source_evidence_results.csv',
        'incomplete_source_evidence_results.csv','strict_source_evidence_selected.csv','nine_angle_coverage.csv','selected_independent_validation.csv']:
        target='pilot_candidate_diagnostic_results.csv' if name=='diagnostic_results.csv' else 'pilot_'+name
        if not (OUT/target).exists():(OUT/target).write_bytes((OUT/name).read_bytes())
    # The candidate calculation completed; only its old NumPy scalar summary failed serialization.
    save('pilot_diagnostic_summary.json',dict(candidate_evaluations=720,angles=9,available_sources=80,
        statuses=dict(Counter(r['numerical_status'] for r in initial)),source_Cw_computations=0,
        elapsed_seconds=None,elapsed_note='Wall time not recovered after original summary serialization failure',
        source_evidence_eligible=7,source_evidence_incomplete=73,strict_Phase_B_ready=False))
    task=read(OUT/'protocol.json');protocol=read(ROOT/task['physical_protocol_path'])
    canonical.validate_protocol(protocol)
    domain=protocol['source_domain']
    inventory=rows(OUT/'exact_source_inventory.csv')
    available=[r for r in inventory if domain['VA'][0]<=float(r['VA'])<=domain['VA'][1]
               and domain['nu_raw'][0]<=float(r['nu_raw'])<=domain['nu_raw'][1]]
    assert len(available)==212
    sources=[]
    for row in available:
        source=dict(row,VA=float.fromhex(row['VA_hex']),nu_raw=float.fromhex(row['nu_raw_hex']),
            C=float(row['C']),w=float(row['w']),classification=row['source_evidence_class'])
        source=with_ensemble(source);canonical.prior_model.helpers().validate_source(source);sources.append(source)
    cached=numeric_records(initial);existing_hashes={r['ensemble_hash'] for r in cached}
    new_sources=[s for s in sources if s['ensemble_hash'] not in existing_hashes];assert len(new_sources)==132
    contexts=read(OUT/'channel_contexts.json');assert len(contexts)==9
    scope=dict(scope=LABEL,available_sources=212,required_pilot_sources=81,available_pilot_sources=80,
        source_domain=domain,physical_protocol_sha256=task['physical_protocol_sha256'],
        inventory_sha256=sha(OUT/'exact_source_inventory.csv'),pilot_candidates_sha256=sha(OUT/'pilot_candidate_diagnostic_results.csv'),
        code_sha256={n:sha(OUT/n) for n in ['extend_catalog.py','diagnostic_model.py','inventory.py','run.py']},
        source_Cw_computations=0,strict_Phase_B_ready=False,full61_sweep_authorized=False)
    save('available_catalog_protocol.json',scope)
    began=time.perf_counter();new=[]
    for context in contexts:
        angle=context['zenith_deg']
        for source in new_sources:
            record={k:source[k] for k in ['family','VA','VA_hex','nu_raw','nu_raw_hex','nu_repo','ensemble_hash','source_path','source_sha256','C','w','classification']}
            record.update(zenith_deg=angle,source_evidence_class=source['classification'],result_scope=LABEL,
                diagnostic_evidence_group='STRICT_SOURCE_EVIDENCE' if source['classification'] in STRICT else 'HISTORICAL_EXACT_EVIDENCE_INCOMPLETE',
                C_hex=source['C'].hex(),w_hex=source['w'].hex(),Cw_reused=True,source_Cw_recomputed=False,
                channel_protocol_sha256=task['physical_protocol_sha256'],diagnostic_protocol_sha256=sha(OUT/'protocol.json'),
                correlation_policy='manuscript_eq14_direct',M0=context['moments']['M0'],
                E_sqrt_eta=context['moments']['mh'],E_eta=context['moments']['m1'],P0=context['moments']['P0'])
            try:
                result=diagnostic_model.evaluate(source,context,protocol);decimals=result.pop('decimal')
                record.update(result,numerical_status='CURRENTLY_VERIFIED_PASS',reason='')
                record.update({'decimal_'+k:v for k,v in decimals.items()})
            except ValueError as error:
                record.update(numerical_status='FAILED_NUMERICAL_VALIDATION',reason=str(error),K_raw=None,
                              I_AB=None,beta_I_AB=None,chi_BE=None,Z_manuscript_eq14=None)
            new.append(record)
        print(json.dumps(dict(angle=angle,additional_sources=len(new_sources),all_available_sources=len(sources))),flush=True)
    write('additional_candidate_results.csv',new)
    combined=cached+new
    for record in combined:
        record.update(available_catalog_protocol_sha256=sha(OUT/'available_catalog_protocol.json'),
            catalog_scope='ALL_COMPATIBLE_HISTORICAL_SOURCES_IN_APPROVED_DOMAIN',
            original_pilot_member=record['ensemble_hash'] in existing_hashes)
    selected=[];strict_selected=[]
    for angle in task['angles_deg']:
        candidates=[r for r in combined if float(r['zenith_deg'])==angle]
        assert len(candidates)==212
        selected.extend(run.select(candidates,protocol));strict_selected.extend(run.select(candidates,protocol,strict=True))
    write('diagnostic_results.csv',combined)
    write('diagnostic_selected_schemes.csv',selected)
    write('strict_source_evidence_results.csv',[r for r in combined if r['source_evidence_class'] in STRICT])
    write('incomplete_source_evidence_results.csv',[r for r in combined if r['source_evidence_class'] not in STRICT])
    write('strict_source_evidence_selected.csv',strict_selected)
    old_validation=rows(OUT/'pilot_selected_independent_validation.csv')
    checked={(float(r['zenith_deg']),r['ensemble_hash']) for r in old_validation}
    new_selected=[r for r in selected+strict_selected if r['numerical_status']=='CURRENTLY_VERIFIED_PASS'
                  and (float(r['zenith_deg']),r['ensemble_hash']) not in checked]
    fresh=run.independent_selected(new_selected,sources)
    independent=old_validation+fresh;write('selected_independent_validation.csv',independent)
    by_pair={(r['ensemble_hash'],float(r['zenith_deg'])):r for r in combined}
    available_hashes={s['ensemble_hash'] for s in sources};matrix=[]
    for source in inventory:
        row={k:source[k] for k in ['family','VA','VA_hex','nu_raw','nu_raw_hex','nu_repo','ensemble_hash','C','w','source_evidence_class']}
        row.update(compatible_exact_Cw_available=True,original_pilot_member=source['ensemble_hash'] in existing_hashes,
                   inside_approved_source_domain=source['ensemble_hash'] in available_hashes)
        for angle in task['angles_deg']:
            record=by_pair.get((source['ensemble_hash'],angle))
            row[f'zenith_{angle:02d}_deg']=('EVALUATED_DIAGNOSTIC_ONLY' if record['numerical_status']=='CURRENTLY_VERIFIED_PASS' else 'NUMERICAL_VALIDATION_FAILED') if record else 'OUTSIDE_APPROVED_DOMAIN_NOT_EVALUATED'
        matrix.append(row)
    missing=next(r for r in rows(OUT/'pilot_source_coverage.csv') if r['diagnostic_eligible']=='False')
    matrix.append({**missing,'original_pilot_member':True,'inside_approved_source_domain':True,
        **{f'zenith_{a:02d}_deg':'MISSING_COMPATIBLE_SOURCE_PAYLOAD' for a in task['angles_deg']}})
    write('nine_angle_coverage.csv',matrix)
    write('sources_outside_approved_domain.csv',[r for r in inventory if r['ensemble_hash'] not in available_hashes])
    canonical.validate_protocol(protocol)
    summary=dict(result_scope=LABEL,source_inventory_count=235,available_catalog_sources=212,
        original_pilot_sources=81,original_pilot_available=80,original_pilot_missing=1,
        angles=task['angles_deg'],channel_contexts=9,candidate_evaluations=len(combined),
        pilot_candidate_results_reused=720,additional_candidate_evaluations=len(new),
        numerical_status_counts=dict(Counter(r['numerical_status'] for r in combined)),
        positive_candidate_rows=sum(r['numerical_status']=='CURRENTLY_VERIFIED_PASS' and r['K_raw']>0 for r in combined),
        negative_candidate_rows=sum(r['numerical_status']=='CURRENTLY_VERIFIED_PASS' and r['K_raw']<0 for r in combined),
        strict_source_rows=sum(r['source_evidence_class'] in STRICT for r in combined),
        incomplete_source_rows=sum(r['source_evidence_class'] not in STRICT for r in combined),
        selected_rows=len(selected),independent_selected_checks=len(independent),
        independent_validation_failures=sum(r['status']!='CURRENTLY_VERIFIED_PASS' for r in independent),
        outside_approved_source_domain=23,source_Cw_computations=0,strict_Phase_B_ready=False,
        strict_Phase_B_complete=False,full61_sweep_executed=False,
        additional_evaluations_elapsed_seconds=time.perf_counter()-began)
    save('diagnostic_summary.json',summary)
    save('finalization_provenance.json',dict(original_candidate_computation_complete=True,
        original_summary_error='NumPy int64 not JSON serializable; corrected with preserved clean helper',
        original_execution_code_snapshot='execution_producers/',original_protocol_sha256=sha(OUT/'protocol.json'),
        current_serializer_sha256=sha(OUT/'inventory.py'),candidate_recomputations_after_serialization_error=0,
        reused_pilot_candidates=720,additional_candidates=len(new),source_Cw_computations=0))
    print(json.dumps(read(OUT/'diagnostic_summary.json'),indent=2))


if __name__=='__main__':extend()
