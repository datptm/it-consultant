# Promise Engine PoC

Local Python CLI and Streamlit demo for store staff to explore synthetic inventory, fulfillment, and pickup-date decisions. It runs on a developer machine; it is not connected to operational systems.

Trust boundary: Streamlit form values and local sample/model files are inputs to validate before use. The app has no uploads, third-party API calls, or webhooks.

## Tech stack
- Language/runtime: Python 3.13+   Framework: Streamlit; scikit-learn models
- Data/storage: synthetic `data/sample.json` and a local `skops` model bundle in ignored `ui/.local/`; no database, cache service, or queue
- Platform: local desktop/browser use; documented commands target PowerShell on Windows

## Commands
- Install: `python -m pip install -e . -r requirements.txt`
- Build: N/A
- Test: `python -m unittest discover -s tests -v`
- Lint/format: `python -m ruff check src ui tests` and `python -m ruff format --check ui`
- Type/static check: N/A
- Run locally: `python -m streamlit run ui/app.py` (CLI: `python -m promise_poc demo --mode rules`)
- A task is DONE only when every check listed above that applies passes.

## Architecture
- `src/promise_poc/`: sample loading, point-in-time features, rules, ML training, and shared evaluation engine
- `src/promise_poc/__main__.py`: CLI entry point; `ui/app.py`: Streamlit entry point; `ui/model_store.py`: local model persistence
- Key decisions: rules and ML share hard feasibility checks; CLI retrains ML models per invocation; web ML evaluation requires a saved compatible model and uses fixed sample time for repeatability

## Conventions
- Style: follow configured Ruff linting; use descriptive Python names and explicit errors
- Tests: `tests/test_*.py` with unittest; synthetic fixtures only; isolate local model artifacts per test
- Commits/PRs: no Git repository or commit convention is present in this workspace; keep changes scoped
- Logging: no central logging format yet; never log secrets or user content

## Security rules
- Validate all external input at the boundary.
- No dynamic code execution or unsafe deserialization on untrusted data.
- File paths: resolve to a canonical path and verify it stays inside the allowed base directory; never rely on string matching.
- Apply resource limits (timeout, memory, size, depth, rate) to anything untrusted.
- Never read, print, or commit secrets, credentials, `.env` files, or real customer data.

## Do NOT
- Add dependencies without asking first.
- Swallow errors (empty catch/except blocks, ignored return values).
- Modify generated `src/promise_poc.egg-info/`, local virtual environments, or ignored model artifacts unless the task explicitly requires it.
- Refactor or reformat code unrelated to the task.
- Run destructive commands (delete, force-push, DB drops) or push to the main branch.
- Edit, reorder, or delete existing change log entries (append only).

## Change log (required)
- Every chat that changes the codebase MUST append one entry to `docs/ai/CHANGELOG.md` before the chat ends.
- "Changes the codebase" means any change to source, tests, config, build/CI files, dependencies, schemas, migrations, or scripts.
  Do NOT log chats that only touched documentation (README, `docs/`, comments, AGENTS.md) or made no changes.
- Chronological, append-only: add the new entry at the END of the file, never edit or remove earlier entries.
  Create the file with a `# Change log` heading if it does not exist.
- One entry per chat. If the chat continues after the entry is written, update that same entry instead of adding a second one.
- Entry format:

      ## YYYY-MM-DD HH:MM (UTC) - <short title>
      - Task: <task-slug or one-line request summary>
      - Changes: <what changed, grouped logically; not a raw diff>
      - Files: `path/a`, `path/b`
      - Why: <reason, linked spec/issue if any>
      - Verification: <commands run and results; what was NOT run>
      - Risks / follow-ups: <or "none">

- Never put secrets, credentials, or real customer data in the log.
- If the task was abandoned or only partly done, still log it and mark it "Status: partial" with what remains.

## Definition of done
- Behavior matches the spec; each requirement has a test that can actually fail.
- No new errors or warnings from build, lint, or static checks; no unrelated changes in the diff.
- Docs/comments updated where behavior changed.
- Change log entry appended (if the chat changed the codebase beyond documentation).
- Summary of changes, risks, and anything not covered by tests.

## Known pitfalls (agent mistakes to avoid)
<!-- Add a line each time the agent repeats a mistake. -->
- The bundled reference time is fixed; using the wall clock can make all sample inventory appear stale.
- The web ML path must load a saved model, while the CLI's ML path deliberately retrains.

## References
- `README.md`, `docs/data-features-models.md`, `docs/resources/methodology.md`, `docs/resources/product-description.md`
