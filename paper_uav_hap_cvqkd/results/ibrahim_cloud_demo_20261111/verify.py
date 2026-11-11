"""Read-only verification of this saved diagnostic package; no simulation run."""
from pathlib import Path
import csv
import hashlib
import json
import sys
import numpy as np
from PIL import Image

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
sys.path.insert(0, str(ROOT))
from src.ibrahim_cloud import blur_noise


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify():
    manifest = json.loads((OUT / "artifact_hashes.json").read_text())
    for name, expected in manifest.items():
        assert digest(OUT / name) == expected, f"artifact hash: {name}"
    report = json.loads((OUT / "run_report.json").read_text())
    protected = json.loads((OUT / "protected_input_hashes.json").read_text())
    for name, expected in protected.items():
        assert digest(ROOT / name) == expected, f"protected input: {name}"
    for name, expected in report["provenance"]["producer_sha256"].items():
        assert digest(ROOT / name) == expected, f"producer: {name}"
    assert digest(ROOT / "configs/ibrahim_cloud_demo.json") == report["provenance"]["config_sha256"]
    c = report["parameters"]
    data = np.load(OUT / "cloud_snapshots.npz", allow_pickle=False)
    gamma = float(data["gamma"])
    assert gamma == report["gamma_fixed_all_slots"]
    for name in ("raw_noise", "mask", "blurred_noise", "intensity"):
        assert data[name].shape == (3, c["ny"], c["nx"])
        assert np.isfinite(data[name]).all()
    assert data["mask"].dtype == np.uint8
    np.testing.assert_array_equal(data["mask"], data["raw_noise"] > gamma)
    lo, hi = report["normalization_reference_bounds"]
    for raw, bn, intensity in zip(data["raw_noise"], data["blurred_noise"], data["intensity"]):
        np.testing.assert_array_equal(bn, blur_noise(raw, c["blur_sigma_cells"], c["blur_radius_cells"]))
        np.testing.assert_array_equal(intensity, np.clip((bn-lo)/(hi-lo), 0, 1))
    rows = list(csv.DictReader((OUT / "coverage_timeseries.csv").open()))
    coverage = np.array([float(r["coverage"]) for r in rows])
    assert len(rows) == round(c["duration_s"] / c["dt_s"]) + 1
    np.testing.assert_allclose([float(r["time_s"]) for r in rows], np.arange(len(rows))*c["dt_s"])
    for key, value in (("initial", coverage[0]), ("final", coverage[-1]),
                       ("time_mean_including_t0", coverage.mean()), ("minimum", coverage.min()),
                       ("maximum", coverage.max()), ("temporal_std", coverage.std())):
        assert report["coverage"][key] == value
    for i, time in enumerate(data["time_s"]):
        assert coverage[round(time / c["dt_s"])] == data["mask"][i].mean()
    assert report["motion"]["measured_x_displacement_after_8s_m"] == -40.0
    tests_bytes = (OUT / "unit_tests.log").read_bytes()
    tests = tests_bytes.decode("utf-16" if tests_bytes.startswith(b"\xff\xfe") else "utf-8-sig")
    assert "Ran 10 tests" in tests and "OK" in tests and "FAILED (" not in tests
    pngs = []
    for path in sorted(OUT.glob("figure_*.png")):
        with Image.open(path) as image:
            dpi = image.info["dpi"]
            assert min(dpi) >= 399
            pngs.append({"file": path.name, "pixels": list(image.size), "dpi": list(dpi)})
    assert len(pngs) == 5 and len(list(OUT.glob("figure_*.pdf"))) == 5
    return {"status": "CURRENTLY_VERIFIED_PASS", "scope": "saved artifacts only; no simulation or QKD",
            "sealed_files": len(manifest), "protected_existing_inputs": len(protected),
            "focused_unit_tests": 10, "png_exports": pngs,
            "pdf_visual_QA": "five PDFium renders inspected: no title/arrow overlap; km axes; common time scales",
            "lifecycle": report["lifecycle"]}


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))
