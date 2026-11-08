import numpy as np
import pytest

from uav_qkd.propulsion import PropulsionParams, propulsion_power, EnergyModel
from uav_qkd.cloud_model import GaussianCluster, CloudField
from uav_qkd.blockage import BlockageModel
from uav_qkd.finite_size import finite_key
from uav_qkd.skr_lookup import SKRLookup


@pytest.fixture
def params():
    return PropulsionParams(P0=79.86, Pi=88.63, U_tip=120., v0=4.03,
                            d0=.6, rho=1.225, s=.05, A=.503, v_max=20.)


def test_power_envelope_and_refinement(params):
    v = np.linspace(0, params.v_max, 1001)
    p = propulsion_power(v, params)
    assert np.isfinite(p).all() and (p > 0).all()
    model = EnergyModel(params, samples=1001)
    energy = model.energy(v, 1.)
    assert energy[0] == pytest.approx(params.P0 + params.Pi)
    assert np.all(energy <= p + 1e-9)
    assert np.diff(np.diff(energy)).min() >= -1e-9
    fine = EnergyModel(params, samples=4001)
    assert np.max(abs(energy - fine.energy(v, 1.))) < .001
    assert model.energy(21, 1.) == np.inf
    with pytest.raises(ValueError):
        model.energy(-1, 1.)


def test_cloud_continuous_translation():
    field = CloudField([GaussianCluster(10., (100., 10.), (20., 30.))], (-5., 0.))
    for t in (0, 1, 300, 1000):
        np.testing.assert_allclose(field.evaluate([[100.-5*t, 10.]], t), [10.])
    assert field.evaluate([[100., 10.]], 1)[0] != field.evaluate([[100., 10.]], 0)[0]
    with pytest.raises(ValueError):
        GaussianCluster(1., (0., 0.), (0., 1.))


def test_cloud_layer_path_not_endpoint():
    field = CloudField([GaussianCluster(10., (50., 0.), (2., 2.))], (0., 0.))
    model = BlockageModel(field, 5., (0., 0., 100.), 0., mode='layer',
                          layer_bottom_m=49., layer_top_m=51., sample_spacing_m=.2)
    assert model.blocked([100., 0.], 0.)
    assert not model.blocked([100., 30.], 0.)
    assert field.evaluate([[100., 0.]], 0.)[0] < 5
    outside = BlockageModel(field, 5., (0., 0., 100.), 0., mode='layer',
                            layer_bottom_m=101., layer_top_m=102., sample_spacing_m=.2)
    assert not outside.blocked([100., 0.], 0.)


def test_accumulated_finite_key():
    assert finite_key(0., 0, 100, 1e-6)['key_bits'] == 0
    a = finite_key(.2, 1, 1e6, 1e-6)
    b = finite_key(.4, 2, 1e6, 1e-6)
    assert b['penalty_bits'] == pytest.approx(np.sqrt(2)*a['penalty_bits'])
    assert b['penalty_per_signal'] < a['penalty_per_signal']
    assert b['penalty_bits'] != pytest.approx(2*a['penalty_bits'])


def test_lookup_formats_units_domain(tmp_path):
    rows = np.array([[0, 0, .001], [1, 0, .002], [0, 1, .003], [1, 1, .004]])
    lookup = SKRLookup.from_array(rows, coordinate_units='m', rate_units='bits/use')
    assert lookup([[.5, .5]])[0] == pytest.approx(.0025)
    with pytest.raises(ValueError, match='domain'):
        lookup([[2., 0.]])
    with pytest.raises(ValueError, match='units'):
        SKRLookup.from_array(rows, coordinate_units='km', rate_units='bits/use')
    for suffix in ('csv', 'npz', 'npy'):
        p = tmp_path / ('rates.'+suffix)
        if suffix == 'csv':
            np.savetxt(p, rows, delimiter=',', header='x_m,y_m,skr_bits_per_use', comments='')
        elif suffix == 'npz':
            np.savez(p, points=rows[:, :2], rates=rows[:, 2])
        else:
            np.save(p, rows)
        loaded = SKRLookup.load(p, coordinate_units='m', rate_units='bits/use')
        np.testing.assert_allclose(loaded([[.5, .5]]), [.0025])
