import csv
from datetime import datetime
from pathlib import Path
from typing import Iterable, Mapping, Optional, Sequence

import numpy as np

DEFAULT_LOGS_DIR = Path(__file__).resolve().parent.parent / "outputs" / "logs"
DEFAULT_DEBUG_LOGS_DIR = Path("logs")

NOISE_LOG_FIELDS = [
    "run_id",
    "timestamp",
    "distance_km",
    "T_eff",
    "eta_atm",
    "eta_geo",
    "chi_line",
    "chi_hom",
    "chi_tot",
    "X_tot",
    "epsilon_bg",
    "epsilon_RIN_s",
    "epsilon_mod",
    "epsilon_ch",
    "epsilon_det",
    "eta_det",
    "V_ele",
]

LOSS_LOG_FIELDS = [
    "run_id",
    "timestamp",
    "distance_km",
    "visibility_km",
    "lambda_nm",
    "xi_km_inv",
    "loss_db_per_km",
    "L_link_km",
    "eta_atm",
    "loss_total_db",
    "eta_sys",
    "eta_geo",
    "T0",
]

FADING_LOG_FIELDS = [
    "run_id",
    "timestamp",
    "distance_km",
    "sigma_r",
    "sigma_s",
    "R",
    "Gamma",
    "N_samples",
    "mean_r",
    "std_r",
    "min_r",
    "max_r",
    "mean_Ti",
    "std_Ti",
    "min_Ti",
    "max_Ti",
    "T_eff",
]

SKR_LOG_FIELDS = [
    "run_id",
    "timestamp",
    "distance_km",
    "V_A",
    "beta",
    "I_AB",
    "chi_BE",
    "Delta",
    "epsilon_total",
    "n_block",
    "N_block",
    "SKR",
    "SKR_clipped",
]

SUMMARY_LOG_FIELDS = [
    "run_id",
    "timestamp",
    "distance_km",
    "T_eff",
    "chi_tot",
    "eta_atm",
    "loss_total_db",
    "SKR",
    "status",
]

FADING_SAMPLES_LOG_FIELDS = [
    "sample_id",
    "distance_km",
    "r_i",
    "eta_point_i",
    "T_i",
    "loss_total_db_i",
    "chi_line_i",
    "chi_tot_i",
    "X_tot_i",
    "I_AB_i",
    "chi_BE_i",
    "SKR_i",
    "SKR_clipped_i",
]


def _timestamp_for_filename(ts: Optional[datetime] = None) -> str:
    t = datetime.utcnow() if ts is None else ts
    return t.strftime("%Y_%m_%d_%H%M%S")


def _timestamp_iso(ts: Optional[datetime] = None) -> str:
    t = datetime.utcnow() if ts is None else ts
    return t.replace(microsecond=0).isoformat()


def make_run_id(ts: Optional[datetime] = None) -> str:
    t = datetime.now() if ts is None else ts
    return t.strftime("%Y%m%d_%H%M%S")


def format_timestamp(ts: Optional[datetime] = None) -> str:
    t = datetime.now() if ts is None else ts
    return t.strftime("%Y-%m-%d %H:%M:%S")


def ensure_log_dir(logs_dir: str | Path = DEFAULT_DEBUG_LOGS_DIR) -> Path:
    log_path = Path(logs_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    return log_path


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


def _format_csv_value(value, precision: int = 6) -> str:
    if value is None:
        return "nan"
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    if isinstance(value, (bool, np.bool_)):
        return "1" if value else "0"
    if isinstance(value, (float, np.floating)):
        if np.isnan(value):
            return "nan"
        if np.isposinf(value):
            return "inf"
        if np.isneginf(value):
            return "-inf"
        return f"{float(value):.{precision}f}"
    return str(value)


def append_csv(
    file_path: str | Path,
    rows: Mapping[str, object] | Iterable[Mapping[str, object]],
    fieldnames: Sequence[str],
) -> Path:
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(rows, Mapping):
        rows_to_write = [dict(rows)]
    else:
        rows_to_write = [dict(row) for row in rows]

    if not rows_to_write:
        return path

    write_header = not path.exists() or path.stat().st_size == 0
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames))
        if write_header:
            writer.writeheader()
        for row in rows_to_write:
            writer.writerow({name: _format_csv_value(row.get(name, np.nan), precision=10) for name in fieldnames})
    return path


