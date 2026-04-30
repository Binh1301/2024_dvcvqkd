from dataclasses import replace
from typing import Optional
import os
import sys
import argparse

import numpy as np

DEFAULT_CHANNEL_LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs", "logs")

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from uav_hap.channel.channel_model import channel
    from uav_hap.config import (
        ChannelParams,
        FiniteSizeParams,
        GeometryParams,
        MonteCarloParams,
        NoiseParams,
        SecurityParams,
    )
    from uav_hap.protocols.gm import noise, optimize_modulation_variance, skr_components
    from uav_hap.utils.channel_logging import (
        _loss_db_from_eta,
        _timestamp_for_filename,
        _timestamp_iso,
        log_channel_sample,
        print_channel_summary,
        save_channel_logs,
        save_channel_summary_plot,
    )
else:
    from .channel.channel_model import channel
    from .config import (
        ChannelParams,
        FiniteSizeParams,
        GeometryParams,
        MonteCarloParams,
        NoiseParams,
        SecurityParams,
    )
    from .protocols.gm import noise, optimize_modulation_variance, skr_components
    from .utils.channel_logging import (
        _loss_db_from_eta,
        _timestamp_for_filename,
        _timestamp_iso,
        log_channel_sample,
        print_channel_summary,
        save_channel_logs,
        save_channel_summary_plot,
    )


def _finite_size_skr(i_ab: float, chi_be: float, sec_cfg: SecurityParams, fs_cfg: FiniteSizeParams) -> tuple[float, float]:
    N_block = max(int(fs_cfg.N_block), 1)
    n_block = int(round(float(fs_cfg.n_ratio) * float(N_block))) if fs_cfg.n is None else int(fs_cfg.n)
    n_block = int(np.clip(n_block, 1, N_block))
    epsilon = max(float(fs_cfg.epsilon_PE) + float(fs_cfg.epsilon_EC) + float(fs_cfg.epsilon_PA), 1e-30)
    delta = 7.0 * np.log2(2.0 / epsilon) / np.sqrt(float(n_block))
    skr_val = (float(n_block) / float(N_block)) * (float(sec_cfg.beta) * float(i_ab) - float(chi_be) - delta)
    return float(max(skr_val, 0.0)), float(delta)


