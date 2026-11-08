"""Pinned Phase5E numeric source and TEST_ONLY cloud/finite-size/solver runner.

No CV-QKD evaluator or lookup regeneration is invoked. Candidate/mission inputs
remain pending; this module only executes explicitly labeled software fixtures.
"""
import argparse
import copy
import csv
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from types import MappingProxyType
import numpy as np
from .config import load_config
from .cloud_model import CloudField,GaussianCluster
from .blockage import BlockageModel
from .rotor_reference import load_reference
from .propulsion import EnergyModel
from .waypoint_graph import WaypointGraph
from .evaluation import Scenario
from .rate_provider import sample_rate_provider
from .experiments import run_methods

ROOT=Path(__file__).resolve().parents[2]
TEST_ARTIFACT_ROOT=ROOT/'test_artifacts'
PHASE5E_PACKAGE_SHA256='7b3f3b4fe7a4cd9c9f046aa456f3a1a4e4b8cf83c327f09e0fba23c28831bfa7'
TEST_ONLY='TEST_ONLY — NOT RESEARCH OR PAPER RESULTS'


def _sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def _read(path):return json.loads(Path(path).read_text(encoding='utf-8'))


@dataclass(frozen=True)
class Phase5ELookup:
    directory: Path
    package_sha256: str
    points: tuple
    _nodes: object
    hap_m: tuple
    uav_altitude_m: float
    area_m: tuple

    def node(self,q):
        q=np.asarray(q,float)
        if q.shape!=(2,) or not np.isfinite(q).all() or tuple(q) not in self._nodes:
            raise ValueError('Phase5E integration requires an exact lookup node; no interpolation/extrapolation fallback')
        rate,transmission,evidence,source=self._nodes[tuple(q)]
        return dict(rate=rate,transmittance=transmission,source_evidence_class=evidence,ensemble_hash=source)


def load_phase5e_lookup(reference,base=ROOT):
    directory=(Path(base)/reference['directory']).resolve();manifest_path=directory/'phase5e_package_manifest.json'
    if (reference.get('package_manifest_sha256')!=PHASE5E_PACKAGE_SHA256 or not manifest_path.is_file()
            or _sha(manifest_path)!=PHASE5E_PACKAGE_SHA256):
        raise ValueError('Pinned Phase5E package missing/mismatched; no historical lookup fallback')
    if (reference.get('coordinate_policy'),reference.get('coordinate_units'),reference.get('rate_units'))!=('exact_nodes_only','m','bits/use'):
        raise ValueError('Phase5E units/coordinate policy mismatch')
    manifest=_read(manifest_path);files=manifest['files']
    actual={str(f.relative_to(directory)).replace('\\','/') for f in directory.rglob('*') if f.is_file() and f!=manifest_path}
    if actual!=set(files):raise ValueError('Phase5E package file coverage mismatch')
    for name,h in files.items():
        path=(directory/name).resolve()
        if not path.is_relative_to(directory) or _sha(path)!=h:raise ValueError('Phase5E package seal mismatch: '+name)
    metadata=_read(directory/'phase5e_validation/target_effective_protocol.json')
    validated=_read(directory/'phase5e_validation/validation_summary.json')
    if (validated['status']!='CURRENTLY_VERIFIED_PASS' or validated['spatial_positions']!=2601
            or validated['unique_geometries']!=294 or validated['full_search_candidate_evaluations']!=62328
            or validated['paper_admissible'] is not False):
        raise ValueError('Phase5E validation report/scope mismatch')
    if (metadata['xi_ch'],metadata['xi_det'],metadata['beta'])!=(.0136,.005,.95):raise ValueError('Phase5E noise/protocol mismatch')
    if metadata['source_normalization'].split(';',1)[0].strip()!='VA=Vmod=2*nbar':raise ValueError('Phase5E modulation convention mismatch')
    with (directory/'skr_map.csv').open(encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f))
    points=tuple((float(r['x_m']),float(r['y_m'])) for r in rows)
    expected=tuple((float(x),float(y)) for y in range(0,2001,40) for x in range(0,2001,40))
    if points!=expected or len({r['group_id'] for r in rows})!=294:raise ValueError('Phase5E grid/order/geometry mismatch')
    rates=np.array([float(r['skr_bits_per_use']) for r in rows]);transmission=np.array([float(r['MB_eta_f']) for r in rows])
    if not np.isfinite([rates,transmission]).all() or np.any((transmission<0)|(transmission>1)):raise ValueError('Invalid Phase5E rate/transmission data')
    with np.load(directory/'skr_map.npz',allow_pickle=False) as data:
        if (data['coordinate_units'].item(),data['rate_units'].item(),data['xi_ch'].item(),data['xi_det'].item())!=('m','bits/use',.0136,.005):
            raise ValueError('Phase5E NPZ units/noise mismatch')
        if data['paper_admissible'].item() is not False:raise ValueError('Phase5E source evidence unexpectedly promoted')
        np.testing.assert_array_equal(data['points'],points);np.testing.assert_array_equal(data['rates'],rates)
        np.testing.assert_array_equal(data['MB_source_evidence_class'],[r['MB_source_evidence_class'] for r in rows])
    for r in rows:
        if float(r['skr_bits_per_use'])!=float(r['MB_K_raw']):raise ValueError('Phase5E raw signed rate alias changed')
    nodes=MappingProxyType({q:(float(rate),float(T),r['MB_source_evidence_class'],r['MB_ensemble_hash'])
                           for q,rate,T,r in zip(points,rates,transmission,rows)})
    physical=metadata['physical']
    hap=tuple(metadata['lookup_hap_projection_m'])+(float(physical['h_hap_km'])*1000.,)
    return Phase5ELookup(directory,PHASE5E_PACKAGE_SHA256,points,nodes,hap,
                         float(physical['h_uav_km'])*1000.,tuple(metadata['lookup_area_m']))


