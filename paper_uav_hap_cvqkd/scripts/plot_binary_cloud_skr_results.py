"""IEEE plots and manuscript assets from verified saved binary-cloud data only."""
from __future__ import annotations
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import zipfile
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.lines import Line2D
from scripts import run_ao_effective_channel_no_fading_noise_reference as saved
from scripts.run_binary_cloud_skr_experiment import ROOT,identity,load_winners,verify_protected
from src.binary_cloud import mean_statistics
from src.binary_cloud_skr import read_csv,STATUS

COLORS=['#2463a6','#d78019','#368259','#a64175']
LABELS=['S1 Reference','S2 Stationary','S3 Moving, lambda=0','S4 Moving, penalty']
CAPTIONS=[
    'Binary cloud snapshots and MB UAV paths for the preregistered default realization 0. Dark cells are fully blocked links, indexed by UAV position; they are not geometric cloud footprints.',
    'Mean per-slot diagnostic SKR for MB policies over 100 independent missions; shaded bands are 95% Monte Carlo t intervals for the mean.',
    'Mean cumulative normalized SKR sum(S)/N_t. The endpoint equals mission-average SKR; it is not a finite-size key yield or a count of secret bits.',
    'Mean MB SKR versus mean flight distance at the eight evaluated penalties. Lines connect evaluated points only and do not establish a continuous optimum.',
    'Average MB SKR and threshold availability versus configured blockage probability; all policies share each mission cloud matrix. Bands are mission-level Monte Carlo intervals.',
    'One-factor sensitivity to Gaussian latent spatial length and temporal AR(1) coefficient. Binary correlations differ from latent parameters; the other parameters retain their default values.',
    'Paired MB and Uniform comparisons under the same four positioning policies and binary-cloud realizations. Each family optimizes its own exact finite source bank; selected energies can differ.']


def column_style(size):
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':7 if size=='single' else 9,
        'axes.labelsize':7 if size=='single' else 9,'axes.titlesize':7 if size=='single' else 9,
        'legend.fontsize':6 if size=='single' else 8,'xtick.labelsize':6 if size=='single' else 8,
        'ytick.labelsize':6 if size=='single' else 8,'pdf.fonttype':42,'ps.fonttype':42,
        'axes.spines.top':False,'axes.spines.right':False,'lines.linewidth':1.15})


