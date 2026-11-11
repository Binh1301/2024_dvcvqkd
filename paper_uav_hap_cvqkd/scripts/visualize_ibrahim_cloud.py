"""Generate isolated Algorithm-1 cloud diagnostics, never QKD/SKR evaluations."""
from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.ibrahim_cloud import CloudConfig, CloudSimulator, motion_diagnostic


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def plot_maps(out, name, arrays, titles, c, label, limits, *, binary=False):
    plt.rcParams.update({"font.family": "serif", "font.size": 10, "pdf.fonttype": 42,
                         "ps.fonttype": 42, "axes.linewidth": .7})
    fig, axes = plt.subplots(1, len(arrays), figsize=(3.3 * len(arrays) + .5, 3.35),
                             squeeze=False, layout="constrained")
    extent = (0, c.width_m / 1000, 0, c.height_m / 1000)
    for ax, array, title in zip(axes[0], arrays, titles):
        im = ax.imshow(array, origin="lower", extent=extent, cmap=ListedColormap(["black", "white"]) if binary else "viridis",
                       vmin=limits[0], vmax=limits[1], interpolation="nearest", aspect="equal")
        ax.set(xlabel="x (km)", ylabel="y (km)", title=title)
        if name.startswith(("figure_C", "figure_D")):
            start, end = ((.20, .02) if c.vx_m_s < 0 else (.02, .20))
            ax.annotate("", xy=(end, 1.04), xytext=(start, 1.04), xycoords="axes fraction",
                        arrowprops={"arrowstyle": "->", "color": "black"}, annotation_clip=False)
    colorbar = fig.colorbar(im, ax=list(axes[0]), shrink=.78, pad=.025, label=label)
    if binary:
        colorbar.set_ticks([0, 1], labels=["0: Clear", "1: Cloud"])
    for suffix in ("png", "pdf"):
        fig.savefig(out / f"{name}.{suffix}", dpi=400, bbox_inches="tight")
    plt.close(fig)


