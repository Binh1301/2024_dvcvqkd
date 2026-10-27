"""Six new IEEE figures from saved Phase D data only; no simulations."""
import csv
import json
from pathlib import Path
import time
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch

OUT=Path(__file__).resolve().parent
BASE=OUT.parent/'phaseC_new_cloud_dp_greedy_stationary_20261025'
NAMES=['figD1_conditional_unconditional_covariance','figD2_binary_latent_correlation',
       'figD3_indexing_cloud_maps','figD4_paired_objective_improvement',
       'figD5_rate_distance_tradeoff','figD6_indexing_robustness']
COLORS=['#444444','#0072B2','#009E73','#D55E00','#8A56A2']


def rows(name):
    with (OUT/name).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def write(name,text):(OUT/name).write_text(text,encoding='utf-8')
def style(ax,x,y):
    ax.set(xlabel=x,ylabel=y);ax.grid(alpha=.22,linewidth=.45)
def interval(r,key='mean',low='ci95_low',high='ci95_high',scale=1):
    v=float(r[key])*scale
    return v,np.array([[v-float(r[low])*scale],[float(r[high])*scale-v]])
def finish(fig,name):
    fig.savefig(OUT/(name+'.png'),dpi=600,bbox_inches='tight',pad_inches=.05,
        metadata={'Description':'DIAGNOSTIC_ONLY; saved Phase C/D records; incomplete source convergence evidence'})
    fig.savefig(OUT/(name+'.pdf'),bbox_inches='tight',pad_inches=.05,
        metadata={'Title':name,'Subject':'DIAGNOSTIC_ONLY; source convergence and security validation incomplete',
                  'Creator':'Matplotlib saved-data renderer'})
    plt.close(fig)