def export(output,settings):
    output=Path(output)
    if (output/'export_receipt.json').exists():raise ValueError('Completed exports are immutable')
    verified=saved.read_json(output/'saved_data_validation.json')
    if verified['status']!='CURRENTLY_VERIFIED_PASS' or saved.read_json(output/'inputs.json')!=identity(settings):
        raise ValueError('Current saved-data verification required before export')
    verify_protected(output)
    figures=output/'figures';plots=output/'plot_data';package=output/'overleaf'
    for path in (figures,plots,package,package/'figures'):path.mkdir(exist_ok=True)
    cloud=np.load(output/'cloud_states.npz',allow_pickle=False)['blocked']
    trajectories=np.load(output/'trajectories.npz',allow_pickle=False);paths=trajectories['paths']
    winners=load_winners(output);positions=np.array([[float(r['x_m']),float(r['y_m'])] for r in read_csv(output/'positions.csv')])
    scenarios=saved.read_json(output/'cloud_scenarios.json');stats=read_csv(output/'summary_statistics.csv');lambda_stats=read_csv(output/'lambda_statistics.csv')
    slots=settings['mission']['slots'];dt=settings['mission']['slot_duration_s'];times=np.arange(1,slots+1)*dt
    def metric(sid,family,scheme,name):
        row=next(r for r in stats if int(r['scenario_id'])==sid and r['family']==family and r['scheme']==scheme and r['metric']==name)
        return {k:float(row[k]) for k in ('mean','sd','se','ci95_low','ci95_high')}
    def rates(sid,f,k):
        family=('MB','Uniform')[f];indices=paths[sid,:,f,k]
        blocked=cloud[sid,np.arange(len(indices))[:,None],indices,np.arange(slots)[None,:]]
        return (~blocked)*np.array([r['K_star'] for r in winners[family]])[indices]
    time_data=[];cumulative_data=[]
    for k,scheme in enumerate(('S1','S2','S3','S4')):
        values=rates(0,0,k);cumulative=np.cumsum(values,axis=1)/slots
        for n in range(slots):
            time_data.append(dict(scheme=scheme,slot=n+1,time_s=float(times[n]),**mean_statistics(values[:,n])))
            cumulative_data.append(dict(scheme=scheme,slot=n+1,time_s=float(times[n]),**mean_statistics(cumulative[:,n])))
    cloud_rows=[]
    for n in (0,9,19,29):
        for j,position in enumerate(positions):cloud_rows.append(dict(record='cloud',slot=n+1,position_index=j,x_m=position[0],y_m=position[1],blocked=bool(cloud[0,0,j,n])))
        for k,scheme in enumerate(('S1','S2','S3','S4')):
            for m,j in enumerate(paths[0,0,0,k,:n+1]):cloud_rows.append(dict(record='path',snapshot_slot=n+1,scheme=scheme,slot=m+1,position_index=int(j),x_m=positions[j,0],y_m=positions[j,1]))
    saved.write_csv(plots/'figure_1_cloud_paths.csv',cloud_rows)
    saved.write_csv(plots/'figure_2_skr_time.csv',time_data);saved.write_csv(plots/'figure_3_cumulative_normalized.csv',cumulative_data)
    saved.write_csv(plots/'figure_4_lambda_tradeoff.csv',lambda_stats)
    p_ids=[r['scenario_id'] for r in scenarios if r['correlation_length_m']==settings['cloud']['correlation_length_m'] and r['temporal_rho']==settings['cloud']['temporal_rho']]
    correlation_ids=[r['scenario_id'] for r in scenarios if r['probability']==settings['cloud']['probability']]
    saved.write_csv(plots/'figure_5_probability.csv',[r for r in stats if int(r['scenario_id']) in p_ids])
    saved.write_csv(plots/'figure_6_correlations.csv',[r for r in stats if int(r['scenario_id']) in correlation_ids])
    saved.write_csv(plots/'figure_7_uniform_MB.csv',[r for r in stats if int(r['scenario_id'])==0])
    saved.write_csv(output/'figure_captions.csv',[dict(figure=i+1,caption=c,scientific_status=STATUS) for i,c in enumerate(CAPTIONS)])
    for size,width in (('single',3.5),('double',7.16)):
        column_style(size)
        # Figure 1: binary masks at candidate links, no altitude projection/geometric clouds.
        fig,axes=plt.subplots(2,2,figsize=(width,4.7 if size=='single' else 5.1))
        for ax,n in zip(axes.flat,(0,9,19,29)):
            ax.pcolormesh(np.arange(11)*100,np.arange(11)*100,cloud[0,0,:,n].reshape(10,10),cmap=ListedColormap(['#ecf2f7','#69747c']),vmin=0,vmax=1,shading='flat',rasterized=False)
            for k in range(4):
                trace=positions[paths[0,0,0,k,:n+1]]
                ax.plot(trace[:,0],trace[:,1],color=COLORS[k],alpha=.85,linewidth=.85)
                ax.scatter(*trace[-1],color=COLORS[k],marker=('s','^','o','x')[k],s=18,zorder=5)
            ax.set(title=f'Slot {n+1} (t={n*dt:g} s)',xlabel='x (m)',ylabel='y (m)',xticks=[0,500,1000],yticks=[0,500,1000],xlim=(0,1000),ylim=(0,1000))
            ax.set_aspect('equal')
        handles=[Line2D([0],[0],color=COLORS[k],marker=('s','^','o','x')[k],label=LABELS[k]) for k in range(4)]
        fig.legend(handles=handles,loc='lower center',ncol=2,bbox_to_anchor=(.5,.015),frameon=False)
        fig.subplots_adjust(left=.14,right=.92,top=.94,bottom=.20,hspace=.65,wspace=.5)
        save_figure(fig,figures,1,size)
        for number,data,ylabel in ((2,time_data,'Mean SKR (bits/use)'),(3,cumulative_data,'Cumulative normalized SKR (bits/use)')):
            fig,ax=plt.subplots(figsize=(width,2.9 if size=='single' else 3.1),layout='constrained')
            for k,scheme in enumerate(('S1','S2','S3','S4')):
                rows=[r for r in data if r['scheme']==scheme];mean=np.array([r['mean'] for r in rows])
                ax.plot(times,mean,color=COLORS[k],label=LABELS[k],drawstyle='steps-post' if number==2 else 'default')
                ax.fill_between(times,[r['ci95_low'] for r in rows],[r['ci95_high'] for r in rows],color=COLORS[k],alpha=.12,step='post' if number==2 else None)
            ax.set(xlabel='Mission time (s)',ylabel=ylabel,xlim=(20,600));ax.grid(alpha=.18)
            if number==2:ax.legend(loc='lower center',bbox_to_anchor=(.5,1.02),ncol=2,frameon=False)
            else:ax.legend(loc='best',frameon=False)
            save_figure(fig,figures,number,size)
        fig,ax=plt.subplots(figsize=(width,2.9 if size=='single' else 3.1),layout='constrained')
        penalties=settings['sweeps']['lambda_bits_per_use'];xs=[];ys=[];xe=[];ye=[]
        for penalty in penalties:
            x=next(r for r in lambda_stats if r['family']=='MB' and float(r['lambda_bits_per_use'])==penalty and r['metric']=='total_flight_distance_m')
            y=next(r for r in lambda_stats if r['family']=='MB' and float(r['lambda_bits_per_use'])==penalty and r['metric']=='average_skr_bits_per_use')
            xs.append(float(x['mean']));ys.append(float(y['mean']));xe.append(float(x['ci95_high'])-float(x['mean']));ye.append(float(y['ci95_high'])-float(y['mean']))
        ax.errorbar(xs,ys,xerr=xe,yerr=ye,fmt='o-',markersize=3,capsize=2,color=COLORS[3],label='Eight evaluated penalties')
        ax.annotate('lambda=0',(xs[0],ys[0]),xytext=(-5,-16),textcoords='offset points',ha='right',fontsize=6 if size=='single' else 8)
        ax.annotate('lambda=0.05',(xs[-1],ys[-1]),xytext=(6,8),textcoords='offset points',fontsize=6 if size=='single' else 8)
        ax.set(xlabel='Mean flight distance (m)',ylabel='Mean SKR (bits/use)');ax.grid(alpha=.18);ax.margins(.14);ax.legend(loc='best',frameon=False)
        save_figure(fig,figures,4,size)
        fig,axes=plt.subplots(2,1,figsize=(width,4.7 if size=='single' else 4.9),layout='constrained',sharex=True)
        p_scenarios=sorted([r for r in scenarios if r['scenario_id'] in p_ids],key=lambda r:r['probability'])
        for ax,name,ylabel in zip(axes,('average_skr_bits_per_use','availability'),('Mean SKR (bits/use)','QKD availability')):
            for k,scheme in enumerate(('S1','S2','S3','S4')):
                values=[metric(r['scenario_id'],'MB',scheme,name) for r in p_scenarios];x=[r['probability'] for r in p_scenarios]
                ax.plot(x,[v['mean'] for v in values],'o-',markersize=2.5,color=COLORS[k],label=LABELS[k])
                ax.fill_between(x,[v['ci95_low'] for v in values],[v['ci95_high'] for v in values],color=COLORS[k],alpha=.1)
            ax.set_ylabel(ylabel);ax.grid(alpha=.18)
        axes[0].legend(loc='best',frameon=False);axes[1].set(xlabel='Configured blockage probability p',ylim=(-.025,1.025))
        save_figure(fig,figures,5,size)
        fig,axes=plt.subplots(2,2,figsize=(width,5.5 if size=='single' else 4.9))
        for col,(parameter,other,default,label) in enumerate((('correlation_length_m','temporal_rho',settings['cloud']['temporal_rho'],'Latent length (m)'),
                ('temporal_rho','correlation_length_m',settings['cloud']['correlation_length_m'],'Latent AR(1) rho'))):
            selected=sorted([r for r in scenarios if r['probability']==settings['cloud']['probability'] and r[other]==default],key=lambda r:r[parameter])
            for row,name in enumerate(('average_skr_bits_per_use','availability')):
                ax=axes[row,col]
                for k,scheme in enumerate(('S1','S2','S3','S4')):
                    values=[metric(r['scenario_id'],'MB',scheme,name) for r in selected];x=[r[parameter] for r in selected]
                    ax.plot(x,[v['mean'] for v in values],'o-',markersize=2.2,color=COLORS[k])
                    ax.fill_between(x,[v['ci95_low'] for v in values],[v['ci95_high'] for v in values],color=COLORS[k],alpha=.10)
                ax.set_xlabel(label);ax.grid(alpha=.18)
                if row==1:ax.set_ylim(0.,1.025)
        axes[0,0].set_ylabel('Mean SKR (bits/use)');axes[1,0].set_ylabel('QKD availability')
        fig.legend(handles=[Line2D([0],[0],color=COLORS[k],label=LABELS[k]) for k in range(4)],loc='lower center',ncol=2,frameon=False)
        fig.subplots_adjust(left=.16,right=.98,top=.96,bottom=.18,hspace=.46,wspace=.47)
        save_figure(fig,figures,6,size)
        fig,axes=plt.subplots(2,1,figsize=(width,4.5 if size=='single' else 4.8),layout='constrained',sharex=True)
        x=np.arange(4)
        for ax,name,ylabel in zip(axes,('average_skr_bits_per_use','availability'),('Mean SKR (bits/use)','QKD availability')):
            for family,offset,color in (('Uniform',-.18,'#929da7'),('MB',.18,COLORS[0])):
                values=[metric(0,family,s,name) for s in ('S1','S2','S3','S4')]
                ax.bar(x+offset,[v['mean'] for v in values],width=.34,color=color,label=family,
                    yerr=[v['ci95_high']-v['mean'] for v in values],capsize=2,error_kw={'linewidth':.7})
            ax.set_ylabel(ylabel);ax.grid(axis='y',alpha=.18)
        axes[0].legend(frameon=False);axes[1].set(xticks=x,xticklabels=['Reference','Stationary','Moving 0','Moving penalty'],xlabel='Matched positioning policy',ylim=(0,1.05))
        save_figure(fig,figures,7,size)
    # Required clear-sky spatial sensitivity diagnostic, separate from the seven main figures.
    column_style('double');fig,axes=plt.subplots(1,2,figsize=(7.16,3.2),layout='constrained')
    for ax,family in zip(axes,('MB','Uniform')):
        values=np.array([r['K_star'] for r in winners[family]]).reshape(10,10)
        mesh=ax.pcolormesh(np.arange(11)*100,np.arange(11)*100,values,shading='flat',rasterized=False)
        ax.set(title=family+' clear-sky SKR',xlabel='x (m)',ylabel='y (m)');ax.set_aspect('equal')
        fig.colorbar(mesh,ax=ax,label='SKR (bits/use)')
    fig.savefig(figures/'clear_sky_spatial_diagnostic.pdf');fig.savefig(figures/'clear_sky_spatial_diagnostic.png',dpi=300);plt.close(fig)
    write_manuscript(output,settings,metric)
    for path in figures.glob('figure_*.pdf'):shutil.copyfile(path,package/'figures'/path.name)
    (package/'plot_data').mkdir(exist_ok=True)
    for path in plots.glob('*.csv'):shutil.copyfile(path,package/'plot_data'/path.name)
    for name in ('table_I_parameters.csv','table_II_performance.csv'):shutil.copyfile(output/name,package/name)
    saved.save(package/'provenance.json',dict(scientific_status=STATUS,settings=settings,
        experiment_receipt_sha256=saved.digest(output/'experiment_receipt.json'),
        clear_source_audit_sha256=saved.digest(output/'audit_receipt.json'),new_source_moments=0))
    compile_status='BLOCKED_BY_ENVIRONMENT';compiler=next((shutil.which(name) for name in ('pdflatex','tectonic') if shutil.which(name)),None)
    compile_detail='No pdflatex or tectonic executable installed; manuscript page layout unverified.'
    if compiler:
        args=[compiler,'-interaction=nonstopmode','-halt-on-error','main.tex'] if Path(compiler).stem=='pdflatex' else [compiler,'main.tex']
        completed=subprocess.run(args,cwd=package,capture_output=True,text=True,timeout=90)
        (output/'latex_compile.log').write_text(completed.stdout+'\n'+completed.stderr,encoding='utf-8')
        compile_status='CURRENTLY_VERIFIED_PASS' if completed.returncode==0 else 'FAILED'
        compile_detail='Compiler exit '+str(completed.returncode)+'; rendered page review remains separate.'
    for path in package.glob('*.tex'):
        content=path.read_text(encoding='utf-8')
        if content.count('{')!=content.count('}'):raise ValueError('Unbalanced TeX braces: '+path.name)
        for reference in re.findall(r'\\(?:input|includegraphics)(?:\[[^]]*\])?\{([^}]+)\}',content):
            target=package/reference
            if not target.exists() and not target.with_suffix('.tex').exists():raise ValueError('Missing TeX path '+reference)
    archive=output/'overleaf_binary_cloud.zip'
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for path in sorted(package.rglob('*')):
            if path.is_file():z.write(path,path.relative_to(package).as_posix())
    names=[p.relative_to(output).as_posix() for folder in (figures,plots,package) for p in folder.rglob('*') if p.is_file()]
    names+=['figure_captions.csv','table_I_parameters.csv','table_II_performance.csv','overleaf_binary_cloud.zip','NUMERICAL_RESULTS_REPORT_VI.md','tradeoff_metrics.json']
    receipt=dict(status='CURRENTLY_VERIFIED_PASS',scope='Saved-data figure/table/TeX export only',scientific_status=STATUS,
        main_figures=7,column_layouts=['single','double'],main_vector_PDFs=14,main_PNGs=14,
        LaTeX_compile=compile_status,LaTeX_detail=compile_detail,LaTeX_lexical_paths='CURRENTLY_VERIFIED_PASS',
        producers={n:saved.digest(ROOT/n) for n in ('scripts/plot_binary_cloud_skr_results.py','scripts/verify_binary_cloud_skr_results.py')},
        output_sha256={n:saved.digest(output/n) for n in names},protected_changes=verify_protected(output))
    saved.save(output/'export_receipt.json',receipt,exclusive=True)
    print('EXPORT_COMPLETE',compile_status,flush=True)


