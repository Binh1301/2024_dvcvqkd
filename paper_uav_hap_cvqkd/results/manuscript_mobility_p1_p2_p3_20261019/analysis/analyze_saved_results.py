"""Analyze immutable saved arrays; no channel, source, cloud or optimizer imports."""
from pathlib import Path
import csv
import hashlib
import json
import math
import shutil

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import spearmanr, t

OUT=Path(__file__).resolve().parent
SIM=OUT.parent
ROOT=SIM.parents[1]
METHODS=('Stationary','Greedy','DP')
TOL=1e-12
BOOTSTRAPS=20000
BOOTSTRAP_SEED=20261019


def read_csv(path):
    with Path(path).open(encoding='utf-8-sig',newline='') as stream:return list(csv.DictReader(stream))


def read_json(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save_json(name,value):
    path=OUT/name;path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')


def write_csv(name,rows):
    if not rows:return
    path=OUT/name;path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='',encoding='utf-8') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)


def describe(values):
    x=np.asarray(values,dtype=float);assert x.ndim==1 and len(x)>1 and np.isfinite(x).all()
    sd=float(x.std(ddof=1));mean=float(x.mean());half=float(t.ppf(.975,len(x)-1))*sd/math.sqrt(len(x))
    return dict(n=len(x),mean=mean,sd=sd,min=float(x.min()),p05=float(np.quantile(x,.05)),
                median=float(np.median(x)),p95=float(np.quantile(x,.95)),max=float(x.max()),
                ci95_t_low=mean-half,ci95_t_high=mean+half)


def percentage(delta,baseline):
    return float(100*delta/baseline) if baseline>TOL else None


def original_integrity():
    startup=read_json(OUT/'startup_manifest.json');changed=[]
    for name,digest in startup['protected_files'].items():
        if not (ROOT/name).is_file() or sha(ROOT/name)!=digest:changed.append(name)
    assert not set(changed)-set(startup['allowed_changed']),changed
    receipt=read_json(SIM/'validation/final_verification.json')
    assert receipt['status']=='CURRENTLY_VERIFIED_PASS'
    for name,digest in receipt['artifacts_sha256'].items():assert sha(SIM/name)==digest,name
    return dict(protected_files=len(startup['protected_files']),unchanged_files=len(startup['protected_files'])-len(changed),
                allowed_changed_files=changed,original_hashed_artifacts=len(receipt['artifacts_sha256']),
                original_final_receipt_sha256=sha(SIM/'validation/final_verification.json'))


def load_and_validate():
    protocol=read_json(SIM/'protocol.json');schedule=read_json(SIM/'mobility/lambda_schedule.json')
    positions=read_csv(SIM/'positions.csv');winners=read_csv(SIM/'p1/winners.csv')
    candidates=read_csv(SIM/'p1/candidate_evaluations.csv');metrics=read_csv(SIM/'mobility/mission_metrics.csv')
    assert [int(r['position_index']) for r in positions]==list(range(100))
    assert [int(r['position_index']) for r in winners]==list(range(100))
    xy=np.array([[float(r['x_m']),float(r['y_m'])] for r in positions]);K=np.array([float(r['K_star']) for r in winners])
    with np.load(SIM/'clouds/states.npz',allow_pickle=False) as data:C=data['blocked'];S=data['usable_skr']
    with np.load(SIM/'mobility/paths.npz',allow_pickle=False) as data:paths=data['paths'];penalties=data['lambda_values']
    assert C.shape==S.shape==(100,100,30) and C.dtype==np.bool_ and np.array_equal(S,(~C)*K[None,:,None])
    assert paths.shape==(100,10,3,30) and np.array_equal(penalties,schedule['values'])
    lookup={(int(r['realization_id']),int(r['lambda_index']),r['strategy']):r for r in metrics}
    assert len(lookup)==len(metrics)==3000 and set(lookup)=={(rid,li,m) for rid in range(100) for li in range(10) for m in METHODS}
    arrays={key:np.empty((100,10,3)) for key in ('K','D','U','availability','changes','blocked')}
    fields=dict(K='average_skr_bits_per_use',D='total_distance_m',U='objective_bits_per_use',availability='availability',changes='repositionings',blocked='blocked_slots')
    for (rid,li,method),row in lookup.items():
        si=METHODS.index(method);path=paths[rid,li,si];legs=np.linalg.norm(np.diff(xy[path],axis=0),axis=1);rates=S[rid,path,np.arange(30)]
        assert np.all(legs<=300) and np.all((path>=0)&(path<100))
        expected=dict(K=float(rates.mean()),D=float(legs.sum()),U=float(rates.mean())-penalties[li]*legs.sum()/1000,
                      availability=float(np.mean(rates>0)),changes=int(np.count_nonzero(np.diff(path))),blocked=int(C[rid,path,np.arange(30)].sum()))
        for key,value in expected.items():
            assert math.isclose(float(row[fields[key]]),value,abs_tol=TOL,rel_tol=TOL),(rid,li,method,key)
            arrays[key][rid,li,si]=value
        if method=='Greedy':assert path[0]==int(np.argmax(S[rid,:,0]))
        if method=='Stationary':assert len(set(path))==1 and math.isclose(rates.mean(),S[rid].mean(axis=1).max(),abs_tol=TOL)
    assert np.all(arrays['U'][:,:,2]>=arrays['U'][:,:,:2].max(axis=2)-TOL)
    assert np.all(np.diff(arrays['D'][:,:,2],axis=1)<=1e-9)
    assert np.all(arrays['K'][:,:,0]==arrays['K'][:,[0],0])
    # Compare independently aggregated saved metrics with the original CI tables.
    mapping=dict(average_skr_bits_per_use='K',total_distance_m='D',objective_bits_per_use='U',availability='availability',repositionings='changes',blocked_slots='blocked')
    for row in read_csv(SIM/'mobility/lambda_statistics.csv'):
        if row['metric'] not in mapping:continue
        li=int(row['lambda_index']);si=METHODS.index(row['strategy']);d=describe(arrays[mapping[row['metric']]][:,li,si])
        for new,old in [('mean','mean'),('sd','sd'),('ci95_t_low','ci95_low'),('ci95_t_high','ci95_high')]:
            assert math.isclose(d[new],float(row[old]),abs_tol=TOL,rel_tol=TOL)
    return dict(protocol=protocol,schedule=schedule,positions=positions,winners=winners,candidates=candidates,xy=xy,K=K,C=C,S=S,paths=paths,penalties=penalties,a=arrays)


