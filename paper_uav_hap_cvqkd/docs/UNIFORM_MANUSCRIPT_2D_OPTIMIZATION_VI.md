# Tối ưu số Uniform 256-QAM theo phép tính manuscript 2D

Ngày 2026-10-19; yêu cầu 6b0f6694. Kết quả: **không có SKR Uniform dương trong 36 điểm exact đã kiểm tra**.
Điểm tốt nhất đã tính trực tiếp: `VA=0.047500000000000001`, `K=-4.8506709947974743e-05` bits/use.
Nhãn kết luận: `BEST_CURRENT_EXACT_TESTED_CANDIDATE_ONLY`; không có chứng chỉ cực đại toàn cục trên mọi VA>0.

## Quy ước cố định và nguồn

Giữ đúng kênh MB recheck: HAP20km/UAV1km, zenith30deg, L21.9393102292km
(làm tròn), lambda1550nm, divergence full-angle233urad, Dr.08m, jitter15.61urad,
sigma_o1.5mrad/FOV6.25mrad, tau_zen.92, wind21m/s, sigma_h1m, rho0, F0infinity,
HV Cn2ground1e-14. Channel được tính đúng một lần, đối chiếu MB ở độ chính xác
cao trước khi tối ưu; số đầy đủ lưu channel_once.json. mean_eta=0.0002640339370277643,
eta_f=0.00024354548877265959. Kênh không phụ thuộc VA; cùng channel hash cho mọi ứng viên.

Theo yêu cầu mới, thống nhất `VA=2*nbar`, `p=1/256`, `nu=0`,
`Delta=sqrt(3*VA/255)`; kiểm tra tổng xác suất và năng lượng mỗi ensemble.
Ghi nhận PDF in VA=nbar/2 là mâu thuẫn đã được user chỉ định cách xử lý cho
so sánh này. Không dùng C,w của MB cho Uniform. Kiểm tra identity binary64,
ensemble hash, source implementation/settings và support256 cho từng source.
Tái sử dụng 30 nguồn Uniform cũ đã xác thực; nguồn mới lưu riêng.

Nguồn mới dùng full-support C4 coherent Gram của repository,
không có finite Fock cutoff và không threshold bỏ support. AP dùng ladder
1050/1250/1450, hai bậc cuối phải có đủ256 mode và đáp ứng tiêu chuẩn hội tụ
đã có. Source receipt lưu toàn bộ rows hội tụ và gate. gmpy2 được cài riêng
trong thư mục tạm và chỉ đưa vào PYTHONPATH của source child để tăng tốc
mpmath; không sửa .venv, code nguồn hay cache cũ. Phép giải hệ chéo trong
worker được thay riêng bằng phép chia từng hàng tương đương đại số; không
đổi eigensolver, công thức, support hoặc precision. Kiểm tra LU/chia hàng
50/1050dps và đối chiếu source đầy đủ được lưu riêng. Version/backend được ghi
trong từng source receipt. PDF không chỉ định Nmax; không tuyên bố đã kiểm
chứng một cutoff hữu hạn không được nêu.

## MI, Holevo và thuật toán tìm kiếm

Giữ Gaussian2D chuẩn hóa `1/(2*pi*sigma_zeta^2)`, mean `2*sqrt(eta_f)*alpha`,
variance **mỗi component** `sigma_zeta^2=1+eta_f*xi_f`. Log-sum-exp dùng cho
mixture. PMF Uniform Cartesian cho phép factor chính xác mixture thành hai
marginal; code vẫn tổng quadrature tensor trên cả hai component của log-ratio2D.
Không thay bằng MI homodyne1D, không đặt1/2 và không dùng correction heterodyne.
Đối chiếu riêng với chính mi_gh tensor256-symbol của MB ở GH16/32/64 tại điểm
tốt nhất, residual lưu same_MB_MI_kernel_check.csv.

Noise `N=(mean_eta-eta_f)*VA+.0186*mean_eta`; R1/xi_det0, beta.95.
Không cộng pure loss hay detector noise vào xi_n. Holevo dùng nguyên
`Z=2*sqrt(eta_f)*C-sqrt(2*N*w)`, `V=1+VA`, `W=1+eta_f*VA+N` và
**nu3=sqrt(V*(V-Z^2/W))**. Entropy chỉ tính khi eigenvalue hợp lệ;
raw K=.95I-chi, không clip.

