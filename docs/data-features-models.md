# Promise Engine PoC data, features, and trained models

This document describes the **working core** of the PoC: its inputs, how they become features and labels, the three trained models, and how their outputs are used to evaluate a request. The authoritative sources for this PoC are the category files in [`data/`](../data/), [`features.py`](../src/promise_poc/features.py), [`ml.py`](../src/promise_poc/ml.py), [`rules.py`](../src/promise_poc/rules.py), and [`engine.py`](../src/promise_poc/engine.py). Broader ideas are described in [`docs/resources/methodology.md`](resources/methodology.md); fields and techniques mentioned only there **are not necessarily implemented** here.

## 1. Three questions the models address

For a request for product `p`, quantity `q`, pickup location `d`, and desired date `D`, the engine evaluates each supply source `s` using three measures:

| Measure | Question | Training label |
|---|---|---|
| `inventory_confidence` | Does the inventory snapshot of `(p, s)` closely match the actual count? | Deviation is no more than **1 unit**. |
| `fulfillment` | Can all `q` units be picked at `s`? | `picked_quantity >= quantity`. |
| `on_time` | Given the lane from `s` to `d` and date `D`, do the goods arrive by `D`? | `date(delivered_at) <= D`; only orders picked in full are considered. |

`inventory_confidence` measures the reliability of **the inventory figure**, not the probability of picking an entire order. Inventory also determines a safety buffer and ATP; `fulfillment` answers a different question that includes the requested quantity. The engine calculates `promise_success = fulfillment × on_time` for feasible sources. In the current training set, the delivery model only sees orders picked in full, so its output is closer to `P(on time | picked in full, delivery features)` than an unconditional on-time probability. Multiplying the outputs gives an **illustrative estimate** that has not been validated or calibrated as an actual success probability.

Two modes use the same data and hard constraints:

- `rules`: scores and probabilities come from fixed, inspectable rules; they are not learned from labels.
- `ml`: three separate classifiers are trained from historical labels; the data quality, ATP, lane, and delivery date rules still apply.

## 2. Sample data and the purpose of each group

All records are **synthetic data**. The time uses ISO 8601 UTC string with suffix `Z`; quantity is integer units of SKU. `reference_time = 2026-11-05T10:30:00Z` ensures CLI commands run the same scenario again. `data/metadata.json` stores this time; each other category has its own JSON array. The default seed produces 30 products, 10 pickup stores and three DCs, 40 routes, 10,000 historical snapshots and 390 current snapshots, 10,000 inventory counts, 10,000 historical orders, and 7 demo requests. The generator is [`scripts/generate_data.py`](../scripts/generate_data.py).

### 2.1. Catalog and routes

| Group | Field | Role in PoC |
|---|---|---|
| `products` | `product_id`, `name`, `category` | Verify SKU existence. `name` and `category` are for description only; not yet part of the feature. |
| `locations` | `location_id`, `location_type`, `country` | Verify the pickup location and match sources with snapshots; `location_type` (`STORE`/`DC`) is a feature. `country` is not used for prediction. |
| `lanes` | `lane_id`, `source_id`, `destination_id`, `delivery_type` | Specify which sources can serve a pickup location and by which delivery method. The PoC uses only `STORE_PICKUP`. |
| `lanes` | `cutoff_hour_utc`, `processing_days`, `transit_days` | Calculate the earliest delivery date from the cutoff and number of business days. `cutoff_hour_utc` is an integer UTC hour. |

Two locations can share the same SKU, but only if there is a suitable route and a snapshot of the SKU at that source. Each option only picks from **one** source; the `lane_id` of the historical order connects the order to the route used when creating the delivery feature.

`DC` means **distribution center**: `DC-001`, `DC-002`, and `DC-003` hold stock and ship it to pickup stores. They are supply sources, not pickup destinations in the UI. `STORE` means a customer pickup location; a store can also supply its own pickup request from stock on hand. Each DC has a route to every store (one processing plus one transit business day), and each store has a same-store pickup route (zero processing and transit days). The original DC uses lane IDs `DC-Sn`; the other DCs use `DC2-Sn` and `DC3-Sn`. Both source types require a usable inventory snapshot and pass the same stock and date feasibility checks. Source type is a categorical ML feature; the current rules do not give DC and STORE separate confidence formulas.

### 2.2. Inventory status and quality signals

