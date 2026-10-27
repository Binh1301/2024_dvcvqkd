# Cập nhật validation — mức sẵn sàng cho pilot chín góc

**Quyết định Phase B: BLOCKED.** Runner đã được chuẩn bị và kiểm tra;
chưa chạy pilot chín góc hoặc sweep 61 góc. `readiness.json` là gate hiện hành.
Đây là bản bổ sung cho Phase A đã seal trong `../skr_vs_zenith_eq14_v43_20261024/`.

## Nguồn của pilot

| Phân loại | Số nguồn |
|---|---:|
| VERIFIED_EXACT | 6 |
| VERIFIED_BY_ALTERNATIVE_EVIDENCE | 1 |
| INSUFFICIENT_EVIDENCE | 74 |
| INVALID | 0 |
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
- Kết quả job: **BLOCKED_BY_ENVIRONMENT**, elapsed `3600.0956285999855` giây.
- Lý do lỗi, nếu có: `Command '['C:\\Users\\HP\\Documents\\GitHub\\2024_dvcvqkd\\paper_uav_hap_cvqkd\\.venv\\Scripts\\python.exe', 'C:\\Users\\HP\\Documents\\GitHub\\2024_dvcvqkd\\paper_uav_hap_cvqkd\\results\\uniform_manuscript_2d_optimization_20261019\\diagonal_solve_worker.py']' timed out after 3600 seconds`.
- Giá trị lưu: C=chưa có, w=chưa có.
- Hash ensemble đầu vào đã khóa trong preflight: `421664627da51107f1420322c7992ba5f12d9bd6af0ff767a473b8b93ffd00d7`.
- Hash ensemble của payload: `chưa có payload`.
- Payload: `chưa có`.
- Payload SHA-256: `chưa có`.
- Phân loại nguồn: `INSUFFICIENT_EVIDENCE`.

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

Kiểm tra chuẩn bị runner/provenance: CURRENTLY_VERIFIED_PASS, **10/10 test đạt**.
Kiểm tra receipt của nguồn Uniform mới không chạy được vì job timeout và không có
payload. Tổng cộng có 11 test khác nhau: 10 đạt, 1 bị skip do dependency này;
hai test binding/classification được kiểm tra lại sau khi job kết thúc.
Kết quả bundle tests, gồm kiểm tra receipt nguồn mới:
`readiness_tests.json` — NOT_RUN.
Các test kiểm tra source binding/alternative evidence, exact VA/receipt nguồn mới,
frozen history/spec binding, ba scheme với raw K âm, context dùng chung, lỗi miền
không bị sửa và gate chặn trước tính kênh/tạo thư mục. Không chạy lại toàn bộ
9 tests khoa học Phase A đã seal; chúng được kiểm tra hash và tái dùng.
`pilot_plan.json` là kế hoạch metadata, không phải kết quả pilot.

## Dependency còn lại và quyết định

Blockers máy đọc: `INSUFFICIENT_SOURCE_EVIDENCE:74; UNIFORM_SOURCE_JOB_BLOCKED_BY_ENVIRONMENT; SOURCE_JOB_CHECK_NOT_RUN`.
Các nguồn `INSUFFICIENT_EVIDENCE` cần receipt/diagnostic hội tụ có thể gắn với
đúng ensemble trước khi dùng pool81 theo gate hiện tại. Fixed MB nằm trong
nhóm cần kiểm tra nếu chưa có bằng chứng được xác minh; không thay source của nó.
Không yêu cầu tính lại toàn bộ catalog212. Không tự mở một chiến dịch C,w lớn
hoặc tăng ngân sách job để lấp các evidence gaps.

Hành động tối thiểu trước pilot với đúng pool 81 nguồn:

1. Bổ sung bằng chứng hội tụ gắn với đúng ensemble cho **73 nguồn đã có payload**:
   26 Uniform và 47 MB, gồm Fixed MB. Ưu tiên phục hồi receipt/diagnostic đã lưu;
   không cần tạo lại các payload C,w đã có chỉ vì thiếu receipt.
2. Có payload cùng receipt hội tụ cho Uniform tại đúng VA hex
   `0x1.9ffff84830112p+0`, nu_raw=0. Attempt duy nhất đã timeout sau
   3600.0956285999855 giây; không có C,w để xác minh hoặc dùng cho pilot.
   Nếu cần tính lại, phải có quyết định riêng về attempt/ngân sách, vì lượt này
   không tự retry hay tăng timeout. `source_job_cleanup.json` xác nhận không còn
   worker nguồn chạy sau timeout.
3. Khi đủ hai dependency nguồn trên, chạy lại các kiểm tra receipt/binding bị
   thiếu và tạo readiness PASS mới trước khi chạy pilot. Không cần mở lại các
   quyết định [0,1], VA=2*nbar hoặc Eq. (14).

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
