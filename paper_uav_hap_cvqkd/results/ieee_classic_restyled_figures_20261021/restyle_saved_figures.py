"""Render saved plot inputs only; keep historical producers and artifacts immutable.

Only audited plotting functions are loaded from old scripts, without their
experimental imports or entry points. All exports go through one style function.
"""
from __future__ import annotations

import ast
import csv
import hashlib
import json
import math
from pathlib import Path
import sys
import types

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.text import Text
from matplotlib import font_manager
import numpy as np

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
RESULTS = ROOT / 'results'
RECORDS = []
GROUP = ''
PRODUCER = ''
SOURCE_READS = set()
SEEN = set()
REAL_SAVEFIG = Figure.savefig
FONT = font_manager.findfont('Times New Roman', fallback_to_default=False)
PALETTE = ['#164a7b', '#b52025', '#222222', '#2f7045', '#78417b']
MARKERS = ['o', '^', 's', 'D', 'v']
STYLES = ['-', '--', '-.', '-', '--']


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rows(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def js(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def numbers(data):
    converted = []
    for row in data:
        item = {}
        for key, value in row.items():
            try: item[key] = float(value)
            except (ValueError, TypeError): item[key] = value
        converted.append(item)
    return converted


def no_write(*args, **kwargs):
    return None


def safe_mkdir(path, *args, **kwargs):
    # Every historical destination already exists. No old directory is created.
    assert Path(path).is_dir(), path


class PlotOnly(ast.NodeTransformer):
    def visit_Call(self, node):
        node = self.generic_visit(node)
        if isinstance(node.func, ast.Attribute):
            if node.func.attr in ('write_text', 'write_bytes', 'copyfile', 'copy2'):
                return ast.copy_location(ast.Call(ast.Name('no_write', ast.Load()), [], []), node)
            if node.func.attr == 'mkdir':
                return ast.copy_location(ast.Call(ast.Name('safe_mkdir', ast.Load()), [node.func.value], []), node)
        return node

    def visit_If(self, node):
        # The historical completion guard protects old exports. This adapter
        # never runs the old entry point and never writes to its destinations.
        if 'final_receipt.json' in ast.unparse(node.test) and '.exists()' in ast.unparse(node.test):
            return None
        return self.generic_visit(node)


def load_plot(path, functions=None, constants=True):
    """Load named plot functions, standard imports and simple plot constants."""
    path = Path(path)
    tree = ast.parse(path.read_text(encoding='utf-8-sig'))
    allowed = ('__future__', 'pathlib', 'csv', 'json', 'hashlib', 'math', 're',
               'numpy', 'matplotlib', 'collections', 'typing', 'scipy.stats')
    def permitted(name):return any(name==base or name.startswith(base+'.') for base in allowed)
    body = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            if all(permitted(n.name) for n in node.names): body.append(node)
        elif isinstance(node, ast.ImportFrom):
            if permitted(node.module or ''): body.append(node)
        elif isinstance(node, ast.FunctionDef):
            if functions is None or node.name in functions: body.append(node)
        elif constants and isinstance(node, (ast.Assign, ast.AnnAssign)):
            # Plot modules only: paths, styles, captions and numerical constants.
            body.append(node)
        elif isinstance(node, ast.Assign):
            try: ast.literal_eval(node.value)
            except (ValueError, TypeError): continue
            body.append(node)
    code = ast.fix_missing_locations(PlotOnly().visit(ast.Module(body=body, type_ignores=[])))
    env = dict(__file__=str(path), __name__='saved_plot_adapter', no_write=no_write,
               safe_mkdir=safe_mkdir, np=np, plt=plt, matplotlib=matplotlib, Path=Path, math=math,
               json=json, csv=csv, hashlib=hashlib, read_csv=rows, read_json=js,
               ROOT=ROOT, OUT=path.parent)
    exec(compile(code, str(path), 'exec'), env)
    for name in ('write_csv', 'csv_save', 'save_csv', 'save_json', 'json_save', '_write'):
        env[name] = no_write
    return types.SimpleNamespace(**env), env


def all_axes(fig):
    axes = list(fig.axes)
    for ax in axes:
        axes.extend(child for child in ax.child_axes if child not in axes)
    return axes


def numeric_fingerprint(fig):
    """Hash data, CI vertices, image arrays, bar geometry and scientific scales."""
    h = hashlib.sha256()
    def add(value):
        value = np.ma.asarray(value)
        h.update(str(value.shape).encode())
        if value.dtype.kind in 'biufc':
            h.update(np.asarray(value.filled(np.nan) if np.ma.isMaskedArray(value) and value.dtype.kind in 'fc' else value, dtype=np.float64).tobytes())
        else: h.update(repr(value.tolist()).encode())
    for ax in all_axes(fig):
        h.update((ax.get_xscale()+'|'+ax.get_yscale()).encode())
        for axis in (ax.xaxis, ax.yaxis):
            for name in ('base', 'linthresh', 'linscale'):
                h.update(repr(getattr(axis._scale, name, None)).encode())
        for line in ax.lines:
            add(line.get_xdata()); add(line.get_ydata())
            h.update(line.get_drawstyle().encode())
        for collection in ax.collections:
            add(collection.get_offsets())
            if collection.get_array() is not None: add(collection.get_array())
            for path in collection.get_paths(): add(path.vertices)
        for image in ax.images: add(image.get_array()); add(image.get_extent())
        for patch in ax.patches: add(patch.get_path().vertices); add(patch.get_patch_transform().get_matrix())
    return h.hexdigest()


def line_style(label, index):
    lower = label.lower()
    if 'minus' in lower or '−' in lower: k = index % len(PALETTE)
    elif 'greedy' in lower: k = 0
    elif 'dynamic' in lower or lower == 'dp' or lower.startswith('dp,'): k = 1
    elif 'stationary' in lower or 'p2' in lower: k = 2
    elif 'uniform' in lower: k = 0
    elif 'fixed mb' in lower: k = 2
    elif 'optimized mb' in lower: k = 1
    else:
        return PALETTE[index % len(PALETTE)], MARKERS[index % 4], ('-', '--', '-.')[index//4 % 3]
    ls = STYLES[k]
    if 'λ=0' in lower or 'λ = 0' in lower: ls = '-.'
    return PALETTE[k], MARKERS[k], ls


def classic(fig):
    """Change presentation only, with exact numerical before/after identity."""
    before = numeric_fingerprint(fig)
    axes = [ax for ax in fig.axes if ax.get_label() != '<colorbar>']
    has_colorbar = len(axes) != len(fig.axes)
    multi = len(axes) > 1
    old_width, old_height = fig.get_size_inches()
    if multi:
        ncols = max(1, len({round(ax.get_position().x0, 2) for ax in axes}))
        nrows = max(1, len({round(ax.get_position().y0, 2) for ax in axes}))
        fig.set_size_inches(7.16, max(2.6, 2.35*nrows))
    elif max((len(ax.get_legend_handles_labels()[0]) for ax in axes), default=0)>6:
        fig.set_size_inches(7.16, 3.0)
    else:
        fig.set_size_inches(3.5 if not has_colorbar else 3.9, 2.75 if not has_colorbar else 3.2)
    boxed=[text for ax in axes for text in ax.texts if text.get_bbox_patch() is not None and len(text.get_text())>65]
    if len(boxed)>1:fig.set_size_inches(7.16,3.15)
    signed_zoom=any(ax.get_yscale()=='symlog' and ax.child_axes for ax in axes)
    if signed_zoom:fig.set_size_inches(7.16,3.4)
    fig.set_facecolor('white')
    old_legends = list(fig.legends)
    legend_labels = [(h, t.get_text()) for leg in old_legends
                     for h, t in zip(leg.legend_handles, leg.get_texts())]
    notes = [text.get_text() for text in fig.texts if text.get_text()]
    notes.extend(text.get_text() for ax in all_axes(fig) for text in ax.texts if text.get_text())
    for legend in old_legends: legend.remove()
    for text in list(fig.texts): text.remove()
    fig._suptitle = fig._supxlabel = fig._supylabel = None
    for ax in [a for a in all_axes(fig) if a.get_label() != '<colorbar>']:
        ax.set_facecolor('white')
        if ax.get_legend() is not None: ax.get_legend().remove()
        for spine in ax.spines.values():
            spine.set_visible(True); spine.set_color('black'); spine.set_linewidth(.65)
        ax.tick_params(which='major', direction='in', width=.6, length=3, labelsize=7.5, colors='black', top=True, right=True)
        ax.tick_params(which='minor', direction='in', width=.45, length=1.6, colors='black', top=True, right=True)
        ax.set_axisbelow(True)
        if not has_colorbar or ax.lines:
            ax.grid(True, which='major', color='.80', linestyle=':', linewidth=.45)
            ax.grid(True, which='minor', color='.91', linestyle=':', linewidth=.3)
        title = ax.get_title()
        if not (title.startswith('(') or (multi and len(title) < 45)):
            ax.set_title('')
        ax.xaxis.label.set_size(8.5); ax.yaxis.label.set_size(8.5)
        ax.title.set_fontsize(8)
        if ax not in axes:
            ax.tick_params(labelsize=6);ax.xaxis.label.set_size(6.5);ax.yaxis.label.set_size(6.5)
        if ax.get_yscale()=='symlog':
            from matplotlib.ticker import SymmetricalLogLocator
            locator=SymmetricalLogLocator(transform=ax.yaxis._scale.get_transform(),subs=[1])
            locator.set_params(numticks=11);ax.yaxis.set_major_locator(locator)
        local_boxes=[text for text in ax.texts if text in boxed]
        for i,text in enumerate(local_boxes):
            if hasattr(text,'set_anncoords'):text.set_anncoords('axes fraction')
            else:text.set_transform(ax.transAxes)
            text.set_position((.02+.50*(i%2),.98-.30*(i//2)))
            text.set(ha='left',va='top',fontsize=6.2)
            text.get_bbox_patch().set(facecolor='white',edgecolor='.65',linewidth=.5)
        for text in ax.texts:text.set_clip_on(True)
        for i, line in enumerate(ax.lines):
            line.set_linewidth(.95)
            label = line.get_label()
            if label and not label.startswith('_'):
                color, marker, ls = line_style(label, i)
                if line.get_linestyle()=='None':ls='None'
                if label.lower().replace(' ','') in ('skr=0','k=0','zeroskr'):
                    color,marker,ls='.35','None',':'
                line.set(color=color, marker=marker, linestyle=ls, markersize=3.3,
                         markerfacecolor='white', markeredgewidth=.65)
                # Match the saved CI band to the corresponding restyled curve.
                bands = [c for c in ax.collections if c.__class__.__name__ == 'FillBetweenPolyCollection']
                if i < len(bands): bands[i].set_facecolor(color)
            elif line.get_marker() not in ('None', 'none', '', ' '):
                line.set_markersize(min(line.get_markersize(), 3.3))
        handles, labels = ax.get_legend_handles_labels()
        if not handles and legend_labels and ax is axes[0]:
            handles, labels = zip(*legend_labels)
        if handles and ax in axes:
            labels = [s.replace('Dynamic Programming (P3)', 'DP (P3)').replace('Dynamic Programming', 'DP')
                      .replace('Optimized Uniform 256-QAM', 'Optimized Uniform')
                      .replace('Fixed MB-shaped 256-QAM', 'Fixed MB')
                      .replace('Optimized MB-shaped 256-QAM', 'Optimized MB') for s in labels]
            legend_args=dict(loc='center left',bbox_to_anchor=(.01,.43)) if boxed else dict(loc='upper center') if signed_zoom else dict(loc='best')
            ax.legend(handles, labels, **legend_args, fontsize=6.4 if multi else 6.7,
                      frameon=True, fancybox=False, edgecolor='.65', facecolor='white',
                      framealpha=.95, borderpad=.35, labelspacing=.25,
                      handlelength=2.3, handletextpad=.45, borderaxespad=.4)
    for ax in all_axes(fig):
        for collection in ax.collections:
            collection.set_rasterized(False)
            if collection.__class__.__name__=='PathCollection':collection.set_sizes(np.minimum(collection.get_sizes(),35))
    for text in fig.findobj(Text):
        text.set_fontfamily('Times New Roman')
        if text not in [ax.xaxis.label for ax in axes]+[ax.yaxis.label for ax in axes]:
            text.set_fontsize(min(text.get_fontsize(), 8))
    # Tight layout is applied after moving legends inside and removing footers.
    fig.set_layout_engine(None)
    fig.tight_layout(pad=.6, w_pad=1.0, h_pad=1.0)
    after = numeric_fingerprint(fig)
    assert before == after, 'Style changed numeric artists or scales'
    return before, notes


def savefig(fig, filename, *args, **kwargs):
    path = Path(filename)
    key = (GROUP, path.stem)
    if key in SEEN: return
    SEEN.add(key)
    fingerprint, notes = classic(fig)
    dest = OUT / 'figures' / GROUP / path.stem
    dest.parent.mkdir(parents=True, exist_ok=True)
    with plt.rc_context({'pdf.fonttype': 42, 'pdf.use14corefonts': False, 'ps.fonttype': 42, 'text.usetex': False,
                         'mathtext.fontset': 'stix', 'savefig.facecolor': 'white'}):
        for ext in ('pdf', 'png'):
            REAL_SAVEFIG(fig, dest.with_suffix('.'+ext), dpi=350, facecolor='white',
                         bbox_inches='tight', pad_inches=.035)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    issues = []
    panels = []
    for ax in fig.axes:
        leg = ax.get_legend()
        if leg is not None:
            a, b = ax.get_window_extent(renderer), leg.get_window_extent(renderer)
            if not (b.x0 >= a.x0-.5 and b.y0 >= a.y0-.5 and b.x1 <= a.x1+.5 and b.y1 <= a.y1+.5):
                issues.append('Legend exceeds axes')
        panels.append(dict(xlabel=ax.get_xlabel(), ylabel=ax.get_ylabel(),
                           xscale=ax.get_xscale(), yscale=ax.get_yscale(),
                           xlim=list(ax.get_xlim()), ylim=list(ax.get_ylim()),
                           line_points=[len(line.get_xdata()) for line in ax.lines],
                           colorbar=ax.get_label() == '<colorbar>'))
    RECORDS.append(dict(group=GROUP, name=path.stem, producer=PRODUCER,
                        original_destination=str(path), fingerprint_before=fingerprint,
                        fingerprint_after=numeric_fingerprint(fig), dimensions_inches=list(fig.get_size_inches()),
                        panels=panels, original_notes=notes, layout_issues=issues,
                        pdf=dest.with_suffix('.pdf').relative_to(OUT).as_posix(),
                        png=dest.with_suffix('.png').relative_to(OUT).as_posix()))
    print('RENDERED', GROUP, path.stem, flush=True)


def activate(group, path, functions=None, constants=True):
    global GROUP, PRODUCER
    GROUP = group
    PRODUCER = Path(path).relative_to(ROOT).as_posix()
    mod, env = load_plot(path, functions, constants)
    if group_complete(group):
        for name in list(vars(mod)):
            if name in ('main','export_results','figures','render','make_figures','_plots','_plot',
                        'plot_results','render_package','plots','make_plots','render_figures','render_plot') or name.startswith('_plot_'):
                setattr(mod,name,no_write)
    return mod, env


def group_complete(group):
    if not group.startswith('historical/'):return False
    folder=RESULTS/group.removeprefix('historical/')
    names={p.stem for p in folder.glob('*.png') if 'manuscript_page' not in p.stem and 'manuscript_38_page' not in p.stem}
    if (folder/'figures').is_dir():names.update(p.stem for p in (folder/'figures').glob('*.png'))
    return bool(names) and all((group,name) in SEEN for name in names)


def core():
    sim = RESULTS/'manuscript_mobility_p1_p2_p3_20261019'
    mod, env = activate('01_mobility', ROOT/'scripts/plot_manuscript_mobility.py')
    mod.export_results(sim, js(sim/'protocol.json'))

    analysis = sim/'analysis'
    mod, env = activate('02_analysis', analysis/'analyze_saved_results.py', ['figures'])
    cloud = np.load(sim/'clouds/states.npz', allow_pickle=False)
    paths = np.load(sim/'mobility/paths.npz', allow_pickle=False)
    metrics = rows(sim/'mobility/mission_metrics.csv')
    data = dict(xy=np.array([[float(r['x_m']),float(r['y_m'])] for r in rows(sim/'positions.csv')]),
                K=np.array([float(r['K_star']) for r in rows(sim/'p1/winners.csv')]),
                C=cloud['blocked'], S=cloud['usable_skr'], paths=paths['paths'],
                penalties=paths['lambda_values'], schedule=js(sim/'mobility/lambda_schedule.json'), a={})
    for key, field in [('K','average_skr_bits_per_use'),('U','objective_bits_per_use')]:
        data['a'][key] = np.array([float(next(r for r in metrics if int(r['realization_id'])==rid and int(r['lambda_index'])==li and r['strategy']==m)[field])
                                   for rid in range(100) for li in range(10) for m in ('Stationary','Greedy','DP')]).reshape(100,10,3)
    summary = js(analysis/'analysis_summary.json')
    mod.figures(data, summary['p1'], summary['p2'], summary['methods'], summary['dynamics'])
    # C_mobility_tradeoff is an exact historical copy, mapped in the inventory.

    comp = analysis/'comparison_figures'
    mod, env = activate('03_comparison', comp/'render_comparisons.py', ['render'])
    mod.render(dict(penalties=paths['lambda_values'], summary=numbers(rows(comp/'figure_data_summary.csv')),
                    paired=numbers(rows(comp/'paired_improvements.csv')),
                    slots=numbers(rows(comp/'representative_slot_data.csv')),
                    cumulative=numbers(rows(comp/'cumulative_skr_data.csv')),
                    p1=numbers(rows(comp/'p1_position_data.csv')), schedule=data['schedule'],
                    rid=int(rows(comp/'representative_slot_data.csv')[0]['realization_id'])))

    folder = RESULTS/'mobility_parameter_sensitivity_20261020'
    mod, env = activate('04_stage_A', ROOT/'scripts/plot_mobility_parameter_sensitivity.py')
    protocol, summary, paired = mod.load(folder)
    mod.render(folder, protocol, summary, paired)

    mod, env = activate('05_stage_B', ROOT/'scripts/plot_mobility_cloud_sensitivity.py', ['main','sha','js','rows','csv_save','json_save'])
    mod.main()

    final = RESULTS/'mobility_parameter_sensitivity_final_20261020'
    mod, env = activate('00_final', final/'build_final_package.py', ['render','sha','rows','save_csv','save_json'])
    summary = {(int(r['figure']), r['case_id'], int(r['lambda_index']), r['method'], r['metric']):r
               for r in numbers(rows(final/'tables/statistical_comparison.csv'))}
    selections = []
    for f, name in enumerate(mod.NAMES, 1):
        points = [r for r in numbers(rows(final/('figures/'+name+'_data.csv'))) if r['method']=='DP']
        seen = set()
        for r in points:
            key = (r['case_id'], r['lambda_index'])
            if key in seen: continue
            seen.add(key)
            selections.append(dict(figure=f, case_id=r['case_id'], lambda_index=int(r['lambda_index']),
                                   lambda_bits_per_use=r['lambda_bits_per_use'], value=r['parameter_value'],
                                   axis=r['x_metric'], source=r['source']))
    mod.render(selections, summary)

    mod, env = activate('06_zenith', RESULTS/'skr_vs_zenith_angle_20261019/render_figures.py')
    mod.main()

    global GROUP, PRODUCER
    GROUP = '00_final'
    p = RESULTS/'manuscript_ieee_compact_20261020/render_compact_figure.py'
    PRODUCER = p.relative_to(ROOT).as_posix()
    tree = PlotOnly().visit(ast.parse(p.read_text(encoding='utf-8')))
    # Remove file-output context only; the saved-data plotting loop is unchanged.
    tree.body = [n for n in tree.body if not (isinstance(n, ast.With) and "'w'" in ast.unparse(n.items[0].context_expr))]
    env = dict(__file__=str(p), __name__='saved_compact_plot', no_write=no_write, safe_mkdir=safe_mkdir)
    exec(compile(ast.fix_missing_locations(tree), str(p), 'exec'), env)


def audit_event(event, args):
    if event=='import' and str(args[0]).split('.')[0] in ('src','scripts'):
        raise PermissionError('Experimental module imports are prohibited in this renderer')
    if event == 'open':
        filename, mode, flags = args
        if isinstance(filename, (str, bytes)):
            path = Path(filename).resolve()
            writing = (isinstance(mode, str) and any(c in mode for c in 'wax+')) or (isinstance(flags, int) and flags & 0x603)
            if writing and not path.is_relative_to(OUT):
                raise PermissionError('Historical/external write blocked: '+str(path))
            if not writing and path.is_relative_to(ROOT) and not path.is_relative_to(OUT):
                SOURCE_READS.add(path)
    if event in ('subprocess.Popen', 'os.system'):
        raise PermissionError('No simulation or external producer execution allowed')


def main():
    assert not (OUT/'validation/final_receipt.json').exists(), 'Completed package is immutable'
    progress = OUT/'validation/render_progress.json'
    if progress.exists():
        RECORDS.extend(js(progress))
        SEEN.update((r['group'],r['name']) for r in RECORDS)
    Figure.savefig = savefig
    sys.addaudithook(audit_event)
    try:
        if sum(not record['group'].startswith('historical/') for record in RECORDS)<48:
            core()
        from restyle_legacy import run
        run(sys.modules[__name__])
        from restyle_more_saved import run as more
        more(sys.modules[__name__])
    finally:
        (OUT/'validation/render_progress.json').write_text(json.dumps(RECORDS, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
        (OUT/'validation/input_manifest.json').write_text(json.dumps({str(p.relative_to(ROOT)):sha(p) for p in sorted(SOURCE_READS) if p.is_file()}, indent=2)+'\n', encoding='utf-8')
    receipt = dict(status='CURRENTLY_VERIFIED_PASS', scope='SAVED_DATA_PRESENTATION_ONLY',
                   numerical_recalculation=False, simulations=0, solver_calls=0, source_moment_calls=0,
                   font='Times New Roman', font_path=FONT, vector_pdf=True, png_dpi=350,
                   figures=RECORDS, renderer_sha256=sha(__file__))
    (OUT/'validation/render_receipt.json').write_text(json.dumps(receipt, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')


if __name__ == '__main__':
    main()
