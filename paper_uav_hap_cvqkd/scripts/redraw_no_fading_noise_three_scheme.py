"""Updated distance figure: validated source cache only, no source oracle or AO."""
from __future__ import annotations

import csv
from datetime import datetime, timezone
import math
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import run_ao_effective_channel_no_fading_noise_reference as d
from scripts import continue_ao_effective_channel_no_fading_noise as continuation
from scripts import render_theta10_D55_three_scheme_log10 as style
from scripts.exact_cache_provenance import source_settings, verify_source_payload
from scripts.run_theta10_D55_unconstrained_three_scheme import candidate_from_payload

OUT = ROOT / "results/skr_vs_distance_effective_channel_no_fading_noise_cache_20261014"
OLD_CURVE = ROOT / "results/skr_vs_distance_theta10urad_D55cm_unconstrained_three_scheme/skr_vs_distance_three_scheme.csv"
REPORT = ROOT / "docs/SKR_DISTANCE_NO_FADING_NOISE_CACHE_REPORT_VI.md"


def channel_moments(config, distance):
    from scripts.calculate_channel_pdf_and_moments import derive_physical_inputs
    from src.manuscript_literal_3moments import LiteralChannel
    from src.manuscript_corrected_3moments import PhysicalFadingDistribution
    vertical = config["channel"]["h_hap_m"] - config["channel"]["h_uav_m"]
    physical = derive_physical_inputs(.92,
        zenith_angle_rad_override=math.acos(vertical/(1000*distance)),
        aperture_radius_m_override=.275, beam_waist_m_override=.0986760647169751)
    raw = LiteralChannel.from_physical(physical)
    moments = PhysicalFadingDistribution(raw).moments(R=1., xi_det=0., xi_ch=.0186)
    return moments, raw.__dict__


def render(rows):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import ticker
    # Core PDF fonts use the same installed backend as the existing renderer.
    matplotlib.rcParams["pdf.use14corefonts"] = True
    with plt.rc_context({"font.size": 11, "axes.labelsize": 13, "axes.titlesize": 17}):
        fig, ax = plt.subplots(figsize=(10.5, 6.5))
        for scheme in style.SCHEMES:
            points = sorted((r for r in rows if r["scheme"] == scheme), key=lambda r:r["distance_km"])
            for number, run in enumerate(style.positive_runs(points)):
                x, y = zip(*run)
                ax.plot(x, y, color=style.COLORS[scheme], marker="o", markersize=4.2,
                    linewidth=1.8, label=scheme if number == 0 else "_nolegend_")
        ax.set_yscale("log", base=10)
        ax.yaxis.set_major_locator(ticker.LogLocator(base=10))
        ax.yaxis.set_major_formatter(ticker.LogFormatterMathtext(base=10))
        ax.yaxis.set_minor_locator(ticker.LogLocator(base=10, subs="auto"))
        ax.yaxis.set_minor_formatter(ticker.NullFormatter())
        ax.set_title("SKR versus Link Distance")
        ax.set_xlabel("Link Distance (km)"); ax.set_ylabel("Secret Key Rate (bits/use)")
        ax.set_xlim(20, 40)
        ax.grid(which="major", alpha=.25)
        ax.grid(which="minor", alpha=.12, linewidth=.5)
        ax.legend(frameon=False, loc="upper right", fontsize=11)
        fig.text(.5, .037, "Effective Gaussian channel: fading-induced variance omitted.",
            ha="center", fontsize=8.5)
        fig.text(.5, .013, "Optimized = best in validated cache; positive rates shown, signed values retained in CSV.",
            ha="center", fontsize=8.5)
        fig.tight_layout(rect=(0, .065, 1, 1))
        fig.savefig(OUT/"skr_vs_distance_three_scheme_log10.png", dpi=300, facecolor="white")
        fig.savefig(OUT/"skr_vs_distance_three_scheme_log10.pdf", facecolor="white")
        plt.close(fig)


