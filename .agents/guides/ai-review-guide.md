# Hướng dẫn review output của AI agent

Tài liệu này dùng cho quy trình: **Spec → Design → Plan → Tests → Implementation → Summary**. Mỗi giai đoạn tạo tài liệu ghi một file markdown trong `docs/ai/<task-slug>/` và dừng lại chờ duyệt.

## 1. Nguyên tắc chung

1. **Review để ra quyết định.** Mỗi file có một câu hỏi chính; trả lời được thì mới duyệt.
2. **Dồn thời gian vào bước đầu.** Sai ở spec thì hỏng cả chuỗi, sai ở plan thì tốn công sửa code, sai ở test thì code đúng cũng bị đánh giá sai.
3. **Đọc "Assumptions" và "Open questions" trước.** Đó là chỗ agent tự thú những điều nó đoán.
4. **Tìm cái bị thiếu, không chỉ cái đang viết.** Lỗi thiếu khó thấy hơn lỗi sai.
5. **Tự nghĩ trước, đọc sau.** Liệt kê nhanh 3-4 tình huống xấu nhất của bạn rồi mới đối chiếu với output, để không bị agent dẫn dắt.
6. **Không giải thích lại được bằng lời của mình thì không duyệt.**

## 2. Checklist chung (áp dụng cho mọi bước)

- [ ] Output bám đúng yêu cầu của tôi, không có thứ tôi chưa hề yêu cầu.
- [ ] Mọi assumption đều được ghi rõ và tôi đồng ý với từng cái.
- [ ] Mọi open question đã được tôi trả lời hoặc loại bỏ.
- [ ] Không mâu thuẫn với `AGENTS.md` (kiến trúc, quy ước, mục "Do NOT").
- [ ] Không thêm dependency mới khi chưa được phép.
- [ ] Có xét tới bảo mật, xử lý lỗi, giới hạn tài nguyên (nếu liên quan dữ liệu không tin cậy).
- [ ] Có xét tới concurrency, môi trường (Windows/Linux, Docker) nếu liên quan.
- [ ] Phạm vi thay đổi nhỏ, tập trung, không "tiện tay" sửa việc khác.
- [ ] Cụ thể, kiểm chứng được; không có câu mơ hồ kiểu "nhanh", "an toàn", "hợp lý".
- [ ] Tôi giải thích lại được nội dung bằng lời của mình.

## 3. Review từng bước

### Bước 1: `01-spec.md`

**Câu hỏi chính:** Đây có đúng là thứ tôi muốn không?

| Kiểm tra | Dấu hiệu có vấn đề |
|---|---|
| Yêu cầu kiểm chứng được | Câu mơ hồ, không có con số hay hành vi cụ thể |
| Không có yêu cầu "tự thêm" | Có FR mà tôi không đề cập |
| Non-goals rõ | Agent mở rộng phạm vi sang việc khác |
| Edge case và hành vi khi lỗi | Chỉ có happy path |
| Acceptance criteria khớp FR | Tiêu chí không trỏ về yêu cầu nào |
| Assumptions đúng | Có điều agent đoán sai về hệ thống thật |

**Cách làm:**
- Trước khi đọc, tự ghi 3-4 trường hợp xấu nhất (file rỗng, quá lớn, hỏng, đầu vào độc hại, lỗi giữa chừng, chạy đồng thời).
- Đọc spec, đối chiếu với danh sách của bạn, bổ sung chỗ thiếu.
- Biến câu mơ hồ thành tiêu chí đo được. Ví dụ: "xử lý file lớn" → "file tới 200MB, dùng stream, RAM không vượt X".
- Trả lời hết Open questions.

**Duyệt khi:** mỗi yêu cầu có thể viết thành một test, và không còn câu hỏi treo.

### Bước 2: `02-design.md`

**Câu hỏi chính:** Kiến trúc và luồng xử lý có đáp ứng spec không?

| Kiểm tra | Dấu hiệu có vấn đề |
|---|---|
| Phương án và đánh đổi | Không giải thích vì sao chọn cách này |
| Thành phần và trách nhiệm | Ranh giới mơ hồ hoặc trùng lặp |
| Sơ đồ và luồng dữ liệu | Sơ đồ không khớp mô tả |
| Giao diện và lỗi | Thiếu đầu vào/đầu ra hoặc hành vi khi lỗi |
| Ràng buộc | Bỏ sót bảo mật, concurrency, tài nguyên hoặc tương thích khi liên quan |

