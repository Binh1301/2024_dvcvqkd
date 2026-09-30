"""Redraw the existing diagnostic SKR table as exact-point line plots.

Only existing CSV/JSON artifacts are read.  Lines connect adjacent tested
points; they do not add, smooth, interpolate, or extrapolate data.
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
COMMON_DIR = ROOT / "paper_uav_hap_cvqkd" / "results" / (
    "revised_uniform_mb_common_feasible_diagnostic"
)
FIGURE_DIR = ROOT / "paper_uav_hap_cvqkd" / "results" / (
    "revised_hap_uav_optical_baseline_figure"
)
PROTOCOLS = ("Uniform 256-QAM", "MB-shaped 256-QAM")
COLORS = {"Uniform 256-QAM": "#1769aa", "MB-shaped 256-QAM": "#c62828"}
BINOMIAL_NOTE = "Binomial omitted: no safe current-compatible exact C,w dataset."
REDRAW_NOTE = (
    "Diagnostic-only redraw using exact-tested common-feasible candidates only. "
    "No interpolation. No new moments. No rerun of channel/security evaluation."
)
BUDGET_NOTE = "Common feasible budget: V_A <= 1.5, AO OFF, phase noise OFF."
BASELINE_NOTE = (
    "Revised baseline: w0 = 0.10 m, D_r = 0.55 m, "
    "epsilon_ch = 0.0186 SNU, beta = 0.95, heterodyne, reverse reconciliation."
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def assert_close(left: str, right: str, label: str) -> None:
    if abs(float(left) - float(right)) > 1e-12 * max(1.0, abs(float(right))):
        raise RuntimeError(f"Source mismatch for {label}: {left!r} != {right!r}")


def load_existing_exact_table() -> tuple[dict, list[dict[str, str]]]:
    report_path = COMMON_DIR / "revised_uniform_mb_common_feasible_report.json"
    table_path = FIGURE_DIR / "skr_distance_table.csv"
    envelope_path = COMMON_DIR / "diagnostic_distance_envelope.csv"
    summary_path = COMMON_DIR / "protocol_summary.csv"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    table_rows = read_csv(table_path)
    envelope_rows = read_csv(envelope_path)
    summary_rows = read_csv(summary_path)

    if report.get("scope") != "DIAGNOSTIC_ONLY":
        raise RuntimeError("The source report is not diagnostic-only.")
    if report.get("lifecycle") != "NOT_READY_FOR_PUBLICATION_SCALE_RUNS":
        raise RuntimeError("The source lifecycle scope changed unexpectedly.")
    if report.get("new_source_moments_computed") is not False:
        raise RuntimeError("The source report permits new source moments.")
    if report.get("interpolation_used") is not False:
        raise RuntimeError("The source report permits interpolation.")
    if report.get("channel_recomputed_at_each_distance") is not True:
        raise RuntimeError("The source report lacks channel-recomputation evidence.")
    if report.get("candidate_counts", {}).get("Binomial_feasible") != 0:
        raise RuntimeError("Binomial data unexpectedly exists in the source diagnostic.")

    if len(table_rows) != len(envelope_rows) or len(table_rows) != 26:
        raise RuntimeError("The redraw table must contain the existing 26 exact rows.")
    if {row["protocol"] for row in table_rows} != set(PROTOCOLS):
        raise RuntimeError("The redraw table contains an unexpected protocol.")
    if {row["protocol"] for row in summary_rows} != set(PROTOCOLS):
        raise RuntimeError("The protocol summary does not match the redraw scope.")

    table_by_key = {
        (row["protocol"], float(row["distance_km"])): row for row in table_rows
    }
    envelope_by_key = {
        (row["protocol"], float(row["distance_km"])): row for row in envelope_rows
    }
    if set(table_by_key) != set(envelope_by_key):
        raise RuntimeError("The redraw table and exact envelope have different rows.")

    for key, row in table_by_key.items():
        if not 0.0 < float(row["V_A"]) <= 1.5 + 1e-12:
            raise RuntimeError(f"Common-budget violation at {key!r}.")
        if not row["exact/hash identifier"] or len(row["exact/hash identifier"]) != 64:
            raise RuntimeError(f"Missing exact/hash identifier at {key!r}.")
        if not row["feasibility status"].startswith("COMMON_BUDGET_AND_PEAK_FEASIBLE"):
            raise RuntimeError(f"Non-feasible row at {key!r}.")
        source = envelope_by_key[key]
        assert_close(row["SKR"], source["SKR"], f"SKR {key!r}")
        assert_close(row["I_AB"], source["I_AB"], f"I_AB {key!r}")
        assert_close(row["beta_I_AB"], source["beta_I_AB"], f"beta I_AB {key!r}")
        assert_close(row["chi_BE"], source["chi_BE"], f"chi_BE {key!r}")
        if row["exact/hash identifier"] != source["source_cache_identifier"]:
            raise RuntimeError(f"Hash mismatch at {key!r}.")

    distances = {float(row["distance_km"]) for row in table_rows}
    if not {float(distance) for distance in range(19, 31)}.issubset(distances):
        raise RuntimeError("The redraw table is missing a required integer distance.")

    summary_by_protocol = {row["protocol"]: row for row in summary_rows}
    uniform = summary_by_protocol["Uniform 256-QAM"]
    mb = summary_by_protocol["MB-shaped 256-QAM"]
    if float(uniform["last_exact_positive_distance_km"]) != 25.0:
        raise RuntimeError("Uniform endpoint summary changed unexpectedly.")
    if float(uniform["first_exact_negative_distance_km"]) != 26.0:
        raise RuntimeError("Uniform negative endpoint summary changed unexpectedly.")
    if float(mb["last_exact_positive_distance_km"]) != 30.0 or mb["first_exact_negative_distance_km"]:
        raise RuntimeError("MB endpoint summary changed unexpectedly.")

    return report, sorted(
        table_rows,
        key=lambda row: (float(row["distance_km"]), PROTOCOLS.index(row["protocol"])),
    )


def row_at(rows: list[dict[str, str]], protocol: str, distance: float) -> dict[str, str]:
    for row in rows:
        if row["protocol"] == protocol and float(row["distance_km"]) == distance:
            return row
    raise RuntimeError(f"Missing {protocol} at {distance:g} km.")


def render(rows: list[dict[str, str]], output_dir: Path) -> tuple[Path, Path]:
    uniform = [row for row in rows if row["protocol"] == PROTOCOLS[0]]
    mb = [row for row in rows if row["protocol"] == PROTOCOLS[1]]
    u25 = row_at(rows, PROTOCOLS[0], 25.0)
    u26 = row_at(rows, PROTOCOLS[0], 26.0)
    mb30 = row_at(rows, PROTOCOLS[1], 30.0)
    u22 = row_at(rows, PROTOCOLS[0], 22.0)
    mb22 = row_at(rows, PROTOCOLS[1], 22.0)
    u25_highlight = row_at(rows, PROTOCOLS[0], 25.0)
    mb25 = row_at(rows, PROTOCOLS[1], 25.0)

    fig, ax = plt.subplots(figsize=(10.6, 8.2), dpi=160)
    fig.suptitle(
        "Positive-SKR vs Link Distance (Diagnostic-Only, Exact-Tested)",
        fontsize=15,
        y=0.975,
    )
    fig.text(0.5, 0.944, BASELINE_NOTE, ha="center", va="top", fontsize=9.5)
    fig.text(0.5, 0.918, BUDGET_NOTE, ha="center", va="top", fontsize=10)

    for protocol, selected in ((PROTOCOLS[0], uniform), (PROTOCOLS[1], mb)):
        ax.plot(
            [float(row["distance_km"]) for row in selected],
            [float(row["SKR"]) for row in selected],
            color=COLORS[protocol],
            marker="o",
            markersize=5.5,
            linewidth=2.0,
            label=protocol,
            zorder=3,
        )

    for protocol, distance in (
        (PROTOCOLS[0], 22.0),
        (PROTOCOLS[1], 22.0),
        (PROTOCOLS[0], 25.0),
        (PROTOCOLS[1], 25.0),
    ):
        point = row_at(rows, protocol, distance)
        ax.scatter(
            [distance],
            [float(point["SKR"])],
            s=92,
            facecolors="none",
            edgecolors=COLORS[protocol],
            linewidths=1.5,
            zorder=4,
        )

    ax.axhline(0.0, color="#333333", linestyle="--", linewidth=1.0, label="SKR = 0", zorder=1)
    ax.annotate(
        "Uniform: last exact-positive\n25 km",
        xy=(25.0, float(u25["SKR"])),
        xytext=(23.55, 0.018),
        arrowprops={"arrowstyle": "->", "color": COLORS[PROTOCOLS[0]], "lw": 1.2},
        bbox={"boxstyle": "round,pad=0.3", "fc": "white", "ec": COLORS[PROTOCOLS[0]], "alpha": 0.92},
        fontsize=9,
        color=COLORS[PROTOCOLS[0]],
    )
    ax.annotate(
        "Uniform: first exact-negative\n26 km",
        xy=(26.0, float(u26["SKR"])),
        xytext=(26.45, -0.0048),
        arrowprops={"arrowstyle": "->", "color": COLORS[PROTOCOLS[0]], "lw": 1.2},
        bbox={"boxstyle": "round,pad=0.3", "fc": "white", "ec": COLORS[PROTOCOLS[0]], "alpha": 0.92},
        fontsize=9,
        color=COLORS[PROTOCOLS[0]],
    )
    ax.annotate(
        "MB remains positive through\nlargest exact-tested distance = 30 km",
        xy=(30.0, float(mb30["SKR"])),
        xytext=(27.05, 0.037),
        arrowprops={"arrowstyle": "->", "color": COLORS[PROTOCOLS[1]], "lw": 1.2},
        bbox={"boxstyle": "round,pad=0.3", "fc": "white", "ec": COLORS[PROTOCOLS[1]], "alpha": 0.92},
        fontsize=9,
        color=COLORS[PROTOCOLS[1]],
    )

    ax.set_xlabel("Link distance L (km)", fontsize=11)
    ax.set_ylabel("SKR (bits/use)", fontsize=11)
    ax.set_xticks(range(19, 31))
    ax.set_xlim(18.65, 30.45)
    ax.set_ylim(-0.008, 0.12)
    ax.grid(True, alpha=0.24, linewidth=0.7)
    ax.legend(loc="upper right", frameon=True)
    ax.text(
        0.015,
        0.025,
        "Lines connect exact-tested points in distance order; no intermediate values added.",
        transform=ax.transAxes,
        fontsize=8.5,
        color="#444444",
    )

    gain22 = float(mb22["SKR"]) - float(u22["SKR"])
    gain25 = float(mb25["SKR"]) - float(u25_highlight["SKR"])
    highlight = (
        f"22 km: Uniform={float(u22['SKR']):.10f} | MB={float(mb22['SKR']):.10f} | "
        f"gain={gain22:.13f} bits/use\n"
        f"25 km: Uniform={float(u25_highlight['SKR']):.10f} | MB={float(mb25['SKR']):.10f} | "
        f"gain={gain25:.13f} bits/use"
    )
    mb_params = (
        "MB best feasible exact candidate at 22 and 25 km: "
        "V_A=1.3833230303, nu_raw=0.2, nu_repo=8.5. "
        "Advantage is driven mainly by larger beta I_AB; lower chi_BE helps at 22 km."
    )
    fig.text(0.5, 0.245, highlight, ha="center", va="top", fontsize=9, family="monospace")
    fig.text(0.5, 0.165, mb_params, ha="center", va="top", fontsize=8.8, wrap=True)
    fig.text(0.5, 0.105, REDRAW_NOTE, ha="center", va="top", fontsize=9)
    fig.text(0.5, 0.065, BINOMIAL_NOTE, ha="center", va="top", fontsize=9, color="#7c2d12")

    fig.tight_layout(rect=(0.075, 0.285, 0.985, 0.875))
    png_path = output_dir / "skr_vs_distance_redraw.png"
    pdf_path = output_dir / "skr_vs_distance_redraw.pdf"
    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")
    plt.close(fig)
    return png_path, pdf_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=FIGURE_DIR)
    args = parser.parse_args()
    report, rows = load_existing_exact_table()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    png_path, pdf_path = render(rows, args.output_dir)

    payload = {
        "status": "DIAGNOSTIC_ONLY_EXACT_POINT_LINE_REDRAW_COMPLETE",
        "source_report_sha256": sha256_file(COMMON_DIR / "revised_uniform_mb_common_feasible_report.json"),
        "source_table_sha256": sha256_file(FIGURE_DIR / "skr_distance_table.csv"),
        "source_envelope_sha256": sha256_file(COMMON_DIR / "diagnostic_distance_envelope.csv"),
        "source_protocol_summary_sha256": sha256_file(COMMON_DIR / "protocol_summary.csv"),
        "source_lifecycle": report["lifecycle"],
        "new_source_moments_computed": False,
        "channel_or_security_rerun": False,
        "interpolation_or_extrapolation": False,
        "line_semantics": "connect existing exact-tested points in distance order only",
        "protocols": list(PROTOCOLS),
        "binomial_note": BINOMIAL_NOTE,
        "output_sha256": {
            png_path.name: sha256_file(png_path),
            pdf_path.name: sha256_file(pdf_path),
        },
    }
    (args.output_dir / "skr_vs_distance_redraw_report.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Wrote {png_path}")
    print(f"Wrote {pdf_path}")
    print("Redraw used only the existing exact-tested common-feasible artifacts.")
    print(BINOMIAL_NOTE)


if __name__ == "__main__":
    main()
