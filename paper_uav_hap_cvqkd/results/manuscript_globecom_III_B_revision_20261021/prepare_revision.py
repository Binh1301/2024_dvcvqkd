"""Prepare a document revision using saved CSVs; no scientific solver imports."""
from pathlib import Path
import csv
import hashlib
import json
import re
import shutil
import subprocess

import fitz
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
BASE = ROOT / 'results/manuscript_ieee_overleaf_20261021'
FINAL = ROOT / 'results/mobility_parameter_sensitivity_final_20261020'
STYLE = ROOT / 'results/ieee_classic_restyled_figures_20261021'
REFERENCE = Path('C:/Users/admin/Downloads/2026__QKD_Sensing_Globecom.pdf')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path):
    with path.open(encoding='utf-8', newline='') as stream:
        return list(csv.DictReader(stream))


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')


def main():
    if (OUT/'validation/final_receipt.json').exists():
        raise FileExistsError('Sealed revision is immutable')
    for name in ['figures', 'data', 'validation', 'references']:
        (OUT/name).mkdir(exist_ok=True)
    # Preserve the startup snapshot once, before creating document assets.
    snapshot = OUT/'startup_manifest.json'
    if not snapshot.exists():
        protected = {}
        for folder in ['src', 'configs', 'tests', 'docs', '.agent', 'results']:
            for path in (ROOT/folder).rglob('*'):
                if path.is_file() and OUT not in path.parents and not any(
                    part in ('__pycache__', '.pytest_cache') for part in path.parts
                ):
                    protected[path.relative_to(ROOT).as_posix()] = sha(path)
        git = {}
        for key, args in [('branch', ['branch','--show-current']), ('head',['rev-parse','HEAD']),
                          ('status',['status','--short']), ('diff',['diff'])]:
            result = subprocess.run(['git',*args], cwd=ROOT, capture_output=True, text=True)
            git[key] = result.stdout
        write_json(snapshot, dict(git=git, protected_sha256=protected))

    authenticated = []
    for name in ['manuscript_ieee_overleaf_20261021', 'manuscript_ieee_compact_20261020',
                 'manuscript_ieee_revision_20261020', 'mobility_parameter_sensitivity_final_20261020',
                 'mobility_parameter_sensitivity_stage_b_20261020',
                 'mobility_parameter_sensitivity_20261020', 'ieee_classic_restyled_figures_20261021']:
        folder = ROOT/'results'/name
        receipt = json.loads((folder/'validation/final_receipt.json').read_text(encoding='utf-8'))
        for member, digest in receipt['artifact_sha256'].items():
            path = ROOT/member if member.split('/')[0] in ('src','scripts','configs','docs','tests','results','.agent') else folder/member
            data=path.read_bytes()
            raw=hashlib.sha256(data).hexdigest()
            newline_only=False
            if raw != digest:
                data.decode('utf-8')
                assert b'\0' not in data
                newline_only=hashlib.sha256(data.replace(b'\r\n',b'\n')).hexdigest()==digest
            assert raw==digest or newline_only, ('historical content mismatch', name, member)
            authenticated.append(dict(receipt=name, member=member, historical_sha256=digest,
                current_sha256=raw,comparison='CRLF_ONLY_CONTENT_IDENTICAL' if newline_only else 'RAW_SHA256_MATCH'))
    write_json(OUT/'validation/authenticated_inputs.json', authenticated)
    assert sha(REFERENCE) == '04fbdd7d6bce2642888e730f75ddc04523874458d847057c93a5476457bd52b2'
    shutil.copyfile(REFERENCE, OUT/'references/globecom_reference.pdf')
    ref = fitz.open(REFERENCE)
    inspections = []
    for index in [3,4,5]:
        ref[index].get_pixmap(matrix=fitz.Matrix(1.3,1.3)).save(OUT/f'references/page_{index+1:02d}.png')
        inspections.append(dict(page=index+1, text=ref[index].get_text()))
    write_json(OUT/'references/inspection.json', inspections)
    for name in ['main.tex', 'main.pdf']:
        shutil.copyfile(BASE/name, OUT/f'validation/baseline_{name.replace(".","_")}')
    old = fitz.open(BASE/'main.pdf')
    for index in range(len(old)):
        old[index].get_pixmap(matrix=fitz.Matrix(1.2,1.2)).save(OUT/f'validation/baseline_page_{index+1:02d}.png')

    config = json.loads((ROOT/'configs/manuscript_mobility.json').read_text())
    assert config['optical']['receiver_diameter_m'] == .08
    assert config['optical']['full_divergence_rad'] == 233e-6
    assert config['mission'] == dict(slots=30, slot_duration_s=20, max_speed_m_per_s=15)
    shutil.copyfile(ROOT/'configs/manuscript_mobility.json', OUT/'data/manuscript_mobility.json')
    findings = json.loads((FINAL/'verified_findings.json').read_text())
    for name in ['verified_findings.json', 'tables/statistical_comparison.csv',
                 'tables/paired_improvements.csv']:
        shutil.copyfile(FINAL/name, OUT/'data'/Path(name).name)
    files = ['fig1_candidate_positions_data.csv','fig2_cloud_blockage_data.csv',
             'fig3_temporal_correlation_data.csv','fig4_skr_mobility_tradeoff_data.csv']
    datasets = {}
    for name in files:
        shutil.copyfile(FINAL/'figures'/name, OUT/'data'/name)
        datasets[name] = read_csv(OUT/'data'/name)

    # Only headings change in the protected scientific prefix. Restore these
    # exact replacements to prove every preceding byte is unchanged.
    original = (BASE/'main.tex').read_text(encoding='utf-8')
    prefix = original.split(r'\section{Optimization Problem}',1)[0]
    assert prefix != original
    heading_edits = [
        (r'\subsection{Recorded Physical-Layer Model and Security Boundary}\n\label{sec:security}'.replace('\\n','\n'),
         r'\section{Recorded Physical-Layer Model}'),
        ('Specifically, the saved MI kernel uses the normalized likelihood',
         '\\section{SKR Performance Analysis}\n\\subsection{Recorded Rate and Security Boundary}\n\\label{sec:security}\nSpecifically, the saved MI kernel uses the normalized likelihood'),
    ]
    revised = prefix
    for before, after in heading_edits:
        assert revised.count(before) == 1, before
        revised = revised.replace(before,after,1)
    recovered = revised
    for before, after in reversed(heading_edits):
        recovered = recovered.replace(after,before,1)
    assert recovered == prefix
    (OUT/'validation/protected_prefix_original.tex.txt').write_text(prefix,encoding='utf-8')
    (OUT/'validation/protected_prefix_revised.tex.txt').write_text(revised,encoding='utf-8')
    write_json(OUT/'validation/heading_edits.json', heading_edits)
    bibliography = original[original.index('% Generated by IEEEtran.bst'):]
    body = (OUT/'revised_sections.tex').read_text(encoding='utf-8')
    # Geometry diagnostics are non-rendering and stay at the revision boundary.
    diagnostics = r'\typeout{REVISION_LAYOUT textheight=\the\textheight;columnwidth=\the\columnwidth;textwidth=\the\textwidth;topmargin=\the\topmargin;headheight=\the\headheight;headsep=\the\headsep;voffset=\the\voffset}'+'\n'
    (OUT/'main.tex').write_text(revised+diagnostics+body+bibliography,encoding='utf-8')
    write_json(OUT/'validation/prefix_preservation.json',dict(
        original_prefix_sha256=hashlib.sha256(prefix.encode()).hexdigest(),
        scientific_prefix_restored_byte_for_byte=(recovered==prefix),
        bibliography_sha256=hashlib.sha256(bibliography.encode()).hexdigest(),
        actual_source_of_external_original_pdf_authenticated=False,
        source='latest sealed single-file Overleaf revision; newer GLOBECOM directory is unfinished',
        heading_exception='Two section headings establish II/III, one subsection establishes III.A; no prose or equation changed',
        security_status=config['security_status'], lifecycle=config['lifecycle']))

    plt.rcParams.update({'font.family':'serif','font.serif':['Times New Roman'],
        'font.size':8,'axes.labelsize':8,'xtick.labelsize':7,'ytick.labelsize':7,
        'legend.fontsize':7,'mathtext.fontset':'stix','axes.linewidth':.65,
        'lines.linewidth':.9,'pdf.fonttype':42,'ps.fonttype':42,'savefig.facecolor':'white'})
    style = {'Stationary':('#1f4b7a','o','-'), 'Greedy':('#a54127','^','--'), 'DP':('#21634c','D','-.')}
    plots = []
    def draw(ax, filename, metric, xlabel, ylabel, panel, scale=1):
        all_rows = datasets[filename]
        for method in style:
            rows = sorted([r for r in all_rows if r['metric']==metric and r['method']==method],key=lambda r:float(r['x']))
            assert rows and all(float(r['lambda_bits_per_use'])==9.468026677248516e-6 for r in rows)
            x=np.array([float(r['x']) for r in rows]); y=np.array([float(r['y']) for r in rows])*scale
            lo=np.array([float(r['ci95_low']) for r in rows])*scale
            hi=np.array([float(r['ci95_high']) for r in rows])*scale
            color,marker,ls=style[method]
            line,=ax.plot(x,y,color=color,marker=marker,ls=ls,ms=3.4,mfc='white',mew=.7,label=method)
            ax.fill_between(x,lo,hi,color=color,alpha=.10,lw=0)
            assert np.array_equal(line.get_xdata(),x) and np.array_equal(line.get_ydata(),y)
            for r in rows:
                plots.append(dict(output_panel=panel,source_csv=filename,**r))
        ax.set(xlabel=xlabel,ylabel=ylabel,facecolor='white')
        ax.grid(True,ls=':',lw=.45,color='.72'); ax.set_axisbelow(True)
        ax.tick_params(direction='in',width=.6,length=2.5)
        for spine in ax.spines.values(): spine.set_color('black')
        ax.legend(loc='upper left',frameon=True,edgecolor='.65',facecolor='white',framealpha=.95,borderpad=.35,handlelength=2.3)
        ax.margins(x=.035)

    fig, ax=plt.subplots(figsize=(3.48,2.16))
    draw(ax,files[1],'unavailability_percent','Cloud blockage probability, $p$','Zero-rate unavailability (%)','Fig. 2')
    ax.set_xticks(np.arange(.1,.9,.1)); ax.set_ylim(bottom=0)
    fig.subplots_adjust(left=.16,right=.985,bottom=.23,top=.97)
    for ext in ['pdf','png']:
        fig.savefig(OUT/f'figures/fig2_cloud_unavailability.{ext}',dpi=350)
    plt.close(fig)
    fig, axes=plt.subplots(1,2,figsize=(7.14,2.37))
    draw(axes[0],files[0],'U','Candidate positions, $J$','Mean objective (bit/use)','Fig. 3(a)')
    axes[0].ticklabel_format(axis='y',style='sci',scilimits=(-4,-4),useMathText=True)
    axes[0].set_xticks([10,20,40,60,80,100])
    axes[0].legend(loc='lower right',frameon=True,edgecolor='.65',fontsize=7)
    draw(axes[1],files[2],'D','Latent temporal correlation, $\\rho$','Mean travel distance (m)','Fig. 3(b)')
    axes[1].set_xticks([0,.3,.6,.9,.98]); axes[1].set_xticklabels(['0','0.3','0.6','0.9','0.98'])
    axes[1].set_ylim(bottom=-20); axes[1].legend(loc='upper right',frameon=True,edgecolor='.65',fontsize=7)
    for ax,panel in zip(axes,['(a)','(b)']): ax.text(.5,-.32,panel,transform=ax.transAxes,ha='center',va='top',fontsize=8)
    fig.subplots_adjust(left=.087,right=.987,bottom=.29,top=.92,wspace=.36)
    for ext in ['pdf','png']:
        fig.savefig(OUT/f'figures/fig3_parameter_sensitivity.{ext}',dpi=350)
    plt.close(fig)
    with (OUT/'data/plotted_points.csv').open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(plots[0])); writer.writeheader(); writer.writerows(plots)
    index=read_csv(STYLE/'figure_index.csv')
    manifest=[]
    for output, source, metric, source_figure in [
        ('fig2_cloud_unavailability.pdf',files[1],'unavailability_percent','fig2_cloud_blockage'),
        ('fig3_parameter_sensitivity.pdf',files[0],'U','fig1_candidate_positions'),
        ('fig3_parameter_sensitivity.pdf',files[2],'D','fig3_temporal_correlation')]:
        record=next(r for r in index if r['figure']==source_figure and '00_final' in r['pdf'])
        manifest.append(dict(output='figures/'+output,output_sha256=sha(OUT/'figures'/output),
            source_csv=(FINAL/'figures'/source).relative_to(ROOT).as_posix(),source_sha256=sha(FINAL/'figures'/source),
            local_csv='data/'+source,selected_metric=metric,latest_verified_restyled_pdf=record['pdf'],
            action='REPLOT_EXACT_SAVED_MEANS_AND_CI; NO_SOLVER_OR_RNG',
            source_receipt='results/mobility_parameter_sensitivity_final_20261020/validation/final_receipt.json'))
    with (OUT/'figure_manifest.csv').open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(manifest[0]));writer.writeheader();writer.writerows(manifest)
    inputs=[BASE/'main.tex', BASE/'main.pdf', ROOT/'configs/manuscript_mobility.json',
            REFERENCE, FINAL/'verified_findings.json', ROOT/'docs/FINAL_MODEL_SPEC.md']
    inputs.extend(FINAL/'figures'/name for name in files)
    write_json(OUT/'input_manifest.json',{str(p):sha(p) for p in inputs})
    print(json.dumps(dict(authenticated_members=len(authenticated), plotted_points=len(plots),
        protected_files=len(json.loads(snapshot.read_text())['protected_sha256']),scientific_evaluations=0)))


if __name__ == '__main__':
    main()
