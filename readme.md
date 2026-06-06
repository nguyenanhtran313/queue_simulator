# ✈️ Airport Queue Theory Simulator (AQTS) - Specification Document

Tài liệu này đặc tả chi tiết kiến trúc dữ liệu đầu vào (Inputs), các kịch bản kiểm thử biến động (Scenarios) và logic cốt lõi của thuật toán mô phỏng Lý thuyết xếp hàng áp dụng tại hệ thống vận hành đa tầng sân bay.

---

## 1. Luồng Di Chuyển Của Hành Khách (Simulation Workflow)

Mô hình giả lập chuỗi hệ thống xếp hàng mở (Open Jackson Network) gồm 4 chặng nối tiếp. Hành khách sau khi hoàn thành chặng trước sẽ lập tức chuyển thành hàng đợi đầu vào của chặng sau:

```text
[Passenger Arrival] 
       │
       ▼
 ┌───────────┐      ┌──────────────┐      ┌─────────────┐      ┌──────────────┐
 │ Chặng 1   │ ---> │ Chặng 2      │ ---> │ Chặng 3     │ ---> │ Chặng 4      │ ---> [Boarding]
 │ Check-in  │      │ An ninh soi  │      │ Xuất nhập   │      │ Cửa khởi     │
 │ Counters  │      │ chiếu (Security)     │ cảnh (Immi) │      │ hành (Gates) │
 └───────────┘      └──────────────┘      └─────────────┘      └──────────────┘
