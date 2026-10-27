"""Isolated v43 components; a blocked probability law never produces an SKR."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import mpmath as mp
import numpy as np

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
POLICY = "manuscript_eq14_direct"
LAW = "manuscript43_Eq10_retained_0_to_1"
BASELINE = dict(h_hap_km=20., h_uav_km=1., h_atm_km=20., Dr_m=.30,
                wavelength_m=1.55e-6, divergence_full_urad=35., jitter_urad=1.561,
                sigma_h_m=.10, rho_x_m=0., rho_y_m=0., F0="Infinity", tau_zen=.92,
                Cn2_ground=1e-14, wind_m_s=21., FOV_half_rad=.00625,
                sigma_AoA_rad=.0015, AO="OFF", phase_noise="OFF")
_HELPERS = None


class ModelBlocked(ValueError):
    """An unresolved mathematical prerequisite, not a zero key rate."""


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def validate_protocol(protocol):
    if protocol["correlation_policy"] != POLICY or protocol["channel_law"] != LAW:
        raise ValueError("Incompatible channel or correlation policy")
    if protocol["physical"] != BASELINE:
        raise ValueError("This isolated adapter supports only the declared physical baseline")
    if (protocol["xi_ch"], protocol["xi_det"], protocol["beta"],
        protocol["measurement"]) != (.0186, .005, .95, "homodyne_1D_Gaussian_effective"):
        raise ValueError("Noise/receiver protocol mismatch")
    for name, expected in protocol["dependency_sha256"].items():
        if sha(ROOT / name) != expected:
            raise ValueError("Dependency changed: " + name)
    if sha(ROOT / protocol["reference_path"]) != protocol["reference_sha256"]:
        raise ValueError("Canonical manuscript identity changed")


def helpers():
    global _HELPERS
    if _HELPERS is None:
        sys.path.insert(0, str(ROOT))
        path = ROOT / "results/manuscript43_homodyne_audit_20261023/audit_model.py"
        spec = importlib.util.spec_from_file_location("_eq14_preserved_helpers", path)
        _HELPERS = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_HELPERS)
    return _HELPERS


def number(value, name, nonnegative=True):
    value = mp.mpf(value)
    if not mp.isfinite(value) or (nonnegative and value < 0):
        raise ValueError("Invalid " + name)
    return value


def correlation_eq14(eta_f, xi_f, C, w):
    """Eq. (14), with no selectable Z, interval, endpoint, or projection."""
    t, xi, c, ww = [number(x, n) for x, n in
                    [(eta_f, "eta_f"), (xi_f, "xi_f"), (C, "C"), (w, "w")]]
    if t > 1:
        raise ValueError("eta_f exceeds one")
    return 2 * mp.sqrt(t) * c - mp.sqrt(2 * t * xi * ww)


def entropy_g(x):
    x = number(x, "entropy argument")
    if x == 0:
        return mp.mpf(0)  # The continuous value of x*log(x) at zero.
    return (x + 1) * mp.log(x + 1, 2) - x * mp.log(x, 2)


def components(vmod, eta_f, xi_f, C, w, *, digits=80):
    """Eqs. (13),(14) for component tests; vmod is explicit, never inferred from VA."""
    with mp.workdps(digits):
        vm, t, xi = number(vmod, "Vmod"), number(eta_f, "eta_f"), number(xi_f, "xi_f")
        if not 0 < t <= 1:
            raise ValueError("Positive effective transmittance required")
        z = correlation_eq14(t, xi, C, w)
        V, W = 1 + vm, 1 + t * vm + t * xi
        if V * W - z*z <= 0:
            raise ValueError("Non-positive covariance")
        delta = V*V + W*W - 2*z*z
        determinant = (V*W - z*z)**2
        discriminant = delta*delta - 4*determinant
        if discriminant < 0:
            raise ValueError("Negative Eq13 discriminant; no repair")
        roots = [(delta + mp.sqrt(discriminant))/2,
                 (delta - mp.sqrt(discriminant))/2, V*(V-z*z/W)]
        if min(roots) < 1:
            raise ValueError("Nonphysical symplectic spectrum; no repair")
        nu1, nu2, nu3 = [mp.sqrt(x) for x in roots]
        chi = entropy_g((nu1-1)/2) + entropy_g((nu2-1)/2) - entropy_g((nu3-1)/2)
        if not mp.isfinite(chi) or chi < 0:
            raise ValueError("Invalid Holevo value; no clipping")
        values = dict(V=V, W=W, Z_manuscript_eq14=z, Delta=delta, D=determinant,
                      nu_1=nu1, nu_2=nu2, nu_3=nu3, chi_BE=chi)
        return {**{k: float(x) for k, x in values.items()},
                "decimal": {k: mp.nstr(x, digits-10) for k, x in values.items()},
                "digits": digits, "correlation_policy": POLICY}


def moment_check(ch, xi_ch, xi_det, digits):
    """Closed Eqs. (18)-(20); survival form checks the same Eq10 tail at rho=0."""
    a = helpers()
    with mp.workdps(digits):
        c = a.raw_coefficients(ch, 0.)
        B, d, c3, mu, lc = [c[k] for k in ["B", "d", "C3", "mu", "logC1"]]
        x1 = -mp.log(B) + mu

        def Q(x):
            return (mp.exp(x*x1-x*mu)*mp.erfc(c3*x1)
                    + mp.exp(x*x/(4*c3*c3)-x*mu)*mp.erfc(x/(2*c3)-c3*x1))/2

        active = {q: c["P1"]*B**q*d*mp.exp(lc)/(d+q)*Q(d+q)
                  for q in [mp.mpf(0), mp.mpf(".5"), mp.mpf(1)]}
        mass = c["P0"] + active[0]
        v = c["v"]
        z = (-mp.log(B) + v/2)/mp.sqrt(v)
        survival = lambda x: mp.erfc(x/mp.sqrt(2))/2
        tail = c["P1"]*(survival(z)
                - mp.exp(-d*mp.log(B)+d*v/2+d*d*v/2)*survival(z+d*mp.sqrt(v)))
        if tail <= 0:
            raise ValueError("Positive raw Eq10 tail was not resolved")
        mean_noise = number(xi_ch, "xi_ch")*active[1] + number(xi_det, "xi_det")*mass
        values = dict(M0=mass, active_mass=active[0], mh=active[mp.mpf(".5")],
                      m1=active[1], P0=c["P0"], P1=c["P1"], stable_tail=tail,
                      one_minus_M0=1-mass, closure_residual=mass+tail-1,
                      mean_eta_xi=mean_noise, atom_noise=number(xi_det, "xi_det")*c["P0"])
        return {"digits": digits, **{k: float(x) for k, x in values.items()},
                "decimal": {k: mp.nstr(x, digits-10) for k, x in values.items()}}


def channel_context(zenith_deg, protocol):
    validate_protocol(protocol)
    if not np.isfinite(zenith_deg) or not 0 <= zenith_deg <= 60:
        raise ValueError("Zenith outside [0,60]")
    a = helpers()
    ch = a.legacy.optical(.30, 35., zenith_deg, .10, mp.mpf("1.561")/mp.mpf("15.61"))
    raw = a.raw_pdf_moments(ch, 0.)
    precision = [moment_check(ch, .0186, .005, n) for n in protocol["numerical"]["digits"]]
    hi = precision[-1]
    moment_residual = max(abs(x["residual"]) for x in raw["direct"].values())
    direct_noise = (.0186*raw["direct"][1.]["value"]
                    + .005*(raw["P0"]+raw["direct"][0.]["value"]))
    noise_residual = abs(hi["mean_eta_xi"]-direct_noise)
    with mp.workdps(120):
        precision_residual = max(float(abs(mp.mpf(precision[0]["decimal"][k])-
                                          mp.mpf(hi["decimal"][k])))
                                 for k in ["M0", "m1", "mh", "mean_eta_xi", "stable_tail"])
    # Strict positivity of Eq10 on eta>1 is a support failure even below a numerical tolerance.
    nonzero_tail = all(mp.mpf(ch[k]) > 0 for k in ["B", "d", "v", "P1"])
    if not nonzero_tail:
        raise ModelBlocked("Degenerate law requires separate mathematical review")
    numerical_pass = (moment_residual <= 2e-10 and noise_residual <= 2e-10 and precision_residual <= 2e-11
                      and abs(hi["stable_tail"]-raw["upper_tail_quadrature"]) <= 2e-12
                      and abs(hi["closure_residual"]) <= 1e-70)
    return dict(zenith_deg=zenith_deg, channel=ch, moments=raw,
                precision=precision, moment_residual=moment_residual,
                direct_mean_eta_xi=direct_noise, noise_moment_residual=noise_residual,
                precision_residual=precision_residual,
                numerical_status="CURRENTLY_VERIFIED_PASS" if numerical_pass else "FAILED",
                mathematical_status="BLOCKED_PDF_SUPPORT_NORMALIZATION",
                law_mathematically_valid=False, channel_law=LAW,
                support_argument="rho=0; B,d,v,P1>0 => Eq10 density positive for eta>1; retained law loses mass",
                zero_atom_noise_extension="limit_eta_xi_equals_xi_det",
                renormalized=False, clipped=False)


def evaluate(source, context, protocol):
    validate_protocol(protocol)
    if context.get("law_mathematically_valid") is not True or context.get("channel_law") != LAW:
        raise ModelBlocked("Eq10 probability-law gate has not passed")
    if protocol["VA_to_Vmod_mapping"] != "AUTHOR_CONFIRMED_VA_EQUALS_VMOD":
        raise ModelBlocked("VA to printed Vmod mapping unresolved")
    if source.get("convergence_status") != "CURRENTLY_VERIFIED_PASS":
        raise ModelBlocked("Exact-source convergence receipt unavailable")
    p, alpha = helpers().validate_source(source)
    m = context["moments"]
    t = m["mh"]**2
    if not 0 < t <= m["m1"] <= 1:
        raise ValueError("Invalid effective moments")
    noise = (m["m1"]-t)*source["VA"] + protocol["xi_ch"]*m["m1"] + protocol["xi_det"]*m["M0"]
    h = components(source["VA"], t, noise/t, source["C"], source["w"], digits=110)
    mi = helpers().homodyne_mi(p, alpha, t, 1+noise, order=128)
    return {**h, "eta_f": t, "xi_f": noise/t, "N_effective": noise,
            "I_AB": mi, "beta_I_AB": protocol["beta"]*mi,
            "K_raw": protocol["beta"]*mi-h["chi_BE"], "source_hash": source["ensemble_hash"],
            "security_valid": False}
