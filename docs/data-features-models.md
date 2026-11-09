# Dữ liệu, feature và mô hình huấn luyện của Promise Engine PoC

Tài liệu này mô tả **phần cốt lõi đang chạy** của PoC: dữ liệu đầu vào, cách biến dữ liệu thành feature và nhãn, ba mô hình huấn luyện, rồi cách dùng đầu ra để đánh giá một yêu cầu. Nguồn sự thật của PoC là [`data/sample.json`](../data/sample.json), [`features.py`](../src/promise_poc/features.py), [`ml.py`](../src/promise_poc/ml.py), [`rules.py`](../src/promise_poc/rules.py) và [`engine.py`](../src/promise_poc/engine.py). Các ý tưởng đầy đủ hơn của bài toán nằm trong [`docs/resources/methodology.md`](resources/methodology.md); những trường hoặc kỹ thuật chỉ xuất hiện ở tài liệu đó **chưa mặc nhiên được hiện thực** ở đây.

## 1. Ba câu hỏi được mô hình hóa

Với một yêu cầu mua sản phẩm `p`, số lượng `q`, điểm nhận `d` và ngày mong muốn `D`, engine xét từng nguồn cung `s` và tách ba đại lượng:

| Đại lượng | Câu hỏi | Nhãn huấn luyện |
|---|---|---|
| `inventory_confidence` | Số tồn kho trong snapshot của `(p, s)` có gần số kiểm kê thực tế không? | Sai lệch không quá **1 đơn vị**. |
| `fulfillment` | Tại `s`, đơn có được lấy đủ `q` đơn vị không? | `picked_quantity >= quantity`. |
| `on_time` | Với tuyến từ `s` tới `d` và ngày `D`, hàng có đến không muộn hơn `D` không? | Ngày của `delivered_at <= D`, chỉ xét đơn đã lấy đủ hàng. |

`inventory_confidence` là độ tin cậy của **con số tồn kho**, không đồng nghĩa với xác suất lấy đủ một đơn. Tồn kho được dùng thêm để tạo vùng đệm và ATP; `fulfillment` trả lời một câu hỏi khác, có xét cả số lượng cần lấy. Engine tính `promise_success = fulfillment × on_time` trên các nguồn còn khả thi. Trong bộ dữ liệu huấn luyện hiện tại, mô hình giao hàng chỉ thấy các đơn đã lấy đủ hàng, nên kết quả của nó gần với `P(đúng hạn | đã lấy đủ hàng, feature giao hàng)` hơn là xác suất đúng hạn vô điều kiện. Tích hai đầu ra là một **ước lượng minh họa**, chưa được kiểm định hay hiệu chỉnh như xác suất thành công thực tế.

Hai chế độ dùng cùng dữ liệu và ràng buộc cứng:

- `rules`: các điểm và xác suất là hằng số/quy tắc dễ kiểm tra, không học từ nhãn.
- `ml`: huấn luyện ba bộ phân loại riêng từ nhãn lịch sử; vẫn áp dụng luật kiểm tra dữ liệu, ATP, tuyến và ngày giao.

## 2. Dữ liệu mẫu và ý nghĩa từng nhóm

Tất cả bản ghi đều là **dữ liệu giả lập**. Thời gian dùng chuỗi ISO 8601 UTC có hậu tố `Z`; số lượng là đơn vị nguyên của SKU. `reference_time = 2026-11-05T10:30:00Z` giữ cho lệnh CLI chạy lại được cùng một tình huống. Bộ mẫu có 2 sản phẩm, 3 địa điểm, 4 tuyến, 11 snapshot (8 lịch sử và 3 hiện hành), 8 sự kiện, 8 lần kiểm kê, 8 đơn lịch sử và 3 yêu cầu demo.

### 2.1. Danh mục và tuyến

| Nhóm | Trường | Vai trò trong PoC |
|---|---|---|
| `products` | `product_id`, `name`, `category` | Xác nhận SKU tồn tại. `name` và `category` chỉ để mô tả; chưa đi vào feature. |
| `locations` | `location_id`, `location_type`, `country` | Xác nhận điểm nhận, ghép nguồn với snapshot; `location_type` (`STORE`/`DC`) là feature. `country` chưa dùng để dự báo. |
| `lanes` | `lane_id`, `source_id`, `destination_id`, `delivery_type` | Xác định một nguồn có thể phục vụ một điểm nhận theo hình thức nào. PoC chỉ dùng `STORE_PICKUP`. |
| `lanes` | `cutoff_hour_utc`, `processing_days`, `transit_days` | Tính ngày giao sớm nhất theo giờ cutoff và số ngày làm việc. `cutoff_hour_utc` là giờ nguyên theo UTC. |

