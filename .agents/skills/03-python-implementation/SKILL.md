---
name: 03-python-implementation
description: Use this skill whenever writing, editing, or refactoring Python code — new features, bug fixes, or cleanups — in codebases that don't rely on a specific framework (plain Python, standard library, or common general-purpose libraries). Defines naming conventions, docstring and comment standards, structural guidelines, and refactor discipline so code stays consistent, readable, and maintainable. Trigger this for any actual code-writing step, after a plan exists (see the planning skill) and after the codebase's existing conventions have been identified (see codebase-explorer) — this skill's defaults apply when the codebase has no stronger convention of its own.
---

# Implementation (Python)

## Purpose

Write Python code that a future reader — human or agent — can understand, trust, and safely modify. Consistency with the existing codebase always wins over these defaults; use this skill to fill gaps, not override established local convention.

## Precedence rule

1. Explicit instructions from the user for this task.
2. Conventions already established in the codebase (found via exploration).
3. The defaults in this skill.

Never silently reformat or restyle unrelated code to match this skill's preferences — stay scoped to the task.

## Naming conventions (PEP 8 baseline)

- `snake_case` for functions, methods, variables, and modules.
- `PascalCase` for classes and exceptions (`UserNotFoundError`, not `user_not_found_error`).
- `UPPER_SNAKE_CASE` for module-level constants.
- Leading underscore (`_helper`) for internal/private functions and attributes not part of the public interface.
- Boolean variables/functions read as predicates: `is_valid`, `has_permission`, `should_retry` — avoid ambiguous names like `flag` or `check`.
- Avoid single-letter names outside of short loop indices (`i`, `j`) or well-known math contexts; prefer `idx`, `item`, `result` over `x`, `y`, `z` for anything with meaning.
- Name things after what they _are_ or _do_, not how they're implemented (`active_users`, not `filtered_list_2`).
- Avoid abbreviations unless they are domain-standard (`cfg`, `db`, `req`/`resp` in HTTP contexts are fine; invented abbreviations are not).

## Type hints

- Add type hints to all new function/method signatures (parameters and return type), including `-> None` where relevant.
- Use `Optional[X]` / `X | None` explicitly rather than leaving a default of `None` untyped.
- Use precise container types (`list[str]`, `dict[str, int]`) over bare `list`/`dict`.
- Don't retrofit type hints onto large swaths of untouched legacy code as a side effect of an unrelated change — scope creep.

## Docstrings

- Every public function, method, and class gets a docstring; private helpers (`_foo`) get one only if their behavior isn't obvious from the name and body.
- Follow whatever docstring style the codebase already uses (Google, NumPy, reST). If none exists, default to Google style:

```python
def resolve_conflicts(local: dict, remote: dict) -> dict:
    """Merge two state dicts, preferring remote values on conflict.

    Args:
        local: The current local state.
        remote: The incoming remote state.

    Returns:
        A merged dict with remote values taking precedence on key conflicts.

    Raises:
        ValueError: If either input is empty.
    """
```

- Docstrings describe _contract_ (inputs, outputs, side effects, exceptions) — not a restatement of the code.

## Comments

- Comment _why_, not _what_. Code should be readable enough that "what" is self-evident from names and structure.
- Good: `# Retry once — the upstream API occasionally drops the first connection after idle.`
- Bad: `# increment counter` above `counter += 1`.
- Use comments to flag non-obvious trade-offs, workarounds for external bugs, or intentional deviations from the "normal" approach — a future editor should not "fix" these by accident.
- Mark unfinished or intentionally incomplete work with `# TODO(reason): ...` rather than leaving it unexplained.
- Delete commented-out dead code rather than leaving it — version control preserves history.

## Structure and style

- One clear responsibility per function; if a function needs "and" to describe what it does, consider splitting it.
- Keep functions short enough to read on one screen where reasonably possible; extract helpers rather than nesting deeply.
- Prefer early returns/guard clauses over deeply nested `if` blocks.
- Avoid mutable default arguments (`def f(items=[])` is a bug waiting to happen — use `None` and initialize inside).
- Prefer composition and small pure functions over deep inheritance hierarchies unless the codebase already commits to inheritance-based design.
- Avoid global mutable state; if unavoidable, isolate and clearly name it.
- Use f-strings for formatting (unless codebase standardizes on `.format()`/`%` already).
- Follow the project's import ordering (stdlib, third-party, local) and avoid wildcard imports (`from x import *`).

## Error handling

- Raise specific, meaningful exceptions (custom exception classes for domain errors) rather than bare `Exception` or silent `pass` in `except` blocks.
- Never swallow exceptions silently; at minimum log with context.
- Only catch exceptions you can meaningfully handle or add context to — otherwise let them propagate.
- Validate inputs at boundaries (public functions, API handlers), not defensively everywhere.

## Logging vs. print

- Use the `logging` module (or the project's existing logging setup) for anything beyond throwaway scripts — never leave debugging `print()` statements in committed code.
- Log at the right level: `debug` for developer detail, `info` for normal operation milestones, `warning` for recoverable issues, `error`/`exception` for failures.

## Refactoring discipline

- Never refactor and change behavior in the same step — separate "restructure" commits/changes from "behavior change" ones where possible.
- Ensure tests exist and pass _before_ refactoring; if they don't exist for the code being touched, add characterization tests first (see `testing-debugging`).
- Preserve public interfaces unless the task explicitly calls for a breaking change; if breaking, call it out clearly.
- Make the smallest change that correctly and cleanly achieves the goal — resist unrelated "drive-by" improvements; note them for a follow-up instead.

## Dependencies

- Don't add a new third-party dependency for something the standard library already does well.
- If a new dependency is genuinely needed, prefer well-maintained, narrowly-scoped libraries and record it in the appropriate manifest (`pyproject.toml`/`requirements.txt`) consistent with how the project already manages dependencies.

## Before considering implementation done

- [ ] Names are clear and consistent with the rest of the codebase.
- [ ] New public functions/classes have type hints and docstrings.
- [ ] No leftover debug `print()`, commented-out code, or unresolved TODOs without explanation.
- [ ] Error handling is specific and doesn't swallow failures silently.
- [ ] The change is scoped to the plan — no unrelated edits mixed in.
- [ ] Code has been mentally (or actually) traced against the acceptance criteria from the plan.