| Group | Field | Meaning and usage |
|---|---|---|
| `snapshots` | `snapshot_id`, `product_id`, `location_id` | Identify an inventory snapshot for a SKU at a source. `snapshot_id` also links the inventory count/historical order to the corresponding snapshot. |
| `snapshots` | `observed_at` | Reference time for historical inventory features. At inference time, only snapshots with `observed_at <= requested_at` are eligible. |
| `snapshots` | `source_updated_at` | Last update in the source system; used to calculate data age, `stock_age_hours`. |
| `snapshots` | `received_at` | When PoC receives a record; must not be later than the evaluation time. Unlike `source_updated_at`: data can be new at the source but arrive at PoC late. |
| `snapshots` | `last_count_at` | Time of the most recent count recorded in the snapshot; used to calculate `days_since_last_count` and as the lower bound when looking for historical count discrepancies. |
| `snapshots` | `on_hand`, `reserved`, `allocated` | Recorded stock, reserved stock, and allocated stock. Inputs to ATP. |
| `snapshots` | `pending_transactions` | Unsynchronized transactions; it's a stock/fulfillment feature and a deduction condition in rules. |
| `snapshots` | `inbound` | Items en route, data available in the sample but **not counted in ATP**. |
| `events` | `event_id`, `product_id`, `location_id`, `event_type`, `quantity_delta` | Stock fluctuations. Currently, only `SALE` is used to calculate the sales rate; `quantity_delta` is negative when selling. |
| `events` | `event_time`, `received_at` | Time the event occurred and time the PoC received it. Both are checked when building features. |
| `counts` | `snapshot_id`, `product_id`, `location_id`, `counted_at` | Post-snapshot inventory check to create labels; inventory checks that occurred before the new evaluation point can be used as historical signals. |
| `counts` | `system_on_hand`, `actual_on_hand` | System count and actual count. Historical discrepancy feature uses both fields; **inventory label** compares `snapshot.on_hand` with `actual_on_hand`, does not use `count.system_on_hand`. |

Do not add `events` again to `on_hand`: snapshot is the system inventory count at its point in time, while PoC events only provide sales rate signals. Doing both can easily double-count stock fluctuations.

### 2.3. Historical orders and requests to evaluate

| Group | Field | Meaning and usage |
|---|---|---|
| `orders` | `order_id`, `snapshot_id`, `lane_id` | Link an order outcome to the snapshot and lane known when the decision was made. |
| `orders` | `requested_at`, `quantity`, `requested_delivery_date` | Request time, quantity, and desired date; features or inputs for feature calculations. |
| `orders` | `picked_quantity`, `picked_at` | Picking outcomes, **used only as the fulfillment label** and to select eligible orders for the delivery model. |
| `orders` | `delivered_at` | Delivery results, **only use as labels** for on-time. |
| `demo_requests` | `request_id`, `product_id`, `quantity`, `destination_id`, `delivery_type`, `requested_at`, `requested_delivery_date` | Requests for inference. The `evaluate` command accepts the key values; without `--at`, it uses `reference_time`. |

Generated historical orders cover all 30 SKUs and all 13 source locations. `products.category` and SKU identification are not features of the three current models, so differences across products are visible in the analytics tab but not learned directly.

## 3. Time rule: what data is allowed to become a feature?

Define `t` as the evaluation time. A feature must be calculated from existing data that has reached PoC no later than `t`; labels can appear after `t`. This is the main boundary to avoid *data leakage*.

1. **Select snapshot when inferring:** for each `(product_id, source_id)`, select the latest snapshot according to `observed_at` among those with `observed_at <= t` and `received_at <= t`. If no suitable snapshot exists, discard the source.
2. **Self-check snapshot:** `source_updated_at`, `last_count_at`, and `received_at` must all be `<= t`; if not, create a feature error. The engine discards the source if `stock_age_hours > 24`.
3. **Sales events:** include only `SALE` events for the matching product and source, with `event_time` in the seven days immediately before `t` and `received_at <= t`. A transaction that occurred before `t` but arrived after `t` cannot explain a past decision.
4. **Historical counts:** consider only counts for the matching product and source with `last_count_at <= counted_at <= t`; choose the latest `counted_at`. If none is eligible, the historical discrepancy feature is `0` in this PoC. A value of `0` means **no known discrepancy signal**, not proof that the data is accurate. The sample has no `received_at` for counts, so the code treats `counted_at` as the time the result became known; real data would need separate timestamps.
5. **Inventory training:** feature taken at `snapshot.observed_at`; inventory count connected by `snapshot_id` and required `counted_at > observed_at`, then create label.
6. **Fulfillment/delivery training:** feature taken at `order.requested_at`; related snapshot must have `received_at <= requested_at`. `picked_at` must come after `requested_at`; `delivered_at` must come after `requested_at` for delivery items in the delivery model.

