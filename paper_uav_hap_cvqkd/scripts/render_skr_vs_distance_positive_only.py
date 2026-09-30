"""Render only positive exact-tested SKR rows from the existing artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from render_skr_vs_distance_redraw_symlog import (
    COLORS,
    DEFAULT_OUTPUT_DIR,
    PROTOCOLS,
    SOURCE_REPORT_PATH,
    TABLE_PATH,
    load_source,
    row_at,
    sha256,
)


TITLE = "Positive-SKR vs Link Distance"
SUBTITLE = "Diagnostic-only, exact-tested, V_A <= 1.5, AO OFF, phase noise OFF"


def plot_series(axis, rows: list[dict[str, str]], protocol: str):
    selected = [row for row in rows if row["protocol"] == protocol]
    if not selected or any(float(row["SKR"]) <= 0.0 for row in selected):
        raise RuntimeError(f"Non-positive or missing plotted rows for {protocol}.")
    return axis.plot(
        [float(row["distance_km"]) for row in selected],
        [float(row["SKR"]) for row in selected],
        color=COLORS[protocol],
        marker="o",
        markersize=4.2,
        linewidth=1.9,
        label=protocol,
        zorder=3,
    )[0]


def render_plot(rows: list[dict[str, str]], output_dir: Path) -> tuple[Path, Path, dict[str, int]]:
    positive_rows = [row for row in rows if float(row["SKR"]) > 0.0]
    counts = {}
    for protocol in PROTOCOLS:
        counts[protocol] = sum(row["protocol"] == protocol for row in positive_rows)
        if counts[protocol] == 0:
            raise RuntimeError(f"No positive rows for {protocol}.")

    uniform_positive = row_at(positive_rows, PROTOCOLS[0], 25.0)
    mb_positive = row_at(positive_rows, PROTOCOLS[1], 800.0)

    positive_values = [float(row["SKR"]) for row in positive_rows]
    figure, axis = plt.subplots(figsize=(10.8, 6.6), dpi=160)
    figure.suptitle(TITLE, fontsize=15, y=0.965)
    figure.text(0.5, 0.925, SUBTITLE, ha="center", va="top", fontsize=9.8)

    axis.set_yscale("log")
    for protocol in PROTOCOLS:
        plot_series(axis, [row for row in positive_rows if row["protocol"] == protocol], protocol)
    axis.set_xlabel("Link distance L (km)", fontsize=10.5)
    axis.set_ylabel("SKR (bits/use)", fontsize=10.5)
    axis.set_xlim(18.0, 820.0)
    axis.set_xticks([30, 100, 300, 500, 800])
    axis.set_ylim(min(positive_values) / 2.0, max(positive_values) * 2.0)
    axis.grid(True, which="both", alpha=0.22, linewidth=0.7)
    axis.legend(loc="upper right", frameon=True, framealpha=0.9, fontsize=8.5)

    axis.annotate(
        "last + : 25 km",
        xy=(float(uniform_positive["distance_km"]), float(uniform_positive["SKR"])),
        xytext=(45.0, 1.5e-3),
        color=COLORS[PROTOCOLS[0]],
        fontsize=8.7,
        arrowprops={"arrowstyle": "->", "color": COLORS[PROTOCOLS[0]], "lw": 1.0},
    )
    axis.text(
        0.08,
        0.49,
        "first - : 26 km",
        transform=axis.transAxes,
        color=COLORS[PROTOCOLS[0]],
        fontsize=8.7,
    )
    axis.annotate(
        "last + : 800 km",
        xy=(float(mb_positive["distance_km"]), float(mb_positive["SKR"])),
        xytext=(610.0, 3.0e-6),
        color=COLORS[PROTOCOLS[1]],
        fontsize=8.7,
        arrowprops={"arrowstyle": "->", "color": COLORS[PROTOCOLS[1]], "lw": 1.0},
    )
    axis.text(
        0.76,
        0.27,
        "first - : 810 km",
        transform=axis.transAxes,
        color=COLORS[PROTOCOLS[1]],
        fontsize=8.7,
    )

    figure.text(
        0.5,
        0.035,
        "Exact-tested redraw only; positive SKR region only; no interpolation.",
        ha="center",
        fontsize=8.5,
        color="#444444",
    )
    figure.subplots_adjust(left=0.095, right=0.985, bottom=0.135, top=0.84)

    png_path = output_dir / "skr_vs_distance_positive_only.png"
    pdf_path = output_dir / "skr_vs_distance_positive_only.pdf"
    figure.savefig(png_path, dpi=300, bbox_inches="tight")
    figure.savefig(pdf_path, bbox_inches="tight")
    plt.close(figure)
    return png_path, pdf_path, counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    source_report, rows = load_source()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    png_path, pdf_path, positive_counts = render_plot(rows, args.output_dir)

    report_path = args.output_dir / "skr_vs_distance_positive_only_report.json"
    payload = {
        "status": "DIAGNOSTIC_ONLY_POSITIVE_ONLY_REDRAW_COMPLETE",
        "figure_title": TITLE,
        "figure_subtitle": SUBTITLE,
        "source_table": {
            "path": str(TABLE_PATH.relative_to(Path(__file__).resolve().parents[2])),
            "sha256": sha256(TABLE_PATH),
            "row_count": len(rows),
        },
        "source_report": {
            "path": str(SOURCE_REPORT_PATH.relative_to(Path(__file__).resolve().parents[2])),
            "sha256": sha256(SOURCE_REPORT_PATH),
            "status": source_report["status"],
        },
        "protocols": list(PROTOCOLS),
        "positive_rows_plotted": positive_counts,
        "negative_rows_plotted": 0,
        "positive_distance_endpoints_km": {
            "uniform_last_positive": 25.0,
            "mb_last_positive": 800.0,
        },
        "sign_annotations": {
            "uniform_first_negative": 26.0,
            "mb_first_negative": 810.0,
        },
        "y_scale": "log",
        "line_semantics": "connect positive exact-tested points in tested distance order",
        "new_source_moments_computed": False,
        "new_candidates_created": False,
        "channel_or_security_rerun": False,
        "interpolation_or_extrapolation": False,
        "binomial_note": "Binomial omitted.",
        "output_sha256": {
            png_path.name: sha256(png_path),
            pdf_path.name: sha256(pdf_path),
        },
    }
    report_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print(f"Validated {len(rows)} existing rows; plotted {sum(positive_counts.values())} positive rows only.")
    print("Uniform: positive through 25 km; first negative annotation at 26 km.")
    print("MB: positive through 800 km; first negative annotation at 810 km.")
    print(f"Wrote {png_path}")
    print(f"Wrote {pdf_path}")
    print(f"Wrote {report_path}")


if __name__ == "__main__":
    main()
