---
doc_id: basic_ml
title: "Basic ML — Dự đoán & Tối ưu hóa Phản hồi Khuyến mãi Khách hàng"
source: "Basic ML/_REQUIREMENT.md"
type: real
lang: vi
---

## Bối cảnh nghiệp vụ

Một ngân hàng (dữ liệu mẫu mã khách hàng tiền tố `TCB...`, phân khúc Priority/Standard) muốn chạy chiến dịch khuyến mãi (SMS/email) tới khách hàng hiện hữu, dựa trên lịch sử phản hồi (`Historical_Promo_Response` = 0/1). Bài toán: dự đoán khách hàng nào có khả năng phản hồi cao nhất, diễn giải được vì sao model dự đoán vậy, và quy đổi thành quyết định kinh doanh + con số ROI so với gửi đại trà.

## Dữ liệu

`customer_promo_data.csv` — 1,000,000 khách hàng (đã scale lên từ bản gốc 1,000 dòng bằng `00_generate_data.py`, backup ở `customer_promo_data_1k_backup.csv`). Cột quan trọng: `Promo_Txn_Count_3M` (tín hiệu mạnh nhất), `Last_Active_Days` (tương quan âm), `Avg_Monthly_Balance_VND` (tương quan dương yếu), target `Historical_Promo_Response`. `Estimated_CLV_VND` trùng thông tin gần như 100% với `Avg_Monthly_Balance_VND` — bẫy đa cộng tuyến, phải loại khi train.

## Các bước pipeline (00 → 09)

00 sinh dữ liệu quy mô lớn → 01 EDA & Statistical Tests (T-test, Chi-square, correlation heatmap) → 02 KMeans Customer Segmentation (phân tích độc lập, không nằm trong luồng dữ liệu chính) → 03 Logistic Regression Benchmark (mốc ROC-AUC) → 04 XGBoost/04b LightGBM Production (lưu `.pkl`, liên kết kỹ thuật thật sự duy nhất trong pipeline) → 05 SHAP Explainability (đọc lại `.pkl` từ bước 4, giải thích model) → 06 Expected Profit Calculation (đọc lại `.pkl`, tính lợi nhuận kỳ vọng = P(phản hồi)×reward − cost) → 07 Uplift Modeling ROI (S-Learner, phân biệt Persuadables/Sure things/Lost causes/Sleeping dogs) → 08 So sánh 6 model (3 Propensity + 3 Uplift, train/test split một lần duy nhất, tránh data leakage) → 09 xây `presentation.html`.

## Business constants

Chi phí gửi ZNS = 500 VND/tin/khách hàng; lợi nhuận trung bình/khách hàng phản hồi = 10,000 VND; break-even threshold = 5%. Quy ước gửi: Propensity gửi nếu P(phản hồi) > 5%, Uplift gửi nếu Uplift Score > 5%.

## Kết quả & tiêu chí thành công

Model production (XGBoost/LightGBM) phải có ROC-AUC cao hơn benchmark Logistic Regression. Phải giải thích được qua SHAP 2 yếu tố quyết định lớn nhất. Chiến lược tối ưu bằng ML và bằng Uplift phải cho lợi nhuận cao hơn gửi đại trà.

## Lưu ý về tính tuần tự

Đánh số 01→09 gợi ý pipeline liền mạch, nhưng phần lớn các bước không thực sự nạp lại output của bước trước — mỗi bước tự đọc `customer_promo_data.csv` gốc. Phụ thuộc kỹ thuật (file .pkl) thật sự chỉ có ở Bước 4 → Bước 5 và Bước 4 → Bước 6. Các bước còn lại nối nhau theo mạch lý luận kinh doanh/phân tích, không phải theo dữ liệu.
