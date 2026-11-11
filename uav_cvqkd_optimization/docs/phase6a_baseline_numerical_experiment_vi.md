# Phase6A — thí nghiệm quỹ đạo numerical diagnostic

Phạm vi: tác giả phê duyệt thực thi bốn thuật toán cho P1/P2 trong scenario tổng hợp xác định; không phải paper-mode, composable-security certification hoặc manuscript update. Yêu cầu nguyên văn tại [author request](approvals/phase6a_author_request.txt), approval hash-bound tại [approval](approvals/phase6a_author_approval.json), cấu hình tại [config](../configs/integration/phase6a_numerical_diagnostic.json).

## Nguồn và các quyết định thực thi

- **Mô hình vật lý:** profile rotor IEEE2019 được nạp nguyên bộ; không thay Z/w, MB-QAM/Holevo hoặc công thức năng lượng/finite-size/solver. Lookup clear-sky Phase5E được kiểm đủ package seals, raw signed SKR bits/use, channel noise0.0136 và detector noise0.005SNU. Đây là finite-catalog212-candidate numerical data, không phải optimum liên tục.
- **Finite-size:** N_full1e8, allocation0.8 và ba epsilon1e-8 lấy theo reference IEEE2025 đã lưu. Tác giả phê duyệt fs1e5uses/s và dt10s cho scenario này; m0=800000/clear-slot. Không biến cấu hình reference gốc thành mission default. Proxy không phải composable-security proof.
- **Mây:** artifact cũ dùng seed42. Đã dùng đúng các câu lệnh sinh NumPy của recipe được pin SHA để tạo realization **mới**,400components,seed20261108; không đổi nhãn artifact42. Giữ miền ban đầu16000x2000m, lưới mẫu400x50 cell-centers40m và clipping15mg/m³ của recipe cũ.
- **Ngưỡng:** empirical percentile90, method linear, trên toàn20000 mẫu miền ban đầu, frozen trước optimization. Kết quả15mg/m³. Do clipping,15.785% mẫu bằng ngưỡng và bị block theo phép >=; không chỉnh threshold để ép đúng10% diện tích. Đây là ngưỡng của scenario tổng hợp, không phải ngưỡng opaque-cloud phổ quát hoặc số từ manuscript.
- **LOS:** giao segment3D HAP→UAV với slab2000..4000m; CLWC giả định đồng nhất theo chiều đứng trong slab. Tái dùng intersection hiện có rồi chia theo độ dài **3D** với spacing<=20m và<=10m. So sánh toàn12100 node-times,0disagreements. Agreement trên mẫu rời rạc không chứng nhận giao liên tục cho mọi vị trí/thời gian. Không dùng endpoint UAV để thay LOS.
- **Mission:** HAP(1000,1000,20000)m,UAV altitude1000m,q0(1000,1000)m,area[0,2000]². Graph11x11,spacing200m,cardinal+hover; diagonal bị loại kể cả khi speed-feasible. dt10s,H100slots=1000s,query destinationq_k tại t_k=k*dt. Tất cả121nodes khớp exact lookup. Cạnh cardinal20m/s<=vmax30m/s.
- **Năng lượng:** P_hover=168.48421774108203W, Emax=1.1*P_hover*1000=185332.63951519027J, dẫn xuất từ raw IEEE profile. Max allowed edge1782.8938973481925J;100 lần max edge=178289.38973481925J<Emax. Vì vậy energy budget không binding trên bất kỳ path100slots của graph này; không được diễn giải scenario này là chứng minh lợi ích khi budget chặt.
- **Lambda:** implementation gốc có score reward_bits−lambda[bits/J]*edge_energy[J]. Trước optimization: Rscale=max_graph(m0*Rclear)=3964.2702319302bits/slot, Escale=max_allowed_edge=1782.8938973481925J. Balanced normalized score0.5*reward/Rscale−0.5*energy/Escale tương đương lambda=Rscale/Escale=2.223503169665061bits/J. Không dùng trực tiếp0.5bits/J và không tune sau khi xem kết quả.
- **DP:** gọi nguyên exact solver, label_cap=None, không beam/heuristic pruning. Predeclared watchdog300s process wall và4GiB RSS; nếu vượt thì lưu failure và chạy reduced benchmark25nodes/20slots riêng, không thay vào bảng full workload. P1/P2 được đánh giá chung trong mỗi lần method chạy; runtime không phải hai phép đo độc lập.
- **Thông tin:** DP có toàn predicted cloud horizon, được ghi là forecast-oracle; greedy chọn action theo current-slot. Mọi method chọn best feasible prefix hồi cứu; không có equal-information superiority hoặc causal online stopping claim.

Emitted uses, allocated signals và cloud erasure tách riêng:

\[
N_{emit,K}=f_sK\Delta t,\qquad n_K=m_0\sum z_k,\qquad
S_K=m_0\sum z_kR_{clear}(q_k),\qquad
\ell_K=\max(0,S_K-7\sqrt{n_K\log_2(2/\epsilon)}).
\]