def log_noise(
    run_id: str,
    timestamp: str,
    distance_km: float,
    T_eff: float,
    eta_atm: float,
    eta_geo: float,
    chi_line: float,
    chi_hom: float,
    chi_tot: float,
    X_tot: float,
    epsilon_bg: float,
    epsilon_RIN_s: float,
    epsilon_mod: float,
    epsilon_ch: float,
    epsilon_det: float,
    eta_det: float,
    V_ele: float,
    logs_dir: str | Path = DEFAULT_DEBUG_LOGS_DIR,
) -> Path:
    row = {
        "run_id": run_id,
        "timestamp": timestamp,
        "distance_km": distance_km,
        "T_eff": T_eff,
        "eta_atm": eta_atm,
        "eta_geo": eta_geo,
        "chi_line": chi_line,
        "chi_hom": chi_hom,
        "chi_tot": chi_tot,
        "X_tot": X_tot,
        "epsilon_bg": epsilon_bg,
        "epsilon_RIN_s": epsilon_RIN_s,
        "epsilon_mod": epsilon_mod,
        "epsilon_ch": epsilon_ch,
        "epsilon_det": epsilon_det,
        "eta_det": eta_det,
        "V_ele": V_ele,
    }
    return append_csv(ensure_log_dir(logs_dir) / "noise_log.csv", row, NOISE_LOG_FIELDS)


def log_loss(
    run_id: str,
    timestamp: str,
    distance_km: float,
    visibility_km: float,
    lambda_nm: float,
    xi_km_inv: float,
    loss_db_per_km: float,
    L_link_km: float,
    eta_atm: float,
    loss_total_db: float,
    eta_sys: float,
    eta_geo: float,
    T0: float,
    logs_dir: str | Path = DEFAULT_DEBUG_LOGS_DIR,
) -> Path:
    row = {
        "run_id": run_id,
        "timestamp": timestamp,
        "distance_km": distance_km,
        "visibility_km": visibility_km,
        "lambda_nm": lambda_nm,
        "xi_km_inv": xi_km_inv,
        "loss_db_per_km": loss_db_per_km,
        "L_link_km": L_link_km,
        "eta_atm": eta_atm,
        "loss_total_db": loss_total_db,
        "eta_sys": eta_sys,
        "eta_geo": eta_geo,
        "T0": T0,
    }
    return append_csv(ensure_log_dir(logs_dir) / "loss_log.csv", row, LOSS_LOG_FIELDS)


def log_fading(
    run_id: str,
    timestamp: str,
    distance_km: float,
    sigma_r: float,
    sigma_s: float,
    R: float,
    Gamma: float,
    N_samples: int,
    mean_r: float,
    std_r: float,
    min_r: float,
    max_r: float,
    mean_Ti: float,
    std_Ti: float,
    min_Ti: float,
    max_Ti: float,
    T_eff: float,
    logs_dir: str | Path = DEFAULT_DEBUG_LOGS_DIR,
) -> Path:
    row = {
        "run_id": run_id,
        "timestamp": timestamp,
        "distance_km": distance_km,
        "sigma_r": sigma_r,
        "sigma_s": sigma_s,
        "R": R,
        "Gamma": Gamma,
        "N_samples": N_samples,
        "mean_r": mean_r,
        "std_r": std_r,
        "min_r": min_r,
        "max_r": max_r,
        "mean_Ti": mean_Ti,
        "std_Ti": std_Ti,
        "min_Ti": min_Ti,
        "max_Ti": max_Ti,
        "T_eff": T_eff,
    }
    return append_csv(ensure_log_dir(logs_dir) / "fading_log.csv", row, FADING_LOG_FIELDS)


def log_skr(
    run_id: str,
    timestamp: str,
    distance_km: float,
    V_A: float,
    beta: float,
    I_AB: float,
    chi_BE: float,
    Delta: float,
    epsilon_total: float,
    n_block: int,
    N_block: int,
    SKR: float,
    SKR_clipped: float,
    logs_dir: str | Path = DEFAULT_DEBUG_LOGS_DIR,
) -> Path:
    row = {
        "run_id": run_id,
        "timestamp": timestamp,
        "distance_km": distance_km,
        "V_A": V_A,
        "beta": beta,
        "I_AB": I_AB,
        "chi_BE": chi_BE,
        "Delta": Delta,
        "epsilon_total": epsilon_total,
        "n_block": n_block,
        "N_block": N_block,
        "SKR": SKR,
        "SKR_clipped": SKR_clipped,
    }
    return append_csv(ensure_log_dir(logs_dir) / "skr_log.csv", row, SKR_LOG_FIELDS)


