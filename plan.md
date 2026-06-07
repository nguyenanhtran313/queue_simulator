Dưới đây là bản **Kế hoạch triển khai kỹ thuật (Technical Implementation Plan)** đã được tinh chỉnh lại. Bản cập nhật này chuyển dịch mô hình giả lập (simulation) lên toàn bộ Frontend để mang lại trải nghiệm tương tác thời gian thực mượt mà nhất (không độ trễ), dễ dàng triển khai và đặc biệt tối ưu để AI Assistant (như tôi) có thể xây dựng một giao diện thực sự ấn tượng (Premium UI).

---

# KẾ HOẠCH TRIỂN KHAI: WEBSITE GIẢ LẬP LÝ THUYẾT XẾP HÀNG SÂN BAY (NODE-BASED SIMULATOR)

## 1. TỔNG QUAN HỆ THỐNG (SYSTEM OVERVIEW)

Mục tiêu là xây dựng một Web App hoạt động hoàn toàn trên trình duyệt (Client-side), mô phỏng trực quan chuỗi quy trình xếp hàng 4 chặng tại sân bay (Check-in -> An ninh -> Xuất nhập cảnh -> Cửa khởi hành). Người dùng có thể cấu hình thông số cho từng Node, thiết lập luồng khách vào và kích hoạt các kịch bản thay đổi lưu lượng trực tiếp bằng slider để kiểm tra sức chịu tải của hệ thống (Stress-test) ngay thời gian thực.

## 2. KIẾN TRÚC CÔNG NGHỆ ĐỀ XUẤT (TECH STACK)

Để loại bỏ độ trễ của API/Websocket và tối đa hóa tính trực quan, hệ thống sẽ được xây dựng theo kiến trúc **100% Frontend (Single Page Application)**:

*   **Core Framework:** React.js (khởi tạo qua Vite).
*   **Calculation Engine:** JavaScript/TypeScript (Sử dụng trực tiếp các công thức Toán học / Lý thuyết xếp hàng để tính toán công suất, chiều dài hàng đợi và thời gian chờ dựa trên chênh lệch lưu lượng vào/ra, thay vì phải chạy vòng lặp giả lập từng cá thể).
*   **Giao diện & Styling:** Tailwind CSS. Tích hợp thiết kế hiện đại (Rich Aesthetics, Dark mode, Glassmorphism).
*   **Biểu đồ (Charts):** `Recharts` hoặc `Chart.js` để hiển thị biểu đồ luồng dữ liệu biến động liên tục ở tốc độ mượt mà.
*   **Hoạt ảnh (Animations):** `Framer Motion` (tùy chọn) để làm mượt các chỉ số và chuyển động đồ họa.

---

## 3. THIẾT KẾ LOGIC & CẤU HÌNH (COMPONENTS SPECIFICATION)

Hệ thống quản lý chuỗi 4 trạm nối tiếp. Các thành phần bao gồm:

### A. Customer Entry Node (Điểm Hành Khách Đến)

Là nguồn sinh ra hành khách đưa vào hệ thống sân bay.

*   **Cấu hình đầu vào:**
    *   `Arrival Rate ($\lambda$)`: Số lượng khách đến trung bình (Khách/phút).
    *   `Distribution`: Cố định hoặc Phân phối Poisson/Exponential.
*   **Kịch bản tức thời (Scenarios):** Sử dụng thanh kéo (Slider) hoặc Nút bấm (Buttons) để lập tức x2, x3 lượng khách (Giả lập xe bus đoàn vừa đến, giờ cao điểm).

### B. Job Nodes (4 Trạm Dịch Vụ Sân Bay)

Chuỗi trạm nối tiếp: **Check-in -> An ninh -> Hải quan -> Cửa khởi hành**.

*   **Cấu hình đầu vào cho mỗi trạm:**
    *   `Capacity (c)`: Số lượng quầy/nhân viên đang mở.
    *   `Processing Time ($\mu$)`: Thời gian xử lý trung bình cho 1 khách.
    *   `Max Queue Capacity`: Sức chứa tối đa của hàng đợi.

