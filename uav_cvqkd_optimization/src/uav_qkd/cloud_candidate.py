"""Explicitly pending LOS-blockage candidate and rigid-cloud reference windows."""
import numpy as np
from .blockage import BlockageModel
from .cloud_channel import CloudPolicy
from .hap_uav_channel import _finite


def build_binary_los_blockage(config, field, hap, uav_altitude_m):
    """Select only after BOTH mode and threshold approval; reuse the LOS model."""
    if config.get('mode') != 'binary_los_blockage':
        raise ValueError('Expected binary_los_blockage candidate mode')
    if config.get('author_approved') is not True or config.get('threshold_approved') is not True or not config.get('approval_provenance'):
        raise ValueError('Cloud mode and threshold must both be explicitly approved with provenance')
    if not config.get('realization_provenance'):
        raise ValueError('The supplied cloud realization needs explicit provenance')
    if (not np.array_equal(config.get('velocity_m_s'), field.velocity)
            or any(c.velocity is not None and not np.array_equal(c.velocity, field.velocity) for c in field.clusters)):
        raise ValueError('Cloud velocity must match the declared rigid realization')
    threshold = _finite(config.get('threshold_mg_m3'), 'cloud threshold mg/m3', minimum=0)
    bottom = _finite(config.get('layer_bottom_m'), 'cloud layer bottom m')
    top = _finite(config.get('layer_top_m'), 'cloud layer top m')
    spacing = _finite(config.get('sample_spacing_m'), 'LOS sample spacing m', minimum=0)
    if threshold <= 0 or spacing <= 0 or top <= bottom:
        raise ValueError('Positive threshold/LOS spacing and cloud thickness are required')
    model = BlockageModel(field, threshold, hap, uav_altitude_m, mode='layer',
                          layer_bottom_m=bottom, layer_top_m=top, sample_spacing_m=spacing)
    # Explicit policy mapping: complete opaque LOS blockage is the existing erasure.
    return model, CloudPolicy('binary_erasure', True, config['approval_provenance'])


def cloud_reference_windows(field, times=(0., 300., 1000.), *, threshold=None):
    """Fixed 2km region at physical time t maps to q_ref=q-v*t at reference t=0.

    Evaluate the analytic Gaussian field at exact 50x50 cell centers. Binary
    panels threshold those SAME values; no nearest-cell shift or new realization.
    """
    if any(c.velocity is not None and not np.array_equal(c.velocity, field.velocity) for c in field.clusters):
        raise ValueError('A single static-reference shift requires rigid common cloud velocity')
    if threshold is not None and _finite(threshold, 'CLWC threshold', minimum=0) <= 0:
        raise ValueError('An explicit positive CLWC threshold is required')
    x = (np.arange(50)+.5)*40.
    X, Y = np.meshgrid(x, x)
    local = np.stack([X,Y],axis=-1)
    result = []
    for t in times:
        t = _finite(t, 'observation time s', minimum=0)
        shift = -np.asarray(field.velocity)*t
        reference = local+shift
        values = field.evaluate(reference,0.)
        result.append(dict(time_s=t, bounds_m=[float(shift[0]),float(shift[0]+2000),float(shift[1]),float(shift[1]+2000)],
                           cell_m=[40.,40.], reference_points_m=reference, clwc_mg_m3=values,
                           blocked=None if threshold is None else values>=threshold))
    return result
