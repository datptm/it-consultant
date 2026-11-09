"""Single-source Promise evaluation shared by rule and ML modes."""

from datetime import date
from typing import Any

from .features import (
    delivery_features,
    fulfillment_features,
    inventory_features,
    parse_time,
)
from .rules import (
    atp,
    confidence_band,
    earliest_delivery_date,
    fulfillment_probability,
    inventory_score,
    on_time_probability,
)


def decide(confidence: float, success: float, is_feasible: bool) -> str:
    """Apply hard feasibility, inventory and promise probability gates."""
    if not is_feasible or confidence < 0.65 or success < 0.85:
        return "REJECT"
    if confidence >= 0.85 and success >= 0.95:
        return "PROMISE"
    return "VERIFY"


def _validate_request(data: dict[str, Any], request: dict[str, Any]) -> tuple[Any, date]:
    product_ids = {product["product_id"] for product in data["products"]}
    destination_ids = {location["location_id"] for location in data["locations"]}
    if request["product_id"] not in product_ids:
        raise ValueError(f"Unknown product: {request['product_id']}")
    if request["destination_id"] not in destination_ids:
        raise ValueError(f"Unknown destination: {request['destination_id']}")
    if type(request["quantity"]) is not int or request["quantity"] <= 0:
        raise ValueError("Quantity must be a positive integer")
    if request["delivery_type"] != "STORE_PICKUP":
        raise ValueError("This PoC supports STORE_PICKUP only")
    at_time = parse_time(request["requested_at"])
    target = date.fromisoformat(request["requested_delivery_date"])
    if target < at_time.date():
        raise ValueError("Requested delivery date cannot be in the past")
    return at_time, target


def evaluate(
    data: dict[str, Any], request: dict[str, Any], mode: str = "rules",
    models: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Evaluate one request against eligible single-source routes."""
    if mode not in {"rules", "ml"}:
        raise ValueError(f"Unknown mode: {mode}")
    at_time, target = _validate_request(data, request)
    if mode == "ml":
        from .ml import predict_success, train_models

        if models is None:
            models = train_models(data)
    candidates = []
    for lane in data["lanes"]:
        if lane["destination_id"] != request["destination_id"] or lane["delivery_type"] != request["delivery_type"]:
            continue
        snapshots = [
            snapshot for snapshot in data["snapshots"]
            if snapshot["product_id"] == request["product_id"]
            and snapshot["location_id"] == lane["source_id"]
            and parse_time(snapshot["observed_at"]) <= at_time
            and parse_time(snapshot["received_at"]) <= at_time
        ]
        if not snapshots:
            continue
        snapshot = max(snapshots, key=lambda item: item["observed_at"])
        features = inventory_features(data, snapshot, at_time)
        if features["stock_age_hours"] > 24:
            continue
        confidence = (
            inventory_score(features) if mode == "rules"
            else predict_success(models["inventory"], features)
        )
        available = atp(snapshot["on_hand"], snapshot["reserved"], snapshot["allocated"], confidence)
        earliest = earliest_delivery_date(at_time, lane)
        if available < request["quantity"] or target < earliest:
            continue
        if mode == "rules":
            fulfillment = fulfillment_probability(request["quantity"], available)
            on_time = on_time_probability(target, earliest)
        else:
            fulfillment = predict_success(
                models["fulfillment"],
                fulfillment_features(data, snapshot, request["quantity"], at_time),
            )
            on_time = predict_success(
                models["delivery"],
                delivery_features(data, snapshot, lane, request["quantity"], at_time, target),
            )
        success = fulfillment * on_time
        decision = decide(confidence, success, True)
        candidates.append({
            "source_id": lane["source_id"], "snapshot_id": snapshot["snapshot_id"],
            "available": available, "earliest": earliest,
            "confidence": confidence, "fulfillment": fulfillment,
            "on_time": on_time, "success": success, "decision": decision,
        })
    if not candidates:
        return {
            "request_id": request["request_id"], "mode": mode,
            "decision": "REJECT", "selected_source_id": None,
            "atp": 0, "earliest_delivery_date": None,
            "promised_delivery_date": None,
            "probabilities": {"inventory_confidence": 0.0, "fulfillment": 0.0,
                              "on_time": 0.0, "promise_success": 0.0},
            "reasons": ["NO_FEASIBLE_SINGLE_SOURCE"],
        }
    rank = {"REJECT": 0, "VERIFY": 1, "PROMISE": 2}
    selected = max(candidates, key=lambda item: (
        rank[item["decision"]], item["success"], item["confidence"],
        -item["earliest"].toordinal(), item["source_id"],
    ))
    reasons = [f"INVENTORY_{confidence_band(selected['confidence'])}", "ATP_SUFFICIENT", "DELIVERY_DATE_FEASIBLE"]
    if selected["decision"] == "VERIFY":
        reasons.append("MANUAL_VERIFICATION_REQUIRED")
    if selected["decision"] == "REJECT":
        reasons.append("PROBABILITY_BELOW_THRESHOLD")
    return {
        "request_id": request["request_id"], "mode": mode,
        "decision": selected["decision"], "selected_source_id": selected["source_id"],
        "snapshot_id": selected["snapshot_id"], "atp": selected["available"],
        "earliest_delivery_date": selected["earliest"].isoformat(),
        "promised_delivery_date": target.isoformat() if selected["decision"] == "PROMISE" else None,
        "probabilities": {
            "inventory_confidence": round(selected["confidence"], 4),
            "fulfillment": round(selected["fulfillment"], 4),
            "on_time": round(selected["on_time"], 4),
            "promise_success": round(selected["success"], 4),
        },
        "reasons": reasons,
    }
