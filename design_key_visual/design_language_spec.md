# Analytics Design System (ADS) - Tiêu chuẩn Ngôn ngữ Thiết kế
*Tài liệu quy chuẩn hệ thống thiết kế (Design System) dành cho các ứng dụng Dashboard & Phân tích Dữ liệu cấp doanh nghiệp (Enterprise B2B). Tài liệu này có thể được nhân bản và tái sử dụng cho nhiều dự án khác nhau.*

---

## 1. Triết lý Thiết kế (Core Principles)
Hệ thống thiết kế này tập trung vào ba nguyên tắc cốt lõi:
1. **Data-First (Dữ liệu là trung tâm):** Giao diện phải lùi về phía sau để làm nền tôn lên dữ liệu. Không sử dụng các chi tiết trang trí thừa, gradient phức tạp hay mảng màu lớn không có ý nghĩa.
2. **Cognitive Ease (Tối giản hóa nhận thức):** Lượng dữ liệu khổng lồ phải được chia nhỏ thành các module dễ đọc, dễ quét (scannable) thông qua khoảng trắng (whitespace) và phân cấp thị giác cực kỳ chặt chẽ.
3. **Modularity (Tính Module hóa):** Các thành phần (Cards, Buttons, Charts, Tables) độc lập và nhất quán, dễ dàng lắp ghép linh hoạt như những mảnh Lego để tạo ra các Dashboard cho nhiều nghiệp vụ khác nhau.

---

## 2. Hệ thống Màu sắc (Color System)
Bảng màu được thiết kế để tạo độ tương phản cao, đảm bảo khả năng đọc số liệu (accessibility) và toát lên sự chuyên nghiệp, tin cậy.

### 2.1. Màu Chính (Primary Colors)
Dùng cho điểm nhấn thương hiệu, các hành động chính (Primary action), thanh điều hướng đang chọn (active state) và định hướng ánh mắt vào các dữ liệu quan trọng nhất.
*Đề xuất sử dụng "Analytics Blue" làm màu chủ đạo:*

| Token (Tên biến) | Mã Hex (HEX) | Chức năng & Ứng dụng |
| :--- | :--- | :--- |
| **Primary 900** | `#174EA6` | Text trên nền màu Primary nhạt, các thành phần hover cần nhấn mạnh mạnh. |
| **Primary 500 (Base)**| `#1A73E8` | **Màu cốt lõi.** Nút bấm (Primary Button), Active Tabs, Thanh biểu đồ chính. |
| **Primary 100** | `#D2E3FC` | Background cho trạng thái hover, vùng chọn (selection background). |
| **Primary 50** | `#E8F0FE` | Nền cho các bộ lọc (pills/chips) đang ở trạng thái active (chọn). |

### 2.2. Màu Trung tính & Bề mặt (Neutrals & Surfaces)
Đóng vai trò "nhường sân khấu" lại cho dữ liệu. Dùng cho background, thẻ (cards), text và đường viền (borders).

| Token (Tên biến) | Mã Hex (HEX) | Chức năng & Ứng dụng |
| :--- | :--- | :--- |
| **Gray 900** | `#202124` | Tiêu đề khối (H1, H2), text quan trọng nhất, Hero Metrics (Số liệu to). |
| **Gray 700** | `#5F6368` | Text phụ (Body), nhãn dữ liệu, tiêu đề cột của bảng biểu. |
| **Gray 400** | `#BDC1C6` | Placeholder text, icon hoặc button ở trạng thái không kích hoạt (disabled). |
| **Gray 200** | `#E8EAED` | Đường viền phân cách mỏng (Dividers), viền ô bảng biểu (Table borders). |
| **Gray 50** | `#F3F4F6` | **Nền hệ thống (App Background).** (Tạo độ chìm để các thẻ nổi lên). |
| **White** | `#FFFFFF` | **Bề mặt Thẻ (Card Surface).** Nơi chứa toàn bộ nội dung. |

### 2.3. Màu Dữ liệu & Trạng thái (Semantic & Categorical Colors)
Tuyệt đối duy trì sự nhất quán của ý nghĩa màu trên mọi dự án. Màu dùng để phân loại đối tượng (Compare Segments) hoặc thể hiện trạng thái (Thành công, Lỗi, Cảnh báo).

| Phân loại | Mã Hex (HEX) | Ý nghĩa / Ứng dụng |
| :--- | :--- | :--- |
| **Success (Xanh lá)** | `#1E8E3E` | Trạng thái Tốt (Active), Đã hoàn thành, Tăng trưởng dương (+). |
| **Warning (Cam)** | `#F29900` | Cảnh báo, Chờ xử lý, Nhấn mạnh ruy-băng, Segment dữ liệu số 2 (Khi so sánh). |
| **Danger (Đỏ)** | `#D93025` | Lỗi, Trạng thái Xấu, Tăng trưởng âm (-), Dừng hoạt động. |
| **Pink (Hồng/Tím)** | `#D81B60` | Điểm nhấn phụ, Segment dữ liệu số 3 (Khi so sánh chéo nhiều nhóm). |

