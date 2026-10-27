# Phase E2 — kiểm tra phổ nguồn thắng

**Kết luận hội tụ C,w: INCONCLUSIVE.** Hoàn tất phần chẩn đoán, kiểm thử
checkpoint/resume và chuẩn bị lần chạy có giới hạn. Chưa chạy lại nguồn thắng
ở 260 chữ số hoặc cao hơn. Giữ **DIAGNOSTIC_ONLY** và
**PHASE_B_STRICT_READY = FALSE**.

## Nguồn và công thức giữ nguyên

Nguồn MB thắng: nu_raw=0.30, nu_repo=12.75, VA=1.358333319784304,
VA_hex=0x1.5bbbbb818a6b0p+0, M=256. Ensemble hash:
b083ac8400f7e1068ec045f9882bd256cbbfdec50b64d66d8b7f2d84c05eb214.
Cache gốc vẫn giữ C=1.067911050328646, w=5.700303183579203e-10 và phân loại
**INSUFFICIENT_EVIDENCE**. Xem input_provenance.json cho payload/array hashes.
Không nội suy, chuẩn hóa lại PMF, đổi VA=2*nbar, đổi hệ số nu, hay sửa ensemble.

Giữ nguyên C=Tr(sqrt(tau) a sqrt(tau) a†), a_tau=sqrt(tau) a tau_MP^(-1/2)
và w là tổng phương sai có trọng số. Eq. (14) vẫn tính trực tiếp
Z=2sqrt(eta_f) C-sqrt(2 eta_f xi_f w). Không sửa MI, Holevo, support kênh,
manuscript, frozen spec hoặc production code.

## Có bao nhiêu mode đã được kiểm tra?

| Bằng chứng | Số mode | Diễn giải |
|---|---:|---|
| Fock NF256, 260 chữ số đã lưu | 231/256 | Trên floor 1e-240; chưa là chứng chỉ toàn support |
| Gram 180 chữ số đã lưu | 186/256 | Trên floor 1e-160 |
| Đối chiếu eigenvalue Fock–Gram | 186 | Sai khác tương đối lớn nhất 2.696633e-27 |
| Chưa phân giải ở Fock tốt nhất | 25 | Không được coi là eigenvalue bằng 0 |
| Nguồn có chứng chỉ hội tụ C,w toàn support | 0 | Chưa có reference đầy đủ hoặc chặn phần dư w |

Tất cả 256 mode **dương về mặt toán học**: xác suất dương, các coherent state
phân biệt, và phép chiếu Vandermonde 256 hàng khả nghịch. E2 bổ sung chứng
minh định lượng bằng số học Fraction chính xác và Decimal làm tròn có hướng:

| Sector photon Fock r | Sector Gram s=(-r) mod 4 | Rank Fock260 | Khoảng eigenvalue Fock **đã giữ** | Condition **đã giữ** | Cận dưới chứng nhận cho lambda_min Gram đầy đủ |
|---:|---:|---:|---|---:|---:|
| 0 | 0 | 58 | [1.2508e-234, 0.5955335] | 4.7612e233 | 1e-302 |
| 1 | 3 | 58 | [1.1137e-236, 0.2408734] | 2.1628e235 | 1e-305 |
| 2 | 2 | 58 | [9.2924e-239, 0.0974250] | 1.0484e237 | 1e-308 |
| 3 | 1 | 57 | [1.3078e-232, 0.0394056] | 3.0131e230 | 1e-312 |

Các cận dưới không phải trị eigenvalue đo được. Condition của toàn phổ vẫn
chưa được đo; cận bảo thủ toàn phổ <2e312. Chứng nhận tính dương không chứng
nhận độ chính xác C,w. Chứng minh và endpoint làm tròn có hướng nằm trong
unresolved_spectrum_error_analysis.md và spectral_lower_bound_certificate.json.

## Nguyên nhân và precision cần thiết

Giới hạn chính là phổ có condition rất lớn, kết hợp floor và precision hữu hạn.
Nâng Fock cutoff không tự khắc phục độ chính xác của eigenvalue cực nhỏ. NF64,
96,128 còn giới hạn số chiều; NF256 đã có rank toán học 256 nhưng precision260
chưa phân giải đủ. Residual tổng rất nhỏ không bảo đảm sai số tương đối của
mode nhỏ hơn residual. Không thấy gần suy biến trong các mode đã giữ ở cùng
sector (relative gap tối thiểu khoảng 0.9732); phần đuôi chưa biết.

C4 giữ đầy đủ phổ. Cần ghép đúng sector: Gram1 ↔ Fock3, Gram3 ↔ Fock1.
Kiểm tra float64 mới xác nhận phép đổi cơ sở; không dùng nó để chứng nhận mode
cực nhỏ. CSV có 32 hàng chẩn đoán theo sector/precision, kèm provenance tới
spectrum gốc. Dòng timeout không được điền eigenvalue hoặc contribution giả.

