"""Standalone, uncalibrated cloud attenuation; no QKD/channel imports.

Eq. (6) means the THREE branches printed in Ibrahim (2024), not the commonly
used five-branch Kim prescription. The missing V=6 point is assigned x=1.3.
These branches have real jumps: 'continuous' here means continuous-valued loss.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import numpy as np


def _positive(value, name, *, zero=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be finite numeric")
    if not math.isfinite(value) or (value < 0 if zero else value <= 0):
        raise ValueError(f"invalid {name}")
    return float(value)


def _array(value, name, *, nonnegative=False):
    a = np.asarray(value, dtype=np.float64)
    if not np.isfinite(a).all() or (nonnegative and np.any(a < 0)):
        raise ValueError(f"{name} must be finite" + (" and nonnegative" if nonnegative else ""))
    return a


@dataclass(frozen=True)
class AttenuationScenario:
    name: str
    l0_g_m3: float
    droplet_cm3: float
    thickness_km: float

    def __post_init__(self):
        if not isinstance(self.name, str) or not self.name or not self.name.replace('_', '').isalnum():
            raise ValueError("scenario name must be an alphanumeric identifier")
        _positive(self.l0_g_m3, "l0_g_m3")
        _positive(self.droplet_cm3, "droplet_cm3")
        _positive(self.thickness_km, "thickness_km")


def gaussian_to_clwc(latent, l0_g_m3, gamma0):
    """Assumed rectified-Gaussian LWC surrogate, g/m^3; no frame normalization."""
    g = _array(latent, "latent")
    scale = _positive(l0_g_m3, "l0_g_m3")
    offset = float(_array(gamma0, "gamma0").item())
    with np.errstate(over="ignore"):
        result = scale * np.maximum(g - offset, 0.0)
    return _array(result, "CLWC", nonnegative=True)


def visibility_km(clwc_g_m3, droplet_cm3):
    """Ibrahim Eq. (7). +inf is the explicit clear-air limiting sentinel only."""
    l = _array(clwc_g_m3, "CLWC", nonnegative=True)
    n = _positive(droplet_cm3, "droplet_cm3")
    v = np.full(l.shape, np.inf)
    positive = l > 0
    with np.errstate(over="ignore", under="ignore"):
        v[positive] = np.exp(math.log(1.002) - .6473*(np.log(l[positive])+math.log(n)))
    if np.any(~np.isfinite(v[positive])) or np.any(v[positive] <= 0):
        raise ValueError("positive-CLWC visibility is outside float64 range")
    return v


def kim_exponent(visibility):
    """Printed Eq. (6); completion at exactly 6 km uses the upper branch.

    V<6: .585*cbrt(V); 6<=V<=50: 1.3; V>50: 1.6.
    +inf accepted as the L=0 visibility limit. No smoothing at 6 or 50.
    """
    v = np.asarray(visibility, dtype=np.float64)
    if np.isnan(v).any() or np.any(v <= 0):
        raise ValueError("visibility must be positive; +inf allowed for clear air")
    return np.where(v < 6, .585*np.cbrt(v), np.where(v <= 50, 1.3, 1.6))


def specific_attenuation_db_km(clwc_g_m3, droplet_cm3, wavelength_nm=1550.0):
    """Literal Eqs. (5)-(7), with paper's dB/km convention and 3.91 factor."""
    l = _array(clwc_g_m3, "CLWC", nonnegative=True)
    wavelength = _positive(wavelength_nm, "wavelength_nm")
    v = visibility_km(l, droplet_cm3)
    result = np.zeros(l.shape)
    positive = l > 0
    # Evaluate only positive L: avoids inf*0 and makes L=0 exactly loss-free.
    with np.errstate(over="ignore", under="ignore"):
        result[positive] = np.exp(math.log(3.91)-np.log(v[positive])
                                  -kim_exponent(v[positive])*math.log(wavelength/550.0))
    return _array(result, "specific attenuation", nonnegative=True)


def path_attenuation_db(specific_db_km, thickness_km, zenith_deg=0.0):
    """Full-slab reference geometry only; actual intersection must be separate."""
    w = _array(specific_db_km, "specific attenuation", nonnegative=True)
    h = _positive(thickness_km, "thickness_km", zero=True)
    z = float(_array(zenith_deg, "zenith_deg").item())
    if not 0 <= z < 90:
        raise ValueError("zenith_deg must be in [0,90); use segment geometry otherwise")
    with np.errstate(over="ignore"):
        a = w * h / math.cos(math.radians(z))
    return _array(a, "path attenuation", nonnegative=True)


def transmittance_from_db(attenuation_db):
    a = _array(attenuation_db, "attenuation", nonnegative=True)
    with np.errstate(under="ignore"):
        t = np.power(10.0, -a/10.0)
    if np.any(t <= 0):
        raise ValueError("transmittance underflows float64; retain dB/logT, do not clip")
    return t


