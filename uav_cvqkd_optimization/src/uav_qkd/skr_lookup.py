"""Strict external SKR table interpolation; no CV-QKD formula or fitted figure."""
from pathlib import Path
import numpy as np
from scipy.interpolate import LinearNDInterpolator
from scipy.spatial import QhullError


def compare_lookup_setup(reference, protocol):
    """Compare the existing physical subset AND separately declared noise inputs."""
    from .phase4_audit import compare_lookup_reference
    from .hap_uav_channel import _finite
    report = compare_lookup_reference(reference, protocol)
    rows = []
    for name, key in [('channel_excess_noise_snu', 'xi_ch'), ('detector_excess_noise_snu', 'xi_det')]:
        target, old = reference.get(name), protocol.get(key)
        if target is not None:
            target = _finite(target, name+' target noise', minimum=0)
        if old is not None:
            old = _finite(old, name+' lookup noise', minimum=0)
        matches = None if target is None or old is None else bool(np.isclose(target, old, rtol=1e-12, atol=0))
        rows.append(dict(parameter=name, reference=target, lookup=old, unit='SNU', matches=matches))
    report['noise_comparison'] = rows
    report['noise_mismatches'] = [r['parameter'] for r in rows if r['matches'] is False]
    report['unresolved_noise_comparisons'] = [r['parameter'] for r in rows if r['matches'] is None]
    return report


def require_lookup_compatibility(reference, protocol):
    """Fail closed for a selected reference; subset matches are not admission.

    Legacy load without a selected reference remains a numeric loader only.
    No source/security evidence or paper_admissible flag is changed here.
    """
    report = compare_lookup_setup(reference, protocol)
    differences = report['physical_mismatches']+report['noise_mismatches']
    if not report['beta_matches']:
        differences.append('reconciliation_efficiency')
    if not report['normalization_matches']:
        differences.append('existing_module_normalization')
    if differences:
        raise ValueError('SKR lookup incompatible with selected reference: '+', '.join(differences))
    # shortcut: the existing protocol lacks a complete mission/context binding;
    # upgrade this gate only when geometry, noise, protocol and lineage are bound.
    raise ValueError('Lookup full compatibility not established: physical subset agreement cannot authorize reuse; complete geometry/noise/protocol evidence is required')


class SKRLookup:
    def __init__(self, points, rates, *, coordinate_units: str, rate_units: str):
        if coordinate_units != 'm' or rate_units != 'bits/use':
            raise ValueError('SKR units must explicitly be m and bits/use; no implicit rescaling')
        self.points, self.rates = np.asarray(points, float), np.asarray(rates, float)
        if self.points.ndim != 2 or self.points.shape[1] != 2 or self.rates.shape != (len(self.points),) or len(self.points) < 3 or not np.isfinite(self.points).all() or not np.isfinite(self.rates).all():
            raise ValueError('Lookup needs finite Nx2 coordinates and N rates, N>=3')
        if len(np.unique(self.points, axis=0)) != len(self.points):
            raise ValueError('Duplicate SKR coordinates are not allowed')
        try:
            self.interpolator = LinearNDInterpolator(self.points, self.rates, fill_value=np.nan)
        except QhullError as e:
            raise ValueError('SKR coordinates must span a two-dimensional domain') from e

    @classmethod
    def from_array(cls, rows, **units):
        rows = np.asarray(rows, float)
        if rows.ndim != 2 or rows.shape[1] != 3:
            raise ValueError('Array format must have columns x_m, y_m, skr_bits_per_use')
        return cls(rows[:, :2], rows[:, 2], **units)

    @classmethod
    def load(cls, path, *, reference=None, protocol=None, **units):
        if reference is not None or protocol is not None:
            if reference is None or protocol is None:
                raise ValueError('Selected-reference loading needs both reference and source protocol')
            require_lookup_compatibility(reference, protocol)
        path = Path(path)
        if not path.is_file():
            raise FileNotFoundError(f'Required external SKR table missing: {path}; no synthetic fallback in paper mode')
        if path.suffix == '.csv':
            rows = np.genfromtxt(path, delimiter=',', names=True, encoding='utf-8-sig')
            required = ['x_m', 'y_m', 'skr_bits_per_use']
            if not set(required) <= set(rows.dtype.names or []):
                raise ValueError('CSV requires x_m,y_m,skr_bits_per_use header')
            return cls.from_array(np.column_stack([np.atleast_1d(rows[n]) for n in required]), **units)
        if path.suffix == '.npy':
            return cls.from_array(np.load(path, allow_pickle=False), **units)
        if path.suffix == '.npz':
            with np.load(path, allow_pickle=False) as d:
                return cls(d['points'], d['rates'], **units)
        raise ValueError('Supported SKR formats: CSV, NPY (Nx3), NPZ (points,rates)')

    def __call__(self, positions):
        q = np.atleast_2d(np.asarray(positions, float))
        if q.ndim != 2 or q.shape[1] != 2 or not np.isfinite(q).all():
            raise ValueError('SKR query must have finite Nx2 coordinates')
        out = np.asarray(self.interpolator(q))
        if not np.isfinite(out).all():
            raise ValueError('SKR query outside lookup domain; extrapolation is disabled')
        return out
