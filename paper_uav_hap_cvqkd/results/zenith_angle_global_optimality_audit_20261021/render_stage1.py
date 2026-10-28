"""Draw audited historical samples only; no interpolation or new rate calls."""
from pathlib import Path
import csv
import hashlib
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

OUT=Path(__file__).resolve().parent
OLD=OUT.parents[1]/'results/skr_vs_zenith_angle_20261019'


def rows(path):
    with path.open(encoding='utf-8',newline='') as f:
        return list(csv.DictReader(f))


def main():
    if (OUT/'validation/final_receipt.json').exists():
        raise FileExistsError('Sealed figures are immutable')
    values=rows(OLD/'all_candidate_evaluations.csv')
    roster=rows(OUT/'original_catalog_candidates.csv')
    audit=rows(OUT/'original_catalog_audit.csv')
    local=rows(OUT/'sampled_uniform_local_maxima.csv')
    angles=[24,30,40,48,52,60]
    plt.rcParams.update({'font.family':'serif','font.serif':['Times New Roman'],
        'font.size':8,'axes.labelsize':8,'axes.titlesize':8,'legend.fontsize':6.6,
        'xtick.labelsize':7,'ytick.labelsize':7,'mathtext.fontset':'stix',
        'axes.linewidth':.65,'lines.linewidth':.9,'pdf.fonttype':42,'ps.fonttype':42})
    points=[];manifest=[]
    def frame(ax):
        ax.grid(True,which='major',ls=':',lw=.45,color='.75');ax.set_axisbelow(True)
        ax.tick_params(direction='in',width=.6,length=2.5)
        for s in ax.spines.values(): s.set_color('black')
    def trace(ax,records,xkey,label,figure,**kwargs):
        ordered=sorted(records,key=lambda r:float(r[xkey]))
        x=np.array([float(r[xkey]) for r in ordered]);y=np.array([float(r['K_raw']) for r in ordered])
        line,=ax.plot(x,y,label=label,markersize=3.1,markerfacecolor='white',markeredgewidth=.65,**kwargs)
        assert np.array_equal(line.get_xdata(),x) and np.array_equal(line.get_ydata(),y)
        for r in ordered:
            points.append(dict(figure=figure,series=label,zenith_deg=r['zenith_deg'],family=r.get('family',r.get('scheme','')),
                nu_raw=r.get('nu_raw',r.get('best_nu_raw','')),VA=r.get('VA',r.get('best_VA','')),
                ensemble_hash=r['ensemble_hash'],x=float(r[xkey]),K_raw=r['K_raw']))
    def finish(fig,name,description):
        fig.tight_layout(pad=.7)
        for ext in ['pdf','png']:
            fig.savefig(OUT/f'figures/{name}.{ext}',dpi=350,facecolor='white')
        plt.close(fig)
        path=OUT/f'figures/{name}.pdf'
        manifest.append(dict(figure=name,pdf='figures/'+path.name,pdf_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            png=f'figures/{name}.png',source='ORIGINAL_218_SOURCE_CATALOG_ONLY',new_evaluations=0,description=description))
    # A and B intentionally contain no invented refined series.
    fig,ax=plt.subplots(figsize=(3.5,2.35));frame(ax)
    trace(ax,[r for r in values if r['family']=='Uniform' and any(r['ensemble_hash']==a['ensemble_hash'] and float(r['zenith_deg'])==float(a['zenith_deg']) for a in audit if a['scheme']=='Optimized Uniform')],
        'zenith_deg','Historical catalog optimum','A_historical_uniform',color='#1f4b7a',marker='o',ls='-')
    ax.axhline(0,color='.3',lw=.55);ax.set(xlabel='Zenith angle (degrees)',ylabel='Raw SKR (bits/use)')
    ax.ticklabel_format(axis='y',style='sci',scilimits=(-4,-4),useMathText=True)
    ax.legend(loc='upper left')
    finish(fig,'fig_A_historical_uniform','Historical Uniform maximum; no new series evaluated')
    fig,ax=plt.subplots(figsize=(3.5,2.35));frame(ax)
    fixed=[r for r in values if r['family']=='MB' and float(r['nu_raw'])==.165 and float(r['VA'])==5.475]
    best=[r for r in audit if r['scheme']=='Optimized MB']
    trace(ax,fixed,'zenith_deg','Fixed MB','B_historical_MB',color='#a54127',marker='^',ls='--')
    trace(ax,best,'zenith_deg','Historical catalog optimum','B_historical_MB',color='#21634c',marker='D',ls='-')
    ax.axhline(0,color='.3',lw=.55);ax.set(xlabel='Zenith angle (degrees)',ylabel='Raw SKR (bits/use)')
    ax.ticklabel_format(axis='y',style='sci',scilimits=(-4,-4),useMathText=True);ax.legend(loc='upper left')
    finish(fig,'fig_B_historical_MB','Fixed MB and historical MB catalog maximum; no new refined values')
    # Exact catalog coverage and selected sites.
    mb=[r for r in roster if r['family']=='MB']
    fig,ax=plt.subplots(figsize=(6.4,3.4));frame(ax)
    ax.scatter([float(r['nu_raw']) for r in mb],[float(r['VA']) for r in mb],s=12,facecolor='none',edgecolor='.55',lw=.6,label='182 historical candidates')
    groups={}
    for r in best:
        groups.setdefault((float(r['best_nu_raw']),float(r['best_VA'])),[]).append(int(r['zenith_deg']))
    for (nu,va),zs in groups.items():
        ax.scatter([nu],[va],marker='D',s=32,c='#a54127',zorder=4)
        label=','.join(map(str,zs)) if len(zs)<5 else f'{min(zs)}--{max(zs)}'
        ax.annotate(label+' deg',(nu,va),xytext=(4,4),textcoords='offset points',fontsize=6.6)
    ax.axhline(8,color='.35',lw=.7,ls='--',label='Numerical catalog upper bound')
    ax.set(xlabel='Raw MB parameter, $\\nu_{\\rm raw}$',ylabel='Modulation variance, $V_A$ (SNU)',yscale='log')
    ax.set_ylim(.018,12);ax.legend(loc='lower right')
    finish(fig,'fig_0_MB_catalog_coverage','All 182 MB sites; diamond annotations show selected zenith angles; logarithmic VA axis')
    # Uniform slices reveal the sampled small-VA maximum and renewed tail rise.
    fig,axes=plt.subplots(2,3,figsize=(7.1,4.55))
    for ax,z in zip(axes.flat,angles):
        frame(ax);sub=[r for r in values if r['family']=='Uniform' and float(r['zenith_deg'])==z]
        trace(ax,sub,'VA','Saved Uniform samples','Uniform_VA_slices',color='#1f4b7a',marker='o',ls='-')
        win=next(r for r in audit if r['scheme']=='Optimized Uniform' and int(r['zenith_deg'])==z)
        ax.plot(float(win['best_VA']),float(win['K_raw']),marker='D',color='#a54127',ms=4.5,ls='none')
        for r in local:
            if int(r['zenith_deg'])==z: ax.plot(float(r['VA']),float(r['K_raw']),marker='s',color='#21634c',mfc='none',ms=4.5)
        ax.set(xscale='log',xlabel='$V_A$ (SNU)',ylabel='Raw SKR (bits/use)',title=f'$\\zeta={z}^\\circ$')
        ax.ticklabel_format(axis='y',style='sci',scilimits=(-4,-4),useMathText=True)
    finish(fig,'fig_U_Uniform_VA_slices','Uniform samples only; diamonds catalog winners, squares sampled neighborhood maxima; logarithmic VA axis')
    styles=[('#1f4b7a','o','-'),('#a54127','^','--'),('#21634c','D','-.'),('#6b4187','s',':')]
    fig,axes=plt.subplots(2,3,figsize=(7.1,4.55))
    for ax,z in zip(axes.flat,angles):
        frame(ax)
        for nu,(color,marker,ls) in zip([.1,.125,.165,.2],styles):
            sub=[r for r in values if r['family']=='MB' and float(r['zenith_deg'])==z and float(r['nu_raw'])==nu]
            trace(ax,sub,'VA',f'$\\nu={nu}$','MB_VA_slices',color=color,marker=marker,ls=ls)
        ax.set(xlabel='$V_A$ (SNU)',ylabel='Raw SKR (bits/use)',title=f'$\\zeta={z}^\\circ$')
        ax.ticklabel_format(axis='y',style='sci',scilimits=(-4,-4),useMathText=True);ax.legend(loc='best',ncol=2,handlelength=1.4,columnspacing=.5)
    finish(fig,'fig_1_MB_K_vs_VA','Historical fixed-nu slices only; segments connect actual irregular samples')
    fig,axes=plt.subplots(2,3,figsize=(7.1,4.55))
    for ax,z in zip(axes.flat,angles):
        frame(ax)
        for va,(color,marker,ls) in zip([2,5.5,8],styles):
            sub=[r for r in values if r['family']=='MB' and float(r['zenith_deg'])==z and float(r['VA'])==va]
            assert sub
            trace(ax,sub,'nu_raw',f'$V_A={va}$','MB_nu_slices',color=color,marker=marker,ls=ls)
        ax.set(xlabel='$\\nu_{\\rm raw}$',ylabel='Raw SKR (bits/use)',title=f'$\\zeta={z}^\\circ$')
        ax.ticklabel_format(axis='y',style='sci',scilimits=(-4,-4),useMathText=True);ax.legend(loc='best',handlelength=1.4)
    finish(fig,'fig_2_MB_K_vs_nu','Historical fixed-VA slices only; no new nu values or interpolation')
    sub=[r for r in values if r['family']=='MB' and float(r['zenith_deg'])==48]
    fig,ax=plt.subplots(figsize=(5.4,3.3));frame(ax)
    scat=ax.scatter([float(r['nu_raw']) for r in sub],[float(r['VA']) for r in sub],c=[float(r['K_raw']) for r in sub],s=20,cmap='viridis',edgecolor='.3',lw=.2)
    winner=next(r for r in best if int(r['zenith_deg'])==48)
    ax.scatter([float(winner['best_nu_raw'])],[float(winner['best_VA'])],marker='D',s=70,facecolor='none',edgecolor='#b22222',lw=1.3,label='Catalog maximum')
    ax.set(xlabel='$\\nu_{\\rm raw}$',ylabel='$V_A$ (SNU)',yscale='log');ax.legend(loc='lower right')
    colorbar=fig.colorbar(scat,ax=ax,label='Raw SKR (bits/use)')
    colorbar.solids.set_rasterized(False)
    finish(fig,'fig_3_MB_sampled_landscape_48deg','182 actually evaluated sites at 48 degrees; scatter colors only, no interpolation')
    fig,axes=plt.subplots(1,3,figsize=(7.1,2.5))
    for ax,scheme,key,label,limit in zip(axes,['Optimized MB','Optimized MB','Optimized Uniform'],
        ['best_VA','best_nu_raw','best_VA'],['MB $V_A$ (SNU)','$\\nu_{\\rm raw}$','Uniform $V_A$ (SNU)'],[8,None,12]):
        frame(ax);sub=[r for r in audit if r['scheme']==scheme];x=[int(r['zenith_deg']) for r in sub];y=[float(r[key]) for r in sub]
        ax.plot(x,y,'-o',color='#1f4b7a',ms=2.8,mfc='white',mew=.6)
        if limit:
            b=[r for r in sub if float(r[key])==limit]
            ax.plot([int(r['zenith_deg']) for r in b],[limit]*len(b),'s',color='#a54127',ms=3,mfc='none')
            ax.axhline(limit,ls='--',color='.5',lw=.6)
        ax.set(xlabel='Zenith angle (degrees)',ylabel=label);ax.set_xticks([0,20,40,60])
    finish(fig,'fig_D_historical_optimal_parameters','Historical winning parameters; open red squares mark VA upper catalog bounds')
    with (OUT/'figure_manifest.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(manifest[0]));w.writeheader();w.writerows(manifest)
    with (OUT/'data/plotted_rate_samples.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(points[0]));w.writeheader();w.writerows(points)
    print(json.dumps(dict(vector_figures=len(manifest),line_plot_samples=len(points),new_evaluations=0)))


if __name__=='__main__':
    main()
