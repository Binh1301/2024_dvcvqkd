"""Plot saved signed SKR on a true base-10 Y axis; no scientific evaluations."""
import csv
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np

OUT=Path(__file__).resolve().parent
SOURCE=OUT.parent/'skr_zenith_heatmap_20261106/skr_vs_zenith.csv'
before=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
with SOURCE.open(encoding='utf-8',newline='') as f:
    rows=list(csv.DictReader(f))
plt.rcParams.update({'font.family':'serif','font.size':10,'axes.labelsize':11})
fig,ax=plt.subplots(figsize=(6.1,4.0))
displayed=0
for family,color in [('Uniform','#2864a0'),('MB','#b54c2f')]:
    data=[r for r in rows if r['scheme']==family]
    x=np.array([float(r['zenith_deg']) for r in data])
    raw=np.array([float(r['K_raw_bits_per_use']) for r in data])
    positive=raw>0
    displayed+=int(positive.sum())
    if positive.any():
        ax.plot(x,np.where(positive,raw,np.nan),color=color,lw=1.7,label=family+' (best-tested catalog)')
    else:
        ax.add_line(Line2D([],[],color=color,lw=1.7,label=family+' (no positive samples)'))
ax.set_yscale('log',base=10)
ax.set(xlabel='Zenith angle (degrees)',ylabel='SKR (bits/use)',
       xlim=(0,max(float(r['zenith_deg']) for r in rows)),ylim=(1e-5,1e-3))
ax.grid(which='major',alpha=.25);ax.legend(fontsize=9,loc='lower left')
fig.tight_layout()
assert ax.get_yscale()=='log' and ax.yaxis.get_transform().base==10
assert len(rows)==64 and displayed==16
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==before
fig.savefig(OUT/'skr_vs_zenith_log10.png',dpi=300,facecolor='white')
plt.close(fig)
(OUT/'validation.json').write_text(json.dumps(dict(status='CURRENTLY_VERIFIED_PASS',
    source=str(SOURCE),source_sha256=before,axis_scale='log',base=10,
    original_rows=len(rows),displayed_positive_rows=displayed,nonpositive_rows_hidden=len(rows)-displayed,
    original_data_changed=False,new_SKR_evaluations=0),indent=2)+'\n')