@dataclass(frozen=True)
class BinaryLOSRateProvider:
    source: Phase5ELookup
    model: BlockageModel

    def slot(self,q,t,m0):
        if not np.isfinite(t) or t<0 or not np.isfinite(m0) or m0<=0:raise ValueError('Explicit nonnegative time and positive m0 required')
        clear=self.source.node(q);z=int(not self.model.blocked(q,t))
        return dict(z_los=z,clear_rate=clear['rate'],retained_rate=clear['rate'],effective_rate=z*clear['rate'],
                    transmittance=z*clear['transmittance'],valid_signals=m0*z,raw_contribution=m0*z*clear['rate'])

    def effective_rate(self,q,t):
        return (not self.model.blocked(q,t))*self.source.node(q)['rate']

    def retained_rate(self,q,t,scenario):
        return self.source.node(q)['rate']


def build_test_scenario(config,*,source=None):
    c=copy.deepcopy(config)
    if str(c.get('mode','')).lower()=='paper':raise ValueError('Phase5F does not authorize paper-mode; missing author inputs/readiness remain')
    if c.get('mode')!='TEST_ONLY' or c.get('fixture_label')!='TEST_ONLY':
        missing=[k for k,v in c.get('parameters',{}).items() if v is None]
        raise ValueError('Missing author decisions; only TEST_ONLY technical fixtures may run: '+', '.join(missing))
    if c.get('cloud_candidate_author_approved') is not False or c.get('paper_mode')!='NOT_RUN':
        raise ValueError('TEST_ONLY execution cannot approve candidate/paper mode')
    f=c['fixture'];base=Path(c['_config_path']).parent
    missing=[k for k in ('hap_m','uav_altitude_m','area_m','initial_m','dt','max_horizon','energy_budget_j',
             'rotor_profile','velocity_samples','energy_tolerance_j','graph','finite_size','lambda_bits_per_j','cloud') if f.get(k) is None]
    finite=f.get('finite_size') if isinstance(f.get('finite_size'),dict) else {}
    missing += ['finite_size.'+k for k in ('m0','epsilon') if finite.get(k) is None]
    if missing:raise ValueError('Missing explicit TEST_ONLY inputs: '+', '.join(missing))
    verified=load_phase5e_lookup(c['lookup'],base)
    if source is not None and (not isinstance(source,Phase5ELookup) or source!=verified):
        raise ValueError('Shared lookup differs from declared source; no fallback')
    source=verified
    if tuple(f['hap_m'])!=source.hap_m or f['uav_altitude_m']!=source.uav_altitude_m or tuple(f['area_m'])!=source.area_m:
        raise ValueError('Mission geometry must match Phase5E lookup geometry')
    if type(f['max_horizon']) is not int or not 1<=f['max_horizon']<=6 or f['graph']['kind']!='points' or len(f['graph']['points_m'])>8:
        raise ValueError('TEST_ONLY runner is bounded to six slots/eight explicit graph points')
    for q in f['graph']['points_m']:source.node(q)
    rotor=load_reference(base/f['rotor_profile'])
    graph=WaypointGraph.build(f['graph']['points_m'],f['initial_m'],f['area_m'],f['dt'],
                              EnergyModel(rotor['params'],f['velocity_samples']),energy_tolerance_j=f['energy_tolerance_j'])
    cloud=f['cloud']
    if cloud['mode']!='binary_los_blockage' or cloud['velocity_m_s']!=[-5.,0.]:raise ValueError('Candidate mode/drift mismatch')
    if cloud['layer_top_m']<=cloud['layer_bottom_m']:raise ValueError('Cloud slab needs explicit positive thickness')
    field=CloudField([GaussianCluster(**r) for r in cloud['clusters']],cloud['velocity_m_s'],cloud['clip_max'])
    if any(c.velocity is not None and not np.array_equal(c.velocity,field.velocity) for c in field.clusters):
        raise ValueError('Per-cluster drift must match the declared [-5,0] m/s cloud drift')
    model=BlockageModel(field,cloud['threshold_mg_m3'],f['hap_m'],f['uav_altitude_m'],mode='layer',
                        layer_bottom_m=cloud['layer_bottom_m'],layer_top_m=cloud['layer_top_m'],sample_spacing_m=cloud['sample_spacing_m'])
    provider=BinaryLOSRateProvider(source,model)
    z=model.sequence(graph.positions,f['max_horizon'],graph.dt)
    scenario=Scenario(graph,np.array([source.node(q)['rate'] for q in graph.positions]),z,
                       f['energy_budget_j'],f['finite_size']['m0'],f['finite_size']['epsilon'])
    scenario=sample_rate_provider(scenario,provider.retained_rate)
    return scenario,dict(source=source,field=field,provider=provider,rotor=rotor,config=c)


