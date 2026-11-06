"""Readable saved-data heatmaps: full data range and variation from center."""
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from matplotlib.ticker import ScalarFormatter
import numpy as np

OUT=Path(__file__).resolve().parent
SOURCE=OUT.parent/'skr_zenith_heatmap_20261106/skr_map.npz'
digest=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
with np.load(SOURCE,allow_pickle=False) as data:
    x=data['x_m']/1000; y=data['y_m']/1000
    z=data['K_raw_bits_per_use'].copy()
assert z.shape==(51,51) and np.isfinite(z).all() and np.all(z>0)
center=float(z[25,25]); relative=100*(z-center)/center
assert relative[25,25]==0 and np.isclose(relative.min(),100*(z.min()/center-1))
plt.rcParams.update({'font.family':'serif','font.size':10,'axes.labelsize':10,
                     'savefig.facecolor':'white','figure.facecolor':'white',
                     'pdf.fonttype':42,'ps.fonttype':42})


def panel(fig,ax,kind):
    if kind=='absolute':
        image=ax.pcolormesh(x,y,z,shading='nearest',cmap='viridis',vmin=z.min(),vmax=z.max())
        levels=np.array([7.5,7.6,7.7,7.8,7.9])*1e-4
        levels=levels[(levels>z.min())&(levels<z.max())]
        contours=ax.contour(x,y,z,levels=levels,colors='white',linewidths=.65)
        ax.clabel(contours,inline=True,fontsize=7,fmt=lambda v:f'{v*1e4:.2f}')
        bar=fig.colorbar(image,ax=ax,pad=.025,fraction=.047)
        fmt=ScalarFormatter(useMathText=True);fmt.set_powerlimits((-4,-4));fmt.set_useOffset(False)
        bar.formatter=fmt;bar.update_ticks()
        bar.set_label('MB asymptotic SKR (bits/use)')
        ax.set_title('(a) Absolute SKR — full data range',fontsize=10,pad=10)
    else:
        limit=float(np.abs(relative).max())
        image=ax.pcolormesh(x,y,relative,shading='nearest',cmap='coolwarm',
                            norm=TwoSlopeNorm(vmin=-limit,vcenter=0.,vmax=limit))
        contours=ax.contour(x,y,relative,levels=[-5,-4,-3,-2,-1],colors='0.3',linewidths=.6)
        ax.clabel(contours,inline=True,fontsize=7,fmt=lambda v:f'{v:g}%')
        bar=fig.colorbar(image,ax=ax,pad=.025,fraction=.047,ticks=[-6,-4,-2,0,2,4,6])
        bar.set_label(r'Change from center $\Delta R/R_0$ (%)')
        ax.set_title('(b) Relative variation from center',fontsize=10,pad=10)
    ax.plot(1,1,'x',color='black',ms=7,mew=1.5)
    ax.annotate('HAP projection',xy=(1,1),xytext=(1.03,1.10),fontsize=7.5,
                bbox=dict(facecolor='white',edgecolor='none',alpha=.82,pad=2))
    ax.set(xlabel='UAV horizontal X (km)',ylabel='UAV horizontal Y (km)',
           xlim=(0,2),ylim=(0,2),aspect='equal',xticks=np.arange(0,2.01,.5),yticks=np.arange(0,2.01,.5))
    ax.tick_params(labelsize=9)


for kind,name in [('absolute','skr_heatmap_absolute'),('relative','skr_heatmap_relative')]:
    fig,ax=plt.subplots(figsize=(5.6,4.6),layout='constrained')
    panel(fig,ax,kind)
    fig.savefig(OUT/(name+'.png'),dpi=300)
    fig.savefig(OUT/(name+'.pdf'))
    plt.close(fig)
fig,axes=plt.subplots(1,2,figsize=(10.8,4.6),layout='constrained')
panel(fig,axes[0],'absolute');panel(fig,axes[1],'relative')
fig.savefig(OUT/'skr_heatmap_absolute_relative.png',dpi=300)
fig.savefig(OUT/'skr_heatmap_absolute_relative.pdf')
plt.close(fig)
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==digest
(OUT/'validation.json').write_text(json.dumps(dict(status='CURRENTLY_VERIFIED_PASS',
    source=str(SOURCE),source_sha256=digest,points=int(z.size),
    min_SKR=float(z.min()),max_SKR=float(z.max()),center_SKR=center,
    relative_min_percent=float(relative.min()),relative_max_percent=float(relative.max()),
    absolute_color_limits=[float(z.min()),float(z.max())],percentile_clipping=False,
    original_data_changed=False,new_SKR_evaluations=0,
    contour_interpolation='Visualization of level sets between existing nodes only',
    scientific_label='Asymptotic, no finite-size correction'),indent=2)+'\n')