def log_summary(
    run_id: str,
    timestamp: str,
    distance_km: float,
    T_eff: float,
    chi_tot: float,
    eta_atm: float,
    loss_total_db: float,
    SKR: float,
    status: str,
    logs_dir: str | Path = DEFAULT_DEBUG_LOGS_DIR,
) -> Path:
    row = {
        "run_id": run_id,
        "timestamp": timestamp,
        "distance_km": distance_km,
        "T_eff": T_eff,
        "chi_tot": chi_tot,
        "eta_atm": eta_atm,
        "loss_total_db": loss_total_db,
        "SKR": SKR,
        "status": status,
    }
    return append_csv(ensure_log_dir(logs_dir) / "summary_log.csv", row, SUMMARY_LOG_FIELDS)


def log_fading_samples(
    run_id: str,
    distance_km: float,
    r_samples,
    T_samples,
    eta_point_samples=None,
    chi_line_samples=None,
    chi_tot_samples=None,
    x_tot_samples=None,
    i_ab_samples=None,
    chi_be_samples=None,
    skr_samples=None,
    logs_dir: str | Path = DEFAULT_DEBUG_LOGS_DIR,
    max_samples: int = 5000,
) -> Path:
    r_arr = np.asarray(r_samples, dtype=float)
    t_arr = np.asarray(T_samples, dtype=float)
    sample_count = int(min(max_samples, r_arr.size, t_arr.size))

    def _optional_array(values):
        if values is None:
            return None
        return np.asarray(values, dtype=float)

    eta_point_arr = _optional_array(eta_point_samples)
    chi_line_arr = _optional_array(chi_line_samples)
    chi_tot_arr = _optional_array(chi_tot_samples)
    x_tot_arr = _optional_array(x_tot_samples)
    i_ab_arr = _optional_array(i_ab_samples)
    chi_be_arr = _optional_array(chi_be_samples)
    skr_arr = _optional_array(skr_samples)

    rows = []
    for idx in range(sample_count):
        skr_value = float(skr_arr[idx]) if skr_arr is not None else float("nan")
        rows.append(
            {
                "sample_id": idx,
                "distance_km": distance_km,
                "r_i": r_arr[idx],
                "eta_point_i": float(eta_point_arr[idx]) if eta_point_arr is not None else float("nan"),
                "T_i": t_arr[idx],
                "loss_total_db_i": _loss_db_from_eta(float(t_arr[idx])),
                "chi_line_i": float(chi_line_arr[idx]) if chi_line_arr is not None else float("nan"),
                "chi_tot_i": float(chi_tot_arr[idx]) if chi_tot_arr is not None else float("nan"),
                "X_tot_i": float(x_tot_arr[idx]) if x_tot_arr is not None else float("nan"),
                "I_AB_i": float(i_ab_arr[idx]) if i_ab_arr is not None else float("nan"),
                "chi_BE_i": float(chi_be_arr[idx]) if chi_be_arr is not None else float("nan"),
                "SKR_i": skr_value,
                "SKR_clipped_i": max(skr_value, 0.0) if np.isfinite(skr_value) else float("nan"),
            }
        )
    out_path = ensure_log_dir(logs_dir) / f"fading_samples_{run_id}.csv"
    return append_csv(out_path, rows, FADING_SAMPLES_LOG_FIELDS)


def save_channel_logs(rows: Iterable[dict], logs_dir: str | Path = DEFAULT_LOGS_DIR, timestamp: Optional[str] = None) -> str:
    rows_list = list(rows)
    if not rows_list:
        raise ValueError("No rows to save.")

    log_dir = Path(logs_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    ts = timestamp if timestamp is not None else _timestamp_for_filename()
    out_path = log_dir / f"channel_log_{ts}.csv"

    fieldnames = list(rows_list[0].keys())
    with out_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows_list:
            writer.writerow({k: _format_csv_value(v) for k, v in row.items()})
    return str(out_path.resolve())


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
    logs_dir: str | Path,
) -> str:
    import matplotlib.pyplot as plt

    log_dir = Path(logs_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    out_path = log_dir / "channel_summary.png"

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
    return str(out_path.resolve())


__all__ = [
    "DEFAULT_LOGS_DIR",
    "DEFAULT_DEBUG_LOGS_DIR",
    "NOISE_LOG_FIELDS",
    "LOSS_LOG_FIELDS",
    "FADING_LOG_FIELDS",
    "SKR_LOG_FIELDS",
    "SUMMARY_LOG_FIELDS",
    "FADING_SAMPLES_LOG_FIELDS",
    "append_csv",
    "ensure_log_dir",
    "format_timestamp",
    "log_channel_sample",
    "log_fading",
    "log_fading_samples",
    "log_loss",
    "log_noise",
    "log_skr",
    "log_summary",
    "make_run_id",
    "save_channel_logs",
    "print_channel_summary",
    "save_channel_summary_plot",
    "_loss_db_from_eta",
    "_timestamp_for_filename",
    "_timestamp_iso",
]
