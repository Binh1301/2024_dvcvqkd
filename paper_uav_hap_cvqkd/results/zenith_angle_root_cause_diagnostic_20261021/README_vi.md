# Zenith-angle root-cause diagnostic

Đọc [report_vi.md](report_vi.md), [validation_report.md](validation_report.md)
và [captions](figure_captions_en.md). Ưu tiên Fig. F (MI–Holevo–K), D (moment),
E (noise), G (nguồn); I/J là đối chứng cơ chế. PDF vector + PNG 350 dpi.

Dữ liệu gốc được giữ nguyên. Có 78 phép tính fixed-source canonical có giới hạn
(cộng 3 lời gọi trùng trước lỗi assert đã xử lý; xem execution_history.json);
không optimization, không C,w mới, không mobility simulation. Script renderer
chỉ đọc CSV. Dùng verify_results.py để kiểm tra chỉ đọc; không chạy lại producer
đã hoàn tất. UNVALIDATED_SECURITY_MODEL; NOT_READY_FOR_PUBLICATION_SCALE_RUNS.
