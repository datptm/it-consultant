"""Create reproducible synthetic history for the local Promise Engine."""

import argparse
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from promise_poc.data import CATEGORIES, DATA_DIR, load_sample_data
from promise_poc.rules import earliest_delivery_date

START = datetime(2026, 6, 1, 8, tzinfo=timezone.utc)
HISTORY_HOURS = 145 * 24
STORE_COUNT = 10
DC_COUNT = 3
PRODUCT_CATEGORIES = (
    "BOARD",
    "FASTENER",
    "INSULATION",
    "PAINT",
    "ELECTRICAL",
    "PLUMBING",
    "HARDWARE",
    "TOOL",
    "FLOORING",
    "ADHESIVE",
)
PRODUCT_NAMES = (
    "13 mm gypsum plasterboard",
    "Galvanized steel wood screws",
    "Mineral wool insulation batts",
    "Interior matte wall paint",
    "Copper electrical cable",
    "PVC water supply pipe",
    "Galvanized corner brackets",
    "Cordless drill driver",
    "Oak laminate flooring planks",
    "Construction adhesive cartridges",
    "Moisture-resistant gypsum board",
    "Stainless steel bolts",
    "Rigid foam insulation panels",
    "Exterior masonry paint",
    "Double electrical outlet",
    "Brass pipe fittings",
    "Heavy-duty door hinges",
    "Tape measure",
    "Ceramic floor tiles",
    "Tile mortar bags",
    "Cement backer board",
    "Drywall anchor screws",
    "Fiberglass insulation rolls",
    "Wood primer",
    "LED ceiling light",
    "PEX tubing",
    "Adjustable shelf brackets",
    "Circular saw blade",
    "Vinyl floor planks",
    "Silicone sealant tubes",
)
PRODUCT_COUNT = len(PRODUCT_NAMES)
BASELINE_LIVE_IDS = {"LIVE-DC", "LIVE-S1", "LIVE-S2"}


def _timestamp(value: datetime) -> str:
    return value.isoformat(timespec="seconds").replace("+00:00", "Z")


def _expand_catalog(catalog: dict[str, Any]) -> dict[str, Any]:
    stores = {item["location_id"]: item for item in catalog["locations"]}
    lanes = {item["lane_id"]: item for item in catalog["lanes"]}
    expanded = dict(catalog)
    expanded["products"] = [
        {
            "product_id": f"SKU-{index:03d}",
            "name": PRODUCT_NAMES[index - 1],
            "category": PRODUCT_CATEGORIES[(index - 1) % len(PRODUCT_CATEGORIES)],
        }
        for index in range(1, PRODUCT_COUNT + 1)
    ]
    expanded["locations"] = [
        stores.get(
            f"STORE-{index:03d}",
            {"location_id": f"STORE-{index:03d}", "location_type": "STORE", "country": "SE"},
        )
        for index in range(1, STORE_COUNT + 1)
    ] + [
        stores.get(
            f"DC-{index:03d}",
            {"location_id": f"DC-{index:03d}", "location_type": "DC", "country": "SE"},
        )
        for index in range(1, DC_COUNT + 1)
    ]
    expanded["lanes"] = []
    for dc_index in range(1, DC_COUNT + 1):
        for index in range(1, STORE_COUNT + 1):
            store_id = f"STORE-{index:03d}"
            lane_id = f"DC-S{index}" if dc_index == 1 else f"DC{dc_index}-S{index}"
            expanded["lanes"].append(
                lanes.get(
                    lane_id,
                    {
                        "lane_id": lane_id,
                        "source_id": f"DC-{dc_index:03d}",
                        "destination_id": store_id,
                        "delivery_type": "STORE_PICKUP",
                        "cutoff_hour_utc": 16,
                        "processing_days": 1,
                        "transit_days": 1,
                    },
                )
            )
    for index in range(1, STORE_COUNT + 1):
        store_id = f"STORE-{index:03d}"
        lane_id = f"S{index}-S{index}"
        expanded["lanes"].append(
            lanes.get(
                lane_id,
                {
                    "lane_id": lane_id,
                    "source_id": store_id,
                    "destination_id": store_id,
                    "delivery_type": "STORE_PICKUP",
                    "cutoff_hour_utc": 16,
                    "processing_days": 0,
                    "transit_days": 0,
                },
            )
        )
    return expanded


