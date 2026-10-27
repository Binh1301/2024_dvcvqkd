# Trial nhiễu dư — 2026-10-22

Đã chạy hai nguồn MB cố định, không tạo C,w, không tối ưu, không thay cache. Mọi K là raw bit/use, không clip. **MATHEMATICAL_DIAGNOSTIC_ONLY; security_valid=false.** Cấu hình bản thảo đạt kiểm tra PDF/moment và covariance. Reference không đạt normalization/moment compatibility trên [0,1]; số reference chỉ là thế đại số, không được chấp nhận là SKR của PDF yêu cầu.

## Công thức và zero

epsilon(eta)=epsilon_ch+epsilon_det/(eta eta_det), eta>0. Đặt M_A=P1 C1 Q(chi²), M=P0+M_A. Giữ nguyên absolute density, không chia cho M hay active probability.

Tích g(eta)=eta epsilon(eta)=epsilon_ch eta+epsilon_det/eta_det có giới hạn hữu hạn ở zero; epsilon(0) không định nghĩa. Boxed primary chọn g(0)=epsilon_det/eta_det, tức detector vẫn có excess trong outage: mean_eta_epsilon=epsilon_ch m1+(epsilon_det/eta_det)M. Active-only chọn g(0)=0: thay M bằng M_A. Hai giả thiết khác nhau về detector tại outage; active-only không conditioning/postselection. Hai noise moments khác đúng (epsilon_det/eta_det)P0. Không nhân atom với biểu thức singular trước khi quy định g(0).

F=(m1-mhalf²)VA; eta_f=mhalf²; N_pre=eta_f epsilon_f=F+mean_eta_epsilon. Untrusted detector loss và excess đều gán cho Eve: t=eta_det eta_f, N_post=eta_det N_pre, b=1+t VA+N_post=1+eta_det[m1 VA+mean_eta_epsilon]. Vacuum baseline bằng 1; không đưa loss vacuum vào excess lần nữa. epsilon_det là output additive quadrature excess SNU theo công thức yêu cầu, không tự đồng nhất với electronic v_el. Không thêm trusted receiver subsystem lần nữa.

a=1+VA; z=2sqrt(eta_det)mhalf C-sqrt(2N_post w). Gamma=[[a,0,z,0],[0,a,0,-z],[z,0,b,0],[0,-z,0,b]]. Homodyne dùng nu3=sqrt[a(a-z²/b)] và MI1D mean 2sqrt(t)Re(alpha), variance 1+N_post. Bob chọn một quadrature; không nhân đôi MI. Heterodyne dùng nu3=a-z²/(b+1), kernel CN(sqrt(t)alpha,1+N_post/2). Không ghép conditional Holevo hai receiver. Dạng entropy giữ nguyên theo receiver; toàn bộ t,N,z,spectrum và MI được tính lại. Chưa chứng minh direct Z_minus là worst case toàn interval.

## Parameters và nguồn

Chung: epsilon_ch=0.0186, epsilon_det=0.0135 SNU, eta_det=0.8, beta=0.95, tau_zen=0.92, lambda=1.55e-6 m, HAP/UAV=20000/1000 m, sigma_h=1 m, angular jitter=15.61e-6 rad, AoA sigma=1.5e-3 rad, FOV=6.25e-3 rad, zero boresight, AO OFF, phase OFF. Không tự thay production tau_zen=null.

Bản thảo: D_r=0.08 m, full divergence=233e-6 rad, zeta=30deg, w0=2lambda/(pi theta), L=21.939310229205779 km, VA=5.475, nu_raw=0.165, C=3.1986564642787387, w=9.973886145561931e-7. Giữ high-precision saved moments từ zenith channel_by_angle.json[30].
Reference: D_r=0.55 m, full divergence=10e-6 rad, w0=0.0986760647169751 m, L=21.9393102292 km, VA=5.5, nu_raw=0.165, C=3.2113076519605626, w=1.0248765983174194e-6. Giữ saved raw moments từ channel_by_distance.csv.

VA=2nbar; MB p_ij tỷ lệ exp[-nu_raw((i-7.5)²+(j-7.5)²)]. Source verification kiểm tra 256 positive probabilities, energy và identity. C,w giữ đúng precision xuất của cache, không tuyên bố AP mới ở 110digits. Reference peak khoảng 51.05 photons; không áp constraint mới lên nguồn lịch sử. Source paths/hashes, ensemble hashes, PDF coefficients và residuals ở result.json. Startup manifest chứa Git HEAD và hashes của 6108 tracked inputs.

