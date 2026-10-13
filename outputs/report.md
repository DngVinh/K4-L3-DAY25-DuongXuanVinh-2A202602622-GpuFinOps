# NimbusAI — GPU Cost Optimization Report

**Period:** monthly

**Baseline spend:** $18,005.62

**Optimized spend:** $10,427.37

**Projected savings:** $7,578.25  (**42%**; precise: 42.09%)

## Savings by lever

| Lever | Savings (USD) |
|---|---|
| Inference (cascade/cache/batch) | $1,211.69 |
| Purchasing (spot/reserved) | $6,366.56 |
| Right-size util-lies | $0.00 |
| Kill idle GPUs | $0.00 |

## Sustainability

- Energy per query (illustrative ordinary query): 0.24 Wh
- Carbon per query (us-east-1, illustrative): 0.091 gCO2e
- Cleanest region: europe-north1
- Cheapest electricity region: us-east-wa

_Figures are June-2026 as-of snapshots; re-baseline before acting._

## Phạm vi, phương pháp và đối soát

Dữ liệu tổng hợp seed=25; snapshot giá tháng 6/2026, không dùng giá thị trường hiện tại. Token log là một ngày (15/06); nhân 30 để mô phỏng tháng có traffic không đổi. Workload tính đúng `hours_per_day × days × num_gpus`, không mặc định mọi job chạy 30 ngày. Reserved trả tiền cả 24 giờ/ngày, kể cả giờ không chạy. Giá 3yr giả định công ty đã có capacity cam kết được dùng chung; job ngắn không đủ cơ sở mua cam kết mới ba năm.

Danh mục workload và API được giả định là hai nhóm chi phí riêng. Cần billing/resource mapping để xác nhận giả định trước khi áp dụng. Training không tạo token phục vụ trong log; chỉ số portfolio/token dưới đây là proxy ngân sách, không phải đơn giá inference thuần.

| Phạm vi | Baseline USD/tháng | Optimized USD/tháng | Baseline $/1M-token | Optimized $/1M-token |
|---|---:|---:|---:|---:|
| API inference, 225,990,810 token/tháng | 1466.22 | 254.54 | 6.488 | 1.126 |
| Portfolio (bao gồm training; proxy) | 18005.62 | 10427.37 | 79.674 | 46.141 |

Telemetry cho thấy cơ hội right-size theo rule cũ $655.20/tháng và idle $600.00/tháng. Hai lever có **$0 được ghi nhận vào tổng** vì không có join key GPU → job, throughput sau đổi GPU, hay trạng thái billing sau mua spot/reserved. Không trừ thêm on-demand savings vào cùng chi phí đã giảm bằng purchasing. Đây là cơ hội kiểm chứng, không phải tiết kiệm cộng thêm đã xác nhận; biểu đồ hiển thị đủ bốn lever.

## M2 — Đóng góp tuần tự từng đòn bẩy

Cùng số request, cùng input/output token. Thứ tự attribution: cascade → cache → batch. Đổi thứ tự có thể đổi đóng góp từng lever, nhưng không đổi tổng cuối.

| Bước | USD/ngày | $/1M-token | Tiết kiệm thêm USD/tháng |
|---|---:|---:|---:|
| Baseline | 48.874161 | 6.488 | 0.00 |
| Cascade | 11.475643 | 1.523 | 1121.96 |
| Cache | 10.279188 | 1.365 | 35.89 |
| Batch | 8.484623 | 1.126 | 53.84 |

Cascade đóng góp lớn nhất trong inference do phần lớn request dùng model nhỏ. Cache chỉ giảm input đã cache; output không được giảm 90%. Batch giảm cả bill 50% nhưng chỉ áp dụng traffic `is_batch=1`. 0.50 × 0.10 = 0.05 chỉ là trường hợp input 100% cache, không phải mọi request được giảm 95%. Chat tương tác không phù hợp batch khi deadline phản hồi không cho phép chờ.

## M1 — GPU-Util lie và tác động tài chính

| GPU | Util % | MFU | MBU | Tiền thuê on-demand USD/tháng |
|---|---:|---:|---:|---:|
| gpu-h100-4 | 98.2 | 0.194 | 0.207 | 1800.00 |
| gpu-a10g-1 | 96.9 | 0.268 | 0.302 | 720.00 |

GPU-Util đo thời gian kernel hoạt động, không đo phần FLOPs đỉnh thực sự khai thác. Memory stalls, thiếu batching hoặc kernel launch overhead có thể gây util cao/MFU thấp; telemetry này chưa chứng minh nguyên nhân cụ thể. Dùng profiler để xác nhận. MFU thấp ở decode có thể là đặc tính memory-bound, không tự động là lãng phí. Prefill tái sử dụng trọng số trên nhiều token nên arithmetic intensity cao; decode ít token/batch phải đọc trọng số liên tục nên thường memory-bound.
Idle: `gpu-h100-5` có 8 giờ/ngày util <10%, $20.00/ngày = $600.00/tháng, 3.90% bill on-demand của fleet telemetry. Không dùng tỷ lệ này làm tỷ lệ idle của toàn portfolio.

