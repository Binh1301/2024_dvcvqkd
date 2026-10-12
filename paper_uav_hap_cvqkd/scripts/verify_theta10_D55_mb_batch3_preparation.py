"""Read-only final artifact verifier; add missing-point proximity metadata, never AP."""
import json
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import prepare_theta10_D55_mb_batch3 as prep


def main():
    out, io = prep.OUT, prep.io
    report = prep.read_json(out / 'batch_3_preparation_report.json')
    protected = prep.read_json(out / 'protected_input_manifest.json')
    for name, expected in protected.items():
        assert io.digest(ROOT / name) == expected, name
    required = ('catalog_145_verification.csv', 'exact_va_slice_22km.csv', 'exact_nu_slice_22km.csv',
                'reference_distance_comparison.csv', 'numerical_accuracy_audit.md', 'missing_source_ranking.csv',
                'batch_3_selected_probes.csv', 'batch_1_batch_2_comparison.csv', 'batch_3_preparation_report.md',
                'batch_3_preparation_report.json')
    assert all((out / name).is_file() for name in required)
    with patch.object(prep.ao.ExactMBEvaluator, 'source_moments', prep.forbidden), \
         patch.object(prep.gram_moments, '_fallback', prep.forbidden), \
         patch.object(prep.ao, 'evaluate_candidate', prep.forbidden), \
         patch.object(prep.sweep, 'make_channel', prep.forbidden):
        sources = io.read_csv(out / 'source_145_provenance.csv')
        matrix = io.read_csv(out / 'catalog_145_exact_objectives.csv')
        maximum = io.read_csv(out / 'catalog_145_verification.csv')
        by_distance = {float(r['L_km']): r for r in maximum}
        assert len(sources) == 145 and len(matrix) == 3770 and len(maximum) == 26
        pairs = {prep.pair(r['nu_raw'], r['V_A']) for r in sources}
        assert len(pairs) == 145 and len({r['source_cache_key'] for r in sources}) == 145
        for r in sources:
            assert io.digest(ROOT / r['source_path']) == r['source_file_sha256']
            assert prep.pair(r['nu_raw'], r['V_A']) == (r['nu_raw_hex'], r['V_A_hex'])
        for distance, cert in by_distance.items():
            ranked = sorted((r for r in matrix if float(r['L_km']) == distance),
                            key=lambda r: float(r['SKR']), reverse=True)
            assert len(ranked) == 145 and {prep.pair(r['nu_raw'], r['V_A']) for r in ranked} == pairs
            assert float(cert['best_K']) == float(ranked[0]['SKR'])
            assert float(cert['runner_up_K']) == float(ranked[1]['SKR'])
            assert float(cert['gap']) == float(ranked[0]['SKR']) - float(ranked[1]['SKR'])
            assert cert['AO_matches_catalog_maximum'] == 'True'
        ranking = io.read_csv(out / 'missing_source_ranking.csv')
        selected = io.read_csv(out / 'batch_3_selected_probes.csv')
        assert len(ranking) == len({prep.pair(r['nu_raw'], r['V_A']) for r in ranking}) == 54
        assert tuple((float(r['nu_raw']), float(r['V_A'])) for r in selected) == prep.PRIORITY
        for r in ranking:
            assert prep.pair(r['nu_raw'], r['V_A']) not in pairs
            assert prep.pair(r['nu_raw'], r['V_A']) == (r['nu_raw_hex'], r['V_A_hex'])
            # Distance to each actual selected optimum, no objective approximation or predicted gain.
            proximity = []
            for distance in json.loads(r['affected_distances']):
                best = by_distance[distance]
                proximity.append({'L_km': distance, 'selected_nu': float(best['best_nu']),
                    'selected_V_A': float(best['best_V_A']),
                    'delta_nu': float(r['nu_raw']) - float(best['best_nu']),
                    'delta_V_A': float(r['V_A']) - float(best['best_V_A']),
                    'same_nu_slice': float(r['nu_raw']).hex() == float(best['best_nu']).hex(),
                    'same_V_A_slice': float(r['V_A']).hex() == float(best['best_V_A']).hex()})
            r['proximity_to_selected_exact_optima'] = json.dumps(proximity)
            r['proximity_note'] = 'Exact parameter differences only; no inferred SKR or arbitrary near-optimum cutoff'
        io.write_csv(out / 'missing_source_ranking.csv', ranking)
        selected = [next(r for r in ranking if prep.pair(r['nu_raw'], r['V_A']) == prep.pair(nu, va))
                    for nu, va in prep.PRIORITY]
        io.write_csv(out / 'batch_3_selected_probes.csv', selected)
        assert report['AP_probes_started'] == report['new_AP_sources'] == 0
        assert report['reproduced_bit_exact'] and report['unchanged_evaluator_repeats'] == 24
        assert report['numerical_accuracy_classification'] == 'ORDERING_REPRODUCED_BUT_ERROR_UNBOUNDED'
        # Check actual sign reversal, not only that the winners' parameters differ.
        comparison = io.read_csv(out / 'reference_distance_comparison.csv')
        a = next(r for r in comparison if float(r['V_A']) == 5.475)
        b = next(r for r in comparison if float(r['V_A']) == 5.5)
        assert float(a['K_22km']) > float(b['K_22km'])
        assert float(a['K_reference']) < float(b['K_reference'])
        report.update(selected_probes=selected, final_verifier_sha256=io.digest(__file__),
                      pairwise_K_5p475_minus_5p5_22km=float(a['K_22km'])-float(b['K_22km']),
                      pairwise_K_5p475_minus_5p5_reference=float(a['K_reference'])-float(b['K_reference']))
        io.save_json(out / 'batch_3_preparation_report.json', report)
        for name, expected in protected.items():
            assert io.digest(ROOT / name) == expected, name
        verified = {'status': 'CURRENTLY_VERIFIED_PASS', 'AP_started': 0,
            'scientific_computation_in_final_verifier': False, 'verified_objectives': len(matrix),
            'compatible_MB_sources': len(sources), 'missing_pairs': len(ranking), 'selected_probes': len(selected),
            'protected_files_unchanged': len(protected), 'required_paths_present': required,
            'final_verifier_sha256': io.digest(__file__),
            'output_artifact_sha256': io.raw_snapshot(p for p in out.iterdir() if p.is_file()
                                                    and p.name != 'final_preparation_verification.json')}
        io.save_json(out / 'final_preparation_verification.json', verified)
        print(json.dumps({k: v for k, v in verified.items() if k != 'output_artifact_sha256'}, indent=2))


if __name__ == '__main__':
    main()
