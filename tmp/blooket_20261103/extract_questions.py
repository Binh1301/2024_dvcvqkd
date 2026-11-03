from pathlib import Path
import json
import re
import fitz

ROOT = Path(__file__).resolve().parent
SOURCE = Path(r'C:\Users\admin\Downloads\Ôn Nhật chuyên ngành 1 -Midterm (2).pdf')
doc = fitz.open(SOURCE)

def cell_text(page, bbox, japanese=False):
    if bbox is None:
        return ''
    rect = fitz.Rect(bbox)
    spans = []
    for block in page.get_text('dict')['blocks']:
        for line in block.get('lines', []):
            for span in line['spans']:
                box = fitz.Rect(span['bbox'])
                if span['size'] >= 10 and rect.contains(box.tl + (box.br - box.tl) / 2):
                    spans.append((span['origin'][1], span['bbox'][0], span['text']))
    lines = []
    for span in sorted(spans):
        if not lines or span[0] - lines[-1][0][0] > 2:
            lines.append([span])
        else:
            lines[-1].append(span)
    text = ('' if japanese else ' ').join(''.join(x[2] for x in sorted(line, key=lambda x: x[1])).strip() for line in lines)
    return re.sub(r'\s+', ' ', text).strip()

questions = []
current = None
last_part = None
all_rows = []
fallback_keys = {31: 'B', 39: 'D', 43: 'D', 53: 'B', 56: 'C', 58: 'C', 60: 'A'}
for page_number, page in enumerate(doc, 1):
    tables = [t for t in page.find_tables().tables if t.bbox[0] < 60 and t.bbox[2] > 550]
    for table in sorted(tables, key=lambda t: t.bbox[1]):
        for row in table.rows:
            if len(row.cells) != 3:
                raise ValueError((page_number, row.cells))
            label, jp, vi = [cell_text(page, c, japanese=i == 1) for i, c in enumerate(row.cells)]
            all_rows.append({'page': page_number, 'label': label, 'jp': jp, 'vi': vi, 'cells': row.cells})
            if 'Câu' in label:
                current = {'label': label, 'page': page_number, 'jp': jp, 'vi': vi, 'answers': []}
                questions.append(current)
                last_part = current
            elif label in 'ABCD' and len(label) == 1:
                assert current is not None
                label_rect = fitz.Rect(row.cells[0])
                label_bold = any(
                    span['text'].strip() == label and 'Bold' in span['font']
                    and label_rect.contains(fitz.Rect(span['bbox']).tl + (fitz.Rect(span['bbox']).br - fitz.Rect(span['bbox']).tl) / 2)
                    for block in page.get_text('dict')['blocks']
                    for line in block.get('lines', []) for span in line['spans']
                )
                ans = {'label': label, 'jp': jp, 'vi': vi, 'page': page_number, 'bold_label': label_bold}
                current['answers'].append(ans)
                last_part = ans
            elif re.fullmatch(r'\d+\.\d+', label) and current and not re.search(r'\d+\.\d+', current['label']):
                current['label'] += ' ' + label
                current['jp'] += jp
                current['vi'] += ' ' + vi
            elif not label and (jp or vi):
                assert last_part is not None
                last_part['jp'] += jp
                last_part['vi'] += ' ' + vi
            elif label or jp or vi:
                raise ValueError(('Unexpected row', page_number, label, jp, vi))

assert len(questions) == sum(p.get_text().count('Câu') for p in doc) == 62
expected_sections = ['CBDCAC', 'BCCADABCAA', 'ACBBDBADDBDB', 'CCBCDACACBDC', 'DADDADDAADB', 'BBBBCACDADA']
expected_keys = ''.join(expected_sections)
assert len(expected_keys) == 62
for i, q in enumerate(questions, 1):
    assert [a['label'] for a in q['answers']] == list('ABCD'), (i, q)
    assert q['jp'] and q['vi'] and all(a['jp'] for a in q['answers'])
    bold_keys = [a['label'] for a in q['answers'] if a['bold_label']]
    assert len(bold_keys) <= 1
    q['correct'] = bold_keys[0] if bold_keys else fallback_keys[i]
    assert q['correct'] == expected_keys[i - 1], (i, q['correct'], expected_keys[i - 1])
    q['correct_evidence'] = 'bold option label in PDF' if bold_keys else 'Vietnamese explanation in PDF'

(ROOT / 'questions.json').write_text(json.dumps(questions, ensure_ascii=False, indent=2), encoding='utf-8')
(ROOT / 'rows.json').write_text(json.dumps(all_rows, ensure_ascii=False, indent=2), encoding='utf-8')
print('TOTAL', len(questions), 'OPTIONS', sum(len(q['answers']) for q in questions))
print('KEY', ''.join(q['correct'] for q in questions))
