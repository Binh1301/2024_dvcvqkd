"""Plot the saved diagnostic tables only; no scientific evaluator imports."""
import csv
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.ticker import AutoMinorLocator
import numpy as np

OUT = Path(__file__).resolve().parent
RECORDS = []
COLORS = ['#1f4e79','#b84623','#222222','#6b4980']
MARKERS = ['o','^','s','D']
STYLES = ['-','--','-.',':']


def read(name, **selection):
    with (OUT/name).open(encoding='utf-8',newline='') as f:
        rows = list(csv.DictReader(f))
    return [r for r in rows if all(r[k]==str(v) for k,v in selection.items())]


def line(ax, name, ykey, label, index=0, *, xkey='zenith_deg', positive=False, selection=None):
    selection = selection or {}
    rows = read(name,**selection)
    x,y = np.array([float(r[xkey]) for r in rows]),np.array([float(r[ykey]) for r in rows])
    if positive:
        y = np.where(y>0,y,np.nan)
    obj, = ax.plot(x,y,label=label,color=COLORS[index%4],marker=MARKERS[index%4],
                   linestyle=STYLES[index%4],mfc='white',mew=.65,ms=3.1,lw=.95)
    obj.set_gid(json.dumps(dict(csv=name,x=xkey,y=ykey,positive_mask=positive,selection=selection)))
    return obj