Fit log-spectrum Fock NF256 cho ước lượng mode cuối khoảng 1e-274..1e-284;
đây là ước lượng lập ngân sách, không phải chặn Gram thực. Cận dưới độc lập
>=1e-312 là cơ sở bổ sung để đề xuất **400 và 500 chữ số**, mỗi mức xây lại
độc lập. Chưa chạy các mức đó.

## Checkpoint/resume và chi phí

**14 kiểm tra focused hiện tại PASS** trong 1.5681s, gồm gián đoạn thực rồi
resume, ghi nguyên tử, bỏ qua sector xong, từ chối sai nguồn/precision/producer,
checksum và eigenpair không nhất quán. Kiểm tra công thức mới chỉ dùng nguồn
4/16 trạng thái ở 50/70 chữ số và Fock NF48; không tính C,w mới cho nguồn thắng.
Lượt phát triển đầu cũng được giữ lại; tổng hai lượt có 20 lời gọi kiểm tra
moment nguồn nhỏ, không phải tính lại catalog. Xem checkpoint_stub_tests.md.

Wrapper lưu matrix, eigenvalue, eigenvector, residual từng eigenpair,
reconstruction/orthogonality, rank, conditioning, CPU/wall và source/code hashes.
Chỉ ghi complete sau khi kiểm tra qua. Contribution C và residual-norm theo
sector cùng correction được lưu ở moments.json sau khi đủ bốn sector.
Complete chỉ có nghĩa checkpoint số hợp lệ, không phải hội tụ toàn support.

Gram260 cũ timeout 180.125s sau bốn log rank 58/57/58/58, không có eigenvector
checkpoint. Không thể tái dựng phép phân rã đó từ log. Mã mới loại bỏ full
256x256 Fourier transform và thay tích ma trận chéo bằng scaling. Runtime
400/500 chưa được đo, không hứa tốc độ từ bài test nhỏ.

## Có chặn sai số phần còn thiếu được không?

Đã có **cận phổ dương và cận tail Gram**, nhưng **chưa có chặn đủ nhỏ cho sai
số w**. Cận có hướng ||H-H_NF256||<=1.802212e-174 vẫn có thể rất lớn so với
các eigenvalue nhỏ nhất. Tau^(-1/2), eigenvector/projector errors, rounding và
truncation của annihilation operator phải được tính vào chặn C,w. Không dùng
discarded mass hoặc việc C,w khớp 50 chữ số như một chứng chỉ sai số.

Ở context primary đã lưu, zenith=0.2132318272752531°,
eta_f=0.22346465369449367, xi_f=0.0816026951989888:
dZ/dC=0.9454409631, dZ/dw=-3999.3802301. Đây chỉ là hệ số sensitivity.
Không có khoảng sai số C,w đáng tin cậy nên không xuất khoảng SKR chứng nhận;
các trường certified interval để null. Không tính mới MI/Holevo/SKR/channel.

## Bước tối thiểu còn lại

Đã chuẩn bị controlled_run_plan.json và controlled_run_authorization_plan.md:
hai mức 400/500 chữ số, bốn matrix 64x64/mức, tối đa 600s/stage,
3600s tổng và 1024MiB working set được lấy mẫu, chạy tuần tự. Lệnh chính xác,
checkpoint paths, hash, success criteria và điều kiện dừng đều có trong kế hoạch.
**Chưa được phê duyệt/thực thi trong lượt E2 này.**

Sau lần chạy được phê duyệt riêng, cần đủ 256 mode ở hai mức, residual/condition
và eigenvector/subspace checks, rồi đánh giá sai số C,w có tính đến inverse
square root. Nếu không đạt, giữ INCONCLUSIVE; không tự tăng precision hoặc
nâng evidence class. Strict Phase B còn các yêu cầu evidence của pool và nguồn
Uniform thiếu từ trước; xác minh một winner không tự giải quyết các yêu cầu đó.

10,166 tệp lịch sử được bảo vệ, gồm toàn bộ gói Phase E. Không sửa cache,
production, manuscript hoặc frozen spec; SHA bản PDF chuẩn vẫn là
f970cd6d810874c8d16fb2ba18aebbe322c27f4fa045387345422201d36fc27b.
Sai khác hash frozen spec lịch sử vẫn được ghi nhận theo binding hiện có,
không ghi đè hoặc bỏ kiểm tra. Không đổi security functional, baseline,
threshold, trạng thái training/test/publication hay Objective C USER_STOPPED.

**INCONCLUSIVE**
