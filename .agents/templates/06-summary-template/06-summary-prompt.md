Stage 6 - SUMMARY. Inputs: approved 01-spec.md, 02-design.md, 03-plan.md, 04-tests.md, and all implementation steps (approved).
Task slug: {{task-slug}}

- Run the full applicable test, lint, type check, and build suites.
- Trace every FR/NFR and other spec item to its implementation and verification result.

Do not change source code or tests.
If you find a gap or failure, report it with evidence and stop for my review.

Write docs/ai/{{task-slug}}/06-summary.md with:
1. Outcome and changes made
2. Spec traceability: each FR/NFR/spec item | implementation | verification | status
3. Full-suite commands and results; list anything not run and why
4. Known limitations, risks, and follow-ups
5. Lessons learned and proposed concise Known pitfalls lines for AGENTS.md

Do not edit AGENTS.md; present proposed lines for my review. Then stop and wait for my review.
