"""Additional archived plot-only adapters. No experiment entry point is invoked."""
import types
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from restyle_legacy import block


def run(r):
    R,S=r.RESULTS,r.ROOT/'scripts'
    def activate(folder,script,functions,constants=False):
        mod,env=r.activate('historical/'+folder,S/script,functions,constants)
        env['OUT']=R/folder
        return mod,env
    def saved_figure(path,fig):
        fig.savefig(Path(path).with_suffix('.pdf'));plt.close(fig)

    # Binary clouds: replace statistical preparation by the saved plotting tables.
    folder='binary_cloud_skr_20261015'
    mod,env=activate(folder,'plot_binary_cloud_skr_results.py',['column_style','save_figure'],True)
    settings=r.js(R/folder/'inputs.json')['settings']
    data=R/folder/'plot_data'; cloud=np.load(R/folder/'cloud_states.npz',allow_pickle=False)['blocked']
    paths=np.load(R/folder/'trajectories.npz',allow_pickle=False)['paths']
    stats=r.numbers(r.rows(R/folder/'summary_statistics.csv'))
    def metric(sid,family,scheme,name):
        return next(x for x in stats if int(x['scenario_id'])==sid and x['family']==family and x['scheme']==scheme and x['metric']==name)
    winner_rows=r.numbers(r.rows(R/folder/'clear_winners.csv'))
    winners={family:sorted([x for x in winner_rows if x['family']==family],key=lambda x:x['position_index']) for family in ('MB','Uniform')}
    env.update(settings=settings,metric=metric,cloud=cloud,paths=paths,winners=winners,
               positions=np.array([[float(x['x_m']),float(x['y_m'])] for x in r.rows(R/folder/'positions.csv')]),
               scenarios=r.js(R/folder/'cloud_scenarios.json'),stats=r.rows(R/folder/'summary_statistics.csv'),
               lambda_stats=r.rows(R/folder/'lambda_statistics.csv'),slots=settings['mission']['slots'],dt=settings['mission']['slot_duration_s'],
               times=np.arange(1,settings['mission']['slots']+1)*settings['mission']['slot_duration_s'],
               time_data=r.numbers(r.rows(data/'figure_2_skr_time.csv')),
               cumulative_data=r.numbers(r.rows(data/'figure_3_cumulative_normalized.csv')),figures=R/folder/'figures')
    env['p_ids']=[x['scenario_id'] for x in env['scenarios'] if x['correlation_length_m']==settings['cloud']['correlation_length_m'] and x['temporal_rho']==settings['cloud']['temporal_rho']]
    block(r,S/'plot_binary_cloud_skr_results.py',82,162,env)

    # Three previously plotted fading comparisons. Only the plotting statements
    # following the producer's numerical work are selected here.
    folder='fading_effective_binary_cloud_20261016'
    mod,env=activate(folder,'run_fading_effective_binary_cloud.py',[],False)
    env.update(output=R/folder,read_csv=r.rows,saved=types.SimpleNamespace(read_json=r.js),np=np,plt=plt)
    block(r,S/'run_fading_effective_binary_cloud.py',385,402,env)
    mod,env=activate(folder,'plot_fading_effective_comparison.py',['plot'],True)
    env['saved']=types.SimpleNamespace(read_json=r.js,save=r.no_write,digest=r.sha)
    mod.plot(R/folder)

    # Historical exact distance curves (including the separately stored fixture).
    for folder in ('skr_vs_link_distance','skr_vs_link_distance/historical_exact_rerun_current_fixture'):
        mod,env=activate(folder,'run_historical_exact_skr_vs_link_distance.py',['plot'])
        envelopes={label:r.numbers(r.rows(R/folder/name)) for label,name in
                   [('Uniform','historical_exact_uniform_envelope.csv'),('MB with AO','historical_exact_mb_ao_envelope.csv'),('MB without AO','historical_exact_mb_noao_envelope.csv')]}
        summaries=r.numbers(r.rows(R/folder/'historical_exact_operation_distance_summary.csv'))
        for row in summaries:
            if row.get('operation_distance_estimate_km')=='':row['operation_distance_estimate_km']=None
        env['CURVE_NAMES']=tuple(envelopes)
        mod.plot(R/folder/'historical_exact_distance_plot',envelopes,summaries)

    # Original distance figures, not an optimizer replay.
    for folder in ('skr_vs_link_distance','skr_vs_link_distance_smoke'):
        mod,env=activate(folder,'run_skr_vs_link_distance.py',['_plot'])
        crossings=r.numbers(r.rows(R/folder/'operation_distance_summary.csv'))
        for row in crossings:
            if row.get('operation_distance_km')=='':row['operation_distance_km']=None
        mod._plot(R/folder/'skr_vs_link_distance',r.numbers(r.rows(R/folder/'skr_vs_link_distance.csv')),
                  crossings)

    # Recorded AO histories and their exact-source slices. No search is executed.
    base='theta10_D55_ao_numerical_optimum_validation'
    for folder in (base,base+'/phase_2A',base+'/overnight_ao_run'):
        mod,env=activate(folder,'audit_theta10_D55_ao_numerical_optimum.py',['make_plots'])
        env.update(REF=21.9393102292,ao=types.SimpleNamespace(save_figure=saved_figure),
                   io=types.SimpleNamespace(write_csv=r.no_write),
                   sweep=types.SimpleNamespace(UNIFORM_SCHEME='Optimized Uniform 256-QAM',FIXED_MB_SCHEME='Fixed MB-shaped 256-QAM'))
        if (R/folder/'cache_only_runs.json').exists():
            runs=r.js(R/folder/'cache_only_runs.json')
        else:
            runs=r.js(R/'theta10_D55_mb_exact_targeted_expansion/batch_3/cache_only_runs.json')
        checkpoint={}; maxima={}
        for distance,tag in [(21.9393102292,'reference'),(22.,'22km')]:
            combined=[];seen=set()
            for var in ('V_A','nu_raw'):
                for row in r.numbers(r.rows(R/folder/f'exact_slice_{tag}_{var}.csv')):
                    key=(row['nu_raw'],row['V_A'])
                    if key not in seen:combined.append(row);seen.add(key)
            checkpoint[str(distance)]={'rows':combined};maxima[distance]=max(combined,key=lambda x:x['SKR'])
        comparison_path=R/folder/'three_scheme_comparison.csv'
        if not comparison_path.exists():comparison_path=R/base/'three_scheme_comparison.csv'
        mod.make_plots(runs,maxima,checkpoint,r.numbers(r.rows(comparison_path)))

    # Saved stopping-parameter sweep. Its x-log scale is retained.
    folder='theta10_D55_ao_stopping_parameter_sensitivity'
    mod,env=activate(folder,'run_theta10_D55_ao_stopping_sensitivity.py',['plots'])
    env['saved']=types.SimpleNamespace(REF=21.9393102292)
    mod.plots(r.numbers(r.rows(R/folder/'sensitivity_by_distance.csv')))

    # Existing two-level landscapes and exact completion, including the draft.
    base='theta10_D55_objective_B_numerical_skr_optimization'
    for folder in (base+'/two_level_2d_skr_grid',base+'/two_level_2d_skr_grid_draft_1'):
        mod,env=activate(folder,'build_theta10_D55_two_level_skr_grid.py',['make_figures'])
        env['audit']=types.SimpleNamespace(REF=21.9393102292)
        coverage=r.numbers(r.rows(R/folder/'exact_cache_coverage.csv'))
        for row in coverage:
            for key in ('Grid_A','Grid_B'):row[key]=str(row[key]).lower()=='true'
        mod.make_figures(coverage,r.numbers(r.rows(R/folder/'existing_skr_grid_reference.csv')),
                         [x for x in r.numbers(r.rows(R/folder/'offgrid_existing_exact_candidates.csv')) if x.get('near_optimal')=='YES'])
    folder=base+'/full_51_grid_exact_completion'
    mod,env=activate(folder,'run_theta10_D55_full_51_grid.py',['render_figures'])
    env['saved']=types.SimpleNamespace(REF=21.9393102292)
    coverage=r.numbers(r.rows(R/folder/'final_grid_51_coverage.csv'))
    for row in coverage:
        for key in ('Grid_A','Grid_B'):row[key]=str(row[key]).lower()=='true'
    ref=r.numbers(r.rows(R/folder/'complete_grid_reference.csv'))
    offgrid=r.numbers(r.rows(R/folder/'offgrid_existing_exact_candidates.csv'))
    mod.render_figures(coverage,ref,offgrid,max(ref+offgrid,key=lambda x:x['SKR']))

    # Revised optical-baseline plotting variants retain the same saved table.
    folder='revised_hap_uav_optical_baseline_figure'
    mod,env=activate(folder,'render_revised_hap_uav_optical_baseline_figure.py',['render_plot','add_common_note'],True)
    data=r.numbers(r.rows(R/folder/'skr_distance_table.csv'))
    for metric,label,name in [('SKR','SKR (bits/use)','skr_vs_distance'),('beta_I_AB',r'$\beta I_{AB}$ (bits/use)','betaIAB_vs_distance'),('chi_BE',r'$\chi_{BE}$ (bits/use)','chiBE_vs_distance')]:
        mod.render_plot(data,R/folder,y_field=metric,y_label=label,png_name=name+'.png',pdf_name=name+'.pdf',zero_line=metric=='SKR')

    # Five existing redraws include both genuine log and signed symlog views.
    common,common_env=activate(folder,'render_skr_vs_distance_redraw_symlog.py',None,True)
    _,extended=common.load_source()
    common.render_plot(extended,R/folder)
    for script in ['render_skr_vs_distance_clean.py','render_skr_vs_distance_positive_only.py']:
        mod,env=activate(folder,script,None,True)
        for name in ['COLORS','PROTOCOLS','row_at','number']:
            if name in common_env:env[name]=common_env[name]
        mod.render_plot(extended,R/folder)
    mod,env=activate(folder,'render_skr_vs_distance_redraw_extended.py',None,True)
    mod.render_plot(extended,R/folder)
    mod,env=activate(folder,'render_skr_vs_distance_redraw.py',None,True)
    _,original=mod.load_existing_exact_table()
    mod.render(original,R/folder)

    # Existing early one-dimensional MB and AO sweeps: use PASS rows only,
    # exactly as in their original renderers. No threshold is estimated here.
    for folder,csvname,name,ykey,xkey in [
        ('mb_skr_sweep_zeta30_va2','mb_skr_sweep.csv','SKR_vs_MB','SKR','mb_parameter'),
        ('mb_skr_sweep_zeta30_va2_ao09','mb_skr_sweep_ao09.csv','SKR_vs_MB_AO09','raw_SKR','mb_parameter'),
        ('mb_skr_sweep_zeta30_va2_ao095_aperture_r004','mb_skr_sweep_ao095_aperture_r004.csv','SKR_vs_MB_AO095_aperture_r004','raw_SKR','mb_parameter'),
        ('mb_skr_sweep_zeta30_va2_ao09_aperture_r008','mb_skr_sweep_ao09_aperture_r008.csv','SKR_vs_MB_AO09_aperture_r008','raw_SKR','mb_parameter'),
        ('ao_threshold_sweep_zeta30_mb015_va2_r004','ao_threshold_sweep.csv','SKR_vs_eta_AO','raw_SKR','eta_ao')]:
        r.GROUP='historical/'+folder;r.PRODUCER='restyle_more_saved.py: saved PASS sweep rows'
        data=[x for x in r.numbers(r.rows(R/folder/csvname)) if x['status']=='PASS']
        fig,ax=plt.subplots();ax.plot([x[xkey] for x in data],[x[ykey] for x in data],marker='o')
        ax.set(xlabel=r'$\nu_{\rm MB}$' if xkey=='mb_parameter' else r'$\eta_{\rm AO}$',ylabel='SKR (bits/use)')
        fig.savefig(R/folder/(name+'.pdf'));plt.close(fig)

    # Recorded alternating-optimization trajectories, not AO execution.
    folder='theta10_D55_alt_opt'
    mod,env=activate(folder,'run_theta10_D55_alt_opt.py',['make_figures'])
    env['save_figure']=saved_figure
    trace=r.numbers(r.rows(R/folder/'ao_iterations.csv'));runs=[]
    for start in dict.fromkeys(x['initialization_id'] for x in trace):
        its=[x for x in trace if x['initialization_id']==start];first=its[0]
        trajectory=[dict(nu=first['nu_before'],V_A=first['V_A_before'])]
        for x in its:
            trajectory.extend([dict(nu=x['nu_before'],V_A=x['optimized_V_A']),dict(nu=x['optimized_nu'],V_A=x['optimized_V_A'])])
        runs.append(dict(start_nu=first.get('initial_nu',first['nu_before']),iterations=its,trajectory=trajectory))
    mod.make_figures(R/folder,runs)

    folder='theta10_D55_ao_final_scientific_results'
    mod,env=activate(folder,'export_theta10_D55_ao_scientific_results.py',['plots','figure'])
    env.update(REF=21.9393102292,sweep=types.SimpleNamespace(UNIFORM_SCHEME='Optimized Uniform 256-QAM',FIXED_MB_SCHEME='Fixed MB-shaped 256-QAM'))
    helper,helperenv=r.load_plot(S/'render_theta10_D55_three_scheme_log10.py',['positive_runs'],False)
    env['positive_runs']=helper.positive_runs
    base=R/'theta10_D55_ao_numerical_optimum_validation/overnight_ao_run'
    checkpoint=r.js(base/'objective_checkpoint.json')
    mod.plots(dict(runs=r.js(base/'cache_only_runs.json'),
                   rankings={float(k):sorted(v['rows'],key=lambda x:x['SKR'],reverse=True) for k,v in checkpoint.items()},
                   comparison=r.numbers(r.rows(R/folder/'three_scheme_exact_data.csv'))))

    folder='ao_effective_channel_no_fading_noise_reference'
    mod,env=activate(folder,'run_ao_effective_channel_no_fading_noise_reference.py',[],False)
    env.update(runs=r.js(R/folder/'optimization_result.json')['runs'],save_figure=saved_figure,plt=plt)
    # Skip only this function's local import of the experimental AO module.
    block(r,S/'run_ao_effective_channel_no_fading_noise_reference.py',464,473,env)

    folder='skr_vs_distance_theta10urad_D10cm'
    mod,env=activate(folder,'run_skr_vs_link_distance_theta10urad.py',['render'])
    mod.render(R/folder/'skr_vs_distance_clean',r.numbers(r.rows(R/folder/'skr_vs_distance_results.csv')))
    folder='hap_uav_sayat_forensics'
    mod,env=activate(folder,'run_hap_uav_sayat_forensic_diagnostic.py',['plots'])
    env['OUTPUT']=R/folder
    mod.plots(r.numbers(r.rows(R/folder/'uniform_existing_exact_phase_off.csv')),
              r.numbers(r.rows(R/folder/'distance_phase_off_existing_exact.csv')))
    folder='effective_channel_va2'
    r.GROUP='historical/'+folder;r.PRODUCER='restyle_more_saved.py:saved categorical raw_K'
    data=r.numbers(r.rows(R/folder/'effective_channel_skr_va2.csv'))
    fig,ax=plt.subplots();ax.bar([x['scheme'] for x in data],[x['raw_K'] for x in data],color=r.PALETTE[:len(data)])
    ax.set_ylabel('Raw SKR (bits/use)');fig.savefig(R/folder/'effective_channel_skr_va2.pdf');plt.close(fig)
    folder='mb_nu_threshold_va2';r.GROUP='historical/'+folder
    r.PRODUCER='restyle_more_saved.py:direct saved DeltaK rows'
    for suffix in ('','_refined'):
        data=r.numbers(r.rows(R/folder/('mb_nu_performance_rows'+suffix+'.csv')))
        fig,ax=plt.subplots()
        for distance in (17.,19.,24.):
            local=[x for x in data if x['L_km']==distance]
            ax.plot([x['nu_MB'] for x in local],[x['DeltaK'] for x in local],marker='o',label=f'L = {distance:g} km')
        ax.axhline(0,color='black',lw=.5);ax.set(xlabel=r'$\nu_{\rm MB}$',ylabel=r'$\Delta K$ (bits/use)')
        fig.savefig(R/folder/('DeltaK_vs_nu_MB'+suffix+'.pdf'));plt.close(fig)
    # The threshold artifact explicitly names the Kruse distance artifact as
    # its baseline; preserve its Uniform values and the saved refined MB rows.
    baseline=r.js(R/'fixed_source_distance_va2_kruse/fixed_source_distance_va2.json')['rows']
    refined=r.js(R/folder/'mb_nu_threshold_va2_refined.json')['evaluation_rows']
    fig,ax=plt.subplots()
    for scheme in ('uniform','binomial'):
        local=[x for x in baseline if x['scheme']==scheme]
        ax.plot([x['L_km'] for x in local],[x['K_raw'] for x in local],label=scheme.title(),marker='o')
    for nu in dict.fromkeys(x['nu_MB'] for x in refined):
        local=[x for x in refined if x['nu_MB']==nu]
        ax.plot([x['L_km'] for x in local],[x['K_MB'] for x in local],label=f'MB {nu:g}',marker='o')
    ax.axhline(0,color='black',lw=.5);ax.set(xlabel='Link distance (km)',ylabel='Raw SKR (bits/use)')
    fig.savefig(R/folder/'SKR_vs_L_all_distributions.pdf');plt.close(fig)
    folder='fixed_source_distance_va2_kruse';r.GROUP='historical/'+folder
    data=r.numbers(r.rows(R/folder/'fixed_source_distance_va2.csv'))
    fig,ax=plt.subplots()
    for scheme in dict.fromkeys(x['scheme'] for x in data):
        local=[x for x in data if x['scheme']==scheme]
        ax.plot([x['L_km'] for x in local],[x['K_raw'] for x in local],label=scheme,marker='o')
    ax.set(xlabel='Link distance (km)',ylabel='Raw SKR (bits/use)');fig.savefig(R/folder/'SKR_vs_distance_three_distributions.pdf');plt.close(fig)

    folder='skr_vs_link_distance/historical_exact_positive_only'
    r.GROUP='historical/'+folder;r.PRODUCER='scripts/filter_positive_historical_distance_artifacts.py: saved plotting block'
    mod,env=r.load_plot(S/'filter_positive_historical_distance_artifacts.py',[],False)
    env.update(OUTPUT=R/folder,positive_by_curve={name:[] for name in ('Uniform','MB with AO','MB without AO')},plt=plt)
    env['FILES']=tuple(env['positive_by_curve'])
    for row in r.rows(R/folder/'positive_skr_rows.csv'):env['positive_by_curve'][row['curve']].append(row)
    block(r,S/'filter_positive_historical_distance_artifacts.py',67,103,env)

    folder='figures_preliminary'
    mod,env=activate(folder,'plot_exact_median_skr.py',['_require_expected','load_median_data','_scaled_axis','make_figure'],True)
    guard,guard_env=r.load_plot(r.ROOT/'src/utils/plotting.py',['require_raw_data_path'],False)
    env['require_raw_data_path']=guard.require_raw_data_path
    data=mod.load_median_data()
    for slide,name in [(False,'exact_median_skr'),(True,'exact_median_skr_slide')]:
        fig,ax=plt.subplots()
        for method,marker,color in zip(mod.METHODS,('o','s','^'),r.PALETTE):
            ax.plot([method['position']],[data[method['key']]*1e4],marker=marker,ls='None',
                    color=color,label=method['label'])
        ax.axhline(0,color='.35',ls=':',lw=.6)
        ax.set(xticks=[method['position'] for method in mod.METHODS],
               xticklabels=[method['label'] for method in mod.METHODS],
               ylabel=r'Raw SKR ($10^{-4}$ bits/use)')
        # Tick labels already identify the categorical methods; no duplicate legend.
        for line in ax.lines:line.set_label('_nolegend_')
        fig.savefig(R/folder/(name+'.pdf'));plt.close(fig)
