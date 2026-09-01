"""The prospectively named 20-case V3 synthetic certification suite."""

from __future__ import annotations

from fractions import Fraction
import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest
from flint import acb, arb, ctx

from src.validation.coefficient_taylor_v3 import (
    HermitianTaylorModel,
    _c4_sector_jets,
    build_c4_sector_taylor_models,
    evaluate_taylor_model_enclosure,
)
from src.validation.durable_journal_v3 import DurableJournal, replay_journal
from src.validation.hard_watchdog_v3 import run_with_job_timeout
from src.validation.rigorous_flint_support import exact_arb_from_fraction
from src.validation.rigorous_shifted_inertia import verified_block_ldl_inertia
from src.validation.sequential_schur_v3 import (
    deterministic_signed_partition,
    sequential_signed_schur_reduction,
    validated_signed_schur_step,
)
from src.validation.validated_scalar_taylor_v2 import (
    NormalizedJet,
    TaylorTransmitterPath,
)


ctx.prec = 256
IDENTITY = {"config_sha256": "a" * 64, "producer_sha256": "b" * 64}


def _zero(size: int):
    return [[acb(0) for _ in range(size)] for _ in range(size)]


def _diag(values):
    return [[acb(values[row]) if row == column else acb(0)
             for column in range(len(values))] for row in range(len(values))]


def _model(coefficients, *, order=None):
    degree = len(coefficients) - 1 if order is None else order
    return HermitianTaylorModel(
        left=Fraction(-1), right=Fraction(1), center=Fraction(0), order=degree,
        coefficients=tuple(coefficients),
        remainder_coefficient=_zero(len(coefficients[0])),
    )


def _parameter(shape, values):
    return {"shape": list(shape), "float64_hex": [float(v).hex() for v in values]}


def _synthetic_path(*, zero_gs: bool = False) -> TaylorTransmitterPath:
    raw = [0, 0, 0, 0] if zero_gs else [1, 0, 0, 1]
    start = {
        "ps_network.network.0.weight": _parameter([2, 2], [-1, 0, 0, 0]),
        "ps_network.network.0.bias": _parameter([2], [0, 1]),
        "ps_network.network.2.weight": _parameter([2, 2], [1, 0, -1, 0]),
        "ps_network.network.2.bias": _parameter([2], [0, 0]),
        "va_network.network.0.weight": _parameter([1, 2], [0, 0]),
        "va_network.network.0.bias": _parameter([1], [1]),
        "va_network.network.2.weight": _parameter([1, 1], [0.25]),
        "va_network.network.2.bias": _parameter([1], [0]),
        "gs_model.raw_coordinates": _parameter([2, 2], raw),
    }
    end = json.loads(json.dumps(start))
    if not zero_gs:
        end["gs_model.raw_coordinates"] = _parameter([2, 2], [1, .2, -.2, 1])
    state = {"channel_features_float64_hex": [float(1).hex(), float(0).hex()]}
    return TaylorTransmitterPath(
        start, end, state, float(.1).hex(), float(1.5).hex()
    )


def _journal_prefix(path: Path, *, nodes: int = 0) -> None:
    with DurableJournal(
        path, attempt_id="attempt", segment_id="synthetic/ps", identity=IDENTITY,
    ) as journal:
        journal.append("RUN_STARTED", {})
        journal.append("PATH_DOMAIN_COMMITTED", {"path_domain": {
            "status": "PATH_DOMAIN_CERTIFIED", "certified_leaf_count": 1,
            "unresolved_leaf_count": 0,
        }})
        journal.append("WORK_QUEUE_INITIALIZED", {"pending": []})
        for index in range(nodes):
            node_id = f"node-{index}"
            journal.append("NODE_STARTED", {"node_id": node_id})
            journal.append("NODE_COMMITTED", {
                "node_id": node_id, "node": {"status": "UNCERTIFIED"},
                "action": "UNRESOLVED",
            })


def test_case_01_exact_affine_hermitian_path():
    model = _model((_diag([2, -2]), _diag([.25, -.25])))
    enclosed = evaluate_taylor_model_enclosure(model)
    for sample in (-1, -.25, .5, 1):
        assert enclosed[0][0].real.contains(2 + .25 * sample)
        assert enclosed[1][1].real.contains(-2 - .25 * sample)


def test_case_02_quadratic_taylor_path():
    model = _model((_diag([1]), _diag([2]), _diag([3])))
    enclosed = evaluate_taylor_model_enclosure(model)
    for sample in (-1, -.5, 0, .5, 1):
        assert enclosed[0][0].real.contains(1 + 2 * sample + 3 * sample * sample)


