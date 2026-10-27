# Uniform còn thiếu — tìm kiếm exact historical identity

Nguồn yêu cầu:

```text
family = Uniform
nu_raw = 0
nu_repo = 0
VA = 1.6249995399703647
VA_hex = 0x1.9ffff84830112p+0
expected_ensemble_hash = 421664627da51107f1420322c7992ba5f12d9bd6af0ff767a473b8b93ffd00d7
```

## Phạm vi tìm và kết quả

Đọc toàn bộ 238 exact cache payloads, 245 catalog/bảng nguồn, catalog Uniform JSON
và numerical provenance đã lưu. Trong 235 canonical source identities tương
thích không có Uniform với đồng thời đúng nu_raw hex, VA hex và ensemble hash.
`missing_uniform_search.json` giữ điều kiện tìm và kết quả **0 exact matches**.

Đối chiếu thêm forensic evidence đã seal tại
`../skr_vs_zenith_eq14_v43_phaseB_unblocking_20261024/`: 2.826 Git text blobs,
7 archive, execution logs và search exact source/array digests trước đó cũng
không phục hồi payload của nguồn này. Không chạy lại toàn bộ forensic search
hoặc exact-source calculation khi index và hashes hiện có vẫn hợp lệ.

Preflight/request và bản ghi timeout có đúng VA/hash nhưng **không có C,w**;
không được coi chúng là source result. Fixed MB cùng VA nhưng nu_raw=0.25 có
PMF và ensemble hash khác; C,w của Fixed MB không dùng cho Uniform.
VA=1.625 cũng không có cùng binary64 identity với VA yêu cầu.

Canonicalization giữ nguyên: helper hiện hành chỉ cho phép chứng minh alias
LF/CRLF của implementation. Không đổi amplitudes, PMF, ordering, source formulas,
VA/nu hoặc precision settings để tạo ra một match.

## Các phép so sánh bị ảnh hưởng

1. Không đánh giá được **9 ô** của chính Uniform này trong ma trận 81×9.
2. Không có Uniform đối chiếu **cùng VA** với Fixed MB, do đó chưa thể gọi chênh
   lệch hai scheme là shaping gain cùng năng lượng ở VA này.
3. Search Uniform có 33/34 candidate dự kiến. Search MB mở rộng có 80/81 nguồn;
   nguồn Uniform thiếu cũng là candidate nu=0 của search MB.
4. Không thể tuyên bố best-tested trên pool 81 đầy đủ hoặc strict pilot hoàn tất.

Fixed MB, 47 nguồn MB và 33 Uniform còn lại của pool pilot vẫn có C,w tương thích
để chạy diagnostic ở cả chín góc. Chẩn đoán catalog rộng hơn dùng 212 nguồn hiện
có trong cùng miền đã duyệt, cũng không có Uniform bị thiếu. Pool mỗi bảng được
khóa chung, không thay theo góc.
Best-tested từ pool này được ghi nhãn restricted catalog, không lấp nguồn thiếu.

## Không thực hiện

Không nội suy, không thế VA lân cận, không đổi Uniform constellation, không dùng
MB moments, không tạo C,w mới và không chạy lại job 3.600 s. Giá trị C,w của nguồn
thiếu để trống; strict evidence classification và readiness vẫn giữ nguyên.
