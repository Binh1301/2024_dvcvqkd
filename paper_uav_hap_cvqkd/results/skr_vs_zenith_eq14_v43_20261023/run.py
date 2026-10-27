"""Phase A producer and read-only verifier. Later phases remain dependency-blocked."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import sys
import unittest

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
REPO = ROOT.parent
SCHEMES = ["Optimized Uniform 256-QAM", "Fixed MB-shaped 256-QAM", "Optimized MB-shaped 256-QAM"]


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def clean(x):
    if isinstance(x, dict): return {str(k): clean(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)): return [clean(v) for v in x]
    if type(x).__module__.startswith("mpmath"): return str(x)
    if hasattr(x, "tolist"): return x.tolist()
    return x


def save(name, data):
    (OUT/name).write_text(json.dumps(clean(data), indent=2, ensure_ascii=False, allow_nan=False)+"\n", encoding="utf-8")


def rows(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def write(name, data):
    fields = list(dict.fromkeys(k for row in data for k in row))
    with (OUT/name).open("w", encoding="utf-8", newline="") as stream:
        w = csv.DictWriter(stream, fieldnames=fields)
        w.writeheader(); w.writerows(clean(data))


def receipt_status(payload, candidates):
    """Require an actual payload-bound precision receipt, not merely a cache label."""
    import mpmath as mp
    canonical = hashlib.sha256(json.dumps({k: v for k, v in payload.items() if k != "_file_sha256"},
                                        sort_keys=True).encode()).hexdigest()
    matching = []
    for path in candidates:
        r = read(path)
        if r.get("payload_file_sha256") != payload["_file_sha256"] and r.get("payload_sha256") != canonical:
            continue
        diagnostic = r.get("diagnostic", {})
        levels = diagnostic.get("fallback_rows", [])
        if (r.get("precision_ladder") != payload["source_settings"]["precision_ladder"]
                or [x.get("digits") for x in levels] != r.get("precision_ladder")):
            continue
        if (not levels or diagnostic.get("support_size") != 256
                or any(x.get("rank") != 256 or x.get("resolved") is not True
                       or mp.mpf(x["minimum_eigenvalue"]) <= 0 for x in levels)):
            continue
        if any(float(x[k]) != payload[k] for x in levels for k in ["C", "w"]):
            continue
        matching.append(dict(path=path.relative_to(ROOT).as_posix(), sha256=sha(path)))
    return matching


def inspect_catalog(protocol):
    import model as m
    import numpy as np
    from scripts.exact_cache_provenance import source_settings, verify_source_payload
    from scripts.run_exact_mb_test2 import ensemble_hash
    from scripts.run_theta10_D55_unconstrained_three_scheme import make_ensemble, unconstrained_config
    from src.manuscript_mobility import _validate_ensemble

    old = rows(ROOT/"results/skr_vs_zenith_manuscript43_20261023/source_catalog.csv")
    newer = read(ROOT/"results/uniform_positive_skr_manuscript43_20261023/source_catalog.json")
    catalog = {}
    for entry in old+newer:
        c = dict(entry)
        c.update(VA=float(c["VA"]), nu_raw=float(c["nu_raw"]), C=float(c["C"]), w=float(c["w"]))
        catalog[c["ensemble_hash"]] = c
    catalog = sorted((c for c in catalog.values() if .05 <= c["VA"] <= 10 and 0 <= c["nu_raw"] <= .4),
                     key=lambda c: (c["family"], c["VA"], c["nu_raw"], c["ensemble_hash"]))
    config = unconstrained_config()
    settings = source_settings(config)
    receipt_dirs = {(ROOT/c["source_path"]).parent.parent/"source_receipts" for c in catalog}
    receipt_dirs.add(ROOT/"results/uniform_manuscript_2d_optimization_20261019/source_receipts")
    receipts = {}
    for directory in sorted(receipt_dirs):
        for path in sorted(directory.glob("*.json")):
            receipts.setdefault(path.stem, []).append(path)
    evidence, coverage = [], []
    fixed = protocol["fixed_MB"]
    common_va = {c["VA"].hex() for c in catalog if c["family"] == "Uniform"} | {fixed["VA_hex"]}
    for c in catalog:
        row = {k: c[k] for k in ["family", "VA", "nu_raw", "ensemble_hash", "source_path", "source_sha256", "C", "w"]}
        row.update(VA_hex=c["VA"].hex(), nu_raw_hex=c["nu_raw"].hex(),
                   nu_repo=42.5*c["nu_raw"], pilot_member=c["VA"].hex() in common_va,
                   identity_status="NOT_RUN", convergence_status="NOT_RUN", primary_evaluation="NOT_RUN")
        try:
            path = ROOT/c["source_path"]
            payload = read(path)
            if sha(path) != c["source_sha256"]: raise ValueError("Payload digest mismatch")
            provenance = verify_source_payload(payload, settings)
            if (payload["V_A_hex"] != c["VA"].hex() or payload["nu_mb_raw_hex"] != c["nu_raw"].hex()
                    or any(payload[k] != c[k] for k in ["ensemble_hash", "C", "w"])):
                raise ValueError("Catalog/payload identity mismatch")
            ensemble = make_ensemble(config, c["family"], c["nu_raw"], c["VA"])
            if ensemble_hash(ensemble) != c["ensemble_hash"]: raise ValueError("Reconstructed ensemble hash mismatch")
            p, alpha = _validate_ensemble(ensemble.probabilities[0].numpy(), ensemble.amplitudes[0].numpy(), c["nu_raw"], c["VA"])
            m.helpers().validate_source({**c, "p": p, "alpha": alpha})
            # Digest checking uses the unmodified payload, not the transient file-digest field.
            candidates = receipts.get(c["ensemble_hash"], []) + receipts.get(payload["cache_key"], [])
            bound = receipt_status({**payload, "_file_sha256": c["source_sha256"]}, candidates)
            row.update(identity_status="CURRENTLY_VERIFIED_PASS", peak_photons=float(np.max(abs(alpha)**2)),
                       nbar=float(p @ abs(alpha)**2), printed_Vmod=float(p @ abs(alpha)**2)/2,
                       source_variance=float(p @ (2*alpha.real)**2), support_size=256,
                       convergence_status="CURRENTLY_VERIFIED_PASS" if bound else "NOT_LOCATED_PAYLOAD_BOUND_RECEIPT",
                       receipt_paths=";".join(x["path"] for x in bound),
                       receipt_search_candidates=";".join(p.relative_to(ROOT).as_posix() for p in candidates))
            evidence.append(dict(ensemble_hash=c["ensemble_hash"], provenance=provenance, receipts=bound,
                                 source_sha256=c["source_sha256"], source_path=c["source_path"]))
        except (ValueError, KeyError, OSError) as error:
            row.update(identity_status="FAILED", reason=str(error))
        coverage.append(row)
    missing = not any(c["family"] == "Uniform" and c["VA"].hex() == fixed["VA_hex"] for c in catalog)
    if missing:
        coverage.append(dict(family="Uniform", VA=fixed["VA"], VA_hex=fixed["VA_hex"], nu_raw=0.,
                             nu_raw_hex=0.0.hex(), nu_repo=0., pilot_member=True,
                             identity_status="MISSING_EXACT_SOURCE", convergence_status="NOT_RUN",
                             primary_evaluation="NOT_RUN", C=None, w=None, ensemble_hash=None))
    counts = {f: sum(c["family"] == f for c in catalog) for f in ["Uniform", "MB"]}
    return coverage, dict(counts=counts, existing_sources=len(catalog),
                         identity_pass=sum(c["identity_status"] == "CURRENTLY_VERIFIED_PASS" for c in coverage),
                         identity_fail=sum(c["identity_status"] == "FAILED" for c in coverage),
                         receipt_pass=sum(c["convergence_status"] == "CURRENTLY_VERIFIED_PASS" for c in coverage),
                         receipt_unlocated=sum(c["convergence_status"] == "NOT_LOCATED_PAYLOAD_BOUND_RECEIPT" for c in coverage),
                         receipt_search_scope=sorted(str(p.relative_to(ROOT)) for p in receipt_dirs),
                         missing_Uniform_at_fixed_VA=missing, pilot_existing=sum(c["VA"].hex() in common_va for c in catalog),
                         pilot_after_one_new_source=sum(c["VA"].hex() in common_va for c in catalog)+int(missing),
                         full_pool_after_one_new_source=len(catalog)+int(missing), evidence=evidence)


def blocked_rows(protocol, context, coverage):
    fixed = next(x for x in coverage if x.get("ensemble_hash") == protocol["fixed_MB"]["ensemble_hash"])
    output = []
    for angle in protocol["angles_deg"]:
        for scheme in SCHEMES:
            row = dict(zenith_deg=angle, scheme=scheme, status="BLOCKED_PHASE_A",
                       reason="EQ10_SUPPORT_NORMALIZATION;VA_VMOD_MAPPING_UNRESOLVED",
                       channel_law=protocol["channel_law"], correlation_policy=protocol["correlation_policy"],
                       protocol_sha256=sha(OUT/"protocol.json"), physical_configuration=json.dumps(protocol["physical"], sort_keys=True),
                       source_hash=None, VA=None, nu_raw=None, C=None, w=None,
                       M0=None, E_eta=None, E_sqrt_eta=None, E_eta_xi=None,
                       eta_f=None, xi_f=None, Z_manuscript_eq14=None,
                       I_AB=None, beta_I_AB=None, chi_BE=None, K_raw=None,
                       moment_status="NOT_RUN", rate_evaluation="NOT_RUN", plot_point=False, security_valid=False)
            if angle == context["zenith_deg"]:
                m = context["precision"][-1]
                row.update(M0=m["M0"], E_eta=m["m1"], E_sqrt_eta=m["mh"], E_eta_xi=m["mean_eta_xi"],
                           moment_status="DIAGNOSTIC_UNNORMALIZED_LAW")
            if scheme == SCHEMES[1]:
                row.update(source_hash=fixed["ensemble_hash"], **{k: fixed[k] for k in ["VA", "nu_raw", "C", "w"]})
            output.append(row)
    return output


def report(protocol, context, catalog, tests, gate):
    hi = context["precision"][-1]
    physical = protocol["physical"]
    table = "\n".join(f"| {k} | {v} |" for k, v in physical.items())
    text = f"""# Phase A — v43, Eq. (14) trực tiếp

