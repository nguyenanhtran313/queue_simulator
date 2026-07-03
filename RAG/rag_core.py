"""RAG engine dùng chung cho query.py (CLI) và api.py (REST).

Hàm chính: answer(question, top_k, source_filter) -> {answer, sources, grounded}
"""
import json
import os
import re
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from google import genai
from google.genai import types

HERE = Path(__file__).parent
INDEX_DIR = HERE / "index"
COLLECTION_NAME = "repo_knowledge"

EMBED_MODEL = "models/gemini-embedding-001"
GEN_MODEL = "models/gemini-flash-latest"
RERANK_MODEL = "models/gemini-flash-lite-latest"

RETRIEVE_TOP_N = 20
DEFAULT_TOP_K = 5
GROUNDED_SCORE_THRESHOLD = 4  # thang 0-10, dưới ngưỡng này coi như "không tìm thấy"

SYSTEM_PROMPT = """Bạn là trợ lý tra cứu tri thức về repo "queue_simulator".
Chỉ được trả lời dựa trên các đoạn CONTEXT được cung cấp bên dưới — tuyệt đối không bịa thêm thông tin ngoài context.
Nếu context không đủ để trả lời, hãy nói rõ "Không tìm thấy thông tin này trong tài liệu hiện có." và gợi ý người dùng hỏi lại theo hướng khác.
Trả lời bằng đúng ngôn ngữ của câu hỏi (Việt hoặc Anh).
Sau mỗi ý lấy từ context, chèn trích dẫn dạng [Tên tài liệu, Mục] khớp với tiêu đề/section được cho trong context.
Văn phong ngắn gọn, đi thẳng vào trọng tâm."""

load_dotenv(HERE / ".env")
_client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
_collection = None


def get_collection():
    global _collection
    if _collection is None:
        if not INDEX_DIR.exists():
            raise RuntimeError("Chưa có index — chạy `python ingest.py` trước.")
        db_client = chromadb.PersistentClient(path=str(INDEX_DIR))
        _collection = db_client.get_collection(COLLECTION_NAME)
    return _collection


def embed_query(text: str):
    resp = _client.models.embed_content(
        model=EMBED_MODEL,
        contents=[text],
        config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY", output_dimensionality=768),
    )
    return resp.embeddings[0].values


def retrieve(question: str, top_n: int = RETRIEVE_TOP_N, source_filter=None):
    collection = get_collection()
    query_emb = embed_query(question)
    res = collection.query(query_embeddings=[query_emb], n_results=top_n)

    candidates = []
    for doc_text, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
        candidates.append({"text": doc_text, "metadata": meta, "distance": dist})

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

    resp = _client.models.generate_content(
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


def generate_answer(question: str, chunks: list):
    context = build_context(chunks)
    prompt = f"CONTEXT:\n{context}\n\nCÂU HỎI: {question}"
    resp = _client.models.generate_content(
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
            "title": meta["title"],
            "section": meta["section"],
            "page": None,
            "url": meta["source"] if meta.get("type") == "real" else None,
            "snippet": c["text"][:280],
        })
    return sources


def answer(question: str, top_k: int = DEFAULT_TOP_K, source_filter=None):
    candidates = retrieve(question, source_filter=source_filter)
    if not candidates:
        return {
            "answer": "Không tìm thấy thông tin này trong tài liệu hiện có.",
            "sources": [],
            "grounded": False,
        }

    top_chunks = rerank(question, candidates, top_k=top_k)
    best_score = top_chunks[0]["rerank_score"] if top_chunks else 0

    if best_score < GROUNDED_SCORE_THRESHOLD:
        return {
            "answer": "Không tìm thấy thông tin này trong tài liệu hiện có. Bạn thử hỏi lại theo hướng khác hoặc nêu rõ tên dự án con (vd Queue Simulator, Basic ML, Test_VSF_driver_allocation...) xem sao.",
            "sources": [],
            "grounded": False,
        }

    relevant_chunks = [c for c in top_chunks if c["rerank_score"] >= GROUNDED_SCORE_THRESHOLD]
    answer_text = generate_answer(question, relevant_chunks)
    return {
        "answer": answer_text,
        "sources": build_sources(relevant_chunks),
        "grounded": True,
    }
