"""Short-path binding around unchanged validated observer-v2 execution."""
import hashlib
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import observer_v2_recovery_entry as original
from scripts.overnight_source_observer import atomic_json

classify = original.classify


def main():
    manifest_path = Path(os.environ['AO_OBSERVER_PATH_MANIFEST'])
    raw = manifest_path.read_bytes()
    manifest = json.loads(raw)
    prefix = Path(sys.argv[sys.argv.index('--prefix') + 1]).resolve()
    mapping = manifest['prefixes'].get(str(prefix))
    if mapping is None:
        raise PermissionError('Observer prefix not in validated production path manifest')
    gate = original.production_gate

    def mapped_gate(authorization, supplied, request_text, contained):
        if Path(supplied).resolve() != prefix or not mapping['AP_candidate']:
            raise PermissionError('Exact production prefix binding mismatch')
        if authorization['path_manifest_sha256'] != hashlib.sha256(raw).hexdigest():
            raise PermissionError('Changed production path manifest')
        if mapping['source_cache_key'] != authorization['source_cache_key']:
            raise PermissionError('Changed scientific source identity')
        # Original gate still verifies exact key, binary64, request, precision,
        # both deadlines, explicit authority and native Job containment.
        gate(authorization, Path(mapping['source_cache_key']), request_text, contained)

    try:
        with patch.object(original, 'production_gate', mapped_gate):
            return original.main()
    except BaseException as exc:
        # Separately preflighted fallback survives a result-sidecar exception.
        atomic_json(Path(manifest['fallback']), {
            'status': 'INSTRUMENTATION_FAILURE', 'error': repr(exc),
            'production_AP_flag': '--approved-ap' in sys.argv,
            'original_precision_or_scientific_method_changed': False})
        print('INSTRUMENTATION_FAILURE: ' + repr(exc), file=sys.stderr, flush=True)
        return 70


if __name__ == '__main__':
    raise SystemExit(main())