def analyze_p1(data):
    rows=[];candidates=data['candidates'];summary=[]
    roster=read_csv(SIM/'source_roster.csv');source_ids={r['ensemble_hash'] for r in roster}
    maxVA=max(float(r['VA']) for r in roster if r['family']=='MB')
    for j,w in enumerate(data['winners']):
        group=[r for r in candidates if int(r['position_index'])==j]
        assert len(group)==233 and {r['ensemble_hash'] for r in group}==source_ids
        mb=sorted([r for r in group if r['family']=='MB'],key=lambda r:(-float(r['K_raw']),float(r['nu_raw']),float(r['VA']),r['ensemble_hash']))
        uniform=max((r for r in group if r['family']=='Uniform'),key=lambda r:float(r['K_raw']))
        matched=next(r for r in group if r['family']=='Uniform' and float(r['VA'])==float(w['VA']))
        assert mb[0]['ensemble_hash']==w['ensemble_hash'] and float(w['K_raw'])==float(mb[0]['K_raw'])
        k,second,u,um=map(float,(w['K_raw'],mb[1]['K_raw'],uniform['K_raw'],matched['K_raw']))
        rows.append(dict(position_index=j,j=j+1,x_m=float(w['x_m']),y_m=float(w['y_m']),distance_km=float(w['distance_km']),zenith_deg=float(w['zenith_deg']),
            MB_nu=float(w['nu_raw']),MB_VA=float(w['VA']),MB_K_raw=k,MB_K_usable=max(0,k),MB_runnerup_nu=float(mb[1]['nu_raw']),MB_runnerup_VA=float(mb[1]['VA']),
            MB_runnerup_K_raw=second,rank_gap=k-second,rank_gap_percent_of_best=100*(k-second)/k,
            Uniform_best_VA=float(uniform['VA']),Uniform_best_K_raw=u,Uniform_best_K_usable=max(0,u),
            usable_family_gain=k-max(0,u),relative_usable_family_gain_percent=None,
            matched_VA=float(w['VA']),Uniform_matched_K_raw=um,matched_raw_gain=k-um,eta_f=float(w['eta_f']),N=float(w['N']),
            I_AB_2D=float(w['I_AB_2D']),chi_BE=float(w['chi_BE']),xi_f=float(w['xi_f'])))
    for key in ('MB_K_raw','Uniform_best_K_raw','Uniform_matched_K_raw','matched_raw_gain','rank_gap','rank_gap_percent_of_best','distance_km','zenith_deg','eta_f','N','I_AB_2D','chi_BE','xi_f'):
        d={k:v for k,v in describe([r[key] for r in rows]).items() if not k.startswith('ci95')}
        summary.append(dict(quantity=key,sd_population=float(np.std([r[key] for r in rows],ddof=0)),**d))
    write_csv('tables/p1_position_details.csv',rows);write_csv('tables/p1_spatial_summary.csv',summary)
    return dict(rows=rows,summary={r['quantity']:r for r in summary},source_configurations=sorted({(r['MB_nu'],r['MB_VA']) for r in rows}),
                MB_catalog_max_VA=maxVA,Uniform_raw_negative_positions=sum(r['Uniform_best_K_raw']<0 for r in rows),
                runnerup_configurations=sorted({(r['MB_runnerup_nu'],r['MB_runnerup_VA']) for r in rows}),
                min_gap_over_two_GH_error_bounds=min(r['rank_gap'] for r in rows)/(2*.95*2e-13))


