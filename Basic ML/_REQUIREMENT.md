# Requirement — Basic ML: Dự đoán & Tối ưu hóa Phản hồi Khuyến mãi Khách hàng

> **Lưu ý:** Thư mục này không có file đề bài/brief gốc nào còn lại — nội dung dưới đây được **suy ngược (reverse-engineer) từ các script Python đã viết** (`00_...` → `07_...`) và dữ liệu mẫu `customer_promo_data.csv`. Đây là bản dựng lại hợp lý nhất dựa trên bằng chứng trong code, không phải bản chép lại đề bài gốc 100%.

## 1. Bối cảnh nghiệp vụ (Business Context)

Một ngân hàng (dữ liệu mẫu có mã khách hàng tiền tố `TCB...`, phân khúc `Priority`/`Gold`/`Standard`) muốn chạy một chiến dịch khuyến mãi tới khách hàng hiện hữu. Ngân hàng có sẵn dữ liệu lịch sử: khách hàng nào từng phản hồi khuyến mãi trước đây (`Historical_Promo_Response` = 0/1) cùng các đặc điểm hành vi/tài chính của họ.

**Bài toán:** Dùng dữ liệu lịch sử để xây dựng mô hình Machine Learning giúp:
1. Dự đoán khách hàng nào có khả năng phản hồi khuyến mãi cao nhất.
2. **So sánh chất lượng 2 model tree-based (XGBoost vs LightGBM)** một cách có hệ thống, không chỉ train song song rồi bỏ đó.
3. Diễn giải được **vì sao** model đưa ra dự đoán đó (để thuyết phục stakeholder không rành kỹ thuật).
4. Quy đổi kết quả model thành **quyết định kinh doanh cụ thể** (nên gửi khuyến mãi cho ai) và **con số lợi nhuận tăng thêm (ROI)** so với cách làm cũ (gửi đại trà).
5. Trình bày toàn bộ pipeline thành 1 trang `presentation.html` tự chứa, phong cách phỏng vấn Data/ML.

## 2. Dữ liệu đầu vào

File: `customer_promo_data.csv` — **10,000 khách hàng**, sinh bởi `00_generate_data.py` (`numpy.random.default_rng(42)`, deterministic — chạy lại luôn ra cùng 1 bộ dữ liệu). Các cột:

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

> **Về tính "tuần tự":** đánh số 00→07 gợi ý một pipeline liền mạch, nhưng đọc kỹ code (`grep` các lệnh `read_csv`/`joblib.load`) thì phần lớn các bước **không thực sự nạp lại output của bước trước** — mỗi bước tự đọc `customer_promo_data.csv` (sinh bởi Bước 0) và tự train model riêng. Sự phụ thuộc **kỹ thuật (file/model)** thật sự có ở: Bước 4/4b → Bước 4c (qua `model_metrics.json` + `04_test_predictions.csv`/`04b_test_predictions.csv`), Bước 4 → Bước 5, Bước 4b → Bước 5b, và Bước 4+4b → Bước 6 (qua 2 file `.pkl`). Bước cuối `build_presentation.py` đọc **toàn bộ artifact** (JSON/CSV/PNG) do các bước 01→07 sinh ra — không train lại gì. Mỗi bước dưới đây có ghi rõ *"Mục đích cho bước sau"* để phân biệt liên kết kỹ thuật vs liên kết lý luận.

