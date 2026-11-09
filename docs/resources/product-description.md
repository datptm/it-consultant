# Promise Hub: tổng hợp ý tưởng, phương pháp và hướng triển khai MVP

**IT Consultant Challenge 2026 · Vòng 1 · Công ty A (nhà bán lẻ vật liệu xây dựng Đan Mạch)**

> *"Khách hàng không mua con số tồn kho. Họ mua một lời hứa mà chúng ta giữ được."*

> **Lưu ý:** mọi con số trong tài liệu (số cửa hàng, baseline, KPI, chi phí giờ công...) là **giả định của nhóm** để minh họa lập luận, cần được đo và xác nhận ở tuần đầu của MVP.

---

## 1. Tóm tắt điều hành

| Nội dung | Tóm tắt |
|---|---|
| **Vấn đề chọn** | Hệ thống phân mảnh: mỗi nước trả lời câu hỏi "có hàng không, bao giờ giao được?" theo một cách khác nhau và không ai hoàn toàn tin câu trả lời. |
| **Quan điểm cốt lõi** | Phân mảnh là **nguyên nhân gốc** của ba thách thức còn lại (thủ công, vận hành không nhất quán, giao hàng kém tin cậy). |
| **Giải pháp** | **Promise Hub**: một lớp dữ liệu và tích hợp dùng chung đặt trên các hệ thống hiện có (ERP, POS, WMS), cung cấp thông tin sản phẩm, tồn kho và ngày giao **kèm điểm tin cậy**. |
| **Điểm khác biệt** | Không giấu sai số của dữ liệu tồn kho, mà **đo lường và hành động theo nó**: mỗi câu trả lời có độ tin cậy để nhân viên biết khi nào nên hứa, khi nào nên xác minh. |
| **MVP** | 12 tuần, thí điểm tại Thụy Điển, khoảng 15 cửa hàng và 1 trung tâm phân phối, chỉ đọc dữ liệu, không thay thế ERP. |
| **Nhân rộng** | Lõi dùng chung, adapter và cấu hình riêng từng nước; mỗi nước có một "chiến thắng đầu tiên" khác nhau từ cùng một nền tảng. |

---

## 2. Bối cảnh và bài toán

Công ty A là nhà bán lẻ vật liệu xây dựng hàng đầu Đan Mạch với hàng trăm cửa hàng tại Đan Mạch, Na Uy và Thụy Điển, phục vụ cả doanh nghiệp xây dựng (B2B) lẫn người tiêu dùng (B2C). Theo đề bài:

- Mỗi nước và khu vực đã tự phát triển hệ thống và quy trình thủ công riêng.
- Bốn thách thức liên quan lẫn nhau: **quy trình thủ công, vận hành không nhất quán, giao hàng và xử lý đơn, hệ thống phân mảnh**.
- Mức độ cấp bách khác nhau theo nước (đề dùng chữ "may", tức chỉ là gợi ý): Đan Mạch nghiêng về quy trình thủ công, Na Uy về vận hành cửa hàng, Thụy Điển về giao hàng.
- Ban điều hành chỉ muốn đầu tư **một** giải pháp số, nhưng không thể triển khai giống hệt nhau ở ba nước.
- Thị trường cạnh tranh cao, thời gian ra thị trường (time to market) là yếu tố then chốt.

**Câu hỏi trung tâm:** *Công ty A nên tập trung vào đâu trước?*

---

## 3. Xác định vấn đề (Identify)

### 3.1. Vấn đề không phải là "nhiều hệ thống", mà là "mất niềm tin vào câu trả lời"

Nói "mỗi nước dùng hệ thống khác nhau" mới chỉ là bề mặt. Vấn đề thật là: tại một thời điểm cụ thể, nhân viên cửa hàng không thể trả lời nhanh và chắc chắn câu hỏi **"sản phẩm này là gì, giá bao nhiêu, còn ở đâu, bao giờ giao được?"**

### 3.2. Chuỗi nhân quả

