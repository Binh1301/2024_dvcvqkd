"""Close readiness evidence after the one authorized job finishes; never run a pilot."""
import io
import json
import unittest

import model
import provenance
import run
from support import OUT, ROOT, PREVIOUS, read, save, sha, write_csv


def report(gate, job, summary):
    counts = summary["counts"]
    rows = run.prior_run.old.rows(OUT / "pilot_source_verification.csv")
    new = next(r for r in rows if r["family"] == "Uniform" and r["VA_hex"] == "0x1.9ffff84830112p+0")
    preflight = read(OUT / "source_job_preflight.json")
    source_values = f"C={new.get('C') or 'chưa có'}, w={new.get('w') or 'chưa có'}"
    text = f"""# Cập nhật validation — mức sẵn sàng cho pilot chín góc

**Quyết định Phase B: {gate['decision']}.** Runner đã được chuẩn bị và kiểm tra;
chưa chạy pilot chín góc hoặc sweep 61 góc. `readiness.json` là gate hiện hành.
Đây là bản bổ sung cho Phase A đã seal trong `../skr_vs_zenith_eq14_v43_20261024/`.

## Nguồn của pilot

| Phân loại | Số nguồn |
|---|---:|
| VERIFIED_EXACT | {counts['VERIFIED_EXACT']} |
| VERIFIED_BY_ALTERNATIVE_EVIDENCE | {counts['VERIFIED_BY_ALTERNATIVE_EVIDENCE']} |
| INSUFFICIENT_EVIDENCE | {counts['INSUFFICIENT_EVIDENCE']} |
| INVALID | {counts['INVALID']} |
| Tổng pool đề xuất | 81 = 34 Uniform + 47 MB |

Danh sách từng nguồn và lý do: `pilot_source_verification.csv`.
Bằng chứng/hash/method/tolerance/limitations: `source_verification_evidence.json`.
`remaining_source_gaps.csv` chỉ rõ các dependency chưa giải quyết.

Đã kiểm tra 1.956 artifact lịch sử có tham chiếu ensemble pilot, khoảng 1,04 GB,
và tìm 138 ứng viên bằng chứng precision trên toàn bộ artifact lịch sử liên quan.
Loại riêng metadata đã quarantine/superseded và kết quả worker giả dùng cho test.
Không truy cập dataset final-test/held-out hay chạy lại các evaluator lịch sử.
Không chỉ giới hạn tìm kiếm trong thư mục `source_receipts`.

Nguồn có receipt trực tiếp được đối chiếu identity của payload, exact VA/nu,
hash ensemble, implementation/settings và precision ladder 1050/1250/1450,
full support 256, eigenvalue dương, resolved và C,w ở các mức precision.

Bằng chứng thay thế tìm được cho **Uniform VA=2, nu_raw=0** trong
`results/effective_channel_va2/source_moments_va2.json` và bản kết quả dẫn xuất.
Cả hash PMF và hash biên độ khớp chính xác với nguồn pilot, không chỉ cùng VA.
Các hàng full-support precision được kiểm tra với tolerance cũ
`1e-7 + 1e-6*abs(reference)` cho C,w; residual và sai khác với payload được lưu.
Giới hạn: các hàng này gắn với exact source arrays thay vì hash file payload
chính của pilot; không tính C,w lại và không chứng nhận security.

Mã cache lịch sử `scripts/run_exact_mb_test2.py` bỏ `fallback_rows` khi ghi
payload dù kernel chỉ nhận fallback đã qua `FULL_SUPPORT_CONVERGED`.
Các hash implementation, precision settings, cờ FRESH/route và việc C,w lặp lại
trong log là thông tin hỗ trợ. Chúng không tái tạo được các hàng precision đã mất;
không dùng chúng một mình để gán đã quan sát hội tụ cho từng nguồn.
**Thiếu receipt không được diễn giải thành C,w sai.**

## Job Uniform còn thiếu

- Yêu cầu duy nhất: VA `1.6249995399703647`, hex `0x1.9ffff84830112p+0`, nu_raw `0`.
- Kết quả job: **{job['status']}**, elapsed `{job.get('elapsed_seconds')}` giây.
- Lý do lỗi, nếu có: `{job.get('reason', 'Không có')}`.
- Giá trị lưu: {source_values}.
- Hash ensemble đầu vào đã khóa trong preflight: `{preflight['ensemble_hash']}`.
- Hash ensemble của payload: `{new.get('ensemble_hash') or 'chưa có payload'}`.
- Payload: `{new.get('source_path') or 'chưa có'}`.
- Payload SHA-256: `{new.get('source_sha256') or 'chưa có'}`.
- Phân loại nguồn: `{new['classification']}`.

`source_job_preflight.json` kiểm tra PMF Uniform, tâm, C4 và
`2*nbar=VA=E[X_A²]` trước job. `source_job_outcome.json` và
`new_exact_source/source_receipts/` giữ kết quả/receipt thực tế.
Dùng đúng producer Python/diagonal đã được kiểm tra trước, giữ precision ladder
1050/1250/1450, full support và kernel C,w. Một attempt, không retry, không dùng
GMP bị Application Control chặn. Không sửa cache lịch sử, không dùng VA=1.625
hoặc C,w của Fixed MB. Số lần tính C,w trong audit provenance bằng 0;
chỉ job nguồn mới này được phép tính C,w.

## Truy nguyên frozen-spec hash

Hash lịch sử `561fecc97cdf9967034ffd6865c1605804b624b98f47a091e47f17e520a2a7b1`
được khôi phục **đúng bytes từ Git commit**
`169791dc624df790914de109233d8a6824551374`.
File hiện tại có hash
`df83ea63af3b475ecca03a44d22d3240ab24d695ff0ebef31f0cd6747db78c15`,
khớp nội dung đã commit tại HEAD sau bốn thay đổi nội dung kế tiếp.
Nguyên nhân là AGENTS giữ hash của snapshot cũ trong khi specification đã được
commit cập nhật; không phải local corruption hay chỉ LF/CRLF.

`inputs/historical_frozen_spec.md`, `inputs/current_frozen_spec.md`,
`inputs/historical_to_current.patch`, `frozen_spec_history.json` lưu bằng chứng.
`specification_comparison.csv` đối chiếu công thức, physical parameters,
precision, correlation policy và source identities.

Thí nghiệm được người dùng duyệt khác mô hình lịch sử: homodyne thực 1D,
effective channel từ moment, xi_det=0.005, aperture30cm/divergence35µrad,
direct Eq14, miền VA/nu hữu hạn và pool81 ensemble cụ thể.
Tài liệu frozen hiện tại còn chứa target tổng quát full-Z/ideal heterodyne
và một refreeze riêng cho baseline55cm/direct-Z, không tự coi các scope đó là
cùng thí nghiệm này.

Đã tạo specification riêng `experiment_spec_v1.json`, SHA-256
`4868392f68af9be5b52b684dac1a23d4242e4cf44a871d4e66944349aa874d21`.
`model.validate_protocol` kiểm tra hash specification này, bản lịch sử và file
frozen hiện tại. Không sửa frozen spec, không đổi hash kỳ vọng cũ trong AGENTS
và không tắt hash check. Sai khác đã được truy nguyên và xử lý bằng versioned
experiment binding cho scope hiện tại; không nâng quyền cho production/toàn dự án.

## Runner và kiểm tra readiness

`run.py` hỗ trợ `--plan`, `--verify-only` và runner `--pilot` có gate.
Các góc cố định: 0,5,10,15,20,30,40,50,60°; dự kiến 9 context và 729 cặp nguồn–góc.
Pool giống nhau tại mọi góc. Uniform chọn VA trên34 nguồn Uniform; Fixed MB
giữ đúng một ensemble; Optimized MB xét toàn bộ81 nguồn gồm Uniform và Fixed MB.
Không thay pool chưa đủ bằng chứng bằng một subset mà không ghi nhận/phê duyệt.

Mỗi context tính moment [0,1] một lần. Mỗi nguồn tính effective eta_f/xi_f,
Z Eq14 trực tiếp, MI homodyne rời rạc, Holevo Eq13 và raw SKR.
Code Eq14/Eq13 dùng lại trực tiếp function đã kiểm tra của Phase A.
Các scheme dùng cùng context, noise, beta và receiver. Giữ SKR âm; không tạo
điểm dương, tìm interval Z, chọn endpoint hay nội suy C,w.
Giữ cùng xi_ch/xi_det; xi_f vẫn được tính lại theo VA và kênh bằng Eq. (17).
GH64/128 và80/110digits vẫn được kiểm tra; điểm ngoài miền có trạng thái lỗi,
không sửa căn/eigenvalue/Z. Checkpoint khóa pool/protocol/code/evidence;
moment, MI và Holevo có timing riêng. Raw candidate records và ba lựa chọn
được xuất nếu pilot được chạy ở một lượt được phép sau này.

Kiểm tra chuẩn bị runner/provenance: {gate['runner_checks_status']}.
Kết quả bundle tests, gồm kiểm tra receipt nguồn mới:
`readiness_tests.json` — {gate['readiness_tests_status']}.
Các test kiểm tra source binding/alternative evidence, exact VA/receipt nguồn mới,
frozen history/spec binding, ba scheme với raw K âm, context dùng chung, lỗi miền
không bị sửa và gate chặn trước tính kênh/tạo thư mục. Không chạy lại toàn bộ
9 tests khoa học Phase A đã seal; chúng được kiểm tra hash và tái dùng.
`pilot_plan.json` là kế hoạch metadata, không phải kết quả pilot.

## Dependency còn lại và quyết định

Blockers máy đọc: `{'; '.join(gate['blockers']) or 'không có'}`.
Các nguồn `INSUFFICIENT_EVIDENCE` cần receipt/diagnostic hội tụ có thể gắn với
đúng ensemble trước khi dùng pool81 theo gate hiện tại. Fixed MB nằm trong
nhóm cần kiểm tra nếu chưa có bằng chứng được xác minh; không thay source của nó.
Không yêu cầu tính lại toàn bộ catalog212. Không tự mở một chiến dịch C,w lớn
hoặc tăng ngân sách job để lấp các evidence gaps.

Các prerequisite về specification và runner đã được xử lý độc lập với source gaps.
Không gọi source C,w sai vì thiếu lịch sử precision. Để đổi policy chấp nhận
bằng chứng hoặc thay pool, cần một quyết định rõ ràng riêng; bản này không áp dụng.

Kiểm chứng chỉ đọc từ project root:

```powershell
.venv/Scripts/python.exe -X utf8 -B results/skr_vs_zenith_eq14_v43_phaseB_readiness_20261024/run.py --verify-only
```

`verification.json` ghi kiểm tra hash/protection/diff cuối. Giữ nguyên production,
PDF, frozen spec và cache nguồn cũ, `UNVALIDATED_SECURITY_MODEL`,
`NOT_READY_FOR_PUBLICATION_SCALE_RUNS` và `ObjectiveC USER_STOPPED`.
Không pilot, sweep61, training, test/held-out hoặc publication evaluation.
"""
    (OUT / "validation_report_vi.md").write_bytes(text.encode("utf-8"))


