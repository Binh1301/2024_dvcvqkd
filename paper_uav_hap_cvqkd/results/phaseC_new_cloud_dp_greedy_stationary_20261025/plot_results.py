"""Render saved Monte Carlo results; no channel or source evaluator imports."""
import csv
import json
from pathlib import Path
import time
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap,LinearSegmentedColormap
from matplotlib.patches import Patch
import numpy as np

OUT=Path(__file__).resolve().parent
LABELS=['Stationary (offline)','Greedy (current slot)','DP (offline)']
ALGORITHMS=['Stationary','Greedy','DP']
COLORS=['#626262','#0072B2','#007F73']
MARKERS=['o','s','^']
NAMES=['fig1_cloud_realizations','fig2_cloud_covariance','fig3_unavailability_vs_p',
    'fig4_usable_skr_vs_p','fig5_objective_vs_p','fig6_distance_vs_p',
    'fig7_representative_trajectories','fig8_mobility_penalty_tradeoff']


def rows(name):
    with (OUT/name).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def read(name):return json.loads((OUT/name).read_text(encoding='utf-8'))
def style(ax,xlabel,ylabel):
    ax.set(xlabel=xlabel,ylabel=ylabel);ax.grid(alpha=.25,linewidth=.5)
def finish(fig,name):
    fig.savefig(OUT/(name+'.png'),dpi=600,bbox_inches='tight',pad_inches=.06,
        metadata={'Description':'DIAGNOSTIC_ONLY; synthetic cloud fields; source convergence evidence incomplete'})
    fig.savefig(OUT/(name+'.pdf'),bbox_inches='tight',pad_inches=.06,
        metadata={'Title':name,'Subject':'DIAGNOSTIC_ONLY; synthetic cloud; incomplete source-convergence evidence',
            'Creator':'Matplotlib saved-data renderer'})
    plt.close(fig)