### Bước 0 — Generate Mock Data (`00_generate_data.py`)
- Sinh 10,000 khách hàng bằng logistic model + nhiễu Bernoulli, có chủ đích giữ đúng mạch lý luận của các bước sau: 4 biến "có tín hiệu thật" (`Promo_Txn_Count_3M`, `Last_Active_Days`, `Avg_Monthly_Balance_VND`, `Segment`), nhóm biến nhiễu độc lập với target nhưng tự tương quan chéo cao (`Txn_Count_3M`, `Txn_Amount_3M_VND`, `App_Logins_3M`), bẫy đa cộng tuyến `Estimated_CLV_VND` ≈ 0.99 `Avg_Monthly_Balance_VND`.
- **Thiết kế phi tuyến "đậm" (v2):** cả `Last_Active_Days` VÀ `Promo_Txn_Count_3M` đều là bậc thang không đơn điệu/bão hoà (không phải đường thẳng), cộng thêm **4 tương tác nhân** (Promo×Last_Active, Segment×Promo, Segment×Last_Active×Promo bậc 3, và 1 "bộ khuếch đại tiêu cực" Last_Active×Promo dồn 1 nhóm khách hàng xuống xác suất gần 0) — toàn bộ cấu trúc này nằm ngoài tầm với của 1 mô hình tuyến tính cộng tính như Logistic Regression. Balance dùng `np.clip(balance_z, -3, 3)` trước khi bình phương để tránh đuôi lognormal tạo ra `z` cực đoan phi thực tế.
- **v1 → v2 (cùng ngày 2026-07-03):** bản v1 (xem lịch sử git) chỉ tạo khoảng cách ROC-AUC ~0.03 giữa LogReg và tree-model, và ở giả định chi phí Zalo ZNS ban đầu hầu như mọi khách hàng đều vượt breakeven — khiến toàn bộ phần "so sánh model" ở Business Impact/Uplift nhạt nhoà, trông như feature không có tác dụng. Bản v2 tăng khoảng cách ROC-AUC lên ~0.06 và nới rộng phổ xác suất dự đoán.
- **v2 → v3 (cùng ngày, sau khi có giả định kinh doanh Zalo ZNS chính xác từ người dùng — tỷ lệ convert 5%, lợi nhuận gộp 100đ/khách hàng):** hạ intercept từ `-2.05` xuống `-5.28` để response rate khớp đúng **~5.2%** (thay vì ~25% ở v2) — response rate thấp này thực tế hơn cho 1 campaign ZNS, và vì breakeven (4.17%) giờ **xấp xỉ sát** response rate nền (5%), model phân loại tốt hơn mới thực sự tạo khác biệt lớn về số người nên liên hệ (chứ không chỉ khác biệt nhẹ như v2). Kết quả v3: ROC-AUC LogReg 0.86 / XGBoost 0.92 / LightGBM 0.92 (gap ~0.055), LightGBM loại được ~68% khách hàng (so với ~19% ở v2, ~0% ở v1), lợi nhuận LightGBM-optimized gấp ~3.8 lần Mass Marketing (so với ~1.02x ở v2) — xem card "Chọn Model Nào?" và tab Uplift trong `presentation.html`.
- ⚠️ **Ràng buộc quan trọng:** response rate của DGP (Bước 0) và tỷ lệ convert giả định ở Bước 6 (`06_Expected_Profit_Calculation.py`) **phải khớp nhau** — nếu đổi 1 trong 2 mà quên đổi cái còn lại, breakeven sẽ lệch pha với response rate thực tế và toàn bộ câu chuyện "model tạo khác biệt" có thể biến mất trở lại (như đã xảy ra giữa v1 và v2).
- **Deliverable:** ghi đè `customer_promo_data.csv`.
- **Mục đích cho bước sau:** nền tảng dữ liệu cho toàn bộ pipeline — mọi bước 01→07b đều đọc file này. Đổi DGP bắt buộc phải chạy lại **toàn bộ** pipeline từ Bước 0 (data mới → model mới → mọi artifact sau đó đều lỗi thời).

### Bước 1 — EDA & Statistical Tests (`01_EDA_and_Stats.py`)
- Kiểm tra chất lượng dữ liệu (missing values, outlier) và baseline response rate.
- Chạy T-test cho biến liên tục, Chi-square cho biến phân loại để xác định biến nào **có ý nghĩa thống kê** (p-value < 0.05) với target.
- Vẽ correlation heatmap để phát hiện đa cộng tuyến giữa các biến.
- **Deliverable:** danh sách biến giữ lại cho model (`Promo_Txn_Count_3M`, `Last_Active_Days`, `Avg_Monthly_Balance_VND`, `Segment`) + biến loại bỏ, kèm `01_correlation_matrix.png`.
- **Mục đích cho bước sau:** ⚠️ chỉ mang tính **tham khảo/diễn giải**, không phải input kỹ thuật bắt buộc — Bước 3/4/7 vẫn tự đưa **gần như toàn bộ cột** (trừ `Customer_ID`/target/`Estimated_CLV_VND`) vào model, không lọc lại theo danh sách "biến ý nghĩa thống kê" mà Bước 1 tìm ra. Giá trị thật của bước này là để người đọc (business) hiểu trước biến nào quan trọng, dùng đối chiếu lại với kết quả SHAP ở Bước 5 sau này.

