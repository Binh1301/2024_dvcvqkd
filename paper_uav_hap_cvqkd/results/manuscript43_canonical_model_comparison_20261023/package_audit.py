"""Package saved fixed checks and traceable comparisons; never run an optimizer."""
import ast
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
REPO = ROOT.parent


def read(name):
    return json.loads((OUT / name).read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def write(name, rows):
    keys = list(dict.fromkeys(k for row in rows for k in row))
    with (OUT / name).open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


# All classifications below refer to the available hash-bound v43, pending v43(2).
# tuple: component, classification, role, expression, effect, recommendation
COMPONENTS = [
("src/channel/atmospheric_loss.py","EQUIVALENT","atmospheric_transmittance_from_tau_zen","tau_zen**sec(zeta); Kruse alternative is DIFFERENT","moments","Use explicit tau_zen route; do not substitute visibility/extinction closure"),
("src/channel/geometry.py","EQUIVALENT","LinkGeometry","L=(h_HAP-h_UAV)sec(zeta) in flat-Earth setting","moments","Use identical geometry and recompute optics for each L"),
("src/channel/scintillation.py","DIFFERENT","hufnagel_valley_scintillation","v_sc=A_ap*sigma_R0_squared versus Eq5 v=sigma_R2","moments","Keep aperture averaging separate; raw Rytov matches at fixed fixture"),
("src/channel/pointing_error.py","DIFFERENT","manuscript_pointing_parameters","nu uses wL whereas available Eq6 uses wL_eff","moments","Propose isolated wL_eff fix only after reference binding"),
("src/channel/turbulence.py","EQUIVALENT","pointing_displacement_variance_m2","sigma_s^2=sigma_h^2+(L theta_jt)^2 for restricted no-extra-motion fixture","moments","Extra orientation/beam-wander terms require separate model identity"),
("src/channel/aoa.py","EQUIVALENT","aoa_outage_probability; sample_aoa_gate","P0=exp(-theta_FOV^2/(2sigma_o^2))","atom; moments","Use half-angle and fixed sigma_o; do not silently add turbulence AoA"),
("src/channel/fso_channel.py","DIFFERENT","sample_fso_channel","reject/resample eta>1 among ACTIVE draws, preserving AoA gate","law; moments; MI; Holevo","Document conditional active law; never call it raw Eq10"),
("scripts/hap_uav_channel_pdf.py","DIFFERENT","f_hp; f_x_direct_quadrature; _sample_physical_active","exact Rician product integrals; active conditioning in sampling","law; moments","Exact product equals Eq10 at rho0 only; distinguish sampled and raw PDF laws"),
("scripts/calculate_channel_pdf_and_moments.py","DIFFERENT","closed_form_channel_moments; production_sampler_check","rho0 product moments plus explicit raw/sampler comparisons; own aperture closure","moments","Reuse individual formula only after matching physical inputs and support"),
("src/modulation/qam256.py","EQUIVALENT","square_qam256; canonical_square_qam256; maxwell_boltzmann_pmf","centered grid; unit RMS gauge; normalized exp(-nu*energy)","source; MI; Holevo","Convert nu_repo=42.5*nu_raw; use same parameter numerator/denominator"),
("src/modulation/normalization.py","BLOCKED","physical_amplitudes","alpha=sqrt(VA/(2Ex))*x, VA=2nbar versus printed Vmod=nbar/2","source; MI; covariance","Resolve printed factor4 with vacuum and commutator; do not relabel old cache"),
("src/modulation/joint_ps_gs.py","DIFFERENT","reference_ensemble; JointTransmitter","general PS/GS/adaptive variance beyond square MB manuscript definition","source; MI; Holevo","Preserve historical module; no training in this audit"),
("src/cvqkd/gram_moments.py","EQUIVALENT","c4_gram_source_moments","full-support Gram representation of same tau,C,w for C4 source","source correlation","Only authenticated full-support routes; complex128 threshold is not a proof"),
("scripts/full_support_c4_worker.py","EQUIVALENT","arbitrary-precision full-support source route","same source C,w without Fock cutoff; verified catalog identity required","source correlation","Preserve cache; no new AP in this task"),
("scripts/exact_cache_provenance.py","EQUIVALENT","verify_source_payload","authenticate actual p,alpha,source settings,hash and route","provenance","Keep source and evaluator identities separate"),
("src/cvqkd/protocol.py","DIFFERENT","ProtocolAssumptions","frozen production ideal heterodyne protocol","MI; Holevo","Do not use as v43 homodyne canonical entrypoint"),
("src/cvqkd/mutual_information.py","DIFFERENT","discrete_mutual_information; deterministic_mutual_information","complex heterodyne conditional; different dimensionality/noise convention","MI; SKR","Preserve historical API; no heterodyne execution here"),
("src/cvqkd/covariance.py","DIFFERENT","standard_form_covariance","conditional lambda3=a-z^2/(b+1), heterodyne","Holevo; SKR","Require homodyne sqrt(a*(a-z^2/b)) in future dedicated entrypoint"),
("src/cvqkd/holevo.py","DIFFERENT","holevo_information; _holevo_from_source_moments","source C,w compatible; production spectrum/protocol heterodyne and interval policy","Holevo; SKR","Reuse authenticated source only; do not import whole heterodyne evaluator"),
("src/cvqkd/secret_key_rate.py","DIFFERENT","fading_secret_key_rate","statewise averaging/positive-part policy rather than one Gaussian effective channel","SKR objective","Keep per-state and pooled effective objectives distinct"),
("src/cvqkd/training_surrogate.py","DIFFERENT","training surrogate","training approximation; no canonical exact-source certification","optimization objective","NOT_RUN; no substitution in audit"),
("src/manuscript_literal_3moments.py","DIFFERENT","effective_channel; detector_noise; total_input_noise","historical v37 eta_f=mh, heterodyne detector chi and old noise law","moments; MI; Holevo","Historical namespace only; do not call manuscript-literal file v43"),
("src/manuscript_corrected_3moments.py","DIFFERENT","PhysicalFadingDistribution; effective_fading_channel","active conditioning and mxi=1+chi_het+(xi_ch-1)m1","law; noise; Holevo","Keep separate model identifier"),
("src/manuscript_corrected_mi.py","DIFFERENT","discrete_fading_mutual_information","complex fading mixture, historical detector convention","MI","Do not combine with homodyne Holevo"),
("src/manuscript_corrected_evaluator.py","DIFFERENT","validate_settings; evaluate_candidate","historical trusted/ideal gate and old evaluator","SKR","Not new untrusted v43 entrypoint"),
("src/manuscript_mobility.py","DIFFERENT","load_catalog; evaluate_source; channel_at_angle","authenticated source loader reusable; historical mixed evaluator different","MI; Holevo; objectives","Reuse catalog/geometry only; source read-only"),
("scripts/recheck_manuscript_homodyne_noise.py","DIFFERENT","channel; security; mi_gh","channel formulas reusable; main historical complex-MI/homodyne pairing","MI; Holevo","Use dimension1 helper only after convention audit; main NOT_RUN"),
("results/zenith_angle_root_cause_diagnostic_20261021/investigate.py","DIFFERENT","historical zenith diagnostic","2D MI plus homodyne Holevo; xi_det0; old8cm/233urad geometry","MI; noise; SKR","Do not infer current1D SKR from historical figure"),
("results/manuscript43_homodyne_audit_20261023/audit_model.py","EQUIVALENT","raw_pdf_moments; homodyne_mi","Eq10 coefficients/retained moments and normalized real1D likelihood, with explicit corrections","moments; MI","Reuse pure helpers; detector eta physical mode remains separate"),
("results/untrusted_positive_skr_feasibility_20261022/model.py","DIFFERENT","power_conserving; bounded; evaluate; full_holevo","random-width law different; bounded() has conditional/erasure alternatives; evaluate has eta_det","law; noise; Holevo","B/C use power_conserving only; new v43 wrapper omits eta_det"),
("results/uniform_positive_skr_manuscript43_20261023/search.py","DIFFERENT","model; Search.context","raw and bounded selectable; no automatic law substitution","all","Pure model helper reused; Search/optimization NOT_RUN"),
("results/skr_vs_zenith_manuscript43_20261023/run_sweep.py","EQUIVALENT","selected_checks; covariance","task v43 real1D/no-eta_det three-moment diagnostics","MI; Holevo validation","Diagnostic only; raw normalization gate and Z policy retained"),
("configs/default.yaml","DIFFERENT","production defaults","historical ideal heterodyne protocol/config","all","Preserve; do not silently change defaults during audit"),
("configs/channel.yaml","BLOCKED","production channel inputs","unresolved tau_zen and turbulence/phase approvals in active production route","moments; security","Fixed task provenance supplies diagnostic tau only, not production approval"),
("docs/FINAL_MODEL_SPEC.md","BLOCKED","frozen authority identity","current df83... differs from AGENTS historical561f...","authority","Preserve bytes; user intent cannot authenticate missing v43(2) PDF"),
]

# tuple: equation, printed expression, implementation(s), class, discrepancy/effect, next action
EQUATIONS = [
("1","alpha_ij=Delta[(i-7.5)+i_c(j-7.5)]","src/modulation/qam256.py:square_qam256; src/modulation/normalization.py:physical_amplitudes","EQUIVALENT","Repository unit-RMS gauge and physical scalar recover same points at fixed nbar","Document Delta; preserve p,alpha hashes"),
("2","p_k=exp(-gamma|k|^2)/sum exp(-nu|k|^2)","src/modulation/qam256.py:maxwell_boltzmann_pmf","BLOCKED","gamma!=nu fails normalization; uncentered indices break C4. Repository uses one centered energy and one parameter","Proposal gamma=nu and k=(i-7.5,j-7.5); convert nu_repo=42.5nu_raw"),
("3 + following sentence","nbar=sum p|alpha|^2; Vmod=nbar/2","src/modulation/normalization.py:physical_amplitudes; audit_fixed.py:literal_internal_consistency output","BLOCKED","For VA3 source nbar1.5; printed Vmod.75 versus Var(2Re alpha)=3 and vacuum1","Proposal Vmod=2nbar at vacuum1; alternative full quadrature rescaling must change CCR/vacuum/covariance too"),
("4","eta_atm=tau_zen^sec(zeta)","src/channel/atmospheric_loss.py:atmospheric_transmittance_from_tau_zen; legacy.optical","EQUIVALENT","Exact attenuation route; Kruse is a separate closure. tau=.92 at fixed1->20km","Use authenticated altitude/visibility; no arbitrary distance rescaling"),
("5","ln Ia~Normal(-sigma_R2/2,sigma_R2); Rytov integral","scripts/recheck_manuscript_homodyne_noise.py:channel; src/channel/scintillation.py:hufnagel_valley_scintillation","DIFFERENT","Raw Rytov matches6.94e-17; production finite-aperture v_sc=.00393937 versus.04145353","Explicitly choose printed v or separately named aperture-averaged closure; HV formula missing from PDF"),
("6","eta_p=A0 exp(-2r^2/weq^2); nu=sqrt(pi)Dr/(2sqrt(2)weff)","src/channel/pointing_error.py:manuscript_pointing_parameters; legacy.optical","DIFFERENT","Production nu uses wL: A0 delta+.0051750780, weq delta+.00469123525m; B/C exact circular collection is another law","Proposal isolated nu argument correction; retain Eq6 approximate collection identity"),
("7","r~Rice(rho,sigma_s), sigma_s^2=sigma_h^2+(L theta_jt)^2","scripts/hap_uav_channel_pdf.py:f_rmis; audit_fixed.py:true_rician_moments","EQUIVALENT","At rho0 Rayleigh; extra production motion terms are only equivalent when zero","Do not discard rho in general configurations"),
("8","transformation of Rice under eta_p=A0 exp(-2r^2/weq^2)","scripts/hap_uav_channel_pdf.py:f_hp; audit_fixed.py:true_rician_moments","EQUIVALENT","I0 term is required for rho!=0; simple power law exact only rho0","Use exact Rice pushforward or label approximation"),
("9","P0 delta0+P1 delta1; P0=exp(-theta_FOV^2/(2sigma_o^2))","src/channel/aoa.py:aoa_outage_probability; legacy.optical","EQUIVALENT","Same atom .00016985667656141065 at fixed FOV half-angle","Keep atom separate; do not transfer eta>1 tail into it"),
("10","P0 delta0 + P1*d*C1/(2B^d)*eta^(d-1)erfc(C3[ln(eta/B)+mu]), eta in[0,1]","audit_model.py:raw_coefficients; raw_pdf_moments","BLOCKED","Critical retained mass.9013297245653482; lognormal continuation has tail.09867027543465177; rho!=0 formula also differs from exact Rice product","No clipping/renormalization; record incompatible support; correction proposal required"),
("11","K=beta I_AB-chi_BE","results/uniform_positive_skr_manuscript43_20261023/search.py:model","EQUIVALENT","Raw negative K retained; blocked rows null. Positive-part/statewise objectives differ","Use raw K only after source/law/physicality gates"),
("12","real y; printed |y-2sqrt(T)alpha|^2 versus corrected (y-2sqrt(T)Re alpha)^2","audit_model.py:homodyne_mi; independent_mi; src/cvqkd/mutual_information.py","BLOCKED","Literal complex-alpha real-y conditional masses.04887046--.98667367; production heterodyne different; corrected likelihood normalized","User-specified real projection diagnostic; proposal explicit Re and 1D measure; never Shannon MI"),
("13","chi=g((nu1-1)/2)+g((nu2-1)/2)-g((nu3-1)/2); nu3=sqrt(V(V-Z^2/W))","legacy.spectrum; full_holevo; src/cvqkd/covariance.py:standard_form_covariance","DIFFERENT","Legacy helper homodyne correct; production a-z^2/(b+1) is heterodyne. Same T,N in V=1+VA,W=1+TVA+N","Require Gamma+iOmega>=0 and nu>=1; no eigenvalue clipping"),
("14","Zminus=2sqrt(T)C-sqrt(2Nw)","legacy.full_holevo; search.py:model","DIFFERENT","Printed one endpoint versus maximizing over physical DBL interval; equal at critical fixture, not proven globally identical","Report policy separately; future literal Zminus needs domain/theory decision"),
("15","tau=sum p|alpha><alpha|; finite Fock approximation printed","src/cvqkd/holevo.py:density_operator; src/cvqkd/gram_moments.py; exact source cache","EQUIVALENT","Full-support Gram mathematically same tau; finite Fock cutoff is approximation with distinct error checks","Preserve same authenticated p,alpha,C,w; do not replace full support with threshold rank"),
("16","w=sum p(<a_tau^dagger a_tau>-|<a_tau>|^2), a_tau=tau^.5 a tau^-.5","src/cvqkd/gram_moments.py; scripts/full_support_c4_worker.py; exact_cache_provenance.py","EQUIVALENT","Exact catalog C=1.9206153338755625,w=.029240798657568498 at UniformVA3; no new AP needed","Reuse under same physical source; new actual ensemble needs new exact moments"),
("17","T=mh^2; N=(m1-T)Vmod+mxi; xi_f=N/T","search.py:model; src/manuscript_literal_3moments.py:effective_channel","DIFFERENT","New wrapper matches user VA convention; historical v37 uses eta_f=mh and different noise; Vmod printed inconsistency unresolved","Require single shared T,N for MI,DBL,Gamma,Holevo; no eta_det"),
("18","m1=P1*B*d*C1/(d+1)*Q(d+1)","audit_model.py:raw_pdf_moments","EQUIVALENT","Closed/direct difference -1.9984e-15 at critical; these are retained subdensity integrals when mass fails","Keep numeric moment but block probability/security interpretation"),
("19","mh=P1*sqrt(B)*d*C1/(d+.5)*Q(d+.5)","audit_model.py:raw_pdf_moments","EQUIVALENT","Closed/direct difference -1.9984e-15; bounded mh=.88216868 differs from raw.77456969","No interpolation or replacement by bounded moments"),
("20","mxi=xi_ch*m1+xi_det[P0+P1*C1*Q(d)]","audit_fixed.py:effective; search.py:model","EQUIVALENT","Continuous-limit eta*xi(0)=xi_det; mass factorM0 required. Raw.01698432 versus bounded.01950070","Do not replace M0 with1 in defective law; operational outage noise remains an assumption"),
("21","m1=P1*d*C1/(2B^d) integral_0^1 eta^d erfc(...) deta","audit_model.py:raw_pdf_moments direct; audit_fixed.py","EQUIVALENT","Integration by parts yields18; atom contributes0 to m1 but not to Eq20 limiting detector term","Distinguish exact integration identity from normalized law"),
("III-B","Optimization=TBD","historical search and optimization scripts","BLOCKED","Available paper defines no optimizer; none executed this task","No optimizer promotion or new global search"),
]


def main():
    assert not (OUT / "package_receipt.json").exists(), "Preserve completed package producer"
    rows = []
    for path, cls, role, expression, effect, action in COMPONENTS:
        target = ROOT / path
        assert target.is_file(), path
        symbols = []
        if target.suffix == ".py":
            tree = ast.parse(target.read_text(encoding="utf-8-sig"))
            symbols = [f"{node.name}:{node.lineno}" for node in ast.walk(tree)
                       if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
        rows.append(dict(path=path, classification=cls, role=role, expression=expression,
                         effect=effect, recommended_action=action, symbols=";".join(symbols),
                         sha256=sha(target), reference="available_v43_SHA256_f970cd6d",
                         requested_v43_2_verified=False))
    write("component_classification.csv", rows)
    write("equation_comparison.csv", [
        dict(equation=e, manuscript_expression=m, implementation=impl, classification=cls,
             difference_and_effect=why, recommended_action=action,
             reference="available_v43_not_yet_bound_to_requested_v43_2")
        for e, m, impl, cls, why, action in EQUATIONS])

    ch = read("fixed_contexts.json")["critical_uniform_positive"]["channel"]
    parameters = [
        ("h_HAP",20000,"m","task and available v43 Section IV","EXACT_MATCH"),
        ("h_UAV",1000,"m","task and available v43 Section IV","EXACT_MATCH"),
        ("lambda",1.55e-6,"m","task and available v43 Section IV","EXACT_MATCH"),
        ("Dr",.30,"m","task recent-positive fixture; manuscript default .08","DIFFERENT"),
        ("zenith",0,"degree","task fixture; manuscript default30","DIFFERENT"),
        ("L",19000,"m","Eq6 flat-Earth altitude difference /cos0","EQUIVALENT"),
        ("full_divergence",10,"urad","task fixture; manuscript default233","DIFFERENT"),
        ("jitter_per_axis",.5,"urad","task fixture; manuscript default15.61","DIFFERENT"),
        ("sigma_h_per_axis",.03,"m","task fixture; manuscript default1","DIFFERENT"),
        ("rho",0,"m","both offsets0; available v43 default","EXACT_MATCH"),
        ("F0","infinity","m","available v43 Section IV and historical optics","EXACT_MATCH"),
        ("tau_zen",.92,"dimensionless","fixed1->20km available v43 and historical protocol; user visibility23km","EXACT_MATCH"),
        ("visibility_reference",23,"km","user table:23->.92,15->.89,5->.75; not altitude extinction profile","BLOCKED"),
        ("wind",21,"m/s","available v43 Section IV; repository HV closure","EXACT_MATCH"),
        ("Cn2_ground",1e-14,"m^(-2/3)","available v43 Section IV; repository HV closure","EXACT_MATCH"),
        ("HV_profile","0.00594*(21/27)^2*(1e-5*h)^10*exp(-h/1000)+2.7e-16*exp(-h/1500)+1e-14*exp(-h/100)","m^(-2/3)","repository; available PDF leaves citation[]","BLOCKED"),
        ("Gd_closure","4.35*(2L/(k*wL^2))^(5/6)*k^(7/6)*dh^(5/6)*sec^(11/6)*integral Cn2*((h-hUAV)/dh)^(5/3) dh","dimensionless","legacy optical; missing explicit PDF formula[]","BLOCKED"),
        ("theta_FOV_half_angle",6.25,"mrad","available v43 Section IV and fixed provenance","EXACT_MATCH"),
        ("sigma_o",1.5,"mrad","available v43 Section IV and fixed provenance","EXACT_MATCH"),
        ("xi_ch",.0186,"SNU","task; previous v43 protocol; PDF defines symbol but no numeric value","EQUIVALENT"),
        ("xi_det",.005,"SNU","task explicit parameter; PDF defines symbol but no numeric value","EQUIVALENT"),
        ("beta",.95,"dimensionless","task and available v43 Section IV","EXACT_MATCH"),
        ("VA",3,"SNU","task; physical actual source VA=2nbar","BLOCKED"),
        ("nbar",1.5,"photons/use","authenticated actual Uniform ensemble","EQUIVALENT"),
        ("printed_Vmod",.75,"printed SNU","available v43 nbar/2; inconsistent with unit vacuum convention","BLOCKED"),
        ("M",256,"states","task and source catalog","EXACT_MATCH"),
        ("p_k",1/256,"probability","Uniform gamma=nu=0","EXACT_MATCH"),
        ("measurement","homodyne real1D","type","task and printed nu3","EQUIVALENT"),
        ("reconciliation","reverse","type","task","EQUIVALENT"),
        ("eta_det","ABSENT","parameter","task requires no separate detector efficiency","EXACT_MATCH"),
        ("eta_xi_at_outage",.005,"SNU","continuous limiting extension of xi_ch*eta+xi_det","EQUIVALENT"),
        ("AO","OFF","state","saved fixture; no AO closure changed","EQUIVALENT"),
        ("extra_phase_noise","OFF_HISTORICAL_ASSUMPTION","state","saved fixture, not hardware validation","BLOCKED"),
    ]
    for key in ["w0_m","wL_m","w_eff_m","w_eq_m","G_d","B","d","v","P0","P1","sigma_s_m"]:
        parameters.append((key,ch[key],"m" if key.endswith("_m") else "dimensionless",
                           "recomputed fixed optics; fixed_contexts.json", "EQUIVALENT"))
    p = read("protocol.json")
    for key in ["mass_tolerance","moment_integration_tolerance","source_tolerance","MI_tolerance",
                "Holevo_tolerance","entropy_tolerance","GH_orders","full_Z_grids","entropy_digits","bounded_width_orders"]:
        parameters.append((key,json.dumps(p[key]),"numerical","prospective protocol.json","EQUIVALENT"))
    write("parameter_provenance.csv",[
        dict(parameter=k,value=v,unit=u,origin=o,classification=cls,
             requested_v43_2_match="BLOCKED_REFERENCE_NOT_LOCATED")
        for k,v,u,o,cls in parameters])

    # Fixed notation checks only; no exact source generation or altered-source SKR.
    levels = np.arange(16, dtype=float)-7.5
    raw = (levels[:,None]+1j*levels[None,:]).reshape(-1)
    energy = abs(raw)**2
    assert abs(energy.mean()-42.5)<1e-14
    nu = .04
    raw_p = np.exp(-nu*energy); raw_p /= raw_p.sum()
    canonical_p = np.exp(-(42.5*nu)*abs(raw/np.sqrt(42.5))**2)
    canonical_p /= canonical_p.sum()
    assert max(abs(raw_p-canonical_p))<2e-16
    mismatch = np.exp(-.03*energy)/np.exp(-.04*energy).sum()
    assert abs(mismatch.sum()-1)>1e-2
    uncentered = (np.arange(16)[:,None]+1j*np.arange(16)[None,:]).reshape(-1)
    uncentered_p=np.exp(-nu*abs(uncentered)**2);uncentered_p/=uncentered_p.sum()
    mean=uncentered_p@raw
    assert abs(mean)>1
    save("source_notation_checks.json",dict(status="CURRENTLY_VERIFIED_PASS",checks=4,
         raw_grid_mean_energy=42.5,nu_raw=nu,nu_unit_RMS=42.5*nu,
         equivalent_PMF_max_residual=float(max(abs(raw_p-canonical_p))),
         gamma_003_nu_004_PMF_mass=float(mismatch.sum()),
         uncentered_energy_PMF_mean_on_centered_grid=[mean.real,mean.imag],
         actual_fixed_source_unchanged=True,new_Cw=False))
    with (OUT/"controlled_comparisons.csv").open(encoding="utf-8") as stream:
        controlled=list(csv.DictReader(stream))
    value=read("pooled_MI_refined.json")["compared_to_Gaussian"]
    controlled.append(dict(diagnostic="pooled_fading_homodyne_MI_refined_same_law",
        classification="DIFFERENT",I_AB=value["I_AB"],chi_BE=value["chi_BE"],
        raw_SKR=value["raw_SKR"],delta_I_AB=value["delta_I_AB"],delta_chi_BE=0.,
        delta_K=value["delta_K"],source_hash=value["source_hash"],
        description="Refined exact same channel; 1D fading mixture instead of Gaussian effective likelihood; Holevo held fixed; diagnostic not new security proof"))
    write("controlled_comparisons_final.csv",controlled)
    save("canonical_model_manifest.json",dict(
        intended_authority="USER_DESIGNATED_MANUSCRIPT_V43_2",
        requested_name="2026__Binh_s_work (43)(2).pdf",
        reference_identity="BLOCKED_REFERENCE_NOT_LOCATED",
        available_reference="inputs/available_v43.pdf",
        available_reference_sha256=sha(OUT/"inputs/available_v43.pdf"),
        available_reference_not_assumed_equal=True,
        mathematical_audit="COMPLETED_AGAINST_AVAILABLE_V43_AND_USER_TASK_FORMULAS",
        canonical_binding="BLOCKED",canonical_evaluator_adopted=False,
        security_status="UNVALIDATED_SECURITY_MODEL",
        lifecycle="NOT_READY_FOR_PUBLICATION_SCALE_RUNS",
        correction_proposal="correction_proposal_v1.md",
        corrections_adopted=False,production_modified=False,
        old_results_and_Cw_modified=False,optimization_executed=False,
        frozen_model_sha256=sha(ROOT/"docs/FINAL_MODEL_SPEC.md")))
    save("external_sources.json",[
        dict(url="https://quantum-journal.org/papers/q-2021-09-13-540/",
             role="Primary DBL asymptotic arbitrary-modulation reference; not certification of this fading/noise receiver"),
        dict(url="https://journals.aps.org/pra/abstract/10.1103/PhysRevA.103.012605",
             role="Primary free-space fading finite-size reference; no automatic transfer of its theorem to this DM implementation")])
    save("package_receipt.json",dict(status="CURRENTLY_VERIFIED_PASS",
        producer_sha256=sha(Path(__file__)),components=len(rows),equation_rows=len(EQUATIONS),
        parameters=len(parameters),fixed_source_notation_checks=4,
        requested_reference_identity="BLOCKED_REFERENCE_NOT_LOCATED"))
    print("Packaged",len(rows),"components,",len(EQUATIONS),"equation rows,",len(parameters),"parameters",flush=True)


if __name__ == "__main__":
    main()
