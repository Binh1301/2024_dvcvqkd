# Phase 5B — physical setup tác giả và candidate cloud blockage

Đã ghi input được tác giả xác nhận vào
[optimized_physical_setup.yaml](../configs/channel/optimized_physical_setup.yaml),
với provenance **AUTHOR_SUPPLIED** và SHA-256 file yêu cầu. Tên “optimized” là
nhãn bộ tham số tác giả cung cấp, không phải chứng nhận optimum toàn cục.
[Reference manuscript gốc](../configs/channel/hap_uav_mb_reference.yaml) giữ
nguyên. Không sửa Z/w, MB-QAM/Holevo, rotor, `paper.yaml`, lookup hoặc hình cũ.

## 1. Lookup cũ thực sự dùng noise nào

| Input | Manuscript reference | Author-tuned target | Lookup đã lưu |
|---|---:|---:|---:|
| Aperture diameter (m) | .08 | .30 | .30 |
| Full-angle divergence (µrad) | 233 | 35 | 35 |
| Pointing jitter mỗi trục (µrad) | 15.61 | 1.561 | 1.561 |
| UAV position SD mỗi trục (m) | 1 | .10 | .10 |
| xi_det (SNU) | null | .005 | .005 |
| xi_ch (SNU) | null | **.0136** | **.0186** |

Kết luận từ dữ liệu lưu: lookup được sinh với **xi_ch=.0186 và xi_det=.005**,
không phải channel=.0136. Đã đối chiếu `execution_physical_protocol.json`,
`authorization.json`, SHA của producer/execution identity, seals CSV/NPZ và325
context/650 winner scalars. Producer gọi evaluator với chính protocol này.

Kiểm tra I/O duy nhất:
`N_effective=(m1-mh²)*VA+xi_ch*m1+xi_det*M0`. Dùng .0186 khớp650 bản ghi với
max residual0; giải ngược channel noise cho range
[.018599999999999985,.018600000000000012]. Thay bằng .0136 trong identity này
lệch output noise khoảng.000932763–.001150302 SNU. Không tính lại SKR, Z/w,
MI hoặc Holevo. Chênh lệch noise đó không phải một phép hiệu chỉnh rate.

Mặc dù .0136+.005=.0186 về số học, **không được gọi .0186 trong lookup là
“total đã gồm detector”**: code cũ dùng .0186*m1 và thêm .005*M0 riêng. Đây là
hai noise terms có trọng số khác nhau, không được đổi nhãn để hợp thức hóa.

Target mới khớp bốn optical fields và detector noise nhưng **không tương thích
lookup cũ do channel noise**. Guard được mở rộng để báo đúng mismatch này,
kiểm noise hữu hạn/không âm, và vẫn không cấp full admission khi chỉ subset
khớp. Labels `INSUFFICIENT_EVIDENCE`, `paper_admissible=false` giữ nguyên.
Không chạy lại2.601 điểm.

## 2. Sanity check Gaussian beam

Theo manuscript PDF p2, full divergence theta:

`w0=2*lambda/(pi*theta)`,
`w(L)=w0*sqrt((1-L/F0)^2+(L*lambda/(pi*w0^2))^2)`.

Với lambda1550nm, theta35µrad full-angle và F0=infinity:
**waist radius tại transmitter w0=.028193161m**, waist diameter=.056386323m.
Helper Gaussian-beam hiện có được tái dùng; không đổi35µrad của tác giả.

| Slant distance | Beam radius w(L) | Beam diameter | Ideal centered circular capture, Dr=.30m | Nominal erf approximation |
|---|---:|---:|---:|---:|
| 19.00km | .333693129m | .667386258m | .332440738 ≈33.24% | .329935835 |
| 21.94km | .384983710m | .769967420m | .261857368 ≈26.19% | .260283961 |

Receiver-plane footprint lớn hơn transmitter waist; không lấy .028m làm bán
kính spot ở UAV. Circular capture là `1-exp(-2*(Dr/2)^2/w(L)^2)`. Cột erf
dùng `[erf(sqrt(pi)*Dr/(2*sqrt(2)*w(L)))]²` cho **diffraction-only diagnostic**.
Full manuscript dùng w_L,eff=w_L*sqrt(1+G_d); bảng không gán G_d paper bằng0,
không tính broadening/turbulence/jitter/AoA/atmosphere và không đại diện tổng
channel transmission hay SKR. 21.94km là khoảng cách yêu cầu cho sanity check;
reference30° chính xác của Phase4 là21.939310229km, không bị thay đổi.

## 3. Candidate binary LOS blockage và cửa sổ quan sát

[binary_los_blockage_candidate.yaml](../configs/cloud/binary_los_blockage_candidate.yaml)
giữ `author_approved=false`, `threshold_approved=false`, L_th/layer/spacing/
realization/seed null. Builder chỉ chạy khi có approval mode **và** threshold,
provenance của approval/realization, field velocity khớp, layer và LOS spacing.
Đây là candidate, chưa phải official paper baseline.