def analyze_p2(data):
    S,C,K,xy,paths=[data[k] for k in ('S','C','K','xy','paths')];A=(~C).mean(axis=2)
    ref=data['protocol']['geometry']['reference_position_index'];clearbest=int(np.argmax(K));rows=[]
    for rid in range(100):
        j=int(paths[rid,0,0,0]);a,ar=float(A[rid,j]),float(A[rid,ref]);k,kr=float(K[j]),float(K[ref])
        chosen=float(S[rid,j].mean());fixed=float(S[rid,ref].mean());gain=chosen-fixed
        byK=.5*(a+ar)*(k-kr);byA=.5*(k+kr)*(a-ar)
        assert abs(gain-byK-byA)<TOL
        means=S[rid].mean(axis=1)
        rows.append(dict(realization_id=rid,position_index=j,j=j+1,x_m=xy[j,0],y_m=xy[j,1],clear_fraction=a,clear_sky_K=k,average_usable_K=chosen,
            blocked_slots=int(C[rid,j].sum()),usable_slots=int((S[rid,j]>0).sum()),reference_position_index=ref,reference_clear_fraction=ar,
            reference_average_K=fixed,gain_vs_reference=gain,gain_vs_reference_percent=percentage(gain,fixed),
            gain_component_clear_sky=byK,gain_component_availability=byA,chosen_has_max_clear_fraction=bool(a==A[rid].max()),
            chosen_is_clear_sky_best=bool(j==clearbest),near_tied_positions_within_1e_minus12=int(np.sum(means.max()-means<=TOL))))
    frequency=[dict(position_index=j,j=j+1,x_m=xy[j,0],y_m=xy[j,1],selected_missions=sum(r['position_index']==j for r in rows),
                    selected_fraction=sum(r['position_index']==j for r in rows)/100,clear_sky_K=K[j]) for j in range(100)]
    write_csv('tables/p2_stationary_missions.csv',rows);write_csv('tables/p2_location_frequency.csv',frequency)
    gain=np.array([r['gain_vs_reference'] for r in rows]);chosen=np.array([r['average_usable_K'] for r in rows]);fixed=np.array([r['reference_average_K'] for r in rows])
    return dict(rows=rows,frequency=frequency,top_locations=sorted(frequency,key=lambda r:(-r['selected_missions'],r['position_index']))[:10],
        reference_position_index=ref,clear_sky_best_position=clearbest,unique_positions=len({r['position_index'] for r in rows}),
        chosen=describe(chosen),reference=describe(fixed),gain=describe(gain),gain_ratio_of_means_percent=percentage(gain.mean(),fixed.mean()),
        mean_clear_fraction=float(np.mean([r['clear_fraction'] for r in rows])),mean_reference_clear_fraction=float(A[:,ref].mean()),
        entirely_clear_missions=sum(r['clear_fraction']==1 for r in rows),max_availability_selected_missions=sum(r['chosen_has_max_clear_fraction'] for r in rows),
        clear_sky_best_selected_missions=sum(r['chosen_is_clear_sky_best'] for r in rows),
        mean_gain_component_clear_sky=float(np.mean([r['gain_component_clear_sky'] for r in rows])),
        mean_gain_component_availability=float(np.mean([r['gain_component_availability'] for r in rows])),
        near_tie_missions=sum(r['near_tied_positions_within_1e_minus12']>1 for r in rows))


