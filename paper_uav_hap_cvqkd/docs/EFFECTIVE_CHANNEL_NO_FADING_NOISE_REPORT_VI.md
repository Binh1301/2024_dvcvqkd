# SKR Gaussian hiệu dụng khi bỏ phương sai fading

Ngày 2026-10-13. Thực hiện đúng quyết định của người dùng trong mode riêng
**effective_channel_no_fading_noise** tại một điểm:
L = 21.9393102292 km, nu_raw = 0.165, V_A = 5.5.
Ideal heterodyne R = 1, xi_det = 0, chi_het = 1, beta_rec = 0.95,
xi_ch = 0.0186; phase noise và AO OFF.

**Kết quả: SKR chẩn đoán = +0.05863015022113771 bit/use.**
Đây là xấp xỉ kênh Gaussian bỏ phương sai fading theo quyết định của người dùng.
Không phải exact fading-channel security lower bound hay tốc độ khóa đã chứng nhận.

## Mode riêng và phạm vi

| File | Vai trò |
|---|---|
| src/effective_channel_no_fading_noise.py | Mapping T_eff/xi cố định; tái dùng discrete MI, Eq. (20) và Holevo tại Z_star |
| configs/effective_channel_no_fading_noise.json | Cấu hình cố định cho đúng một candidate |
| scripts/run_effective_channel_no_fading_noise.py | Entry riêng, xác minh cache/physics; marker ngăn execution lặp |
| tests/test_effective_channel_no_fading_noise.py | 5 kiểm tra scoped, gồm uncertainty và MI likelihood phức đầy đủ |
| results/effective_channel_no_fading_noise/reference_20261013/ | Snapshot, result, test output và preservation receipts |

Module mới nằm ngoài src/channel và src/cvqkd để giữ nguyên historical objective
identity. Historical, manuscript_literal_3moments và manuscript_corrected_3moments
giữ nguyên code/config/results. Không đổi default mode hoặc frozen specification.

Chạy entry đúng một lần:

    .\.venv\Scripts\python.exe -B scripts/run_effective_channel_no_fading_noise.py

Execution marker đã tồn tại sau lần này; entry sẽ từ chối duplicate run.
Các phép GH8/16/32 và kiểm tra full 256-symbol đều thuộc cùng một candidate,
không phải sweep hoặc optimization.

## PDF, ba mômen và source được giữ nguyên

Physics được tái dựng bằng helper cũ với đúng override D55/theta10:
HAP/UAV 20/1 km, lambda 1550 nm, tau_zen = 0.92, w0 =
0.0986760647169751 m, receiver diameter 0.55 m và cùng jitter/AoA/HV profile.
Raw Eq. (10) input dictionary phải bằng dictionary của corrected ideal reference.
Physical law vẫn condition active trên 0 < eta <= 1 và giữ atom outage.

| Quantity | Giá trị giữ nguyên |
|---|---:|
| Physical mixed mass | 0.9999999999999999 |
| Raw mass trên [0,1] | 0.9841200272202841 |
| m1 = mean eta | 0.23790886783673015 |
| mh = mean sqrt eta | 0.40114871429673266 |
| mn = mean eta xi_total | 1.7665162371050331 |
| T_eff = mh² | 0.16092029098192165 |
| C từ cache | 3.2113076519605626 |
| w từ cache | 1.0248765983174194e-6 |

Residual mới − corrected reference cho cả ba mômen, physical/raw mass và outage
atom đều bằng 0. Không tính lại C,w.

Source key:
77fc4a06afc0dba6d2e357db36dc216d34677f30d69fdf1f78781b105af39f1c.
Ensemble hash:
430914e792382cce5d92b0ff5ba4e8a641e912bce78c8565dbc18540b92b2faa.
Payload SHA-256:
d0b9a83a625437a6f056e990b3de61aa95c375940ee7a804056ca44c607026e9.

Cache bytes, exact parameter hex, source settings/producer identity, PMF và
amplitudes được kiểm tra. Cùng ensemble được dùng cho MI và Holevo.
Scientific context mới:
e598b9ed108c19336fdfa0da75c0dd4afeea4c3b0e37e185d837bb28cb302454.

