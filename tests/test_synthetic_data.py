"""Generated history remains reproducible and usable by all three models."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from promise_poc.analytics import summarize_data  # noqa: E402
from promise_poc.data import load_sample_data  # noqa: E402
from promise_poc.engine import evaluate  # noqa: E402
from promise_poc.features import build_training_rows, inventory_features, parse_time  # noqa: E402
from scripts.generate_data import generate_history  # noqa: E402


class SyntheticDataTests(unittest.TestCase):
    def test_loader_reads_separate_categories(self):
        data = load_sample_data()

        self.assertEqual(len(data["products"]), 30)
        self.assertEqual(
            sum(location["location_type"] == "STORE" for location in data["locations"]), 10
        )
        self.assertEqual(
            {
                location["location_id"]
                for location in data["locations"]
                if location["location_type"] == "DC"
            },
            {"DC-001", "DC-002", "DC-003"},
        )
        self.assertEqual(len(data["lanes"]), 40)
        self.assertEqual(len(data["snapshots"]), 10390)
        self.assertEqual(len(data["counts"]), 10000)
        self.assertEqual(len(data["orders"]), 10000)
        self.assertEqual(len(data["demo_requests"]), 7)
        self.assertEqual(data["reference_time"], "2026-11-05T10:30:00Z")

    def test_generation_is_repeatable_and_links_outcomes(self):
        catalog = load_sample_data()
        first = generate_history(catalog, rows=120, seed=42)
        second = generate_history(catalog, rows=120, seed=42)

        self.assertEqual(first, second)
        self.assertEqual(len(first["counts"]), 120)
        self.assertEqual(len(first["orders"]), 120)
        snapshots = {item["snapshot_id"]: item for item in first["snapshots"]}
        lanes = {item["lane_id"]: item for item in first["lanes"]}
        for count, order in zip(first["counts"], first["orders"]):
            snapshot = snapshots[count["snapshot_id"]]
            self.assertEqual(order["snapshot_id"], snapshot["snapshot_id"])
            self.assertGreater(parse_time(count["counted_at"]), parse_time(snapshot["observed_at"]))
            self.assertGreater(
                parse_time(order["requested_at"]), parse_time(snapshot["received_at"])
            )
            self.assertEqual(lanes[order["lane_id"]]["source_id"], snapshot["location_id"])

    def test_expanded_catalog_has_routes_and_current_stock(self):
        generated = generate_history(load_sample_data(), rows=120, seed=42)
        product_ids = {item["product_id"] for item in generated["products"]}
        stores = {
            item["location_id"]
            for item in generated["locations"]
            if item["location_type"] == "STORE"
        }
        live_pairs = {
            (item["product_id"], item["location_id"])
            for item in generated["snapshots"]
            if item["snapshot_id"].startswith("LIVE-")
        }
        routes = {(item["source_id"], item["destination_id"]) for item in generated["lanes"]}
        dcs = {"DC-001", "DC-002", "DC-003"}

        self.assertEqual(product_ids, {f"SKU-{index:03d}" for index in range(1, 31)})
        self.assertEqual(stores, {f"STORE-{index:03d}" for index in range(1, 11)})
        self.assertEqual(len(live_pairs), 390)
        self.assertTrue(
            all((dc, store) in routes for dc in dcs for store in stores)
            and all((store, store) in routes for store in stores)
        )
        self.assertTrue(
            all(
                (product, source) in live_pairs
                for product in product_ids
                for source in stores | dcs
            )
        )

    def test_engine_uses_another_dc_when_other_sources_have_no_stock(self):
        data = generate_history(load_sample_data(), rows=120)
        for snapshot in data["snapshots"]:
            if snapshot["snapshot_id"].startswith("LIVE-") and snapshot["product_id"] == "SKU-001":
                snapshot.update(on_hand=0, reserved=0, allocated=0)
                if snapshot["location_id"] == "DC-003":
                    snapshot["on_hand"] = 100

        result = evaluate(data, data["demo_requests"][0], "rules")

        self.assertEqual(result["decision"], "PROMISE")
        self.assertEqual(result["selected_source_id"], "DC-003")

    def test_products_have_specific_english_names_that_survive_regeneration(self):
        bundled = load_sample_data()
        products = {item["product_id"]: item for item in bundled["products"]}

        self.assertEqual(products["SKU-001"]["name"], "13 mm gypsum plasterboard")
        self.assertEqual(products["SKU-002"]["name"], "Galvanized steel wood screws")
        self.assertEqual(products["SKU-030"]["name"], "Silicone sealant tubes")
        self.assertEqual(len({item["name"] for item in products.values()}), 30)
        self.assertTrue(all(item["name"].isascii() for item in products.values()))
        self.assertTrue(all("Synthetic" not in item["name"] for item in products.values()))
        self.assertEqual(generate_history(bundled, rows=120)["products"], bundled["products"])

    def test_new_product_and_store_can_be_evaluated(self):
        data = load_sample_data()
        request = {
            **data["demo_requests"][0],
            "product_id": "SKU-030",
            "destination_id": "STORE-010",
            "quantity": 1,
        }

        result = evaluate(data, request, "rules")

        self.assertEqual(result["decision"], "PROMISE")
        self.assertIn(result["selected_source_id"], {"STORE-010", "DC-001", "DC-002", "DC-003"})

    def test_bundled_history_matches_default_seed(self):
        bundled = load_sample_data()
        regenerated = generate_history(bundled)

        for category in (
            "products",
            "locations",
            "lanes",
            "snapshots",
            "events",
            "counts",
            "orders",
            "demo_requests",
        ):
            self.assertEqual(regenerated[category], bundled[category])

    def test_demo_scenarios_cover_decisions_and_feasibility(self):
        data = load_sample_data()
        results = {
            request["request_id"]: evaluate(data, request, "rules")
            for request in data["demo_requests"]
        }

        self.assertEqual(
            {request_id: result["decision"] for request_id, result in results.items()},
            {
                "REQ-001": "PROMISE",
                "REQ-002": "REJECT",
                "REQ-003": "PROMISE",
                "REQ-004": "REJECT",
                "REQ-005": "VERIFY",
                "REQ-006": "REJECT",
                "REQ-007": "REJECT",
            },
        )
        self.assertEqual(results["REQ-003"]["selected_source_id"], "STORE-001")
        self.assertEqual(results["REQ-005"]["selected_source_id"], "STORE-001")
        self.assertEqual(results["REQ-005"]["atp"], 5)
        self.assertAlmostEqual(results["REQ-005"]["probabilities"]["fulfillment"], 0.9)
        self.assertLess(results["REQ-006"]["probabilities"]["inventory_confidence"], 0.65)
        self.assertGreater(results["REQ-006"]["probabilities"]["promise_success"], 0.95)
        for request_id in ("REQ-002", "REQ-004", "REQ-007"):
            self.assertIsNone(results[request_id]["selected_source_id"])
        requests = {request["request_id"]: request for request in data["demo_requests"]}
        later_pickup = {**requests["REQ-004"], "requested_delivery_date": "2026-11-10"}
        fresh_inventory = {**requests["REQ-007"], "requested_at": data["reference_time"]}
        self.assertEqual(evaluate(data, later_pickup, "rules")["decision"], "PROMISE")
        self.assertEqual(evaluate(data, fresh_inventory, "rules")["decision"], "PROMISE")

    def test_training_has_both_outcomes_and_index_preserves_features(self):
        data = load_sample_data()
        snapshots = {item["snapshot_id"]: item for item in data["snapshots"]}
        training = {
            kind: build_training_rows(data, kind)
            for kind in ("inventory", "fulfillment", "delivery")
        }
        for rows in training.values():
            self.assertGreaterEqual(len(rows), 6500)
            self.assertEqual({label for _, label in rows}, {0, 1})
        for index in (0, 111, 9999):
            snapshot = snapshots[data["counts"][index]["snapshot_id"]]
            actual = inventory_features(data, snapshot, parse_time(snapshot["observed_at"]))
            indexed = training["inventory"][index][0]
            self.assertEqual(indexed, actual)

    def test_summary_rates_match_raw_outcomes(self):
        data = load_sample_data()
        summary = summarize_data(data)

        self.assertEqual(summary["inventory"]["rows"], 10000)
        self.assertEqual(summary["fulfillment"]["rows"], 10000)
        self.assertEqual(
            summary["fulfillment"]["positive"],
            sum(item["picked_quantity"] >= item["quantity"] for item in data["orders"]),
        )
        self.assertEqual(summary["delivery"]["rows"], summary["fulfillment"]["positive"])
        self.assertEqual(sum(row["Orders"] for row in summary["by_product"]), 10000)
        self.assertEqual(len(summary["by_location"]), 13)
        self.assertTrue(
            all(
                next(row["Orders"] for row in summary["by_location"] if row["Source"] == dc) > 0
                for dc in ("DC-001", "DC-002", "DC-003")
            )
        )
        self.assertGreater(
            next(row["Orders"] for row in summary["by_location"] if row["Source"] == "STORE-010"),
            0,
        )


if __name__ == "__main__":
    unittest.main()
