"""Direct v43 evaluator under the separately versioned pilot specification."""
import mpmath as mp
import time

from support import OUT, ROOT, prior_model, read, sha

POLICY = "manuscript_eq14_direct"
correlation_eq14 = prior_model.correlation_eq14
components = prior_model.components
ModelBlocked = prior_model.ModelBlocked


def validate_protocol(protocol):
    prior_model.validate_protocol(protocol)
    spec_path = ROOT / protocol["experiment_spec_path"]
    if sha(spec_path) != protocol["experiment_spec_sha256"]:
        raise ModelBlocked("Versioned experimental specification changed")
    history_path = ROOT / protocol["frozen_history_path"]
    if sha(history_path) != protocol["frozen_history_sha256"]:
        raise ModelBlocked("Frozen-spec history evidence changed")
    spec, history = read(spec_path), read(history_path)
    historical = spec["historical_spec"]
    current = spec["current_repository_spec"]
    if (sha(ROOT / historical["path"]) != historical["sha256"]
            or historical["sha256"] != "561fecc97cdf9967034ffd6865c1605804b624b98f47a091e47f17e520a2a7b1"
            or sha(ROOT / current["path"]) != current["sha256"]
            or current["sha256"] != history["current_sha256"]
            or history["current_equals_HEAD"] is not True):
        raise ModelBlocked("Historical/current frozen-spec provenance check failed")
    if (protocol["pilot_angles_deg"] != [0, 5, 10, 15, 20, 30, 40, 50, 60]
            or protocol["pilot_pool_size"] != 81
            or spec["correlation_policy"] != POLICY
            or spec["physical"] != protocol["physical"]
            or spec["truncation_policy"] != protocol["truncation_policy"]):
        raise ModelBlocked("Unapproved experiment identity")


def channel_context(zenith_deg, protocol):
    validate_protocol(protocol)
    context = prior_model.channel_context(zenith_deg, protocol)
    context["protocol_sha256"] = sha(OUT / "protocol.json")
    context["experiment_spec_sha256"] = protocol["experiment_spec_sha256"]
    return context


def evaluate(source, context, protocol):
    validate_protocol(protocol)
    if (context.get("numerical_experiment_accepted") is not True
            or context.get("numerical_status") != "CURRENTLY_VERIFIED_PASS"
            or context.get("channel_law") != prior_model.LAW
            or context.get("protocol_sha256") != sha(OUT / "protocol.json")
            or context.get("renormalized") is not False or context.get("clipped") is not False):
        raise ModelBlocked("Validated [0,1] channel context required")
    if source.get("classification") not in {"VERIFIED_EXACT", "VERIFIED_BY_ALTERNATIVE_EVIDENCE"}:
        raise ModelBlocked("Source evidence insufficient; missing receipts do not imply incorrect C,w")
    p, alpha = prior_model.helpers().validate_source(source)
    if abs(float(p @ (2*alpha.real)**2)-source["VA"]) > protocol["numerical"]["source_tolerance"]:
        raise ValueError("VA=Vmod=2*nbar quadrature mismatch")
    moments = context["moments"]
    t = moments["mh"]**2
    if not 0 < t <= moments["m1"] <= 1:
        raise ValueError("Invalid effective moments")
    noise = ((moments["m1"]-t)*source["VA"] + protocol["xi_ch"]*moments["m1"]
             + protocol["xi_det"]*moments["M0"])
    began = time.perf_counter()
    h = components(source["VA"], t, noise/t, source["C"], source["w"], digits=110)
    low = components(source["VA"], t, noise/t, source["C"], source["w"], digits=80)
    with mp.workdps(120):
        if any(abs(mp.mpf(h["decimal"][k])-mp.mpf(low["decimal"][k])) > mp.mpf("2e-11")
               for k in ["Z_manuscript_eq14", "chi_BE"]):
            raise ValueError("Eq14/Holevo precision agreement unresolved")
    holevo_seconds = time.perf_counter()-began
    began = time.perf_counter()
    mi64, mi = [prior_model.helpers().homodyne_mi(p, alpha, t, 1+noise, order=order)
                for order in [64, 128]]
    if abs(mi-mi64) > protocol["numerical"]["MI_tolerance"]:
        raise ValueError("MI GH64/128 agreement unresolved; higher-order validation required")
    return {**h, "eta_f": t, "xi_f": noise/t, "N_effective": noise,
        "M0": moments["M0"], "E_sqrt_eta": moments["mh"], "E_eta": moments["m1"],
        "E_eta_xi": protocol["xi_ch"]*moments["m1"]+protocol["xi_det"]*moments["M0"],
        "Vmod": source["VA"], "I_AB": mi, "beta_I_AB": protocol["beta"]*mi,
        "chi_BE": h["chi_BE"], "K_raw": protocol["beta"]*mi-h["chi_BE"],
        "MI_GH64_128_difference": abs(mi-mi64), "source_hash": source["ensemble_hash"],
        "MI_seconds": time.perf_counter()-began, "Holevo_seconds": holevo_seconds,
        "probability_deficit": context["probability_deficit"],
        "truncation_status": "USER_ACCEPTED_APPROXIMATION", "security_valid": False}