```
Mỗi nước tự xây hệ thống (lịch sử, sáp nhập, nhu cầu địa phương)
   → Dữ liệu sản phẩm, giá, tồn kho khác nhau, không đồng bộ
      → Nhân viên gọi điện, dùng Excel, đối soát tay      (= quy trình thủ công)
      → Mỗi cửa hàng trả lời khách một kiểu               (= vận hành không nhất quán)
      → Hứa sai ngày giao, giao trễ                       (= giao hàng kém tin cậy)
         → Mọi cải tiến phải làm lại ba lần, khó nhân rộng
```

Ba thách thức còn lại phần lớn là **triệu chứng**; phân mảnh là **nguyên nhân gốc chung**.

### 3.3. Bối cảnh ngành hỗ trợ lập luận

- Các nước Bắc Âu có chuẩn dữ liệu sản phẩm ngành riêng (**NOBB** ở Na Uy, **FINFO** ở Thụy Điển, **Byggebasen** ở Đan Mạch), nên dữ liệu sản phẩm không tự đồng nhất giữa các nước.
- Ngành phân phối vật liệu xây dựng Bắc Âu đang hợp nhất qua mua bán sáp nhập, và đây gần như chắc chắn là một nguồn gốc của sự phân mảnh. Đối thủ lớn lên nhanh nên chậm trễ là rủi ro cạnh tranh.
- ERP thường không được thiết kế để làm "nguồn dữ liệu sản phẩm cho kênh số", nên sự phân mảnh lộ rõ nhất khi dữ liệu phải đi ra cửa hàng, web và khách B2B.

### 3.4. Ai gặp vấn đề

| Nhóm | Nỗi đau |
|---|---|
| Nhân viên quầy/cửa hàng | Không chắc còn hàng, phải gọi cửa hàng khác hoặc kho, mỗi nước một giao diện |
| Khách B2B (nhà thầu, thợ) | Cần biết chắc hàng có và ngày giao để không dừng công trình; giao sai hẹn là mất khách |
| Khách cá nhân (DIY) | Web ghi còn hàng nhưng đến cửa hàng thì hết |
| Điều phối giao hàng, kho | Lập kế hoạch trên dữ liệu trễ hoặc sai |
| Quản lý dữ liệu sản phẩm | Đưa một sản phẩm mới ra ba thị trường phải nhập và chuẩn hóa nhiều lần |
| Ban điều hành, IT tập đoàn | Không có số liệu hợp nhất, mỗi cải tiến phải làm lại cho từng nước |

**Persona chính của MVP:** nhân viên quầy phục vụ khách B2B (nhà thầu).

**Kịch bản minh họa (giả định):** 7 giờ sáng, nhà thầu cần 60 tấm thạch cao giao vào thứ Năm. Hệ thống tại quầy báo "còn hàng". Nhân viên gọi cửa hàng khác và kho, mất 3 cuộc gọi, 40 phút, rồi hứa thứ Năm. Thực tế hàng đến thứ Sáu và công trình dừng một ngày.

---

## 4. Ưu tiên hóa (Prioritise)

### 4.1. Ma trận chấm điểm

Nhóm chấm điểm 1 đến 5 (đánh giá chủ quan dựa trên thông tin đề bài):

| Tiêu chí (trọng số) | Thủ công | Vận hành cửa hàng | Giao hàng | **Phân mảnh** |
|---|---|---|---|---|
| Phạm vi ảnh hưởng ba nước (25%) | 3 | 3 | 3 | **5** |
| Là nguyên nhân gốc, nền tảng (20%) | 2 | 3 | 2 | **5** |
| Tốc độ ra giá trị với MVP (20%) | 4 | 2 | 3 | 3 |
| Tính khả thi, rủi ro (15%) | 4 | 2 | 3 | 3 |
| Đo lường được ROI (10%) | 4 | 2 | 4 | 4 |
| Tiềm năng AI (10%) | 4 | 3 | 4 | 4 |
| **Điểm có trọng số** | 3,35 | 2,55 | 3,00 | **4,10** |

### 4.2. Vì sao không chọn ba vấn đề còn lại