Builder tái dùng `BlockageModel` cắt HAP→UAV segment với cloud slab rồi sample
CLWC trên phần giao; không test endpoint UAV thay cho LOS. Candidate map rõ
sang policy cũ `binary_erasure`: blocked→T=0,rate contribution=0,m=0, skip SKR
backend; clear→clear-sky MB rate và m0. Không thêm analog attenuation hay hệ số
CLWC→extinction. LOS lấy mẫu cần kiểm tra độ hội tụ spacing trước scientific
use; đây không phải chứng nhận giao cắt liên tục.

| Time | Left edge trong static cloud-reference | Window x-range |
|---|---:|---|
| 0s | 0m | [0,2000]m |
| 300s | 1500m | [1500,3500]m |
| 1000s | 5000m | [5000,7000]m |

Với drift(-5,0)m/s, `q_ref=q_local-v*t`; vùng UAV vật lý vẫn cố định. Mỗi
window2000×2000m,50×50 cells, cell40×40m. Offset1500m tương ứng37.5cells,
không snap. Helper mới evaluate Gaussian analytic tại đúng cell centers trong
reference t=0, rồi threshold **chính array CLWC đó** để tạo mask binary.
Không cần nội suy khi có analytic field; bản vẽ/NPZ lịch sử với bilinear local
sampling được giữ nguyên và kiểm exact starts cùng masks từ cùng field.

Finite-size vẫn là `finite_size_aware_key_yield_proxy`: m_k=m0*z_k,
n_K=sum(m_k),S_K=sum(m_k*R_clear(q_k)); một penalty
`7*sqrt(n_K*log2(2/epsilon))` trên toàn accumulated prefix, không cộng theo
slot, không double-count cloud. Không tuyên bố composable security.

## 4. Chuẩn bị regeneration và quyết định còn thiếu

Đã chuẩn bị [recipe chính xác](../configs/lookup/optimized_physical_setup_regeneration.yaml)
và [validation plan](phase5b_lookup_regeneration_validation_plan_vi.md): target
native protocol, hashes input/catalog, exact51×51 geometry và212 candidates.
Projection(1000,1000)m là geometry replay lookup, **không phải HAPxy mission
được tự chốt**. Recipe `PREPARED_NOT_RUN`, execution=false, output namespace
mới chưa được tạo; không chuyển authorization lịch sử sang run mới.

Chỉ còn cần cho base experiment:

- Chốt target noise dùng.0136 như yêu cầu mới (và quyền regenerate riêng),
  hay chọn rõ historical .0186 scenario; không sửa metadata cũ.
- L_th, cloud altitude/thickness, LOS spacing validation, realization/seed
  có provenance và approval mode/threshold.
- HAPxy và q0; energy budget, waypoint graph và prediction horizon.
- Symbol rate và eta_valid/m0 với accounting không chứa lại cloud erasure.
- Những input base khác vẫn chưa được task này chốt: nguyên profile rotor
  cho mission, epsilon/block interpretation, prior greedy lambda và scope/quyền
  chạy research proxy theo [decision sheet Phase5](phase5_author_decisions_vi.md).

Không cần hỏi lại bốn optical values hoặc detector noise đã xác nhận. Không
điền null từ demo, không coi finite-size reference là mission default.

## 5. Kiểm thử và artifacts

Baseline112 passed in6.20s. Lần chạy cuối **127 passed in7.25s,0 failed,
0 errors,0 skipped** (112 cũ +15 case mới), exit0:

```powershell
python -X utf8 -m pytest -q --junitxml=docs/phase5b_validation/tests.xml
```

Các tests mới kiểm provenance sáu input, beam SI và
full angle, exact windows, common-field binary mask, rigid drift, pending
approval, nội điểm LOS khác endpoint, clear saved-response replay/blocked skip,
one-block finite-size, noise inference từ650 saved winners, lookup refusal và
noise domain. Chỉ software fixtures có số cloud giả lập; không xuất research
rates/trajectories mới. Kết quả cuối: xem
[verification.json](phase5b_validation/verification.json) và
[tests.xml](phase5b_validation/tests.xml).

Review độc lập: [phase5b_independent_review.md](phase5b_independent_review.md).
Đã bổ sung regression RED→GREEN cho noise nonfinite/negative và ghi lại
mass-tolerance role trong recipe là inherited diagnostic, không phải approval.
Checkpoint audit trước sửa giữ riêng; audit hiện hành:
[physical_and_noise_audit_verified.json](phase5b_validation/physical_and_noise_audit_verified.json).

File mới:3 config kể trên, `physical_setup.py`, `cloud_candidate.py`,
`phase5b_audit.py`, tests Phase5B, kế hoạch/report/validation artifacts.
File cũ sửa duy nhất: `src/uav_qkd/skr_lookup.py` cho noise comparison/refusal.
Catalog vẫn **1 READY,9 BLOCKED**; IEEE2019 rotor riêng vẫn READY.
Không chạy paper-mode, tạo hình mới, đổi lifecycle/evidence, commit hoặc push.