Hai địa điểm có thể cùng giữ một SKU, nhưng chỉ được xét nếu có cả tuyến phù hợp và snapshot của SKU tại nguồn đó. Mỗi phương án chỉ lấy hàng từ **một** nguồn; `lane_id` của đơn lịch sử nối đơn với tuyến dùng khi tạo feature giao hàng.

### 2.2. Trạng thái tồn kho và các tín hiệu chất lượng

| Nhóm | Trường | Ý nghĩa và cách dùng |
|---|---|---|
| `snapshots` | `snapshot_id`, `product_id`, `location_id` | Định danh một ảnh chụp tồn kho cho một SKU tại một nguồn. `snapshot_id` cũng nối kiểm kê/đơn lịch sử tới ảnh chụp tương ứng. |
| `snapshots` | `observed_at` | Mốc để tạo feature cho bài toán tồn kho lịch sử. Khi suy luận, chỉ chọn snapshot có `observed_at <= requested_at`. |
| `snapshots` | `source_updated_at` | Lần cập nhật ở hệ thống nguồn; dùng tính tuổi dữ liệu `stock_age_hours`. |
| `snapshots` | `received_at` | Lúc PoC nhận bản ghi; phải không muộn hơn thời điểm đang đánh giá. Khác với `source_updated_at`: dữ liệu có thể mới ở nguồn nhưng đến PoC muộn. |
| `snapshots` | `last_count_at` | Thời điểm kiểm kê gần nhất do snapshot khai báo; dùng tính `days_since_last_count` và làm mốc dưới khi tìm sai lệch kiểm kê lịch sử. |
| `snapshots` | `on_hand`, `reserved`, `allocated` | Số ghi nhận, số giữ chỗ và số đã phân bổ. Đầu vào của ATP. |
| `snapshots` | `pending_transactions` | Số giao dịch chưa đồng bộ; là feature tồn kho/fulfillment và điều kiện trừ điểm trong rules. |
| `snapshots` | `inbound` | Hàng đang về, có trong mẫu để thấy dữ liệu này **không được cộng vào ATP**. |
| `events` | `event_id`, `product_id`, `location_id`, `event_type`, `quantity_delta` | Các biến động tồn kho. Hiện chỉ sự kiện `SALE` được dùng để tính tốc độ bán; `quantity_delta` âm khi bán. |
| `events` | `event_time`, `received_at` | Thời điểm nghiệp vụ và thời điểm PoC nhận sự kiện. Cả hai điều kiện thời gian đều được kiểm tra khi tạo feature. |
| `counts` | `snapshot_id`, `product_id`, `location_id`, `counted_at` | Kiểm kê sau snapshot để tạo nhãn; kiểm kê đã xảy ra trước mốc đánh giá mới có thể dùng làm tín hiệu lịch sử. |
| `counts` | `system_on_hand`, `actual_on_hand` | Số hệ thống và số thực đếm. Feature sai lệch lịch sử dùng cả hai trường; **nhãn inventory** so `snapshot.on_hand` với `actual_on_hand`, không dùng `count.system_on_hand`. |

Không cộng các `events` thêm lần nữa vào `on_hand`: snapshot là số tồn kho hệ thống tại mốc của nó, còn sự kiện trong PoC chỉ cung cấp tín hiệu tốc độ bán. Làm cả hai sẽ dễ đếm trùng biến động.

### 2.3. Đơn lịch sử và yêu cầu cần đánh giá

