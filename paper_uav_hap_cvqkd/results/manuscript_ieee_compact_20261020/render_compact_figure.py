"""Render saved figure CSV rows only. Never imports an experimental evaluator."""
from pathlib import Path
import csv
import hashlib
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
SOURCE = ROOT / 'results/mobility_parameter_sensitivity_final_20261020/figures'
SETTINGS = [
    ('fig1_candidate_positions_data.csv', 'U', 'Candidate positions, $J$', 'Objective (bit/use)', '(a) Objective'),
    ('fig2_cloud_blockage_data.csv', 'unavailability_percent', 'Blockage probability, $p$', 'Unavailability (%)', '(b) Unavailability'),
    ('fig3_temporal_correlation_data.csv', 'D', 'Latent correlation, $\\rho$', 'Travel distance (m)', '(c) Travel distance')]
STYLES = {'Stationary': ('tab:blue', 'o', '-', 'P2'), 'Greedy': ('tab:orange', 'D', '--', 'Greedy'),
          'DP': ('tab:red', '^', '-', 'DP')}
plt.rcParams.update({'font.family': 'serif', 'font.serif': ['Times New Roman', 'DejaVu Serif'],
                     'font.size': 9, 'axes.labelsize': 9, 'axes.titlesize': 9,
                     'xtick.labelsize': 8.5, 'ytick.labelsize': 8.5, 'legend.fontsize': 9,
                     'pdf.fonttype': 42, 'ps.fonttype': 42})
fig, axes = plt.subplots(1, 3, figsize=(7.16, 2.25))
fig.subplots_adjust(left=.073, right=.995, bottom=.29, top=.76, wspace=.58)
all_rows = []
inputs = {}
for panel, (ax, settings) in enumerate(zip(axes, SETTINGS), 1):
    filename, metric, xlabel, ylabel, title = settings
    path = SOURCE / filename
    inputs[filename] = hashlib.sha256(path.read_bytes()).hexdigest()
    with path.open(encoding='utf-8', newline='') as stream:
        rows = [r for r in csv.DictReader(stream) if r['metric'] == metric]
    for method, (color, marker, linestyle, label) in STYLES.items():
        selected = sorted([r for r in rows if r['method'] == method], key=lambda r: float(r['x']))
        x, y, lo, hi = ([float(r[k]) for r in selected] for k in ('x', 'y', 'ci95_low', 'ci95_high'))
        assert selected and all(a <= b <= c for a, b, c in zip(lo, y, hi))
        line, = ax.plot(x, y, color=color, marker=marker, linestyle=linestyle,
                        linewidth=1.15, markersize=3.7, markerfacecolor='white', label=label)
        assert list(line.get_xdata()) == x and list(line.get_ydata()) == y
        ax.fill_between(x, lo, hi, color=color, alpha=.10, linewidth=0)
        all_rows.extend(dict(compact_panel=panel, **r) for r in selected)
    ax.set(xlabel=xlabel, ylabel=ylabel, title=title)
    ax.grid(True, color='.85', linewidth=.4)
    ax.tick_params(direction='in', width=.6, length=2.5)
    for spine in ax.spines.values():
        spine.set_linewidth(.6)
axes[0].set(xticks=[10,20,40,60,80,100], ylim=(0, .000175), yticks=[0,.00005,.0001,.00015])
fmt=ScalarFormatter(useMathText=True);fmt.set_powerlimits((0,0));axes[0].yaxis.set_major_formatter(fmt)
axes[1].set(xticks=[.1,.2,.3,.4,.5,.6,.7,.8], ylim=(-1,31), yticks=[0,10,20,30])
axes[2].set(xticks=[0,.3,.6,.9,.98], xticklabels=['0','.3','.6','.9','.98'],
            ylim=(-40,1700), yticks=[0,500,1000,1500])
axes[2].tick_params(axis='x', labelrotation=90)
for label in axes[2].get_xticklabels():
    label.set_ha('center')
handles, labels = axes[0].get_legend_handles_labels()
fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(.53,1.015),
           ncol=3, frameon=False, columnspacing=2.5, handlelength=2.6)
fig.canvas.draw()
renderer=fig.canvas.get_renderer()
assert all(text.get_fontsize() >= 8.5 for ax in axes for text in [ax.xaxis.label,ax.yaxis.label,ax.title,*ax.get_xticklabels(),*ax.get_yticklabels()])
for ax in axes:
    for text in [ax.xaxis.label, ax.yaxis.label, ax.title, *ax.get_xticklabels(), *ax.get_yticklabels()]:
        box=text.get_window_extent(renderer)
        assert box.x0 >= -.5 and box.y0 >= -.5 and box.x1 <= fig.bbox.width+.5 and box.y1 <= fig.bbox.height+.5, text.get_text()
fig.savefig(OUT/'figures/compact_sensitivity.pdf', metadata={'Title':'Saved-data mobility sensitivity for compact IEEE layout'})
with (OUT/'figures/compact_sensitivity_data.csv').open('w',encoding='utf-8',newline='') as stream:
    writer=csv.DictWriter(stream,fieldnames=list(all_rows[0]));writer.writeheader();writer.writerows(all_rows)
metadata=dict(scope='SAVED_DATA_RENDERING_ONLY',panels=3,points=len(all_rows),figsize_inches=[7.16,2.25],
              minimum_font_points=8.5,inputs_sha256=inputs,simulations=0,interpolated_points=0,
              pdf_sha256=hashlib.sha256((OUT/'figures/compact_sensitivity.pdf').read_bytes()).hexdigest())
(OUT/'figures/render_metadata.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8')
print(json.dumps(metadata))
