# queue_simulator — ghi chú cho Claude Code

Repo này là một **sandbox cá nhân**, chứa nhiều dự án con độc lập. Không coi đây là một app duy nhất — mỗi thư mục có mục đích và cách chạy riêng.

## Cấu trúc thư mục

| Thư mục | Nội dung | Cách chạy |
|---|---|---|
| `Queue Simulator/` | **Universal Queue Simulator** — web app mô phỏng lý thuyết xếp hàng sân bay. `index.html` là single-file React (UMD) + Babel-standalone + Tailwind CDN + Chart.js, **không có build step**. `implementation_plan.md` là tài liệu thiết kế bổ sung, `_REQUIREMENT.md` là đề bài/kế hoạch triển khai gốc. `presentation.html`/`index_backup.html`/`index_final_backup.html` là các bản lưu/trình bày. | Mở thẳng `index.html` bằng trình duyệt. |
| `Test_VSF_driver_allocation/` | Mô phỏng phân bổ tài xế + điều phối xe (Smart Dispatching), là **Phase 3 & 4** của case study "Xanh SM" tuyển dụng Data Team — xem `_REQUIREMENT.md`. `phase1_simulation.py` chạy simulation, `build_presentation.py` đọc kết quả và sinh `presentation.html`. Dữ liệu mock: `mock_drivers.csv`, `mock_riders.csv`, `realtime_heatmap.csv`. **Đây là khu vực đang được sửa tích cực nhất.** | `python phase1_simulation.py` rồi `python build_presentation.py` |
| `Test_VSF_forecast_demand/` | Dự báo nhu cầu đặt xe theo lưới H3 + LightGBM — là **Phase 1 & 2** của cùng case study "Xanh SM" nói trên (xem `_REQUIREMENT.md` để rõ mối liên hệ với `Test_VSF_driver_allocation/`). `step1_2_pipeline.py` sinh mock data + train model, `generate_eda.py` vẽ thêm EDA, output vào `output/`, có `Vinsmart_Presentation.html`. ⚠️ 2 script đang hard-code đường dẫn output tuyệt đối tới máy khác — phải sửa path trước khi chạy lại. | `python step1_2_pipeline.py` rồi `python generate_eda.py` |
| `Test_VSF_dinhgia_bds/` | Case study định giá bất động sản tự động (AVM) — **không liên quan** tới 2 thư mục VSF ở trên dù trùng tiền tố tên, xem `_REQUIREMENT.md`. `generate_data.py` sinh `real_estate_valuation_dataset.csv`, `compare_models.py` so sánh 5 thuật toán regression (best: LightGBM, R²≈97.3%). | `python generate_data.py` rồi `python compare_models.py` |
| `Basic ML/` | Chuỗi bài tự học ML (case study dự đoán khách hàng ngân hàng phản hồi khuyến mãi, 10,000 dòng mock — xem `_REQUIREMENT.md`), **đánh số thứ tự và phải chạy tuần tự** vì bài sau dùng output (`.pkl`, `.csv`, `.json`) của bài trước: `00_generate_data` → `01_EDA_and_Stats` → `02_KMeans_Segmentation` → `03_Logistic_Regression_Benchmark` → `04_XGBoost_Production` **và** `04b_LightGBM_Production` (cả 2, không phải chọn 1) → `04c_Model_Comparison` (so sánh 2 model) → `05_SHAP_Analysis`/`05b_SHAP_Analysis_LightGBM` → `06_Expected_Profit_Calculation` → `07_Uplift_Modeling_ROI` **và** `07b_Uplift_Modeling_ROI_LightGBM` (S-learner XGBoost vs LightGBM, quyết định chiến lược targeting cuối cùng theo lợi nhuận nhân quả) → `build_presentation.py` (đọc toàn bộ artifact, ra `presentation.html` phong cách Google Analytics). | `python 0X_Ten_Bai.py` theo đúng thứ tự, kết thúc bằng `python build_presentation.py` |

## Quy ước chung

- Không có `package.json`/`requirements.txt` ở đâu trong repo — mỗi script tự chứa import riêng (pandas, sklearn, xgboost, lightgbm, shap, h3...). Nếu thiếu package, hỏi user trước khi cài, không tự ý `pip install`.
- Không có test suite hay formatter chính thức. Đừng đề xuất thêm CI/lint framework trừ khi được yêu cầu.
- File `.csv`/`.png`/`.pkl` trong các thư mục là **output đã sinh ra**, không phải input cần chỉnh sửa tay. Khi cần xem nội dung CSV lớn, dùng `pandas.read_csv(...).head()` thay vì đọc toàn bộ file.
- `presentation.html` ở mỗi thư mục thường là **file được generate tự động** bởi script Python tương ứng (vd `build_presentation.py`) — sửa trực tiếp trong HTML sẽ bị ghi đè lần chạy sau; nên sửa ở script sinh ra nó.
- **File mô tả đề bài/yêu cầu/kế hoạch của mỗi thư mục con luôn đặt tên `_REQUIREMENT.md`** (dấu gạch dưới ở đầu để file luôn nổi lên đầu danh sách, dễ tìm khi mở thư mục). Khi review một thư mục con và không rõ đề bài gốc, tái dựng lại yêu cầu từ code/output có sẵn rồi ghi ra `_REQUIREMENT.md` theo đúng quy tắc đặt tên này — không đặt tên khác (vd `REQUIREMENT.md`, `requirements.md`).
- Ngôn ngữ giao tiếp mặc định trong repo này: **tiếng Việt**.
