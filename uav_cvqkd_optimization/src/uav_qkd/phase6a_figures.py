"""Render sealed Phase6A diagnostic results; never optimize or generate a cloud."""
import argparse
import copy
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from .paper_figures import STYLES
from .finite_size import finite_key
from .cloud_model import CloudField, GaussianCluster
from .blockage import BlockageModel
from .phase6a_experiment import los_samples, config_hash

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'results/phase6a_baseline_20261109_rss_retry_20261110'
DEFAULT_OUTPUT=ROOT/'results/paper_figures/phase6a'
METHODS=tuple(STYLES)
MARKERS=dict(zip(METHODS,('o','s','^','D')))
LABELS={m:('DP (forecast oracle)' if m=='Pareto DP' else m) for m in METHODS}
STEMS={4:'fig4_dynamic_cloud_trajectories',5:'fig5_accumulated_key_vs_time',
       6:'fig6_energy_budget_sensitivity',7:'fig7_energy_key_tradeoff'}
CAPTIONS={
4:'UAV trajectories under dynamic cloud blockage (P2). Shading indicates sampled HAP–UAV LOS blockage for UAV coordinates on a 50-by-50 visualization grid; it is not an endpoint-cloud-cell test. Paths show saved slot endpoints up to each snapshot. Historical segments crossing a snapshot-shaded region do not imply blockage at their traversal times; continuous inter-slot LOS clearance is not certified. Cloud drift is (-5, 0) m/s. All methods share the initial point and HAP ground projection. Coincident current positions use nested markers. DP uses a perfect future-cloud forecast; greedy actions are myopic. Phase 6A numerical diagnostic, not security-certified results.',
5:'Accumulated finite-size key-yield proxy versus mission time along saved P2 trajectories. A single finite-size correction is applied to each accumulated prefix; curves are not linear ramps from terminal average rates. Phase 6A uses 100 slots of 10 s. P1 selects the same saved paths in this scenario. DP is a forecast oracle; the proxy is not a composable-security proof.',
6:'Impact of available propulsion energy on (a) P1 average key-yield proxy rate and (b) P2 accumulated key-yield proxy. Each point comes from a matched, sealed budget experiment; selected stopping times are recorded separately.',
7:'Propulsion energy versus accumulated finite-size key-yield proxy for the four saved P2 trajectories at one nonbinding budget. Percentages indicate sampled clear-LOS fractions. Points are not connected and do not define a Pareto frontier. DP produces more key while consuming more energy and has perfect future-cloud information.'}


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def write(path,value):Path(path).write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')