def generate_history(
    catalog: dict[str, Any], rows: int = 10000, seed: int = 2026
) -> dict[str, Any]:
    """Build linked historical outcomes without changing the supplied catalog."""
    if type(rows) is not int or not 100 <= rows <= 20000:
        raise ValueError("rows must be between 100 and 20000")
    if type(seed) is not int or not 0 <= seed <= 2**32 - 1:
        raise ValueError("seed must be a nonnegative 32-bit integer")
    rng = random.Random(seed)
    catalog = _expand_catalog(catalog)
    data = {
        key: catalog[key]
        for key in ("reference_time", "products", "locations", "lanes", "demo_requests")
    }
    data["snapshots"] = [
        item for item in catalog["snapshots"] if item["snapshot_id"] in BASELINE_LIVE_IDS
    ]
    live_pairs = {(item["product_id"], item["location_id"]) for item in data["snapshots"]}
    live_rng = random.Random(seed ^ 0xA5A5A5A5)
    for product in data["products"]:
        for location in data["locations"]:
            product_id = product["product_id"]
            location_id = location["location_id"]
            if (product_id, location_id) in live_pairs:
                continue
            on_hand = live_rng.randint(20, 100)
            data["snapshots"].append(
                {
                    "snapshot_id": f"LIVE-{product_id}-{location_id}",
                    "product_id": product_id,
                    "location_id": location_id,
                    "observed_at": "2026-11-05T10:00:00Z",
                    "source_updated_at": "2026-11-05T09:00:00Z",
                    "received_at": "2026-11-05T10:00:00Z",
                    "last_count_at": "2026-11-04T10:00:00Z",
                    "on_hand": on_hand,
                    "reserved": live_rng.randint(0, 8),
                    "allocated": live_rng.randint(0, 5),
                    "pending_transactions": 0,
                    "inbound": live_rng.randint(0, 20),
                }
            )
    data["counts"] = []
    data["orders"] = []
    data["events"] = []
    product_ids = [item["product_id"] for item in data["products"]]
    location_ids = [item["location_id"] for item in data["locations"]]
    lanes_by_source = {
        source_id: [lane for lane in data["lanes"] if lane["source_id"] == source_id]
        for source_id in location_ids
    }
    for index in range(rows):
        product_id = rng.choice(product_ids)
        location_id = rng.choice(location_ids)
        lane = rng.choice(lanes_by_source[location_id])
        observed = START + timedelta(hours=rng.randrange(HISTORY_HOURS), minutes=rng.randrange(60))
        stale = rng.random() < 0.2
        age_hours = rng.randint(25, 48) if stale else rng.randint(0, 12)
        on_hand = rng.randint(5, 100)
        reserved = rng.randint(0, min(on_hand, 12))
        allocated = rng.randint(0, min(on_hand - reserved, 8))
        pending = rng.randint(1, 4) if rng.random() < 0.25 else 0
        snapshot_id = f"GEN-{index:05d}"
        snapshot = {
            "snapshot_id": snapshot_id,
            "product_id": product_id,
            "location_id": location_id,
            "observed_at": _timestamp(observed),
            "source_updated_at": _timestamp(observed - timedelta(hours=age_hours)),
            "received_at": _timestamp(observed),
            "last_count_at": _timestamp(observed - timedelta(days=rng.randint(1, 45))),
            "on_hand": on_hand,
            "reserved": reserved,
            "allocated": allocated,
            "pending_transactions": pending,
            "inbound": rng.randint(0, 20),
        }
        data["snapshots"].append(snapshot)
        is_accurate = rng.random() < (0.5 if stale or pending else 0.85)
        deviation = rng.choice((-1, 0, 1)) if is_accurate else rng.choice((-6, -5, -4, 4, 5, 6))
        data["counts"].append(
            {
                "snapshot_id": snapshot_id,
                "product_id": product_id,
                "location_id": location_id,
                "counted_at": _timestamp(observed + timedelta(hours=3)),
                "system_on_hand": on_hand,
                "actual_on_hand": max(0, on_hand + deviation),
            }
        )
        requested = observed + timedelta(hours=1)
        quantity = rng.randint(1, 20)
        raw_available = on_hand - reserved - allocated
        pick_success = raw_available >= quantity and rng.random() < (
            0.7 if stale or pending else 0.94
        )
        picked = quantity if pick_success else rng.randrange(quantity)
        earliest = earliest_delivery_date(requested, lane)
        target = earliest + timedelta(days=rng.randint(0, 3))
        delay = rng.choices((0, 1, 2, 3, 4), weights=(50, 22, 15, 9, 4))[0]
        delivered = datetime.combine(
            earliest + timedelta(days=delay), datetime.min.time(), timezone.utc
        )
        delivered += timedelta(hours=15)
        delivered = max(delivered, requested + timedelta(hours=4))
        data["orders"].append(
            {
                "order_id": f"GEN-O-{index:05d}",
                "snapshot_id": snapshot_id,
                "lane_id": lane["lane_id"],
                "requested_at": _timestamp(requested),
                "quantity": quantity,
                "picked_quantity": picked,
                "picked_at": _timestamp(requested + timedelta(hours=2)),
                "requested_delivery_date": target.isoformat(),
                "delivered_at": _timestamp(delivered),
            }
        )
        if index % 3 == 0:
            event_time = observed - timedelta(days=rng.randint(1, 6))
            data["events"].append(
                {
                    "event_id": f"GEN-E-{index:05d}",
                    "product_id": product_id,
                    "location_id": location_id,
                    "event_type": "SALE",
                    "quantity_delta": -rng.randint(1, 8),
                    "event_time": _timestamp(event_time),
                    "received_at": _timestamp(event_time + timedelta(hours=1)),
                }
            )
    return data


def write_history(data: dict[str, Any], directory: Path = DATA_DIR) -> None:
    """Write category files inside the project's data directory."""
    base = DATA_DIR.resolve()
    destination = directory.resolve()
    if not destination.is_relative_to(base):
        raise ValueError("Output directory must stay inside data")
    destination.mkdir(parents=True, exist_ok=True)
    paths = {
        category: (destination / f"{category}.json").resolve()
        for category in ("metadata", *CATEGORIES)
    }
    for category, path in paths.items():
        if not path.is_relative_to(destination):
            raise ValueError(f"Output path must stay inside data: {category}")
    for category in CATEGORIES:
        paths[category].write_text(
            json.dumps(data[category], ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    paths["metadata"].write_text(
        json.dumps({"reference_time": data["reference_time"]}, indent=2) + "\n", encoding="utf-8"
    )


def main() -> None:
    """Regenerate the bundled historical records with a fixed or supplied seed."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=2026)
    arguments = parser.parse_args()
    try:
        write_history(generate_history(load_sample_data(), arguments.rows, arguments.seed))
    except ValueError as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
