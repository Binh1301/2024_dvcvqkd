"""Render saved continuous attenuation diagnostics only, without RNG/cloud runs."""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import time
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
plt.rcParams.update({'font.family':'DejaVu Serif','font.size':10,
    'axes.labelsize':10,'axes.titlesize':11,'legend.fontsize':8,
    'pdf.fonttype':42,'ps.fonttype':42,'savefig.dpi':400,
    'axes.spines.top':False,'axes.spines.right':False})


def rows(out,name):
    with (out/name).open(encoding='utf-8') as stream: return list(csv.DictReader(stream))


def plot(out):
    started=time.perf_counter()
    cfg=json.loads((out/'configuration.json').read_text())
    meta=json.loads((out/'metadata.json').read_text())
    source=ROOT/cfg['input_npz']
    expected=meta['source_sha256']
    if hashlib.sha256(source.read_bytes()).hexdigest()!=expected:
        raise ValueError('Saved Gaussian source changed')
    with np.load(source,allow_pickle=False) as d: g=d['X']
    with np.load(out/'cloud_clwc.npz',allow_pickle=False) as d: l=d['clwc_g_m3']
    with np.load(out/'cloud_attenuation_db.npz',allow_pickle=False) as d: a=d['attenuation_db']
    with np.load(out/'cloud_transmittance.npz',allow_pickle=False) as d: t=d['transmittance']
    slots=cfg['snapshot_slots'];times=np.arange(len(g))
    receipts=[]

    def save(fig,name):
        fig.savefig(out/(name+'.png'),dpi=400,facecolor='white')
        fig.savefig(out/(name+'.pdf'),facecolor='white')
        plt.close(fig)
        receipts.append(name)

    def maps(z,name,title,units,cmap,limits,extra):
        fig,axs=plt.subplots(2,4,figsize=(13.6,7.2),layout='constrained')
        for ax,k in zip(axs.flat,slots):
            im=ax.imshow(z[k],origin='lower',extent=[0,2,0,2],cmap=cmap,
                vmin=limits[0],vmax=limits[1],interpolation='nearest',rasterized=True)
            ax.set(title=f'k = {k} s',xlabel='x (km)',ylabel='y (km)')
        ax=axs.flat[-1]
        # Shared bins and actual counts include the atom at zero (or T=1).
        ax.hist(z.ravel(),bins=70,color='#386887',histtype='stepfilled',alpha=.8,
                weights=np.full(z.size,1/z.size))
        ax.set(xlabel=units,ylabel='Probability per bin',title='All cells and slots')
        ax.grid(alpha=.15)
        fig.colorbar(im,ax=list(axs.flat[:7]),label=units,shrink=.85,pad=.015)
        fig.suptitle(title+'\n'+extra,fontsize=13)
        save(fig,name)

    maps(g,'figure_A_gaussian_cloud','A. Saved stationary Gaussian cloud field',
         'Dimensionless G','RdBu_r',(-np.max(abs(g)),np.max(abs(g))),
         'Unchanged input; wind (-5, 0) m/s; no new Gaussian simulation')
    maps(l,'figure_B_illustrative_clwc','B. Illustrative cloud liquid-water content',
         r'CLWC (g m$^{-3}$)','Blues',(0,l.max()),
         r'UNCALIBRATED: $L=0.1\max(G-\gamma_0,0)$; fixed $\gamma_0$')
    maps(a,'figure_C_continuous_attenuation','C. Continuous-valued cloud attenuation',
         'Cloud attenuation (dB)','magma',(0,a.max()),
         'UNCALIBRATED: 1550 nm; N = 100 cm^-3; H = 0.5 km; vertical reference')
    maps(t,'figure_D_cloud_transmittance','D. Cloud power transmittance',
         r'$T_{\mathrm{cloud}}$','viridis',(0,1),
         r'UNCALIBRATED: $T=10^{-A/10}$; consistent full [0, 1] display scale')

    stats=rows(out,'time_statistics.csv')
    ref=[r for r in stats if r['scenario']==cfg['primary_scenario']]
    spatial,temporal=rows(out,'spatial_correlation.csv'),rows(out,'temporal_correlation.csv')
    cdf=rows(out,'empirical_cdf.csv')
    ecdf=[r for r in cdf if r['scenario']==cfg['primary_scenario']]
    fig,axs=plt.subplots(3,3,figsize=(14,10),layout='constrained')
    ax=axs[0,0];ax.plot(times,[float(r['mean_db']) for r in ref],color='#136a8a')
    ax.set(title='Mean attenuation',xlabel='Time (s)',ylabel='Mean A (dB)')
    ax=axs[0,1];ax.plot(times,[float(r['max_db']) for r in ref],color='#b24936')
    ax.set(title='Maximum attenuation',xlabel='Time (s)',ylabel='Max A (dB)')
    ax=axs[0,2]
    ax.boxplot([a[k].ravel() for k in slots],tick_labels=[str(k) for k in slots],
               showfliers=False,widths=.6)
    ax.set(title='Spatial distributions at selected slots',xlabel='Slot k (s)',ylabel='A (dB)')
    ax.text(.98,.98,'Boxes: quartiles; whiskers: 1.5 IQR\nOutlier markers omitted only here',
            transform=ax.transAxes,va='top',ha='right',fontsize=7)
    colors=dict(G='#555555',L='#2e9a70',A='#ad413c',T='#3b67ad')
    for field in ['G','L','A','T']:
        for column,axis in [(0,'x'),(1,'y')]:
            sub=[r for r in spatial if r['field']==field and r['axis']==axis]
            axs[1,column].plot([float(r['lag_m']) for r in sub],[float(r['pearson_r']) for r in sub],
                marker='.',label=field,color=colors[field])
        sub=[r for r in temporal if r['field']==field]
        axs[1,2].plot([float(r['lag_s']) for r in sub],[float(r['pearson_r']) for r in sub],
                marker='.',label=field,color=colors[field])
    for j in [0,1]: axs[1,j].set(title=f'Pooled spatial correlation ({["x","y"][j]})',xlabel='Separation (m)',ylabel='Pearson r')
    axs[1,2].set(title='Pooled Eulerian temporal correlation',xlabel='Lag (s)',ylabel='Pearson r')
    for ax in axs[1]: ax.legend(ncol=2)
    histogram=rows(out,'attenuation_histogram.csv')
    left=np.array([float(r['left_db']) for r in histogram]);right=np.array([float(r['right_db']) for r in histogram])
    ax=axs[2,0];ax.bar(left,[float(r['probability']) for r in histogram],width=right-left,align='edge',color='#477692')
    ax.set(title='All-space/time attenuation histogram',xlabel='A (dB)',ylabel='Probability per bin',yscale='log')
    ax=axs[2,1];ax.plot([float(r['attenuation_db']) for r in ecdf],[float(r['cdf']) for r in ecdf],color='#ad413c')
    ax.vlines(0,0,np.mean(a==0),color='#ad413c')
    ax.set(title='Empirical CDF, including A=0 atom',xlabel='A (dB)',ylabel='P(A <= a)',ylim=(0,1.02))
    ax=axs[2,2]
    for k in slots:
        weights=np.full(a[k].size,1/a[k].size)
        ax.hist(a[k].ravel(),bins=30,range=(0,a.max()),weights=weights,histtype='step',label=str(k))
    ax.set(title='Spatial histograms by slot',xlabel='A (dB)',ylabel='Probability per bin',yscale='log');ax.legend(ncol=3,title='Slot k')
    for ax in axs.flat: ax.grid(alpha=.17)
    fig.suptitle('E. Empirical attenuation statistics - one correlated mission, no iid confidence intervals\n'
                 'G: Gaussian; L: CLWC; A: loss; T: transmittance. All physical parameters uncalibrated.',fontsize=13)
    save(fig,'figure_E_attenuation_statistics')

    groups=[['L0_low','reference','L0_high'],['H_thin','reference','H_thick'],['N_low','reference','N_high']]
    fig,axs=plt.subplots(2,3,figsize=(13.5,7.6),layout='constrained')
    lookup={s['name']:s for s in cfg['scenarios']}
    for j,(group,title) in enumerate(zip(groups,['CLWC scale L0 (g/m^3)','Layer thickness H (km)','Droplet concentration N (cm^-3)'])):
        for name,color in zip(group,['#277b91','#333333','#bd4d3c']):
            sub=[r for r in stats if r['scenario']==name];s=lookup[name]
            value=s[['l0_g_m3','thickness_km','droplet_cm3'][j]]
            label=f'{value:g}'
            axs[0,j].plot([float(r['time_s']) for r in sub],[float(r['mean_db']) for r in sub],label=label,color=color)
            sub=[r for r in cdf if r['scenario']==name]
            axs[1,j].plot([float(r['attenuation_db']) for r in sub],[float(r['cdf']) for r in sub],label=label,color=color)
        axs[0,j].set(title=title,xlabel='Time (s)',ylabel='Spatial mean A (dB)')
        axs[1,j].set(xlabel='A (dB)',ylabel='Empirical CDF',ylim=(0,1.02))
        for ax in axs[:,j]:ax.legend(title=title.split('(')[0].strip());ax.grid(alpha=.17)
    fig.suptitle('F. ILLUSTRATIVE, UNCALIBRATED physical scenarios\n'
        'Same saved G and fixed gamma; vary one parameter, hold the other two at reference values',fontsize=13)
    save(fig,'figure_F_physical_scenarios')

    fig,axs=plt.subplots(3,1,figsize=(12,8),sharex=True,layout='constrained')
    for ax,(iy,ix),color in zip(axs,cfg['probe_indices_yx'],['#136a8a','#a24a3e','#477947']):
        ax.plot(times,a[:,iy,ix],lw=.9,color=color)
        ax.set(ylabel='A (dB)',title=f'Fixed cloud-layer coordinate x={(ix+.5)*40:.0f} m, y={(iy+.5)*40:.0f} m')
        ax.grid(alpha=.17);ax.set_ylim(0,a.max()*1.03)
    axs[-1].set_xlabel('Time (s)')
    fig.suptitle('G. Attenuation at fixed cloud-layer coordinates\n'
                 'Combined wind advection and AR(1) evolution; vertical reference, uncalibrated',fontsize=13)
    save(fig,'figure_G_attenuation_time_series')

    # Fixed global palette and scale. Row reversal gives physical y upward.
    cmap=matplotlib.colormaps['magma']
    palette=(cmap(np.linspace(0,1,252))[:,:3]*255).astype(np.uint8).ravel().tolist()
    palette+= [255,255,255,0,0,0,160,160,160,220,220,220]
    font=ImageFont.load_default(size=13)
    frames=[]
    vmax=float(a.max())
    for k in range(len(a)):
        frame=Image.new('P',(370,360),252);frame.putpalette(palette)
        indices=np.rint(np.flipud(a[k])/vmax*251).astype(np.uint8)
        field=Image.fromarray(np.repeat(np.repeat(indices,6,axis=0),6,axis=1))
        field.putpalette(palette);frame.paste(field,(20,42))
        draw=ImageDraw.Draw(frame)
        draw.text((10,3),f'Illustrative A (dB); k={k:03d} s',font=font,fill=253)
        draw.text((10,20),'1550 nm; vertical H=0.5 km; y up',font=font,fill=253)
        for r in range(300):
            draw.line((331,42+r,343,42+r),fill=int(round((299-r)/299*251)))
        draw.text((322,345),f'0 - {vmax:.1f}',font=font,fill=253)
        draw.text((20,345),'x: 0 - 2 km; y: 0 - 2 km',font=font,fill=253)
        frames.append(frame)
    frames[0].save(out/'cloud_continuous_attenuation.gif',save_all=True,
        append_images=frames[1:],duration=50,loop=0,optimize=False,disposal=2)
    receipt={'plotter_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
             'figures':receipts,'PNG_dpi':400,'GIF_frames':len(frames),'GIF_duration_ms':50,
             'GIF_field_bbox_xyxy':[20,42,320,342],'GIF_palette_colors':252,
             'attenuation_color_min_max_db':[0,vmax],
             'source_unchanged':hashlib.sha256(source.read_bytes()).hexdigest()==expected,
             'render_seconds':time.perf_counter()-started,'only_saved_data':True}
    (out/'render_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',type=Path)
    plot(p.parse_args().output.resolve())
