Stage 4 - TESTS FIRST. Inputs: approved 01-spec.md, 02-design.md, and 03-plan.md.
Task slug: {{task-slug}}
Write tests only; do not implement the feature.

1. Write docs/ai/{{task-slug}}/04-tests.md with:
   - Test matrix: test name | spec ref (FR/NFR/edge case) | type (unit/integration) | expected result
   - Cases to cover: happy path, edge cases, failure paths, security/abuse cases, concurrency cases (if relevant): {{extra cases I want}}
   - Test data/fixtures needed and what is mocked (and why)
   - Spec items NOT covered by tests, with reason
2. Create the test files listed in the matrix, following existing test conventions.
3. Run test command. 
   Report which tests fail and confirm each fails for the RIGHT reason (missing feature, not a typo or import error).
   Paste the failing-test summary into 04-tests.md.

Do not modify existing fixtures. Then stop and wait for my review.
