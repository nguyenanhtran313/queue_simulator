---
doc_id: glossary
title: "Glossary — Thuật ngữ kỹ thuật dùng trong các dự án của repo"
source: "fabricated (nội dung minh hoạ do RAG demo tự soạn, không phải tài liệu gốc)"
type: fabricated
lang: vi
---

## H3 (Uber H3 Spatial Index)

Hệ thống lưới không gian dạng lục giác do Uber phát triển, dùng để chia bản đồ thành các ô (hexagon) có kích thước đều nhau ở mỗi độ phân giải (resolution). Ưu điểm so với lưới vuông (như Google S2) là khoảng cách từ tâm một ô tới tất cả các ô lân cận đều bằng nhau, thuận tiện cho bài toán tính bán kính đón khách/ETA trong gọi xe. Dùng trong `Test_VSF_driver_allocation/` và `Test_VSF_forecast_demand/` với Resolution 8 (~0.7 km²/ô).

## AVM (Automated Valuation Model)

Mô hình định giá bất động sản tự động, dùng Machine Learning để ước tính giá trị một tài sản (thường là căn hộ, nhà đất) dựa trên đặc điểm của nó và dữ liệu giao dịch lịch sử, thay cho việc thẩm định giá thủ công. Dùng trong `Test_VSF_dinhgia_bds/`.

## SHAP (SHapley Additive exPlanations)

Kỹ thuật giải thích model Machine Learning (explainability/interpretability), dựa trên lý thuyết trò chơi hợp tác (Shapley value), cho biết mỗi đặc trưng (feature) đóng góp bao nhiêu vào một dự đoán cụ thể. Dùng ở Bước 5 của `Basic ML/` để diễn giải model XGBoost/LightGBM dự đoán phản hồi khuyến mãi.

## Uplift Modeling

Kỹ thuật ML dự đoán mức độ thay đổi hành vi khách hàng **do tác động của một can thiệp** (như gửi khuyến mãi), khác với mô hình dự đoán thông thường (Propensity Modeling) chỉ dự đoán khả năng xảy ra hành vi mà không tách được phần "sẽ xảy ra dù có can thiệp hay không". Chia khách hàng thành 4 nhóm: Sure Things (mua dù có hay không có khuyến mãi), Lost Causes (không mua dù thế nào), Sleeping Dogs (khuyến mãi phản tác dụng), Persuadables (nhóm mục tiêu chính — chỉ mua nếu có khuyến mãi). Dùng ở Bước 7–8 của `Basic ML/`.

## ROC-AUC

Chỉ số đánh giá model phân loại nhị phân (0/1), đo khả năng phân biệt giữa lớp dương và lớp âm ở mọi ngưỡng xác suất, giá trị từ 0.5 (ngẫu nhiên) tới 1.0 (hoàn hảo). Được ưu tiên hơn Accuracy đơn thuần khi dữ liệu mất cân bằng lớp (như tỷ lệ phản hồi khuyến mãi thấp trong `Basic ML/`).

## RAG (Retrieval-Augmented Generation)

Kiến trúc kết hợp truy hồi thông tin (retrieval) từ một kho tri thức (vector store) với mô hình ngôn ngữ lớn (LLM) để sinh câu trả lời có căn cứ (grounded), giảm hiện tượng bịa đặt (hallucination) và cho phép trích dẫn nguồn. Đây chính là kiến trúc dùng trong thư mục `RAG/` của repo này.

## Semantic Chunking

Kỹ thuật chia văn bản dài thành các đoạn (chunk) nhỏ hơn để đưa vào vector store, nhưng thay vì cắt theo số ký tự cố định, semantic chunking cắt theo ranh giới ngữ nghĩa (ví dụ theo heading, hoặc theo điểm mà độ tương đồng embedding giữa các câu liền kề giảm mạnh) — giúp mỗi chunk giữ được một ý trọn vẹn, cải thiện chất lượng retrieval so với fixed-size chunking.

## Rerank (Cross-Encoder Reranking)

Bước xử lý sau khi retrieval trả về danh sách ứng viên (top-N) từ vector search, dùng một mô hình khác (cross-encoder, hoặc LLM chấm điểm) để đánh giá lại độ liên quan giữa câu hỏi và từng đoạn văn một cách chính xác hơn, rồi chọn ra top-k tốt nhất đưa vào context cho LLM sinh câu trả lời.

## Bipartite Matching

Bài toán ghép cặp tối ưu giữa hai tập hợp (ở đây là tài xế và khách hàng) sao cho tổng chi phí (thường là thời gian chờ ETA) là nhỏ nhất, thường giải bằng thuật toán Hungarian/Kuhn-Munkres. Dùng trong Phase 3 của `Test_VSF_driver_allocation/` thay cho thuật toán Greedy (ghép tài xế gần nhất) vốn dễ gây cục bộ tối ưu.
