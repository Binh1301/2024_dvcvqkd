"""Render the diagnostic-only revised-baseline figures from an exact envelope.

This renderer deliberately consumes the already validated common-feasible exact
cache envelope.  It does not generate source moments, interpolate C,w, or
rerun the channel/security evaluator.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = ROOT / "paper_uav_hap_cvqkd" / "results" / (
    "revised_uniform_mb_common_feasible_diagnostic"
)
DEFAULT_OUTPUT_DIR = ROOT / "paper_uav_hap_cvqkd" / "results" / (
    "revised_hap_uav_optical_baseline_figure"
)
REPORT_NAME = "revised_uniform_mb_common_feasible_report.json"
ENVELOPE_NAME = "diagnostic_distance_envelope.csv"

PLOT_TITLE = "Diagnostic-only SKR vs Distance under Revised Optical Baseline"
PLOT_NOTE = "Common feasible budget: V_A <= 1.5, AO OFF, phase noise OFF"
BINOMIAL_NOTE = "Binomial omitted: no safe current-compatible exact C,w dataset"
PROTOCOLS = ("Uniform 256-QAM", "MB-shaped 256-QAM")
COLORS = {"Uniform 256-QAM": "#1f77b4", "MB-shaped 256-QAM": "#d62728"}
MARKERS = {"Uniform 256-QAM": "o", "MB-shaped 256-QAM": "s"}
TABLE_FIELDS = (
    "distance_km",
    "protocol",
    "V_A",
    "nu_raw",
    "nu_repo",
    "I_AB",
    "beta_I_AB",
    "chi_BE",
    "SKR",
    "exact/hash identifier",
    "feasibility status",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_source() -> tuple[dict, list[dict[str, str]]]:
    report_path = SOURCE_DIR / REPORT_NAME
    envelope_path = SOURCE_DIR / ENVELOPE_NAME
    report = json.loads(report_path.read_text(encoding="utf-8"))
    with envelope_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    if report.get("scope") != "DIAGNOSTIC_ONLY":
        raise RuntimeError("Source report is not diagnostic-only.")
    if report.get("lifecycle") != "NOT_READY_FOR_PUBLICATION_SCALE_RUNS":
        raise RuntimeError("Source report lifecycle scope changed unexpectedly.")
    if report.get("channel_recomputed_at_each_distance") is not True:
        raise RuntimeError("Source report does not confirm channel recomputation.")
    if report.get("new_source_moments_computed") is not False:
        raise RuntimeError("Source report permits new source moments unexpectedly.")
    if report.get("interpolation_used") is not False:
        raise RuntimeError("Source report permits interpolation unexpectedly.")
    if report.get("plot_mode") != "EXACT_MARKERS_ONLY_NO_INTERPOLATION":
        raise RuntimeError("Source plot mode is not exact-marker-only.")

    max_va = float(report["common_feasible_budget"]["max_V_A"])
    for row in rows:
        protocol = row["protocol"]
        if protocol not in PROTOCOLS:
            raise RuntimeError(f"Unexpected protocol in envelope: {protocol!r}")
        va = float(row["V_A"])
        if not 0.0 < va <= max_va + 1e-12:
            raise RuntimeError(f"Budget violation in envelope: {protocol} V_A={va}")
        if row["exact_status"] != "SAFE_CURRENT_HASH_MATCHED_EXACT_CW":
            raise RuntimeError(f"Non-exact row in envelope: {row['exact_status']}")
        if row["common_budget_feasible"].lower() != "true":
            raise RuntimeError("Envelope contains a non-budget-feasible row.")
        if row["peak_constraint_feasible"].lower() != "true":
            raise RuntimeError("Envelope contains a non-peak-feasible row.")
        if row["channel_recomputed_at_distance"].lower() != "true":
            raise RuntimeError("Envelope contains a row without channel recomputation.")
        if not row["source_cache_identifier"]:
            raise RuntimeError("Envelope row has no exact/hash identifier.")

    if not rows:
        raise RuntimeError("The exact envelope is empty.")
    present = {row["protocol"] for row in rows}
    if set(PROTOCOLS) != present:
        raise RuntimeError(f"Expected exactly Uniform and MB rows, found {present!r}")
    required_distances = {float(distance) for distance in range(19, 31)}
    distances = {float(row["distance_km"]) for row in rows}
    if not required_distances.issubset(distances):
        raise RuntimeError("The envelope is missing one or more required integer distances.")

    return report, sorted(
        rows, key=lambda row: (float(row["distance_km"]), PROTOCOLS.index(row["protocol"]))
    )


def render_table(rows: list[dict[str, str]], output_path: Path) -> None:
    output_rows = []
    for row in rows:
        output_rows.append(
            {
                "distance_km": row["distance_km"],
                "protocol": row["protocol"],
                "V_A": row["V_A"],
                "nu_raw": row["nu"] if row["protocol"] == "MB-shaped 256-QAM" else "",
                "nu_repo": row["nu_repo"] if row["protocol"] == "MB-shaped 256-QAM" else "",
                "I_AB": row["I_AB"],
                "beta_I_AB": row["beta_I_AB"],
                "chi_BE": row["chi_BE"],
                "SKR": row["SKR"],
                "exact/hash identifier": row["source_cache_identifier"],
                "feasibility status": (
                    "COMMON_BUDGET_AND_PEAK_FEASIBLE_EXACT_HASH_MATCHED"
                ),
            }
        )
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=TABLE_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(output_rows)


def add_common_note(fig: plt.Figure, *, include_binomial: bool) -> None:
    fig.suptitle(PLOT_TITLE, fontsize=14, y=0.98)
    fig.text(0.5, 0.935, PLOT_NOTE, ha="center", va="top", fontsize=10)
    if not include_binomial:
        fig.text(0.5, 0.905, BINOMIAL_NOTE, ha="center", va="top", fontsize=9, color="#7c2d12")


def render_plot(
    rows: list[dict[str, str]],
    output_dir: Path,
    *,
    y_field: str,
    y_label: str,
    png_name: str,
    pdf_name: str,
    title: str | None = None,
    zero_line: bool = False,
) -> None:
    fig, ax = plt.subplots(figsize=(8.6, 5.5), dpi=160)
    add_common_note(fig, include_binomial=False)
    if title is not None:
        ax.set_title(title, fontsize=11, pad=18)
    for protocol in PROTOCOLS:
        selected = [row for row in rows if row["protocol"] == protocol]
        ax.scatter(
            [float(row["distance_km"]) for row in selected],
            [float(row[y_field]) for row in selected],
            label=protocol,
            color=COLORS[protocol],
            marker=MARKERS[protocol],
            s=44,
            edgecolors="white",
            linewidths=0.6,
            zorder=3,
        )
    if zero_line:
        ax.axhline(0.0, color="#444444", linewidth=0.9, linestyle="--", label="SKR = 0", zorder=1)
    ax.set_xlabel("HAP-UAV link distance [km]")
    ax.set_ylabel(y_label)
    ax.set_xticks(range(19, 31))
    ax.set_xlim(18.5, 30.5)
    ax.grid(True, alpha=0.25, linewidth=0.6)
    ax.legend(frameon=True, loc="best")
    ax.text(
        0.01,
        0.02,
        "Exact-tested markers only; no interpolation or smoothing.",
        transform=ax.transAxes,
        fontsize=8.5,
        color="#444444",
    )
    fig.tight_layout(rect=(0, 0.04, 1, 0.875))
    fig.savefig(output_dir / png_name, dpi=300, bbox_inches="tight")
    fig.savefig(output_dir / pdf_name, bbox_inches="tight")
    plt.close(fig)


def find_row(rows: list[dict[str, str]], protocol: str, distance: float) -> dict[str, str]:
    for row in rows:
        if row["protocol"] == protocol and float(row["distance_km"]) == distance:
            return row
    raise RuntimeError(f"Missing {protocol} row at {distance:g} km")


def positive_endpoints(rows: list[dict[str, str]], protocol: str) -> tuple[float | None, float | None]:
    protocol_rows = sorted(
        (row for row in rows if row["protocol"] == protocol),
        key=lambda row: float(row["distance_km"]),
    )
    positives = [row for row in protocol_rows if float(row["SKR"]) > 0.0]
    negatives = [row for row in protocol_rows if float(row["SKR"]) < 0.0]
    return (
        float(positives[-1]["distance_km"]) if positives else None,
        float(negatives[0]["distance_km"]) if negatives else None,
    )


def print_summary(report: dict, rows: list[dict[str, str]]) -> None:
    for protocol in PROTOCOLS:
        last_positive, first_negative = positive_endpoints(rows, protocol)
        print(
            f"{protocol}: last exact-positive distance: "
            f"{last_positive:g} km; first exact-negative distance: "
            f"{first_negative:g} km" if first_negative is not None else
            f"{protocol}: last exact-positive distance: "
            f"{last_positive:g} km; first exact-negative distance: none"
        )

    for distance in (22.0, 25.0):
        uniform = find_row(rows, "Uniform 256-QAM", distance)
        mb = find_row(rows, "MB-shaped 256-QAM", distance)
        gain = float(mb["SKR"]) - float(uniform["SKR"])
        print(
            f"{distance:g} km: Uniform SKR={float(uniform['SKR']):.12g}; "
            f"MB SKR={float(mb['SKR']):.12g}; gain={gain:.12g}"
        )
        print(
            f"  Uniform beta I_AB={float(uniform['beta_I_AB']):.12g}, "
            f"chi_BE={float(uniform['chi_BE']):.12g}; MB beta I_AB="
            f"{float(mb['beta_I_AB']):.12g}, chi_BE={float(mb['chi_BE']):.12g}"
        )

    for distance in (22.0, 25.0):
        mb = find_row(rows, "MB-shaped 256-QAM", distance)
        print(
            f"Best feasible exact MB parameters at {distance:g} km: "
            f"V_A={float(mb['V_A']):.12g}, nu_raw={float(mb['nu']):.12g}, "
            f"nu_repo={float(mb['nu_repo']):.12g}, "
            f"source/hash={mb['source_cache_identifier']}"
        )

    mb_last_positive, mb_first_negative = positive_endpoints(rows, "MB-shaped 256-QAM")
    if mb_first_negative is None and mb_last_positive == max(
        float(row["distance_km"]) for row in rows
    ):
        print("MB remains positive through the largest exact-tested distance.")

    attribution = report["security_term_attribution"]
    print(
        "Driver: larger beta I_AB is primary "
        f"(positive-contribution sums: beta={attribution['larger_beta_I_AB_positive_contribution_sum']:.12g}, "
        f"lower-chi={attribution['lower_chi_BE_positive_contribution_sum']:.12g})."
    )
    print(BINOMIAL_NOTE)
    print("No continuous/global optimum or precise interpolated L_max is claimed.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for the requested figures and table.",
    )
    args = parser.parse_args()
    report, rows = read_source()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    render_table(rows, args.output_dir / "skr_distance_table.csv")
    render_plot(
        rows,
        args.output_dir,
        y_field="SKR",
        y_label="SKR [bits/use]",
        png_name="skr_vs_distance.png",
        pdf_name="skr_vs_distance.pdf",
        zero_line=True,
    )
    render_plot(
        rows,
        args.output_dir,
        y_field="beta_I_AB",
        y_label=r"$\beta I_{AB}$ [bits/use]",
        png_name="betaIAB_vs_distance.png",
        pdf_name="betaIAB_vs_distance.pdf",
        title=r"$\beta I_{AB}$ versus distance",
    )
    render_plot(
        rows,
        args.output_dir,
        y_field="chi_BE",
        y_label=r"$\chi_{BE}$ [bits/use]",
        png_name="chiBE_vs_distance.png",
        pdf_name="chiBE_vs_distance.pdf",
        title=r"$\chi_{BE}$ versus distance",
    )

    report_payload = {
        "status": "DIAGNOSTIC_ONLY_FIGURE_RENDER_COMPLETE",
        "source_report": str((SOURCE_DIR / REPORT_NAME).relative_to(ROOT)),
        "source_report_sha256": sha256_file(SOURCE_DIR / REPORT_NAME),
        "source_envelope_sha256": sha256_file(SOURCE_DIR / ENVELOPE_NAME),
        "reused_existing_common_feasible_artifact": True,
        "new_source_moments_computed": False,
        "channel_recomputed_at_each_distance_in_source_run": True,
        "interpolation_used": False,
        "plot_mode": "EXACT_MARKERS_ONLY_NO_INTERPOLATION",
        "binomial_status": BINOMIAL_NOTE,
        "main_title": PLOT_TITLE,
        "main_note": PLOT_NOTE,
        "output_sha256": {
            name: sha256_file(args.output_dir / name)
            for name in (
                "skr_vs_distance.png",
                "skr_vs_distance.pdf",
                "skr_distance_table.csv",
                "betaIAB_vs_distance.png",
                "betaIAB_vs_distance.pdf",
                "chiBE_vs_distance.png",
                "chiBE_vs_distance.pdf",
            )
        },
    }
    (args.output_dir / "figure_report.json").write_text(
        json.dumps(report_payload, indent=2) + "\n", encoding="utf-8"
    )
    print_summary(report, rows)
    print(f"Output directory: {args.output_dir}")


if __name__ == "__main__":
    main()
