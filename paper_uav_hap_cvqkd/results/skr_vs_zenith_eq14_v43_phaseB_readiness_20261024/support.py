"""Local artifact helpers; historical modules are imported without running their CLIs."""
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
PREVIOUS = ROOT / "results/skr_vs_zenith_eq14_v43_20261024"
sys.path.insert(0, str(ROOT))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


prior_model = load("_approved_phase_a_model", PREVIOUS / "model.py")
prior_run = load("_approved_phase_a_run", PREVIOUS / "run.py")
sha, read = prior_run.sha, prior_run.read


def save(path, value):
    Path(path).write_bytes((json.dumps(prior_run.old.clean(value), indent=2,
        ensure_ascii=False, allow_nan=False)+"\n").encode("utf-8"))


def write_csv(path, rows):
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with Path(path).open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def pilot_rows():
    with (PREVIOUS / "source_catalog_coverage.csv").open(encoding="utf-8", newline="") as f:
        rows = [r for r in csv.DictReader(f) if r["pilot_member"] == "True"]
    for r in rows:
        r["VA"], r["nu_raw"] = float.fromhex(r["VA_hex"]), float.fromhex(r["nu_raw_hex"])
        for key in ["C", "w"]:
            r[key] = float(r[key]) if r.get(key) else None
    generated = list((OUT / "new_exact_source/exact_source_cache").glob("*.json"))
    if len(generated) > 1:
        raise ValueError("Only one new source was authorized")
    if generated:
        payload = read(generated[0])
        row = next(r for r in rows if not r.get("source_path"))
        if payload["V_A_hex"] != row["VA_hex"] or payload["nu_mb_raw_hex"] != 0.0.hex():
            raise ValueError("New source VA/nu identity mismatch")
        row.update(source_path=generated[0].relative_to(ROOT).as_posix(), source_sha256=sha(generated[0]),
            ensemble_hash=payload["ensemble_hash"], C=payload["C"], w=payload["w"])
    if len(rows) != 81:
        raise ValueError("Pilot must retain the proposed 81-source roster")
    return rows


def with_ensemble(row):
    return prior_run.source_with_ensemble(row)


def input_digests(source):
    return {"pmf_sha256": hashlib.sha256(source["p"].tobytes()).hexdigest(),
            "amplitude_sha256": hashlib.sha256(source["alpha"].tobytes()).hexdigest()}
