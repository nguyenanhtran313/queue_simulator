---
name: run-driver-allocation
description: Run the driver-allocation simulation in Test_VSF_driver_allocation and regenerate its presentation.html. Use when the user asks to re-run, refresh, or rebuild the driver allocation simulation/presentation.
---

Chạy lại toàn bộ pipeline mô phỏng phân bổ tài xế trong `Test_VSF_driver_allocation/`:

1. Chạy `python phase1_simulation.py` trong thư mục `Test_VSF_driver_allocation/` để sinh/refresh kết quả simulation (đọc `mock_drivers.csv`, `mock_riders.csv`, ghi `realtime_heatmap.csv`).
2. Chạy `python build_presentation.py` trong cùng thư mục để đọc kết quả bước 1 và sinh lại `presentation.html`.
3. Báo lại cho user đường dẫn `presentation.html` vừa được cập nhật, và nêu ngắn gọn nếu có lỗi ở bước nào.

Nếu script báo thiếu package Python, hỏi user trước khi cài đặt — không tự ý `pip install`.
