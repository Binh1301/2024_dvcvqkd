"""Saved-data renderer controls; fixtures are synthetic, never research evidence."""
import csv
import hashlib
import importlib
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def fixture(out, degenerate=False):
    positions = [dict(position_index=i, x_m=x, y_m=y, z_m=1000)
                 for i, (x, y) in enumerate(((250, 250), (750, 250), (250, 750), (750, 750)))]
    write_csv(out/'positions.csv', positions)
    winners = [dict(p, K_raw=(-.2 if i == 0 else i/10), K_star=i/10,
                    VA=1+i, nu_raw=i/100, family='MB') for i, p in enumerate(positions)]
    write_csv(out/'p1/winners.csv', winners)
    write_csv(out/'p1/family_winners.csv', winners)
    blocked = np.zeros((2, 4, 30), dtype=bool)
    blocked[0, 0, ::2] = True
    (out/'clouds').mkdir()
    np.savez(out/'clouds/states.npz', blocked=blocked, usable_skr=np.zeros_like(blocked, dtype=float))
    values = [0.] if degenerate else [0., .001, .01]
    (out/'mobility').mkdir()
    (out/'mobility/lambda_schedule.json').write_text(json.dumps(dict(values=values, representative=0.)), encoding='utf-8')
    paths = [dict(strategy=s, slot=t+1, realization_id=0, lambda_bits_per_use=0.,
                  position_index=(t % 4 if s != 'Stationary' else 0),
                  x_m=positions[t % 4 if s != 'Stationary' else 0]['x_m'],
                  y_m=positions[t % 4 if s != 'Stationary' else 0]['y_m'])
             for s in ('Stationary', 'Greedy', 'DP') for t in range(30)]
    write_csv(out/'mobility/representative_paths.csv', paths)
    write_csv(out/'mobility/representative_metrics.csv', [dict(strategy=s, average_skr_bits_per_use=.1)
                                                       for s in ('Stationary', 'Greedy', 'DP')])
    stats = [dict(lambda_index=i, lambda_bits_per_use=v, strategy=s, metric=m,
                  mean=.1 if m == 'average_skr_bits_per_use' else 100., ci95_low=0.,
                  ci95_high=.2 if m == 'average_skr_bits_per_use' else 200., realizations=2)
             for i, v in enumerate(values) for s in ('Stationary', 'Greedy', 'DP')
             for m in ('average_skr_bits_per_use', 'total_distance_m')]
    write_csv(out/'mobility/lambda_statistics.csv', stats)
    rows = [dict(distance_km=20+i, Uniform_K_raw=v, Fixed_MB_K_raw=v+.1,
                 Optimized_MB_K_raw=v+.2) for i, v in enumerate((.2, -.1, 0., .1))]
    write_csv(out/'figures/figure1_distance.csv', rows)
    return dict(geometry=dict(grid_side_m=1000), mission=dict(slot_duration_s=20, max_speed_m_per_s=100))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class SavedPlotTests(unittest.TestCase):
    def renderer(self):
        return importlib.import_module('scripts.plot_manuscript_mobility')

    def test_export_preserves_raw_inputs_and_emits_vector_pdf_and_350dpi_png(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder)
            settings = fixture(out)
            inputs = {p: digest(p) for p in out.rglob('*') if p.is_file()}
            renderer = self.renderer()
            plotted = []
            original_plot, original_close = renderer.plt.Axes.plot, renderer.plt.close

            def observe_plot(ax, *args, **kwargs):
                if kwargs.get('label') == 'Optimized Uniform':
                    self.assertEqual(kwargs.get('marker'), 'o')
                    plotted.append(np.array(args[1], copy=True))
                return original_plot(ax, *args, **kwargs)

            def inspect_headroom(fig=None):
                if isinstance(fig, renderer.plt.Figure) and fig._suptitle is not None:
                    fig.canvas.draw()
                    canvas = fig.canvas.get_renderer()
                    title = fig._suptitle.get_window_extent(canvas)
                    legend = fig.legends[0].get_window_extent(canvas)
                    self.assertGreater(title.ymin, legend.ymax)
                    self.assertGreater(legend.ymin, max(ax.get_window_extent(canvas).ymax for ax in fig.axes))
                    if fig._suptitle.get_text() == 'Clouds and feasible UAV trajectories':
                        self.assertIn('Mission ID 0; λ = 0 bits/use', [t.get_text() for t in fig.texts])
                if isinstance(fig, renderer.plt.Figure) and any(ax.get_xlabel() == 'λ (bits/use)' for ax in fig.axes):
                    self.assertIn('λ axis: base-10 symlog; linear threshold = 0.001 bits/use',
                                  [t.get_text() for t in fig.texts])
                return original_close(fig)

            with patch.object(renderer.plt.Axes, 'plot', observe_plot), patch.object(renderer.plt, 'close', inspect_headroom):
                renderer.export_results(out, settings)
            np.testing.assert_equal(plotted[0], [.2, np.nan, np.nan, .1])
            np.testing.assert_equal(plotted[1], [.2, -.1, 0., .1])
            self.assertEqual(inputs, {p: digest(p) for p in inputs})
            receipt = json.loads((out/'figures/render_receipt.json').read_text())
            self.assertFalse(receipt['scientific_recalculation'])
            self.assertEqual(receipt['nonpositive_exclusions'], {
                'Uniform_K_raw': 2, 'Fixed_MB_K_raw': 1, 'Optimized_MB_K_raw': 0})
            self.assertEqual(receipt['symlog_linthresh'], .001)
            self.assertEqual(len(receipt['figure_paths']), 22)
            for relative in receipt['figure_paths']:
                path = out/relative
                self.assertTrue(path.exists(), relative)
                if path.suffix == '.pdf':
                    self.assertNotIn(b'/Subtype /Image', path.read_bytes())
                else:
                    png = path.read_bytes()
                    idx = png.index(b'pHYs')
                    xppm, yppm, unit = struct.unpack('>IIB', png[idx+4:idx+13])
                    self.assertEqual(unit, 1)
                    self.assertAlmostEqual(xppm*.0254, 350, delta=.05)
                    self.assertEqual(xppm, yppm)
            with (out/'figures/plot_data/fig1_distance_display.csv').open(newline='') as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(float(rows[1]['Uniform_K_raw']), -.1)
            self.assertEqual(rows[1]['Uniform_K_log_display'], '')
            self.assertEqual(rows[2]['Uniform_K_log_display'], '')
            self.assertEqual(float(rows[3]['Uniform_K_log_display']), .1)
            self.assertEqual(receipt['renderer_sha256'], digest(Path(self.renderer().__file__)))

    def test_degenerate_lambda_has_no_invented_threshold_or_sweep(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder)
            settings = fixture(out, degenerate=True)
            self.renderer().export_results(out, settings)
            receipt = json.loads((out/'figures/render_receipt.json').read_text())
            self.assertIsNone(receipt['symlog_linthresh'])
            self.assertIn('single', receipt['captions']['fig3_mobility_tradeoff'].lower())

    def test_invalid_ordered_path_fails_before_export(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder)
            settings = fixture(out)
            settings['mission']['max_speed_m_per_s'] = .01
            with self.assertRaisesRegex(ValueError, 'feasible'):
                self.renderer().export_results(out, settings)
            self.assertFalse((out/'figures/render_receipt.json').exists())


if __name__ == '__main__':
    unittest.main()
