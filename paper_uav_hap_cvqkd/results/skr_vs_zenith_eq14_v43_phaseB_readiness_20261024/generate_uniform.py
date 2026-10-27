"""Exactly one approved Uniform job, reusing the validated Python source producer."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
HISTORICAL = ROOT / "results/uniform_positive_skr_manuscript43_20261023"
VA = float.fromhex("0x1.9ffff84830112p+0")


def main():
    if sys.argv[1:] != ["1.6249995399703647"] or float(sys.argv[1]).hex() != VA.hex():
        raise ValueError("Only the explicitly approved binary64 VA is permitted")
    if (OUT / "new_exact_source").exists():
        raise FileExistsError("Exactly one attempt; preserve its outcome")
    sys.path.insert(0, str(HISTORICAL))
    spec = importlib.util.spec_from_file_location("_validated_python_source", HISTORICAL / "source_python_job.py")
    producer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(producer)
    producer.OUT = OUT  # Redirect this module instance only; historical files stay untouched.
    config = producer.base.unconstrained_config()
    ensemble = producer.base.make_ensemble(config, "Uniform", 0., VA)
    p, alpha = ensemble.probabilities[0].numpy(), ensemble.amplitudes[0].numpy()
    assert p.shape == alpha.shape == (256,)
    assert abs(p.sum()-1) < 1e-13 and (p == 1/256).all()
    assert abs(2*(p @ abs(alpha)**2)-VA) < 2e-12
    assert abs(p @ alpha) < 1e-12 and abs(p @ alpha**2) < 1e-12
    identity = producer.base.ensemble_hash(ensemble)
    preflight = dict(VA=VA, VA_hex=VA.hex(), nu_raw_hex=0.0.hex(), ensemble_hash=identity,
        nbar=float(p @ abs(alpha)**2), X_variance=float(p @ (2*alpha.real)**2),
        producer_path=(HISTORICAL / "source_python_job.py").relative_to(ROOT).as_posix(),
        producer_sha256=hashlib.sha256((HISTORICAL / "source_python_job.py").read_bytes()).hexdigest(),
        launcher_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), source_jobs_authorized=1)
    (OUT / "source_job_preflight.json").write_bytes((json.dumps(preflight, indent=2)+"\n").encode())
    producer.main()
    assert producer.base.ensemble_hash(ensemble) == identity


if __name__ == "__main__":
    main()