def main():
    began=time.perf_counter()
    plt.rcParams.update({'font.family':'serif','font.serif':['Times New Roman','STIXGeneral'],
        'mathtext.fontset':'stix','font.size':9,'axes.labelsize':9.5,'axes.titlesize':9.5,
        'xtick.labelsize':8,'ytick.labelsize':8,'legend.fontsize':8,
        'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'ps.fonttype':42,
        'lines.linewidth':1.3})
    cov=rows('cloud_validation_metrics.csv')
    fig,axes=plt.subplots(1,2,figsize=(7.16,3.05),layout='constrained')
    for name,color,marker,target in [('conditional',COLORS[1],'o',9),('unconditional',COLORS[2],'s',28/3)]:
        a=[r for r in cov if r['test']==name and r['i']==r['j']]
        x=np.arange(1,101)
        axes[0].plot(x,[float(r['estimate']) for r in a],linestyle='none',marker=marker,
            markersize=2.5,color=color,label=name.capitalize())
        axes[0].axhline(target,color=color,linestyle='--',linewidth=1)
    style(axes[0],'Cell index $j$','Diagonal covariance')
    axes[0].legend(loc='upper center',bbox_to_anchor=(.5,1.16),ncol=2,frameon=False,fontsize=7)
    for name,color,marker in [('conditional',COLORS[1],'o'),('unconditional',COLORS[2],'s')]:
        matrix=np.load(OUT/f'covariance_{name}.npy')
        lag=np.arange(1,21)
        estimates=[np.diag(matrix,k).mean() for k in lag]
        axes[1].plot(lag,estimates,linestyle='none',marker=marker,markersize=3,
                     color=color,label=name.capitalize())
    axes[1].plot(lag,9*.9**lag,color=COLORS[0],linestyle='--',label='$9(0.9)^{|i-j|}$')
    style(axes[1],'Index separation $|i-j|$','Off-diagonal covariance')
    axes[1].set(xticks=[1,5,10,15,20]);axes[1].legend(frameon=False)
    finish(fig,NAMES[0])

    data=rows('binary_spatial_correlations.csv')
    fig,ax=plt.subplots(figsize=(3.5,3.05),layout='constrained')
    for p,color,marker in [(.4,COLORS[1],'o'),(.5,COLORS[2],'s'),(.8,COLORS[3],'^')]:
        a=[r for r in data if float(r['p'])==p]
        x=np.array([float(r['unconditional_G_correlation']) for r in a])
        y=np.array([float(r['binary_normalized_covariance']) for r in a])
        low=np.array([float(r['binary_ci95_low']) for r in a]);high=np.array([float(r['binary_ci95_high']) for r in a])
        ax.errorbar(x,y,yerr=[y-low,high-y],fmt=marker,color=color,markersize=3.5,
            capsize=2,elinewidth=.7,markerfacecolor='white',label=f'$p={p}$ empirical')
        ax.scatter(x,[float(r['predicted_binary_correlation']) for r in a],marker='x',s=18,color=color,zorder=4)
    ax.plot([0,.9],[0,.9],color='#999999',linestyle=':',linewidth=1,label='Equality reference')
    style(ax,'Unconditional latent correlation','Binary blockage correlation')
    ax.set(xlim=(-.035,.92),ylim=(-.10,.94));ax.legend(frameon=False,loc='upper left',fontsize=7)
    finish(fig,NAMES[1])

    archive=np.load(OUT/'indexing_realizations.npz')
    assignments=['Row','Column','Serpentine','Random_A','Random_B']
    labels=['Row-major','Column-major','Serpentine','Random A','Random B']
    fig,axes=plt.subplots(2,3,figsize=(7.16,4.8),layout='constrained')
    for ax,name,label in zip(axes.ravel(),assignments,labels):
        C=archive[f'C_{name}_p0.5'][0,:,0]
        ax.pcolormesh(np.arange(11)*100,np.arange(11)*100,C.reshape(10,10),
            cmap=ListedColormap(['white','#647F97']),vmin=0,vmax=1,edgecolors='#DDDDDD',linewidth=.2)
        ax.set(title=label,xlabel='$x$ (m)',ylabel='$y$ (m)',aspect='equal',xticks=[0,500,1000],yticks=[0,500,1000])
    axes.ravel()[-1].axis('off')
    axes.ravel()[-1].legend(handles=[Patch(facecolor='white',edgecolor='gray',label='Clear'),
        Patch(facecolor='#647F97',label='Blocked')],loc='center',frameon=False)
    axes.ravel()[-1].text(.5,.2,'Same latent label field\nMission 0, slot 1, $p=0.5$',ha='center',va='center',transform=axes.ravel()[-1].transAxes)
    finish(fig,NAMES[2])

    paired=rows('paired_algorithm_statistics.csv')
    fig,axes=plt.subplots(1,2,figsize=(7.16,3.05),layout='constrained')
    for ax,baseline,color in zip(axes,['Greedy','Stationary'],[COLORS[1],COLORS[2]]):
        a=[r for r in paired if r['baseline']==baseline and r['metric']=='objective_U']
        for r in a:
            v,error=interval(r,low='bootstrap_ci95_low',high='bootstrap_ci95_high',scale=1e6)
            ax.errorbar(float(r['p']),v,yerr=error,fmt='o',color=color,capsize=3,markersize=4)
        ax.axhline(0,color='#777777',linewidth=.7)
        style(ax,'Calibrated blockage probability $p$',r'$\Delta U$ ($10^{-6}$ bits/use)')
        ax.set(title=f'DP minus {baseline}',xticks=[.4,.5,.8],xlim=(.35,.85))
    finish(fig,NAMES[3])

    fig,ax=plt.subplots(figsize=(3.5,3.05),layout='constrained')
    for p,color,offset in [(.4,COLORS[1],(6,6)),(.5,COLORS[2],(6,5)),(.8,COLORS[3],(-35,8))]:
        distance=next(r for r in paired if float(r['p'])==p and r['baseline']=='Greedy' and r['metric']=='total_distance_m')
        rate=next(r for r in paired if float(r['p'])==p and r['baseline']=='Greedy' and r['metric']=='average_usable_skr')
        x,xe=interval(distance,low='bootstrap_ci95_low',high='bootstrap_ci95_high')
        y,ye=interval(rate,low='bootstrap_ci95_low',high='bootstrap_ci95_high',scale=1e6)
        ax.errorbar(x,y,xerr=xe,yerr=ye,fmt='o',capsize=3,color=color,markersize=4)
        ax.annotate(f'$p={p}$',(x,y),xytext=offset,textcoords='offset points',fontsize=8)
    ax.axhline(0,color='#888888',linewidth=.7);ax.axvline(0,color='#888888',linewidth=.7)
    style(ax,'DP minus Greedy distance (m)',r'$\Delta\overline{K}$ ($10^{-6}$ bits/use)')
    ax.margins(.18);finish(fig,NAMES[4])

    pairs=rows('indexing_paired_statistics.csv');summary=rows('indexing_summary.csv')
    fig,axes=plt.subplots(1,2,figsize=(7.16,3.2),layout='constrained')
    for i,(name,label,color,marker) in enumerate(zip(assignments,labels,COLORS,['o','s','^','D','v'])):
        a=[r for r in pairs if r['indexing']==name and r['baseline']=='Greedy' and r['metric']=='objective_U']
        for r in a:
            v,e=interval(r,scale=1e6)
            axes[0].errorbar(float(r['p'])+(i-2)*.009,v,yerr=e,fmt=marker,color=color,
                capsize=2,markersize=3.3,label=label if float(r['p'])==.4 else None)
    style(axes[0],'Calibrated blockage probability $p$',r'$\Delta U_{\rm DP-Greedy}$ ($10^{-6}$ bits/use)')
    axes[0].set(xticks=[.4,.5,.8],xlim=(.35,.85));axes[0].legend(frameon=False,loc='upper left',fontsize=7)
    for a,color,marker,offset in [('Stationary',COLORS[0],'o',-.17),('Greedy',COLORS[1],'s',0),('DP',COLORS[2],'^',.17)]:
        for i,name in enumerate(assignments):
            r=next(r for r in summary if r['indexing']==name and float(r['p'])==.8 and r['algorithm']==a and r['metric']=='zero_rate_unavailability')
            v,e=interval(r,scale=100)
            axes[1].errorbar(i+offset,v,yerr=e,fmt=marker,color=color,capsize=2,markersize=3.5,label=a if i==0 else None)
    style(axes[1],'Index assignment','Zero-rate unavailability (%)')
    axes[1].set(title='$p=0.8$',xticks=np.arange(5),xticklabels=['Row','Col.','Snake','Rnd. A','Rnd. B'])
    axes[1].legend(frameon=False,loc='center left',bbox_to_anchor=(.02,.60),fontsize=7)
    finish(fig,NAMES[5])
    captions=[
        'Conditional and unconditional covariance diagnostics from 100 saved missions. Dashed diagonals are 9 and 28/3; off-diagonal targets are identical. Points are raw entry/lag summaries, with no smoothing.',
        'Binary versus unconditional latent correlations for six fixed cell pairs. Open markers and mission95%CI are empirical known-marginal estimates; crosses show the independently integrated mixture prediction. The dotted equality line is a reference, not a fitted model.',
        'Cloud masks for five index assignments using the exact same latent label field (mission 0, slot 1, p=0.5). Row/column are transpose-related; other mappings change physical correlation patterns.',
        'DP objective improvement over Greedy and offline Stationary, with 10000-replicate paired mission bootstrap 95% CI. All results use 100 paired missions and lambda_ref; intervals are pointwise.',
        'Paired DP-minus-Greedy rate and distance differences with bootstrap 95% CI. At p=0.4 the rate interval crosses zero; at p=0.8 improved rate requires greater travel. No curve is fitted or interpolated.',
        'Indexing robustness: paired objective gains with Student-t 95% CI (horizontal offsets are visual only), and unavailability at p=0.8. Five fixed assignments are tested; they are not an exhaustive permutation study.'
    ]
    write('figure_captions.tex','% All figures DIAGNOSTIC_ONLY; source convergence evidence incomplete.\n'+
        '\n'.join('% '+n+'\n\\caption{'+c.replace('%','\\%').replace('_','\\_')+'}\n' for n,c in zip(NAMES,captions)))
    index='# Phase D figures — DIAGNOSTIC_ONLY\n\n| Figure | PNG600dpi | VectorPDF |\n|---|---|---|\n'
    for n,c in zip(NAMES,captions):index+=f'| {n} | [PNG]({n}.png) | [PDF]({n}.pdf) |\n'
    index+='\n'+ '\n\n'.join(f'**Figure {i+1}.** {c}' for i,c in enumerate(captions))
    index+='\n\nPhase C figures are reused by reference, unchanged: [Phase C figure index](../phaseC_new_cloud_dp_greedy_stationary_20261025/figure_index.md).\n'
    write('figure_index.md',index)
    write('figure_render_receipt.json',json.dumps(dict(status='RENDERED_AWAITING_VISUAL_QA',figures=NAMES,
        pairs=6,png_dpi=600,elapsed_seconds=time.perf_counter()-began,simulations_called=False),indent=2))


if __name__=='__main__':main()
