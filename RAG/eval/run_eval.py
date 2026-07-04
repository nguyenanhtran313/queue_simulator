"""Eval tự động: chạy golden_qa.jsonl qua rag_core.answer(), đo:
  - grounded_accuracy: tỉ lệ grounded (True/False) đúng như kỳ vọng
  - doc_hit_rate: trong các câu expect_grounded=true, tỉ lệ có đúng
    expect_doc_id nằm trong sources trả về (proxy cho Recall@k)

Chạy: python eval/run_eval.py   (từ thư mục RAG/)
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent.parent))

import rag_core

HERE = Path(__file__).parent
GOLDEN_PATH = HERE / "golden_qa.jsonl"
REPORT_PATH = HERE / "report.json"


def load_golden():
    items = []
    for line in GOLDEN_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            items.append(json.loads(line))
    return items


def run():
    items = load_golden()
    results = []

    for item in items:
        result = rag_core.answer(item["question"])
        grounded_ok = result["grounded"] == item["expect_grounded"]
        doc_ids_returned = [s["doc_id"] for s in result["sources"]]
        doc_hit = None
        if item["expect_grounded"] and item.get("expect_doc_id"):
            doc_hit = item["expect_doc_id"] in doc_ids_returned

        results.append({
            "question": item["question"],
            "expect_grounded": item["expect_grounded"],
            "got_grounded": result["grounded"],
            "grounded_ok": grounded_ok,
            "expect_doc_id": item.get("expect_doc_id"),
            "doc_ids_returned": doc_ids_returned,
            "doc_hit": doc_hit,
            "answer": result["answer"],
        })

        status = "OK  " if grounded_ok and doc_hit is not False else "FAIL"
        print(f"[{status}] {item['question'][:70]}")
        if not grounded_ok:
            print(f"       -> grounded kỳ vọng={item['expect_grounded']}, thực tế={result['grounded']}")
        if doc_hit is False:
            print(f"       -> kỳ vọng nguồn '{item['expect_doc_id']}', trả về {doc_ids_returned}")

    total = len(results)
    grounded_correct = sum(1 for r in results if r["grounded_ok"])
    doc_checks = [r for r in results if r["doc_hit"] is not None]
    doc_correct = sum(1 for r in doc_checks if r["doc_hit"])

    summary = {
        "total": total,
        "grounded_accuracy": grounded_correct / total if total else 0,
        "doc_hit_rate": (doc_correct / len(doc_checks)) if doc_checks else None,
        "doc_hit_checked": len(doc_checks),
    }

    print("\n" + "=" * 60)
    print(f"Grounded accuracy : {grounded_correct}/{total} ({summary['grounded_accuracy']:.0%})")
    if doc_checks:
        print(f"Doc hit rate      : {doc_correct}/{len(doc_checks)} ({summary['doc_hit_rate']:.0%})")

    REPORT_PATH.write_text(
        json.dumps({"summary": summary, "results": results}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\nBáo cáo chi tiết: {REPORT_PATH}")


if __name__ == "__main__":
    run()