| Nhóm | Trường | Ý nghĩa và cách dùng |
|---|---|---|
| `orders` | `order_id`, `snapshot_id`, `lane_id` | Nối kết quả đơn hàng với ảnh chụp và tuyến đã biết lúc ra quyết định. |
| `orders` | `requested_at`, `quantity`, `requested_delivery_date` | Thời điểm, lượng và ngày mong muốn; là feature hoặc đầu vào để tính feature. |
| `orders` | `picked_quantity`, `picked_at` | Kết quả lấy hàng, **chỉ dùng làm nhãn** fulfillment và để chọn đơn hợp lệ cho mô hình giao hàng. |
| `orders` | `delivered_at` | Kết quả giao hàng, **chỉ dùng làm nhãn** on-time. |
| `demo_requests` | `request_id`, `product_id`, `quantity`, `destination_id`, `delivery_type`, `requested_at`, `requested_delivery_date` | Yêu cầu cần suy luận. Lệnh `evaluate` cho nhập các giá trị chính; nếu không truyền `--at` thì dùng `reference_time`. |

Các đơn lịch sử trong mẫu đều gắn với `SKU-001` tại `DC-001`; các yêu cầu demo có cả `SKU-002` ở cửa hàng. Vì vậy mô hình ML **chưa có bằng chứng học được cách khái quát** sang SKU/địa điểm khác. `products.category` và định danh SKU không phải feature của ba mô hình hiện tại.

## 3. Quy tắc thời gian: dữ liệu nào được phép trở thành feature?

Gọi `t` là thời điểm đánh giá. Một feature phải được tính từ dữ liệu đã tồn tại và đã đến PoC không muộn hơn `t`; nhãn có thể xuất hiện sau `t`. Đây là ranh giới chính để tránh *data leakage*.

1. **Chọn snapshot khi suy luận:** với mỗi `(product_id, source_id)`, chọn snapshot mới nhất theo `observed_at` trong các bản có `observed_at <= t` và `received_at <= t`. Không có snapshot phù hợp thì bỏ nguồn.
2. **Kiểm tra bản thân snapshot:** `source_updated_at`, `last_count_at` và `received_at` đều phải `<= t`; nếu không, tạo feature báo lỗi. Engine còn bỏ nguồn nếu `stock_age_hours > 24`.
3. **Sự kiện bán:** chỉ cộng `SALE` của đúng sản phẩm/nguồn, có `event_time` nằm trong cửa sổ 7 ngày ngay trước `t` và `received_at <= t`. Một giao dịch xảy ra trước `t` nhưng đến sau `t` không được dùng để giải thích quyết định quá khứ.
4. **Kiểm kê lịch sử:** chỉ xét kiểm kê của đúng sản phẩm/nguồn với `last_count_at <= counted_at <= t`; chọn bản có `counted_at` mới nhất. Không có bản hợp lệ thì feature sai lệch lịch sử là `0` trong PoC. Giá trị `0` này có nghĩa **không có tín hiệu sai lệch đã biết**, không chứng minh dữ liệu thật sự chính xác. Mẫu không có `received_at` cho kiểm kê, nên mã đang xem `counted_at` là thời điểm kết quả đã biết; dữ liệu thật cần tách hai mốc này.
5. **Huấn luyện inventory:** feature lấy tại `snapshot.observed_at`; kiểm kê được nối bằng `snapshot_id` và bắt buộc `counted_at > observed_at`, rồi mới tạo nhãn.
6. **Huấn luyện fulfillment/delivery:** feature lấy tại `order.requested_at`; snapshot liên quan phải có `received_at <= requested_at`. `picked_at` phải sau `requested_at`; `delivered_at` phải sau `requested_at` đối với hàng đưa vào mô hình giao hàng.

Các kiểm tra trên bảo vệ feature khỏi một số trường hợp dùng tương lai. Đây là bộ dữ liệu minh họa, chưa có hệ thống lưu snapshot bất biến hay đối soát biến động giữa lúc snapshot và lúc kiểm kê. Vì thế một nhãn tồn kho dựa trên kiểm kê muộn vẫn có thể bị ảnh hưởng bởi giao dịch phát sinh trong khoảng giữa nếu áp dụng nguyên xi cho dữ liệu thật.

## 4. Feature của từng mô hình

### 4.1. Inventory Confidence

Một hàng feature tương ứng với **một snapshot của một SKU tại một nguồn, nhìn tại thời điểm `t`**.

