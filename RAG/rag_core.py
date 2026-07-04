"""RAG engine dùng chung cho query.py (CLI) và api.py (REST).

Hàm chính: answer(question, top_k, source_filter, history) -> {answer, sources, grounded}
"""
import json
import os
import re
import time
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from rank_bm25 import BM25Okapi

HERE = Path(__file__).parent
INDEX_DIR = HERE / "index"
COLLECTION_NAME = "repo_knowledge"

EMBED_MODEL = "models/gemini-embedding-001"
GEN_MODEL = "models/gemini-flash-latest"
RERANK_MODEL = "models/gemini-flash-lite-latest"

RETRIEVE_TOP_N = 20
DEFAULT_TOP_K = 5
GROUNDED_SCORE_THRESHOLD = 4  # thang 0-10, dưới ngưỡng này coi như "không tìm thấy"
RRF_K = 60  # hằng số chuẩn của Reciprocal Rank Fusion
MAX_HISTORY_TURNS = 6

SYSTEM_PROMPT = """Bạn là trợ lý tra cứu tri thức về repo "queue_simulator".
Chỉ được trả lời dựa trên các đoạn CONTEXT được cung cấp bên dưới — tuyệt đối không bịa thêm thông tin ngoài context.
Nếu context không đủ để trả lời, hãy nói rõ "Không tìm thấy thông tin này trong tài liệu hiện có." và gợi ý người dùng hỏi lại theo hướng khác.
Trả lời bằng đúng ngôn ngữ của câu hỏi (Việt hoặc Anh).
Sau mỗi ý lấy từ context, chèn trích dẫn dạng [Tên tài liệu, Mục] khớp với tiêu đề/section được cho trong context.
Văn phong ngắn gọn, đi thẳng vào trọng tâm."""

def with_retry(fn, *args, retries=4, base_delay=2.0, **kwargs):
    """Retry với exponential backoff cho lỗi tạm thời (503 quá tải / 429 rate limit)."""
    for attempt in range(retries):
        try:
            return fn(*args, **kwargs)
        except genai_errors.ServerError:
            if attempt == retries - 1:
                raise
            time.sleep(base_delay * (2 ** attempt))
        except genai_errors.ClientError as e:
            if getattr(e, "code", None) == 429 and attempt < retries - 1:
                time.sleep(base_delay * (2 ** attempt))
            else:
                raise


load_dotenv(HERE / ".env")
_client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
_collection = None
_bm25_index = None
_bm25_chunks = None  # list song song với _bm25_index: [{"id", "text", "metadata"}, ...]


def get_collection():
    global _collection
    if _collection is None:
        if not INDEX_DIR.exists():
            raise RuntimeError("Chưa có index — chạy `python ingest.py` trước.")
        db_client = chromadb.PersistentClient(path=str(INDEX_DIR))
        _collection = db_client.get_collection(COLLECTION_NAME)
    return _collection


def tokenize(text: str):
    return re.findall(r"[\wÀ-ỹ]+", text.lower())


def get_bm25_index():
    """Build BM25 index trong bộ nhớ từ toàn bộ chunk hiện có trong Chroma.
    Cache theo process — gọi lại ingest.py rồi restart process (api.py/query.py)
    để BM25 thấy dữ liệu mới."""
    global _bm25_index, _bm25_chunks
    if _bm25_index is None:
        collection = get_collection()
        data = collection.get(include=["documents", "metadatas"])
        _bm25_chunks = [
            {"id": id_, "text": doc, "metadata": meta}
            for id_, doc, meta in zip(data["ids"], data["documents"], data["metadatas"])
        ]
        tokenized = [tokenize(c["text"]) for c in _bm25_chunks]
        _bm25_index = BM25Okapi(tokenized)
    return _bm25_index, _bm25_chunks


def embed_query(text: str):
    resp = with_retry(
        _client.models.embed_content,
        model=EMBED_MODEL,
        contents=[text],
        config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY", output_dimensionality=768),
    )
    return resp.embeddings[0].values