### Bước 2 — KMeans Customer Segmentation (`02_KMeans_Segmentation.py`)
- Phân cụm khách hàng theo hành vi (không dùng Age/Gender) sau khi chuẩn hóa dữ liệu.
- Tìm số cụm K tối ưu bằng Elbow Method + Silhouette Score.
- Profile từng cụm (giá trị trung bình các đặc trưng) để có thể đặt tên nhóm khách hàng.
- **Deliverable:** `02_kmeans_evaluation.png` + `customer_promo_data_clustered.csv`.
- **Mục đích cho bước sau:** ⚠️ không có bước nào (03→07) đọc lại `customer_promo_data_clustered.csv` — đây là một **phân tích độc lập, không nằm trong luồng dữ liệu chính**. Giá trị của nó là cung cấp thêm góc nhìn "chân dung khách hàng" (persona) song song, không phải để làm feature/input cho model dự đoán phản hồi khuyến mãi.

### Bước 3 — Logistic Regression Benchmark (`03_Logistic_Regression_Benchmark.py`)
- Xây model baseline dự đoán `Historical_Promo_Response`, dùng pipeline chuẩn hóa (numeric) + one-hot encoding (categorical).
- Xử lý mất cân bằng lớp bằng `class_weight='balanced'`.
- **Deliverable:** classification report + ROC-AUC score, model lưu ra `03_logreg_model.pkl`, metric ghi vào `model_metrics.json`.
- **Mục đích cho bước sau:** `model_metrics.json` được Bước 4c đọc để so sánh 3 model; `03_logreg_model.pkl` được Bước 6 `joblib.load()` lại để tính luôn Expected Profit cho benchmark — cần thiết để trả lời câu hỏi kinh doanh "Logistic Regression có Recall cao, vậy có nên dùng thay XGBoost/LightGBM không?" bằng số tiền cụ thể thay vì chỉ so ROC-AUC.

### Bước 4 — XGBoost & LightGBM Production Models (`04_XGBoost_Production.py`, `04b_LightGBM_Production.py`)
- Xây 2 model tree-based mạnh hơn benchmark, không cần scale numeric, xử lý phi tuyến/tương tác tốt hơn Logistic Regression. Cấu hình (n_estimators/learning_rate/max_depth/subsample) được canh cho tập train 8,000 dòng, `scale_pos_weight`/`class_weight='balanced'` xử lý mất cân bằng lớp (~15-23% response), cùng đánh giá ở threshold 0.5 để so sánh công bằng.
- **Deliverable:** model `.pkl` (`04_xgboost_model.pkl` / `04b_lightgbm_model.pkl`), dự đoán trên test set (`04_test_predictions.csv` / `04b_test_predictions.csv` — có `Customer_ID` để merge chính xác), và ghi metric vào `model_metrics.json` chung.
- **Mục đích cho bước sau:** ✅ liên kết kỹ thuật — `.pkl` được Bước 5/5b và Bước 6 `joblib.load()` lại; `model_metrics.json` + `04_test_predictions.csv`/`04b_test_predictions.csv` được Bước 4c đọc để so sánh.

### Bước 4c — Model Comparison (`04c_Model_Comparison.py`)
- **Bước còn thiếu trong bản gốc, được bổ sung để thực sự so sánh chất lượng 2 model** thay vì chỉ train song song rồi dùng cứng 1 model ở các bước sau.
- Merge dự đoán của 2 model theo `Customer_ID`, so ROC-AUC/Accuracy/Precision/Recall/F1 (kèm cả benchmark Logistic Regression từ Bước 3), vẽ ROC curve chồng, Precision-Recall curve chồng, confusion matrix cạnh nhau, feature importance cạnh nhau (đồng bộ `importance_type='gain'` giữa 2 thư viện để so sánh công bằng).
- **Deliverable:** `04c_roc_comparison.png`, `04c_pr_comparison.png`, `04c_confusion_matrices.png`, `04c_feature_importance_comparison.png`, `model_comparison_summary.json` (field `best_model_by_auc_key`/`_name` — **chỉ là xếp hạng theo ROC-AUC**, không phải khuyến nghị kinh doanh cuối cùng, xem Bước 6).
- **Mục đích cho bước sau:** `model_comparison_summary.json` được `build_presentation.py` đọc để dựng tab "So sánh Model" — phần trọng tâm của bản trình bày.

  ⚠️ **Insight quan trọng:** model có ROC-AUC cao nhất (XGBoost) **không nhất thiết** là model tạo lợi nhuận cao nhất. ROC-AUC đo chất lượng xếp hạng trung bình trên *toàn bộ* dải ngưỡng, trong khi quyết định kinh doanh ở Bước 6 chỉ dùng *1 ngưỡng cụ thể* (breakeven ≈ cost/reward) — 1 model có thể thắng AUC tổng thể nhưng thua đúng ở vùng ngưỡng doanh nghiệp thực sự dùng. `build_presentation.py` tách rõ 2 khái niệm `best_model_by_auc_*` (Bước 4c, thống kê) vs `best_model_by_profit_*` (Bước 6, kinh doanh) để không nhầm lẫn — dù ở mức chi phí liên hệ hiện tại (xem Bước 6) chênh lệch lợi nhuận sổ sách giữa các model chỉ vài chục nghìn VND, không đáng kể. Insight **quan trọng hơn** của cả pipeline nằm ở Bước 6→7, xem cảnh báo bên dưới.