Scenario lưu Rclear chưa mask; z được dùng đúng một lần trong valid-signal/raw contribution accounting. Blocked LOS có zero raw contribution. Một penalty được áp dụng trên mỗi accumulated prefix, không cộng slotwise. Clear-sky center full100slots: n=8e7,raw396427.02319302bits,penalty319190.55758722057bits,key proxy77236.46560579946bits.

## Thực thi và trạng thái

Lệnh thực tế từ package root:

```powershell
$env:PYTHONPATH='src'
python -X utf8 -B -u -m uav_qkd.phase6a_experiment --output results/phase6a_baseline_20261109
```

Tên thư mục giữ đúng yêu cầu tác giả. Ngày phiên làm việc2026-11-10 (Asia/Bangkok). Branch lúc bắt đầu `feat/11/8`,HEAD `965d93f94207895c1ce85d02576ef9388108bc19`,tracked worktree sạch; mọi file mới của task được tách riêng. Không commit/push.

**Preflight PASS; lần RSS retry hoàn tất đủ8/8 selected algorithm–objective solutions**, cả bốn methods FEASIBLE. Dataset chính:
[phase6a_baseline_20261109_rss_retry_20261110](../results/phase6a_baseline_20261109_rss_retry_20261110/).
Không có SKR regeneration hoặc native quantum evaluator call.

## Kết quả P1 — maximized accumulated proxy / elapsed time

| Method | P1 (bits/s) | Key proxy (bits) | Energy (J) | Stopping time (s) | Valid signals | LOS clear fraction |
|---|---:|---:|---:|---:|---:|---:|
| Stationary | 25.160230297 | 25160.230296656 | 168484.217741082 | 1000 | 61600000 | 0.77 |
| SKR-Greedy | 33.623045287 | 33623.045287247 | 169660.838380330 | 1000 | 64800000 | 0.81 |
| Energy-Aware Greedy | 33.276467694 | 33276.467693714 | 169170.579780643 | 1000 | 64800000 | 0.81 |
| Pareto DP (forecast oracle) | 77.040107780 | 77040.107779909 | 170641.355579704 | 1000 | 80000000 | 1.00 |

## Kết quả P2 — maximized accumulated proxy

| Method | P2 (bits) | Average proxy rate (bits/s) | Energy (J) | Stopping time (s) | Valid signals | LOS clear fraction |
|---|---:|---:|---:|---:|---:|---:|
| Stationary | 25160.230296656 | 25.160230297 | 168484.217741082 | 1000 | 61600000 | 0.77 |
| SKR-Greedy | 33623.045287247 | 33.623045287 | 169660.838380330 | 1000 | 64800000 | 0.81 |
| Energy-Aware Greedy | 33276.467693714 | 33.276467694 | 169170.579780643 | 1000 | 64800000 | 0.81 |
| Pareto DP (forecast oracle) | 77040.107779909 | 77.040107780 | 170641.355579704 | 1000 | 80000000 | 1.00 |

P1/P2 được đánh giá riêng trên mọi feasible prefix; trong scenario này cả hai chọnK100. Không épK cố định hoặc ép hai nghiệm giống nhau. DP tránh toàn bộ sampled blockage trong quỹ đạo được chọn, với raw clear-sky rates chính xác của từng node; không gán constant winner rate hoặc rate center cho toàn path. Ba baseline đều có key proxy dương, không có bước retune để làm dương.

Full trajectory có cảq0 tại0s vàq_k tại10..1000s trong `P1_trajectory.csv`/`P2_trajectory.csv` của từng thư mục method. Có clear state, raw clear rate, effective scheduled rate, contribution, emitted uses, allocation trước cloud, valid signals, accumulated raw/key proxy và cumulative energy. Xem `comparison_P1.csv`, `comparison_P2.csv`, `results.json`, `scenario.npz` và `cloud_realization.npz`.

## DP, runtime và memory

| Method | Joint P1/P2 computation (s) | Child process wall incl. spawn (s) | Parent-sampled child RSS peak (MiB) |
|---|---:|---:|---:|
| Stationary | 0.110566900 | 0.963544400 | 77.3984375 |
| SKR-Greedy | 0.117715800 | 0.998441700 | 78.11328125 |
| Energy-Aware Greedy | 0.113326000 | 1.010020400 | 77.5234375 |
| Pareto DP | 172.815173800 | 173.674637100 | 241.1796875 |

DP sinh10436173labels, strict dominance loại8072853labels trong cùng(k,j,u); peak frontier97060labels. `label_cap=null`, heuristic discarded labels=0, horizon100; classification **exact-on-graph theo solver float64 hiện có**, không phải optimum continuous trajectory/MB domain hoặc certificate cho numerical energy hull. Actual peak RSS được quan sát bởi parent là252895232bytes, mẫu100ms, không phải continuous-memory maximum chính xác. Python allocation peak không đo trong lần RSS retry.

**Lịch sử lần chạy được giữ nguyên:**

