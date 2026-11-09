---
name: 01-codebase-explorer
description: Language-agnostic skill for exploring an existing codebase in any programming language or stack. Use this at the start of any task that touches existing code, before planning or writing code. Explores the repository's structure, documentation, history, and current state to build an accurate mental model of what exists, what has already been done, what is in progress, and what is missing. Trigger this whenever the user asks to work on, fix, extend, or understand a project you have not already mapped in this session — e.g. "look into this repo", "add a feature to X", "why is Y broken", "what's the state of this project". Do not skip this because the task seems small; a wrong assumption about existing structure is the most common cause of bad changes.
---

# Codebase Explorer

## Purpose

Build a grounded, evidence-based understanding of a codebase before any planning or coding happens. Never assume structure, conventions, or completeness from the task description alone — verify by reading.

## When to use

- First contact with a repository in a session.
- Before implementing a feature, fixing a bug, or refactoring, if the relevant area hasn't been explored yet.
- When the user asks "what does this do", "what's left to do", "what's the current state", or similar.
- When resuming work that may have been partially done (by a human or a prior agent run).

Skip only if the exact files and context needed are already known from earlier in the same session.

## Process

Work top-down: docs and metadata first, then structure, then code, then history. Stop early if the task is narrow and you've already found what you need — this skill is about being grounded, not exhaustive.

### 1. Read project-level documentation first

Look for, and read, whichever of these exist:

- `README.md`, `README.rst`
- `docs/` directory (architecture docs, ADRs, design docs)
- `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`
- `CHANGELOG.md` / `HISTORY.md`
- `TODO.md`, `ROADMAP.md`, `BACKLOG.md`
- `.github/` (issue templates, workflow files reveal CI/CD and quality gates)
- Package/dependency manifests (whichever apply): e.g. `package.json`, `pyproject.toml`, `pom.xml`/`build.gradle`, `Cargo.toml`, `go.mod`, `Gemfile`, `composer.json`
- Any `AGENTS.md`, `CLAUDE.md`, or similar agent-instruction files — these take priority, as they encode standing project rules

If docs are missing or stale (check dates/last-updated vs. recent commits), note that explicitly rather than trusting them blindly.

### 2. Map the structure

- List the top-level directory tree (2–3 levels deep is usually enough).
- Identify the main package(s)/module(s) vs. tests vs. scripts vs. config.
- Identify entry points (main/executable files, CLI definitions, service bootstrap code, build/run scripts).
- Identify configuration and environment handling (`.env.example`, `config/` directories, environment-specific settings files).

### 3. Identify conventions actually in use

Don't assume a style guide is followed — check real files:

- Naming conventions (files, functions, classes/types, variables).
- Documentation/comment style (formal doc-comment blocks, inline comments, plain, or none).
- Type usage — statically typed, gradually typed, or untyped, and how consistently.
- Test framework and layout (dedicated `tests/` directory vs. colocated test files, naming pattern used for test files).
- Dependency management tool and lockfile convention.
- Logging approach (a logging library/framework vs. raw console output, structured vs. plain logging).
- Error-handling patterns (exceptions, error codes/result types, silent failures).

### 4. Assess current state of the actual task area

For the specific feature/module/bug relevant to the request:

- Read the relevant files fully, not just grep hits.
- Trace how the relevant code is called (who imports it, who calls it).
- Search for markers like `TODO`, `FIXME`, `XXX`, `HACK`, stubbed/unimplemented functions, and commented-out code near the area.
- Check test coverage for that area — do tests exist? Do they pass? What do they assert (this often reveals intended behavior better than docs)?
- Check recent git history for that area if available (`git log --oneline -- <path>`, `git blame` on suspicious lines) to see what changed recently and why.

### 5. Identify gaps, risks, and open questions

- What does documentation claim that the code doesn't actually do (or vice versa)?
- What looks unfinished, inconsistent, or duplicated?
- What assumptions would be risky to make without asking the user?

## Output

Summarize findings before moving to planning or implementation, using this structure:

```
## Codebase Overview
- Purpose / domain of the project (1-2 sentences)
- Language/runtime, key dependencies, package manager

## Structure
- Key directories and what lives in each
- Entry points

## Conventions Observed
- Naming, docstrings, typing, testing, logging, error handling

## Relevant Area (for this task)
- Files involved and their current responsibilities
- How they're currently used/called
- Existing tests and what they cover

## State: Done / In Progress / Missing
- What's already implemented and working
- What's partially done (TODOs, stubs, disabled code)
- What's missing relative to the request

## Open Questions / Risks
- Ambiguities, undocumented assumptions, or conflicting signals worth confirming before proceeding
```

Keep this proportional to task size — a one-file bug fix needs a few lines, not the full template.

## Anti-patterns to avoid

- Trusting a README over what the code actually does.
- Grepping for a symbol and reading only the matching line without its surrounding context.
- Skipping test files — they're often the most reliable spec of intended behavior.
- Declaring a codebase "clean" or "well-structured" without having read enough of it to justify the claim.
