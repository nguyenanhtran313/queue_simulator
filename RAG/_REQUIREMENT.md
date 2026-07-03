# RAG for queue_simulator — Trợ lý tra cứu tri thức về chính repo này

> **Tên dự án:** `repo-knowledge-RAG`
> **Loại:** Retrieval-Augmented Generation (RAG) — API tra cứu, không có UI riêng
> **Trạng thái:** Đã triển khai MVP (P0→P2 xong), chạy được end-to-end
> **Đề bài gốc:** ban đầu là bản kế hoạch RAG cho domain "Data Governance" (xem lịch sử git nếu cần đối chiếu). Đã **chốt lại đề bài** theo yêu cầu trực tiếp của user (2026-07-03): thu hẹp phạm vi thành RAG tra cứu thông tin về **chính các dự án con trong repo `queue_simulator`**, mục đích chính là chìa REST API ra cho chatbot ngoài (Dify, N8N) gọi vào lấy context để trả lời người dùng.

---

## 1. Mục tiêu

1. Trả lời câu hỏi về các dự án con trong repo (Queue Simulator, Test_VSF_driver_allocation, Test_VSF_forecast_demand, Test_VSF_dinhgia_bds, Basic ML...) bằng tiếng Việt/Anh, **grounded** trên corpus đã nạp, kèm trích dẫn `[Tên tài liệu, Mục]`.
2. Từ chối trả lời ("Không tìm thấy thông tin này trong tài liệu hiện có") khi câu hỏi nằm ngoài corpus — không bịa.
3. Chìa REST API (`POST /ask`, `GET /health`) để Dify/N8N/chatbot khác gọi vào lấy context.

## 2. Corpus (`RAG/corpus/`)

Corpus gồm 10 file Markdown, mỗi file có YAML frontmatter `{doc_id, title, source, type, lang}`, `type` là `real` hoặc `fabricated`:

| File | type | Nội dung |
|---|---|---|
| `00_repo_overview.md` | real | Tổng hợp từ `CLAUDE.md` gốc — cấu trúc thư mục & quy ước chung |
| `01_queue_simulator.md` | real | Từ `Queue Simulator/_REQUIREMENT.md` |
| `02_driver_allocation.md` | real | Từ `Test_VSF_driver_allocation/_REQUIREMENT.md` |
| `03_forecast_demand.md` | real | Từ `Test_VSF_forecast_demand/_REQUIREMENT.md` |
| `04_dinhgia_bds.md` | real | Từ `Test_VSF_dinhgia_bds/_REQUIREMENT.md` |
| `05_basic_ml.md` | real | Từ `Basic ML/_REQUIREMENT.md` |
| `06_faq.md` | fabricated | FAQ nội bộ minh hoạ do RAG tự soạn |
| `07_glossary.md` | fabricated | Glossary thuật ngữ kỹ thuật (H3, AVM, SHAP, Uplift Modeling...) |
| `08_changelog.md` | fabricated | Changelog minh hoạ các mốc phát triển |
| `09_ops_troubleshooting.md` | fabricated | Vận hành & khắc phục sự cố thường gặp |

Các file `type: fabricated` là nội dung **bịa thêm có chủ đích** (theo yêu cầu user) để có đủ dữ liệu đa dạng kiểm thử chunking/retrieval/rerank — không phải tài liệu gốc của dự án. Khi trả lời, RAG vẫn trích dẫn các nguồn này bình thường (vì với client gọi API, đây là một phần "tài liệu đã nạp" hợp lệ), nhưng `sources[].url` chỉ được điền cho nguồn `type: real` (trỏ về file thật trong repo); nguồn `fabricated` có `url: null` để phân biệt.

Muốn thêm tài liệu: thêm file `.md` mới vào `corpus/` (đúng format frontmatter) rồi chạy lại `python ingest.py`.

## 3. Kiến trúc đã triển khai

```
corpus/*.md
  → ingest.py: parse frontmatter → chia theo heading (##) → semantic chunking
    (percentile-based, kiểu LangChain SemanticChunker: embed từng câu, cắt tại
    điểm cosine-distance giữa 2 câu liền kề vượt percentile 80, ép thêm
    MIN_CHARS=200/MAX_CHARS=1200, overlap ~1 câu giữa các chunk liền kề)
  → embed bằng Gemini (models/gemini-embedding-001, task_type=RETRIEVAL_DOCUMENT, dim=768)
  → lưu vào Chroma (local, RAG/index/, collection "repo_knowledge")

[Câu hỏi] → rag_core.answer()
  → embed câu hỏi (task_type=RETRIEVAL_QUERY)
  → dense retrieval top-20 từ Chroma (lọc thêm theo source_filter nếu có)
  → rerank: Gemini flash-lite chấm điểm liên quan 0-10 cho từng candidate, lấy top-k
  → nếu điểm rerank cao nhất < 4/10 → trả "không tìm thấy", grounded=false, dừng (không gọi LLM sinh câu trả lời)
  → ngược lại: assemble prompt (system prompt bắt buộc grounded + citation) → Gemini
    (models/gemini-flash-latest, temperature=0.1) sinh câu trả lời có trích dẫn
  → trả {answer, sources, grounded}
```

