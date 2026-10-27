# Chẩn đoán timeout Uniform tại đúng VA của Fixed MB

## Kết luận có thể xác minh

Attempt duy nhất dùng `nu_raw=0`, VA binary64 `0x1.9ffff84830112p+0`
(`1.6249995399703647`), ensemble
`421664627da51107f1420322c7992ba5f12d9bd6af0ff767a473b8b93ffd00d7`.
`../skr_vs_zenith_eq14_v43_phaseB_readiness_20261024/source_job_outcome.json`
ghi `TimeoutExpired`, timeout child 3.600 giây, elapsed tổng
3600.0956285999855 giây, backend Python. Không có payload hoặc receipt hội tụ.

Call chain được traceback xác nhận:

```text
generate_uniform.main
  -> source_python_job.main
  -> gram_moments.c4_gram_source_moments
  -> source_uniform_diagonal.fallback
  -> subprocess.run(diagonal_solve_worker.py, timeout=3600)
  -> full_support_c4_worker.main -> _row
```

**Nguyên nhân trực tiếp:** subprocess exact-source vượt deadline wall-clock.
**Chưa xác định được bottleneck chính bên trong worker:** không có stage timer,
precision progress, peak-memory trace hay profile riêng của attempt này. Không
được kết luận chắc rằng `eighe`, tạo Gram, nhân ma trận hoặc kiểm tra hội tụ đã
chiếm phần lớn thời gian. Chưa có bằng chứng worker thất bại hội tụ về mặt số.

## Hoạt động trước timeout

Đã phục hồi 9 snapshot process từ bản ghi thực thi; xem
`historical_process_observations.json` và `uniform_cpu_timeline.json`.
Worker thực có PID **33676**, cùng thời điểm khởi tạo 09:40:09 ngày 24/10.
Các snapshot UTC có các mốc user-mode CPU:

| UTC | User CPU tích lũy (s) |
|---|---:|
| 02:52:02 | 535.4375 |
| 03:03:17 | 944.8125 |
| 03:09:48 | 1237.15625 |
| 03:12:27 | 1363.234375 |
| 03:20:50 | 1724.515625 |
| 03:25:25 | 1922.984375 |
| 03:29:50 | 2155.484375 |
| 03:34:39 | 2380.421875 |

Snapshot 02:56:38 ghi **total** CPU 676.59375 s; không trộn cột này với user CPU
trong bảng. `UserModeTime` của Win32_Process được đổi từ đơn vị 100 ns.
Mốc UTC là timestamp bản ghi tool call; lệnh polling hoàn tất sau đó vài giây.
PID giữ nguyên và CPU tăng cho thấy hoạt động tính toán tiếp diễn trong khoảng
quan sát, không phải process luôn chờ I/O. Điều này **không chứng minh tiến triển
hội tụ**, không loại trừ vấn đề bộ nhớ hay thời gian scheduler, và không cho biết
worker đang ở 1050, 1250 hay 1450 digits. Không có dữ liệu đủ để tách các nguyên
nhân này. Các lần restart audit provenance là process khác; không có bằng chứng
source worker đã restart hoặc tự retry.

## Những gì code thực sự làm

Nguồn: `scripts/full_support_c4_worker.py`, `_sectors` dòng 25, `_row` dòng 64,
`main` dòng 208. Hash và số dòng được lưu trong `uniform_diagnostic_checks.json`.
Đường chạy đã dùng patch diagonal solve được xác minh từ trước; không phải
đường LU nhiều vế phải ban đầu.

- Mỗi precision tạo lại bốn block coherent-state và bốn C4 sector 64×64.
- Mỗi precision gọi `mp.eighe` cho từng sector. Nếu chạy xong cả ba mức, có
  12 eigendecomposition và 49.152 lần gọi complex exponential theo vòng lặp.
  Đây là đếm tĩnh theo code, không phải số lần đã quan sát trong attempt timeout.
- Eigensystem được tái tính ở precision cao hơn để kiểm tra độ ổn định. Đây là
  công việc có mục đích; không thể dùng số float64 hoặc eigensystem precision
  thấp thay cho reference cao hơn.
