"""Write a positive-SKR-only view of an existing historical distance run."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "results" / "skr_vs_link_distance" / "historical_exact_rerun_current_fixture"
OUTPUT = ROOT / "results" / "skr_vs_link_distance" / "historical_exact_positive_only"
FILES = {
    "Uniform": "historical_exact_uniform_envelope.csv",
    "MB with AO": "historical_exact_mb_ao_envelope.csv",
    "MB without AO": "historical_exact_mb_noao_envelope.csv",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict]) -> None:
    fields = sorted({key for row in rows for key in row}) or ["status"]
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    positive_by_curve = {}
    combined = []
    summary = []
    removed = 0
    for curve, filename in FILES.items():
        rows = read_csv(SOURCE / filename)
        positive = [row for row in rows if float(row["SKR"]) > 0.0]
        removed += len(rows) - len(positive)
        positive_by_curve[curve] = positive
        write_csv(OUTPUT / f"positive_{filename}", positive)
        combined.extend(positive)
        best = max(positive, key=lambda row: float(row["SKR"])) if positive else None
        summary.append({
            "curve": curve,
            "positive_row_count": len(positive),
            "first_positive_distance_km": None if not positive else float(positive[0]["distance_km"]),
            "last_positive_distance_km": None if not positive else float(positive[-1]["distance_km"]),
            "max_positive_SKR": None if best is None else float(best["SKR"]),
            "max_positive_nu_raw": None if best is None else float(best["nu_raw"]),
            "max_positive_V_A": None if best is None else float(best["V_A"]),
            "status": "POSITIVE_ROWS_PLOTTED" if positive else "NO_POSITIVE_ROWS",
        })

    write_csv(OUTPUT / "positive_skr_rows.csv", combined)
    write_csv(OUTPUT / "positive_skr_summary.csv", summary)

    colors = {"Uniform": "#64748b", "MB with AO": "#2563eb", "MB without AO": "#dc2626"}
    figure, ax = plt.subplots(figsize=(9.5, 5.8), dpi=160)
    for curve in FILES:
        rows = positive_by_curve[curve]
        if not rows:
            continue
        ax.plot(
            [float(row["distance_km"]) for row in rows],
            [float(row["SKR"]) for row in rows],
            color=colors[curve],
            marker="o",
            markersize=4,
            linewidth=1.8,
            label=curve,
        )
    ax.axhline(0.0, color="#111827", linewidth=0.9, linestyle=(0, (4, 3)))
    ax.set_ylim(bottom=0.0)
    ax.set_xlabel("Link distance L (km)")
    ax.set_ylabel("SKR (bits/use)")
    ax.set_title("Positive-SKR-only historical exact points", weight="bold")
    ax.ticklabel_format(axis="y", style="sci", scilimits=(0, 0), useMathText=True)
    ax.grid(axis="both", color="#cbd5e1", linewidth=0.6, alpha=0.7)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    if any(positive_by_curve.values()):
        ax.legend(frameon=True)
    omitted = [curve for curve, rows in positive_by_curve.items() if not rows]
    note = "Negative rows omitted; original historical artifacts preserved."
    if omitted:
        note += " No positive rows: " + ", ".join(omitted) + "."
    figure.text(0.5, 0.018, note, ha="center", va="bottom", fontsize=8.5, color="#475569")
    figure.subplots_adjust(left=0.10, right=0.96, bottom=0.15, top=0.90)
    stem = OUTPUT / "skr_positive_only"
    figure.savefig(stem.with_suffix(".png"), dpi=300, facecolor="white")
    figure.savefig(stem.with_suffix(".pdf"), facecolor="white")
    plt.close(figure)

    report = {
        "status": "POSITIVE_SKR_ONLY_VIEW_COMPLETE",
        "source_directory": str(SOURCE),
        "output_directory": str(OUTPUT),
        "negative_rows_removed_from_view": removed,
        "new_source_moments_computed": False,
        "original_artifacts_deleted": False,
        "curves": summary,
    }
    (OUTPUT / "positive_skr_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
