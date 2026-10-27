"""Targeted detector/beam probe after the primary StageB catalog is available."""
import csv
import numeric as n
import search as s


def main():
    if (s.OUT/'detector_probe.json').exists():raise FileExistsError('Preserve probe')
    sources=n.previous.load_catalog(s.read(s.ROOT/'configs/manuscript_mobility.json'))
    with (s.OUT/'catalog_B_0.csv').open() as f:best=max(csv.DictReader(f),key=lambda r:float(r['K_raw']))
    c=next(c for c in sources if c['ensemble_hash']==best['ensemble_hash']);rows=[]
    for div in [10.,25.,35.]:
        for noise in [.005,.002,.001,.0005,0.]:
            par=(20.,1.,30.,div,1.,.05,.8,noise,.92)
            r=s.clean(n.evaluate(c,par));rows.append(r);print('PROBE',div,noise,r['K_raw'],flush=True)
    s.save('detector_probe.json',dict(source_hash=c['ensemble_hash'],rows=rows))


if __name__=='__main__':main()