def validate_quantities(report,a):
    dt=float(a['dt']);m0=float(a['m0']);epsilon=float(a['epsilon']);count=0
    if len(report['runs'])!=4 or {r['method'] for r in report['runs']}!=set(METHODS):raise ValueError('Four methods required')
    for run in report['runs']:
        if run['status']!='FEASIBLE' or set(run['solutions'])!={'P1','P2'}:raise ValueError('Complete feasible P1/P2 results required')
        for obj,sol in run['solutions'].items():
            path=sol['path_indices'];q=np.asarray(sol['trajectory_m']);rows=sol['series']
            if len(rows)!=sol['K'] or len(path)!=sol['K']+1 or path[0]!=int(a['initial']):raise ValueError('Invalid saved stopping prefix')
            if sol['K']>len(a['z']) or sol['mission_time_s']!=sol['K']*dt:raise ValueError('Saved slot/time units mismatch')
            np.testing.assert_array_equal(q,a['positions'][path])
            energy=0.;u=0;acc=0.
            for k,(i,j,row) in enumerate(zip(path,path[1:],rows),1):
                if row['waypoint']!=j or (row['x_m'],row['y_m'])!=tuple(a['positions'][j]):raise ValueError('Saved prefix coordinate mismatch')
                edge=float(a['costs'][i,j]);energy+=edge;z=int(a['z'][k-1,j]);u+=z
                rate=float(a['rates'][j] if a['rates'].ndim==1 else a['rates'][k-1,j]);acc+=z*rate
                expected=finite_key(acc,u,m0,epsilon)
                expected.update(energy_j=energy,a=acc,unblocked_slots=u,blocked_slots=k-u,clear=z,
                                average_skr_bits_s=expected['key_bits']/(k*dt))
                if not np.isfinite(edge) or energy>float(a['budget']) or row['k']!=k or row['time_s']!=k*dt:raise ValueError('Invalid saved prefix feasibility/time')
                for name,val in expected.items():
                    if not np.isclose(row[name],val,rtol=1e-12,atol=1e-8):raise ValueError('Saved prefix mismatch: '+name)
                count+=1
            for name in ('key_bits','energy_j','valid_signals','asymptotic_bits','penalty_bits','average_skr_bits_s','unblocked_slots','blocked_slots'):
                if not np.isclose(sol[name],rows[-1][name],rtol=1e-12,atol=1e-8):raise ValueError('Terminal prefix mismatch: '+name)
            metric=sol['key_bits']/sol['mission_time_s'] if obj=='P1' else sol['key_bits']
            if not np.isclose(sol['objective_value'],metric,rtol=1e-12,atol=1e-8):raise ValueError('Saved objective mismatch')
            if not np.isclose(sol['average_skr_bits_s'],sol['key_bits']/sol['mission_time_s'],rtol=1e-12,atol=1e-8):raise ValueError('Saved rate/time mismatch')
    return dict(prefix_rows=count,coordinate_units='m',energy_units='J',rate_units='bits/s',key_units='bits')


def load_bundle(directory):
    directory=Path(directory).resolve()
    if not directory.is_dir():raise ValueError('A sealed result directory is required, not a demonstration CSV')
    seals=read(directory/'output_manifest.json')
    actual={str(p.relative_to(directory)).replace('\\','/') for p in directory.rglob('*') if p.is_file() and p.name!='output_manifest.json'}
    if actual!=set(seals):raise ValueError('Result seal coverage mismatch')
    for name,h in seals.items():
        path=(directory/name).resolve()
        if not path.is_relative_to(directory) or sha(path)!=h:raise ValueError('Result seal mismatch: '+name)
    config=read(directory/'config.json');report=read(directory/'results.json');inputs=read(directory/'input_manifest.json')
    if (config['mode']!='NUMERICAL_DIAGNOSTIC' or report['paper_mode']!='NOT_RUN' or report['paper_admissible'] is not False
            or report['config_sha256']!=config_hash(config)):raise ValueError('Diagnostic scope/config mismatch')
    resolutions={}
    for path,h in inputs['inputs'].items():
        if sha(path)!=h:raise ValueError('Historical input mismatch: '+path)
    for name,h in inputs['producers'].items():
        options=[ROOT/name]
        if name.replace('\\','/').endswith('/phase6a_experiment.py'):
            options += list((ROOT/'docs/phase6a_validation').glob('executed_runner*.py'))
        match=next((p for p in options if p.is_file() and sha(p)==h),None)
        if match is None:raise ValueError('Missing exact executed producer: '+name)
        resolutions[name]=str(match)
    with np.load(directory/'scenario.npz',allow_pickle=False) as data:a={k:data[k].copy() for k in data.files}
    with np.load(directory/'cloud_realization.npz',allow_pickle=False) as data:cloud={k:data[k].copy() for k in data.files}
    preflight=read(directory/'preflight.json')
    if float(a['dt'])!=config['mission']['dt_s'] or len(a['z'])!=config['mission']['slots']:raise ValueError('Config/saved time mismatch')
    if (int(cloud['seed'])!=config['cloud']['realization_seed'] or len(cloud['amplitude'])!=config['cloud']['components']
            or float(cloud['threshold_mg_m3'])!=np.percentile(cloud['field'],90,method='linear')):raise ValueError('Saved cloud realization mismatch')
    validation=validate_quantities(report,a)
    for run in report['runs']:
        folder=directory/run['method'].lower().replace(' ','_')
        for obj,sol in run['solutions'].items():
            with (folder/(obj+'_trajectory.csv')).open(encoding='utf-8',newline='') as stream:rows=list(csv.DictReader(stream))
            if len(rows)!=sol['K']+1:raise ValueError('Trajectory CSV coverage mismatch')
            for csvrow,row in zip(rows[1:],sol['series']):
                for name in ('time_s','x_m','y_m','clear','energy_j','key_bits','valid_signals','penalty_bits'):
                    if float(csvrow[name])!=row[name]:raise ValueError('CSV/JSON mismatch: '+name)
    return dict(directory=directory,report=report,config=config,preflight=preflight,arrays=a,cloud=cloud,dt=float(a['dt']),
                slots=len(a['z']),validation=validation,executed_producer_resolution=resolutions)