def save_figure(fig,directory,number,size):
    fig.savefig(directory/f'figure_{number}_{size}.pdf')
    fig.savefig(directory/f'figure_{number}_{size}.png',dpi=300)
    plt.close(fig)


def write_manuscript(output,settings,metric):
    package=output/'overleaf';cloud=settings['cloud'];mission=settings['mission'];opt=settings['optimization']
    parameters=[('HAP altitude',20000,'m'),('UAV altitude',1000,'m'),('UAV area side',1000,'m'),('Candidate positions',100,'count'),
        ('MB exact sources',197,'count'),('Uniform exact sources',30,'count'),('Slots',mission['slots'],'count'),
        ('Slot duration',mission['slot_duration_s'],'s'),('Mission realizations',cloud['realizations'],'count'),
        ('Blockage probability',cloud['probability'],'probability'),('Latent spatial length',cloud['correlation_length_m'],'m'),
        ('Latent temporal coefficient',cloud['temporal_rho'],'per slot'),('Maximum UAV speed',mission['max_speed_m_per_s'],'m/s'),
        ('Reference flight distance',opt['reference_distance_m'],'m'),('Default movement penalty',opt['positive_lambda_bits_per_use'],'bits/use'),
        ('Availability threshold',opt['K_min_bits_per_use'],'bits/use'),('Clear zenith transmittance',.92,'power ratio'),
        ('Beam waist',settings['channel']['beam_waist_m'],'m'),('Receiver diameter',.55,'m'),('Reconciliation efficiency',.95,'ratio'),
        ('Channel excess noise',.0186,'SNU'),('Detector efficiency',1.,'ideal'),('Detector excess noise',0.,'SNU')]
    saved.write_csv(output/'table_I_parameters.csv',[dict(parameter=n,value=v,unit=u) for n,v,u in parameters])
    performance=[]
    for family in ('MB','Uniform'):
        for scheme in ('S1','S2','S3','S4'):
            row=dict(family=family,scheme=scheme)
            for name in ('average_skr_bits_per_use','availability','total_flight_distance_m','penalized_objective_bits_per_use'):
                for field,value in metric(0,family,scheme,name).items():row[name+'_'+field]=value
            performance.append(row)
    saved.write_csv(output/'table_II_performance.csv',performance)
    table1=r'\begin{table}[t]\caption{Synthetic demonstration settings.}\label{tab:binary_settings}\centering\small\resizebox{\columnwidth}{!}{\begin{tabular}{lrl}\hline Parameter & Value & Unit\\\hline'+'\n'
    table1+='\n'.join(f'{name} & {value:g} & {unit}'+r'\\' for name,value,unit in parameters)
    table1+='\n'+r'\hline\end{tabular}}\end{table}'+'\n'
    (package/'table_I_parameters.tex').write_text(table1,encoding='utf-8')
    table2=r'\begin{table}[t]\caption{Default binary-cloud results: Monte Carlo mission means; SKR is a preliminary diagnostic functional.}\label{tab:binary_performance}\centering\small\resizebox{\columnwidth}{!}{\begin{tabular}{llrrrr}\hline Source & Policy & SKR & Objective & Avail. & Flight (m)\\\hline'+'\n'
    table2+='\n'.join(f"{r['family']} & {r['scheme']} & {r['average_skr_bits_per_use_mean']:.5f} & {r['penalized_objective_bits_per_use_mean']:.5f} & {r['availability_mean']:.3f} & {r['total_flight_distance_m_mean']:.1f}"+r'\\' for r in performance)
    table2+='\n'+r'\hline\end{tabular}}\end{table}'+'\n'
    (package/'table_II_performance.tex').write_text(table2,encoding='utf-8')
    method=r'''\section{Mobility-Aware HAP--UAV Source and Position Optimization}
We use one UAV on 100 cell centers in a $1\,\mathrm{km}\times1\,\mathrm{km}$ region.
The HAP and UAV altitudes are fixed at 20 km and 1 km. The reference cell is
$(450,450)$ m and preserves the original 21.9393102292 km slant range.
\subsection{Correlated Binary Link Blockage}
Let $d_{ij}=\|\mathbf q_i-\mathbf q_j\|_2$ and $\Sigma_{ij}=\exp(-d_{ij}/\ell)$.
With $LL^{\mathsf T}=\Sigma$ and independent standard normal vectors,
\begin{align}
\mathbf z_1&=L\boldsymbol\xi_1,\\
\mathbf z_n&=\rho\mathbf z_{n-1}+\sqrt{1-\rho^2}L\boldsymbol\xi_n,\\
c_{j,n}&=\mathbb{I}\{z_{j,n}<\Phi^{-1}(p)\}.
\end{align}
The synthetic default is $p=0.4$, $\ell=250$ m, $\rho=0.9$ per 20 s slot.
The latent parameters are not Bernoulli correlation coefficients or measured meteorology.
Complete cloud blockage gives zero usable rate without evaluating QKD formulas at zero transmittance.
\subsection{Finite-Catalog Source Search and Positioning}
For each fixed position the existing common-ensemble discrete-input MI and direct-$Z_\star$
Holevo evaluator gives $K_j(c)=0.95 I_{AB,j}(c)-\chi_{BE,j}(c)$.
P1 searches all 197 MB exact-source pairs, or the separate 30-source Uniform variance bank:
\begin{align}
K_j^\star&=\left[\max_{c\in\mathcal C_{\rm src}} K_j(c)\right]^+,\\
S_{j,n}&=(1-c_{j,n})K_j^\star.
\end{align}
P2 selects the stationary location maximizing $N_t^{-1}\sum_n S_{j,n}$.
P3 maximizes $N_t^{-1}\sum_n S_{j_n,n}-\lambda D_{\rm fly}/D_{\rm ref}$,
with $D_{\rm fly}=\sum_{n=2}^{N_t}d_{j_{n-1},j_n}$ and
$d_{j_{n-1},j_n}\le v_{\max}\Delta t$. Exact finite-grid dynamic programming uses
\begin{align}
F_1(j)&=S_{j,1}/N_t,\\
F_n(j)&=S_{j,n}/N_t+\max_{i\in\mathcal N(j)}\{F_{n-1}(i)-\lambda d_{ij}/D_{\rm ref}\}.
\end{align}
Backtracking recovers the trajectory. Initial position is freely chosen before the mission;
deployment, relocation interruptions, reacquisition and source-switching overhead are excluded.
Availability $A=N_t^{-1}\sum_n\mathbb{I}\{S_{j_n,n}\ge K_{\min}\}$,
with $K_{\min}=0.001$ bits/use, is an evaluation metric only.
\subsection{Scientific Scope}
All reported rates use the existing effective Gaussian diagnostic with
$T_{\rm eff}=\mathbb E[\sqrt\eta]^2$ and $\xi_{\rm eff}=0.0186$ SNU.
It omits fading-induced variance and does not establish a full fading-channel security bound,
finite-size key yield, or an operational protocol. The distance penalty is not propulsion energy.
Cloud schedules are known offline; optimality holds only on the finite source catalog and UAV grid.
'''
    (package/'optimization_section.tex').write_text(method,encoding='utf-8')
    mb=[r for r in performance if r['family']=='MB'];s3=mb[2];s4=mb[3]
    tradeoff=dict(S4_SKR_retained_ratio_of_means_percent=100*s4['average_skr_bits_per_use_mean']/s3['average_skr_bits_per_use_mean'],
        S4_flight_reduction_ratio_of_means_percent=100*(1-s4['total_flight_distance_m_mean']/s3['total_flight_distance_m_mean']),
        S4_mean_SKR=s4['average_skr_bits_per_use_mean'],S3_mean_SKR=s3['average_skr_bits_per_use_mean'],
        S4_mean_flight_m=s4['total_flight_distance_m_mean'],S3_mean_flight_m=s3['total_flight_distance_m_mean'])
    saved.save(output/'tradeoff_metrics.json',tradeoff)
    numerical=r'''\section{Numerical Results}
We evaluate 16 cloud configurations with 100 independent missions each, 30 slots per mission,
and paired common Gaussian innovations across parameter sweeps. Source searches use 22,700
authenticated clear-sky records; the different cloud model never reuses old cloud-dependent rates.
Error bars describe Monte Carlo uncertainty of mission means, with variability computed between missions.
S2 is selected separately for each mission using the full known cloud schedule; it is a hindsight
stationary oracle rather than a single location frozen across independent future missions.
Default mean MB rates for S1--S4 are @MEANS@ bits/use.
S4 uses $\lambda=0.001$ bits/use and has mean flight distance @FLIGHT@ m.
Uniform and MB optimize their own finite source banks, so their comparison includes different selected
modulation energies and does not isolate shaping gain at matched energy.
These results remain preliminary Gaussian diagnostics ignoring fading variance.
\input{table_I_parameters}
\input{table_II_performance}
'''
    numerical=numerical.replace('@MEANS@',', '.join(f"{r['average_skr_bits_per_use_mean']:.8f}" for r in mb)).replace('@FLIGHT@',f"{s4['total_flight_distance_m_mean']:.3f}")
    for i,caption in enumerate(CAPTIONS,1):
        numerical+='\n'+r'\begin{figure}[t]\centering'+f'\n'+r'\includegraphics[width=\columnwidth]{figures/figure_'+str(i)+r'_single.pdf}'+'\n'+r'\caption{'+caption.replace('_',r'\_')+r'}\label{fig:binary_'+str(i)+r'}\end{figure}'+'\n'
    (package/'numerical_results_section.tex').write_text(numerical,encoding='utf-8')
    main=r'''\documentclass[conference]{IEEEtran}
\usepackage{graphicx,amsmath,amssymb,url}
\begin{document}
\title{Preliminary Binary-Cloud-Aware HAP--UAV CV-QKD Numerical Study}
\author{Diagnostic export for review}
\maketitle
\input{optimization_section}
\input{numerical_results_section}
\end{document}
'''
    (package/'main.tex').write_text(main,encoding='utf-8')
    (package/'README_VI.md').write_text('Upload toàn bộ thư mục này lên Overleaf; chọn main.tex. Cần IEEEtran, graphicx, amsmath, amssymb và url. Đây là kết quả minh họa sơ bộ, không phải chứng nhận bảo mật fading. Hai cỡ hình single/double được lưu; mặc định dùng single.\n',encoding='utf-8')
    report='# Binary-cloud-aware joint UAV/source optimization\n\nNgày 2026-10-15. '+STATUS+'.\n\n'
    report+='Đã dùng 16 cấu hình × 100 mission độc lập, 30 slot × 20 s; tổng 1.600 mission và 7.600 lượt DP. Tái sử dụng 19.700 MB + 3.000 Uniform clear-sky evaluations, không dùng hàng cloud cũ. Smoke 30 clear evaluations khớp cache; không tạo C,w/AP/AO mới.\n\n'
    report+='| Nguồn | Scheme | Mean SKR (bits/use) | SD | Availability | Mean flight (m) | Mean objective |\n|---|---|---:|---:|---:|---:|---:|\n'
    for r in performance:report+=f"| {r['family']} | {r['scheme']} | {r['average_skr_bits_per_use_mean']:.10f} | {r['average_skr_bits_per_use_sd']:.6f} | {r['availability_mean']:.6f} | {r['total_flight_distance_m_mean']:.3f} | {r['penalized_objective_bits_per_use_mean']:.10f} |\n"
    report+='\nS4 giữ '+format(tradeoff['S4_SKR_retained_ratio_of_means_percent'],'.6f')+'% SKR trung bình S3 và giảm '+format(tradeoff['S4_flight_reduction_ratio_of_means_percent'],'.6f')+'% quãng bay trung bình (tỷ số các mean, không phải mean của tỷ số từng mission).\n\n'
    report+='Cloud tổng hợp: p=0.4, ell=250 m, rho=0.9; PCG64 SeedSequence([20261015, realization_id]). Covariance latent exp(-d/ell), khởi tạo dừng, threshold Phi^-1(p). Ell/rho không phải correlation Bernoulli. Không cloud radius, velocity hoặc phép chiếu độ cao mây. Gong et al. (2020), DOI 10.1109/LWC.2019.2958804, chỉ là bối cảnh network availability, không phải nguồn hiệu chuẩn kernel này.\n\n'
    report+='P1 tối ưu đúng catalog theo vị trí một lần; P2 chọn mean cao nhất; P3 dùng DP sẵn có. S5 là Uniform ghép đủ bốn chính sách. K_min=0.001 bits/use chỉ dùng đánh giá, không điều khiển quỹ đạo. Vị trí đầu tự chọn; lambda=0.001 bits/use, D_ref=1000 m, tốc độ 15 m/s. Bỏ deployment, travel-time interruption, optical reacquisition và switching overhead. HAP 20 km/UAV 1 km, reference index44=(450,450)m giữ L_ref=21.9393102292km.\n\n'
    report+='Dữ liệu đầy đủ: [summary.csv](summary.csv), [mission statistics](summary_statistics.csv), [paired differences](paired_statistics.csv), [lambda statistics](lambda_statistics.csv), [cloud matrices](cloud_states.npz), [trajectories](trajectories.npz), [clear sources](clear_winners.csv), [source roster](source_roster.csv), [cache reuse](cache_reuse_audit.csv). CSV per-slot minh họa chỉ cho default realization0; mọi mission khác tái dựng từ NPZ. Realization0 được chọn trước, không chọn theo gain.\n\n'
    report+='S2 chọn riêng vị trí cố định cho từng mission với toàn bộ lịch cloud biết trước; đây là stationary oracle hindsight, không phải một vị trí được freeze rồi kiểm tra trên mission tương lai. Với horizon30 slot và100 vị trí, selection theo lịch đã biết có thể cho availability rất cao.\n\nKhoảng tin cậy t 95% và SD/SE lấy giữa mission độc lập, không lấy từng cell/slot như mẫu độc lập. Khoảng t không cắt tại0/1 nên cận có thể vượt miền availability; point estimate vẫn nằm trong[0,1]. Common innovations giúp so sánh ghép cặp giữa cấu hình; không gọi 1.600 mission độc lập giữa các cấu hình. Availability dùng >=K_min; nếu mọi clear rate đạt ngưỡng thì bằng tỷ lệ không blockage trên đường đi. Reference bằng0 có improvement phần trăm để trống, vẫn lưu delta tuyệt đối.\n\n'
    report+='[Clear-sky spatial variation](clear_sky_spatial_variation.csv) và [bản đồ](figures/clear_sky_spatial_diagnostic.png) mô tả độ biến thiên nguồn/kênh trong vùng1km. [Fading omission audit](fading_omission_audit.csv) tách (mean_eta-T_eff)VA và (mean_eta-T_eff)xi_ch bị bỏ. Đánh giá dùng ideal heterodyne, beta=.95, xi=.0186, phase/adaptive optics OFF, cùng ensemble cho MI/Holevo direct Z_star. Đây không phải lower bound bảo mật fading đã xác lập, finite-size yield, matched-energy PS gain, tối ưu liên tục hay năng lượng đẩy.\n\n'
    report+='Bảy hình có 14 vector PDF/14 PNG 300dpi và plotting CSV. Figure3 là sum(S)/N_t, không phải tổng bit khóa. Figure4 chỉ nối tám penalty đã tính. Không còn hình cloud velocity. LaTeX lexical/path kiểm tra riêng; trạng thái compiler trong export_receipt.json, không mặc nhiên coi bố cục manuscript đã đạt.\n\n'
    report+='Tests:23 primary tests (20 mới và3 normalization cũ) cộng3 regression tests cho verifier. Sửa verifier chỉ để nhận tie vài ULP giữa các cell đối xứng; không đổi source/kênh/DP hoặc kết quả thí nghiệm.\n\nProvenance: startup_manifest.json, audit_receipt.json, correlation_audit.json, test_receipt.json, smoke_receipt.json, experiment_receipt.json, saved_data_validation.json, export_receipt.json và final_validation.json. LF/CRLF chỉ chấp nhận khi hash chứng minh cùng nội dung, payload/ensemble và historical objective key đều xác minh; không sửa artifacts cũ. Lifecycle NOT_READY_FOR_PUBLICATION_SCALE_RUNS, frozen-hash discrepancy và ObjectiveC USER_STOPPED giữ nguyên. Không training/test dataset access, publication evaluation, commit hoặc push.\n\n'
    report+='Chạy từ root dự án bằng .venv-binary-cloud/Scripts/python.exe -B; runner scripts/run_binary_cloud_skr_experiment.py có --stage audit/smoke/experiment/export và --output. Lượt hoàn tất từ chối ghi đè; resume chỉ cùng input/producer, checkpoint nguyên tử theo scenario. Bộ kiểm tra: scripts/verify_binary_cloud_skr_results.py --exports. Môi trường hiện dùng system-site packages với packaging lấy offline từ pip-vendored copy trong venv riêng; không sửa Python hệ thống.\n'
    (output/'NUMERICAL_RESULTS_REPORT_VI.md').write_text(report,encoding='utf-8')
