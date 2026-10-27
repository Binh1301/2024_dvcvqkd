"""Bounded sequential independent workers; immutable historical caches."""
import argparse
import csv
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import numpy as np

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]


def save(name,value):
    (OUT/name).write_bytes((json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode('utf-8'))


def rows_file(name,data):
    keys=list(dict.fromkeys(k for r in data for k in r))
    with (OUT/name).open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=keys);writer.writeheader();writer.writerows(data)


def working_set(pid):
    class Counters(ctypes.Structure):
        _fields_=[('cb',wintypes.DWORD),('PageFaultCount',wintypes.DWORD)]+[(n,ctypes.c_size_t) for n in
            ['PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage',
             'QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage']]
    kernel=ctypes.WinDLL('kernel32',use_last_error=True);psapi=ctypes.WinDLL('psapi',use_last_error=True)
    kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];kernel.OpenProcess.restype=wintypes.HANDLE
    kernel.CloseHandle.argtypes=[wintypes.HANDLE]
    psapi.GetProcessMemoryInfo.argtypes=[wintypes.HANDLE,ctypes.POINTER(Counters),wintypes.DWORD]
    handle=kernel.OpenProcess(0x410,False,pid)
    if not handle:raise OSError(ctypes.get_last_error(),'OpenProcess memory monitor')
    try:
        counter=Counters();counter.cb=ctypes.sizeof(counter)
        if not psapi.GetProcessMemoryInfo(handle,ctypes.byref(counter),counter.cb):raise OSError(ctypes.get_last_error(),'GetProcessMemoryInfo')
        return int(counter.WorkingSetSize)
    finally:kernel.CloseHandle(handle)


def plan():
    small=json.loads((OUT/'inputs/small_sources.json').read_text())
    jobs=[]
    for s in small:
        for N in [24,48,96]:jobs.append(dict(source=s['name'],method='A',NF=N,digits=16,stage='sanity'))
        jobs.append(dict(source=s['name'],method='B',NF=None,digits=16,stage='sanity'))
    for s in small:
        jobs.append(dict(source=s['name'],method='A',NF=64 if s['M']<64 else 96,digits=80 if s['M']<64 else 140,stage='sanity'))
        jobs.append(dict(source=s['name'],method='B',NF=None,digits=80 if s['M']<64 else 140,stage='sanity'))
    for source in ['Winner_MB','Fixed_MB']:
        for N in [24,32,48,64,96,128,256]:jobs.append(dict(source=source,method='A',NF=N,digits=16,stage='target'))
        jobs.append(dict(source=source,method='B',NF=None,digits=16,stage='target'))
        for N,digits in [(64,80),(96,100),(128,140)]:jobs.append(dict(source=source,method='A',NF=N,digits=digits,stage='target'))
        for digits in [80,180,260]:jobs.append(dict(source=source,method='B',NF=None,digits=digits,stage='target'))
    for source in ['Winner_MB','Fixed_MB']:
        jobs.append(dict(source=source,method='A',NF=256,digits=260,stage='full_rank_spot'))
    return jobs


