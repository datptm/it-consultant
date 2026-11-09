---
name: 02-planning
description: Language-agnostic planning skill, usable regardless of programming language or stack. Use this after exploring a codebase (or when the task is small enough to skip exploration) and before writing or editing any code. Turns a request into a concrete, scoped plan — clarified requirements, an approach with trade-offs considered, explicit in/out-of-scope boundaries, acceptance criteria, and a step sequence. Trigger this for any non-trivial feature, bug fix, or refactor; skip only for truly mechanical one-line changes where a plan would add no value.
---

# Planning

## Purpose

Convert "what the user asked for" into "what will actually be built," in writing, before code is touched. Most costly mistakes in agentic coding come from starting to implement on an ambiguous or under-scoped understanding of the task — this skill exists to catch that earlier and cheaply.

## When to use

- Any feature addition, bug fix, or refactor that touches more than a couple of lines or more than one file.
- Any task where the request could reasonably be interpreted more than one way.
- Any task where more than one viable technical approach exists.

Skip for trivial, unambiguous, single-line/single-file changes — but still state the one-line plan inline before editing.

## Process

### 1. Clarify the actual requirement

- Restate the request in your own words, including the implicit goal behind it (why is this being asked for?).
- Distinguish what was explicitly requested from what you're inferring.
- If genuinely ambiguous in a way that would change the approach, ask one focused question. Otherwise, pick the most reasonable interpretation, state the assumption, and proceed.

### 2. Define scope boundaries

- **In scope**: what this change will do.
- **Out of scope**: adjacent things it will deliberately NOT do (e.g. "will not refactor unrelated module X even though it has similar issues").
- Explicit non-goals prevent both under-delivery and unrequested scope creep.

### 3. Consider approaches

For anything with real design choices:

- List 2–3 viable approaches briefly.
- Note the trade-off each makes (simplicity vs. flexibility, performance vs. readability, blast radius, consistency with existing patterns found during exploration).
- Pick one and state why, referencing what was found in the codebase (existing patterns should usually win over "better" but foreign patterns, unless the user asked for a change in direction).

### 4. Define acceptance criteria

Write down, before coding, how you and the user will know the task is done:

- Concrete behavior: "given X input, Y happens."
- Any explicit constraints (performance, compatibility, no breaking changes to public API, etc.).
- This becomes the seed for the test scenarios written under `testing-debugging`.

### 5. Sequence the work

- Break the task into an ordered list of concrete steps (files to touch, in what order, and why that order — e.g. data layer before API layer before UI).
- Flag steps that are risky, reversible-vs-not, or that touch shared/critical code.
- Flag any step that depends on an assumption that could be wrong.

### 6. Surface risks and unknowns up front

- Call out anything uncertain: unclear existing behavior, missing tests to lean on, external dependencies, migrations, concurrency concerns.
- Better to flag a risk now than discover it mid-implementation.

## Output

```
## Understood Task
<restated request + inferred goal>

## Scope
In scope: ...
Out of scope: ...

## Approach
Chosen approach: ...
Why: ...
Alternatives considered: ... (brief)

## Acceptance Criteria
- ...
- ...

## Plan
1. ...
2. ...
3. ...

## Risks / Open Questions
- ...
```

For small tasks, compress this to a few lines rather than filling every section — the goal is clarity, not ceremony.

## Anti-patterns to avoid

- Starting to write code while still figuring out the approach in your head — write the plan down first, even briefly.
- Silently expanding scope beyond the request ("while I was in there I also...") without calling it out.
- Picking an approach because it's the first one that came to mind rather than because it fits the codebase's existing patterns.
- Treating acceptance criteria as an afterthought written after the code, rather than a target defined before it.
