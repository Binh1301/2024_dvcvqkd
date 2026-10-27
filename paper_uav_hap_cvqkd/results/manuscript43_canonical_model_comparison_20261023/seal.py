"""Seal current artifacts after read-only verification; completed outputs immutable."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name,value):
    (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")


if __name__=="__main__":
    if (OUT/"final_seal.json").exists():
        raise FileExistsError("Preserve completed audit seal; use verify.py read-only")
    result=subprocess.run([sys.executable,"-X","utf8","-B",str(OUT/"verify.py")],
                          cwd=ROOT,capture_output=True,text=True,encoding="utf-8",check=True)
    verification=json.loads(result.stdout)
    write("verification.json",verification)
    files={p.relative_to(OUT).as_posix():sha(p) for p in sorted(OUT.rglob("*"))
           if p.is_file() and "__pycache__" not in p.parts
           and p.name not in {"verification.json","artifact_manifest.json","final_seal.json"}}
    write("artifact_manifest.json",dict(files=files,scope="new audit artifacts only"))
    ledgers=["docs/EVIDENCE.md","docs/DECISION_LOG.md","docs/PROJECT_STATE.md",
             "docs/NEXT_ACTIONS.md",".agent/SESSION_HANDOFF.md"]
    write("final_seal.json",dict(status="CURRENTLY_VERIFIED_PASS",
         verification_sha256=sha(OUT/"verification.json"),
         artifact_manifest_sha256=sha(OUT/"artifact_manifest.json"),
         ledgers={rel:sha(ROOT/rel) for rel in ledgers},
         canonical_binding="BLOCKED_REFERENCE_NOT_LOCATED",security_approved=False,
         production_changed=False,optimization=False))
    print(result.stdout,end="")
