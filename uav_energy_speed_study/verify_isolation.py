"""Record or verify the bytes and timestamps outside this experiment."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent


def snapshot():
    files = {}
    directories = []
    for folder, dirs, names in os.walk(ROOT):
        dirs[:] = sorted(d for d in dirs if Path(folder, d) != BASE)
        directories.extend(Path(folder, d).relative_to(ROOT).as_posix() for d in dirs)
        for name in sorted(names):
            path = Path(folder, name)
            stat = path.stat()
            with path.open('rb') as stream:
                digest = hashlib.file_digest(stream, 'sha256').hexdigest()
            files[path.relative_to(ROOT).as_posix()] = {
                'bytes': stat.st_size, 'mtime_ns': stat.st_mtime_ns, 'sha256': digest,
            }
    return {'files': files, 'directories': sorted(directories)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['record', 'verify'])
    action = parser.parse_args().action
    output = BASE / 'results'
    output.mkdir(exist_ok=True)
    baseline = output / 'outside_baseline.json'
    current = snapshot()
    if action == 'record':
        env = dict(os.environ, GIT_OPTIONAL_LOCKS='0')
        current['git'] = {
            key: subprocess.check_output(['git', '--no-optional-locks', *args], cwd=ROOT,
                                         env=env, text=True).strip()
            for key, args in {
                'branch': ['branch', '--show-current'], 'commit': ['rev-parse', 'HEAD'],
                'tracked_status': ['status', '--porcelain', '--untracked-files=no'],
            }.items()
        }
        with baseline.open('x', encoding='utf-8') as stream:
            json.dump(current, stream, indent=2)
        print(f"Recorded {len(current['files'])} outside files, including .git and .venv.")
        return
    original = json.loads(baseline.read_text(encoding='utf-8'))
    before, after = original['files'], current['files']
    report = {
        'experiment_folder': str(BASE),
        'files_checked': len(before),
        'bytes_checked': sum(row['bytes'] for row in before.values()),
        'added_files': sorted(after.keys() - before.keys()),
        'removed_files': sorted(before.keys() - after.keys()),
        'changed_files': sorted(k for k in before.keys() & after.keys() if before[k] != after[k]),
        'added_directories': sorted(set(current['directories']) - set(original['directories'])),
        'removed_directories': sorted(set(original['directories']) - set(current['directories'])),
        'baseline_sha256': hashlib.sha256(baseline.read_bytes()).hexdigest(),
    }
    report['status'] = ('CURRENTLY_VERIFIED_PASS' if not any(report[k] for k in
                        ('added_files', 'removed_files', 'changed_files',
                         'added_directories', 'removed_directories')) else 'FAILED')
    (output / 'isolation_check.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    if report['status'] != 'CURRENTLY_VERIFIED_PASS':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
