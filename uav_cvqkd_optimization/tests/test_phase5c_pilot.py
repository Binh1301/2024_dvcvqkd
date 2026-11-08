"""Pilot orchestration software fixtures; no fabricated research outcomes."""
import pytest


def test_five_positions_are_bounded_and_distinct_in_radius():
    from uav_qkd.skr_pilot import select_positions,read_rows,LOOKUP
    rows=read_rows(LOOKUP/'skr_map.csv')
    chosen=select_positions(rows)
    assert len(chosen)==5
    assert [(r['x_m'],r['y_m']) for r in chosen[:3]]==[(1000.,1000.),(1480.,1000.),(0.,0.)]
    assert len({r['radius2_m2'] for r in chosen})==5
    assert len({r['point_id'] for r in chosen})==5


def test_reproduction_comparison_checks_signed_rates_and_exact_source_identity():
    from uav_qkd.skr_pilot import compare_candidate
    r={k:1. for k in ('eta_f','xi_f','I_AB','chi_BE','K_raw')}
    r.update(ensemble_hash='source',VA=.5,nu_raw=.1)
    assert compare_candidate(r,r)['passed']
    changed=dict(r,K_raw=-1.)
    assert not compare_candidate(changed,r)['passed']
    assert not compare_candidate(dict(r,ensemble_hash='other'),r)['passed']
    assert not compare_candidate(dict(r,VA=.6),r)['passed']


def test_gate_requires_all_five_successful_reproductions():
    from uav_qkd.skr_pilot import require_reproduction_pass
    good=[dict(passed=True) for _ in range(5)]
    require_reproduction_pass(good)
    for bad in (good[:4],good[:4]+[dict(passed=False)],[]):
        with pytest.raises(ValueError,match='reproduction'):
            require_reproduction_pass(bad)


def test_trial_noise_changes_only_requested_scalar():
    from uav_qkd.skr_pilot import effective_protocol
    base=dict(xi_ch=.0186,xi_det=.005,beta=.95,numerical={'MI_tolerance':2e-10})
    a=effective_protocol(base,.0186);b=effective_protocol(base,.0136)
    assert {k for k in a if a[k]!=b[k]}=={'xi_ch'}
    assert base['xi_ch']==.0186
    with pytest.raises(ValueError):effective_protocol(base,.01)


def test_virtual_module_filenames_are_not_treated_as_source_files():
    from types import SimpleNamespace
    from uav_qkd.skr_pilot import repository_producers
    assert repository_producers([SimpleNamespace(__file__='_nonexistent_virtual_ops.py')])=={}


def test_resume_rejects_reproduction_checkpoint_as_target():
    from uav_qkd.skr_pilot import validate_checkpoint,read,ROOT
    from copy import deepcopy
    d=ROOT/'results/phase5c_skr_noise_pilot_20261107'
    manifest=read(d/'input_manifest.json');config=read(d/'config.json')
    record=read(d/'target/p0.json')
    validate_checkpoint(record,'target',config['points'][0],record['input_manifest_sha256'],manifest['config_sha256'],config['effective_protocols']['target'],manifest['roster'])
    for change in ('stage','trial_config_sha256','active_effective_protocol','candidates'):
        bad=deepcopy(record)
        if change=='stage':bad[change]='reproduction'
        elif change=='trial_config_sha256':bad[change]='other'
        elif change=='active_effective_protocol':bad[change]=config['effective_protocols']['reproduction']
        else:bad[change]=bad[change][:-1]
        with pytest.raises(ValueError):validate_checkpoint(bad,'target',config['points'][0],record['input_manifest_sha256'],manifest['config_sha256'],config['effective_protocols']['target'],manifest['roster'])


def test_historical_csvs_must_match_original_seal(tmp_path):
    from uav_qkd.skr_pilot import verify_historical_file,LOOKUP,sha
    assert verify_historical_file(LOOKUP/'source_pool.csv')==sha(LOOKUP/'source_pool.csv')
    # Boundary check uses an independent software fixture root, not the dataset.
    import json
    (tmp_path/'source_pool.csv').write_text('changed')
    (tmp_path/'final_manifest.json').write_text(json.dumps({'files':{'source_pool.csv':'0'*64}}))
    with pytest.raises(ValueError,match='Historical'):
        verify_historical_file(tmp_path/'source_pool.csv',directory=tmp_path)


def test_output_boundary_refuses_other_projects_and_unowned_resume(tmp_path,monkeypatch):
    from uav_qkd import skr_pilot
    monkeypatch.setattr(skr_pilot,'ROOT',tmp_path)
    with pytest.raises(ValueError,match='namespace'):
        skr_pilot.validate_output_directory(tmp_path/'historical',resume=True)
    path=tmp_path/'results/phase5c_unknown';path.mkdir(parents=True)
    (path/'keep.txt').write_text('historical')
    with pytest.raises(ValueError,match='config'):
        skr_pilot.validate_output_directory(path,resume=True)
    assert [f.name for f in path.iterdir()]==['keep.txt']
