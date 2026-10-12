"""Render the existing theta10/D55 three-scheme CSV on a log10 y-axis.

This renderer is data-only: it reads the stored exact SKR values, omits
non-positive points from the log plot, and never calls a physical or security
evaluator.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import sys
import types

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import ticker


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = (
    ROOT
    / "results"
    / "skr_vs_distance_theta10urad_D55cm_unconstrained_three_scheme"
    / "skr_vs_distance_three_scheme.csv"
)
DEFAULT_OUTPUT_DIR = DEFAULT_INPUT.parent
CAPTION = (
    "Only positive SKR values are shown on the logarithmic scale. "
    "Optimized Uniform becomes non-positive between 25 and 25.5 km."
)

SCHEMES = (
    "Optimized Uniform 256-QAM",
    "Fixed MB-shaped 256-QAM",
    "Optimized MB-shaped 256-QAM",
)
COLORS = {
    "Optimized Uniform 256-QAM": "#2563eb",
    "Fixed MB-shaped 256-QAM": "#f28e2b",
    "Optimized MB-shaped 256-QAM": "#d62728",
}
LABELS = {
    "Optimized Uniform 256-QAM": "Optimized Uniform 256-QAM",
    "Fixed MB-shaped 256-QAM": "Fixed MB-shaped 256-QAM",
    "Optimized MB-shaped 256-QAM": "Optimized MB-shaped 256-QAM",
}


def read_rows(path: Path) -> list[dict[str, float | str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return [
            {
                "distance_km": float(raw["distance_km"]),
                "K": float(raw["K"]),
                "scheme": raw["scheme"],
            }
            for raw in csv.DictReader(stream)
        ]


def positive_runs(rows: list[dict[str, float | str]]):
    """Yield positive finite runs; non-positive points create a hard break."""

    run: list[tuple[float, float]] = []
    for row in rows:
        distance = float(row["distance_km"])
        skr = float(row["K"])
        if math.isfinite(distance) and math.isfinite(skr) and skr > 0.0:
            run.append((distance, skr))
        elif run:
            yield run
            run = []
    if run:
        yield run


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def render(input_csv: Path, output_dir: Path) -> tuple[Path, Path, Path]:
    rows = read_rows(input_csv)
    output_dir.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(9.0, 5.6), dpi=160)
    for scheme in SCHEMES:
        scheme_rows = sorted(
            (row for row in rows if row["scheme"] == scheme),
            key=lambda row: float(row["distance_km"]),
        )
        first_run = True
        for run in positive_runs(scheme_rows):
            distances, skr = zip(*run)
            ax.plot(
                distances,
                skr,
                marker="o",
                markersize=3.8,
                linewidth=1.7,
                color=COLORS[scheme],
                label=LABELS[scheme] if first_run else "_nolegend_",
            )
            first_run = False

    ax.set_yscale("log", base=10)
    ax.yaxis.set_major_locator(ticker.LogLocator(base=10))
    ax.yaxis.set_major_formatter(
        ticker.LogFormatterMathtext(base=10, labelOnlyBase=True)
    )
    ax.yaxis.set_minor_locator(ticker.LogLocator(base=10, subs="auto"))
    ax.yaxis.set_minor_formatter(ticker.NullFormatter())
    ax.set_title("SKR versus Link Distance")
    ax.set_xlabel("Link Distance (km)")
    ax.set_ylabel("Secret Key Rate (bits/use)")
    ax.set_xlim(20, 40)
    ax.grid(which="major", alpha=0.25)
    ax.grid(which="minor", alpha=0.12, linewidth=0.5)
    ax.legend(frameon=False)
    fig.tight_layout()

    png = output_dir / "skr_vs_distance_three_scheme_log10.png"
    pdf = output_dir / "skr_vs_distance_three_scheme_log10.pdf"
    fig.savefig(png, dpi=300, facecolor="white")
    # The local Application Control policy blocks fontTools' iup extension.
    # Core PDF fonts keep this renderer-only export independent of that DLL.
    sys.modules.setdefault(
        "fontTools.varLib.iup",
        types.ModuleType("fontTools.varLib.iup"),
    ).iup_delta_optimize = lambda *args, **kwargs: None
    matplotlib.rcParams["pdf.use14corefonts"] = True
    fig.savefig(pdf, facecolor="white")
    plt.close(fig)

    uniform = sorted(
        (row for row in rows if row["scheme"] == SCHEMES[0]),
        key=lambda row: float(row["distance_km"]),
    )
    positive_uniform = [row for row in uniform if float(row["K"]) > 0.0]
    first_nonpositive = next(
        (float(row["distance_km"]) for row in uniform if float(row["K"]) <= 0.0),
        None,
    )
    report = output_dir / "skr_vs_distance_three_scheme_log10_report.json"
    report.write_text(
        json.dumps(
            {
                "status": "DATA_ONLY_LOG10_RENDER_COMPLETE",
                "source_csv": input_csv.name,
                "source_csv_sha256": sha256(input_csv),
                "yscale": "log",
                "base": 10,
                "omission_rule": "plot only exact K > 0; source CSV is unchanged",
                "renderer_only": True,
                "new_source_moments_computed": False,
                "new_candidates_created": False,
                "channel_or_security_rerun": False,
                "interpolation_or_extrapolation": False,
                "figure_caption": CAPTION,
                "uniform_last_positive_distance_km": (
                    float(positive_uniform[-1]["distance_km"])
                    if positive_uniform
                    else None
                ),
                "uniform_first_nonpositive_distance_km": first_nonpositive,
                "plotted_positive_rows": {
                    scheme: sum(
                        1
                        for row in rows
                        if row["scheme"] == scheme and float(row["K"]) > 0.0
                    )
                    for scheme in SCHEMES
                },
                "artifacts": {
                    "png": png.name,
                    "pdf": pdf.name,
                    "renderer": Path(__file__).name,
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return png, pdf, report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-csv", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    png, pdf, report = render(args.input_csv.resolve(), args.output_dir.resolve())
    print(f"input_csv={args.input_csv.resolve()}")
    print("yscale=log base=10")
    print(f"png={png}")
    print(f"pdf={pdf}")
    print(f"report={report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