**Đã triển khai và kiểm tra thành phần Phase A; Phase B–F bị chặn.** Đây không phải sweep SKR đã hoàn tất.

## Tham số

| Tham số | Giá trị |
|---|---|
{table}
| xi_ch / xi_det | 0.0186 / 0.005 SNU |
| beta / receiver | 0.95 / homodyne 1D, reverse reconciliation |
| VA / nu_raw | [0.05,10] / [0,0.40] |
| Photon đỉnh | Ghi giá trị; không áp giới hạn 30 theo lựa chọn của người dùng |

Xem `parameters.csv` để phân biệt default PDF và lựa chọn thí nghiệm.
PDF chuẩn có SHA-256 `{protocol['reference_sha256']}`; không sửa bản thảo.

## Công thức và phạm vi triển khai

`model.correlation_eq14` chỉ tính

$$Z=2\\sqrt{{\\eta_f}}C-\\sqrt{{2\\eta_f\\xi_f w}}.$$

Không có tìm kiếm Z, endpoint tùy chọn, projection, full-Z grid hoặc nhánh on_cap.
`model.components` tính Eq. (13) với Vmod được truyền rõ ràng cho **fixture kiểm tra thành phần**.
`model.evaluate` chặn tính MI/Holevo/SKR khi luật xác suất, mapping VA hoặc receipt C,w chưa qua gate.
MI dùng helper Gaussian homodyne thực 1D đã có; không dùng MI Shannon hay heterodyne.
Eq. (20) giữ đóng góp atom `xi_det*P0`; không chia cho eta tại zero.

