"""Plot checks use measured synthetic test bundles, never paper results."""
import copy
import json
from pathlib import Path
import numpy as np
import pytest
import matplotlib.pyplot as plt

from uav_qkd.config import load_config
from uav_qkd.propulsion import PropulsionParams, propulsion_power
from uav_qkd.paper_figures import (
    STYLES, load_figure_inputs, generate_figures, plot_fig01_rotor_power,
    plot_fig02_cloud_maps, plot_fig03_skr_lookup, plot_fig04_trajectory_p1,
    plot_fig06_energy, plot_fig07_finite_size, plot_fig08_key_comparison,
    plot_fig09_runtime_memory, plot_fig10_sensitivity, validate_report,
)

ROOT = Path(__file__).parents[1]
DEMO = ROOT/'results/final_demo_20261107'


@pytest.fixture(scope='module')
def demo(tmp_path_factory):
    from uav_qkd.experiments import run_experiment
    directory = tmp_path_factory.mktemp('current_producer_synthetic_fixture')
    run_experiment(load_config(ROOT/'configs/demo.yaml'), directory, figures=False)
    return load_figure_inputs(ROOT/'configs/demo.yaml', directory, exploratory=True)


def test_default_paper_export_blocks_missing_data_without_placeholders(tmp_path):
    report = generate_figures(ROOT/'configs/paper.yaml', None, tmp_path)
    assert report['paper_mode'] == 'NOT_RUN'
    assert [row['status'] for row in report['figures']] == ['READY']+['BLOCKED']*9
    assert len(list(tmp_path.glob('fig*.json'))) == 10
    assert len(list(tmp_path.glob('fig*.pdf'))) == len(list(tmp_path.glob('fig*.png'))) == 1
    assert 'INSUFFICIENT_EVIDENCE' in json.dumps(report)
    for row in report['figures']:
        assert row['inputs'] and row['configuration'] and row['caption']
        if row['status'] == 'BLOCKED':
            assert row['reasons'] and row['outputs'] == {}


def test_styles_and_rotor_values_are_exact():
    colors = [STYLES[name]['color'] for name in STYLES]
    assert colors == ['#777777', '#0072b2', '#e69f00', '#009e73']
    assert len(set(s['linestyle'] for s in STYLES.values())) == 4
    c = load_config(ROOT/'configs/paper.yaml')
    fig = plot_fig01_rotor_power(c, 'single')
    assert fig.get_size_inches()[0] == pytest.approx(3.5)
    power, envelope = fig.axes[0].lines[:2]
    np.testing.assert_allclose(power.get_ydata(), propulsion_power(power.get_xdata(), PropulsionParams(**c['propulsion'])))
    assert np.all(envelope.get_ydata() <= power.get_ydata()+1e-8)
    assert power.get_ydata()[0] == pytest.approx(1371.321522813272)
    plt.close(fig)


def test_demo_cannot_be_promoted_without_explicit_exploratory():
    with pytest.raises(ValueError, match='EXPLORATORY'):
        load_figure_inputs(ROOT/'configs/demo.yaml', DEMO)


def test_cloud_binary_is_exact_threshold_of_same_field(demo):
    fig = plot_fig02_cloud_maps(demo, 'double')
    images = [ax.images[0] for ax in fig.axes if ax.images]
    n = len(demo['config']['plot_times_s'])
    for gray, binary in zip(images[:n], images[n:]):
        np.testing.assert_array_equal(np.asarray(binary.get_array()),
                                      np.asarray(gray.get_array()) >= demo['config']['cloud']['threshold_mg_m3'])
        assert gray.get_extent() == binary.get_extent()
    plt.close(fig)


def test_skr_plot_retains_native_values(demo):
    fig = plot_fig03_skr_lookup(demo, 'double')
    values = np.asarray(fig.axes[0].collections[0].get_array()).ravel()
    np.testing.assert_allclose(np.sort(values), np.sort(demo['context']['lookup'].rates))
    plt.close(fig)


def test_trajectories_and_energy_use_selected_prefixes(demo):
    fig = plot_fig04_trajectory_p1(demo, 'double')
    for line, run in zip(fig.axes[0].lines[:4], demo['report']['runs']):
        q = np.asarray(run['solutions']['P1']['trajectory_m'])
        np.testing.assert_array_equal(line.get_xdata(), q[:, 0])
        np.testing.assert_array_equal(line.get_ydata(), q[:, 1])
    plt.close(fig)
    fig = plot_fig06_energy(demo, 'double')
    for line, run in zip(fig.axes[0].lines[:4], demo['report']['runs']):
        sol = run['solutions']['P1']
        assert line.get_ydata()[-1] == sol['energy_j']
        assert line.get_xdata()[-1] == sol['mission_time_s']
    plt.close(fig)


