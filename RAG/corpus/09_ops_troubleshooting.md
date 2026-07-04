---
doc_id: ops_troubleshooting
title: "Vận hành & Khắc phục sự cố thường gặp"
source: "fabricated (nội dung minh hoạ do RAG demo tự soạn, không phải tài liệu gốc)"
type: fabricated
lang: vi
---

## Lỗi thiếu file .pkl khi chạy Basic ML/05_SHAP_Analysis.py hoặc 06_Expected_Profit_Calculation.py

Hai script này dùng `joblib.load()` để nạp lại model đã train từ `04_XGBoost_Production.py` (hoặc bản `04b_LightGBM_Production.py`). Nếu chưa chạy Bước 4 trước, sẽ báo lỗi không tìm thấy file `04_xgboost_model.pkl`/`04b_lightgbm_model.pkl`. Cách khắc phục: chạy `python 04_XGBoost_Production.py` (hoặc `04b_LightGBM_Production.py`) trước, rồi mới chạy Bước 5/6.

## Lỗi đường dẫn khi chạy Test_VSF_forecast_demand

`step1_2_pipeline.py` và `generate_eda.py` đang hard-code đường dẫn tuyệt đối `c:\_Antigravity\_AG_playground\Test\output\...`, khác với vị trí thực tế của thư mục `output/` trong repo hiện tại. Trước khi chạy lại trên máy khác, cần sửa các đường dẫn này thành đường dẫn tương đối hoặc dùng `os.path.dirname(__file__)` để script tự tìm đúng thư mục của chính nó.

## Test_VSF_dinhgia_bds/compare_models.py chạy nhưng không thấy LightGBM trong kết quả so sánh

`xgboost` và `lightgbm` được import dạng optional (bọc trong `try/except ImportError`) trong `compare_models.py`. Nếu máy chưa cài 2 package này, script vẫn chạy được nhưng chỉ so sánh được 3 thuật toán (Linear Regression, Random Forest, Gradient Boosting) — sẽ không tái hiện được kết quả "LightGBM tốt nhất, R²=97.3%" đã ghi nhận trong comment cuối file. Cách khắc phục: cài `xgboost` và `lightgbm` trước khi chạy (hỏi user trước khi tự ý `pip install`, theo quy ước repo).

## RAG trả lời "không tìm thấy trong tài liệu" dù câu hỏi có vẻ liên quan

Điều này có thể xảy ra khi: (1) câu hỏi dùng thuật ngữ quá khác với corpus (thử diễn đạt lại), (2) `top_k`/ngưỡng rerank đang lọc quá chặt, hoặc (3) thông tin thực sự chưa có trong `RAG/corpus/` — cần bổ sung tài liệu mới rồi chạy lại `python ingest.py`. Đây là hành vi **được thiết kế có chủ đích** để chống hallucination (bịa đặt câu trả lời), không phải lỗi.

## API RAG (`api.py`) trả lỗi 500 khi gọi POST /ask

Kiểm tra: (1) biến môi trường `GEMINI_API_KEY` trong `RAG/.env` có tồn tại và hợp lệ không, (2) đã chạy `python ingest.py` để tạo index tại `RAG/index/` chưa — nếu chưa, `rag_core.py` sẽ không có vector store để truy vấn, (3) log lỗi cụ thể ở console chạy `uvicorn`.
