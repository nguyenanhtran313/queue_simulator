# Kế hoạch Triển khai: Hệ thống Điều phối & Dự đoán Nhu cầu Xanh SM (Smart Dispatching System)

Bản kế hoạch này mô tả kiến trúc và các bước triển khai một hệ thống toàn diện cho nền tảng gọi xe (ride-hailing), tập trung vào:
1. **Lưới không gian (Spatial Indexing) & Real-time Heatmap** bằng H3 (Uber) hoặc S2 (Google) tại TP.HCM.
2. **Dự đoán nhu cầu (Demand Forecasting)** bằng Machine Learning.
3. **Phân tích hành vi & Cơ chế điều phối, chính sách hoa hồng (Incentives)** cho tài xế.

---

## Phần 1: Lưới Không Gian & Visualize Real-time Heatmap

### 1.1 So sánh H3 (Uber) vs S2 (Google)
Để phân tích dữ liệu không gian, ta cần chia bản đồ TP.HCM thành các ô nhỏ (grid).
*   **Google S2 (Hình tứ giác/vuông):** Tốt cho việc tìm kiếm điểm lân cận, nhưng khoảng cách từ tâm đến các điểm lân cận (cạnh và góc) là không đồng đều.
*   **Uber H3 (Hình lục giác):** Khoảng cách từ tâm đến tất cả các ô lân cận luôn bằng nhau (neighbor distance). Điều này cực kỳ quan trọng trong bài toán gọi xe để tính toán bán kính đón khách (ETA).
*   **Quyết định:** Chọn **Uber H3** với độ phân giải **Resolution 8** (mỗi ô rộng khoảng 0.73 km², độ dài cạnh ~461m) hoặc **Resolution 9** (~0.1 km²) để chia lưới TP.HCM.

### 1.2 Kiến trúc Visualize Real-time Heatmap
*   **Luồng dữ liệu (Data Pipeline):** Vị trí GPS của xe (Driver) và Tọa độ đặt xe (Rider) gửi liên tục về server thông qua WebSocket/MQTT.
*   **Xử lý (Stream Processing):** Dùng Apache Kafka hoặc Flink để stream data. Mỗi tọa độ GPS sẽ được map sang `H3 Index` tương ứng thông qua thư viện `h3-py`.
*   **Lưu trữ trạng thái (State Store):** Dùng **Redis** để lưu số đếm (count) real-time: `(H3_Index, Số lượng Khách đang tìm xe, Số lượng Xe đang trống)`.
*   **Visualize (Frontend):** Sử dụng **Kepler.gl** hoặc **deck.gl** kết hợp với Mapbox. Các thư viện này render layer H3 (HexagonLayer) cực kỳ mượt mà với hàng triệu điểm dữ liệu. Ô nào "Thiếu xe, thừa khách" sẽ hiển thị màu Đỏ đậm (Nóng), ô nào "Thừa xe, thiếu khách" màu Xanh (Lạnh).

---

## Phần 2: Machine Learning Dự Đoán Nhu Cầu (Demand Forecasting)

Mục tiêu: Biết trước 15 - 30 phút tới ở khu vực (Hexagon) nào sẽ có nhu cầu đặt xe cao để chuẩn bị sẵn xe.

### 2.1 Thu thập Data (Features Engineering)
*   **Spatial (Không gian):** `H3_Index`, Vị trí POI (Quận 1, Sân bay Tân Sơn Nhất, Bến xe miền Đông, các TTTM).
*   **Temporal (Thời gian):** Giờ trong ngày, Ngày trong tuần (Cuối tuần/Ngày thường), Tháng, Lễ/Tết.
*   **Contextual (Ngữ cảnh):** Thời tiết (Nắng/Mưa - ảnh hưởng cực lớn đến nhu cầu xe taxi), Sự kiện lớn trong thành phố (concert, bóng đá).
*   **Historical:** Lịch sử số lượng booking tại ô H3 đó trong khoảng thời gian t-1, t-2, t-3 (lag features).

### 2.2 Các mô hình Machine Learning phù hợp
1.  **Mô hình dạng cây (LightGBM / XGBoost):** Dễ training, xử lý tabular data tốt. Biến đổi bài toán thành supervised learning: `(Thời gian, Không gian, Thời tiết) -> Dự đoán Số lượng Request`.
2.  **Mô hình Deep Learning (LSTM / GRU):** Dự đoán chuỗi thời gian cho từng ô H3.
3.  **ST-GCN (Spatio-Temporal Graph Convolutional Networks):** Nâng cao. Mạng neural đồ thị kết hợp cả tính liên kết không gian (các ô H3 gần nhau) và thời gian. 
*Đề xuất giai đoạn đầu: Dùng LightGBM vì tốc độ inference nhanh và đủ tốt.*

---

## Phần 3: Phân tích Hành vi Driver & Cơ chế Điều Phối (Dispatching & Incentives)

