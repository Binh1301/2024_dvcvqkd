"""Execution-only profiling: owner-thread snapshots or low-overhead stage clocks."""
import argparse
from contextlib import contextmanager
import cProfile
from datetime import datetime,timezone
from functools import wraps
import json
import os
from pathlib import Path
import pstats
import statistics
import threading
import time


def atomic_json(path,data):
    path=Path(path);temporary=path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    temporary.replace(path)


class OwnerProfiler:
    """Only the profiled thread dumps, immediately reenables; totals never summed."""
    def __init__(self,prefix):
        self.prefix=Path(prefix);self.profiler=cProfile.Profile();self.snapshots=[]
        self.owner=threading.get_ident();self.start=time.monotonic();self.cpu=time.process_time()
    def __enter__(self):
        self.profiler.enable();return self
    def snapshot(self,final=False):
        assert self.owner==threading.get_ident()
        self.profiler.dump_stats(str(self.prefix)+'.prof')
        stats=pstats.Stats(str(self.prefix)+'.prof')
        previous=self.snapshots[-1]['cumulative_profile_self_seconds'] if self.snapshots else 0
        record={'utc':datetime.now(timezone.utc).isoformat(),'wall_seconds':time.monotonic()-self.start,
                'process_cpu_seconds':time.process_time()-self.cpu,'cumulative_profile_self_seconds':stats.total_tt,
                'delta_profile_self_seconds':stats.total_tt-previous,'final':final,
                'scope':'Owner-thread cProfile; CPU process aggregate; cumulative snapshots are NOT summed'}
        self.snapshots.append(record)
        atomic_json(str(self.prefix)+'_snapshots.json',self.snapshots)
        if not final:self.profiler.enable()
    def __exit__(self,*args):
        self.snapshot(final=True)


class StageObserver:
    """No numeric operation changed. Persist cumulative/exclusive completed stages
    and explicitly OPEN intervals. A forcibly killed stage is never called complete.
    """
    def __init__(self,prefix,interval=10):
        self.prefix=Path(prefix);self.interval=interval;self.lock=threading.RLock()
        self.start=time.monotonic();self.cpu=time.process_time();self.stack=[];self.completed=[]
        self.snapshots=0;self.stop=threading.Event();self.error=None
        self.instrumentation_cpu=0.;self.instrumentation_wall=0.
        self.owner=threading.get_ident();self.finished=False
    def snapshot(self):
        wall,cpu=time.monotonic(),time.process_time()
        with self.lock:
            self.snapshots+=1
            data={'mode':'LIGHTWEIGHT_EXECUTION_STAGE_TIMING','utc':datetime.now(timezone.utc).isoformat(),
                  'pid':os.getpid(),'owner_thread':self.owner,'wall_seconds':wall-self.start,
                  'process_cpu_seconds':cpu-self.cpu,'snapshot_count':self.snapshots,'finished':self.finished,
                  'open_stages':[{k:f[k] for k in ('name','digits','wall_start','cpu_start')} for f in self.stack],
                  'completed_stages':list(self.completed),'observer_error':self.error,
                  'snapshot_CPU_seconds_measured':self.instrumentation_cpu,
                  'snapshot_wall_seconds_measured':self.instrumentation_wall,
                  'scope':'AP process CPU includes its observer; completed stage exclusive times exclude nested stage times; snapshots cumulative, not added'}
        atomic_json(str(self.prefix)+'_stage_snapshot.json',data)
        # One append-only heartbeat remains readable after timeout even if last JSON incomplete.
        with Path(str(self.prefix)+'_heartbeats.jsonl').open('a',encoding='utf-8') as log:
            log.write(json.dumps({k:data[k] for k in ('utc','pid','wall_seconds','process_cpu_seconds','snapshot_count','open_stages','finished')})+'\n')
        self.instrumentation_cpu+=time.process_time()-cpu
        self.instrumentation_wall+=time.monotonic()-wall
    def __enter__(self):
        self.snapshot()
        def watch():
            while not self.stop.wait(self.interval):
                try:self.snapshot()
                except BaseException as exc:
                    self.error=repr(exc);return
        self.thread=threading.Thread(target=watch,daemon=True);self.thread.start();return self
    def __exit__(self,*args):
        self.stop.set();self.thread.join(timeout=3)
        assert not self.thread.is_alive(),'Observer thread cleanup failed'
        self.finished=True;self.snapshot()
        if self.error:raise RuntimeError('Observer persistence failed: '+self.error)
    @contextmanager
    def stage(self,name,digits=None):
        assert self.owner==threading.get_ident()
        frame={'name':name,'digits':digits,'wall_start':time.monotonic()-self.start,
               'cpu_start':time.process_time()-self.cpu,'child_wall':0.,'child_cpu':0.}
        with self.lock:self.stack.append(frame)
        ok=False
        try:
            yield;ok=True
        finally:
            wall=time.monotonic()-self.start-frame['wall_start'];cpu=time.process_time()-self.cpu-frame['cpu_start']
            with self.lock:
                assert self.stack.pop() is frame
                if self.stack:
                    self.stack[-1]['child_wall']+=wall;self.stack[-1]['child_cpu']+=cpu
                self.completed.append({'name':name,'digits':digits,'wall_start':frame['wall_start'],
                  'cpu_start':frame['cpu_start'],'wall_seconds_inclusive':wall,'CPU_seconds_inclusive':cpu,
                  'wall_seconds_exclusive':max(0.,wall-frame['child_wall']),
                  'CPU_seconds_exclusive':max(0.,cpu-frame['child_cpu']),'completed_normally':ok})
    def wrap(self,function,name,digits_getter=None):
        @wraps(function)
        def observed(*args,**kwargs):
            digits=digits_getter(args,kwargs) if digits_getter else None
            with self.stage(name,digits):return function(*args,**kwargs)
        return observed


