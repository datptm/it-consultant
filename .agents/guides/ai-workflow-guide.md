# Quy trình làm việc với AI agent (tóm tắt)

**Tư duy cốt lõi:** Tôi định nghĩa thế nào là đúng, agent giúp tôi đến đó nhanh hơn, và tôi chứng minh bằng test chứ không bằng cảm giác.

**Chuỗi làm việc:** Setup → Spec → Design → Plan → Tests → Implement từng bước → Summary/verify → Review → Cải tiến context

```
Setup → 01-spec → 02-design → 03-plan → 04-tests
      → 05-implement (từng bước) → 06-summary → Review diff → Merge
      → Ghi bài học vào AGENTS.md
```

Quy tắc xuyên suốt: mỗi giai đoạn ghi output vào `docs/ai/<task-slug>/` rồi **dừng chờ duyệt**. Chỉ sang bước sau khi tôi nhắn `APPROVED`.

---

## 1. Setup agent (làm một lần cho mỗi repo)

| Hạng mục | Việc cần làm |
|---|---|
| Context file | Tạo `CLAUDE.md` (hoặc `AGENTS.md`, dùng `@AGENTS.md` để import nếu dùng nhiều công cụ) |
| Nội dung context | Mô tả dự án, tech stack, lệnh test/lint/type check, kiến trúc, quy ước, quy tắc bảo mật, mục **Do NOT**, workflow, definition of done, **Known pitfalls** |
| Branch | Agent chỉ làm việc trên branch riêng, không bao giờ trên main |
| Quyền hạn | Cho phép tự chạy test/lint; lệnh có tác dụng phụ (xóa file, push, cài package) phải hỏi |
| Dữ liệu nhạy cảm | Không để secret, `.env`, dữ liệu khách hàng trong tầm đọc của agent |
| CI | Lint, type check, test, quét dependency chạy tự động, kể cả với code AI viết |

**Quy tắc workflow nên đặt vào `AGENTS.md`:**
```
- Work in stages: 01-spec -> 02-design -> 03-plan -> 04-tests -> implement.
  Each documentation stage writes its output to docs/ai/<task-slug>/ then STOPS.
- Do not start the next stage until I reply "APPROVED".
- No source code before stage 4 is approved (stage 4 writes tests only).
- Never invent requirements. Unknowns go under "Open questions";
  mark guesses as "Assumption:".
- A task is DONE only when test + lint + type check pass.
```

---

## 2. Spec → `01-spec.md`

**Mục tiêu:** chốt "đúng" nghĩa là gì, trước khi bàn cách làm.

**Prompt (điền phần trong `{{}}`, bỏ dòng không dùng):**
```
Stage 1 - SPEC. Read the relevant code first, but do not change anything.
Task slug: {{task-slug}}

## My brief
- Goal / problem: {{what and why}}
- Users / context: {{who uses it, where it runs}}
- Must have: {{...}}
- Out of scope: {{...}}
- Constraints: {{performance, security, compatibility, OS, dependencies}}
- Success looks like: {{measurable outcomes}}

Write docs/ai/{{task-slug}}/01-spec.md with:
1. Goal and non-goals
2. Functional requirements (numbered FR-1.., each testable)
3. Non-functional requirements (performance, security, reliability, limits)
4. Edge cases and failure behavior
5. Acceptance criteria (each mapped to an FR)
6. Assumptions
7. Open questions

Then stop and wait for my review.
```

**Review nhanh:**
- Tự ghi 3-4 tình huống xấu nhất **trước** khi đọc, rồi đối chiếu.
- Đọc Assumptions và Open questions trước.
- Xóa yêu cầu agent tự thêm; biến câu mơ hồ thành tiêu chí đo được.
- **Duyệt khi:** mỗi yêu cầu có thể viết thành một test và không còn câu hỏi treo.

---

## 3. Design → `02-design.md`

**Mục tiêu:** mô tả chi tiết cách tiếp cận và kiến trúc dựa trên spec đã duyệt.

**Prompt:**
```
Stage 2 - DESIGN. Inputs: approved 01-spec.md and the affected code.
Task slug: {{task-slug}}
Re-read the approved spec and relevant architecture. Do not write source code.

Write docs/ai/{{task-slug}}/02-design.md with:
1. Chosen approach and why it fits the spec and existing architecture
2. Alternatives considered and trade-offs
3. Architecture: components, responsibilities, and their interactions
4. Diagram of the relevant components or flow (Mermaid or a simple text diagram)
5. Key interfaces and data flow, including error handling
6. Security, concurrency, resource limits, and compatibility where relevant
7. Risks, assumptions, and open questions

Give enough detail for the implementation plan to follow the design.
Flag any conflict with AGENTS.md or need for a new dependency.
Then stop and wait for my review.
```

**Review nhanh:**
- Phương án chọn và đánh đổi phù hợp với spec và kiến trúc hiện có.
- Thành phần, trách nhiệm, luồng dữ liệu và sơ đồ khớp nhau.
- Giao diện, xử lý lỗi và các ràng buộc liên quan đủ rõ để lập plan.
- **Duyệt khi:** không cần quyết định lại kiến trúc trong lúc triển khai.

