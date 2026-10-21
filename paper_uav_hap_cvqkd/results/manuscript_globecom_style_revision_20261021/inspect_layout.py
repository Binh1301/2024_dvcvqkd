"""Render all pages and measure occupied IEEE column bands, including floats."""
import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0,'C:/Users/HP/.codex/tools/manuscript-pdf-20261020')
import pypdfium2 as pdfium
from pypdf import PdfReader

OUT=Path(__file__).resolve().parent


def main():
    if (OUT/'validation/final_receipt.json').exists():raise FileExistsError('Sealed inspection is immutable')
    log=(OUT/'main.log').read_text(encoding='utf-8')
    match=re.search(r'GLOBECOM_LAYOUT(.*?)\[',log,re.S)
    layout=match.group(1).replace('\n','')
    names=['textheight','columnwidth','textwidth','topmargin','headheight','headsep','voffset']
    values={n:float(re.search(n+r'=([-\d.]+)pt',layout).group(1)) for n in names}
    pt=72/72.27
    height=values['textheight']*pt
    top=(72.27+values['topmargin']+values['headheight']+values['headsep']+values['voffset'])*pt
    bottom=top+height
    document=pdfium.PdfDocument(str(OUT/'main.pdf'))
    pages=[document[i] for i in range(len(document))]
    texts=[page.get_textpage() for page in pages]
    def locate(phrase):
        found=[]
        for i,text in enumerate(texts):
            search=text.search(phrase,match_case=False)
            while True:
                hit=search.get_next()
                if hit is None:break
                start,count=hit
                boxes=[text.get_charbox(j) for j in range(start,start+count) if text.get_text_range(j,1).strip()]
                found.append(dict(page=i+1,column=1 if min(b[0] for b in boxes)<290 else 2,
                    x_left=min(b[0] for b in boxes),y_top=pages[i].get_height()-max(b[3] for b in boxes),
                    y_bottom=pages[i].get_height()-min(b[1] for b in boxes),char_index=start,char_count=count))
        return found
    starts=locate('JOINT SOURCE AND MOBILITY OPTIMIZATION')
    ends=locate('can represent secure keys.')
    assert len(starts)==len(ends)==1,(starts,ends)
    start,end=starts[0],ends[0]
    first=(start['page']-1)*2+start['column']-1
    last=(end['page']-1)*2+end['column']-1
    bands={}
    for k in range(first,last+1):
        key=(k//2+1,k%2+1)
        bands.setdefault(key,[]).append((start['y_top'] if k==first else top,
            end['y_bottom'] if k==last else bottom,'reading flow'))
    float_info=[]
    for number,end_phrase in [(1,'bootstrap intervals.'),(2,'binary cloud correlation.')]:
        caption=locate(f'Fig. {number}.')
        assert len(caption)==1,caption
        c=caption[0];page=pages[c['page']-1]
        candidates=[v for v in locate(end_phrase) if v['page']==c['page'] and v['char_index']>c['char_index']]
        finish=min(candidates,key=lambda v:v['char_index'])
        forms=[obj for obj in page.get_objects(max_depth=1) if obj.type==5
               and obj.get_bounds()[2]-obj.get_bounds()[0]>values['textwidth']*pt*.9
               and page.get_height()-obj.get_bounds()[1]<=c['y_top']+3]
        assert forms,('missing full-width figure',number)
        form=min(forms,key=lambda obj:c['y_top']-(page.get_height()-obj.get_bounds()[1]))
        box=form.get_bounds();form_top=page.get_height()-box[3];form_bottom=page.get_height()-box[1]
        for col in (1,2):bands.setdefault((c['page'],col),[]).append((form_top,finish['y_bottom'],f'figure {number} and caption'))
        float_info.append(dict(number=number,page=c['page'],top_pdf_pt=form_top,bottom_pdf_pt=form_bottom,
            caption_top=c['y_top'],caption_bottom=finish['y_bottom'],scale=form.get_matrix().a,
            native_minimum_legend_font_pt=6.4,rendered_minimum_legend_font_pt=6.4*form.get_matrix().a))
    merged=[]
    for (pn,col),intervals in sorted(bands.items()):
        union=[]
        for low,high,_ in sorted(intervals):
            assert top-5<=low<high<=bottom+5,(pn,col,low,high,top,bottom)
            if union and low<=union[-1][1]:union[-1][1]=max(union[-1][1],high)
            else:union.append([low,high])
        merged.append(dict(page=pn,column=col,bands_top_origin_pdf_pt=union,
            occupied_height_pdf_pt=sum(b-a for a,b in union)))
    total=sum(x['occupied_height_pdf_pt'] for x in merged)
    pdf_sha=hashlib.sha256((OUT/'main.pdf').read_bytes()).hexdigest()
    result=dict(pdf_sha256=pdf_sha,method='Union of reading-flow column bands plus both full-width vector figure/caption bands; no double counting',
        units='PDF points, top origin,72 per inch',ieee_layout_tex_pt=values,
        body_top_pdf_pt=top,body_bottom_pdf_pt=bottom,column_height_pdf_pt=height,
        start=start,end=end,float_bands=float_info,column_bands=merged,
        occupied_equivalent_columns=total/height,occupied_equivalent_pages=total/(2*height),
        reading_flow_span_pages=((last-first)*height+end['y_bottom']-start['y_top'])/(2*height),
        target_pages=1.5,bibliography_excluded=True,
        note='Parameter table and all equations/captions are inside the counted bands. The body font and IEEE geometry are unchanged.')
    (OUT/'validation/layout_measurement.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    rendered=[]
    for i,page in enumerate(pages):
        name=f'page_{i+1:02d}.png';path=OUT/'validation'/name
        page.render(scale=1.8).to_pil().save(path)
        rendered.append(dict(page=i+1,png=name,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    reader=PdfReader(OUT/'main.pdf')
    text='\n\n'.join(page.extract_text() for page in reader.pages)
    (OUT/'validation/extracted_manuscript.txt').write_text(text,encoding='utf-8',newline='\n')
    (OUT/'validation/pdf_inspection.json').write_text(json.dumps(dict(pdf_sha256=pdf_sha,pages=rendered),indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(pages=len(pages),occupied_equivalent_pages=result['occupied_equivalent_pages'],
        occupied_equivalent_columns=result['occupied_equivalent_columns'],start=start,end=end,floats=float_info),indent=2))


if __name__=='__main__':main()
