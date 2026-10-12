"""Observer-v2 entry integration; production requires fresh authorization and Job."""
import argparse
import ctypes
from ctypes import wintypes
from contextlib import ExitStack,redirect_stdout
from io import StringIO
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts import overnight_source_observer_v2 as v2
from scripts.overnight_source_observer import StageObserver,atomic_json,dummy_work


class InstrumentationFailure(RuntimeError):pass
class ScientificWorkerFailure(RuntimeError):pass


def original_call(function):
    def guarded(*args,**kwargs):
        try:return function(*args,**kwargs)
        except (InstrumentationFailure,ScientificWorkerFailure):raise
        except Exception as exc:
            raise ScientificWorkerFailure(f'{type(exc).__name__}: {exc}') from exc
    return guarded


class CheckedStageObserver(StageObserver):
    """Only execution errors get instrument labels; original operation errors stay separate."""
    def snapshot(self):
        cpu=time.thread_time();before=self.instrumentation_cpu
        try:return super().snapshot()
        except Exception as exc:raise InstrumentationFailure('Snapshot persistence: '+repr(exc)) from exc
        finally:self.instrumentation_cpu=before+time.thread_time()-cpu
    def __enter__(self):
        try:return super().__enter__()
        except Exception as exc:
            if isinstance(exc,InstrumentationFailure):raise
            raise InstrumentationFailure('Observer initialization: '+repr(exc)) from exc
    def __exit__(self,*args):
        try:return super().__exit__(*args)
        except Exception as exc:
            if isinstance(exc,InstrumentationFailure):raise
            raise InstrumentationFailure('Observer shutdown: '+repr(exc)) from exc
    def wrap(self,function,name,digits_getter=None):
        wrapped=super().wrap(original_call(function),name,digits_getter)
        def checked(*args,**kwargs):
            try:return wrapped(*args,**kwargs)
            except (InstrumentationFailure,ScientificWorkerFailure):raise
            except Exception as exc:
                raise InstrumentationFailure(f'Stage metadata/accounting {name}: {exc!r}') from exc
        return checked


def context(worker):
    mp=worker.mp
    return {'context_identity':id(mp.mp),'dps':mp.mp.dps,'prec':mp.mp.prec,
            'prec_rounding':list(mp.mp._prec_rounding),'backend':str(mp.libmp.BACKEND)}


def execute_worker(worker,prefix,enabled=True,interval=10):
    """Common entry callable; all numerical calls remain the supplied originals.
    A production caller requires separate explicit approval and containment.
    """
    if not enabled:return original_call(worker.main)()
    factory=lambda path:CheckedStageObserver(path,interval=interval)
    with patch.object(v2,'StageObserver',factory),patch.object(worker,'main',original_call(worker.main)):
        return v2.run_observed(worker,prefix)


def classify(receipt,worker_result=None,started=True):
    if not started:return 'NOT_RUN'
    reason=receipt.get('power_watch',{}).get('abort_reason')
    if reason=='UNEXPECTED_SUSPEND_OR_SCHEDULER_GAP':return 'WATCHDOG_ABORT'
    if reason in ('AC_LOST_OR_CRITICAL_BATTERY',) or str(reason).startswith('POWER_CHECK_FAILED'):
        return 'AC_SAFETY_ABORT'
    if receipt.get('deadline_exceeded') or reason=='ABSOLUTE_DEADLINE':return 'TIMEOUT'
    status=(worker_result or {}).get('status')
    if status in ('INSTRUMENTATION_FAILURE','NUMERICAL_FAILURE'):return status
    if receipt.get('returncode')==0 and status=='SUCCESS':return 'SUCCESS'
    # Unknown execution failure must never be presented as a mathematical failure.
    return 'INSTRUMENTATION_FAILURE'


