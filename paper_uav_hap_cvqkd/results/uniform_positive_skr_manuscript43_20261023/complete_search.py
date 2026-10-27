"""Complete saved staged diagnostics; never alter old results or source caches."""
import itertools
import math
import sys
from pathlib import Path
import search as s

OUT=s.OUT
SCHEMES=s.verified.SCHEMES


def validated_sources():
    for path in (OUT/'new_exact_source/exact_source_cache').glob('*.json'):
        payload=s.read(path)
        receipt=s.read(OUT/'new_exact_source/source_receipts'/(payload['ensemble_hash']+'.json'))
        if receipt['payload_file_sha256']!=s.a.sha(path) or receipt['precision_ladder']!=[1050,1250,1450]:
            raise ValueError('Fresh source receipt or precision mismatch')
        diag=receipt['diagnostic']
        if diag['route']=='ARBITRARY_PRECISION_FALLBACK':
            if [r['digits'] for r in diag['fallback_rows']]!=[1050,1250,1450] or any(
                r['rank']!=256 or not r['resolved'] for r in diag['fallback_rows'][-2:]):
                raise ValueError('Fresh full-support convergence not evidenced')
    return s.bank(include_new=True)


def unique(rows):
    return list({x['context_id']:x for x in rows}.values())


def validate(search,row):
    if row['raw_SKR'] is None:return row
    ctx=search.context(s.geometry(row),row['channel_law'])
    c=search.source_by_hash[row['source_hash']]
    fine=s.model(c,ctx['moments'],128,129)
    checks=s.verified.selected_checks(c,fine,ctx['moments'])
    if checks['status']!='CURRENTLY_VERIFIED_PASS':raise ValueError('Selected numerical validation failed')
    difference=fine['K_raw']-row['raw_SKR']
    if abs(difference)>2e-8:raise ValueError('Selected raw rate unstable')
    result=search.row(ctx,fine,row['stage'],'')
    result.update(scheme=row.get('scheme','Optimized Uniform 256-QAM'),nu_raw=c['nu_raw'],
        validation_status='CURRENTLY_VERIFIED_PASS_SECURITY_PROVISIONAL',
        K_coarse=row['raw_SKR'],K_fine_minus_coarse=difference)
    (OUT/'selected_validation').mkdir(exist_ok=True)
    s.save(OUT/'selected_validation'/(s.key([row['context_id'],c['ensemble_hash']])+'.json'),
        dict(row=result,value=fine,validation=checks))
    return result


def compare(search,g,law,stage):
    uniform=search.optimize(g,stage,law)
    mb=[c for c in s.r.catalog() if c['family']=='MB']
    for c in mb:search.source_by_hash[c['ensemble_hash']]=c
    fixed=next(c for c in mb if c['ensemble_hash']=='01c79ae70c9aacd627a5eb0e689b0b383df80bae9d89ba17088fd81f69e34754')
    rows=[uniform,search.optimize(g,stage,law,[fixed]),search.optimize(g,stage,law,mb)]
    return [validate(search,{**row,'scheme':name}) for name,row in zip(SCHEMES,rows)]


def extend():
    if (OUT/'extension_receipt.json').exists():raise FileExistsError('Preserve completed extension')
    search=s.Search(validated_sources());rows=[]
    for diameter,sigma,angle in itertools.product([.35,.4,.45,.5,.55,.6],[.03,.1,.2],[0.,10.,20.,30.,40.,50.,60.]):
        rows.append(search.optimize((diameter,60.,.5,sigma,angle),'C_div60_extension'))
    s.save(OUT/'stage_C_extension.json',rows)
    initial=s.read(OUT/'screen_receipt.json')
    finalists=[initial['A_best'],initial['B_best'],initial['C_best'],initial['secondary_best'],s.best(rows)]
    checked=[validate(search,row) for row in finalists if row is not None]
    s.save(OUT/'initial_finalists_validated.json',checked)
    # Check the independent optical quadrature before using a secondary positive.
    ch=search.context(s.geometry(initial['secondary_best']),s.BOUNDED)['channel']
    m32=s.a.legacy.power_conserving(ch,32);m64=s.a.legacy.power_conserving(ch,64)
    errors={k:abs(m32[k]-m64[k]) for k in ['m1','mh','eta_f']}
    if max(errors.values())>2e-11:raise ValueError('Bounded width quadrature failed convergence')
    s.save(OUT/'bounded_moment_validation.json',dict(status='CURRENTLY_VERIFIED_PASS',
        order32=m32,order64=m64,residuals=errors,threshold=2e-11,
        support_upper_bound=ch['eta_atm'],M0=1.,AoA_atom=ch['P0'],
        note='Independent bounded law, not normalized or repaired Eq10'))
    s.save(OUT/'extension_receipt.json',dict(status='CURRENTLY_VERIFIED_PASS',best=s.best(rows),
        rows=len(rows),source_count=len(search.sources),producer_sha256=s.a.sha(Path(__file__))))
    print('EXTENSION',s.best(rows),flush=True)


