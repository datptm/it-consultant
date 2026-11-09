# Change log

## 2026-11-05 16:15 (UTC) - Promise Engine CLI PoC
- Task: Hiện thực PoC Promise Engine rule-based và ML-based với dữ liệu mẫu và CLI.
- Changes: Thêm dữ liệu nghiệp vụ giả lập; rule tính điểm tồn kho, ATP và ngày giao; ba mô hình logistic regression huấn luyện trong bộ nhớ; engine quyết định theo một nguồn cung và CLI demo/evaluate, trong đó rule mode chạy độc lập với thư viện ML; kiểm thử và hướng dẫn chạy. Khai báo dependency runtime cần thiết trong `requirements.txt` đồng nhất với `pyproject.toml`.
- Files: `data/sample.json`, `src/promise_poc/__init__.py`, `src/promise_poc/data.py`, `src/promise_poc/rules.py`, `src/promise_poc/features.py`, `src/promise_poc/ml.py`, `src/promise_poc/engine.py`, `src/promise_poc/__main__.py`, `tests/test_promise.py`, `pyproject.toml`, `requirements.txt`, `.gitignore`, `README.md`, `docs/ai/CHANGELOG.md`
- Why: Minh họa luồng đánh giá lời hứa cốt lõi từ `docs/resources/methodology.md` bằng dữ liệu nhỏ, không triển khai API hoặc hạ tầng.
- Verification: Python 3.13 và 3.12: `unittest discover -s tests -v` đều 17/17 qua; `python -m compileall -q src tests` qua; Python 3.13: `demo --mode rules` chạy không cần ML, `demo --mode ml` và `evaluate --mode ml` chạy thành công. `requirements.txt` được kiểm tra khớp chính xác với `project.dependencies` trong `pyproject.toml`. Không chạy lại test cho thay đổi chỉ ở manifest; không chạy lệnh cài editable hoặc linter vì chưa có linter được cấu hình.
- Risks / follow-ups: Dữ liệu ít và xác suất chưa hiệu chỉnh, chỉ phù hợp minh họa; thư mục dependency cục bộ `.deps` cần môi trường có quyền đọc thích hợp hoặc cài lại bằng lệnh trong README.

## 2026-11-08 12:57 (UTC) - Streamlit UI and saved ML models
- Task: Add a Streamlit web UI with sample, evaluation, and ML training tabs, plus Ruff and documentation.
- Changes: Added a three-tab English UI with sample and custom evaluations; configurable three-model training with real progress and local `skops` persistence; saved-model validation and explicit retraining prompts; Ruff configuration and dependency declarations; updated project instructions and usage documentation.
- Files: `ui/__init__.py`, `ui/app.py`, `ui/model_store.py`, `src/promise_poc/ml.py`, `tests/test_ml_training.py`, `tests/test_model_store.py`, `tests/test_ui.py`, `requirements.txt`, `pyproject.toml`, `.gitignore`, `README.md`, `AGENTS.md`, `docs/data-features-models.md`, `docs/ai/CHANGELOG.md`
- Why: Make the synthetic Promise Engine PoC explorable in a browser while separating web ML training from evaluation and reusing the latest local model.
- Verification: `.venv\Scripts\python.exe -m unittest discover -s tests -v` passed 31/31; `python -m ruff check src ui tests`, `python -m ruff format --check ui`, `python -m compileall -q src ui tests`, and `python -m pip check` passed in the project virtual environment. Streamlit started on localhost and `/_stcore/health` returned `ok`. The documented editable install command was not rerun because it can rewrite generated egg-info; dependencies were installed with `pip install -r requirements.txt`. No manual browser visual review was run.
- Risks / follow-ups: Synthetic training data is tiny and probabilities are uncalibrated. A saved model requires the same scikit-learn version and sample contents; otherwise the UI asks for retraining.