def run(config_path, output, reference_pdf=None, gif=False):
    settings = json.loads(config_path.read_text(encoding="utf-8"))
    c = CloudConfig(**settings["simulation"])
    times = settings["snapshot_times_s"]
    if len(times) != 3 or len(set(times)) != 3:
        raise ValueError("exactly three distinct snapshot times required")
    slots = []
    for t in times:
        if not isinstance(t, (int, float)) or not np.isfinite(t) or not 0 <= t <= c.duration_s:
            raise ValueError("snapshot time outside simulation")
        slot = round(t / c.dt_s)
        if not np.isclose(slot * c.dt_s, t, atol=1e-9, rtol=0):
            raise ValueError("snapshot times must lie on time slots")
        slots.append(slot)
    if reference_pdf is not None and not reference_pdf.is_file():
        raise FileNotFoundError(reference_pdf)
    # Refuse to replace previously generated artifacts, including partial runs.
    output.mkdir(parents=True, exist_ok=False)
    tracked = subprocess.check_output(["git", "ls-files", "src", "configs", "docs/FINAL_MODEL_SPEC.md",
                                       "docs/SECURITY_SCOPE_FREEZE.md"], cwd=ROOT, text=True).splitlines()
    protected = {p: sha256(ROOT / p) for p in tracked}
    sim = CloudSimulator(c)
    snapshots, records, animation = {}, [], []
    for slot in range(round(c.duration_s / c.dt_s) + 1):
        frame = sim.frame() if slot == 0 else sim.step()
        if slot in slots:
            snapshots[slot] = frame
        records.append({"time_s": frame.time_s, "coverage": float(frame.mask.mean()),
                        "raw_mean": float(frame.raw_noise.mean()), "raw_std": float(frame.raw_noise.std()),
                        "intensity_mean": float(frame.intensity.mean()),
                        "intensity_clipped_fraction": frame.normalization_clipped_fraction})
        if gif and slot % max(1, round(5 / c.dt_s)) == 0:
            # Independent mask preview, black clear / white cloud, nearest-neighbor only.
            animation.append(Image.fromarray(frame.mask * 255).resize((400, 400), Image.Resampling.NEAREST))
    frames = [snapshots[slot] for slot in slots]
    data = {"time_s": np.array(times), "gamma": np.array(sim.gamma),
            "reference_field": sim.reference_field, "initial_fine": sim.initial_fine,
            "initial_coarse_upsampled": sim.initial_coarse}
    for name in ("raw_noise", "mask", "blurred_noise", "intensity"):
        data[name] = np.stack([getattr(f, name) for f in frames])
    np.savez_compressed(output / "cloud_snapshots.npz", **data)
    with (output / "coverage_timeseries.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    fields = [sim.initial_fine, sim.initial_coarse, sim.reference_field]
    limits = min(a.min() for a in fields), max(a.max() for a in fields)
    plot_maps(output, "figure_A_multiscale", fields,
              ["Fine Gaussian noise", "Upsampled coarse noise", "Combined field at t = 0 s"],
              c, "Gaussian field (a.u.)", limits)
    label = "Normalized Cloud Intensity" if c.normalization == "reference_minmax" else "Blurred Gaussian field (a.u.)"
    intensity_limits = ((0, 1) if c.normalization == "reference_minmax" else
                        (min(f.intensity.min() for f in frames), max(f.intensity.max() for f in frames)))
    # Figure B uses separate colorbars because intensity and binary state have different meanings.
    for suffix, array, title, binary, lim, bar in (
        ("intensity", frames[0].intensity, f"Continuous intensity at t = {times[0]:g} s", False, intensity_limits, label),
        ("mask", frames[0].mask, f"Binary mask at t = {times[0]:g} s", True, (0, 1), "Cloud mask")):
        plot_maps(output, f"figure_B_{suffix}", [array], [title], c, bar, lim, binary=binary)
    titles = [f"t = {t:g} s" for t in times]
    plot_maps(output, "figure_C_dynamic_intensity", [f.intensity for f in frames], titles, c, label, intensity_limits)
    plot_maps(output, "figure_D_dynamic_masks", [f.mask for f in frames], titles, c, "Cloud mask", (0, 1), binary=True)
    if gif:
        animation[0].save(output / "cloud_masks.gif", save_all=True, append_images=animation[1:], duration=100, loop=0)
    coverage = np.array([r["coverage"] for r in records])
    producers = [Path(__file__).resolve(), ROOT / "src/ibrahim_cloud.py", ROOT / "tests/test_ibrahim_cloud.py"]
    report = {"status": "CURRENTLY_VERIFIED_PASS", "scope": "SYNTHETIC_CLOUD_DIAGNOSTIC_ONLY",
              "parameters": asdict(c), "parameter_origin": settings.get("parameter_origin"),
              "snapshot_times_s": times, "gamma_fixed_all_slots": sim.gamma,
              "threshold_reference": "initial raw G0; empirical linear quantile; never recalibrated",
              "normalization_reference_bounds": sim.normalization_bounds,
              "coverage": {"initial": float(coverage[0]), "final": float(coverage[-1]),
                           "time_mean_including_t0": float(coverage.mean()), "minimum": float(coverage.min()),
                           "maximum": float(coverage.max()), "temporal_std": float(coverage.std()),
                           "snapshots": [float(f.mask.mean()) for f in frames], "slots_including_t0": len(records),
                           "scope": "one seeded, correlated mission; no independent-sample confidence interval"},
              "motion": motion_diagnostic(c),
              "max_normalization_clipped_fraction": max(r["intensity_clipped_fraction"] for r in records),
              "wrapping_period_x_s": None if c.vx_m_s == 0 else c.width_m / abs(c.vx_m_s),
              "assumptions": ["independent N(0,1) fine/coarse draws per step; PCG64",
                              "periodic bilinear coarse interpolation with coarse knots every u cells",
                              "periodic first-order semi-Lagrangian advection; repeated steps diffuse structure",
                              "unit-sum Gaussian blur on raw continuous field, with periodic boundary",
                              "fixed reference min-max intensity normalization clips only display intensity",
                              "no meteorological thickness calibration; no physical CLWC or attenuation",
                              "geometric wrapping period is not exact field recurrence under diffusion/evolution"],
              "reference_pdf": None if reference_pdf is None else {"path": str(reference_pdf.resolve()),
                                                                   "sha256": sha256(reference_pdf), "algorithm_pdf_page": 10},
              "provenance": {"git_branch": subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip(),
                             "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                             "config_sha256": sha256(config_path),
                             "producer_sha256": {p.relative_to(ROOT).as_posix(): sha256(p) for p in producers},
                             "numpy": np.__version__, "scipy": __import__("scipy").__version__,
                             "matplotlib": matplotlib.__version__, "python": sys.version},
              "lifecycle": "NOT_READY_FOR_PUBLICATION_SCALE_RUNS",
              "security_model": "UNVALIDATED_SECURITY_MODEL",
              "frozen_spec_actual_sha256": sha256(ROOT / "docs/FINAL_MODEL_SPEC.md"),
              "frozen_spec_historical_sha256": "561fecc97cdf9967034ffd6865c1605804b624b98f47a091e47f17e520a2a7b1",
              "frozen_spec_historical_mismatch": True,
              "scientific_integration": {"QKD_channel_changed": False, "SKR_changed": False,
                                         "finite_size_changed": False, "UAV_optimization_changed": False,
                                         "training_or_final_test_access": False}}
    changed = [p for p, digest in protected.items() if sha256(ROOT / p) != digest]
    report["protected_tracked_files"] = {"count": len(protected), "changed": changed}
    write_json(output / "protected_input_hashes.json", protected)
    if changed or report["motion"]["status"] != "CURRENTLY_VERIFIED_PASS":
        report["status"] = "FAILED"
    write_json(output / "run_report.json", report)
    write_json(output / "config_used.json", settings)
    write_json(output / "artifact_hashes.json", {p.name: sha256(p) for p in sorted(output.iterdir()) if p.is_file()})
    print(json.dumps({"status": report["status"], "output": str(output), "coverage": report["coverage"],
                      "motion": report["motion"]}, indent=2))
    if report["status"] != "CURRENTLY_VERIFIED_PASS":
        raise RuntimeError("diagnostic verification failed; inspect run_report.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs/ibrahim_cloud_demo.json")
    parser.add_argument("--output", type=Path, default=ROOT / "results/ibrahim_cloud_demo_20261111")
    parser.add_argument("--reference-pdf", type=Path)
    parser.add_argument("--gif", action="store_true")
    args = parser.parse_args()
    run(args.config, args.output, args.reference_pdf, args.gif)
