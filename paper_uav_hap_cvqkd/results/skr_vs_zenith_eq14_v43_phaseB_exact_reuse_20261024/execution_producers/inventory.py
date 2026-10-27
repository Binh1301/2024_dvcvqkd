"""Consolidate saved exact payloads; never compute source moments."""
import csv
import hashlib
import json
from pathlib import Path
import re
import sys

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
PRIOR=ROOT/'results/skr_vs_zenith_eq14_v43_phaseB_readiness_20261024'
UNBLOCK=ROOT/'results/skr_vs_zenith_eq14_v43_phaseB_unblocking_20261024'
sys.path.insert(0,str(PRIOR))
import model as canonical
from support import with_ensemble, input_digests, prior_run
sys.path.insert(0,str(ROOT))
from scripts.exact_cache_provenance import verify_source_payload,source_settings,json_hash
from scripts.run_theta10_D55_unconstrained_three_scheme import make_ensemble,unconstrained_config
from scripts.run_exact_mb_test2 import ensemble_hash
sys.path.insert(0,str(OUT))  # Historical imports must not shadow this diagnostic's runner.

STRICT={'VERIFIED_EXACT','VERIFIED_BY_ALTERNATIVE_EVIDENCE'}
LABEL='HISTORICAL_EXACT_RESTRICTED_CATALOG_DIAGNOSTIC'


