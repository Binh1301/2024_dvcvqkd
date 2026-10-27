"""Read-only binding and prior-artifact check; no scientific evaluator calls."""
import csv
import hashlib
import json
from pathlib import Path

OUT=Path(__file__).resolve().parent
AUDIT=OUT.parent
ROOT=AUDIT.parents[1]
REPO=ROOT.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def rows(path):
    with path.open(encoding="utf-8",newline="") as stream:
        return list(csv.DictReader(stream))


def main():
    binding=read(OUT/"binding.json")
    assert binding["reference_identity"]=="USER_CONFIRMED_AVAILABLE_REFERENCE"
    assert binding["canonical_binding"]=="CONFIRMED_BY_USER"
    assert binding["confirmation"]=="đúng cái đấy rồi"
    expected=binding["reference_sha256"]
    assert sha(Path(binding["confirmed_local_path"]))==expected
    assert sha(AUDIT/"inputs/available_v43.pdf")==expected
    for rel,digest in binding["prior_package_seal"].items():
        assert sha(AUDIT/rel)==digest,rel
    for rel,digest in read(AUDIT/"artifact_manifest.json")["files"].items():
        assert sha(AUDIT/rel)==digest,rel
    protected=read(AUDIT/"startup_manifest.json")["protected"]
    for rel,digest in protected.items():
        assert sha(REPO/rel)==digest,rel
    old,new=rows(AUDIT/"three_model_comparison.csv"),rows(OUT/"three_model_comparison_bound.csv")
    assert len(old)==len(new)==9
    for previous,current in zip(old,new):
        for key,value in previous.items():
            if key not in {"manuscript_equivalent","requested_PDF_identity_verified"}:
                assert current[key]==value,(key,current["scenario"])
        assert current["requested_PDF_identity_verified"]=="True"
        assert current["manuscript_equivalent"]==("EXACT_MATCH" if current["channel_model"]=="A_Eq10" else "DIFFERENT")
    assert sum(row["validation_status"]=="BLOCKED_PDF_NORMALIZATION" for row in new)==2
    for name,changed in [
        ("parameter_provenance",{"requested_v43_2_match"}),
        ("equation_comparison",{"reference"}),
        ("component_classification",{"reference","requested_v43_2_verified"})]:
        previous,current=rows(AUDIT/(name+".csv")),rows(OUT/(name+"_bound.csv"))
        assert len(previous)==len(current)
        for a,b in zip(previous,current):
            assert all(a[k]==b[k] for k in a if k not in changed),name
    assert not binding["canonical_evaluator_adopted"] and not binding["corrections_adopted"]
    assert binding["security_status"]=="UNVALIDATED_SECURITY_MODEL"
    assert binding["lifecycle"]=="NOT_READY_FOR_PUBLICATION_SCALE_RUNS"
    registry=ROOT/"docs/MANUSCRIPT43_CANONICAL_REFERENCE.md"
    assert expected in registry.read_text(encoding="utf-8") and "ACTIVE_REFERENCE_USER_CONFIRMED" in registry.read_text(encoding="utf-8")
    for rel in ["docs/EVIDENCE.md","docs/DECISION_LOG.md","docs/PROJECT_STATE.md","docs/NEXT_ACTIONS.md"]:
        original=(OUT/"startup_ledgers"/Path(rel).name).read_bytes().split(b"\n",2)[-1]
        assert original in (ROOT/rel).read_bytes(),rel
    if (OUT/"final_seal.json").exists():
        seal=read(OUT/"final_seal.json")
        for rel,digest in seal["files"].items():
            assert sha(ROOT/rel)==digest,rel
    return dict(status="CURRENTLY_VERIFIED_PASS",reference_identity=binding["reference_identity"],
        canonical_binding=binding["canonical_binding"],reference_sha256=expected,
        prior_protected_files=len(protected),
        prior_audit_artifacts=len(read(AUDIT/"artifact_manifest.json")["files"]),
        comparison_rows=9,numeric_values_unchanged=True,
        numerical_evaluator_rerun=False,production_changed=False,old_Cw_changed=False,
        Eq10_critical_status="BLOCKED_PDF_NORMALIZATION",
        corrections_adopted=False,canonical_evaluator_adopted=False,
        security_status=binding["security_status"],lifecycle=binding["lifecycle"])


if __name__=="__main__":
    print(json.dumps(main(),indent=2))
