"""Primary corrected SKR entry: four fixed optical comparisons, no optimization."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def main():
    from scripts.run_manuscript_literal_3moments import verified_candidate
    from scripts.run_theta10_D55_unconstrained_three_scheme import unconstrained_config
    from src.full_fading_channel import OpticalConfig,FullFadingLaw
    from src.full_fading_evaluator import MODEL,evaluate_candidate
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scientific-model',choices=[MODEL],default=MODEL)
    parser.add_argument('--config',type=Path,default=ROOT/'configs/corrected_full_fading.json')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    settings=json.loads(args.config.read_text())
    expected=dict(scientific_model=MODEL,xi_ch=.0186,beta=.95,detector='ideal_heterodyne',
                  R=1.,xi_det=0.,phase_noise='OFF',AO='OFF')
    if any(settings.get(k)!=v for k,v in expected.items()):
        raise ValueError('Unsupported primary scientific configuration')
    if len(settings['baselines'])!=2 or len(settings['optical_modes'])!=2:
        raise ValueError('This entry is restricted to the two fixed baseline comparisons')
    args.output.mkdir(parents=True,exist_ok=False)
    candidate=verified_candidate(ROOT/settings['source_payload'],unconstrained_config())
    if candidate['nu_raw']!=settings['nu_raw'] or candidate['V_A']!=settings['V_A']:
        raise ValueError('Fixed source parameters do not match cache')
    records=[]; flat=[]
    for baseline in settings['baselines']:
        for mode in settings['optical_modes']:
            start=time.monotonic()
            law=FullFadingLaw(OpticalConfig(**baseline,support_policy=settings['support_policy']),mode)
            result=evaluate_candidate(candidate,law,settings)
            result['baseline']=baseline['name']
            result['elapsed_s']=time.monotonic()-start
            path=args.output/(baseline['name']+'_'+mode+'.json')
            path.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
            records.append(result)
            e,s=result['effective'],result['security']
            for method in ('gaussian_effective','actual_fading_mixture'):
                flat.append(dict(baseline=baseline['name'],optical_mode=mode,
                    **{k:e[k] for k in ('mean_eta','mean_sqrt_eta','eta_f','variance_sqrt_eta','N_eff','xi_eff','a','b')},
                    C=result['C'],w=result['w'],nu_raw=result['nu_raw'],VA=result['VA'],
                    **{k:s[k] for k in ('Z_minus','Z_plus','Z_worst','lambda_1','lambda_2','lambda_3')},
                    **result[method]))
            print(f"{baseline['name']} {mode}: Gaussian K={result['gaussian_effective']['K_raw']:.12g}; mixture K={result['actual_fading_mixture']['K_raw']:.12g}; mixture delta={result['mixture_last_difference']:.3g}",flush=True)
    with (args.output/'decomposition.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(flat[0]));writer.writeheader();writer.writerows(flat)
    files=['src/full_fading_channel.py','src/full_fading_evaluator.py','scripts/run_full_fading_model.py',
           'scripts/verify_full_fading_model.py','tests/test_full_fading_pipeline.py',
           'scripts/run_manuscript_corrected_3moments.py','src/manuscript_corrected_3moments.py',
           'src/manuscript_literal_3moments.py','src/cvqkd/mutual_information.py',
           'scripts/exact_cache_provenance.py','src/cvqkd/gram_moments.py',
           'src/cvqkd/spectral_frechet.py','scripts/full_support_c4_worker.py',
           'src/modulation/qam256.py','src/modulation/joint_ps_gs.py','src/modulation/normalization.py']
    receipt=dict(scientific_model=MODEL,settings=settings,
        config_sha256=hashlib.sha256(args.config.read_bytes()).hexdigest(),
        producer_hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files},
        outputs={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in args.output.iterdir() if p.is_file()},
        numerical_convergence_pass=all(r['mixture_convergence_pass'] for r in records),
        reference_status=settings['reference_status'],
        publication_readiness='NOT_READY_FOR_PUBLICATION_SCALE_RUNS',
        optimization_run=False,new_source_moments_built=False)
    (args.output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return 0 if receipt['numerical_convergence_pass'] else 2


if __name__=='__main__': raise SystemExit(main())
