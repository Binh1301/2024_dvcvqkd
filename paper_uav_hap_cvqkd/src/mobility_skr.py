"""Existing exact-source Gaussian SKR connected to binary cloud channel states.

No source oracle, interpolation, new covariance or Holevo expression is used.
"""
from __future__ import annotations

import csv
from dataclasses import asdict, is_dataclass, replace
import json
import math
from pathlib import Path

from scripts import run_ao_effective_channel_no_fading_noise_reference as existing
from scripts.exact_cache_provenance import source_settings, verify_source_payload
from scripts.run_theta10_D55_unconstrained_three_scheme import unconstrained_config, candidate_from_payload
from scripts.calculate_channel_pdf_and_moments import derive_physical_inputs
from src.manuscript_literal_3moments import LiteralChannel
from src.manuscript_corrected_3moments import PhysicalFadingDistribution
from src.uav_mobility import link_geometry, scalar, cloud_transmittance

ROOT = Path(__file__).resolve().parents[1]
MODEL = "effective_channel_no_fading_noise"


def load_candidates(settings, protected_hashes):
    config = unconstrained_config()
    roster_path = ROOT / settings["source_roster"]
    receipt = existing.read_json(ROOT / settings["source_roster_receipt"])
    if existing.digest(roster_path) != receipt["source_roster_sha256"]:
        raise ValueError("Validated source roster hash differs")
    if settings["source_family"] != "MB":
        raise ValueError("This experiment uses the exact MB catalog only")
    with roster_path.open(encoding="utf-8", newline="") as stream:
        roster = [r for r in csv.DictReader(stream) if r["family"] == "MB"]
    candidates = []
    for row in roster:
        path = ROOT / row["source_path"]
        if existing.digest(path) != row["source_payload_sha256"]:
            raise ValueError("Source roster payload hash mismatch")
        payload = existing.read_json(path)
        payload["_provenance"] = verify_source_payload(payload, source_settings(config))
        payload["_path"] = row["source_path"]
        candidate = candidate_from_payload(config, {payload["ensemble_hash"]: payload}, "MB",
            float.fromhex(payload["nu_mb_raw_hex"]), float.fromhex(payload["V_A_hex"]))
        existing.authenticate(candidate, protected_hashes, config)
        for name in ("C", "w", "nu_raw", "V_A"):
            if candidate[name] != float(row[name]):
                raise ValueError(f"Source roster {name} mismatch")
        if candidate["ensemble_hash"] != row["ensemble_hash"] or candidate["nu_raw"] <= 0:
            raise ValueError("MB source identity mismatch")
        candidates.append(candidate)
    if not candidates or len({c["ensemble_hash"] for c in candidates}) != len(candidates):
        raise ValueError("Empty or duplicate source catalog")
    return sorted(candidates, key=lambda c:(c["nu_raw"], c["V_A"])), config, roster


def channel_state(settings, position, blocked):
    geometry, channel = settings["geometry"], settings["channel"]
    if settings["scientific_model"] != MODEL:
        raise ValueError("Use the existing no-fading-noise Gaussian mode")
    if (channel["R"], channel["xi_det"], channel["xi_ch"], channel["beta_rec"]) != (1.,0.,.0186,.95):
        raise ValueError("Existing ideal heterodyne/noise/reconciliation convention required")
    if channel["phase_noise"] != "OFF" or channel["adaptive_optics"] != "OFF":
        raise ValueError("Phase noise and adaptive optics must remain off")
    if channel["clear_atmosphere_excludes_added_cloud_loss"] is not True:
        raise ValueError("Clear atmosphere must exclude the added cloud attenuation")
    distances, zenith = link_geometry([position], geometry["hap_horizontal_m"],
                                      geometry["h_hap_m"], geometry["h_uav_m"])
    physical = derive_physical_inputs(channel["clear_tau_zen"],
        zenith_angle_rad_override=float(zenith[0]),
        aperture_radius_m_override=channel["receiver_radius_m"],
        beam_waist_m_override=channel["beam_waist_m"])
    if physical["h_hap_m"] != geometry["h_hap_m"] or physical["h_uav_m"] != geometry["h_uav_m"]:
        raise ValueError("Geometry altitude differs from the protected physics producer")
    if not math.isclose(physical["link_length_m"], float(distances[0]), abs_tol=1e-9, rel_tol=0.):
        raise ValueError("Geometry/physical link lengths disagree")
    if channel["cloud_conditioning"] != "multiply_raw_channel_then_condition_active_on_0_T_le_1_preserve_outage":
        raise ValueError("Unsupported channel conditioning; no silent convention change")
    transmission = cloud_transmittance(settings["cloud"]["attenuation_db"], blocked)
    clear = LiteralChannel.from_physical(physical)
    # Multiplying RAW T by the cloud factor precedes the existing physical conditioning.
    raw = clear if transmission == 1. else replace(clear, eta_atm=clear.eta_atm * transmission)
    moments = PhysicalFadingDistribution(raw).moments(R=1., xi_det=0., xi_ch=.0186)
    physical_record = {k:asdict(v) if is_dataclass(v) else v for k,v in physical.items()}
    return dict(position_m=list(map(float, position)), distance_m=float(distances[0]),
        zenith_rad=float(zenith[0]), blocked=bool(blocked), cloud_transmittance=transmission,
        physical=existing.config_identity(physical_record), clear_raw_channel=asdict(clear),
        cloud_raw_channel=asdict(raw), moments=moments)


