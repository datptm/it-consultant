"""Streamlit demonstration of the synthetic Promise Engine."""

from datetime import date
from typing import Any

import streamlit as st

from promise_poc.data import SAMPLE_PATH, load_sample_data
from promise_poc.engine import evaluate
from promise_poc.features import build_training_rows
from promise_poc.ml import TrainingConfig, train_models
from ui.model_store import ModelStore, ModelStoreError, SavedModels

REASONS = {
    "INVENTORY_HIGH": "High inventory confidence",
    "INVENTORY_MEDIUM": "Medium inventory confidence",
    "INVENTORY_LOW": "Low inventory confidence",
    "ATP_SUFFICIENT": "Enough available stock",
    "DELIVERY_DATE_FEASIBLE": "Requested date is feasible",
    "MANUAL_VERIFICATION_REQUIRED": "Manual verification required",
    "PROBABILITY_BELOW_THRESHOLD": "Predicted success is below the decision threshold",
    "NO_FEASIBLE_SINGLE_SOURCE": "No feasible single source for this request",
}


def _render_result(result: dict[str, Any]) -> None:
    decision = result["decision"]
    if decision == "PROMISE":
        st.success("Decision: PROMISE")
    elif decision == "VERIFY":
        st.warning("Decision: VERIFY")
    else:
        st.error("Decision: REJECT")

    source = result["selected_source_id"]
    if source is None:
        st.write("No feasible single source")
        st.caption("Probabilities are unavailable because no eligible route was found.")
    else:
        source_col, atp_col, earliest_col, promised_col = st.columns(4)
        source_col.metric("Selected source", source)
        atp_col.metric("Available to promise", result["atp"])
        earliest_col.metric("Earliest date", result["earliest_delivery_date"])
        promised_col.metric("Promised date", result["promised_delivery_date"] or "—")
        labels = (
            ("Inventory confidence", "inventory_confidence"),
            ("Fulfillment", "fulfillment"),
            ("On time", "on_time"),
            ("Promise success", "promise_success"),
        )
        for column, (label, key) in zip(st.columns(4), labels):
            column.metric(label, f"{result['probabilities'][key]:.1%}")
    st.write("Reasons: " + "; ".join(REASONS.get(reason, reason) for reason in result["reasons"]))


def _render_scenarios(data: dict[str, Any], saved: SavedModels | None) -> None:
    mode = st.radio("Evaluation mode", ["Rules", "ML"], horizontal=True, key="sample_mode")
    if mode == "ML" and saved is None:
        st.info("Train models in the ML training tab before using ML evaluation.")
        return
    products = {product["product_id"]: product["name"] for product in data["products"]}
    for request in data["demo_requests"]:
        with st.container(border=True):
            st.subheader(f"{request['request_id']} · {products[request['product_id']]}")
            st.caption(
                f"{request['quantity']} units · {request['destination_id']} · "
                f"requested for {request['requested_delivery_date']}"
            )
            result = evaluate(data, request, mode.lower(), saved.models if saved else None)
            _render_result(result)


