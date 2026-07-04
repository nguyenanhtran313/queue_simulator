"""Ingest RAG/corpus/*.md -> semantic chunking -> Gemini embedding -> Chroma index.

Mặc định incremental: chỉ re-chunk/re-embed các file corpus có nội dung thay đổi
(so với RAG/index/manifest.json), dựa vào hash nội dung từng file.

Chạy: python ingest.py             # incremental (khuyến nghị)
      python ingest.py --rebuild   # xoá và build lại toàn bộ collection từ đầu
"""
import argparse
import hashlib
import json
import os
import re
import statistics
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

import chromadb
import yaml
from dotenv import load_dotenv
from google import genai
from google.genai import errors as genai_errors
from google.genai import types

HERE = Path(__file__).parent
CORPUS_DIR = HERE / "corpus"
INDEX_DIR = HERE / "index"
MANIFEST_PATH = INDEX_DIR / "manifest.json"
COLLECTION_NAME = "repo_knowledge"

EMBED_MODEL = "models/gemini-embedding-001"
TARGET_CHARS = 800
MAX_CHARS = 1200
MIN_CHARS = 200
BREAKPOINT_PERCENTILE = 80  # càng thấp càng cắt nhiều chunk nhỏ

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
    resp = with_retry(
        client.models.embed_content,
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


def file_hash(raw_text: str) -> str:
    return hashlib.sha256(raw_text.encode("utf-8")).hexdigest()


def build_chunks_for_doc(meta: dict, body: str, path: Path):
    sections = split_into_sections(body) or [(None, body)]
    chunks = []
    for sec_idx, (heading, sec_text) in enumerate(sections):
        sub_chunks = semantic_chunk_section(sec_text)
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
    print(f"[ingest] {path.name}: {len(sections)} section(s) -> {len(chunks)} chunk(s)")
    return chunks


def load_manifest():
    if MANIFEST_PATH.exists():
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return {}


def save_manifest(manifest: dict):
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def full_rebuild(db_client):
    print("[ingest] --rebuild: xoá và build lại toàn bộ collection.")
    try:
        db_client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = db_client.create_collection(COLLECTION_NAME)

    manifest = {}
    all_chunks = []
    for path in sorted(CORPUS_DIR.glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        meta, body = load_corpus_file(path)
        doc_chunks = build_chunks_for_doc(meta, body, path)
        all_chunks.extend(doc_chunks)
        manifest[meta["doc_id"]] = {"hash": file_hash(raw), "chunk_ids": [c["id"] for c in doc_chunks]}

    texts = [c["text"] for c in all_chunks]
    embeddings = embed_texts(texts, task_type="RETRIEVAL_DOCUMENT")
    collection.add(
        ids=[c["id"] for c in all_chunks],
        embeddings=embeddings,
        documents=texts,
        metadatas=[c["metadata"] for c in all_chunks],
    )
    save_manifest(manifest)
    print(f"[ingest] Đã build lại {len(all_chunks)} chunk từ {len(manifest)} tài liệu.")


def incremental_ingest(db_client):
    manifest = load_manifest()
    try:
        collection = db_client.get_collection(COLLECTION_NAME)
    except Exception:
        collection = db_client.create_collection(COLLECTION_NAME)

    files_on_disk = sorted(CORPUS_DIR.glob("*.md"))
    seen_doc_ids = set()
    changed_docs = []  # (meta, body, path, raw)
    unchanged_count = 0

    for path in files_on_disk:
        raw = path.read_text(encoding="utf-8")
        meta, body = load_corpus_file(path)
        doc_id = meta["doc_id"]
        seen_doc_ids.add(doc_id)
        h = file_hash(raw)
        if manifest.get(doc_id, {}).get("hash") == h:
            unchanged_count += 1
            continue
        changed_docs.append((meta, body, path, raw, h))

    removed_doc_ids = [d for d in manifest if d not in seen_doc_ids]

    if not changed_docs and not removed_doc_ids:
        print(f"[ingest] Không có thay đổi — {unchanged_count} tài liệu đã cập nhật, giữ nguyên index.")
        return

    # xoá chunk cũ của các doc bị đổi hoặc bị xoá khỏi corpus/
    ids_to_delete = []
    for doc_id in [*[m["doc_id"] for m, *_ in changed_docs], *removed_doc_ids]:
        ids_to_delete.extend(manifest.get(doc_id, {}).get("chunk_ids", []))
    if ids_to_delete:
        collection.delete(ids=ids_to_delete)

    # re-chunk + re-embed các doc thay đổi
    new_chunks = []
    for meta, body, path, raw, h in changed_docs:
        doc_chunks = build_chunks_for_doc(meta, body, path)
        new_chunks.extend(doc_chunks)
        manifest[meta["doc_id"]] = {"hash": h, "chunk_ids": [c["id"] for c in doc_chunks]}

    if new_chunks:
        texts = [c["text"] for c in new_chunks]
        embeddings = embed_texts(texts, task_type="RETRIEVAL_DOCUMENT")
        collection.add(
            ids=[c["id"] for c in new_chunks],
            embeddings=embeddings,
            documents=texts,
            metadatas=[c["metadata"] for c in new_chunks],
        )

    for doc_id in removed_doc_ids:
        del manifest[doc_id]

    save_manifest(manifest)
    print(
        f"[ingest] {unchanged_count} không đổi, {len(changed_docs)} thay đổi/mới "
        f"({len(new_chunks)} chunk), {len(removed_doc_ids)} tài liệu bị gỡ."
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rebuild", action="store_true", help="Xoá và build lại toàn bộ collection từ đầu")
    args = parser.parse_args()

    INDEX_DIR.mkdir(exist_ok=True)
    db_client = chromadb.PersistentClient(path=str(INDEX_DIR))

    if args.rebuild or not MANIFEST_PATH.exists():
        full_rebuild(db_client)
    else:
        incremental_ingest(db_client)


if __name__ == "__main__":
    main()
