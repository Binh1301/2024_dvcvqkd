"""Read-only historical effective-noise I/O audit; no Z/w, MI or Holevo calls."""
import hashlib
import json
from pathlib import Path
import numpy as np


def audit_lookup_noise(directory, requested_channel_noise=.0136):
    directory = Path(directory)
    parent = directory.parents[1]
    def read(path):
        return json.loads(Path(path).read_text(encoding='utf-8'))
    def sha(path):
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    manifest = read(directory/'final_manifest.json')['files']
    verified = {}
    def verify(path):
        name = path.relative_to(directory).as_posix()
        expected = manifest[name]
        actual = sha(path)
        if actual != expected:
            raise ValueError('Historical lookup seal mismatch: '+name)
        verified[str(path.resolve())] = actual
    for name in ('execution_physical_protocol.json','authorization.json','execution_identity.json','skr_map.csv','skr_map.npz','run.py'):
        verify(directory/name)
    protocol = read(directory/'execution_physical_protocol.json')
    authorization = read(directory/'authorization.json')
    if [protocol['xi_ch'],protocol['xi_det']] != [authorization['xi_ch'],authorization['xi_det']]:
        raise ValueError('Historical protocol and authorization noise disagree')
    identity = read(directory/'execution_identity.json')
    for name, expected in identity['producers'].items():
        path = parent/name
        if sha(path) != expected:
            raise ValueError('Historical producer binding mismatch: '+name)
        verified[str(path.resolve())] = expected
    inferred, old_residual, requested_residual = [], [], []
    contexts = sorted((directory/'contexts').glob('*.json'))
    if not contexts:
        raise ValueError('Historical lookup has no saved scalar contexts')
    for path in contexts:
        verify(path)
        context = read(path)
        if context['execution_identity_sha256'] != sha(directory/'execution_identity.json'):
            raise ValueError('Context execution identity mismatch')
        moments = context['moments']
        m1, mh, mass = moments['m1'], moments['mh'], moments['M0']
        for winner in context['winners'].values():
            noise = winner['N_effective']
            fading = (m1-mh**2)*winner['VA']
            actual = fading+protocol['xi_ch']*m1+protocol['xi_det']*mass
            requested = fading+requested_channel_noise*m1+protocol['xi_det']*mass
            if not np.isclose(noise,actual,rtol=1e-12,atol=1e-14):
                raise ValueError('Stored noise scalar differs from bound generator inputs')
            inferred.append((noise-fading-protocol['xi_det']*mass)/m1)
            old_residual.append(abs(noise-actual))
            requested_residual.append(abs(noise-requested))
    return dict(actual_channel_excess_noise_snu=protocol['xi_ch'],actual_detector_excess_noise_snu=protocol['xi_det'],
                requested_channel_excess_noise_snu=requested_channel_noise,context_count=len(contexts),stored_winner_checks=len(inferred),
                channel_noise_inferred_range=[min(inferred),max(inferred)],max_effective_noise_residual_old=max(old_residual),
                min_effective_noise_residual_requested=min(requested_residual),max_effective_noise_residual_requested=max(requested_residual),
                scope='Stored scalar N_effective I/O identity only; not SKR regeneration or Z/w validation',
                expression='N_effective=(m1-mh^2)*VA+xi_ch*m1+xi_det*M0',verified_inputs_and_producers=verified,
                new_skr_evaluations=0,source_evidence_promoted=False)
