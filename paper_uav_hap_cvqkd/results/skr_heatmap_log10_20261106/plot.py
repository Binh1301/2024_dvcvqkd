"""Logarithmic color scale for the saved MB map; no SKR evaluations."""
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from matplotlib.ticker import LogFormatterMathtext, NullFormatter
import numpy as np

OUT=Path(__file__).resolve().parent
SOURCE=OUT.parent/'skr_zenith_heatmap_20261106/skr_map.npz'
digest=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
with np.load(SOURCE,allow_pickle=False) as data:
    x=data['x_m']/1000
    y=data['y_m']/1000
    z=data['K_raw_bits_per_use']
assert z.shape==(51,51) and np.isfinite(z).all() and np.all(z>0)
vmin=10.**np.floor(np.log10(z.min()))
vmax=10.**np.ceil(np.log10(z.max()))
norm=LogNorm(vmin=vmin,vmax=vmax)
assert np.isclose(norm(np.sqrt(vmin*vmax)),.5)
plt.rcParams.update({'font.family':'serif','font.size':10,'axes.labelsize':11})
fig,ax=plt.subplots(figsize=(5.5,4.5))
image=ax.pcolormesh(x,y,z,shading='nearest',cmap='viridis',norm=norm)
ax.plot(1,1,'x',color='black',ms=7,mew=1.4,label='HAP projection / center')
ax.set(xlabel='UAV horizontal X (km)',ylabel='UAV horizontal Y (km)',
       xlim=(0,2),ylim=(0,2),aspect='equal')
ax.legend(loc='upper right',fontsize=8,framealpha=.85)
cbar=fig.colorbar(image,ax=ax,pad=.035,ticks=[vmin,vmax],format=LogFormatterMathtext(base=10))
cbar.ax.yaxis.set_minor_formatter(NullFormatter())
cbar.set_label('MB SKR (bits/use), log scale')
fig.tight_layout()
fig.savefig(OUT/'skr_heatmap_log10.png',dpi=300,facecolor='white')
plt.close(fig)
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==digest
(OUT/'validation.json').write_text(json.dumps(dict(status='CURRENTLY_VERIFIED_PASS',
    source=str(SOURCE),source_sha256=digest,color_normalization='LogNorm, base-10 ticks',
    color_limits=[float(vmin),float(vmax)],points=int(z.size),
    min_SKR=float(z.min()),max_SKR=float(z.max()),center_SKR=float(z[25,25]),
    original_data_changed=False,new_SKR_evaluations=0),indent=2)+'\n')
