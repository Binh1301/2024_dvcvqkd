Không có điểm SKR dương ở Rx8–30cm trong miền đã thử.

| Cấu hình | Rx (cm) | Divergence (µrad) | Jitter (µrad) | σh (m) | Tx99 (cm) | VA | νraw | K (bit/use) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 — Ít thay đổi về khẩu độ thu | 40.1 | 25.0785813719 | 1.561 | 0.1 | 11.9411648851 | 1.77777775971 | 0.3 | 0.000283673880404 |
| 2 — Cân bằng, có dự trữ pointing | 55 | 35 | 3 | 0.1 | 8.55621357843 | 2.15 | 0.22 | 0.035149837665 |
| 3 — Hiệu năng cao hơn, đòi hỏi Tx lớn | 55 | 15 | 3 | 0.1 | 19.9644983497 | 2.15 | 0.22 | 0.0804568149166 |


Cấu hình2 là kịch bản có dự trữ pointing tốt nhất trong shortlist; Rx40.1/55cm vẫn cần chứng minh SWaP. Các tốc độ là numerical diagnostic; chưa xác nhận hardware/security.