def main():
    began=time.perf_counter()
    config=read('experiment_config.json');primary=config['primary_geometry'];pvalues=config['Monte_Carlo']['probabilities']
    assert read('focused_tests.json')['status']=='CURRENTLY_VERIFIED_PASS'
    summary=rows('summary_comparison.csv')
    lookup={(r['geometry'],r['case_id'],r['algorithm'],r['metric']):r for r in summary}
    plt.rcParams.update({'font.family':'serif','font.serif':['Times New Roman','STIXGeneral'],'mathtext.fontset':'stix',
        'font.size':9,'axes.labelsize':9.5,'xtick.labelsize':8.5,'ytick.labelsize':8.5,'legend.fontsize':8,
        'axes.spines.top':False,'axes.spines.right':False,'lines.linewidth':1.5,'pdf.fonttype':42,'ps.fonttype':42})
    with np.load(OUT/'cloud_realizations.npz') as data:
        cloud=data['C_zero'][0];gamma=data['Gamma'];points=data['positions']
    cmap=ListedColormap(['#FFFFFF','#647F97'])
    fig,axes=plt.subplots(1,3,figsize=(7.16,2.75),layout='constrained')
    for ax,n in zip(axes,[0,9,29]):
        ax.pcolormesh(np.arange(11)*100,np.arange(11)*100,cloud[:,n].reshape(10,10),
            cmap=cmap,vmin=0,vmax=1,edgecolors='#DDDDDD',linewidth=.3)
        ax.set(xlabel='$x$ (m)',ylabel='$y$ (m)',title=f'Slot {n+1}',aspect='equal',xticks=[0,500,1000],yticks=[0,500,1000])
    axes[1].legend(handles=[Patch(facecolor='white',edgecolor='gray',label='Clear'),
        Patch(facecolor='#647F97',label='Blocked')],loc='upper center',bbox_to_anchor=(.5,-.27),ncol=2)
    finish(fig,NAMES[0])

    fig,axes=plt.subplots(1,2,figsize=(7.16,3.25),layout='constrained')
    image=axes[0].pcolormesh(np.arange(101)+.5,np.arange(101)+.5,gamma,cmap='viridis',shading='flat')
    axes[0].set(xlabel='Position index $j$',ylabel='Position index $i$',aspect='equal',title='Conditional covariance $\\Gamma$')
    bar=fig.colorbar(image,ax=axes[0],shrink=.86,label='Covariance');bar.solids.set_rasterized(False)
    axes[1].pcolormesh(np.arange(11)*100,np.arange(11)*100,np.arange(1,101).reshape(10,10),cmap='Blues',edgecolors='white',linewidth=.3)
    for j,(x,y) in enumerate(points):axes[1].text(x,y,str(j+1),ha='center',va='center',fontsize=7.4,color='white' if j>=70 else 'black')
    axes[1].set(xlabel='$x$ (m)',ylabel='$y$ (m)',title='Row-major indices',aspect='equal')
    finish(fig,NAMES[1])

    for name,metric,ylabel,scale in [
        (NAMES[2],'zero_rate_unavailability','Zero-rate unavailability (%)',100),
        (NAMES[3],'average_usable_skr','Average usable SKR (bits/use)',1),
        (NAMES[4],'objective_U','Penalized objective $U$ (bits/use)',1),
        (NAMES[5],'total_distance_m','Total travel distance (m)',1)]:
        fig,ax=plt.subplots(figsize=(7.16,3.5),layout='constrained')
        for algorithm,color,marker,label in zip(ALGORITHMS,COLORS,MARKERS,LABELS):
            records=[lookup[(primary,f'new_calibrated_p{p:.1f}',algorithm,metric)] for p in pvalues]
            means=np.array([float(r['mean'])*scale for r in records]);low=np.array([float(r['ci95_low'])*scale for r in records]);high=np.array([float(r['ci95_high'])*scale for r in records])
            ax.plot(pvalues,means,color=color,marker=marker,markersize=4,label=label,
                linestyle='--' if algorithm=='Stationary' else '-',markerfacecolor='white')
            ax.fill_between(pvalues,low,high,color=color,alpha=.13,linewidth=0)
        style(ax,'Calibrated cloud blockage probability $p$',ylabel)
        ax.set(xticks=pvalues,xlim=(.08,.82))
        if scale==100:ax.set_ylim(bottom=-1)
        if metric in ['average_usable_skr','objective_U']:ax.ticklabel_format(axis='y',style='sci',scilimits=(-4,-4),useMathText=True)
        ax.legend();finish(fig,name)

    trajectories=rows('algorithm_trajectories.csv')
    selected=[r for r in trajectories if r['geometry']==primary and r['case_id']=='new_zero' and int(r['mission_id'])==0]
    fig,ax=plt.subplots(figsize=(5.6,4.8),layout='constrained')
    image=ax.pcolormesh(np.arange(11)*100,np.arange(11)*100,cloud.mean(axis=1).reshape(10,10),
        cmap=LinearSegmentedColormap.from_list('mission_cloud',['white','#8F8F8F']),vmin=0,vmax=1,edgecolors='white',linewidth=.4)
    bar=fig.colorbar(image,ax=ax,shrink=.82,label='Blocked-slot fraction (mission 0)')
    bar.solids.set_rasterized(False);bar.solids.set_edgecolor('face');bar.solids.set_linewidth(0)
    for algorithm,color,marker,label in zip(ALGORITHMS,COLORS,MARKERS,LABELS):
        records=sorted([r for r in selected if r['algorithm']==algorithm],key=lambda r:int(r['slot']))
        assert len(records)==30
        x=[float(r['x_m']) for r in records];y=[float(r['y_m']) for r in records]
        ax.plot(x,y,color=color,marker=marker,markersize=3.5,markerfacecolor='white',linewidth=1.5,label=label)
        ax.scatter(x[0],y[0],s=45,facecolors='none',edgecolors=color,linewidths=1.2,zorder=5)
        ax.scatter(x[-1],y[-1],s=30,marker='x',color=color,zorder=6)
    ax.set(xlabel='$x$ (m)',ylabel='$y$ (m)',xlim=(0,1000),ylim=(0,1000),aspect='equal')
    ax.legend(loc='upper left',framealpha=.95)
    ax.text(.02,.02,'Open ring: start; cross: end',transform=ax.transAxes,fontsize=8,
        bbox=dict(facecolor='white',edgecolor='none',alpha=.8))
    finish(fig,NAMES[6])

    lambda_values=config['lambda_values_bits_per_use']
    cases=[f'new_p0.4_lambda{i}' if value!=config['lambda_ref_bits_per_use'] else 'new_calibrated_p0.4' for i,value in enumerate(lambda_values)]
    fig,ax=plt.subplots(figsize=(7.16,3.65),layout='constrained')
    for algorithm,color,marker,label in zip(ALGORITHMS,COLORS,MARKERS,LABELS):
        distance=[lookup[(primary,case,algorithm,'total_distance_m')] for case in cases]
        rate=[lookup[(primary,case,algorithm,'average_usable_skr')] for case in cases]
        x=np.array([float(r['mean']) for r in distance]);y=np.array([float(r['mean']) for r in rate])
        xerr=np.array([[float(r['mean'])-float(r['ci95_low']) for r in distance],[float(r['ci95_high'])-float(r['mean']) for r in distance]])
        yerr=np.array([[float(r['mean'])-float(r['ci95_low']) for r in rate],[float(r['ci95_high'])-float(r['mean']) for r in rate]])
        ax.errorbar(x,y,xerr=xerr,yerr=yerr,color=color,marker=marker,markersize=4,markerfacecolor='white',
            capsize=1.5,elinewidth=.55,label=label)
        if algorithm=='DP':
            for i,text in [(0,'$\\lambda=0$'),(4,'$\\lambda=\\lambda_{ref}$'),(9,'Largest $\\lambda$')]:
                ax.annotate(text,xy=(x[i],y[i]),xytext=(5,9 if i!=4 else -17),textcoords='offset points',fontsize=8,color=color)
    style(ax,'Mean total travel distance (m)','Mean usable SKR (bits/use)')
    ax.ticklabel_format(axis='y',style='sci',scilimits=(-4,-4),useMathText=True);ax.legend(loc='lower right')
    finish(fig,NAMES[7])
    (OUT/'figure_render_receipt.json').write_bytes((json.dumps(dict(status='CURRENTLY_VERIFIED_PASS',
        result_scope='DIAGNOSTIC_ONLY',figure_pairs=8,dpi=600,elapsed_seconds=time.perf_counter()-began,
        numerical_evaluations=0,source_computations=0),indent=2)+'\n').encode())
    print('Eight PNG600dpi/vectorPDF pairs rendered from saved data only.')


if __name__=='__main__':main()
