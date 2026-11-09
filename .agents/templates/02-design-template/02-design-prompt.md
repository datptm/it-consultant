Stage 2 - DESIGN. Inputs: approved 01-spec.md and the affected code.
Task slug: {{task-slug}}
Re-read the approved spec and relevant architecture. Explain how the problem in the approved spec will be solved as a brief system design document. Do not write source code.

Write docs/ai/{{task-slug}}/02-design.md with these sections:
1. Problem summary: goals, scope, and constraints from the spec
2. Proposed solution: the end-to-end method and important business rules
3. Domain model and database schema, when persistence is needed: entities/tables, key fields, relationships, constraints, and useful indexes
4. Important interactions or interfaces and failure behavior, at a system-design level
5. Diagram of the system flow or key interactions (Mermaid or a simple text diagram)
6. Security, consistency/concurrency, reliability, and scaling considerations where relevant
7. Alternatives considered and trade-offs
8. Risks and assumptions
9. Open questions (for me to answer)

Then stop and wait for my review.
