"""Verify the partial paper config without running a scientific mission.

Run from the package directory: python -X utf8 scripts/verify_paper_configuration.py
"""
from pathlib import Path
import hashlib
import json
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from uav_qkd.config import load_config, build_scenario
from uav_qkd.propulsion import PropulsionParams, EnergyModel, propulsion_power


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    out = ROOT/'results/paper_configuration_audit_20261107'
    config = load_config(ROOT/'configs/paper.yaml')
    p = PropulsionParams(**config['propulsion'])
    p0 = .012/8*1.225*.05*.79*200**3
    pi = 1.1*100**1.5/np.sqrt(2*1.225*.79)
    assert abs(p.P0-p0) < 1e-10 and abs(p.Pi-pi) < 1e-10
    assert abs(float(propulsion_power(0., p))-(p0+pi)) < 1e-9
    speeds = np.linspace(0, p.v_max, 301)
    powers = propulsion_power(speeds, p)
    energy_rows = []
    previous = None
    for count in (2001, 4001, 8001):
        energies = EnergyModel(p, count).energy(speeds, 1.)
        assert np.isfinite(energies).all() and np.all(energies <= powers+1e-9)
        assert np.min(np.diff(np.diff(energies))) >= -1e-8
        change = None if previous is None else float(np.max(abs(energies-previous)))
        if change is not None:
            assert change < config['energy_tolerance_j']
        energy_rows.append(dict(velocity_samples=count, max_energy_change_j=change))
        previous = energies
    model = EnergyModel(p, 8001)
    assert model.energy(0., 1.) == p.P0+p.Pi
    assert model.energy(p.v_max+1, 1.) == np.inf
    try:
        build_scenario(config)
    except ValueError as error:
        rejection = str(error)
        assert 'Missing scientific inputs' in rejection
    else:
        raise AssertionError('Incomplete paper configuration unexpectedly entered experiment execution')
    protected = json.loads((out/'protected_previous_results.json').read_text(encoding='utf-8'))
    workspace = ROOT.parent
    for path, digest in protected.items():
        assert sha(workspace/path) == digest, f'Historical result changed: {path}'
    receipt = dict(status='CURRENTLY_VERIFIED_PASS',
                   scope='reference rotor numerics and expected rejection of incomplete paper config',
                   paper_experiment_status='NOT_RUN',
                   partial_configuration_load='CURRENTLY_VERIFIED_PASS',
                   required_input_gate='CURRENTLY_VERIFIED_PASS', validation_error=rejection,
                   derived_P0_W=float(p0), derived_Pi_W=float(pi), hover_power_W=float(p0+pi),
                   v0_derived_m_s=float(np.sqrt(100/(2*1.225*.79))), v0_table_m_s=p.v0,
                   energy_convergence=energy_rows, protected_previous_result_files=len(protected),
                   paper_yaml_sha256=sha(ROOT/'configs/paper.yaml'), producer_sha256=sha(__file__))
    (out/'configuration_validation.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