**Duyệt khi:** thiết kế đủ cụ thể để lập kế hoạch triển khai mà không phải quyết định lại kiến trúc.

### Bước 3: `03-plan.md`

**Câu hỏi chính:** Cách làm này có hợp lý, đủ nhỏ để review, và phủ hết spec không?

| Kiểm tra | Dấu hiệu có vấn đề |
|---|---|
| Bảng traceability đủ | FR/NFR nào đó không nằm trong bước nào |
| Danh sách file thay đổi hợp lý | Chạm nhiều file không liên quan |
| Bám thiết kế đã duyệt | Bước triển khai đổi kiến trúc mà không giải thích |
| Từng bước nhỏ, kiểm chứng độc lập | Bước nào cũng "implement toàn bộ" |
| Rủi ro cụ thể | Rủi ro viết chung chung cho có |
| Tương thích ngược | Không đề cập hành vi cũ bị ảnh hưởng |
| Dependency | Thêm thư viện lạ, tên gói không rõ nguồn |

**Cách làm:**
- Đánh dấu từng dòng trong bảng traceability; ô trống là yêu cầu bị bỏ rơi.
- Mỗi bước nên thay đổi dưới khoảng 150 dòng; bước nào lớn hơn thì yêu cầu chia nhỏ.
- Kiểm tra riêng phần concurrency, bảo mật, tài nguyên: agent hay lướt qua các mục này.
- Nếu dùng thư viện mới, tự xác minh nó có thật, còn được bảo trì, và được phép dùng.

**Duyệt khi:** làm theo từng bước thì mỗi bước đều chạy và kiểm tra được, không bước nào bất ngờ.

### Bước 4: `04-tests.md` và file test

**Câu hỏi chính:** Test này có thể bắt được lỗi thật không?

| Kiểm tra | Dấu hiệu có vấn đề |
|---|---|
| Mỗi spec item có test | Có FR không test nào trỏ tới |
| Phần "không cover" có lý do | Bỏ qua mà không giải thích |
| Fail đúng lý do | Fail do lỗi import, typo, thiếu fixture |
| Assertion cụ thể | Chỉ assert "không ném lỗi" hoặc điều hiển nhiên |
| Mock hợp lý | Mock luôn cả logic cần kiểm chứng |
| Có test xấu | Thiếu abuse case, edge case, lỗi giữa chừng |
| Không sửa fixture cũ | Fixture hiện có bị thay đổi |

**Cách làm:**
- Xem output chạy test thật, không chỉ đọc bản tóm tắt.
- Với mỗi test, tự hỏi: "Nếu code sai theo cách X thì test này có đỏ không?"
- Sau khi implement xong, thử **kiểm tra đột biến**: cố tình phá một dòng logic quan trọng (bỏ kiểm tra độ sâu, đổi `<=` thành `<`). Test vẫn xanh nghĩa là test yếu.

**Duyệt khi:** test đỏ vì đúng lý do và phủ đủ spec, kể cả các trường hợp xấu.

### Bước 5: Implementation (từng bước nhỏ)

**Câu hỏi chính:** Code này đúng spec, an toàn, và tôi hiểu nó không?

Quy trình mỗi lần review một bước implement:

1. Xem **diff**, không đọc file hoàn chỉnh. Diff lớn hơn khoảng 300 dòng thì yêu cầu chia nhỏ.
2. Tự chạy test, lint, type check; không chỉ tin câu "đã pass" của agent.
3. Đọc diff theo checklist bên dưới.
4. Thử thủ công với dữ liệu thật: một file đúng, một file hỏng, một file lớn.
5. Kiểm tra diff có thay đổi ngoài kế hoạch không.

Khi giao việc cho agent, dùng `05-impl-template/05-impl-prompt.md` với đúng số bước
trong plan. Mỗi prompt chỉ triển khai một bước; duyệt diff và kết quả kiểm tra
trước khi gửi prompt cho bước tiếp theo. Sau khi mọi bước được duyệt, dùng
`06-summary-template/06-summary-prompt.md` để chạy full suite và review summary/traceability.

**Checklist review code:**

