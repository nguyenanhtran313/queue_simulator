---
name: run-queue-simulator
description: Open the Universal Queue Simulator (Queue Simulator/index.html) in the default browser. Use when the user asks to run, open, preview, or test the queue simulator app.
---

`Queue Simulator/index.html` là một single-file web app (React UMD + Babel-standalone + Tailwind CDN + Chart.js), không cần build step hay dev server.

1. Mở file `index.html` trong thư mục `Queue Simulator/` bằng trình duyệt mặc định của hệ điều hành (trên Windows: `start "" "Queue Simulator/index.html"`, hoặc tương đương qua Git Bash — nhớ quote đường dẫn vì tên thư mục có khoảng trắng).
2. Nếu user muốn xem bản trình bày/backup thay vì bản đang phát triển, hỏi rõ họ muốn mở `presentation.html`, `index_backup.html` hay `index_final_backup.html` (đều nằm trong `Queue Simulator/`).
3. App không gọi backend nào — mọi logic tính toán chạy 100% trên trình duyệt. Không cần khởi động server nào khác.
