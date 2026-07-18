---
name: design-powerbi-report
description: Build or redesign a Power BI report page (via powerbi-report-mcp, PBIR format) following the "Merchant Hub / OMD DATA" operational-dashboard design language reverse-engineered from a real sample. Use whenever the user asks to create a new Power BI report/dashboard page, or to restyle one "giống Merchant Hub" / "theo mẫu dashboard cũ".
---

Khi dựng hoặc redesign 1 report page Power BI qua `powerbi-report-mcp` (PBIR), áp dụng ngôn ngữ thiết kế dưới đây — rút ra từ dashboard mẫu "Merchant Hub / OMD DATA | T-SHOP" (`.claude/skills/powerbi-modeling-mcp/Merchant Hub.pdf`). Đây là bản tóm tắt đầy đủ, không cần mở lại PDF gốc trừ khi cần soi chi tiết pixel.

## 1. Khi nào dùng
Dashboard vận hành (operational BI) nhiều widget, mật độ thông tin dày, dùng để theo dõi số liệu hàng ngày — khác với slide trình bày (`design-html-page` dùng cho HTML report/trang trình bày, ít widget hơn, nhiều khoảng trắng hơn).

## 2. Header & breadcrumb (lặp lại y hệt trên mọi page)
- Góc trên-trái: `<TÊN HỆ THỐNG>` (đen, bold) + `| <TÊN MODULE>` (đỏ, bold). Nếu là trang con: nối thêm `/ <TÊN SUBPAGE>` cũng tô đỏ — breadcrumb phân cấp bằng dấu `/`.
- Ngay dưới: 2 dòng metadata xám nhỏ, không bold: `Refresh At <ngày giờ>` và `Latest <mốc dữ liệu mới nhất> <ngày giờ>` — luôn hiển thị để chứng minh độ tươi dữ liệu.
- Góc trên-phải: slicer **Calendar** cố định (dropdown "Multiple selections"/"All"), mọi trang đều có ở đúng vị trí này. Slicer phụ (nếu có) đặt bên trái slicer Calendar: dropdown đơn, nút bấm ngang (segmented button), hoặc range slider 2 đầu kèm date-picker.

## 3. Hàng KPI card
- Dãy card ngang, nền trắng, góc bo nhẹ, đổ bóng mờ tách khỏi nền canvas xám nhạt.
- Nội dung: **số lớn bold đen** phía trên + **label xám thường** phía dưới.
- **Thanh accent màu mỏng bên trái card** — đây không phải style card mặc định của Power BI, phải dựng bằng 1 shape/rectangle màu đặt lớp dưới, đè Card visual lên trên (offset để lộ mép trái ~3-4px).
- Màu accent mã hoá theo **luồng nghiệp vụ**, không phải trang trí ngẫu nhiên (xem mục 5).

## 4. Biểu đồ
- Bố cục lưới đều cột (2-3 card/hàng), tiêu đề nhỏ đậm góc trên-trái mỗi card.
- Chart mặc định: **Area chart + Line chart combo 2 trục** — measure chính tô vùng màu nhạt bán trong suốt, measure phụ vẽ **nét đứt** trên trục phải. Ưu tiên area mượt hơn bar chart.
- Màu area **phải khớp** với màu accent KPI card phía trên nó trong cùng khối nghiệp vụ.
- Donut chart: nhãn % đặt ngoài vòng kèm leader line; nhóm thiểu số/phụ luôn tô xám.

## 5. Quy tắc màu theo luồng nghiệp vụ (semantic color)
Một màu gắn cố định với một luồng nghiệp vụ, dùng lại xuyên suốt ở KPI card / chart / border — không đổi màu giữa các trang cho cùng 1 luồng:
- **Đỏ**: nhóm cảnh báo/rủi ro/hoá đơn điện tử (E-invoice), hoặc marker cho trang con đang review lỗi (card viền đỏ dày hơn bình thường + số cũng tô đỏ).
- **Xanh dương**: luồng chính (Orders, Merchant Active/MCA) — màu primary của toàn bộ report.
- **Xanh lá**: nhóm session/tương tác/đăng ký hoạt động (Session, Subscription, Staff app).
- **Xám**: giá trị blank/thiếu/nhóm thiểu số (`---`, hệ điều hành phụ...).

