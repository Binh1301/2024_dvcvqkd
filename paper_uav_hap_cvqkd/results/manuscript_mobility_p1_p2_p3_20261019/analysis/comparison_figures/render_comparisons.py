"""Eight saved-data figures. No physical evaluator, source, cloud or optimizer imports."""
from pathlib import Path
import csv
import hashlib
import json
import math

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter, AutoMinorLocator
import numpy as np
from scipy.stats import t

OUT=Path(__file__).resolve().parent
ANALYSIS=OUT.parent
SIM=ANALYSIS.parent
ROOT=SIM.parents[1]
PRODUCER_BYTES=Path(__file__).read_bytes()
METHODS=('Stationary','Greedy','DP')
LABELS={'Stationary':'Stationary (P2)','Greedy':'Greedy','DP':'Dynamic Programming (P3)'}
STYLES={'Stationary':dict(color='tab:blue',linestyle='-',marker='o',markersize=6.5),
        'Greedy':dict(color='tab:orange',linestyle='--',marker='s',markersize=6),
        'DP':dict(color='tab:red',linestyle='-',marker='^',markersize=6)}
NAMES=['fig1_average_skr_vs_lambda','fig2_objective_vs_lambda','fig3_travel_distance_vs_lambda',
       'fig4_dp_objective_gain_vs_lambda','fig5_skr_vs_travel_distance','fig6_per_slot_skr_comparison',
       'fig7_cumulative_skr_vs_time','fig8_uniform_vs_mb_positions']
TOL=1e-12