def analyze_methods(data):
    a=data['a'];penalties=data['penalties'];method_rows=[];paired=[];mission_pairs=[]
    rng=np.random.default_rng(BOOTSTRAP_SEED)
    # Resample whole missions with common counts for all methods and penalties.
    counts=rng.multinomial(100,np.full(100,.01),size=BOOTSTRAPS).astype(float)
    deltas=[];keys=[]
    for li,penalty in enumerate(penalties):
        for si,method in enumerate(METHODS):
            row=dict(lambda_index=li,lambda_bits_per_use=float(penalty),lambda_multiplier=data['schedule']['multipliers'][li],method=method)
            for metric in a:
                row.update({metric+'_'+key:value for key,value in describe(a[metric][:,li,si]).items()})
            method_rows.append(row)
        for base in (0,1):
            for metric in ('K','U'):
                delta=a[metric][:,li,2]-a[metric][:,li,base];deltas.append(delta);keys.append((li,base,metric))
            for rid in range(100):
                dk=float(a['K'][rid,li,2]-a['K'][rid,li,base]);du=float(a['U'][rid,li,2]-a['U'][rid,li,base])
                mission_pairs.append(dict(realization_id=rid,lambda_index=li,lambda_bits_per_use=float(penalty),baseline=METHODS[base],
                    delta_K=dk,delta_U=du,delta_K_percent=percentage(dk,a['K'][rid,li,base]),delta_U_percent=percentage(du,a['U'][rid,li,base])))
    delta_matrix=np.stack(deltas,axis=1);boot_means=counts@delta_matrix/100
    for column,(li,base,metric) in enumerate(keys):
        delta=delta_matrix[:,column];den=a[metric][:,li,base];valid=den>TOL;relative=100*delta[valid]/den[valid]
        lo,hi=np.quantile(boot_means[:,column],[.025,.975])
        paired.append(dict(lambda_index=li,lambda_bits_per_use=float(penalties[li]),baseline=METHODS[base],metric=metric,**describe(delta),
            ci95_bootstrap_low=float(lo),ci95_bootstrap_high=float(hi),strict_improvement_missions=int(np.sum(delta>TOL)),
            equal_missions=int(np.sum(np.abs(delta)<=TOL)),inferior_missions=int(np.sum(delta<-TOL)),strict_fraction=float(np.mean(delta>TOL)),
            equal_fraction=float(np.mean(np.abs(delta)<=TOL)),literal_positive_missions=int(np.sum(delta>0)),
            ratio_of_means_percent=percentage(delta.mean(),den.mean()),relative_valid_missions=int(valid.sum()),
            mean_per_mission_percent=float(relative.mean()) if len(relative) else None,median_per_mission_percent=float(np.median(relative)) if len(relative) else None))
    # All original paired mean/SD/t intervals must reproduce from the same mission rows.
    old=read_csv(SIM/'mobility/paired_statistics.csv')
    for r in paired:
        metric={'K':'average_skr_bits_per_use','U':'objective_bits_per_use'}[r['metric']]
        saved=next(x for x in old if int(x['lambda_index'])==r['lambda_index'] and x['comparison']=='DP-'+r['baseline'] and x['metric']==metric)
        for new,previous in [('mean','mean'),('sd','sd'),('ci95_t_low','ci95_low'),('ci95_t_high','ci95_high')]:
            assert math.isclose(r[new],float(saved[previous]),abs_tol=TOL,rel_tol=TOL)
    write_csv('tables/method_comparison.csv',method_rows);write_csv('tables/paired_comparisons.csv',paired);write_csv('tables/mission_paired_gains.csv',mission_pairs)
    write_csv('tables/mobility_penalty_summary.csv',[{k:r[k] for k in ('lambda_index','lambda_bits_per_use','lambda_multiplier','method','K_mean','K_sd','D_mean','U_mean','availability_mean','changes_mean')} for r in method_rows])
    return dict(method_rows=method_rows,paired=paired,mission_pairs=mission_pairs)


