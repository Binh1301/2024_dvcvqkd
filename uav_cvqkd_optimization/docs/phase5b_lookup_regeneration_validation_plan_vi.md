# Kế hoạch validation lookup theo target tác giả — chưa cho phép chạy

Recipe: [optimized_physical_setup_regeneration.yaml](../configs/lookup/optimized_physical_setup_regeneration.yaml).
Trạng thái `PREPARED_NOT_RUN`, execution/publication authorization=false.
Đây là input recipe chính xác, **chưa có executor được chọn hoặc được chạy**.
Không gọi `execute()` của producer cũ: nó gắn OUT với thư mục lịch sử bất biến.

## Input đã bind

- Target Dr=.30m, full divergence35µrad, jitter1.561µrad, position SD.10m;
  xi_ch=.0136 và xi_det=.005SNU. Target native protocol ghi đầy đủ physical,
  beta, law/correlation/noise/normalization conventions và numerical settings.
- Bản thảo gốc .08m/233µrad/15.61µrad/1m giữ riêng. Recipe lấy context còn lại
  từ protocol receiver30 đã hash-bind; không gọi đây là mặc định manuscript.
- Native geometry file được hash-bind:51×51 nodes, x/y0..2000m inclusive,
  spacing40m; projection(1000,1000)m và delta_h19000m. Đây là **replay geometry
  của lookup cũ**, chưa phải tác giả chọn HAPxy cho nhiệm vụ bay mới.
- Mỗi node dùng zeta=atan2(hypot(x-1000,y-1000),19000),
  L=hypot(19000,hypot(x-1000,y-1000)). Các điểm cùng radius² dùng chung đúng
  context; không làm tròn góc về integer hoặc nội suy rate để điền bảng.
- Catalog212 source:33 Uniform,179MB; source_pool và source_payload_binding
  có hash. Tái dùng source payload/C/w theo decision hiện tại, không sinh nguồn,
  không kiểm chứng lại công thức Z/w. Claim chỉ finite-catalog argmax.
- Output dự kiến là namespace mới `results/optimized_physical_setup_lookup_PENDING_APPROVAL`;
  thư mục này **chưa được tạo**. Nếu đã tồn tại phải chọn tên khác, không overwrite.

## Cổng trước execution

1. Tác giả xác nhận base target xi_ch=.0136 thay cho historical .0186 và cấp
   phép riêng việc tính lại2.601 điểm. Xác nhận hiện tại đã được ghi như input
   target; chưa có quyền regenerate hay thay metadata của dữ liệu cũ.
2. Kiểm lại lifecycle và quyền cho đúng workload. Source/security labels cũ
   được giữ nguyên; không lách gate hoặc suy authorization từ recipe.
3. Verify SHA các input/producers, source roster, exact source scalar forwarding,
   scope và native conventions trước khi dựng runner mới. Quyết định HAPxy
   mission khác replay geometry đòi hỏi input geometry/rate tương ứng.

## Validation sau khi có phép

1. Seal cấu hình/producer/input mới trước tính toán; giữ output và logs riêng.
2. Kiểm SI, full/half angle, aperture diameter/radius, power/amplitude gain,
   beta, VA=Vmod convention và không normalize/thay channel law ngầm.
3. Đối chiếu scalar effective input với
   T=mh² và N=(m1-mh²)*VA+.0136*m1+.005*M0; giữ mass convention của producer.
   Không dùng .0186 như channel noise mới, cũng không cộng detector lần hai.
4. Benchmark small set được tác giả cho phép trước full grid: center/corners
   và geometry riêng; kiểm finite/domain, deterministic repeated inputs và
   interface noise forwarding. Không yêu cầu khớp rate cũ khi noise đã đổi,
   không ép dấu SKR hay hướng gain.
5. Khi được phép full grid: đúng2601 node/325 radius groups của geometry này,
   đúng212 candidate mỗi context nếu giữ nguyên catalog; ghi numerical failures
   đầy đủ. Winner phải có row/source identity, raw signed K, I_AB, chi_BE,
   VA/nu, context hash và source evidence. Không dựng dữ liệu để bù failure.
6. Kiểm CSV/NPZ đồng nhất, tọa độ/thứ tự/đơn vị, symmetry của geometry hiện tại,
   raw/potential policy, reproducibility và input/output seals. Không xem finite
   catalog là optimum liên tục hay suy composable security.
7. Full compatibility/admission là bước riêng với geometry/noise/protocol và
   evidence phù hợp. `require_lookup_compatibility` hiện vẫn fail-closed khi
   chỉ có subset matching; recipe không tự vô hiệu hóa guard đó.

Tất cả bước evaluation ở trên hiện là **NOT_RUN**. Không có run, rate mới,
runtime benchmark hoặc figure paper nào được tạo bởi kế hoạch này.
