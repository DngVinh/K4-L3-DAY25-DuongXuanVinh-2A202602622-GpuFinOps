"""Generate the graded narrative from mission results, without copied figures."""
from finops import pricing
from missions._common import catalog_by_type


def technical_sections(r1, r2, r3, r4, baseline, optimized, potential_rightsize, potential_idle):
    tokens = r2["total_tokens"]
    lines = [
        "", "", "## Phạm vi, phương pháp và đối soát", "",
        "Dữ liệu tổng hợp seed=25; snapshot giá tháng 6/2026, không dùng giá thị trường hiện tại. "
        "Token log là một ngày (15/06); nhân 30 để mô phỏng tháng có traffic không đổi. "
        "Workload tính đúng `hours_per_day × days × num_gpus`, không mặc định mọi job chạy 30 ngày. "
        "Reserved trả tiền cả 24 giờ/ngày, kể cả giờ không chạy. Giá 3yr giả định công ty đã có "
        "capacity cam kết được dùng chung; job ngắn không đủ cơ sở mua cam kết mới ba năm.",
        "",
        "Danh mục workload và API được giả định là hai nhóm chi phí riêng. Cần billing/resource mapping "
        "để xác nhận giả định trước khi áp dụng. Training không tạo token phục vụ trong log; "
        "chỉ số portfolio/token dưới đây là proxy ngân sách, không phải đơn giá inference thuần.",
        "",
        "| Phạm vi | Baseline USD/tháng | Optimized USD/tháng | Baseline $/1M-token | Optimized $/1M-token |",
        "|---|---:|---:|---:|---:|",
        f"| API inference, {tokens*30:,} token/tháng | {r2['baseline_exact']*30:.2f} | {r2['optimized_exact']*30:.2f} | {r2['baseline_per_m']:.3f} | {r2['optimized_per_m']:.3f} |",
        f"| Portfolio (bao gồm training; proxy) | {baseline:.2f} | {optimized:.2f} | {pricing.dollars_per_million(baseline,tokens*30):.3f} | {pricing.dollars_per_million(optimized,tokens*30):.3f} |",
        "",
        f"Telemetry cho thấy cơ hội right-size theo rule cũ ${potential_rightsize:,.2f}/tháng "
        f"và idle ${potential_idle:,.2f}/tháng. Hai lever có **$0 được ghi nhận vào tổng** vì không có "
        "join key GPU → job, throughput sau đổi GPU, hay trạng thái billing sau mua spot/reserved. "
        "Không trừ thêm on-demand savings vào cùng chi phí đã giảm bằng purchasing. "
        "Đây là cơ hội kiểm chứng, không phải tiết kiệm cộng thêm đã xác nhận; biểu đồ hiển thị đủ bốn lever.",
        "", "## M2 — Đóng góp tuần tự từng đòn bẩy", "",
        "Cùng số request, cùng input/output token. Thứ tự attribution: cascade → cache → batch. "
        "Đổi thứ tự có thể đổi đóng góp từng lever, nhưng không đổi tổng cuối.", "",
        "| Bước | USD/ngày | $/1M-token | Tiết kiệm thêm USD/tháng |",
        "|---|---:|---:|---:|",
    ]
    previous = None
    for name, amount in r2["stages"].items():
        delta = 0 if previous is None else (previous-amount)*30
        lines.append(f"| {name} | {amount:.6f} | {pricing.dollars_per_million(amount,tokens):.3f} | {delta:.2f} |")
        previous = amount
    lines += ["", "Cascade đóng góp lớn nhất trong inference do phần lớn request dùng model nhỏ. "
              "Cache chỉ giảm input đã cache; output không được giảm 90%. Batch giảm cả bill 50% "
              "nhưng chỉ áp dụng traffic `is_batch=1`. 0.50 × 0.10 = 0.05 chỉ là trường hợp input "
              "100% cache, không phải mọi request được giảm 95%. Chat tương tác không phù hợp batch "
              "khi deadline phản hồi không cho phép chờ.",
              "", "## M1 — GPU-Util lie và tác động tài chính", "",
              "| GPU | Util % | MFU | MBU | Tiền thuê on-demand USD/tháng |",
              "|---|---:|---:|---:|---:|"]
    cat = catalog_by_type()
    for r in r1["lies"]:
        lines.append(f"| {r['gpu_id']} | {r['gpu_util_pct']:.1f} | {r['mfu']:.3f} | {r['mbu']:.3f} | {float(cat[r['gpu_type']]['on_demand_hr'])*720:.2f} |")
    fleet_daily = sum(float(cat[r["gpu_type"]]["on_demand_hr"])*24 for r in r1["summary"])
    lines += ["", "GPU-Util đo thời gian kernel hoạt động, không đo phần FLOPs đỉnh thực sự khai thác. "
              "Memory stalls, thiếu batching hoặc kernel launch overhead có thể gây util cao/MFU thấp; "
              "telemetry này chưa chứng minh nguyên nhân cụ thể. Dùng profiler để xác nhận. "
              "MFU thấp ở decode có thể là đặc tính memory-bound, không tự động là lãng phí. "
              "Prefill tái sử dụng trọng số trên nhiều token nên arithmetic intensity cao; decode "
              "ít token/batch phải đọc trọng số liên tục nên thường memory-bound.",
              f"Idle: `gpu-h100-5` có 8 giờ/ngày util <10%, ${r1['idle_waste_daily']:.2f}/ngày "
              f"= ${potential_idle:.2f}/tháng, {r1['idle_waste_daily']/fleet_daily:.2%} bill "
              "on-demand của fleet telemetry. Không dùng tỷ lệ này làm tỷ lệ idle của toàn portfolio.",
              "", "## M3 — Purchasing theo từng job", "",
              "| Job | GPU | Days | GPU-hours | Tier | Baseline USD | Optimized USD |",
              "|---|---|---:|---:|---|---:|---:|"]
    for r in r3["recommendations"]:
        lines.append(f"| {r['job_id']} | {r['gpu_type']} | {r['days']:.0f} | {r['gpu_hours']:.0f} | {r['tier']} | {r['on_demand']:.2f} | {r['optimized']:.2f} |")
    lines += ["", f"M3: ${r3['on_demand_monthly']:,.2f} → ${r3['optimized_monthly']:,.2f}, "
              f"giảm {r3['savings_pct']:.1f}%. Spot có overhead 3% + 0.05 interruption/GPU-hour × "
              "0.5 giờ rework, tức effective hours = 1.055 × useful hours. Đây là kỳ vọng đơn giản, "
              "không mô phỏng correlation khi nhiều GPU của cùng job bị thu hồi. Điểm hòa vốn "
              "reserved bằng giá reserved/on-demand; policy 55% là xấp xỉ. Job search 18h/ngày "
              "phải trả reserved 24h/ngày. Job ngắn dùng spot/on-demand hoặc capacity reserved có sẵn, "
              "không ký hợp đồng ba năm chỉ dựa trên một tháng.",
              "", "## M4 — Showback, chargeback và FOCUS-style export", "",
              "| Team | USD/ngày | Tỷ lệ bill API |", "|---|---:|---:|"]
    for team, amount in sorted(r4["by_team_exact"].items(), key=lambda x:-x[1]):
        lines.append(f"| {team} | {amount:.6f} | {amount/r4['total_exact']:.2%} |")
    lines += ["", f"Tag coverage team+project = {r4['tag_coverage_exact']:.2%}; "
              f"chargeback gate ≥80%: **{r4['chargeback_ready']}**. Xuất đủ {r4['export_rows']} request, "
              f"tổng BilledCost ≈ ${r4['total_exact']:.6f}/ngày, đối soát M2 (sai số làm tròn tối đa "
              "0.000012 USD với 2,400 dòng). Dòng thiếu project vẫn được giữ; yêu cầu owner bổ sung "
              "và chưa phân bổ cưỡng ép khoản chưa rõ. Chuẩn hóa cột chi phí giúp so sánh nhiều provider. "
              "Export là schema FOCUS-style tối giản của lab, chưa khẳng định tuân thủ toàn bộ FOCUS 1.x.",
              "", "## Extension 2 — Right-sizing theo MBU, VRAM và bandwidth", "",
              "Sàng lọc inference MBU <0.60; candidate cần VRAM ≥ max(mem)/0.90, bandwidth ≥ "
              "max(achieved BW)/0.80 và compute ≥ max(achieved TFLOPs)/0.80. Chọn candidate rẻ nhất "
              "chỉ sau khi vượt các điều kiện; MBU thấp không đủ để kết luận memory-bound.", "",
              "| GPU | Hiện tại → đề xuất | MBU | GB cần | TB/s cần | Peak BW cũ → mới | $/GB-VRAM-hour cũ → mới | USD/tháng giảm |",
              "|---|---|---:|---:|---:|---|---|---:|"]
    for r in r1["rightsize"]:
        lines.append(f"| {r['gpu_id']} | {r['current']} → {r['target']} | {r['mbu']:.3f} | {r['required_gb']:.2f} | {r['required_bw']:.3f} | {r['current_bw']:.2f} → {r['target_bw']:.2f} | {r['current_usd_gb']:.5f} → {r['target_usd_gb']:.5f} | {r['savings_monthly']:.2f} |")
    rs = sum(r["savings_monthly"] for r in r1["rightsize"])
    lines += ["", f"Tổng cơ hội right-size inference: **${rs:.2f}/tháng** theo on-demand 24×30. "
              "A100 không chuyển L4 vì bộ nhớ không đủ; MI300X có $/GB tốt nhưng bill/giờ cao hơn A100. "
              "Hai A10G chuyển L4 giảm 20% bill/giờ, đủ bandwidth đo được với headroom. "
              "Benchmark p95 latency, throughput, model fit/KV-cache và phần mềm trước khi thực hiện. "
              "Không cộng $288 vào lever util-lies: `gpu-a10g-1` đã nằm trong cả hai cách sàng lọc.",
              "", "## Extension 4 — Ngân sách reasoning", "",
              "| Traffic | Request | USD/ngày sau M2 | Wh/ngày |", "|---|---:|---:|---:|"]
    reason = r2["reasoning"]
    for flag, g in reason["groups"].items():
        lines.append(f"| {'Reasoning' if flag else 'Ordinary'} | {g['requests']} | {g['cost']:.6f} | {g['wh']:.2f} |")
    gr = reason["groups"][True]
    totalwh = sum(g["wh"] for g in reason["groups"].values())
    cap5 = r2["reasoning_5pct"]
    lines += ["", f"Reasoning chiếm **{reason['traffic_share']:.2%} traffic**, "
              f"**{gr['cost']/r2['optimized_exact']:.2%} chi phí API**, "
              f"**{gr['wh']/totalwh:.2%} năng lượng**. Energy model của lab dùng 80× cho cùng số token; "
              "dataset còn nhân output reasoning 6× nên không diễn giải toàn bộ chênh lệch là do phần cứng. "
              "Không có phụ phí reasoning riêng trong giá API: chi phí tăng qua output token.",
              f"Trần **10%**: đổi {reason['converted']:.0f} request, tiết kiệm ${reason['saved_usd']:.2f} "
              f"và {reason['saved_wh']:.2f} Wh/ngày; chưa binding. Trần **5%**: chuyển kỳ vọng "
              f"{cap5['converted']:.0f} request/ngày sang ordinary, tiết kiệm **${cap5['saved_usd']:.6f}/ngày "
              f"(${cap5['saved_usd']*30:.2f}/tháng)** và **{cap5['saved_wh']:.2f} Wh/ngày "
              f"({cap5['saved_wh']*30/1000:.2f} kWh/tháng)**.",
              "Routing đề xuất: chỉ cho reasoning khi classifier xác định task cần suy luận nhiều bước "
              "và confidence model thường <0.80; gate này là đề xuất vì CSV không có complexity/confidence. "
              "Ưu tiên queue eval khó, quota 10% requests/ngày, budget USD và Wh riêng; "
              "thử A/B trần 5% và yêu cầu accuracy giảm không quá 1 điểm phần trăm. "
              "Counterfactual giữ input, model, cache, batch; giảm output/6 và bỏ multiplier 80×. "
              "Đây là mô phỏng chuyển request, không chứng minh chất lượng tương đương; không cộng vào M5.",
              "", "## Extension 5 — Carbon-aware regional scheduling", "",
              "Chỉ lấy job training interruptible, đúng số ngày, năng lượng = GPU-hours × TDP. "
              "Đây là estimate công suất danh định, không phải điện đo bằng power_w, chưa gồm PUE "
              "hay spot rework. CSV không có carbon theo giờ nên chỉ tối ưu vùng, chưa tối ưu giờ.", "",
              "| Region | USD/kWh | gCO2e/kWh | USD điện | kgCO2e |", "|---|---:|---:|---:|---:|"]
    carbon = r3["carbon"]
    for r in carbon["regions"]:
        lines.append(f"| {r['region']} | {r['usd_kwh']:.3f} | {r['g_kwh']} | {r['energy_usd']:.3f} | {r['carbon_g']/1000:.3f} |")
    lines += ["", "| Job | kWh | us-east-1 kgCO2e | europe-north1 kgCO2e |", "|---|---:|---:|---:|"]
    for r in carbon["jobs"]:
        lines.append(f"| {r['job_id']} | {r['wh']/1000:.2f} | {r['baseline_carbon_g']/1000:.3f} | {r['clean_carbon_g']/1000:.3f} |")
    regions = {r["region"]:r for r in carbon["regions"]}
    east, north = regions["us-east-1"], regions["europe-north1"]
    lines += ["", f"Tổng {carbon['wh']/1000:,.2f} kWh. Chuyển us-east-1 → europe-north1 giảm "
              f"**{(east['carbon_g']-north['carbon_g'])/1000:.3f} kgCO2e "
              f"({(1-north['carbon_g']/east['carbon_g'])*100:.2f}%)** và "
              f"**${east['energy_usd']-north['energy_usd']:.3f}** tiền điện. "
              f"Rẻ nhất: **{carbon['cheapest']}**; sạch nhất: **{carbon['cleanest']}**; "
              f"cân bằng theo policy minimize điện với carbon ≤100 g/kWh: **{carbon['balanced']}**. "
              "So với vùng sạch nhất, us-east-wa rẻ hơn nhưng carbon cao hơn; không có một vùng "
              "đồng thời đạt cả hai minimum. Chi phí điện thường đã nằm trong GPU rent, "
              "không cộng savings điện vào bill thuê để tránh đếm hai lần. "
              "Training có thể di chuyển dễ hơn inference; cân nhắc latency tới users, data residency, "
              "egress, thời gian chuyển checkpoint và giá/availability GPU theo vùng.",
              f"Traffic thực tế trung bình **{totalwh/r2['requests']:.3f} Wh/request**, khác minh họa "
              "800-token ordinary 0.24 Wh ở phần Sustainability. Carbon minh họa = Wh/1000 × "
              "380 g/kWh; không áp dụng một query minh họa cho toàn bộ reasoning traffic.",
              "", "## Hành động ưu tiên và điều kiện nghiệm thu", "",
              "1. Áp dụng showback + budget trước, kiểm tra purchasing: spot cho training checkpointable "
              "và capacity reserved sẵn có cho inference ổn định. Purchasing đóng góp lớn nhất "
              "trong portfolio; xác nhận lịch job, interruption, cam kết dài hạn và owner thiếu tag.",
              "2. Triển khai cascade → cache → batch cho traffic đúng điều kiện; theo dõi $/1M-token, "
              "accuracy và p95 latency. Benchmark các GPU bị lie, lịch idle, thử A10G → L4; "
              "chỉ ghi nhận savings bổ sung khi đối soát resource mapping và đơn giá cuối.",
              "3. Quota reasoning và job training chọn vùng: A/B trần 5%, đo Wh, dùng europe-north1 "
              "nếu carbon ưu tiên hoặc us-east-wa nếu cost với carbon constraint ưu tiên. "
              "Nghiệm thu khi quality/SLO đạt và billing chứng minh savings, không chỉ GPU-Util giảm.",
              "", "## Tái lập và tiêu chí chấm điểm", "",
              "Chạy từ repo root (Windows):", "", "```powershell",
              ".\\.venv\\Scripts\\python.exe missions/run_all.py",
              ".\\.venv\\Scripts\\python.exe verify.py",
              ".\\.venv\\Scripts\\python.exe -m pytest -q",
              ".\\.venv\\Scripts\\python.exe validation/check_extensions.py", "```", "",
              "A: verify 11/11 (30 điểm). B: 15 tests gốc, giữ nguyên tests/ (20 điểm). "
              "C: báo cáo, waterfall bốn lever, baseline/optimized và sustainability (30 điểm). "
              "D: ba extension có code, so sánh và số liệu; tối đa 20 điểm do giảng viên đánh giá. "
              "Nộp report.md, savings.png, focus_export.csv và writeup.md. "
              "Bonus không chấm điểm; không cần GPU, API key hay cloud account."]
    return "\n".join(lines) + "\n"


