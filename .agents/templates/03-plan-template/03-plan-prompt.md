Stage 3 - PLAN. Inputs: approved 01-spec.md and 02-design.md.
Task slug: {{task-slug}}
Re-read the spec, design, and affected code. Do not write source code.

Write docs/ai/{{task-slug}}/03-plan.md with these sections:
1. Implementation summary based on the approved design
2. Files to create or modify (path + change + why)
3. Small, ordered implementation steps, each independently verifiable (target < ~200 changed lines per step)
4. Verification for each step, including relevant tests and checks
5. Spec traceability: table mapping each FR/NFR to step(s)
6. Implementation risks and assumptions
7. Open questions (for me to answer)

Flag any step that conflicts with the approved design or AGENTS.md, or needs a new dependency.
Then stop and wait for my review.