These checks prevent some forms of future data from entering features. This is an illustrative dataset: there is no immutable snapshot store or reconciliation of transactions between a snapshot and its count. A label derived from a later count could therefore be affected by intervening transactions if the same method were applied unchanged to real data.

## 4. Features of each model

### 4.1. Inventory Confidence

A feature row corresponds to **a snapshot of a SKU at a source, viewed at the moment `t`**.

| Feature | Type/Unit | Formula or source | Meaning |
|---|---|---|---|
| `stock_age_hours` | Real number, hours | `(t - source_updated_at) / 1 hour` | Age of the source data. |
| `days_since_last_count` | Real number, days | `(t - last_count_at) / 1 day` | Time since the last count; it can be fractional. |
| `sales_velocity_7d` | Real number, units/day | Total `abs(quantity_delta)` for eligible `SALE` events in seven days, divided by `7` | Observed sales rate over a fixed window. |
| `historical_discrepancy` | Real number, ratio | With the latest valid inventory: `abs(system_on_hand - actual_on_hand) / max(actual_on_hand, 1)`; missing record then `0` | Known inventory deviation. |
| `pending_transactions` | Integer | `snapshot.pending_transactions` | Out-of-sync transaction signal. |
| `on_hand` | Integer, unit | `snapshot.on_hand` | System inventory scale. |
| `location_type` | Categorical string | `STORE` or `DC` from `locations` | Type of supply source. |

`stock_age_hours` and `days_since_last_count` are calculated from the evaluation time, not the CLI's wall clock. `sales_velocity_7d` is total units sold divided by seven even if only one sale occurred in the seven-day window. There are no 30-day features, inventory adjustment rates, inbound reliability measures, or product group codes, although the methodology proposes them.

### 4.2. Fulfillment

One feature corresponds to **one order at a source at the request time**.

| Feature | Type/Unit | Formula or source | Meaning |
|---|---|---|---|
| `requested_quantity` | Integer, units | `order.quantity` or the new request quantity | Quantity that must be picked in full. |
| `raw_available` | Integer, unit | `on_hand - reserved - allocated` | Number to consider before applying safety buffer. **Not ATP.** |
| `pending_transactions` | Integer | The current snapshot | Risk from unsynchronized data. |
| `stock_age_hours` | Real number, hour | Same calculation as Inventory Confidence | Source data freshness. |
| `location_type` | Categorical string | Source type from `locations` | Distinguishes stores from DCs if the training data permits. |

The fulfillment model **does not** use `inventory_confidence` or `effective_atp` directly as features. This avoids building training features from *in-sample* predictions by the inventory model and then using a different definition at inference time. The engine still enforces ATP as a hard constraint before using the fulfillment output.

### 4.3. On-time Delivery

A feature row represents **one lane, quantity, and proposed delivery date at request time**.

| Feature | Type/Unit | Formula or source | Meaning |
|---|---|---|---|
| `quantity` | Integer, units | Requested quantity | Order size. |
| `lead_days` | Integer, calendar days | `requested_delivery_date - date(requested_at)` | Days allowed between order placement and the desired date. |
| `slack_days` | Integer, calendar days | `requested_delivery_date - earliest_delivery_date` | Time beyond the earliest date calculated by lane rules. |
| `delivery_type` | Classification string | `lane.delivery_type` | Receipt form; current sample only `STORE_PICKUP` |
| `source_type` | Categorical string | Type of shipping location | `STORE` or `DC`. |

The earliest delivery date is calculated **before** prediction: if an order is placed on a weekend or at or after the cutoff, the calculation starts on the next business day; it then adds `processing_days + transit_days`, skipping Saturday and Sunday at each step. The PoC uses UTC and has no holiday calendar. `lead_days` and `slack_days` are differences in **calendar days**, whereas processing and transit use **business days**. Carrier, distance, warehouse load, weather, and historical lane delays are not yet used.

## 5. Creating labels and training sets

| Model | A row starts from | Label `1` | Label `0` | Sample count |
|---|---|---|---|---|
| Inventory | A `count` connected to snapshot via `snapshot_id` | `abs(snapshot.on_hand - count.actual_on_hand) <= 1` | Large deviation greater than 1 | 10,000: **7,246/2,754** |
| Fulfillment | An `order` linked to a snapshot by `snapshot_id` | `picked_quantity >= quantity` | Picked too few items | 10,000: **7,071/2,929** |
| Delivery | An `order` picked in full and linked to a snapshot and lane | `date(delivered_at) <= requested_delivery_date` | Delivered after the desired date | 7,071: **5,425/1,646** |

