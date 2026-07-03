---
doc_id: faq_repo
title: "FAQ nội bộ — Câu hỏi thường gặp về các dự án trong repo"
source: "fabricated (nội dung minh hoạ do RAG demo tự soạn, không phải tài liệu gốc)"
type: fabricated
lang: vi
---

## Queue Simulator có cần cài đặt gì không?

Không. `Queue Simulator/index.html` là file HTML đơn (single-file), tự chứa React qua UMD build và Babel-standalone để biên dịch JSX ngay trên trình duyệt, cộng Tailwind CDN và Chart.js CDN. Chỉ cần mở file bằng trình duyệt (double-click hoặc `start index.html`), không cần Node.js, không cần `npm install`, không có bước build.

## Test_VSF_driver_allocation và Test_VSF_forecast_demand khác nhau thế nào?

Cả hai là hai phần của cùng một case study tuyển dụng "Xanh SM — Smart Dispatching & Demand Forecasting". `Test_VSF_forecast_demand` làm Phase 1 (lưới không gian H3) và Phase 2 (dự báo nhu cầu bằng LightGBM) — đơn giản hơn, tập trung riêng vào bài toán forecast. `Test_VSF_driver_allocation` là bản mở rộng, làm tiếp Phase 3 (điều phối tài xế, Bipartite Matching, chính sách hoa hồng) và Phase 4 (dashboard & metrics), đồng thời là thư mục đang được chỉnh sửa tích cực nhất trong repo hiện tại.

## Tại sao Test_VSF_dinhgia_bds có tên giống Test_VSF nhưng lại không liên quan?

Tên thư mục trùng tiền tố `Test_VSF_` chỉ là trùng hợp cách đặt tên, không phải bằng chứng cùng một case study. Không tìm thấy `presentation.html` hay tài liệu nào trong `Test_VSF_dinhgia_bds/` nhắc tới "Xanh SM" hay "Vinsmart" — đây là một bài định giá bất động sản (AVM) độc lập.

## Vì sao Basic ML phải chạy đúng thứ tự 00 → 09?

Vì các bài sau dùng lại output (file `.pkl` hoặc `.csv`) của bài trước ở một vài điểm nhất định — cụ thể là Bước 4 (train model, lưu `.pkl`) là input bắt buộc cho Bước 5 (SHAP) và Bước 6 (Expected Profit). Nếu bỏ qua Bước 4 mà chạy thẳng Bước 5/6, script sẽ báo lỗi vì thiếu file model. Các bước còn lại tuy không phụ thuộc file lẫn nhau về mặt kỹ thuật, nhưng nên chạy theo đúng thứ tự vì đó là mạch trình bày logic cho người đọc (business).

## RAG này lấy dữ liệu từ đâu?

Corpus của RAG gồm 2 loại: (1) tài liệu thật, lấy nguyên từ các file `_REQUIREMENT.md` và `CLAUDE.md` có sẵn trong repo; (2) tài liệu bịa thêm (FAQ, glossary, changelog, ghi chú vận hành) do RAG tự soạn nhằm có đủ nội dung đa dạng để kiểm thử chunking/retrieval/rerank, không phải tài liệu gốc của dự án — các file này được đánh dấu `type: fabricated` trong metadata.

## Muốn thêm tài liệu mới vào RAG thì làm sao?

Thêm file Markdown mới (có frontmatter `doc_id`, `title`, `source`, `type`, `lang`) vào `RAG/corpus/`, rồi chạy lại `python ingest.py` để nạp lại toàn bộ corpus vào vector store Chroma tại `RAG/index/`.
