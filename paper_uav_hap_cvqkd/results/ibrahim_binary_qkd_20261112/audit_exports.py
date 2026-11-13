"""Inspect saved exports; render PDF pages for human visual review."""
from pathlib import Path
import json
import subprocess
import numpy as np
import pypdfium2 as pdfium
from PIL import Image

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
receipt = json.loads((OUT / 'render_receipt.json').read_text())
qa = OUT / 'visual_qa'
qa.mkdir(exist_ok=True)
pdf_checks = []
for name in receipt['figures']:
    path = OUT / (name + '.pdf')
    # Default Python owns pypdf; project Python owns the renderer and NumPy.
    code = """import json,sys
from pypdf import PdfReader
r=PdfReader(sys.argv[1]); p=r.pages[0]
fonts=p['/Resources']['/Font'].get_object()
embedded=[]
for f in fonts.values():
 f=f.get_object()
 if '/DescendantFonts' in f: f=f['/DescendantFonts'][0].get_object()
 d=f.get('/FontDescriptor',{}).get_object()
 embedded.append(any(k in d for k in ['/FontFile','/FontFile2','/FontFile3']))
print(json.dumps(dict(pages=len(r.pages),raster_images=sum(len(p.images) for p in r.pages),embedded_fonts=embedded)))
"""
    result = subprocess.run(['python', '-c', code, str(path)], capture_output=True, text=True, check=True)
    check = json.loads(result.stdout)
    assert check['pages'] == 1 and check['raster_images'] == 0
    assert check['embedded_fonts'] and all(check['embedded_fonts'])
    with Image.open(OUT / (name + '.png')) as png:
        assert all(abs(x - 400) < .1 for x in png.info['dpi'])
        check['PNG_dpi'] = png.info['dpi']
        check['PNG_size'] = png.size
    doc = pdfium.PdfDocument(path)
    doc[0].render(scale=1.5).to_pil().save(qa / (name + '.png'))
    doc.close()
    check['name'] = name
    pdf_checks.append(check)

with np.load(OUT / 'diagnostic_binary_blockage.npz') as data:
    b = data['binary_blockage']
colors = np.array(receipt['state_RGB_colors'], dtype=np.uint8)
with Image.open(OUT / 'figure_G_binary_qkd_1000_frames.gif') as gif:
    assert gif.n_frames == 1000
    for k in range(1000):
        gif.seek(k)
        assert gif.info['duration'] == 50
        rgb = np.array(gif.convert('RGB'))
        expected = colors[np.repeat(np.repeat(np.flipud(b[k]), 4, axis=0), 4, axis=1)]
        assert np.array_equal(rgb[45:245, 10:210], expected), k
        assert np.all(rgb[45:245, 230:430] == colors[2]), k
        if k in (0, 400, 999):
            gif.convert('RGB').save(qa / f'GIF_frame_{k:03d}.png')

(OUT / 'export_audit.json').write_text(json.dumps({
    'status': 'CURRENTLY_VERIFIED_PASS', 'PDF_checks': pdf_checks,
    'GIF_frames_pixel_checked': 1000, 'GIF_order_orientation_and_official_unknown': 'PASS',
    'visual_review': 'Rendered pages; separate inspection receipt is visual_review.json',
}, indent=2) + '\n')
print('Six PDFs: embedded fonts, zero raster images; PNG400dpi; all 1000 GIF frames match saved arrays')
