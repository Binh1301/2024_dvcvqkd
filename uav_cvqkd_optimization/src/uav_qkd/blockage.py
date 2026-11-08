"""Sample LOS inside a declared cloud slab, never silently at the UAV endpoint."""
import numpy as np
from .cloud_model import CloudField


class BlockageModel:
    def __init__(self, field: CloudField, threshold: float, hap, uav_altitude_m: float,
                 *, mode: str, sample_spacing_m: float, layer_bottom_m=None, layer_top_m=None):
        if not np.isfinite(threshold) or threshold <= 0 or not np.isfinite(sample_spacing_m) or sample_spacing_m <= 0:
            raise ValueError('CLWC threshold and LOS sample spacing must be positive and finite')
        if np.shape(hap) != (3,) or not np.isfinite(hap).all() or not np.isfinite(uav_altitude_m):
            raise ValueError('HAP must be a finite 3D position and UAV altitude finite')
        if mode not in ('layer', 'projected_path_2d'):
            raise ValueError('Blockage mode must be layer or explicitly projected_path_2d')
        if mode == 'layer' and (layer_bottom_m is None or layer_top_m is None or not np.isfinite([layer_bottom_m, layer_top_m]).all() or layer_bottom_m > layer_top_m):
            raise ValueError('layer mode requires finite layer_bottom_m <= layer_top_m')
        self.field, self.threshold = field, threshold
        self.hap, self.uav_altitude_m = np.asarray(hap, float), uav_altitude_m
        self.mode, self.spacing = mode, sample_spacing_m
        self.bottom, self.top = layer_bottom_m, layer_top_m

    def projected_segment(self, position) -> np.ndarray | None:
        q = np.asarray(position, float)
        if q.shape != (2,) or not np.isfinite(q).all():
            raise ValueError('UAV horizontal position must be a finite pair')
        lo, hi = 0., 1.
        if self.mode == 'layer':
            dz = self.uav_altitude_m - self.hap[2]
            if dz == 0:
                if not self.bottom <= self.hap[2] <= self.top:
                    return None
            else:
                a, b = sorted(((self.bottom-self.hap[2])/dz, (self.top-self.hap[2])/dz))
                lo, hi = max(0., a), min(1., b)
                if lo > hi:
                    return None
        return np.array([self.hap[:2]+s*(q-self.hap[:2]) for s in (lo, hi)])

    def blocked(self, position, time: float) -> bool:
        segment = self.projected_segment(position)
        if segment is None:
            return False
        count = max(2, int(np.ceil(np.linalg.norm(segment[1]-segment[0])/self.spacing))+1)
        points = np.linspace(segment[0], segment[1], count)
        return bool(np.any(self.field.evaluate(points, time) >= self.threshold))

    def sequence(self, positions, slots: int, dt: float) -> np.ndarray:
        return np.array([[not self.blocked(q, k*dt) for q in positions]
                         for k in range(1, slots+1)], dtype=np.int8)