- **Không dùng LangChain/LlamaIndex** — orchestration tự viết mỏng, đúng quy ước repo.
- **Embedding + rerank + generation đều qua Gemini API** (không cần model local nặng như bge-reranker/torch) — đơn giản hoá so với kế hoạch gốc, đổi lại toàn bộ pipeline đều tốn API call (không có phần "miễn phí chạy local" như bản kế hoạch Data Governance cũ).
- **Không có hybrid BM25** ở bản MVP này — chỉ dense retrieval + LLM rerank. Có thể bổ sung sau nếu cần.

## 4. Cấu trúc thư mục

```
RAG/
├── _REQUIREMENT.md   # file này
├── .env               # GEMINI_API_KEY (không commit — đã thêm vào .gitignore ở root)
├── corpus/            # 10 tài liệu nguồn (.md + frontmatter)
├── ingest.py           # nạp: parse → semantic chunk → embed → lưu Chroma
├── rag_core.py         # engine dùng chung: answer(question, top_k, source_filter)
├── query.py             # CLI hỏi-đáp nhanh (gọi rag_core)
├── api.py                # REST API (FastAPI) bọc rag_core → POST /ask, GET /health
└── index/                 # vector store Chroma đã build (output, gitignore, không sửa tay)
```

## 5. Hợp đồng REST API (đã triển khai đúng theo bản này)

```
POST /ask
  body:  { "question": "Test_VSF_dinhgia_bds có liên quan gì tới Xanh SM?",
           "top_k": 5,                    # tuỳ chọn, mặc định 5
           "source_filter": ["dinhgia_bds"] }  # tuỳ chọn, match theo doc_id/title (substring, không phân biệt hoa thường)
  resp:  { "answer": "…câu trả lời có trích dẫn [Tên tài liệu, Mục]…",
           "sources": [
             { "title": "...", "section": "...", "page": null,
               "url": "Test_VSF_dinhgia_bds/_REQUIREMENT.md" hoặc null nếu nguồn fabricated,
               "snippet": "…280 ký tự đầu của chunk…" }
           ],
           "grounded": true }             # false nếu không tìm thấy trong corpus

GET /health   → { "status": "ok" | "index_missing", "docs_indexed": 10 }
```

Chạy server: `uvicorn api:app --host 0.0.0.0 --port 8000` (trong thư mục `RAG/`). CORS đang mở `allow_origins=["*"]` để Dify/N8N gọi vào dễ dàng — cân nhắc siết lại nếu deploy ra ngoài mạng nội bộ.

## 6. Cách chạy

```
cd RAG
python ingest.py     # build lại index mỗi khi corpus/ thay đổi
python query.py       # test nhanh qua CLI
uvicorn api:app --host 0.0.0.0 --port 8000   # chạy API cho Dify/N8N gọi vào
```

## 7. Đã kiểm thử (smoke test thủ công, 2026-07-03)

- Câu hỏi trong corpus (Queue Simulator có cần Node.js không? / khác biệt driver_allocation vs forecast_demand? / Basic ML dùng gì để giải thích model?) → trả lời đúng, có trích dẫn, `grounded: true`.
- Câu hỏi ngoài corpus ("Giá cổ phiếu Apple hôm nay bao nhiêu?") → từ chối đúng, `grounded: false`, không bịa.
- `source_filter: ["dinhgia_bds"]` → chỉ trả nguồn từ đúng tài liệu được lọc.
- `GET /health` → `{"status": "ok", "docs_indexed": 10}`.

Chưa có bộ eval tự động (golden Q&A / RAGAS) — nếu cần đo Recall@k/Faithfulness một cách hệ thống, đây là việc nên làm tiếp theo.

## 8. Việc chưa làm / có thể làm thêm (không nằm trong MVP đã chốt)

- Hybrid search (dense + BM25).
- UI chat (Streamlit/Gradio hay single-file HTML).
- Eval tự động (`eval/golden_qa.jsonl` + RAGAS hoặc LLM-as-judge).
- Multi-turn conversation (nhớ ngữ cảnh phiên) — hiện `POST /ask` là stateless, mỗi câu hỏi độc lập.
- Incremental ingest (hiện `ingest.py` xoá và build lại toàn bộ collection mỗi lần chạy).