| Feature | Kiểu/đơn vị | Công thức hoặc nguồn | Ý nghĩa |
|---|---|---|---|
| `stock_age_hours` | Số thực, giờ | `(t - source_updated_at) / 1 giờ` | Dữ liệu nguồn cũ bao lâu. |
| `days_since_last_count` | Số thực, ngày | `(t - last_count_at) / 1 ngày` | Đã lâu chưa kiểm kê; có thể là số lẻ. |
| `sales_velocity_7d` | Số thực, đơn vị/ngày | Tổng `abs(quantity_delta)` của các `SALE` hợp lệ trong 7 ngày, chia `7` | Tốc độ bán quan sát được trong một cửa sổ cố định. |
| `historical_discrepancy` | Số thực, tỷ lệ | Với kiểm kê hợp lệ mới nhất: `abs(system_on_hand - actual_on_hand) / max(actual_on_hand, 1)`; thiếu bản ghi thì `0` | Độ lệch kiểm kê đã biết. |
| `pending_transactions` | Số nguyên | `snapshot.pending_transactions` | Tín hiệu giao dịch chưa đồng bộ. |
| `on_hand` | Số nguyên, đơn vị | `snapshot.on_hand` | Quy mô số tồn kho hệ thống. |
| `location_type` | Chuỗi phân loại | `STORE` hoặc `DC` từ `locations` | Loại nguồn cung. |

`stock_age_hours` và `days_since_last_count` được tính từ thời điểm đang đánh giá, không từ đồng hồ lúc chạy lệnh CLI. `sales_velocity_7d` là tổng số bán/7 ngay cả khi trong 7 ngày chỉ có một sự kiện. Chưa có feature 30 ngày, tỷ lệ điều chỉnh tồn kho, mức độ tin cậy của inbound hoặc mã nhóm sản phẩm dù tài liệu phương pháp có đề xuất.

### 4.2. Fulfillment

Một hàng feature tương ứng với **một đơn tại một nguồn ở thời điểm yêu cầu**.

| Feature | Kiểu/đơn vị | Công thức hoặc nguồn | Ý nghĩa |
|---|---|---|---|
| `requested_quantity` | Số nguyên, đơn vị | `order.quantity` hoặc lượng yêu cầu mới | Lượng cần lấy đủ. |
| `raw_available` | Số nguyên, đơn vị | `on_hand - reserved - allocated` | Số có thể xét trước khi áp dụng safety buffer. **Không phải ATP.** |
| `pending_transactions` | Số nguyên | Snapshot đang xét | Rủi ro dữ liệu chưa đồng bộ. |
| `stock_age_hours` | Số thực, giờ | Cùng phép tính với Inventory Confidence | Độ mới của dữ liệu nguồn. |
| `location_type` | Chuỗi phân loại | Loại nguồn từ `locations` | Phân biệt cửa hàng và DC nếu có dữ liệu học. |

Mô hình fulfillment **không** nhận trực tiếp `inventory_confidence` hay `effective_atp` làm feature. Cách này tránh việc tạo feature huấn luyện bằng dự đoán *in-sample* của mô hình inventory rồi dùng một định nghĩa khác lúc suy luận. Engine vẫn áp dụng ATP như ràng buộc cứng trước khi tin đầu ra fulfillment.

### 4.3. On-time Delivery

Một hàng feature tương ứng với **một tuyến, một lượng hàng và một ngày được đề nghị tại thời điểm yêu cầu**.

| Feature | Kiểu/đơn vị | Công thức hoặc nguồn | Ý nghĩa |
|---|---|---|---|
| `quantity` | Số nguyên, đơn vị | Lượng yêu cầu | Quy mô đơn. |
| `lead_days` | Số nguyên, ngày lịch | `requested_delivery_date - date(requested_at)` | Số ngày khách cho phép từ lúc đặt tới ngày mong muốn. |
| `slack_days` | Số nguyên, ngày lịch | `requested_delivery_date - earliest_delivery_date` | Dư địa sau ngày sớm nhất do quy tắc tuyến tính được. |
| `delivery_type` | Chuỗi phân loại | `lane.delivery_type` | Hình thức nhận; mẫu hiện chỉ có `STORE_PICKUP`. |
| `source_type` | Chuỗi phân loại | Loại địa điểm xuất hàng | `STORE` hoặc `DC`. |

