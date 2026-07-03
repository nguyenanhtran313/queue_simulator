"""Ingest RAG/corpus/*.md -> semantic chunking -> Gemini embedding -> Chroma index.

Chạy: python ingest.py
"""
import os
import re
import statistics
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

import chromadb
import yaml
from dotenv import load_dotenv
from google import genai
from google.genai import types

HERE = Path(__file__).parent
CORPUS_DIR = HERE / "corpus"
INDEX_DIR = HERE / "index"
COLLECTION_NAME = "repo_knowledge"

EMBED_MODEL = "models/gemini-embedding-001"
TARGET_CHARS = 800
MAX_CHARS = 1200
MIN_CHARS = 200
BREAKPOINT_PERCENTILE = 80  # càng thấp càng cắt nhiều chunk nhỏ

load_dotenv(HERE / ".env")
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])


def load_corpus_file(path: Path):
    raw = path.read_text(encoding="utf-8")
    if raw.startswith("---"):
        _, fm_text, body = raw.split("---", 2)
        meta = yaml.safe_load(fm_text)
    else:
        meta = {"doc_id": path.stem, "title": path.stem, "source": str(path), "type": "unknown", "lang": "vi"}
        body = raw
    return meta, body.strip()


def split_into_sections(body: str):
    """Chia theo heading level-2 (## ...), giữ heading làm metadata 'section'."""
    lines = body.split("\n")
    sections = []
    current_heading = None
    current_lines = []
    for line in lines:
        m = re.match(r"^##\s+(.*)$", line.strip())
        if m:
            if current_lines:
                sections.append((current_heading, "\n".join(current_lines).strip()))
            current_heading = m.group(1).strip()
            current_lines = []
        else:
            current_lines.append(line)
    if current_lines:
        sections.append((current_heading, "\n".join(current_lines).strip()))
    return [(h, t) for h, t in sections if t]


def split_sentences(text: str):
    text = re.sub(r"\n+", " ", text).strip()
    units = re.split(r'(?<=[.!?:])\s+(?=[A-ZĐ0-9À-Ỹ"\'\-\*])', text)
    return [u.strip() for u in units if u.strip()]


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    return dot / (na * nb + 1e-9)


def embed_texts(texts, task_type):
    if not texts:
        return []
    resp = client.models.embed_content(
        model=EMBED_MODEL,
        contents=texts,
        config=types.EmbedContentConfig(task_type=task_type, output_dimensionality=768),
    )
    return [e.values for e in resp.embeddings]


def semantic_chunk_section(text: str):
    """Percentile-based semantic chunking: cắt tại các điểm mà độ tương đồng
    ngữ nghĩa giữa 2 câu liền kề giảm mạnh nhất (kiểu LangChain SemanticChunker),
    sau đó ép thêm ràng buộc MIN/MAX_CHARS."""
    sentences = split_sentences(text)
    if len(sentences) <= 1:
        return [text] if text else []

    embeddings = embed_texts(sentences, task_type="RETRIEVAL_DOCUMENT")
    distances = [1 - cosine(embeddings[i], embeddings[i + 1]) for i in range(len(sentences) - 1)]

    if len(distances) >= 2:
        threshold = statistics.quantiles(distances, n=100)[BREAKPOINT_PERCENTILE - 1]
    elif len(distances) == 1:
        threshold = distances[0] + 1e-6  # 1 breakpoint duy nhất -> không cắt, để MAX_CHARS quyết định
    else:
        threshold = 1.0

    groups = [[sentences[0]]]
    group_chars = len(sentences[0])
    for i in range(1, len(sentences)):
        sent = sentences[i]
        dist = distances[i - 1]
        prospective_chars = group_chars + 1 + len(sent)
        is_semantic_break = group_chars >= MIN_CHARS and dist > threshold
        is_size_break = prospective_chars > MAX_CHARS
        if is_semantic_break or is_size_break:
            groups.append([sent])
            group_chars = len(sent)
        else:
            groups[-1].append(sent)
            group_chars = prospective_chars

    # merge trailing group nhỏ hơn MIN_CHARS vào group trước (nếu có)
    merged = []
    for g in groups:
        text_g = " ".join(g)
        if merged and len(text_g) < MIN_CHARS:
            merged[-1] = merged[-1] + g
        else:
            merged.append(g)

    # overlap ~15%: mỗi chunk (trừ chunk đầu) mượn câu cuối của chunk trước làm ngữ cảnh
    chunks = []
    for i, g in enumerate(merged):
        if i > 0 and merged[i - 1]:
            overlap_sent = merged[i - 1][-1]
            if overlap_sent not in g:
                g = [overlap_sent] + g
        chunks.append(" ".join(g))
    return chunks


def build_chunks():
    chunks = []
    for path in sorted(CORPUS_DIR.glob("*.md")):
        meta, body = load_corpus_file(path)
        sections = split_into_sections(body) or [(None, body)]
        doc_chunk_count = 0
        for sec_idx, (heading, sec_text) in enumerate(sections):
            sub_chunks = semantic_chunk_section(sec_text)
            doc_chunk_count += len(sub_chunks)
            for chunk_idx, chunk_text in enumerate(sub_chunks):
                chunk_id = f"{meta['doc_id']}::{sec_idx}-{chunk_idx}"
                chunks.append({
                    "id": chunk_id,
                    "text": chunk_text,
                    "metadata": {
                        "doc_id": meta.get("doc_id", path.stem),
                        "title": meta.get("title", path.stem),
                        "section": heading or meta.get("title", path.stem),
                        "source": str(meta.get("source", "")),
                        "type": meta.get("type", "unknown"),
                        "lang": meta.get("lang", "vi"),
                    },
                })
        print(f"[ingest] {path.name}: {len(sections)} section(s) -> {doc_chunk_count} chunk(s)")
    return chunks


def main():
    INDEX_DIR.mkdir(exist_ok=True)
    chunks = build_chunks()
    print(f"[ingest] Tổng cộng {len(chunks)} chunk từ {len(list(CORPUS_DIR.glob('*.md')))} tài liệu.")

    texts = [c["text"] for c in chunks]
    embeddings = embed_texts(texts, task_type="RETRIEVAL_DOCUMENT")

    db_client = chromadb.PersistentClient(path=str(INDEX_DIR))
    try:
        db_client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = db_client.create_collection(COLLECTION_NAME)

    collection.add(
        ids=[c["id"] for c in chunks],
        embeddings=embeddings,
        documents=texts,
        metadatas=[c["metadata"] for c in chunks],
    )
    print(f"[ingest] Đã lưu index vào {INDEX_DIR} (collection='{COLLECTION_NAME}').")


if __name__ == "__main__":
    main()