## Historical implementation và đối chứng

Mã của hình đang mở đã dùng excess-only N_old=(m1-mhalf²)VA+0.0186m1, ideal detector. Nó không đưa vacuum vào excess nhưng ghép MI2D với Holevo homodyne. Reference dùng ideal heterodyne GH8, N_old=eta_f*0.0186 và bỏ fading variance khỏi noise covariance. Vì vậy actual old replay so với trial không phải đối chứng chỉ thay một noise term: còn khác receiver/detector/fading treatment. Bảng số ở dưới ghi rõ khác biệt.

Nhánh khác src/manuscript_literal_3moments.py có detector_noise=(2-R+2xi_det)/R, cấu trúc heterodyne, không phải chi_hom. Không có mapping xác lập xi_det=v_el=epsilon_det. Trial không đặt 0.0135 vào electronic parameter đó và không chạy total noise như excess để đếm lại vacuum.

Đối chiếu matched detector có định nghĩa vật lý: khai báo chi_hom=(1-eta_det+epsilon_det)/eta_det với output excess theo yêu cầu. Đây là convention bổ sung cho trial, không gọi nó là implementation historical vừa tìm thấy. Total noise=1/eta-1+epsilon_ch+chi_hom/eta. Trừ đúng total vacuum [1/(eta eta_det)-1] thì còn epsilon_ch+epsilon_det/(eta eta_det). Cùng zero extension thì hai nhánh số phải giống nhau. Script tính lại covariance, MI/Holevo cả hai: **matched Delta I_AB, Delta chi_BE, Delta K bằng 0** ở cả bốn hàng comparison.csv. Không tạo historical secure-rate giả từ total-noise chèn vào excess covariance.

Riêng manuscript, nếu chỉ thay MI2D bằng MI homodyne1D nhưng giữ ideal detector/N_old thì K khoảng -0.000816386961588192. Dấu dương trong hình cũ không còn sau riêng sửa measurement pairing.

## PDF: manuscript PASS, reference FAILED

Manuscript retained mass=1 tại precision input lưu; P0=0.0001698566765614106550, M_A=0.9998301433234385893450. Direct log-eta integration q=0,1/2,1 và noise khớp closed form trong 2e-13. Script vẫn dùng mass tính ra, không thay bằng 1.

Reference: xét đúng raw-moment closure lịch sử power-pointing zero-boresight times lognormal, d=chi², v=4sigma_X², B=A0 eta_atm. Đây không phải tuyên bố xác thực mọi sampler khác trong src/channel. M=0.9999634640362218031; M_A=0.9997936073596603928; upper-tail mass bị loại khoảng 3.65359637782e-5, vượt tolerance1e-10.
Saved m1=0.2793516597874326, truncated m1=0.2793146828468279935.
Saved mhalf=0.4484713170554535, truncated mhalf=0.4484345618430249457.
Vì support khác nhau, target dùng saved m1 không bằng integral[0,1]; residual=0.0186*(saved_m1-truncated_m1), khoảng 6.87771095246e-7. Đây là support mismatch, không phải numerical error. Script nhận diện trước covariance; số thế sau đó có retained_law_compatible=false. Không normalize, không đổi moment, không chuyển upper-tail mass về zero/one. Cần task khác chọn thống nhất law/support để có reference SKR được chấp nhận.

## Validation, security và scope

validation.json:111 producer checks PASS về số học/provenance, gồm source/PMF/energy, analytical/direct quadrature, fading variance, Gamma+iOmega và spectrum độc lập, MI entropy bound/Holevo nonnegative, matched formula/rate, entropy80/110digits,6108 protected files. **Không** biến reference PDF acceptance FAILED thành PASS.
independent_review.json:27 checks bổ sung; thực sự lập covariance epsilon_det=0 để kiểm tra b=eta_det*b_old+1-eta_det, z=sqrt(eta_det)*z_old, detector contribution chỉ một lần; ideal eta_det=1/epsilon_det=0 phục hồi security homodyne cũ; đối chiếu actual saved historical manuscript I/chi/K.

Manuscript MI GH16/32/64. Reference GH8 gốc vẫn chạy và lưu, thêm GH16/32/64 kiểm tra: GH8 lệch GH64 khoảng3.41e-11 bit/use; GH32/64 tối đa1.33e-15. Headline trial dùng GH64 có khai báo, không gọi nó là GH8. Source C,w không tính lại. Không RNG mới nên không đổi seeds.