def scientific_identity(settings, baseline_config):
    names = {p.relative_to(ROOT).as_posix() for folder in ("src/channel","src/cvqkd","src/modulation")
             for p in (ROOT/folder).rglob("*.py")}
    names.update(("src/effective_channel_no_fading_noise.py", "src/manuscript_literal_3moments.py",
        "src/manuscript_corrected_3moments.py", "src/mobility_skr.py", "src/uav_mobility.py",
        "scripts/run_ao_effective_channel_no_fading_noise_reference.py",
        "scripts/run_theta10_D55_unconstrained_three_scheme.py", "scripts/run_exact_mb_test2.py",
        "scripts/calculate_channel_pdf_and_moments.py", "scripts/exact_cache_provenance.py", "scripts/_common.py"))
    return dict(mode=MODEL, baseline_config=existing.config_identity(baseline_config),
        geometry=settings["geometry"], channel=settings["channel"],
        scientific_implementation={n:existing.digest(ROOT/n) for n in sorted(names)},
        security="chi_BE_at_direct_Z_star", MI="discrete_256_QAM_GH_product_8_16_32")


def objective_key(identity, state, candidate, payload_hash):
    return existing.hash_json(dict(schema="mobility-exact-objective-v1", identity=identity,
        channel_state=state, ensemble_hash=candidate["ensemble_hash"],
        source_cache_key=candidate["source_cache_key"], source_payload_sha256=payload_hash,
        nu_raw_hex=float(candidate["nu_raw"]).hex(), V_A_hex=float(candidate["V_A"]).hex(),
        C_hex=float(candidate["C"]).hex(), w_hex=float(candidate["w"]).hex()))


def validate_result(row, candidate, state):
    for name in ("I_AB","chi_BE","SKR","T_eff","Z_star","a","b","lambda_1","lambda_2","lambda_3"):
        scalar(row[name], name)
    if row["ensemble_hash"] != candidate["ensemble_hash"] or row["C"] != candidate["C"] or row["w"] != candidate["w"]:
        raise ValueError("Cached objective/source mismatch")
    if row["T_eff"] != state["moments"]["mean_sqrt_eta"]**2 or row["xi_eff"] != .0186:
        raise ValueError("Cached objective/channel mismatch")
    t, va = row["T_eff"], candidate["V_A"]
    if row["N_eff"] != t*.0186 or abs(row["a"]-(1+va)) > 1e-13 or abs(row["b"]-(1+t*(va+.0186))) > 1e-13:
        raise ValueError("Cached objective/noise/covariance mismatch")
    z = 2*math.sqrt(t)*candidate["C"] - math.sqrt(2*t*.0186*candidate["w"])
    if abs(row["Z_star"]-z) > 1e-13:
        raise ValueError("Cached correlation identity failed")
    if abs(row["SKR"]-(.95*row["I_AB"]-row["chi_BE"])) > 1e-14:
        raise ValueError("Cached signed SKR identity failed")
    if row["numerical_repairs"] or min(row[k] for k in ("lambda_1","lambda_2","lambda_3")) < 1:
        raise ValueError("Cached nonphysical/repaired covariance rejected")
    return row


class ExactStateCache:
    """Private, hash-bound objective journal; existing sources are read-only."""
    def __init__(self, path, identity, protected_hashes, config):
        self.path, self.identity = Path(path), identity
        self.hashes, self.config = protected_hashes, config
        self.records, self.new_evaluations, self.hits = {}, 0, 0
        self.path.parent.mkdir(exist_ok=True)
        if self.path.exists():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                record = json.loads(line)
                if existing.hash_json(record["row"]) != record["row_sha256"] or record["key"] in self.records:
                    raise ValueError("Objective journal corruption or duplicate key")
                self.records[record["key"]] = record

    def evaluate(self, candidate, state):
        payload_hash = existing.digest(ROOT/candidate["source_path"])
        if self.hashes.get(candidate["source_path"]) != payload_hash:
            raise ValueError("Source bytes changed after startup")
        key = objective_key(self.identity, state, candidate, payload_hash)
        if key in self.records:
            record = self.records[key]
            self.hits += 1
            return key, validate_result(record["row"], candidate, state)
        complete = existing.evaluate_authenticated(candidate, state["moments"], self.config, self.hashes)
        names = ("nu_raw", "V_A", "C", "w", "ensemble_hash", "source_cache_key", "source_path",
            "source_payload_sha256", "T_eff", "xi_eff", "N_eff", "a", "b", "Z_star",
            "Z_signal", "Z_penalty", "lambda_1", "lambda_2", "lambda_3", "I_AB", "beta_I_AB",
            "chi_BE", "SKR", "MI_orders", "numerical_repairs", "Holevo_target",
            "certified_fading_security_lower_bound")
        row = {name:complete[name] for name in names}
        validate_result(row, candidate, state)
        record = dict(key=key, row=row, row_sha256=existing.hash_json(row))
        with self.path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(record, allow_nan=False, separators=(",", ":"))+"\n")
            stream.flush()
        self.records[key] = record
        self.new_evaluations += 1
        return key, row