## Phát hiện toán học tại 0 độ

- M0 = `{hi['decimal']['M0']}`.
- Tail ổn định trên eta>1 = `{hi['decimal']['stable_tail']}`.
- P0 = `{hi['decimal']['P0']}`; active retained mass = `{hi['decimal']['active_mass']}`.
- Sai khác closed/direct moment lớn nhất = `{context['moment_residual']:.6g}`.
- Kiểm tra số: **{context['numerical_status']}**; tính hợp lệ luật xác suất: **{context['mathematical_status']}**.

Với rho=0, B,d,v,P1 dương, Eq. (10) có mật độ dương trên eta>1. Giới hạn tích phân tới 1
giữ thiếu mass. Tail dương là đặc tính luật, không biến mất nhờ tăng precision hay nới tolerance.
Kiểm tra dừng tại góc 0; 60 góc còn lại không được chạy. File 183 hàng chỉ ghi trạng thái BLOCKED.
`channel_preflight.json` lưu closed form, tích phân độc lập, precision80/110 và định nghĩa atom.
Survival-form được dùng để **kiểm tra tích phân của cùng Eq. (10)**, không thay PDF hoặc moment bản thảo.

Catalog dùng VA=2*nbar, còn PDF in Vmod=nbar/2: trên cùng ensemble, printed Vmod=VA/4.
Không đổi source hay tự đồng nhất hai biến. Mapping vẫn `UNRESOLVED_AUTHOR_REVIEW_REQUIRED`.
Diễn giải X=2Re(alpha) được giữ như convention người dùng yêu cầu, không sửa likelihood in trong PDF.
MB giữ cùng PMF centered và nu_repo=42.5*nu_raw; khác biệt ký hiệu gamma/nu trong PDF được báo riêng.
HV và Gd dùng closure hiện có của repository; bản thảo chưa điền đầy đủ tham chiếu cho hai thành phần này.