| Nhóm | Câu hỏi |
|---|---|
| Đúng spec | Mỗi yêu cầu có code và test tương ứng? Có hành vi nào agent tự thêm? |
| Edge case | Rỗng, hỏng, cực lớn, ký tự lạ, encoding, giá trị biên? |
| Bảo mật | Input được validate ở ranh giới? Path traversal? Giải tuần tự hoặc thực thi dữ liệu không tin cậy? Log có lộ dữ liệu? Giới hạn tài nguyên (timeout, RAM, độ sâu, kích thước)? |
| Concurrency | Có trạng thái dùng chung giữa các luồng/worker? Có race condition, deadlock? Tài nguyên có được giải phóng khi lỗi? |
| Xử lý lỗi | Có nuốt lỗi (`except: pass`)? Thông báo lỗi có rõ và an toàn? Lỗi có để lại trạng thái dở dang? |
| Hiệu năng | Có load toàn bộ vào RAM? Vòng lặp lồng nhau không cần thiết? |
| Thiết kế | Đúng kiến trúc trong `AGENTS.md`? Trách nhiệm tách bạch? Không lặp code? |
| Dependency | Có gói mới? Tên có thật? Nguồn đáng tin? |
| Test | Test có thật sự fail khi code sai không? Có test cho lỗi vừa phát hiện? |
| Khả năng bảo trì | Tên rõ nghĩa, không có code thừa, không có TODO bị bỏ quên? |

**Lỗi AI hay gặp, nên soi kỹ:**
- Kiểm tra chuỗi thay vì chuẩn hóa dữ liệu (ví dụ `startswith("..")` thay vì `resolve()` + `is_relative_to`).
- Tin kích thước **khai báo** trong header thay vì lượng dữ liệu **thực tế**.
- Bắt exception quá rộng rồi bỏ qua.
- Test chỉ mock mọi thứ rồi assert điều hiển nhiên.
- Bịa tên hàm/thư viện không tồn tại; dùng API đã lỗi thời.
- Sửa test cho khớp code thay vì sửa code cho đúng test.
- Thêm tính năng ngoài yêu cầu, hoặc refactor chỗ không liên quan.
- Bỏ sót đóng file/kết nối trong nhánh lỗi.

**Duyệt khi:** test, lint, type check đều pass do chính bạn chạy; diff nằm trong kế hoạch; bạn giải thích lại được từng phần.

### Bước 6: Summary (`06-summary.md`)

**Câu hỏi chính:** Mọi yêu cầu trong spec đã được thực hiện và kiểm chứng chưa?

- Đối chiếu từng FR/NFR và các mục spec khác với code và kết quả kiểm tra; không chấp nhận dòng traceability thiếu bằng chứng.
- Xem output thật của full test, lint, type check và build (nếu áp dụng); xác minh mọi lệnh bị bỏ qua có lý do.
- Kiểm tra limitation, risk, follow-up và Known pitfalls được đề xuất có cụ thể, tái sử dụng được, và dựa trên bài học thực tế.
- **Duyệt khi:** traceability đầy đủ, kết quả kiểm tra rõ ràng, phần chưa giải quyết được nêu minh bạch, và summary được review.

## 4. Cách follow up để AI sửa tốt nhất

### 4.1. Chọn đúng kênh sửa

| Tình huống | Cách làm |
|---|---|
| Chỉnh nhỏ, bạn biết đáp án | Tự sửa trực tiếp trong file, rồi báo agent đọc lại |
| Nhiều góp ý hoặc cần agent suy nghĩ lại | Gửi danh sách góp ý đánh số |
| Lỗi lặp lại nhiều lần | Ghi vào mục "Known pitfalls" của `AGENTS.md` và thêm test |
| Phiên làm việc dài, agent bắt đầu lạc | Mở phiên mới, chỉ nạp `AGENTS.md` và các file đã duyệt |

### 4.2. Cấu trúc một góp ý tốt

Mỗi góp ý nên có đủ bốn phần: **vị trí**, **vấn đề**, **tiêu chí đúng/lý do**, **phạm vi sửa**.

```
Feedback on 01-spec.md:
1. FR-3: "reject large files" is vague. Limit = 200MB of ACTUAL extracted bytes,
   not header-declared size (headers can be forged).
2. Remove FR-6: out of scope, I never requested it.
3. Missing edge case: encrypted archives -> reject with a clear error.
4. Open question Q2: answer is "no, keep it synchronous".

Revise ONLY these points. Keep everything else unchanged.
Then list what you changed (short diff summary) and stop.
```

Ba điểm mấu chốt:
- **Đánh số** để agent trả lời từng điểm và bạn kiểm tra được.
- **Nêu lý do hoặc tiêu chí đúng** để agent sửa đúng hướng và áp dụng được cho các trường hợp tương tự.
- **Giới hạn phạm vi** ("chỉ sửa các điểm này") để tránh agent viết lại cả file và đưa lỗi mới vào.

### 4.3. Mẫu prompt theo tình huống

