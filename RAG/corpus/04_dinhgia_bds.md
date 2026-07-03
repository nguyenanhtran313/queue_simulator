---
doc_id: dinhgia_bds
title: "Test_VSF_dinhgia_bds — Định giá Bất động sản tự động (AVM)"
source: "Test_VSF_dinhgia_bds/_REQUIREMENT.md"
type: real
lang: vi
---

## Bối cảnh

Xây dựng mô hình Định giá Bất động sản tự động (Automated Valuation Model - AVM) cho căn hộ chung cư, dựa trên dữ liệu giao dịch lịch sử mô phỏng. Đây là dạng bài toán thường gặp ở công ty proptech muốn cho phép người dùng tự ước tính giá nhà online. **Không liên quan tới case study Xanh SM** dù tên thư mục có tiền tố `Test_VSF_` giống 2 thư mục kia — không có bằng chứng cùng một case study.

## Dữ liệu

`real_estate_valuation_dataset.csv` — 5,000 giao dịch mô phỏng do `generate_data.py` sinh ra, gồm: đặc điểm cơ bản (diện tích, phòng ngủ, phòng tắm), dữ liệu không gian (tầng, hướng, khoảng cách tới trung tâm/bệnh viện/trường/siêu thị), dữ liệu phi cấu trúc đại diện (URL ảnh giả, `image_quality_score`), đặc điểm khác (tuổi công trình, nội thất, pháp lý), biến động thị trường theo thời gian (market sentiment, lãi suất). Biến mục tiêu: `price_vnd`.

## Phương pháp

`compare_models.py`: tiền xử lý (tách năm/tháng, loại cột không mang tín hiệu), chuẩn hóa + one-hot encode, chia train/test 80/20, huấn luyện và so sánh **5 thuật toán regression**: Linear Regression, Random Forest, Gradient Boosting, XGBoost, LightGBM. Đánh giá bằng MAE, RMSE, R², cùng 2 chỉ số "độ chính xác kinh doanh": % căn đoán lệch giá không quá 5%, không quá 10%.

## Kết quả

**LightGBM Regressor** tốt nhất: R² = 97.3%, MAE ≈ 149 triệu VND, thời gian train chỉ 0.23 giây. Diễn giải kinh doanh: nhà 4 tỷ thì AI đưa ra khoảng giá 3.85–4.15 tỷ.

## Lưu ý kỹ thuật quan trọng

`image_quality_score` không hề được dùng để tính `price_vnd` trong `generate_data.py` — biến "chất lượng ảnh" chỉ tồn tại như một cột dữ liệu, chưa thực sự ảnh hưởng tới giá mô phỏng lẫn model dự đoán. `xgboost`/`lightgbm` là optional (try/except ImportError) — nếu máy không có 2 package này, script vẫn chạy nhưng chỉ so sánh 3 model, sẽ không ra được kết quả "LightGBM tốt nhất". Không có bước lưu model ra `.pkl` — script chỉ in kết quả ra console.
