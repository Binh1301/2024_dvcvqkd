# Kế hoạch khôi phục Uniform — chưa được thực thi

## Bước tiếp theo được khuyến nghị

**Chuẩn bị và kiểm tra wrapper observability/checkpoint trước khi xin một attempt
nguồn mới.** Không lặp lại mù job 3.600 s. Lượt này chỉ chẩn đoán và lập kế hoạch;
không tạo wrapper thay kernel, không chạy source job và không tăng ngân sách.
Đường chạy có checkpoint dưới đây là đề xuất cần triển khai/kiểm tra trước lượt
được phép; hiện repository chưa có recovery runner này. Không gọi đó là sẵn sàng.

## Input khóa

- Uniform 256-QAM, `nu_raw=0`, `nu_repo=42.5*nu_raw=0`.
- VA decimal `1.6249995399703647`; binary64 `0x1.9ffff84830112p+0`.
- `VA=Vmod=2*nbar`, `X_A=2*Re(alpha)`; giữ ordering và amplitudes từ builder hiện có.
- Expected ensemble hash:
  `421664627da51107f1420322c7992ba5f12d9bd6af0ff767a473b8b93ffd00d7`.
- Producer Python hiện có:
  `results/uniform_positive_skr_manuscript43_20261023/source_python_job.py`,
  SHA-256 `3f37cf9a89e5a626081deaa5cef2f85b988872a53ac09b20d782ee9264241b8f`.
- Kernel `scripts/full_support_c4_worker.py`, SHA-256
  `2cd1feeb3e1d6e734fd36df9928878f378a55dc3b1a5d58c7f816302c26859e1`.
- Dùng phép diagonal solve đã được xác minh trong
  `results/uniform_manuscript_2d_optimization_20261019/diagonal_solve_worker.py`.
- Precision ladder giữ nguyên **1050/1250/1450**, full support 256; giữ source
  settings, physicality tolerance, implementation hashes và MB convention cũ.
- Python backend hiện được phép; không dùng đường GMP bị Application Control chặn.

## Lệnh tham chiếu có thể tái lập với producer hiện tại

Đây là lệnh cho **một lượt tương lai được duyệt riêng**, không chạy trong task này.
Tên output là một ví dụ mới ở cấp con trực tiếp của `results/`, vì launcher tính
project root từ vị trí file. Lệnh không ghi vào attempt timeout hay cache lịch sử.

```powershell
Set-Location 'C:\Users\HP\Documents\GitHub\2024_dvcvqkd\paper_uav_hap_cvqkd'
$futureUniformDir = Join-Path (Get-Location) 'results/skr_vs_zenith_eq14_v43_uniform_recovery_authorized_attempt01'
if (Test-Path -LiteralPath $futureUniformDir) { throw 'Preserve existing attempt; choose a new authorized run ID' }
New-Item -ItemType Directory -Path $futureUniformDir | Out-Null
Copy-Item -LiteralPath 'results/skr_vs_zenith_eq14_v43_phaseB_readiness_20261024/generate_uniform.py' -Destination (Join-Path $futureUniformDir 'generate_uniform.py')
& '.venv/Scripts/python.exe' -X utf8 -B (Join-Path $futureUniformDir 'generate_uniform.py') '1.6249995399703647' 2>&1 | Tee-Object -FilePath (Join-Path $futureUniformDir 'console.log')
```

**Giới hạn rõ ràng:** lệnh tham chiếu trên giữ producer cũ, timeout 3.600 s và
**không có checkpoint/resume**. Nó là đường chạy chuẩn để đối chiếu, không phải
khuyến nghị retry ngay. Không dùng nó để tuyên bố đã giải quyết nguyên nhân timeout.
Sau khi wrapper checkpoint được kiểm tra, ghi lệnh CLI thật của wrapper ấy cùng
producer hash vào một protocol tương lai riêng, trước khi thực thi. Không chỉ
thay đường dẫn trong một lệnh giả định tới script chưa tồn tại.

## Đặc tả tối thiểu cho wrapper checkpoint tương lai

1. Dùng builder hiện có tạo đúng ensemble; ghi cả PMF/amplitude digest, 64 orbit
   probabilities/prototypes dạng `float.hex`, source settings và expected hash.
   Khóa request SHA-256 trước khi tạo worker; xác minh lại ngay trước khi ghép payload.
2. Gọi **nguyên `_row(p,z,digits)`** của kernel đã hash, với cùng diagonal solve,
   tuần tự ở ba mức. Không thay eigensolver, không hạ precision và không bỏ mức
   1050 để chạy nhanh hơn. Không đồng thời mở thêm source job.