def execute():
    protocol=json.loads((OUT/'protocol.json').read_text());jobs=plan()
    assert os.name=='nt'
    assert working_set(os.getpid())>0
    (OUT/'jobs').mkdir(exist_ok=True)
    if (OUT/'job_receipts.json').exists():raise FileExistsError('Do not overwrite completed batch')
    save('job_plan.json',jobs)
    env=dict(os.environ,OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',OMP_NUM_THREADS='1',PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1')
    start=time.monotonic();receipts=[]
    for number,job in enumerate(jobs):
        stem=f"{number:02d}_{job['source']}_{job['method']}_N{job['NF']}_d{job['digits']}"
        target=OUT/'jobs'/f'{stem}.json';log=OUT/'jobs'/f'{stem}.log'
        if time.monotonic()-start>=protocol['total_worker_wall_seconds']:
            receipts.append(dict(**job,job=stem,status='NOT_RUN_TOTAL_BUDGET',elapsed_seconds=0));save('job_receipts.json',receipts);continue
        script=OUT/('independent_fock_Cw.py' if job['method']=='A' else 'independent_gram_Cw.py')
        command=[sys.executable,'-X','utf8','-B',str(script),str(OUT/'inputs'/f"{job['source']}.npz"),str(target),'--digits',str(job['digits'])]
        if job['method']=='A':command+=['--cutoff',str(job['NF'])]
        then=time.monotonic();peak=0;status='COMPLETED';budget=min(protocol['per_job_timeout_seconds'],protocol['total_worker_wall_seconds']-(then-start))
        with log.open('w',encoding='utf-8') as stream:
            process=subprocess.Popen(command,stdout=stream,stderr=subprocess.STDOUT,env=env,cwd=ROOT,
                creationflags=subprocess.CREATE_NO_WINDOW)
            while process.poll() is None:
                if time.monotonic()-then>budget:
                    status='INCONCLUSIVE_TIMEOUT';process.kill();break
                try:
                    current=working_set(process.pid);peak=max(peak,current)
                    if current>protocol['worker_working_set_limit_MiB']*1024**2:
                        status='INCONCLUSIVE_MEMORY_LIMIT';process.kill();break
                except OSError:
                    if process.poll() is None:
                        status='BLOCKED_MEMORY_MONITOR';process.kill();break
                time.sleep(.2)
            process.wait()
        if process.returncode!=0 and status=='COMPLETED':status='FAILED_WORKER'
        receipt=dict(**job,job=stem,status=status,returncode=process.returncode,
            elapsed_seconds=time.monotonic()-then,observed_peak_working_set_MiB=peak/1024**2,
            timeout_seconds=budget,log=log.relative_to(OUT).as_posix(),
            output=target.relative_to(OUT).as_posix() if target.exists() else '',
            producer_sha256=hashlib.sha256(script.read_bytes()).hexdigest())
        receipts.append(receipt);save('job_receipts.json',receipts)
        print(json.dumps(receipt),flush=True)
        if job['stage']=='sanity' and status not in ['COMPLETED']:
            print('Sanity worker failed; stop before expensive targets',flush=True);break
    save('execution_summary.json',dict(elapsed_seconds=time.monotonic()-start,planned_jobs=len(jobs),jobs_recorded=len(receipts),
        completed_jobs=sum(r['status']=='COMPLETED' for r in receipts),new_catalog_sources_modified=0,
        full_catalog_recomputed=False,production_Cw_evaluator_called=False,repository_moments_read_from_cache=True,
        new_independent_source_checks=True,working_set_policy='Polled Windows process working set; terminate above1024MiB; observed peak is sampled',
        source_generation_scope='Selected two MB ensembles plus independent small numerical sanity ensembles only',PHASE_B_STRICT_READY=False))


def collect():
    data=[];metadata={r['name']:r for r in json.loads((OUT/'inputs/source_metadata.json').read_text())}
    for receipt in json.loads((OUT/'job_receipts.json').read_text()):
        if receipt['status']!='COMPLETED':
            data.append(dict(source=receipt['source'],method=receipt['method'],NF=receipt['NF'],digits=receipt['digits'],numerical_status=receipt['status'],job=receipt['job']));continue
        result=json.loads((OUT/receipt['output']).read_text())
        for row in result['rows']:
            record=dict(source=receipt['source'],job=receipt['job'],**row)
            ref=metadata.get(receipt['source'])
            if ref:
                C0,w0=float(ref['C']),float(ref['w']);C,w=float(row['C']),float(row['w_residual'])
                record.update(C_repo=C0,w_repo=w0,delta_C_vs_repo=C-C0,delta_w_vs_repo=w-w0,
                    C_absolute_error=abs(C-C0),w_absolute_error=abs(w-w0),C_relative_error=abs(C-C0)/abs(C0),w_relative_error=abs(w-w0)/abs(w0))
            record['numerical_status']='INCONCLUSIVE_RETAINED_RANK_OR_PRECISION' if not row['full_source_rank_resolved'] else 'FULL_RETAINED_RANK_DIAGNOSTIC'
            if float(row['w_residual'])<0 or row['material_negative']:record['numerical_status']='NUMERICAL_INSTABILITY'
            data.append(record)
    rows_file('convergence_diagnostics.csv',data)
    return data


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--collect',action='store_true');args=parser.parse_args()
    if args.collect:collect()
    else:execute();collect()