## Noise và covariance theo quyết định mới

Mode này dùng đúng

$$
\xi_{\rm eff}=\xi_{\rm ch}=0.0186,\qquad
N_{\rm eff}=T_{\rm eff}\xi_{\rm ch},
$$

$$
a=1+V_A,\qquad b=1+T_{\rm eff}(V_A+\xi_{\rm ch}),
$$

$$
Z^*=2\sqrt{T_{\rm eff}}C-\sqrt{2T_{\rm eff}\xi_{\rm ch}w}.
$$

| Thành phần | Giá trị |
|---|---:|
| N_eff | 0.0029931174122637422 |
| Z_signal | 2.576423871590478 |
| Z_penalty | 0.0000783272110041651 |
| Z_star | 2.576345544379474 |

Không giữ b corrected cũ trong khi chỉ sửa Z. Ma trận mới là

$$
\Gamma=
\begin{pmatrix}
6.5&0&2.576345544379474&0\\
0&6.5&0&-2.576345544379474\\
2.576345544379474&0&1.8880547178128329&0\\
0&-2.576345544379474&0&1.8880547178128329
\end{pmatrix}.
$$

Ba mômen vẫn mô tả physical fading law cũ, nhưng mapping Gaussian này cố ý không
bảo toàn đầy đủ Bob second moment của luật đó. Full fading variance là
1 + m1(V_A + xi_ch) = 2.312923878043779, còn b mới là 1.8880547178128329.
Chênh lệch 0.42486916023094623 gồm:

- Fading variance bỏ đi: (m1 − T_eff)V_A = 0.42343717270144676.
- Channel noise đổi từ m1 xi_ch sang T_eff xi_ch theo quyết định mới.

Không sửa mn hoặc PDF để ép chênh lệch này bằng 0. Nhãn
matches_full_fading_covariance = false và validated_fading_security_lower_bound =
NOT_ESTABLISHED được lưu trong result.

## MI và Holevo được tính mới

Likelihood Gaussian hiệu dụng dùng cùng ensemble discrete 256-QAM:

$$
Y|i\sim {\rm CN}\left(\sqrt{T_{\rm eff}}\alpha_i,\,
1+\frac{T_{\rm eff}\xi_{\rm ch}}{2}\right).
$$

Complex noise variance = 1.001496558706132. MI được tính mới với
deterministic_mutual_information; không dùng MI từ corrected có N_fading và
không thay bằng Gaussian-modulation formula.

| GH order | I_AB (bit/use) |
|---|---:|
| 8 | 0.5279406103287818 |
| 16 | 0.5279406103849569 |
| 32 | 0.527940610384956 |

GH16→32 difference = 8.881784197001252e-16, nhỏ hơn tolerance 1e-8.
Test đối chiếu GH8/product với likelihood phức đầy đủ của 256 symbols pass
ở 12 decimal places. Đây là kiểm tra quadrature và factorization; không phải
bound cho sai số khi bỏ variance fading.

Holevo được tính lại bằng source C,w đã xác minh, cùng T_eff và xi_ch của MI,
target trực tiếp chi_BE(Z_star). Không tự coi Z_star là maximum trên khoảng
correlation của actual fading law. Không có numerical repair/clipping ở điểm này.

## Đầy đủ các output được yêu cầu

| Quantity | effective_channel_no_fading_noise |
|---|---:|
| T_eff | 0.16092029098192165 |
| xi_eff | 0.0186 |
| a | 6.5 |
| b | 1.8880547178128329 |
| Z_star | 2.576345544379474 |
| lambda_1 | 5.615399951552535 |
| lambda_2 | 1.0034546693653674 |
| lambda_3 | 4.201720703868558 |
| I_AB | 0.527940610384956 |
| chi_BE | 0.4429134296445705 |
| beta I_AB | 0.5015435798657082 |
| SKR = beta I_AB − chi_BE | **+0.05863015022113771** |

