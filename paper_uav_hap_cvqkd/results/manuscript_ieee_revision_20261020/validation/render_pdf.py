"""Render the compiled review PDF; no experimental code is imported."""
from pathlib import Path
import hashlib
import importlib.metadata
import json
import sys

sys.path.insert(0, 'C:/Users/HP/.codex/tools/manuscript-pdf-20261020')
import pypdfium2 as pdfium
from pypdf import PdfReader

out = Path(__file__).resolve().parents[1]
pdf = out / 'main.pdf'
doc = pdfium.PdfDocument(str(pdf))
reader = PdfReader(pdf)
pages = []
all_text = []
for i, page in enumerate(doc):
    target = out / 'validation' / f'page_{i+1:02d}.png'
    bitmap = page.render(scale=150/72)
    im = bitmap.to_pil()
    im.save(target, dpi=(150,150))
    text = reader.pages[i].extract_text()
    all_text.append(f'PAGE {i+1}\n{text}')
    pages.append(dict(page=i+1, width_pt=page.get_width(), height_pt=page.get_height(),
                      png=target.name, pixels=im.size, extracted_characters=len(text),
                      sha256=hashlib.sha256(target.read_bytes()).hexdigest()))
    bitmap.close()
    page.close()
doc.close()
(out / 'validation/manuscript_extracted.txt').write_text('\n\n'.join(all_text),encoding='utf-8')
result = dict(pdf_sha256=hashlib.sha256(pdf.read_bytes()).hexdigest(), pages=pages,
              renderer='pypdfium2', renderer_version=importlib.metadata.version('pypdfium2'),
              pillow_version=importlib.metadata.version('Pillow'), dpi=150)
(out / 'validation/pdf_inspection.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