Khảo sát toàn bộ30 nguồn cũ (0.02 đến5), thêm coarse points8/12 và dùng
fine grid .025,.05,.075,.1 vì vùng tốt nhất nằm dưới .1. Từ bracket cũ
.04/.05/.06, tính thêm exact .0475/.0525 với khoảng cách nhỏ nhất .0025.
Grid .5 đều từ .1 đến12 trong task là gợi ý, không bắt buộc; coarse grid
được thích nghi để tái sử dụng tất cả nguồn cũ và tập trung nguồn mới gần
vùng hứa hẹn. Không nội suy source/MI/Holevo/SKR. Toàn bộ lời gọi và
grid-refinement receipt được lưu; không gọi đây là optimizer hội tụ toàn cục.
Miền đã khảo sát
`[0.02,12.0]`; ngoài miền này chưa có chứng chỉ.

## Bảng toàn bộ ứng viên

| VA | C | w | I_AB 2D | beta I_AB | chi_BE | K raw |
|---:|---:|---:|---:|---:|---:|---:|
| 0.02 | 0.100471991680169 | 0.000536536244896915 | 7.02718287280071e-06 | 6.67582372916068e-06 | 5.54296204055962e-05 | -4.87537966764355e-05 |
| 0.025 | 0.112462723679362 | 0.000668745931079513 | 8.78397234293781e-06 | 8.34477372579091e-06 | 5.70145893928696e-05 | -4.86698156670787e-05 |
| 0.04 | 0.142753888786397 | 0.00106091861774206 | 1.40543257585551e-05 | 1.33516094706273e-05 | 6.18760541891237e-05 | -4.85244447184964e-05 |
| 0.0475 | 0.155833513862087 | 0.00125455869808086 | 1.66894940315785e-05 | 1.58550193299996e-05 | 6.43617292779744e-05 | -4.85067099479747e-05 |
| 0.05 | 0.159974429207972 | 0.00131875093520797 | 1.75678822061785e-05 | 1.66894880958696e-05 | 6.51978685334735e-05 | -4.8508380437604e-05 |
| 0.0525 | 0.164019870254256 | 0.00138276788991311 | 1.8446269756237e-05 | 1.75239562684251e-05 | 6.60376773412881e-05 | -4.85137210728629e-05 |
| 0.06 | 0.175648561623243 | 0.00157377855093877 | 2.10814286572908e-05 | 2.00273572244263e-05 | 6.8578456832493e-05 | -4.85510996080667e-05 |
| 0.075 | 0.197059267642505 | 0.00195122014895017 | 2.63517295905015e-05 | 2.50341431109765e-05 | 7.37507269124203e-05 | -4.87165838014438e-05 |
| 0.08 | 0.203754979284052 | 0.00207570925639118 | 2.81084915696791e-05 | 2.67030669911952e-05 | 7.55001182315766e-05 | -4.87970512403814e-05 |
| 0.1 | 0.228844729573444 | 0.00256726720873028 | 3.51355144963014e-05 | 3.33787387714864e-05 | 8.26143097014677e-05 | -4.92355709299814e-05 |
| 0.11 | 0.240558069854732 | 0.00280932061743215 | 3.86490109646831e-05 | 3.6716560416449e-05 | 8.62368708685256e-05 | -4.95203104520766e-05 |
| 0.12 | 0.25182149807467 | 0.00304897361509742 | 4.21624974369179e-05 | 4.0054372565072e-05 | 8.99000065170512e-05 | -4.98456339519792e-05 |
| 0.13 | 0.262692933541304 | 0.00328628608103336 | 4.56759739127923e-05 | 4.33921752171527e-05 | 9.36016683869419e-05 | -5.02094931697893e-05 |
| 0.14 | 0.273219209736273 | 0.00352131587165093 | 4.91894403925991e-05 | 4.67299683729692e-05 | 9.73399764294503e-05 | -5.06100080564811e-05 |
| 0.15 | 0.283438818610477 | 0.00375411886522138 | 5.27028968759844e-05 | 5.00677520321851e-05 | 0.000101113196809763 | -5.10454447775778e-05 |
| 0.18 | 0.312554369307042 | 0.00443969710748261 | 6.32432063496561e-05 | 6.00810460321733e-05 | 0.000112626832273971 | -5.25457862417979e-05 |
| 0.2 | 0.330903815752694 | 0.00488655473569616 | 7.02700293523357e-05 | 6.67565278847189e-05 | 0.000120450518034158 | -5.36939901494391e-05 |
| 0.3 | 0.414005874661513 | 0.00701140261764722 | 0.000105403544621386 | 0.000100133367390316 | 0.00016102059239398 | -6.08872250036636e-05 |
| 0.5 | 0.556400739055678 | 0.0108121168962504 | 0.000175667576610003 | 0.000166884197779503 | 0.000247151294607847 | -8.02670968283437e-05 |
| 0.6 | 0.621190379339373 | 0.0125269300162773 | 0.000210798093435742 | 0.000200258188763955 | 0.000291778841987376 | -9.15206532234208e-05 |
| 0.7 | 0.683366367105727 | 0.0141317761954571 | 0.000245927610886707 | 0.000233631230342371 | 0.000337034526109597 | -0.000103403295767226 |
| 0.75 | 0.713691300909947 | 0.0148946165896451 | 0.000263491994863198 | 0.000250317395120038 | 0.000359825966905589 | -0.000109508571785551 |
| 0.8 | 0.743592233293653 | 0.0156316466576354 | 0.000281056129015609 | 0.000267003322564829 | 0.000382694002562939 | -0.000115690679998111 |
| 0.9 | 0.802315161606083 | 0.0170295254258827 | 0.000316183647875956 | 0.000300374465482158 | 0.000428576522433913 | -0.000128202056951755 |
| 1 | 0.859851106546499 | 0.0183276104749635 | 0.000351310167520175 | 0.000333744659144166 | 0.000474535040133993 | -0.000140790380989828 |
| 1.075 | 0.902365633435172 | 0.0192369861680698 | 0.000377654401550025 | 0.000358771681472524 | 0.000508981085326458 | -0.000150209403853934 |
| 1.25 | 0.99988008268491 | 0.0211516425071069 | 0.000439122095410248 | 0.000417165990639735 | 0.000589037619666181 | -0.000171871629026446 |
| 1.5 | 1.13614338732452 | 0.0234149401836767 | 0.000526927779361707 | 0.000500581390393622 | 0.000702047013665328 | -0.000201465623271706 |
| 2 | 1.4019995788968 | 0.0265433382287139 | 0.000702520418762031 | 0.000667394397823929 | 0.000921390163367901 | -0.000253995765543972 |
| 2.05 | 1.42825353575676 | 0.0267721057447194 | 0.000720078309472915 | 0.00068407439399927 | 0.000942796454641214 | -0.000258722060641944 |
| 3 | 1.92061533387556 | 0.0292407986575685 | 0.00105363080673643 | 0.00100094926639961 | 0.00133289183419375 | -0.000331942567794139 |
| 3.025 | 1.93345502118266 | 0.0292712454692487 | 0.00106240728739577 | 0.00100928692302598 | 0.00134278008111527 | -0.00033349315808929 |
| 4 | 2.43153408140466 | 0.0297439449341525 | 0.00140464138440533 | 0.00133440931518506 | 0.00171693908709742 | -0.000382529771912366 |
| 5 | 2.93889491693631 | 0.0294536377992886 | 0.00175555220468102 | 0.00166777459444697 | 0.00208298399059325 | -0.000415209396146283 |
| 8 | 4.45175251925098 | 0.0275822345546513 | 0.00280768664953961 | 0.00266730231706263 | 0.00312055939835323 | -0.0004532570812906 |
| 12 | 6.46047679033918 | 0.0253199116340987 | 0.00420913917396524 | 0.00399868221526698 | 0.00443232614033276 | -0.000433643925065783 |