### Bước 5 / 5b — SHAP Explainability (`05_SHAP_Analysis.py` cho XGBoost, `05b_SHAP_Analysis_LightGBM.py` cho LightGBM)
- Load lại model `.pkl` tương ứng, diễn giải model production (biến "hộp đen" AI thành "hộp trong suốt"): biểu đồ Bar (feature importance tổng thể), Dot (chiều hướng tác động), Dependence Plot (tìm ngưỡng bùng phát) cho 2 biến quan trọng nhất. Output của 2 script có hậu tố riêng (`_xgb.png` / `_lgbm.png`) để không ghi đè lẫn nhau.
- **Deliverable:** 4 ảnh SHAP mỗi model (8 ảnh tổng) + phần giải thích cách đọc biểu đồ in ra console.
- **Mục đích cho bước sau:** thuần diễn giải, `build_presentation.py` nhúng cả 8 ảnh để so sánh 2 model có đồng thuận về yếu tố quan trọng hay không — bằng chứng thuyết phục hơn 1 model đơn lẻ.

### Bước 6 — Expected Profit Calculation (`06_Expected_Profit_Calculation.py`)
- Load **cả 3** model `.pkl` (Bước 3 + 4 + 4b — bao gồm cả Logistic Regression benchmark, không chỉ 2 model tree-based) để lấy xác suất phản hồi từng khách hàng theo từng model.
- Gắn giả định kinh doanh — kênh gửi khuyến mãi: **Zalo ZNS**, tính phí theo tin gửi **thành công**. `cost_per_email = 500 VND`. Tỷ lệ convert trung bình (khách nhận tin → ra đơn) = **5%** (khớp response rate của `00_generate_data.py`, xem bên dưới). Lợi nhuận gộp SAU CÙNG (đã trừ chi phí tin) trung bình = **100 VND/khách hàng được gửi** → suy ra `reward_per_response = (100 + 500) / 5% = 12,000 VND` (lợi nhuận gộp NẾU khách convert, trước khi trừ chi phí tin — kiểm tra: `5% × 12,000 − 500 = 100`, khớp đúng giả định). Breakeven = cost/reward = **4.17%** — xấp xỉ tỷ lệ convert nền nên model phân loại **thực sự tạo khác biệt lớn** về số khách hàng nên liên hệ (LogReg loại ~22%, XGBoost ~63%, LightGBM ~68%) và lợi nhuận (Mass Marketing → LightGBM-optimized gấp ~3.8 lần).
- Con số chi phí/lợi nhuận này do người dùng cung cấp trong quá trình review (không tự sinh từ `customer_promo_data.csv`), và tỷ lệ convert 5% quyết định trực tiếp cách canh intercept của DGP ở Bước 0 — **đổi 1 trong 2 (giả định kinh doanh hoặc DGP) đều phải đổi cả 2 cho khớp nhau**, nếu không breakeven và response rate thực tế sẽ lệch pha.
- **Tiêu chí chọn model (theo yêu cầu người dùng):** không chỉ argmax lợi nhuận — ưu tiên model "vừa lời tốt, vừa Accuracy/Recall tốt để còn kế thừa sau này", vì gửi sai (false positive) mất phí mà không thu lợi nhuận. `build_presentation.py` implement quy tắc: nếu chênh lệch lợi nhuận giữa XGBoost/LightGBM < 10%, ưu tiên model có Recall cao hơn (`recommended_classifier_key` trong code) thay vì model lời nhất thuần tuý — trên dữ liệu hiện tại, XGBoost được chọn (Recall 81.6% vs LightGBM 77.7%, lợi nhuận chỉ kém 5.9%).
- Tính lợi nhuận kỳ vọng từng khách hàng theo từng model = `P(phản hồi) × reward − cost`; chỉ gửi nếu > 0. So 4 kịch bản: Mass Marketing / Logistic Regression-optimized / XGBoost-optimized / LightGBM-optimized — `best_scenario` = kịch bản lợi nhuận **"sổ sách"** cao nhất trong 3 model (chênh lệch thực tế nhỏ ở mức chi phí này).
- **Deliverable:** `06_campaign_decisions.csv` (cột riêng cho từng model), `06_profit_comparison.json`, `06_profit_comparison.png`.
- **Mục đích cho bước sau:** `06_profit_comparison.json` được `build_presentation.py` đọc trực tiếp cho tab "Business Impact" và cho card "Chọn Model Nào?" ở tab "So sánh Model".

  ⚠️ **Giới hạn của cách tính này (chỉ lộ ra ở Bước 7/7b):** `P(phản hồi)` là xác suất **tương quan** (correlational) — nó không phân biệt được khách hàng phản hồi *vì* được liên hệ, hay đằng nào cũng phản hồi dù không ai gọi (Sure Things). Khi kiểm tra lại bằng Uplift Score, lợi nhuận nhân quả thực của cả 4 kịch bản Bước 6 tuy vẫn dương (vì chi phí liên hệ quá rẻ so với lợi nhuận), nhưng **thấp hơn** lợi nhuận đạt được nếu target đúng bằng Uplift — Bước 7/7b tồn tại để chứng minh và tận dụng khoảng cách đó, không phải "kỹ thuật nâng cao cho vui".