def snapshot_index(bundle,time):
    index=time/bundle['dt']
    if not np.isfinite(time) or time<0 or int(index)!=index or index>bundle['slots']:raise ValueError('Snapshot must be a saved slot boundary')
    return int(index)


def los_maps(bundle,times,positions):
    c=bundle['config'];g=bundle['cloud'];cloud=c['cloud'];m=c['mission']
    field=CloudField([GaussianCluster(float(a),(float(x),float(y)),(float(sx),float(sy)))
        for a,x,y,sx,sy in zip(g['amplitude'],g['component_x'],g['component_y'],g['sigma_x'],g['sigma_y'])],
        velocity=cloud['velocity_m_s'],clip_max=bundle['preflight']['cloud']['clip_max_mg_m3'])
    model=BlockageModel(field,float(g['threshold_mg_m3']),m['hap_m'],m['uav_altitude_m'],mode='layer',
        sample_spacing_m=cloud['sample_spacing_3d_m'],layer_bottom_m=cloud['layer_bottom_m'],layer_top_m=cloud['layer_top_m'])
    nodes,groups=los_samples(model,positions,cloud['sample_spacing_3d_m']);maps=[]
    for time in times:
        values=field.evaluate(nodes,time)
        maps.append([not np.any(values[index]>=model.threshold) for index in groups])
    return np.asarray(maps,dtype=np.int8)


def configure_style():
    plt.rcParams.update({'font.family':'serif','font.serif':['Times New Roman','DejaVu Serif'],
        'mathtext.fontset':'stix','font.size':8,'axes.labelsize':8,'xtick.labelsize':7,'ytick.labelsize':7,
        'legend.fontsize':7,'axes.linewidth':.6,'lines.linewidth':1.2,'pdf.fonttype':42,'ps.fonttype':42,
        'svg.fonttype':'none','savefig.facecolor':'white','axes.facecolor':'white'})


def run_for(bundle,method):return next(r for r in bundle['report']['runs'] if r['method']==method)


def key_history(bundle,method,objective):
    rows=run_for(bundle,method)['solutions'][objective]['series']
    return np.r_[0.,[r['time_s'] for r in rows]],np.r_[0.,[r['key_bits'] for r in rows]]


