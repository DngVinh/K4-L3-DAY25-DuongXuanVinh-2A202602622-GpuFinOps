# Bài phân tích Lab 25 — GPU FinOps

**Sinh viên:** Dương Xuân Vinh · **MSSV:** 2A202602622 · **Lớp:** K4-L3
**Dữ liệu:** mô phỏng seed=25, giá snapshot tháng 6/2026.

## 1. Baseline và optimized

Portfolio mô phỏng giảm từ **$18,005.62** xuống **$10,427.37/tháng**, tiết kiệm
**$7,578.25 (42.09%)**. API inference riêng giảm từ
**$1466.22** xuống **$254.54/tháng**;
**$6.488 → $1.126/1M-token**, giảm **82.6%**.
Mẫu có 7,533,027 input+output token/ngày. Portfolio gồm training nên
không dùng portfolio/token làm đơn giá inference. Workloads tính đúng ngày hoạt động;
reserved trả cả giờ không chạy, giả định dùng commitment có sẵn. API và GPU workload
được coi là hai nhóm chi phí riêng, cần billing mapping xác nhận khi triển khai thực tế.

## 2. Đóng góp từng đòn bẩy

Purchasing đóng góp **$6,366.56/tháng**, lớn nhất
trong portfolio. Trong inference, cascade giảm
**$1121.96/tháng**, cache giảm thêm
**$35.89**, batch giảm thêm
**$53.84**. Cascade thắng vì phần lớn request
đủ dùng model nhỏ; cần kiểm chứng quality. Cache giảm input được cache, batch chỉ cho
job không cần phản hồi tức thì. Đóng góp là attribution tuần tự, không độc lập.

Telemetry có cơ hội idle **$600.00/tháng** và right-size util-lies;
hai khoản được ghi **$0 bổ sung** trong tổng vì không có GPU→job mapping và có thể trùng
với purchasing. Cách này tránh trừ giá on-demand một lần nữa trên chi phí spot/reserved.

## 3. GPU-Util lie

`gpu-h100-4` có GPU-Util **98.2%** nhưng MFU **0.194**; `gpu-a10g-1` có **96.9%** và **0.268**.
Util là thời gian kernel hoạt động; memory stalls hoặc overhead có thể khiến GPU bận
nhưng không khai thác peak FLOPs. Đây là giả thuyết cần profiler, không phải nguyên nhân
đã chứng minh. H100 bị lie có bill on-demand **$1,800/tháng**; MFU thấp không có nghĩa toàn
bộ phần chưa đạt peak đều có thể thu hồi thành tiền. Decode thường memory-bound, nên
cần MBU, VRAM, throughput và latency trước khi đổi GPU.

## 4. Ba phần mở rộng và insight

**Right-sizing MBU:** kiểm tra max VRAM với 10% dự phòng, bandwidth/compute với 20%
headroom. Hai A10G có thể thử L4, giảm 20% bill/giờ và tổng **$288/tháng** theo on-demand
24×30. Hai A100 giữ nguyên vì L4 thiếu VRAM; MI300X có $/GB thấp nhưng đắt hơn theo giờ.
Đó là lý do không chọn GPU chỉ theo giá giờ hay chỉ theo $/GB. Cơ hội cần benchmark
SLO và không cộng vào ledger khi chưa đối soát.

**Reasoning budget:** 201 request reasoning,
**8.38% traffic**, chi phí **$1.396464/ngày**
và **29787.74 Wh/ngày**. Trần 10% chưa binding nên savings bằng 0.
Kịch bản trần 5% chuyển kỳ vọng 81 request sang ordinary, giảm
**$12.43/tháng** và **357.97 kWh/tháng**.
Counterfactual giảm output/6 theo generator và bỏ energy multiplier 80×, chưa chứng minh
accuracy. Chỉ dùng reasoning cho task nhiều bước khi confidence <0.80, theo dõi quota,
USD/Wh và A/B quality; CSV không có confidence nên rule chưa replay được.

**Carbon scheduling:** ba training job interruptible có **1,673.20 kWh**
theo GPU TDP × giờ hoạt động. us-east-1 → europe-north1 giảm
**585.620 kgCO2e (92.11%)**, điện giảm
**$50.196**. Sạch nhất là europe-north1;
rẻ nhất là us-east-wa. Nếu policy carbon ≤100 g/kWh và ưu tiên tiền điện, chọn us-east-wa.
CSV không có hourly carbon; đây là chọn vùng, chưa tối ưu giờ. TDP chưa gồm PUE/rework;
điện thường nằm trong rent nên không cộng thêm savings điện vào bill thuê.

## 5. Ba hành động đầu tiên cho NimbusAI

1. Đối soát billing theo owner, showback và budget; coverage **91.79%**
   vượt gate 80% nhưng cần xử lý project còn thiếu. Dùng spot/checkpoint cho training,
   reserved có sẵn cho inference đều; không mua commitment mới cho job ngắn.
2. Triển khai cascade/cache/batch với quality và latency gate; profiler GPU bị lie,
   benchmark A10G→L4 và lịch idle. Chỉ ghi nhận tiền giảm sau resource-level reconciliation.
3. Quota reasoning, thử cap 5% với accuracy giảm ≤1 điểm phần trăm; chuyển training
   sang vùng phù hợp mục tiêu cost/carbon, kiểm tra data residency, egress và availability.

Chi tiết bảng, giả định và lệnh tái lập nằm trong `report.md`; `savings.png` thể hiện
waterfall đủ bốn lever, `focus_export.csv` giữ đủ 2,400 request để đối soát chi phí.
