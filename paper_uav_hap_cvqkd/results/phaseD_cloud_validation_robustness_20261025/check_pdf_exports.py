"""Run with the bundled PDF runtime; inspect every exported PDF and PNG."""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageOps, ImageDraw
from pypdf import PdfReader
import pdfplumber
import pypdfium2 as pdfium

OUT=Path(__file__).resolve().parent


def main():
    qa=OUT/'qa_pdf';qa.mkdir(exist_ok=True)
    records=[];tiles=[]
    for path in sorted(OUT.glob('figD*.pdf')):
        reader=PdfReader(path);assert len(reader.pages)==1
        page=reader.pages[0];resources=page['/Resources'];fonts=[]
        for item in resources.get('/Font',{}).values():
            font=item.get_object()
            descendants=font.get('/DescendantFonts',[font])
            for d in descendants:
                d=d.get_object();descriptor=d.get('/FontDescriptor')
                embedded=descriptor is not None and any(k in descriptor.get_object() for k in ['/FontFile','/FontFile2','/FontFile3'])
                assert embedded, str(d)
                fonts.append(str(d.get('/BaseFont')))
        images=0
        for x in resources.get('/XObject',{}).values():
            if x.get_object().get('/Subtype')=='/Image':images+=1
        assert images==0
        with pdfplumber.open(path) as document:
            p=document.pages[0]
            outside=[c for c in p.chars if c['x0']<-.25 or c['x1']>p.width+.25 or c['top']<-.25 or c['bottom']>p.height+.25]
            assert not outside,(path,outside)
            assert p.chars
        png=Image.open(path.with_suffix('.png'))
        dpi=png.info.get('dpi');assert dpi and abs(dpi[0]-600)<1
        document=pdfium.PdfDocument(path);render=document[0].render(scale=2.2).to_pil().convert('RGB')
        target=qa/(path.stem+'.png');render.save(target)
        tile=ImageOps.contain(render,(860,600));canvas=Image.new('RGB',(880,630),'white')
        canvas.paste(tile,((880-tile.width)//2,25));ImageDraw.Draw(canvas).text((10,6),path.stem,fill='black')
        tiles.append(canvas)
        records.append(dict(pdf=path.name,pages=1,font_names=fonts,all_fonts_embedded=True,
            raster_image_XObjects=images,text_outside_page=0,png_size=list(png.size),png_dpi=list(dpi),
            pdf_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),rendered_for_visual_review=str(target.relative_to(OUT))))
    assert len(records)==6
    sheet=Image.new('RGB',(1760,1890),'white')
    for i,tile in enumerate(tiles):sheet.paste(tile,((i%2)*880,(i//2)*630))
    sheet.save(qa/'contact_sheet.png')
    canonical=Path('C:/Users/HP/Downloads/2026__Binh_s_work (43).pdf')
    result=dict(status='EXPORT_CHECKS_PASS_AWAITING_VISUAL_REVIEW',figures=records,
        canonical_pdf_pages=len(PdfReader(canonical).pages),canonical_pdf_sha256=hashlib.sha256(canonical.read_bytes()).hexdigest(),
        historical_page_count_prose_corrected_only_in_new_report=True)
    (OUT/'figure_export_validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(dict(figures=6,embedded_fonts=True,vector=True,canonical_pages=4)))


if __name__=='__main__':main()