def retrieve(question: str, top_n: int = RETRIEVE_TOP_N, source_filter=None):
    """Hybrid retrieval: dense (Gemini embedding qua Chroma) + sparse (BM25),
    kết hợp bằng Reciprocal Rank Fusion (RRF) trước khi đưa sang bước rerank."""
    collection = get_collection()
    query_emb = embed_query(question)
    dense_res = collection.query(query_embeddings=[query_emb], n_results=top_n)
    dense_ids = dense_res["ids"][0]
    dense_lookup = {
        id_: {"text": doc, "metadata": meta}
        for id_, doc, meta in zip(dense_ids, dense_res["documents"][0], dense_res["metadatas"][0])
    }

    bm25_index, bm25_chunks = get_bm25_index()
    bm25_scores = bm25_index.get_scores(tokenize(question))
    bm25_ranked = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)
    bm25_ranked = [i for i in bm25_ranked if bm25_scores[i] > 0][:top_n]

    fused_scores = {}
    all_chunks = dict(dense_lookup)
    for rank, id_ in enumerate(dense_ids):
        fused_scores[id_] = fused_scores.get(id_, 0.0) + 1.0 / (RRF_K + rank + 1)
    for rank, i in enumerate(bm25_ranked):
        c = bm25_chunks[i]
        fused_scores[c["id"]] = fused_scores.get(c["id"], 0.0) + 1.0 / (RRF_K + rank + 1)
        all_chunks.setdefault(c["id"], {"text": c["text"], "metadata": c["metadata"]})

    ranked_ids = sorted(fused_scores, key=lambda id_: fused_scores[id_], reverse=True)[:top_n]
    candidates = [
        {"text": all_chunks[id_]["text"], "metadata": all_chunks[id_]["metadata"], "fused_score": fused_scores[id_]}
        for id_ in ranked_ids
    ]

    if source_filter:
        needles = [s.lower() for s in source_filter]
        candidates = [
            c for c in candidates
            if any(n in c["metadata"]["doc_id"].lower() or n in c["metadata"]["title"].lower() for n in needles)
        ]
    return candidates


def rerank(question: str, candidates: list, top_k: int = DEFAULT_TOP_K):
    """Dùng Gemini (flash-lite) chấm điểm liên quan 0-10 cho từng candidate,
    tránh phải cài cross-encoder cục bộ (bge-reranker cần torch, khá nặng)."""
    if not candidates:
        return []

    passages = "\n\n".join(
        f"[{i}] ({c['metadata']['title']} — {c['metadata']['section']}): {c['text'][:500]}"
        for i, c in enumerate(candidates)
    )
    prompt = f"""Câu hỏi: "{question}"

Dưới đây là danh sách đoạn văn (đánh số [0], [1], ...). Chấm điểm mức độ liên quan của TỪNG đoạn với câu hỏi, thang điểm 0-10 (0 = hoàn toàn không liên quan, 10 = trả lời trực tiếp câu hỏi).

{passages}

Chỉ trả về JSON thuần dạng {{"scores": [{{"index": 0, "score": 7}}, ...]}} cho đủ tất cả {len(candidates)} đoạn, không giải thích thêm."""

    resp = with_retry(
        _client.models.generate_content,
        model=RERANK_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.0, response_mime_type="application/json"),
    )
    try:
        parsed = json.loads(resp.text)
        scores = {item["index"]: item["score"] for item in parsed["scores"]}
    except (json.JSONDecodeError, KeyError, TypeError):
        # fallback: giữ nguyên thứ tự dense retrieval nếu LLM rerank lỗi format
        scores = {i: (10 - i) for i in range(len(candidates))}

    for i, c in enumerate(candidates):
        c["rerank_score"] = scores.get(i, 0)

    candidates.sort(key=lambda c: c["rerank_score"], reverse=True)
    return candidates[:top_k]