## Nguồn và provenance

- Có {catalog['counts']['Uniform']} Uniform và {catalog['counts']['MB']} MB trong miền yêu cầu.
- Tái dựng p,alpha, xác minh ensemble hash/payload/source code/settings: {catalog['identity_pass']} PASS; {catalog['identity_fail']} FAILED.
- Receipt hội tụ gắn được với đúng payload: {catalog['receipt_pass']}.
- Chưa tìm thấy receipt đạt yêu cầu trong các thư mục nguồn đã khảo sát: {catalog['receipt_unlocated']}.
- Pool pilot hiện có {catalog['pilot_existing']}; sau một Uniform còn thiếu sẽ là {catalog['pilot_after_one_new_source']}.
- Toàn catalog sau nguồn bổ sung sẽ là {catalog['full_pool_after_one_new_source']}; chưa tạo nguồn đó.

Hash đúng không tự chứng minh precision hội tụ. `source_identity_audit.json` ghi phạm vi tìm receipt;
không kết luận receipt không tồn tại ở mọi nơi và không tái chạy AP để thay thế bằng chứng thiếu.
Fixed MB giữ VA hex `{protocol['fixed_MB']['VA_hex']}` và hash `{protocol['fixed_MB']['ensemble_hash']}`.
`source_catalog_coverage.csv` ghi cả photon đỉnh, nbar, printed Vmod và trạng thái từng nguồn.

## Kiểm chứng và điều kiện tiếp tục

{tests['tests_run']} tests thành phần/gate: {tests['status']}. Xem `unit_tests.json` và `unit_tests.log`.
Các fixture tổng hợp không phải kết quả HAP–UAV, không dùng chọn baseline hoặc báo SKR dương.
`gate.json` ghi `phase_B_ready=false`; source generation, optimization, SKR sweep và figure đều NOT_RUN.
Phases B–F được CLI từ chối trước mọi tính toán; chưa triển khai source_job/renderer vì dependency này.

Trước khi tiếp tục cần: (1) tác giả giải quyết support/normalization của Eq. (10),
(2) khóa mapping VA–Vmod, (3) cung cấp/xác thực receipt hội tụ nguồn còn thiếu và kiểm tra lại lifecycle.
Mọi sửa công thức chỉ là đề xuất riêng và cần phê duyệt rõ ràng; package này không áp dụng correction nào.

`UNVALIDATED_SECURITY_MODEL`, `NOT_READY_FOR_PUBLICATION_SCALE_RUNS` và sai khác frozen hash được giữ.
Không có kết luận finite-key/composable security hoặc khả thi phần cứng từ các tests này.

Chạy kiểm chứng chỉ đọc từ project root:

```powershell
.\\.venv\\Scripts\\python.exe -X utf8 -B results/skr_vs_zenith_eq14_v43_20261023/run.py --verify-only
```

