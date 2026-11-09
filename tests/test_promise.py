"""Behavioral checks for the small Promise Engine."""

import json
import os
import subprocess
import sys
import unittest
from datetime import date, datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from promise_poc.data import load_sample_data  # noqa: E402
from promise_poc.engine import decide, evaluate  # noqa: E402
from promise_poc.features import build_training_rows, inventory_features, parse_time  # noqa: E402
from promise_poc.ml import train_models  # noqa: E402
from promise_poc.rules import atp, earliest_delivery_date, inventory_score  # noqa: E402


class RulesTests(unittest.TestCase):
    def test_atp_rounds_buffer_up_and_excludes_inbound(self):
        self.assertEqual(atp(20, 5, 2, 0.85), 11)
        self.assertEqual(atp(2, 4, 0, 1.0), 0)

    def test_inventory_penalties_and_bands(self):
        features = {"days_since_last_count": 31, "pending_transactions": 1,
                    "historical_discrepancy": 0.2, "sales_velocity_7d": 6,
                    "stock_age_hours": 25}
        self.assertEqual(inventory_score(features), 0.2)

    def test_delivery_cutoff_skips_weekend(self):
        requested_at = datetime(2026, 11, 6, 17, 0, tzinfo=timezone.utc)
        lane = {"cutoff_hour_utc": 16, "processing_days": 1, "transit_days": 1}
        self.assertEqual(earliest_delivery_date(requested_at, lane), date(2026, 11, 11))

    def test_decision_boundaries_and_inventory_gate(self):
        self.assertEqual(decide(0.85, 0.95, True), "PROMISE")
        self.assertEqual(decide(0.85, 0.9499, True), "VERIFY")
        self.assertEqual(decide(0.85, 0.85, True), "VERIFY")
        self.assertEqual(decide(0.85, 0.8499, True), "REJECT")
        self.assertEqual(decide(0.70, 0.99, True), "VERIFY")
        self.assertEqual(decide(0.60, 0.99, True), "REJECT")
        self.assertEqual(decide(0.99, 0.99, False), "REJECT")


class DataAndEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_sample_data()

    def test_training_labels_use_later_outcome_without_future_features(self):
        rows = build_training_rows(self.data, "inventory")
        self.assertEqual(len(rows), 10000)
        self.assertEqual({label for _, label in rows}, {0, 1})
        first_features, first_label = rows[0]
        first_count = self.data["counts"][0]
        first_snapshot = next(
            item for item in self.data["snapshots"] if item["snapshot_id"] == first_count["snapshot_id"]
        )
        self.assertEqual(first_label, int(abs(first_count["actual_on_hand"] - first_snapshot["on_hand"]) <= 1))
        self.assertNotIn("actual_on_hand", first_features)
        self.assertNotIn("counted_at", first_features)
        self.assertGreaterEqual(first_features["stock_age_hours"], 0)

    def test_unreceived_sale_cannot_change_historical_features(self):
        data = json.loads(json.dumps(self.data))
        snapshot = next(item for item in data["snapshots"] if item["snapshot_id"] == "GEN-00000")
        at_time = parse_time(snapshot["observed_at"])
        baseline = inventory_features(data, snapshot, at_time)["sales_velocity_7d"]
        data["events"].append({
            "product_id": "SKU-001", "location_id": "DC-001", "event_type": "SALE",
            "quantity_delta": -1000, "event_time": "2026-09-30T11:00:00Z",
            "received_at": "2026-10-02T11:00:00Z",
        })
        self.assertEqual(inventory_features(data, snapshot, at_time)["sales_velocity_7d"], baseline)

    def test_order_training_has_both_outcomes(self):
        for kind, length in (("fulfillment", 10000), ("delivery", None)):
            with self.subTest(kind=kind):
                rows = build_training_rows(self.data, kind)
                if length is None:
                    self.assertGreater(len(rows), 6500)
                else:
                    self.assertEqual(len(rows), length)
                self.assertEqual({label for _, label in rows}, {0, 1})

    def test_rule_mode_selects_eligible_single_source(self):
        result = evaluate(self.data, self.data["demo_requests"][0], "rules")
        self.assertEqual(result["selected_source_id"], "DC-003")
        self.assertEqual(result["decision"], "PROMISE")
        self.assertGreaterEqual(result["probabilities"]["promise_success"], 0.95)

    def test_insufficient_stock_rejects(self):
        request = {**self.data["demo_requests"][0], "quantity": 10000}
        result = evaluate(self.data, request, "rules")
        self.assertEqual(result["decision"], "REJECT")
        self.assertIsNone(result["selected_source_id"])

    def test_inbound_stock_is_not_available_to_promise(self):
        data = json.loads(json.dumps(self.data))
        for snapshot in data["snapshots"]:
            if snapshot["snapshot_id"].startswith("LIVE-") and snapshot["product_id"] == "SKU-001":
                snapshot.update(on_hand=0, reserved=0, allocated=0, inbound=100)
        request = {**data["demo_requests"][0], "quantity": 11}
        self.assertEqual(evaluate(data, request, "rules")["decision"], "REJECT")

    def test_nonpositive_quantity_is_invalid(self):
        request = {**self.data["demo_requests"][0], "quantity": 0}
        with self.assertRaisesRegex(ValueError, "positive integer"):
            evaluate(self.data, request, "rules")

    def test_impossible_date_rejects(self):
        request = {**self.data["demo_requests"][0],
                   "requested_delivery_date": "2026-11-05"}
        self.assertEqual(evaluate(self.data, request, "rules")["decision"], "REJECT")

    def test_stale_inventory_cannot_be_promised(self):
        data = json.loads(json.dumps(self.data))
        for snapshot in data["snapshots"]:
            if snapshot["snapshot_id"].startswith("LIVE"):
                snapshot["source_updated_at"] = "2026-10-01T00:00:00Z"
        result = evaluate(data, data["demo_requests"][0], "rules")
        self.assertNotEqual(result["decision"], "PROMISE")

    def test_ml_mode_trains_three_models_and_returns_probabilities(self):
        models = train_models(self.data)
        self.assertEqual(set(models), {"inventory", "fulfillment", "delivery"})
        result = evaluate(self.data, self.data["demo_requests"][0], "ml", models)
        for key in ("inventory_confidence", "fulfillment", "on_time", "promise_success"):
            self.assertGreaterEqual(result["probabilities"][key], 0)
            self.assertLessEqual(result["probabilities"][key], 1)

    def test_cli_demo_and_direct_evaluate(self):
        commands = [
            ["demo", "--mode", "rules"],
            ["demo", "--mode", "ml"],
            ["evaluate", "--product-id", "SKU-001", "--quantity", "2",
             "--destination-id", "STORE-001", "--date", "2026-11-10",
             "--mode", "rules"],
        ]
        for arguments in commands:
            with self.subTest(arguments=arguments):
                completed = subprocess.run(
                    [sys.executable, "-m", "promise_poc", *arguments],
                    cwd=ROOT,
                    env={**os.environ, "PYTHONPATH": str(ROOT / "src") + os.pathsep + os.environ.get("PYTHONPATH", "")},
                    capture_output=True, text=True, check=True,
                )
                output = json.loads(completed.stdout)
                if arguments[0] == "demo":
                    self.assertEqual(len(output), 7)
                    self.assertTrue(all("decision" in item for item in output))
                else:
                    self.assertIn("decision", output)

    def test_cli_rejects_unknown_product_without_traceback(self):
        completed = subprocess.run(
            [sys.executable, "-m", "promise_poc", "evaluate", "--product-id", "UNKNOWN",
             "--quantity", "1", "--destination-id", "STORE-001", "--date", "2026-11-10"],
            cwd=ROOT,
            env={**os.environ, "PYTHONPATH": str(ROOT / "src") + os.pathsep + os.environ.get("PYTHONPATH", "")},
            capture_output=True, text=True,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("Unknown product", completed.stderr)
        self.assertNotIn("Traceback", completed.stderr)

    def test_rule_cli_runs_without_ml_packages(self):
        completed = subprocess.run(
            [sys.executable, "-S", "-m", "promise_poc", "demo", "--mode", "rules"],
            cwd=ROOT, env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
            capture_output=True, text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(json.loads(completed.stdout)[0]["decision"], "PROMISE")


if __name__ == "__main__":
    unittest.main()
