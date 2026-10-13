# Đối chiếu yêu cầu Lab 25

Nguồn đã đọc: README.md, README_en.md, CODELAB.md, Guide.md, Rubric.md,
ba README bonus, engine finops/, năm missions, generator, verify.py và tests gốc.
Slide `day25-gpu-finops-cost-optimization` được tài liệu nhắc tới nhưng không có
trong workspace; không suy diễn thêm yêu cầu hoặc số liệu từ slide chưa cung cấp.

| Hạng mục | Tiêu chí | Bằng chứng |
|---|---|---|
| A — 30 điểm | verify.py đạt 11/11 | Chạy verify.py; kết quả validation/results.txt |
| B — 20 điểm | 15 tests gốc pass, không sửa tests/ | pytest -q; Git diff tests/ rỗng |
| C.1 — 15 điểm | Baseline/optimized/% savings; lever; sustainability | report.md: tổng chi phí, M2 tuần tự, bảng vùng |
| C.2 — 10 điểm | Giải thích GPU-Util lie; hành động ưu tiên; cost-carbon | report.md: M1, carbon scheduling, hành động ưu tiên |
| C.3 — 5 điểm | PNG đọc được, số liệu khớp missions | savings.png: waterfall bốn lever; số liệu sinh từ pipeline |
| D — tối đa 20 điểm | ≥2 extensions có code, trước/sau, insight | Ba extension 2/4/5 trong finops/extensions.py; report.md |
| Extension 2 | VRAM, peak bandwidth, $/GB và monthly savings | A10G→L4, A100 giữ nguyên; thêm compute/headroom |
| Extension 4 | Tách USD/Wh và traffic share, cap 10% | Cap 10% không binding; thêm sensitivity 5% |
| Extension 5 | Đủ 5 vùng, cost/carbon, trade-off | Tính ngày thực tế cho training; rẻ/sạch/cân bằng rõ ràng |
| Write-up | 1–2 trang tương đương Markdown, đủ năm câu hỏi | writeup.md |
| Bộ nộp | report.md, savings.png, focus_export.csv, write-up | Đủ bốn file trong outputs/ |

## Quy tắc thực hiện

- Không sửa tests/ hoặc verify.py, không hardcode kết quả để pass.
- Giữ nguyên dữ liệu seed=25; không dùng GPU/cloud/API key cho đường chấm điểm.
- Giá và carbon là snapshot minh họa, không phải báo giá hiện tại.
- Đơn vị chính là USD/1M input+output token; tách portfolio proxy khỏi inference.
- Reserved tính cả giờ nhàn rỗi; job dùng đúng cột days.
- Không cộng savings trùng resource hoặc trừ điện lần hai khỏi tiền thuê GPU.
- Các cơ hội right-size/idle chưa có mapping được ghi rõ conditional, không tính
  thêm vào tổng. Vẫn hiển thị bốn lever và số tiền cơ hội trong báo cáo.
- Bonus không chấm điểm; không tuyên bố đã chạy GPU model hoặc Docker khi chưa chạy.
- Điểm nội dung C/D do giảng viên quyết định; bảng này không tự xác nhận điểm 100.

## Tái lập

```powershell
.\.venv\Scripts\python.exe missions/run_all.py
.\.venv\Scripts\python.exe verify.py
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe validation/check_extensions.py
```

Các check bổ sung đặt ở validation/ để giữ nguyên toàn bộ tests của giảng viên.