def analyze_dynamics(data):
    a,paths,S,C,K,xy,penalties=[data[k] for k in ('a','paths','S','C','K','xy','penalties')]
    li=int(np.flatnonzero(penalties==data['schedule']['representative'])[0]);p=float(penalties[li]);A=(~C).mean(axis=2)
    gainU=a['U'][:,li,2]-a['U'][:,li,0];gainG=a['U'][:,li,2]-a['U'][:,li,1]
    large=int(np.argmax(gainU));moving=np.flatnonzero((a['D'][:,li,2]>0)&(gainU>TOL));similar=min((int(r) for r in moving),key=lambda r:(abs(gainG[r]),r))
    little=int(np.flatnonzero((np.abs(gainU)<=TOL)&(a['D'][:,li,2]==0))[0])
    selected=[('large_DP_gain',large),('similar_Greedy_DP_moving',similar),('little_mobility_benefit',little)]
    conditions=[];moves=[];representatives=[];slot_rows=[];maps=[];transitions=[];witnesses=[]
    for rid in range(100):
        p2j=int(paths[rid,li,0,0]);slot_upper=float(S[rid].max(axis=0).mean());headroom=slot_upper-a['K'][rid,li,0]
        conditions.append(dict(realization_id=rid,global_blocked_fraction=float(C[rid].mean()),spatial_clear_fraction_sd=float(A[rid].std()),
            max_clear_fraction=float(A[rid].max()),entirely_clear_positions=int(np.sum(A[rid]==1)),all_positions_blocked_slots=int(C[rid].all(axis=0).sum()),
            p2_clear_fraction=float(A[rid,p2j]),p2_K=float(a['K'][rid,li,0]),slot_oracle_upper_K=slot_upper,oracle_headroom=float(headroom),
            delta_K_DP_Stationary=float(a['K'][rid,li,2]-a['K'][rid,li,0]),delta_U_DP_Stationary=float(gainU[rid]),
            delta_U_DP_Greedy=float(gainG[rid]),DP_distance_m=float(a['D'][rid,li,2]),
            lambda0_headroom_captured_fraction=float((a['K'][rid,0,2]-a['K'][rid,0,0])/headroom) if headroom>TOL else None))
        dp=paths[rid,li,2]
        for n in range(1,30):
            before,after=int(dp[n-1]),int(dp[n])
            if before==after:continue
            distance=float(np.linalg.norm(xy[after]-xy[before]));immediate=(S[rid,after,n]-S[rid,before,n])/30-p*distance/1000
            remaining_distance=distance+float(np.linalg.norm(np.diff(xy[dp[n:]],axis=0),axis=1).sum())
            future=float((S[rid,dp[n:],np.arange(n,30)].sum()-S[rid,before,n:].sum())/30-p*remaining_distance/1000)
            assert future>=-TOL
            moves.append(dict(realization_id=rid,lambda_index=li,slot=n+1,from_position=before,to_position=after,distance_m=distance,
                from_current_blocked=bool(C[rid,before,n]),to_current_blocked=bool(C[rid,after,n]),
                immediate_objective_delta_vs_stay=float(immediate),remaining_objective_gain_vs_freeze=future,
                subsequent_gain_after_current_slot=float(future-immediate),temporarily_disadvantageous=bool(immediate<-TOL),
                future_blocked_slots_if_frozen=int(C[rid,before,n:].sum())))
        for k in range(1,10):
            for si,method in ((1,'Greedy'),(2,'DP')):
                dd=float(a['D'][rid,k,si]-a['D'][rid,k-1,si]);dk=float(a['K'][rid,k,si]-a['K'][rid,k-1,si])
                changed=np.flatnonzero(paths[rid,k,si]!=paths[rid,k-1,si]);first=int(changed[0]) if len(changed) else None
                transitions.append(dict(realization_id=rid,method=method,lower_lambda_index=k-1,upper_lambda_index=k,delta_D_m=dd,delta_K=dk,
                    delta_U=float(a['U'][rid,k,si]-a['U'][rid,k-1,si]),path_changed=bool(len(changed)),first_divergent_slot=None if first is None else first+1))
                if method=='Greedy' and dd>1e-9:
                    assert first is not None and first>0
                    before=int(paths[rid,k,si,first-1]);oldj=int(paths[rid,k-1,si,first]);newj=int(paths[rid,k,si,first])
                    dold=float(np.linalg.norm(xy[oldj]-xy[before]));dnew=float(np.linalg.norm(xy[newj]-xy[before]))
                    oldlo=float(S[rid,oldj,first]-30*penalties[k-1]*dold/1000);newlo=float(S[rid,newj,first]-30*penalties[k-1]*dnew/1000)
                    oldhi=float(S[rid,oldj,first]-30*penalties[k]*dold/1000);newhi=float(S[rid,newj,first]-30*penalties[k]*dnew/1000)
                    assert oldlo>=newlo-TOL and newhi>=oldhi-TOL
                    witnesses.append(dict(realization_id=rid,lower_lambda_index=k-1,upper_lambda_index=k,first_divergent_slot=first+1,
                        previous_position=before,lower_lambda_choice=oldj,upper_lambda_choice=newj,old_leg_m=dold,new_leg_m=dnew,
                        old_choice_score_at_lower_lambda=oldlo,new_choice_score_at_lower_lambda=newlo,
                        old_choice_score_at_upper_lambda=oldhi,new_choice_score_at_upper_lambda=newhi,
                        delta_total_distance_m=dd,delta_mean_K=dk))
    for role,rid in selected:
        for j in range(100):maps.append(dict(role=role,realization_id=rid,position_index=j,x_m=xy[j,0],y_m=xy[j,1],cloud_free_fraction=float(A[rid,j]),K_clear=K[j]))
        for si,method in enumerate(METHODS):
            path=paths[rid,li,si];row=dict(role=role,realization_id=rid,lambda_index=li,lambda_bits_per_use=p,method=method)
            row.update({key:float(values[rid,li,si]) for key,values in a.items()});row.update(initial_position=int(path[0]),final_position=int(path[-1]))
            representatives.append(row)
            for n,j in enumerate(path):slot_rows.append(dict(role=role,realization_id=rid,method=method,slot=n+1,position_index=int(j),
                x_m=xy[j,0],y_m=xy[j,1],blocked=bool(C[rid,j,n]),usable_K=float(S[rid,j,n]),global_blocked_fraction=float(C[rid,:,n].mean())))
    groups=[]
    labels={'P2_all_30_slots_clear':np.array([r['p2_clear_fraction']==1 for r in conditions]),'P2_has_blocked_slots':np.array([r['p2_clear_fraction']<1 for r in conditions]),
            'oracle_headroom_zero':np.array([r['oracle_headroom']<=TOL for r in conditions]),'oracle_headroom_positive':np.array([r['oracle_headroom']>TOL for r in conditions])}
    for name,mask in labels.items():
        if mask.sum()<2:continue
        delta=gainU[mask];groups.append(dict(group=name,missions=int(mask.sum()),mean_delta_U=float(delta.mean()),mean_delta_K=float((a['K'][:,li,2]-a['K'][:,li,0])[mask].mean()),
             strict_U_fraction=float(np.mean(delta>TOL)),mean_DP_distance_m=float(a['D'][mask,li,2].mean()),**{k:v for k,v in describe(delta).items() if k.startswith('ci95')}))
    correlations=[]
    for feature in ('global_blocked_fraction','spatial_clear_fraction_sd','entirely_clear_positions','p2_clear_fraction','oracle_headroom'):
        for target in ('delta_K_DP_Stationary','delta_U_DP_Stationary'):
            rho=float(spearmanr([r[feature] for r in conditions],[r[target] for r in conditions]).statistic)
            correlations.append(dict(feature=feature,target=target,Spearman_rho=rho,missions=100,interpretation='exploratory_association_not_causal_or_confirmatory'))
    stopping=[];frontier=[]
    for rid in range(100):
        first=int(np.flatnonzero(a['D'][rid,:,2]<=1e-9)[0])
        stopping.append(dict(realization_id=rid,first_stationary_lambda_index=first,first_stationary_lambda=float(penalties[first]),
            previous_tested_lambda=None if first==0 else float(penalties[first-1]),
            interpretation='already_stationary_at_zero' if first==0 else 'threshold_only_bracketed_by_tested_penalties'))
    for k in range(10):
        frontier.append(dict(lambda_index=k,lambda_bits_per_use=float(penalties[k]),lambda_multiplier=data['schedule']['multipliers'][k],
            DP_mean_K=float(a['K'][:,k,2].mean()),DP_mean_D=float(a['D'][:,k,2].mean()),
            K_retained_vs_lambda0_percent=float(100*a['K'][:,k,2].mean()/a['K'][:,0,2].mean()),
            distance_reduction_vs_lambda0_percent=float(100*(1-a['D'][:,k,2].mean()/a['D'][:,0,2].mean())),
            stationary_DP_missions=int(np.sum(a['D'][:,k,2]<=1e-9)),
            same_K_less_distance_vs_previous_missions=0 if k==0 else int(np.sum((np.abs(a['K'][:,k,2]-a['K'][:,k-1,2])<=TOL)&(a['D'][:,k,2]<a['D'][:,k-1,2]-1e-9)))))
    for name,rows in [('cloud_conditions',conditions),('dp_move_diagnostics',moves),('penalty_transitions',transitions),('greedy_nonmonotonic_witnesses',witnesses),
                      ('dp_stop_penalty_by_mission',stopping),('pareto_dp_summary',frontier),
                      ('representative_missions',representatives),('representative_slot_details',slot_rows),('representative_cloud_maps',maps),('cloud_condition_groups',groups),('cloud_gain_correlations',correlations)]:write_csv('tables/'+name+'.csv',rows)
    return dict(representative_lambda_index=li,selected_missions=selected,representatives=representatives,conditions=conditions,groups=groups,correlations=correlations,
        move_count=len(moves),temporarily_disadvantageous_moves=sum(r['temporarily_disadvantageous'] for r in moves),
        temporarily_disadvantageous_missions=len({r['realization_id'] for r in moves if r['temporarily_disadvantageous']}),
        moves_in_selected=[r for r in moves if r['realization_id'] in {rid for role,rid in selected}],
        greedy_nonmonotonic_transitions=len(witnesses),greedy_nonmonotonic_missions=len({r['realization_id'] for r in witnesses}),witnesses=witnesses,frontier=frontier)


