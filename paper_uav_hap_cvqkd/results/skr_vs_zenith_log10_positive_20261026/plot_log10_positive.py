"""Positive-only base-10 display of immutable saved SKR; no scientific evaluation."""
import hashlib
import importlib.util
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import LogFormatterMathtext, LogLocator, MultipleLocator, NullFormatter
import numpy as np

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
PRIOR = ROOT / 'results/skr_vs_zenith_eq14_v43_phaseB_publication_figures'
STEM = 'skr_vs_zenith_log10_positive'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    if (OUT / (STEM + '.pdf')).exists():
        raise FileExistsError('Preserve completed figure; use a new version for another render')
    spec = importlib.util.spec_from_file_location('saved_figure_helpers', PRIOR / 'plot_skr_vs_zenith.py')
    helper = importlib.util.module_from_spec(spec); spec.loader.exec_module(helper)
    series, original_validation = helper.load_and_validate()
    font = helper.configure_fonts()
    fig, ax = plt.subplots(figsize=(3.5, 2.7), layout='constrained')
    statistics = {}; positive_values = []
    for i, scheme in enumerate(helper.SCHEMES):
        rows = series[scheme]
        x = np.array([float(r['zenith_deg']) for r in rows])
        raw = np.array([float(r['K_raw']) for r in rows])
        keep = raw > 0
        # NaN breaks the curve at every excluded sample, without changing its value.
        display = np.where(keep, raw, np.nan)
        label = helper.LABELS[i] + (' (no positive samples)' if not keep.any() else '')
        line, = ax.plot(x, display, label=label, **helper.STYLES[i], markersize=3.3,
                       markerfacecolor='white', markeredgewidth=.8, markevery=5,
                       zorder=3, clip_on=False)
        assert np.array_equal(line.get_xdata(), x)
        assert np.array_equal(line.get_ydata(), display, equal_nan=True)
        assert np.array_equal(display[keep], raw[keep]) and np.all(np.isnan(display[~keep]))
        positive_values.extend(raw[keep])
        statistics[helper.LABELS[i]] = dict(total_samples=len(rows), displayed_positive=int(keep.sum()),
            hidden_negative=int((raw < 0).sum()), hidden_zero=int((raw == 0).sum()),
            displayed_angles_deg=x[keep].tolist(), source_raw_values_unchanged=True)
    assert [v['displayed_positive'] for v in statistics.values()] == [0, 6, 16]
    ax.set_yscale('log', base=10, nonpositive='mask')
    ax.yaxis.set_major_locator(LogLocator(base=10))
    ax.yaxis.set_major_formatter(LogFormatterMathtext(base=10))
    ax.yaxis.set_minor_locator(LogLocator(base=10, subs=np.arange(2, 10)))
    ax.yaxis.set_minor_formatter(NullFormatter())
    ax.set(xlim=(0, 60), ylim=(10**math.floor(math.log10(min(positive_values))),
                              10**math.ceil(math.log10(max(positive_values)))),
           xlabel='Zenith angle (deg)', ylabel='Secret key rate (bits/use)')
    ax.xaxis.set_major_locator(MultipleLocator(10))
    ax.grid(which='major', color='#D7D7D7', linewidth=.45, alpha=.7)
    ax.grid(which='minor', axis='y', color='#E8E8E8', linewidth=.3, alpha=.5)
    ax.tick_params(direction='out', length=3, width=.65)
    ax.legend(loc='upper right', frameon=True, facecolor='white', edgecolor='#CCCCCC', framealpha=1)
    assert ax.get_yscale() == 'log' and ax.yaxis._scale.base == 10
    assert ax.get_ylim()[0] > 0 and ax.get_xlim() == (0, 60)
    description = ('DIAGNOSTIC_ONLY; positive raw SKR only on base10 log Y; '
                   'nonpositive samples hidden for display; source CSV unchanged; '
                   'Uniform has no positive samples; source convergence evidence incomplete')
    fig.savefig(OUT / (STEM + '.png'), dpi=600, bbox_inches='tight', pad_inches=.045,
                metadata={'Description': description})
    fig.savefig(OUT / (STEM + '.pdf'), bbox_inches='tight', pad_inches=.045,
                metadata={'Title': 'Positive secret key rate versus zenith angle',
                          'Subject': description, 'Keywords': 'DIAGNOSTIC_ONLY, base10 logarithmic, positive samples',
                          'Creator': 'Matplotlib saved-CSV renderer'})
    plt.close(fig)
    startup = helper.read(OUT / 'startup_manifest.json')
    for name, expected in startup['protected'].items():
        assert sha(ROOT.parent / name) == expected, name
    validation = dict(status='CURRENTLY_VERIFIED_PASS', result_scope='DIAGNOSTIC_ONLY',
        source_csv=str((helper.SOURCE / 'best_scheme_by_angle.csv').relative_to(ROOT)),
        source_csv_sha256=sha(helper.SOURCE / 'best_scheme_by_angle.csv'),
        helper_sha256=sha(PRIOR / 'plot_skr_vs_zenith.py'), renderer_sha256=sha(__file__),
        original_selection_validation=original_validation, statistics=statistics,
        y_scale='log', log_base=10, y_limits=[1e-5, 1e-3], x_limits_deg=[0,60],
        displayed_samples=22, hidden_nonpositive_samples=161, negative_source_data_preserved=True,
        zero_clipping=False, interpolation=False, smoothing=False, new_SKR_Cw_channel_MI_Holevo_evaluations=0,
        font=font, png_dpi=600, protected_historical_files=len(startup['protected']),
        outputs={ext:dict(path=STEM+'.'+ext,sha256=sha(OUT/(STEM+'.'+ext))) for ext in ['pdf','png']})
    (OUT / 'plot_validation.json').write_bytes((json.dumps(validation,indent=2,ensure_ascii=False)+'\n').encode('utf-8'))
    print(json.dumps(dict(status=validation['status'], displayed=22, hidden=161,
                         y_scale='log10', protected=len(startup['protected']))))


if __name__ == '__main__':
    main()
