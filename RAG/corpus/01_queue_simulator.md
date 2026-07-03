---
doc_id: queue_simulator
title: "Queue Simulator — Website giả lập lý thuyết xếp hàng sân bay"
source: "Queue Simulator/_REQUIREMENT.md"
type: real
lang: vi
---

## Tổng quan hệ thống

Queue Simulator là một Web App hoạt động hoàn toàn trên trình duyệt (client-side), mô phỏng trực quan chuỗi quy trình xếp hàng 4 chặng tại sân bay: Check-in → An ninh → Xuất nhập cảnh → Cửa khởi hành. Người dùng cấu hình thông số cho từng Node, thiết lập luồng khách vào và kích hoạt các kịch bản thay đổi lưu lượng trực tiếp bằng slider để kiểm tra sức chịu tải (stress-test) ngay thời gian thực.

## Kiến trúc công nghệ

Kiến trúc 100% Frontend (Single Page Application), không có backend, không độ trễ API/WebSocket:
- Core Framework: React.js (khởi tạo qua Vite trong kế hoạch gốc; bản triển khai thực tế trong repo là single-file HTML dùng React UMD + Babel-standalone + Tailwind CDN + Chart.js, không có build step).
- Calculation Engine: JavaScript — dùng công thức toán học của lý thuyết xếp hàng (Queueing Theory) để tính công suất, chiều dài hàng đợi, thời gian chờ, thay vì mô phỏng từng cá thể.
- Charts: Chart.js.

## Thiết kế logic

Hệ thống quản lý chuỗi 4 trạm nối tiếp:
- **Customer Entry Node**: nguồn sinh hành khách, cấu hình Arrival Rate (λ, khách/phút) và Distribution (cố định hoặc Poisson/Exponential). Có kịch bản tức thời (x2, x3 lượng khách) mô phỏng xe bus đoàn/giờ cao điểm.
- **Job Nodes** (4 trạm: Check-in, An ninh, Hải quan, Cửa khởi hành): mỗi trạm cấu hình Capacity (số quầy mở), Processing Time (μ), Max Queue Capacity.
- **Customer Exit Node**: ghi nhận tổng thời gian (lead time) từ lúc vào đến lúc ra khỏi hệ thống.

## Chỉ số đầu ra

Tại mỗi Job Node: Current Queue Length, Server Utilization Rate ρ = λ/(c×μ), Average Waiting Time, Bottleneck Warning (cảnh báo đỏ nhấp nháy nếu ρ ≥ 1.0 hoặc hàng đợi sắp tràn).

## Tiêu chí nghiệm thu

Trang web chạy độc lập ở frontend, giao diện chuyên nghiệp hiện đại, slider tác động lập tức tới hệ thống đang giả lập, biểu đồ render mượt thời gian thực, cảnh báo tự động đổi màu đúng node là nút thắt cổ chai (bottleneck).