- Sau eigendecomposition có nhiều phép nhân ma trận 64×64 và tính residual w.
  `mp.diag(z)`, hệ số từ p và các phép nhân với ma trận chéo xuất hiện lặp lại.
- Mọi row nằm trong list comprehension. Chỉ sau cả ba row và guard cuối, worker
  mới `json.dump` ra stdout. Không có checkpoint theo row/sector, stage log hay
  resume. Nếu đã hoàn tất row trước timeout thì kết quả ấy vẫn chỉ ở RAM.
- Parent dùng `capture_output=True`. Nhánh exception chỉ lưu loại lỗi/lý do;
  không lưu `TimeoutExpired.stdout/stderr`. Worker hiện cũng không phát progress.
- Không có vòng retry hoặc vòng tăng precision vô hạn. Ba row luôn chạy tuần tự.

## Kiểm tra nhẹ trên đúng ensemble

Chỉ xây ensemble và bốn sector float64, rồi xem eigenvalues của gate; không gọi
`c4_gram_source_moments`, `_row` hay AP eigensolver. Hash ensemble khớp preflight,
PMF đều 1/256, và `2*nbar=VA` trong tolerance 2e-12.

Gate float64 có minimum eigenvalue **−1.0951711763191722e−16**; số eigenvalues
dương lần lượt 36/35/35/35. Kiểm tra này mất khoảng 0.00344 s trên lượt đo cuối.
Nó giải thích nhu cầu fallback, **không xác định rank toán học hoặc C,w**. Không
được xem eigenvalues âm cỡ rounding ở đây là chứng cứ nguồn vật lý sai.

Hai receipt Uniform Python đã lưu tại VA=0.25 và VA=10 lần lượt mất
1930.035589 và 1916.598589 s. Đây là hai ensemble khác, không phải cam kết runtime
cho VA đang thiếu. Không nội suy C,w hay thời gian để khẳng định job này phải xong.
Profile của các MB probe khác không được gán sang attempt Uniform này.

## Cơ hội tăng tốc, chưa triển khai vào evaluator

| Đề xuất | Lợi ích có thể có | Điều kiện trước khi dùng |
|---|---|---|
| Timer/progress theo row, sector, eigensolver; stack dump định kỳ | Xác định bottleneck và còn hoạt động hay không | Chỉ thêm observability, log phải tồn tại khi timeout |
| Checkpoint từng row đã hoàn tất | Resume không mất row cũ | Khóa exact request, producer, precision, backend và receipt; ghi atomic |
| Checkpoint eigensystem từng sector | Giảm mất việc trong một row lâu | Round-trip arbitrary-precision values không mất bits; cần kiểm tra riêng |
| Hoist `diag(z)` và hệ số p trong cùng precision | Bỏ tạo ma trận giống nhau | Không tái sử dụng giá trị đã làm tròn từ precision thấp |
| Row/column scaling thay nhân dense với diagonal | Có thể giảm phép toán dư | Kiểm tra tương đương trên ma trận tổng hợp và nguồn có receipt; không đổi C,w |
| Hoist phần Uniform `p=1/256` | Giảm tính sqrt/hệ số trùng | Giữ ordering và amplitudes binary64; chưa đo speedup |
| Backend nhanh đã được hệ điều hành cho phép | Có thể giảm chi phí MP | Không load lại/di chuyển DLL bị Application Control chặn |

Không có intermediate đáng tin cậy để resume attempt cũ. Không dùng eigenvectors
từ VA khác, không thay đổi precision ladder, support, tolerance hoặc công thức.
Không chạy parallel nhiều row trước khi có phép đo memory/runtime của một job.
Không có speedup thực nghiệm được công bố từ lượt này.

## Giới hạn kết luận

CPU activity đã được phục hồi; numerical stage và thời gian từng hàm vẫn UNKNOWN.
Nguyên nhân sâu hơn có thể là chi phí MP thuần Python của eigensolver/ma trận,
điều kiện số của ensemble hoặc mức CPU được cấp. Đây là giả thuyết để profiling,
không phải chẩn đoán đã xác nhận. Xem `uniform_recovery_plan.md` cho bước tiếp theo.