Không chạy lại producer Phase A đã seal; verifier không nhập evaluator, không tính lại nguồn hoặc kênh.
"""
    (OUT/"validation_report_vi.md").write_text(text, encoding="utf-8")


def phase_a():
    if (OUT/"gate.json").exists() or (OUT/"artifact_manifest.json").exists():
        raise FileExistsError("Preserve completed Phase A; use --verify-only")
    import model as m
    protocol = read(OUT/"protocol.json")
    m.validate_protocol(protocol)
    started = datetime.now(timezone.utc).isoformat()
    import test_model
    log = io.StringIO()
    result = unittest.TextTestRunner(stream=log, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(test_model))
    (OUT/"unit_tests.log").write_text(log.getvalue(), encoding="utf-8")
    tests = dict(status="CURRENTLY_VERIFIED_PASS" if result.wasSuccessful() else "FAILED",
                 tests_run=result.testsRun, failures=len(result.failures), errors=len(result.errors),
                 producer_sha256=sha(OUT/"test_model.py"))
    save("unit_tests.json", tests)
    if not result.wasSuccessful(): raise ValueError("Component tests failed; see unit_tests.log")
    coverage, catalog = inspect_catalog(protocol)
    write("source_catalog_coverage.csv", coverage)
    save("source_identity_audit.json", catalog)
    context = m.channel_context(0, protocol)
    save("channel_preflight.json", context)
    output = blocked_rows(protocol, context, coverage)
    write("skr_vs_zenith.csv", output)
    write("optimal_parameters_vs_zenith.csv", [{k: r[k] for k in
          ["zenith_deg", "scheme", "VA", "nu_raw", "source_hash", "status", "reason", "rate_evaluation"]} for r in output])
    defaults = dict(Dr_m=.08, divergence_full_urad=233., jitter_urad=15.61, sigma_h_m=1.)
    write("parameters.csv", [dict(parameter=k, value=v, manuscript_default=defaults.get(k, v),
          provenance="USER_EXPERIMENT_OVERRIDE" if k in defaults else "MANUSCRIPT_DEFAULT_AND_USER_REQUEST")
          for k, v in protocol["physical"].items()] + [dict(parameter=k, value=protocol[k],
          manuscript_default="SYMBOL_ONLY" if k != "beta" else .95, provenance="USER_REQUEST") for k in ["xi_ch", "xi_det", "beta"]])
    write("equation_to_code.csv", [dict(equations=eq, implementation=impl, status=status) for eq, impl, status in [
        ("1-3,15-16", "run.inspect_catalog; source hashes and receipts", "VA_VMOD_MAPPING_UNRESOLVED"),
        ("4-8", "preserved optical; HV/Gd closure", "REPOSITORY_CLOSURE_DISCLOSED"),
        ("9-10", "model.channel_context", "BLOCKED_PDF_SUPPORT_NORMALIZATION"),
        ("18-20", "raw_pdf_moments; model.moment_check", context["numerical_status"]),
        ("17", "model.evaluate", "BLOCKED_BEFORE_RATE_EVALUATION"),
        ("12", "preserved homodyne_mi; real quadrature convention", "COMPONENT_TESTED"),
        ("14", "model.correlation_eq14", "COMPONENT_TESTED_DIRECT_ONLY"),
        ("13", "model.components", "COMPONENT_TESTED_HOMODYNE"),
        ("11", "model.evaluate", "BLOCKED_BEFORE_RATE_EVALUATION")]])
    gate = dict(status="BLOCKED_PHASE_A", implementation_checks=tests["status"],
                channel_numerical_status=context["numerical_status"],
                mathematical_status=context["mathematical_status"],
                blockers=["EQ10_SUPPORT_NORMALIZATION", "VA_VMOD_MAPPING_UNRESOLVED", "FROZEN_SPEC_HASH_DISCREPANCY"],
                phase_B_ready=False, phase_A_dependency_report_complete=True,
                source_counts=catalog["counts"], existing_source_identity_pass=catalog["identity_pass"],
                convergence_receipts_pass=catalog["receipt_pass"], convergence_receipts_unlocated=catalog["receipt_unlocated"],
                evaluated_channel_angles=[0], operational_candidate_evaluations=0, source_jobs=0,
                optimization="NOT_RUN", figures="NOT_RUN", phases_B_to_F="NOT_RUN",
                correlation_policy=m.POLICY, security_status=protocol["security_status"], lifecycle=protocol["lifecycle"],
                manuscript_changed=False, production_changed=False, old_sources_changed=False,
                protocol_sha256=sha(OUT/"protocol.json"),
                producer_sha256={n: sha(OUT/n) for n in ["model.py", "run.py", "test_model.py"]})
    if catalog["receipt_unlocated"]: gate["blockers"].append("SOURCE_CONVERGENCE_RECEIPTS_UNLOCATED")
    if catalog["identity_fail"]: gate["blockers"].append("SOURCE_IDENTITY_FAILURE")
    if context["numerical_status"] != "CURRENTLY_VERIFIED_PASS": gate["blockers"].append("NUMERICAL_PREFLIGHT_FAILED")
    save("gate.json", gate)
    report(protocol, context, catalog, tests, gate)
    save("execution_history.json", dict(started_UTC=started, completed_UTC=datetime.now(timezone.utc).isoformat(),
        channel_angles=[0], source_generation=False, source_AP=False, optimization=False,
        physical_SKR_evaluations=0, synthetic_component_tests=tests["tests_run"], later_phases="NOT_RUN"))
    save("artifact_manifest.json", dict(files={p.relative_to(OUT).as_posix(): sha(p) for p in sorted(OUT.rglob("*"))
         if p.is_file() and "__pycache__" not in p.parts and p.name not in ["artifact_manifest.json", "verification.json"]}))
    return gate


def verify():
    """Read saved evidence only; no model/source/numerical imports."""
    manifest = read(OUT/"artifact_manifest.json")
    for name, digest in manifest["files"].items():
        if sha(OUT/name) != digest: raise ValueError("Artifact changed: "+name)
    start = read(OUT/"startup_manifest.json")
    for name, digest in start["protected"].items():
        if sha(REPO/name) != digest: raise ValueError("Protected historical file changed: "+name)
    gate = read(OUT/"gate.json")
    if gate["phase_B_ready"] or gate["operational_candidate_evaluations"] != 0 or gate["source_jobs"] != 0:
        raise ValueError("Phase A authorization boundary violated")
    table = rows(OUT/"skr_vs_zenith.csv")
    if len(table) != 183 or {(int(r["zenith_deg"]), r["scheme"]) for r in table} != {(n, s) for n in range(61) for s in SCHEMES}:
        raise ValueError("Missing or duplicate output rows")
    for r in table:
        if r["status"] != "BLOCKED_PHASE_A" or r["correlation_policy"] != "manuscript_eq14_direct":
            raise ValueError("Invalid blocked row")
        if any(r[k] != "" for k in ["I_AB", "beta_I_AB", "chi_BE", "K_raw", "Z_manuscript_eq14"]):
            raise ValueError("Blocked point contains a rate or Z")
    for path in OUT.glob("*.png"):
        raise ValueError("Phase A must not produce figures: "+str(path))
    if list(OUT.glob("*.pdf")): raise ValueError("Phase A must not produce PDF figures")
    return dict(status="CURRENTLY_VERIFIED_PASS", artifact_files=len(manifest["files"]),
                protected_historical_files=len(start["protected"]), blocked_rows=len(table),
                source_identity_pass=gate["existing_source_identity_pass"], phase_B_ready=False,
                phase_A_mathematical_status=gate["mathematical_status"], evaluator_rerun=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--phase", choices=list("ABCDEF"))
    group.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    if args.verify_only:
        print(json.dumps(verify(), indent=2)); return 0
    if args.phase != "A":
        gate = read(OUT/"gate.json") if (OUT/"gate.json").exists() else {"blockers": ["PHASE_A_NOT_RUN"]}
        print(json.dumps(dict(status="BLOCKED_PHASE_DEPENDENCY", phase=args.phase,
            blockers=gate["blockers"], message="B-F are not implemented or executed while Phase A mathematical dependencies remain unresolved.")))
        return 2
    print(json.dumps(phase_a(), indent=2)); return 0


if __name__ == "__main__":
    raise SystemExit(main())
