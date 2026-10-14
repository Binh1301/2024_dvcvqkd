# Một điểm tham chiếu corrected — ideal heterodyne

Ngày 2026-10-13. Thực hiện theo attachment `6abbafa6-e256-485a-9d73-bd96b2685dc4/Pasted text.txt`. Đã hoàn tất đúng **một candidate**: `L=21.9393102292 km, ν_raw=.165, VA=5.5`. R=1, ξ_det=0, ξ_ch=.0186, beta=.95, phase/AO OFF. C,w lấy từ cache đã xác minh, không tính lại.

**Blocker trusted-detector được bỏ khỏi đường ideal riêng.** Nhánh này dùng config/entry/results mới, không sửa hoặc ghi đè historical, literal, corrected trusted config, raw Eq. (10), Eq. (20), source caches hay kết quả trước.

Điểm tham chiếu đã tính được covariance, Holevo và các SKR chẩn đoán. **MI sampling chưa đạt precision target**; không gọi các con số SKR dưới đây là security lower bound đã được chứng nhận.

## Bằng chứng và file mới

| Path repository-relative | Vai trò |
|---|---|
| `configs/manuscript_corrected_3moments_ideal_reference.json` | Ideal receiver, một fixed candidate; sampling budget 4096/seed20261013, không nới tolerance |
| `scripts/run_manuscript_corrected_ideal_reference.py` | Entry ideal riêng; recompute channel, hai mức Holevo, hai loại MI; exclusive execution marker |
| `tests/test_manuscript_corrected_ideal_reference.py` | 5 tests ideal/third moment/covariance/entropy/interval/receiver |
| `docs/MANUSCRIPT_CORRECTED_IDEAL_REFERENCE_REPORT_VI.md` | Báo cáo này |
| `results/manuscript_corrected_3moments/ideal_heterodyne_reference_20261013/` | Startup snapshot, tests, execution marker, single-point result và integrity receipts |

Các file state/evidence được cập nhật theo EVID-0181/DEC-0164. Producer/config/source/ensemble hashes nằm trong `reference_result.json`; startup snapshot bind 3663 protected files. `preflight_tests.json` là receipt **29 tests CURRENTLY_VERIFIED_PASS** (24 cũ + 5 ideal), 0 failure/error. `integrity_receipt.json` kiểm tra lại sau hoàn tất.

Source payload: `results/exact_mb_test2/exact_source_cache/77fc4a06afc0dba6d2e357db36dc216d34677f30d69fdf1f78781b105af39f1c.json`. Candidate/cache/ensemble được xác minh bằng parameter hex, implementation/settings, ensemble hash và payload bytes theo protected source manifest. Không lấy C,w bằng interpolation hoặc source oracle.

## Physical channel và ba moment

| Field | Kết quả hiện tại |
|---|---:|
| raw_pdf_mass | 0.9841200272202841 |
| physical_pdf_mass | 0.9999999999999999 |
| mean_eta | 0.23790886783673015 |
| mean_sqrt_eta | 0.40114871429673266 |
| mean_eta_xi_total | **1.7665162371050331** |
| chi_het | **1** |
| AoA atom P0, vẫn giữ | 0.00016985667656141038 |

Raw Eq. (10) và coefficients không đổi. Physical law vẫn condition active trên `(0,1]`, giữ P0 delta0 và P1. Không sửa raw PDF để bắt mass=1. Tất cả ba moment được recompute từ cùng luật physical hiện tại, dùng independent quadrature checks.

\[
m_n=2+(\xi_{\rm ch}-1)m_1.
\]

Giá trị `2.662230522819319` của third moment nonideal trước đây **không được tái sử dụng**. Chi_het giảm từ1.8957142857142857 về1, nên m_n giảm đúng0.8957142857142857. Pure-loss/measurement terms trong m_n chỉ dùng bookkeeping; không đưa toàn bộ m_n vào quantum covariance hoặc Z.

## Effective channel, source và covariance

\[
T_{\rm eff}=m_h^2,\quad N_{\rm eff}=(m_1-T_{\rm eff})V_A+m_1\xi_{\rm ch},
\]

\[
N_{\rm eff}=(m_1-T_{\rm eff})V_A+m_n+m_1-1-\chi_{\rm het}.
\]

