import copy
import json
import csv
from pathlib import Path
import numpy as np
import pytest

from uav_qkd.config import load_config, build_scenario
from uav_qkd.experiments import run_experiment


ROOT = Path(__file__).parents[1]


def test_demo_reproducible_and_paper_fails_closed(tmp_path):
    config = load_config(ROOT/'configs/demo.yaml')
    s1, _ = build_scenario(config)
    s2, _ = build_scenario(config)
    np.testing.assert_array_equal(s1.z, s2.z)
    np.testing.assert_array_equal(s1.rates, s2.rates)
    run_experiment(config, tmp_path, figures=False, sensitivities=False)
    data = json.loads((tmp_path/'results.json').read_text(encoding='utf-8'))
    assert len(data['runs']) == 4
    assert data['data_status'] == 'SYNTHETIC DEMONSTRATION — NOT PAPER RESULTS'
    assert (tmp_path/'summary.csv').is_file() and (tmp_path/'trajectories.csv').is_file()
    for run in data['runs']:
        assert run['runtime_s'] >= 0 and run['python_peak_bytes'] > 0
        for solution in run['solutions'].values():
            assert solution['energy_j'] <= config['energy_budget_j']
    paper = load_config(ROOT/'configs/paper.yaml')
    with pytest.raises(ValueError, match='Missing scientific inputs'):
        build_scenario(paper)


@pytest.mark.parametrize('key,value', [('dt', 0), ('m0', 0), ('epsilon', 1),
                                      ('energy_budget_j', float('nan')), ('max_horizon', 0)])
def test_bad_config_rejected(key, value):
    config = copy.deepcopy(load_config(ROOT/'configs/demo.yaml'))
    config[key] = value
    with pytest.raises(ValueError):
        build_scenario(config)


def test_synthetic_flag_cannot_enter_paper_mode():
    c = load_config(ROOT/'configs/demo.yaml')
    c['mode'] = 'paper'
    with pytest.raises(ValueError, match='synthetic|scientific|provenance'):
        build_scenario(c)


def test_approximate_run_never_launches_exact_dp(tmp_path, monkeypatch):
    from uav_qkd import experiments
    c = load_config(ROOT/'configs/demo.yaml')
    c['dp'] = dict(mode='approximate', label_cap=1)
    original = experiments.solve_dp
    def approximate_only(s, **kwargs):
        assert kwargs.get('label_cap') is not None, 'Approximate run launched unbounded exact DP'
        return original(s, **kwargs)
    monkeypatch.setattr(experiments, 'solve_dp', approximate_only)
    experiments.run_experiment(c, tmp_path, figures=False, sensitivities=False)


def test_every_synthetic_table_has_status(tmp_path):
    c = load_config(ROOT/'configs/demo.yaml')
    run_experiment(c, tmp_path, figures=False, sensitivities=False)
    for path in tmp_path.glob('*.csv'):
        with path.open(encoding='utf-8') as f:
            for row in csv.DictReader(f):
                assert row.get('data_status') == 'SYNTHETIC DEMONSTRATION — NOT PAPER RESULTS', path.name


def test_saved_result_verifier_detects_corruption(tmp_path):
    from uav_qkd.verify import verify_results
    c = load_config(ROOT/'configs/demo.yaml')
    run_experiment(c, tmp_path, figures=False, sensitivities=False)
    assert verify_results(tmp_path)['trajectory_metric_checks'] == 80
    with (tmp_path/'summary.csv').open('a', encoding='utf-8') as f:
        f.write('tampered')
    with pytest.raises(ValueError, match='hash mismatch'):
        verify_results(tmp_path)