3. Thêm marker bắt đầu/kết thúc cho mỗi row, `_sectors` và từng `mp.eighe`.
   Ghi log trực tiếp ra file riêng, flush ngay; lấy CPU/RSS/PID định kỳ. Có thể
   dùng `faulthandler.dump_traceback_later` để giữ stack khi row lâu. Không dùng
   dump cProfile từ thread giám sát nếu thao tác đó vô tình tắt profiling.
4. Khi row hoàn tất, ghi `row_1050.json`, `row_1250.json`, `row_1450.json` qua file
   tạm rồi atomic replace. Mỗi file chứa request/ensemble/producer/backend hashes,
   precision, rank, resolved, minimum eigenvalue, C,w strings của kernel, timing,
   trạng thái và SHA-256 receipt. Chưa ghép final C,w nếu thiếu row hoặc evidence.
5. Resume chỉ nhận checkpoint đúng mọi identity, hash, precision và schema.
   Không có checkpoint từ attempt cũ để reuse. Row sai identity/hash phải dừng,
   không tự ghi đè. Row đã hoàn tất không cần tính lại trong cùng request.
6. Checkpoint trong một row tại từng sector là cải tiến tiếp theo, chỉ làm nếu
   timer cho thấy một row vượt ngân sách. Nếu lưu eigenvectors/eigenvalues, phải
   round-trip đầy đủ giá trị arbitrary precision, không dùng complex128 hay
   chuỗi 50 chữ số cho các ma trận cần dùng tiếp. Cần kiểm tra riêng trước resume.
7. Khi đủ rows, áp dụng guard hiện có và tạo cache payload bằng identity/schema
   của producer cũ; receipt phải giữ toàn bộ precision rows, request, code hashes,
   backend, elapsed/CPU và payload file hash. Không sửa bất kỳ cache cũ nào.

Wrapper này chỉ thay orchestration/observability, không thay định nghĩa C,w.
Trước khi chạy nguồn thật, dùng stub trả rows đã lưu để kiểm tra checkpoint,
resume, timeout, dependency mismatch, atomic write và việc không tạo payload
khi chưa đủ precision. Sau đó reviewer xác nhận lệnh, output và ngân sách.

## Hội tụ và kiểm chứng đầu ra

- Mọi mức mà readiness receipt checker yêu cầu phải resolved, rank 256,
  minimum eigenvalue dương hữu hạn. Không lấy rank float64 làm bằng chứng.
- Giữ kiểm tra cuối kernel cho 1250/1450:
  `abs(a-b) <= 1e-7 + 1e-6*max(abs(a),abs(b))` cho C và w.
- Giữ nguyên strict `check_receipt` của Phase A: exact payload binding, đầy đủ
  ladder và support; C,w của từng row phải khớp payload ở độ biểu diễn mà checker
  đã yêu cầu. Nếu guard kernel qua nhưng receipt checker chưa qua, báo REVIEW,
  không nới tolerance hoặc tự nâng hạng nguồn.
- Kiểm tra PMF, centering, C4, exact VA/nu, `2*nbar=VA`, ensemble hash trước/sau;
  xác minh payload cache key, source implementation/settings và file hash.
- Không dùng C,w hoặc eigensystem từ VA lân cận hay Fixed MB.
- Sau khi nguồn hợp lệ vẫn phải giải quyết 73 evidence gaps khác và chạy lại
  readiness. Một Uniform thành công không tự cho phép pilot.

## Ngân sách và failure handling cần phê duyệt trước

Đề xuất thảo luận cho đúng một source: per-row tối đa 3.600 s, tổng row budget
tối đa 10.800 s, tuần tự. Đây là **ngân sách đề xuất chưa được áp dụng/cho phép**,
không phải dự báo runtime. Chỉ chốt sau khi instrumentation và stub tests qua.
Có thể vẫn timeout trong row đầu; checkpoint theo row không giải quyết trường
hợp đó, và cần dựa trên profile để quyết định checkpoint sector hay tối ưu khác.

Theo dõi wall-clock, CPU và memory riêng. Timeout thì terminate đúng process
tree của job, giữ log/stack/checkpoints, đánh dấu BLOCKED; không auto retry.
Không sửa tolerance, chuyển backend trái chính sách, hoặc tạo payload cuối từ
rows thiếu. Khi clock hết, dừng dù có vẻ sắp xong. Không hứa thời gian hoàn tất.

## Artifacts kỳ vọng của lượt tương lai

`request.json`, `preflight.json`, code/backend/environment manifest,
`progress.jsonl`, `stderr.log`, `cpu_memory.jsonl`, ba row checkpoints/receipts,
`exact_source_cache/<key>.json`, `source_receipts/<ensemble_hash>.json`,
`outcome.json`, final validation receipt và protection manifest.
Nếu thất bại, final payload/receipt hội tụ phải vắng mặt hoặc mang trạng thái
chưa được chấp nhận rõ ràng. Không ghi đè attempt 3.600 s đã seal.