def plot_fig4(bundle,maps,times=(0,300,1000)):
    fig,axes=plt.subplots(1,3,figsize=(7.16,3.25),sharex=True,sharey=True)
    fig.subplots_adjust(left=.065,right=.99,bottom=.28,top=.90,wspace=.12)
    for ax,t,clear,label in zip(axes,times,maps,'abc'):
        ax.imshow(1-clear,origin='lower',extent=(0,2,0,2),cmap=matplotlib.colors.ListedColormap(['white','#d4d4d4']),
                  vmin=0,vmax=1,interpolation='nearest',rasterized=True)
        k=snapshot_index(bundle,t)
        for m in METHODS:
            q=np.asarray(run_for(bundle,m)['solutions']['P2']['trajectory_m'])[:k+1]/1000
            ax.plot(q[:,0],q[:,1],color=STYLES[m]['color'],linestyle=STYLES[m]['linestyle'],lw=1.3)
        # Nested hollow endpoint markers preserve coincident physical coordinates.
        for m,size in reversed(list(zip(METHODS,(3,5,7,9)))):
            q=np.asarray(run_for(bundle,m)['solutions']['P2']['trajectory_m'])[k]/1000
            ax.plot(*q,marker=MARKERS[m],ms=size,mfc='none',mec=STYLES[m]['color'],mew=.9,linestyle='none',clip_on=False)
        initial=bundle['arrays']['positions'][int(bundle['arrays']['initial'])]/1000
        ax.plot(*initial,'k*',ms=5)
        ax.annotate('',xy=(.12,1.86),xytext=(.70,1.86),arrowprops=dict(arrowstyle='->',lw=.7))
        ax.text(.12,1.70,'Cloud drift: 5 m/s',fontsize=6.5)
        ax.set(xlim=(0,2),ylim=(0,2),xticks=[0,1,2],yticks=[0,1,2],xlabel='$x$ (km)')
        ax.set_title(f'({label})  $t={t}$ s',fontsize=8,pad=4)
    axes[0].set_ylabel('$y$ (km)')
    handles=[Line2D([],[],color=STYLES[m]['color'],ls=STYLES[m]['linestyle'],marker=MARKERS[m],ms=4,
                      label=LABELS[m]) for m in METHODS]
    handles += [Line2D([],[],color='black',marker='*',ls='none',label='Initial / HAP projection'),
                Patch(fc='#d4d4d4',label='Blocked LOS'),Patch(fc='white',ec='.5',label='Clear LOS')]
    fig.legend(handles=handles,loc='lower center',bbox_to_anchor=(.51,.015),ncol=4,frameon=False,fontsize=6.1,
               columnspacing=1.1,handlelength=2.1)
    return fig


def plot_fig5(bundle):
    fig,ax=plt.subplots(figsize=(3.5,2.75));fig.subplots_adjust(left=.19,right=.97,bottom=.18,top=.92)
    for m in METHODS:
        t,key=key_history(bundle,m,'P2')
        ax.plot(t,key,color=STYLES[m]['color'],ls=STYLES[m]['linestyle'],marker=MARKERS[m],
                ms=3,markevery=10,mfc='white',mew=.7,label=LABELS[m])
    ax.set(xlabel='Mission time (s)',ylabel='Accumulated key-yield proxy (bits)',xlim=(0,1000),ylim=(0,84000))
    ax.ticklabel_format(axis='y',style='sci',scilimits=(0,0),useMathText=True)
    ax.grid(alpha=.18,lw=.5);ax.legend(loc='upper left',frameon=False,fontsize=6.6,title='P2 trajectories',title_fontsize=7)
    return fig


def plot_fig7(bundle):
    fig,ax=plt.subplots(figsize=(3.5,2.75));fig.subplots_adjust(left=.19,right=.97,bottom=.18,top=.92)
    offsets={'Stationary':(5,-13),'SKR-Greedy':(5,-3),'Energy-Aware Greedy':(-24,10),'Pareto DP':(-64,-3)}
    for m in METHODS:
        sol=run_for(bundle,m)['solutions']['P2']
        point=(sol['energy_j']/1000,sol['key_bits'])
        ax.scatter(*point,c=STYLES[m]['color'],marker=MARKERS[m],s=34,label=LABELS[m],zorder=3)
        ax.annotate(f"{100*sol['unblocked_slots']/sol['K']:.0f}% clear",point,xytext=offsets[m],
                    textcoords='offset points',fontsize=6.3,color=STYLES[m]['color'])
    ax.set(xlabel='Propulsion energy (kJ)',ylabel='Accumulated key-yield proxy (bits)',xlim=(168.1,171.1),ylim=(0,85000),xticks=[168.5,169.5,170.5])
    ax.ticklabel_format(axis='y',style='sci',scilimits=(0,0),useMathText=True)
    ax.grid(alpha=.18,lw=.5);ax.legend(loc='upper left',frameon=False,fontsize=6.5)
    return fig