Ngày sớm nhất được tính **trước** khi dự đoán: nếu đặt vào cuối tuần hoặc từ giờ cutoff trở đi thì bắt đầu ngày làm việc kế tiếp; sau đó cộng `processing_days + transit_days`, mỗi bước bỏ qua thứ Bảy và Chủ nhật. PoC dùng UTC và không có lịch ngày lễ. `lead_days` và `slack_days` là chênh lệch **ngày lịch**, còn processing/transit là **ngày làm việc**. Chưa dùng carrier, khoảng cách, tải kho, thời tiết hay lịch sử trễ của tuyến.

## 5. Cách tạo nhãn và tập huấn luyện

| Mô hình | Một hàng bắt đầu từ | Nhãn `1` | Nhãn `0` | Số hàng mẫu |
|---|---|---|---|---|
| Inventory | Một `count` nối tới snapshot bằng `snapshot_id` | `abs(snapshot.on_hand - count.actual_on_hand) <= 1` | Sai lệch lớn hơn 1 | 8: **4/4** |
| Fulfillment | Một `order` nối tới snapshot bằng `snapshot_id` | `picked_quantity >= quantity` | Lấy thiếu | 8: **6/2** |
| Delivery | Một `order` đã lấy đủ, nối tới snapshot và lane | `date(delivered_at) <= requested_delivery_date` | Giao sau ngày mong muốn | 6: **3/3** |

Tỷ lệ `4/4`, `6/2`, `3/3` lần lượt là số nhãn `1`/`0`, **không phải** tỷ lệ thực tế của nghiệp vụ. Hai đơn lấy thiếu bị loại khỏi tập Delivery; chúng vẫn có nhãn fulfillment `0`. PoC so **ngày** giao, không so giờ trong ngày. Tolerance tồn kho là hằng số **1 đơn vị**, chưa cấu hình theo loại hàng hoặc lượng tồn. Mã không phân biệt đơn hủy do khách, lỗi vận tải, đổi ngày hứa hay kiểm kê chưa xác minh vì dữ liệu mẫu chưa có các trạng thái đó.

Để thấy sự khác biệt giữa feature và nhãn: với `H1`, snapshot ghi `on_hand = 20` lúc 10:00, kiểm kê lúc 12:00 thấy `actual_on_hand = 20`, nên nhãn inventory là `1`. Feature của `H1` được dựng ở **10:00**; giá trị thực đếm lúc 12:00 không có mặt trong từ điển feature. Với `H2`, snapshot ghi `20` và sau đó đếm được `13`, sai lệch `7 > 1`, nên nhãn là `0`.

## 6. Huấn luyện ML hiện tại

[`train_models`](../src/promise_poc/ml.py) thực hiện cùng một quy trình cho `inventory`, `fulfillment`, `delivery`:

1. Gọi `build_training_rows(data, kind)` để nhận danh sách `(feature_dict, nhãn 0/1)` theo định nghĩa ở trên.
2. Từ chối huấn luyện nếu tập của mô hình không có đủ **cả hai lớp** nhãn.
3. Tạo pipeline `DictVectorizer()` → `LogisticRegression(C=1, max_iter=1000)` theo mặc định của CLI; giao diện web có thể đổi `C` và `max_iter`. `DictVectorizer` giữ feature số và mã hóa các chuỗi phân loại thành cột chỉ báo; Logistic Regression học trọng số cho xác suất lớp `1`.
4. `fit` trên **toàn bộ** các hàng của mô hình đó. Khi suy luận, gọi `predict_proba` và lấy đúng cột có nhãn lớp `1`.

Mỗi lần dùng CLI `--mode ml`, cả ba pipeline được huấn luyện mới **trong bộ nhớ** từ `data/sample.json`; CLI không dùng file mô hình, registry hoặc bước học tăng dần. Mặc định `C=1`, `max_iter=1000`; các tham số khác dùng mặc định của phiên bản scikit-learn đã cài. PoC không có chuẩn hóa thang số, xử lý giá trị thiếu, cân bằng lớp, chọn siêu tham số, chia tập theo thời gian, validation/test độc lập hay hiệu chỉnh xác suất. Vì vậy các con số như `0.82` hoặc `0.99` từ `predict_proba` **không thể được diễn giải** là tần suất thành công đã được chứng minh.

