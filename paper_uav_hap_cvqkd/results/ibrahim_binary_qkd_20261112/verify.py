"""Read-only verification of this sealed diagnostic package; no QKD/field runs."""
from pathlib import Path
import csv
import hashlib
import json
import numpy as np
from PIL import Image

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name):
    return json.loads((OUT / name).read_text(encoding='utf-8'))


def verify():
    manifest = load('artifact_hashes.json')
    excluded = {'artifact_hashes.json', 'verification.json'}
    actual = {p.relative_to(OUT).as_posix() for p in OUT.rglob('*')
              if p.is_file() and '__pycache__' not in p.parts and p.name not in excluded}
    assert actual == set(manifest), 'Export roster changed'
    for name, digest in manifest.items():
        assert sha(OUT / name) == digest, name
    protected = load('protected_inputs.json')
    inputs = load('input_hashes.json')
    design = load('design_receipt.json')
    for mapping in (protected, inputs, design['producer_hashes'], load('producer_hashes.json')):
        for name, digest in mapping.items():
            assert sha(ROOT / name) == digest, name
    assert sha(ROOT / 'docs/FINAL_MODEL_SPEC.md') == design['frozen_actual_sha256']
    assert design['frozen_actual_sha256'] != design['frozen_historical_expected_sha256']
    cfg = load('configuration.json')
    assert cfg == design['settings']
    assert cfg['diagnostic_threshold_db'] == .1 and cfg['official_fallback_to_diagnostic'] is False
    with np.load(ROOT / cfg['gaussian_input'], allow_pickle=False) as data:
        g = data['X']
        coordinates = {k: data[k] for k in ('time_s', 'x_m', 'y_m')}
    assert g.shape == (1000, 50, 50) and g.dtype == np.float64 and np.isfinite(g).all()
    np.testing.assert_array_equal(coordinates['time_s'], np.arange(1000))
    for key in ('x_m', 'y_m'):
        np.testing.assert_array_equal(coordinates[key], (np.arange(50) + .5) * 40)
    arrays = []
    continuous = ROOT / cfg['continuous_directory']
    for filename, key in [('cloud_clwc.npz', 'clwc_g_m3'),
                          ('cloud_attenuation_db.npz', 'attenuation_db'),
                          ('cloud_transmittance.npz', 'transmittance')]:
        with np.load(continuous / filename, allow_pickle=False) as data:
            z = data[key]
            assert z.shape == g.shape and z.dtype == np.float64 and np.isfinite(z).all()
            arrays.append(z)
            for k, values in coordinates.items():
                np.testing.assert_array_equal(data[k], values)
    liquid, a, t = arrays
    assert np.all(liquid >= 0) and np.all(a >= 0) and np.all((t > 0) & (t <= 1))
    np.testing.assert_allclose(t, 10 ** (-a / 10), rtol=1e-15, atol=0)
    for name in ('diagnostic_binary_blockage.npz', 'diagnostic_qkd_availability.npz', 'official_pending_status.npz'):
        with np.load(OUT / name, allow_pickle=False) as data:
            for k, values in coordinates.items():
                np.testing.assert_array_equal(data[k], values)
            assert str(data['axis_order']) == 't,y,x'
    with np.load(OUT / 'diagnostic_binary_blockage.npz') as data:
        b = data['binary_blockage']
        assert b.dtype == np.uint8 and b.shape == a.shape
        np.testing.assert_array_equal(b, (a >= .1).astype(np.uint8))
        assert data['resolved_mask'].all() and np.all(data['classification_status'] == 3)
        assert np.all(data['clear_sky_available'] == 1) and str(data['scope']) == cfg['diagnostic_scope']
    with np.load(OUT / 'diagnostic_qkd_availability.npz') as data:
        assert data['qkd_available'].dtype == np.bool_
        np.testing.assert_array_equal(data['qkd_available'], b == 0)
        assert data['resolved_mask'].all()
    with np.load(OUT / 'diagnostic_threshold_0p1db.npz') as data:
        assert np.all(data['diagnostic_threshold_db'] == .1)
        assert 'NOT_VALIDATED' in str(data['scope'])
    with np.load(OUT / 'official_pending_status.npz') as data:
        assert data['binary_blockage'].shape == a.shape
        assert np.all(data['binary_blockage'] == 255)
        assert not data['qkd_available'].any() and not data['resolved_mask'].any()
        assert np.all(data['clear_sky_available'] == 255) and np.all(data['classification_status'] == 2)
        assert 'critical_attenuation_db' not in data.files
    assert not list(OUT.glob('*critical*threshold*.npz'))
    official = load('official_055_status.json')
    assert official['status'] == 'BLOCKED_BY_ENVIRONMENT'
    assert official['native_import_returncode'] != 0 and official['receiver_diameter_m'] == .55
    for flag in ('SKR_evaluation_executed', 'threshold_search_executed', 'threshold_validated', 'fallback_to_0p1db'):
        assert official[flag] is False
    assert official['critical_attenuation_db'] is None
    assert sha(ROOT / official['configuration']) == official['configuration_sha256']
    assert '4551' in (OUT / 'official_055_native_probe.log').read_text()
    s = load('statistics.json')
    blocked, affected = int((b == 1).sum()), int((a > 0).sum())
    assert blocked == s['diagnostic_blocked_cell_slots'] == 596876
    assert affected == s['cloud_affected_cell_slots'] == 601800
    assert s['diagnostic_blocked_fraction'] == blocked / a.size
    assert s['diagnostic_cloud_induced_fraction_given_assumed_clear'] == blocked / a.size
    assert s['diagnostic_blocked_fraction_given_cloud_affected'] == blocked / affected
    assert s['source_mean_attenuation_db'] == float(a.mean())
    assert s['source_maximum_attenuation_db'] == float(a.max())
    assert s['source_minimum_physical_transmittance'] == float(t.min())
    assert all(s[k] is None for k in ('official_blocked_fraction', 'official_secure_availability_fraction', 'official_cloud_induced_fraction_given_clear'))
    assert load('metadata.json')['statistics'] == s
    rows = list(csv.DictReader((OUT / 'frame_blockage_statistics.csv').open(newline='')))
    assert len(rows) == 2000
    for k in range(1000):
        row, pending = rows[k], rows[k + 1000]
        n, c = int((b[k] == 1).sum()), int((a[k] > 0).sum())
        assert row['mode'] == 'diagnostic_0p1db' and pending['mode'] == 'official_055_pending'
        assert int(row['slot']) == int(pending['slot']) == k
        assert float(row['time_s']) == float(pending['time_s']) == k
        assert int(row['blocked_cells']) == int(row['cloud_induced_blocked_cells']) == n
        assert int(row['cloud_affected_clear_cells']) == c
        assert float(row['blockage_ratio']) == float(row['cloud_induced_ratio_given_clear']) == n / 2500
        assert float(row['blocked_ratio_given_cloud_affected_clear']) == n / c
        assert int(pending['unresolved_cells']) == 2500 and int(pending['available_cells']) == 0
        assert pending['blockage_ratio'] == pending['cloud_induced_ratio_given_clear'] == ''
    receipt = load('render_receipt.json')
    assert sha(ROOT / 'scripts/plot_ibrahim_binary_qkd.py') == receipt['plotter_sha256']
    audit = load('export_audit.json')
    assert audit['GIF_frames_pixel_checked'] == 1000
    assert len(audit['PDF_checks']) == 6
    assert all(x['raster_images'] == 0 and all(x['embedded_fonts']) for x in audit['PDF_checks'])
    assert load('visual_review.json')['status'] == 'CURRENTLY_VERIFIED_PASS'
    colors = np.array(receipt['state_RGB_colors'], dtype=np.uint8)
    with Image.open(OUT / 'figure_G_binary_qkd_1000_frames.gif') as gif:
        assert gif.n_frames == 1000
        for k in range(1000):
            gif.seek(k)
            rgb = np.array(gif.convert('RGB'))
            expected = colors[np.repeat(np.repeat(np.flipud(b[k]), 4, axis=0), 4, axis=1)]
            assert np.array_equal(rgb[45:245, 10:210], expected) and gif.info['duration'] == 50
            assert np.all(rgb[45:245, 230:430] == colors[2])
    test = load('test_scope.json')
    assert test['returncode'] == 0 and test['expected_total'] == 67 and test['full_repository_suite'] == 'NOT_RUN'
    assert 'Ran 67 tests' in (OUT / 'tests.log').read_text() and '\nOK' in (OUT / 'tests.log').read_text()
    assert load('worktree_checks.json')['git_diff_check_returncode'] == 0
    inventory = load('git_change_inventory.json')
    assert all((ROOT / name).is_file() for name in inventory['task_new_files'])
    assert all((ROOT / name).is_file() for name in inventory['task_modified_ledger_files'])
    return dict(status='CURRENTLY_VERIFIED_PASS', artifacts_checked=len(manifest),
                old_files_unchanged=len(protected), original_Gaussian_frames_reused=1000,
                cell_slots_checked=int(a.size), GIF_frames_pixel_checked=1000,
                scoped_tests=67, full_repository_suite='NOT_RUN',
                official_threshold_validated=False, diagnostic_threshold_db=.1)


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2))
