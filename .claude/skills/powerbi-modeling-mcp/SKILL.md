---
name: powerbi-modeling-mcp
description: Thao tác an toàn trên semantic model Power BI Desktop đang mở qua MCP server powerbi-modeling-mcp (đọc/sửa measure, table, relationship, M-query...). Dùng khi user yêu cầu kết nối/sửa/review 1 file Power BI Desktop đang mở, hoặc hỏi về quy tắc đặt tên measure trong Power BI.
---

Ghi chú: các file `.pbix` không thuộc repo này — server `powerbi-modeling-mcp` kết nối trực tiếp tới instance Power BI Desktop đang chạy trên máy, tách biệt hoàn toàn với repo.

## Kết nối
1. `connection_operations` `ListLocalInstances` để tìm instance đang mở (kèm port).
2. `Connect` bằng connection string trả về.
3. Nếu 1 câu lệnh báo "Connection is not open" / timeout → Desktop đã restart (port đổi). Gọi lại `ListLocalInstances` lấy port mới rồi `Connect` lại.

## An toàn vs Rủi ro

**An toàn** (chỉ đổi metadata, không đụng report layout):
- Sửa `description`, `formatString`, DAX `expression` của measure.
- Sửa `DisplayFolder`.
- Sửa M-query (`partition_operations Update` → phải gọi thêm `RefreshWithXMLA` để nạp lại dữ liệu, không tự động refresh).

**Rủi ro — có thể vỡ visual trên report**:
- `Move` measure sang bảng khác, `Rename` bảng/cột/measure qua MCP này. Lý do: report Power BI lưu tham chiếu field theo cặp (Bảng, Tên field); sửa qua XMLA/TOM (ngoài UI Desktop) không đồng bộ lại report layout, nên visual không tìm thấy field cũ → lỗi.
- Chỉ Move/Rename measure đã tồn tại nếu chắc chắn không có visual nào đang dùng, hoặc đã hỏi user trước.

## Quy tắc đặt tên & tổ chức Measure

- **Prefix `#`**: measure ra số tuyệt đối (Count/Sum/DistinctCount), kể cả các measure GAP (dù đơn vị hiển thị là %).
- **Prefix `%`**: measure ra tỷ lệ/phần trăm (margin, conversion rate, growth rate).
- **Không prefix**: measure thời gian/text/tiện ích hệ thống (VD `Refresh At`, `Read Me`).
- **Gap tuyệt đối giữa 2 kỳ/2 mốc so sánh**: `#GAP <BaseMeasure> (<Kiểu so sánh>)` — VD `#GAP %Margin (MOM)`, `#GAP #Total Price (actual vs target)`.
- **Tăng trưởng tương đối**: `%GAP <BaseMeasure> (<Kiểu so sánh>)` — VD `%GAP #Total Price (MOM)`.
- **Description**: 2 câu cố định — `<Mô tả ngắn tiếng Việt> [<Công thức DAX rút gọn, VD Sum(total_price)/DistinctCount(x)/Max(x)>]. <Mục đích, bắt đầu bằng "Đo lường..." hoặc "Dùng để...">.`
- **DisplayFolder**: dùng 1 folder phẳng `_Measure` cho mọi measure (dấu `_` để nổi lên đầu Field List).