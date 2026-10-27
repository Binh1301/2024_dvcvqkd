# Tái sử dụng exact source moments cho chẩn đoán chín góc

## Phạm vi và quyền sử dụng

Yêu cầu người dùng `3aadec7f` cho phép tái sử dụng payload exact lịch sử tương
thích trong một phân tích **DIAGNOSTIC-ONLY**, kể cả 73 nguồn hiện mang nhãn
`INSUFFICIENT_EVIDENCE`. Quyền này không đổi phân loại convergence evidence,
standard strict hoặc lifecycle. Bản yêu cầu nguyên văn được giữ trong
`authorization.txt`; `protocol.json` khóa scope và hashes.

Không tạo progress wrapper, checkpoint/resume cho source generation, source job,
hay bất kỳ C,w mới nào. Không chạy optimizer liên tục hoặc sweep 61 góc.

## Nguồn đã hợp nhất

Đọc 238 file `exact_source_cache/*.json` và xác minh:

1. Schema và cache key nguyên gốc, source settings, implementation hashes.
2. Canonicalization chỉ áp dụng LF/CRLF của implementation theo helper đã được
   chấp nhận; không chuẩn hóa code, làm tròn VA/nu hoặc đổi payload.
3. Tái dựng **ensemble**, không tái tính C,w: M=256, square 16×16 QAM, Uniform
   hoặc MB PMF đúng convention, exact VA/nu hex, `nu_repo=42.5*nu_raw`.
4. Ensemble hash, PMF/energy/centering/C4, `VA=2*nbar` và `X_A=2Re(alpha)`.
5. C,w hữu hạn, không âm, bằng chính giá trị lưu trong payload; giữ C/w hex để
   kiểm tra round-trip binary64.

Kết quả: **235 canonical source identities**, 38 Uniform và 197 MB, từ 238
payloads. Ba duplicate aliases được gộp sau khi canonical identity và C,w hex
khớp: Uniform VA=0.05; MB VA=2/nu_raw=0.20; MB VA=2/nu_raw=0.22. Các đường dẫn
và hashes nguyên gốc vẫn được giữ; không ghi cache mới đè cache cũ.

`exact_source_inventory.csv` là inventory hợp nhất. `source_payload_provenance.json`
giữ proof của từng source/alias. Pool pilot được giữ riêng. Để tận dụng toàn bộ
nguồn cũ trong miền đã duyệt, `available_catalog_protocol.json` khóa thêm một
chẩn đoán catalog khả dụng 212 nguồn; 23 nguồn ngoài VA/nu domain chỉ được ghi
inventory. Tổng inventory 235 khác catalog zenith cũ 233 vì phạm vi lịch sử được
mở rộng; đây không phải một lần tạo thêm hai source.

## Catalog và numerical provenance

Đối chiếu **245 file catalog/bảng nguồn** và **59.439 hàng gắn được với source**;
không thấy conflict C,w/VA/nu. Có catalog MB-shaping cũ
`results/exact_source_moments_catalog_20261012/all_211_exact_source_moments.csv`
và catalog zenith 233 nguồn, cùng catalog JSON Uniform mới hơn.
`historical_catalog_index.json` giữ paths/hashes/row counts;
`catalog_cross_checks.csv` giữ kết quả đối chiếu. Nhiều hàng là dữ liệu dẫn xuất
lặp lại; số hàng này không phải số source độc lập hay evidence hội tụ mới.

Tương thích toán học của payload và evidence về numerical convergence là hai
thuộc tính khác nhau. Bằng chứng nguồn của pool 81 giữ đúng taxonomy cũ:
6 VERIFIED_EXACT, 1 VERIFIED_BY_ALTERNATIVE_EVIDENCE, 74 INSUFFICIENT_EVIDENCE,
0 INVALID. Trong nhóm 74, có 73 payload dùng được cho diagnostic và một Uniform
chưa có payload. Không nâng hạng nguồn vì tính SKR thành công.

## Quy tắc đánh giá

