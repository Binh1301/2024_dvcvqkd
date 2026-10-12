"""Render saved Phase2A records with numeric CSV axes; no scientific rerun."""
from pathlib import Path
import sys
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts import run_theta10_D55_ao_phase2a as run


def main():
    run.supervisor.verify_protected(run.OUT)
    output=run.OUT/'verified_figures'
    if output.exists():
        raise SystemExit('Verified renderer output exists; do not overwrite')
    checkpoint=run.read(run.OUT/'objective_checkpoint.json')
    runs=run.read(run.OUT/'cache_only_runs.json')
    comparison=[{**r,'L_km':float(r['L_km']),'K':float(r['K'])}
                for r in run.io.read_csv(run.OUT/'three_scheme_comparison.csv')]
    maxima={float(d):max(v['rows'],key=lambda r:float(r['SKR'])) for d,v in checkpoint.items()}
    assert len(maxima)==26 and len(comparison)==78
    output.mkdir()
    with patch.object(run.prep.audit,'OUT',output):
        paths=run.prep.audit.make_plots(runs,maxima,checkpoint,comparison)
    run.io.save_json(output/'renderer_validation.json',{'status':'CURRENTLY_VERIFIED_PASS',
        'source':'SAVED_PHASE2A_RECORDS_ONLY','CSV_numeric_axes':True,'new_AP':False,'new_objectives':False,
        'new_channel':False,'new_AO':False,'figure_paths':paths,
        'exact_comparison_csv_sha256':run.io.digest(run.OUT/'three_scheme_comparison.csv'),
        'renderer_sha256':run.io.digest(__file__),
        'note':'Explicit CSV float decoding prevents categorical axis conversion; original draft figures untouched.'})
    print('VERIFIED_NUMERIC_RENDERER_PASS')


if __name__=='__main__':
    main()
