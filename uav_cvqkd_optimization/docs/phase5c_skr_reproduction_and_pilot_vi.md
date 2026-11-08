# Phase5C — tái lập SKR và pilot channel noise .0136

**Đã tạo kết quả số thực bằng producer hiện có.** Reproduction .0186 PASS
trước khi chạy target .0136. Có2120 fresh evaluator calls tại5 positions,
212 candidates/position/noise; không full regeneration hay paper-mode.

Artifact chính:
[summary.json](../results/phase5c_skr_noise_pilot_20261107/summary.json),
[input manifest](../results/phase5c_skr_noise_pilot_20261107/input_manifest.json),
[output manifest](../results/phase5c_skr_noise_pilot_20261107/output_manifest.json),
[CSV so sánh đầy đủ MB/Uniform](phase5c_validation/pilot_comparison.csv),
[validation bổ sung](phase5c_validation/pilot_validation_final.json).

## 1. Provenance và cấu hình đã cô lập

Native optical inputs khớp author optimized setup: aperture.30m, full-angle
divergence35µrad, pointing jitter1.561µrad, UAV position SD.10m. Detector excess
noise giữ.005SNU. Historical protocol/authorization/source và650 saved winners
xác nhận xi_ch=.0186, không phải “total đã gồm detector”. Target đã được tác
giả xác nhận **xi_ch=.0136**. Mỗi trial/checkpoint ghi active noise và hash;
không sửa metadata để hai cấu hình khớp nhau.

Giữ `VA=Vmod=2*nbar`, X_A=2Re(alpha), bits/use, reverse asymptotic và real1D
homodyne Gaussian-effective convention, beta.95; law [0,1] retained, không
renormalize. Catalog212 source giữ ordered identities/payload hashes/C,w:
179MB và33Uniform, chọn max raw signed K riêng từng family; không optimizer
liên tục hoặc source generation. Z/w và MB-QAM/Holevo source không đổi.

Native validator của `channel_context` hard-code noise.0186. Wrapper không
sửa/bypass validator: tạo **physical contexts mới theo original validated
protocol**, rồi đưa **active effective-noise protocol riêng** vào nguyên hàm
diagnostic `evaluate(source,context,protocol)`. Hàm này tính N từ m1,mh,M0 và
noise scalar mới. Những moment vật lý này không phụ thuộc xi_ch; context đầy
đủ giữa hai stages được kiểm identical. Target không giả rằng experimental
spec lịch sử xi_ch=.0186 đã phê duyệt.0136; quyền target là task Phase5C mới.

## 2. Reproduction có đạt không, kiểm những điểm nào

Đạt. Toàn bộ **1060 candidate rows** ở.0186 khớp dữ liệu lịch sử cho T_f,
xi_f,I_AB,chi_BE,K_raw với **max deviation=0 binary64**; winner/source identity
MB vàUniform giống hệt. Tolerance chốt trước là atol2e-10,rtol0, không nới
sau xem kết quả. Cả5 point checks phải PASS mới mở target stage.

1480m là node có sẵn trên grid40m; không đưa1500m off-grid vào pilot hoặc nội
suy để so với lookup. Hai điểm high/low bổ sung được chọn deterministically
từ ranking lookup, loại radius groups đã chọn. Đây là diagnostic selection,
không phải held-out statistical sample.

| Point (x,y), m | Vai trò | K_raw .0186 | K_raw .0136 | Delta bits/use |
|---|---|---:|---:|---:|
| (1000,1000) | HAP projection/zenith | .000796087808086 | .004955337789913 | .004159249981827 |
| (1480,1000) | Trung gian | .000790484394200 | .004948237183718 | .004157752789517 |
| (0,0) | Xa nhất trong domain | .000747067033827 | .004893349597699 | .004146282563873 |
| (1000,960) | High lookup, geometry riêng | .000796048935177 | .004955288516825 | .004159239581648 |
| (40,0) | Low lookup, geometry riêng | .000749004693711 | .004895794346112 | .004146789652401 |

Domain2000×2000m của lookup dùng projection(1000,1000)m và delta_h19km;
góc xa nhất chỉ khoảng4.2568°, L≈19.05256km. Không nhầm domain này với
zenith sweep tới30.2726°/22km hoặc reference beam21.94km của Phase5B.

## 3. Channel/MI/Holevo và MB selection thay đổi thế nào

MB winner ở cả5 points và cả2 noises đều giữ **VA=1.358333319784304,
nu_raw=.3** và cùng ensemble hash. Target SKR tăng tại5 điểm đã tính; không
suy rộng gain ra mọi điểm chưa chạy hoặc nghiệm ngoài finite catalog.

Ví dụ tại projection:

| Quantity | .0186 | .0136 |
|---|---:|---:|
| T_f | .22346671313982036 | .22346671313982036 |
| xi_f | .08160274506950238 | .07645521414890293 |
| I_AB (bits/use) | .18820419088097678 | .18839151917224706 |
| chi_BE (bits/use) | .17799789352884182 | .17401660542372194 |
| Raw signed K (bits/use) | .0007960878080861267 | .00495533778991275 |

Không có thay đổi T_f vì geometry/physical moments không đổi. xi_f giảm theo
N=(m1-mh²)*VA+xi_ch*m1+xi_det*M0. Các con số MI/Holevo là fresh native
evaluations, không phải suy rate bằng scale/noise delta. CSV cung cấp đầy đủ
quantities cho cả5 positions và2 families; Uniform signed K vẫn âm, không clip.