def axes(n=1, rows=1, size=None):
    size = size or ((3.5,2.6) if n==1 else (7.16,2.7 if rows==1 else 4.7))
    fig, axs = plt.subplots(rows,n//rows,figsize=size,layout='constrained',squeeze=False)
    flat = list(axs.flat)
    for i,ax in enumerate(flat):
        ax.set_xlabel('Zenith angle (deg)')
        ax.set_xlim(0,60)
        ax.set_xticks(np.arange(0,61,15))
        ax.xaxis.set_minor_locator(AutoMinorLocator(3))
        ax.tick_params(which='both',direction='in',top=True,right=True,width=.6)
        ax.grid(True,which='major',ls=':',lw=.5,color='.78')
        ax.grid(True,which='minor',ls=':',lw=.3,color='.90')
        ax.set_axisbelow(True)
        if n>1:
            ax.text(.98,1.02,f'({chr(97+i)})',transform=ax.transAxes,va='bottom',ha='right',fontsize=8)
    return fig,flat


def finish(name,fig,axs):
    meta = dict(name=name,figsize_inches=list(fig.get_size_inches()),axes=[])
    for ax in axs:
        if ax.get_yscale()=='linear':
            ax.ticklabel_format(axis='y',style='sci',scilimits=(-2,3),useMathText=True)
            ax.yaxis.set_minor_locator(AutoMinorLocator(2))
        handles,labels = ax.get_legend_handles_labels()
        if labels:
            ax.legend(loc='best',fontsize=6.4,framealpha=.96,edgecolor='.6',fancybox=False,
                      borderpad=.3,handlelength=2.2,labelspacing=.25)
        numeric = []
        for obj in ax.get_lines():
            if not obj.get_gid():
                continue
            y = np.asarray(obj.get_ydata(),dtype=float)
            numeric.append(dict(source=json.loads(obj.get_gid()),label=obj.get_label(),
                x=list(map(float,obj.get_xdata())),y=[float(v) if np.isfinite(v) else None for v in y],
                marker=obj.get_marker(),linestyle=obj.get_linestyle()))
        meta['axes'].append(dict(xscale=ax.get_xscale(),yscale=ax.get_yscale(),
            xlabel=ax.get_xlabel(),ylabel=ax.get_ylabel(),curves=numeric))
    for ext in ['pdf','png']:
        fig.savefig(OUT/'figures'/f'{name}.{ext}',dpi=350,facecolor='white')
    plt.close(fig)
    RECORDS.append(meta)


def main():
    if (OUT/'render_receipt.json').exists():
        raise FileExistsError('Completed figures are immutable')
    times = Path('C:/Windows/Fonts/times.ttf')
    if times.exists():
        font_manager.fontManager.addfont(str(times))
    plt.rcParams.update({'font.family':'serif','font.serif':['Times New Roman','STIXGeneral','DejaVu Serif'],
        'font.size':8,'axes.labelsize':8,'xtick.labelsize':7,'ytick.labelsize':7,
        'axes.linewidth':.65,'axes.edgecolor':'black','axes.labelcolor':'black',
        'figure.facecolor':'white','axes.facecolor':'white','savefig.facecolor':'white',
        'pdf.fonttype':42,'ps.fonttype':42,'mathtext.fontset':'stix','legend.fontsize':6.4})
    for log in [True,False]:
        fig,axs = axes()
        for i,(key,label) in enumerate([('Uniform_K_raw','Uniform (catalog)'),('Fixed_MB_K_raw','MB (fixed)'),
                                         ('Optimized_MB_K_raw','MB (catalog)')]):
            line(axs[0],'diagnostic_summary.csv',key,label,i,positive=log)
        axs[0].set_ylabel('Raw SKR (bit/use)')
        if log:
            axs[0].set_yscale('log')
            axs[0].set_ylim(5e-6,1.2e-3)
        else:
            axs[0].axhline(0,color='.35',lw=.6)
        finish('fig_01_original_semilog' if log else 'fig_02_raw_signed',fig,axs)

    fig,axs = axes(2)
    line(axs[0],'channel_parameters.csv','distance_km',r'$L$',0)
    axs[0].set_ylabel('Propagation distance (km)')
    line(axs[1],'channel_parameters.csv','eta_atm',r'$\eta_{\rm atm}$',1)
    axs[1].set_ylabel('Atmospheric transmittance')
    finish('fig_A_geometry_atmosphere',fig,axs)

    fig,axs = axes(4,2)
    for i,(key,label) in enumerate([('wL_m',r'$w_L$'),('w_eff_m',r'$w_{\rm eff}$'),('w_eq_m',r'$w_{\rm eq}$')]):
        line(axs[0],'channel_parameters.csv',key,label,i)
    axs[0].set_ylabel('Beam radius (m)')
    for i,(key,label) in enumerate([('sigma_s_squared_m2',r'$\sigma_s^2$'),('sigma_h_squared_m2',r'$\sigma_h^2$'),
                                   ('angular_jitter_variance_m2',r'$(L\theta_{\rm jt})^2$')]):
        line(axs[1],'channel_parameters.csv',key,label,i)
    axs[1].set_ylabel(r'Displacement variance (m$^2$)')
    line(axs[2],'channel_parameters.csv','A0',r'$A_0$',0)
    axs[2].set_ylabel('Maximum collection fraction')
    line(axs[3],'channel_parameters.csv','chi2',r'$d=w_{\rm eq}^2/(4\sigma_s^2)$',1)
    axs[3].set_ylabel('Pointing shape parameter')
    finish('fig_B_beam_pointing',fig,axs)

    fig,axs = axes(3)
    line(axs[0],'channel_parameters.csv','lognormal_log_variance',r'$v_{\log}=\sigma_R^2$',0)
    axs[0].set_ylabel('Rytov / lognormal log variance')
    line(axs[1],'channel_parameters.csv','scintillation_index',r'$\exp(v_{\log})-1$',1)
    axs[1].set_ylabel('Scintillation index')
    line(axs[2],'channel_parameters.csv','P0',r'$P_0$ (outage)',2)
    axs[2].set_ylabel('AoA outage probability')
    axs[2].set_ylim(0,2.2e-4)
    finish('fig_C_scintillation_outage',fig,axs)

    fig,axs = axes(3)
    line(axs[0],'channel_moments.csv','mean_T',r'$\langle T\rangle$',0)
    line(axs[0],'channel_moments.csv','T_eff',r'$T_f$',1)
    axs[0].set_ylabel('Power transmittance')
    line(axs[1],'channel_moments.csv','variance_sqrt_T',r'${\rm Var}(\sqrt{T})$',2)
    axs[1].set_ylabel(r'${\rm Var}(\sqrt{T})$')
    line(axs[2],'channel_moments.csv','R_f',r'$R_f$',3)
    axs[2].set_ylabel('Relative fading penalty')
    finish('fig_D_channel_moments',fig,axs)

    fig,axs = axes(3)
    line(axs[0],'noise_decomposition.csv','xi_fading',r'$\xi_{\rm fading}$',0)
    line(axs[0],'noise_decomposition.csv','xi_f',r'$\xi_f$',1)
    axs[0].set_ylabel('Input-referred excess (SNU)')
    line(axs[1],'noise_decomposition.csv','xi_physical',r'$\xi_{\rm physical}$',2)
    axs[1].set_ylabel('Input-referred excess (SNU)')
    for i,(key,label) in enumerate([('N_total',r'$N$'),('N_fading',r'$N_{\rm fading}$'),('N_physical',r'$N_{\rm physical}$')]):
        line(axs[2],'noise_decomposition.csv',key,label,i)
    axs[2].set_ylabel('Output-referred excess (SNU)')
    finish('fig_E_noise_decomposition',fig,axs)

    fig,axs = axes(3)
    for ax,key,label in zip(axs,['beta_I_AB','chi_BE','K_raw'],[r'$\beta I_{AB}^{2D}$',r'$\chi_{BE}^{\rm hom}$',r'$K=\beta I_{AB}^{2D}-\chi_{BE}^{\rm hom}$']):
        line(ax,'skr_decomposition.csv',key,label,axs.index(ax),selection={'scheme':'Fixed MB'})
        ax.set_ylabel('Information / rate (bit/use)')
    axs[2].axhline(0,color='.35',lw=.6)
    finish('fig_F_MI_Holevo_SKR',fig,axs)

    fig,axs = axes(2)
    line(axs[0],'source_optimization_effect.csv','Fixed_MB_K_raw','MB (fixed)',0)
    line(axs[0],'source_optimization_effect.csv','Optimized_MB_K_raw','MB (catalog)',1)
    axs[0].axhline(0,color='.35',lw=.6)
    axs[0].set_ylabel('Raw SKR (bit/use)')
    line(axs[1],'source_optimization_effect.csv','optimization_gain',r'$K_{\rm opt}-K_{\rm fixed}$',2)
    axs[1].set_ylabel('Source-selection gain (bit/use)')
    finish('fig_G_source_optimization',fig,axs)

    fig,axs = axes(2)
    for i,(prefix,label) in enumerate([('Uniform','Uniform (catalog)'),('Fixed_MB','MB (fixed)'),('Optimized_MB','MB (catalog)')]):
        line(axs[0],'source_optimization_effect.csv',prefix+'_VA',label,i)
        line(axs[1],'source_optimization_effect.csv',prefix+'_nu_raw',label,i)
    axs[0].set_ylabel(r'Modulation variance $V_A$ (SNU)')
    axs[1].set_ylabel(r'MB parameter $\nu_{\rm raw}$')
    finish('fig_H_selected_source_parameters',fig,axs)

    fig,axs = axes(2)
    line(axs[0],'skr_decomposition.csv','K_raw','Original fixed MB',0,selection={'scheme':'Fixed MB'})
    line(axs[0],'controlled_diagnostics.csv','K_raw','Fading shape fixed at 30 deg',1,
         selection={'check':'A_frozen_normalized_fading_at_30deg'})
    axs[0].axhline(0,color='.35',lw=.6)
    axs[0].set_ylabel('Raw SKR (bit/use)')
    line(axs[1],'controlled_diagnostics.csv','K_raw','Nonfading, matched mean T',2,
         selection={'check':'C_deterministic_matched_mean_T'})
    axs[1].set_ylabel('Raw SKR (bit/use)')
    finish('fig_I_controlled_diagnostics',fig,axs)

    fig,axs = axes(size=(3.5,2.7))
    for i,(key,label) in enumerate([('log_total',r'$\log(1+R_f)$'),('log_pointing','Pointing'),
                                    ('log_scintillation','Scintillation'),('log_outage','AoA outage')]):
        line(axs[0],'fading_factor_decomposition.csv',key,label,i)
    axs[0].set_yscale('log')
    axs[0].set_ylim(1e-4,.3)
    axs[0].set_ylabel('Additive log-factor contribution')
    finish('fig_J_relative_fading_factors',fig,axs)
    digest = lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    receipt = dict(style='CLASSIC_IEEE_TIMES',font=font_manager.findfont('Times New Roman'),
        producer_sha256=digest(Path(__file__)),scientific_evaluators_called=False,
        csv_sha256={p.name:digest(p) for p in OUT.glob('*.csv')},figures=RECORDS)
    (OUT/'render_receipt.json').write_text(json.dumps(receipt,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print('Rendered',len(RECORDS),'vector PDF / PNG 350 dpi pairs from saved diagnostic CSV only')


if __name__=='__main__':
    main()
