# Requirement — Basic ML: Dự đoán & Tối ưu hóa Phản hồi Khuyến mãi Khách hàng

> **Lưu ý quan trọng:** Thư mục này không có file đề bài/brief gốc nào còn lại. Nội dung dưới đây được **suy ngược (reverse-engineer) từ 7 script Python đã viết** (`01_...` → `07_...`) và dữ liệu mẫu `customer_promo_data.csv`. Đây là bản dựng lại hợp lý nhất dựa trên bằng chứng trong code, không phải bản chép lại đề bài gốc 100% — nếu có brief/slide gốc ở đâu đó (email, khóa học, Notion...), nên đối chiếu lại.

## 1. Bối cảnh nghiệp vụ (Business Context)

Một ngân hàng (dữ liệu mẫu có mã khách hàng tiền tố `TCB...`, phân khúc `Priority`/`Standard`) muốn chạy một chiến dịch khuyến mãi (gửi SMS/email) tới khách hàng hiện hữu. Ngân hàng có sẵn dữ liệu lịch sử: khách hàng nào từng phản hồi khuyến mãi trước đây (`Historical_Promo_Response` = 0/1) cùng các đặc điểm hành vi/tài chính của họ.

**Bài toán:** Dùng dữ liệu lịch sử để xây dựng mô hình Machine Learning giúp:
1. Dự đoán khách hàng nào có khả năng phản hồi khuyến mãi cao nhất.
2. Diễn giải được **vì sao** model đưa ra dự đoán đó (để thuyết phục stakeholder không rành kỹ thuật).
3. Quy đổi kết quả model thành **quyết định kinh doanh cụ thể** (nên gửi khuyến mãi cho ai) và **con số lợi nhuận tăng thêm (ROI)** so với cách làm cũ (gửi đại trà).

## 2. Dữ liệu đầu vào

File: `customer_promo_data.csv` — 1,000 khách hàng, các cột:

| Cột | Ý nghĩa |
|---|---|
| `Customer_ID` | Mã khách hàng (định danh, không dùng làm feature) |
| `Age`, `Gender` | Nhân khẩu học |
| `Segment` | Phân khúc khách hàng (Priority/Standard) |
| `Avg_Monthly_Balance_VND` | Số dư tài khoản trung bình/tháng |
| `Txn_Count_3M`, `Txn_Amount_3M_VND` | Số lượng & tổng giá trị giao dịch 3 tháng gần nhất |
| `App_Logins_3M` | Số lần đăng nhập app 3 tháng gần nhất |
| `Promo_Txn_Count_3M` | Số lần từng dùng khuyến mãi trong 3 tháng gần nhất |
| `Last_Active_Days` | Số ngày kể từ lần hoạt động cuối |
| `Historical_Promo_Response` | **Biến mục tiêu (target)** — khách hàng có phản hồi khuyến mãi trước đây không (1/0) |
| `Estimated_CLV_VND` | Giá trị vòng đời khách hàng ước tính (⚠️ trùng thông tin gần như 100% với `Avg_Monthly_Balance_VND` — bẫy đa cộng tuyến, phải loại bỏ khi train) |

## 3. Yêu cầu từng bước (Scope of Work)

### Bước 1 — EDA & Statistical Tests (`01_EDA_and_Stats.py`)
- Kiểm tra chất lượng dữ liệu (missing values, outlier) và baseline response rate.
- Chạy T-test cho biến liên tục, Chi-square cho biến phân loại để xác định biến nào **có ý nghĩa thống kê** (p-value < 0.05) với target.
- Vẽ correlation heatmap để phát hiện đa cộng tuyến giữa các biến.
- **Deliverable:** danh sách biến giữ lại cho model (`Promo_Txn_Count_3M`, `Last_Active_Days`, `Avg_Monthly_Balance_VND`, `Segment`) + biến loại bỏ, kèm `01_correlation_matrix.png`.

### Bước 2 — KMeans Customer Segmentation (`02_KMeans_Segmentation.py`)
- Phân cụm khách hàng theo hành vi (không dùng Age/Gender) sau khi chuẩn hóa dữ liệu.
- Tìm số cụm K tối ưu bằng Elbow Method + Silhouette Score.
- Profile từng cụm (giá trị trung bình các đặc trưng) để có thể đặt tên nhóm khách hàng.
- **Deliverable:** `02_kmeans_evaluation.png` + `customer_promo_data_clustered.csv`.

### Bước 3 — Logistic Regression Benchmark (`03_Logistic_Regression_Benchmark.py`)
- Xây model baseline dự đoán `Historical_Promo_Response`, dùng pipeline chuẩn hóa (numeric) + one-hot encoding (categorical).
- Xử lý mất cân bằng lớp bằng `class_weight='balanced'`.
- **Deliverable:** classification report + ROC-AUC score làm mốc so sánh cho các model sau.

