"""Render a clean symlog redraw from the existing extended exact table only.

This is a visualization-only consumer.  It reads the already exported table
and redraw report, validates their provenance, and never evaluates a channel,
security term, source moment, candidate, or interpolated crossing.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = ROOT / "paper_uav_hap_cvqkd" / "results" / (
    "revised_hap_uav_optical_baseline_figure"
)
DEFAULT_OUTPUT_DIR = SOURCE_DIR
TABLE_PATH = SOURCE_DIR / "skr_distance_table_extended.csv"
SOURCE_REPORT_PATH = SOURCE_DIR / "skr_vs_distance_redraw_extended_report.json"
PROTOCOLS = ("Uniform 256-QAM", "MB-shaped 256-QAM")
COLORS = {"Uniform 256-QAM": "#1769aa", "MB-shaped 256-QAM": "#c62828"}
LINTHRESH = 1e-11
EXPECTED_TITLE = "Positive-SKR vs Link Distance"
EXPECTED_SUBTITLE = "Diagnostic-only, exact-tested, V_A <= 1.5, AO OFF, phase noise OFF"
TABLE_FIELDS = {
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
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def number(row: dict[str, str], field: str) -> float:
    value = float(row[field])
    if not math.isfinite(value):
        raise RuntimeError(f"Non-finite {field} in {row['protocol']} at {row['distance_km']} km.")
    return value


def row_at(rows: list[dict[str, str]], protocol: str, distance: float) -> dict[str, str]:
    for row in rows:
        if row["protocol"] == protocol and float(row["distance_km"]) == distance:
            return row
    raise RuntimeError(f"Missing {protocol} at {distance:g} km.")


def load_source() -> tuple[dict, list[dict[str, str]]]:
    report = json.loads(SOURCE_REPORT_PATH.read_text(encoding="utf-8"))
    rows = read_csv(TABLE_PATH)

    if report.get("status") != "DIAGNOSTIC_ONLY_EXTENDED_EXACT_POINT_LINE_REDRAW_COMPLETE":
        raise RuntimeError("The existing redraw report is not the expected extended diagnostic.")
    if report.get("source_largest_tested_distance_km") != 1000.0:
        raise RuntimeError("The source report does not describe the 1000-km extended grid.")
    if report.get("source_distance_count") != 83:
        raise RuntimeError("The source distance count changed unexpectedly.")
    if report.get("new_source_moments_computed") is not False:
        raise RuntimeError("The source report permits new source moments.")
    if report.get("interpolation_or_extrapolation") is not False:
        raise RuntimeError("The source report permits interpolation or extrapolation.")
    if report.get("channel_or_security_rerun_during_render") is not False:
        raise RuntimeError("The source report does not describe a render-only artifact.")
    if report.get("output_sha256", {}).get(TABLE_PATH.name) != sha256(TABLE_PATH):
        raise RuntimeError("The existing table hash does not match its redraw report.")

    if not rows or set(rows[0]) != TABLE_FIELDS:
        raise RuntimeError("The existing table schema changed unexpectedly.")
    if len(rows) != 2 * report["source_distance_count"]:
        raise RuntimeError("The existing table row count does not match the report.")
    if {row["protocol"] for row in rows} != set(PROTOCOLS):
        raise RuntimeError("The existing table contains an unexpected protocol.")

    distances = sorted({number(row, "distance_km") for row in rows})
    if len(distances) != report["source_distance_count"]:
        raise RuntimeError("The existing table has an unexpected unique-distance count.")
    if not {19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0, 27.0, 28.0, 29.0, 30.0}.issubset(distances):
        raise RuntimeError("The required 19--30 km exact-tested points are incomplete.")

    for row in rows:
        number(row, "V_A")
        if not 0.0 < float(row["V_A"]) <= 1.5 + 1e-12:
            raise RuntimeError("A table row violates the common V_A <= 1.5 budget.")
        for field in ("I_AB", "beta_I_AB", "chi_BE", "SKR"):
            number(row, field)
        if row["feasibility status"] != "COMMON_BUDGET_AND_PEAK_FEASIBLE_EXACT_HASH_MATCHED":
            raise RuntimeError("A non-feasible or non-exact row entered the redraw.")
        identifier = row["exact/hash identifier"]
        if len(identifier) != 64:
            raise RuntimeError("A table row lacks a 64-character exact/hash identifier.")
        try:
            int(identifier, 16)
        except ValueError as exc:
            raise RuntimeError("A table hash identifier is not hexadecimal.") from exc
        if row["protocol"] == PROTOCOLS[1] and (not row["nu_raw"] or not row["nu_repo"]):
            raise RuntimeError("An MB row lacks its nu identifier.")

    uniform = row_at(rows, PROTOCOLS[0], 25.0)
    uniform_negative = row_at(rows, PROTOCOLS[0], 26.0)
    mb = row_at(rows, PROTOCOLS[1], 800.0)
    mb_negative = row_at(rows, PROTOCOLS[1], 810.0)
    if float(uniform["SKR"]) <= 0.0 or float(uniform_negative["SKR"]) >= 0.0:
        raise RuntimeError("Uniform sign endpoints changed unexpectedly.")
    if float(mb["SKR"]) <= 0.0 or float(mb_negative["SKR"]) >= 0.0:
        raise RuntimeError("MB sign endpoints changed unexpectedly.")
    return report, sorted(
        rows,
        key=lambda row: (float(row["distance_km"]), PROTOCOLS.index(row["protocol"])),
    )


def plot_series(axis, rows: list[dict[str, str]], protocol: str, *, linewidth: float = 1.8):
    selected = [row for row in rows if row["protocol"] == protocol]
    return axis.plot(
        [float(row["distance_km"]) for row in selected],
        [float(row["SKR"]) for row in selected],
        color=COLORS[protocol],
        marker="o",
        markersize=3.8,
        linewidth=linewidth,
        label=protocol,
        zorder=3,
    )[0]


def annotate_endpoint(axis, text: str, row: dict[str, str], xytext: tuple[float, float], protocol: str):
    axis.annotate(
        text,
        xy=(float(row["distance_km"]), float(row["SKR"])),
        xycoords="data",
        xytext=xytext,
        textcoords="axes fraction",
        color=COLORS[protocol],
        fontsize=8.5,
        ha="left",
        va="center",
        arrowprops={"arrowstyle": "->", "color": COLORS[protocol], "lw": 1.0},
        zorder=5,
    )


def render_plot(rows: list[dict[str, str]], output_dir: Path) -> tuple[Path, Path]:
    uniform_positive = row_at(rows, PROTOCOLS[0], 25.0)
    uniform_negative = row_at(rows, PROTOCOLS[0], 26.0)
    mb_positive = row_at(rows, PROTOCOLS[1], 800.0)
    mb_negative = row_at(rows, PROTOCOLS[1], 810.0)

    figure, axis = plt.subplots(figsize=(10.8, 6.8), dpi=160)
    figure.suptitle(EXPECTED_TITLE, fontsize=15, y=0.965)
    figure.text(0.5, 0.925, EXPECTED_SUBTITLE, ha="center", va="top", fontsize=9.8)

    axis.set_yscale("symlog", linthresh=LINTHRESH, linscale=1.0, base=10)
    for protocol in PROTOCOLS:
        plot_series(axis, rows, protocol)
    axis.axhline(0.0, color="#333333", linestyle="--", linewidth=1.0, label="SKR = 0", zorder=1)
    axis.set_xlabel("Link distance L (km)", fontsize=10.5)
    axis.set_ylabel("SKR (bits/use)", fontsize=10.5)
    axis.set_xlim(18.0, 1010.0)
    axis.set_xticks([30, 100, 300, 500, 800, 1000])
    axis.grid(True, which="major", alpha=0.22, linewidth=0.7)
    axis.legend(loc="upper right", frameon=True, framealpha=0.9, fontsize=8.5)

    annotate_endpoint(axis, "last + : 25 km", uniform_positive, (0.08, 0.83), PROTOCOLS[0])
    annotate_endpoint(axis, "first - : 26 km", uniform_negative, (0.08, 0.20), PROTOCOLS[0])
    annotate_endpoint(axis, "last + : 800 km", mb_positive, (0.62, 0.88), PROTOCOLS[1])
    annotate_endpoint(axis, "first - : 810 km", mb_negative, (0.62, 0.08), PROTOCOLS[1])

    inset = axis.inset_axes([0.60, 0.10, 0.35, 0.28])
    near = [row for row in rows if 790.0 <= float(row["distance_km"]) <= 820.0]
    inset.set_yscale("symlog", linthresh=LINTHRESH, linscale=1.0, base=10)
    for protocol in PROTOCOLS:
        plot_series(inset, near, protocol, linewidth=1.45)
    inset.axhline(0.0, color="#333333", linestyle="--", linewidth=0.8, zorder=1)
    inset.set_xlim(790.0, 820.0)
    inset.set_ylim(-3.0e-9, 6.0e-12)
    inset.set_title("MB sign bracket", fontsize=8.8, pad=2)
    inset.set_xlabel("L (km)", fontsize=7.5, labelpad=1)
    inset.set_ylabel("SKR", fontsize=7.5, labelpad=1)
    inset.set_xticks([790, 800, 810, 820])
    inset.tick_params(labelsize=7)
    inset.grid(True, which="major", alpha=0.2, linewidth=0.5)

    figure.text(0.5, 0.035, "Exact-tested redraw only; no interpolation.", ha="center", fontsize=8.5, color="#444444")
    figure.subplots_adjust(left=0.095, right=0.985, bottom=0.135, top=0.84)

    png_path = output_dir / "skr_vs_distance_redraw_symlog.png"
    pdf_path = output_dir / "skr_vs_distance_redraw_symlog.pdf"
    figure.savefig(png_path, dpi=300, bbox_inches="tight")
    figure.savefig(pdf_path, bbox_inches="tight")
    plt.close(figure)
    return png_path, pdf_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    source_report, rows = load_source()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    png_path, pdf_path = render_plot(rows, args.output_dir)

    report_path = args.output_dir / "skr_vs_distance_redraw_symlog_report.json"
    payload = {
        "status": "DIAGNOSTIC_ONLY_SYMLOG_REDRAW_COMPLETE",
        "figure_title": EXPECTED_TITLE,
        "figure_subtitle": EXPECTED_SUBTITLE,
        "source_table": {
            "path": str(TABLE_PATH.relative_to(ROOT)),
            "sha256": sha256(TABLE_PATH),
            "row_count": len(rows),
        },
        "source_report": {
            "path": str(SOURCE_REPORT_PATH.relative_to(ROOT)),
            "sha256": sha256(SOURCE_REPORT_PATH),
            "status": source_report["status"],
        },
        "source_distance_count": source_report["source_distance_count"],
        "source_largest_tested_distance_km": source_report["source_largest_tested_distance_km"],
        "y_scale": {"type": "symlog", "base": 10, "linthresh": LINTHRESH},
        "line_semantics": "connect existing exact-tested points in tested distance order",
        "annotations": {
            "uniform": {"last_exact_positive_km": 25.0, "first_exact_negative_km": 26.0},
            "mb": {"last_exact_positive_km": 800.0, "first_exact_negative_km": 810.0},
        },
        "inset": {"title": "MB sign bracket", "distance_range_km": [790.0, 820.0]},
        "new_source_moments_computed": False,
        "new_candidates_created": False,
        "channel_or_security_rerun": False,
        "interpolation_or_extrapolation": False,
        "binomial_note": "Binomial omitted.",
        "near_zero_numerical_caveat": (
            "The MB 800/810-km values are O(1e-11) bits/use and remain low-rate "
            "diagnostic observations, not convergence or publication evidence."
        ),
        "output_sha256": {
            png_path.name: sha256(png_path),
            pdf_path.name: sha256(pdf_path),
        },
    }
    report_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print(f"Validated {len(rows)} existing exact-tested rows from the table/report.")
    print("Uniform endpoints: 25 km positive, 26 km negative.")
    print("MB endpoints: 800 km positive, 810 km negative.")
    print(f"Wrote {png_path}")
    print(f"Wrote {pdf_path}")
    print(f"Wrote {report_path}")


if __name__ == "__main__":
    main()
