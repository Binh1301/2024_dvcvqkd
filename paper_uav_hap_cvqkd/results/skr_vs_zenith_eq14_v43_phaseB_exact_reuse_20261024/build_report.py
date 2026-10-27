"""Reports from saved CSV/JSON only; never recompute source or channel quantities."""
from inventory import OUT,ROOT,PRIOR,read,rows,sha,save


def main():
    summary=read(OUT/'diagnostic_summary.json');selected=rows(OUT/'diagnostic_selected_schemes.csv')
    independent=rows(OUT/'selected_independent_validation.csv');contexts=read(OUT/'channel_contexts.json')
    table=[]
    for angle in summary['angles']:
        group=[r for r in selected if float(r['zenith_deg'])==angle]
        table.append('| '+str(angle)+' | '+' | '.join(f"{float(r['K_raw']):.12g}" for r in group)+' |')
    primary=read(PRIOR/'protocol.json');physical=primary['physical']
    text=f'''# Tái sử dụng exact C,w — chẩn đoán SKR theo chín góc zenith

**DIAGNOSTIC-ONLY hoàn tất. Strict Phase B vẫn BLOCKED. Số phép tính C,w mới: 0.**

## Kết quả nguồn và phạm vi

Đã xác minh 238 payload lịch sử, hợp nhất thành 235 source identities tương thích:
38 Uniform và 197 MB. Đối chiếu 245 catalog/bảng nguồn, 59.439 hàng gắn với nguồn,
không thấy xung đột. `exact_source_inventory.csv` giữ identity, raw/binary64
VA/nu, nu_repo, C,w/hex, convention, original path/hash, aliases và numerical provenance.
Không thay đổi C,w hoặc source artifacts; dedup chỉ khi identity và C,w khớp.

Pool pilot yêu cầu có 81 nguồn: **80 phục hồi và tái sử dụng được** (33 Uniform,
47 MB). Taxonomy giữ nguyên: 6 VERIFIED_EXACT, 1 VERIFIED_BY_ALTERNATIVE_EVIDENCE,
74 INSUFFICIENT_EVIDENCE, 0 INVALID. Nhóm 74 gồm 73 payload tương thích thiếu
receipt và một Uniform chưa có payload. Không gán SKR thành công thành convergence PASS.

Uniform còn thiếu: nu_raw=0, VA=1.6249995399703647,
VA_hex=0x1.9ffff84830112p+0. Không tìm thấy source giống hệt trong catalog/cache;
không nội suy hoặc dùng VA=1.625/MB moments. Xem `missing_uniform_source.md`.

## Hai phạm vi chẩn đoán riêng

1. **Pilot khả dụng 80 nguồn:** 720 cặp nguồn–góc; giữ nguyên trong
   `pilot_candidate_diagnostic_results.csv`, cùng selection và views có prefix
   `pilot_`. Matrix của pool 81 là `pilot_nine_angle_coverage.csv`, có chín ô thiếu.
2. **Toàn catalog khả dụng trong miền đã duyệt:** 212 nguồn (33 Uniform,179 MB),
   VA=[0.05,10], nu_raw=[0,0.40]. Tái dùng đúng 720 kết quả trên và bổ sung 1.188
   cặp của 132 nguồn khác. Không thay thế Uniform thiếu bằng nguồn bổ sung.
   `available_catalog_protocol.json` khóa scope này.

`diagnostic_results.csv` có **1.908 hàng**, mọi hàng qua GH64/128 và Eq14/Holevo
80/110 digits. **12 hàng K dương, 1.896 hàng K âm**, không clipping hoặc bỏ hàng âm.
`nine_angle_coverage.csv` gồm 236 hàng: 235 source đã có và một Uniform thiếu.
212 hàng được đánh giá ở chín góc; 23 source ngoài miền chỉ được inventory,
ghi OUTSIDE_APPROVED_DOMAIN_NOT_EVALUATED. Mỗi pool giữ giống nhau ở mọi góc.

Mọi selection mang nhãn **HISTORICAL_EXACT_RESTRICTED_CATALOG_DIAGNOSTIC**:
best-tested trên finite available catalog, không phải optimum liên tục, full
pool có Uniform thiếu, strict pilot hoàn tất hay publication/security approval.

## Cấu hình và công thức giữ nguyên

| Tham số | Giá trị |
|---|---|
| HAP/UAV | {physical['h_hap_km']:g}/{physical['h_uav_km']:g} km |
| Receiver diameter | {physical['Dr_m']:g} m |
| Wavelength/full divergence | 1550 nm / {physical['divergence_full_urad']:g} urad |
| Jitter mỗi trục / position SD | {physical['jitter_urad']:g} urad / {physical['sigma_h_m']:g} m |
| tau_zen | {physical['tau_zen']} |
| xi_ch / xi_det / beta | {primary['xi_ch']} / {primary['xi_det']} / {primary['beta']} |
| Receiver/reconciliation | homodyne real1D / asymptotic RR |
| AO/phase noise | OFF/OFF |

Giữ VA=Vmod=2*nbar, X_A=2Re(alpha), nu_repo=42.5*nu_raw. Mỗi nguồn dùng một cặp
C,w không đổi theo góc. Chín context được tính bằng implementation canonical:
moments trên [0,1], atom riêng, deficit chỉ diagnostic, không clip/renormalize PDF.
Mỗi nguồn–góc tính lại effective channel/noise, MI, Holevo và raw K.

```text
eta_f = E[sqrt(eta)]^2
xi_f = ((E[eta]-eta_f)*VA + xi_ch*E[eta] + xi_det*M0)/eta_f
Z = 2*sqrt(eta_f)*C - sqrt(2*eta_f*xi_f*w)
K_raw = beta*I_AB - chi_BE
```

Eq14 và Eq13 dùng nguyên function objects; discrete homodyne MI cùng likelihood
variance 1+eta_f*xi_f. Không Z optimization, endpoint, clipping, spectrum repair,
source interpolation, Gaussian-input MI hoặc đổi PDF/manuscript.

## Kết quả best-tested trên catalog 212 nguồn, bits/use

| Zenith (deg) | Uniform | Fixed MB | Optimized MB trong catalog khả dụng |
|---:|---:|---:|---:|
{chr(10).join(table)}

Optimized MB dương tại các **góc đã lấy mẫu 0,5,10,15°**; không suy ra ngưỡng liên
tục. Best sampled K=0.0007960878080861267 tại0°, VA=1.358333319784304,
nu_raw=0.30. Uniform không có điểm dương trong catalog này. Fixed MB dương
tại0° và5°, giữ đúng VA=1.6249995399703647/nu_raw=0.25, C,w/hash cũ.

**Cả 12 candidate rows dương đều dựa trên INSUFFICIENT_EVIDENCE source.** Đây là
kết quả có điều kiện trên payload lịch sử, không chứng minh accuracy của C,w.
Không thể gọi chênh lệch Uniform/MB là shaping gain cùng VA khi thiếu Uniform
đối chiếu hoặc các nguồn có VA khác nhau.

## Tách nguồn đủ evidence và thiếu evidence

- `strict_source_evidence_results.csv`: 22 nguồn trong miền, 198 hàng, gồm
  6 Uniform direct receipts,1 Uniform alternative và15 MB direct receipts từ
  audit cũ. Không nâng hạng 73 nguồn của pool pilot.
- `incomplete_source_evidence_results.csv`: 190 nguồn,1.710 hàng, gồm Fixed MB.
  Mọi rate giữ source evidence class và diagnostic label.
- `strict_source_evidence_selected.csv`: selection chỉ trong22 nguồn đủ evidence;
  tất cả K được chọn vẫn âm. Fixed MB không có selection strict vì thiếu receipt.

Các nhãn source evidence không biến mô hình kênh thành security-certified model.
Giữ UNVALIDATED_SECURITY_MODEL và NOT_READY_FOR_PUBLICATION_SCALE_RUNS.

## Kiểm chứng và execution history

5 focused reuse tests PASS: identity/coverage không đổi, direct equation function
objects, hai source regression khớp canonical evaluator, gate diagnostic không
đổi class và giữ signed ranking. Thêm2 postprocessing regression tests PASS.
36 kiểm tra độc lập selection đều PASS; trong đó tái dùng27 check pilot và
bổ sung9 check mới. Adaptive-output-density MI so với GH, covariance spectrum
so với Eq13, conditional covariance đều được kiểm tra độc lập.

- Max GH64/128 delta: {max(float(r['MI_GH64_128_difference']) for r in rows(OUT/'diagnostic_results.csv')):.6g} bit/use.
- Max adaptive MI delta: {max(float(r['MI_difference']) for r in independent):.6g} bit/use.
- Max covariance spectrum delta: {max(float(r['covariance_spectrum_difference']) for r in independent):.6g}.
- Có0 candidate với |K|<=1e-8; không cần thay tolerance để xác định dấu.

Các lỗi điều phối được giữ evidence: lần test đầu import nhầm runner lịch sử;
JSON summary gặp NumPy scalar; phần mở rộng đọc K từ CSV còn là string. Đã sửa
import path/serializer/numeric conversion, không đổi công thức hoặc tolerance.
720 kết quả pilot được giữ nguyên. Lần mở rộng đầu đã tính1.188 cặp nhưng lỗi
trước khi lưu; phải tính lại1.188 cặp một lần. Lần sửa lưu candidate table trước
xếp hạng. Không có phép tính C,w nào trong các lần này. `execution_history.json`
phân biệt1.908 cặp duy nhất, các lần tính lặp và4 regression rate calls.

## Strict Phase B và preservation

**PHASE_B_STRICT_READY = FALSE.** Hai dependency cũ vẫn còn: 73 convergence
evidence gaps của nguồn pilot, gồm Fixed MB, và một Uniform thiếu payload/receipt.
SKR dương hoặc numerical PASS không gỡ hai dependency đó. Strict gate cũ không
bị sửa; quyền sử dụng insufficient payloads chỉ áp dụng diagnostic được duyệt.

`artifact_integrity_report.md`, `artifact_manifest.json`, `verification.json`
ghi startup Git/diff, hashes, checks và preservation. Không sửa production,
frozen spec, manuscript, source caches/catalogs hoặc lịch sử đã seal. Không chạy
strict pilot, sweep61, training/test/held-out/publication hay source generation.
**Tổng C,w mới/tái tính: 0.**
'''
    (OUT/'validation_report_vi.md').write_bytes(text.encode('utf-8'))


if __name__=='__main__':main()
