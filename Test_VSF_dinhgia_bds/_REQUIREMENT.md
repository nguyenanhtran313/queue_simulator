# Requirement — Test_VSF_dinhgia_bds: Định giá Bất động sản tự động (AVM)

> **Lưu ý:** thư mục này không có file đề bài hay presentation.html nào (khác với 2 thư mục `Test_VSF_forecast_demand`/`Test_VSF_driver_allocation`), nên bản Requirement dưới đây hoàn toàn được suy ngược lại từ code `generate_data.py` + `compare_models.py`. Không tìm thấy bằng chứng cho thấy đây cùng case study "Xanh SM" — có vẻ là một bài luyện tập/case study **riêng biệt** dù tên thư mục có tiền tố giống nhau.

## 1. Bối cảnh nghiệp vụ

Xây dựng một mô hình **Định giá Bất động sản tự động (Automated Valuation Model - AVM)** cho căn hộ chung cư, dựa trên dữ liệu giao dịch lịch sử — dạng bài toán thường gặp ở các công ty proptech/sàn bất động sản muốn cho phép người dùng tự ước tính giá nhà online.

**Mục tiêu cụ thể (suy từ code):** So sánh nhiều thuật toán Machine Learning khác nhau để tìm ra model dự đoán giá nhà (`price_vnd`) chính xác nhất, đồng thời đưa ra được các chỉ số "dễ hiểu cho business" (không chỉ số liệu thống kê thuần túy) để thuyết phục các bên liên quan (sales, ban lãnh đạo) về độ tin cậy của model.

## 2. Dữ liệu

`real_estate_valuation_dataset.csv` — 5,000 giao dịch **mô phỏng** (do `generate_data.py` sinh ra, không phải dữ liệu thật), gồm các nhóm biến:

| Nhóm | Cột | Ghi chú |
|---|---|---|
| Đặc điểm cơ bản | `area_sqm`, `bedrooms`, `bathrooms` | Diện tích quyết định số phòng ngủ/tắm theo quy tắc suy ra chứ không random độc lập |
| Dữ liệu không gian | `floor_level`, `total_floors`, `orientation`, `distance_to_center/hospital/school/supermarket_km` | Khoảng cách sinh theo phân phối exponential (đa số gần, ít nhà xa) |
| Dữ liệu phi cấu trúc (đại diện) | `balcony_view_type`, `image_quality_score`, `living_room_image_url`, `balcony_image_url` | ⚠️ Ảnh **không được xử lý thật** (không có computer vision) — chỉ có URL giả và 1 điểm số ảnh (`image_quality_score`) đại diện, và điểm số này **không hề dùng để tính giá** trong `generate_data.py` (xem mục 6) |
| Đặc điểm khác | `building_age_years`, `furniture_status`, `legal_status` | Nội thất, tình trạng pháp lý, tuổi công trình |
| Biến động thị trường theo thời gian | `market_sentiment_index`, `interest_rate_pct`, `transaction_date` | Mô phỏng dạng sóng sin theo thời gian (thị trường lên xuống theo chu kỳ), 2 năm giao dịch gần nhất |
| **Biến mục tiêu** | `price_vnd` | Tính từ đơn giá/m² theo khoảng cách tới trung tâm, nhân với hàng loạt hệ số điều chỉnh (hướng, tầng, view, nội thất, pháp lý, tuổi nhà, tâm lý thị trường) + nhiễu ngẫu nhiên |

## 3. Yêu cầu từng bước

### `generate_data.py` — Sinh dữ liệu mô phỏng
- Sinh 5,000 bản ghi giao dịch bất động sản với đầy đủ các nhóm biến ở mục 2.
- Giá (`price_vnd`) phải được tính theo công thức tổ hợp nhiều hệ số thực tế (không random thuần túy), để dữ liệu mô phỏng đúng logic thị trường thật: gần trung tâm đắt hơn, hướng Đông Nam/Nam đắt hơn Tây, view Hồ đắt hơn view bị che khuất, sổ đỏ đắt hơn giấy tờ chưa hoàn thiện, nhà cũ giảm giá theo tuổi, thị trường đang "nóng" thì giá nhích lên.

### `compare_models.py` — So sánh mô hình dự đoán giá
- Tiền xử lý: tách năm/tháng từ `transaction_date`, loại bỏ các cột không mang tín hiệu dự đoán (`property_id`, 2 URL ảnh, `transaction_date` gốc), chuẩn hóa biến số (`StandardScaler`) + one-hot encode biến phân loại.
- Chia tập train/test 80/20.
- Huấn luyện và so sánh **5 thuật toán regression**: Linear Regression, Random Forest, Gradient Boosting, XGBoost, LightGBM.
- Đánh giá bằng MAE, RMSE, R² — và tự tạo thêm 2 chỉ số "độ chính xác kinh doanh" dễ hiểu hơn: % số căn được đoán lệch giá không quá 5%, và không quá 10% so với giá thật.
- In bảng so sánh, chọn ra model tốt nhất theo R² Score.

## 4. Kết quả đã đạt được (ghi nhận sẵn trong comment cuối `compare_models.py`)

- **LightGBM Regressor** là model tốt nhất: R² = 97.3%, MAE ≈ 149 triệu VND, thời gian train chỉ 0.23s.
- Diễn giải kinh doanh có sẵn: nhà 4 tỷ thì AI đưa ra khoảng giá 3.85–4.15 tỷ; tốc độ nhanh phù hợp phục vụ định giá online cho nhiều user cùng lúc.

## 5. Lưu ý kỹ thuật quan trọng (phát hiện khi review code)

- **`image_quality_score` không hề được dùng để tính `price_vnd`** trong `generate_data.py` (không nằm trong bất kỳ multiplier nào) — nghĩa là biến "chất lượng ảnh" chỉ tồn tại như một cột dữ liệu, chưa thực sự ảnh hưởng tới giá mô phỏng lẫn model dự đoán. Nếu đề bài gốc yêu cầu chứng minh giá trị của dữ liệu ảnh/phi cấu trúc, phần này **chưa được hiện thực đầy đủ**.
- `xgboost`/`lightgbm` là optional (`try/except ImportError`) trong `compare_models.py` — nếu máy không có 2 package này, script vẫn chạy được nhưng chỉ so sánh 3 model (Linear/RandomForest/GradientBoosting), sẽ không tìm ra được kết quả "LightGBM tốt nhất" đã ghi trong comment.
- Không có bước lưu model (`.pkl`) như ở `Basic ML/` hay `Test_VSF_forecast_demand/` — script chỉ in kết quả so sánh ra console, không có model production nào được persist để tái sử dụng.

## 6. Cần xác nhận thêm

- Đây là bài tự luyện tập hay case study tuyển dụng của một công ty proptech cụ thể? Không có presentation.html hay tài liệu nào nêu rõ tên công ty/bối cảnh thật (khác với 2 thư mục VSF kia có lộ tên "Xanh SM").
- Đề bài gốc có yêu cầu xử lý thật dữ liệu ảnh (computer vision) không, hay việc dùng `image_quality_score` như một con số đại diện đã là đúng phạm vi được giao?
- Có cần bổ sung bước lưu model tốt nhất ra `.pkl` để dùng cho một app định giá thực tế (tương tự cách `Basic ML/04_XGBoost_Production.py` làm) không?