- **Quy trình thủ công:** có thể cho kết quả nhanh, nhưng tự động hóa trên dữ liệu chưa đáng tin chỉ làm lỗi chạy nhanh hơn.
- **Giao hàng và xử lý đơn:** lời hứa giao hàng phụ thuộc vào việc dữ liệu tồn kho đáng tin trước.
- **Vận hành cửa hàng:** muốn chuẩn hóa cách làm việc thì cần dữ liệu và công cụ nhất quán trước.

### 4.3. Thừa nhận đánh đổi

Nếu làm theo kiểu "big-bang" (hợp nhất toàn bộ hệ thống), phân mảnh sẽ chậm và rủi ro, điểm tốc độ và khả thi thấp. Vì vậy MVP được thiết kế là **lớp mỏng chạy trên hệ thống cũ, không thay ERP**.

---

## 5. Giải pháp: Promise Hub

### 5.1. Kiến trúc năm lớp

| Lớp | Thành phần |
|---|---|
| **Trải nghiệm** | Store Assistant App (web/tablet), widget tình trạng hàng cho cổng B2B và web, dashboard điều phối |
| **Dịch vụ dùng chung** | Product Master, Unified Inventory, **Promise Engine** (ATP kèm độ tin cậy), Search |
| **Mô hình dữ liệu chuẩn** | Product (ánh xạ NOBB/FINFO/Byggebasen), Price, Stock, Delivery Promise |
| **Tích hợp** | API gateway, luồng sự kiện (event streaming), **adapter riêng từng nước** |
| **Nguồn dữ liệu** | ERP, POS, WMS, TMS, feed nhà cung cấp, thương mại điện tử |

### 5.2. Nguyên tắc thiết kế

1. **Strangler approach:** không thay thế hệ thống cũ, bọc và đọc dữ liệu qua adapter; giai đoạn đầu chỉ đọc (read-only) để giảm rủi ro.
2. **Lõi dùng chung, adapter tùy biến theo nước:** khớp với yêu cầu "một giải pháp chiến lược không đồng nghĩa một cách triển khai giống hệt nhau".
3. **API-first, ưu tiên cấu hình hoặc mua sẵn hơn tự xây** để rút ngắn time to market.
4. **Chủ quyền dữ liệu:** hạ tầng đặt tại EU, tuân thủ GDPR, có nhật ký kiểm toán. Điều này khớp định hướng "phát triển ở châu Âu cho châu Âu" của ban tổ chức.

---

## 6. Tính năng cốt lõi: lời hứa có độ tin cậy

### 6.1. Ý tưởng

Dữ liệu tồn kho **luôn có sai số**. Thay vì hiển thị một con số như thể nó chắc chắn, Promise Hub hiển thị con số **kèm điểm tin cậy** và thời điểm xác minh gần nhất. Ví dụ trên màn hình nhân viên:

```
Tấm thạch cao 13 mm chống ẩm  (mã sản phẩm đã hài hòa NOBB/FINFO/Byggebasen)
Cửa hàng: 40 tấm · Độ tin cậy 92% · kiểm lần cuối 2 giờ trước
Kho (DC): 1.200 tấm · Độ tin cậy 97%
Giao hàng: thứ Năm · Xác suất đúng hạn 90%
[Hứa với khách]   [Xác minh tồn kho]   [Báo sai lệch]
```

### 6.2. Cách tính điểm tin cậy

**Đầu vào (tín hiệu):**
- thời gian kể từ lần kiểm kho gần nhất,
- tốc độ xuất nhập của mặt hàng (hàng xoay nhanh dễ sai lệch hơn),
- tỷ lệ sai lệch lịch sử theo mặt hàng và theo địa điểm,
- số giao dịch chưa đồng bộ,
- độ trễ của hệ thống nguồn,
- loại sản phẩm (hàng rời, hàng nhỏ lẻ, hàng cồng kềnh).

**Ba dải hành động:**

| Dải | Ý nghĩa | Hành động gợi ý |
|---|---|---|
| 🟢 Cao | Đủ tin cậy | Hứa với khách ngay |
| 🟡 Trung bình | Cần xác minh | Quét hoặc kiểm tra nhanh trước khi hứa |
| 🔴 Thấp | Không đáng tin | Không hứa; gợi ý cửa hàng hoặc kho khác, hoặc ngày giao thận trọng hơn |

