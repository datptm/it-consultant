# Promise Engine PoC

PoC dòng lệnh và giao diện Streamlit cho ba thành phần trong [`docs/resources/methodology.md`](docs/resources/methodology.md): độ tin cậy tồn kho, khả năng lấy đủ hàng và khả năng giao đúng hạn. Dữ liệu trong `data/sample.json` hoàn toàn giả lập.

Chi tiết dữ liệu, cách tạo feature/nhãn và ba mô hình huấn luyện: [`docs/data-features-models.md`](docs/data-features-models.md).

## Cài và chạy

Yêu cầu Python 3.13. Tại thư mục gốc của dự án:

```powershell
python -m pip install -e . -r requirements.txt
python -m promise_poc demo --mode rules
python -m promise_poc demo --mode ml
python -m promise_poc evaluate --product-id SKU-001 --quantity 2 --destination-id STORE-001 --date 2026-11-10 --mode ml
python -m streamlit run ui/app.py
python -m unittest discover -s tests -v
python -m ruff check src ui tests
python -m ruff format --check ui
```

`demo` trả về ba kết quả JSON. `evaluate` nhận ngày giao dạng `YYYY-MM-DD`; có thể thêm `--at 2026-11-05T10:30:00Z`. Nếu bỏ `--at`, CLI dùng mốc `reference_time` trong dữ liệu mẫu, giúp chạy lại cùng một kết quả. PoC chỉ hỗ trợ `STORE_PICKUP` và chọn một nguồn cung; các ngày làm việc là thứ Hai đến thứ Sáu, giờ cutoff theo UTC, không tính ngày lễ.

Chế độ `ml` huấn luyện lại ba mô hình logistic regression trong bộ nhớ mỗi lần gọi CLI. Các nhãn được tạo từ kiểm kê, số lượng lấy hàng và ngày giao thực tế; feature chỉ lấy dữ liệu đã có trước thời điểm yêu cầu. Tập mẫu rất nhỏ, chưa có tập kiểm định hay hiệu chỉnh xác suất. Xác suất của cả hai chế độ chỉ minh họa luồng quyết định và **không dùng để cam kết giao hàng thực tế**. Quy tắc kiểm tra dữ liệu nguồn quá 24 giờ, ATP và ngày giao vẫn áp dụng ở cả hai chế độ.

## Giao diện web

Chạy `python -m streamlit run ui/app.py` từ thư mục gốc rồi mở địa chỉ mà Streamlit hiển thị. Giao diện tiếng Anh có ba tab:

- **Sample scenarios:** xem ba yêu cầu mẫu ở chế độ Rules hoặc ML.
- **Evaluate a request:** chọn sản phẩm, số lượng, cửa hàng nhận, ngày mong muốn và chế độ đánh giá. Mốc yêu cầu luôn là `reference_time` trong dữ liệu mẫu để kết quả lặp lại được.
- **ML training:** xem số hàng và nhãn của ba tập huấn luyện, chỉnh `C` và `max_iter` dùng chung, rồi bấm **Train and save**. Thanh tiến độ cập nhật sau mỗi mô hình.

Giao diện web chỉ dùng mô hình ML đã huấn luyện và lưu bằng `skops` ở `ui/.local/latest.skops` (thư mục này không đưa vào version control). Nếu chưa có mô hình, tệp hỏng, dữ liệu mẫu thay đổi hoặc phiên bản scikit-learn không tương thích, hãy huấn luyện lại ở tab **ML training**. Đổi tham số trên form không làm đổi kết quả cho đến khi huấn luyện và lưu thành công. Khác với giao diện web, CLI `--mode ml` vẫn tự huấn luyện lại mỗi lần chạy. Không tải dữ liệu lên hoặc ghi vào hệ thống vận hành.
