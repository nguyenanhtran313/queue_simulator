# Requirement — Test_VSF_forecast_demand: Dự báo Nhu cầu Đặt xe (Demand Forecasting)

> **Lưu ý:** thư mục này không có file đề bài riêng, nhưng may mắn `Vinsmart_Presentation.html` (báo cáo tự sinh) có ghi khá rõ bối cảnh + kết quả. Bản Requirement dưới đây tổng hợp lại từ presentation đó + đọc code `step1_2_pipeline.py` / `generate_eda.py`.

## 1. Bối cảnh

- `Vinsmart_Presentation.html` ghi rõ đây là bài cho **"Tuyển dụng Data Team - Vinsmart Future"** — có vẻ là case study/take-home test tuyển dụng, không phải app nội bộ tự phát triển.
- Thư mục anh em **`Test_VSF_driver_allocation/`** là bản mở rộng đầy đủ hơn của **cùng một case study**: `presentation.html` ở đó có tiêu đề **"Xanh SM - Smart Dispatching & Demand Forecasting"** (Xanh SM là dịch vụ taxi điện thuộc GSM/Vingroup), chia làm 4 Phase: (1) Spatial Indexing & Real-time Heatmap, (2) Demand Forecasting, (3) Smart Dispatching & Behavior Analysis, (4) Output & Metrics.
- Vậy `Test_VSF_forecast_demand/` chính là bản làm **Phase 1 & 2** của case study đó (nền tảng không gian + dự báo nhu cầu) — làm trước, đơn giản hơn bản trong `Test_VSF_driver_allocation/`.

## 2. Mục tiêu bài toán

Xây dựng mô hình AI dự báo **nhu cầu đặt xe (demand)** tại từng khu vực nhỏ trong thành phố, theo từng khung giờ, làm nền tảng cho thuật toán điều phối xe (supply dispatching) ở giai đoạn sau. Mục đích kinh doanh cuối cùng: giảm thời gian chờ của khách và giảm tỷ lệ tài xế chạy rỗng.

## 3. Phương pháp luận yêu cầu

- **Không gian (Spatial):** Chia thành phố thành lưới ô lục giác bằng thư viện `h3` (độ phân giải 8, ~0.7 km²/ô), tâm tại khu vực Hoàn Kiếm - Hà Nội, bán kính 4 ô → 61 hexagons.
- **Thời gian (Temporal):** Chia theo khung 30 phút/slot, 30 ngày dữ liệu (1,440 time-slots).
- Vì không có dữ liệu thật, phải **tự mô phỏng (mock)** dữ liệu nhu cầu sao cho hợp lý: 2 đỉnh cao điểm rõ rệt (8h sáng đi làm, 18h chiều tan tầm), có đỉnh phụ buổi trưa (12h30), giảm nhu cầu vào cuối tuần, nhiễu ngẫu nhiên, và mỗi hexagon có mức nhu cầu nền (base demand) khác nhau (khu đông đúc vs khu vắng).

## 4. Yêu cầu từng bước

### `step1_2_pipeline.py` — Bước 1 (tạo dữ liệu) + Bước 2 (xây mô hình dự báo)
- **Bước 1:** Sinh `mock_demand.csv` — dữ liệu demand giả lập theo lưới H3 × time-slot 30 phút, bám theo đặc tính giao thông thực tế mô tả ở mục 3.
- **Bước 2:** Feature engineering — tạo lag features (nhu cầu 1/2/3 slot trước, và `lag_48` = cùng giờ ngày hôm trước); train `LightGBM Regressor` dự báo `demand`; đánh giá bằng MAE/RMSE; vẽ biểu đồ so sánh Thực tế vs Dự báo cho 1 hexagon mẫu trong 2 ngày cuối của tập test.

### `generate_eda.py` — EDA bổ sung
- Biểu đồ nhu cầu trung bình theo giờ trong ngày (`eda_hourly.png`).
- Biểu đồ phân phối nhu cầu Ngày thường vs Cuối tuần (`eda_weekend.png`).

## 5. Output mong đợi (`output/`)

| File | Nội dung |
|---|---|
| `mock_demand.csv` | Dữ liệu mô phỏng nhu cầu theo hexagon × time-slot |
| `eda_hourly.png` | EDA — nhu cầu trung bình theo giờ |
| `eda_weekend.png` | EDA — ngày thường vs cuối tuần |
| `demand_forecast_chart.png` | So sánh Thực tế vs Dự báo (model LightGBM) |
| `Vinsmart_Presentation.html` | Báo cáo trình bày kết quả (đã generate sẵn) |

## 6. Kết quả đã đạt được (ghi nhận trong presentation)

- **MAE ≈ 1.25 cuốc xe / 30 phút / hexagon** — được đánh giá là mức sai số rất thấp, model dự báo "cực kỳ chính xác".
- Đường dự báo bám rất sát đường thực tế trong biểu đồ so sánh 2 ngày cuối của tập test.

## 7. Định hướng tiếp theo (đã nêu sẵn trong presentation, được triển khai tiếp ở `Test_VSF_driver_allocation/`)

- **Smart Matching:** thuật toán Bipartite Matching ghép tài xế rỗng gần nhất với khách theo khoảng cách H3, tối thiểu hóa ETA.
- **Dynamic Repositioning:** phát hiện ô lục giác có Cầu > Cung trong 30 phút tới (nhờ model dự báo), kêu gọi/thưởng tài xế đang chạy rỗng di chuyển tới trước khi "bão" khách xảy ra.
- **Simulation:** chạy môi trường giả lập để chứng minh tỷ lệ tài xế chạy rỗng giảm.

## 8. Lưu ý kỹ thuật quan trọng (phát hiện khi review code)

- **Cả 2 script đang hard-code đường dẫn tuyệt đối** tới `c:\_Antigravity\_AG_playground\Test\output\...` (một workspace/máy khác), không khớp với vị trí thực tế `Test_VSF_forecast_demand\output\` trong repo hiện tại. Nếu muốn chạy lại, **phải sửa đường dẫn trước** — nên đổi sang đường dẫn tương đối hoặc dùng `os.path.dirname(__file__)`.
- `generate_eda.py` đọc `mock_demand.csv` từ đường dẫn cứng đó, nên phải chạy `step1_2_pipeline.py` xong (và sửa đường dẫn khớp nhau) trước khi chạy `generate_eda.py`.

## 9. Cần xác nhận thêm

- "Vinsmart Future" trong presentation có phải tên thật của nhà tuyển dụng, hay là tên placeholder AI tự đặt khi sinh báo cáo (sản phẩm thật được nhắc xuyên suốt case study đầy đủ hơn ở `Test_VSF_driver_allocation` là **Xanh SM**)?
- Đây là bài test tuyển dụng đang làm dở / đã nộp, hay chỉ là bài tự luyện tập mô phỏng theo case thật? Nếu đang làm thật, cần biết phạm vi yêu cầu chính xác (chỉ Phase 1-2 ở đây, hay cả 4 Phase như bản đầy đủ) và deadline.