---

## 4. Plan → `03-plan.md`

**Mục tiêu:** chia thiết kế đã duyệt thành các bước triển khai nhỏ, kiểm chứng được.

**Prompt:**
```
Stage 3 - PLAN. Inputs: approved 01-spec.md and 02-design.md.
Task slug: {{task-slug}}
Re-read the spec, design, and affected code. Do not write source code.

Write docs/ai/{{task-slug}}/03-plan.md with:
1. Implementation summary based on the approved design
2. Files to create or modify (path + change + why)
3. Small, ordered implementation steps, each independently verifiable
   (target < ~150 changed lines per step)
4. Verification for each step, including relevant tests and checks
5. Spec traceability: each FR/NFR -> step(s)
6. Implementation risks and open questions

Flag any step that conflicts with the approved design or AGENTS.md, or needs a new dependency.
Then stop and wait for my review.
```

**Review nhanh:**
- Bảng traceability không có ô trống.
- Danh sách file thay đổi hợp lý, không chạm việc không liên quan.
- Mỗi bước đủ nhỏ để review; không thêm dependency lạ.
- Rủi ro về concurrency, bảo mật, tài nguyên được nêu cụ thể.
- **Duyệt khi:** làm theo từng bước thì mỗi bước đều chạy và kiểm tra được.

---

## 5. Tests → `04-tests.md` + file test

**Mục tiêu:** biến spec thành test chạy được và đang đỏ đúng lý do.

**Prompt:**
```
Stage 4 - TESTS FIRST. Inputs: approved 01-spec.md, 02-design.md, and 03-plan.md.
Task slug: {{task-slug}}
Write tests only; do not implement the feature.

1. Write docs/ai/{{task-slug}}/04-tests.md with:
   - Test matrix: name | spec ref | type | expected result
   - Cases: happy path, edge cases, failure paths, security/abuse cases, concurrency cases (if relevant): {{extra cases I want}}
   - Fixtures needed and what is mocked (and why)
   - Spec items NOT covered, with reason
2. Create the test files, following existing conventions.
3. Run: {{test command}}. 
   Confirm each test fails for the RIGHT reason (missing feature, not typo/import error). 
   Paste the failing summary into 04-tests.md.

Do not modify existing fixtures. Then stop and wait for my review.
```

**Review nhanh:**
- Mỗi spec item có test; phần không cover có lý do chính đáng.
- Xem output chạy thật: test đỏ vì thiếu tính năng, không phải lỗi import hay typo.
- Assertion cụ thể; mock không che mất logic cần kiểm chứng.
- **Duyệt khi:** test phủ đủ spec (kể cả trường hợp xấu) và đang đỏ đúng lý do.

---

## 6. Implement từng bước nhỏ

**Mục tiêu:** làm đúng từng bước của plan, mỗi bước kiểm chứng được, diff nhỏ để review.

**Prompt (lặp cho mỗi bước N):**
```
Stage 5 - IMPLEMENT. Inputs: approved 01-spec.md, 02-design.md, 03-plan.md, and 04-tests.md.
Task slug: {{task-slug}}
Implement step {{N}} of docs/ai/{{task-slug}}/03-plan.md only.

- Follow the approved spec, design, and plan; make the related tests pass without modifying them.
- Change only files listed for this step. Do not add dependencies or do unrelated cleanup.
- If the spec, design, plan, or tests conflict or this step needs a larger change, explain the issue and stop before editing.
- Run: {{test command}}, {{lint command}}, {{type check command}} (use the applicable repo commands).
- Report changed files, verification commands and results, and any risks or uncovered checks.

Then stop and wait for my review before starting another step.
```

The implementation prompt expects the approved spec, design, plan, and tests. It limits
changes to the current step, asks the agent to stop on conflicts, and requires
verification results before pausing for review.

**Quy tắc:**
- Diff mỗi bước lý tưởng dưới khoảng 150-300 dòng; lớn hơn thì yêu cầu chia nhỏ.
- Không sửa test để khớp code. Nếu cho rằng test sai, agent phải nêu spec item nào bị mâu thuẫn và dừng lại.
- Phát hiện spec/design/plan thiếu hoặc sai thì quay lại sửa file upstream trước, rồi mới tiếp tục code.

---

## 7. Verify (tôi tự chạy, không chỉ tin lời agent)

- [ ] `test`, `lint`, `type check` đều pass do **chính tôi chạy**.
- [ ] Thử thủ công với dữ liệu thật: một trường hợp đúng, một hỏng, một cực lớn.
- [ ] **Kiểm tra đột biến:** cố tình phá một dòng logic quan trọng (bỏ kiểm tra giới hạn, đổi `<=` thành `<`); test vẫn xanh nghĩa là test yếu.
- [ ] Diff nằm trong phạm vi plan; không file ngoài kế hoạch, không dependency mới.
- [ ] CI pass trên branch.