def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def rows(path):
    with Path(path).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def save(name,value):(OUT/name).write_bytes((json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8'))
def write(name,records):
    fields=list(dict.fromkeys(k for record in records for k in record))
    with (OUT/name).open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(records)


def prepare():
    if (OUT/'inventory_summary.json').exists():raise FileExistsError('Preserve completed inventory')
    config=unconstrained_config();settings=source_settings(config)
    pilot=rows(PRIOR/'pilot_source_verification.csv')
    pilot_by_hash={r['ensemble_hash']:r for r in pilot if r['ensemble_hash']}
    prior_full=rows(ROOT/'results/skr_vs_zenith_eq14_v43_20261024/source_catalog_coverage.csv')
    full_by_hash={r['ensemble_hash']:r for r in prior_full if r.get('ensemble_hash')}
    consolidated={};aliases={};rejected=[];provenance=[]
    for path in sorted((ROOT/'results').glob('**/exact_source_cache/*.json')):
        if re.search(r'final[_-]?test|held[_-]?out',str(path),re.I):continue
        payload=read(path)
        try:
            proof=verify_source_payload(payload,settings)
            va=float.fromhex(payload['V_A_hex']);nu=float.fromhex(payload['nu_mb_raw_hex'])
            family='Uniform' if nu==0 else 'MB'
            ensemble=make_ensemble(config,family,nu,va)
            if ensemble_hash(ensemble)!=payload['ensemble_hash']:raise ValueError('Reconstructed ensemble differs')
            c=dict(family=family,VA=va,VA_hex=va.hex(),nu_raw=nu,nu_raw_hex=nu.hex(),
                nu_repo=42.5*nu,nu_repo_hex=payload['nu_mb_repo_hex'],ensemble_hash=payload['ensemble_hash'],
                C=payload['C'],w=payload['w'],C_hex=float(payload['C']).hex(),w_hex=float(payload['w']).hex(),
                source_path=path.relative_to(ROOT).as_posix(),source_sha256=sha(path))
            source={**c,'p':ensemble.probabilities[0].numpy(),'alpha':ensemble.amplitudes[0].numpy()}
            p,alpha=canonical.prior_model.helpers().validate_source(source)
            if abs(float(p @ (2*alpha.real)**2)-va)>2e-12:raise ValueError('VA quadrature convention differs')
            identity=proof['canonical_source_cache_key']
            alias=dict(path=c['source_path'],sha256=c['source_sha256'],cache_key=payload['cache_key'])
            if identity in consolidated:
                existing=consolidated[identity]
                if any(c[k]!=existing[k] for k in ['ensemble_hash','VA_hex','nu_raw_hex','C_hex','w_hex']):
                    raise ValueError('Conflicting values under identical canonical source identity')
            else:
                old=pilot_by_hash.get(c['ensemble_hash'],full_by_hash.get(c['ensemble_hash'],{}))
                classification=old.get('classification') or ('VERIFIED_EXACT' if old.get('convergence_status')=='CURRENTLY_VERIFIED_PASS' else 'INSUFFICIENT_EVIDENCE')
                c.update(canonical_source_identity=identity,M=256,geometry='square_16x16_QAM',
                    distribution='Uniform1/256' if family=='Uniform' else 'Maxwell_Boltzmann',
                    normalization='VA=Vmod=2*nbar; X_A=2Re(alpha)',MB_convention=payload['mb_convention'],
                    C_w_definitions='Preserved full-support C4 coherent-state Gram source kernel',
                    compatibility_status='CURRENTLY_VERIFIED_PASS',source_evidence_class=classification,
                    convergence_receipts=old.get('receipt_paths',''),source_route=payload['source_moment_route'],
                    source_settings_json=json.dumps(payload['source_settings'],sort_keys=True),
                    input_digests_json=json.dumps(input_digests(source),sort_keys=True),
                    pilot_member=c['ensemble_hash'] in pilot_by_hash)
                consolidated[identity]=c
                provenance.append(dict(identity=identity,source=c['source_path'],proof=proof))
            aliases.setdefault(identity,[]).append(alias)
        except (ValueError,KeyError,TypeError) as error:
            rejected.append(dict(path=path.relative_to(ROOT).as_posix(),sha256=sha(path),reason=str(error)))
    inventory=sorted(consolidated.values(),key=lambda r:(r['family'],r['VA'],r['nu_raw'],r['canonical_source_identity']))
    by_path={alias['path']:c for c in inventory for alias in aliases[c['canonical_source_identity']]}
    by_hash={c['ensemble_hash']:c for c in inventory}
    for c in inventory:
        a=aliases[c['canonical_source_identity']]
        c.update(alias_count=len(a),alias_paths=';'.join(x['path'] for x in a))
    save('source_payload_provenance.json',dict(verified=provenance,aliases=aliases,rejected=rejected))

    # Catalog rows are corroboration; only payload/hash-bound matches authorize reuse.
    catalog_files=[];catalog_checks=[]
    for path in sorted((ROOT/'results').rglob('*.csv')):
        if OUT in path.parents or re.search(r'final[_-]?test|held[_-]?out',str(path),re.I):continue
        if not any(word in path.name.lower() for word in ['catalog','exact_source','source_moments','source_moment_audit']):continue
        records=rows(path);catalog_files.append(dict(path=path.relative_to(ROOT).as_posix(),sha256=sha(path),rows=len(records)))
        for index,r in enumerate(records):
            source=by_path.get(r.get('source_path','').replace('\\','/')) or by_hash.get(r.get('ensemble_hash',''))
            if not source:continue
            conflicts=[]
            for key in ['C','w']:
                if r.get(key) and float(r[key])!=source[key]:conflicts.append(key)
            if r.get('VA_hex') and r['VA_hex']!=source['VA_hex']:conflicts.append('VA_hex')
            if r.get('nu_raw_hex') and r['nu_raw_hex']!=source['nu_raw_hex']:conflicts.append('nu_raw_hex')
            catalog_checks.append(dict(path=path.relative_to(ROOT).as_posix(),row=index+2,
                source_identity=source['canonical_source_identity'],status='CONFLICT' if conflicts else 'MATCH',conflicts=';'.join(conflicts)))
    # The later Uniform JSON catalog is also included without reauthoring it.
    jpath=ROOT/'results/uniform_positive_skr_manuscript43_20261023/source_catalog.json'
    jdata=read(jpath);catalog_files.append(dict(path=jpath.relative_to(ROOT).as_posix(),sha256=sha(jpath),rows=len(jdata)))
    for i,r in enumerate(jdata):
        source=by_hash.get(r.get('ensemble_hash',''))
        if source:
            assert all(float(r[k])==source[k] for k in ['C','w'])
            catalog_checks.append(dict(path=jpath.relative_to(ROOT).as_posix(),row=i,source_identity=source['canonical_source_identity'],status='MATCH',conflicts=''))
    save('historical_catalog_index.json',catalog_files);write('catalog_cross_checks.csv',catalog_checks)
    write('exact_source_inventory.csv',inventory)
    coverage=[]
    expected=read(PRIOR/'source_job_preflight.json')['ensemble_hash']
    for r in pilot:
        source=by_hash.get(r['ensemble_hash']) if r['ensemble_hash'] else None
        if source:
            assert all(r[k]==source[k] for k in ['VA_hex','nu_raw_hex','ensemble_hash'])
            assert all(float(r[k])==source[k] for k in ['C','w'])
        c=dict(r,nu_repo=42.5*float.fromhex(r['nu_raw_hex']),
            expected_ensemble_hash=r['ensemble_hash'] or expected,
            canonical_source_identity=source['canonical_source_identity'] if source else '',
            compatible_exact_Cw_available=bool(source),diagnostic_eligible=bool(source),
            strict_source_eligible=bool(source) and r['classification'] in STRICT,
            diagnostic_evidence_group=('STRICT_SOURCE_EVIDENCE' if r['classification'] in STRICT else 'HISTORICAL_EXACT_EVIDENCE_INCOMPLETE') if source else 'MISSING_SOURCE',
            reuse_policy='Existing C,w unchanged; no source calculation',
            missing_impact='' if source else 'Excluded from available Uniform and MB pool; same-VA Uniform-vs-FixedMB comparison unavailable; original81-source optimum not evaluated')
        coverage.append(c)
    assert len(coverage)==81
    missing_matches=[c for c in inventory if c['family']=='Uniform' and c['VA_hex']=='0x1.9ffff84830112p+0' and c['nu_raw_hex']==0.0.hex()]
    save('missing_uniform_search.json',dict(VA_hex='0x1.9ffff84830112p+0',nu_raw_hex=0.0.hex(),expected_ensemble_hash=expected,
        exact_payload_matches=missing_matches,source_cache_files=sum(len(v) for v in aliases.values())+len(rejected),
        historical_catalog_files=len(catalog_files),previous_Git_archive_search_path=UNBLOCK.relative_to(ROOT).as_posix()+'/expanded_evidence_scan.json',
        canonicalization_policy='Existing exact_cache_provenance LF-only implementation aliases; exact binary64 VA/nu and reconstructed p,alpha/hash; no parameter rounding or moment interpolation'))
    write('pilot_source_coverage.csv',coverage)
    summary=dict(source_cache_files=sum(len(v) for v in aliases.values())+len(rejected),
        compatible_canonical_sources=len(inventory),compatible_payload_files=sum(len(v) for v in aliases.values()),
        rejected_payload_files=len(rejected),pilot_sources=81,pilot_available=sum(r['diagnostic_eligible'] for r in coverage),
        pilot_strict_source_evidence=sum(r['strict_source_eligible'] for r in coverage),
        pilot_incomplete_evidence=sum(r['diagnostic_eligible'] and not r['strict_source_eligible'] for r in coverage),
        missing_Uniform_found=bool(missing_matches),catalog_files=len(catalog_files),catalog_bound_rows=len(catalog_checks),
        catalog_conflicts=sum(r['status']=='CONFLICT' for r in catalog_checks),source_Cw_computations=0,
        strict_Phase_B_ready=False,result_label=LABEL)
    save('inventory_summary.json',summary)
    print(json.dumps(summary,indent=2))


if __name__=='__main__':prepare()
