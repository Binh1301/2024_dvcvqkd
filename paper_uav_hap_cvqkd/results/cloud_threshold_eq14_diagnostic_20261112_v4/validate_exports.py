"""Run --render with project Python and --fonts with pypdf Python."""
from pathlib import Path
import json
import sys

OUT=Path(__file__).resolve().parent
if sys.argv[1]=='--render':
    import pypdfium2 as pdf
    q=OUT/'qa';q.mkdir(exist_ok=True)
    for p in OUT.glob('figure_*.pdf'):
        d=pdf.PdfDocument(p);assert len(d)==1
        d[0].render(scale=1.4).to_pil().save(q/(p.stem+'.png'))
elif sys.argv[1]=='--fonts':
    from pypdf import PdfReader
    exports=[]
    for p in sorted(OUT.glob('figure_*.pdf')):
        page=PdfReader(p).pages[0];fonts=[]
        for ref in page['/Resources']['/Font'].values():
            f=ref.get_object();d=f['/DescendantFonts'][0].get_object() if '/DescendantFonts' in f else f
            desc=d.get('/FontDescriptor');desc=desc.get_object() if desc else {}
            assert any(k in desc for k in ['/FontFile','/FontFile2','/FontFile3']) and f['/Subtype']!='/Type3'
            fonts.append(str(f['/BaseFont']))
        images=len(page.images)
        if not p.stem.startswith('figure_3'):assert images==0
        exports.append(dict(file=p.name,embedded_fonts=fonts,images=images,native_text_characters=len(page.extract_text())))
    assert len(exports)==3
    (OUT/'pdf_export_validation.json').write_bytes((json.dumps(dict(status='CURRENTLY_VERIFIED_PASS',files=exports),indent=2)+'\n').encode())
else:raise ValueError('Use --render or --fonts')