def dummy_work(count):
    value=0
    for i in range(count):value=(value+i)%123457
    return value


def benchmark():
    """Pure-Python dummy overhead, not a prediction for arbitrary-precision work."""
    plain,profiled,staged=[],[],[]
    import tempfile
    with tempfile.TemporaryDirectory() as directory:
        for _ in range(3):
            start=time.perf_counter();expected=dummy_work(500000);plain.append(time.perf_counter()-start)
            start=time.perf_counter()
            with OwnerProfiler(Path(directory)/'dummy') as profile:
                result=dummy_work(250000);profile.snapshot();dummy_work(250000)
            profiled.append(time.perf_counter()-start)
            start=time.perf_counter()
            with StageObserver(Path(directory)/'stage',interval=.05) as observer:
                result=observer.wrap(dummy_work,'dummy')(500000)
            staged.append(time.perf_counter()-start);assert result==expected
    p,c,s=map(statistics.median,(plain,profiled,staged))
    return {'plain_seconds':plain,'cProfile_seconds':profiled,'stage_seconds':staged,
            'cProfile_dummy_overhead_fraction':c/p-1,'stage_dummy_overhead_fraction':s/p-1,
            'real_AP_mode':'LIGHTWEIGHT_EXECUTION_STAGE_TIMING',
            'qualification':'Dummy overhead only. Full detailed cProfile is not used for long AP; no claimed full call-profile coverage.'}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--ap',action='store_true')
    parser.add_argument('--prefix',type=Path,required=True);parser.add_argument('--dummy',action='store_true')
    args=parser.parse_args()
    if args.dummy:
        with StageObserver(args.prefix,interval=.05) as observer:
            observer.wrap(dummy_work,'dummy')(1000000)
        return
    if not args.ap:parser.error('Explicit AP flag required')
    # ONLY this explicitly supervised CLI branch imports/invokes the original worker.
    import sys
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
    from scripts import full_support_c4_worker as worker
    originals={name:getattr(worker,name) for name in ('_row','_sectors','_lu_solve_matrix')}
    eigen=worker.mp.eighe
    with StageObserver(args.prefix) as observer:
        worker._row=observer.wrap(originals['_row'],'precision_row',lambda a,k:int(a[2]))
        worker._sectors=observer.wrap(originals['_sectors'],'Gram_sector_construction',lambda a,k:worker.mp.dps)
        worker._lu_solve_matrix=observer.wrap(originals['_lu_solve_matrix'],'multi_RHS_LU',lambda a,k:worker.mp.dps)
        worker.mp.eighe=observer.wrap(eigen,'Hermitian_eigensystem',lambda a,k:worker.mp.dps)
        try:
            with observer.stage('original_worker_main'):worker.main()
        finally:
            for name,function in originals.items():setattr(worker,name,function)
            worker.mp.eighe=eigen


if __name__=='__main__':main()