### C. Customer Exit Node (Cất Cánh/Rời Đi)

*   **Logic tính toán:** Ghi nhận tổng thời gian (Lead time) từ lúc bước vào sân bay đến lúc ra khỏi hệ thống.

---

## 4. CÁC CHỈ SỐ ĐẦU RA CẦN ĐO LƯỜNG (OUTPUT METRICS)

Tại mỗi **Job Node**, Calculation Engine sẽ áp dụng công thức để tính toán và hiển thị ngay trên UI:

1.  `Current Queue Length`: Số lượng người đang chờ xếp hàng.
2.  `Server Utilization Rate (%)`: Hiệu suất sử dụng quầy ($\rho$).
3.  `Average Waiting Time`: Thời gian chờ trung bình ước tính.
4.  `Bottleneck Warning`: Đổi màu khu vực cảnh báo (Nhấp nháy Đỏ) ngay lập tức nếu $\rho \ge 1.0$ hoặc hàng đợi sắp tràn.

---

## 5. KẾ HOẠCH PHÁT TRIỂN CHI TIẾT (DEVELOPMENT ROADMAP)

Việc lập trình sẽ chia làm 3 giai đoạn (Sprints):

### Giai đoạn 1: Xây dựng Lõi Tính toán (JS Calculation Core)

*   Thiết lập các hàm tính toán Toán học / Queueing Theory (như tính hệ số sử dụng $\rho = \lambda / (c \times \mu)$, độ dài hàng đợi $L_q$, thời gian chờ $W_q$).
*   Đánh giá chênh lệch luồng khách (Flow Rate): Tính toán lượng khách dồn ứ dựa trên `Arrival Rate` của chặng trước chuyển sang và `Capacity` của chặng hiện tại.
*   Quản lý State toàn cục để các Components UI có thể truy xuất thông tin Node và phản hồi lập tức khi người dùng kéo Slider.

### Giai đoạn 2: Thiết kế Giao diện Tương Tác & Dashboard (Premium UI)

*   **Khu vực điều khiển (Controls):** Bảng panel chứa các thanh trượt (Sliders) để tăng/giảm nhanh số lượng quầy và lượng khách đến.
*   **Khu vực hiển thị luồng (Visual Flow):** Thiết kế sơ đồ theo dạng các khối thẻ (Cards) nối tiếp nhau. Mỗi ô hiển thị rõ nét con số `Đang chờ` và `Hiệu suất %`.
*   **Phong cách thiết kế:** Ứng dụng màu sắc tương phản rõ ràng (Xanh: Bình thường, Vàng: Bắt đầu ùn ứ, Đỏ: Quá tải nghiêm trọng), thiết kế phẳng, bóng bẩy mang phong cách công nghệ.

### Giai đoạn 3: Biểu đồ và Tối ưu hóa (Charts & Polish)

*   Tích hợp Recharts để vẽ biểu đồ đường Line Chart đa luồng (thể hiện số khách kẹt ở từng trạm).
*   Kiểm thử tính liên tục: Khi đang chạy, việc người dùng thao tác vào các Slider phải tác động tới biểu đồ một cách trơn tru, biểu đồ chạy liên tục như một nhịp tim hệ thống.

---

## 6. TIÊU CHÍ NGHIỆM THU (ACCEPTANCE CRITERIA)

*   [ ] Trang web hoạt động hoàn toàn độc lập ở Frontend (chạy `npm run dev` thông qua Vite), không phụ thuộc Backend Python.
*   [ ] Giao diện Dashboard (UI) toát lên sự chuyên nghiệp, hiện đại, phối màu chuẩn UI/UX.
*   [ ] Thanh trượt (Slider) thay đổi thông số phải tác động lập tức tới lượng khách/quầy ngay trong lúc hệ thống đang giả lập.
*   [ ] Biểu đồ biến động mượt mà, render thời gian thực chính xác.
*   [ ] Hệ thống cảnh báo tự động thay đổi màu sắc tại chính xác Node đang là "Nút thắt cổ chai" (Bottleneck).