## Điểm tốt nhất đã kiểm tra

`VA=0.047500000000000001`, `nu=0`.

| Đại lượng | Giá trị |
|---|---:|
| `C` | 0.15583351386208738 |
| `w` | 0.0012545586980808594 |
| `eta_f` | 0.000243545488772659583047535 |
| `xi_f` | 0.0241607124422107260181079 |
| `W` | 1.00001745264323753521926 |
| `Z` | 0.00474235003909576512563438 |
| `nu_1` | 1.04748901596442398294329 |
| `nu_2` | 1.00000646860766151816256 |
| `nu_3` | 1.04748875519394795399833 |
| `I_AB` | 0.000016689494031578547 |
| `beta_I_AB` | 0.00001585501932999961965 |
| `chi_BE` | 0.0000643617292779743641236098 |
| `K` | -0.0000485067099479747444736098 |

## So sánh với MB cố định

| Scheme | nu_raw | VA | I_AB 2D | chi_BE | K raw |
|---|---:|---:|---:|---:|---:|
| Uniform_best_exact_tested | 0.0 | 0.0475 | 1.66894940315785e-05 | 6.43617292779744e-05 | -4.85067099479747e-05 |
| MB_fixed_reference | 0.165 | 5.475 | 0.001922199913607 | 0.0017294319205515 | 9.66579973751463e-05 |

`Delta K=K_MB-K_Uniform=0.00014516470732312103` bits/use. Không tính phần trăm vì Uniform raw SKR không dương.
MB là điểm tham chiếu cố định, không tối ưu hoặc tạo source MB.

## Kiểm tra và hiện vật

