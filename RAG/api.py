"""REST API bọc rag_core -> để Dify/N8N/web UI gọi vào.

Chạy: uvicorn api:app --host 0.0.0.0 --port 8000
"""
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import rag_core

app = FastAPI(title="queue_simulator RAG API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lịch sử hội thoại theo session, chỉ lưu trong bộ nhớ tiến trình (mất khi restart server).
# session_id do client tự sinh (vd uuid) và gửi lại ở mỗi request để duy trì ngữ cảnh multi-turn.
SESSIONS: Dict[str, list] = {}


class AskRequest(BaseModel):
    question: str
    top_k: int = rag_core.DEFAULT_TOP_K
    source_filter: Optional[List[str]] = None
    session_id: Optional[str] = None


class Source(BaseModel):
    doc_id: str
    title: str
    section: str
    page: Optional[int] = None
    url: Optional[str] = None
    snippet: str


class AskResponse(BaseModel):
    answer: str
    sources: List[Source]
    grounded: bool


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="question không được để trống")

    history = SESSIONS.get(req.session_id, []) if req.session_id else None
    try:
        result = rag_core.answer(
            req.question, top_k=req.top_k, source_filter=req.source_filter, history=history
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    if req.session_id:
        session_history = SESSIONS.setdefault(req.session_id, [])
        session_history.append({"question": req.question, "answer": result["answer"]})
        del session_history[: -rag_core.MAX_HISTORY_TURNS]

    return result


@app.post("/session/{session_id}/reset")
def reset_session(session_id: str):
    SESSIONS.pop(session_id, None)
    return {"status": "ok"}


@app.get("/health")
def health():
    corpus_dir = Path(__file__).parent / "corpus"
    docs_indexed = len(list(corpus_dir.glob("*.md")))
    try:
        rag_core.get_collection()
        status = "ok"
    except RuntimeError:
        status = "index_missing"
    return {"status": status, "docs_indexed": docs_indexed}