## M3 — Purchasing theo từng job

| Job | GPU | Days | GPU-hours | Tier | Baseline USD | Optimized USD |
|---|---|---:|---:|---|---:|---:|
| job-train-llm | H100 | 14 | 2240 | spot | 5600.00 | 3544.80 |
| job-train-embed | A100 | 5 | 200 | spot | 358.00 | 232.10 |
| job-finetune | H100 | 3 | 36 | spot | 90.00 | 56.97 |
| job-infer-chat | A10G | 30 | 4320 | reserved | 4320.00 | 2592.00 |
| job-infer-rag | A100 | 30 | 2160 | reserved | 3866.40 | 2160.00 |
| job-infer-search | L4 | 30 | 2160 | reserved | 1728.00 | 1296.00 |
| job-dev-sandbox | A10G | 22 | 352 | spot | 352.00 | 148.54 |
| job-batch-eval | H100 | 30 | 90 | spot | 225.00 | 142.43 |

M3: $16,539.40 → $10,172.84, giảm 38.5%. Spot có overhead 3% + 0.05 interruption/GPU-hour × 0.5 giờ rework, tức effective hours = 1.055 × useful hours. Đây là kỳ vọng đơn giản, không mô phỏng correlation khi nhiều GPU của cùng job bị thu hồi. Điểm hòa vốn reserved bằng giá reserved/on-demand; policy 55% là xấp xỉ. Job search 18h/ngày phải trả reserved 24h/ngày. Job ngắn dùng spot/on-demand hoặc capacity reserved có sẵn, không ký hợp đồng ba năm chỉ dựa trên một tháng.

## M4 — Showback, chargeback và FOCUS-style export

| Team | USD/ngày | Tỷ lệ bill API |
|---|---:|---:|
| assistant | 2.592175 | 30.55% |
| search | 2.493312 | 29.39% |
| eval | 1.794565 | 21.15% |
| rag | 1.604571 | 18.91% |

Tag coverage team+project = 91.79%; chargeback gate ≥80%: **True**. Xuất đủ 2400 request, tổng BilledCost ≈ $8.484623/ngày, đối soát M2 (sai số làm tròn tối đa 0.000012 USD với 2,400 dòng). Dòng thiếu project vẫn được giữ; yêu cầu owner bổ sung và chưa phân bổ cưỡng ép khoản chưa rõ. Chuẩn hóa cột chi phí giúp so sánh nhiều provider. Export là schema FOCUS-style tối giản của lab, chưa khẳng định tuân thủ toàn bộ FOCUS 1.x.

## Extension 2 — Right-sizing theo MBU, VRAM và bandwidth

Sàng lọc inference MBU <0.60; candidate cần VRAM ≥ max(mem)/0.90, bandwidth ≥ max(achieved BW)/0.80 và compute ≥ max(achieved TFLOPs)/0.80. Chọn candidate rẻ nhất chỉ sau khi vượt các điều kiện; MBU thấp không đủ để kết luận memory-bound.

| GPU | Hiện tại → đề xuất | MBU | GB cần | TB/s cần | Peak BW cũ → mới | $/GB-VRAM-hour cũ → mới | USD/tháng giảm |
|---|---|---:|---:|---:|---|---|---:|
| gpu-a100-0 | A100 → A100 | 0.276 | 75.22 | 0.884 | 2.00 → 2.00 | 0.02237 → 0.02237 | 0.00 |
| gpu-a100-1 | A100 → A100 | 0.247 | 74.44 | 0.846 | 2.00 → 2.00 | 0.02237 → 0.02237 | 0.00 |
| gpu-a10g-0 | A10G → L4 | 0.235 | 22.56 | 0.227 | 0.60 → 0.30 | 0.04167 → 0.03333 | 144.00 |
| gpu-a10g-1 | A10G → L4 | 0.302 | 22.67 | 0.265 | 0.60 → 0.30 | 0.04167 → 0.03333 | 144.00 |

Tổng cơ hội right-size inference: **$288.00/tháng** theo on-demand 24×30. A100 không chuyển L4 vì bộ nhớ không đủ; MI300X có $/GB tốt nhưng bill/giờ cao hơn A100. Hai A10G chuyển L4 giảm 20% bill/giờ, đủ bandwidth đo được với headroom. Benchmark p95 latency, throughput, model fit/KV-cache và phần mềm trước khi thực hiện. Không cộng $288 vào lever util-lies: `gpu-a10g-1` đã nằm trong cả hai cách sàng lọc.

## Extension 4 — Ngân sách reasoning

| Traffic | Request | USD/ngày sau M2 | Wh/ngày |
|---|---:|---:|---:|
| Ordinary | 2199 | 7.088159 | 1887.56 |
| Reasoning | 201 | 1.396464 | 29787.74 |