def simulate_uav_hap_cvqkd(
    geometry: Optional[GeometryParams] = None,
    channel_params: Optional[ChannelParams] = None,
    noise_params: Optional[NoiseParams] = None,
    security_params: Optional[SecurityParams] = None,
    monte_carlo: Optional[MonteCarloParams] = None,
    finite_size: Optional[FiniteSizeParams] = None,
    L_m: Optional[float] = None,
    sigma_r_m: Optional[float] = None,
    xi_phase: Optional[float] = None,
    N: Optional[int] = None,
    n: Optional[int] = None,
    histogram_bins: Optional[int] = 50,
    enable_logging: bool = False,
    log_every: int = 1,
    logs_dir: str = DEFAULT_CHANNEL_LOG_DIR,
    save_summary_plot: bool = False,
) -> dict:
    geom = GeometryParams() if geometry is None else geometry
    ch_cfg = ChannelParams() if channel_params is None else channel_params
    nz_cfg = NoiseParams() if noise_params is None else noise_params
    sec_cfg = SecurityParams() if security_params is None else security_params
    mc_cfg = MonteCarloParams() if monte_carlo is None else monte_carlo
    fs_cfg = FiniteSizeParams() if finite_size is None else finite_size

    if L_m is not None:
        geom = replace(geom, H_HAP_m=float(geom.H_UAV_m) + float(L_m), tilt_deg=0.0)
    if sigma_r_m is not None:
        ch_cfg = replace(ch_cfg, sigma_r_m=float(sigma_r_m))
    if xi_phase is not None:
        nz_cfg = replace(nz_cfg, xi_phase=float(xi_phase))
    if N is not None:
        mc_cfg = replace(mc_cfg, N=int(N))
    if n is not None:
        fs_cfg = replace(fs_cfg, n=int(n))

    rng = np.random.default_rng(mc_cfg.seed)
    fading = channel(
        geometry=geom,
        channel_params=ch_cfg,
        N=int(mc_cfg.N),
        rng=rng,
        L_override_m=L_m,
    )
    T_samples = np.asarray(fading["T_samples"], dtype=float)

    noise_terms = noise(T_samples=T_samples, noise_params=nz_cfg)
    T_eff = float(fading["T_eff"])
    T_eff_arr = np.array([T_eff], dtype=float)
    noise_terms_eff = noise(T_samples=T_eff_arr, noise_params=nz_cfg)
    comps_eff = skr_components(
        T_samples=T_eff_arr,
        noise_terms=noise_terms_eff,
        security_params=sec_cfg,
        detection=nz_cfg.detection,
        eta_d=noise_terms_eff["eta_d"],
    )
    K_eff_raw = float(comps_eff["SKR"][0])
    K_eff = float(max(K_eff_raw, 0.0))
    K_samples = np.full_like(T_samples, K_eff, dtype=float)
    I_AB_eff = float(comps_eff["I_AB"][0])
    chi_BE_eff = float(comps_eff["chi_BE"][0])
    K_finite, delta = _finite_size_skr(i_ab=I_AB_eff, chi_be=chi_BE_eff, sec_cfg=sec_cfg, fs_cfg=fs_cfg)
    P_out = float(1.0 if K_eff_raw < 0.0 else 0.0)

    result = {
        "K_eff": K_eff,
        "K_finite": K_finite,
        "Delta_finite": delta,
        "P_out": P_out,
        "T_eff": T_eff,
        "T_samples": T_samples,
        "K_samples": K_samples,
        "K_samples_raw": np.full_like(T_samples, K_eff_raw, dtype=float),
        "I_AB_samples": np.full_like(T_samples, I_AB_eff, dtype=float),
        "chi_BE_samples": np.full_like(T_samples, chi_BE_eff, dtype=float),
        "I_AB_eff": I_AB_eff,
        "chi_BE_eff": chi_BE_eff,
        "X_tot_samples": noise_terms["X_tot"],
        "X_line_samples": noise_terms["X_line"],
        "X_D": noise_terms["X_D"],
        "xi_tot": noise_terms["xi_tot"],
        "L_m": fading["L_m"],
        "sigma_r_m": fading["sigma_r_m"],
        "channel_factors": {
            "eta_atm": fading["eta_atm"],
            "eta_geo": fading["eta_geo"],
            "eta_SMF": fading["eta_SMF"],
            "eta_sys": fading["eta_sys"],
        },
        "channel_geometry": {
            "zeta_rad": fading["zeta_rad"],
            "W_L_m": fading["W_L_m"],
            "z_R_m": fading["z_R_m"],
            "x": fading["x"],
            "T0": fading["T0"],
            "T0_amp": fading["T0_amp"],
            "Gamma": fading["Gamma"],
            "R_m": fading["R_m"],
        },
    }

    if sec_cfg.optimize_VA:
        va_opt = optimize_modulation_variance(
            T_eff=float(fading["T_eff"]),
            noise_params=nz_cfg,
            beta=float(sec_cfg.beta),
            VA_min=float(sec_cfg.VA_min),
            VA_max=float(sec_cfg.VA_max),
            VA_points=int(sec_cfg.VA_points),
        )
        result["VA_optimization"] = va_opt

    if histogram_bins is not None and int(histogram_bins) > 0:
        counts, edges = np.histogram(T_samples, bins=int(histogram_bins), range=(0.0, 1.0), density=False)
        result["T_histogram"] = {"counts": counts, "bin_edges": edges}

    if enable_logging:
        step = int(log_every)
        if step <= 0:
            raise ValueError("log_every must be >= 1.")

        sample_count = T_samples.size
        sample_indices = np.arange(0, sample_count, step, dtype=int)
        if sample_count > 0 and (sample_indices.size == 0 or sample_indices[-1] != sample_count - 1):
            sample_indices = np.append(sample_indices, sample_count - 1)

        r_samples = np.asarray(fading["r_samples"], dtype=float)
        eta_point_samples = np.asarray(fading["eta_point_samples"], dtype=float)
        eta_geo = float(fading["eta_geo"])
        eta_atm = float(fading["eta_atm"])
        eta_smf = float(fading["eta_SMF"])
        xi_jitter = float(getattr(nz_cfg, "xi_jitter", 0.0))
        x_tot = np.asarray(noise_terms["X_tot"], dtype=float)
        eta_d = float(noise_terms["eta_d"])
        snr_samples = (
            eta_d * T_samples * float(sec_cfg.VA)
            / np.maximum(1.0 + eta_d * T_samples * x_tot, 1e-15)
        )

        run_ts = _timestamp_for_filename()
        row_ts = _timestamp_iso()
        beam_spot_radius_m = float(fading["W_L_m"])
        receiver_aperture_m = 2.0 * float(fading["aperture_radius_m"])
        sigma_uav_m = float(np.sqrt(max(float(fading["sigma2_UAV_m2"]), 0.0)))
        sigma_turb_m = float(np.sqrt(max(float(fading["sigma2_turb_m2"]), 0.0)))

        rows = []
        for idx in sample_indices:
            rows.append(
                log_channel_sample(
                    sample_id=int(idx),
                    distance_m=float(fading["L_m"]),
                    theta_rad=float(fading["zeta_rad"]),
                    receiver_aperture_m=receiver_aperture_m,
                    beam_spot_radius_m=beam_spot_radius_m,
                    eta_geo=eta_geo,
                    pointing_r_m=float(r_samples[idx]),
                    sigma_r_m=float(fading["sigma_r_m"]),
                    sigma_uav_m=sigma_uav_m,
                    sigma_turb_m=sigma_turb_m,
                    eta_point=float(eta_point_samples[idx]),
                    eta_smf=eta_smf,
                    eta_atm=eta_atm,
                    t_total=float(T_samples[idx]),
                    xi_ch=float(noise_terms["xi_tot"]),
                    xi_det=float(nz_cfg.epsilon_det),
                    xi_phase=float(nz_cfg.xi_phase),
                    xi_jitter=xi_jitter,
                    xi_total=float(noise_terms["xi_tot"]) + xi_jitter,
                    snr=float(snr_samples[idx]),
                    skr=float(K_eff),
                    outage_flag=bool(K_eff_raw < 0.0),
                    timestamp=row_ts,
                )
            )

        csv_path = save_channel_logs(rows=rows, logs_dir=logs_dir, timestamp=run_ts)
        total_loss_db = _loss_db_from_eta(T_samples)
        geo_loss_db = np.full_like(T_samples, _loss_db_from_eta(eta_geo), dtype=float)
        point_loss_db = _loss_db_from_eta(eta_point_samples)
        smf_loss_db = np.full_like(T_samples, _loss_db_from_eta(eta_smf), dtype=float)
        xi_total_samples = np.full_like(T_samples, float(noise_terms["xi_tot"]) + xi_jitter, dtype=float)

        print_channel_summary(
            total_loss_db=total_loss_db,
            geo_loss_db=geo_loss_db,
            point_loss_db=point_loss_db,
            smf_loss_db=smf_loss_db,
            xi_total=xi_total_samples,
            skr_samples=K_samples,
            csv_path=csv_path,
        )

        result["channel_log_csv"] = csv_path
        result["logged_samples"] = len(rows)
        result["log_every"] = step
        if save_summary_plot:
            plot_path = save_channel_summary_plot(
                total_loss_db=total_loss_db,
                point_loss_db=point_loss_db,
                skr_samples=K_samples,
                logs_dir=logs_dir,
            )
            result["channel_summary_plot"] = plot_path

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="UAV-HAP CV-QKD simulation")
    parser.add_argument("--no-plots", action="store_true", help="Run simulation without opening plots")
    parser.add_argument("--log-channel", action="store_true", help="Enable detailed channel CSV logging")
    parser.add_argument("--log-every", type=int, default=1, help="Log every N Monte Carlo samples")
    parser.add_argument("--logs-dir", type=str, default=DEFAULT_CHANNEL_LOG_DIR, help="Directory for channel CSV logs")
    parser.add_argument("--summary-plot", action="store_true", help="Save optional channel_summary.png")
    args = parser.parse_args()

    out = simulate_uav_hap_cvqkd(
        enable_logging=args.log_channel,
        log_every=args.log_every,
        logs_dir=args.logs_dir,
        save_summary_plot=args.summary_plot,
    )
    print(f"K_eff    = {out['K_eff']:.6f} bits/use")
    print(f"K_finite = {out['K_finite']:.6f} bits/use")
    print(f"P_out    = {out['P_out']:.6f}")
    if "channel_log_csv" in out:
        print(f"channel_log_csv = {out['channel_log_csv']}")
    if "channel_summary_plot" in out:
        print(f"channel_summary_plot = {out['channel_summary_plot']}")

    if not args.no_plots:
        if __package__ in (None, ""):
            from uav_hap.plots.performance_plots import example_usage
        else:
            from .plots.performance_plots import example_usage
        example_usage(show=True)


if __name__ == "__main__":
    main()
