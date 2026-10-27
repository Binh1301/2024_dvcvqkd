"""PDF/PNG QA using the existing bundled PDFium runtime; no scientific imports."""
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path.home() / '.codex/tools/manuscript-pdf-20261020'))
from PIL import Image
from pypdf import PdfReader
import pypdfium2 as pdfium

OUT = Path(__file__).resolve().parent
STEM = 'skr_vs_zenith_log10_positive'
pdf = OUT / (STEM + '.pdf'); png = OUT / (STEM + '.png')
reader = PdfReader(pdf); assert len(reader.pages) == 1
page = reader.pages[0]; resources = page['/Resources']; fonts = []
for item in resources['/Font'].values():
    font = item.get_object()
    for descendant in font.get('/DescendantFonts', [font]):
        descendant = descendant.get_object(); descriptor = descendant['/FontDescriptor'].get_object()
        assert any(name in descriptor for name in ['/FontFile','/FontFile2','/FontFile3'])
        fonts.append(str(descendant['/BaseFont']))
images = [item for item in resources.get('/XObject', {}).values()
          if item.get_object().get('/Subtype') == '/Image']
assert not images
text = page.extract_text()
assert 'Zenith angle' in text and 'bits/use' in text and 'no positive samples' in text
with Image.open(png) as picture:
    dimensions = list(picture.size); dpi = list(picture.info['dpi']); assert abs(dpi[0]-600) < 1
document = pdfium.PdfDocument(pdf)
render = document[0].render(scale=3.2).to_pil(); render.save(OUT / 'qa_render.png')
result = dict(status='EXPORT_PASS_AWAITING_VISUAL_REVIEW', result_scope='DIAGNOSTIC_ONLY',
              pages=1, all_fonts_embedded=True, fonts=fonts, raster_image_XObjects=0,
              png_dimensions=dimensions, png_dpi=dpi, PDF_native_text=text,
              rendered_preview='qa_render.png',
              pdf_sha256=hashlib.sha256(pdf.read_bytes()).hexdigest(),
              png_sha256=hashlib.sha256(png.read_bytes()).hexdigest())
(OUT / 'export_validation.json').write_bytes((json.dumps(result,indent=2,ensure_ascii=False)+'\n').encode('utf-8'))
print(json.dumps({k:result[k] for k in ['status','pages','all_fonts_embedded','raster_image_XObjects','png_dimensions']}))
