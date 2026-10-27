"""Cache source-independent geometry and existing-source curves while AP jobs run."""
import complete_search as c
s=c.s


def main():
    if (s.OUT/'precompute_receipt.json').exists():raise FileExistsError('Preserve completed phase')
    search=s.Search(s.bank())
    row=s.read(s.OUT/'screen_receipt.json')['secondary_best'];gd=s.geometry(row)
    for angle in range(31):
        c.compare(search,(*gd[:4],float(angle)),s.BOUNDED,'PRECOMPUTE_SECONDARY')
        if angle%5==0:print('PRECOMPUTE',angle,'/30',flush=True)
    for diameter in [.3,.35,.4,.45,.5,.55,.6]:
        for law in [s.RAW,s.BOUNDED]:
            search.optimize((diameter,*gd[1:]),'PRECOMPUTE_DIAMETER',law)
    for g in [(.3,35.,1.561,.1,0.),gd,(.3,35.,gd[2],gd[3],0.),
              (.3,gd[1],1.561,gd[3],0.),(.3,gd[1],gd[2],.1,0.)]:
        for law in [s.RAW,s.BOUNDED]:search.optimize(g,'PRECOMPUTE_ABLATION',law)
    s.save(s.OUT/'precompute_receipt.json',dict(status='CURRENTLY_VERIFIED_PASS',
        source_count=len(search.sources),source_jobs_pending=True,contexts=len(search.contexts),
        producer_sha256=s.a.sha(__file__),note='Final selection waits for bounded fresh-source attempts'))
    print('PRECOMPUTE COMPLETE',flush=True)


if __name__=='__main__':main()
