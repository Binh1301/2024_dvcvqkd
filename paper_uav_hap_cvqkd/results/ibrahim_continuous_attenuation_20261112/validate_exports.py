"""Export QA: --render with project Python; --inspect with pypdf Python."""
from pathlib import Path
import argparse
import hashlib
import json

OUT=Path(__file__).resolve().parent


def render():
    import pypdfium2 as pdf
    from PIL import Image
    qa=OUT/'qa';qa.mkdir(exist_ok=True)
    comparisons=[]
    for path in sorted(OUT.glob('figure_*.pdf')):
        document=pdf.PdfDocument(path);assert len(document)==1
        preview=qa/(path.stem+'_preview.png')
        image=document[0].render(scale=1.4).to_pil().convert('RGB')
        same=None
        if preview.exists():
            with Image.open(preview) as previous:
                same=(previous.convert('RGB').size==image.size and previous.convert('RGB').tobytes()==image.tobytes())
        image.save(preview)
        comparisons.append({'file':path.name,'preview':preview.name,'pixels_unchanged_since_previous_inspection':same})
    with Image.open(OUT/'cloud_continuous_attenuation.gif') as animation:
        assert animation.n_frames==1000
        for k in [0,400,999]:
            animation.seek(k);animation.convert('RGB').save(qa/f'gif_frame_{k:03}.png')
    (OUT/'render_diff_validation.json').write_text(json.dumps(comparisons,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(comparisons,indent=2))


def inspect():
    from pypdf import PdfReader
    files=[]
    for path in sorted(OUT.glob('figure_*.pdf')):
        reader=PdfReader(path);assert len(reader.pages)==1
        fonts=[]
        for _,ref in reader.pages[0]['/Resources']['/Font'].items():
            font=ref.get_object()
            target=font['/DescendantFonts'][0].get_object() if '/DescendantFonts' in font else font
            descriptor=target.get('/FontDescriptor');descriptor=descriptor.get_object() if descriptor else {}
            embedded=any(name in descriptor for name in ['/FontFile','/FontFile2','/FontFile3'])
            assert embedded and font['/Subtype']!='/Type3'
            fonts.append({'name':str(font['/BaseFont']),'subtype':str(font['/Subtype']),'embedded':embedded})
        images=len(reader.pages[0].images)
        if path.name.startswith(('figure_E','figure_F','figure_G')):assert images==0
        text=reader.pages[0].extract_text();assert len(text)>100
        files.append({'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                      'pages':1,'fonts':fonts,'raster_images':images,'native_text_characters':len(text)})
    assert len(files)==7
    (OUT/'pdf_export_validation.json').write_text(json.dumps({'status':'CURRENTLY_VERIFIED_PASS','files':files},indent=2)+'\n',encoding='utf-8')
    print('Seven embedded-font PDF exports PASS; E/F/G pure vector')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    group=p.add_mutually_exclusive_group(required=True)
    group.add_argument('--render',action='store_true');group.add_argument('--inspect',action='store_true')
    if p.parse_args().render:render()
    else:inspect()
