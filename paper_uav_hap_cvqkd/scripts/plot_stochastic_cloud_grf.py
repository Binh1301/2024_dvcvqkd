"""A-H cloud figures and all-slot GIF from saved arrays only."""
from pathlib import Path
import argparse,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from scipy.stats import norm,t
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[1]


def save(fig,out,name):
    for ext in ('png','pdf'):fig.savefig(out/f'{name}.{ext}',dpi=400,bbox_inches='tight')
    plt.close(fig)


def map_panel(ax,array,title,extent,limits,binary=False):
    im=ax.imshow(array,origin='lower',extent=extent,aspect='equal',interpolation='nearest',
                 cmap=ListedColormap(['black','white']) if binary else 'viridis',vmin=limits[0],vmax=limits[1])
    ax.set(title=title,xlabel='x (km)',ylabel='y (km)');return im


def render(out):
    d=np.load(out/'cloud_fields.npz',allow_pickle=False);e=np.load(out/'ensemble_validation.npz',allow_pickle=False)
    frozen=np.load(out/'frozen_fields.npz',allow_pickle=False)
    meta=json.loads(str(d['parameters_json']));c=meta['parameters'];r=json.loads((out/'validation.json').read_text())
    X=d['latent_field'];I=d['relative_intensity'];mask=d['diagnostic_mask'];snaps=e['snapshot_slots'];times=d['time_s']
    plt.rcParams.update({'font.family':'serif','font.size':9,'pdf.fonttype':42,'ps.fonttype':42,'lines.linewidth':1.15})
    extent=(0,c['nx']*c['dx_m']/1000,0,c['ny']*c['dy_m']/1000)
    xlim=float(np.max(abs(X)));imax=float(max(I.max(),frozen['relative_intensity'].max()))
    fig,ax=plt.subplots(1,3,figsize=(12.5,3.35),layout='constrained')
    h=np.linspace(-800,800,81);cov=np.exp(-np.hypot(h[:,None],h[None,:])/c['ell_c_m'])
    im=ax[0].imshow(cov,origin='lower',extent=(-.8,.8,-.8,.8),cmap='viridis',vmin=0,vmax=1)
    ax[0].set(title='Exponential target covariance',xlabel='x separation (km)',ylabel='y separation (km)')
    fig.colorbar(im,ax=ax[0],shrink=.75,label='Covariance')
    im=map_panel(ax[1],X[0],'Initial Gaussian field',extent,(-xlim,xlim));fig.colorbar(im,ax=ax[1],shrink=.75,label='Latent G (a.u.)')
    bins=e['histogram_edges'];centres=(bins[:-1]+bins[1:])/2;width=np.diff(bins)
    for k,col in zip((0,400,999),('#2166ac','#1b9e77','#b2182b')):
        if k in snaps:
            j=list(snaps).index(k);ax[2].stairs(e['histogram'][:,j].mean(0)/width,bins,label=f'k={k}',color=col)
    ax[2].stairs(np.diff(norm.cdf(bins))/width,bins,color='black',linestyle='--',label='N(0,1), same bins')
    ax[2].set(xlim=(-4,4),xlabel='Latent G',ylabel='Histogram density',title='Ensemble marginal histograms');ax[2].legend(fontsize=7)
    save(fig,out,'figure_A_covariance_initial_GRF')
    fig,ax=plt.subplots(1,2,figsize=(7.2,3.3),layout='constrained')
    im=map_panel(ax[0],I[0],'Initial relative intensity',extent,(0,imax));fig.colorbar(im,ax=ax[0],shrink=.8,label='Relative Cloud Intensity (a.u.)')
    im=map_panel(ax[1],mask[0],'Initial presence diagnostic',extent,(0,1),True)
    cb=fig.colorbar(im,ax=ax[1],shrink=.8);cb.set_ticks([0,1],labels=['Clear','Cloud'])
    save(fig,out,'figure_B_intensity_presence')
    fig,axs=plt.subplots(2,4,figsize=(11.8,6.1),layout='constrained')
    for ax,k in zip(axs.flat,snaps):im=map_panel(ax,X[k],f'k={k}, t={k*c["dt_s"]:g} s',extent,(-xlim,xlim))
    axs.flat[-1].set_axis_off();fig.colorbar(im,ax=list(axs.flat)[:len(snaps)],shrink=.7,label='Latent G (a.u.)')
    fig.suptitle(f'Fixed observation ROI; vx={c["vx_m_s"]:g} m/s')
    save(fig,out,'figure_C_spatial_snapshots')
    names=list(e['metric_names']);metrics=e['metrics'];means=metrics.mean(0)
    ci=t.ppf(.975,len(metrics)-1)*metrics.std(0,ddof=1)/np.sqrt(len(metrics))
    fig,axs=plt.subplots(2,3,figsize=(10.4,6.2),layout='constrained')
    for ax,k in zip(axs[0],(0,400,999)):
        im=map_panel(ax,I[k],f'Relative intensity, k={k}',extent,(0,imax))
    fig.colorbar(im,ax=list(axs[0]),shrink=.7,label='Relative intensity (a.u.)')
    for name,label in [('component_count','8-connected components')]:
        j=names.index(name);axs[1,0].plot(times,metrics[0,:,j],color='#aaaaaa',lw=.7,label='Main seed')
        axs[1,0].plot(times,means[:,j],label='Ensemble mean');axs[1,0].fill_between(times,means[:,j]-ci[:,j],means[:,j]+ci[:,j],alpha=.2)
        axs[1,0].set(xlabel='Time (s)',ylabel=label);axs[1,0].legend(fontsize=7)
    for name,color,label in [('mean_area_m2','#2166ac','Mean component area'),('max_area_m2','#b2182b','Largest component area')]:
        j=names.index(name);axs[1,1].plot(times,metrics[0,:,j]/1e6,color=color,label=label)
    axs[1,1].set(xlabel='Time (s)',ylabel='Area (km²)');axs[1,1].legend(fontsize=7)
    import csv
    tracks=list(csv.DictReader((out/'track_segments.csv').open()))
    main_tracks=[v for v in tracks if int(v['seed'])==c['seed']]
    spans=[float(v['observed_span_s']) for v in main_tracks]
    shifted=np.array(spans)+c['dt_s']
    axs[1,2].hist(shifted,bins=np.geomspace(c['dt_s'],max(shifted.max(),2*c['dt_s']),22),color='#2166ac')
    axs[1,2].set(xlabel='Observed span + dt (s)',ylabel='Segments',xscale='log',yscale='log',title='Censored / ambiguous segments included')
    save(fig,out,'figure_D_intensity_morphology')
    fig,axs=plt.subplots(3,1,figsize=(7.6,7.0),sharex=True,layout='constrained')
    for ax,name,label,target in zip(axs,['mean','variance','cloud_fraction'],['Latent ROI mean','Latent ROI variance','Diagnostic cloud fraction'],[0,r['expected_ROI_population_variance'],c['initial_fraction']]):
        j=names.index(name);ax.plot(times,metrics[0,:,j],color='#aaaaaa',lw=.7,label='Main seed')
        ax.plot(times,means[:,j],color='#2166ac',label=f'Mean of {len(metrics)} seeds')
        ax.fill_between(times,means[:,j]-ci[:,j],means[:,j]+ci[:,j],color='#2166ac',alpha=.18,label='Approx. 95% seed-level CI')
        ax.axhline(target,color='#b2182b',ls='--',lw=.8,label='Theoretical expectation');ax.set_ylabel(label);ax.grid(alpha=.15)
    axs[0].legend(ncol=2,fontsize=7);axs[-1].set_xlabel('Time (s)')
    save(fig,out,'figure_E_time_statistics')
    fig,ax=plt.subplots(figsize=(6.5,4),layout='constrained')
    lags=e['spatial_lags_cells'];distance=np.hypot(lags[:,0]*c['dx_m'],lags[:,1]*c['dy_m'])
    dense=np.linspace(0,max(distance),300);ax.plot(dense/1000,np.exp(-dense/c['ell_c_m']),'k-',label='exp(-distance / ell_c)')
    for ti,color,mark,label in [(0,'#2166ac','o','Initial ensemble'),(1,'#1b9e77','s','Final ensemble')]:
        val=e['spatial_covariance'][:,ti];err=t.ppf(.975,len(val)-1)*val.std(0,ddof=1)/np.sqrt(len(val))
        ax.errorbar(distance/1000,val.mean(0),yerr=err,fmt=mark,color=color,capsize=2,ms=4,label=label)
    ax.set(xlabel='Separation (km)',ylabel='Latent covariance',title='Spatial covariance: axial and diagonal lags');ax.legend();ax.grid(alpha=.15)
    save(fig,out,'figure_F_spatial_covariance')
    fig,axs=plt.subplots(1,2,figsize=(10.2,3.8),layout='constrained')
    lags=e['temporal_lags'];dense=np.linspace(0,max(lags)*c['dt_s'],400)
    vals=e['material_correlation'];err=t.ppf(.975,len(vals)-1)*vals.std(0,ddof=1)/np.sqrt(len(vals))
    axs[0].plot(dense,np.exp(-dense/c['tau_c_s']),'k-',label='Theory: rho^lag')
    axs[0].errorbar(lags*c['dt_s'],vals.mean(0),yerr=err,fmt='o',color='#2166ac',capsize=3,ms=4,label='Motion-compensated ensemble')
    axs[0].set(xlabel='Lag (s)',ylabel='Material-frame autocorrelation');axs[0].legend(fontsize=7)
    h=e['h_xy_m'];st=e['space_time_covariance'];lag_index=list(lags).index(8)
    targets=[(-200,0),(-40,0),(0,0),(40,0),(200,0)];indices=[list(map(tuple,h)).index(v) for v in targets]
    hx=np.array([v[0] for v in targets]);val=st[:,lag_index,indices]
    err=t.ppf(.975,len(val)-1)*val.std(0,ddof=1)/np.sqrt(len(val))
    theory=c['rho'] if 'rho' in c else meta['rho']
    curve=np.linspace(-220,220,300)
    axs[1].plot(curve,theory**8*np.exp(-abs(curve-c['vx_m_s']*8*c['dt_s'])/c['ell_c_m']),'k-',label='R(h,8) theory')
    axs[1].errorbar(hx,val.mean(0),yerr=err,fmt='o',color='#2166ac',capsize=3,label='Ensemble covariance')
    axs[1].axvline(-40,color='#b2182b',ls='--',lw=.8,label='Peak h = v*8 s = -40 m')
    axs[1].set(xlabel='h_x from earlier to later point (m)',ylabel='Space-time covariance');axs[1].legend(fontsize=7)
    for ax in axs:ax.grid(alpha=.15)
    save(fig,out,'figure_G_temporal_space_time')
    fig,axs=plt.subplots(2,2,figsize=(8.4,6.8),layout='constrained')
    for ax,array,title in [(axs[0,0],frozen['relative_intensity'][-1],'Frozen field, final relative intensity'),(axs[0,1],I[-1],'Evolving field, final relative intensity')]:
        im=map_panel(ax,array,title,extent,(0,imax))
    fig.colorbar(im,ax=list(axs[0]),shrink=.7,label='Relative intensity (a.u.)')
    axs[1,0].plot(times,(frozen['latent_field']>meta['theta_c_actual']).mean((1,2)),label='Frozen, rho=1')
    axs[1,0].plot(times,mask.mean((1,2)),label='Evolving, rho<1');axs[1,0].set(xlabel='Time (s)',ylabel='Eulerian ROI cloud fraction');axs[1,0].legend(fontsize=7)
    mse=metrics[:,:,names.index('material_RMS_change')]**2
    mean=mse.mean(0);half=t.ppf(.975,len(mse)-1)*mse.std(0,ddof=1)/np.sqrt(len(mse))
    axs[1,1].plot(times,mean,color='#2166ac',label='Evolving ensemble MSE');axs[1,1].fill_between(times,mean-half,mean+half,alpha=.18)
    axs[1,1].plot(times,2*(1-np.exp(-times/c['tau_c_s'])),'k--',label='Theory: 2(1-rho^k)')
    axs[1,1].axhline(0,color='#1b9e77',label='Frozen material MSE=0');axs[1,1].set(xlabel='Time (s)',ylabel='Material-frame mean squared change');axs[1,1].legend(fontsize=7)
    save(fig,out,'figure_H_frozen_evolving')
    palette=np.vstack([(plt.colormaps['viridis'](np.linspace(0,1,254))[:,:3]*255).astype(np.uint8),[[0,0,0],[255,255,255]]]).astype(np.uint8).ravel().tolist()
    font=ImageFont.load_default();frames=[]
    for k in range(c['slots']):
        canvas=Image.new('P',(400,234),254);canvas.putpalette(palette)
        for offset,array in [(0,np.minimum(253,np.floor(I[k]/imax*253)).astype(np.uint8)),(200,np.where(mask[k],255,254).astype(np.uint8))]:
            im=Image.fromarray(np.flipud(array));im.putpalette(palette);canvas.paste(im.resize((200,200),Image.Resampling.NEAREST),(offset,34))
        draw=ImageDraw.Draw(canvas);draw.text((4,2),f'k={k:03d}; t={times[k]:g}s; vx={c["vx_m_s"]:g} m/s',fill=255,font=font)
        draw.text((4,18),'Relative intensity',fill=255,font=font);draw.text((204,18),'Presence diagnostic',fill=255,font=font);frames.append(canvas)
    frames[0].save(out/'cloud_1000_slots.gif',save_all=True,append_images=frames[1:],duration=50,loop=0,optimize=False,disposal=2)
    print(f'Exported A-H and {len(frames)} GIF frames',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('output',type=Path,nargs='?',default=ROOT/'results/stochastic_cloud_grf_20261111')
    render(parser.parse_args().output)
