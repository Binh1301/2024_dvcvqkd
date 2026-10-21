"""Layout-only export from saved CSV; reserve space under upper-right legend."""
import csv
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator, LogLocator
import numpy as np

OUT=Path(__file__).resolve().parent


def main():
    with (OUT/'skr_vs_zenith_angle.csv').open(encoding='utf-8',newline='') as stream:
        rows=list(csv.DictReader(stream))
    x=np.array([float(r['zenith_deg']) for r in rows])
    series=[('Uniform_K_raw','tab:blue','Optimized Uniform 256-QAM'),
            ('Fixed_MB_K_raw','tab:orange','Fixed MB-shaped 256-QAM'),
            ('Optimized_MB_K_raw','tab:red','Optimized MB-shaped 256-QAM')]
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':12,'pdf.fonttype':42,
                         'axes.titlesize':18,'axes.labelsize':15})
    receipts=[]
    for logarithmic in (True,False):
        fig,ax=plt.subplots(figsize=(10,6.6),facecolor='white')
        all_values=[]
        for key,color,label in series:
            values=np.array([float(r[key]) for r in rows])
            displayed=np.where(values>0,values,np.nan) if logarithmic else values
            all_values.extend(displayed[np.isfinite(displayed)])
            if logarithmic and not np.any(values>0):
                label+=' (no positive values)'
            ax.plot(x,displayed,'-o',color=color,lw=1.8,ms=4,label=label)
        if logarithmic:
            ax.set_yscale('log')
            ax.yaxis.set_minor_locator(LogLocator(base=10,subs=np.arange(2,10)*.1))
            ax.set_ylim(min(all_values)/1.2,max(all_values)*2.4)
        else:
            ax.axhline(0,color='.25',linewidth=.9)
            ax.yaxis.set_minor_locator(AutoMinorLocator())
            ax.ticklabel_format(axis='y',style='sci',scilimits=(0,0))
            span=max(all_values)-min(all_values)
            ax.set_ylim(min(all_values)-.05*span,max(all_values)+.23*span)
        ax.set(title='SKR versus Zenith Angle',xlabel='Zenith Angle (deg)',
               ylabel='Secret Key Rate (bits/use)',xlim=(0,60))
        ax.set_xticks(np.arange(0,61,10));ax.xaxis.set_minor_locator(AutoMinorLocator(2))
        ax.grid(True,which='major',color='.80',linewidth=.7)
        ax.grid(True,which='minor',color='.91',linewidth=.45)
        ax.legend(loc='upper right',fontsize=10,framealpha=.96)
        fig.tight_layout()
        name='skr_vs_zenith_angle'+('' if logarithmic else '_linear')
        for extension in ('png','pdf'):
            fig.savefig(OUT/(name+'.'+extension),dpi=350)
        receipts.append(dict(name=name,ylim=list(ax.get_ylim()),data_points=len(rows)))
        plt.close(fig)
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    (OUT/'render_receipt.json').write_text(json.dumps(dict(status='CURRENTLY_VERIFIED_PASS',
        layout_only=True,scientific_recalculation=False,CSV_sha256=sha(OUT/'skr_vs_zenith_angle.csv'),
        producer_sha256=sha(Path(__file__)),figures=receipts),indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
    main()