def finalize():
    if (OUT / "artifact_manifest.json").exists():
        raise FileExistsError("Preserve completed readiness evidence")
    attempts = list((OUT / "new_exact_source").glob("python_attempt_*.json"))
    if len(attempts) != 1:
        raise ValueError("Exactly one source-job attempt must be recorded")
    job = read(attempts[0])
    if job["status"] == "RUNNING":
        raise ValueError("Wait for the single authorized source job; never launch another")
    save(OUT / "source_job_outcome.json", dict(job, attempt_path=attempts[0].relative_to(ROOT).as_posix(),
        attempt_sha256=sha(attempts[0]), total_authorized_attempts=1, historical_caches_modified=False))
    protocol = read(OUT / "protocol.json")
    for name in ["support.py", "model.py", "run.py", "provenance.py", "generate_uniform.py", "test_readiness.py", "finalize_readiness.py"]:
        protocol["dependency_sha256"][(OUT / name).relative_to(ROOT).as_posix()] = sha(OUT / name)
    save(OUT / "protocol.json", protocol)
    model.validate_protocol(protocol)
    summary = provenance.investigate()
    import test_readiness
    initial = read(OUT / "readiness_tests_initial.json")
    if initial["producer_sha256"] != sha(OUT / "test_readiness.py"):
        raise ValueError("Readiness tests changed after initial verification")
    names = ["test_single_source_job_exact_VA_and_full_receipt",
             "test_historical_spec_hash_recovered_and_versioned_spec_bound",
             "test_classifications_cover_the_proposed_pool_without_invalidating_missing_receipts"]
    log = io.StringIO()
    result = unittest.TextTestRunner(stream=log, verbosity=2).run(unittest.TestSuite(
        test_readiness.ReadinessTests(name) for name in names))
    (OUT / "readiness_tests_final.log").write_bytes(log.getvalue().encode())
    tests_pass = initial["status"] == "CURRENTLY_VERIFIED_PASS" and result.wasSuccessful() and not result.skipped
    test_status = "CURRENTLY_VERIFIED_PASS" if tests_pass else "NOT_RUN" if result.skipped and result.wasSuccessful() else "FAILED"
    save(OUT / "readiness_tests.json", dict(status=test_status,
        unique_tests=11, initial_tests_run=initial["tests_run"], final_tests_run=result.testsRun,
        total_executions=initial["tests_run"]+result.testsRun, final_failures=len(result.failures),
        final_errors=len(result.errors), final_skipped=len(result.skipped),
        initial_receipt="readiness_tests_initial.json", final_log="readiness_tests_final.log",
        source_job_test=names[0], producer_sha256=sha(OUT / "test_readiness.py"), pilot_executed=False))
    rows = run.prior_run.old.rows(OUT / "pilot_source_verification.csv")
    gaps = [r for r in rows if r["classification"] not in provenance.ACCEPTED]
    write_csv(OUT / "remaining_source_gaps.csv", gaps)
    blockers = []
    if summary["counts"]["INSUFFICIENT_EVIDENCE"]:
        blockers.append("INSUFFICIENT_SOURCE_EVIDENCE:"+str(summary["counts"]["INSUFFICIENT_EVIDENCE"]))
    if summary["counts"]["INVALID"]:
        blockers.append("INVALID_SOURCE_IDENTITIES:"+str(summary["counts"]["INVALID"]))
    if all(r.get("source_path") for r in rows):
        try:
            run.check_pool_identity(rows, protocol)
        except model.ModelBlocked:
            blockers.append("POOL_IDENTITY_DIFFERS_FROM_VERSIONED_SPEC")
    if job["status"] != "CURRENTLY_VERIFIED_PASS": blockers.append("UNIFORM_SOURCE_JOB_"+job["status"])
    if not tests_pass: blockers.append("SOURCE_JOB_CHECK_NOT_RUN" if test_status == "NOT_RUN" else "READINESS_CHECKS_FAILED")
    dependencies = {n: sha(OUT / n) for n in ["protocol.json", "source_verification_summary.json",
        "source_verification_evidence.json", "pilot_source_verification.csv", "readiness_tests.json",
        "experiment_spec_v1.json", "frozen_spec_history.json", "source_job_outcome.json"]}
    dependencies = {(OUT / n).relative_to(ROOT).as_posix(): h for n, h in dependencies.items()}
    dependencies.update(protocol["dependency_sha256"])
    for row in rows:
        if row.get("source_path"): dependencies[row["source_path"]] = row["source_sha256"]
    evidence = read(OUT / "source_verification_evidence.json")
    for item in evidence["sources"]:
        if item["source"]["classification"] not in provenance.ACCEPTED: continue
        for receipt in item["direct_receipts"]+item["alternative_evidence"]:
            dependencies[receipt["path"]] = receipt["sha256"]
    gate = dict(decision="BLOCKED" if blockers else "PASS", phase_B_ready=not blockers,
        blockers=blockers, source_status_counts=summary["counts"], verified_available=summary["verified_available"],
        proposed_pool_size=81, source_job_status=job["status"], source_job_attempts=1,
        frozen_spec_resolution="CURRENTLY_VERIFIED_PASS_DISTINCT_VERSIONED_EXPERIMENT",
        pilot_runner_prepared=True, runner_checks_status=initial["status"], readiness_tests_status=test_status,
        phase_A_9_checks="SEALED_HASH_VERIFIED_REUSED", correlation_policy=model.POLICY,
        dependency_sha256=dependencies, pilot_executed=False, full_sweep_executed=False,
        channel_evaluations_in_this_readiness_task=0, operational_candidate_evaluations=0,
        source_Cw_recomputations_in_audit=0, security_status=protocol["security_status"], lifecycle=protocol["lifecycle"])
    save(OUT / "readiness.json", gate)
    save(OUT / "pilot_plan.json", run.plan())
    report(gate, job, summary)
    print(json.dumps({k: v for k, v in gate.items() if k != "dependency_sha256"}, indent=2))


if __name__ == "__main__":
    finalize()
