"""Reproduce the IEEE2019 reference-aircraft Figure02 without a mission run.

python -m uav_qkd.rotor_power_figure --output figures/ieee_2019
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from .rotor_reference import load_reference, power_components, characteristic_speeds

ROOT = Path(__file__).resolve().parents[2]
STEM = 'fig02_propulsion_power_ieee2019'


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _source_verification(config):
    source = config['source']
    audit_path=ROOT/source['parameter_audit']
    with audit_path.open(encoding='utf-8') as f:
        audit=json.load(f)
    if _sha(config['_config_path'])!=audit['reference_config_sha256']:
        raise ValueError('Aircraft profile differs from the source-verified IEEE2019 configuration snapshot')
    if source['pdf_sha256']!=audit['sha256'] or source['doi']!=audit['doi']:
        raise ValueError('Configured source identity differs from the parameter verification audit')
    path = Path(source['local_pdf'])
    if not path.is_file():
        return dict(status='PENDING_SOURCE_FILE_VERIFICATION', path=str(path), sha256=None)
    actual = _sha(path)
    if actual != source['pdf_sha256']:
        raise ValueError('IEEE2019 source PDF hash differs from the manually inspected source')
    return dict(status='CURRENTLY_VERIFIED_PASS', path=str(path), sha256=actual,
                parameter_audit=str(audit_path.resolve()), parameter_audit_sha256=_sha(audit_path),
                reference_config_sha256=audit['reference_config_sha256'],
                basis='Manual DOI/equation/Section V/Table I inspection; current PDF and raw-parameter profile match verified snapshots')


def plot_reference(reference, speeds, column='single'):
    """Four native power curves with computed hover/ME/MR markers."""
    if column not in ('single', 'double'):
        raise ValueError('Column must be single or double')
    plt.rcParams.update({'font.family':'serif', 'font.serif':['Times New Roman','DejaVu Serif'],
                         'mathtext.fontset':'stix', 'font.size':7.5, 'axes.labelsize':7.5,
                         'xtick.labelsize':6.5, 'ytick.labelsize':6.5, 'legend.fontsize':7,
                         'axes.linewidth':.6, 'pdf.fonttype':42, 'ps.fonttype':42})
    width=3.5 if column=='single' else 7.16
    fig,ax=plt.subplots(figsize=(width,3.05),facecolor='white')
    params=reference['params']
    count=reference['config']['numerics']['plot_samples']
    if isinstance(count,bool) or int(count)!=count or count<3:
        raise ValueError('Plot sample count must be an integer >=3')
    v=np.linspace(0,params.v_max,int(count))
    parts=power_components(v,params)
    for key,label,color,style,lw in [
        ('total_W',r'$P_{\mathrm{total}}$', 'black','-',1.7),
        ('blade_profile_W','Blade profile','#0072b2','--',1.1),
        ('induced_W','Induced','#d55e00','-.',1.1),
        ('parasite_W','Parasite','#009e73',':',1.2)]:
        ax.plot(v,parts[key],label=label,color=color,linestyle=style,linewidth=lw)
    hover=reference['derived']['hover_power_W']
    ax.scatter([0],[hover],s=20,marker='o',color='black',clip_on=False,zorder=5)
    ax.annotate(f'Hovering power\n{hover:.2f} W',xy=(0,hover),xytext=(.03,.61),textcoords='axes fraction',
                fontsize=6.8,ha='left',arrowprops=dict(arrowstyle='-',lw=.6,color='black'))
    for kind,marker,offset in [('ME','v',(.32,.51)),('MR','D',(.60,.78))]:
        point=speeds[kind]
        ax.scatter([point['speed_m_s']],[point['power_W']],s=22,marker=marker,color='black',zorder=5)
        label=rf'$V_{{\mathrm{{{kind}}}}}$'+f" = {point['speed_m_s']:.2f} m/s"
        ax.annotate(label,xy=(point['speed_m_s'],point['power_W']),xytext=offset,textcoords='axes fraction',
                    fontsize=6.8,ha='center',arrowprops=dict(arrowstyle='-',lw=.6,color='black'))
    ax.set(xlabel='UAV speed (m/s)',ylabel='Propulsion power (W)',xlim=(0,params.v_max),
           ylim=(0,1.1*float(parts['total_W'].max())))
    ax.legend(loc='upper left',frameon=False)
    fig.tight_layout()
    return fig,v,parts


def export_figure(profile_path, output, *, column='single'):
    output=Path(output)
    if output.exists() and any(output.iterdir()):
        raise FileExistsError('Refusing to overwrite a nonempty output directory; choose a new path')
    reference=load_reference(profile_path)
    config=reference['config']
    if config['name']!='ieee_2019':
        raise ValueError('This Figure02 requires the explicitly named ieee_2019 profile')
    verification=_source_verification(config)
    settings=config['numerics']
    speeds=characteristic_speeds(reference['params'],grid_samples=settings['grid_samples'],
                                  xatol=settings['optimizer_xatol_m_s'])
    fig,v,parts=plot_reference(reference,speeds,column)
    source_status=verification['status']
    if source_status!='CURRENTLY_VERIFIED_PASS':
        fig.text(.5,.01,'EXPLORATORY: SOURCE FILE VERIFICATION PENDING',ha='center',fontsize=5.5,color='#a00000')
        fig.tight_layout(rect=(0,.06,1,1))
    output.mkdir(parents=True,exist_ok=True)
    try:
        for extension in ('pdf','png'):
            fig.savefig(output/f'{STEM}.{extension}',dpi=600,facecolor='white')
    finally:
        plt.close(fig)
    data_path=output/f'{STEM}.csv'
    with data_path.open('w',newline='',encoding='utf-8') as f:
        writer=csv.writer(f)
        writer.writerow(['speed_m_s','total_W','blade_profile_W','induced_W','parasite_W'])
        writer.writerows(zip(v,parts['total_W'],parts['blade_profile_W'],parts['induced_W'],parts['parasite_W']))
    caption=(
        'Figure 02. Rotary-Wing UAV Propulsion Power Versus Flight Speed. '
        'Total, blade-profile, induced and parasite powers are computed from Eq.(12), '
        'with coefficients derived from Eq.(64) using the rounded Table I aircraft parameters '
        'of Zeng, Xu and Zhang, IEEE Transactions on Wireless Communications, 18(4), '
        '2329-2345, April 2019, doi:10.1109/TWC.2019.2902559. '
        'The speed limit is 30 m/s from Section V. The induced velocity is derived '
        f"as {reference['derived']['v0_derived_m_s']:.9f} m/s; Table I reports its rounded value 4.03 m/s. "
        'ME minimizes P(V); MR minimizes P(V)/V over positive speed. Both are found by '
        'grid-bracketed bounded numerical refinement and checked against a dense sweep. '
        'This is a reference-aircraft model illustration, not a measurement or a CV-QKD mission result.')
    if source_status!='CURRENTLY_VERIFIED_PASS':
        caption='EXPLORATORY: local source-file verification pending. '+caption
    (output/f'{STEM}.caption.txt').write_text(caption+'\n',encoding='utf-8')
    manifest=dict(status='READY' if source_status=='CURRENTLY_VERIFIED_PASS' else 'EXPLORATORY',
                  source_variant=config['name'],source=config['source'],source_verification=verification,
                  configuration=config,derived=reference['derived'],characteristic_speeds=speeds,
                  column=column,width_in=3.5 if column=='single' else 7.16,png_dpi=600,
                  paper_mode='NOT_RUN',scope='Reference rotor model only; no QKD/cloud/mission or security promotion',
                  inputs={str(Path(profile_path).resolve()):_sha(profile_path)},
                  producers={str(ROOT/'src/uav_qkd'/name):_sha(ROOT/'src/uav_qkd'/name)
                             for name in ('propulsion.py','rotor_reference.py','rotor_power_figure.py')},
                  caption=caption,outputs={})
    for extension in ('pdf','png','csv','caption.txt'):
        path=output/f'{STEM}.{extension}'
        manifest['outputs'][extension]=dict(path=str(path.resolve()),sha256=_sha(path))
    (output/f'{STEM}.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')
    return manifest


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile',default='configs/rotor/ieee_2019.yaml')
    parser.add_argument('--output',default='figures/ieee_2019')
    parser.add_argument('--column',choices=['single','double'],default='single')
    args=parser.parse_args(argv)
    try:
        result=export_figure(args.profile,args.output,column=args.column)
    except (ValueError,KeyError,OSError,RuntimeError) as error:
        parser.exit(2,f'Reference figure error: {error}\n')
    print(json.dumps(dict(status=result['status'],derived=result['derived'],speeds=result['characteristic_speeds']),indent=2))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