## 4. Numerical diagnostics, runtime và kiểm tra độc lập

Không có native numerical exception trong2120 calls. GH64/128 MI difference
max **4.440892098500626e-16**, dưới2e-10; native80/110-digit precision guard
2e-11 vẫn chạy nguyên trạng. Noise/T/xi/K identities, ordered roster và
argmax winners của cả2120 records được kiểm lại, không gọi evaluator lần nữa.

Pilot process elapsed **38.0597s**, gồm preparation6.6377s. Reproduction:
context6.6089s + evaluator11.8480s; target: context.9496s + evaluator11.7012s.
Seed=null vì deterministic analytic/GH/native multiprecision; không có
cloud, finite-size, Monte Carlo realization hay runtime benchmark trajectory.

Hai lỗi setup trước evaluations được giữ rõ: CLI thiếu PYTHONPATH và module
ảo Torch có `__file__` nhưng không có file thực. Đã sửa source-file collection;
lần retry chưa có rate checkpoint cũ và **2120 calls đều fresh**.

[Review độc lập](phase5c_independent_review.md) xác nhận24 output seals,552
input hash entries,59 producer entries, all candidates/scalars và historical
comparisons. Review tìm2 lỗi wrapper: resume thiếu stage/noise/roster checks và
historical comparison CSVs chưa bind original seal. Đã sửa bằng regression
RED→GREEN; kiểm lại toàn bộ actual artifacts cho thấy dữ liệu fresh hiện tại
đúng. Không rewrite completed pilot để che lỗi wrapper.

Thêm output-boundary regression: wrapper mới chỉ ghi namespace phase5c_ trong
results của package và không resume thư mục thiếu pilot config. Không thay
producer lịch sử hoặc chạy thêm evaluations để sửa các guard orchestration này.

Bytes wrapper **thực sự đã chạy** được archive tại
[executed_producer_snapshot.py](phase5c_validation/executed_producer_snapshot.py),
SHA khớp input manifest. Source wrapper hiện tại có revision kiểm tra chặt hơn;
supplemental validation ghi riêng cả hai hashes và bind source_pool/5 historical
candidate CSVs với original final manifest. Pilot cũ vẫn immutable, không tự
thay producer hash bằng code sửa sau đó. Native producer/core không thay đổi.

## 5. Full regeneration có nên phê duyệt không

Khuyến nghị **phê duyệt một full target lookup trong phạm vi numerical
finite-catalog diagnostic**, với checkpoint/seals/validation rõ. Pilot đã
reproduce và target chạy ổn; đây không phải phê duyệt tự động hoặc paper claim.
Full lookup vẫn **NOT_RUN**, cần xác nhận riêng của tác giả.

Kế hoạch:
[phase5c_full_regeneration_plan_vi.md](phase5c_full_regeneration_plan_vi.md).
2601 nodes có **294 unique map geometries**,212 candidates/group =62.328
calls, trong đó179MB/group =52.626MB calls. Con số325 trước đó bao gồm zenith
sweep contexts ngoài map; không dùng nó làm map workload estimate.

Ước tính cùng host từ target-warm và reproduction-cold timing: **12.5–18.2
phút**, cộng thay đổi I/O/checkpoint/tải máy nếu có. Đây là projection tuyến
tính, không phải runtime full đã đo hoặc confidence interval. Kế hoạch mô tả
resume, output mới, tolerance, lossless native-schema adapter và cách đưa rate
vào dynamic solver; không sửa rejection guard để cấp paper admission.

## 6. Còn thiếu gì cho paper-mode

Target noise.0136 đã xác nhận, không còn là câu hỏi tham số. Vẫn cần: cloud
mode/L_th/altitude/thickness/realization/seed/LOS resolution được chọn và phê
duyệt; HAPxy/q0 cho mission; nguyên rotor profile, Emax/graph/horizon;
fs/eta_valid/m0; epsilon/block interpretation, prior lambda; dữ liệu lookup
đúng geometry/noise với admission/provenance phù hợp và quyền/lifecycle cho run.

`binary_los_blockage` giữ candidate, không có cloud trong hai pilots.
`INSUFFICIENT_EVIDENCE`, `paper_admissible=false`, security_model limitations
và NOT_READY lifecycle giữ nguyên. Positive diagnostic K và finite-size proxy
không phải composable-security proof. Native truncated law/Gaussian-effective
aggregation và inherited source evidence vẫn phải được diễn giải đúng scope.
Frozen historical/current spec hash discrepancy được ghi nhận, không sửa
spec hoặc coi scoped pilot authorization là mở gate publication.

Test suite cuối: **135 passed in9.76s,0 failed,0 errors,0 skipped** (127 tests
có sẵn +8 case mới). Chạy từ thư mục package:

```powershell
python -X utf8 -m pytest -q --junitxml=docs/phase5c_validation/tests_final.xml
```

Catalog giữ1 READY/9 BLOCKED; IEEE rotor reference riêng vẫn READY. Preservation:
[verification.json](phase5c_validation/verification.json),
[tests_final.xml](phase5c_validation/tests_final.xml). Không thay original inputs/results,
Z/w/MB-QAM/Holevo, rotor hay `paper.yaml`; không full regeneration,
paper-mode, figures, commit hoặc push.