def dummy_entry(prefix,mode='success',enabled=True,iterations=500000,duration=0.,interval=.1):
    from scripts import full_support_c4_worker as worker
    before=context(worker);calls=[];outputs=StringIO();started=time.monotonic();cpu=time.process_time()
    saved={n:getattr(worker,n) for n in ('main','_row','_sectors','_lu_solve_matrix')};saved_eigen=worker.mp.eighe
    request={'probabilities_float64_hex':[float(.25).hex()],
      'prototypes_float64_hex':[[float(.5).hex(),float(.5).hex()]],
      'precision_ladder_decimal_digits':[1050,1250,1450]}
    def sector(p,z):
        calls.append(('sectors',worker.mp.mp.dps));dummy_work(iterations);return 'DUMMY_GRAM'
    def eigen(g):calls.append(('eigen',worker.mp.mp.dps));return 'DUMMY_EIGEN'
    def solve(a,b):calls.append(('solve',worker.mp.mp.dps));return 'DUMMY_SOLVE'
    def row(p,z,digits):
        with worker.mp.workdps(digits):
            if mode=='numerical_failure':raise FloatingPointError('INJECTED_DUMMY_SCIENTIFIC_FAILURE')
            worker._sectors(p,z);worker.mp.eighe('DUMMY_GRAM');worker._lu_solve_matrix('A','B')
        # Synthetic fixture only, quarantined and NEVER accepted as scientific C,w.
        return {'digits':digits,'resolved':True,'rank':256,'C':'1','w':'0','minimum_eigenvalue':'1'}
    result={'dummy_only':True,'original_AP_source_moments_executed':0,
            'fixture_outputs_are_non_scientific':True,'observer_enabled':enabled,'context_before':before,
            'worker_file':str(Path(worker.__file__).resolve()),'worker_main_path':'original main/JSON entry + replaced dummy numerical leaves'}
    try:
        with ExitStack() as stack:
            for name,function in (('_row',row),('_sectors',sector),('_lu_solve_matrix',solve)):
                stack.enter_context(patch.object(worker,name,function))
            stack.enter_context(patch.object(worker.mp,'eighe',eigen))
            stack.enter_context(patch.object(sys,'stdin',StringIO(json.dumps(request))))
            stack.enter_context(redirect_stdout(outputs))
            if mode=='instrumentation_failure':
                def bad_snapshot(self):raise InstrumentationFailure('INJECTED_DUMMY_OBSERVER_FAILURE')
                stack.enter_context(patch.object(CheckedStageObserver,'snapshot',bad_snapshot))
            if duration:
                main=worker.main
                def delayed():
                    until=time.monotonic()+duration
                    while time.monotonic()<until:dummy_work(20000)
                    return main()
                stack.enter_context(patch.object(worker,'main',delayed))
            execute_worker(worker,prefix,enabled=enabled,interval=interval)
        result.update(status='SUCCESS',worker_stdout=json.loads(outputs.getvalue()),calls=calls)
    except InstrumentationFailure as exc:
        result.update(status='INSTRUMENTATION_FAILURE',error=repr(exc),calls=calls)
    except ScientificWorkerFailure as exc:
        result.update(status='NUMERICAL_FAILURE',error=repr(exc),calls=calls)
    finally:
        result.update(context_after=context(worker),wall_seconds=time.monotonic()-started,
              process_cpu_seconds=time.process_time()-cpu,
              original_hooks_restored=all(getattr(worker,n) is f for n,f in saved.items()) and worker.mp.eighe is saved_eigen)
    assert result['context_before']==result['context_after']
    assert result['original_hooks_restored']
    atomic_json(str(prefix)+'_worker_result.json',result)
    return result


def in_windows_job():
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.GetCurrentProcess.restype=wintypes.HANDLE
    kernel.IsProcessInJob.argtypes=[wintypes.HANDLE,wintypes.HANDLE,ctypes.POINTER(wintypes.BOOL)]
    kernel.IsProcessInJob.restype=wintypes.BOOL
    flag=wintypes.BOOL()
    if not kernel.IsProcessInJob(kernel.GetCurrentProcess(),None,ctypes.byref(flag)):
        raise OSError(ctypes.get_last_error(),'Cannot verify Job containment')
    return bool(flag.value)


