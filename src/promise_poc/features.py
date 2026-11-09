"""Point-in-time features and labels from synthetic operational records."""

from bisect import bisect_right
from datetime import date, datetime, timedelta
from typing import Any

from .rules import earliest_delivery_date


def parse_time(value: str) -> datetime:
    """Read an ISO UTC timestamp from sample data or CLI input."""
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset().total_seconds() != 0:
        raise ValueError("Timestamps must include UTC timezone")
    return parsed


def inventory_features(
    data: dict[str, Any],
    snapshot: dict[str, Any],
    at_time: datetime,
) -> dict[str, float | int | str]:
    """Build inventory features using only facts received by at_time."""
    source_time = parse_time(snapshot["source_updated_at"])
    last_count = parse_time(snapshot["last_count_at"])
    received = parse_time(snapshot["received_at"])
    if max(source_time, last_count, received) > at_time:
        raise ValueError("Snapshot contains future information")
    prior_counts = [
        count
        for count in data["counts"]
        if count["product_id"] == snapshot["product_id"]
        and count["location_id"] == snapshot["location_id"]
        and parse_time(count["counted_at"]) >= last_count
        and parse_time(count["counted_at"]) <= at_time
    ]
    discrepancy = 0.0
    if prior_counts:
        latest = max(prior_counts, key=lambda item: item["counted_at"])
        discrepancy = abs(latest["system_on_hand"] - latest["actual_on_hand"]) / max(
            latest["actual_on_hand"], 1
        )
    sales_last_week = sum(
        abs(event["quantity_delta"])
        for event in data["events"]
        if event["product_id"] == snapshot["product_id"]
        and event["location_id"] == snapshot["location_id"]
        and event["event_type"] == "SALE"
        and 0 <= (at_time - parse_time(event["event_time"])).total_seconds() < 7 * 86400
        and parse_time(event["received_at"]) <= at_time
    )
    location = next(
        item for item in data["locations"] if item["location_id"] == snapshot["location_id"]
    )
    return {
        "stock_age_hours": (at_time - source_time).total_seconds() / 3600,
        "days_since_last_count": (at_time - last_count).total_seconds() / 86400,
        "sales_velocity_7d": sales_last_week / 7,
        "historical_discrepancy": discrepancy,
        "pending_transactions": snapshot["pending_transactions"],
        "on_hand": snapshot["on_hand"],
        "location_type": location["location_type"],
    }


def fulfillment_features(
    data: dict[str, Any],
    snapshot: dict[str, Any],
    quantity: int,
    at_time: datetime,
) -> dict[str, float | int | str]:
    """Describe requested units and raw stock without an outcome feature."""
    inventory = inventory_features(data, snapshot, at_time)
    return {
        "requested_quantity": quantity,
        "raw_available": snapshot["on_hand"] - snapshot["reserved"] - snapshot["allocated"],
        "pending_transactions": snapshot["pending_transactions"],
        "stock_age_hours": inventory["stock_age_hours"],
        "location_type": inventory["location_type"],
    }


def delivery_features(
    data: dict[str, Any],
    snapshot: dict[str, Any],
    lane: dict[str, Any],
    quantity: int,
    at_time: datetime,
    target: date,
) -> dict[str, float | int | str]:
    """Describe route and calendar slack known before fulfillment."""
    location = next(
        item for item in data["locations"] if item["location_id"] == snapshot["location_id"]
    )
    earliest = earliest_delivery_date(at_time, lane)
    return {
        "quantity": quantity,
        "lead_days": (target - at_time.date()).days,
        "slack_days": (target - earliest).days,
        "delivery_type": lane["delivery_type"],
        "source_type": location["location_type"],
    }


def build_training_rows(
    data: dict[str, Any],
    kind: str,
) -> list[tuple[dict[str, float | int | str], int]]:
    """Construct independent model examples with post-request labels only."""
    return [(features, label) for features, label, _ in build_training_examples(data, kind)]


def build_training_examples(
    data: dict[str, Any],
    kind: str,
) -> list[tuple[dict[str, float | int | str], int, datetime]]:
    """Return labeled examples with the time each prediction would have been made."""
    snapshots = {item["snapshot_id"]: item for item in data["snapshots"]}
    histories: dict[str, dict[tuple[str, str], tuple[list[datetime], list[dict[str, Any]]]]] = {}
    for category, time_field in (
        (("counts", "counted_at"), ("events", "event_time")) if kind != "delivery" else ()
    ):
        by_source: dict[tuple[str, str], list[tuple[datetime, dict[str, Any]]]] = {}
        for item in data[category]:
            key = (item["product_id"], item["location_id"])
            by_source.setdefault(key, []).append((parse_time(item[time_field]), item))
        for items in by_source.values():
            items.sort(key=lambda pair: pair[0])
        histories[category] = {
            key: ([time for time, _ in items], [item for _, item in items])
            for key, items in by_source.items()
        }

    def at_time_data(snapshot: dict[str, Any], at_time: datetime) -> dict[str, Any]:
        key = (snapshot["product_id"], snapshot["location_id"])
        count_times, count_history = histories["counts"].get(key, ([], []))
        count_position = bisect_right(count_times, at_time)
        prior_count = (
            count_history[count_position - 1 : count_position]
            if count_position
            and count_times[count_position - 1] >= parse_time(snapshot["last_count_at"])
            else []
        )
        event_times, event_history = histories["events"].get(key, ([], []))
        first = bisect_right(event_times, at_time - timedelta(days=7))
        last = bisect_right(event_times, at_time)
        return {
            "locations": data["locations"],
            "counts": prior_count,
            "events": event_history[first:last],
        }

    if kind == "inventory":
        rows = []
        for count in data["counts"]:
            snapshot = snapshots[count["snapshot_id"]]
            at_time = parse_time(snapshot["observed_at"])
            if parse_time(count["counted_at"]) <= at_time:
                raise ValueError("Inventory label must be observed after snapshot")
            features = inventory_features(at_time_data(snapshot, at_time), snapshot, at_time)
            label = int(abs(snapshot["on_hand"] - count["actual_on_hand"]) <= 1)
            rows.append((features, label, at_time))
        return rows
    if kind not in {"fulfillment", "delivery"}:
        raise ValueError(f"Unknown model kind: {kind}")
    rows = []
    for order in data["orders"]:
        snapshot = snapshots[order["snapshot_id"]]
        at_time = parse_time(order["requested_at"])
        if parse_time(snapshot["received_at"]) > at_time:
            raise ValueError("Order uses a future inventory snapshot")
        if parse_time(order["picked_at"]) <= at_time:
            raise ValueError("Fulfillment label must be observed after request")
        if kind == "fulfillment":
            features = fulfillment_features(
                at_time_data(snapshot, at_time), snapshot, order["quantity"], at_time
            )
            rows.append((features, int(order["picked_quantity"] >= order["quantity"]), at_time))
            continue
        if order["picked_quantity"] < order["quantity"]:
            continue
        lane = next(item for item in data["lanes"] if item["lane_id"] == order["lane_id"])
        target = date.fromisoformat(order["requested_delivery_date"])
        features = delivery_features(data, snapshot, lane, order["quantity"], at_time, target)
        delivered = parse_time(order["delivered_at"])
        if delivered <= at_time:
            raise ValueError("Delivery label must be observed after request")
        rows.append((features, int(delivered.date() <= target), at_time))
    return rows
