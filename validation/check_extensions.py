"""Additional independent checks; the instructor's tests/ stays untouched.

Run: python validation/check_extensions.py
"""
from pathlib import Path
import csv
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from finops import extensions
from missions._common import load_csv, catalog_by_type
from missions.m2_inference_levers import MODEL_PRICES, run as inference
from missions.m3_purchasing import run as purchasing


class ExtensionChecks(unittest.TestCase):
    def test_rightsize_rejects_cheap_gpu_with_insufficient_vram(self):
        result = extensions.rightsize_candidates(load_csv("gpu_telemetry.csv"), catalog_by_type())
        by_id = {r["gpu_id"]: r for r in result}
        self.assertEqual(by_id["gpu-a100-0"]["target"], "A100")
        self.assertGreater(by_id["gpu-a100-0"]["required_gb"], 24)
        self.assertAlmostEqual(sum(r["savings_monthly"] for r in result), 288)

    def test_rightsize_rejects_bandwidth_regression(self):
        cat = catalog_by_type()
        # Fits VRAM and compute on L4, but L4 bandwidth cannot sustain demand.
        tel = [{"gpu_id": "probe", "gpu_type": "A10G", "workload": "infer",
                "mem_used_gb": "10", "achieved_bw_tbs": "0.4", "achieved_tflops": "10"}]
        self.assertEqual(extensions.rightsize_candidates(tel, cat)[0]["target"], "A10G")

    def test_rightsize_excludes_training_and_empty_input(self):
        self.assertEqual(extensions.rightsize_candidates([], catalog_by_type()), [])
        tel = [r for r in load_csv("gpu_telemetry.csv") if r["workload"] == "train"]
        self.assertEqual(extensions.rightsize_candidates(tel, catalog_by_type()), [])

    def test_reasoning_ten_percent_cap_is_nonbinding(self):
        result = extensions.reasoning_budget(load_csv("token_usage.csv"), MODEL_PRICES)
        self.assertEqual(result["groups"][True]["requests"], 201)
        self.assertEqual(result["converted"], 0)
        self.assertEqual(result["saved_usd"], 0)
        self.assertEqual(result["saved_wh"], 0)

    def test_reasoning_counterfactual_has_analytic_expected_result(self):
        # 1k input+6k output large-model reasoning -> 1k+1k ordinary.
        rows = [{"is_reasoning": "1", "input_tokens": "1000", "output_tokens": "6000",
                 "route_tier": "large", "cached_input_tokens": "0", "is_batch": "0"}]
        result = extensions.reasoning_budget(rows, MODEL_PRICES, cap=0)
        self.assertAlmostEqual(result["saved_usd"], 0.093 - 0.018)
        self.assertAlmostEqual(result["saved_wh"], 168 - 0.6)
        self.assertEqual(result["converted"], 1)

    def test_reasoning_empty_input_and_invalid_cap(self):
        result = extensions.reasoning_budget([], MODEL_PRICES, cap=0)
        self.assertEqual(result["traffic_share"], 0)
        with self.assertRaises(ValueError):
            extensions.reasoning_budget([], MODEL_PRICES, cap=1.1)

    def test_five_percent_cap_reaches_target_and_preserves_group_total(self):
        rows = load_csv("token_usage.csv")
        result = extensions.reasoning_budget(rows, MODEL_PRICES, cap=0.05)
        self.assertEqual(result["groups"][True]["requests"] - result["converted"], 120)
        self.assertAlmostEqual(sum(g["cost"] for g in result["groups"].values()), inference(False)["optimized_exact"])
        self.assertGreater(result["saved_wh"], 0)

    def test_carbon_uses_actual_days_and_training_only(self):
        result = extensions.carbon_scheduling(load_csv("workloads.csv"), catalog_by_type())
        self.assertEqual(len(result["jobs"]), 3)
        self.assertAlmostEqual(result["wh"], (20*14*8*700)+(10*5*4*400)+(6*3*2*700))
        self.assertAlmostEqual(sum(r["baseline_carbon_g"]-r["clean_carbon_g"] for r in result["jobs"]), 585620)
        self.assertEqual(result["cheapest"], "us-east-wa")
        self.assertEqual(result["cleanest"], "europe-north1")
        self.assertNotEqual(result["cheapest"], result["cleanest"])

    def test_purchasing_charges_unused_reserved_hours(self):
        result = purchasing(False)
        search = next(r for r in result["recommendations"] if r["job_id"] == "job-infer-search")
        self.assertEqual(search["optimized"], 24*30*4*0.45)
        training = next(r for r in result["recommendations"] if r["job_id"] == "job-train-llm")
        self.assertEqual(training["on_demand"], 20*14*8*2.5)

    def test_full_export_reconciles_with_inference(self):
        with (ROOT/"outputs"/"focus_export.csv").open(encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 2400)
        self.assertEqual(len({r["ResourceId"] for r in rows}), 2400)
        self.assertLess(abs(sum(float(r["BilledCost"]) for r in rows) - inference(False)["optimized_exact"]), 0.000012)


if __name__ == "__main__":
    unittest.main(verbosity=2)
