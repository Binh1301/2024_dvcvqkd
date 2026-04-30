import csv
import os
from datetime import datetime
from typing import Iterable, Optional

import numpy as np

DEFAULT_LOGS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "outputs", "logs"))


def _timestamp_for_filename(ts: Optional[datetime] = None) -> str:
    t = datetime.utcnow() if ts is None else ts
    return t.strftime("%Y_%m_%d_%H%M%S")


def _timestamp_iso(ts: Optional[datetime] = None) -> str:
    t = datetime.utcnow() if ts is None else ts
    return t.replace(microsecond=0).isoformat()


def _loss_db_from_eta(eta):
    eta_arr = np.asarray(eta, dtype=float)
    out = np.full_like(eta_arr, np.inf, dtype=float)
    pos = eta_arr > 0.0
    out[pos] = -10.0 * np.log10(eta_arr[pos])
    if np.isscalar(eta):
        return float(out.item())
    return out


def log_channel_sample(
    sample_id: int,
    distance_m: float,
    theta_rad: float,
    receiver_aperture_m: float,
    beam_spot_radius_m: float,
    eta_geo: float,
    pointing_r_m: float,
    sigma_r_m: float,
    sigma_uav_m: float,
    sigma_turb_m: float,
    eta_point: float,
    eta_smf: float,
    eta_atm: float,
    t_total: float,
    xi_ch: float,
    xi_det: float,
    xi_phase: float,
    xi_jitter: float,
    xi_total: float,
    snr: float,
    skr: float,
    outage_flag: bool,
    timestamp: str,
) -> dict:
    return {
        "sample_id": int(sample_id),
        "distance_m": float(distance_m),
        "distance_km": float(distance_m) / 1000.0,
        "theta_rad": float(theta_rad),
        "receiver_aperture_m": float(receiver_aperture_m),
        "beam_spot_radius_m": float(beam_spot_radius_m),
        "eta_geo": float(eta_geo),
        "loss_geo_db": _loss_db_from_eta(float(eta_geo)),
        "pointing_r_m": float(pointing_r_m),
        "sigma_r_m": float(sigma_r_m),
        "sigma_uav_m": float(sigma_uav_m),
        "sigma_turb_m": float(sigma_turb_m),
        "eta_point": float(eta_point),
        "loss_point_db": _loss_db_from_eta(float(eta_point)),
        "eta_smf": float(eta_smf),
        "loss_smf_db": _loss_db_from_eta(float(eta_smf)),
        "eta_atm": float(eta_atm),
        "loss_atm_db": _loss_db_from_eta(float(eta_atm)),
        "T_total": float(t_total),
        "loss_total_db": _loss_db_from_eta(float(t_total)),
        "xi_ch": float(xi_ch),
        "xi_det": float(xi_det),
        "xi_phase": float(xi_phase),
        "xi_jitter": float(xi_jitter),
        "xi_total": float(xi_total),
        "snr": float(snr),
        "skr": float(skr),
        "outage_flag": int(bool(outage_flag)),
        "timestamp": timestamp,
    }


def _format_csv_value(value):
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    if isinstance(value, (bool, np.bool_)):
        return "1" if value else "0"
    if isinstance(value, (float, np.floating)):
        if np.isinf(value):
            return "inf"
        if np.isnan(value):
            return "nan"
        return f"{float(value):.6f}"
    return str(value)


def save_channel_logs(rows: Iterable[dict], logs_dir: str = DEFAULT_LOGS_DIR, timestamp: Optional[str] = None) -> str:
    rows_list = list(rows)
    if not rows_list:
        raise ValueError("No rows to save.")

    os.makedirs(logs_dir, exist_ok=True)
    ts = timestamp if timestamp is not None else _timestamp_for_filename()
    out_path = os.path.abspath(os.path.join(logs_dir, f"channel_log_{ts}.csv"))

    fieldnames = list(rows_list[0].keys())
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows_list:
            writer.writerow({k: _format_csv_value(v) for k, v in row.items()})
    return out_path


def print_channel_summary(
    total_loss_db: np.ndarray,
    geo_loss_db: np.ndarray,
    point_loss_db: np.ndarray,
    smf_loss_db: np.ndarray,
    xi_total: np.ndarray,
    skr_samples: np.ndarray,
    csv_path: str,
) -> None:
    finite_total = np.asarray(total_loss_db, dtype=float)
    finite_geo = np.asarray(geo_loss_db, dtype=float)
    finite_point = np.asarray(point_loss_db, dtype=float)
    finite_smf = np.asarray(smf_loss_db, dtype=float)
    xi_arr = np.asarray(xi_total, dtype=float)
    skr_arr = np.asarray(skr_samples, dtype=float)

    print("===== CHANNEL SUMMARY =====")
    print(f"Mean total loss (dB): {np.mean(finite_total):.6f}")
    print(f"Mean geo loss: {np.mean(finite_geo):.6f}")
    print(f"Mean pointing loss: {np.mean(finite_point):.6f}")
    print(f"Mean SMF loss: {np.mean(finite_smf):.6f}")
    print(f"Mean xi_total: {np.mean(xi_arr):.6f}")
    print(f"Mean SKR: {np.mean(skr_arr):.6f}")
    print(f"Outage probability: {np.mean(skr_arr < 0.0):.6f}")
    print(f"CSV saved to: {csv_path}")


def save_channel_summary_plot(
    total_loss_db: np.ndarray,
    point_loss_db: np.ndarray,
    skr_samples: np.ndarray,
    logs_dir: str,
) -> str:
    import matplotlib.pyplot as plt

    os.makedirs(logs_dir, exist_ok=True)
    out_path = os.path.abspath(os.path.join(logs_dir, "channel_summary.png"))

    fig, axes = plt.subplots(1, 3, figsize=(13, 4), dpi=150)
    axes[0].hist(np.asarray(total_loss_db, dtype=float), bins=50, color="#1f77b4", alpha=0.8)
    axes[0].set_title("Total loss (dB)")
    axes[0].set_xlabel("dB")
    axes[0].set_ylabel("Count")

    axes[1].hist(np.asarray(point_loss_db, dtype=float), bins=50, color="#ff7f0e", alpha=0.8)
    axes[1].set_title("Pointing loss (dB)")
    axes[1].set_xlabel("dB")
    axes[1].set_ylabel("Count")

    axes[2].hist(np.asarray(skr_samples, dtype=float), bins=50, color="#2ca02c", alpha=0.8)
    axes[2].set_title("SKR distribution")
    axes[2].set_xlabel("bits/use")
    axes[2].set_ylabel("Count")

    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)
    return out_path


__all__ = [
    "DEFAULT_LOGS_DIR",
    "log_channel_sample",
    "save_channel_logs",
    "print_channel_summary",
    "save_channel_summary_plot",
    "_loss_db_from_eta",
    "_timestamp_for_filename",
    "_timestamp_iso",
]
