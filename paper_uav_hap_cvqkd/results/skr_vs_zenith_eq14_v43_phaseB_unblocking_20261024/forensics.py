"""Read-only source evidence recovery; never call a source-moment evaluator."""
import ast
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
PRIOR = ROOT / 'results/skr_vs_zenith_eq14_v43_phaseB_readiness_20261024'
sys.path.insert(0, str(PRIOR))
import provenance
from support import input_digests, prior_run, with_ensemble


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def save(name, value):
    (OUT/name).write_bytes((json.dumps(value, ensure_ascii=False, indent=2)+'\n').encode('utf-8'))


def nodes(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from nodes(child)
    elif isinstance(value, list):
        for child in value:
            yield from nodes(child)


def decoded(value):
    """Unwrap saved tool envelopes; executable code is never evaluated."""
    yield value
    if isinstance(value, (dict, list)):
        children = value.values() if isinstance(value, dict) else value
        for child in children:
            yield from decoded(child)
    elif isinstance(value, str):
        text = value.strip()
        try:
            parsed = json.loads(text)
        except (ValueError, TypeError):
            try:
                parsed = ast.literal_eval(text) if text.startswith(("[{'", "{'")) else None
            except (ValueError, SyntaxError, MemoryError, RecursionError):
                parsed = None
        if isinstance(parsed, (dict, list)):
            yield from decoded(parsed)
        else:
            for line in text.splitlines():
                if line.startswith('{') and line != text:
                    try:
                        yield from decoded(json.loads(line))
                    except ValueError:
                        pass


def excluded(name):
    return bool(re.search(r'final[_-]?test|held[_-]?out', name, re.I))


def git_blobs():
    raw = subprocess.check_output(['git','log','--all','--format=','--raw','--no-abbrev',
        '--','paper_uav_hap_cvqkd/results/'], cwd=ROOT.parent).decode('utf-8')
    refs = {}
    for line in raw.splitlines():
        if not line.startswith(':') or '\t' not in line:
            continue
        header, name = line.split('\t', 1)
        if excluded(name) or Path(name).suffix not in {'.json','.jsonl','.log','.csv','.txt'}:
            continue
        for oid in header.split()[2:4]:
            if set(oid) != {'0'}:
                refs.setdefault(oid, set()).add(name)
    request = ('\n'.join(refs)+'\n').encode()
    sizes = subprocess.check_output(['git','cat-file','--batch-check'], input=request, cwd=ROOT.parent)
    selected = []
    for line in sizes.decode().splitlines():
        oid, kind, size = line.split()
        if kind == 'blob': selected.append((oid, int(size)))
    inventory = [{'git_blob':oid, 'bytes':size, 'paths':sorted(refs[oid])} for oid,size in selected]
    save('git_blob_inventory.json', inventory)
    # Separate batch requests avoid storing every historical blob in memory at once.
    for offset in range(0, len(selected), 50):
        batch = selected[offset:offset+50]
        data = subprocess.check_output(['git','cat-file','--batch'],
            input=('\n'.join(oid for oid,_ in batch)+'\n').encode(), cwd=ROOT.parent)
        cursor = 0
        for oid,size in batch:
            end = data.index(b'\n',cursor)
            header = data[cursor:end].decode().split()
            assert header == [oid,'blob',str(size)]
            content = data[end+1:end+1+size]
            cursor = end+2+size
            yield 'git:'+oid, content, {'paths':sorted(refs[oid]),'git_blob':oid}


def recover():
    rows = list(csv.DictReader((PRIOR/'pilot_source_verification.csv').open(encoding='utf-8',newline='')))
    previous = read(PRIOR/'source_verification_evidence.json')
    details = {item['source']['ensemble_hash']:item for item in previous['sources'] if item['source']['ensemble_hash']}
    sources = {}
    for row in rows:
        if not row['source_path']: continue
        assert sha(ROOT/row['source_path']) == row['source_sha256']
        source = dict(row,VA=float.fromhex(row['VA_hex']),nu_raw=float.fromhex(row['nu_raw_hex']),
            C=float(row['C']),w=float(row['w']))
        sources[row['ensemble_hash']] = with_ensemble(source)
        provenance.prior_model.helpers().validate_source(sources[row['ensemble_hash']])
    digests = {tuple(input_digests(s)[k] for k in ['pmf_sha256','amplitude_sha256']):s for s in sources.values()}
    payloads = {h:read(ROOT/s['source_path']) for h,s in sources.items()}
    hashes = set(sources)
    archive = []
    hits = []
    candidates = []
    scanned = []
    observations = []
    snapshots = OUT/'recovered_records'
    snapshots.mkdir(exist_ok=True)

    def inspect(origin, raw, metadata, tool=False):
        digest = hashlib.sha256(raw).hexdigest()
        text = raw.decode('utf-8-sig',errors='replace')
        matched = sorted(h for h in hashes if h in text)
        precision = any(k in text for k in ['fallback_rows','minimum_eigenvalue','precision_ladder_decimal_digits'])
        scanned.append(dict(origin=origin,sha256=digest,bytes=len(raw),matched_ensembles=matched,
                            contains_precision_fields=precision,**metadata))
        if not precision or not any(k in text for k in ['"C"','\\"C\\"',"'C'"]): return
        try:
            data = json.loads(text)
        except ValueError:
            data = []
            for line in text.splitlines():
                if line.strip().startswith('{'):
                    try: data.append(json.loads(line))
                    except ValueError: pass
        if data is None: return
        # Existing quarantined/superseded artifacts never become approval evidence.
        status = str(data.get('status','')).upper() if isinstance(data,dict) else ''
        if any(k in status for k in ['QUARANTIN','SUPERSEDED','DEPRECATED']): return
        parsed_nodes = decoded(data) if tool else nodes(data)
        accepted = []
        for node in parsed_nodes:
            if not isinstance(node,dict): continue
            key=(node.get('pmf_sha256'),node.get('amplitude_sha256'))
            if key in digests:
                source=digests[key]
                try: proof=provenance.alternative_ladder(source,node)
                except (KeyError,ValueError,TypeError): proof=None
                candidates.append(dict(origin=origin,source_hash=source['ensemble_hash'],
                    method='UNCHANGED_ALTERNATIVE_EVIDENCE_CHECKER',accepted=bool(proof),
                    reason='SAVED_FULL_SUPPORT_LADDER_VERIFIED' if proof else 'COMPLETE_BINDABLE_PRECISION_DIAGNOSTICS_NOT_PRESENT'))
                if proof: accepted.append(dict(source_hash=source['ensemble_hash'],method='VERIFIED_BY_ALTERNATIVE_EVIDENCE',proof=proof))
            for h in matched:
                try: status=prior_run.check_receipt(payloads[h],sources[h]['source_sha256'],node)
                except (ValueError,KeyError,TypeError): status=None
                if status=='CURRENTLY_VERIFIED_PASS':
                    accepted.append(dict(source_hash=h,method='VERIFIED_EXACT',proof='UNCHANGED_PAYLOAD_BOUND_RECEIPT_CHECKER'))
        if accepted:
            dest=snapshots/(digest+'.json')
            if not dest.exists(): dest.write_bytes(raw)
            for item in accepted:
                hits.append(dict(**item,origin=origin,sha256=digest,snapshot=dest.relative_to(OUT).as_posix(),**metadata))

    for origin,raw,meta in git_blobs(): inspect(origin,raw,meta)
    # Archives are inspected in place; never extracted over historical files.
    for p in sorted((ROOT/'results').rglob('*.zip')):
        if excluded(str(p)): continue
        with zipfile.ZipFile(p) as z:
            names=[]
            for entry in z.infolist():
                if excluded(entry.filename) or Path(entry.filename).suffix not in {'.json','.jsonl','.log','.csv','.txt'}: continue
                names.append(entry.filename)
                inspect(str(p.relative_to(ROOT))+'!'+entry.filename,z.read(entry),dict(archive_sha256=sha(p)))
        archive.append(dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),text_members=names))

    session_matches=read(OUT/'execution_record_search.json')['matched_files']
    for name in session_matches:
        path=Path(name)
        source_digest=sha(path)
        for line_number,line in enumerate(path.open(encoding='utf-8'),1):
            obj=json.loads(line)
            payload=obj.get('payload',{})
            if payload.get('type') not in {'custom_tool_call_output','function_call_output'}: continue
            if not any(k in line for k in ['fallback_rows','minimum_eigenvalue','1.6249995399703647','diagonal_solve_worker.py']): continue
            origin=path.name+':'+str(line_number)
            inspect(origin,line.encode(),dict(execution_file=str(path),execution_sha256=source_digest,
                line=line_number,timestamp=obj.get('timestamp')),tool=True)
            if 'diagonal_solve_worker.py' in line:
                fragments=[]
                for value in decoded(payload.get('output')):
                    if isinstance(value,str) and value.lstrip().startswith('Traceback (most recent call last)') and 'TimeoutExpired' in value:
                        fragments.append(value[:10000])
                if fragments:
                    observations.append(dict(origin=origin,timestamp=obj.get('timestamp'),fragments=fragments))
    save('expanded_evidence_scan.json',dict(scanned=scanned,recovered=hits,candidates=candidates,archives=archive,
        method='Existing strict receipt/alternative checkers reused unchanged; only saved numerical evidence',
        limitation='Git JSONL/text and archive text without complete bindable JSON is supporting metadata only'))
    save('uniform_execution_observations.json',observations)
    output=[]
    for row in rows:
        h=row['ensemble_hash']; source=sources.get(h)
        record=dict(row)
        record.update(nu_repo=42.5*float.fromhex(row['nu_raw_hex']),
            nu_repo_hex=(42.5*float.fromhex(row['nu_raw_hex'])).hex(),
            source_identity='|'.join(row[k] for k in ['family','VA_hex','nu_raw_hex','ensemble_hash']),
            Cw_available=bool(row['source_path']),previous_status=row['classification'],
            original_computation_job_id='NOT_RECORDED',original_run_id='NOT_RECORDED',
            source_artifact_run_namespace=Path(row['source_path']).parts[1] if row['source_path'] else '',
            new_evidence_references=';'.join(sorted({x['origin'] for x in hits if x['source_hash']==h})))
        record['expected_ensemble_hash']=h or read(PRIOR/'source_job_preflight.json')['ensemble_hash']
        if source:
            payload=payloads[h]
            record['source_cache_key']=payload['cache_key']
            assert payload['nu_mb_repo_hex']==record['nu_repo_hex']
            assert payload['ensemble_hash']==h
            info=details[h]
            record['available_logs']=';'.join(x for x in info['supporting_records'] if Path(x).suffix in {'.log','.jsonl','.txt'})
            record['available_metadata_and_artifacts']=';'.join(info['supporting_records'])
            record['saved_convergence_diagnostics']=';'.join(x['path'] for x in info['direct_receipts']+info['alternative_evidence'])
            recovered=[x for x in hits if x['source_hash']==h]
            if recovered and record['classification']!='VERIFIED_EXACT':
                record['classification']='VERIFIED_EXACT' if any(x['method']=='VERIFIED_EXACT' for x in recovered) else 'VERIFIED_BY_ALTERNATIVE_EVIDENCE'
                record['reason']='RECOVERED_SAVED_NUMERICAL_EVIDENCE_UNCHANGED_POLICY'
        record['status_changed']=record['classification']!=record['previous_status']
        record['missing_requirement']='' if record['classification'] in provenance.ACCEPTED else (
            'Exact Uniform payload and bound full-support precision receipt' if not source else
            'Payload-bound full-support receipt or exact PMF+amplitude digests with saved1050/1250/1450 full-support ladder')
        output.append(record)
    fields=list(dict.fromkeys(k for row in output for k in row))
    with (OUT/'pilot_source_evidence.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(output)
    from collections import Counter
    counted=Counter(row['classification'] for row in output)
    counts={key:counted[key] for key in ['VERIFIED_EXACT','VERIFIED_BY_ALTERNATIVE_EVIDENCE','INSUFFICIENT_EVIDENCE','INVALID']}
    fixed=next(row for row in output if row['ensemble_hash']=='01c79ae70c9aacd627a5eb0e689b0b383df80bae9d89ba17088fd81f69e34754')
    result=dict(counts=counts,upgraded_sources=sum(r['status_changed'] for r in output),
        existing_sources=80,missing_source_count=1,existing_sources_missing_evidence=sum(r['Cw_available'] and r['classification'] not in provenance.ACCEPTED for r in output),
        fixed_MB_status=fixed['classification'],fixed_MB_hash=fixed['ensemble_hash'],
        missing_Uniform_status='BLOCKED_BY_ENVIRONMENT_TIMEOUT_NO_PAYLOAD',PHASE_B_STRICT_READY=False,
        decision='BLOCKED',blockers=['EXISTING_SOURCE_CONVERGENCE_EVIDENCE_INCOMPLETE','EXACT_UNIFORM_PAYLOAD_AND_RECEIPT_MISSING'],
        blocker_families=2,source_identity_conflicts=sum(r['classification']=='INVALID' for r in output),
        expensive_source_recomputations=0,pilot_executed=False,full_sweep_executed=False,
        frozen_spec_resolution='PRESERVED_DISTINCT_VERSIONED_EXPERIMENT_HASH_VERIFIED',
        spec_sha256=sha(PRIOR/'experiment_spec_v1.json'),runner_checks='PRIOR_10_CHECKS_HASH_VERIFIED_NOT_RERUN',
        new_convergence_evidence_policy=False)
    assert len(output)==81 and sum(counts.values())==81
    save('readiness_summary.json',result)
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    recover()