def read_json(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read_csv(path):
    with Path(path).open(encoding='utf-8-sig',newline='') as stream:return list(csv.DictReader(stream))
def save_json(name,value):(OUT/name).write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
def write_csv(name,rows):
    with (OUT/name).open('w',newline='',encoding='utf-8') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
def f(value):return f'{value:.12g}'


def integrity():
    startup=read_json(OUT/'startup_manifest.json');changed=[]
    for name,digest in startup['protected_files'].items():
        if not (ROOT/name).is_file() or sha(ROOT/name)!=digest:changed.append(name)
    if set(changed)-set(startup['allowed_changed']):raise ValueError('Protected input changed: '+str(changed))
    count=0
    for receipt,base,field in ((SIM/'validation/final_verification.json',SIM,'artifacts_sha256'),
                               (ANALYSIS/'analysis_receipt.json',ANALYSIS,'artifact_sha256')):
        record=read_json(receipt)
        if record['status']!='CURRENTLY_VERIFIED_PASS':raise ValueError('Unverified saved results')
        for name,digest in record[field].items():
            if sha(base/name)!=digest:raise ValueError('Receipt input changed: '+name)
            count+=1
    return dict(protected_files=len(startup['protected_files']),allowed_changed_files=changed,verified_prior_artifact_hashes=count)


def inventory():
    files=['mobility/mission_metrics.csv','mobility/time_series.csv','mobility/p2_positions.csv','positions.csv',
           'p1/winners.csv','p1/family_winners.csv','p1/candidate_evaluations.csv','source_roster.csv',
           'analysis/tables/method_comparison.csv','analysis/tables/paired_comparisons.csv']
    result=[]
    for name in files:
        with (SIM/name).open(encoding='utf-8-sig',newline='') as stream:
            reader=csv.DictReader(stream);columns=reader.fieldnames;count=sum(1 for _ in reader)
        units='K, U, MI, Holevo: bits/use; distance/x/y/z: m (distance_km: km); angle: degree; availability: fraction; VA: SNU; indices/counts: dimensionless'
        result.append(dict(path=(SIM/name).relative_to(ROOT).as_posix(),rows=count,columns=columns,units=units,sha256=sha(SIM/name)))
        print('DATA',name,'rows='+str(count),'columns='+str(len(columns)),flush=True)
    for name in ('mobility/paths.npz','clouds/states.npz'):
        with np.load(SIM/name,allow_pickle=False) as arrays:
            members={key:dict(shape=list(arrays[key].shape),dtype=str(arrays[key].dtype)) for key in arrays}
        result.append(dict(path=(SIM/name).relative_to(ROOT).as_posix(),members=members,
            units='paths: zero-based position indices; lambda_values: bits/use; blocked: bool True=blocked; usable_skr: bits/use',sha256=sha(SIM/name)))
        print('DATA',name,members,flush=True)
    save_json('data_inventory.json',result)
    lines=['# Data inventory','', 'Project-relative paths. Complete observed schemas; no inferred missing columns.','']
    for row in result:
        lines+=['## '+row['path'],'',row['units'],'']
        if 'rows' in row:lines+=['Rows: '+str(row['rows']), '', '`'+', '.join(row['columns'])+'`','']
        else:lines+=['`'+json.dumps(row['members'])+'`','']
    (OUT/'data_inventory.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')


def load_data():
    protocol=read_json(SIM/'protocol.json');schedule=read_json(SIM/'mobility/lambda_schedule.json')
    with np.load(SIM/'mobility/paths.npz',allow_pickle=False) as arrays:paths=arrays['paths'];penalties=arrays['lambda_values']
    with np.load(SIM/'clouds/states.npz',allow_pickle=False) as arrays:S=arrays['usable_skr'];C=arrays['blocked']
    if paths.shape!=(100,10,3,30) or S.shape!=(100,100,30) or C.shape!=(100,100,30):raise ValueError('Unexpected dimensions')
    assert S.shape==C.shape==(100,100,30) and C.dtype==np.bool_
    assert np.array_equal(penalties,np.array(schedule['values'])) and np.all(np.diff(penalties)>0) and penalties[0]==0
    positions=read_csv(SIM/'positions.csv');xy=np.array([[float(r['x_m']),float(r['y_m'])] for r in positions])
    assert [int(r['position_index']) for r in positions]==list(range(100))
    winners=read_csv(SIM/'p1/winners.csv');K=np.array([float(r['K_star']) for r in winners])
    assert np.array_equal(S,(~C)*K[None,:,None])
    rows=read_csv(SIM/'mobility/mission_metrics.csv');lookup={(int(r['realization_id']),int(r['lambda_index']),r['strategy']):r for r in rows}
    assert len(lookup)==len(rows)==3000 and set(lookup)=={(r,l,m) for r in range(100) for l in range(10) for m in METHODS}
    keys={'K':'average_skr_bits_per_use','D':'total_distance_m','U':'objective_bits_per_use','availability':'availability'}
    arrays={k:np.empty((100,10,3)) for k in keys}
    for (rid,li,method),row in lookup.items():
        si=METHODS.index(method);path=paths[rid,li,si];rates=S[rid,path,np.arange(30)]
        assert np.all((path>=0)&(path<100))
        legs=np.linalg.norm(np.diff(xy[path],axis=0),axis=1);assert np.all(legs<=300)
        actual=dict(K=float(rates.mean()),D=float(legs.sum()),U=float(rates.mean())-penalties[li]*legs.sum()/protocol['optimization']['reference_distance_m'],availability=float(np.mean(rates>0)))
        for key,value in actual.items():
            if not math.isclose(value,float(row[keys[key]]),abs_tol=TOL,rel_tol=TOL):raise ValueError('Metric mismatch '+str((rid,li,method,key)))
            arrays[key][rid,li,si]=float(row[keys[key]])
        assert float(row['lambda_bits_per_use'])==penalties[li]
    for rid in range(100):
        for li in range(10):
            for base in (0,1):
                if arrays['U'][rid,li,2]<arrays['U'][rid,li,base]-TOL:
                    raise ValueError('DP dominance violation: mission='+str(rid)+' lambda='+repr(float(penalties[li]))+' baseline='+METHODS[base])
    assert np.all(arrays['D'][:,:,0]==0) and np.all(arrays['K'][:,:,0]==arrays['K'][:,[0],0])
    assert np.all(np.diff(arrays['D'][:,:,2],axis=1)<=1e-9)
    saved={(int(r['lambda_index']),r['method']):r for r in read_csv(ANALYSIS/'tables/method_comparison.csv')}
    summary=[]
    for li,penalty in enumerate(penalties):
        for si,method in enumerate(METHODS):
            row=dict(lambda_index=li,lambda_bits_per_use=float(penalty),lambda_multiplier=schedule['multipliers'][li],strategy=method,missions=100)
            for key,values in arrays.items():
                x=values[:,li,si];mean=float(x.mean());sd=float(x.std(ddof=1));half=float(t.ppf(.975,99))*sd/10
                expected=dict(mean=mean,sd=sd,median=float(np.median(x)),ci95_t_low=mean-half,ci95_t_high=mean+half)
                for name,value in expected.items():
                    old=float(saved[li,method][key+'_'+name]);assert math.isclose(old,value,abs_tol=TOL,rel_tol=TOL)
                    row[key+'_'+name]=old
            summary.append(row)
    oldpairs={(int(r['lambda_index']),r['baseline'],r['metric']):r for r in read_csv(ANALYSIS/'tables/paired_comparisons.csv')}
    paired=[]
    for li in range(10):
        for base in (0,1):
            for metric in ('K','U'):
                delta=arrays[metric][:,li,2]-arrays[metric][:,li,base];den=arrays[metric][:,li,base];saved=oldpairs[li,METHODS[base],metric]
                assert abs(float(saved['mean'])-float(delta.mean()))<TOL
                assert int(saved['strict_improvement_missions'])==int(np.sum(delta>TOL))
                assert np.all(den>TOL)
                row=dict(lambda_index=li,lambda_bits_per_use=float(penalties[li]),baseline=METHODS[base],metric=metric,missions=100,
                    mean=float(delta.mean()),sd=float(delta.std(ddof=1)),median=float(np.median(delta)),
                    ci95_bootstrap_low=float(saved['ci95_bootstrap_low']),ci95_bootstrap_high=float(saved['ci95_bootstrap_high']),
                    strict_improvement_missions=int(np.sum(delta>TOL)),equal_missions=int(np.sum(np.abs(delta)<=TOL)),inferior_missions=int(np.sum(delta<-TOL)),
                    ratio_of_means_percent=float(100*delta.mean()/den.mean()),bootstrap_resamples=20000,bootstrap_seed=20261019)
                paired.append(row)
    li=int(np.flatnonzero(penalties==schedule['representative'])[0]);gain=arrays['U'][:,li,2]-arrays['U'][:,li,0]
    eligible=(gain>TOL)&(arrays['U'][:,li,2]>arrays['U'][:,li,1]+TOL)
    assert np.any(eligible);rid=min(np.flatnonzero(eligible),key=lambda r:(-gain[r],r));rid=int(rid)
    slots=[];cumulative=[]
    for si,method in enumerate(METHODS):
        path=paths[rid,li,si];values=S[rid,path,np.arange(30)];prefix=np.r_[0.,np.cumsum(values)]
        assert np.all(np.diff(prefix)>=0) and abs(prefix[-1]/30-arrays['K'][rid,li,si])<TOL
        for n,j in enumerate(path):slots.append(dict(realization_id=rid,lambda_index=li,lambda_bits_per_use=float(penalties[li]),strategy=method,slot=n+1,
            position_index=int(j),x_m=float(xy[j,0]),y_m=float(xy[j,1]),blocked=bool(C[rid,j,n]),usable_skr=float(values[n])))
        for n,value in enumerate(prefix):cumulative.append(dict(realization_id=rid,lambda_bits_per_use=float(penalties[li]),strategy=method,slot=n,cumulative_skr_sum=float(value)))
    family=read_csv(SIM/'p1/family_winners.csv');p1=[]
    for j in range(100):
        pair={r['family']:r for r in family if int(r['position_index'])==j};assert set(pair)=={'Uniform','MB'}
        p1.append(dict(j=j+1,position_index=j,Uniform_K_raw=float(pair['Uniform']['K_raw']),MB_K_raw=float(pair['MB']['K_raw']),
            Uniform_K_usable=float(pair['Uniform']['K_star']),MB_K_usable=float(pair['MB']['K_star']),Uniform_VA=float(pair['Uniform']['VA']),MB_nu=float(pair['MB']['nu_raw']),MB_VA=float(pair['MB']['VA'])))
    write_csv('figure_data_summary.csv',summary);write_csv('paired_improvements.csv',paired);write_csv('representative_slot_data.csv',slots)
    write_csv('cumulative_skr_data.csv',cumulative);write_csv('p1_position_data.csv',p1)
    return dict(protocol=protocol,schedule=schedule,penalties=penalties,a=arrays,summary=summary,paired=paired,rid=rid,li=li,slots=slots,cumulative=cumulative,p1=p1)


def render(data):
    traces=[];styles={};penalties=data['penalties'];linear=float(penalties[1])
    def axes(ylabel,lambda_axis=False,annotation=None):
        fig,ax=plt.subplots(figsize=(7.2,3.65));fig.subplots_adjust(left=.115,right=.98,bottom=.22 if lambda_axis else .18,top=.82)
        ax.set_ylabel(ylabel);ax.set_axisbelow(True);ax.minorticks_on()
        ax.grid(which='major',color='.82',lw=.55);ax.grid(which='minor',color='.92',lw=.35)
        if lambda_axis:
            ax.set_xscale('symlog',base=10,linthresh=linear);ax.set_xlabel('Mobility penalty λ (bits/use)')
            ax.set_xticks([0,1e-6,1e-5,1e-4,1e-3]);ax.set_xticklabels(['0','$10^{-6}$','$10^{-5}$','$10^{-4}$','$10^{-3}$'])
            ax.set_xlim(-linear*.12,float(penalties[-1])*1.25)
            fig.text(.54,.025,f'Base-10 symlog; linear threshold = {linear:.6g} bits/use',ha='center',fontsize=7.5)
        else:ax.xaxis.set_minor_locator(AutoMinorLocator())
        if annotation:fig.text(.54,.86,annotation,ha='center',fontsize=8)
        if 'distance' not in ylabel.lower():
            formatter=ScalarFormatter(useMathText=True);formatter.set_powerlimits((0,0));formatter.set_useOffset(False);ax.yaxis.set_major_formatter(formatter)
        return fig,ax
    def draw(fig_index,ax,x,y,method,curve=None,step=False,markevery=None,source=''):
        x=np.asarray(x);y=np.asarray(y);assert len(x)==len(y) and np.isfinite(x).all() and np.isfinite(y).all()
        style=dict(STYLES[method],linewidth=2.1,markerfacecolor='white',markeredgewidth=1.2,label=LABELS[method] if curve is None else curve)
        if markevery:style['markevery']=markevery
        line=(ax.step if step else ax.plot)(x,y,**style,**({'where':'mid'} if step else {}))[0]
        key=NAMES[fig_index-1]+':'+style['label'];styles[key]={k:style[k] for k in ('color','linestyle','marker','markersize','linewidth')}
        for n,(vx,vy) in enumerate(zip(line.get_xdata(),line.get_ydata())):
            traces.append(dict(figure=fig_index,curve=style['label'],method=method,point_index=n,x=float(vx),y=float(vy),source=source))
    def save(fig,ax,index,ncol=3):
        handles,labels=ax.get_legend_handles_labels()
        if index in (1,2,3,5,6,7):
            ordered=[(handles[labels.index(LABELS[m])],LABELS[m]) for m in METHODS]
            handles,labels=zip(*ordered)
        fig.legend(handles,labels,loc='upper center',bbox_to_anchor=(.54,.99),ncol=ncol,frameon=False,fontsize=8.5)
        for ext in ('pdf','png'):fig.savefig(OUT/(NAMES[index-1]+'.'+ext),dpi=350,facecolor='white')
        plt.close(fig)
    with plt.rc_context({'font.family':'serif','font.size':9,'axes.labelsize':10,'xtick.labelsize':9,'ytick.labelsize':9,
                         'pdf.fonttype':42,'axes.linewidth':.8,'figure.facecolor':'white','savefig.facecolor':'white'}):
        for index,key,label in ((1,'K','Average usable SKR (bits/use)'),(2,'U','Mean mobility-penalized\nobjective U (bits/use)'),(3,'D','Average total UAV travel\ndistance (m)')):
            fig,ax=axes(label,True);upper=0.;lower=0.
            for method in METHODS:
                rows=sorted([r for r in data['summary'] if r['strategy']==method],key=lambda r:r['lambda_bits_per_use'])
                mean=np.array([r[key+'_mean'] for r in rows]);lo=np.array([r[key+'_ci95_t_low'] for r in rows]);hi=np.array([r[key+'_ci95_t_high'] for r in rows])
                draw(index,ax,penalties,mean,method,source='figure_data_summary.csv:'+key+'_mean')
                ax.fill_between(penalties,lo,hi,color=STYLES[method]['color'],alpha=.08,linewidth=0)
                upper=max(upper,float(hi.max()));lower=min(lower,float(lo.min()))
            ax.set_ylim(lower-.025*upper,upper*1.12);save(fig,ax,index)
        fig,ax=axes('Mean objective improvement (bits/use)',True)
        for base,color_method in (('Stationary','Stationary'),('Greedy','Greedy')):
            rows=[r for r in data['paired'] if r['baseline']==base and r['metric']=='U']
            draw(4,ax,penalties,[r['mean'] for r in rows],color_method,curve='DP minus '+('Stationary' if base=='Stationary' else 'Greedy'),source='paired_improvements.csv:U')
            ax.fill_between(penalties,[r['ci95_bootstrap_low'] for r in rows],[r['ci95_bootstrap_high'] for r in rows],color=STYLES[color_method]['color'],alpha=.12,linewidth=0)
        ax.axhline(0,color='.35',lw=.8);ax.set_ylim(-2e-6,max(r['ci95_bootstrap_high'] for r in data['paired'] if r['metric']=='U')*1.12);save(fig,ax,4,ncol=2)
        fig,ax=axes('Average usable SKR (bits/use)');ax.set_xlabel('Average total UAV travel distance (m)')
        for method in ('Greedy','DP'):
            group=[r for r in data['summary'] if r['strategy']==method]
            draw(5,ax,[r['D_mean'] for r in group],[r['K_mean'] for r in group],method,source='figure_data_summary.csv:increasing_lambda')
        stationary=next(r for r in data['summary'] if r['strategy']=='Stationary')
        draw(5,ax,[0],[stationary['K_mean']],'Stationary',source='figure_data_summary.csv:Stationary')
        ax.set_ylim(0,max(r['K_mean'] for r in data['summary'])*1.15);ax.set_xlim(-50,max(r['D_mean'] for r in data['summary'])*1.08);save(fig,ax,5)
        annotation=f'Mission ID {data["rid"]}; λ = {data["schedule"]["representative"]:.8g} bits/use (post hoc case)'
        fig,ax=axes('Usable SKR (bits/use)',annotation=annotation);ax.set_xlabel('Time slot n')
        for method in METHODS:
            rows=[r for r in data['slots'] if r['strategy']==method]
            draw(6,ax,[r['slot'] for r in rows],[r['usable_skr'] for r in rows],method,step=True,markevery=2,source='representative_slot_data.csv')
        peak=max(r['usable_skr'] for r in data['slots'])
        ax.set_ylim(-.025*peak,peak*1.13);ax.set_xlim(.5,30.5);save(fig,ax,6)
        fig,ax=axes('Cumulative usable-SKR sum',annotation=annotation);ax.set_xlabel('Time slot n')
        for method in METHODS:
            rows=[r for r in data['cumulative'] if r['strategy']==method]
            draw(7,ax,[r['slot'] for r in rows],[r['cumulative_skr_sum'] for r in rows],method,markevery=3,source='cumulative_skr_data.csv')
        peak=max(r['cumulative_skr_sum'] for r in data['cumulative'])
        ax.set_ylim(-.025*peak,peak*1.12);ax.set_xlim(-.5,30.5);save(fig,ax,7)
        fig,ax=axes('Optimized clear-sky SKR\n(bits/use)');ax.set_xlabel('UAV candidate position index j')
        for key,method,label in [('Uniform_K_raw','Stationary','Optimized Uniform 256-QAM'),('MB_K_raw','DP','Optimized MB-shaped 256-QAM')]:
            draw(8,ax,[r['j'] for r in data['p1']],[r[key] for r in data['p1']],method,curve=label,markevery=5,source='p1_position_data.csv:'+key)
        ax.axhline(0,color='.4',lw=.8);ax.set_xlim(0,101);ax.set_xticks([1,20,40,60,80,100]);ax.set_ylim(min(r['Uniform_K_raw'] for r in data['p1'])*1.28,max(r['MB_K_raw'] for r in data['p1'])*1.15);save(fig,ax,8,ncol=2)
    write_csv('plotted_points.csv',traces);save_json('render_metadata.json',dict(producer_sha256=hashlib.sha256(PRODUCER_BYTES).hexdigest(),styles=styles,
        dimensions_inches=[7.2,3.65],png_dpi=350,pdf_vector=True,symlog_linear_threshold=linear,zero_lambda_retained=True,
        raw_negative_P1_retained=True,curve_connection='straight segments or slot steps through stored points; no smoothing',
        mean_CI='unmodified stored Student-t95 pointwise intervals; standard deviations are separate CSV columns',
        paired_CI='stored 20000-resample whole-mission paired percentile bootstrap, seed20261019; not recomputed',
        representative_mission_id=data['rid'],representative_lambda=data['schedule']['representative']))


def documents(data):
    rid=data['rid'];li=data['li'];lam=data['schedule']['representative'];lambda_hi=data['schedule']['lambda_hi']
    threshold=data['penalties'][1];requested=9.46803e-6
    selected=[r for r in data['paired'] if r['lambda_index']==li]
    lookup={(r['baseline'],r['metric']):r for r in selected}
    checked={base:{metric:lookup[base,metric]['ratio_of_means_percent'] for metric in ('K','U')} for base in ('Stationary','Greedy')}
    save_json('findings.json',dict(representative_lambda_exact=lam,requested_rounded_lambda=requested,
        requested_rounded_value_exists_exactly=bool(np.any(data['penalties']==requested)),rounding_difference=requested-lam,
        lambda_hi=lambda_hi,representative_lambda_index=li,mission_id=rid,percentage_denominator='mean of the same baseline across the same 100 missions; 100*(mean_DP-mean_baseline)/mean_baseline',
        percentages=checked,strict_U_wins={base:lookup[base,'U']['strict_improvement_missions'] for base in ('Stationary','Greedy')},
        all_100_DP_stationary_first_tested_lambda=float(data['penalties'][next(k for k in range(10) if np.all(data['a']['D'][:,k,2]==0))]),
        security_status='UNVALIDATED_SECURITY_MODEL',lifecycle='NOT_READY_FOR_PUBLICATION_SCALE_RUNS'))
    common=f'λ-axis uses base-10 symlog with linear threshold {f(threshold)} bits/use and retains λ=0. '
    captions=[
        'Average usable SKR for Stationary (P2), Greedy, and Dynamic Programming (P3), averaged over the same 100 independent synthetic cloud missions at ten stored penalties. Shaded bands are pointwise Student-t 95% confidence intervals for the means, not standard deviations. '+common+'These unpenalized rates are distinct from the optimized objective.',
        'Mean mobility-penalized objective U=K̄−λD/1000 for the three strategies over 100 common cloud missions. Pointwise Student-t 95% mean intervals are shaded. DP satisfies mission-wise objective dominance within 1e−12 bits/use under common speed constraints and freely selectable initial locations; P2/DP use the complete horizon whereas Greedy uses current-slot states. '+common,
        'Mean total UAV travel distance over 100 common missions, with pointwise Student-t 95% intervals. Stationary distance is exactly zero. DP distance is non-increasing at the tested penalties in each mission; Greedy has no such global guarantee. '+common,
        'Paired objective differences DP−Stationary and DP−Greedy, formed within each of the 100 missions before averaging. Bands are pointwise 95% percentile-bootstrap intervals from the existing 20,000 whole-mission paired resamples (seed 20261019); the horizontal line marks zero. '+common+'These are numerical-model uncertainty intervals, not security confidence bounds.',
        f'Mean usable SKR versus mean travel distance for Greedy and DP at the ten evaluated penalties; points are connected in increasing λ order, not distance order. Stationary is a single reference point at zero distance. Coincident high-penalty points overlap without jitter. λhi={f(lambda_hi)} bits/use. The curves are sampled policy tradeoffs, not a globally optimal physical Pareto frontier.',
        f'Per-slot usable SKR for Stationary (P2), Greedy, and DP (P3), read as S[j_n,n] along saved trajectories for mission {rid} at the stored λ={lam!r} bits/use. This case is selected post hoc as the largest DP−P2 objective gain among missions with strict DP gains over both baselines. All methods use the same cloud matrix. Zero-rate slots are verified against each selected trajectory’s boolean cloud states; lines are slot steps through saved data.',
        f'Cumulative usable-SKR sums R(n)=sum(t=1..n)S[j_t,t] for Stationary (P2), Greedy, and DP (P3), using the same mission {rid} and λ={lam!r} bits/use as Fig. 6. R(0)=0 is the empty sum. All curves are non-decreasing. The ordinate sums rate values over slots; physical secret-bit counts require a pulse rate and channel uses per slot, which are unspecified.',
        'Family-wise optimized raw clear-sky SKR at 100 saved candidate locations, ordered by manuscript index j=1,...,100 (x-first grid ordering). Negative Uniform values are retained with a zero reference line. MB selects (ν,VA)=(0.125,8) throughout the region. Each family chooses from its own finite catalog, including different variance choices; this is not a fixed-energy shaping-isolation claim. No percentage gain is assigned to zero or negative Uniform rates.'
    ]
    (OUT/'figure_captions_en.md').write_text('# IEEE-style figure captions\n\n'+ '\n\n'.join(f'**Figure {i+1}.** {caption.rstrip()}' for i,caption in enumerate(captions))+
        '\n\nAll rates are manuscript-style mixed 2D-MI/homodyne-Holevo numerical outputs. UNVALIDATED_SECURITY_MODEL; NOT_READY_FOR_PUBLICATION_SCALE_RUNS.\n',encoding='utf-8')
    mapping=[]
    sources=['figure_data_summary.csv:K','figure_data_summary.csv:U','figure_data_summary.csv:D','paired_improvements.csv:metric=U',
             'figure_data_summary.csv:D_mean,K_mean; ordered by lambda','representative_slot_data.csv','cumulative_skr_data.csv','p1_position_data.csv:raw']
    upstream=['mobility/mission_metrics.csv + analysis/tables/method_comparison.csv']*3+['mobility/mission_metrics.csv + analysis/tables/paired_comparisons.csv',
        'mobility/mission_metrics.csv','mobility/paths.npz + clouds/states.npz','mobility/paths.npz + clouds/states.npz','p1/family_winners.csv']
    for i,name in enumerate(NAMES):mapping.append(dict(figure=i+1,pdf=name+'.pdf',png=name+'.png',plot_data=sources[i],original_source=upstream[i],
        mission_scope='100 paired missions' if i<5 else ('post-hoc mission '+str(rid) if i<7 else '100 deterministic positions'),caption='figure_captions_en.md:Figure '+str(i+1)))
    write_csv('figure_source_mapping.csv',mapping)
    p2K=float(np.mean(data['a']['K'][:,li,0]));gK=float(np.mean(data['a']['K'][:,li,1]));dK=float(np.mean(data['a']['K'][:,li,2]))
    notes=[
        f'# Diễn giải tám hình so sánh\n\nUNVALIDATED_SECURITY_MODEL — NOT_READY_FOR_PUBLICATION_SCALE_RUNS\n\nKhông có lượt chạy mới của vật lý, SKR, nguồn, mây hoặc P1/P2/P3/Greedy. Tất cả metric được đối chiếu trực tiếp từ đường và S đã lưu. '
        f'Yêu cầu ghi λ={requested:.8g}; số làm tròn đó không có chính xác trong schedule. Dùng giá trị đại diện đã chốt λ={lam!r} bits/use, không thêm điểm λ mới. '
        'Kiểm kê đầy đủ: [data_inventory.md](data_inventory.md).',
        f'## Hình1 — SKR trung bình\n\nỞ λ đại diện: P2={f(p2K)}, Greedy={f(gK)}, DP={f(dK)} bits/use. DP tăng {checked["Stationary"]["K"]:.8f}% và {checked["Greedy"]["K"]:.8f}% so với hai baseline. '
        'Đây là tỷ lệ của các mean trên cùng100 mission, không mean của phần trăm cá thể. Đường P2 không đổi theo λ. '
        'DP mean K cao hơn hoặc bằng hai mean baseline trong tập10λ này; không suy ra điều đó cho từng mission khi λ>0. Trục y bắt đầu0 nên chênh vài phần trăm ở vùng trên khá nhỏ; hình4 cho effect-size objective rõ hơn.',
        f'## Hình2 — Objective tối ưu\n\nKhông có vi phạm U_DP≥U_P2,U_Greedy vượt1e−12 trong1000 cặp mission–λ. Ở λ đại diện, gain meanU lần lượt '
        f'{checked["Stationary"]["U"]:.8f}% và {checked["Greedy"]["U"]:.8f}%. Điều này hỗ trợ hiệu quả của DP trong bài toán lưới/horizon đã cho, không phải bảo đảm bảo mật hoặc điều khiển causal. '
        'Các strategy có cùng miền điểm đầu tự do; chúng không nhất thiết có cùng tọa độ đầu hay lượng thông tin.',
        '## Hình3 — Quãng đường\n\nP2 luôn0m. MeanD DP giảm từ1482,687833973m tại λ=0 xuống0 tại0,1λhi; ở0,03λhi vẫn có7 mission di chuyển. '
        'Greedy có31 lần tăngD giữa λ kề nhau trên25 mission. MeanD Greedy tăng673,874746570→675,150250806m giữa0,0001 và0,0003λhi; mức1,2755m nhỏ trên trục0–khoảng1700m, không nên phóng đại bằng mắt. '
        'Không ép đường đơn điệu. Tại λ=0 DP đi nhiều hơn Greedy ở trung bình; tại λ đại diện DP đi ít hơn. Greedy dừng hoàn toàn từ0,03λhi nhưng dừng ở điểm được chọn theo slot đầu, không tự trở thành P2.',
        f'## Hình4 — Gain objective theo cặp\n\nỞ λ đại diện: DP thắng P2 trong{lookup["Stationary","U"]["strict_improvement_missions"]}/100 mission, thắng Greedy trong{lookup["Greedy","U"]["strict_improvement_missions"]}/100; còn lại hòa trong1e−12. '
        f'Bootstrap CI95% meanΔU/P2=[{f(lookup["Stationary","U"]["ci95_bootstrap_low"])},{f(lookup["Stationary","U"]["ci95_bootstrap_high"])}], '
        f'meanΔU/Greedy=[{f(lookup["Greedy","U"]["ci95_bootstrap_low"])},{f(lookup["Greedy","U"]["ci95_bootstrap_high"])}] bits/use. '
        'Cả hai dương tại điểm này nhưng CI là pointwise, chưa hiệu chỉnh nhiều so sánh. Ở λ lớn DP hòa P2 nên không có gain mobility dương để tuyên bố. '
        'Gain DP−Greedy lớn ở λ cao phần lớn phản ánh chọn điểm đứng yên offline tốt hơn lựa chọn slot-đầu của Greedy, không phải DP đang bay nhiều.',
        '## Hình5 — K và quãng đường\n\nCác điểm nối theo λ tăng, giữ cả các đoạn quay lại do Greedy không đơn điệu. λ=0,0001λhi của DP giữ99,953824% meanK tạiλ0 trong khi giảm64,026687% meanD. '
        'Tại0,003λhi, DP dùng172,432989779m so với430,610183254m của Greedy và có meanK cao hơn. Các điểm này mô tả chính sách/λ đã thử, không phải Pareto frontier vật lý toàn cục hoặc năng lượng. '
        'Không có λ tối ưu phổ quát khi chưa hiệu chuẩn chi phí bay và ưu tiên kỹ thuật.',
        f'## Hình6 — Theo slot, mission{rid}\n\nChọn hậu nghiệm bằng tiêu chí đã ghi trong caption, không thay mission0 của báo cáo gốc. P2 bị chặn4slot; Greedy và DP không bị chặn dọc đường đã chọn. '
        'DP đi847,2135955m/5 lần đổi vị trí, Greedy1088,6349517m/7 lần. DP có thể chấp nhận utility tức thời thấp để tránh blockage về sau; chẳng hạn slot2:81→80 khi cả hai điểm đang clear, trong khi điểm81 bị chặn21slot còn lại. '
        'Đây là ví dụ giải thích có chọn theo kết quả, không phải một mẫu đại diện ngẫu nhiên cho gain trung bình.',
        '## Hình7 — Cộng dồn\n\nBa đường lấy cumulative sum đúng theo cùng mission/λ của hình6; cuối đường bằng30 lần meanK của method. Đường riêng lẻ không giảm. '
        'DP có thể thấp hơn Greedy ở prefix đầu; không yêu cầu thứ tự giữa các đường tại mọi slot. Không gọi ordinate là tổng bit khóa: chưa có pulse rate, channel uses hoặc overhead khi di chuyển/reacquisition.',
        '## Hình8 — P1 raw Uniform và MB\n\nUniform tối ưu có raw K âm ở100/100 điểm; MB raw K dương, cùng(ν,VA)=(0,125;8) tại100điểm. '
        'Giữ nguyên raw âm trên trục tuyến tính và vạch0; không tính phần trăm shaping gain trên Uniform âm/usable0. VA8 là biên catalog; hai family tối ưu VA riêng nên không cô lập PMF ở cùng năng lượng. '
        'Các răng cưa do thứ tự index x-first: chuyển từ cuối một hàng sang đầu hàng kế, không phải đường bay hoặc đường liên tục theo khoảng cách.',
        '## Bốn hình ưu tiên cho manuscript\n\n**2,4,5,8**: hình2 kiểm trực tiếp mục tiêu P3 với3 phương án; hình4 hiển thị độ lớn chênh theo cặp và uncertainty mà đường tuyệt đối có thể che; hình5 cho tradeoff K–D; hình8 cho kết quả nguồn P1 và raw âm Uniform. '
        'Hình1/3 bổ sung giải thích theoλ nhưng một phần trùng thông tin hình5; hình6/7 hợp appendix hoặc đoạn giải thích cơ chế vì chỉ là một ví dụ hậu nghiệm. '
        'Cả8 hình không có phương án Fixed44 nên không tự chứng minh gain P2 so với không chọn vị trí. Muốn nêu gain85,46% đó phải dẫn bảng P2/reference trong analysis trước, giữ rõ baseline44 được tái dựng hậu phân tích.',
        '## Giới hạn\n\n100 mission độc lập theo các streamSeedSequence khác nhau, nhưng ô/slot trong một mission tương quan; CI dùng đơn vị mission. '
        'P2/DP biết toàn bộ mây, Greedy biết current-slot oracle; không có cùng-information ablation. Hình học/mây tổng hợp, complete blockage, finitecatalog/grid, bỏ qua transit/reacquisition, distance chưa là joule. '
        'Không nâng lifecycle, không thêm test/held-out, không sửa detector/evaluator/frozen/cache/manuscript ngoài repo. Các cảnh báo bảo mật vẫn giữ nguyên.'
    ]
    for i,name in enumerate(NAMES):notes.insert(2*i+2,f'![Figure {i+1}]({name}.png)')
    (OUT/'figure_interpretation_vi.md').write_text('\n\n'.join(notes)+'\n',encoding='utf-8')
    index=['# Bộ tám hình so sánh P1–P2–P3','',
        'UNVALIDATED_SECURITY_MODEL; NOT_READY_FOR_PUBLICATION_SCALE_RUNS.','',
        'Chỉ hậu xử lý 100 mission × 10 λ đã lưu; không chạy lại vật lý, SKR, nguồn, mây hoặc thuật toán tối ưu. '
        'PDF vector và PNG 350 dpi, khổ đôi 7,2 inch.','',
        '| Hình | Nội dung | PDF | PNG |','|---|---|---|---|']
    titles=['SKR trung bình theo λ','Objective theo λ','Quãng đường theo λ','Gain objective theo cặp',
        'Tradeoff SKR–quãng đường','SKR theo slot','Cộng dồn SKR','P1 raw Uniform–MB']
    index += [f'| {i+1} | {title} | [PDF]({name}.pdf) | [PNG]({name}.png) |' for i,(title,name) in enumerate(zip(titles,NAMES))]
    index += ['', '## Tám câu hỏi nghiên cứu','',
        f'1. **DP có SKR cao hơn?** Mean DP ≥ hai mean baseline ở cả 10 λ trong dữ liệu này. Tại λ={lam!r}, '
        f'meanK tăng {checked["Stationary"]["K"]:.5f}% so với P2 và {checked["Greedy"]["K"]:.5f}% so với Greedy. '
        'Đây không phải bảo đảm cho từng mission: tại λ này, DP có unpenalized K thấp hơn Greedy ở 25/100 mission.',
        f'2. **DP có objective cao nhất?** Không vi phạm U_DP≥U_P2,U_Greedy trong 1.000 mission–λ, dung sai 1e−12. '
        f'Tại λ đại diện, meanU tăng {checked["Stationary"]["U"]:.5f}%/{checked["Greedy"]["U"]:.5f}%; '
        f'thắng nghiêm ngặt {lookup["Stationary","U"]["strict_improvement_missions"]}/100 và {lookup["Greedy","U"]["strict_improvement_missions"]}/100 mission.',
        '3. **Quãng đường đổi thế nào?** DP D không tăng theo λ trong từng mission. MeanD DP từ 1482,687834m tại λ=0 về 0 ở 0,1λhi. '
        'Greedy có 31 lần tăng D giữa λ kề nhau trên 25 mission; không ép đơn điệu.',
        '4. **Khi nào mobility bớt có lợi?** Ở 0,03λhi vẫn còn 7 mission DP di chuyển; ở 0,1λhi tất cả DP đứng yên và hòa P2. '
        'Chỉ suy ra khoảng chuyển tiếp giữa các điểm đã thử, không suy ra ngưỡng λ liên tục. Greedy dừng sớm hơn ở 0,03λhi nhưng không trở thành P2.',
        '5. **Đổi quãng đường lấy SKR thế nào?** DP tại 0,0001λhi giữ 99,953824% meanK của λ=0, giảm 64,026687% meanD. '
        'Tại 0,003λhi: DP đi 172,432990m so với Greedy 430,610183m, đồng thời có meanK cao hơn. Đây là các chính sách đã thử, không phải Pareto frontier vật lý.',
        f'6. **Từng mission có gì khác?** Hình6–7 dùng mission{rid}, chọn hậu nghiệm với DP strict thắng cả hai baseline. '
        'P2 bị chặn 4 slot; Greedy/DP tránh được blockage trên đường đã chọn. DP đổi điểm 5 lần/847,213595m, Greedy 7 lần/1088,634952m. '
        'Cumulative sum là tổng các giá trị SKR theo slot, chưa phải số bit khóa vật lý.',
        '7. **MB tốt hơn Uniform?** Raw MB dương và raw Uniform tối ưu âm ở cả 100 vị trí. MB chọn (ν,VA)=(0,125;8), tại biên VA catalog. '
        'Mỗi họ tối ưu VA riêng; không phải shaping gain ở cùng năng lượng, không chia phần trăm cho Uniform âm/usable0.',
        '8. **Hình nào mạnh nhất?** Ưu tiên 2,4,5,8: mục tiêu P3 trực tiếp; chênh lệch objective theo cặp và CI; tradeoff K–D; kết quả nguồn P1. '
        'Hình1/3 bổ sung nhưng trùng phần thông tin hình5; hình6/7 giải thích cơ chế bằng một ví dụ hậu nghiệm. '
        'Tám hình không có Fixed44 nên không tự chứng minh lợi ích chọn vị trí P2 so với một điểm cố định không tối ưu.',
        '', '## Thống kê và giới hạn','',
        'Phần trăm dùng 100×(meanDP−meanBaseline)/meanBaseline trên cùng100 mission, không lấy mean phần trăm từng mission. '
        'Mean/SD mẫu/median và CI Student-t được đối chiếu lại; CI bootstrap cho chênh lệch theo cặp tái sử dụng artifact đã xác thực '
        '(20.000 whole-mission resamples, seed20261019), là pointwise CI chưa hiệu chỉnh nhiều so sánh. '
        'Hình1 dùng trục gồm0 nên chênh vài phần trăm khó nhìn; hình4 biểu diễn độ lớn chênh rõ hơn.',
        f'λ được yêu cầu ở dạng làm tròn {requested!r} không tồn tại chính xác trong schedule. Dùng λ đại diện đã lưu {lam!r}; '
        f'chênh lệch làm tròn {requested-lam:.12g} bits/use. Không tạo λ mới.',
        'P2/DP là benchmark offline; Greedy đọc trạng thái slot hiện tại. Mây và hình học tổng hợp; catalog/lưới hữu hạn; distance chưa hiệu chuẩn thành năng lượng; '
        'mô hình MI2D/Holevo homodyne chưa được xác thực an toàn lượng tử. Frozen-hash discrepancy và Objective C USER_STOPPED được giữ nguyên. '
        'Không final-test/held-out, không nâng lifecycle, không sửa bản thảo ngoài repo, không commit/push.',
        '', '## Dữ liệu và kiểm chứng','',
        '[Inventory](data_inventory.md) · [Mean/SD/median/CI](figure_data_summary.csv) · [Paired gains](paired_improvements.csv) · '
        '[Source map](figure_source_mapping.csv) · [Captions tiếng Anh](figure_captions_en.md) · '
        '[Giải thích từng hình](figure_interpretation_vi.md) · [Validation](figure_validation.md) · [Receipt](validation_receipt.json)',
        '', 'Tái kiểm tra bằng Python môi trường dự án: `python -X utf8 -B verify_figures.py` tại thư mục này. '
        'Renderer từ chối ghi đè khi đã có receipt hoàn tất.']
    (OUT/'comparison_report_vi.md').write_text('\n'.join(index)+'\n',encoding='utf-8')


def main():
    if (OUT/'validation_receipt.json').exists():raise FileExistsError('Completed figure package is immutable')
    before=integrity();inventory();data=load_data();render(data);documents(data);after=integrity();assert before==after
    save_json('computation_checks.json',dict(status='CURRENTLY_VERIFIED_PASS',original_integrity=after,mission_metrics_checked=3000,
        path_slot_values_checked=90000,DP_dominance_comparisons=2000,new_optimizer_calls=0,new_physical_SKR=0,new_cloud_missions=0,new_source_moments=0))
    print('COMPARISON_RENDERED',8,'figure pairs; mission',data['rid'],'lambda',repr(data['schedule']['representative']),flush=True)


if __name__=='__main__':main()
