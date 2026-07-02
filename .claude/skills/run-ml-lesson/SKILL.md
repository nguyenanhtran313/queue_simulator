---
name: run-ml-lesson
description: Run one or more of the numbered ML learning scripts in "Basic ML", in the correct order. Use when the user asks to run/redo a specific lesson number (e.g. "chạy bài 04"), or to re-run the whole ML learning sequence.
---

Các script trong `Basic ML/` được đánh số theo thứ tự phụ thuộc — bài sau dùng output (`.pkl`, `.csv`) của bài trước:

```
01_EDA_and_Stats.py
02_KMeans_Segmentation.py
03_Logistic_Regression_Benchmark.py
04_XGBoost_Production.py  (hoặc 04b_LightGBM_Production.py — nhánh thay thế)
05_SHAP_Analysis.py       (có bản riêng cho LightGBM: "05_SHAP_Analysis LightBGM.py")
06_Expected_Profit_Calculation.py
07_Uplift_Modeling_ROI.py
```

Cách thực hiện:

1. Nếu user chỉ định một số bài cụ thể (ví dụ `/run-ml-lesson 04`), chỉ chạy đúng script đó bằng `python <ten_file>.py` trong thư mục `Basic ML/` (nhớ quote đường dẫn vì tên thư mục có khoảng trắng) — nhưng trước tiên kiểm tra output của các bài trước đó (file `.pkl`/`.csv` tương ứng) đã tồn tại chưa; nếu chưa, cảnh báo user và hỏi có muốn chạy lại từ đầu chuỗi không.
2. Nếu user không chỉ định số bài, hoặc muốn "chạy lại toàn bộ", chạy tuần tự từ `01` đến `07` theo đúng thứ tự trên.
3. Khi có 2 phiên bản của cùng bước (04 vs 04b, hoặc 05 thường vs 05 LightGBM), hỏi user muốn chạy nhánh XGBoost hay LightGBM trước khi chạy, trừ khi họ đã nói rõ trong yêu cầu.
4. Báo lại các file output mới được sinh ra (`.png`, `.pkl`, `.csv`) sau khi chạy xong.
