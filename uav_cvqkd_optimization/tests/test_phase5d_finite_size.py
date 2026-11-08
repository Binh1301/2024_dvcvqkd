"""Pure-math finite-size sensitivity checks; no channel or SKR reevaluation."""
import json
import math
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_strict_integer_threshold_and_single_terminal_penalty():
    from uav_qkd.finite_size_feasibility import block_proxy, positive_block_threshold
    threshold = positive_block_threshold(7., .5)
    assert threshold['n_crit'] == 2.
    assert threshold['n_min'] == 3
    assert block_proxy(7., 2, .5)['key_bits'] == 0.
    assert block_proxy(7., 3, .5)['key_bits'] > 0.
    result = block_proxy(1., 100, .5)
    assert result['penalty_bits'] == pytest.approx(70 * math.sqrt(2))
    assert result['key_bits'] == pytest.approx(100 - 70 * math.sqrt(2))


def test_threshold_uses_unrounded_input_near_integer_boundary():
    from uav_qkd.finite_size_feasibility import positive_block_threshold
    assert positive_block_threshold(math.nextafter(7., math.inf), .5)['n_min'] == 2
    assert positive_block_threshold(math.nextafter(7., 0.), .5)['n_min'] == 3


@pytest.mark.parametrize('r,n,eps', [(math.nan, 1, .5), (1., -1, .5),
    (1., 1.5, .5), (1., True, .5), (1., 1, 0.), (1., 1, 1.), (1., 1, math.nan)])
def test_invalid_block_domains_fail_closed(r, n, eps):
    from uav_qkd.finite_size_feasibility import block_proxy
    with pytest.raises(ValueError):
        block_proxy(r, n, eps)


def test_nonpositive_raw_rate_has_no_positive_threshold():
    from uav_qkd.finite_size_feasibility import block_proxy, positive_block_threshold
    for r in (0., -.1):
        assert positive_block_threshold(r, 3e-8)['n_min'] is None
        assert block_proxy(r, 10**8, 3e-8)['key_bits'] == 0.
    assert block_proxy(.01, 0, 3e-8)['key_bits'] == 0.


def test_cloud_fraction_only_enters_mission_budget_once():
    from uav_qkd.finite_size_feasibility import mission_requirements
    clear = mission_requirements(.01, 3e-8, 100., 1.)
    half = mission_requirements(.01, 3e-8, 100., .5)
    assert half['feasible'] is None  # Actual mission feasibility needs the unassigned product.
    assert half['required_product_strict_gt_per_s'] == 2 * clear['required_product_strict_gt_per_s']
    assert half['integer_budget_product_ge_per_s'] == 2 * clear['integer_budget_product_ge_per_s']
    assert 'key_bits' not in half  # f_s and eta_valid remain unassigned.
    blocked = mission_requirements(.01, 3e-8, 100., 0.)
    assert blocked['feasible'] is False
    assert blocked['key_bits'] == 0.
    assert blocked['required_product_strict_gt_per_s'] is None


@pytest.mark.parametrize('T,c', [(0., .5), (math.inf, .5), (1., -.1), (1., 1.1), (1., math.nan)])
def test_invalid_mission_domains_fail_closed(T, c):
    from uav_qkd.finite_size_feasibility import mission_requirements
    with pytest.raises(ValueError):
        mission_requirements(.01, 3e-8, T, c)


def test_artifacts_use_all_actual_pilot_rates_and_no_mission_defaults(tmp_path):
    from uav_qkd.finite_size_feasibility import generate
    summary = generate(ROOT, tmp_path)
    pilot = json.loads((ROOT / 'results/phase5c_skr_noise_pilot_20261107/summary.json').read_text())
    assert len(summary['rates']) == 10
    for row in summary['rates']:
        source = next(p for p in pilot['comparisons'] if p['point']['point_id'] == row['point_id'])
        assert row['r_clear_raw'] == source[row['noise_case']]['K_raw']
        assert row['security_valid'] is False
    assert summary['reference_only']['n_block_reference'] == 80_000_000
    assert summary['mission_parameters'] == {'f_s': None, 'eta_valid': None, 'm0': None}
    assert summary['row_counts'] == {'block_sensitivity': 210, 'mission_sensitivity': 750}
    assert summary['reference_only']['delta_reference_bits_per_signal'] == pytest.approx(.0039898819698402565)


def test_changed_pilot_payload_is_rejected(tmp_path):
    from uav_qkd.finite_size_feasibility import verify_pilot
    (tmp_path / 'output_manifest.json').write_text(json.dumps({'summary.json': '0' * 64}))
    (tmp_path / 'summary.json').write_text('{}')
    with pytest.raises(ValueError, match='hash'):
        verify_pilot(tmp_path)


def test_missing_pilot_manifest_coverage_is_rejected(tmp_path):
    from uav_qkd.finite_size_feasibility import verify_pilot
    (tmp_path / 'output_manifest.json').write_text('{}')
    with pytest.raises(ValueError, match='coverage'):
        verify_pilot(tmp_path)


def test_nonempty_output_is_rejected_before_any_writes(tmp_path):
    from uav_qkd.finite_size_feasibility import generate
    keep = tmp_path / 'keep.txt'
    keep.write_bytes(b'preserve existing results\n')
    with pytest.raises(FileExistsError, match='nonempty'):
        generate(ROOT, tmp_path)
    assert keep.read_bytes() == b'preserve existing results\n'
    assert list(tmp_path.iterdir()) == [keep]
