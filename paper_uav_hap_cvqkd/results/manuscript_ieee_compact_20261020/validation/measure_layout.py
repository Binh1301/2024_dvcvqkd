"""Measure rendered PDF coordinates and union of occupied column bands."""
from pathlib import Path
import hashlib
import json
import re
import sys
sys.path.insert(0, 'C:/Users/HP/.codex/tools/manuscript-pdf-20261020')
import pypdfium2 as pdfium

OUT = Path(__file__).resolve().parents[1]
log = (OUT / 'main.log').read_text(encoding='utf-8')
layout = re.search(r'COMPACT_LAYOUT(.*?)\(system_model\)', log, re.S).group(1).replace('\n','')
names = ('textheight', 'columnwidth', 'textwidth', 'topmargin', 'headheight', 'headsep', 'voffset')
values = {name: float(re.search(name+r'=([-\d.]+)pt',layout).group(1)) for name in names}
PT = 72 / 72.27
height = values['textheight'] * PT
top = (72.27 + values['topmargin'] + values['headheight'] + values['headsep'] + values['voffset']) * PT
bottom = top + height
doc = pdfium.PdfDocument(str(OUT / 'main.pdf'))
pages = [doc[i] for i in range(len(doc))]
texts = [page.get_textpage() for page in pages]


def locate(phrase):
    found = []
    for i, text in enumerate(texts):
        search = text.search(phrase, match_case=False)
        while True:
            result = search.get_next()
            if result is None:
                break
            start, count = result
            boxes = [text.get_charbox(j) for j in range(start, start+count)
                     if text.get_text_range(j,1).strip()]
            found.append(dict(page=i+1, column=1 if min(b[0] for b in boxes)<290 else 2,
                              x_left=min(b[0] for b in boxes),
                              y_top=pages[i].get_height()-max(b[3] for b in boxes),
                              y_bottom=pages[i].get_height()-min(b[1] for b in boxes),
                              char_index=start,char_count=count))
    return found


starts = locate('II. OPTIMIZATION PROBLEM')
ends = locate('secure keys.')
headings = locate('V. CONCLUSION')
assert len(starts)==len(ends)==len(headings)==1
start, end = starts[0], ends[0]
bands = {}
first = (start['page']-1)*2+start['column']-1
last = (end['page']-1)*2+end['column']-1
for k in range(first,last+1):
    page, column = k//2+1,k%2+1
    bands.setdefault((page,column),[]).append((start['y_top'] if k==first else top,
                                              end['y_bottom'] if k==last else bottom,'text flow'))

caption_start = locate('Fig. 1. Parameter sensitivity')[0]
caption_end = locate('whole-mission bootstrap intervals.')[0]
assert caption_start['page']==caption_end['page']
figure_page = caption_start['page']
forms = [obj for obj in pages[figure_page-1].get_objects(max_depth=1)
         if obj.type==5 and obj.get_bounds()[2]-obj.get_bounds()[0] > values['textwidth']*PT*.9]
assert len(forms)==1
box = forms[0].get_bounds()
form_top = pages[figure_page-1].get_height()-box[3]
form_bottom = pages[figure_page-1].get_height()-box[1]
for column in (1,2):
    bands.setdefault((figure_page,column),[]).append((form_top,caption_end['y_bottom'],'full-width figure and caption'))

merged=[]
for (page,column),intervals in sorted(bands.items()):
    intervals = sorted(intervals)
    union=[]
    for lo,hi,_ in intervals:
        assert top-5 <= lo < hi <= bottom+5
        if union and lo<=union[-1][1]: union[-1][1]=max(union[-1][1],hi)
        else: union.append([lo,hi])
    merged.append(dict(page=page,column=column,bands_top_origin_pdf_pt=union,
                       occupied_height_pdf_pt=sum(hi-lo for lo,hi in union)))
total = sum(row['occupied_height_pdf_pt'] for row in merged)
result=dict(pdf_sha256=hashlib.sha256((OUT/'main.pdf').read_bytes()).hexdigest(),
            method='Union of rendered reading-flow column bands plus full vector-figure/caption bands; no double counting',
            coordinate_units='PDF points from page top, 72 per inch',body_top_pdf_pt=top,
            body_bottom_pdf_pt=bottom,column_height_pdf_pt=height,
            column_width_pdf_pt=values['columnwidth']*PT,start=start,
            conclusion_heading=headings[0],end=end,figure_page=figure_page,
            figure_form_top_pdf_pt=form_top,figure_form_bottom_pdf_pt=form_bottom,
            figure_caption_bottom_pdf_pt=caption_end['y_bottom'],
            figure_nominal_font_pt=8.5,figure_minimum_rendered_font_pt=8.5*forms[0].get_matrix().a,
            figure_extends_outside_heading_to_end_column_flow=(figure_page,end['column'])==(end['page'],1),
            column_bands=merged,occupied_equivalent_columns=total/height,
            occupied_equivalent_pages=total/(2*height),
            reading_flow_span_pages=((last-first)*height+end['y_bottom']-start['y_top'])/(2*height),
            bibliography_excluded='Bibliography follows Conclusion; citations inside prose are included.')
(OUT/'validation/layout_measurement.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
