# Bộ tám hình so sánh P1–P2–P3

UNVALIDATED_SECURITY_MODEL; NOT_READY_FOR_PUBLICATION_SCALE_RUNS.

Chỉ hậu xử lý 100 mission × 10 λ đã lưu; không chạy lại vật lý, SKR, nguồn, mây hoặc thuật toán tối ưu. PDF vector và PNG 350 dpi, khổ đôi 7,2 inch.

| Hình | Nội dung | PDF | PNG |
|---|---|---|---|
| 1 | SKR trung bình theo λ | [PDF](fig1_average_skr_vs_lambda.pdf) | [PNG](fig1_average_skr_vs_lambda.png) |
| 2 | Objective theo λ | [PDF](fig2_objective_vs_lambda.pdf) | [PNG](fig2_objective_vs_lambda.png) |
| 3 | Quãng đường theo λ | [PDF](fig3_travel_distance_vs_lambda.pdf) | [PNG](fig3_travel_distance_vs_lambda.png) |
| 4 | Gain objective theo cặp | [PDF](fig4_dp_objective_gain_vs_lambda.pdf) | [PNG](fig4_dp_objective_gain_vs_lambda.png) |
| 5 | Tradeoff SKR–quãng đường | [PDF](fig5_skr_vs_travel_distance.pdf) | [PNG](fig5_skr_vs_travel_distance.png) |
| 6 | SKR theo slot | [PDF](fig6_per_slot_skr_comparison.pdf) | [PNG](fig6_per_slot_skr_comparison.png) |
| 7 | Cộng dồn SKR | [PDF](fig7_cumulative_skr_vs_time.pdf) | [PNG](fig7_cumulative_skr_vs_time.png) |
| 8 | P1 raw Uniform–MB | [PDF](fig8_uniform_vs_mb_positions.pdf) | [PNG](fig8_uniform_vs_mb_positions.png) |

## Tám câu hỏi nghiên cứu

1. **DP có SKR cao hơn?** Mean DP ≥ hai mean baseline ở cả 10 λ trong dữ liệu này. Tại λ=9.468026677248516e-06, meanK tăng 4.16162% so với P2 và 2.69538% so với Greedy. Đây không phải bảo đảm cho từng mission: tại λ này, DP có unpenalized K thấp hơn Greedy ở 25/100 mission.
2. **DP có objective cao nhất?** Không vi phạm U_DP≥U_P2,U_Greedy trong 1.000 mission–λ, dung sai 1e−12. Tại λ đại diện, meanU tăng 3.07498%/4.41766%; thắng nghiêm ngặt 61/100 và 89/100 mission.
3. **Quãng đường đổi thế nào?** DP D không tăng theo λ trong từng mission. MeanD DP từ 1482,687834m tại λ=0 về 0 ở 0,1λhi. Greedy có 31 lần tăng D giữa λ kề nhau trên 25 mission; không ép đơn điệu.
4. **Khi nào mobility bớt có lợi?** Ở 0,03λhi vẫn còn 7 mission DP di chuyển; ở 0,1λhi tất cả DP đứng yên và hòa P2. Chỉ suy ra khoảng chuyển tiếp giữa các điểm đã thử, không suy ra ngưỡng λ liên tục. Greedy dừng sớm hơn ở 0,03λhi nhưng không trở thành P2.
5. **Đổi quãng đường lấy SKR thế nào?** DP tại 0,0001λhi giữ 99,953824% meanK của λ=0, giảm 64,026687% meanD. Tại 0,003λhi: DP đi 172,432990m so với Greedy 430,610183m, đồng thời có meanK cao hơn. Đây là các chính sách đã thử, không phải Pareto frontier vật lý.
6. **Từng mission có gì khác?** Hình6–7 dùng mission84, chọn hậu nghiệm với DP strict thắng cả hai baseline. P2 bị chặn 4 slot; Greedy/DP tránh được blockage trên đường đã chọn. DP đổi điểm 5 lần/847,213595m, Greedy 7 lần/1088,634952m. Cumulative sum là tổng các giá trị SKR theo slot, chưa phải số bit khóa vật lý.
7. **MB tốt hơn Uniform?** Raw MB dương và raw Uniform tối ưu âm ở cả 100 vị trí. MB chọn (ν,VA)=(0,125;8), tại biên VA catalog. Mỗi họ tối ưu VA riêng; không phải shaping gain ở cùng năng lượng, không chia phần trăm cho Uniform âm/usable0.
8. **Hình nào mạnh nhất?** Ưu tiên 2,4,5,8: mục tiêu P3 trực tiếp; chênh lệch objective theo cặp và CI; tradeoff K–D; kết quả nguồn P1. Hình1/3 bổ sung nhưng trùng phần thông tin hình5; hình6/7 giải thích cơ chế bằng một ví dụ hậu nghiệm. Tám hình không có Fixed44 nên không tự chứng minh lợi ích chọn vị trí P2 so với một điểm cố định không tối ưu.

## Thống kê và giới hạn

Phần trăm dùng 100×(meanDP−meanBaseline)/meanBaseline trên cùng100 mission, không lấy mean phần trăm từng mission. Mean/SD mẫu/median và CI Student-t được đối chiếu lại; CI bootstrap cho chênh lệch theo cặp tái sử dụng artifact đã xác thực (20.000 whole-mission resamples, seed20261019), là pointwise CI chưa hiệu chỉnh nhiều so sánh. Hình1 dùng trục gồm0 nên chênh vài phần trăm khó nhìn; hình4 biểu diễn độ lớn chênh rõ hơn.
λ được yêu cầu ở dạng làm tròn 9.46803e-06 không tồn tại chính xác trong schedule. Dùng λ đại diện đã lưu 9.468026677248516e-06; chênh lệch làm tròn 3.32275148422e-12 bits/use. Không tạo λ mới.
P2/DP là benchmark offline; Greedy đọc trạng thái slot hiện tại. Mây và hình học tổng hợp; catalog/lưới hữu hạn; distance chưa hiệu chuẩn thành năng lượng; mô hình MI2D/Holevo homodyne chưa được xác thực an toàn lượng tử. Frozen-hash discrepancy và Objective C USER_STOPPED được giữ nguyên. Không final-test/held-out, không nâng lifecycle, không sửa bản thảo ngoài repo, không commit/push.

## Dữ liệu và kiểm chứng

[Inventory](data_inventory.md) · [Mean/SD/median/CI](figure_data_summary.csv) · [Paired gains](paired_improvements.csv) · [Source map](figure_source_mapping.csv) · [Captions tiếng Anh](figure_captions_en.md) · [Giải thích từng hình](figure_interpretation_vi.md) · [Validation](figure_validation.md) · [Receipt](validation_receipt.json)

Tái kiểm tra bằng Python môi trường dự án: `python -X utf8 -B verify_figures.py` tại thư mục này. Renderer từ chối ghi đè khi đã có receipt hoàn tất.
