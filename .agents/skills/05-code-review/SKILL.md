---
name: 05-code-review
description: Language-agnostic code review skill, applicable to any programming language or stack. Use this when reviewing a diff, pull request, or set of proposed/completed code changes — whether written by the user, another agent, or yourself. Evaluates correctness, maintainability, security, performance, and whether the change actually matches the stated requirement, then produces a structured, severity-ranked report. Trigger this whenever the user asks to "review", "check", "audit" code or a diff, before merging/finalizing a non-trivial change, or as a self-check pass after implementation.
---

# Code Review

## Purpose

Catch correctness issues, hidden risks, and maintainability problems before they ship — with a report that is specific, actionable, and honestly prioritized rather than a vague "looks good."

## Process

### 1. Understand intent before judging the diff

- Read the associated requirement/plan/ticket/description first. A change can be well-written and still wrong if it doesn't do what was asked.
- If no stated requirement is available, infer intent from the diff itself and state that inference explicitly in the report.

### 2. Review the diff itself, not just the final files

- Read the actual diff (added/removed/changed lines), not only the resulting file — this surfaces what was deliberately changed vs. pre-existing.
- Check that the diff is scoped to the stated task — flag unrelated changes mixed in, even if individually reasonable.
- Check for leftover debug code, commented-out blocks, stray print/log statements, and unresolved TODOs without justification.

### 3. Correctness

- Trace the logic against the requirement: does it actually produce the intended behavior for the described cases?
- Check boundary conditions and off-by-one risks (loop bounds, slicing, index arithmetic).
- Check error handling: are failure modes handled, or silently swallowed/ignored?
- Check for state/mutation bugs: shared mutable defaults, unintended aliasing, mutating input arguments the caller didn't expect to change.
- Check concurrency safety if the code touches shared state across threads/processes/async tasks.
- Cross-check against existing tests: do they actually exercise this change, or just pass incidentally?

### 4. Edge cases beyond what's tested

Actively look for scenarios the change might not handle, using the same categories as `testing-debugging`:

- Empty/null/zero inputs, boundary values, malformed input, duplicate/repeated calls, unexpected types.
- What happens if an external dependency (network, file, DB) fails or returns something unexpected?
- What happens under partial failure (e.g. the function does 3 things and the 2nd one throws — is state left consistent)?
- Flag any edge case found that isn't covered by a test.

### 5. Security

- Injection risks (SQL, command, path traversal) wherever user/external input reaches a query, shell command, file path, or template.
- Unsafe deserialization of untrusted input (native/language-level deserialization of arbitrary objects, dynamic code evaluation of external input, permissive config/data parsers that allow arbitrary type construction).
- Secrets or credentials hardcoded or logged.
- Missing input validation/sanitization at trust boundaries.
- Overly broad exception handling that could mask security-relevant failures.
- Any new dependency: is it reasonably trustworthy/maintained, and actually necessary?

### 6. Performance

- Obviously inefficient patterns introduced (N+1 queries/calls, quadratic loops over data that can grow large, repeated recomputation of the same value, unnecessary copies of large structures).
- Only flag performance issues that matter at realistic scale — don't nitpick micro-optimizations on code that runs once at startup on small input.

### 7. Maintainability

- Naming, structure, and comments are clear and consistent with the language's idioms and the codebase's established conventions (see the `implementation` skill for the Python-specific version of these standards, where applicable).
- Is the change consistent with existing patterns in the codebase, or does it introduce a new, inconsistent style without justification?
- Is complexity proportional to the problem, or is this over-engineered (unneeded abstraction, speculative generality) or under-engineered (duplicated logic that should be extracted)?
- Are public interfaces/signatures changed in a way that could break other callers? Were those callers checked?

### 8. Requirement match

- Explicitly confirm: does this diff satisfy the original acceptance criteria, fully?
- Note anything requested that appears to be missing, and anything delivered that wasn't requested (scope creep).

## Severity levels

Use consistently in the report:

- **Blocker** — incorrect behavior, security vulnerability, data loss/corruption risk, or breaks the stated requirement. Must be fixed before merging.
- **Major** — real risk (edge case likely to occur in production, meaningful performance problem, significant maintainability debt) but not an immediate correctness/security failure.
- **Minor** — style/consistency issues, missing but low-risk edge case handling, small clarity improvements.
- **Nit** — purely cosmetic (naming preference, formatting) — optional to address.

## Output format

```
## Summary
<1-3 sentences: does this change do what it's supposed to, at what quality>

## Requirement Match
- Satisfied: ...
- Missing / partial: ...
- Out-of-scope additions: ...

## Findings

### Blockers
- [file:line] <issue> — <why it matters> — <suggested fix>

### Major
- [file:line] <issue> — <why it matters> — <suggested fix>

### Minor
- [file:line] <issue> — <suggested fix>

### Nits
- [file:line] <issue>

## Edge Cases Not Covered by Tests
- <scenario> — <risk if it occurs>

## Security Notes
- <finding, or "none found">

## Performance Notes
- <finding, or "none found relevant at current scale">

## Verdict
Approve / Approve with minor changes / Request changes (blockers present)
```

Omit empty sections rather than writing "none" repeatedly, except Security and Performance where an explicit "none found" is worth stating.

## Anti-patterns to avoid

- Giving a generic "looks good" without having actually traced the logic against requirements.
- Flooding the report with nits while missing a real correctness or security issue — lead with severity, not volume.
- Reviewing only the new code in isolation without checking how it interacts with existing callers/callees.
- Rubber-stamping because tests pass — passing tests only prove what they actually assert, not full correctness.
