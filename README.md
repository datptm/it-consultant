# Promise Engine PoC

A CLI and Streamlit proof of concept for the three components described in [`docs/resources/methodology.md`](docs/resources/methodology.md): inventory confidence, fulfillment probability, and on-time delivery probability. The category files in [`data/`](data/) are entirely synthetic.

For details of the data, feature and label creation, and three trained models, see [`docs/data-features-models.md`](docs/data-features-models.md).

## Install and run

Python 3.13 is required. From the project root:

```powershell
python -m pip install -e . -r requirements.txt
python -m promise_poc demo --mode rules
python -m promise_poc demo --mode ml
python -m promise_poc evaluate --product-id SKU-001 --quantity 2 --destination-id STORE-001 --date 2026-11-10 --mode ml
python -m streamlit run ui/app.py
python -m scripts.generate_data --rows 10000 --seed 2026
python -m unittest discover -s tests -v
python -m ruff check src ui tests
python -m ruff format --check ui
```

`demo` returns seven JSON results. `evaluate` accepts a delivery date in `YYYY-MM-DD` format and optionally `--at 2026-11-05T10:30:00Z`. Without `--at`, the CLI uses the sample data's `reference_time` so repeated runs produce the same result. The PoC supports only `STORE_PICKUP` and a single supply source. Working days are Monday through Friday, cutoff times are in UTC, and holidays are not accounted for.

In `ml` mode, the CLI retrains three logistic regression models in memory on every invocation. Labels come from inventory counts, picked quantities, and actual delivery dates; features use only data available before the request time. The bundled data has 30 products, 10 pickup stores, three distribution centers, 10,000 generated historical snapshots, counts, and orders, plus 390 current snapshots. Web training uses later synthetic rows for validation and test scores, but there is no independent real-world dataset or probability calibration. Probabilities in both modes illustrate the decision process and **must not be used for real delivery commitments**. Checks for source data older than 24 hours, ATP, and delivery dates apply in both modes.

The generator writes `products.json`, `locations.json`, `lanes.json`, `snapshots.json`, `events.json`, `counts.json`, `orders.json`, `demo_requests.json`, and `metadata.json` under `data/`. The same seed and row count produce the same records. It builds a catalog of 30 products, 10 stores, and three DCs, with 30 DC-to-store routes and 10 same-store pickup routes; preserves the three original live snapshots and all bundled demo requests; creates live stock for the remaining product/location pairs; and replaces historical records. Saved web models become incompatible after any category file changes and must be retrained.

Product names are English descriptions of construction and hardware items. SKU IDs and categories remain fixed when the history is regenerated.

Historical rows span June through October 2026. Each snapshot has a later inventory count and a linked order on a lane from its source. The generator varies stock age, reservations, pending transactions, count discrepancies, requested quantities, pick outcomes, and delivery delays. It makes accurate counts and full picks less likely when stock is stale or transactions are pending. These rules create useful patterns for exploration, but they also encode assumptions into the labels; the resulting accuracy and on-time rates are properties of the generator. See [Synthetic data generation](docs/synthetic-data-generation.md) for the exact rules and record timeline.

## Web interface

Run `python -m streamlit run ui/app.py` from the project root and open the address shown by Streamlit. The English interface has four tabs:

- **Sample scenarios:** view seven named requests in Rules or ML mode, with large labeled values for quantity, store, pickup date, request time, and delivery method.
- **Evaluate a request:** choose a product, quantity, pickup store, desired date, and evaluation mode. The request time is always the sample data's `reference_time` for repeatable results.
- **ML training:** view row and label counts for the three training sets, adjust shared `C` and `max_iter` values, then click **Train and save**. The progress bar updates after each model. After training, the tab shows the chronological 70% train / 15% validation / 15% test split and validation/test accuracy, precision, and recall for each model. These results are saved with the models and remain visible after reloading the page.
- **Data analytics:** inspect label balance, inventory accuracy, full-pick and on-time rates, and outcome counts by product and source location.

The bundled scenarios cover the main decision and feasibility paths:

| Request | Scenario | Rules result |
|---|---|---|
| REQ-001 | DC fulfillment | PROMISE |
| REQ-002 | Insufficient stock at any single source | REJECT |
| REQ-003 | Pickup from store stock | PROMISE |
| REQ-004 | Pickup date before any eligible source can supply | REJECT |
| REQ-005 | Limited stock margin | VERIFY |
| REQ-006 | Low inventory confidence despite enough stock and time | REJECT |
| REQ-007 | Inventory older than the 24-hour freshness limit | REJECT |

Each scenario uses its displayed request time. REQ-006 uses a historical time, and REQ-007 uses a time two days after the sample reference. The descriptions and outcomes above apply to the bundled default-seed data; ML decisions or outcomes after regenerating history with other settings may differ.

The web interface uses only an ML model previously trained and saved with `skops` at `ui/.local/latest.skops` (this directory is excluded from version control). If the model is missing or corrupt, or the sample data or scikit-learn version changes, retrain it in the **ML training** tab. Changing form parameters has no effect on evaluation results until training and saving succeed. Unlike the web interface, the CLI's `--mode ml` retrains on every run. No data is uploaded or written to operational systems.
