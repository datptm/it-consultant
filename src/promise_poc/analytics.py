"""Summarize synthetic training outcomes for the local dashboard."""

from collections import defaultdict
from typing import Any


def summarize_data(data: dict[str, Any]) -> dict[str, Any]:
    """Count training labels and group historical outcomes by product and source location."""
    snapshots = {item["snapshot_id"]: item for item in data["snapshots"]}
    location_types = {item["location_id"]: item["location_type"] for item in data["locations"]}
    by_product = defaultdict(lambda: {"Orders": 0, "Picked in full": 0, "On time": 0})
    by_location = defaultdict(lambda: {"Orders": 0, "Picked in full": 0, "On time": 0})
    accurate = sum(
        abs(snapshots[count["snapshot_id"]]["on_hand"] - count["actual_on_hand"]) <= 1
        for count in data["counts"]
    )
    picked = 0
    on_time = 0
    for order in data["orders"]:
        snapshot = snapshots[order["snapshot_id"]]
        product = by_product[snapshot["product_id"]]
        location = by_location[snapshot["location_id"]]
        full_pick = order["picked_quantity"] >= order["quantity"]
        timely = full_pick and order["delivered_at"][:10] <= order["requested_delivery_date"]
        picked += full_pick
        on_time += timely
        for group in (product, location):
            group["Orders"] += 1
            group["Picked in full"] += full_pick
            group["On time"] += timely
    return {
        "inventory": {"rows": len(data["counts"]), "positive": accurate},
        "fulfillment": {"rows": len(data["orders"]), "positive": picked},
        "delivery": {"rows": picked, "positive": on_time},
        "by_product": [{"Product": key, **value} for key, value in sorted(by_product.items())],
        "by_location": [
            {"Source": key, "Type": location_types[key], **value}
            for key, value in sorted(by_location.items())
        ],
    }
