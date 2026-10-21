"""Consolidate immutable saved outputs; no production scientific/optimizer imports."""
from pathlib import Path
import csv
import hashlib
import json

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator, FixedLocator, ScalarFormatter
import numpy as np

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
BASE=ROOT/'results/manuscript_mobility_p1_p2_p3_20261019'
A=ROOT/'results/mobility_parameter_sensitivity_20261020'
B=ROOT/'results/mobility_parameter_sensitivity_stage_b_20261020'
LAM=9.468026677248516e-6
METHODS=('Stationary','Greedy','DP')
METRICS=('K','U','D','availability','unavailability_percent','repositionings','blocked_slots','positive_slots')
STYLE={'Stationary':dict(color='tab:blue',linestyle='-',marker='o'),
       'Greedy':dict(color='tab:orange',linestyle='--',marker='D'),
       'DP':dict(color='tab:red',linestyle='-',marker='^')}
LABEL={'Stationary':'Stationary (P2)','Greedy':'Greedy','DP':'Dynamic Programming (P3)'}
NAMES=('fig1_candidate_positions','fig2_cloud_blockage','fig3_temporal_correlation','fig4_skr_mobility_tradeoff')


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def js(p):return json.loads(p.read_text(encoding='utf-8'))
def rows(p):
    with p.open(encoding='utf-8-sig',newline='') as stream:return list(csv.DictReader(stream))
def save_csv(name,data):
    with (OUT/name).open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(data[0]));writer.writeheader();writer.writerows(data)
