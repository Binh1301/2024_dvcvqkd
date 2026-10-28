"""Check the exported CSV, PNG, PDF and source provenance without recomputing plots."""
from pathlib import Path
import csv
import hashlib
import json
import math
from PIL import Image
from pypdf import PdfReader

BASE = Path(__file__).resolve().parent


def main():
    report = json.loads((BASE / 'validation.json').read_text(encoding='utf-8'))
    assert report['status'] == 'PASS' and all(row['passed'] for row in report['checks'])
    for path, expected in ((BASE / 'main.py', report['producer_sha256']),
                           (BASE.parent / 'main.py', report['model_source_sha256'])):
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, path
    preservation = json.loads((BASE / 'preservation.json').read_text(encoding='utf-8'))
    assert preservation['status'] == 'PASS'
    for name, digest in preservation['before_sha256'].items():
        assert hashlib.sha256((BASE.parent / name).read_bytes()).hexdigest() == digest, name

    rows, feasible, max_distance_error, max_time_error = 0, 0, 0., 0.
    with (BASE / 'data/emin_grid.csv').open(newline='', encoding='utf-8') as stream:
        for row in csv.DictReader(stream):
            rows += 1
            d, t = float(row['distance_m']), float(row['time_s'])
            valid = row['feasible'] == 'True'
            assert valid == (d <= 30*t)
            if not valid:
                assert row['minimum_energy_J'] == row['constant_energy_J'] == ''
                assert row['strategy'] == 'infeasible'
                continue
            feasible += 1
            energy, constant, saved, percent = [float(row[k]) for k in
                ('minimum_energy_J', 'constant_energy_J', 'savings_J', 'savings_percent')]
            speed, fly, hover = [float(row[k]) for k in ('fly_speed_m_s', 'fly_time_s', 'hover_time_s')]
            assert all(math.isfinite(x) for x in (energy, constant, saved, percent, speed, fly, hover))
            assert 0 <= speed <= 30 and fly >= 0 and hover >= 0
            assert 0 < energy <= constant+1e-7
            assert abs(energy+saved-constant) < 1e-7
            assert abs(percent-100*saved/constant) < 1e-10
            max_distance_error = max(max_distance_error, abs(speed*fly-d))
            max_time_error = max(max_time_error, abs(fly+hover-t))
    assert rows == 491*491 and feasible == report['summary']['feasible_grid_points']
    assert max_distance_error < 1e-8 and max_time_error < 1e-10

    figures = []
    pngs, pdfs = sorted((BASE / 'figures').glob('*.png')), sorted((BASE / 'figures').glob('*.pdf'))
    assert len(pngs) == len(pdfs) == 8
    assert [p.stem for p in pngs] == [p.stem for p in pdfs]
    for png, pdf in zip(pngs, pdfs):
        with Image.open(png) as im:
            size, dpi = im.size, im.info['dpi']
            assert min(size) > 1500 and all(abs(x-320) < 0.02 for x in dpi)
            im.verify()
        reader = PdfReader(pdf)
        assert len(reader.pages) == 1
        page = reader.pages[0]
        assert len(page.images) == 0, f'Raster image found in {pdf.name}'
        text = page.extract_text()
        assert len(text) > 60 and '/Font' in page['/Resources']
        figures.append(dict(stem=png.stem, png_pixels=list(size), png_dpi=list(dpi),
                            pdf_pages=1, pdf_raster_images=0))
    result = dict(status='PASS', numerical_checks=len(report['checks']), grid_rows=rows,
                  feasible_rows=feasible, max_csv_distance_residual_m=max_distance_error,
                  max_csv_time_residual_s=max_time_error, figures=figures,
                  previous_files_unchanged=preservation['files_checked'],
                  scope='CSV round trip, PNG resolution, PDF resources/text, source and old-file hashes.')
    (BASE / 'artifact_checks.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    manifest = {p.relative_to(BASE).as_posix(): dict(bytes=p.stat().st_size,
                sha256=hashlib.sha256(p.read_bytes()).hexdigest())
                for p in sorted(BASE.rglob('*')) if p.is_file() and '.cache' not in p.parts
                and p.name != 'artifact_manifest.json'}
    (BASE / 'artifact_manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(status='PASS', numerical_checks=len(report['checks']),
                         grid_rows=rows, png_files=len(pngs), vector_pdf_files=len(pdfs),
                         old_files_unchanged=preservation['files_checked'],
                         deliverable_files=len(manifest)+1), indent=2))


if __name__ == '__main__':
    main()
