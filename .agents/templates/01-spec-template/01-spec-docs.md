Stage 1 - SPEC. Read the relevant code first, but do not change anything.
Task slug: {{task-slug}}

## Brief files
- Folder containing the brief: {{path-to-brief-folder}}
- Specific files to prioritize (optional): {{file-paths-or-all-files-in-folder}}

Read the brief files in the specified folder before drafting the spec. Use their contents as my brief. If the folder contains many files, focus on the listed files and other files that are clearly part of the brief; do not treat unrelated project files as requirements.

If you cannot access or read a file, or if the brief files conflict or leave an important requirement unclear, record that under Assumptions or Open questions. Do not silently choose between conflicting instructions or invent requirements.

Write docs/ai/{{task-slug}}/01-spec.md with these sections:
1. Goal and non-goals
2. Functional requirements (numbered, e.g. FR-1, each testable)
3. Non-functional requirements (performance, security, reliability, limits)
4. Edge cases and failure behavior
5. Acceptance criteria (Given/When/Then or checklist, each mapped to an FR)
6. Assumptions
7. Open questions (for me to answer)

Then stop and wait for my review.