def save_json(name,data):(OUT/name).write_text(json.dumps(data,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8',newline='\n')


def authenticate():
    bindings={};receipts=[]
    for path,folder,field in ((BASE/'validation/final_verification.json',BASE,'artifacts_sha256'),
          (BASE/'analysis/analysis_receipt.json',BASE/'analysis','artifact_sha256'),
          (BASE/'analysis/comparison_figures/validation_receipt.json',BASE/'analysis/comparison_figures','artifact_sha256'),
          (A/'validation/final_receipt.json',A,'artifact_sha256'),
          (A/'analysis/figure_report_review_20261020/validation_receipt.json',A/'analysis/figure_report_review_20261020','artifact_sha256'),
          (B/'validation/final_receipt.json',B,'artifact_sha256')):
        r=js(path);assert r['status']=='CURRENTLY_VERIFIED_PASS',path
        receipts.append(dict(path=path.relative_to(ROOT).as_posix(),sha256=sha(path),members=len(r[field])))
        bindings[path.relative_to(ROOT).as_posix()]=sha(path)
        for n,h in r[field].items():
            assert sha(folder/n)==h,n;bindings[(folder/n).relative_to(ROOT).as_posix()]=h
        for n,h in r.get('producer_sha256',{}).items():assert sha(ROOT/n)==h,n;bindings[n]=h
    for manifest in (A/'input_manifest.json',B/'input_manifest.json'):
        for n,h in js(manifest)['bindings'].items():assert sha(ROOT/n)==h,n;bindings[n]=h
    refs={
        'manuscript':Path('C:/Users/HP/Downloads/2026__Binh_s_work__Copy___Copy_ (9).pdf'),
        'gong':Path('C:/Users/HP/Downloads/Network_Availability_Maximization_for_Free-Space_Optical_Satellite_Communications.pdf'),
        'request':Path('C:/Users/HP/.codex/attachments/0dc017fa-98f7-436e-8fdd-24f37d0aa13b/Pasted text.txt')}
    assert sha(refs['manuscript'])==js(BASE/'protocol.json')['manuscript_sha256']
    record=dict(status='CURRENTLY_VERIFIED_PASS',bindings=bindings,receipts=receipts,
                external_inputs={k:dict(path=str(p),sha256=sha(p)) for k,p in refs.items()},
                scope='Saved data only;zero optimization,quantum/channel/source/cloud-generation calls;no RNG draws')
    save_json('input_manifest.json',record)
    (OUT/'request.txt').write_bytes(refs['request'].read_bytes())
    return record


def describe(v,weights):
    boot=weights@v
    return dict(mean=float(v.mean()),sd=float(v.std(ddof=1)),median=float(np.median(v)),
                ci95_low=float(np.quantile(boot,.025)),ci95_high=float(np.quantile(boot,.975)))


def build_data():
    if (OUT/'validation/final_receipt.json').exists():raise FileExistsError('Completed package is immutable')
    authenticate();pa=js(A/'protocol.json');pb=js(B/'protocol.json');parent=js(BASE/'protocol.json')
    selections=[]
    for figure,axis,proto,source in ((1,'J',pa,A),(2,'probability',pb,B),(3,'temporal',pb,B)):
        for m in sorted([r for r in proto['memberships'] if r['axis']==axis],key=lambda r:r['value']):
            selections.append(dict(figure=figure,axis=axis,value=m['value'],case_id=m['case_id'],lambda_index=1,lambda_bits_per_use=LAM,source=source.relative_to(ROOT).as_posix()))
    schedule=js(BASE/'mobility/lambda_schedule.json')
    for li,lam in enumerate(schedule['values']):selections.append(dict(figure=4,axis='lambda',value=lam,case_id='base',lambda_index=li,lambda_bits_per_use=lam,source=BASE.relative_to(ROOT).as_posix()))
    save_csv('tables/configurations.csv',selections)
    protocol=dict(scope='FINAL_SAVED_DATA_ANALYSIS_ONLY',selected_figures=list(NAMES),settings=parent,
                  representative_lambda=LAM,configurations=selections,style=STYLE,figure_width_inches=7.2,png_dpi=350,
                  no_solver=True,no_cloud_generation=True,no_quantum_evaluation=True,no_new_parameter_points=True,
                  uncertainty='Reuse Stage A/B bootstrap summaries;reconstruct missing tradeoff mean CIs from stored Stage A count vectors;reuse original tradeoff paired CIs(seed20261019)',
                  security_status='UNVALIDATED_SECURITY_MODEL',lifecycle='NOT_READY_FOR_PUBLICATION_SCALE_RUNS')
    save_json('protocol.json',protocol)
    with np.load(A/'existing_data/bootstrap_counts.npz',allow_pickle=False) as z:counts=z['counts']
    assert counts.shape==(20000,100) and np.all(counts.sum(axis=1)==100)
    weights=counts.astype(float)/100
    current={source:{(r['case_id'],int(r['realization_id']),int(r['lambda_index']),r['method']):r for r in rows(source/('existing_data/mission_metrics.csv' if source==A else 'mobility/mission_metrics.csv'))} for source in (A,B)}
    summaries={source:{(r['case_id'],int(r['lambda_index']),r['method']):r for r in rows(source/('existing_data/aggregate_statistics.csv' if source==A else 'mobility/aggregate_statistics.csv'))} for source in (A,B)}
    pairs={source:{(r['case_id'],int(r['lambda_index']),r['baseline'],r['metric']):r for r in rows(source/('existing_data/paired_improvements.csv' if source==A else 'mobility/paired_improvements.csv'))} for source in (A,B)}
    original={(int(r['realization_id']),int(r['lambda_index']),r['strategy']):r for r in rows(BASE/'mobility/mission_metrics.csv')}
    oldpairs={(int(r['lambda_index']),r['baseline'],r['metric']):r for r in rows(BASE/'analysis/comparison_figures/paired_improvements.csv')}
    raw=[];statistics=[];contrasts=[]
    for selection in selections:
        f,cid,li=selection['figure'],selection['case_id'],selection['lambda_index'];source=ROOT/selection['source']
        values=np.empty((100,3,8))
        for rid in range(100):
            for si,method in enumerate(METHODS):
                if f==4:
                    r=original[rid,li,method];data=dict(K=float(r['average_skr_bits_per_use']),U=float(r['objective_bits_per_use']),D=float(r['total_distance_m']),
                        availability=float(r['availability']),unavailability_percent=100*(1-float(r['availability'])),repositionings=float(r['repositionings']),blocked_slots=float(r['blocked_slots']),positive_slots=float(r['positive_slots']))
                else:data={key:float(current[source][cid,rid,li,method][key]) for key in METRICS}
                values[rid,si]=[data[k] for k in METRICS]
                raw.append(dict(figure=f,case_id=cid,parameter_value=selection['value'],lambda_index=li,lambda_bits_per_use=selection['lambda_bits_per_use'],realization_id=rid,method=method,**data,source=selection['source']))
        for si,method in enumerate(METHODS):
            for ki,metric in enumerate(METRICS):
                if f==4:
                    stats=describe(values[:,si,ki],weights);origin='Reconstructed from saved missions and existing Stage A bootstrap counts'
                else:
                    r=summaries[source][cid,li,method];stats={n:float(r[metric+'_'+n]) for n in ('mean','sd','median','ci95_low','ci95_high')};origin='Reused verified Stage A/B summary'
                statistics.append(dict(figure=f,case_id=cid,parameter_value=selection['value'],lambda_index=li,lambda_bits_per_use=selection['lambda_bits_per_use'],method=method,metric=metric,valid_missions=100,**stats,ci_method='pointwise percentile bootstrap',bootstrap_seed=20261020,bootstrap_resamples=20000,source=selection['source'],ci_origin=origin))
        for baseline in METHODS[:2]:
            for metric in ('K','U','D','availability'):
                origin='Reused verified paired CI;ratio CI blank where not stored'
                if f==4 and (li,baseline,metric) in oldpairs:
                    r=oldpairs[li,baseline,metric];stats={n:float(r[n]) for n in ('mean','sd','median')};stats.update(ci95_low=float(r['ci95_bootstrap_low']),ci95_high=float(r['ci95_bootstrap_high']))
                    signs=[int(r[k]) for k in ('strict_improvement_missions','equal_missions','inferior_missions')];ratio=r['ratio_of_means_percent'];ratio_low=ratio_high='';seed=20261019
                elif f==4:
                    bi=METHODS.index(baseline);ki=METRICS.index(metric);delta=values[:,2,ki]-values[:,bi,ki]
                    stats=describe(delta,weights);tol=1e-9 if metric=='D' else 1e-12
                    signs=[int(np.sum(delta>tol)),int(np.sum(abs(delta)<=tol)),int(np.sum(delta<-tol))]
                    ratio=ratio_low=ratio_high='';seed=20261020;origin='Reconstructed missing paired CI from saved missions and existing count vectors'
                else:
                    r=pairs[source][cid,li,baseline,metric];stats={n:float(r[n]) for n in ('mean','sd','median','ci95_low','ci95_high')}
                    signs=[int(r[k]) for k in ('strict_positive','ties','negative')];ratio=r['ratio_of_means_percent'];ratio_low=r['ratio_ci95_low'];ratio_high=r['ratio_ci95_high'];seed=20261020
                contrasts.append(dict(figure=f,case_id=cid,parameter_value=selection['value'],lambda_index=li,lambda_bits_per_use=selection['lambda_bits_per_use'],baseline=baseline,metric=metric,valid_missions=100,**stats,strict_positive=signs[0],ties=signs[1],negative=signs[2],ratio_of_means_percent=ratio,ratio_ci95_low=ratio_low,ratio_ci95_high=ratio_high,bootstrap_seed=seed,bootstrap_resamples=20000,source=selection['source'],ci_origin=origin))
    save_csv('tables/selected_missions.csv',raw);save_csv('tables/statistical_comparison.csv',statistics);save_csv('tables/paired_improvements.csv',contrasts)
    summary_index={(r['figure'],r['case_id'],r['lambda_index'],r['method'],r['metric']):r for r in statistics}
    pair_index={(r['figure'],r['case_id'],r['lambda_index'],r['baseline'],r['metric']):r for r in contrasts}

    cases={r['case_id']:i for i,r in enumerate(pb['cases'])}
    with np.load(B/'clouds/states.npz',allow_pickle=False) as z:C=z['blocked']
    with np.load(B/'mobility/paths.npz',allow_pickle=False) as z:paths=z['paths']
    def longest_clear(row):
        best=current_run=0
        for blocked in row:
            current_run=0 if blocked else current_run+1;best=max(best,current_run)
        return best
    temporal=[];spatial=[]
    for m in pb['memberships']:
        if m['axis'] not in ('temporal','spatial'):continue
        ci=cases[m['case_id']]
        for rid in range(100):
            cloud=C[ci,rid];stationary=paths[ci,rid,1,0];dp=paths[ci,rid,1,2];dp_row=current[B][m['case_id'],rid,1,'DP'];p2_row=current[B][m['case_id'],rid,1,'Stationary']
            shared=dict(case_id=m['case_id'],parameter_value=m['value'],realization_id=rid,
                        global_blockage_fraction=float(cloud.mean()),stationary_clear_fraction=float((~cloud[stationary[0]]).mean()),
                        all_horizon_clear_positions=int(np.all(~cloud,axis=1).sum()),global_temporal_switch_fraction=float(np.not_equal(cloud[:,1:],cloud[:,:-1]).mean()),
                        stationary_longest_clear_run_slots=longest_clear(cloud[stationary[0]]),stationary_cell_switches=int(np.count_nonzero(np.diff(cloud[stationary[0]]))),
                        DP_repositionings=int(np.count_nonzero(np.diff(dp))),DP_moving_mission=int(np.any(np.diff(dp))),DP_distance=float(dp_row['D']),
                        DP_minus_P2_U=float(dp_row['U'])-float(p2_row['U']),unavoidable_all_sites_blocked_fraction=float(np.all(cloud,axis=0).mean()),
                        stationary_availability=float(p2_row['availability']),DP_availability=float(dp_row['availability']))
            (temporal if m['axis']=='temporal' else spatial).append(shared)
    for label,data in (('temporal',temporal),('spatial',spatial)):
        save_csv('tables/'+label+'_evidence_missions.csv',data);summ=[]
        for value in sorted({r['parameter_value'] for r in data}):
            group=[r for r in data if r['parameter_value']==value]
            for key in group[0]:
                if key in ('case_id','parameter_value','realization_id'):continue
                v=np.array([r[key] for r in group],float);summ.append(dict(parameter_value=value,metric=key,valid_missions=100,**describe(v,weights)))
        save_csv('tables/'+label+'_evidence_summary.csv',summ)
    probability=[]
    for selection in [r for r in selections if r['figure']==2]:
        cid=selection['case_id'];gp=np.array([float(current[B][cid,rid,1,'Greedy']['U'])-float(current[B][cid,rid,1,'Stationary']['U']) for rid in range(100)])
        den=np.array([float(current[B][cid,rid,1,'Stationary']['U']) for rid in range(100)]);valid=den.mean()>1e-12
        delta=pair_index[2,cid,1,'Stationary','U'];r=dict(probability=selection['value'],DP_minus_P2_U=delta['mean'],DP_minus_P2_U_ci95_low=delta['ci95_low'],DP_minus_P2_U_ci95_high=delta['ci95_high'],DP_gain_U_percent=delta['ratio_of_means_percent'])
        for method in METHODS:
            for key in ('K','U','unavailability_percent'):
                r[method+'_'+key]=summary_index[2,cid,1,method,key]['mean']
        r.update({'Greedy_minus_P2_U_'+key:value for key,value in describe(gp,weights).items()});r['Greedy_gain_U_percent']=100*float(gp.mean())/float(den.mean()) if valid else None
        probability.append(r)
    save_csv('tables/cloud_probability_discussion.csv',probability)
    effects=[r for r in rows(A/'existing_data/parameter_effects.csv') if r['axis'] in ('J','speed','horizon')]+rows(B/'mobility/parameter_effects.csv')
    save_csv('tables/parameter_effects.csv',effects)
    winners=rows(BASE/'p1/winners.csv');assert len(winners)==100
    assert {(r['family'],float(r['nu_raw']),float(r['VA'])) for r in winners}=={('MB',.125,8.)}
    Kmap=np.array([float(r['K_star']) for r in winners])
    default={m:{k:summary_index[2,'base',1,m,k]['mean'] for k in METRICS} for m in METHODS}
    default_gain={baseline:{key:100*(default['DP'][key]-default[baseline][key])/default[baseline][key] for key in ('K','U')} for baseline in METHODS[:2]}
    references={('Stationary','K'):4.16,('Greedy','K'):2.70,('Stationary','U'):3.07,('Greedy','U'):4.42}
    assert all(round(default_gain[m][k],2)==expected for (m,k),expected in references.items())
    save_json('verified_findings.json',dict(default=default,default_gain_percent=default_gain,P1=dict(sources=233,MB=197,Uniform=36,selected_nu=.125,selected_VA=8,selected_ensemble_hashes=sorted({r['ensemble_hash'] for r in winners}),K_min=float(Kmap.min()),K_max=float(Kmap.max())),
              temporal_summary=[r for r in rows(OUT/'tables/temporal_evidence_summary.csv') if r['parameter_value'] in ('0','0.98')],new_optimizer_calls=0,new_clouds=0,new_quantum_evaluations=0))
    render(selections,summary_index)
    return selections


def render(selections,summary):
    points=[];meta={}
    def srow(selection,method,metric):return summary[selection['figure'],selection['case_id'],selection['lambda_index'],method,metric]
    def configure(ax,xlabel,ylabel,scientific=False):
        ax.set_xlabel(xlabel);ax.set_ylabel(ylabel);ax.set_axisbelow(True)
        ax.grid(color='.84',lw=.5);ax.grid(which='minor',color='.94',lw=.35);ax.yaxis.set_minor_locator(AutoMinorLocator(2))
        if scientific:
            sf=ScalarFormatter(useMathText=True);sf.set_powerlimits((0,0));sf.set_useOffset(False);ax.yaxis.set_major_formatter(sf)
    def draw(f,panel,ax,group,method,metric,xmetric=None):
        data=[srow(r,method,metric) for r in group];xx=[r['value'] for r in group] if xmetric is None else [srow(r,method,xmetric)['mean'] for r in group]
        y=[r['mean'] for r in data];lo=[r['ci95_low'] for r in data];hi=[r['ci95_high'] for r in data]
        reference=f==4 and method=='Stationary'
        style=STYLE[method];line=ax.plot(xx,y,lw=1.9,ms=8 if reference else 5.4,mfc='none' if reference else 'white',mew=1.1,label=LABEL[method],zorder=6 if reference else 4,**style)[0]
        if xmetric is None:ax.fill_between(xx,lo,hi,color=style['color'],alpha=.10,lw=0)
        else:
            xdata=[srow(r,method,xmetric) for r in group]
            ax.errorbar(xx,y,xerr=[[x-r['ci95_low'] for x,r in zip(xx,xdata)],[r['ci95_high']-x for x,r in zip(xx,xdata)]],
                        yerr=[[v-l for v,l in zip(y,lo)],[h-v for h,v in zip(hi,y)]],fmt='none',ecolor=style['color'],alpha=.25,elinewidth=.6,capsize=1.5,zorder=1)
        for i,(x,yy) in enumerate(zip(line.get_xdata(),line.get_ydata())):
            row=group[i];points.append(dict(figure=f,panel=panel,case_id=row['case_id'],parameter_value=row['value'],lambda_index=row['lambda_index'],lambda_bits_per_use=row['lambda_bits_per_use'],method=method,metric=metric,x_metric=xmetric or row['axis'],point_index=i,x=float(x),y=float(yy),ci95_low=lo[i],ci95_high=hi[i],
                x_ci95_low=srow(row,method,xmetric)['ci95_low'] if xmetric else '',x_ci95_high=srow(row,method,xmetric)['ci95_high'] if xmetric else '',color=style['color'],marker=style['marker'],linestyle=style['linestyle'],source='tables/statistical_comparison.csv'))
    def finish(fig,axs,f):
        for panel,ax in enumerate(axs,1):
            pp=[p for p in points if p['figure']==f and p['panel']==panel];bounds=[p[k] for p in pp for k in ('y','ci95_low','ci95_high')];lo=min(0,min(bounds));hi=max(bounds);span=max(hi-lo,1e-12);ax.set_ylim(lo-.04*span,hi+.13*span)
        handles,labels=axs[0].get_legend_handles_labels();fig.legend(handles,labels,loc='upper center',bbox_to_anchor=(.54,.99),ncol=3,frameon=False,fontsize=8)
        note='100 paired missions; pointwise 95% bootstrap CI; λ = λref' if f<4 else '100 paired missions; points connected in saved λ order; pointwise 95% CI'
        fig.text(.54,.035,note,ha='center',fontsize=7.5)
        fig.canvas.draw();renderer=fig.canvas.get_renderer();issues=[]
        for ax in axs:
            visible_xticks=[label for label,value in zip(ax.get_xticklabels(),ax.get_xticks()) if ax.get_xlim()[0]<=value<=ax.get_xlim()[1]]
            visible_yticks=[label for label,value in zip(ax.get_yticklabels(),ax.get_yticks()) if ax.get_ylim()[0]<=value<=ax.get_ylim()[1]]
            for artist in (ax.xaxis.label,ax.yaxis.label,ax.title,ax.yaxis.get_offset_text(),*visible_xticks,*visible_yticks):
                b=artist.get_window_extent(renderer)
                if b.x0<0 or b.y0<0 or b.x1>fig.bbox.x1 or b.y1>fig.bbox.y1:issues.append(artist.get_text())
        assert not issues,issues
        meta[NAMES[f-1]]=dict(panels=[dict(xlim=list(ax.get_xlim()),ylim=list(ax.get_ylim()),xscale=ax.get_xscale(),yscale=ax.get_yscale(),xlabel=ax.get_xlabel(),ylabel=ax.get_ylabel()) for ax in axs],layout_issues=issues)
        for ext in ('pdf','png'):fig.savefig(OUT/'figures'/(NAMES[f-1]+'.'+ext),dpi=350,facecolor='white')
        plt.close(fig)
    with plt.rc_context({'font.family':'serif','font.size':8.5,'axes.labelsize':9,'axes.linewidth':.7,'pdf.fonttype':42}):
        for f in range(1,5):
            group=[r for r in selections if r['figure']==f];panels=2 if f in (2,3) else 1
            fig,axs=plt.subplots(1,panels,figsize=(7.2,3.4),squeeze=False);axs=list(axs[0]);fig.subplots_adjust(left=.12,right=.98,bottom=.25,top=.79,wspace=.44)
            if f==1:
                ax=axs[0];configure(ax,'Number of Candidate UAV Positions','Mobility-Penalized Objective (bits/use)',True)
                for m in METHODS:draw(f,1,ax,group,m,'U')
                xx=[r['value'] for r in group];ax.set_xticks(xx);ax.set_xlim(5,105);ax.xaxis.set_minor_locator(FixedLocator([(a+b)/2 for a,b in zip(xx,xx[1:])]))
            elif f==2:
                for panel,(ax,key,label) in enumerate(zip(axs,('K','unavailability_percent'),('Mean Usable SKR (bits/use)','QKD Unavailability (%)')),1):
                    configure(ax,'Cloud Blockage Probability',label,key=='K');ax.set_title('(a) Mean Usable SKR' if panel==1 else '(b) QKD Unavailability',fontsize=9)
                    for m in METHODS:draw(f,panel,ax,group,m,key)
                    ax.set_xticks([r['value'] for r in group]);ax.set_xlim(.07,.83);ax.tick_params(axis='x',labelsize=7.8)
            elif f==3:
                for panel,(ax,key,label) in enumerate(zip(axs,('U','D'),('Mobility-Penalized Objective (bits/use)','Total Travel Distance (m)')),1):
                    configure(ax,'Temporal Cloud Correlation',label,key=='U');ax.set_title('(a) Objective' if panel==1 else '(b) Travel distance',fontsize=9)
                    for m in METHODS:draw(f,panel,ax,group,m,key)
                    ax.set_xticks([r['value'] for r in group]);ax.set_xlim(-.04,1.02);plt.setp(ax.get_xticklabels(),rotation=90,ha='center')
                for row,offset in ((group[0],(10,-25)),(group[-1],(-66,22))):
                    yy=srow(row,'DP','D')['mean'];axs[1].annotate(f'DP: {yy:.1f} m',xy=(row['value'],yy),xytext=offset,textcoords='offset points',fontsize=7.4,arrowprops=dict(arrowstyle='-',color='.5',lw=.5))
            else:
                ax=axs[0];configure(ax,'Total Travel Distance (m)','Mean Usable SKR (bits/use)',True)
                draw(f,1,ax,[group[0]],'Stationary','K','D')
                for m in ('Greedy','DP'):draw(f,1,ax,group,m,'K','D')
                for li,text,offset in ((0,'λ = 0',(-45,-25)),(4,'λ = λref',(12,-38))):
                    row=group[li];ax.annotate(text,xy=(srow(row,'DP','D')['mean'],srow(row,'DP','K')['mean']),xytext=offset,textcoords='offset points',fontsize=7.5,arrowprops=dict(arrowstyle='-',color='.5',lw=.5))
                ax.set_xlim(-55,max(p['x_ci95_high'] for p in points if p['figure']==4)*1.08)
            finish(fig,axs,f)
    save_csv('figures/plotted_points.csv',points)
    for f,name in enumerate(NAMES,1):save_csv('figures/'+name+'_data.csv',[r for r in points if r['figure']==f])
    save_json('figures/render_metadata.json',dict(status='CURRENTLY_VERIFIED_PASS',point_count=len(points),figure_width_inches=7.2,png_dpi=350,style=STYLE,figures=meta,producer_sha256=sha(Path(__file__)),no_smoothing=True,true_penalty_order=True))
    mapping=[]
    for f,name in enumerate(NAMES,1):
        sources=sorted({r['source'] for r in selections if r['figure']==f})
        mapping.append(dict(figure=f,pdf='figures/'+name+'.pdf',png='figures/'+name+'.png',figure_source_csv='figures/'+name+'_data.csv',statistical_table='tables/statistical_comparison.csv',paired_table='tables/paired_improvements.csv',input_directory=';'.join(sources),penalty_scope='all10 saved penalties' if f==4 else str(LAM),mission_ids='0-99',pdf_sha256=sha(OUT/'figures'/(name+'.pdf')),png_sha256=sha(OUT/'figures'/(name+'.png'))))
    save_csv('figure_source_mapping.csv',mapping)
    print('FINAL_DATA_RENDERED',len(selections),'configurations;',len(points),'actual artist points;no simulation calls',flush=True)


if __name__=='__main__':build_data()