def main():
    import torch
    torch.set_num_threads(1)
    OUT.mkdir(exist_ok=True)
    if (OUT/"figure_receipt.json").exists():
        raise ValueError("Completed figure exists; preserve its artifacts")
    paths = [p for folder in ("src", "scripts", "configs", "tests", "results", "docs", ".agent")
        for p in (ROOT/folder).rglob("*") if p.is_file() and "__pycache__" not in p.parts
        and OUT not in p.parents and p.relative_to(ROOT).as_posix() not in d.STATE
        and p.resolve() not in (Path(__file__).resolve(), REPORT)]
    manifest = dict(captured_utc=datetime.now(timezone.utc).isoformat(),
        branch=subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip(),
        HEAD=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        initial_git_status=subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True),
        initial_git_diff=subprocess.check_output(["git", "diff"], cwd=ROOT).decode("utf-8"),
        state_before={name:(ROOT/name).read_text(encoding="utf-8") for name in d.STATE},
        protected_hashes={p.relative_to(ROOT).as_posix():d.digest(p) for p in paths},
        producer_sha256=d.digest(Path(__file__)),
        authorization="User chose best validated cached C,w at each distance; no new AP/AO.",
        fixed_MB=dict(nu_raw=.2, V_A=1.3833230302980657),
        scientific_model="effective_channel_no_fading_noise", xi_ch=.0186, beta_rec=.95,
        R=1., xi_det=0., phase_noise="OFF", adaptive_optics="OFF",
        frozen_actual_sha256=d.digest(ROOT/"docs/FINAL_MODEL_SPEC.md"),
        frozen_historical_expected="561fecc97cdf9967034ffd6865c1605804b624b98f47a091e47f17e520a2a7b1")
    if (OUT/"startup_manifest.json").exists():
        manifest=d.read_json(OUT/"startup_manifest.json")
        d.verify_protected(manifest)
    else:
        d.save(OUT/"startup_manifest.json", manifest, exclusive=True)
    prior = d.read_json(continuation.OUT/"completion_integrity_receipt.json")
    for name, expected in prior["output_sha256"].items():
        assert d.digest(ROOT/name) == expected, name
    obj = d.Objective()  # Loads/authenticates existing sources; allow_new=False.
    for path in sorted((continuation.OUT/"exact_source_cache").glob("*.json")):
        payload = d.read_json(path)
        payload["_provenance"] = verify_source_payload(payload, source_settings(obj.config))
        payload["_path"] = path.relative_to(ROOT).as_posix()
        obj.payloads[payload["ensemble_hash"]] = payload
        obj.points.add((float.fromhex(payload["nu_mb_raw_hex"]), float.fromhex(payload["V_A_hex"])))
    candidates, roster = [], []
    for nu, va in sorted(obj.points):
        candidate = candidate_from_payload(obj.config, obj.payloads, "Uniform" if nu==0 else "MB", nu, va)
        assert candidate is not None
        d.authenticate(candidate, manifest["protected_hashes"], obj.config)
        candidates.append(candidate)
        roster.append({k:candidate[k] for k in ("family", "nu_raw", "V_A", "C", "w", "ensemble_hash", "source_cache_key", "source_path", "source_moment_route")}
            | dict(source_payload_sha256=d.digest(ROOT/candidate["source_path"])))
    assert len(candidates)==227 and sum(c["family"]=="Uniform" for c in candidates)==30
    fixed = next(c for c in candidates if c["nu_raw"]==.2 and c["V_A"]==1.3833230302980657)
    with OLD_CURVE.open(encoding="utf-8", newline="") as stream:
        distances = sorted({float(r["distance_km"]) for r in csv.DictReader(stream)})
    assert len(distances)==26 and distances[0]==20 and distances[-1]==40
    if not (OUT/"source_roster.csv").exists():
        d.write_csv(OUT/"source_roster.csv", roster)
    chosen, scores, failures, channels, order_checks = [], [], [], [], []
    for distance in distances:
        moments, raw = channel_moments(obj.config, distance)
        channels.append(dict(distance_km=distance, raw_channel=raw, **moments,
            T_eff=moments["mean_sqrt_eta"]**2))
        local = []
        for candidate in candidates:
            try:
                result = d.evaluate_authenticated(candidate, moments, obj.config, manifest["protected_hashes"])
            except ValueError as error:
                failures.append(dict(distance_km=distance, nu_raw=candidate["nu_raw"], V_A=candidate["V_A"],
                    ensemble_hash=candidate["ensemble_hash"], status="FAILED_NUMERICAL_EVALUATION", error=str(error)))
                continue
            row = {k:result[k] for k in ("nu_raw", "V_A", "C", "w", "T_eff", "xi_eff", "N_eff", "a", "b", "Z_star",
                "lambda_1", "lambda_2", "lambda_3", "I_AB", "beta_I_AB", "chi_BE", "SKR", "source_cache_key",
                "source_path", "source_payload_sha256", "ensemble_hash", "MI_orders")}
            row["MI_last_refinement_difference"]=abs(result["MI_orders"][-1]["I_AB"]-result["MI_orders"][-2]["I_AB"])
            row.update(distance_km=distance, family=candidate["family"], K=result["SKR"],
                status="CURRENTLY_VERIFIED_PASS", scientific_model=manifest["scientific_model"],
                fading_noise_included=False, selection="BEST_VALIDATED_CACHE_ONLY")
            scores.append(row);local.append(row)
        selections = [max((r for r in local if r["family"]==family), key=lambda r:r["K"])
            for family in ("Uniform", "MB")]
        fixed_row = next(r for r in local if r["ensemble_hash"]==fixed["ensemble_hash"])
        for scheme, row in zip(style.SCHEMES, (selections[0], fixed_row, selections[1])):
            chosen.append(dict(row, scheme=scheme,
                selection="FIXED_EXISTING_ENSEMBLE" if row is fixed_row else "BEST_VALIDATED_CACHE_ONLY"))
        for family, selected in zip(("Uniform", "MB"), selections):
            pool=[r for r in local if r["family"]==family]
            winners={str(order):max(pool, key=lambda r:next(o["SKR"] for o in r["MI_orders"] if o["order"]==order))["ensemble_hash"] for order in (8,16,32)}
            order_checks.append(dict(distance_km=distance,family=family,winners=winners,
                GH16_32_winner_stable=winners["16"]==winners["32"],
                GH8_16_32_winner_stable=len(set(winners.values()))==1))
        print("DISTANCE",distance,"T_eff",moments["mean_sqrt_eta"]**2,"K",[r["K"] for r in chosen[-3:]],flush=True)
    reference = next(r for r in chosen if r["distance_km"]==21.9393102292 and r["scheme"]==style.SCHEMES[2])
    assert reference["ensemble_hash"]==prior["best_exact"]["ensemble_hash"]
    assert abs(reference["K"]-prior["best_exact"]["SKR"])<5e-12
    assert len(chosen)==78 and len(scores)+len(failures)==227*26
    for row in scores:
        assert abs(row["K"]-(.95*row["I_AB"]-row["chi_BE"]))<1e-14
        assert row["xi_eff"]==.0186 and row["N_eff"]==row["T_eff"]*.0186
        assert row["lambda_1"]>=1 and row["lambda_2"]>=1 and row["lambda_3"]>=1
    d.write_csv(OUT/"skr_vs_distance_three_scheme.csv", chosen)
    d.write_csv(OUT/"all_cached_candidate_evaluations.csv", scores)
    d.write_csv(OUT/"numerical_failures.csv", failures)
    d.save(OUT/"channel_moments_by_distance.json", channels, exclusive=True)
    render(chosen)
    uniform = [r for r in chosen if r["scheme"]==style.SCHEMES[0]]
    positive_uniform = [r for r in uniform if r["K"]>0]
    first_nonpositive = next((r["distance_km"] for r in uniform if r["K"]<=0),None)
    lines=["# Vẽ lại SKR theo khoảng cách với mô hình bỏ phương sai fading", "",
        "Chọn điểm tốt nhất trong cache đã xác thực tại mỗi L, theo yêu cầu người dùng. Giữ ba màu và bố cục log10 của hình gốc.", "",
        f"Cache: {len(candidates)} ensemble, gồm 30 Uniform và 197 MB. 26 khoảng cách cũ, 78 điểm chọn; {len(scores)} đánh giá hợp lệ, {len(failures)} đánh giá không đạt guard được ghi riêng.",
        "Fixed MB giữ nguyên nu_raw=0.2, VA=1.3833230302980657 và đúng ensemble/hash cũ. Các tham số của hai đường tối ưu được chọn riêng ở mỗi L trong ngân hàng cache hữu hạn; không phải nghiệm AO liên tục.", "",
        "Tính lại Eq. (10), luật PDF vật lý chuẩn hóa và ba mômen tại từng khoảng cách bằng producer hiện hành. T_eff=mean_sqrt_eta², xi_eff=0.0186, N_eff=T_eff*xi_ch; b=1+T_eff(VA+xi_ch), Z*=2sqrt(T_eff)C-sqrt(2T_eff*xi_ch*w). Ideal heterodyne R=1, xi_det=0, chi_het=1; beta=0.95; phase/adaptive optics OFF.",
        "MI discrete 256-QAM tính mới GH8/16/32, Holevo tại direct Z_star; cùng ensemble/noise ở hai nhánh. C,w đọc nguyên từ cache; không AP, AO, source generation, Monte Carlo hay nội suy C,w/SKR.", "",
        f"Tại L=21.9393102292 km: MB tốt nhất (nu,VA)=({reference['nu_raw']},{reference['V_A']}), K={reference['K']:.17g}; khớp kết quả continuation đã lưu.",
        f"Uniform trên log10: cuối dương={positive_uniform[-1]['distance_km'] if positive_uniform else None} km; điểm đầu không dương={first_nonpositive} km. Giữ nguyên signed K trong CSV, không vẽ K<=0 lên log và không nối qua điểm không dương.", "",
        "Đây là xấp xỉ Gaussian bỏ phương sai fading, chưa là security lower bound của kênh fading. Optimized trên hình chỉ có nghĩa best in validated cache; không chứng nhận tối ưu liên tục/toàn cục. Frozen model và lifecycle NOT_READY_FOR_PUBLICATION_SCALE_RUNS giữ nguyên.", "",
        "Files: [PNG](../results/skr_vs_distance_effective_channel_no_fading_noise_cache_20261014/skr_vs_distance_three_scheme_log10.png), [PDF](../results/skr_vs_distance_effective_channel_no_fading_noise_cache_20261014/skr_vs_distance_three_scheme_log10.pdf), [CSV](../results/skr_vs_distance_effective_channel_no_fading_noise_cache_20261014/skr_vs_distance_three_scheme.csv).", ""]
    REPORT.write_text("\n".join(lines),encoding="utf-8",newline="\n")
    receipt = dict(status="CURRENTLY_VERIFIED_PASS" if not failures else "COMPLETE_WITH_NUMERICAL_EXCLUSIONS",
        scientific_model=manifest["scientific_model"], distance_count=26, selected_rows=78,
        source_count=227, Uniform_sources=30, MB_sources=197, cached_evaluations=len(scores),
        numerical_failures=failures, GH_winner_checks=order_checks, reference=reference,
        source_roster_sha256=d.digest(OUT/"source_roster.csv"), old_curve_sha256=d.digest(OLD_CURVE),
        new_source_moments_computed=False, new_AP_or_AO=False, interpolation=False,
        channel_and_MI_Holevo_recomputed=True, continuous_or_global_optimum=False,
        certified_fading_security_bound=False, signed_values_preserved=True,
        uniform_last_positive_km=positive_uniform[-1]["distance_km"] if positive_uniform else None,
        uniform_first_nonpositive_km=first_nonpositive, protected_files=len(manifest["protected_hashes"]),
        protected_changes=d.verify_protected(manifest), report_sha256=d.digest(REPORT),
        producer_sha256=d.digest(Path(__file__)), output_sha256={p.name:d.digest(p) for p in OUT.iterdir() if p.is_file()},
        frozen_mismatch_is_preexisting=True, publication_lifecycle="NOT_READY_FOR_PUBLICATION_SCALE_RUNS",
        commit_or_push=False)
    d.save(OUT/"figure_receipt.json",receipt,exclusive=True)
    print("FIGURE_COMPLETE",receipt["status"],"protected",receipt["protected_files"],"failures",len(failures),flush=True)


if __name__=="__main__":main()