**Khởi động (cold start):**
- Tuần 1 đến 6: chấm điểm theo **quy tắc** (ví dụ trừ điểm theo số ngày từ lần kiểm kho, giao dịch chưa đồng bộ, lịch sử sai lệch).
- Từ tuần 7: chuyển sang **mô hình ML** huấn luyện trên lịch sử điều chỉnh tồn kho và nhật ký kiểm kho định kỳ từ ERP.
- **Hiệu chỉnh:** so sánh xác suất dự đoán với kết quả kiểm kho thực tế (đường cong hiệu chỉnh, Brier score), để "92%" thực sự nghĩa là xấp xỉ 92% đúng.

### 6.3. Vòng phản hồi (data flywheel)

Mỗi khi nhân viên chạm "xác nhận đúng" hoặc "báo sai lệch", dữ liệu được sửa và đồng thời trở thành nhãn huấn luyện cho mô hình. Nhân viên cửa hàng không bị thay thế bởi AI, mà trở thành **cảm biến chất lượng dữ liệu**, điều này cũng hỗ trợ việc chấp nhận thay đổi.

---

## 7. Vai trò của AI

AI được dùng có chọn lọc, đúng loại kỹ thuật cho đúng việc:

| Chức năng | Kỹ thuật | Giai đoạn | Lý do |
|---|---|---|---|
| Tính ngày giao | Quy tắc + ML | MVP | Ràng buộc cố định cộng độ trễ học từ lịch sử |
| Chấm điểm tin cậy | ML cổ điển | MVP (quy tắc trước, ML sau) | Cần xác suất được hiệu chỉnh, chi phí thấp |
| Phát hiện bất thường tồn kho | ML cổ điển | MVP-lite | Nhận diện mẫu trên dữ liệu số |
| Hài hòa dữ liệu sản phẩm (ánh xạ thuộc tính, loại trùng, dịch Đan Mạch/Na Uy/Thụy Điển) | AI tạo sinh, có người duyệt | MVP | Dữ liệu văn bản phi cấu trúc, nhiều biến thể |
| Bản nháp ánh xạ tích hợp và test | AI tạo sinh, lập trình viên duyệt | MVP (khi xây) | Giảm thời gian và chi phí mỗi adapter khi mở rộng |
| Tìm kiếm ngôn ngữ tự nhiên ba thứ tiếng | AI tạo sinh, embeddings | MVP-lite hoặc giai đoạn 2 | Nhân viên và thợ mô tả, không nhớ mã |
| Dự báo nhu cầu, dự đoán ngày giao nâng cao | ML | Giai đoạn 2 | Cần dữ liệu sạch từ Hub trước |

**Rào chắn (guardrails):** mô hình và dữ liệu đặt tại EU; ngưỡng độ tin cậy với người duyệt trong vòng lặp; nhật ký kiểm toán đầy đủ; các ca dùng này thuộc nhóm rủi ro thấp theo EU AI Act (cần xác nhận lại khi triển khai thật). Cần tính đến chi phí vận hành AI (token, đánh giá chất lượng).

---

## 8. Hướng triển khai MVP

### 8.1. Giả thuyết cần kiểm chứng

> *Nếu nhân viên và khách B2B có một nguồn sự thật duy nhất về sản phẩm, tồn kho và ngày giao, kèm độ tin cậy, thì thời gian tra cứu, số cuộc gọi đối soát và tỷ lệ hứa giao sai sẽ giảm rõ rệt.*

### 8.2. Phạm vi

| Trong phạm vi | Ngoài phạm vi |
|---|---|
| 1 adapter ERP và 1 adapter POS/WMS tại nước thí điểm (chỉ đọc) | Thay thế ERP |
| Mô hình dữ liệu chuẩn cho nhóm SKU bán chạy (giả định 10.000 đến 20.000 SKU) | Định giá, tài chính, nhân sự |
| Hài hòa dữ liệu sản phẩm có AI hỗ trợ | Dựng lại toàn bộ thương mại điện tử |
| Tồn kho hợp nhất và Promise Engine cho khoảng 15 cửa hàng và 1 trung tâm phân phối | Ghi ngược (write-back) mọi loại đơn hàng |
| Store Assistant App: tìm kiếm, xem tồn kho cửa hàng/kho lân cận, ngày giao dự kiến, báo lỗi dữ liệu | Logistics xuyên biên giới, dự báo nâng cao |
| Dashboard KPI | |

