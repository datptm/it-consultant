---
name: 04-testing-debugging
description: Language-agnostic testing and debugging skill, applicable to any programming language or test framework. Use this when writing tests for new or changed code, and when investigating and fixing a bug. Guides deep analysis of business and system requirements to derive test scenarios spanning happy paths, edge cases, and failure modes, and provides a structured procedure for reproducing, diagnosing, and fixing defects with a regression test. Trigger this after implementation (or before it, for TDD) for any feature/fix, and any time the user reports a bug, unexpected behavior, or failing test.
---

# Testing & Debugging

## Part 1 — Deriving test scenarios

### Step 1: Extract the real requirements

Before writing any test, be explicit about what the code is supposed to guarantee:

- Functional requirements: what inputs produce what outputs/side effects.
- Business rules: constraints, invariants, validation rules implied by the domain (e.g. "a discount can't take a price below zero", "a user can't book overlapping slots").
- System requirements: performance expectations, concurrency behavior, idempotency, ordering guarantees, integration contracts with other components.

Pull these from: the task's acceptance criteria (from `planning`), existing tests on related code, docstrings/docs, and direct inspection of the implementation's branches.

### Step 2: Enumerate scenarios systematically

For each function/feature under test, work through these categories — don't skip straight to the obvious happy path:

**Happy path**

- The typical, expected usage with valid, well-formed input.
- More than one happy path if the function has meaningfully different valid modes (e.g. "with optional param" vs. "without").

**Boundary / edge cases**

- Empty input (empty string, empty list/array, empty map/object, zero, null/nil/undefined where allowed).
- Minimum/maximum valid values; one below/above valid range.
- Single-element vs. many-element collections.
- Duplicate values, already-sorted vs. reverse-sorted input, unicode/special characters in strings.
- Off-by-one boundaries in loops, ranges, and comparisons.

**Invalid input / failure modes**

- Wrong type, null/nil where not allowed, malformed structure.
- Values that violate business rules (negative price, invalid state transition).
- Missing required fields/arguments.
- Expected exception type and message/content, not just "it raises something."

**State and interaction**

- Behavior across repeated calls (idempotency — calling twice gives the same safe result, or explicitly doesn't).
- Ordering dependencies (does calling B before A matter?).
- Concurrent/parallel access if relevant (race conditions, shared mutable state).

**External dependencies and integration**

- Dependency returns success, returns an error, times out, or returns unexpected/malformed data.
- Network/IO failures if the code touches external systems — simulate via mocking, don't skip.

**Regression**

- If fixing a bug: the exact scenario that reproduced it, expressed as a test that fails before the fix and passes after.

### Step 3: Prioritize

Not everything needs equal depth. Prioritize scenarios that are:

1. Most likely in real usage.
2. Highest impact if wrong (data loss, security, money, silent corruption).
3. Historically fragile (areas with past bugs, complex branching logic).

## Part 2 — Writing tests

- Use the project's existing test framework and conventions (found via exploration); if none exists, use whatever is the standard, idiomatic choice for the language/ecosystem.
- One behavior per test; test names describe the scenario and expectation (e.g. `returns empty list when no matches`), not a generic label like `test 1`.
- Structure tests as **Arrange / Act / Assert**, with clear separation (blank line or comments) between the three.
- Use parametrized/table-driven tests (whatever the framework's mechanism is) to cover multiple similar cases without duplicating test bodies.
- Use fixtures/setup-and-teardown hooks for shared setup; keep them minimal and explicit rather than deeply nested/implicit.
- Mock or stub external dependencies (network, filesystem, time, randomness) at the boundary — don't let unit tests depend on real external state.
- Assert on specific, meaningful conditions — avoid overly broad assertions (checking that a result is merely truthy/non-null when you mean to check it equals a specific expected value).
- Keep unit tests fast and isolated; reserve slower integration/end-to-end tests for genuine cross-component behavior, and mark/separate them accordingly.
- Aim for coverage of behavior, not a coverage percentage — a test suite that hits every line but asserts nothing meaningful is worse than fewer, sharper tests.

## Part 3 — Debugging procedure

When investigating a reported or discovered bug:

### 1. Reproduce

- Get a minimal, reliable way to trigger the bug before touching any code.
- If it's intermittent, note conditions that seem to correlate (timing, input size, environment).

### 2. Isolate

- Narrow down the smallest scope that still reproduces it (specific function, specific input) — bisect by commenting out/removing surrounding complexity in a scratch copy if needed.
- Check recent changes to the affected area (`git log`, `git blame`) — regressions often trace to a recent, specific commit.

### 3. Form a hypothesis before changing code

- State what you believe is wrong and why, based on evidence (error message, stack trace, logs, actual vs. expected values) — not a guess.
- If uncertain, add temporary logging/prints or use a debugger to inspect actual state at the point of failure, rather than speculatively editing code.

### 4. Confirm root cause, not just symptom

- Distinguish "where it broke" (symptom) from "why it's wrong" (root cause). A null/nil where a value was expected is a symptom; find where that null should have been prevented or handled.
- Watch for the bug being a symptom of a bad assumption made elsewhere in the code, not a local logic error.

### 5. Fix and add a regression test

- Write a failing test that reproduces the bug first, confirm it fails, then fix the code, then confirm the test passes.
- Check for the same root cause elsewhere in the codebase (was this pattern copy-pasted anywhere else?).

### 6. Verify no collateral damage

- Run the full relevant test suite, not just the new test, to catch regressions the fix might introduce.

## Output format for a debugging session

```
## Bug
<description + how it manifests>

## Reproduction
<minimal steps/input to trigger it>

## Root Cause
<what is actually wrong, and why>

## Fix
<what was changed and why this addresses the root cause, not just the symptom>

## Regression Test
<test added to prevent recurrence>
```

## Anti-patterns to avoid

- Writing only happy-path tests and calling coverage "done."
- Fixing symptoms (adding a null-check) without understanding why the null appeared.
- Changing code before being able to reliably reproduce the issue.
- Asserting on implementation details (internal call counts, private attributes) instead of observable behavior, which makes tests brittle to harmless refactors.
