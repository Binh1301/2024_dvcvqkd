"""Include cached Stage-A points when completing physical/source coordinates."""
import run_study as s


def main():
    if (s.OUT/'source_coverage.json').exists():raise FileExistsError('Preserve completed coverage')
    s.initialize();old=s.read(s.OUT/'optimization.json')
    s.save('optimization_phase1.json',old)
    contexts={tuple(v['parameters']):v for v in old['contexts']};coverage=[]
    for diameter in [x['D_r'] for x in old['history']]:
        for index,(eta,noise) in enumerate(s.CORNERS):
            physical=[r for r in s.ROWS if r['D_r']==diameter and r['ensemble_hash']==s.fixed()['ensemble_hash']
                and r['radial_order']==128 and r['width_order']==16 and r['divergence_urad'] in s.DIV
                and r['zenith_deg'] in s.ANGLES and (r['jitter_urad'],r['sigma_h_m']) in s.TIERS
                and (r['eta_det'],r['epsilon_det'])==(eta,noise)]
            assert len(physical)==90,(diameter,eta,noise,len(physical))
            original_stage_count=sum(r['stage']=='physical_screen' for r in physical)
            for iteration in range(2):
                before=set(contexts)
                winners={v['best_MB']['ensemble_hash']:s.source(v['best_MB']) for p,v in contexts.items() if p[9]==diameter and p[6:8]==(eta,noise)}
                tested=[s.evaluate(c,s.par(r),'complete_physical_source_coordinate') for c in winners.values() for r in physical]
                for branch,condition in [('moderate',lambda r:r['jitter_urad']>=3),('all',lambda r:True)]:
                    winner=max((r for r in tested if condition(r)),key=lambda r:r['K_raw']);p=s.par(winner)
                    if p not in contexts:contexts[p]=s.catalog(p,f'complete_D{diameter:g}_d{index}_{branch}_{iteration}')
                if set(contexts)==before:break
            coverage.append(dict(D_r=diameter,eta_det=eta,epsilon_det=noise,physical_contexts=90,
                original_stage_label_count=original_stage_count,cached_A_points_included=90-original_stage_count,
                source_hashes_scanned=list(winners),coordinate_iterations=iteration+1))
            s.save('source_coverage_progress.json',coverage)
    s.save('optimization.json',{**old,'contexts':list(contexts.values()),'coverage_extension':'source_coverage.json',
        'phase1_snapshot':'optimization_phase1.json','global_optimum':False})
    s.save('source_coverage.json',dict(status='CURRENTLY_VERIFIED_PASS',coverage=coverage,
        note='Stage labels are provenance, not set membership. Include the two cached Stage-A optical points in each90-node physical branch.',
        model_changed=False,source_moments_changed=False))
    print('SOURCE COVERAGE COMPLETE',len(s.ROWS),'contexts',len(contexts),flush=True)


if __name__=='__main__':main()