## 6. Bảng & matrix
- Style mặc định Power BI: header có mũi tên sort, gridline mảnh xám, không zebra-stripe.
- Dòng **Total luôn bold + có đường kẻ trên** phân tách với data phía trên.
- Matrix phân cấp: dùng icon +/- expand/collapse, dòng cha in đậm.
- **Heatmap bằng conditional formatting** (không cần chart riêng): matrix áp background color scale (thang xanh dương đậm-nhạt) lên chính bảng số — dùng cho ma trận 2 chiều dày đặc (vd giờ x ngày).
- Bảng raw detail luôn đặt cuối trang, scroll ngang, phục vụ audit nhanh ngay trên dashboard.

## 7. Footnote / ghi chú data quality
Dưới card có dữ liệu cần giải thích: 1 dòng *italic, xám, size nhỏ*, bắt đầu bằng `*`, mô tả caveat (vd blank do thiếu tracking, trường free-text...). Bắt buộc ghi ngay tại chỗ, không giấu trong tooltip — đây là quy ước tạo niềm tin dữ liệu cho người xem.

## 8. Typography & mật độ
- Font Segoe UI (mặc định Power BI theme), không dùng font trang trí.
- Nền canvas xám rất nhạt (~`#F2F2F2`), card nền trắng.
- Mật độ **dày đặc** — đây là dashboard vận hành, chấp nhận nhiều widget/trang, khoảng cách giữa card nhỏ (~8-12px), khác hẳn triết lý "nhiều whitespace" của slide trình bày.

## 9. Lưu ý khi dựng bằng cách sửa trực tiếp file PBIR (JSON) trên đĩa
Có thể không cần qua `powerbi-report-mcp` — nếu project là `.pbip` (đã Save As từ Power BI Desktop dạng Power BI Project), report layer nằm ở `<Tên Report>.Report/definition/pages/<pageId>/page.json` + `visuals/<visualId>/visual.json`, sửa trực tiếp bằng Read/Write/Edit là đủ, không cần MCP. Chỉ áp dụng khi Power BI Desktop **đang đóng** file đó (tránh ghi đè/xung đột với phiên đang mở).
- **KPI card `cardVisual` có sẵn property `accentBar`** (`objects.accentBar`: `show`, `color`, `width`) — đây là accent border trái **native**, không cần dựng thủ công bằng shape+card đè lớp như từng nghĩ. Set màu bằng `color.solid.color.expr.Literal.Value: "'#HEXCODE'"` để gán đúng màu nhóm nghiệp vụ (mục 5), không dùng `ThemeDataColor` tham chiếu index vì ColorId của theme được Power BI gán tuần tự theo thứ tự measure xuất hiện trong toàn report — không đoán trước được, nên set hex trực tiếp cho chắc.
- Theme màu (mục 5) nên khai báo thành 1 file theme JSON đăng ký trong `report.json` → `resourcePackages` (xem `StaticResources/RegisteredResources/*.json`) dùng chung cho report; nhưng với card/chart accent thì set hex trực tiếp trong visual (xem bullet trên) để không phụ thuộc ColorId.
- Area+line 1 measure/trục (mini chart theo ngày): visual `lineChart` với `objects.lineStyles.areaShow: true` + `lineChartType: 'smooth'` là đủ để ra area mượt — không cần combo 2 trục nếu mỗi chart chỉ có 1 measure. Combo 2 trục (measure phụ nét đứt) mới cần `lineStackedColumnComboChart`.
- Category axis nên set `show: false` (ẩn hẳn trục ngày) cho mini chart trong dashboard dày đặc — chỉ giữ `valueAxis` với `showAxisTitle: false` (vẫn hiện số, ẩn tiêu đề).
- Heatmap matrix (mục 6): bật conditional formatting kiểu "Background color" theo value trên field số trong Matrix visual, không phải Table visual.
- Measure trong query phải trỏ đúng **Entity = bảng gốc chứa measure đó** (`Expression.SourceRef.Entity`), tra trong TMDL (`SemanticModel/definition/tables/*.tmdl`) chứ không mặc định "Measure Collection" — nhiều measure thực ra sống ở bảng fact riêng (vd `f_firebase`, `f_txn_cks_hddt`).
