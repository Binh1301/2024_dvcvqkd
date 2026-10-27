"""Read-only verification of the display transform and preserved artifacts."""
import csv
import hashlib
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
read = lambda path: json.loads(Path(path).read_text(encoding='utf-8'))


def verify():
    startup = read(OUT / 'startup_manifest.json')
    for name, digest in startup['protected'].items():
        assert sha(ROOT.parent / name) == digest, name
    result = read(OUT / 'plot_validation.json')
    assert sha(ROOT / result['source_csv']) == result['source_csv_sha256']
    assert sha(OUT / 'plot_log10_positive.py') == result['renderer_sha256']
    assert result['y_scale'] == 'log' and result['log_base'] == 10
    assert result['y_limits'] == [1e-5, 1e-3] and result['x_limits_deg'] == [0, 60]
    assert result['displayed_samples'] == 22 and result['hidden_nonpositive_samples'] == 161
    assert result['negative_source_data_preserved'] and not result['zero_clipping']
    assert not result['interpolation'] and not result['smoothing']
    assert result['new_SKR_Cw_channel_MI_Holevo_evaluations'] == 0
    with (ROOT / result['source_csv']).open(encoding='utf-8', newline='') as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 183 and sum(float(r['K_raw']) > 0 for r in rows) == 22
    assert sum(float(r['K_raw']) < 0 for r in rows) == 161
    for ext, output in result['outputs'].items():
        assert sha(OUT / output['path']) == output['sha256']
    export = read(OUT / 'export_validation.json')
    assert export['visual_review'] == 'PASS' and export['all_fonts_embedded']
    assert export['raster_image_XObjects'] == 0
    assert export['pdf_sha256'] == result['outputs']['pdf']['sha256']
    manifest = read(OUT / 'artifact_manifest.json')
    for name, digest in manifest['artifacts'].items():
        assert sha(OUT / name) == digest, name
    return dict(status='CURRENTLY_VERIFIED_PASS', result_scope='DIAGNOSTIC_ONLY',
                y_scale='log10', displayed_positive_samples=22, hidden_negative_samples=161,
                original_csv_unchanged=True, historical_pdf_unchanged=True,
                protected_historical_files=len(startup['protected']),
                new_scientific_evaluations=0, visual_review='PASS')


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2))