Hai đường agree trong1e-10. Không loại intrinsic heterodyne noise: chi_het vẫn1; ideal complex likelihood vẫn có variance shot noise bằng1.

| Field | Giá trị |
|---|---:|
| T_eff | 0.16092029098192165 |
| fading_noise_output | 0.42343717270144676 |
| channel_excess_noise_output | 0.0044251049417631805 |
| N_eff | 0.42786227764320994 |
| xi_eff | 2.658846035092476 |
| nu_raw | 0.165 |
| VA | 5.5 |
| C | 3.2113076519605626 |
| w | 1.0248765983174194e-6 |
| a | 6.5 |
| b | 2.312923878043779 |
| Z_star | **2.575487382363995** |

\[
b=1+m_1(V_A+\xi_{\rm ch}),\qquad
Z^*(T,\xi)=2\sqrt T C-\sqrt{2T\xi w}.
\]

Eq. (20) giữ nguyên và được tái dùng với `T=T_eff, ξ=ξ_eff`. T_eff, N_eff, b và Z_star không đổi khi chuyển detector; chỉ total-noise moment đổi. Test so sánh trực tiếp ideal/nonideal xác nhận điều này; không dùng các con số đã báo trước như đầu vào thay cho việc recompute.

## Holevo tại Z_star và trên khoảng hợp lệ

| Field | Giá trị |
|---|---:|
| lambda_1 tại Z_star | 5.668978112682573 |
| lambda_2 tại Z_star | 1.4819019907263522 |
| lambda_3 tại Z_star | 4.497800281293246 |
| chi_BE_at_Z_star | **1.2195896239728028 bits/use** |
| Z_admissible_interval | [2.575487382363995, 2.5773603608169613] |
| Z_worst_case, numeric | **2.575487382363995** |
| chi_BE_worst_case, numeric | **1.2195896239728028 bits/use** |
| chi tại upper endpoint | 1.2185959107733892 bits/use |

Interval có justification từ DBL Eqs. (11)–(13), với fixed centered C4 ensemble, phase-compensated independent pooled fading: c1=m_h C, c2=m_h VA/2, nB=(m1 VA+m1 ξ_ch)/2. Intersect standard-form uncertainty cap. Không tự bịa interval hoặc giả định Z_star tối đa hóa Holevo.

Current search: grid257, denser grid515, bounded refinement; dense-grid shortfall0, refinement success, không invalid covariance evaluation, không numerical repairs. Test độc lập còn dùng4097-grid. Ở **điểm này**, worst numeric correlation trùng lower endpoint; đây là kết quả tìm kiếm, không giả thiết chung. Các eigenvalues tại worst point do đó trùng các values tại Z_star.

Covariance positive và quantum uncertainty checks pass; entropy finite/stable, λj≥1. Ideal conditional spectrum dùng đúng `λ3=a−Z²/(b+1)`. `rigorous_global_error_enclosure=false`: numerical maximum chưa là enclosure sai số continuous supremum. Không tuyên bố finite-size/composable/operational security certification.

## Actual discrete fading-mixture MI

\[
p(y|i)=P_0\mathrm{CN}(y;0,1)+P_1\int_0^1
\mathrm{CN}(y;\sqrt\eta\alpha_i,1+\eta\xi_{\rm ch}/2)
f_{\rm active,phys}(\eta)d\eta.
\]

Đây là joint complex mixture; không factorize I/Q sau pooling và không dùng Gaussian-modulation Eq. (17). Sampling từ exact rho0 conditioned physical law; likelihood tích phân bằng positive quadrature. Correct MB/VA/ensemble được truyền nguyên vẹn.

| Field | Giá trị |
|---|---:|
| I_AB estimate | **0.4652637991973034 bits/use** |
| MC samples / seed | 4096 / 20261013 |
| Sampling standard error | **0.019468676410223464 bits/use** |
| 95% normal CI, sampling only | [0.42710519343326536, 0.5034224049613414] |
| Sampling SE target | 0.002 bits/use |
| MI precision status | **SAMPLING_PRECISION_NOT_MET** |
| Likelihood quadrature order | 32→64 |
| Paired refinement mean difference | 5.238964994016047e-10 bits/use |
| Quadrature status | CONVERGED_NUMERICALLY |
| H(p) | 5.693536774554172 bits/use |