Physical covariance chỉ là điều kiện cần: Gaussian-surrogate MI cho discrete-input fading, direct-Zminus worst case, outage flags/conditioning, estimation và operational security chưa xác lập. Cả bốn trial không được gọi là security-valid; reference còn không đạt support/normalization.

Frozen SHA256 df83ea63af3b475ecca03a44d22d3240ab24d695ff0ebef31f0cd6747db78c15 khớp re-freeze PROJECT_STATE(2026-10-01), khác historical expected hash trong AGENTS. Giữ blocker trước đây, UNVALIDATED_SECURITY_MODEL, NOT_READY_FOR_PUBLICATION_SCALE_RUNS, ObjectiveC USER_STOPPED. Không sửa frozen model.

## Files và phương trình đề xuất

Mới: scripts/run_corrected_excess_noise_trial.py và namespace kết quả này; cập nhật tối thiểu5 project ledgers theo evidence protocol. Không sửa production evaluator, scientific source, configs, caches, lịch sử hay manuscript. Script từ chối overwrite output đã tồn tại.
Đã chạy tại project root: .venv/Scripts/python.exe -X utf8 -B scripts/run_corrected_excess_noise_trial.py.
Không sweep, optimizer, C,w/AP/Fock generation, training/test/held-out/publication, commit/push.

Đã inspect: AGENTS, FINAL_MODEL_SPEC, SECURITY_SCOPE_FREEZE, NUMERICAL_CONVERGENCE_PREREGISTRATION, PROJECT_STATE/EVIDENCE/DECISION_LOG/NEXT_ACTIONS/SESSION_HANDOFF, PROPOSED_NUMERICAL_CERTIFICATION_PROTOCOL, security_model_consistency_audit; configs/default.yaml, manuscript_corrected_3moments.json, trusted_heterodyne_skr.json; zenith protocol/channel/source/decomposition; reference ao_objective_evaluations/channel_by_distance và2 source payloads.
Functions inspected/reused: recheck_manuscript_homodyne_noise:security/mi_gh; run_manuscript_literal_3moments:verified_candidate; exact_cache_provenance; unconstrained_three_scheme:candidate_from_payload/unconstrained_config/channel_row; theta10 distance:evaluate_candidate; LiteralChannel/moments/total_input_noise/detector_noise; trusted_heterodyne_skr:effective_channel; calculate_channel_pdf_and_moments:closed_form_channel_moments/_truncated_moment; optical:_channel_row; deterministic_mutual_information.

Nên sửa cách viết total noise/excess noise trong bản thảo. replacement_noise_equations.tex đề xuất LaTeX cho phần moment/detector đã kiểm tra ở cấu hình8cm với zero extension khai báo. Chưa sửa manuscript hoặc xác thực toàn security model; không thay Q/moment reference trước khi giải quyết support mismatch.

## Bảng số đầy đủ

| Configuration | Outage convention | I_AB | beta I_AB | chi_BE | K_raw | Retained law compatible |
| --- | --- | --- | --- | --- | --- | --- |
| manuscript_8cm_233urad_30deg | boxed_limit_at_zero | 0.00075876348709594168 | 0.00072082531274114464 | 0.059445139992718707 | -0.05872431467997756 | 1 |
| manuscript_8cm_233urad_30deg | active_only_unconditioned | 0.00075876520275712197 | 0.00072082694261926589 | 0.059436873020217308 | -0.05871604607759804 | 1 |
| reference_55cm_10urad | boxed_limit_at_zero | 0.45910467289437484 | 0.4361494392496561 | 1.1401354105470365 | -0.70398597129738039 | 0 |
| reference_55cm_10urad | active_only_unconditioned | 0.45910505466768203 | 0.43614980193429792 | 1.140132529314491 | -0.70398272738019319 | 0 |

### manuscript_8cm_233urad_30deg / primary boxed

| Quantity | Actual historical implementation | Corrected trial |
| --- | --- | --- |
| Distance km | 21.93931022920578 | 21.93931022920578 |
| Receiver | MIXED_2D_MI_HOMODYNE_HOLEVO | homodyne |
| Detector security convention | ideal detector | untrusted |
| eta_det | 1 | 0.80000000000000004 |
| epsilon_det | 0 | 0.0135 |
| VA | 5.4749999999999996 | 5.4749999999999996 |
| nu_raw | 0.16500000000000001 | 0.16500000000000001 |
| mean eta | 0.0002640339370277643 | 0.0002640339370277643 |
| mean sqrt eta | 0.015605944020553823 | 0.015605944020553823 |
| eta_f | 0.00024354548877265959 | 0.00024354548877265959 |
| mean noise term | 4.9110312287164157e-06 | 0.016879911031228715 |
| eta_f epsilon_f | 0.00011708528542541466 | 0.016992085285425413 |
| I_AB | 0.0019221999136069705 | 0.00075876348709594168 |
| beta I_AB | 0.001826089917926622 | 0.00072082531274114464 |
| chi_BE | 0.0017294319205515029 | 0.059445139992718707 |
| K_raw | 9.6657997375119024e-05 | -0.05872431467997756 |