### Bước 7 / 7b — Uplift Modeling ROI (`07_Uplift_Modeling_ROI.py` = S-learner XGBoost, `07b_Uplift_Modeling_ROI_LightGBM.py` = S-learner LightGBM)
- Đi xa hơn dự đoán thông thường: phân biệt 4 nhóm khách hàng theo lý thuyết Uplift (Sure things / Lost causes / Sleeping dogs / **Persuadables** — nhóm mục tiêu chính).
- Dùng S-Learner (đưa biến `Treatment` = từng dùng khuyến mãi hay chưa vào làm feature, **tự train một model mới** — không tái dùng `.pkl` của Bước 4/4b) để tính Uplift Score = P(mua | có KM) − P(mua | không KM). Chạy **song song 2 base learner độc lập** (XGBoost và LightGBM) để kiểm chứng chéo, giống cách 04/04b đã làm với bài toán phân loại. Dùng cùng giả định chi phí/lợi nhuận với Bước 6 (Zalo ZNS, 500đ / 12.000đ).
- Tính lợi nhuận gia tăng (Incremental Profit) từ Uplift Score, quyết định gửi khuyến mãi theo tiêu chí này thay vì chỉ theo xác suất mua thô ở Bước 6.
- **Deliverable:** `07_uplift_decisions.csv` / `07b_uplift_decisions.csv` — danh sách khách hàng target theo từng base learner, sắp xếp theo Uplift Score giảm dần.
- **Mục đích cho bước sau:** `build_presentation.py` merge `06_campaign_decisions.csv` với cả 2 file uplift theo `Customer_ID` để: (1) tính lại lợi nhuận **nhân quả thực** cho các kịch bản của Bước 6 (card "Kiểm Tra Nhân Quả"), và (2) so sánh trực tiếp 2 base learner Uplift với nhau (card "So sánh 2 Base Learner") — base learner nào cho lợi nhuận nhân quả cao hơn sẽ là **khuyến nghị targeting cuối cùng của toàn bộ pipeline**.

  ⚠️ **2 tầng giới hạn cần biết:** (1) `Treatment` được suy ra từ hành vi quá khứ (`Promo_Txn_Count_3M > 0`), **không phải** một cờ ngẫu nhiên hoá từ thử nghiệm A/B thật — đây là uplift modeling kiểu quan sát (observational), kết luận nhân quả vẫn có thể lẫn confounding bias. (2) Tỷ lệ đồng thuận giữa 2 base learner Uplift (~84%) thấp hơn hẳn so với bài toán phân loại thường (~95%) — ước lượng Uplift Score (hiệu số 2 xác suất) vốn nhạy/nhiễu hơn ước lượng 1 xác suất đơn, đây là giới hạn cố hữu của kỹ thuật, không phải lỗi triển khai. Nếu deploy thật, nên chạy 1 A/B test nhỏ để kiểm chứng lại Uplift Score trước khi rollout toàn bộ (đã ghi trong khuyến nghị "Bước tiếp theo" của `presentation.html`).

