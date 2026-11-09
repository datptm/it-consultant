# Synthetic data generation

This guide explains how [`scripts/generate_data.py`](../scripts/generate_data.py) creates the local Promise Engine sample data. The records are invented for a repeatable demonstration. The probabilities below are rules in the generator, not estimates learned from operational data.

## Run and output

From the project root:

```powershell
python -m scripts.generate_data --rows 10000 --seed 2026
```

`--rows` controls the number of **historical situations**, not the total number of records. It defaults to 10,000 and must be an integer from 100 through 20,000. `--seed` defaults to 2026 and must be an integer from 0 through `2**32 - 1`. A given seed and row count reproduce the same output when the input catalog and generator code are unchanged.

The command loads the current category files from `data/`, generates a new data dictionary, and writes `products.json`, `locations.json`, `lanes.json`, `snapshots.json`, `events.json`, `counts.json`, `orders.json`, `demo_requests.json`, and `metadata.json` back under `data/`. Writing replaces the contents of those category files. The output path must resolve inside the project `data/` directory. Changing a category file invalidates the saved web model bundle, so the ML training tab must be used again after generation.

## Catalog, routes, and current inventory

The generator first expands the catalog to 30 named SKUs (`SKU-001` through `SKU-030`), 10 pickup stores (`STORE-001` through `STORE-010`), and three distribution centers (`DC-001` through `DC-003`). Product categories cycle through 10 fixed category names. Existing location and route records with the expected IDs are reused; missing ones receive defaults. Every DC has a pickup route to every store, and every store has a same-store pickup route. This creates 30 DC-to-store routes plus 10 same-store routes. New routes use a 16:00 UTC cutoff; DC routes take one processing and one transit business day, while same-store routes take zero days. Only `STORE_PICKUP` is generated.

The three original current snapshots (`LIVE-DC`, `LIVE-S1`, and `LIVE-S2`) are preserved. For every other SKU/source combination, the generator creates a current snapshot dated 2026-11-05. These additional snapshots have `on_hand` from 20 to 100, `reserved` from 0 to 8, `allocated` from 0 to 5, `pending_transactions = 0`, and `inbound` from 0 to 20. Thus the default catalog has one current snapshot for each of the 30 × 13 = **390** SKU/source combinations. The original seven demo requests and the fixed `reference_time` (`2026-11-05T10:30:00Z`) are carried forward.

Current snapshots support the demo and request evaluation. They are distinct from the generated historical situations used to build ML training labels.

## One historical situation

For each requested historical row, the generator chooses a SKU, a source location, and one of that source's routes. It chooses a snapshot time from a 145-day window starting at 2026-06-01 08:00 UTC. Records are generated in random order; their IDs (`GEN-00000`, `GEN-00001`, and so on) do not indicate chronological order.

Each situation produces one historical snapshot, one later physical count, and one linked order. The count and order both contain the snapshot's `snapshot_id`. The order also contains a route ID. The key times are:

| Record or event | Time relative to snapshot observation |
|---|---|
| Inventory snapshot received | At observation time |
| Order requested | 1 hour later |
| Order picked | 3 hours later, or 2 hours after the request |
| Inventory physically counted | 3 hours later |
| Delivery recorded | At the calculated delivery time, always at least 4 hours after the request |

All timestamps are UTC. The later count, pick result, and delivery result are outcomes used for labels; they are not available as features at the earlier prediction time.

### Snapshot inputs

| Field or condition | Generation rule |
|---|---|
| `stale` | A random draw marks about 20% of snapshots stale. |
| Source data age | 25–48 hours if stale; otherwise 0–12 hours. `source_updated_at = observed_at - age`. |
| `on_hand` | Random integer from 5 to 100. |
| `reserved` | Random integer from 0 to `min(on_hand, 12)`. |
| `allocated` | Random integer from 0 to `min(on_hand - reserved, 8)`. |
| `pending_transactions` | About 25% receive a random value from 1 to 4; the rest receive 0. |
| `last_count_at` | 1–45 days before observation. |
| `inbound` | Random integer from 0 to 20. |

The stale flag is expressed in the stored record through `source_updated_at`; there is no separate `stale` JSON field. The snapshot's `received_at` equals its `observed_at`. The script gives each historical snapshot its own independently drawn stock figures; it does not maintain a continuous inventory ledger between snapshots.