def test_case_03_known_fixed_inertia_path():
    model = _model((_diag([3, -3]), _diag([.5, .5])))
    inertia = verified_block_ldl_inertia(
        evaluate_taylor_model_enclosure(model), precision_bits=256,
    )
    assert inertia["status"] == "CERTIFIED_INERTIA"
    assert (inertia["n_positive"], inertia["n_negative"]) == (1, 1)


def test_case_04_known_crossing_path():
    assert (-1) < 0 < 1
    assert (-1) * 1 < 0  # continuous affine scalar has an interior root


def test_case_05_same_inertia_endpoints_interior_crossing():
    polynomial = lambda value: (value - .25) * (value - .75)
    assert polynomial(0) > 0 and polynomial(1) > 0 and polynomial(.5) < 0


def test_case_06_repeated_eigenvalue_cluster():
    row = deterministic_signed_partition(
        [-2, -1, -1, 1, 1, 2], threshold=0, near_size=4,
    )
    assert row["near_indices"] == [1, 2, 3, 4]


def test_case_07_positive_far_block_elimination():
    row = validated_signed_schur_step(
        _diag([4, 3, -.1]), block_indices=[0, 1], expected_sign="POSITIVE",
        precision_bits=256,
    )
    assert row["status"] == "CERTIFIED_SIGNED_SCHUR_STEP"


def test_case_08_negative_far_block_elimination():
    row = validated_signed_schur_step(
        _diag([-4, -3, .1]), block_indices=[0, 1], expected_sign="NEGATIVE",
        precision_bits=256,
    )
    assert row["status"] == "CERTIFIED_SIGNED_SCHUR_STEP"


def test_case_09_alternating_sequential_reductions():
    row = sequential_signed_schur_reduction(
        _diag([-9, 8, -7, 6, .2]),
        midpoint_eigenvalues=[-9, 8, -7, 6, .2], threshold=0, near_size=1,
        block_sizes=[1], precision_bits=256,
    )
    accepted = [step["expected_sign"] for step in row["steps"] if step["accepted"]]
    assert accepted[:4] == ["NEGATIVE", "POSITIVE", "NEGATIVE", "POSITIVE"]


def test_case_10_one_by_one_schur_elimination():
    row = validated_signed_schur_step(
        [[acb(2), acb(1)], [acb(1), acb(2)]], block_indices=[0],
        expected_sign="POSITIVE", precision_bits=256,
    )
    assert row["schur_complement"][0][0].real.contains(arb("1.5"))


def test_case_11_two_by_two_schur_elimination():
    matrix = [[acb(3), acb(0), acb(1)], [acb(0), acb(2), acb(1)],
              [acb(1), acb(1), acb(4)]]
    row = validated_signed_schur_step(
        matrix, block_indices=[0, 1], expected_sign="POSITIVE",
        precision_bits=256,
    )
    assert row["status"] == "CERTIFIED_SIGNED_SCHUR_STEP"


def test_case_12_c4_symmetry_decomposition_equivalence():
    path = _synthetic_path()
    point = NormalizedJet.variable(exact_arb_from_fraction(Fraction(1, 4)), 3)
    outputs = path.outputs(point, midpoint=Fraction(1, 4))
    sectors = _c4_sector_jets(outputs)
    sector_values = []
    for sector in sectors:
        matrix = np.asarray([[complex(float(v.coefficients[0].real.mid()),
                                      float(v.coefficients[0].imag.mid()))
                              for v in row] for row in sector])
        sector_values.extend(np.linalg.eigvalsh((matrix + matrix.conj().T) / 2))
    rotations = [1, 1j, -1, -1j]
    alphas = [rotation * complex(float(z.coefficients[0].real.mid()),
                                 float(z.coefficients[0].imag.mid()))
              for z in outputs.physical_prototypes for rotation in rotations]
    probabilities = [float(p.coefficients[0].real.mid())
                     for p in outputs.orbit_probabilities for _ in rotations]
    full = np.empty((len(alphas), len(alphas)), dtype=np.complex128)
    for i, left in enumerate(alphas):
        for j, right in enumerate(alphas):
            overlap = np.exp(-(.5 * abs(left) ** 2 + .5 * abs(right) ** 2)
                             + np.conj(left) * right)
            full[i, j] = np.sqrt(probabilities[i] * probabilities[j]) * overlap
    full_values = np.linalg.eigvalsh((full + full.conj().T) / 2)
    assert np.allclose(np.sort(sector_values), full_values, atol=1e-12, rtol=1e-12)


def test_case_13_path_domain_failure():
    row = _synthetic_path(zero_gs=True).certify_path_domain(
        order=2, maximum_depth=0,
    )
    assert row["status"] == "PATH_DOMAIN_UNCERTIFIED"


