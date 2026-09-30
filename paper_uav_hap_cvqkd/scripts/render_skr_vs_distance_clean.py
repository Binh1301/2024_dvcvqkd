"""Render a clean positive-SKR figure from the existing artifact table only."""

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
    sha256,
)


ROOT = Path(__file__).resolve().parents[2]
TITLE = "SKR versus Link Distance"


def plot_series(axis, rows: list[dict[str, str]], protocol: str) -> None:
    selected = [row for row in rows if row["protocol"] == protocol]
    if not selected or any(float(row["SKR"]) <= 0.0 for row in selected):
        raise RuntimeError(f"Non-positive or missing rows for {protocol}.")
    axis.plot(
        [float(row["distance_km"]) for row in selected],
        [float(row["SKR"]) for row in selected],
        color=COLORS[protocol],
        marker="o",
        markersize=4.2,
        linewidth=1.9,
        label=protocol,
        zorder=3,
    )


def render_plot(rows: list[dict[str, str]], output_dir: Path) -> tuple[Path, Path, dict[str, int]]:
    positive_rows = [row for row in rows if float(row["SKR"]) > 0.0]
    counts = {
        protocol: sum(row["protocol"] == protocol for row in positive_rows)
        for protocol in PROTOCOLS
    }
    if any(count == 0 for count in counts.values()):
        raise RuntimeError("A protocol has no positive rows.")

    values = [float(row["SKR"]) for row in positive_rows]
    figure, axis = plt.subplots(figsize=(11.6, 6.2), dpi=160, facecolor="white")
    axis.set_facecolor("white")
    for protocol in PROTOCOLS:
        plot_series(axis, positive_rows, protocol)

    axis.set_title(TITLE, fontsize=16, fontweight="normal", pad=14)
    axis.set_xlabel("Link distance L (km)", fontsize=11)
    axis.set_ylabel("SKR (bits/use)", fontsize=11)
    axis.set_yscale("log")
    axis.set_xlim(18.0, 820.0)
    axis.set_xticks([30, 100, 300, 500, 800])
    axis.set_ylim(min(values) / 2.0, max(values) * 2.0)
    axis.grid(True, which="major", color="#d9d9d9", linewidth=0.7, alpha=0.7)
    axis.set_axisbelow(True)
    axis.legend(
        loc="upper right",
        frameon=False,
        ncol=2,
        handlelength=2.4,
        columnspacing=1.6,
        fontsize=9.5,
    )
    figure.subplots_adjust(left=0.09, right=0.985, bottom=0.14, top=0.88)

    png_path = output_dir / "skr_vs_distance_clean.png"
    pdf_path = output_dir / "skr_vs_distance_clean.pdf"
    figure.savefig(png_path, dpi=300, bbox_inches="tight", facecolor="white")
    figure.savefig(pdf_path, bbox_inches="tight", facecolor="white")
    plt.close(figure)
    return png_path, pdf_path, counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    source_report, rows = load_source()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    png_path, pdf_path, positive_counts = render_plot(rows, args.output_dir)

    report_path = args.output_dir / "skr_vs_distance_clean_report.json"
    payload = {
        "status": "POSITIVE_ONLY_CLEAN_REDRAW_COMPLETE",
        "figure_title": TITLE,
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
        "protocols": list(PROTOCOLS),
        "positive_rows_plotted": positive_counts,
        "negative_rows_plotted": 0,
        "y_scale": "log",
        "line_semantics": "connect positive exact-tested points in tested distance order",
        "new_source_moments_computed": False,
        "new_candidates_created": False,
        "channel_or_security_rerun": False,
        "interpolation_or_extrapolation": False,
        "binomial_included": False,
        "output_sha256": {
            png_path.name: sha256(png_path),
            pdf_path.name: sha256(pdf_path),
        },
    }
    report_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print(f"Validated {len(rows)} existing rows; plotted {sum(positive_counts.values())} positive rows.")
    print(f"Wrote {png_path}")
    print(f"Wrote {pdf_path}")
    print(f"Wrote {report_path}")


if __name__ == "__main__":
    main()