def build_context(chunks: list):
    return "\n\n---\n\n".join(
        f"[Nguồn: {c['metadata']['title']}, Mục: {c['metadata']['section']}]\n{c['text']}"
        for c in chunks
    )


def build_history_block(history: list):
    if not history:
        return ""
    lines = []
    for turn in history[-MAX_HISTORY_TURNS:]:
        lines.append(f"Người dùng: {turn['question']}")
        lines.append(f"Trợ lý: {turn['answer']}")
    return "LỊCH SỬ HỘI THOẠI TRƯỚC ĐÓ (để hiểu ngữ cảnh câu hỏi hiện tại):\n" + "\n".join(lines) + "\n\n"


def rewrite_standalone_question(question: str, history: list):
    """Nếu có lịch sử hội thoại, viết lại câu hỏi follow-up (vd 'còn cái kia thì sao?')
    thành câu hỏi độc lập để retrieval tìm đúng tài liệu."""
    if not history:
        return question

    history_text = "\n".join(
        f"Người dùng: {t['question']}\nTrợ lý: {t['answer']}" for t in history[-MAX_HISTORY_TURNS:]
    )
    prompt = f"""Lịch sử hội thoại:
{history_text}

Câu hỏi tiếp theo của người dùng: "{question}"

Nếu câu hỏi tiếp theo phụ thuộc vào ngữ cảnh hội thoại trước (vd dùng đại từ, nhắc "cái kia", "còn...thì sao"), hãy viết lại thành một câu hỏi độc lập, đầy đủ ngữ cảnh, giữ nguyên ngôn ngữ gốc. Nếu câu hỏi đã độc lập rồi thì trả lại y nguyên. Chỉ trả về câu hỏi đã viết lại, không giải thích thêm."""

    resp = with_retry(
        _client.models.generate_content,
        model=RERANK_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.0),
    )
    rewritten = resp.text.strip()
    return rewritten or question


def generate_answer(question: str, chunks: list, history: list = None):
    context = build_context(chunks)
    history_block = build_history_block(history)
    prompt = f"{history_block}CONTEXT:\n{context}\n\nCÂU HỎI HIỆN TẠI: {question}"
    resp = with_retry(
        _client.models.generate_content,
        model=GEN_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT, temperature=0.1),
    )
    return resp.text.strip()


def build_sources(chunks: list):
    sources = []
    seen = set()
    for c in chunks:
        meta = c["metadata"]
        key = (meta["doc_id"], meta["section"])
        if key in seen:
            continue
        seen.add(key)
        sources.append({
            "doc_id": meta["doc_id"],
            "title": meta["title"],
            "section": meta["section"],
            "page": None,
            "url": meta["source"] if meta.get("type") == "real" else None,
            "snippet": c["text"][:280],
        })
    return sources


def answer(question: str, top_k: int = DEFAULT_TOP_K, source_filter=None, history: list = None):
    retrieval_question = rewrite_standalone_question(question, history)
    candidates = retrieve(retrieval_question, source_filter=source_filter)
    if not candidates:
        return {
            "answer": "Không tìm thấy thông tin này trong tài liệu hiện có.",
            "sources": [],
            "grounded": False,
        }

    top_chunks = rerank(retrieval_question, candidates, top_k=top_k)
    best_score = top_chunks[0]["rerank_score"] if top_chunks else 0

    if best_score < GROUNDED_SCORE_THRESHOLD:
        return {
            "answer": "Không tìm thấy thông tin này trong tài liệu hiện có. Bạn thử hỏi lại theo hướng khác hoặc nêu rõ tên dự án con (vd Queue Simulator, Basic ML, Test_VSF_driver_allocation...) xem sao.",
            "sources": [],
            "grounded": False,
        }

    relevant_chunks = [c for c in top_chunks if c["rerank_score"] >= GROUNDED_SCORE_THRESHOLD]
    answer_text = generate_answer(question, relevant_chunks, history=history)
    return {
        "answer": answer_text,
        "sources": build_sources(relevant_chunks),
        "grounded": True,
    }
