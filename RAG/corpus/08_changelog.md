---
doc_id: changelog
title: "Changelog minh hoạ — Các mốc phát triển đáng chú ý trong repo"
source: "fabricated (nội dung minh hoạ do RAG demo tự soạn dựa trên ghi chú trong _REQUIREMENT.md, không phải changelog chính thức)"
type: fabricated
lang: vi
---

## 2026-07-03 — Basic ML scale dữ liệu lên 1 triệu dòng

`00_generate_data.py` được thêm vào để sinh 1,000,000 dòng dữ liệu khách hàng mock thay cho bộ gốc 1,000 dòng, hiệu chỉnh để tái lập đúng các quan hệ thống kê đã phát hiện ở Bước 1 (EDA). Bộ dữ liệu gốc 1,000 dòng được giữ lại backup tại `customer_promo_data_1k_backup.csv`. Đồng thời bổ sung Bước 8 (`08_Model_Comparison_ROI.py`) để so sánh công bằng 6 model (3 Propensity + 3 Uplift) trên cùng một train/test split, tránh lạc quan giả do data leakage ở các bước trước.

## 2026-07-03 — Thêm thư mục RAG/

Bổ sung dự án `RAG/` — RAG (Retrieval-Augmented Generation) engine tra cứu thông tin về chính các dự án trong repo, chìa API `POST /ask` cho các chatbot bên ngoài (Dify, N8N) gọi vào lấy context để trả lời người dùng. Corpus khởi điểm gồm các file `_REQUIREMENT.md`/`CLAUDE.md` thật cộng thêm một số tài liệu minh hoạ (FAQ, glossary, changelog) tự soạn.

## Ghi chú lịch sử (suy ra từ _REQUIREMENT.md, không có ngày chính xác)

- `Test_VSF_forecast_demand/` và `Test_VSF_driver_allocation/` được xác định là 2 phần của cùng case study tuyển dụng "Xanh SM — Smart Dispatching & Demand Forecasting" (Phase 1–2 và Phase 3–4 tương ứng).
- `Test_VSF_dinhgia_bds/` không có `presentation.html` hay tài liệu đề bài gốc — được xác nhận là một case study riêng biệt (định giá bất động sản/AVM), không liên quan tới case study Xanh SM dù trùng tiền tố tên thư mục.
- 2 script trong `Test_VSF_forecast_demand/` (`step1_2_pipeline.py`, `generate_eda.py`) được ghi nhận đang hard-code đường dẫn output tuyệt đối tới một máy khác — cần sửa path trước khi chạy lại trên máy hiện tại.
