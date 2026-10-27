"""User-approved numerical conventions; preserved v43 equations and old artifacts."""
import importlib.util
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
PREVIOUS = ROOT / "results/skr_vs_zenith_eq14_v43_20261023"
spec = importlib.util.spec_from_file_location("_preserved_eq14", PREVIOUS / "model.py")
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)

# Reuse the exact equation implementations, including their domain checks.
sha, read, helpers = previous.sha, previous.read, previous.helpers
correlation_eq14, components = previous.correlation_eq14, previous.components
ModelBlocked, POLICY, LAW = previous.ModelBlocked, previous.POLICY, previous.LAW
TRUNCATION = dict(integration_domain=[0, 1],
    outside_mass="IGNORED_IN_NUMERICAL_EVALUATOR_RECORDED_AS_DIAGNOSTIC",
    renormalize=False, clip=False, replace_pdf=False, normalization_is_blocker=False,
    claim_mathematically_normalized=False, scope="SELECTED_PHYSICAL_BASELINE_ONLY")


def validate_protocol(protocol):
    previous.validate_protocol(protocol)
    if (protocol.get("truncation_policy") != TRUNCATION
            or protocol.get("VA_to_Vmod_mapping") != "AUTHOR_CONFIRMED_VA_EQUALS_VMOD"
            or protocol.get("source_normalization") != "VA=Vmod=2*nbar; X_A=2Re(alpha)"):
        raise ModelBlocked("Approved truncation/variance convention required")


def channel_context(zenith_deg, protocol):
    validate_protocol(protocol)
    context = previous.channel_context(zenith_deg, protocol)
    # Only the acceptance policy changes; every moment and tail remains untouched.
    context.update(mathematical_status="TRUNCATED_LAW_NOT_NORMALIZED",
        numerical_experiment_accepted=context["numerical_status"] == "CURRENTLY_VERIFIED_PASS",
        truncation_status="USER_ACCEPTED_APPROXIMATION",
        probability_deficit=context["precision"][-1]["one_minus_M0"],
        outside_probability_ignored=True, protocol_sha256=sha(OUT / "protocol.json"))
    return context


def evaluate(source, context, protocol):
    validate_protocol(protocol)
    if (context.get("numerical_experiment_accepted") is not True
            or context.get("numerical_status") != "CURRENTLY_VERIFIED_PASS"
            or context.get("channel_law") != LAW
            or context.get("protocol_sha256") != sha(OUT / "protocol.json")
            or context.get("renormalized") is not False or context.get("clipped") is not False):
        raise ModelBlocked("Approved, numerically validated channel context required")
    if source.get("convergence_status") != "CURRENTLY_VERIFIED_PASS":
        raise ModelBlocked("Convergence evidence unavailable; C,w are not classified as incorrect")
    p, alpha = helpers().validate_source(source)
    if abs(float(p @ (2*alpha.real)**2) - source["VA"]) > protocol["numerical"]["source_tolerance"]:
        raise ValueError("X_A variance disagrees with VA=Vmod=2*nbar")
    m = context["moments"]
    t = m["mh"]**2
    if not 0 < t <= m["m1"] <= 1:
        raise ValueError("Invalid effective moments")
    noise = ((m["m1"]-t)*source["VA"] + protocol["xi_ch"]*m["m1"]
             + protocol["xi_det"]*m["M0"])
    h = components(source["VA"], t, noise/t, source["C"], source["w"], digits=110)
    mi = helpers().homodyne_mi(p, alpha, t, 1+noise, order=128)
    return {**h, "eta_f": t, "xi_f": noise/t, "N_effective": noise,
        "Vmod": source["VA"], "I_AB": mi, "beta_I_AB": protocol["beta"]*mi,
        "K_raw": protocol["beta"]*mi-h["chi_BE"], "source_hash": source["ensemble_hash"],
        "probability_deficit": context["probability_deficit"],
        "truncation_status": "USER_ACCEPTED_APPROXIMATION", "security_valid": False}