def _render_evaluator(data: dict[str, Any], saved: SavedModels | None) -> None:
    products = {product["product_id"]: product["name"] for product in data["products"]}
    stores = [
        location["location_id"]
        for location in data["locations"]
        if location["location_type"] == "STORE"
    ]
    st.caption(f"Request time: {data['reference_time']} (fixed sample reference time)")
    with st.form("evaluate_form"):
        product_id = st.selectbox(
            "Product",
            list(products),
            format_func=lambda item: f"{item} · {products[item]}",
            key="product",
        )
        destination_id = st.selectbox("Pickup store", stores, key="destination")
        quantity = st.number_input(
            "Quantity", min_value=1, max_value=10000, value=2, step=1, key="quantity"
        )
        requested_date = st.date_input(
            "Requested pickup date",
            value=date.fromisoformat(data["demo_requests"][0]["requested_delivery_date"]),
            min_value=date.fromisoformat(data["reference_time"][:10]),
            key="delivery_date",
        )
        mode = st.selectbox("Mode", ["Rules", "ML"], key="evaluate_mode")
        submitted = st.form_submit_button("Evaluate", key="evaluate_submit")
    if not submitted:
        return
    if mode == "ML" and saved is None:
        st.info("Train models in the ML training tab before using ML evaluation.")
        return
    request = {
        "request_id": "UI-001",
        "product_id": product_id,
        "quantity": int(quantity),
        "destination_id": destination_id,
        "delivery_type": "STORE_PICKUP",
        "requested_at": data["reference_time"],
        "requested_delivery_date": requested_date.isoformat(),
    }
    try:
        result = evaluate(data, request, mode.lower(), saved.models if saved else None)
    except ValueError as error:
        st.error(f"Invalid request: {error}")
        return
    _render_result(result)


def _render_training(data: dict[str, Any], store: ModelStore, saved: SavedModels | None) -> None:
    st.write("Train three logistic regression models from the bundled synthetic history.")
    st.caption(
        "These tiny training sets have no independent validation or calibrated probabilities."
    )
    if st.session_state.pop("training_complete", False):
        st.progress(100, text="Trained all three models")
        st.success("Training complete. The saved models are ready for ML evaluation.")
    if saved is None:
        st.info("No saved models yet. Train before using ML evaluation.")
    else:
        st.caption(
            f"Latest saved model: C = {saved.config.c:g}, "
            f"max_iter = {saved.config.max_iter}, trained {saved.trained_at}"
        )
    rows = []
    for kind in ("inventory", "fulfillment", "delivery"):
        training_rows = build_training_rows(data, kind)
        positives = sum(label for _, label in training_rows)
        rows.append(
            {
                "Model": kind.title(),
                "Rows": len(training_rows),
                "Positive": positives,
                "Negative": len(training_rows) - positives,
            }
        )
    st.table(rows)
    with st.form("train_form"):
        c = st.number_input(
            "C (inverse regularization strength)",
            min_value=0.01,
            max_value=100.0,
            value=saved.config.c if saved else 1.0,
            step=0.01,
            key="train_c",
        )
        max_iter = st.number_input(
            "Maximum iterations",
            min_value=100,
            max_value=5000,
            value=saved.config.max_iter if saved else 1000,
            step=100,
            key="train_max_iter",
        )
        submitted = st.form_submit_button("Train and save", key="train_submit")
    if not submitted:
        return
    try:
        config = TrainingConfig(c=c, max_iter=max_iter)
        progress_bar = st.progress(0, text="Training inventory model")

        def on_progress(kind: str, completed: int, total: int) -> None:
            progress_bar.progress(int(completed / total * 100), text=f"Trained {kind} model")

        models = train_models(data, config=config, progress=on_progress)
        store.save(models, config, SAMPLE_PATH)
    except (ValueError, ModelStoreError, OSError) as error:
        st.error(f"Training was not saved: {error}")
        return
    st.session_state["training_complete"] = True
    st.rerun()


def main() -> None:
    """Render the local PoC without training during evaluation."""
    st.set_page_config(page_title="Promise Engine PoC", layout="wide")
    st.title("Promise Engine PoC")
    st.caption(
        "Synthetic data only · Store pickup · Illustrative decisions, not real delivery promises"
    )
    data = load_sample_data()
    store = ModelStore()
    try:
        saved = store.load(SAMPLE_PATH)
    except ModelStoreError as error:
        st.warning(str(error))
        saved = None
    sample_tab, evaluate_tab, training_tab = st.tabs(
        ["Sample scenarios", "Evaluate a request", "ML training"]
    )
    with sample_tab:
        _render_scenarios(data, saved)
    with evaluate_tab:
        _render_evaluator(data, saved)
    with training_tab:
        _render_training(data, store, saved)


main()