Pool yêu cầu có 81 nguồn. Pool khả dụng chứa **80 nguồn: 33 Uniform + 47 MB**,
giống nhau ở cả chín góc 0,5,10,15,20,30,40,50,60°. Mỗi nguồn dùng nguyên C,w ở
cả chín góc. `Cw_reused=True` và `source_Cw_recomputed=False` được ghi ở từng hàng.

Catalog chẩn đoán mở rộng có **212 nguồn: 33 Uniform + 179 MB**, cùng pool tại
mọi góc, trong miền VA=[0.05,10], nu_raw=[0,0.40] giữ nguyên. Tái dùng 720 kết quả
pilot và bổ sung 1.188 cặp cho 132 nguồn còn lại; chín channel contexts được dùng
chung. Không coi 132 nguồn bổ sung là thay thế Uniform còn thiếu.

Mỗi góc tính một channel context bằng code đã được phê duyệt; giữ moments [0,1],
atom tại 0, deficit metadata và noise conventions. Mỗi source–angle tính lại
eta_f, xi_f, direct Eq. (14), discrete homodyne MI, Eq. (13) Holevo và signed raw K.
Eq. (14)/Eq. (13) dùng **chính function objects** của evaluator canonical; không
có đối số Z, Z search, endpoint, projection, eigenvalue repair hoặc interpolation.

`diagnostic_model.evaluate` giữ nguyên các biểu thức và kiểm tra số 80/110 digits,
GH64/128; thay gate convergence strict bằng gate tương thích diagnostic được
người dùng cho phép. Source classification không thay đổi. Strict evaluator cũ
vẫn từ chối các nguồn insufficient. Regression trên hai nguồn đã verified cho
kết quả eta_f/xi_f/Z/MI/Holevo/K khớp chính xác với strict evaluator.

`diagnostic_results.csv` giữ 1.908 candidate records của catalog mở rộng.
`pilot_candidate_diagnostic_results.csv` giữ nguyên 720 hàng của pool pilot.
Hai view chính tách biệt:

- `strict_source_evidence_results.csv`: 22 source đủ evidence (7 Uniform,
  15 MB), 198 cặp. Đây vẫn là chẩn đoán kênh; không phải strict Phase B hoàn tất.
- `incomplete_source_evidence_results.csv`: 190 source, 1.710 cặp, gồm Fixed MB;
  giữ nhãn source evidence incomplete.
- Các file `pilot_strict_source_evidence_results.csv` và
  `pilot_incomplete_source_evidence_results.csv` giữ hai nhóm 63/657 hàng của
  pool pilot ban đầu; không đổi evidence class của 73 nguồn đó.

`diagnostic_selected_schemes.csv` chọn best-tested trong 33 Uniform, một Fixed MB,
và toàn bộ 212 nguồn cho MB mở rộng có chứa Uniform. File
`pilot_diagnostic_selected_schemes.csv` giữ selection từ 80 nguồn riêng. Mọi selection mang nhãn
**HISTORICAL_EXACT_RESTRICTED_CATALOG_DIAGNOSTIC**. Không tuyên bố full-catalog
optimum, optimum liên tục hay shaping gain cùng VA khi thiếu nguồn đối chiếu.

Nếu phép tính ngoài miền hoặc chưa qua kiểm tra số, rate để trống với lý do;
không biến lỗi thành zero. Giá trị K âm được giữ nguyên. Independent adaptive MI
và covariance spectrum kiểm tra các selection; chi tiết nằm ở receipt riêng.
Không tính lại source C,w để làm các kiểm chứng đó.

## Kết luận về strict readiness

Uniform bị thiếu không được thay bằng VA làm tròn, nguồn lân cận hoặc C,w của
Fixed MB. Bảy nguồn đủ evidence trong pool pilot đều là Uniform; catalog mở rộng
có thêm 15 MB đủ evidence, nhưng Fixed MB vẫn thiếu receipt. 73 evidence gaps và một
payload thiếu vẫn ngăn strict Phase B. Chi tiết số cuối: `diagnostic_summary.json`
và `validation_report_vi.md`. **Số phép tính C,w mới: 0.**