The analytics tab shows current counts of labels `1`/`0`; these are **not** real business success rates. Orders with insufficient picks are excluded from the Delivery set, but retain fulfillment label `0`. The PoC compares the **delivery date**, not the time within that day. Inventory tolerance is fixed at **1 unit**, with no configuration by item type or stock level. The code cannot distinguish customer cancellations, carrier failures, changes to promised dates, or unverified counts because the sample lacks those statuses.

To see the difference between feature and label: an inventory feature is built at the snapshot's `observed_at` time, while the connected count's `actual_on_hand` is observed later and supplies the label. A difference of at most one unit is positive; a larger difference is negative. The actual count value and count timestamp are never included in that snapshot's feature dictionary.

## 6. Current ML Training

[`train_models`](../src/promise_poc/ml.py) performs the same process for `inventory`, `fulfillment`, `delivery`:

1. Call `build_training_rows(data, kind)` to receive the list `(feature_dict, label 0/1)` as defined above.
2. Refuse to train if the model's dataset does not contain **both label classes**.
3. By default, create a `DictVectorizer()` → `StandardScaler(with_mean=False)` → `LogisticRegression(C=1, max_iter=1000)` pipeline for the CLI; the web interface can change `C` and `max_iter`. `DictVectorizer` retains numeric features and turns categorical strings into indicator columns; scaling keeps the numeric ranges tractable for the larger dataset; logistic regression learns weights to estimate the probability of class `1`.
4. `fit` on **all** rows for that model. At inference time, call `predict_proba` and take the column for class `1`.

Each time CLI `--mode ml` is used, all three pipelines are retrained **in memory** from the category files in `data/`; CLI does not use model files, registry, or incremental learning steps. Default `C=1`, `max_iter=1000`; other parameters use defaults from the installed scikit-learn version. CLI training still fits all available rows. PoC does not include handling missing values, class balancing, hyperparameter selection, external validation data, or probability calibration. Therefore, numbers like `0.82` or `0.99` from `predict_proba` **cannot be interpreted** as proven success rates.

Streamlit interface at `ui/app.py` separates training from ML evaluation: the **ML training** tab adjusts `C` (0.01–100) and `max_iter` (100–5000) shared across all three pipelines. For each model it sorts examples by prediction time, fits the earliest 70%, then scores the next 15% as validation and final 15% as test. It displays each split's row count and accuracy, precision, and recall (positive class `1`; zero precision or recall when the denominator is zero). The fitted models and report are saved together in a `skops` bundle at `ui/.local/latest.skops`. The evaluation tab only loads the saved bundle and does not retrain; if the bundle is missing or incompatible with the scikit-learn version or the sample data content, the user must retrain. Older saved bundles can still be loaded but have no report until retrained. The bundle is only for local demo purposes and not a model registry or model quality evidence.

The generated history includes all 30 SKUs and all 13 source locations, but SKU and source ID are not model features. The held-out scores measure these synthetic patterns only. Do not use them to make commercial commitments.

## 7. From feature to decision: where do rules and ML differ?

### 7.1. Rule scores and shared ATP calculation

Rules mode begins with `inventory_confidence = 1,00` and subtracts the following penalties. A `>` comparison is **strict**: equality does not trigger a penalty.

| Condition | Points deducted |
|---|---:|
| `days_since_last_count > 30` | 0,15 |
| `pending_transactions > 0` | 0,20 |
| `historical_discrepancy > 0,10` | 0,20 |
| `sales_velocity_7d > 5` units/day | 0,10 |
| `stock_age_hours > 24` | 0,15 |

The final score has a lower bound of `0`. Separately, `stock_age_hours > 24` is a **source exclusion condition** in the engine, even if the score would otherwise remain in the `HIGH` band. Both modes use their own inventory confidence value to calculate:

```text
safety_buffer = ceil(on_hand × (1 − inventory_confidence) × 0,5)
ATP = max(0, on_hand − reserved − allocated − safety_buffer)
```

`inbound` is excluded from the formula. `ceil` rounds the safety buffer up to an integer, making ATP more conservative when confidence is low. The engine then excludes a source if `ATP < requested_quantity` or the requested date precedes the lane's earliest delivery date. The ML model **cannot override** either exclusion.

### 7.2. Three outputs in two modes

