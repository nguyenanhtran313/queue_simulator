---
doc_id: forecast_demand
title: "Test_VSF_forecast_demand — Dự báo Nhu cầu Đặt xe (Xanh SM Phase 1 & 2)"
source: "Test_VSF_forecast_demand/_REQUIREMENT.md"
type: real
lang: vi
---

## Bối cảnh

`Vinsmart_Presentation.html` ghi rõ đây là bài cho "Tuyển dụng Data Team - Vinsmart Future". Thư mục anh em `Test_VSF_driver_allocation/` là bản mở rộng đầy đủ hơn của cùng case study "Xanh SM - Smart Dispatching & Demand Forecasting". `Test_VSF_forecast_demand/` là bản làm Phase 1 & 2 (nền tảng không gian + dự báo nhu cầu), đơn giản hơn bản trong `Test_VSF_driver_allocation/`.

## Mục tiêu bài toán

Xây dựng mô hình AI dự báo nhu cầu đặt xe tại từng khu vực nhỏ trong thành phố, theo từng khung giờ, làm nền tảng cho thuật toán điều phối xe ở giai đoạn sau. Mục đích kinh doanh: giảm thời gian chờ của khách và giảm tỷ lệ tài xế chạy rỗng.

## Phương pháp luận

- **Không gian**: lưới ô lục giác bằng thư viện `h3`, độ phân giải 8 (~0.7 km²/ô), tâm tại khu vực Hoàn Kiếm - Hà Nội, bán kính 4 ô → 61 hexagons.
- **Thời gian**: khung 30 phút/slot, 30 ngày dữ liệu (1,440 time-slots).
- Dữ liệu mock mô phỏng: 2 đỉnh cao điểm (8h sáng, 18h chiều), đỉnh phụ buổi trưa (12h30), giảm nhu cầu cuối tuần, nhiễu ngẫu nhiên, mỗi hexagon có base demand khác nhau.

## Các bước triển khai

`step1_2_pipeline.py`: Bước 1 sinh `mock_demand.csv`; Bước 2 feature engineering (lag features 1/2/3 slot trước + lag_48 = cùng giờ hôm trước), train **LightGBM Regressor** dự báo demand, đánh giá bằng MAE/RMSE. `generate_eda.py`: vẽ `eda_hourly.png` (nhu cầu theo giờ) và `eda_weekend.png` (ngày thường vs cuối tuần).

## Kết quả đạt được

MAE ≈ 1.25 cuốc xe / 30 phút / hexagon — sai số rất thấp, model dự báo "cực kỳ chính xác". Đường dự báo bám rất sát đường thực tế trong biểu đồ so sánh 2 ngày cuối tập test.

## Định hướng tiếp theo (triển khai ở Test_VSF_driver_allocation)

Smart Matching (Bipartite Matching ghép tài xế rỗng gần nhất theo khoảng cách H3), Dynamic Repositioning (kêu gọi tài xế di chuyển trước khi khu vực "bão" khách), Simulation để chứng minh giảm tỷ lệ chạy rỗng.

## Lưu ý kỹ thuật quan trọng

Cả 2 script (`step1_2_pipeline.py`, `generate_eda.py`) đang hard-code đường dẫn tuyệt đối tới `c:\_Antigravity\_AG_playground\Test\output\...` (một máy khác), không khớp vị trí thực tế `Test_VSF_forecast_demand\output\` trong repo hiện tại. Phải sửa đường dẫn (nên đổi sang đường dẫn tương đối hoặc `os.path.dirname(__file__)`) trước khi chạy lại.