def production_gate(authorization,prefix,request_text,contained):
    """No authorization file is created by recovery; this path remains NOT_RUN."""
    expected='db17b04f09fb7555f681236d204ce658a95c1f413a3ab1b48cc2fefae322ae59'
    if not contained:raise PermissionError('NOT_RUN: Native Job containment required')
    if authorization.get('status')!='EXPLICITLY_APPROVED_CONTROLLED_PROBE_A_OBSERVER_V2':
        raise PermissionError('NOT_RUN: Fresh explicit probeA observer-v2 authority required')
    if authorization.get('source_cache_key')!=expected or Path(prefix).name!=expected:
        raise PermissionError('NOT_RUN: Exact authorized cache key mismatch')
    if authorization.get('pair_hex')!=[float(.165).hex(),float(5.49375).hex()]:
        raise PermissionError('NOT_RUN: Exact binary64 pair mismatch')
    if time.monotonic()>=authorization['deadline_monotonic'] or datetime.now(timezone.utc)>=datetime.fromisoformat(authorization['deadline_utc']):
        raise PermissionError('NOT_RUN: Authorized absolute deadline expired')
    request=json.loads(request_text)
    digest=hashlib.sha256(json.dumps(request,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    if digest!=authorization.get('request_sha256') or request['precision_ladder_decimal_digits']!=[1050,1250,1450]:
        raise PermissionError('NOT_RUN: Input request/prospectively frozen precision mismatch')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--dummy-mode',choices=('success','instrumentation_failure','numerical_failure'))
    group.add_argument('--approved-ap',action='store_true')
    parser.add_argument('--authorization',type=Path)
    parser.add_argument('--prefix',type=Path,required=True);parser.add_argument('--duration',type=float,default=.4)
    parser.add_argument('--without-observer',action='store_true');parser.add_argument('--spawn-child',action='store_true')
    parser.add_argument('--marker',default='observer_v2_dummy')
    args=parser.parse_args()
    if args.approved_ap:
        if args.authorization is None:parser.error('Fresh explicit authorization file required')
        authorization=json.loads(args.authorization.read_text(encoding='utf-8'))
        request_text=sys.stdin.read()
        production_gate(authorization,args.prefix,request_text,in_windows_job())
        from scripts import full_support_c4_worker as worker
        try:
            with patch.object(sys,'stdin',StringIO(request_text)):
                execute_worker(worker,args.prefix,enabled=not args.without_observer)
            status='SUCCESS';error=None;code=0
        except InstrumentationFailure as exc:status='INSTRUMENTATION_FAILURE';error=repr(exc);code=70
        except ScientificWorkerFailure as exc:status='NUMERICAL_FAILURE';error=repr(exc);code=71
        atomic_json(str(args.prefix)+'_worker_result.json',{'status':status,'error':error,'dummy_only':False})
        return code
    if args.spawn_child:
        child=subprocess.Popen([sys.executable,'-B','-c','import time; time.sleep(60)',args.marker],
                  creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        print('DUMMY_CHILD_PID='+str(child.pid),flush=True)
    result=dummy_entry(args.prefix,args.dummy_mode,not args.without_observer,duration=args.duration)
    result['native_job_contains_worker']=in_windows_job()
    atomic_json(str(args.prefix)+'_worker_result.json',result)
    print(json.dumps({k:result[k] for k in ('status','dummy_only','original_AP_source_moments_executed','wall_seconds')}),flush=True)
    return {'SUCCESS':0,'INSTRUMENTATION_FAILURE':70,'NUMERICAL_FAILURE':71}[result['status']]


if __name__=='__main__':raise SystemExit(main())
