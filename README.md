# Promise Engine PoC

A local Python CLI and Streamlit demo for exploring whether a product can be promised for pickup at a store on a requested date. It combines inventory confidence, fulfillment probability, and on-time delivery probability with hard checks for stock availability, data freshness, and pickup-date feasibility. Each request returns a `PROMISE`, `VERIFY`, or `REJECT` decision with reasons. The app uses only [synthetic sample data](data/) and is not connected to operational systems.

The PoC supports only `STORE_PICKUP`; each request must be fulfilled from one source, without splitting stock. [Technical specification](docs/resources/technical-specification.md) describes the decision rules; [Data, features, and models](docs/data-features-models.md) explains the training data and predictions.

## Install

Use Python 3.13 or newer. In PowerShell, run these commands from the project root (the directory containing `pyproject.toml`):

```powershell
python --version
python -m pip install -e . -r requirements.txt
```

You can create and activate a virtual environment first with `python -m venv .venv` and `.\.venv\Scripts\Activate.ps1`. The install command includes the CLI package, Streamlit, scikit-learn, `skops`, and Ruff.

## Quick start

Run the seven bundled scenarios in rules mode:

```powershell
python -m promise_poc demo --mode rules
```

Or start the web app and open the local address printed by Streamlit:

```powershell
python -m streamlit run ui/app.py
```

The web app can evaluate Rules requests immediately. To use ML in the web app, open **ML training** and click **Train and save** first. The CLI trains its ML models in memory each time you run it with `--mode ml`.

## CLI commands and arguments

Both commands print JSON to the terminal. Run `python -m promise_poc --help` or add `--help` after a command for the full CLI help.

| Command | What it does | Example |
|---|---|---|
| `demo` | Evaluates all seven bundled requests. | `python -m promise_poc demo --mode ml` |
| `evaluate` | Evaluates one store pickup request. | `python -m promise_poc evaluate --product-id SKU-001 --quantity 2 --destination-id STORE-001 --date 2026-11-10 --mode rules` |

| Argument | Applies to | Meaning |
|---|---|---|
| `--mode` | Both | `rules` or `ml`; defaults to `rules`. ML retrains three models on each CLI invocation. |
| `--product-id` | `evaluate` | Required product ID from `data/products.json`, such as `SKU-001`. |
| `--quantity` | `evaluate` | Required positive integer number of units. |
| `--destination-id` | `evaluate` | Required pickup store ID from `data/locations.json`, such as `STORE-001`. |
| `--date` | `evaluate` | Required desired pickup date in `YYYY-MM-DD` format. |
| `--at` | `evaluate` | Optional request time in UTC, such as `2026-11-05T10:30:00Z`. Defaults to the bundled sample reference time (`2026-11-05T10:30:00Z`). |

The fixed default request time keeps the sample inventory current and makes repeated results comparable. Dates in examples are tied to that reference time; when using a different `--at`, choose a date that makes sense for that request time.

## Regenerate synthetic data

The data generator is an optional script. Its defaults reproduce the bundled synthetic history:

```powershell
python -m scripts.generate_data --rows 10000 --seed 2026
```

| Argument | Meaning |
|---|---|
| `--rows` | Number of historical situations to generate, from 100 to 20,000; defaults to 10,000. |
| `--seed` | Random seed from 0 to 4,294,967,295; defaults to 2026. The same seed and row count produce the same records with unchanged inputs and generator code. |

This script **replaces the category JSON files in `data/`**, including historical snapshots, counts, and orders. It retains the bundled demo requests and original live snapshots while building a catalog of 30 products, 10 stores, and three distribution centers. After regenerating data, retrain any saved web ML model in the **ML training** tab. See [Synthetic data generation](docs/synthetic-data-generation.md) for the records and generation rules.

## Web interface

The web interface has four tabs:

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

The web interface uses only an ML model previously trained and saved with `skops` at `ui/.local/latest.skops` (this directory is excluded from version control). If the model is missing or corrupt, or the sample data or scikit-learn version changes, retrain it in the **ML training** tab. Changing form parameters has no effect on evaluation results until training and saving succeed.

## Data and limitations

The bundled data contains 30 construction and hardware products, 10 pickup stores, three distribution centers, 10,000 generated historical snapshots with linked counts and orders, and 390 current snapshots. Historical rows span June through October 2026. The generator deliberately makes accurate counts and full picks less likely when inventory is stale or transactions are pending, so model scores reflect those programmed patterns.

Rules and ML use the same hard checks for data older than 24 hours, available-to-promise stock, and feasible pickup dates. Working days are Monday through Friday; route cutoff times are in UTC and holidays are not accounted for. The models have no independent real-world dataset or probability calibration. **Decisions and probabilities are illustrative and must not be used for real delivery commitments.** No data is uploaded or written to operational systems.

## Development checks

Run these from the project root after changes to the code:

```powershell
python -m unittest discover -s tests -v
python -m ruff check src ui tests
python -m ruff format --check ui
```
