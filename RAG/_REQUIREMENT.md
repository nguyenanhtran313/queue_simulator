# RAG for queue_simulator — Trợ lý tra cứu tri thức về chính repo này

> **Tên dự án:** `repo-knowledge-RAG`
> **Loại:** Retrieval-Augmented Generation (RAG) — REST API + UI chat đơn giản đi kèm
> **Trạng thái:** MVP (P0→P2) + vòng mở rộng thứ 2 (hybrid search, multi-turn, incremental ingest, eval tự động, UI chat) đã xong, chạy được end-to-end
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
  → ingest.py: parse frontmatter → hash nội dung file (so với index/manifest.json,
    incremental — chỉ re-chunk/re-embed file thay đổi) → chia theo heading (##)
    → semantic chunking (percentile-based, kiểu LangChain SemanticChunker: embed
    từng câu, cắt tại điểm cosine-distance giữa 2 câu liền kề vượt percentile 80,
    ép thêm MIN_CHARS=200/MAX_CHARS=1200, overlap ~1 câu giữa các chunk liền kề)
  → embed bằng Gemini (models/gemini-embedding-001, task_type=RETRIEVAL_DOCUMENT, dim=768)
  → upsert vào Chroma (local, RAG/index/, collection "repo_knowledge") + cập nhật manifest.json

[Câu hỏi] → rag_core.answer(question, top_k, source_filter, history)
  → nếu có history (multi-turn): Gemini flash-lite viết lại câu hỏi follow-up
    ("còn cái kia thì sao?") thành câu hỏi độc lập, dùng câu này cho retrieval+rerank
  → embed câu hỏi (task_type=RETRIEVAL_QUERY)
  → hybrid retrieval: dense (Chroma, top-20) + sparse (BM25 trong bộ nhớ, build từ
    toàn bộ chunk trong collection) → hợp nhất bằng Reciprocal Rank Fusion (k=60)
    (lọc thêm theo source_filter nếu có)
  → rerank: Gemini flash-lite chấm điểm liên quan 0-10 cho từng candidate, lấy top-k
  → nếu điểm rerank cao nhất < 4/10 → trả "không tìm thấy", grounded=false, dừng (không gọi LLM sinh câu trả lời)
  → ngược lại: assemble prompt (system prompt bắt buộc grounded + citation, kèm
    block lịch sử hội thoại nếu có) → Gemini (models/gemini-flash-latest, temperature=0.1)
    sinh câu trả lời có trích dẫn dựa trên CÂU HỎI GỐC của người dùng (không phải bản viết lại)
  → trả {answer, sources (kèm doc_id), grounded}

Mọi lời gọi Gemini (embed/rerank/generate) đều bọc qua with_retry() — exponential
backoff cho lỗi tạm thời (503 UNAVAILABLE / 429 rate limit), 4 lần thử.
```

- **Không dùng LangChain/LlamaIndex** — orchestration tự viết mỏng, đúng quy ước repo.
- **Embedding + rerank + generation đều qua Gemini API** (không cần model local nặng như bge-reranker/torch) — đơn giản hoá so với kế hoạch gốc, đổi lại toàn bộ pipeline đều tốn API call (không có phần "miễn phí chạy local" như bản kế hoạch Data Governance cũ).
- **Hybrid search (dense + BM25 qua `rank_bm25`)**: BM25 build lại trong bộ nhớ mỗi khi process (api.py/query.py) khởi động, từ toàn bộ document/metadata đang có trong Chroma — restart process sau khi `ingest.py` chạy xong để BM25 thấy dữ liệu mới.
- **Multi-turn**: `api.py` giữ lịch sử hội thoại trong bộ nhớ tiến trình theo `session_id` (client tự sinh, gửi kèm mỗi request `/ask`), tối đa `MAX_HISTORY_TURNS=6` lượt gần nhất — mất khi restart server (chưa có persistence). CLI `query.py` giữ history trong biến cục bộ của vòng lặp REPL, gõ `reset` để xoá.

## 4. Cấu trúc thư mục

```
RAG/
├── _REQUIREMENT.md   # file này
├── .env               # GEMINI_API_KEY (không commit — đã thêm vào .gitignore ở root)
├── corpus/            # 10 tài liệu nguồn (.md + frontmatter)
├── ingest.py           # nạp: parse → hash diff (incremental) → semantic chunk → embed → upsert Chroma
├── rag_core.py         # engine dùng chung: answer(question, top_k, source_filter, history)
├── query.py             # CLI hỏi-đáp nhanh, multi-turn qua REPL (gọi rag_core)
├── api.py                # REST API (FastAPI) bọc rag_core → POST /ask, GET /health, POST /session/{id}/reset
├── chat.html              # UI chat single-file (mở thẳng bằng trình duyệt, gọi API qua fetch)
├── eval/
│   ├── golden_qa.jsonl        # bộ câu hỏi mẫu để eval tự động
│   └── run_eval.py             # chạy golden_qa qua rag_core, in + ghi eval/report.json
└── index/                 # vector store Chroma đã build + manifest.json (output, gitignore, không sửa tay)
```

## 5. Hợp đồng REST API (đã triển khai đúng theo bản này)

```
POST /ask
  body:  { "question": "Test_VSF_dinhgia_bds có liên quan gì tới Xanh SM?",
           "top_k": 5,                    # tuỳ chọn, mặc định 5
           "source_filter": ["dinhgia_bds"],  # tuỳ chọn, match theo doc_id/title (substring, không phân biệt hoa thường)
           "session_id": "uuid-tuỳ-client-tự-sinh" }  # tuỳ chọn — có thì nhớ ngữ cảnh multi-turn
  resp:  { "answer": "…câu trả lời có trích dẫn [Tên tài liệu, Mục]…",
           "sources": [
             { "doc_id": "dinhgia_bds", "title": "...", "section": "...", "page": null,
               "url": "Test_VSF_dinhgia_bds/_REQUIREMENT.md" hoặc null nếu nguồn fabricated,
               "snippet": "…280 ký tự đầu của chunk…" }
           ],
           "grounded": true }             # false nếu không tìm thấy trong corpus

POST /session/{session_id}/reset   → { "status": "ok" }   # xoá lịch sử hội thoại của session
GET /health                         → { "status": "ok" | "index_missing", "docs_indexed": 10 }
```

Chạy server: `uvicorn api:app --host 0.0.0.0 --port 8000` (trong thư mục `RAG/`). CORS đang mở `allow_origins=["*"]` để Dify/N8N gọi vào dễ dàng — cân nhắc siết lại nếu deploy ra ngoài mạng nội bộ.

Lịch sử hội thoại theo `session_id` chỉ lưu trong bộ nhớ tiến trình của `api.py` (mất khi restart server) — đủ cho demo/nội bộ, không phải giải pháp production nhiều instance.

## 6. Cách chạy

```
cd RAG
python ingest.py               # incremental: chỉ re-embed file corpus/ thay đổi (dựa vào index/manifest.json)
python ingest.py --rebuild     # build lại toàn bộ collection từ đầu (dùng khi nghi index hỏng/không nhất quán)
python query.py                 # CLI hỏi-đáp nhanh, hỗ trợ multi-turn (gõ "reset" để xoá lịch sử)
uvicorn api:app --host 0.0.0.0 --port 8000   # chạy API cho Dify/N8N/chat.html gọi vào
python eval/run_eval.py          # chạy bộ eval tự động, in kết quả + ghi eval/report.json

# UI chat: mở thẳng RAG/chat.html bằng trình duyệt (cần api.py đang chạy ở localhost:8000,
# hoặc sửa ô "API base URL" trên giao diện nếu server chạy nơi khác)
```

## 7. Đã kiểm thử

Smoke test thủ công (2026-07-03):
- Câu hỏi trong corpus, câu hỏi ngoài corpus, `source_filter`, `GET /health` — xem chi tiết lịch sử git nếu cần.

Eval tự động (2026-07-03, `eval/golden_qa.jsonl`, 18 câu — 15 in-scope theo từng tài liệu + 3 out-of-scope):
- Grounded accuracy: 18/18 (100%) — model từ chối đúng 3 câu ngoài phạm vi, trả lời đúng 15 câu trong phạm vi.
- Doc hit rate: 15/15 (100%) — đúng tài liệu kỳ vọng luôn nằm trong `sources` trả về.
- Chưa dùng RAGAS/LLM-as-judge cho Faithfulness — hiện chỉ đo grounded đúng/sai và có trúng nguồn kỳ vọng hay không (proxy cho Recall@k), không đo chất lượng văn phong câu trả lời.

Multi-turn: test thủ công 2 lượt hỏi liên tiếp qua `rag_core.answer(history=...)` — câu follow-up dùng đại từ ("R2 của nó là bao nhiêu?") được viết lại đúng thành câu hỏi độc lập trước khi retrieval, trả lời đúng ngữ cảnh (LightGBM Regressor, R²=97.3%). Test lại qua `POST /ask` với `session_id` chung cho 2 request — cùng kết quả.

Incremental ingest: chạy `ingest.py` lần đầu (full rebuild, tạo `manifest.json`), chạy lại ngay không sửa gì → in "Không có thay đổi, giữ nguyên index", không gọi API embed nào.

## 8. Việc chưa làm / có thể làm thêm

- Eval dùng RAGAS/LLM-as-judge để đo Faithfulness (mức độ câu trả lời bám sát context) một cách định lượng hơn — hiện `eval/run_eval.py` chỉ đo grounded đúng/sai + doc hit rate.
- Session/history lưu bền (Redis/SQLite) thay vì in-memory — hiện mất lịch sử khi restart `api.py`, không chia sẻ được giữa nhiều instance nếu scale ngang.
- BM25 index tự rebuild khi có ingest mới (hiện phải restart process `api.py`/`query.py` để BM25 thấy dữ liệu mới, vì nó cache trong bộ nhớ theo process).
- Giới hạn dung lượng `SESSIONS` trong `api.py` (hiện không có cơ chế dọn session cũ/hết hạn — chấp nhận được cho demo/nội bộ, cần xem lại nếu public-facing lâu dài).