def figures(data,p1,p2,methods,dynamics):
    folder=OUT/'figures';folder.mkdir(exist_ok=True);xy=data['xy']/1000;edges=np.linspace(0,1,11);colors=dict(Stationary='black',Greedy='tab:orange',DP='tab:red')
    def save(fig,name):
        fig.tight_layout()
        fig.savefig(folder/(name+'.pdf'),dpi=350);fig.savefig(folder/(name+'.png'),dpi=350);plt.close(fig)
    def heat(values,title,label,cmap='viridis',vmin=None,vmax=None):
        fig,ax=plt.subplots(figsize=(5,4));mesh=ax.pcolormesh(edges,edges,np.array(values).reshape(10,10),cmap=cmap,vmin=vmin,vmax=vmax,rasterized=False)
        bar=fig.colorbar(mesh,ax=ax,pad=.03);bar.solids.set_rasterized(False);bar.set_label(label)
        ax.set(xlabel='x (km)',ylabel='y (km)',title=title,aspect='equal',xlim=(0,1),ylim=(0,1))
        return fig,ax
    with plt.rc_context({'font.family':'serif','font.size':9,'pdf.fonttype':42,'axes.grid':False}):
        fig,ax=heat(data['K'],'A: P1 clear-sky usable SKR','K* (bits/use)');save(fig,'A_p1_spatial_skr')
        fig,ax=heat([r['selected_missions'] for r in p2['frequency']],'B: Optimal stationary location frequency','Selections in 100 missions','Blues',0,max(r['selected_missions'] for r in p2['frequency']))
        ref=p2['reference_position_index'];ax.scatter(*xy[ref],marker='x',color='tab:red',s=45,label='Predefined reference (44)');ax.legend(loc='lower right',fontsize=7);save(fig,'B_stationary_frequency')
        for ext in ('pdf','png'):shutil.copyfile(SIM/'figures'/('fig3_mobility_tradeoff.'+ext),folder/('C_mobility_tradeoff.'+ext))
        penalties=data['penalties'];linthresh=float(penalties[1]);paired=methods['paired']
        fig,ax=plt.subplots(figsize=(5.7,3.8))
        for base,color in [('Stationary','tab:blue'),('Greedy','tab:orange')]:
            rows=[r for r in paired if r['metric']=='U' and r['baseline']==base]
            mean=np.array([r['mean'] for r in rows]);low=np.array([r['ci95_bootstrap_low'] for r in rows]);hi=np.array([r['ci95_bootstrap_high'] for r in rows])
            ax.plot(penalties,mean,marker='o',ms=3,color=color,label='DP − '+base);ax.fill_between(penalties,low,hi,color=color,alpha=.17)
        ax.set_xscale('symlog',linthresh=linthresh);ax.set(xlabel='λ (bits/use)',ylabel='Mean paired ΔU (bits/use)',title='D: Objective gain; paired-bootstrap 95% CI')
        ax.ticklabel_format(axis='y',style='sci',scilimits=(0,0));ax.grid(alpha=.25);ax.legend(fontsize=8);fig.text(.5,.01,f'Base-10 symlog; linear threshold {linthresh:.6g} bits/use',ha='center',fontsize=7);fig.tight_layout(rect=(0,.05,1,1))
        fig.savefig(folder/'D_objective_improvement.pdf',dpi=350);fig.savefig(folder/'D_objective_improvement.png',dpi=350);plt.close(fig)
        li=dynamics['representative_lambda_index'];p=float(penalties[li])
        for role,rid in dynamics['selected_missions']:
            fig,ax=heat((~data['C'][rid]).mean(axis=1),f'E: Mission {rid}; λ={p:.6g} bits/use','Cloud-free fraction','Blues_r',0,1)
            ax.scatter(xy[:,0],xy[:,1],s=5,color='.4',alpha=.5)
            for si,method in enumerate(METHODS):
                path=data['paths'][rid,li,si];coords=xy[path]
                if method=='Stationary':ax.scatter(*coords[0],marker='*',s=80,color=colors[method],zorder=8,label=method)
                else:
                    ax.plot(coords[:,0],coords[:,1],color=colors[method],ls='--' if method=='Greedy' else '-',lw=2 if method=='Greedy' else 1.2,label=method)
                    ax.scatter(*coords[0],marker='o',s=30,facecolors='none',edgecolors=colors[method],zorder=9)
                    ax.scatter(*coords[-1],marker='X',s=30,color=colors[method],zorder=9)
            ax.plot([],[],'o',fillstyle='none',color='.4',label='Start');ax.plot([],[],'X',color='.4',label='End');ax.legend(loc='lower right',fontsize=6,ncol=2)
            save(fig,f'E_mission_{rid:02d}_{role}')
            fig,ax=plt.subplots(figsize=(5.5,3.2))
            for si,method in enumerate(METHODS):
                path=data['paths'][rid,li,si];rates=data['S'][rid,path,np.arange(30)]
                ax.step(np.arange(1,31),rates,where='mid',color=colors[method],ls='--' if method=='Greedy' else '-',label=method)
            ax.set(xlabel='Slot',ylabel='Usable SKR (bits/use)',title=f'Saved slot rates: mission {rid}; λ={p:.6g}');ax.grid(alpha=.25);ax.legend(fontsize=7);save(fig,f'E_slot_rates_mission_{rid:02d}')
        for metric in ('U','K'):
            fig,axes=plt.subplots(2,1,figsize=(6.4,5),sharex=True)
            for ax,base in zip(axes,(0,1)):
                values=[data['a'][metric][:,k,2]-data['a'][metric][:,k,base] for k in range(10)]
                ax.boxplot(values,tick_labels=[f'{v:g}' for v in data['schedule']['multipliers']],showfliers=True,widths=.5,flierprops={'markersize':2})
                ax.axhline(0,color='.5',lw=.6);ax.set(ylabel=f'Δ{metric} (bits/use)',title='DP − '+METHODS[base]);ax.grid(axis='y',alpha=.25)
                ax.ticklabel_format(axis='y',style='sci',scilimits=(0,0))
            axes[-1].set_xlabel('λ / λ$_{hi}$');fig.suptitle(f'F: Paired {metric} gain distributions; 100 missions',fontsize=10);fig.tight_layout(rect=(0,0,1,.95))
            fig.savefig(folder/f'F_paired_{metric}_distribution.pdf',dpi=350);fig.savefig(folder/f'F_paired_{metric}_distribution.png',dpi=350);plt.close(fig)
        fig,ax=plt.subplots(figsize=(5,3.5));x=np.array([r['oracle_headroom'] for r in dynamics['conditions']]);y=np.array([r['delta_U_DP_Stationary'] for r in dynamics['conditions']])
        points=ax.scatter(x*1e6,y*1e6,s=15,c=[r['p2_clear_fraction'] for r in dynamics['conditions']],cmap='viridis',vmin=0,vmax=1)
        bar=fig.colorbar(points,ax=ax);bar.solids.set_rasterized(False);bar.set_label('P2 cloud-free fraction')
        ax.set(xlabel='Oracle headroom (10$^{-6}$ bits/use)',ylabel='DP − Stationary ΔU (10$^{-6}$ bits/use)',title='G: Cloud diversity and mobility gain');ax.grid(alpha=.25);save(fig,'G_cloud_headroom_gain')