Reasoning chiếm **8.38% traffic**, **16.46% chi phí API**, **94.04% năng lượng**. Energy model của lab dùng 80× cho cùng số token; dataset còn nhân output reasoning 6× nên không diễn giải toàn bộ chênh lệch là do phần cứng. Không có phụ phí reasoning riêng trong giá API: chi phí tăng qua output token.
Trần **10%**: đổi 0 request, tiết kiệm $0.00 và 0.00 Wh/ngày; chưa binding. Trần **5%**: chuyển kỳ vọng 81 request/ngày sang ordinary, tiết kiệm **$0.414247/ngày ($12.43/tháng)** và **11932.44 Wh/ngày (357.97 kWh/tháng)**.
Routing đề xuất: chỉ cho reasoning khi classifier xác định task cần suy luận nhiều bước và confidence model thường <0.80; gate này là đề xuất vì CSV không có complexity/confidence. Ưu tiên queue eval khó, quota 10% requests/ngày, budget USD và Wh riêng; thử A/B trần 5% và yêu cầu accuracy giảm không quá 1 điểm phần trăm. Counterfactual giữ input, model, cache, batch; giảm output/6 và bỏ multiplier 80×. Đây là mô phỏng chuyển request, không chứng minh chất lượng tương đương; không cộng vào M5.

## Extension 5 — Carbon-aware regional scheduling

Chỉ lấy job training interruptible, đúng số ngày, năng lượng = GPU-hours × TDP. Đây là estimate công suất danh định, không phải điện đo bằng power_w, chưa gồm PUE hay spot rework. CSV không có carbon theo giờ nên chỉ tối ưu vùng, chưa tối ưu giờ.

| Region | USD/kWh | gCO2e/kWh | USD điện | kgCO2e |
|---|---:|---:|---:|---:|
| us-east-1 | 0.120 | 380 | 200.784 | 635.816 |
| us-west-2 | 0.070 | 120 | 117.124 | 200.784 |
| europe-north1 | 0.090 | 30 | 150.588 | 50.196 |
| europe-central2 | 0.180 | 660 | 301.176 | 1104.312 |
| us-east-wa | 0.055 | 90 | 92.026 | 150.588 |

| Job | kWh | us-east-1 kgCO2e | europe-north1 kgCO2e |
|---|---:|---:|---:|
| job-train-llm | 1568.00 | 595.840 | 47.040 |
| job-train-embed | 80.00 | 30.400 | 2.400 |
| job-finetune | 25.20 | 9.576 | 0.756 |

Tổng 1,673.20 kWh. Chuyển us-east-1 → europe-north1 giảm **585.620 kgCO2e (92.11%)** và **$50.196** tiền điện. Rẻ nhất: **us-east-wa**; sạch nhất: **europe-north1**; cân bằng theo policy minimize điện với carbon ≤100 g/kWh: **us-east-wa**. So với vùng sạch nhất, us-east-wa rẻ hơn nhưng carbon cao hơn; không có một vùng đồng thời đạt cả hai minimum. Chi phí điện thường đã nằm trong GPU rent, không cộng savings điện vào bill thuê để tránh đếm hai lần. Training có thể di chuyển dễ hơn inference; cân nhắc latency tới users, data residency, egress, thời gian chuyển checkpoint và giá/availability GPU theo vùng.
Traffic thực tế trung bình **13.198 Wh/request**, khác minh họa 800-token ordinary 0.24 Wh ở phần Sustainability. Carbon minh họa = Wh/1000 × 380 g/kWh; không áp dụng một query minh họa cho toàn bộ reasoning traffic.

## Hành động ưu tiên và điều kiện nghiệm thu

1. Áp dụng showback + budget trước, kiểm tra purchasing: spot cho training checkpointable và capacity reserved sẵn có cho inference ổn định. Purchasing đóng góp lớn nhất trong portfolio; xác nhận lịch job, interruption, cam kết dài hạn và owner thiếu tag.
2. Triển khai cascade → cache → batch cho traffic đúng điều kiện; theo dõi $/1M-token, accuracy và p95 latency. Benchmark các GPU bị lie, lịch idle, thử A10G → L4; chỉ ghi nhận savings bổ sung khi đối soát resource mapping và đơn giá cuối.
3. Quota reasoning và job training chọn vùng: A/B trần 5%, đo Wh, dùng europe-north1 nếu carbon ưu tiên hoặc us-east-wa nếu cost với carbon constraint ưu tiên. Nghiệm thu khi quality/SLO đạt và billing chứng minh savings, không chỉ GPU-Util giảm.

## Tái lập và tiêu chí chấm điểm

Chạy từ repo root (Windows):

```powershell
.\.venv\Scripts\python.exe missions/run_all.py
.\.venv\Scripts\python.exe verify.py
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe validation/check_extensions.py
```

A: verify 11/11 (30 điểm). B: 15 tests gốc, giữ nguyên tests/ (20 điểm). C: báo cáo, waterfall bốn lever, baseline/optimized và sustainability (30 điểm). D: ba extension có code, so sánh và số liệu; tối đa 20 điểm do giảng viên đánh giá. Nộp report.md, savings.png, focus_export.csv và writeup.md. Bonus không chấm điểm; không cần GPU, API key hay cloud account.