Covariance physicality được kiểm tra độc lập qua Gamma+iOmega, spectrum của
iOmega Gamma và entropy. Mọi lambda >= 1; không clip SKR.

## So sánh với hai mode trước

Các cột historical/corrected đọc từ artifacts đã lưu và được hash-bind.
Chỉ cột mode mới tính lại MI/Holevo trong execution này.

| Quantity | Historical | Corrected Gaussian có fading noise | Mode mới bỏ fading noise |
|---|---:|---:|---:|
| T_eff | 0.2011265222214531 | 0.16092029098192165 | 0.16092029098192165 |
| xi_eff | 0.0186 | 2.658846035092476 | 0.0186 |
| a | 6.5 | 6.5 | 6.5 |
| b | 2.109936825531311 | 2.312923878043779 | 1.8880547178128329 |
| Z_star | 2.8802711769958247 | 2.575487382363995 | 2.576345544379474 |
| lambda_1 | 5.394530138863511 | 5.668978112682573 | 5.615399951552535 |
| lambda_2 | 1.0044669643948223 | 1.4819019907263522 | 1.0034546693653674 |
| lambda_3 | 3.832433898680368 | 4.497800281293246 | 4.201720703868558 |
| I_AB | 0.6341892631163653 | 0.4484184676941574 | 0.527940610384956 |
| chi_BE | 0.5244988060866094 | 1.2195896239728028 | 0.4429134296445705 |
| SKR (bit/use) | +0.07798099387393764 | −0.7935920796633533 | **+0.05863015022113771** |

Corrected actual fading-mixture MI cũ là 0.4652637991973034, MCSE =
0.019468676410223464, K = −0.7775890147353646; sampling precision chưa đạt.
Đây là một likelihood khác, không được dùng để thay thế MI Gaussian mới.
xi_eff corrected ở bảng là effective covariance noise; mixture conditional
likelihood cũ dùng physical xi_ch = 0.0186 và random eta.

Mode mới thấp hơn historical 0.01935084365279993 bit/use, vì vẫn giữ T_eff
từ PDF physical corrected, không khôi phục historical channel moments.
So với corrected Gaussian surrogate, K tăng 0.852222229884491 bit/use.
Các phép so này là so sánh diagnostic model, không phải gain đã chứng minh
cho physical fading protocol.

## Validation, preservation và dừng

5 tests CURRENTLY_VERIFIED_PASS; 0 failure/error. Nội dung:

- PDF/mômen unchanged và T_eff = mh².
- N_eff, xi_eff, b và Eq. (20) cùng noise convention.
- Independent covariance/symplectic/entropy/SKR.
- Fresh product MI đối chiếu full 256-symbol complex likelihood.
- Mapping không mutate input; nonideal/unnormalized input fail closed.

Startup snapshot bảo vệ 3217 file source/config/test/doc/scientific artifact cũ,
không tính bytecode và năm state files được phép cập nhật. Tất cả hashes khớp
sau execution; protected_changes = []. Source C,w, checkpoint và mọi result cũ
không đổi. Marker/result mới chỉ có một execution/candidate.

Frozen spec hash vẫn
df83ea63af3b475ecca03a44d22d3240ab24d695ff0ebef31f0cd6747db78c15;
historical expected-hash discrepancy là blocker có trước, không bị sửa.
Lifecycle vẫn NOT_READY_FOR_PUBLICATION_SCALE_RUNS.

Artifacts:
[reference_result.json](../results/effective_channel_no_fading_noise/reference_20261013/reference_result.json),
[validation_receipt.json](../results/effective_channel_no_fading_noise/reference_20261013/validation_receipt.json),
[test_output.txt](../results/effective_channel_no_fading_noise/reference_20261013/test_output.txt).
Các producer/input/config/source hashes và comparison rows nằm trong JSON.

Không AP/source recomputation, AO, 182-candidate search, distance sweep,
Objective C restart, Monte Carlo mới, training/heldout/final-test/publication,
commit hoặc push. Dừng sau one-point diagnostic và report.