Tất cả ứng viên có GH16/32/64; max difference
`3.78681e-16` bits/use. Điểm tốt nhất
được kiểm tra thêm entropy80/110dps. Xác thực PMF, normalization, source identity,
channel equality, eigenvalue, noise/SKR identity, không nội suy hoặc nhầm
source MB được lưu trong summary.json. Chỉ số PASS là kiểm tra số học trong
phạm vi này, không phải security proof.

Kết quả lưu results/uniform_manuscript_2d_optimization_20261019/:
all_candidates.csv, MI_convergence.csv, source/convergence receipts,
candidate_records, summary.json, search_protocol.json, local_optimizer.json,
Uniform_MB_comparison.csv, channel_once.json, integrity receipt và bốn hình
PNG350dpi/vectorPDF (ba hình được yêu cầu và một hình phóng vùng refine).
Đường nối hình chỉ để dẫn mắt; tất cả điểm là đánh giá exact, có giữ raw âm
và đường K=0. Không suy ra sign/cực đại giữa các điểm từ đường vẽ.

Production evaluator, công thức khoa học đang dùng, optical config, old source
caches/MB artifacts/frozen spec không đổi. Frozen historical hash discrepancy
được giữ nguyên. Không baseline/threshold certification, training/test-data/
final-test/held-out/publication evaluation, ObjectiveC restart, external edit,
commit hoặc push. Giữ UNVALIDATED_SECURITY_MODEL và NOT_READY_FOR_PUBLICATION_SCALE_RUNS.

**Trả lời:** Trong các ứng viên đã tính trực tiếp tại L21.9393102292km,
Uniform không đạt SKR dương theo manuscript-style2D với noise đã sửa;
best-tested VA=0.047500000000000001, raw K=-4.8506709947974743e-05,
chênh so với MB=0.00014516470732312103 bits/use. Chưa chứng minh kết luận cho mọi VA>0;
tổ hợp MI2D/Holevo homodyne vẫn là phép so sánh số được yêu cầu.

## X?c nh?n ho?n t?t v? h?nh

Ki?m tra l?u trong `validation_receipt.json`: 36 ?ng vi?n ??u qua ??i chi?u
source/ensemble, covariance positivity, uncertainty matrix v? spectrum t?nh
tr?c ti?p. 188 self-check trong producer v? 6 ki?m tra ??c l?p ban ??u ??t.
C? 6 source m?i ph?c v? t?m ki?m; m?t source VA=.05 t?nh l?i ri?ng ?? ki?m
tra ph?p gi?i h? ch?o kh?p bitwise v?i cache c?. T?ng c?ng 7 payload m?i,
kh?ng ph?i 7 ?ng vi?n m?i. C?c ngu?n ??c l?p ? c? coarse v? refinement
???c chu?n b? v?i concurrency2; objective ???c t?nh tu?n t?.

Ba h?nh ch?nh ?? xem tr?c quan; c? b?n h?nh ??u qua ki?m tra PNG>=300dpi
v? vector PDF kh?ng c? raster image. ???ng zero hi?n th? tr?n c?c h?nh ch?nh.
Mi?n kh?o s?t l? t?p 36 ?i?m trong [0.02,12]; kh?ng ph?i ch?ng ch? cho to?n
b? kho?ng li?n t?c ?? ho?c cho m?i VA>0. Kho source m?i ???c l?u ri?ng v?i kho source c?. Experimental FLINT trial kh?ng c? k?t qu? ???c ch?p nh?n,
kh?ng g?p ph?n v?o b?t k? ?ng vi?n n?o; to?n b? s? b?o c?o d?ng C4/diagonal
route ?? ??i chi?u source ??y ??.

1. Uniform SKR: [PNG](../results/uniform_manuscript_2d_optimization_20261019/uniform_SKR_vs_VA.png), [PDF vector](../results/uniform_manuscript_2d_optimization_20261019/uniform_SKR_vs_VA.pdf).
2. MI, beta MI v? Holevo: [PNG](../results/uniform_manuscript_2d_optimization_20261019/uniform_MI_Holevo_vs_VA.png), [PDF vector](../results/uniform_manuscript_2d_optimization_20261019/uniform_MI_Holevo_vs_VA.pdf).
3. Uniform v? MB c? ??nh: [PNG](../results/uniform_manuscript_2d_optimization_20261019/uniform_vs_fixed_MB.png), [PDF vector](../results/uniform_manuscript_2d_optimization_20261019/uniform_vs_fixed_MB.pdf).

C?ch x?c minh/replay ???c ghi t?i `results/uniform_manuscript_2d_optimization_20261019/RUN.md`;
kh?ng c?n ch?y l?i source AP ?? ??c ho?c x?c minh k?t qu? ?? l?u.
