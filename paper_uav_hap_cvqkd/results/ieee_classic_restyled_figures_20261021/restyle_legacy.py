"""Audited saved-data adapters for the older, separately labelled configurations."""
from pathlib import Path
import ast
import contextlib
import io
import types
import numpy as np
import matplotlib.pyplot as plt


def block(r, path, start, end, env):
    """Execute only the explicitly reviewed plotting statements in an old producer."""
    if r.group_complete(r.GROUP):return
    tree = ast.parse(path.read_text(encoding='utf-8-sig'))
    selected = []
    def collect(body):
        for node in body:
            if start <= node.lineno and node.end_lineno <= end:
                selected.append(node)
            elif node.lineno <= start <= node.end_lineno:
                collect(getattr(node, 'body', []))
    collect(tree.body)
    assert selected, (path, start, end)
    code = ast.fix_missing_locations(r.PlotOnly().visit(ast.Module(body=selected,type_ignores=[])))
    exec(compile(code, str(path), 'exec'), env)


def run(r):
    R, S = r.RESULTS, r.ROOT/'scripts'
    def activate(folder, script, functions, constants=False):
        mod, env = r.activate('historical/'+folder, S/script, functions, constants)
        return mod, env
    def simple(folder, csvname, name, xkey, ykeys, group=None, xlabel=None, ylabel='SKR (bits/use)', log=False):
        r.GROUP='historical/'+folder
        r.PRODUCER='restyle_legacy.py:direct saved columns; no evaluator'
        source=R/folder/csvname; data=r.numbers(r.rows(source))
        fig,ax=plt.subplots()
        if group:
            identity=lambda row:(row[group],row.get('nu_MB','')) if group=='modulation' else row[group]
            for label in dict.fromkeys(identity(row) for row in data):
                local=[row for row in data if identity(row)==label]
                xx=[row[xkey] for row in local]; yy=[row[ykeys[0]] for row in local]
                text=(str(label[0])+(' '+str(label[1]) if label[1]!='' else '')) if isinstance(label,tuple) else str(label)
                ax.plot(xx,np.where(np.asarray(yy)>0,yy,np.nan) if log else yy,label=text,marker='o')
        else:
            for key in ykeys:
                ax.plot([row[xkey] for row in data],[row[key] for row in data],label=key,marker='o')
        ax.set(xlabel=xlabel or xkey,ylabel=ylabel)
        if log: ax.set_yscale('log')
        ax.legend()
        fig.savefig(R/folder/(name+'.pdf'));plt.close(fig)

    # Extra current uniform-source diagnostics (four figures, no optimization).
    folder='uniform_manuscript_2d_optimization_20261019'
    mod,env=activate(folder,'optimize_uniform_manuscript_2d.py',['plot_results'])
    env['OUT']=R/folder
    mod.plot_results(r.numbers(r.rows(R/folder/'all_candidates.csv')),r.numbers(r.rows(R/folder/'Uniform_MB_comparison.csv')))

    # Saved-data MB comparison plotters have no physical-layer imports.
    for name in ('plot_joint_skr_comparison.py','plot_joint_skr_methods_and_mb_sweep.py',
                 'plot_mb_fixed_va2_vs_optimized.py','plot_mb_parameter_comparison.py','plot_mb_va2_exact_range.py'):
        mod,env=activate('joint_mb_va_global',name,None,True)
        with contextlib.redirect_stdout(io.StringIO()):mod.main()

    # Conventional log renderers: use the original positive-run rule, without
    # executing their font workaround, receipts or entry points.
    logscript=S/'render_theta10_D55_three_scheme_log10.py'
    for folder,csvname in [
        ('skr_vs_distance_theta10urad_D55cm_three_scheme','skr_vs_distance_three_scheme.csv'),
        ('skr_vs_distance_theta10urad_D55cm_unconstrained_three_scheme','skr_vs_distance_three_scheme.csv'),
        ('skr_vs_distance_theta10urad_D55cm_catalog182_20261012','skr_vs_distance_three_scheme.csv'),
        ('skr_vs_distance_effective_channel_no_fading_noise_cache_20261014','skr_vs_distance_three_scheme.csv'),
        ('theta10_D55_alt_opt_distance_sweep','three_scheme_alt_opt.csv'),
        ('theta10_D55_alt_opt_26distance_strict_rerun','three_scheme_alt_opt.csv')]:
        mod,env=activate(folder,logscript.name,['read_rows','positive_runs','render'],True)
        actual=tuple(dict.fromkeys(row['scheme'] for row in r.rows(R/folder/csvname)))
        env.update(SCHEMES=actual,COLORS={name:r.PALETTE[i] for i,name in enumerate(actual)},LABELS={name:name for name in actual})
        tree=ast.parse(logscript.read_text(encoding='utf-8'))
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='render')
        fn.body=[n for n in fn.body if n.end_lineno<=134]
        exec(compile(ast.fix_missing_locations(r.PlotOnly().visit(ast.Module(body=[fn],type_ignores=[]))),str(logscript),'exec'),env)
        env['render'](R/folder/csvname,R/folder)

    # Signed companions keep every negative/zero point and original scale.
    folder='skr_vs_distance_theta10urad_D55cm_three_scheme'
    simple(folder,'skr_vs_distance_three_scheme.csv','skr_vs_distance_three_scheme','distance_km',['K'],'scheme','Link distance (km)')
    folder='skr_vs_distance_theta10urad_D55cm_unconstrained_three_scheme'
    mod,env=activate(folder,'run_theta10_D55_unconstrained_three_scheme.py',['render'],False)
    env.update(output=R/folder,selected=[dict(row,SKR=row['K']) for row in r.numbers(r.rows(R/folder/'skr_vs_distance_three_scheme.csv'))])
    block(r,S/'run_theta10_D55_unconstrained_three_scheme.py',377,407,env)

    # Complete recorded uniform receiver/waist/variance/distance diagnostics.
    folder='revised_uniform_baseline_diagnostic'
    mod,env=activate(folder,'run_revised_uniform_baseline_diagnostic.py',['_plots','_save_plot'])
    mod._plots(R/folder,*[r.numbers(r.rows(R/folder/name)) for name in
               ['table2_uniform_va_sweep_exact_available.csv','table3_nearby_receiver_aperture.csv','table4_nearby_beam_waist.csv','distance_sweep.csv']])

    folder='redesigned_baseline_global_mb_va'
    mod,env=activate(folder,'run_redesigned_global_mb_va_optimization.py',['make_figures','save_figure'])
    data=r.numbers(r.rows(R/folder/'evaluated_points.csv'))
    mod.make_figures(R/folder,data,max(data,key=lambda row:row['SKR']))

    for folder in ('revised_uniform_mb_distance_diagnostic','revised_uniform_mb_common_feasible_diagnostic','revised_uniform_mb_common_feasible_extended_diagnostic'):
        script='run_revised_uniform_mb_distance_diagnostic.py' if folder=='revised_uniform_mb_distance_diagnostic' else 'run_revised_uniform_mb_common_feasible_diagnostic.py'
        functions=['_plots','_save_plot'] if folder=='revised_uniform_mb_distance_diagnostic' else ['_save_scatter']
        mod,env=activate(folder,script,functions)
        data=r.numbers(r.rows(R/folder/'diagnostic_distance_envelope.csv'))
        env['PROTOCOLS']=tuple(dict.fromkeys(row['protocol'] for row in data))
        if folder=='revised_uniform_mb_distance_diagnostic':
            env['PROTOCOLS']=tuple(dict.fromkeys(row['protocol'] for row in data));env['PLOT_TITLE_SUFFIX']='saved configuration'
            mod._plots(R/folder,data,sorted(set(row['distance_km'] for row in data)))
        else:
            # Three same-unit quantities were three independent historical figures.
            for metric,name,label in [('SKR','diagnostic_skr_vs_distance','SKR (bits/use)'),('beta_I_AB','diagnostic_beta_iab_vs_distance',r'$\beta I_{AB}$ (bits/use)'),('chi_BE','diagnostic_chi_be_vs_distance',r'$\chi_{BE}$ (bits/use)')]:
                mod._save_scatter(R/folder/name,data,metric,ylabel=label,title='',zero_line=metric=='SKR')

    folder='beam_waist_diagnostic'
    mod,env=activate(folder,'run_uniform_beam_waist_diagnostic.py',['_plot_sweep','_plot_distance','_plot_heatmap'])
    env['OUTPUT']=R/folder
    # Filenames are discovered below by their exact saved column schemas.
    tables={p.name:r.numbers(r.rows(p)) for p in (R/folder).glob('*.csv')}
    for name,data in tables.items():
        if not data:continue
        if name=='beam_waist_sweep.csv':mod._plot_sweep(data)
        if name=='beam_waist_distance_skr.csv':mod._plot_distance(data)
        if name=='beam_waist_receiver_heatmap.csv':mod._plot_heatmap(data)

    # Earlier deterministic-cloud mobility: only saved paths and CSV rate columns.
    folder='mobility_aware_skr_20261014/full'
    mod,env=activate(folder,'plot_mobility_skr_results.py',['plot_results','read_csv'],True)
    settings=r.js(R/folder/'inputs.json')
    settings=settings.get('settings',settings)
    mod.plot_results(R/folder,settings)

    # The numerical-package renderer reads explicit plot_data CSVs. Its geometric
    # cloud-footprint helper is evaluated from saved settings only.
    folder='mobility_numerical_results_package_20261014'
    mod,env=activate(folder,'plot_mobility_numerical_package.py',['render_package'],True)
    helper,henv=r.load_plot(r.ROOT/'src/mobility_results_package.py',['projected_cloud_footprint'],False)
    env['projected_cloud_footprint']=helper.projected_cloud_footprint
    env['SCHEMES']=tuple(dict.fromkeys(row['scheme'] for row in r.rows(R/folder/'plot_data/figure_2_skr_time.csv')))
    settings=r.js(R/'mobility_aware_skr_20261014/full/inputs.json');settings=settings.get('settings',settings)
    mod.render_package(R/folder,settings,include_uniform=True)

    # Older direct-noise figures whose original standalone renderer is absent:
    # the authenticated source CSV is plotted directly, with no inferred rates.
    for folder,csvname,name in [
        ('direct_noise_distance_va2_compare','direct_noise_distance_va2.csv','SKR_vs_L_all_distributions_direct_noise'),
        ('per_realization_direct_noise_va2','per_realization_direct_noise_va2.csv','SKR_vs_L_all_distributions'),
        ('updated_noise_smooth_distance_va2','updated_noise_smooth_distance_va2.csv','SKR_vs_L_all_distributions')]:
        simple(folder,csvname,name,'L_km',['K_raw_bar' if folder=='per_realization_direct_noise_va2' else 'K_raw'],'modulation','Link distance (km)')
    simple('updated_noise_smooth_distance_va2','updated_noise_smooth_distance_va2.csv','SKR_vs_L_all_distributions_log_bits_per_pulse','L_km',['K_raw'],'modulation','Link distance (km)',log=True)
    simple('updated_noise_extended_distance_va2','extended_distance_va2.csv','SKR_vs_L_extended_log','L_km',['K_raw'],'modulation','Link distance (km)',log=True)
    for folder in ('fixed_source_distance_va2','fixed_source_distance_va2_kruse'):
        for name,key,label in [('K_raw_vs_distance','K_raw','Raw SKR (bits/use)'),('I_AB_vs_distance','I_AB',r'$I_{AB}$ (bits/use)'),('chi_BE_bound_vs_distance','chi_BE_bound',r'$\chi_{BE}$ (bits/use)'),('Z_star_vs_distance','Z_star',r'$Z_-$')]:
            simple(folder,'fixed_source_distance_va2.csv',name,'L_km',[key],'scheme','Link distance (km)',label)

    # One extra current paired-gap figure, using the already saved CI bounds.
    folder=R/'mobility_parameter_sensitivity_20261020/analysis/figure_report_review_20261020'
    r.GROUP='04_stage_A';r.PRODUCER=str((folder/'fig_S1_paired_objective_gaps_data.csv').relative_to(r.ROOT))
    data=r.numbers(r.rows(folder/'fig_S1_paired_objective_gaps_data.csv'))
    fig,axs=plt.subplots(1,3,figsize=(7.16,2.7))
    for panel,ax in enumerate(axs,1):
        local=[d for d in data if d['panel']==panel]
        for base in dict.fromkeys(d['baseline'] for d in local):
            group=[d for d in local if d['baseline']==base]
            xx,yy,lo,hi=([d[k] for d in group] for k in ('x','y','ci95_low','ci95_high'))
            ax.plot(xx,yy,label='DP minus '+base,marker='o');ax.fill_between(xx,lo,hi,alpha=.10)
        ax.set(xlabel={'J':'Candidate positions, $J$','speed':'Maximum speed (m/s)','probability':'Blockage probability, $p$'}.get(local[0]['axis'],local[0]['axis']),ylabel='Paired objective gain (bits/use)')
    fig.savefig(folder/'fig_S1_paired_objective_gaps.pdf');plt.close(fig)
