"""Measured extension scenarios; all assumptions use the local synthetic lab."""
from __future__ import annotations

from finops import pricing, sustainability as s


def rightsize_candidates(telemetry, catalog):
    """Screen inference GPUs with 10% VRAM and 20% bandwidth/compute headroom.

    Low MBU is a screening signal, not proof of a memory bottleneck. Actual
    throughput, p95 latency and accelerator/software compatibility need testing.
    """
    grouped = {}
    for row in telemetry:
        if row["workload"] == "infer":
            grouped.setdefault(row["gpu_id"], []).append(row)
    result = []
    for gid, rows in grouped.items():
        current = catalog[rows[0]["gpu_type"]]
        mbu = sum(float(r["achieved_bw_tbs"]) for r in rows) / len(rows) / float(current["peak_bw_tbs"])
        memory = max(float(r["mem_used_gb"]) for r in rows) / 0.90
        bandwidth = max(float(r["achieved_bw_tbs"]) for r in rows) / 0.80
        compute = max(float(r["achieved_tflops"]) for r in rows) / 0.80
        feasible = [c for c in catalog.values()
                    if float(c["hbm_gb"]) >= memory
                    and float(c["peak_bw_tbs"]) >= bandwidth
                    and float(c["peak_tflops_fp16"]) >= compute
                    and float(c["on_demand_hr"]) < float(current["on_demand_hr"])] if mbu < 0.60 else []
        target = min(feasible, key=lambda c: float(c["on_demand_hr"])) if feasible else current
        delta = float(current["on_demand_hr"]) - float(target["on_demand_hr"])
        result.append({"gpu_id": gid, "current": current["gpu_type"], "target": target["gpu_type"],
                       "mbu": mbu, "required_gb": memory, "required_bw": bandwidth,
                       "current_bw": float(current["peak_bw_tbs"]), "target_bw": float(target["peak_bw_tbs"]),
                       "current_usd_gb": float(current["on_demand_hr"])/float(current["hbm_gb"]),
                       "target_usd_gb": float(target["on_demand_hr"])/float(target["hbm_gb"]),
                       "savings_monthly": delta * len(rows) * 30,
                       "savings_pct": delta / float(current["on_demand_hr"]) * 100})
    return result


def reasoning_budget(rows, model_prices, cap=0.10):
    """Expected uniform conversion to ordinary requests above a traffic cap.

    Synthetic generator makes reasoning output 6x ordinary output. Conversion
    preserves input/model/cache/batch, divides output by 6 and removes the 80x
    energy multiplier. This is a counterfactual, not a measured quality result.
    """
    if not 0 <= cap <= 1:
        raise ValueError("cap must be between zero and one")
    groups = {False: {"requests": 0, "cost": 0.0, "wh": 0.0},
              True: {"requests": 0, "cost": 0.0, "wh": 0.0}}
    ordinary_cost = ordinary_wh = 0.0
    for r in rows:
        reasoning = bool(int(r["is_reasoning"]))
        inp, out = int(r["input_tokens"]), int(r["output_tokens"])
        pin, pout = model_prices[r["route_tier"]]
        cached, batch = int(r["cached_input_tokens"]), bool(int(r["is_batch"]))
        g = groups[reasoning]
        g["requests"] += 1
        g["cost"] += pricing.request_cost(inp, out, pin, pout, cached_in=cached, batch=batch)
        g["wh"] += s.wh_per_query(inp + out, is_reasoning=reasoning)
        if reasoning:
            ordinary_cost += pricing.request_cost(inp, out / 6, pin, pout, cached_in=cached, batch=batch)
            ordinary_wh += s.wh_per_query(inp + out / 6)
    n = len(rows)
    nr = groups[True]["requests"]
    converted = max(0.0, nr - cap * n)
    fraction = converted / nr if nr else 0.0
    return {"groups": groups, "cap": cap, "converted": converted,
            "traffic_share": nr/n if n else 0.0,
            "saved_usd": fraction * (groups[True]["cost"] - ordinary_cost),
            "saved_wh": fraction * (groups[True]["wh"] - ordinary_wh)}


def carbon_scheduling(jobs, catalog):
    """TDP-based energy scenario for interruptible training, using actual days.

    No hourly grid signals exist in the dataset: regional selection only.
    GPU TDP is a capacity estimate; excludes PUE, transfers and regional rent.
    """
    eligible = []
    for j in jobs:
        if j["kind"] == "train" and int(j["interruptible"]):
            wh = (float(j["hours_per_day"]) * float(j["days"]) * int(j["num_gpus"])
                  * float(catalog[j["gpu_type"]]["watts"]))
            eligible.append({"job_id": j["job_id"], "wh": wh,
                             "baseline_carbon_g": s.carbon_g(wh, "us-east-1"),
                             "clean_carbon_g": s.carbon_g(wh, "europe-north1")})
    wh = sum(j["wh"] for j in eligible)
    regions = [{"region": r, "usd_kwh": s.REGION_PRICE_KWH[r], "g_kwh": s.REGION_CARBON[r],
                "energy_usd": s.energy_cost_usd(wh, r), "carbon_g": s.carbon_g(wh, r)}
               for r in s.REGION_CARBON]
    cheapest = min(regions, key=lambda r: r["energy_usd"])["region"]
    cleanest = min(regions, key=lambda r: r["carbon_g"])["region"]
    # Explicit balanced policy: minimize electricity cost under 100 g/kWh.
    balanced = min((r for r in regions if r["g_kwh"] <= 100), key=lambda r: r["energy_usd"])["region"]
    return {"jobs": eligible, "wh": wh, "regions": regions,
            "cheapest": cheapest, "cleanest": cleanest, "balanced": balanced}
