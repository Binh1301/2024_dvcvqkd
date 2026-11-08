from dataclasses import replace
from pathlib import Path
import numpy as np
import pytest
from uav_qkd.config import load_config
from uav_qkd.propulsion import propulsion_power
from uav_qkd.rotor_reference import load_reference, power_components, characteristic_speeds
from uav_qkd.rotor_power_figure import export_figure

ROOT = Path(__file__).parents[1]


@pytest.fixture
def ieee():
    return load_reference(ROOT/'configs/rotor/ieee_2019.yaml')


def test_ieee_coefficients_are_derived_from_the_source_set(ieee):
    p = ieee['params']
    assert p.P0 == pytest.approx(.012/8*1.225*.05*.503*120**3)
    assert p.Pi == pytest.approx(1.1*20**1.5/np.sqrt(2*1.225*.503))
    assert p.v0 == pytest.approx(np.sqrt(20/(2*1.225*.503)))
    assert p.P0 == pytest.approx(79.86, abs=.01)
    assert p.Pi == pytest.approx(88.63, abs=.01)
    assert p.P0+p.Pi == pytest.approx(168.48, abs=.01)
    assert ieee['config']['aircraft']['mean_induced_velocity_hover_m_s'] == 4.03
    assert p.v_max == 30 and p.A == .503 and p.U_tip == 300*.4


def test_component_sum_hover_and_induced_monotonicity(ieee):
    p = ieee['params']; v = np.linspace(0, 30, 1001)
    parts = power_components(v, p)
    assert np.isfinite(np.array(list(parts.values()))).all()
    assert (np.array(list(parts.values())) >= 0).all()
    np.testing.assert_allclose(parts['total_W'], parts['blade_profile_W']+parts['induced_W']+parts['parasite_W'], rtol=2e-15)
    np.testing.assert_allclose(parts['total_W'], propulsion_power(v, p))
    assert parts['total_W'][0] == pytest.approx(p.P0+p.Pi)
    assert np.diff(parts['induced_W']).max() < 0


def test_induced_power_remains_stable_at_large_speed(ieee):
    # Numerical stress only, outside the source aircraft's allowed flight range.
    p = replace(ieee['params'], v_max=1e6)
    part = power_components(np.array([1e4, 1e5, 1e6]), p)
    assert np.all(part['induced_W'] > 0)
    np.testing.assert_allclose(part['induced_W'], p.Pi*p.v0/np.array([1e4,1e5,1e6]), rtol=1e-6)


def test_characteristic_speeds_pass_dense_grid_and_stationarity(ieee):
    p = ieee['params']; result = characteristic_speeds(p, grid_samples=20001)
    grid = np.linspace(0, p.v_max, 50001)
    power = propulsion_power(grid, p)
    assert 0 <= result['ME']['speed_m_s'] <= p.v_max
    assert 0 < result['MR']['speed_m_s'] <= p.v_max
    assert result['ME']['objective_value'] <= power.min()+1e-8
    assert result['MR']['objective_value'] <= np.min(power[1:]/grid[1:])+1e-8
    h=1e-3
    for kind in ('ME','MR'):
        v=result[kind]['speed_m_s']
        objective = lambda x: float(propulsion_power(x,p))/(x if kind=='MR' else 1.)
        assert abs((objective(v+h)-objective(v-h))/(2*h)) < 1e-4
        assert result[kind]['grid_check_passed']


def test_profiles_preserve_the_arxiv_default_and_do_not_mix(ieee):
    old = load_reference(ROOT/'configs/rotor/arxiv_2018_v1.yaml')
    paper = load_config(ROOT/'configs/paper.yaml')
    for name,value in vars(old['params']).items():
        assert value == pytest.approx(paper['propulsion'][name], abs=1e-10)
    assert old['config']['name'] == 'arxiv_2018_v1'
    assert ieee['config']['name'] == 'ieee_2019'
    assert old['params'].v0 == 7.2
    assert old['params'].A == .79 and ieee['params'].A == .503
    assert old['params'].d0 == .3 and ieee['params'].d0 == .6
    assert old['params'].v_max == 60 and ieee['params'].v_max == 30


@pytest.mark.parametrize('value', [-1., 30.001, float('nan')])
def test_invalid_speeds_rejected(ieee,value):
    with pytest.raises(ValueError):
        power_components(value,ieee['params'])


def test_reference_figure_export_and_overwrite_guard(ieee,tmp_path):
    from PIL import Image
    result=export_figure(ROOT/'configs/rotor/ieee_2019.yaml',tmp_path)
    assert result['source_variant']=='ieee_2019'
    assert result['paper_mode']=='NOT_RUN'
    assert result['outputs']['pdf']['sha256']
    with Image.open(tmp_path/'fig02_propulsion_power_ieee2019.png') as im:
        assert im.width==2100
        assert im.info['dpi'][0]==pytest.approx(600,abs=.02)
    assert (tmp_path/'fig02_propulsion_power_ieee2019.pdf').read_bytes().startswith(b'%PDF')
    with pytest.raises(FileExistsError):
        export_figure(ROOT/'configs/rotor/ieee_2019.yaml',tmp_path)


@pytest.mark.parametrize('change', ['weight','policy'])
def test_modified_aircraft_cannot_keep_ieee_source_verified_label(tmp_path,change):
    import yaml
    config=load_config(ROOT/'configs/rotor/ieee_2019.yaml')
    config.pop('_config_path')
    if change=='weight':
        config['aircraft']['weight_N']=100.
    else:
        config['induced_velocity_policy']='table_value'
    path=tmp_path/'mixed.yaml'
    path.write_text(yaml.safe_dump(config),encoding='utf-8')
    with pytest.raises(ValueError,match='source|verified|profile'):
        export_figure(path,tmp_path/'export')