| Output | `rules` | `ml` |
|---|---|---|
| Inventory | Penalty in the table above. | Probability of class `1` for the Inventory model from 7 features in section 4.1. |
| Fulfillment | If ATP is deficient: source is eliminated. If sufficient and has at least 2 units surplus: `0,99`; if sufficient but has less than 2 units surplus: `0,90`. | Probability of class `1` for the Fulfillment model from 5 features in section 4.2, after passing through the ATP gate. |
| On-time | If the desired date is after the earliest date: `0,99`; if it matches the earliest date: `0,96`. Early dates are eliminated. | Probability of class `1` for the Delivery model from 5 features in section 4.3, after passing through the delivery date gate. |

The fixed rules values `0,90`, `0,96`, and `0,99` are **illustrative parameters**, not estimates from actual success rates. The engine multiplies the Fulfillment and On-time outputs **before rounding**; JSON rounds each probability to four decimal places.

### 7.3. Thresholds and source selection

| Conditions after the source passes through ATP/delivery date | Decision |
|---|---|
| `inventory_confidence < 0,65` **or** `promise_success < 0,85` | `REJECT` |
| `inventory_confidence >= 0,85` **and** `promise_success >= 0,95` | `PROMISE` |
| The remaining cases | `VERIFY` |

The inventory ranges used in `reasons` are `HIGH` from `0,85`, `MEDIUM` from `0,65` to below `0,85`, `LOW` below `0,65`. When there are multiple sources, the engine prioritizes deciding `PROMISE` over `VERIFY` over `REJECT`; at the same priority level, it compares success probability, confidence, earliest date first, then `source_id` in descending lexicographical order. Therefore, the selected source is not necessarily the one with the highest probability if the decision level differs. If there are no feasible sources, the result is `REJECT` with `NO_FEASIBLE_SINGLE_SOURCE`; the promised date only appears when the decision is `PROMISE`.

## 8. A manual case on sample data

`REQ-001` requests **2** units of `SKU-001` for pickup at `STORE-001`, placed at `2026-11-05T10:30:00Z`, with a desired date of `2026-11-10`. Lane `DC-S1` can ship from `DC-001`; its cutoff is 16:00 UTC, processing takes one business day, and transit takes one business day.

1. Snapshot `LIVE-DC` at 10:00 has `on_hand = 100`, `reserved = 10`, `allocated = 0`, `pending_transactions = 0`, `source_updated_at = 09:00`. At 10:30: `stock_age_hours = 1,5`, `days_since_last_count ≈ 1,0208`, `sales_velocity_7d = 0`, `historical_discrepancy = 0` within the current window. With no penalty conditions applied, the confidence rules are `1,00`.
2. `safety_buffer = ceil(100 × (1 − 1,00) × 0,5) = 0`; `ATP = 100 − 10 − 0 − 0 = 90`, sufficient for 2 units. `inbound = 20` in the snapshot does not increase ATP.
3. Placed before the cutoff on Thursday 05/11; two business days later is Monday **09/11**. The desired date 10/11 is later than the earliest date, so rules mode assigns `on_time = 0,99`. ATP exceeds the request by at least two units, so rules mode assigns `fulfillment = 0,99`.
4. `promise_success = 0,99 × 0,99 = 0,9801`. Confidence `1,00 >= 0,85` and success `0,9801 >= 0,95`, so this candidate qualifies for `PROMISE`. The other two DCs also qualify with equal probability, confidence, and earliest date; the final tie-break selects `DC-003`. The promised date is `2026-11-10`.

ML mode uses **the same snapshot, lane, request, and ATP/date gates**, but replaces the three rules-based values with model predictions. Limited data can make the ML decision differ from rules, including a `REJECT` for this example; that reflects the sample's limitations, not evidence that ML is safer.

## 9. How to reproduce and interpret limitations

After installing [`README.md`](../README.md), run from the root directory:

```powershell
python -m promise_poc demo --mode rules
python -m promise_poc demo --mode ml
python -m promise_poc evaluate --product-id SKU-001 --quantity 2 --destination-id STORE-001 --date 2026-11-10 --mode ml
```

The `demo` commands return seven requests covering DC fulfillment, store pickup, stock shortage, an infeasible date, manual verification for a narrow stock margin, rejection for low inventory confidence, and stale inventory. Optional `scenario_name` and `description` fields explain each case in the UI; they are not model features. Each request has its own evaluation time, including a historical low-confidence case and a later stale-data case. The expected Rules outcomes in README apply to the bundled default-seed history; different generator settings or ML predictions may change them. The CLI does not record feedback or retrain after a decision; a later ML run still learns from the same generated history unless the files are regenerated. A serious probability evaluation still requires reliable real-world historical data, error analysis by SKU/source/lane, and calibration measures such as Brier score on held-out data. These steps **are not part of the current PoC**.