1. [Lần đầu có tracemalloc](../results/phase6a_baseline_20261109/) hoàn tất6/8 selections; DP full bị watchdog dừng sau300.1084979999978s, peak RSS parent490102784bytes. Last observed progressk93,generated7599858,peak79438; đây không phải final label count hoặc nghiệm full. Benchmark25nodes/20slots được chạy riêng và không thay vào bảng full. Mã producer đã thực thi lưu tại [executed_runner_with_tracemalloc.py](phase6a_validation/executed_runner_with_tracemalloc.py).
2. Lần retry bỏ allocation tracing, giữ **nguyên config hash và mọi array/scenario input**; cả bốn methods được chạy lại với cùng instrumentation policy RSS. Ba baseline solution dictionaries tái lập chính xác, DP full hoàn tất. Không thay đổi resource limits, thuật toán, dominance, λ hoặc mục tiêu để đạt kết quả. Đây là so sánh instrumentation trên cùng workload, không phải chứng nhận statistical speedup.
3. Trong retry, Windows trảWinError5 khi rename progress.tmp→progress.json gầnk97 (last complete progress timestamp148.04s), làm thread sampler child ngừng sớm. Solver vẫn hoàn tất bình thường và parent watchdog/RSS sampler chạy đến cuối; **memory trong bảng dùng parent100ms**, không dùng peak child235724800bytes như một phép đo10ms đầy đủ. `progress.tmp` còn lại được giữ và hash-seal, không sửa dữ liệu để che lỗi. Final labels lấy trực tiếp từ completed solver diagnostics, không từ stale progress.
4. Sau khi lưu [executed_runner_rss_retry.py](phase6a_validation/executed_runner_rss_retry.py) khớp producer hash của retry, sửa riêng telemetry: retry transient Windows rename lock, ghi lỗi progress và tiếp tục RSS sampling. Hai regression tests tái hiệnRED→GREEN. Không tính lại/ghi đè kết quả khoa học; source snapshots phân biệt executed code và bản code đã sửa cho lần chạy tương lai.

## Kiểm chứng và tests

[Artifact verification](phase6a_validation/artifact_verification.json) PASS:22output hashes mỗi attempt,7input hashes,32producer hashes (producer đã thực thi được đối chiếu snapshot tương ứng),1267existing files không thay đổi. Kiểm độc lập đủ8selected full trajectories/800prefix rows: cardinal/speed/budget, source raw rate, z, emitted/allocation/valid signals, accumulated penalty và objective arithmetic. Shared scenario digest khớp giữa hai attempt; tất cả baseline solution objects tái lập exact. Không sửa original config/model/rotor/paper.yaml/lookup/pilots/results.

[Independent review](phase6a_independent_review.md) kiểm riêng actual artifacts, full/reduced separation, nguồn/hashes và prefix quantities. Suite cuối trên mã đã sửa telemetry: **206 passed in103.31s,0failed,0errors,0skipped**, exit0; gồm193tests có sẵn và13case mới. Lệnh `python -X utf8 -m pytest -q --junitxml=docs/phase6a_validation/tests.xml`; evidence tại [tests.xml](phase6a_validation/tests.xml) và [verification receipt](phase6a_validation/verification.json). Hai regression lỗi file lock đã tái hiệnFAILED trước khi sửa, sau đóPASS; không giấu lỗi runtime của producer cũ. Console observation được lưu riêng tại [telemetry observation](phase6a_validation/telemetry_console_observation.json).

Thay đổi chỉ gồm runner numerical diagnostic mới,13focused tests,config/approval/source request,report/plan/review/validation và hai kết quả mới. File lịch sử và mathematical models không thay đổi. Figure catalog vẫn1READY/9BLOCKED, paper-modeNOT_RUN; không tạo hình paper, không nâng source/security evidence và không commit/push.

## Phạm vi bảo toàn và việc tiếp theo

Parent frozen spec có current SHA df83ea63af3b475ecca03a44d22d3240ab24d695ff0ebef31f0cd6747db78c15 khác historical expected hash trong AGENTS. Không restore/đổi spec; publication/model-sensitive work vẫn bị chặn. Phase6A chỉ tiêu thụ sealed numerical rates và scenario vừa được tác giả cho phép, không chạy native quantum model, training/heldout/final-test hoặc nâng lifecycle/source/security labels.

Sensitivity tiếp theo cần phê duyệt riêng: Emax thấp hơn để budget thực sự binding; CLWC threshold/seed/layer; LOS spacing nhỏ hơn gần boundary; graph/dt resolution và DP runtime scaling; fs/allocation/epsilon trong scope proxy; forecast uncertainty hoặc baseline cùng quyền dự báo. Không tự chạy các sweep này.

Independent review ghi một minor ngoài cấu hình phê duyệt: biểu thức lambda tổng quát cho trọng số khác0.5 cần đảo tỷ số trọng số. Với weight0.5 cố định trong config hash-bound hiện tại, hệ số đã tính đúng và không ảnh hưởng kết quả. Thay đổi trọng số phải có task sửa/kiểm thử riêng trước khi chạy.
