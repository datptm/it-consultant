# Promise Engine PoC

A CLI and Streamlit proof of concept for the three components described in [`docs/resources/methodology.md`](docs/resources/methodology.md): inventory confidence, fulfillment probability, and on-time delivery probability. The data in `data/sample.json` is entirely synthetic.

For details of the data, feature and label creation, and three trained models, see [`docs/data-features-models.md`](docs/data-features-models.md).

## Install and run

Python 3.13 is required. From the project root:

```powershell
python -m pip install -e . -r requirements.txt
python -m promise_poc demo --mode rules
python -m promise_poc demo --mode ml
python -m promise_poc evaluate --product-id SKU-001 --quantity 2 --destination-id STORE-001 --date 2026-11-10 --mode ml
python -m streamlit run ui/app.py
python -m unittest discover -s tests -v
python -m ruff check src ui tests
python -m ruff format --check ui
```

`demo` returns three JSON results. `evaluate` accepts a delivery date in `YYYY-MM-DD` format and optionally `--at 2026-11-05T10:30:00Z`. Without `--at`, the CLI uses the sample data's `reference_time` so repeated runs produce the same result. The PoC supports only `STORE_PICKUP` and a single supply source. Working days are Monday through Friday, cutoff times are in UTC, and holidays are not accounted for.

In `ml` mode, the CLI retrains three logistic regression models in memory on every invocation. Labels come from inventory counts, picked quantities, and actual delivery dates; features use only data available before the request time. The sample is very small, with no validation set or probability calibration. Probabilities in both modes illustrate the decision process and **must not be used for real delivery commitments**. Checks for source data older than 24 hours, ATP, and delivery dates apply in both modes.

## Web interface

Run `python -m streamlit run ui/app.py` from the project root and open the address shown by Streamlit. The English interface has three tabs:

- **Sample scenarios:** view three sample requests in Rules or ML mode.
- **Evaluate a request:** choose a product, quantity, pickup store, desired date, and evaluation mode. The request time is always the sample data's `reference_time` for repeatable results.
- **ML training:** view row and label counts for the three training sets, adjust shared `C` and `max_iter` values, then click **Train and save**. The progress bar updates after each model.

The web interface uses only an ML model previously trained and saved with `skops` at `ui/.local/latest.skops` (this directory is excluded from version control). If the model is missing or corrupt, or the sample data or scikit-learn version changes, retrain it in the **ML training** tab. Changing form parameters has no effect on evaluation results until training and saving succeed. Unlike the web interface, the CLI's `--mode ml` retrains on every run. No data is uploaded or written to operational systems.