def sweep_signature(bundle):
    c=copy.deepcopy(bundle['config']);c['mission'].pop('energy_budget_hover_multiplier',None)
    h=hashlib.sha256(json.dumps(c,sort_keys=True).encode())
    for group in (bundle['arrays'],bundle['cloud']):
        for name in sorted(group):
            if name in ('budget','data_status'):continue
            a=group[name];h.update(name.encode());h.update(repr((a.shape,str(a.dtype))).encode());h.update(a.tobytes())
    return h.hexdigest()


def validate_sweep(bundles):
    if len(bundles)<2 or len({float(b['arrays']['budget']) for b in bundles})!=len(bundles):
        raise ValueError('At least two distinct energy budgets required; no fabricated sensitivity curve')
    if len({sweep_signature(b) for b in bundles})!=1:raise ValueError('Sweep non-budget scientific inputs differ')
    return sorted(bundles,key=lambda b:float(b['arrays']['budget']))


def load_energy_sweep(directories):
    bundles=validate_sweep([load_bundle(p) for p in directories])
    if sweep_signature(bundles[0])!=sweep_signature(load_bundle(SOURCE)):raise ValueError('Sweep is not the Phase6A non-budget scenario')
    return bundles


def plot_fig6(bundles):
    bundles=validate_sweep(bundles)
    fig,axes=plt.subplots(1,2,figsize=(7.16,2.8));fig.subplots_adjust(left=.08,right=.98,bottom=.21,top=.88,wspace=.32)
    for ax,obj,label in zip(axes,('P1','P2'),('Average key-yield proxy (bits/s)','Accumulated key-yield proxy (bits)')):
        for m in METHODS:
            values=[run_for(b,m)['solutions'][obj]['objective_value'] for b in bundles]
            ax.plot([float(b['arrays']['budget'])/1000 for b in bundles],values,
                color=STYLES[m]['color'],ls=STYLES[m]['linestyle'],marker=MARKERS[m],ms=3,label=LABELS[m])
        ax.set(xlabel=r'Available energy budget $E_{\max}$ (kJ)',ylabel=label)
        ax.set_title('(a) P1' if obj=='P1' else '(b) P2',fontsize=8);ax.grid(alpha=.18)
    axes[0].legend(frameon=False,fontsize=6.4)
    return fig


def validate_output(output):
    output=Path(output).resolve()
    for protected in (SOURCE,ROOT/'results/phase6a_baseline_20261109'):
        if output==protected.resolve() or output.is_relative_to(protected.resolve()):raise ValueError('Never write into original Phase6A results')
    if output.exists() and any(output.iterdir()):raise FileExistsError('Preserve existing figure exports; choose a new directory')
    return output


def save_csv(path,rows):
    with path.open('x',encoding='utf-8',newline='') as stream:
        names=list(dict.fromkeys(k for r in rows for k in r));writer=csv.DictWriter(stream,fieldnames=names)
        writer.writeheader();writer.writerows(rows)


def export_figure(fig,number,output,bundle,extra=None):
    files=[];size=fig.get_size_inches().tolist()
    for extension in ('pdf','svg','png'):
        path=output/(STEMS[number]+'.'+extension);fig.savefig(path,dpi=600);files.append(path)
    plt.close(fig)
    provenance=dict(generation_status='GENERATED_NUMERICAL_DIAGNOSTIC',paper_ready=False,paper_admissible=False,
        figure_number=number,objective='P2' if number!=6 else 'P1/P2',source_directory=str(bundle['directory']),
        source_hashes={str(p.relative_to(bundle['directory'])):sha(p) for p in bundle['directory'].rglob('*') if p.is_file()},
        producer_sha256=sha(__file__),render_dependency_sha256={name:sha(Path(__file__).parent/name) for name in
            ('cloud_model.py','blockage.py','finite_size.py','paper_figures.py','phase6a_experiment.py')},
        software=dict(numpy=np.__version__,matplotlib=matplotlib.__version__,backend=matplotlib.get_backend()),
        figure_size_in=size,validation=bundle['validation'],units=dict(coordinates='km converted from m',energy='kJ converted from J',time='s',key='bits',rate='bits/s'),
        caption=CAPTIONS[number],outputs={p.name:sha(p) for p in files},png_dpi=600,
        limitations=['Synthetic cloud scenario','Finite-size performance proxy, not composable security',
            'DP forecast oracle vs myopic greedy','Nonbinding base energy budget','Exact only on discretized proxy graph'])
    if extra:provenance.update(extra)
    write(output/(STEMS[number]+'.json'),provenance)
    (output/(STEMS[number]+'.caption.txt')).write_text(CAPTIONS[number],encoding='utf-8')
    return provenance