def self_checks():
    assert percentage(1.,0.) is None and percentage(1.,-1.) is None and percentage(1.,1e-14) is None
    assert percentage(1.,2.)==50
    d=describe([1.,2.,3.]);assert d['mean']==2 and d['sd']==1 and d['median']==2
    assert describe([0.,0.,0.])['ci95_t_high']==0
    assert abs(.5*(.8+.6)*(2.-1.)+.5*(2.+1.)*(.8-.6)-(.8*2-.6*1))<1e-15


def main():
    if (OUT/'analysis_receipt.json').exists():raise FileExistsError('Completed analysis is immutable; do not overwrite')
    self_checks();before=original_integrity();data=load_and_validate()
    p1=analyze_p1(data);p2=analyze_p2(data);methods=analyze_methods(data);dynamics=analyze_dynamics(data)
    summary=dict(status='CURRENTLY_VERIFIED_PASS',scope='SAVED_NUMERICAL_RESULTS_ONLY',security_status='UNVALIDATED_SECURITY_MODEL',
        lifecycle='NOT_READY_FOR_PUBLICATION_SCALE_RUNS',original_integrity=before,bootstrap=dict(resamples=BOOTSTRAPS,seed=BOOTSTRAP_SEED,
        unit='whole_independent_mission',method='paired percentile mean-difference CI with common resampling counts'),
        equality_absolute_tolerance=TOL,relative_denominator_minimum=TOL,p1=p1,p2=p2,methods=methods,dynamics=dynamics)
    save_json('analysis_summary.json',summary);figures(data,p1,p2,methods,dynamics)
    from write_analysis_report import write_reports
    write_reports(summary,data)
    after=original_integrity();assert before==after
    save_json('computation_validation.json',dict(status='CURRENTLY_VERIFIED_PASS',self_checks='passed',source_rows=23300,
        mission_metrics=3000,slot_values_checked=90000,paired_comparisons=40,new_cloud_missions=0,new_SKR_evaluations=0,
        new_source_moments=0,optimizer_calls=0,original_integrity=after))
    print('ANALYSIS_COMPUTED',len(methods['method_rows']),'method rows;',len(methods['paired']),'paired rows;',dynamics['selected_missions'],flush=True)


if __name__=='__main__':main()