---

## 8. Summary → `06-summary.md`

**Mục tiêu:** kiểm tra toàn bộ spec sau khi mọi bước implement đã được duyệt, rồi ghi lại kết quả, giới hạn, rủi ro và bài học.

**Prompt:**
```
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
```

Agent chỉ đề xuất các dòng **Known pitfalls** trong summary; bạn review rồi tự cập nhật `AGENTS.md` nếu phù hợp.

---

## 9. Review kết quả (diff)

Đọc diff như đọc code của người lạ chưa có lý do để tin.

| Nhóm | Câu hỏi chính |
|---|---|
| Đúng spec | Mỗi yêu cầu có code và test? Agent có tự thêm gì không? |
| Edge case | Rỗng, hỏng, cực lớn, encoding, giá trị biên? |
| Bảo mật | Validate ở ranh giới? Path traversal? Giới hạn tài nguyên? Log lộ dữ liệu? |
| Concurrency | Trạng thái dùng chung? Race/deadlock? Giải phóng tài nguyên khi lỗi? |
| Xử lý lỗi | Có nuốt lỗi? Trạng thái dở dang? |
| Dependency | Gói mới có thật, nguồn đáng tin? |
| Test | Có thể fail khi code sai không? |
| Tôi có hiểu không | Không giải thích lại được thì không merge |

**Lỗi AI hay gặp:** kiểm tra chuỗi thay vì chuẩn hóa đường dẫn; tin kích thước khai báo trong header; `except` quá rộng rồi bỏ qua; test chỉ mock rồi assert điều hiển nhiên; bịa tên hàm/thư viện; sửa test cho khớp code; làm lan phạm vi; quên đóng tài nguyên ở nhánh lỗi.

---

## 10. Follow up để AI sửa

| Tình huống | Cách làm |
|---|---|
| Chỉnh nhỏ, tôi biết đáp án | Tự sửa trực tiếp trong file, báo agent đọc lại |
| Nhiều góp ý | Gửi danh sách đánh số |
| Lỗi lặp lại | Thêm vào **Known pitfalls** trong `AGENTS.md` và thêm test |
| Phiên dài, agent bắt đầu lạc | Mở phiên mới, chỉ nạp `AGENTS.md` và các file đã duyệt |

**Mẫu góp ý (đánh số, có lý do, giới hạn phạm vi):**
```
Feedback on 01-spec.md:
1. FR-3: "reject large files" is vague. Limit = 200MB of ACTUAL extracted
   bytes, not header-declared size (headers can be forged).
2. Remove FR-6: out of scope.
3. Missing edge case: encrypted archives -> reject with a clear error.

Revise ONLY these points. Keep everything else unchanged.
List what you changed, then stop.
```

**Quy tắc:**
- Luôn yêu cầu "list what you changed" để không có thay đổi âm thầm.
- File luôn là bản đúng nhất; đừng để quyết định chỉ nằm trong chat.
- Sửa upstream trước (spec → design → plan → tests → code).
- Nêu **lý do**, không chỉ lệnh cấm.
- Sau hai vòng sửa chưa đạt thì tự viết phần then chốt hoặc chia nhỏ lại task.
- Bắt được lỗi thì hỏi thêm: "Còn chỗ nào khác có cùng kiểu lỗi này không?"

---

## 11. Kết thúc và cải tiến

- Ghi **Review log** vào cuối file đã duyệt hoặc trong PR:
  ```
  - Reviewer / Date:
  - Decision: APPROVED / APPROVED WITH CHANGES / REJECTED
  - Changes requested:
  - Remaining risks / not covered:
  - Added to AGENTS.md "Known pitfalls":
  ```
- Mỗi lỗi agent lặp lại: thêm một dòng vào **Known pitfalls** và một test chặn lỗi đó.
- Giữ `AGENTS.md` ngắn (dưới khoảng 100-150 dòng), chỉ ghi điều agent không tự suy ra được từ code.

---

## 12. Checklist một dòng cho mỗi task

1. [ ] Context file và guardrails đã sẵn sàng, đang ở branch riêng
2. [ ] Spec: duyệt, hết open questions
3. [ ] Design: duyệt kiến trúc, sơ đồ và luồng xử lý
4. [ ] Plan: duyệt, traceability đủ, các bước nhỏ
5. [ ] Tests: duyệt, đỏ đúng lý do
6. [ ] Implement từng bước, mỗi bước test + lint + type check pass
7. [ ] Summary: full suites pass, traceability đủ, summary ghi rõ limitation/risk/follow-up
8. [ ] Tôi tự verify, kiểm tra đột biến, thử dữ liệu thật
9. [ ] Review diff theo checklist, hiểu toàn bộ code
10. [ ] Ghi review log, cập nhật Known pitfalls nếu phù hợp
11. [ ] Merge qua CI

> Chi tiết cách review từng bước và các mẫu prompt follow up xem thêm trong `ai-review-guide.md`.
