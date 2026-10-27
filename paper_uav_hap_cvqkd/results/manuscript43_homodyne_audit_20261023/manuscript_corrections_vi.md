# Đề xuất sửa manuscript43 — không chỉnh sửa PDF

| ID | Equation / nội dung | Loại phát hiện | Đề xuất |
| --- | --- | --- | --- |
| M01 | Sau(3),Vmod=n̄/2 | Confirmed mathematical error dưới X=2Reα | Sửa Vmod=2n̄; giữ exact source/caches |
| M02 | (12),complexα trong Gaussian1D | Confirmed mathematical error | Real mean2√T Reα;y∈R;không nhân MI lên2 |
| M03 | (2),γ ở tử/ν ởZ | Missing definition/notation; lỗi normalization nếu khác nhau | Dùng cùng shaping symbol ở numerator/denominator |
| M04 | (2),norm indexk không centered | Missing convention; khác source hiện có | Ghi centered raw energy hoặc physical-energy mapping rõ |
| M05 | ξdet sau(17),(20) | Missing reference-plane definition | Phân biệt εdet/ηdet,χhom và independentξdet |
| M06 | σξ² sau(12) | Missing measurement-plane definition | Physical output dùng1+ηdet[(m1−mh²)VA+m1ξch]+εdet và signalTtotal=ηdetmh² |
| M07 | W,Z ở(13),(14) | Security-model ambiguity với untrusted detector | Cùng physical quantumTtotal,Npost cho Z,Γ,χ;rescale measurement không rescale quantumΓ tùy ý |
| M08 | (10),(18)–(20),support[0,1] | Confirmed normalization failure tại context đã lưu | BáoM0,tail,atom0;quyết định model trước fullprotocol;không silent renormalization |
| M09 | (8)→(10) khiρ≠0 | Confirmed exact-product inconsistency bằng moment counterexample | Ghi approximation/domain hoặc bổ sung derivation choρ≠0 |
| M10 | (5),σR² | Missing approximation/variance convention | v=Var(logIa)≈rawRytov khi weak;Var(log amplitude)=v/4 |
| M11 | Gaussian effective MI | Missing approximation statement | Constant noise là moment matching;fading conditional noise phụ thuộcX² |
| M12 | (14),lowerZ vs worstχ | Security/numerical scope | Physical interval và full-Zmax nếu dùng;finite-grid không là global proof |
| M13 | Homodyne claim vs production2D path | Numerical protocol-pairing issue khi dùng sai caller | Dùng homodyne1D;old2DMI+homodyneHolevo không là consistentnew rate |
| M14 | [] choGd,Cn²;OptimizationTBD | Notation/writing và missing provenance | Bổ sung nguồn/derivation;không mô tảTBD như đã triển khai |

Với y thực nhưng mean phứcμ=2√ηfα:

\[
\int_{\mathbb R}\frac{e^{-|y-\mu|^2/(2\sigma^2)}}{\sqrt{2\pi\sigma^2}}\,dy
=e^{-(\operatorname{Im}\mu)^2/(2\sigma^2)}.
\]

Với centeredC4, \(E[X^2]=2E|\alpha|^2=2\bar n\). Vì vậy lỗi Vmod là hệ số4; không đổi C,w để khớp cách viết đó.

ConventionB (\(\xi_{\rm det}=\chi_{\rm hom}\)) có thể tái tạo MI của measurementrescaled. Nó không cho phép dùng quantumΓrescaled standard form với CCR/vacuum cũ. Physical detectorloss là quantumloss; electronics làεdet; đều untrusted trongC.

Exact untruncated product moments từ Eq.(8) và lognormal Eq.(5):

\[
P_1 B^q e^{v(q^2-q)/2}\frac{d}{d+q}
\exp\left[-\frac{\rho^2q}{2\sigma_s^2(d+q)}\right],\quad d=\chi^2.
\]

Whole-support moment của Eq.(10):

\[
P_1B^q\frac{d}{d+q}
\exp\left[\log C_1+\frac{(d+q)^2}{4C_3^2}-(d+q)\mu\right].
\]

Chúng trùng khiρ=0, không trùng tổng quát. Rician_product_checks.csv là bằng chứng định lượng; không thay truncated moments trong audit.

Tài liệu: [Denys–Brown–Leverrier](https://arxiv.org/html/2103.13945v3) cho DM correlation/homodyne; [Laudenbach et al.](https://arxiv.org/pdf/1703.09278) cho receiver/noise framework. Các reference không tự phê chuẩn protocol/security scope của repo. Số liệu và trạng thái code/cache nằm trong report_vi.md cùng CSV/receipts.