def generate(output=DEFAULT_OUTPUT,energy_sweep=None):
    output=validate_output(output);bundle=load_bundle(SOURCE);configure_style()
    bundles=None
    if energy_sweep is not None:
        spec=read(energy_sweep)
        if spec.get('schema_version')!=1:raise ValueError('Unsupported energy sweep schema')
        bundles=load_energy_sweep([Path(energy_sweep).parent/r['directory'] for r in spec['runs']])
    output.mkdir(parents=True,exist_ok=True)
    times=[0,300,1000];grid=(np.arange(50)+.5)*40;X,Y=np.meshgrid(grid,grid);points=np.c_[X.ravel(),Y.ravel()]
    maps=los_maps(bundle,times,points).reshape(3,50,50)
    graph_masks=los_maps(bundle,[300,1000],bundle['arrays']['positions'])
    np.testing.assert_array_equal(graph_masks,bundle['arrays']['z'][[29,99]])
    np.savez_compressed(output/'fig4_los_maps.npz',times_s=times,clear=maps,x_m=grid,y_m=grid,
        graph_clear=graph_masks,graph_times_s=[300,1000],graph_positions_m=bundle['arrays']['positions'])
    plotted=[]
    for m in METHODS:
        for t,key in zip(*key_history(bundle,m,'P2')):plotted.append(dict(method=m,objective='P2',time_s=t,key_bits=key))
    save_csv(output/'fig5_plotted_data.csv',plotted)
    points_data=[]
    for m in METHODS:
        sol=run_for(bundle,m)['solutions']['P2']
        points_data.append(dict(method=m,objective='P2',energy_kj=sol['energy_j']/1000,key_bits=sol['key_bits'],
            clear_fraction=sol['unblocked_slots']/sol['K'],K_slots=sol['K'],duration_s=sol['mission_time_s'],
            key_bits_per_propulsion_joule=sol['key_bits']/sol['energy_j']))
    save_csv(output/'fig7_plotted_data.csv',points_data)
    manifests={}
    manifests[4]=export_figure(plot_fig4(bundle,maps),4,output,bundle,dict(snapshot_times_s=times,
        visualization_shape=[50,50],simulation_graph_shape=[11,11],LOS_3d_sampling_m=20,
        maps_source='Saved400Gaussian coefficients; reconstructed LOS only; no new realization/optimization',
        derived_map_sha256=sha(output/'fig4_los_maps.npz'),graph_snapshot_agreement=True))
    manifests[5]=export_figure(plot_fig5(bundle),5,output,bundle,dict(plotted_data_sha256=sha(output/'fig5_plotted_data.csv')))
    manifests[7]=export_figure(plot_fig7(bundle),7,output,bundle,dict(plotted_data_sha256=sha(output/'fig7_plotted_data.csv')))
    if energy_sweep is None:
        found=[]
        for path in sorted((ROOT/'results').rglob('sensitivities.csv')):
            with path.open(encoding='utf-8',newline='') as stream:rows=list(csv.DictReader(stream))
            found.append(dict(path=str(path),sha256=sha(path),rows=len(rows),
                data_status=sorted({r.get('data_status','') for r in rows}),admitted=False,
                reason='Different synthetic demonstration; not the sealed Phase6A physical/cloud/proxy scenario'))
        manifests[6]=dict(generation_status='BLOCKED_MISSING_MATCHED_ENERGY_SWEEP',paper_ready=False,
            missing='At least two distinct energy budgets with matched sealed four-method P1/P2 results',
            current_budget_j=float(bundle['arrays']['budget']),search_results=found,outputs={},caption=CAPTIONS[6],
            producer_sha256=sha(__file__),source_output_manifest_sha256=sha(bundle['directory']/'output_manifest.json'))
        write(output/(STEMS[6]+'.json'),manifests[6])
    else:
        rows=[]
        for b in bundles:
            for m in METHODS:
                for obj in ('P1','P2'):
                    sol=run_for(b,m)['solutions'][obj]
                    rows.append(dict(budget_kj=float(b['arrays']['budget'])/1000,method=m,objective=obj,K_slots=sol['K'],
                        duration_s=sol['mission_time_s'],objective_value=sol['objective_value'],source=str(b['directory'])))
        save_csv(output/'fig6_plotted_data.csv',rows)
        manifests[6]=export_figure(plot_fig6(bundles),6,output,bundle,dict(
            source_bundles=[dict(directory=str(b['directory']),manifest_sha256=sha(b['directory']/'output_manifest.json')) for b in bundles],
            plotted_data_sha256=sha(output/'fig6_plotted_data.csv')))
    write(output/'status.json',dict(figures={str(k):v['generation_status'] for k,v in manifests.items()},
        paper_ready=False,source_dt_s=bundle['dt'],source_slots=bundle['slots'],source_duration_s=bundle['dt']*bundle['slots'],
        task_context_discrepancies=['Task says dt1s/K1000slots; sealed data use dt10s/K100slots/T1000s',
            'Snapshot999s unavailable; use saved boundary1000s'],validation=bundle['validation']))
    schema=dict(schema_version=1,required=['schema_version','runs'],runs='Array of at least2 objects with directory:string (relative to this JSON)',
        directory_contract='Sealed Phase6A-format config.json/results.json/scenario.npz/cloud_realization.npz/trajectories/input_manifest/output_manifest; four methods and P1/P2 feasible solutions',
        constraints=['Distinct energy budgets','Same non-budget config and scientific arrays','No demo substitutes','Raw rate units bits/use; objective units P1bits/s/P2bits; time slots/seconds separate'],
        selected_stopping_times='K_slots and duration_s are extracted from each saved objective and exported in fig6_plotted_data.csv',
        invocation='python -m uav_qkd.phase6a_figures --output NEW_DIRECTORY --energy-sweep PATH_TO_REAL_SWEEP_JSON')
    write(output/'energy_sweep_schema.json',schema)
    (output/'captions.tex').write_text('\n\n'.join('% Fig. '+str(n)+'\n% '+CAPTIONS[n] for n in (4,5,6,7)),encoding='utf-8')
    snippets=[]
    for n in sorted(k for k,v in manifests.items() if v['generation_status']=='GENERATED_NUMERICAL_DIAGNOSTIC'):
        env='figure*' if n in (4,6) else 'figure';width='\\textwidth' if n in (4,6) else '\\columnwidth'
        snippets.append('\\begin{'+env+'}[t]\n\\centering\n\\includegraphics[width='+width+']{'+STEMS[n]+'.pdf}\n\\caption{'+CAPTIONS[n].replace('–','--')+'}\n\\label{fig:phase6a-'+str(n)+'}\n\\end{'+env+'}')
    if bundles is None:snippets.append('% Fig.6 pending; no graphic generated. After a matched sweep, use figure* with fig6_energy_budget_sensitivity.pdf.')
    (output/'figures_ieee.tex').write_text('\n\n'.join(snippets),encoding='utf-8')
    write(output/'output_manifest.json',{p.name:sha(p) for p in output.iterdir() if p.is_file() and p.name!='output_manifest.json'})
    return manifests


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=DEFAULT_OUTPUT)
    parser.add_argument('--energy-sweep',type=Path)
    args=parser.parse_args();result=generate(args.output,args.energy_sweep)
    print(json.dumps({k:v['generation_status'] for k,v in result.items()}))