Mass/moment quadrature checks pass1e-6, likelihood refinement pass1e-4; entropy-bound diagnostic pass. Standard error **không đạt** mục tiêu. Không nới tolerance hoặc tăng budget để đổi FAILED precision thành PASS. Không gọi estimator này là exact MI hoặc một bound đã chứng minh.

Seed này tình cờ có0 outage trong4096 sampled uses; expected outage probability vẫnP0, và atom vẫn xuất hiện **đúng trọng số trong likelihood** cũng như Bernoulli sampling law. Không xóa outage, không conditioning lại các sampled uses theo observed outage.

## Effective Gaussian MI — kết quả riêng

Surrogate likelihood dùng cùng discrete256 ensemble:

\[
Y|i\sim\mathrm{CN}(\sqrt{T_{\rm eff}}\alpha_i,1+N_{\rm eff}/2).
\]

Recompute bằng `deterministic_mutual_information`, `T=T_eff, epsilon=xi_eff`; không dùng ξ_ch làm epsilon ở đây. Phương sai complex `1.213931138821605`. GH8/16/32 lần lượt cho:

| GH order | I_AB approximation |
|---|---:|
| 8 | 0.4484184676630707 |
| 16 | 0.4484184676941583 |
| 32 | **0.4484184676941574** |

Last refinement difference8.881784197001252e-16, dưới1e-8. Đây là **effective Gaussian channel approximation**, không phải actual fading-mixture MI. Tolerance convergence chỉ kiểm tra quadrature, không bound sai số thay thế mixture bằng AWGN. Không dùng kết quả này âm thầm để thay MI sampling chưa đạt precision.

## Signed SKR diagnostics

| MI model | beta_I_AB | K_at_Z_star | K_conservative dùng numeric interval maximum |
|---|---:|---:|---:|
| Actual mixture, Monte Carlo point estimate | 0.44200060923743817 | **−0.7775890147353646** | **−0.7775890147353646** |
| Effective Gaussian approximation | 0.42599754430944947 | **−0.7935920796633533** | **−0.7935920796633533** |

Đơn vị bits/use. Giữ nguyên giá trị âm; không clipping hoặc gọi K_operational=0 là raw SKR. K_conservative ở bảng là diagnostic từ **numeric** max Holevo; `validated_security_lower_bound=NOT_ESTABLISHED`. Sai số sampling của K point estimate có standard error beta×MI_SE; CI chỉ xét sampling, không bao gồm source moments/quadrature/security-bound errors.

`scientific_validation_status=NOT_ESTABLISHED_MI_PRECISION`. Blocker nonideal detector của lượt trước đã được tránh bằng lựa chọn ideal do user chốt; precision của actual MI và rigorous full-error certification chưa được xác lập. Giá trị âm này thuộc đúng candidate/model được đánh giá, không chứng minh tối ưu toàn cục hoặc mọi protocol không thể phát khóa.

## Các kiểm tra yêu cầu và preservation

13 mục validation trong task được đối chiếu trong `required_validation_checks.json`. Software checks hiện hành29tests PASS bao gồm chi_het1, third moment, mass, Teff, dual noise, covariance/spectrum/entropy, ideal receiver noise, no double counting, actual historical regression `0.07798099387393764`, literal regression/mass và protected files. Những PASS này **không** biến sampling precision failure thành scientific PASS.

3663 protected files không thay đổi; giữ cả corrected implementation/config/results trước, historical code/results, literal mode, catalog182, Objective B/C và exact caches. Frozen SHA256 vẫn `df83ea63af3b475ecca03a44d22d3240ab24d695ff0ebef31f0cd6747db78c15`; historical AGENTS hash mismatch không bị sửa hoặc che giấu. Lifecycle vẫn NOT_READY_FOR_PUBLICATION_SCALE_RUNS; Objective C USER_STOPPED/PID0.

Không AP/source recomputation, AO, restartC, all182, full26, training/held-out/final-test/publication evaluation, commit hoặc push. Chỉ một execution marker và một reference result; wall time của scientific entry khoảng6.016s. Dừng sau single-point diagnostic và report. Numerical refinement/sample expansion/optimization cần một yêu cầu mới; không tự tiếp tục để đạt precision target.
