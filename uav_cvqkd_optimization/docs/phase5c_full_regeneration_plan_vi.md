# Kế hoạch full lookup target .0136 sau pilot — chưa được chạy

Pilot thực:
[summary.json](../results/phase5c_skr_noise_pilot_20261107/summary.json),
[validation độc lập](phase5c_validation/pilot_validation_final.json).
**Full regeneration authorization vẫn false.** Tác giả đã xác nhận target
noise .0136; quyết định còn chờ ở đây là quyền chạy full, không hỏi lại giá trị.

## Input và workload chính xác

- Giữ bốn optical values .30m/35µrad/1.561µrad/.10m, detector .005SNU,
  channel .0136SNU; beta.95 và native conventions hiện tại. Chỉ thay xi_ch
  so với protocol lịch sử; không sửa C/w, MB-QAM/Holevo hoặc dữ liệu gốc.
- Geometry replay lookup:51×51 nodes x/y0..2000m, HAP projection(1000,1000)m,
  HAP/UAV altitude20000/1000m. 2.601 spatial points có **294 radius² groups**,
  không phải325. Số325 lịch sử gồm294 map geometries và các context thêm của
  zenith sweep. Tài liệu Phase5B ghi325 cho map phải được đọc theo correction
  Phase5C này; artifact cũ không bị sửa.
- Mỗi group dùng exact atan2/hypot, không nearest-angle hoặc rate interpolation.
  Grouping này chỉ đúng context đối xứng hiện tại; không áp cho geometry/model
  khác. Projection trên chưa tự trở thành HAPxy mission được tác giả chốt.
- Catalog212 nguồn có hash:179MB và33Uniform; argmax raw signed K riêng từng
  family, giữ tie policy theo thứ tự catalog. Tổng **62.328 evaluations**,
  trong đó52.626MB. Tính ngây thơ mỗi node riêng là551.412 calls, không cần
  thiết với symmetry hiện tại. Không gọi đây là optimum liên tục.
- Dùng recipe đã chuẩn bị ở
  [Phase5B](../configs/lookup/optimized_physical_setup_regeneration.yaml) như
  input reference có version; tạo run config mới bind pilot/source/protocol
  hashes và ghi quyền mới. Không dùng authorization lịch sử của run cũ.

## Chi phí dựa trên phép đo thực

Pilot2120 calls tại5 positions×2 noises, elapsed38.0597s; preparation6.6377s.
Target stage: context+.catalog12.6508435s/5 =2.5301687s/context; reproduction
kể cold overhead18.4568625s/5 =3.6913725s/context. Ánh xạ tuyến tính294 contexts
cộng preparation cho khoảng **750.5–1091.9s (12.5–18.2 phút)** trên host hiện
tại. Đây là planning estimate từ hai chế độ cache/cold quan sát được, không
phải confidence interval hay runtime full đã đo. I/O, sealing, validation,
cache/import và tải host có thể thay đổi; không nhân runtime pytest làm benchmark.

## Checkpoint/resume và output

1. Namespace mới đề xuất `results/phase5c_target_noise_lookup_FULL_PENDING_APPROVAL`;
   chưa được tạo. Nếu đã tồn tại chọn namespace khác, không overwrite.
2. Seal config, ordered catalog/payloads, physical/noise protocol và producer
   snapshots trước evaluation. Không monkey-patch hard-coded validator cũ;
   bind rõ physical context và active effective-noise protocol như pilot đã
   kiểm, giữ native evaluator và native numerical guards.
3. Checkpoint mỗi unique geometry: full candidate rows, context, selected
   winners, diagnostics/runtime, config/input hash, noise, seed=null deterministic.
   Atomic write checkpoint rồi seal; chỉ resume complete sealed records. Kiểm
   geometry/stage/noise/config, ordered roster, scalar identities và winner
   policy trước reuse; partial/unsealed records không được tự nhận đã hoàn tất.
4. Native GH64/128 tolerance2e-10; precision agreement80/110 digits2e-11;
   pilot reproduction atol2e-10,rtol0, exact source identity. Không nới tolerance
   hoặc sửa sign/rate để vượt gate. Failure được lưu và dừng trước export đầy đủ.
5. Sau tính đủ294 contexts, map về đúng2601 nodes; kiểm CSV/NPZ/order/symmetry,
   all candidates/winners, signed raw vs separately defined potential, source
   labels, input/output hashes và reproducibility. Không sao chép rate cũ làm
   target hoặc tái label evidence.

## Schema adapter và dynamic-rate solver

Native CSV có x_m,y_m,MB_K_raw và các cột nguồn/quantity liên quan. Một adapter
mới phải xuất riêng x_m,y_m,skr_bits_per_use và/hoặc NPZ points[N,2],rates[N],
lossless binary64 (17 significant digits/round-trip verification), bind source
CSV hash/protocol/candidate policy. Chốt dùng MB_K_raw hay max(0,MB_K_raw)
trong run config; không clip ngầm. Đơn vị m và bits/use, không tự đổi sang bits/s.

`SKRLookup` nội suy chỉ khi query ở trong domain và có scope/accuracy rõ; cần
kiểm sai số off-grid trước claim. Full compatibility/admission vẫn cần positive
context binding; rejection guard hiện tại không tự cấp quyền khi subset khớp.
Sau khi dữ liệu được chấp nhận, solver nhận static clear-sky R[j] hoặc snapshot
R[k,j] qua `Scenario`/`sample_link_provider` và `run_methods`. Binary LOS erasure
dùng cùng clear rate với z[k,j],m0; không cộng analog loss lần hai. Cloud hiện
chưa được chọn, nên không tạo cloud rates hay trajectory từ bảng mới.

## Trước sử dụng cho paper

Cần permission/lifecycle đúng phạm vi, model/protocol/noise/geometry/source
lineage được chấp nhận, dữ liệu đầy đủ và validation PASS có seals. Numeric
pilot/full PASS không nâng `INSUFFICIENT_EVIDENCE`, `paper_admissible` hoặc
security scope. Vẫn cần cloud approval/parameters, HAPxy/q0, rotor/Emax/graph/
horizon, fs/eta_valid/m0, epsilon/block interpretation, lambda và scope của
finite-size-aware proxy. Không có training/final-test/publication access được
phê duyệt bởi kế hoạch này.
