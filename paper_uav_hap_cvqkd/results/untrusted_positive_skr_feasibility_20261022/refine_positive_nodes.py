"""Refine only the GH64 nodes that failed the already saved GH128 comparison."""
from pathlib import Path
import model as m
import run as r
from extend_bright import read_csv

OUT=Path(__file__).resolve().parent


def main():
    prior=r.read(OUT/'positive_MI_verification.json')
    if prior['status']!='FAILED':raise ValueError('Only an incomplete convergence check may be refined')
    sources=m.load_catalog(r.read(m.ROOT/'configs/manuscript_mobility.json'))
    factors={c['ensemble_hash']:m.source_factors(c) for c in sources}
    failed=[x for x in read_csv('positive_MI_node_checks.csv') if x['status']=='FAILED']
    records=[]
    for row in failed:
        x,px=factors[row['ensemble_hash']]
        previous=row['I_AB_GH128'];ladder=[]
        for order in (256,512,1024):
            value=m.mi_gh(px,x.astype(complex),row['t_after_detector'],row['N_post'],order,dimension=1)
            delta=value-previous;ladder.append(dict(order=order,value=value,difference=delta))
            if abs(delta)<2e-13:break
            previous=value
        else:raise AssertionError('Positive-node GH refinement still unresolved at1024')
        chi=.95*row['I_AB_GH128']-row['K_GH128']
        assert .95*value-chi>0
        records.append({**row,'I_AB_refined':value,'refined_order':order,'final_adjacent_difference':delta,'K_refined':.95*value-chi,
                        'status':'CURRENTLY_VERIFIED_PASS','coarse_GH64_status':'FAILED'})
    r.write('positive_MI_refined_nodes.csv',records)
    r.save('positive_MI_GH64_initial_failure.json',prior)
    r.save('positive_MI_verification.json',dict(status='CURRENTLY_VERIFIED_PASS',positive_nodes=prior['positive_nodes'],
        initial_failed_nodes=len(failed),refined_nodes=len(records),failed_nodes=0,tolerance=2e-13,
        maximum_initial_GH64_difference=prior['maximum_difference'],
        maximum_final_adjacent_difference=max(abs(x['final_adjacent_difference']) for x in records),
        maximum_refined_order=max(x['refined_order'] for x in records),
        final_tables_A_B_C_and_recommendations_affected=False,raw_GH64_search_tables_preserved=True,security_valid=False))
    print('REFINED POSITIVE NODES PASS',len(records),flush=True)


if __name__=='__main__':main()