def combine_clear_cloud(clear_transmittance, cloud_transmittance):
    """Optional pure multiplication interface; never calls the QKD model."""
    a = _array(clear_transmittance, "clear transmittance", nonnegative=True)
    b = _array(cloud_transmittance, "cloud transmittance", nonnegative=True)
    if np.any(a > 1) or np.any(b > 1) or np.any(b <= 0):
        raise ValueError("require clear in [0,1] and cloud in (0,1]")
    result = a*b
    if np.any((a > 0) & (result == 0)):
        raise ValueError("total transmittance underflows; no clipping applied")
    return result


def layer_intersection(uav_xyz_m, hap_xyz_m, base_m, top_m):
    """Exact finite straight segment/slab overlap, including partial penetration.

    The horizontal midpoint is a representative cloud coordinate, not UAV xy.
    A horizontal segment on a slab boundary has zero interior overlap.
    """
    p = _array(uav_xyz_m, "UAV point")
    q = _array(hap_xyz_m, "HAP point")
    if p.shape != (3,) or q.shape != (3,):
        raise ValueError("points must be xyz triples in metres")
    base, top = float(_array(base_m, "base").item()), float(_array(top_m, "top").item())
    if not base < top:
        raise ValueError("cloud top must exceed base")
    d = q-p
    distance = float(np.linalg.norm(d))
    if not math.isfinite(distance) or distance == 0:
        raise ValueError("distinct finite endpoints required")
    zenith = math.degrees(math.acos(min(1.0, abs(float(d[2]))/distance)))
    if d[2] == 0:
        lo, hi = (0.0, 1.0) if base < p[2] < top else (0.0, 0.0)
    else:
        a, b = sorted(((base-p[2])/d[2], (top-p[2])/d[2]))
        lo, hi = max(0.0, float(a)), min(1.0, float(b))
    intersects = hi > lo
    return {"intersects": intersects, "path_length_km": distance*(hi-lo)/1000 if intersects else 0.0,
            "zenith_deg": zenith, "segment_fraction": [lo, hi] if intersects else [],
            "representative_xyz_m": (p+(lo+hi)/2*d).tolist() if intersects else None,
            "horizontal_travel_in_layer_m": float(np.linalg.norm(d[:2]))*(hi-lo) if intersects else 0.0}


def sample_clwc(clwc_yx, x_m, y_m, xy_m):
    """Bilinear interpolation within saved cell centres; no wrapping/extrapolation."""
    l = _array(clwc_yx, "CLWC map", nonnegative=True)
    x, y = _array(x_m, "x_m"), _array(y_m, "y_m")
    xy = _array(xy_m, "cloud xy")
    if x.ndim != 1 or y.ndim != 1 or len(x) < 2 or len(y) < 2 or l.shape != (len(y), len(x)) or xy.shape != (2,):
        raise ValueError("incompatible map/coordinate shapes")
    if np.any(np.diff(x) <= 0) or np.any(np.diff(y) <= 0):
        raise ValueError("coordinate axes must be strictly increasing")
    if not (x[0] <= xy[0] <= x[-1] and y[0] <= xy[1] <= y[-1]):
        raise ValueError("cloud intersection outside saved map centres; no modulo sampling")
    ix = min(int(np.searchsorted(x, xy[0], side="right"))-1, len(x)-2)
    iy = min(int(np.searchsorted(y, xy[1], side="right"))-1, len(y)-2)
    fx, fy = (xy[0]-x[ix])/(x[ix+1]-x[ix]), (xy[1]-y[iy])/(y[iy+1]-y[iy])
    return float((1-fy)*((1-fx)*l[iy,ix]+fx*l[iy,ix+1]) + fy*((1-fx)*l[iy+1,ix]+fx*l[iy+1,ix+1]))


def representative_link_attenuation(clwc_yx, x_m, y_m, uav_xyz_m, hap_xyz_m,
                                    base_m, top_m, droplet_cm3, wavelength_nm=1550.0):
    """Slab midpoint approximation for horizontally varying L, exact segment length.

    For appreciable horizontal variation along the in-cloud path, replace this
    explicit approximation with a path integral before physical integration.
    """
    geometry = layer_intersection(uav_xyz_m, hap_xyz_m, base_m, top_m)
    if geometry["intersects"]:
        l = sample_clwc(clwc_yx, x_m, y_m, geometry["representative_xyz_m"][:2])
        a = float(specific_attenuation_db_km(l, droplet_cm3, wavelength_nm))*geometry["path_length_km"]
    else:
        l, a = 0.0, 0.0
    return {"attenuation_db": a, "transmittance": float(transmittance_from_db(a)),
            "representative_clwc_g_m3": l, "geometry": geometry,
            "approximation": "CLWC at slab-segment midpoint; no horizontal path integration"}


def pooled_pearson(a, b):
    """Empirical pairwise Pearson r; no iid or Gaussian-covariance claim."""
    a, b = np.asarray(a, dtype=float).ravel(), np.asarray(b, dtype=float).ravel()
    ac, bc = a-a.mean(), b-b.mean()
    denominator = math.sqrt(float(ac@ac)*float(bc@bc))
    if denominator == 0:
        raise ValueError("Pearson correlation undefined for constant samples")
    return float(ac@bc/denominator)