**Vì sao thí điểm ở Thụy Điển (giả định):** đề nêu giao hàng và xử lý đơn là điểm đau lớn ở đó, nên giá trị của "ngày giao đáng tin" thể hiện nhanh nhất. Phương án thay thế là Đan Mạch (thị trường nhà, phối hợp dễ hơn).

### 8.3. Lộ trình 12 tuần

| Tuần | Hoạt động chính | Kết quả bàn giao |
|---|---|---|
| **1–2 Khám phá** | Phỏng vấn nhân viên và điều phối, chọn cửa hàng thí điểm và cửa hàng đối chứng, kiểm toán dữ liệu (mức trùng SKU, lấy mẫu độ chính xác tồn kho), thiết lập KPI nền, xin quyền truy cập API, rà soát bảo mật và GDPR | Báo cáo baseline, danh sách SKU ưu tiên, kế hoạch tích hợp |
| **3–4 Nền tảng** | Mô hình dữ liệu chuẩn v1, adapter ERP chỉ đọc, đường ống sự kiện, pipeline hài hòa sản phẩm với hàng đợi duyệt cho người | Dữ liệu sản phẩm và tồn kho hợp nhất cho nhóm SKU ưu tiên |
| **5–6 Lõi tính năng** | Unified Inventory, Promise Engine theo quy tắc, bản alpha Store Assistant, thử với 2 cửa hàng | Bản demo chạy được trên dữ liệu thật |
| **7–8 Hoàn thiện** | Mô hình ML độ tin cậy v1, nút phản hồi, dashboard KPI, kiểm thử hiệu năng và bảo mật | Bản sẵn sàng thí điểm |
| **9–10 Thí điểm** | Triển khai tại khoảng 15 cửa hàng và 1 DC, đào tạo, "champion" tại mỗi cửa hàng, họp đứng hằng ngày để thu phản hồi | Dữ liệu sử dụng thực tế |
| **11–12 Đo và quyết định** | So sánh cửa hàng thí điểm với cửa hàng đối chứng tương đương, tổng kết, quyết định go/no-go, lập kế hoạch đợt tiếp theo | Báo cáo kết quả và đề xuất mở rộng |

### 8.4. Đội ngũ gợi ý (khoảng 8 người)

Product owner, kiến trúc sư, 3 kỹ sư tích hợp/backend, 1 kỹ sư dữ liệu/AI, 1 UX/frontend, 1 QA.

### 8.5. Cách đo hiệu quả

- Đo **baseline ở tuần 1** trước khi can thiệp.
- Dùng **cửa hàng đối chứng** có quy mô và đặc điểm tương đồng để tách tác động của MVP khỏi yếu tố mùa vụ.
- Theo dõi cả chỉ số kết quả (đúng hạn, thời gian tiết kiệm) lẫn chỉ số chấp nhận (tỷ lệ nhân viên dùng hằng tuần).

### 8.6. Tiêu chí dừng hoặc điều chỉnh (go/no-go)

| Tiêu chí | Ngưỡng |
|---|---|
| Độ chính xác tồn kho hiển thị | ≥ 92% |
| Nhân viên quầy dùng hằng tuần | ≥ 60% |
| Độ chính xác lời hứa giao đúng hạn | +5 điểm % so với baseline |

**Nếu không đạt 2 trong 3 tiêu chí:** tạm dừng và điều chỉnh trước khi mở rộng, không tiếp tục đầu tư theo quán tính.

---

## 9. Tác động kinh doanh