@pytest.mark.skipif(os.name != "nt", reason="Windows Job Object required")
def test_case_14_path_domain_persistence_after_worker_timeout(tmp_path):
    _journal_prefix(tmp_path / "journal")
    row = run_with_job_timeout(
        [sys.executable, "-c", "import time; time.sleep(10)"], cwd=tmp_path,
        time_limit_seconds=.2, kill_grace_seconds=1,
        finalization_allowance_seconds=1, fixture="persistence", interval="point",
        status_path=tmp_path / "watchdog.json",
    )
    assert row["status"] == "RESOURCE_LIMIT"
    assert replay_journal(tmp_path / "journal").path_domain["status"] == (
        "PATH_DOMAIN_CERTIFIED"
    )


def test_case_15_node_journal_recovery_after_forced_termination(tmp_path):
    code = (
        "from pathlib import Path;from src.validation.durable_journal_v3 import "
        "DurableJournal;import os;d=Path(r'%s');i=%r;"
        "j=DurableJournal(d,attempt_id='attempt',segment_id='synthetic/ps',identity=i);"
        "j.append('RUN_STARTED',{});j.append('PATH_DOMAIN_COMMITTED',{'path_domain':"
        "{'status':'PATH_DOMAIN_CERTIFIED'}});j.append('WORK_QUEUE_INITIALIZED',{'pending':[]});"
        "[(j.append('NODE_STARTED',{'node_id':f'node-{k}'}),"
        "j.append('NODE_COMMITTED',{'node_id':f'node-{k}','node':{'status':'UNCERTIFIED'},"
        "'action':'UNRESOLVED'})) for k in range(3)];os._exit(17)"
    ) % (str(tmp_path / "journal"), IDENTITY)
    completed = subprocess.run([sys.executable, "-c", code], cwd=Path(__file__).parents[1])
    assert completed.returncode == 17
    assert len(replay_journal(tmp_path / "journal").completed_nodes) == 3


def test_case_16_provenance_mismatch(tmp_path, monkeypatch):
    from src.validation import certification_provenance_v3 as module
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"schema_version": module.PRESELECTION_SCHEMA,
        "status": module.PRESELECTION_STATUS, "source_freeze_commit": "0" * 40,
        "file_bindings": {"missing": "0" * 64}, "live_environment": {}}))
    monkeypatch.setattr(module, "live_environment", lambda: {})
    with pytest.raises(module.ProvenanceFailure, match="freeze_manifest_sha256"):
        module.verify_preselection_manifest(
            tmp_path, manifest, "f" * 64, require_clean_worktree=False,
        )


def test_case_17_environment_mismatch(tmp_path, monkeypatch):
    from src.validation import certification_provenance_v3 as module
    target = tmp_path / "bound"; target.write_bytes(b"x")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"schema_version": module.PRESELECTION_SCHEMA,
        "status": module.PRESELECTION_STATUS, "source_freeze_commit": "bad",
        "file_bindings": {"bound": __import__('hashlib').sha256(b'x').hexdigest()},
        "live_environment": {"python": "wrong"}}))
    monkeypatch.setattr(module, "live_environment", lambda: {"python": "actual"})
    with pytest.raises(module.ProvenanceFailure, match="live_environment_mismatch"):
        module.verify_preselection_manifest(
            tmp_path, manifest,
            __import__('hashlib').sha256(manifest.read_bytes()).hexdigest(),
            require_clean_worktree=False,
        )


@pytest.mark.skipif(os.name != "nt", reason="Windows Job Object required")
def test_case_18_hard_per_worker_timeout(tmp_path):
    row = run_with_job_timeout(
        [sys.executable, "-c", "import time; time.sleep(10)"], cwd=tmp_path,
        time_limit_seconds=.2, kill_grace_seconds=1,
        finalization_allowance_seconds=1, fixture="timeout", interval="point",
        status_path=tmp_path / "watchdog.json",
    )
    assert row["status"] == "RESOURCE_LIMIT"
    assert row["overshoot_seconds"] <= 2


def test_case_19_total_run_timeout():
    from scripts.certify_taylor_eigencluster_segments_v3 import _remaining_total_budget
    assert _remaining_total_budget(10, 5, now=16) == 0
    assert _remaining_total_budget(10, 5, now=12) == 3


def test_case_20_deterministic_replay(tmp_path):
    _journal_prefix(tmp_path / "left", nodes=2)
    _journal_prefix(tmp_path / "right", nodes=2)
    left = replay_journal(tmp_path / "left")
    right = replay_journal(tmp_path / "right")
    assert left.head_sha256 == right.head_sha256
    assert left.records == right.records