Giao diện Streamlit ở `ui/app.py` tách huấn luyện khỏi đánh giá ML: tab **ML training** cho chỉnh `C` (0,01–100) và `max_iter` (100–5000) dùng chung cho cả ba pipeline, huấn luyện trên đúng bộ mẫu này rồi lưu một bundle `skops` ở `ui/.local/latest.skops`. Tab đánh giá chỉ tải bundle đã lưu, không tự huấn luyện; nếu chưa có hoặc bundle không tương thích với phiên bản scikit-learn hay nội dung dữ liệu mẫu, người dùng phải huấn luyện lại. CLI vẫn giữ mặc định `C=1`, `max_iter=1000` và tự huấn luyện mỗi lần gọi. Bundle chỉ phục vụ demo cục bộ, không phải model registry hoặc bằng chứng chất lượng mô hình.

Trong tập huấn luyện mẫu, các đơn và kiểm kê đều thuộc DC/SKU đầu tiên; khi áp dụng mô hình cho cửa hàng hoặc SKU khác, bộ mã hóa có thể gặp giá trị phân loại chưa thấy và Logistic Regression phải ngoại suy. Không dùng kết quả này để đánh giá hiệu quả mô hình hay đưa ra cam kết thương mại.

## 7. Từ feature tới quyết định: rules và ML khác nhau ở đâu?

### 7.1. Điểm rule và ATP chung

Chế độ rules bắt đầu `inventory_confidence = 1,00`, rồi trừ các khoản sau. Điều kiện `>` là **nghiêm ngặt**, bằng ngưỡng thì chưa bị trừ.

| Điều kiện | Điểm trừ |
|---|---:|
| `days_since_last_count > 30` | 0,15 |
| `pending_transactions > 0` | 0,20 |
| `historical_discrepancy > 0,10` | 0,20 |
| `sales_velocity_7d > 5` đơn vị/ngày | 0,10 |
| `stock_age_hours > 24` | 0,15 |

Điểm cuối được chặn dưới ở `0`. Riêng `stock_age_hours > 24` còn là **điều kiện loại nguồn** trong engine, kể cả khi điểm sau trừ vẫn nằm ở dải `HIGH`. Hai chế độ đều dùng xác suất inventory của mình để tính:

```text
safety_buffer = ceil(on_hand × (1 − inventory_confidence) × 0,5)
ATP = max(0, on_hand − reserved − allocated − safety_buffer)
```

Hàng `inbound` không tham gia công thức. `ceil` làm tròn vùng đệm lên số nguyên, khiến ATP thận trọng hơn khi điểm tin cậy thấp. Sau đó engine loại nguồn nếu `ATP < requested_quantity` hoặc ngày yêu cầu sớm hơn ngày tuyến có thể giao. Mô hình ML **không được phép vượt qua** các điều kiện loại này.

### 7.2. Ba đầu ra ở hai chế độ

| Đầu ra | `rules` | `ml` |
|---|---|---|
| Inventory | Điểm trừ ở bảng trên. | Xác suất lớp `1` của mô hình Inventory từ 7 feature ở mục 4.1. |
| Fulfillment | Nếu ATP thiếu: nguồn bị loại. Nếu đủ và dư ít nhất 2 đơn vị: `0,99`; nếu đủ nhưng dư dưới 2: `0,90`. | Xác suất lớp `1` của mô hình Fulfillment từ 5 feature ở mục 4.2, sau khi qua cổng ATP. |
| On-time | Nếu ngày mong muốn sau ngày sớm nhất: `0,99`; nếu đúng ngày sớm nhất: `0,96`. Ngày quá sớm bị loại. | Xác suất lớp `1` của mô hình Delivery từ 5 feature ở mục 4.3, sau khi qua cổng ngày giao. |

Những giá trị cố định `0,90`, `0,96` và `0,99` của rules là **tham số minh họa**, chưa được ước lượng từ tỷ lệ thành công thực tế. Engine nhân hai đầu ra Fulfillment và On-time **trước khi làm tròn**; JSON chỉ làm tròn mỗi xác suất đến bốn chữ số thập phân.

### 7.3. Ngưỡng và chọn nguồn