| KPI | Baseline (giả định) | Mục tiêu thí điểm | Mục tiêu khi mở rộng |
|---|---|---|---|
| Độ chính xác lời hứa giao đúng hạn | Đo ở tuần 1 | +5 điểm % | +10 điểm % |
| Độ chính xác tồn kho hiển thị | ~85% | ≥ 92% | ≥ 95% |
| Thời gian nhân viên mất cho tra cứu, gọi đối soát | Đo ở tuần 1 | −40% | −50% |
| Thời gian chuẩn hóa dữ liệu sản phẩm mới | 4–6 tuần | ≤ 2 tuần | < 1 tuần |
| Thời gian tích hợp một thị trường mới | 12 tháng trở lên | không áp dụng | < 6 tháng |

**Ví dụ tính ROI (số minh họa):**

- Tiết kiệm công = số cửa hàng × số người dùng × phút tiết kiệm mỗi ngày × số ngày × giá giờ công.
- Ví dụ: 300 cửa hàng × 3 người × 10 phút/ngày × 300 ngày ≈ 45.000 giờ/năm; với 35 EUR/giờ ≈ **1,6 triệu EUR/năm**.
- Cộng thêm doanh thu giữ lại do giảm số đơn mất vì "không chắc có hàng" (cần doanh thu thật để tính).
- Cần bổ sung ước lượng chi phí đầu tư MVP và thời gian hoàn vốn (nên có khoảng dao động).

---

## 10. Nhân rộng (Scale)

### 10.1. Lõi dùng chung và phần tùy biến

| Dùng chung (Global core) | Tùy biến theo nước (Local) |
|---|---|
| Mô hình dữ liệu chuẩn, hub tích hợp, API, bảo mật, giám sát | Adapter cho ERP/POS/WMS từng nước |
| Promise Engine, thiết kế UX, mô hình AI | Chuẩn dữ liệu sản phẩm (NOBB, FINFO, Byggebasen), ngôn ngữ, tiền tệ (SEK, NOK, DKK) |
| Quy trình quản trị dữ liệu | Quy tắc giao hàng, đối tác vận tải, thỏa thuận giá B2B |
| | Đào tạo, quản lý thay đổi, tham vấn đại diện người lao động (cần kiểm tra yêu cầu từng nước) |

**Cấu hình thay cho mã:** khác biệt giữa các nước (quy tắc giao hàng, đơn vị, thuế, ngôn ngữ) được khai báo bằng cấu hình. Thêm một nước nghĩa là thêm một gói cấu hình và một adapter.

### 10.2. Một nền tảng, ba "chiến thắng đầu tiên"

| Nước | Điểm đau theo đề | Giá trị đầu tiên từ Hub |
|---|---|---|
| **Thụy Điển** (thí điểm) | Giao hàng, xử lý đơn | Ngày giao đáng tin cậy |
| **Na Uy** (đợt 2) | Vận hành cửa hàng | Store Assistant chuẩn hóa trải nghiệm ở quầy |
| **Đan Mạch** (đợt 3) | Quy trình thủ công | Tự động hóa chuẩn hóa dữ liệu, giảm đối soát tay |

### 10.3. Lộ trình

Đợt 0 nền tảng và làm sạch dữ liệu → Đợt 1 Thụy Điển (12 tuần) → Đợt 2 Na Uy → Đợt 3 Đan Mạch → mở rộng chức năng giai đoạn 2 (đặt hàng, dự báo, cổng B2B).

### 10.4. Ràng buộc triển khai

- **Mùa xây dựng cao điểm** (giả định xuân đến hè): tránh go-live và đào tạo trong giai đoạn này, đặt khung đóng băng thay đổi.
- **Chất lượng dữ liệu nguồn:** cần bước làm sạch ở Đợt 0.
- **Hiệu năng và độ trễ** khi đồng bộ gần thời gian thực.
- **Chấp nhận của nhân viên:** dùng champion tại từng cửa hàng.

---

## 11. Rủi ro và cách giảm

| Rủi ro | Giảm thiểu |
|---|---|
| Tranh chấp quyền sở hữu dữ liệu giữa các nước | Chủ sở hữu dữ liệu theo miền, hội đồng quản trị dữ liệu |
| Dự án phình thành dự án thay ERP (scope creep) | Danh sách "ngoài phạm vi" được ký duyệt, các cổng go/no-go |
| Nhân viên không dùng | Thiết kế cùng nhân viên cửa hàng, champion, theo dõi tỷ lệ sử dụng |
| Phụ thuộc nhà cung cấp | API mở, kiến trúc tách lớp |
| Dữ liệu nguồn quá kém | Đợt làm sạch dữ liệu; điểm tin cậy **phơi bày** vấn đề thay vì che giấu |
| Thiếu dữ liệu lịch sử để huấn luyện ML | Khởi động bằng quy tắc, chuyển ML khi đủ dữ liệu |

