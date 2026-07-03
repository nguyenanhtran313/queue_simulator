---
name: run-ml-lesson
description: Run one or more of the numbered ML learning scripts in "Basic ML", in the correct order. Use when the user asks to run/redo a specific lesson number (e.g. "chạy bài 04"), or to re-run the whole ML learning sequence.
---

Các script trong `Basic ML/` được đánh số theo thứ tự phụ thuộc — bài sau dùng output (`.pkl`, `.csv`, `.json`) của bài trước:

```
00_generate_data.py               (sinh customer_promo_data.csv, 10,000 dong, seed=42)
01_EDA_and_Stats.py
02_KMeans_Segmentation.py
03_Logistic_Regression_Benchmark.py (sinh 03_logreg_model.pkl)
04_XGBoost_Production.py          va 04b_LightGBM_Production.py (ca 2, khong phai chon 1)
04c_Model_Comparison.py           (so sanh XGBoost vs LightGBM vs benchmark — can chay ca 04 va 04b truoc)
05_SHAP_Analysis.py               (XGBoost)  va  05b_SHAP_Analysis_LightGBM.py  (LightGBM)
06_Expected_Profit_Calculation.py (can ca 03_logreg_model.pkl, 04_xgboost_model.pkl, 04b_lightgbm_model.pkl —
                                    o muc chi phi gia dinh hien tai, 3 model gan nhu hoi tu (khong tao khac
                                    biet loi nhuan dang ke) — buoc quyet dinh targeting thuc su la 07/07b)
07_Uplift_Modeling_ROI.py         va 07b_Uplift_Modeling_ROI_LightGBM.py (ca 2, S-learner XGBoost vs LightGBM —
                                    day moi la buoc quyet dinh chien luoc targeting cuoi cung theo LOI NHUAN
                                    NHAN QUA, khac voi model co ROC-AUC cao nhat o 04c)
build_presentation.py             (buoc cuoi — doc toan bo artifact 00-07b, khong train lai, ra presentation.html)
```

Cách thực hiện:

1. Nếu user chỉ định một số bài cụ thể (ví dụ `/run-ml-lesson 04`), chỉ chạy đúng script đó bằng `python <ten_file>.py` trong thư mục `Basic ML/` (nhớ quote đường dẫn vì tên thư mục có khoảng trắng) — nhưng trước tiên kiểm tra output của các bài trước đó (file `.pkl`/`.csv`/`.json` tương ứng) đã tồn tại chưa; nếu chưa, cảnh báo user và hỏi có muốn chạy lại từ đầu chuỗi không.
2. Nếu user không chỉ định số bài, hoặc muốn "chạy lại toàn bộ", chạy tuần tự từ `00` đến `07b` rồi `build_presentation.py` theo đúng thứ tự trên.
3. Bài 04 và 04b **không phải 2 nhánh thay thế** — cả 2 đều cần chạy (04c/06/build_presentation.py đều cần cả 2 model). Tương tự 05/05b và 07/07b đều nên chạy cả cặp để có đủ dữ liệu so sánh 2 base learner.
4. Báo lại các file output mới được sinh ra (`.png`, `.pkl`, `.csv`, `.json`, `presentation.html`) sau khi chạy xong.
