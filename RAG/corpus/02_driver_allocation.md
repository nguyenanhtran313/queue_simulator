---
doc_id: driver_allocation
title: "Test_VSF_driver_allocation — Xanh SM Smart Dispatching System (Phase 3 & 4)"
source: "Test_VSF_driver_allocation/_REQUIREMENT.md"
type: real
lang: vi
---

## Bối cảnh

Hệ thống điều phối & dự đoán nhu cầu cho nền tảng gọi xe Xanh SM (dịch vụ taxi điện thuộc GSM/Vingroup) — case study tuyển dụng Data Team. Gồm 4 phần: (1) Spatial Indexing & Real-time Heatmap, (2) Demand Forecasting bằng ML, (3) Phân tích hành vi & cơ chế điều phối/hoa hồng cho tài xế, (4) Dashboard & Metrics.

## Lưới không gian: H3 vs S2

So sánh Google S2 (lưới vuông, khoảng cách tới điểm lân cận không đều) và Uber H3 (lưới lục giác, khoảng cách tới mọi ô lân cận luôn bằng nhau — quan trọng cho tính bán kính đón khách/ETA). Quyết định chọn **Uber H3**, Resolution 8 (~0.73 km²/ô) hoặc Resolution 9 (~0.1 km²) để chia lưới TP.HCM.

## Kiến trúc real-time heatmap

Vị trí GPS driver/rider gửi qua WebSocket/MQTT → stream processing bằng Kafka/Flink, map tọa độ sang H3 Index qua thư viện `h3-py` → lưu state real-time trong Redis (H3_Index, số khách đang tìm xe, số xe trống) → visualize bằng Kepler.gl/deck.gl + Mapbox (HexagonLayer), ô "thiếu xe thừa khách" màu đỏ đậm, ô "thừa xe thiếu khách" màu xanh.

## Demand Forecasting

Mục tiêu: biết trước 15–30 phút tới khu vực (hexagon) nào có nhu cầu cao. Feature: spatial (H3_Index, POI như Quận 1, sân bay Tân Sơn Nhất), temporal (giờ, ngày trong tuần, lễ tết), contextual (thời tiết, sự kiện), historical (lag features t-1, t-2, t-3). Mô hình đề xuất: LightGBM/XGBoost (giai đoạn đầu, nhanh và đủ tốt), LSTM/GRU, hoặc ST-GCN (nâng cao, kết hợp không gian + thời gian).

## Bài toán Matching & Repositioning

Thay vì thuật toán Greedy (tài xế gần nhất), dùng **Bipartite Matching** (Kuhn-Munkres/Hungarian Algorithm): gom request trong batching window 3–5 giây, ghép N tài xế với M khách sao cho tổng ETA toàn hệ thống nhỏ nhất. Repositioning: khi model dự báo một khu vực sắp thiếu xe, hệ thống phát tín hiệu heatmap trên app tài xế để điều hướng tài xế đang rảnh tới trước.

## Chính sách hoa hồng & Incentives cho tài xế

- **Surge Pricing**: khi cầu > cung tại 1 ô H3, tăng giá cước (1.2x, 1.5x), trích % tăng thêm cộng vào thu nhập driver.
- **Dynamic Commission**: driver chạy từ vùng lạnh sang vùng nóng được giảm % chiết khấu (vd từ 25% xuống 15%) cho cuốc đó.
- **Repositioning Bonus**: thưởng cố định/điểm loyalty khi driver chịu chạy rỗng tới vùng đang thiếu hụt.
- **Consecutive Trip Streak**: thưởng thêm khi nhận liên tiếp 3 cuốc trong khu vực H3 chỉ định mà không từ chối.
- **Destination Matching**: cuối ca, ưu tiên cuốc có điểm đến hướng về nhà tài xế.

## Roadmap

Phase 1 Foundation (2–3 tuần, mock data + H3 + heatmap frontend) → Phase 2 Demand Prediction (3–4 tuần, LightGBM) → Phase 3 Dispatch & Incentive Simulator (4 tuần, Matching Algorithm + Incentive Engine) → Phase 4 Dashboard & Metrics (Fulfillment rate, ETA trung bình, chi phí incentive).
