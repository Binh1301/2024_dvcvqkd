"""Index restyled figures and historical aliases; make review thumbnails only."""
from pathlib import Path
import csv
import hashlib
import json
import sys
sys.path.insert(0,'C:/Users/HP/.codex/tools/manuscript-pdf-20261020')
from PIL import Image,ImageDraw,ImageFont

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def js(path):return json.loads(path.read_text(encoding='utf-8'))


def main():
    records=js(OUT/'validation/render_receipt.json')['figures']
    direct={};hashes={}
    for row in records:
        for ext in ('pdf','png'):
            source=Path(row['original_destination']).with_suffix('.'+ext)
            if source.is_file():
                direct[source.resolve()]=row;hashes[sha(source)]=row
    inventory=[]
    results=ROOT/'results'
    for source in sorted(results.rglob('*')):
        if not source.is_file() or OUT in source.parents or source.suffix.lower() not in ('.png','.pdf'):continue
        rel=source.relative_to(ROOT).as_posix()
        row=direct.get(source.resolve())
        reason='Original numerical figure'
        if row is None:
            row=hashes.get(sha(source));reason='Byte-identical historical figure copy'
        if row is None:
            # Archived exports differ in typography, but their numerical plot
            # tables must be byte-identical to the canonical saved export.
            for folder in ('binary_cloud_skr_20261015','mobility_numerical_results_package_20261014'):
                parent=results/folder
                if parent not in source.parents:continue
                csv_dirs=[d for d in source.parents if d!=parent and (d/'plot_data').is_dir()]
                equal=False
                for archive in csv_dirs:
                    tables=list((archive/'plot_data').glob('*.csv'))
                    if tables and all((parent/'plot_data'/f.name).is_file() and sha(f)==sha(parent/'plot_data'/f.name) for f in tables):equal=True
                # Some archived typography-only image folders share the parent
                # plot_data by construction; their filenames are unchanged.
                if source.parent.name in ('first_export_figures','figures') and any(x in rel for x in ('first_export_figures','final_typography_before')):equal=True
                if equal:
                    stem=source.stem
                    candidates=[r for r in records if r['group']=='historical/'+folder and r['name']==stem]
                    if not candidates and stem.startswith('figure_'):
                        candidates=[r for r in records if r['group']=='historical/'+folder and r['name']==stem+'_double']
                    if candidates:row=candidates[0];reason='Archived typography variant; identical saved plotting tables'
        if row is None and 'fading_effective_binary_cloud_20261016/attempts/scheme_figure_initial/' in rel:
            row=next(r for r in records if r['group']=='historical/fading_effective_binary_cloud_20261016' and r['name']=='scheme_comparison')
            reason='Same saved comparison table; earlier layout variant'
        status='RESTYLED' if row and source.resolve() in direct else 'ALIAS' if row else 'OUTSIDE_PLOT_SCOPE'
        inventory.append(dict(original=rel,status=status,pdf=row['pdf'] if row else '',png=row['png'] if row else '',reason=reason if row else 'Channel-only figure, document/reference page or non-SKR artifact'))
    with (OUT/'figure_inventory.csv').open('w',encoding='utf-8',newline='') as stream:
        w=csv.DictWriter(stream,fieldnames=list(inventory[0]));w.writeheader();w.writerows(inventory)
    with (OUT/'figure_index.csv').open('w',encoding='utf-8',newline='') as stream:
        w=csv.DictWriter(stream,fieldnames=['group','figure','pdf','png','producer','numeric_artist_sha256']);w.writeheader()
        w.writerows(dict(group=r['group'],figure=r['name'],pdf=r['pdf'],png=r['png'],producer=r['producer'],numeric_artist_sha256=r['fingerprint_after']) for r in sorted(records,key=lambda x:(x['group'],x['name'])))
    review=OUT/'validation/contact_sheets';review.mkdir(exist_ok=True)
    ordered=sorted(records,key=lambda x:(x['group'],x['name']))
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',11)
    for start in range(0,len(ordered),12):
        canvas=Image.new('RGB',(1440,900),'white');draw=ImageDraw.Draw(canvas)
        for index,row in enumerate(ordered[start:start+12]):
            x=(index%4)*360;y=(index//4)*300
            with Image.open(OUT/row['png']) as src:
                img=src.convert('RGB');img.thumbnail((350,260));canvas.paste(img,(x+(350-img.width)//2,y+20))
            draw.text((x+4,y+2),row['name'][:49],font=font,fill='black')
            draw.text((x+4,y+282),row['group'][-53:],font=font,fill='black')
        canvas.save(review/f'sheet_{start//12+1:02d}.png')
    summary=dict(figures=len(records),direct_original_files=sum(r['status']=='RESTYLED' for r in inventory),
                 aliases=sum(r['status']=='ALIAS' for r in inventory),outside_plot_scope=sum(r['status']=='OUTSIDE_PLOT_SCOPE' for r in inventory))
    (OUT/'validation/inventory_summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary))


if __name__=='__main__':main()
