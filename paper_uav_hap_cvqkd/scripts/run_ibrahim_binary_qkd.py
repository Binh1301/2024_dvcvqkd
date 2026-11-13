"""Deterministic diagnostic conversion; official 0.55 m results remain separate."""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import subprocess
import sys
import time
import numpy as np
import yaml

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.ibrahim_binary_qkd import classify_attenuation,frame_statistics


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,value):path.write_bytes((json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode())


def official_probe(out,cfg):
    config=ROOT/cfg['official_configuration']
    settings=yaml.safe_load(config.read_text(encoding='utf-8'))
    assert settings['channel']['receiver_diameter_m']==.55
    code='from src.cvqkd.secret_key_rate import fading_secret_key_rate\nfrom src.cvqkd.holevo import _holevo_from_source_moments\nprint("NATIVE_IMPORT_SUCCESS")'
    try:
        p=subprocess.run([sys.executable,'-X','utf8','-B','-c',code],cwd=ROOT,
                         capture_output=True,text=True,encoding='utf-8',timeout=45)
        log=p.stdout+p.stderr;status='BLOCKED_BY_ENVIRONMENT' if p.returncode else 'BLOCKED_BY_SCIENTIFIC_PREREQUISITES'
        returncode=p.returncode
    except subprocess.TimeoutExpired as error:
        log='Native import timeout45s: '+str(error);status='BLOCKED_BY_ENVIRONMENT';returncode=None
    (out/'official_055_native_probe.log').write_bytes(log.encode())
    record=dict(status=status,receiver_diameter_m=.55,configuration=cfg['official_configuration'],
        configuration_sha256=sha(config),configuration_declared_status=settings['status'],settings=settings,
        native_import_returncode=returncode,native_import_succeeded=returncode==0,
        SKR_evaluation_executed=False,threshold_search_executed=False,threshold_validated=False,
        critical_attenuation_db=None,clear_sky_availability='UNRESOLVED',fallback_to_0p1db=False,
        scientific_prerequisites=['Frozen historical-hash discrepancy remains unresolved',
          'Configuration declaration is not a validated position-dependent threshold',
          'Source/security convergence and admissible branch evidence required before operational threshold adoption'],
        interpretation='Import probe only, not a numerical 0.55 m SKR evaluation. Diagnostic workflow continues independently.')
    save(out/'official_055_status.json',record)
    return record


def run(out,config,resume_preexport=False):
    if out.exists() and (not resume_preexport or (out/'metadata.json').exists() or list(out.glob('*.npz'))):
        raise FileExistsError('Fresh output required; resume is allowed only before any binary export')
    started=time.perf_counter();cfg=json.loads(config.read_text(encoding='utf-8'))
    if cfg['diagnostic_threshold_db']!=.1 or cfg['official_fallback_to_diagnostic'] is not False:
        raise ValueError('Only the explicitly illustrative 0.1 dB scenario is authorized by this configuration')
    if resume_preexport:
        assert json.loads((out/'design_receipt.json').read_text())['settings']==cfg
    out.mkdir(parents=True,exist_ok=resume_preexport)
    (out/'startup_git_diff.patch').write_bytes(subprocess.check_output(['git','diff'],cwd=ROOT))
    save(out/'startup.json',dict(branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip(),
        HEAD=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        git_status=subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True)))
    ledger=out/'startup_ledgers';ledger.mkdir(exist_ok=resume_preexport)
    for n in ['docs/PROJECT_STATE.md','docs/EVIDENCE.md','docs/DECISION_LOG.md','docs/NEXT_ACTIONS.md','.agent/SESSION_HANDOFF.md']:
        (ledger/Path(n).name).write_bytes((ROOT/n).read_bytes())
    previous=ROOT/'results/cloud_threshold_eq14_diagnostic_20261112_v4'
    protected=json.loads((previous/'protected_inputs.json').read_text())
    for folder in ROOT.joinpath('results').iterdir():
        if folder.is_dir() and (folder.name.startswith('cloud_threshold_') or folder.name in [
            'ibrahim_cloud_demo_20261111','ibrahim_stationary_cloud_20261111','stochastic_cloud_grf_20261111','ibrahim_continuous_attenuation_20261112']):
            for f in folder.rglob('*'):
                if f.is_file() and '__pycache__' not in f.parts:protected[f.relative_to(ROOT).as_posix()]=sha(f)
    excluded={'src/ibrahim_binary_qkd.py','tests/test_ibrahim_binary_qkd.py','configs/ibrahim_binary_qkd.json',
              'scripts/run_ibrahim_binary_qkd.py','scripts/plot_ibrahim_binary_qkd.py','scripts/report_ibrahim_binary_qkd.py'}
    for directory in ['src','configs','scripts','tests']:
        for f in (ROOT/directory).rglob('*'):
            name=f.relative_to(ROOT).as_posix()
            if f.is_file() and '__pycache__' not in f.parts and name not in excluded:protected[name]=sha(f)
    save(out/'protected_inputs.json',protected)
    producers=[n for n in sorted(excluded) if (ROOT/n).exists()]
    save(out/'design_receipt.json',dict(settings=cfg,config_sha256=sha(config),
        producer_hashes={n:sha(ROOT/n) for n in producers},gaussian_regeneration=False,QKD_source_modification=False,
        authorized_fallback='Independent illustrative diagnostic only; no official threshold fallback',
        frozen_actual_sha256=sha(ROOT/'docs/FINAL_MODEL_SPEC.md'),
        frozen_historical_expected_sha256='561fecc97cdf9967034ffd6865c1605804b624b98f47a091e47f17e520a2a7b1'))
    save(out/'configuration.json',cfg)
    official=json.loads((out/'official_055_status.json').read_text()) if resume_preexport else official_probe(out,cfg)
    continuous=ROOT/cfg['continuous_directory'];manifest=json.loads((continuous/'artifact_hashes.json').read_text())
    source_paths=[ROOT/cfg['gaussian_input'],continuous/'cloud_clwc.npz',continuous/'cloud_attenuation_db.npz',continuous/'cloud_transmittance.npz']
    input_hashes={};structures={};arrays={}
    for path in source_paths:
        expected=(json.loads((path.parent/'artifact_hashes.json').read_text())[path.name])
        assert sha(path)==expected,path
        input_hashes[path.relative_to(ROOT).as_posix()]=sha(path)
        with np.load(path,allow_pickle=False) as d:
            structures[path.name]={k:dict(shape=list(d[k].shape),dtype=str(d[k].dtype)) for k in d.files}
            for name in ['X','clwc_g_m3','attenuation_db','transmittance']:
                if name in d:arrays[name]=d[name]
            coordinates={k:d[k] for k in ['time_s','x_m','y_m']}
            if 'common' not in arrays:arrays['common']=coordinates
            else:
                for key,value in coordinates.items():np.testing.assert_array_equal(value,arrays['common'][key])
    g,l,a,t=(arrays[k] for k in ['X','clwc_g_m3','attenuation_db','transmittance']);common=arrays['common']
    assert all(z.shape==(1000,50,50) and z.dtype==np.float64 and np.isfinite(z).all() for z in [g,l,a,t])
    np.testing.assert_array_equal(common['time_s'],np.arange(1000))
    np.testing.assert_array_equal(common['x_m'],(np.arange(50)+.5)*40)
    np.testing.assert_array_equal(common['y_m'],(np.arange(50)+.5)*40)
    np.testing.assert_allclose(t,10**(-a/10),rtol=1e-15,atol=0)
    old_meta=json.loads((continuous/'metadata.json').read_text())
    primary=old_meta['primary_scenario']
    primary_name=primary['name'] if isinstance(primary,dict) else primary
    reference=next(s for s in old_meta['scenarios'] if s['name']==primary_name)
    assert float(a.mean())==reference['attenuation_db']['mean'] and float(a.max())==reference['attenuation_db']['maximum']
    assert float(t.min())==reference['transmittance']['minimum']
    diagnostic=classify_attenuation(a,.1,1,mode='diagnostic')
    pending=classify_attenuation(a,np.nan,255,mode='validated_input')
    np.savez_compressed(out/'diagnostic_binary_blockage.npz',binary_blockage=diagnostic['binary_blockage'],
        classification_status=diagnostic['classification_status'],clear_sky_available=diagnostic['clear_sky_available'],
        resolved_mask=diagnostic['resolved_mask'],**common,axis_order=np.array('t,y,x'),scope=np.array(cfg['diagnostic_scope']))
    np.savez_compressed(out/'diagnostic_qkd_availability.npz',qkd_available=diagnostic['qkd_available'],
        resolved_mask=diagnostic['resolved_mask'],**common,axis_order=np.array('t,y,x'),scope=np.array(cfg['diagnostic_scope']))
    np.savez_compressed(out/'diagnostic_threshold_0p1db.npz',diagnostic_threshold_db=np.full((50,50),.1),
        x_m=common['x_m'],y_m=common['y_m'],scope=np.array('ILLUSTRATIVE_NOT_VALIDATED_0P55M'))
    np.savez_compressed(out/'official_pending_status.npz',**pending,**common,axis_order=np.array('t,y,x'),
        scope=np.array('OFFICIAL_0P55M_PENDING_NO_THRESHOLD_VALIDATED'))
    records=[]
    for mode,classification in [('diagnostic_0p1db',diagnostic),('official_055_pending',pending)]:
        for row in frame_statistics(a,classification):records.append(dict(mode=mode,time_s=float(common['time_s'][row['slot']]),**row))
    with (out/'frame_blockage_statistics.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)
    blocked=int(np.sum(diagnostic['binary_blockage']==1));affected=int(np.sum(a>0));total=a.size
    stats=dict(total_cell_slots=total,cloud_affected_cell_slots=affected,
        diagnostic_clear_assumed_feasible_cell_slots=total,diagnostic_blocked_cell_slots=blocked,
        diagnostic_available_cell_slots=total-blocked,diagnostic_blocked_fraction=blocked/total,
        diagnostic_cloud_induced_fraction_given_assumed_clear=blocked/total,
        diagnostic_blocked_fraction_given_cloud_affected=blocked/affected,
        cloud_affected_but_diagnostic_available_cell_slots=affected-blocked,
        first_frame_blocked_fraction=float(np.mean(diagnostic['binary_blockage'][0]==1)),
        last_frame_blocked_fraction=float(np.mean(diagnostic['binary_blockage'][-1]==1)),
        official_unresolved_cell_slots=total,official_blocked_fraction=None,
        official_cloud_induced_fraction_given_clear=None,official_secure_availability_fraction=None,
        source_mean_attenuation_db=float(a.mean()),source_maximum_attenuation_db=float(a.max()),
        source_minimum_physical_transmittance=float(t.min()),
        blocked_cells_with_nonzero_physical_transmittance=int(np.sum((diagnostic['binary_blockage']==1)&(t>0))))
    save(out/'statistics.json',stats)
    metadata=dict(model='Independent QKD-aware binary availability classification',scope=cfg['diagnostic_scope'],
        diagnostic_threshold_source='USER_AUTHORIZED_ILLUSTRATIVE_0P1_DB_NOT_QKD_CALIBRATED',
        official_threshold_validated=False,official_status=official['status'],
        threshold_equality='A>=threshold is unavailable',binary_encoding={'0':'available within assumed diagnostic','1':'unavailable','255':'unresolved'},
        classification_status_encoding={'0':'caller-supplied validated threshold','1':'known clear-sky unavailable','2':'unresolved','3':'diagnostic assumed threshold'},
        qkd_available_encoding='Boolean True only for resolved b=0; False at unknown. Always carry resolved_mask.',
        clear_sky_encoding={'0':'known unavailable','1':'known/assumed feasible according to scope','255':'unknown'},
        axis_order='t,y,x',coordinate_interpretation=cfg['coordinate_interpretation'],
        diagnostic_clear_feasibility='ASSUMED_TRUE_NOT_MEASURED_OR_VALIDATED',
        original_seed=20261111,wind_m_s=[-5,0],dt_s=1.,last_frame_s=999,
        inputs=input_hashes,input_npz_structures=structures,physical_arrays_modified=False,
        Gaussian_frames_regenerated=0,cloud_geometry_or_normalization_changed=False,
        official_critical_threshold_npz_created=False,binary_T_or_R_approximation_exported=False,
        binary_approximation_reason='No validated clear-sky 0.55 m T/R maps; optional API only, no invented physical inputs',
        binary_conversion_seconds=time.perf_counter()-started,statistics=stats)
    save(out/'metadata.json',metadata);save(out/'input_hashes.json',input_hashes)
    for name,h in protected.items():assert sha(ROOT/name)==h,name
    for name,h in input_hashes.items():assert sha(ROOT/name)==h,name
    print(json.dumps(dict(official_threshold_validated=False,official_probe=official['status'],statistics=stats),indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--config',type=Path,default=ROOT/'configs/ibrahim_binary_qkd.json')
    parser.add_argument('--resume-preexport',action='store_true')
    args=parser.parse_args();run(args.output.resolve(),args.config.resolve(),args.resume_preexport)