The actual historical and trial columns are NOT matched-detector or noise-only comparisons.

| Quantity | Corrected boxed value |
| --- | --- |
| fading_excess_output_pre_detector | 0.00011217425419669825 |
| channel_excess_output_pre_detector | 4.9110312287164157e-06 |
| detector_excess_output_pre_detector | 0.016875000000000001 |
| eta_f_epsilon_f | 0.016992085285425413 |
| epsilon_f | 69.769657286844179 |
| eta_f_after_detector | 0.00019483639101812767 |
| total_excess_output_post_detector | 0.013593668228340332 |
| nu_1 | 6.4739391318220569 |
| nu_2 | 1.0135995292912217 |
| nu_3 | 6.4710840001112615 |

### reference_55cm_10urad / primary boxed

| Quantity | Actual historical implementation | Corrected trial |
| --- | --- | --- |
| Distance km | 21.9393102292 | 21.9393102292 |
| Receiver | heterodyne | heterodyne |
| Detector security convention | ideal detector | untrusted |
| eta_det | 1 | 0.80000000000000004 |
| epsilon_det | 0 | 0.0135 |
| VA | 5.5 | 5.5 |
| nu_raw | 0.16500000000000001 | 0.16500000000000001 |
| mean eta | 0.27935165978743259 | 0.27935165978743259 |
| mean sqrt eta | 0.44847131705545351 | 0.44847131705545351 |
| eta_f | 0.20112652222145311 | 0.20112652222145311 |
| mean noise term | 0.0037409533133190278 | 0.02207032432765749 |
| eta_f epsilon_f | 0.0037409533133190278 | 0.45230858094054477 |
| I_AB | 0.63418926311636525 | 0.45910467289437484 |
| beta I_AB | 0.60247979996054701 | 0.4361494392496561 |
| chi_BE | 0.52449880608660937 | 1.1401354105470365 |
| K_raw | 0.077980993873937643 | -0.70398597129738039 |

The actual historical and trial columns are NOT matched-detector or noise-only comparisons.

| Quantity | Corrected boxed value |
| --- | --- |
| fading_excess_output_pre_detector | 0.43023825661288728 |
| channel_excess_output_pre_detector | 0.0051959408720462464 |
| detector_excess_output_pre_detector | 0.016874383455611243 |
| eta_f_epsilon_f | 0.45230858094054477 |
| epsilon_f | 2.248875861546118 |
| eta_f_after_detector | 0.16090121777716249 |
| total_excess_output_post_detector | 0.36184686475243583 |
| nu_1 | 5.6612702919581048 |
| nu_2 | 1.4080738544849341 |
| nu_3 | 4.4571488242473292 |

### Changes from actual historical output (confounded)

| Configuration | Delta I_AB | Delta chi_BE | Delta K |
| --- | --- | --- | --- |
| manuscript_8cm_233urad_30deg | -0.0011634364265110289 | 0.0577157080721672 | -0.05882097267735268 |
| reference_55cm_10urad | -0.17508459022199047 | 0.61563660446042712 | -0.78196696517131803 |

### Matched total-noise converted to excess (declared trial convention)

| Configuration/outage | Historical total converted K | Corrected K | Delta I_AB | Delta chi_BE | Delta K |
| --- | --- | --- | --- | --- | --- |
| manuscript_8cm_233urad_30deg/boxed_limit_at_zero | -0.05872431467997756 | -0.05872431467997756 | 0 | 0 | 0 |
| manuscript_8cm_233urad_30deg/active_only_unconditioned | -0.05871604607759804 | -0.05871604607759804 | 0 | -4.9897966875095516e-110 | 4.9897966875095516e-110 |
| reference_55cm_10urad/boxed_limit_at_zero | -0.70398597129738039 | -0.70398597129738039 | 0 | 0 | 0 |
| reference_55cm_10urad/active_only_unconditioned | -0.70398272738019319 | -0.70398272738019319 | 0 | 0 | 0 |

