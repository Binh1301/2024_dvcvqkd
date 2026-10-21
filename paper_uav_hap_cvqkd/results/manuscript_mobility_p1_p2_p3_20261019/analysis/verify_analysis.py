"""Independent arithmetic/provenance checks on the saved-data analysis package."""
from pathlib import Path
import csv
import hashlib
import json
import math
import re

import numpy as np
from PIL import Image

OUT=Path(__file__).resolve().parent
SIM=OUT.parent
ROOT=SIM.parents[1]


def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def rows(path):
    with Path(path).open(encoding='utf-8-sig',newline='') as stream:return list(csv.DictReader(stream))
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    checks=[]
    def check(name,condition):
        if not condition:raise AssertionError(name)
        checks.append(name)
    original=read(SIM/'validation/final_verification.json')
    for name,digest in original['artifacts_sha256'].items():check('original:'+name,sha(SIM/name)==digest)
    startup=read(OUT/'startup_manifest.json');changed=[]
    for name,digest in startup['protected_files'].items():
        if not (ROOT/name).is_file() or sha(ROOT/name)!=digest:changed.append(name)
    check('old_project_preservation',not set(changed)-set(startup['allowed_changed']))
    summary=read(OUT/'analysis_summary.json');p1=rows(OUT/'tables/p1_position_details.csv');p2=rows(OUT/'tables/p2_stationary_missions.csv')
    check('P1_positions',len(p1)==100 and [int(r['position_index']) for r in p1]==list(range(100)))
    check('P1_source_and_negative_raw',all(float(r['MB_nu'])==.125 and float(r['MB_VA'])==8 and float(r['Uniform_best_K_raw'])<0 and r['relative_usable_family_gain_percent']=='' for r in p1))
    check('P1_no_spatial_inference_CI',all(not any(k.startswith('ci95') for k in r) for r in summary['p1']['summary'].values()))
    for key in ('MB_K_raw','distance_km','zenith_deg','rank_gap'):
        values=np.array([float(r[key]) for r in p1]);s=summary['p1']['summary'][key]
        check('P1_stats:'+key,all(math.isclose(s[k],v,abs_tol=1e-16,rel_tol=1e-12) for k,v in [('mean',values.mean()),('min',values.min()),('max',values.max()),('sd_population',values.std(ddof=0))]))
    with np.load(SIM/'clouds/states.npz',allow_pickle=False) as data:S=data['usable_skr'];C=data['blocked']
    check('P2_missions',len(p2)==100 and [int(r['realization_id']) for r in p2]==list(range(100)))
    for row in p2:
        rid=int(row['realization_id']);j=int(row['position_index']);ref=44
        check('P2_metrics:'+str(rid),abs(float(row['average_usable_K'])-S[rid,j].mean())<1e-16 and
            abs(float(row['reference_average_K'])-S[rid,ref].mean())<1e-16 and int(row['blocked_slots'])==int(C[rid,j].sum()) and
            abs(float(row['gain_component_clear_sky'])+float(row['gain_component_availability'])-float(row['gain_vs_reference']))<1e-16)
    frequency=rows(OUT/'tables/p2_location_frequency.csv')
    check('P2_frequency',len(frequency)==100 and sum(int(r['selected_missions']) for r in frequency)==100)
    metrics=rows(SIM/'mobility/mission_metrics.csv');lookup={(int(r['realization_id']),int(r['lambda_index']),r['strategy']):r for r in metrics}
    paired=rows(OUT/'tables/paired_comparisons.csv');comparison=rows(OUT/'tables/method_comparison.csv')
    check('method_table_keys',len(comparison)==30 and len({(r['lambda_index'],r['method']) for r in comparison})==30)
    for row in comparison:
        li=int(row['lambda_index']);method=row['method']
        for metric,field in [('K','average_skr_bits_per_use'),('D','total_distance_m'),('U','objective_bits_per_use')]:
            values=np.array([float(lookup[rid,li,method][field]) for rid in range(100)])
            for label,value in [('mean',values.mean()),('sd',values.std(ddof=1)),('median',np.median(values)),('p05',np.quantile(values,.05)),('p95',np.quantile(values,.95))]:
                check('method:'+str(li)+method+metric+label,math.isclose(float(row[metric+'_'+label]),value,abs_tol=1e-12,rel_tol=1e-12))
    check('paired_keys',len(paired)==40 and len({(r['lambda_index'],r['baseline'],r['metric']) for r in paired})==40)
    counts=np.random.default_rng(20261019).multinomial(100,np.full(100,.01),size=20000).astype(float)
    delta_vectors=[]
    for row in paired:
        li=int(row['lambda_index']);base=row['baseline'];field={'K':'average_skr_bits_per_use','U':'objective_bits_per_use'}[row['metric']]
        a=np.array([float(lookup[rid,li,'DP'][field]) for rid in range(100)]);b=np.array([float(lookup[rid,li,base][field]) for rid in range(100)]);delta=a-b
        delta_vectors.append(delta)
        check('paired_counts:'+str(li)+base+field,int(row['strict_improvement_missions'])==int(sum(delta>1e-12)) and int(row['equal_missions'])==int(sum(np.abs(delta)<=1e-12)) and int(row['inferior_missions'])==int(sum(delta<-1e-12)))
        check('paired_mean:'+str(li)+base+field,math.isclose(float(row['mean']),float(delta.mean()),abs_tol=1e-16,rel_tol=1e-12))
        check('paired_relative:'+str(li)+base+field,math.isclose(float(row['ratio_of_means_percent']),100*delta.mean()/b.mean(),abs_tol=1e-10,rel_tol=1e-12))
    intervals=np.quantile(counts@np.stack(delta_vectors,axis=1)/100,[.025,.975],axis=0)
    check('all40_bootstrap_CIs',all(abs(float(row['ci95_bootstrap_low'])-intervals[0,k])<1e-16 and abs(float(row['ci95_bootstrap_high'])-intervals[1,k])<1e-16 for k,row in enumerate(paired)))
    representatives=rows(OUT/'tables/representative_missions.csv')
    check('representative_keys',len(representatives)==9 and {int(r['realization_id']) for r in representatives}=={0,9,84})
    with np.load(SIM/'mobility/paths.npz',allow_pickle=False) as data:paths=data['paths']
    check('similar_mission_same_paths',np.array_equal(paths[9,4,1],paths[9,4,2]))
    check('little_mission_stationary',np.array_equal(paths[0,4,0],paths[0,4,2]) and len(set(paths[0,4,2]))==1)
    moves=rows(OUT/'tables/dp_move_diagnostics.csv');witnesses=rows(OUT/'tables/greedy_nonmonotonic_witnesses.csv')
    check('moves_and_negative_immediate',len(moves)==112 and sum(r['temporarily_disadvantageous']=='True' for r in moves)==52)
    check('continuation_gain_nonnegative',all(float(r['remaining_objective_gain_vs_freeze'])>=-1e-12 for r in moves))
    check('greedy_nonmonotonic_distinct_scores',len(witnesses)==31 and all(float(r['old_choice_score_at_lower_lambda'])>=float(r['new_choice_score_at_lower_lambda'])-1e-12 and float(r['new_choice_score_at_upper_lambda'])>=float(r['old_choice_score_at_upper_lambda'])-1e-12 for r in witnesses))
    for name in ('report_analysis_vi.md','numerical_results_discussion_en.md'):
        text=(OUT/name).read_text(encoding='utf-8')
        check('scope:'+name,'UNVALIDATED_SECURITY_MODEL' in text and 'NOT_READY_FOR_PUBLICATION_SCALE_RUNS' in text)
        for link in re.findall(r'\]\(([^)]+)\)',text):check('link:'+link,(OUT/link).is_file())
    figures=[]
    for png in sorted((OUT/'figures').glob('*.png')):
        with Image.open(png) as image:check('dpi:'+png.name,min(image.info['dpi'])>=349)
        pdf=png.with_suffix('.pdf');raw=pdf.read_bytes();check('vector:'+pdf.name,raw.startswith(b'%PDF') and b'/Subtype /Image' not in raw)
        figures.append(png.stem)
    check('13_figure_pairs',len(figures)==13)
    check('visual_review',read(OUT/'visual_review.json')['status']=='CURRENTLY_VERIFIED_PASS')
    for ext in ('pdf','png'):check('original_C_copied_exactly:'+ext,sha(OUT/'figures'/('C_mobility_tradeoff.'+ext))==sha(SIM/'figures'/('fig3_mobility_tradeoff.'+ext)))
    result=dict(status='CURRENTLY_VERIFIED_PASS',saved_artifact_analysis_only=True,new_SKR_evaluations=0,optimizer_calls=0,new_cloud_missions=0,
        checks=len(checks),check_names=checks,figures=figures,protected_files=len(startup['protected_files']),
        allowed_changed_files=startup['allowed_changed'],
        preservation_policy='Only the five startup-authorized documentation ledgers may change; all other protected files must match',
        original_final_receipt_sha256=sha(SIM/'validation/final_verification.json'),
        artifact_sha256={p.relative_to(OUT).as_posix():sha(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='analysis_receipt.json' and p.suffix!='.log'})
    path=OUT/'analysis_receipt.json'
    if path.exists():check('existing_receipt_immutable',read(path)==result)
    else:path.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('ANALYSIS_VERIFIED',result['checks'],'checks;',len(figures),'figure pairs; original artifacts unchanged')


if __name__=='__main__':main()
