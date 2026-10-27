"""Read-only manuscript extraction and page rendering; source PDF stays unchanged."""
import hashlib
import json
from pathlib import Path
import fitz

OUT = Path(__file__).resolve().parent
path = OUT/'inputs/manuscript_v43.pdf'
before = hashlib.sha256(path.read_bytes()).hexdigest()
doc = fitz.open(path)
pages = []
for index, page in enumerate(doc):
    text_path = OUT/'inputs'/f'page_{index+1}.txt'
    text_path.write_text(page.get_text(sort=True), encoding='utf-8')
    png = OUT/'inputs'/f'page_{index+1}.png'
    page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False).save(png)
    pages.append(dict(page=index+1, text=text_path.name, png=png.name))
assert len(pages) == 4
assert hashlib.sha256(path.read_bytes()).hexdigest() == before
(OUT/'pdf_capture.json').write_text(json.dumps(dict(status='CURRENTLY_VERIFIED_PASS',
    manuscript_sha256=before, pages=pages, renderer='PyMuPDF1.26.5', source_modified=False),
    indent=2)+'\n', encoding='utf-8')
print('PDF READ-ONLY CAPTURE', len(pages), before)