def _scenario_digest(s):
    h=hashlib.sha256()
    for a in (s.graph.positions,s.graph.costs,s.rates,s.z):h.update(np.asarray(a).tobytes())
    h.update(repr((s.graph.initial,s.graph.dt,s.budget,s.horizon,s.m0,s.epsilon)).encode())
    return h.hexdigest()


def run_test_only(config,output):
    output=Path(output).resolve()
    if not output.is_relative_to(TEST_ARTIFACT_ROOT.resolve()) or not output.name.startswith('phase5f_'):
        raise ValueError('TEST_ONLY artifacts must stay in test_artifacts/phase5f_, never research results')
    if output.exists() and any(output.iterdir()):raise FileExistsError('Preserve completed TEST_ONLY artifacts')
    s,ctx=build_test_scenario(config);before=_scenario_digest(s)
    weight=ctx['config']['fixture']['lambda_bits_per_j']
    runs=run_methods(s,config,weight,measure=False)
    if _scenario_digest(s)!=before:raise ValueError('A method changed shared scenario inputs')
    report=dict(data_status=TEST_ONLY,source_kind='REAL_PHASE5E_NUMERICAL_DIAGNOSTIC_LOOKUP',
        source_package_sha256=ctx['source'].package_sha256,source_directory=str(ctx['source'].directory),
        paper_mode='NOT_RUN',cloud_candidate_author_approved=False,paper_admissible=False,source_evidence_promoted=False,
        config=ctx['config'],shared_scenario_sha256=before,runs=runs,
        information_scope='DP full predicted cloud horizon; greedy current-slot actions; all methods retrospective best feasible prefix',
        time_convention='destination q_k at t_k=k*dt; zero-based row k-1',
        rate_convention='effective scheduled rate=z*Rclear; Scenario.rates=Rclear per retained use and m=m0*z, once',
        fixture_seed=ctx['config']['fixture']['cloud']['seed'],
        seed_role='Recorded fixture identifier; coefficients are explicit, no random cloud generated',
        science_scope='No author-approved mission/cloud settings; no SKR evaluation/regeneration/security certification')
    output.mkdir(parents=True,exist_ok=True)
    def write(name,value):
        with (output/name).open('x',encoding='utf-8') as f:json.dump(value,f,indent=2,ensure_ascii=False,allow_nan=False)
    write('dry_run.json',report)
    np.savez_compressed(output/'scenario_TEST_ONLY.npz',positions=s.graph.positions,rates=s.rates,z=s.z,
        edge_costs_j=s.graph.costs,data_status=TEST_ONLY,source_package_sha256=ctx['source'].package_sha256)
    rows=[]
    for k in range(s.horizon):
        for j,q in enumerate(s.graph.positions):rows.append(dict(data_status=TEST_ONLY,k=k+1,t_s=(k+1)*s.graph.dt,waypoint=j,x_m=q[0],y_m=q[1],**ctx['provider'].slot(q,(k+1)*s.graph.dt,s.m0)))
    with (output/'slot_quantities_TEST_ONLY.csv').open('x',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    base=Path(config['_config_path']).parent
    paths=[Path(config['_config_path']),base/config['fixture']['rotor_profile']]
    paths += [ctx['source'].directory/name for name in ('phase5e_package_manifest.json','skr_map.csv','skr_map.npz',
              'phase5e_validation/target_effective_protocol.json','phase5e_validation/validation_summary.json')]
    write('input_manifest.json',dict(data_status=TEST_ONLY,inputs={str(f.resolve()):_sha(f) for f in paths},
        producers={str(f.relative_to(ROOT)):_sha(f) for f in sorted((ROOT/'src/uav_qkd').glob('*.py'))},
        realization=ctx['config']['fixture']['cloud'],source_admissibility='NUMERIC_TEST_INPUT_ONLY_NOT_PAPER_ADMISSION'))
    write('output_manifest.json',{f.name:_sha(f) for f in output.iterdir() if f.is_file() and f.name!='output_manifest.json'})
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--config',required=True);parser.add_argument('--output',required=True)
    args=parser.parse_args();report=run_test_only(load_config(args.config),args.output)
    print(json.dumps(dict(data_status=report['data_status'],methods=len(report['runs']),paper_mode=report['paper_mode']),ensure_ascii=False))
