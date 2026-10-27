# Những khác biệt toán học đã xác nhận

Tham chiếu tạm thời: bản43 SHA f970cd6d...fc27b, **chưa xác minh v43(2)**. Production, cache và outputs lịch sử được giữ nguyên. Công thức/số đầy đủ ở report_vi.md và equation_comparison.csv; file/function/line/hash ở component_classification.csv.

## 1. Khác ký hiệu, không tự đổi mô hình

- i_c/j_c chỉ đơn vị ảo; d=χ²; T=ηf; N=Tξf; C=tr(τ½aτ½a†). Chỉ tương đương khi dùng cùng convention và actual source.
- Δ của grid raw và scalar physical normalization có thể khác tên nhưng phải tạo cùng p,α.
- B và C của task chỉ là hai nhãn gọi cùng function power_conserving; không có “luật C mới” thứ ba.

## 2. Chuyển parameter tương đương có điều kiện

- Raw centered grid mean energy42,5 → unit-RMS gauge: νrepo=42,5νraw; physical α=Δk → νphys=νraw/Δ². Áp dụng trước tính PMF, không đổi denominator độc lập.
- Scaling classical y→y/2 đồng bộ mean/std giữ MI; không thay quantum covariance/source.
- Full-support Gram của cùng ensemble biểu diễn cùng τ,C,w với coherent-state definition. Finite Fock approximation và threshold rank không tự tương đương về sai số số học.
- Riceρ0=Rayleigh; Eq10 bằng primitive product khiρ0 trên whole-positive support, nhưng retained support [0,1] vẫn có normalization blocker.

## 3. Sai khác implementation so với bản43

- src/channel/pointing_error.py:manuscript_pointing_parameters dùng wL trong ν, trong khi Eq6 in weff. Tại critical A0 tăng0,0051750780, weq tăng0,00469123525m. Đề xuất sửa một đối số sau khi ràng buộc đúng v43(2); chưa sửa.
- Không gọi production src/cvqkd/covariance.py là lỗi cho protocol của nó: λ3=a−z²/(b+1) đúng là nhánh heterodyne được frozen trước đây, **khác yêu cầu homodyne**. Đưa nó vào v43 homodyne mới là defect tích hợp.
- Tương tự production complex MI không phải homodyne1D. Historical zenith dùng2D MI/homodyne Holevo là diagnostic không nhất quán receiver; không tái dùng làm SKR canonical.
- Tên manuscript_literal_3moments.py không bảo đảm version43: file định nghĩa v37 ηf=mh và detector/noise khác. “Literal” phải kèm version/hash.

## 4. Các thay đổi luật thực sự

- A độc lập lognormal amplitude × approximate pointing, continuationη>1; [0,1] retained law thiếu mass.
- B=C random-width Gaussian beam và exact circular aperture, support[0,ηatm]. Không conditional normalization/clipping; vẫn là luật khác.
- sample_fso_channel reject/resample activeη>1 → conditional active. bounded(...invalid_tail_to_erasure) chuyển tail vào0. Clipping tại1 sẽ tạo atom1. Các phép toán này không hoán đổi nhau.
- Finite aperture averaging v_sc=AapσR² khác Eq5 v=σR², dù raw Rytov integral khớp.
- Extra pointing/beam wander/orientation/AoA turbulence, phase/AO closures chỉ khớp fixture khi đã tắt hoặc bằng0; không suy rộng tương đương.
- Kruse/visibility extinction khác τzen^secζ fixed-profile route; user visibility table chưa cho phép altitude extrapolation.
- Historical detector efficiencyηdet với output epsilon khác ξch+ξdet/η không cóηdet; không biến đổi qua việc gọi epsilon là cùng mộtξdet.
- Gaussian effective likelihood chỉ giữ hai moment/noise, khác fading-mixture likelihood; ΔK+0,0002895433959 tại fixed law khi chỉ thay MI và giữχ.
- Averaged/statewise positive-part SKR khác rawK của một pooled effective channel.
- Maxχ trên DBL physical interval khác literal Zminus Eq14 về policy; bằng nhau tại fixture chính, chưa theorem cho mọi input.

## 5. Điểm manuscript cần tác giả sửa hoặc làm rõ

- Eq2 γ/ν: nếu khác nhau PMF không chuẩn hóa; |k|² phải nói rõ centered coordinate.
- Vmod=n̄/2 xung đột Eq12 coherent mean2Reα và Eq13 vacuum1. Có thể dùng normalization khác, nhưng phải đổi toàn bộ CCR/vacuum/covariance. Cách sửa ngắn trong convention hiện dùng là Vmod=2n̄.
- Eq12 real y và complexα trong modulus làm conditional mass<1; cần Reα cho homodyne, hoặc định nghĩa protocol khác. Không normalize likelihood sai một cách âm thầm.
- Eq10 continuation có support(0,∞); moment tích phân[0,1] giữ thiếu mass. Luật passive-loss toàn cục không được xác lập bằng việc gate số chấp nhận tiny tail.
- Eq10ρ≠0 khớp hai log-cumulant của Rice nhưng không exact; tỷ số whole-support moment là exp[ρ²q³/(2σs²d²(d+q))].
- Eq20 đòi hỏi extensionηξ(0)=ξdet; ghi rõ noise lúc outage và unit củaξdet.
- HV/Gd citations trống và optimizationTBD chưa là đặc tả đầy đủ.
- Fock Nmax và source-support inverse cần quy tắc sai số/provenance; số C,w hữu hạn không thay một chứng minh hỗ trợ.

## 6. Giới hạn số học

- Critical mass thiếu9,867% được closed/direct/stable-tail kiểm tra: modeling failure, không phải precision failure.
- Control35 thiếu1,0569955e-10 vượt tolerance1e-10: fail, không nới ngưỡng.
- Tiny-tail subtraction1−M0 có cancellation; stable erfc-survival thay phép trừ khi cần relative tail. Tail4,8e-246 không thể suy từ một residual3,4e-83.
- Pooled quadrature cũ chưa hội tụ ở tolerance đăng ký; giữ nguyên record fail. Addendum thay biến tương đương và level mới cho hội tụ1,06e-13, không sửa channel law hoặc tolerance.
- Full-Z grid/local refinement chưa rigorous enclosure; GH/check count không là global certification.

## 7. Giả định security chưa được giải quyết

- Ràng buộc theorem DBL/source covariance với DM modulation, fading effective reduction, real homodyne receiver và untrusted noise cụ thể.
- CSI/public announcements, outage flag, pulse selection, sifting/reconciliation và rate per emitted/retained pulse phải định nghĩa.
- Noise extension trong outage không tự mô tả dữ liệu Bob; không lấy một identity moment làm detector proof.
- Finite size, parameter estimation, composable/coherent-attack scope chưa được thực thi.
- Calibration turbulence/PAT/phase/LO/detector, hardware feasibility chưa được kiểm tra.
- Có mass1, Γphysical và K>0 chưa đủ phê duyệt secure-SKR.

Không có correction nào trong file này được tự động áp dụng. UNVALIDATED_SECURITY_MODEL và NOT_READY_FOR_PUBLICATION_SCALE_RUNS giữ nguyên.