### Bước 4 — XGBoost Production Model (`04_XGBoost_Production.py`, có bản thay thế `04b_LightGBM_Production.py`)
- Xây model tree-based mạnh hơn benchmark, không cần scale numeric, xử lý phi tuyến tốt hơn.
- So sánh ROC-AUC với Logistic Regression.
- **Deliverable:** model đã train lưu ra `.pkl` (`04_xgboost_model.pkl` / `04b_lightgbm_model.pkl`) để tái sử dụng ở các bước sau mà không cần train lại.

### Bước 5 — SHAP Explainability (`05_SHAP_Analysis.py`, bản LightGBM riêng)
- Diễn giải model production (biến "hộp đen" AI thành "hộp trong suốt"): biểu đồ Bar (feature importance tổng thể), Dot (chiều hướng tác động), Dependence Plot (tìm ngưỡng bùng phát) cho 2 biến quan trọng nhất.
- **Deliverable:** 4 ảnh SHAP + phần giải thích cách đọc biểu đồ in ra console.

### Bước 6 — Expected Profit Calculation (`06_Expected_Profit_Calculation.py`)
- Gắn giả định kinh doanh: chi phí gửi 1 lượt = 500 VND, lợi nhuận nếu khách phản hồi = 50,000 VND.
- Tính lợi nhuận kỳ vọng từng khách hàng = `P(phản hồi) × reward − cost`; chỉ gửi khuyến mãi nếu > 0.
- So sánh 2 kịch bản: gửi đại trà (mass marketing) vs gửi chọn lọc theo ML, ra con số **chênh lệch lợi nhuận (ROI improvement)**.
- **Deliverable:** `06_campaign_decisions.csv` (danh sách khách hàng nên gửi + xác suất + lợi nhuận kỳ vọng).

### Bước 7 — Uplift Modeling ROI (`07_Uplift_Modeling_ROI.py`)
- Đi xa hơn dự đoán thông thường: phân biệt 4 nhóm khách hàng theo lý thuyết Uplift (Sure things / Lost causes / Sleeping dogs / **Persuadables** — nhóm mục tiêu chính).
- Dùng S-Learner (đưa biến `Treatment` = từng dùng khuyến mãi hay chưa vào làm feature) để tính Uplift Score = P(mua | có KM) − P(mua | không KM).
- Tính lợi nhuận gia tăng (Incremental Profit) từ Uplift Score, quyết định gửi khuyến mãi theo tiêu chí này thay vì chỉ theo xác suất mua thô ở Bước 6.
- **Deliverable:** `07_uplift_decisions.csv` — danh sách khách hàng target theo Uplift, sắp xếp theo Uplift Score giảm dần.

## 4. Ràng buộc & quy ước kỹ thuật

- Các bước phải chạy **tuần tự** vì bước sau phụ thuộc output (`.pkl`, `.csv`) của bước trước — đặc biệt Bước 5 và 6 bắt buộc phải có `04_xgboost_model.pkl` (hoặc bản LightGBM) từ Bước 4.
- Luôn loại `Customer_ID` và `Estimated_CLV_VND` khỏi feature set khi train (tránh học nhiễu / đa cộng tuyến).
- Metric đánh giá chính: ROC-AUC (so sánh model) và Expected Profit/ROI (so sánh giá trị kinh doanh) — không chỉ dừng ở accuracy vì dữ liệu mất cân bằng lớp.

## 5. Tiêu chí thành công suy luận được (Success Criteria)

- Model production (XGBoost/LightGBM) phải có ROC-AUC cao hơn benchmark Logistic Regression.
- Phải giải thích được (qua SHAP) 2 yếu tố quyết định lớn nhất tới hành vi phản hồi khuyến mãi.
- Phải chốt được bằng số tiền cụ thể: chiến lược tối ưu bằng ML (Bước 6) và bằng Uplift (Bước 7) phải cho lợi nhuận cao hơn chiến lược gửi đại trà.

## 6. Việc cần làm rõ thêm nếu muốn xác nhận đúng đề gốc

- Đây là bài tự luyện tập cá nhân hay case study lấy từ một khóa học/công ty cụ thể? Nếu có brief gốc, nên đối chiếu để bổ sung phần mình có thể đã suy diễn sai (vd: con số chi phí 500đ/lợi nhuận 50,000đ có phải giả định đề bài cho sẵn hay tự đặt).
- Dữ liệu `customer_promo_data.csv` là mock hoàn toàn hay có phần lấy từ nguồn thật — không có script sinh dữ liệu này trong thư mục (khác với `_Test_VSF_forecast_demand` hay `_Teset_VSF_dinhgia_bds` là có `generate_*.py` riêng).
