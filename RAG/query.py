"""CLI hỏi-đáp nhanh, không cần chạy server API.

Chạy: python query.py
"""
import sys

sys.stdout.reconfigure(encoding="utf-8")

import rag_core


def main():
    print("RAG queue_simulator — gõ câu hỏi (Ctrl+C hoặc 'exit' để thoát, 'reset' để xoá lịch sử hội thoại)\n")
    history = []
    while True:
        try:
            question = input("Hỏi: ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            break
        if not question or question.lower() in {"exit", "quit"}:
            break
        if question.lower() == "reset":
            history = []
            print("(đã xoá lịch sử hội thoại)\n")
            continue

        result = rag_core.answer(question, history=history)
        print(f"\nTrả lời: {result['answer']}\n")
        if result["sources"]:
            print("Nguồn:")
            for s in result["sources"]:
                print(f"  - {s['title']} — {s['section']}")
        print(f"grounded={result['grounded']}\n{'-' * 60}")
        history.append({"question": question, "answer": result["answer"]})


if __name__ == "__main__":
    main()