def writeup(r1, r2, r3, r4, baseline, optimized):
    reasoning = r2["reasoning"]
    cap = r2["reasoning_5pct"]
    carbon = r3["carbon"]
    east = next(r for r in carbon["regions"] if r["region"] == "us-east-1")
    north = next(r for r in carbon["regions"] if r["region"] == "europe-north1")
    return f"""# Bài phân tích Lab 25 — GPU FinOps

**Sinh viên:** Dương Xuân Vinh · **MSSV:** 2A202602622 · **Lớp:** K4-L3
**Dữ liệu:** mô phỏng seed=25, giá snapshot tháng 6/2026.

## 1. Baseline và optimized

Portfolio mô phỏng giảm từ **${baseline:,.2f}** xuống **${optimized:,.2f}/tháng**, tiết kiệm
**${baseline-optimized:,.2f} ({(1-optimized/baseline)*100:.2f}%)**. API inference riêng giảm từ
**${r2['baseline_exact']*30:.2f}** xuống **${r2['optimized_exact']*30:.2f}/tháng**;
**${r2['baseline_per_m']:.3f} → ${r2['optimized_per_m']:.3f}/1M-token**, giảm **{r2['savings_pct']:.1f}%**.
Mẫu có {r2['total_tokens']:,} input+output token/ngày. Portfolio gồm training nên
không dùng portfolio/token làm đơn giá inference. Workloads tính đúng ngày hoạt động;
reserved trả cả giờ không chạy, giả định dùng commitment có sẵn. API và GPU workload
được coi là hai nhóm chi phí riêng, cần billing mapping xác nhận khi triển khai thực tế.

## 2. Đóng góp từng đòn bẩy

Purchasing đóng góp **${r3['on_demand_monthly']-r3['optimized_monthly']:,.2f}/tháng**, lớn nhất
trong portfolio. Trong inference, cascade giảm
**${(r2['stages']['Baseline']-r2['stages']['Cascade'])*30:.2f}/tháng**, cache giảm thêm
**${(r2['stages']['Cascade']-r2['stages']['Cache'])*30:.2f}**, batch giảm thêm
**${(r2['stages']['Cache']-r2['stages']['Batch'])*30:.2f}**. Cascade thắng vì phần lớn request
đủ dùng model nhỏ; cần kiểm chứng quality. Cache giảm input được cache, batch chỉ cho
job không cần phản hồi tức thì. Đóng góp là attribution tuần tự, không độc lập.

Telemetry có cơ hội idle **${r1['idle_waste_daily']*30:.2f}/tháng** và right-size util-lies;
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

**Reasoning budget:** {reasoning['groups'][True]['requests']} request reasoning,
**{reasoning['traffic_share']:.2%} traffic**, chi phí **${reasoning['groups'][True]['cost']:.6f}/ngày**
và **{reasoning['groups'][True]['wh']:.2f} Wh/ngày**. Trần 10% chưa binding nên savings bằng 0.
Kịch bản trần 5% chuyển kỳ vọng {cap['converted']:.0f} request sang ordinary, giảm
**${cap['saved_usd']*30:.2f}/tháng** và **{cap['saved_wh']*30/1000:.2f} kWh/tháng**.
Counterfactual giảm output/6 theo generator và bỏ energy multiplier 80×, chưa chứng minh
accuracy. Chỉ dùng reasoning cho task nhiều bước khi confidence <0.80, theo dõi quota,
USD/Wh và A/B quality; CSV không có confidence nên rule chưa replay được.

**Carbon scheduling:** ba training job interruptible có **{carbon['wh']/1000:,.2f} kWh**
theo GPU TDP × giờ hoạt động. us-east-1 → europe-north1 giảm
**{(east['carbon_g']-north['carbon_g'])/1000:.3f} kgCO2e (92.11%)**, điện giảm
**${east['energy_usd']-north['energy_usd']:.3f}**. Sạch nhất là europe-north1;
rẻ nhất là us-east-wa. Nếu policy carbon ≤100 g/kWh và ưu tiên tiền điện, chọn us-east-wa.
CSV không có hourly carbon; đây là chọn vùng, chưa tối ưu giờ. TDP chưa gồm PUE/rework;
điện thường nằm trong rent nên không cộng thêm savings điện vào bill thuê.

## 5. Ba hành động đầu tiên cho NimbusAI

1. Đối soát billing theo owner, showback và budget; coverage **{r4['tag_coverage_exact']:.2%}**
   vượt gate 80% nhưng cần xử lý project còn thiếu. Dùng spot/checkpoint cho training,
   reserved có sẵn cho inference đều; không mua commitment mới cho job ngắn.
2. Triển khai cascade/cache/batch với quality và latency gate; profiler GPU bị lie,
   benchmark A10G→L4 và lịch idle. Chỉ ghi nhận tiền giảm sau resource-level reconciliation.
3. Quota reasoning, thử cap 5% với accuracy giảm ≤1 điểm phần trăm; chuyển training
   sang vùng phù hợp mục tiêu cost/carbon, kiểm tra data residency, egress và availability.

Chi tiết bảng, giả định và lệnh tái lập nằm trong `report.md`; `savings.png` thể hiện
waterfall đủ bốn lever, `focus_export.csv` giữ đủ 2,400 request để đối soát chi phí.
"""
