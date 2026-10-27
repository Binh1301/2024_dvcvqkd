"""Evidence-first completion and seal; preserve every pre-existing ledger block."""
from datetime import datetime,timezone
import difflib
import json
from pathlib import Path
import subprocess
import verify as v

OUT=v.OUT;ROOT=v.ROOT
def save(path,data):path.write_bytes((json.dumps(data,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode('utf-8'))


def main():
    if (OUT/'final_seal.json').exists():raise FileExistsError('Do not overwrite completed seal')
    end=v.read(OUT/'completion_receipt.json');raw=end['primary_best'];sec=end['secondary_best']
    assert v.read(OUT/'visual_verification.json')['status']=='CURRENTLY_VERIFIED_PASS'
    result=v.audit()
    result['status']='CURRENTLY_VERIFIED_PASS'
    result['scope']='Saved finite exact-tested diagnostic; not security certification or continuous optimization'
    result['UTC']=datetime.now(timezone.utc).isoformat()
    result['protected_file_count']=len(v.read(OUT/'startup_manifest.json')['protected'])
    result['candidate_rows']=end['candidate_rows']
    result['channel_contexts']=end['channel_contexts']
    result['producer_sha256']=v.sha(__file__)
    save(OUT/'verification.json',result)
    check=subprocess.run(['git','diff','--check'],cwd=ROOT,capture_output=True,text=True)
    if check.returncode:raise RuntimeError(check.stdout+check.stderr)
    save(OUT/'git_diff_check.json',dict(status='CURRENTLY_VERIFIED_PASS',exit_code=check.returncode))
    for path in (OUT/'startup_ledgers').glob('*.md'):
        if path.name=='SESSION_HANDOFF.md':continue
        current=(ROOT/'docs'/path.name).read_bytes()
        old_body=path.read_bytes().split(b'\n',1)[1].lstrip(b'\n')
        if old_body not in current:raise ValueError('Pre-existing ledger content missing: '+path.name)
    ncheck=sum(len(v.read(p)['validation']['checks']) for p in (OUT/'selected_validation').glob('*.json'))
    protected=result['protected_file_count'];gap=str(end['source_gaps'])
    proof=v.sha(OUT/'verification.json')
    evidence=f"""## EVID-0218 - Uniform v43 staged search; primary no positive, bounded law separate

2026-10-23 user9f6181d7. Completed isolated results/
uniform_positive_skr_manuscript43_20261023/ with report_vi.md, candidate_comparison.csv,
StageA/B/C, explicit channel/source exclusion catalogs, same-law three-scheme tables,
matched aperture/parameter/law comparisons and three vectorPDF/350dpiPNG pairs.
Prospective protocol and outcome-adaptive completion plan are hash-bound.
Verification CURRENTLY_VERIFIED_PASS applies to saved finite diagnostic only;
verification.json SHA256 {proof}.
{protected} pre-existing protected files unchanged; branch/HEAD/frozen identity preserved.

Only Uniform p=1/256,VA=2*nbar,real1D Gaussian-effective homodyne/RR,beta.95;
v43 xi_ch.0186/xi_det.005 and NO eta_det. Same Tf=mh^2 and
N=(m1-Tf)VA+.0186m1+.005M0 in MI/DBL/covariance/full-Z homodyne Holevo.
Keep raw Eq10 [0,1] mass1e-10 gate,explicit AoA atom and true eta>1 tail;
no normalization/clipping/tail reassignment/interpolation or source substitution.
{end['uniform_source_count']} exact Uniform and197 MB sources; {end['candidate_rows']} CSV rows,
{end['channel_contexts']} channel contexts,{end['candidate_failure_count']} covariance/information failures.
{ncheck} saved selected MI/Holevo/covariance checks plus guard/source/PDF/moment checks.

Primary Uniform positive found={end['primary_positive_found']}; strongest raw
K={raw['raw_SKR']:.17g} atDr{raw['Dr_m']}m,fullDiv{raw['divergence_urad']}urad,
jitter{raw['jitter_urad']}urad,positionSD{raw['sigma_h_m']}m,
zenith{raw['zenith_deg']}deg,VA{raw['VA']}.
Failed-mass geometries have unavailable rates,not0. StageC extends divergence60
without relaxing the gate; larger receiver is not automatically normalized.

Independently defined bounded random-width/circular-aperture law is SECONDARY,
not Eq10 repair/replacement. AtDr.30,fullDiv10urad,jitter.5urad,positionSD.03m,
zenith0,L19km,Uniform VA{sec['VA']} has K={sec['raw_SKR']:.17g}.
All secondary contexts checked GH32/64; best channel also independent GH96/radial
Legendre512. Same-law MB shaping gain at this receiver30 geometry is
{end['shaping_gain']['power_conserving_random_width']:.17g} bit/use.
Larger-aperture secondary results are separately tabulated; Dr.30 is smallest
tested positive aperture,not a proven global/hardware minimum.

GMP launch failed before source computation: Windows ApplicationControl blocked
gmpy2 DLL. Standard Python MP fallback retained full-support/kernel and fixed
1050/1250/1450-digit ladder,3600s budget,versioned new cache.
Requested initial exact-source gaps={gap}; full requested initial-point
availability={end['full_VA_requested_domain_complete']}. Failures/timeouts and
coverage limits explicit,no invented C,w. No policy bypass.

All maxima best exact-tested; no global-Z enclosure,operational/finite-key/
composable security,flight/PAT/payload verification or secure-default claim.
Production/security functional/frozen config/old caches/history unchanged.
Keep UNVALIDATED_SECURITY_MODEL,NOT_READY_FOR_PUBLICATION_SCALE_RUNS,
historical frozen-hash discrepancy,ObjectiveC USER_STOPPED. No training/test/
heldout/publication,baseline/default/threshold approval,commit/push. STOP.

"""
    decision=f"""## DEC-0201 - Retain primary Uniform nonpositive result and separate bounded-law evidence

2026-10-23 EVID-0218 accepts user9f6181d7 finite staged diagnostic artifacts.
Primary raw Eq10 retains strict mass1e-10 gate; no positive Uniform claim
from blocked PDFs or a secondary law. Secondary receiver30 Uniform
K={sec['raw_SKR']:.17g} is numerical/model-provisional only,with explicit
10urad divergence/.5urad jitter/.03m position engineering assumptions.
Compare shaping only within the same law,geometry and noise convention.
Requested exact-source gaps {gap} remain coverage limits; finite-catalog
selection is not continuous/global optimization or security certification.
OS ApplicationControl is respected; no automatic source retry or broader search.
Keep scientific production/frozen/cache history untouched and all lifecycle/
security/frozen blockers,ObjectiveC USER_STOPPED. No publication/default/
baseline/threshold approval. Deliver and STOP; new scope requires new request.

"""
    state=f"""## Current: Uniform positive-SKR investigation COMPLETE WITH EXPLICIT MODEL/COVERAGE LIMITS; STOP

2026-10-23 EVID-0218/DEC-0201,user9f6181d7. Deliver results/
uniform_positive_skr_manuscript43_20261023/report_vi.md,candidate_comparison.csv,
stage/per-angle/aperture/ablation/source/law tables,three figure pairs and
read-only verify.py/final_seal.json. Numeric saved-artifact checks pass;
{protected} protected historical/scientific files unchanged.
Primary Eq10 Uniform no positive found in valid tested points; best
K={raw['raw_SKR']:.17g},Dr{raw['Dr_m']},div{raw['divergence_urad']},
jitter{raw['jitter_urad']},sigma{raw['sigma_h_m']},angle{raw['zenith_deg']},VA{raw['VA']}.
Secondary bounded random-width law is independent,not a PDF repair;receiver30
Uniform VA{sec['VA']},K={sec['raw_SKR']:.17g},div10/jitter.5/sigma.03/zenith0.
Same v43 xi_det.005/no eta_det,homodyne/RR/same Tf,N throughout.
Initial exact-source gaps={gap}; no interpolation/global/secure-positive claim.
All new source attempts use separate cache; GMP policy blocker respected.
No production/frozen/old-source/history changes,training/test/heldout/publication
or default/baseline/threshold promotion. Keep UNVALIDATED_SECURITY_MODEL,
NOT_READY_FOR_PUBLICATION_SCALE_RUNS,frozen discrepancy,ObjectiveC USER_STOPPED.

"""
    next_action="""## Current: deliver Uniform staged diagnostic and law/coverage qualifications; STOP

EVID-0218/DEC-0201 complete. Open results/
uniform_positive_skr_manuscript43_20261023/report_vi.md for Q1-Q6 and parameter
tables,candidate_comparison.csv and figures. verify.py reads saved evidence only.
Do not rerun completed producers,overwrite old caches/receipts,repair raw PDF,
mix channel laws,call finite exact-tested argmax global,or label secondary
positive secure/flight-validated. Source gaps and OS blocker remain explicit.
No automatic retry/optimization/publication/default/baseline/threshold work.
Keep lifecycle/security/frozen blockers,ObjectiveC USER_STOPPED. Deliver and STOP.

"""
    # Artifact -> Evidence -> Decision -> State -> Next -> Handoff.
    def prepend(name,block):
        path=ROOT/name;head,rest=path.read_bytes().split(b'\n',1)
        path.write_bytes(head+b'\n\n'+block.encode('utf-8')+rest.lstrip(b'\n'))
    prepend('docs/EVIDENCE.md',evidence)
    prepend('docs/DECISION_LOG.md',decision)
    path=ROOT/'docs/PROJECT_STATE.md';old=path.read_text(encoding='utf-8')
    start=old.index('## Current: staged Uniform positive-SKR investigation AUTHORIZED IN PROGRESS')
    stop=old.index('## Current: manuscript43 zenith sweep COMPLETE; STOP',start)
    path.write_bytes((old[:start]+state+old[stop:]).encode('utf-8'))
    prepend('docs/NEXT_ACTIONS.md',next_action)
    handoff=f"""# Session Handoff

2026-10-23 EVID-0218/DEC-0201,user9f6181d7: staged Uniform diagnostic COMPLETE
WITH MODEL/COVERAGE LIMITS. Deliver results/
uniform_positive_skr_manuscript43_20261023/report_vi.md,candidate_comparison.csv,
three PNG350dpi/vectorPDF pairs,source/channel/matched tables,validation and seal.
Read-only: .venv/Scripts/python.exe -X utf8 -B
results/uniform_positive_skr_manuscript43_20261023/verify.py.
No evaluator rerun; no further automatic authorized work. Deliver and STOP.

Primary raw Eq10 Uniform Kmax={raw['raw_SKR']:.17g} atDr{raw['Dr_m']},div{raw['divergence_urad']},
jitter{raw['jitter_urad']},positionSD{raw['sigma_h_m']},zenith{raw['zenith_deg']},VA{raw['VA']}.
Secondary independently bounded random-width law receiver30 Uniform
K={sec['raw_SKR']:.17g},VA{sec['VA']},div10urad,jitter.5urad,positionSD.03m,zenith0.
Same v43 .0186/.005,no eta_det,homodyne1D/RR/beta.95,Tf=mh^2,
same effective N in MI,DBL,covariance/full-Z Holevo. Do not mix laws or
transfer positive to Eq10. Dr.30 smallest tested positive only in secondary;
engineering feasibility and security provisional.
GMP DLL blocked by ApplicationControl; standard Python exact fallback keeps
precision1050/1250/1450 and3600s bound,separate new cache. Gaps={gap}.
No source interpolation,normalizationrepair/eigenclipping/positive forcing.

Branch feat/image,HEAD9cc25e9f8320542b61adaec05c755e98fe93cdc2 unchanged.
{protected} protected files unchanged;only own namespace and5 relevant ledgers.
Frozen actualdf83ea63af3b475ecca03a44d22d3240ab24d695ff0ebef31f0cd6747db78c15
differs historicalexpected561fecc97cdf9967034ffd6865c1605804b624b98f47a091e47f17e520a2a7b1.
Preserve UNVALIDATED_SECURITY_MODEL,NOT_READY_FOR_PUBLICATION_SCALE_RUNS,
ObjectiveC USER_STOPPED. No production/default/baseline/threshold changes,
training/test/heldout/publication,commit/push. Historical receipt ledger hashes
remain snapshots; old numerical artifact bytes are preserved.
Ponytail full; PDF rendering/visual QA; no subagents or new dependencies.
"""
    (ROOT/'.agent/SESSION_HANDOFF.md').write_bytes(handoff.encode('utf-8'))
    changes=[]
    for name in v.read(OUT/'startup_manifest.json')['allowed_ledger_changes']:
        before=(OUT/'startup_ledgers'/Path(name).name).read_text(encoding='utf-8').splitlines(True)
        after=(ROOT/name).read_text(encoding='utf-8').splitlines(True)
        changes.extend(difflib.unified_diff(before,after,fromfile='startup/'+name,tofile=name))
    for path in sorted(OUT.glob('*.py')):
        changes.extend(difflib.unified_diff([],path.read_text(encoding='utf-8').splitlines(True),
            fromfile='/dev/null',tofile=path.relative_to(ROOT).as_posix()))
    (OUT/'scoped_changes.patch').write_bytes(''.join(changes).encode('utf-8'))
    check=subprocess.run(['git','diff','--check'],cwd=ROOT,capture_output=True,text=True)
    if check.returncode:raise RuntimeError(check.stdout+check.stderr)
    save(OUT/'final_seal.json',dict(status='CURRENTLY_VERIFIED_PASS',
        UTC=datetime.now(timezone.utc).isoformat(),
        artifacts={p.relative_to(OUT).as_posix():v.sha(p) for p in sorted(OUT.rglob('*'))
            if p.is_file() and p.name!='final_seal.json'},
        ledgers={n:v.sha(ROOT/n) for n in v.read(OUT/'startup_manifest.json')['allowed_ledger_changes']},
        verification_sha256=v.sha(OUT/'verification.json'),production_or_old_cache_changed=False))
    final=v.audit()
    print(json.dumps(final,indent=2))


if __name__=='__main__':main()
