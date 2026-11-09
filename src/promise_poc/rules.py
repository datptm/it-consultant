"""Deterministic inventory and delivery baselines."""

from datetime import date, datetime, timedelta
from math import ceil


def inventory_score(features: dict[str, float | int | str]) -> float:
    """Return a pilot inventory score in [0, 1] from documented penalties."""
    penalty = 0
    if features["days_since_last_count"] > 30:
        penalty += 15
    if features["pending_transactions"] > 0:
        penalty += 20
    if features["historical_discrepancy"] > 0.1:
        penalty += 20
    if features["sales_velocity_7d"] > 5:
        penalty += 10
    if features["stock_age_hours"] > 24:
        penalty += 15
    return max(0.0, (100 - penalty) / 100)


def confidence_band(confidence: float) -> str:
    """Classify the inventory score using the pilot thresholds."""
    if confidence >= 0.85:
        return "HIGH"
    if confidence >= 0.65:
        return "MEDIUM"
    return "LOW"


def atp(on_hand: int, reserved: int, allocated: int, confidence: float) -> int:
    """Calculate nonnegative integer ATP with a rounded-up safety buffer."""
    if min(on_hand, reserved, allocated) < 0 or not 0 <= confidence <= 1:
        raise ValueError("Inventory quantities and confidence must be valid")
    buffer = ceil(on_hand * (1 - confidence) * 0.5)
    return max(0, on_hand - reserved - allocated - buffer)


def _next_business_day(day: date) -> date:
    next_day = day + timedelta(days=1)
    while next_day.weekday() >= 5:
        next_day += timedelta(days=1)
    return next_day


def earliest_delivery_date(requested_at: datetime, lane: dict[str, int]) -> date:
    """Apply UTC cutoff and weekday-only processing plus transit days."""
    if requested_at.tzinfo is None:
        raise ValueError("requested_at must include UTC timezone")
    day = requested_at.date()
    if day.weekday() >= 5 or requested_at.hour >= lane["cutoff_hour_utc"]:
        day = _next_business_day(day)
    for _ in range(lane["processing_days"] + lane["transit_days"]):
        day = _next_business_day(day)
    return day


def fulfillment_probability(quantity: int, available: int) -> float:
    """Estimate picking success from sufficient ATP and spare units."""
    if available < quantity:
        return 0.0
    return 0.99 if available - quantity >= 2 else 0.90


def on_time_probability(target: date, earliest: date) -> float:
    """Estimate delivery success from the calendar slack."""
    if target < earliest:
        return 0.0
    return 0.99 if target > earliest else 0.96
