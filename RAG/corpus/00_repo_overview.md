---
doc_id: repo_overview
title: "queue_simulator — Tổng quan repo & cấu trúc thư mục"
source: CLAUDE.md
type: real
lang: vi
---

## Repo là gì

`queue_simulator` là một sandbox cá nhân, chứa nhiều dự án con độc lập. Đây không phải một app duy nhất — mỗi thư mục có mục đích và cách chạy riêng biệt, không chia sẻ code hay dependency với nhau.

## Danh sách thư mục con

### Queue Simulator/
Universal Queue Simulator — web app mô phỏng lý thuyết xếp hàng sân bay. `index.html` là single-file React (UMD) + Babel-standalone + Tailwind CDN + Chart.js, không có build step. Chạy bằng cách mở thẳng `index.html` trong trình duyệt.

### Test_VSF_driver_allocation/
Mô phỏng phân bổ tài xế + điều phối xe (Smart Dispatching), là Phase 3 & 4 của case study "Xanh SM" tuyển dụng Data Team. `phase1_simulation.py` chạy simulation, `build_presentation.py` đọc kết quả và sinh `presentation.html`. Dữ liệu mock: `mock_drivers.csv`, `mock_riders.csv`, `realtime_heatmap.csv`. Đây là khu vực đang được sửa tích cực nhất trong repo.

### Test_VSF_forecast_demand/
Dự báo nhu cầu đặt xe theo lưới H3 + LightGBM — là Phase 1 & 2 của cùng case study "Xanh SM". `step1_2_pipeline.py` sinh mock data + train model, `generate_eda.py` vẽ thêm EDA, output vào `output/`, có `Vinsmart_Presentation.html`. Lưu ý: 2 script đang hard-code đường dẫn output tuyệt đối tới máy khác — phải sửa path trước khi chạy lại.

### Test_VSF_dinhgia_bds/
Case study định giá bất động sản tự động (AVM) — không liên quan tới 2 thư mục VSF ở trên dù trùng tiền tố tên. `generate_data.py` sinh `real_estate_valuation_dataset.csv`, `compare_models.py` so sánh 5 thuật toán regression (best: LightGBM, R²≈97.3%).

### Basic ML/
Chuỗi bài tự học ML (case study dự đoán khách hàng ngân hàng phản hồi khuyến mãi), đánh số thứ tự và phải chạy tuần tự vì bài sau dùng output (.pkl, .csv) của bài trước: 01_EDA_and_Stats → 02_KMeans_Segmentation → 03_Logistic_Regression_Benchmark → 04_XGBoost_Production/04b_LightGBM_Production → 05_SHAP_Analysis → 06_Expected_Profit_Calculation → 07_Uplift_Modeling_ROI → 08_Model_Comparison_ROI.

### RAG/
Trợ lý tra cứu tri thức về chính repo này — RAG (Retrieval-Augmented Generation) engine tự build bằng Python, chìa ra REST API (`POST /ask`) để các chatbot ngoài (Dify, N8N) gọi vào hỏi–đáp về nội dung các dự án con trong repo.

## Quy ước chung của repo

- Không có `package.json`/`requirements.txt` chung ở đâu trong repo — mỗi script tự chứa import riêng. Không tự ý `pip install` khi chưa hỏi user.
- Không có test suite hay formatter chính thức.
- File `.csv`/`.png`/`.pkl` trong các thư mục là output đã sinh ra, không phải input cần chỉnh sửa tay.
- `presentation.html` ở mỗi thư mục thường được generate tự động bởi script Python tương ứng — sửa trực tiếp trong HTML sẽ bị ghi đè lần chạy sau.
- File mô tả đề bài/yêu cầu/kế hoạch của mỗi thư mục con luôn đặt tên `_REQUIREMENT.md` (dấu gạch dưới ở đầu để nổi lên đầu danh sách).
- Ngôn ngữ giao tiếp mặc định trong repo này: tiếng Việt.
