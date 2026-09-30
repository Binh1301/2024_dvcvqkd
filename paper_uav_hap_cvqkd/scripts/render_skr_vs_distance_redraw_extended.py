"""Render the extended exact-tested SKR distance envelope.

The extended envelope is produced by the cache-only diagnostic runner.  This
script only validates existing rows and renders them; it never evaluates a
channel, security term, source moment, candidate, or interpolated crossing.
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
    "revised_uniform_mb_common_feasible_extended_diagnostic"
)
DEFAULT_OUTPUT_DIR = ROOT / "paper_uav_hap_cvqkd" / "results" / (
    "revised_hap_uav_optical_baseline_figure"
)
PROTOCOLS = ("Uniform 256-QAM", "MB-shaped 256-QAM")
COLORS = {"Uniform 256-QAM": "#1769aa", "MB-shaped 256-QAM": "#c62828"}
BINOMIAL_NOTE = "Binomial omitted: no safe current-compatible exact C,w dataset."
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


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def row_at(rows: list[dict[str, str]], protocol: str, distance: float) -> dict[str, str]:
    for row in rows:
        if row["protocol"] == protocol and float(row["distance_km"]) == distance:
            return row
    raise RuntimeError(f"Missing {protocol} at {distance:g} km.")


def load_source() -> tuple[dict, list[dict[str, str]]]:
    report_path = SOURCE_DIR / "revised_uniform_mb_common_feasible_report.json"
    envelope_path = SOURCE_DIR / "diagnostic_distance_envelope.csv"
    summary_path = SOURCE_DIR / "protocol_summary.csv"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    rows = read_csv(envelope_path)
    summaries = read_csv(summary_path)

    if report.get("status") != "COMMON_FEASIBLE_UNIFORM_MB_DISTANCE_EXTENSION_COMPLETE_CACHE_ONLY":
        raise RuntimeError("The source report is not the expected cache-only extension.")
    if report.get("scope") != "DIAGNOSTIC_ONLY":
        raise RuntimeError("The extended source is not diagnostic-only.")
    if report.get("lifecycle") != "NOT_READY_FOR_PUBLICATION_SCALE_RUNS":
        raise RuntimeError("The source lifecycle scope changed unexpectedly.")
    if report.get("new_source_moments_computed") is not False:
        raise RuntimeError("The source report permits new source moments.")
    if report.get("interpolation_used") is not False:
        raise RuntimeError("The source report permits interpolation.")
    if report.get("channel_recomputed_at_each_distance") is not True:
        raise RuntimeError("The source report lacks per-distance channel evidence.")
    if report.get("no_new_source_moments") is not True or report.get("no_new_candidate_generation") is not True:
        raise RuntimeError("The extension provenance is not cache-only.")
    if report.get("candidate_counts", {}).get("Binomial_feasible") != 0:
        raise RuntimeError("Binomial data unexpectedly exists in the extension.")

    if {row["protocol"] for row in rows} != set(PROTOCOLS):
        raise RuntimeError("The extension contains an unexpected protocol.")
    if len(rows) != 2 * len(report["distances_km"]):
        raise RuntimeError("The envelope row count does not match the distance list.")
    if {float(row["distance_km"]) for row in rows} != set(map(float, report["distances_km"])):
        raise RuntimeError("The envelope distances do not match the source report.")
    if {row["protocol"] for row in summaries} != set(PROTOCOLS):
        raise RuntimeError("The protocol summary scope changed unexpectedly.")

    for row in rows:
        if not 0.0 < float(row["V_A"]) <= 1.5 + 1e-12:
            raise RuntimeError("A row violates the common V_A budget.")
        if row["exact_status"] != "SAFE_CURRENT_HASH_MATCHED_EXACT_CW":
            raise RuntimeError("A non-exact row entered the extension.")
        if row["common_budget_feasible"].lower() != "true" or row["peak_constraint_feasible"].lower() != "true":
            raise RuntimeError("A non-feasible row entered the extension.")
        if row["channel_recomputed_at_distance"].lower() != "true":
            raise RuntimeError("A row lacks channel recomputation evidence.")
        if len(row["source_cache_identifier"]) != 64:
            raise RuntimeError("A row lacks a 64-character exact/hash identifier.")

    summary_by_protocol = {row["protocol"]: row for row in summaries}
    uniform_summary = summary_by_protocol[PROTOCOLS[0]]
    mb_summary = summary_by_protocol[PROTOCOLS[1]]
    if float(uniform_summary["last_exact_positive_distance_km"]) != 25.0:
        raise RuntimeError("Uniform last-positive endpoint changed unexpectedly.")
    if float(uniform_summary["first_exact_negative_distance_km"]) != 26.0:
        raise RuntimeError("Uniform first-negative endpoint changed unexpectedly.")
    if float(mb_summary["last_exact_positive_distance_km"]) != 800.0:
        raise RuntimeError("MB last-positive endpoint is not 800 km.")
    if float(mb_summary["first_exact_negative_distance_km"]) != 810.0:
        raise RuntimeError("MB first-negative endpoint is not 810 km.")
    if float(row_at(rows, PROTOCOLS[1], 800.0)["SKR"]) <= 0.0:
        raise RuntimeError("MB 800-km point is not positive.")
    if float(row_at(rows, PROTOCOLS[1], 810.0)["SKR"]) >= 0.0:
        raise RuntimeError("MB 810-km point is not negative.")

    return report, sorted(
        rows,
        key=lambda row: (float(row["distance_km"]), PROTOCOLS.index(row["protocol"])),
    )


def write_table(rows: list[dict[str, str]], path: Path) -> None:
    output_rows = []
    for row in rows:
        output_rows.append(
            {
                "distance_km": row["distance_km"],
                "protocol": row["protocol"],
                "V_A": row["V_A"],
                "nu_raw": row["nu"] if row["protocol"] == PROTOCOLS[1] else "",
                "nu_repo": row["nu_repo"] if row["protocol"] == PROTOCOLS[1] else "",
                "I_AB": row["I_AB"],
                "beta_I_AB": row["beta_I_AB"],
                "chi_BE": row["chi_BE"],
                "SKR": row["SKR"],
                "exact/hash identifier": row["source_cache_identifier"],
                "feasibility status": "COMMON_BUDGET_AND_PEAK_FEASIBLE_EXACT_HASH_MATCHED",
            }
        )
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=TABLE_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(output_rows)


def plot_series(axis, rows: list[dict[str, str]], protocol: str, *, linewidth: float = 1.8):
    selected = [row for row in rows if row["protocol"] == protocol]
    return axis.plot(
        [float(row["distance_km"]) for row in selected],
        [float(row["SKR"]) for row in selected],
        color=COLORS[protocol],
        marker="o",
        markersize=4.0,
        linewidth=linewidth,
        label=protocol,
        zorder=3,
    )[0]


def render_plot(rows: list[dict[str, str]], output_dir: Path) -> tuple[Path, Path]:
    u25 = row_at(rows, PROTOCOLS[0], 25.0)
    u26 = row_at(rows, PROTOCOLS[0], 26.0)
    mb800 = row_at(rows, PROTOCOLS[1], 800.0)
    mb810 = row_at(rows, PROTOCOLS[1], 810.0)
    u22 = row_at(rows, PROTOCOLS[0], 22.0)
    mb22 = row_at(rows, PROTOCOLS[1], 22.0)
    mb25 = row_at(rows, PROTOCOLS[1], 25.0)

    figure, axis = plt.subplots(figsize=(12.0, 8.4), dpi=160)
    figure.suptitle(
        "Positive-SKR vs Link Distance (Diagnostic-Only, Exact-Tested)",
        fontsize=15,
        y=0.975,
    )
    figure.text(
        0.5,
        0.945,
        "Common feasible budget: V_A <= 1.5, AO OFF, phase noise OFF",
        ha="center",
        va="top",
        fontsize=10,
    )
    figure.text(
        0.5,
        0.921,
        "Extended exact-tested distance grid through 1000 km; inset magnifies the MB sign bracket.",
        ha="center",
        va="top",
        fontsize=9,
    )

    for protocol in PROTOCOLS:
        plot_series(axis, rows, protocol)
    axis.axhline(0.0, color="#333333", linestyle="--", linewidth=1.0, label="SKR = 0", zorder=1)
    axis.set_xlabel("Link distance L (km)", fontsize=11)
    axis.set_ylabel("SKR (bits/use)", fontsize=11)
    axis.set_xlim(0.0, 1020.0)
    axis.grid(True, alpha=0.24, linewidth=0.7)
    axis.legend(loc="upper right", frameon=True)

    axis.annotate(
        "Uniform last exact-positive\n25 km",
        xy=(25.0, float(u25["SKR"])),
        xytext=(70.0, 0.024),
        arrowprops={"arrowstyle": "->", "color": COLORS[PROTOCOLS[0]], "lw": 1.2},
        bbox={"boxstyle": "round,pad=0.3", "fc": "white", "ec": COLORS[PROTOCOLS[0]], "alpha": 0.94},
        fontsize=9,
        color=COLORS[PROTOCOLS[0]],
    )
    axis.annotate(
        "Uniform first exact-negative\n26 km",
        xy=(26.0, float(u26["SKR"])),
        xytext=(125.0, -0.004),
        arrowprops={"arrowstyle": "->", "color": COLORS[PROTOCOLS[0]], "lw": 1.2},
        bbox={"boxstyle": "round,pad=0.3", "fc": "white", "ec": COLORS[PROTOCOLS[0]], "alpha": 0.94},
        fontsize=9,
        color=COLORS[PROTOCOLS[0]],
    )
    axis.annotate(
        "MB last exact-positive\n800 km",
        xy=(800.0, float(mb800["SKR"])),
        xytext=(590.0, 0.025),
        arrowprops={"arrowstyle": "->", "color": COLORS[PROTOCOLS[1]], "lw": 1.2},
        bbox={"boxstyle": "round,pad=0.3", "fc": "white", "ec": COLORS[PROTOCOLS[1]], "alpha": 0.94},
        fontsize=9,
        color=COLORS[PROTOCOLS[1]],
    )
    axis.annotate(
        "MB first exact-negative\n810 km",
        xy=(810.0, float(mb810["SKR"])),
        xytext=(690.0, -0.004),
        arrowprops={"arrowstyle": "->", "color": COLORS[PROTOCOLS[1]], "lw": 1.2},
        bbox={"boxstyle": "round,pad=0.3", "fc": "white", "ec": COLORS[PROTOCOLS[1]], "alpha": 0.94},
        fontsize=9,
        color=COLORS[PROTOCOLS[1]],
    )

    inset = axis.inset_axes([0.55, 0.12, 0.40, 0.36])
    near = [row for row in rows if 750.0 <= float(row["distance_km"]) <= 1000.0]
    for protocol in PROTOCOLS:
        plot_series(inset, near, protocol, linewidth=1.5)
    inset.axhline(0.0, color="#333333", linestyle="--", linewidth=0.8)
    inset.set_xlim(750.0, 1010.0)
    inset.set_ylim(-3.5e-11, 4.0e-11)
    inset.set_title("Exact MB sign bracket", fontsize=9)
    inset.set_xlabel("L (km)", fontsize=8)
    inset.set_ylabel("SKR", fontsize=8)
    inset.tick_params(labelsize=7)
    inset.grid(True, alpha=0.25, linewidth=0.5)

    gain22 = float(mb22["SKR"]) - float(u22["SKR"])
    gain25 = float(mb25["SKR"]) - float(u25["SKR"])
    highlights = (
        f"22 km: Uniform={float(u22['SKR']):.10f} | MB={float(mb22['SKR']):.10f} | gain={gain22:.13f} bits/use\n"
        f"25 km: Uniform={float(u25['SKR']):.10f} | MB={float(mb25['SKR']):.10f} | gain={gain25:.13f} bits/use"
    )
    figure.text(0.5, 0.225, highlights, ha="center", va="top", fontsize=9, family="monospace")
    figure.text(
        0.5,
        0.157,
        "MB best feasible exact candidate at 22 and 25 km: V_A=1.3833230303, "
        "nu_raw=0.2, nu_repo=8.5. MB advantage is mainly due to larger beta I_AB.",
        ha="center",
        va="top",
        fontsize=8.8,
    )
    figure.text(
        0.5,
        0.101,
        "Diagnostic-only extended redraw using exact-tested common-feasible candidates only. "
        "No interpolation. No new moments. No rerun of channel/security evaluation.",
        ha="center",
        va="top",
        fontsize=8.8,
    )
    figure.text(0.5, 0.064, BINOMIAL_NOTE, ha="center", va="top", fontsize=9, color="#7c2d12")
    figure.text(
        0.5,
        0.035,
        "Lines connect exact-tested points in distance order; inset values remain exact-tested markers, not a fitted crossing.",
        ha="center",
        va="top",
        fontsize=8.2,
        color="#444444",
    )

    figure.tight_layout(rect=(0.065, 0.27, 0.985, 0.875))
    png_path = output_dir / "skr_vs_distance_redraw_extended.png"
    pdf_path = output_dir / "skr_vs_distance_redraw_extended.pdf"
    figure.savefig(png_path, dpi=300, bbox_inches="tight")
    figure.savefig(pdf_path, bbox_inches="tight")
    plt.close(figure)
    return png_path, pdf_path


def print_summary(report: dict, rows: list[dict[str, str]]) -> None:
    uniform = row_at(rows, PROTOCOLS[0], 25.0)
    uniform_negative = row_at(rows, PROTOCOLS[0], 26.0)
    mb_positive = row_at(rows, PROTOCOLS[1], 800.0)
    mb_negative = row_at(rows, PROTOCOLS[1], 810.0)
    print("Uniform: last exact-positive = 25 km; first exact-negative = 26 km")
    print("MB: last exact-positive = 800 km; first exact-negative = 810 km")
    print(
        "MB loses positive SKR on the exact-tested bracket 800 km to 810 km "
        f"(SKR {float(mb_positive['SKR']):.12g} -> {float(mb_negative['SKR']):.12g})."
    )
    print("MB remains positive 775 km farther than Uniform on the exact-tested endpoints (800 - 25 km).")
    print("The extended figure includes both positivity-loss regions: Uniform 25/26 km and MB 800/810 km.")
    print(
        f"Uniform endpoint SKRs: 25 km={float(uniform['SKR']):.12g}, "
        f"26 km={float(uniform_negative['SKR']):.12g}."
    )
    print(BINOMIAL_NOTE)
    print("No continuous/global optimum or interpolated L_max is claimed.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    report, rows = load_source()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    table_path = args.output_dir / "skr_distance_table_extended.csv"
    write_table(rows, table_path)
    png_path, pdf_path = render_plot(rows, args.output_dir)

    payload = {
        "status": "DIAGNOSTIC_ONLY_EXTENDED_EXACT_POINT_LINE_REDRAW_COMPLETE",
        "source_report_sha256": sha256(SOURCE_DIR / "revised_uniform_mb_common_feasible_report.json"),
        "source_envelope_sha256": sha256(SOURCE_DIR / "diagnostic_distance_envelope.csv"),
        "source_protocol_summary_sha256": sha256(SOURCE_DIR / "protocol_summary.csv"),
        "source_distance_count": len(report["distances_km"]),
        "source_largest_tested_distance_km": max(report["distances_km"]),
        "uniform_endpoint": {"last_exact_positive_km": 25.0, "first_exact_negative_km": 26.0},
        "mb_endpoint": {"last_exact_positive_km": 800.0, "first_exact_negative_km": 810.0},
        "mb_exact_tested_positive_extension_over_uniform_km": 775.0,
        "near_zero_numerical_caveat": (
            "The MB 800/810-km SKRs are O(1e-11) bits/use; this endpoint bracket is "
            "a low-rate diagnostic observation and is not a numerical-convergence or publication claim."
        ),
        "line_semantics": "connect existing exact-tested points in distance order only",
        "new_source_moments_computed": False,
        "channel_or_security_rerun_during_render": False,
        "interpolation_or_extrapolation": False,
        "binomial_note": BINOMIAL_NOTE,
        "output_sha256": {
            table_path.name: sha256(table_path),
            png_path.name: sha256(png_path),
            pdf_path.name: sha256(pdf_path),
        },
    }
    report_path = args.output_dir / "skr_vs_distance_redraw_extended_report.json"
    report_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print_summary(report, rows)
    print(f"Wrote {png_path}")
    print(f"Wrote {pdf_path}")
    print(f"Wrote {table_path}")
    print(f"Wrote {report_path}")


if __name__ == "__main__":
    main()