Đây là phần tối ưu hóa hoạt động (Operations Research) và Gamification, nhằm điều chỉnh "Cung" chạy theo "Cầu".

### 3.1 Bài toán Matching (Điều phối cuốc xe)
Thay vì thuật toán "Tham lam" (Greedy) cứ tài xế nào gần nhất thì phát cuốc (khiến hệ thống bị cục bộ), nên dùng **Bipartite Matching** (Thuật toán Kuhn-Munkres/Hungarian):
*   Gom các request đặt xe trong 1 cửa sổ thời gian nhỏ (ví dụ 3-5 giây gọi là batching window).
*   Thuật toán sẽ ghép cặp N tài xế với M khách hàng sao cho **tổng thời gian chờ (Total ETA) của toàn hệ thống là nhỏ nhất**.

### 3.2 Repositioning (Điều hướng xe chạy rỗng)
Khi mô hình ML (ở Phần 2) báo rằng: *30 phút nữa Sân bay Tân Sơn Nhất thiếu xe, nhưng hiện tại Quận 3 đang thừa xe trống.*
*   Hệ thống cần phát tín hiệu (Heatmap trên app tài xế) để "dụ" tài xế từ Quận 3 chạy lên Sân bay.
*   Tuy nhiên, tài xế sẽ không chạy rỗng nếu tốn xăng/điện mà không có tiền. Ta cần **Chính sách kích cầu (Incentives)**.

### 3.3 Phân tích hành vi Driver & Chính sách Hoa Hồng (Incentives)
Tài xế thường có hành vi (Personas):
1.  Thích chạy cuốc ngắn trong trung tâm (cày cuốc lấy thưởng số lượng).
2.  Thích chạy cuốc dài (đi xa, đỡ kẹt xe).
3.  Tránh kẹt xe, né các quận ngập nước.

**Các chiến lược điều động (Incentives) áp dụng thực tế:**
*   **Surge Pricing (Giá tăng vọt):** Khi cầu > cung tại một ô H3 (màu đỏ). Tăng giá cước khách hàng (1.2x, 1.5x) và trích % giá tăng thêm này cộng trực tiếp vào thu nhập của Driver. Điều này hút tài xế chạy về vùng đỏ.
*   **Dynamic Commission (Hoa hồng động):** Nếu Driver nhận một cuốc đi từ Vùng Lạnh (Cung > Cầu) sang Vùng Nóng (Cầu > Cung), hãng giảm tỷ lệ chiết khấu (hoa hồng) thu của tài xế (ví dụ từ 25% xuống 15%) cho riêng cuốc đó.
*   **Repositioning Bonus (Thưởng di chuyển rỗng):** Nếu Driver chịu chạy xe không từ điểm A đến điểm B (Vùng đang thiết hụt), ngay khi tới điểm B, hệ thống cộng thẳng tiền thưởng cố định hoặc "Điểm tích lũy loyalty".
*   **Consecutive Trip Streak (Chuỗi cuốc liên hoàn):** Thưởng thêm tiền nếu tài xế nhận liên tiếp 3 cuốc xe trong khu vực H3 hệ thống chỉ định mà không từ chối/hủy.
*   **Destination Matching:** Sắp hết ca làm việc, phân tích xem nhà tài xế ở đâu, hệ thống ưu tiên "nổ" các cuốc xe có điểm đến hướng về nhà của họ để tối ưu.

---

## Phần 4: Lộ trình Thực hiện (Roadmap)

*   **Phase 1: Foundation (2-3 tuần)**
    *   Mô phỏng dữ liệu (Mock data) bằng Python: Sinh ngẫu nhiên các tọa độ đón khách, vị trí tài xế tại khu vực trung tâm TP.HCM.
    *   Tích hợp H3 Index, xuất dữ liệu.
    *   Dựng Frontend (React + deck.gl) để xem real-time Heatmap.
*   **Phase 2: Demand Prediction (3-4 tuần)**
    *   Tạo tập dữ liệu lịch sử giả định (có yếu tố ngày đêm, cuối tuần, khu vực).
    *   Train mô hình LightGBM dự đoán nhu cầu tại từng H3 Index.
    *   Render kết quả dự báo lên bản đồ.
*   **Phase 3: Dispatch & Incentive Simulator (4 tuần)**
    *   Viết logic bắt cặp xe - khách (Matching Algorithm).
    *   Xây dựng module "Incentive Engine": Tính toán giá Surge và tự động áp dụng khi chênh lệch Cung/Cầu vượt ngưỡng.
*   **Phase 4: Dashboard & Metrics**
    *   Bảng điều khiển cho Operation Manager theo dõi: Tỉ lệ hoàn thành cuốc (Fulfillment rate), Thời gian chờ trung bình (ETA), Chi phí khuyến mãi (Incentive spend).

---
*Ghi chú: Nếu bạn muốn bắt đầu bằng cách mô phỏng sinh dữ liệu mock-data (H3 và vị trí tài xế tại HCM) và dựng Heatmap ngay, hãy cho tôi biết!*