---

## 12. Các giả định chính

1. Mỗi nước có ít nhất một ERP và hệ thống kho với API hoặc cơ chế xuất dữ liệu.
2. Quy mô khoảng 300 cửa hàng (đề chỉ nói "hàng trăm").
3. Thụy Điển có điểm đau về giao hàng đúng như ví dụ trong đề.
4. Công ty chấp nhận hạ tầng cloud đặt tại EU.
5. Các con số baseline, KPI và ROI chỉ mang tính minh họa, được xác nhận ở tuần 1.
6. Mùa cao điểm ngành xây dựng là xuân đến hè.

---

## 13. Câu hỏi giám khảo có thể hỏi và hướng trả lời

| Câu hỏi | Hướng trả lời |
|---|---|
| Vì sao chọn phân mảnh mà không chọn vấn đề thiết thực hơn như giao hàng? | Phân mảnh là nguyên nhân gốc và chung cho cả ba nước; giao hàng và thủ công cần dữ liệu đáng tin trước. Đã có ma trận chấm điểm và thừa nhận đánh đổi. |
| Không phải đây là dự án hợp nhất ERP kéo dài nhiều năm? | Không. Hub chạy trên hệ thống cũ, chỉ đọc, phạm vi 12 tuần, có tiêu chí dừng. |
| Lấy dữ liệu đâu để huấn luyện mô hình tin cậy? | Khởi động bằng quy tắc, từ tuần 7 dùng lịch sử điều chỉnh tồn kho và kiểm kho từ ERP; vòng phản hồi của nhân viên bổ sung nhãn. |
| Vì sao không dùng AI tạo sinh cho mọi thứ? | Mỗi chức năng dùng đúng kỹ thuật: tính ngày giao cần quy tắc và ML, còn ánh xạ thuộc tính hay tìm kiếm ngôn ngữ tự nhiên mới hợp AI tạo sinh. |
| Làm sao biết MVP thành công? | KPI baseline đo ở tuần 1, cửa hàng đối chứng, ba tiêu chí go/no-go rõ ràng. |
| Điều gì khác nhau giữa ba nước? | Lõi dùng chung; adapter, chuẩn dữ liệu, quy tắc giao hàng, đào tạo là phần riêng; mỗi nước có "chiến thắng đầu tiên" khác nhau. |
| Chi phí và hoàn vốn? | Nêu ước lượng đội khoảng 8 người trong 12 tuần, so với lợi ích minh họa; xác nhận bằng số liệu pilot. |

---

## 14. Phụ lục: cấu trúc 10 slide

| # | Slide | Vai trò theo đề |
|---|---|---|
| 1 | Tóm tắt điều hành | Tổng quan |
| 2 | Vấn đề và nguyên nhân gốc | Identify |
| 3 | Vì sao ưu tiên vấn đề này | Prioritise |
| 4 | Kiến trúc giải pháp | Solve |
| 5 | Tính năng cốt lõi: lời hứa có độ tin cậy | Solve |
| 6 | AI dùng ở đâu, không dùng ở đâu | AI |
| 7 | Phạm vi MVP, lộ trình, tiêu chí dừng | Solve |
| 8 | Tác động kinh doanh | Business impact |
| 9 | Nhân rộng | Scale |
| 10 | Rủi ro, giả định, đề nghị quyết định | Kết |

**Đối chiếu tiêu chí chấm điểm:**

| Tiêu chí | Slide đáp ứng |
|---|---|
| Problem Understanding | 2 |
| Prioritisation & Critical Thinking | 3, 6, 10 |
| Business Impact | 8 |
| Feasible solution | 4, 7, 9 |
| Structured thinking & Innovation | 5, 6 và toàn bộ mạch kể |