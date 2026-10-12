"""Versioned observer-only correction; failed executed producer remains untouched."""
import argparse
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.overnight_source_observer import StageObserver


def run_observed(worker,prefix):
    originals={name:getattr(worker,name) for name in ('_row','_sectors','_lu_solve_matrix')}
    eigen=worker.mp.eighe
    # mpmath is a MODULE; its precision context lives at module.mp, not module.dps.
    def digits(args,kwargs):return int(worker.mp.mp.dps)
    with StageObserver(prefix) as observer:
        worker._row=observer.wrap(originals['_row'],'precision_row',lambda a,k:int(a[2]))
        worker._sectors=observer.wrap(originals['_sectors'],'Gram_sector_construction',digits)
        worker._lu_solve_matrix=observer.wrap(originals['_lu_solve_matrix'],'multi_RHS_LU',digits)
        worker.mp.eighe=observer.wrap(eigen,'Hermitian_eigensystem',digits)
        try:
            with observer.stage('original_worker_main'):return worker.main()
        finally:
            for name,function in originals.items():setattr(worker,name,function)
            worker.mp.eighe=eigen


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--ap',action='store_true')
    parser.add_argument('--prefix',type=Path,required=True);args=parser.parse_args()
    if not args.ap:parser.error('Explicit AP authorization/flag required')
    from scripts import full_support_c4_worker
    return run_observed(full_support_c4_worker,args.prefix)


if __name__=='__main__':main()