| Điều kiện sau khi nguồn qua ATP/ngày giao | Quyết định |
|---|---|
| `inventory_confidence < 0,65` **hoặc** `promise_success < 0,85` | `REJECT` |
| `inventory_confidence >= 0,85` **và** `promise_success >= 0,95` | `PROMISE` |
| Các trường hợp còn lại | `VERIFY` |

Các dải inventory dùng trong `reasons` là `HIGH` từ `0,85`, `MEDIUM` từ `0,65` đến dưới `0,85`, `LOW` dưới `0,65`. Khi có nhiều nguồn, engine ưu tiên quyết định `PROMISE` hơn `VERIFY` hơn `REJECT`; trong cùng mức ưu tiên, so xác suất thành công, confidence, ngày giao sớm hơn rồi `source_id` theo thứ tự từ điển giảm dần. Vì vậy nguồn được chọn không nhất thiết chỉ là nguồn có xác suất lớn nhất nếu mức quyết định khác nhau. Không có nguồn khả thi thì kết quả là `REJECT` với `NO_FEASIBLE_SINGLE_SOURCE`; ngày hứa chỉ xuất hiện khi quyết định là `PROMISE`.

## 8. Một ca tính tay trên dữ liệu mẫu

`REQ-001` yêu cầu **2** `SKU-001` nhận tại `STORE-001`, đặt lúc `2026-11-05T10:30:00Z`, mong muốn ngày `2026-11-10`. Tuyến `DC-S1` cho phép xuất từ `DC-001`, cutoff 16:00 UTC, xử lý 1 ngày làm việc và vận chuyển 1 ngày làm việc.

1. Snapshot `LIVE-DC` lúc 10:00 có `on_hand = 100`, `reserved = 10`, `allocated = 0`, `pending_transactions = 0`, `source_updated_at = 09:00`. Tại 10:30: `stock_age_hours = 1,5`, `days_since_last_count ≈ 1,0208`, `sales_velocity_7d = 0`, `historical_discrepancy = 0` trong cửa sổ đang xét. Không điều kiện trừ điểm nào áp dụng, nên confidence rules là `1,00`.
2. `safety_buffer = ceil(100 × (1 − 1,00) × 0,5) = 0`; `ATP = 100 − 10 − 0 − 0 = 90`, đủ 2 đơn vị. `inbound = 20` trong snapshot không làm ATP tăng.
3. Đặt trước cutoff vào thứ Năm 05/11; cộng 2 ngày làm việc thành thứ Hai **09/11**. Ngày mong muốn 10/11 muộn hơn ngày sớm nhất, nên `on_time` rules là `0,99`. ATP dư ít nhất 2 đơn vị, nên `fulfillment` rules là `0,99`.
4. `promise_success = 0,99 × 0,99 = 0,9801`. Confidence `1,00 >= 0,85` và success `0,9801 >= 0,95`, nên kết quả rules là `PROMISE`, nguồn `DC-001`, ngày hứa `2026-11-10`.

Chế độ ML dùng **cùng snapshot, tuyến, yêu cầu và cổng ATP/ngày giao**, nhưng thay ba con số do rules tạo bằng ba dự đoán từ mô hình. Dữ liệu ít khiến quyết định ML có thể khác rules, kể cả `REJECT` cho ca trên; đây là dấu hiệu giới hạn của bộ mẫu, không phải bằng chứng ML an toàn hơn.

## 9. Cách tái hiện và giới hạn diễn giải

Sau khi cài theo [`README.md`](../README.md), chạy từ thư mục gốc:

```powershell
python -m promise_poc demo --mode rules
python -m promise_poc demo --mode ml
python -m promise_poc evaluate --product-id SKU-001 --quantity 2 --destination-id STORE-001 --date 2026-11-10 --mode ml
```

Các lệnh `demo` trả về ba yêu cầu để thấy nguồn đủ hàng, thiếu hàng và một SKU khác. CLI không ghi phản hồi hay huấn luyện lại sau quyết định; lần chạy ML sau vẫn học từ cùng 8 đơn/kiểm kê mẫu. Muốn đánh giá xác suất một cách nghiêm túc cần dữ liệu lịch sử đủ lớn và đáng tin, chia train/validation/test theo thời gian, kiểm tra sai lệch theo SKU/nguồn/tuyến, và đo calibration như Brier score trên tập chưa dùng để huấn luyện. Những bước đó **chưa nằm trong PoC hiện tại**.