**Tự sửa trực tiếp trong file:**
```
I edited 01-spec.md directly. Treat my edits as the source of truth.
Re-read it, summarize what changed in your understanding,
then update 02-design.md and 03-plan.md accordingly. Stop after that.
```

**Yêu cầu agent tự phản biện trước khi duyệt:**
```
Before I approve: list the 5 weakest points of this plan, what could break
in production, and which spec items you are least sure are covered.
Do not change any file yet.
```

**Sửa lỗi trong implementation:**
```
Issue in src/archive.py, function extract_entry():
- Path check uses string matching, so "a/../../evil.txt" bypasses it.
- Correct approach: resolve the path and verify it is inside the target dir
  (resolve() + is_relative_to), also reject symlinks pointing outside.
Steps: (1) add a failing test for this case, (2) fix the code,
(3) run tests/lint/type check, (4) show the diff. Do not touch other files.
```

**Agent làm sai phạm vi:**
```
Your diff changes files outside the plan (utils/logging.py, config.py).
Revert those changes. Keep only what step 2 of 03-plan.md requires.
If you think those changes are needed, explain why and wait for my decision.
```

**Agent tự sửa test cho khớp code:**
```
Do not modify tests to make them pass. Tests encode the approved spec.
If you believe a test is wrong, explain which spec item it contradicts and stop.
```

**Không hiểu một đoạn code:**
```
Explain lines 40-72 of parser.py: what each branch handles, which inputs reach it,
and what happens on failure. Do not change the code.
```

### 4.4. Quy tắc khi follow up

- **Luôn yêu cầu "list what you changed"** để biết agent đã sửa gì, tránh thay đổi âm thầm.
- **File luôn là bản đúng nhất.** Đừng để quyết định chỉ nằm trong chat; hãy cập nhật vào file.
- **Sửa theo thứ tự upstream trước:** sửa spec thì cập nhật design, plan và tests theo, rồi mới tới code.
- **Mỗi lần một nhóm vấn đề liên quan.** Trộn nhiều chủ đề khiến agent bỏ sót.
- **Nêu lý do, không chỉ lệnh cấm.** "Không dùng X vì môi trường air-gapped không tải được gói lúc chạy" hiệu quả hơn "không dùng X".
- **Hai vòng sửa vẫn chưa đạt:** dừng lại, tự viết phần then chốt hoặc đổi cách chia nhỏ task, thay vì tiếp tục vòng lặp.
- **Bắt được lỗi, hãy hỏi thêm:** "Còn chỗ nào khác trong diff có cùng kiểu lỗi này không?"

## 5. Những điều nên tránh

- Duyệt vì "trông có vẻ ổn".
- Để agent sửa file đã duyệt mà không báo.
- Để nhiều thay đổi tồn đọng rồi review một lần.
- Sửa qua lại nhiều vòng trong chat mà không cập nhật file.
- Tin kết quả "đã chạy test" mà không tự chạy lại.
- Merge đoạn code mình không hiểu.

## 6. Mẫu ghi nhận sau khi duyệt

Đặt ở cuối mỗi file đã duyệt (hoặc trong PR) để có dấu vết:

```
## Review log
- Reviewer: <tên>   Date: <ngày>
- Decision: APPROVED / APPROVED WITH CHANGES / REJECTED
- Changes requested: <tóm tắt các góp ý đã yêu cầu>
- Remaining risks / not covered: <nếu có>
- Added to AGENTS.md "Known pitfalls": <nếu có>
```

## 7. Tóm tắt nhanh

| Bước | Câu hỏi chính | Việc làm cốt lõi |
|---|---|---|
| Spec | Có đúng ý mình không? | Đối chiếu edge case tự nghĩ, biến câu mơ hồ thành tiêu chí đo được |
| Design | Kiến trúc phù hợp spec? | Soi sơ đồ, trách nhiệm, luồng dữ liệu và rủi ro |
| Plan | Hợp lý, đủ nhỏ, phủ hết spec? | Kiểm tra bảng traceability, chia bước nhỏ, soi rủi ro |
| Tests | Bắt được lỗi thật không? | Xem test fail đúng lý do, soi assertion và mock, kiểm tra đột biến |
| Implement | Đúng, an toàn, mình hiểu? | Tự chạy kiểm tra, đọc diff theo checklist, thử dữ liệu thật |
| Follow up | Sửa đúng và gọn | Góp ý đánh số, có lý do, giới hạn phạm vi, ghi lỗi lặp vào `AGENTS.md` |