def test_finite_size_and_comparisons_use_saved_terminal_values(demo):
    fig = plot_fig07_finite_size(demo, 'double')
    for ax, key in zip(fig.axes, ('valid_signals', 'asymptotic_bits', 'penalty_bits', 'key_bits')):
        for line, run in zip(ax.lines, demo['report']['runs']):
            assert line.get_ydata()[-1] == run['solutions']['P2'][key]
    plt.close(fig)
    fig = plot_fig08_key_comparison(demo, 'single')
    for ax, objective, metric in zip(fig.axes, ('P1', 'P2'), ('average_skr_bits_s', 'key_bits')):
        np.testing.assert_allclose([bar.get_height() for bar in ax.patches],
                                  [run['solutions'][objective][metric] for run in demo['report']['runs']])
    plt.close(fig)


def test_runtime_memory_uses_measured_values(demo):
    fig = plot_fig09_runtime_memory(demo, 'double')
    for ax, key, factor in zip(fig.axes, ('runtime_s', 'python_peak_bytes', 'sampled_peak_rss_bytes'), (1., 2**20, 2**20)):
        np.testing.assert_allclose([bar.get_height() for bar in ax.patches],
                                  [run[key]/factor for run in demo['report']['runs']])
    plt.close(fig)


def test_corrupt_metrics_and_missing_runtime_are_rejected(demo):
    report = copy.deepcopy(demo['report'])
    report['runs'][0]['solutions']['P2']['series'][-1]['penalty_bits'] += 1
    with pytest.raises(ValueError, match='penalty_bits'):
        validate_report(report)
    report = copy.deepcopy(demo['report'])
    del report['runs'][0]['runtime_s']
    with pytest.raises(ValueError, match='runtime_s'):
        validate_report(report)


def test_sensitivity_plot_uses_recorded_rows(demo):
    fig = plot_fig10_sensitivity(demo, 'double')
    first = [row for row in demo['sweeps'] if row['sensitivity']=='energy' and row['method']=='Stationary' and row['objective']=='P2']
    np.testing.assert_allclose(fig.axes[0].lines[0].get_ydata(), [float(row['objective_value']) for row in first])
    plt.close(fig)


def test_mismatched_configuration_and_output_overwrite_are_rejected(tmp_path):
    with pytest.raises(ValueError, match='configuration'):
        load_figure_inputs(ROOT/'configs/paper.yaml', DEMO, exploratory=True)
    tmp_path.joinpath('keep.txt').write_text('historical')
    with pytest.raises(FileExistsError):
        generate_figures(ROOT/'configs/paper.yaml', None, tmp_path)
    assert tmp_path.joinpath('keep.txt').read_text() == 'historical'


def test_empty_or_incomplete_saved_seal_cannot_authenticate_measurements(tmp_path):
    report = json.loads((DEMO/'results.json').read_text(encoding='utf-8'))
    report['runs'][0]['runtime_s'] = 123456789.
    tmp_path.joinpath('results.json').write_text(json.dumps(report), encoding='utf-8')
    tmp_path.joinpath('input_manifest.json').write_bytes((DEMO/'input_manifest.json').read_bytes())
    tmp_path.joinpath('output_manifest.json').write_text('{}')
    with pytest.raises(ValueError, match='seal|manifest'):
        load_figure_inputs(ROOT/'configs/demo.yaml', tmp_path, exploratory=True)


def test_missing_audit_inputs_produce_blocked_manifests(tmp_path, monkeypatch):
    from uav_qkd import paper_figures
    monkeypatch.setattr(paper_figures, 'AUDIT', tmp_path/'missing_audit')
    result = generate_figures(ROOT/'configs/paper.yaml', None, tmp_path/'figures')
    assert result['counts']['BLOCKED'] == 10
    assert len(list((tmp_path/'figures').glob('fig*.json'))) == 10
    assert not list((tmp_path/'figures').glob('*.pdf'))


def test_captions_include_rotor_version_and_dp_classification(tmp_path):
    result = generate_figures(ROOT/'configs/paper.yaml', None, tmp_path)
    first = result['figures'][0]
    assert '1804.02238v1' in first['caption']
    assert first['source_variant'] == 'arxiv_v1_2018_not_IEEE_2019_parameter_table'


def test_short_paths_remain_visible_without_changing_coordinates(demo):
    fig = plot_fig04_trajectory_p1(demo, 'single')
    q = np.vstack([r['solutions']['P1']['trajectory_m'] for r in demo['report']['runs']])
    xspan = fig.axes[0].get_xlim()[1]-fig.axes[0].get_xlim()[0]
    assert xspan < 10*np.ptp(q[:, 0])
    plt.close(fig)


@pytest.mark.parametrize('column,width', [('single', 3.5), ('double', 7.16)])
def test_exported_png_has_ieee_width_and_600_dpi(tmp_path, column, width):
    from PIL import Image
    result = generate_figures(ROOT/'configs/paper.yaml', None, tmp_path, column=column)
    with Image.open(tmp_path/'fig01_rotor_power.png') as im:
        assert im.width == round(width*600)
        assert im.info['dpi'][0] == pytest.approx(600, abs=.02)
    assert (tmp_path/'fig01_rotor_power.pdf').read_bytes().startswith(b'%PDF')
    assert result['figures'][0]['width_in'] == width