---

## 3. Không gian & Cấu trúc (Layout & Spacing System)

### 3.1. Hệ thống Lưới Spacing (8pt Grid System)
Toàn bộ khoảng cách (padding, margin) giữa các thành phần tuân thủ bội số của 8 (hoặc 4 cho chi tiết rất nhỏ) để tạo sự nhịp nhàng thị giác.
*   **4px (0.25rem):** Khoảng cách sát (vd: giữa Icon và Text trong 1 nút).
*   **8px (0.5rem):** Padding trong các thành phần nhỏ (Pill filters, Input).
*   **16px (1rem):** Khoảng cách mặc định giữa các phần tử trong cùng một khối.
*   **24px (1.5rem):** Padding mặc định viền xung quanh bên trong Thẻ (Card Padding).
*   **32px (2rem)+:** Gutter (Khoảng cách) giữa các Thẻ với nhau trên Grid.

### 3.2. Kiến trúc Thẻ Dữ liệu (Card Architecture)
Thẻ là hạt nhân của Dashboard. Không giới hạn nội dung bên trong, nhưng phải bám chặt định dạng bao bọc bên ngoài:
*   **Background:** Luôn là White (`#FFFFFF`).
*   **Border Radius (Bo góc):** `8px` tạo sự hiện đại nhưng vẫn đủ độ cứng cáp của ứng dụng Enterprise.
*   **Elevation (Độ sâu / Bóng đổ):** Khước từ sử dụng viền kẻ (Solid border). Thay vào đó dùng bóng đổ rất nhạt, lan rộng để tách thẻ khỏi nền xám `Gray 50`.
    *   *Shadow mờ:* `box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);`

---

## 4. Typography (Hệ thống Text & Phân cấp)
Hệ thống sử dụng Font chữ hiện đại, không chân (Sans-serif) tập trung vào độ sắc nét để đọc số liệu: `Roboto`, `Inter` hoặc `System UI`.

*   **Phân cấp (Hierarchy):**
    *   **Hero Numbers (Số KPI trọng điểm):** Kích thước siêu lớn (36px - 48px). Dùng chữ mỏng (Light) hoặc trung bình (Medium), tuyệt đối không dùng in nghiêng. Màu: `Gray 900`.
    *   **Section/Block Headers:** In hoa (All-caps), kích thước nhỏ (11px-12px), khoảng cách chữ rộng (Letter-spacing: 1px). Dùng làm nhãn (label) điều hướng, giúp người dùng biết mình đang đọc khối nào mà không tranh chấp với số liệu. Màu: `Gray 700`.
    *   **Data Content (Dữ liệu bảng):** 13px - 14px, Regular, màu `Gray 700`. 
    *   **Quy tắc Căn lề:** 
        *   Tên hạng mục, chuỗi chữ: Căn Trái.
        *   Số lượng, tỷ lệ %, Tiền tệ: Luôn Căn Phải (Để dễ dàng so sánh hàng chục/trăm/nghìn).

---

## 5. Nguyên tắc Trực quan hóa Dữ liệu (Data Visualization Rules)

1.  **Dữ liệu tối đa, Mực in tối thiểu (Max Data, Min Ink):** Bỏ hết các đường lưới dọc/ngang (Gridlines) trong bảng nếu có thể, hoặc dùng viền nét cực mỏng (`Gray 200`). Trục biểu đồ nên được làm mờ bớt.
2.  **Quy tắc Micro-charts:** Tích hợp trực tiếp các biểu đồ cột hoặc thanh ngang thu nhỏ (Sparklines) ngay trong các ô của bảng số liệu. Điều này cung cấp bối cảnh (Context) trực quan sát sườn con số thay vì bắt mắt phải dò đi tìm biểu đồ ở chỗ khác.
3.  **Đồng bộ Màu sắc theo Ngữ cảnh:** Nếu bạn có 2 bộ lọc Segment (vd: Segment 1 màu Xanh, Segment 2 màu Cam). Mọi biểu đồ, mọi con số, mọi thanh bar liên quan đến Segment đó trên màn hình ĐỀU PHẢI áp dụng đúng màu tương ứng.
4.  **Tương tác Đa chiều (Cross-filtering):** Khi người dùng Hover/Click vào một cột trên biểu đồ chính, các dữ liệu (chỉ số rời, bảng phụ) bên trong cùng Thẻ cũng phải tự động highlight hoặc filter tương ứng.