### Bước cuối — Presentation (`build_presentation.py`)
- Đọc **toàn bộ artifact** (không train lại gì) do Bước 00→07b sinh ra — JSON metrics, CSV quyết định, PNG biểu đồ/SHAP — nhúng ảnh dạng base64 để ra 1 file `presentation.html` tự chứa.
- Thiết kế phong cách Google Analytics: top-tab navigation, KPI stat-tile, bảng/biểu đồ tối giản, Chart.js cho phần dữ liệu động (ROC/PR curve, so sánh metric, so sánh lợi nhuận), ảnh PNG cho phần matplotlib-only (SHAP, correlation heatmap, KMeans elbow).
- Báo lỗi tiếng Việt rõ ràng nếu thiếu artifact đầu vào (giống cách skill `run-ml-lesson` kiểm tra dependency).

## 4. Ràng buộc & quy ước kỹ thuật

- Nên chạy **tuần tự 00→07 rồi `build_presentation.py`** — thứ tự này vừa phản ánh **mạch lý luận trình bày cho business** (data → EDA → phân khúc → benchmark → model mạnh hơn → so sánh → giải thích → định lượng lợi nhuận → tối ưu lợi nhuận → trình bày), vừa là ràng buộc kỹ thuật thật sự ở một số cặp bước (00→tất cả; 04/04b→4c/5/5b/6; 01-07→build_presentation.py). Xem chi tiết dependency ở từng bước tại Mục 3.
- Luôn loại `Customer_ID` và `Estimated_CLV_VND` khỏi feature set khi train (tránh học nhiễu / đa cộng tuyến).
- Metric đánh giá chính: ROC-AUC (so sánh model) và Expected Profit/ROI (so sánh giá trị kinh doanh) — không chỉ dừng ở accuracy vì dữ liệu mất cân bằng lớp (~15-23% response).
- `class_weight='balanced'`/`scale_pos_weight` cải thiện quyết định ở threshold nhưng làm lệch xác suất thô (probability calibration) — Bước 6/7 dùng trực tiếp xác suất này để tính tiền, đây là một giới hạn đã biết (xem "Bước tiếp theo" ở tab Kết luận của `presentation.html`), không phải bug.

## 5. Tiêu chí thành công suy luận được (Success Criteria)

- Model production (XGBoost/LightGBM) phải có ROC-AUC cao hơn benchmark Logistic Regression — được xác minh tự động ở `04c_Model_Comparison.py` (không chỉ so sánh thủ công bằng mắt như bản gốc).
- Phải giải thích được (qua SHAP, cả 2 model) 2 yếu tố quyết định lớn nhất tới hành vi phản hồi khuyến mãi.
- Phải chốt được bằng số tiền cụ thể — nhưng con số "sổ sách" (Bước 6) không được coi là căn cứ cuối cùng: phải đối chiếu lại bằng lợi nhuận **nhân quả** (Bước 7) trước khi kết luận chiến lược nào thực sự đáng triển khai. Tiêu chí thành công thật sự: tìm ra được **ít nhất 1 kịch bản có lợi nhuận nhân quả dương** — trên bộ dữ liệu mock này, chỉ Uplift Targeting làm được điều đó.
- `presentation.html` phải mở được độc lập (self-contained, không cần server) và trình bày được toàn bộ mạch lý luận trên theo phong cách phỏng vấn chuyên nghiệp, bao gồm cả phần "lật lại" kết quả Bước 6 bằng Bước 7 — không chỉ trình bày các con số đẹp mà giấu đi giới hạn phương pháp luận.

## 6. Ghi chú giả định

- Dữ liệu `customer_promo_data.csv` là mock 100%, sinh bởi `00_generate_data.py` với seed cố định (42) — không lấy từ nguồn thật.
- Kênh gửi khuyến mãi giả định là **Zalo ZNS** — chi phí 500 VND/tin nhắn gửi **thành công**, tỷ lệ convert trung bình 5%, lợi nhuận gộp sau cùng (đã trừ chi phí tin) trung bình 100 VND/khách hàng được gửi → suy ra lợi nhuận gộp 12,000 VND/lượt convert. Các con số này do người dùng cung cấp trong quá trình review (2026-07-03), không phải số liệu tự sinh từ `customer_promo_data.csv` hay số liệu ngân hàng thật đã kiểm chứng.