## How the three outcomes are generated

### 1. Inventory count accuracy

The script draws whether a count is accurate using the snapshot's stale state and pending transactions:

| Condition | Chance of an accurate count |
|---|---:|
| Stale **or** `pending_transactions > 0` | 50% |
| Neither condition | 85% |

If accurate, it adds a deviation chosen from `-1`, `0`, or `+1` to `on_hand`. Otherwise, the deviation is chosen from `-6`, `-5`, `-4`, `+4`, `+5`, or `+6`. The stored `actual_on_hand` is clamped to zero; `system_on_hand` is the snapshot's original `on_hand`. The count is recorded three hours after observation.

The Inventory ML label is `1` when `abs(snapshot.on_hand - actual_on_hand) <= 1`, and `0` otherwise. The accuracy probabilities are therefore baked into the synthetic label distribution. They do not measure real-world count accuracy.

### 2. Full picking of an order

The requested quantity is a random integer from 1 to 20. The generator computes:

```text
raw_available = on_hand - reserved - allocated
```

If `raw_available < quantity`, picking cannot succeed. Otherwise it draws success with a 70% chance when stock is stale **or** has pending transactions, and a 94% chance when neither condition applies. On success, `picked_quantity = quantity`; on failure, it is a random integer from 0 through `quantity - 1`.

The Fulfillment ML label is `1` when `picked_quantity >= quantity`. This generator uses raw availability for the pick outcome. The decision engine separately applies its inventory confidence, safety buffer, ATP, freshness, and date checks when evaluating a new request. `inbound` is generated but is not added to raw availability or ATP.

### 3. Delivery date

The script calls the same `earliest_delivery_date` function used by the rules engine. That function applies the route's UTC cutoff and skips weekends when advancing processing and transit **business days**. The requested pickup date is the earliest date plus a random 0–3 **calendar days**.

A separate draw adds a delivery delay to the earliest date:

| Delay in calendar days | 0 | 1 | 2 | 3 | 4 |
|---|---:|---:|---:|---:|---:|
| Draw weight | 50% | 22% | 15% | 9% | 4% |

Delivery is recorded at 15:00 UTC on that calculated date, unless that would be earlier than four hours after the order request; in that case the later time is used. The delay and requested-date slack use calendar days, so they can produce weekend dates even though route processing and transit skip weekends.

The Delivery ML label is `1` when the delivery **date** is on or before the requested date. Every generated order has a `delivered_at` field, including failed picks, but the Delivery training set includes only orders picked in full. Consequently, its label is conditional on full picking, and its row count is smaller than the Inventory and Fulfillment counts.

## Sales events

For historical row indices divisible by three, including index zero, the generator creates one `SALE` event for the same SKU and source. It occurs 1–6 days before the snapshot, has a negative quantity change of 1–8 units, and is marked received one hour after its event time. With 10,000 historical rows this produces **3,334** events.

Events provide a historical sales-velocity feature when they were available before a prediction time. The generator does not apply them to update `on_hand`, and its count, pick, and delivery outcome formulas do not directly use event quantity. A single event may be visible to later snapshots of the same SKU and source if its timestamp is in their feature window.

## Counts and ML evaluation

With the default 10,000 rows, the generated data contains 10,000 historical snapshots, 10,000 counts, 10,000 orders, and 390 current snapshots, for 10,390 snapshots in total. The bundled default-seed history yields 10,000 Inventory examples, 10,000 Fulfillment examples, and 7,071 Delivery examples because only fully picked orders enter the last set. Those exact outcome counts can change with a different seed or row count.

The Streamlit training flow sorts examples by the time at which a prediction would have been made. It trains on the earliest 70%, reports metrics on the next 15% (validation), and reports metrics on the final 15% (test), separately for each model. This chronological split checks whether a model recognizes patterns in later **synthetic** records. It does not validate performance or probability calibration against real transactions.

The main limitations follow directly from the generator: stock levels across snapshots do not form a consistent ledger; sale events do not cause stock changes; count accuracy and picking success are explicitly tied to stale data and pending transactions; delivery delay is drawn from fixed weights rather than operational conditions. A model may score well by learning those programmed relationships. See [Data, features, and models](data-features-models.md) for the exact features and the decision engine's use of the labels.