def finish():
    if (OUT/'completion_receipt.json').exists():raise FileExistsError('Preserve completed search')
    search=s.Search(validated_sources())
    A=[search.optimize((.3,35.,1.561,.1,float(angle)),'A_final',adaptive=True) for angle in range(31)]
    B0=s.read(OUT/'stage_B_initial.json');C0=s.read(OUT/'stage_C_initial.json')+s.read(OUT/'stage_C_extension.json')
    B=[search.optimize(s.geometry(x),'B_final') for x in sorted(s.numeric(unique(B0)),key=lambda x:-x['raw_SKR'])[:16]]
    C=[]
    for diameter in [.35,.4,.45,.5,.55,.6]:
        subset=[x for x in unique(C0) if x['Dr_m']==diameter]
        C.extend(search.optimize(s.geometry(x),'C_final') for x in sorted(s.numeric(subset),key=lambda x:-x['raw_SKR'])[:4])
    primary=s.best(A+B+C+B0+C0)
    secondary0=s.read(OUT/'secondary_initial.json')
    secondary=[search.optimize(s.geometry(x),'SECONDARY_final',s.BOUNDED) for x in sorted(s.numeric(secondary0),key=lambda x:-x['raw_SKR'])[:8]]
    secondary_best=s.best(secondary)
    comparisons=[]
    for row in [primary,secondary_best]:
        comparisons.extend(compare(search,s.geometry(row),row['channel_law'],'THREE_SCHEME_FINAL'))
    law_comparison=[]
    for setting,row in [('primary_best_geometry',primary),('secondary_best_geometry',secondary_best)]:
        for law in [s.RAW,s.BOUNDED]:
            law_comparison.append(dict(**validate(search,search.optimize(s.geometry(row),'MATCHED_LAWS',law)),
                physical_setting=setting))
    zenith=[];three=[]
    gd=s.geometry(secondary_best)
    for angle in range(31):
        g=(*gd[:4],float(angle))
        rows=compare(search,g,s.BOUNDED,'SECONDARY_zenith')
        three.extend(rows);zenith.append(rows[0])
        if angle%10==0:print('FINAL SECONDARY ANGLE',angle,flush=True)
    diameters=[]
    for diameter in [.3,.35,.4,.45,.5,.55,.6]:
        for law in [s.RAW,s.BOUNDED]:
            row=search.optimize((diameter,*gd[1:]),'MATCHED_DIAMETER',law)
            diameters.append(validate(search,row))
    ablation=[]
    variants=dict(baseline=(.3,35.,1.561,.1,0.),all_improved=gd,
        revert_divergence=(.3,35.,gd[2],gd[3],0.),
        revert_jitter=(.3,gd[1],1.561,gd[3],0.),
        revert_position=(.3,gd[1],gd[2],.1,0.))
    for name,g in variants.items():
        for law in [s.RAW,s.BOUNDED]:
            ablation.append(dict(**validate(search,search.optimize(g,'MATCHED_ABLATION',law)),ablation=name))
    A=[validate(search,row) for row in A]
    leaders=[validate(search,row) for row in [s.best(A),s.best(B),s.best(C)] if row is not None]
    for name,rows in [('stage_A_final',A),('stage_B_final',B),('stage_C_final',C),
        ('three_scheme_comparison',comparisons),('secondary_zenith',zenith),
        ('three_scheme_zenith',three),('diameter_comparison',diameters),('ablation',ablation),
        ('validated_leaders',leaders),('law_comparison',law_comparison)]:
        s.save(OUT/(name+'.json'),rows);s.write(OUT/(name+'.csv'),rows)
    primary_final=next(x for x in comparisons if x['channel_law']==s.RAW and x['scheme']==SCHEMES[0])
    secondary_final=next(x for x in comparisons if x['channel_law']==s.BOUNDED and x['scheme']==SCHEMES[0])
    # Enumerate every source evaluation once; blocked channels get explicit null rates.
    all_rows=[];failures=[];channel_rows=[]
    for path in sorted((OUT/'contexts').glob('*.json')):
        ctx=s.read(path)
        channel_rows.append(dict(context_id=path.stem,geometry=ctx['geometry'],law=ctx['law'],
            moments=ctx['moments'],source_evaluations=len(ctx['evaluations']),failures=ctx['failures']))
        if not ctx['moments']['normalized_within_tolerance']:
            all_rows.append(dict(**search.row(ctx,None,'ALL_CONTEXTS','FAILED_PDF_NORMALIZATION'),family='Uniform',nu_raw=0.))
        for value in ctx['evaluations'].values():
            all_rows.append(dict(**search.row(ctx,value,'ALL_CONTEXTS',''),family=value['family'],nu_raw=value['nu_raw']))
        for value in ctx['failures'].values():
            failures.append(dict(context_id=path.stem,**value))
            c=search.source_by_hash[value['source_hash']]
            failed=search.row(ctx,None,'ALL_CONTEXTS',value['reason'])
            failed.update(VA=c['VA'],source_hash=c['ensemble_hash'],source_path=c['source_path'],
                source_sha256=c['source_sha256'],family=c['family'],nu_raw=c['nu_raw'])
            all_rows.append(failed)
    s.write(OUT/'candidate_comparison.csv',sorted(all_rows,key=lambda x:(x['raw_SKR'] is None,-(x['raw_SKR'] or 0))))
    s.save(OUT/'channel_catalog.json',channel_rows);s.save(OUT/'candidate_failures.json',failures)
    s.save(OUT/'source_catalog.json',[{k:c[k] for k in ['family','VA','nu_raw','ensemble_hash','source_path','source_sha256','C','w']}
        for c in search.source_by_hash.values()])
    gaps=[va for va in [10.,.25] if va not in {c['VA'] for c in search.sources}]
    attempts=[s.read(p) for p in (OUT/'new_exact_source').glob('python_attempt_*.json')]
    s.save(OUT/'completion_receipt.json',dict(status='CURRENTLY_VERIFIED_PASS',scope='FINITE_EXACT_TESTED_DIAGNOSTIC',
        primary_best=primary_final,secondary_best=secondary_final,uniform_source_count=len(search.sources),
        secondary_best_scope='Receiver30 optical screen, fixed at Dr.30m',
        secondary_best_all_tested=s.best([x for x in secondary+zenith+diameters+ablation if x['channel_law']==s.BOUNDED]),
        MB_source_count=197,source_gaps=gaps,source_attempts=attempts,
        requested_source_availability_status='BLOCKED_BY_ENVIRONMENT' if gaps else 'CURRENTLY_VERIFIED_PASS',
        full_VA_requested_domain_complete=not gaps,global_optimum=False,security_valid=False,
        coverage_scope='Finite exact-tested search; completeness flag means requested initial new-source points only',
        candidate_rows=len(all_rows),channel_contexts=len(channel_rows),candidate_failure_count=len(failures),
        primary_positive_found=any(x['raw_SKR'] is not None and x['raw_SKR']>0 and x['channel_law']==s.RAW
            and x['family']=='Uniform' for x in all_rows),
        secondary_positive_found=secondary_final['raw_SKR']>0,
        shaping_gain={law:next(x['raw_SKR'] for x in comparisons if x['channel_law']==law and x['scheme']==SCHEMES[2])
            -next(x['raw_SKR'] for x in comparisons if x['channel_law']==law and x['scheme']==SCHEMES[0])
            for law in [s.RAW,s.BOUNDED]},
        producer_sha256=s.a.sha(Path(__file__)),protocol_sha256=s.a.sha(OUT/'protocol.json'),
        completion_plan_sha256=s.a.sha(OUT/'completion_plan.json')))
    print('COMPLETION',s.read(OUT/'completion_receipt.json'),flush=True)


if __name__=='__main__':
    {'extend':extend,'finish':finish}[sys.argv[1]]()
