---
name: design-html-page
description: Build or redesign a standalone, self-contained HTML page (report, dashboard, checklist, comparison page) following this repo's Analytics Design System — the "Google Analytics style". Use whenever creating a new HTML artifact/presentation file in this repo, or when the user asks to restyle something "kiểu Google Analytics" / "theo ADS" / "theo design system".
---

Khi build hoặc redesign một trang HTML độc lập (report, dashboard, checklist, trang so sánh...) theo phong cách Analytics Design System (ADS) của repo này, áp dụng toàn bộ nội dung dưới đây — đây là bản sao đầy đủ của ngôn ngữ thiết kế, không cần đọc file nào khác.

## 1. Triết lý thiết kế

1. **Data-First:** giao diện lùi lại làm nền cho dữ liệu. Không trang trí thừa, không gradient phức tạp, không mảng màu lớn vô nghĩa.
2. **Cognitive Ease:** chia nhỏ dữ liệu thành module dễ quét (scannable) bằng whitespace và phân cấp thị giác chặt chẽ.
3. **Modularity:** Card/Button/Chart/Table là các khối độc lập, nhất quán, ghép được linh hoạt như Lego cho nhiều loại dashboard khác nhau.

## 2. Hệ thống màu sắc

**Primary (Analytics Blue)** — điểm nhấn thương hiệu, action chính, active state:
| Token | Hex | Dùng cho |
|---|---|---|
| `primary900` | `#174EA6` | Text trên nền Primary nhạt, hover cần nhấn mạnh |
| `primary500` (base) | `#1A73E8` | Nút chính, active tab, thanh biểu đồ chính |
| `primary100` | `#D2E3FC` | Nền hover, vùng chọn (selection) |
| `primary50` | `#E8F0FE` | Nền cho pill/chip đang active |

**Neutrals & Surfaces** — nhường sân khấu cho dữ liệu:
| Token | Hex | Dùng cho |
|---|---|---|
| `gray900` | `#202124` | Tiêu đề khối, text quan trọng nhất, Hero Metrics |
| `gray700` | `#5F6368` | Text phụ (body), nhãn dữ liệu, tiêu đề cột bảng |
| `gray400` | `#BDC1C6` | Placeholder, icon/button disabled |
| `gray200` | `#E8EAED` | Divider mỏng, viền ô bảng |
| `gray50` | `#F3F4F6` | **Nền hệ thống (app background)** |
| `white` | `#FFFFFF` | **Bề mặt Card** |

**Semantic & Categorical** — giữ nhất quán ý nghĩa xuyên suốt dự án:
| Token | Hex | Ý nghĩa |
|---|---|---|
| `success` | `#1E8E3E` | Tốt/Active/Hoàn thành/Tăng trưởng dương |
| `warning` | `#F29900` | Cảnh báo, chờ xử lý, **Segment dữ liệu số 2** khi so sánh |
| `danger` | `#D93025` | Lỗi, Xấu, Tăng trưởng âm, Dừng hoạt động |
| `pink` | `#D81B60` | Điểm nhấn phụ, Segment dữ liệu số 3 |

Quy tắc: khi so sánh 2 nhóm/segment song song (2 cột, 2 track, 2 filter...), Segment 1 = `primary500`, Segment 2 = `warning`. Mọi chart/số liệu/thanh bar liên quan tới segment đó phải dùng đúng màu này xuyên suốt trang — không đổi màu giữa chừng.

## 3. Không gian & cấu trúc

**8pt Grid System** — mọi padding/margin là bội số của 8 (hoặc 4 cho chi tiết rất nhỏ):
- `4px` (0.25rem) — khoảng sát (icon-text trong 1 nút)
- `8px` (0.5rem) — padding thành phần nhỏ (pill filter, input)
- `16px` (1rem) — khoảng cách mặc định giữa phần tử cùng khối
- `24px` (1.5rem) — padding mặc định bên trong Card
- `32px` (2rem)+ — gutter giữa các Card trên Grid

**Kiến trúc Card** — hạt nhân của dashboard:
- Background luôn `white`.
- Border-radius `8px`.
- **Không dùng viền solid bọc quanh card** — dùng box-shadow rất nhạt để tách card khỏi nền `gray50`: `box-shadow: 0 1px 3px rgba(0,0,0,.12), 0 1px 2px rgba(0,0,0,.24);`
- Một border-left màu accent (3–4px) để gắn nhãn segment/category là hợp lệ — đó là thông tin (phân loại), không phải trang trí, nên không vi phạm quy tắc "không viền".

## 4. Typography

Một họ font sans-serif duy nhất: `Roboto, "Segoe UI", system-ui, -apple-system, Arial, sans-serif` (không có CDN font trong trang self-contained, dựa vào font hệ thống — không trộn thêm serif). Phân cấp bằng size/weight/case, không đổi họ font:

- **Hero Numbers** (KPI trọng điểm): 36–48px, weight Light/Medium, tuyệt đối không in nghiêng, màu `gray900`, `font-variant-numeric: tabular-nums`.
- **Section/Block Headers** (nhãn điều hướng khối, không tranh chấp với số liệu): viết hoa toàn bộ, 11–12px, letter-spacing ~1px, màu `gray700`.
- **Data Content** (dữ liệu bảng, checklist): 13–14px Regular, màu `gray700`; phần cần nhấn mạnh trong câu dùng `gray900` + semibold.
- **Căn lề:** tên hạng mục/chuỗi chữ → căn trái. Số lượng/tỷ lệ %/tiền tệ → luôn căn phải (dễ so sánh hàng chục/trăm/nghìn).

## 5. Nguyên tắc trực quan hóa dữ liệu

1. **Max Data, Min Ink:** bỏ hết gridline dọc/ngang nếu có thể, hoặc dùng viền cực mảnh `gray200`. Trục biểu đồ nên làm mờ bớt.
2. **Micro-charts:** tích hợp cột/thanh ngang thu nhỏ (sparkline) ngay trong ô bảng/card thay vì để chart riêng ở chỗ khác — cho context ngay cạnh con số.
3. **Đồng bộ màu theo ngữ cảnh:** 1 segment = 1 màu cố định xuyên suốt mọi chart/số liệu/bar liên quan (xem mục 2).
4. **Tương tác đa chiều:** hover/click vào một cột trên chart chính nên tự động highlight/filter các số liệu liên quan trong cùng Card.

## 6. Rule bắt buộc: luôn giãn ngang hết khổ, không chừa lề hai bên quá lớn

Lỗi hay lặp lại: trang bị bó vào một cột hẹp (vd `max-width: 1100–1200px`) giữa màn hình rộng, để lại khoảng trắng chết hai bên. Áp dụng:

- **Container chính** của layout dạng dashboard/nhiều cột/bảng so sánh: đặt `max-width` rộng hơn nhiều — tối thiểu `1600px`, hoặc dùng `max-width: 96vw`/không giới hạn và chỉ chặn ở màn hình siêu rộng (vd `2000px`+). Padding hai bên dùng `clamp()` theo viewport (vd `clamp(1.5rem, 4vw, 3rem)`) thay vì số cố định nhỏ, để lề co giãn theo màn hình thay vì luôn để lại dải trắng cố định to.
- **Grid nhiều cột** (card KPI, hai track so sánh, bảng...) phải thực sự lấp đầy chiều ngang của container đó (`display:grid`/`flex` với `1fr`), không co cụm lại giữa trang.
- **Ngoại lệ hợp lý — không áp dụng máy móc**: đoạn văn xuôi dài (lede, mô tả, câu giải thích) và text trong từng item/label vẫn nên giữ `max-width` ở mức dễ đọc (~60–80 ký tự) để không kéo dài hết cỡ màn hình gây khó đọc — chỉ riêng khối văn bản đó được phép hẹp hơn container, không phải cả trang.
- Kiểm tra lại trên khung nhìn rộng (>1600px): nếu thấy hai dải trắng lớn đối xứng hai bên trong khi nội dung chính (card/table/grid) bị bó hẹp ở giữa, đó là dấu hiệu sai — nới `max-width`/padding ra.

## 7. Kỹ thuật dựng file

- Tự chứa hoàn toàn: không gọi CDN font/script/CSS ngoài (khớp CSP của Artifact tool) — dùng font-stack hệ thống ở mục 4.
- JS thuần (vanilla), không framework, đặt trong `<script>` cuối file.
- Nếu trang có trạng thái tương tác cần nhớ lại (checklist, filter đã chọn...), dùng `localStorage` — không cần backend.
- Responsive: gộp layout nhiều cột về 1 cột ở breakpoint ~900px cho mobile/tablet; bảng/nội dung rộng cho vào container riêng có `overflow-x:auto` để không làm `body` cuộn ngang.
- Tôn trọng `prefers-reduced-motion` cho các transition (progress bar, checkbox...).
- Đặt `<title>` rõ ràng ở đầu file (không bọc `<!DOCTYPE>/<html>/<head>/<body>` — khớp cách Artifact tool wrap file).

## 8. Quy trình khi được gọi

1. Xác định trang cần build là dạng gì (dashboard nhiều cột / checklist / trang so sánh / báo cáo văn xuôi) để quyết định mức áp mục 6 — dashboard/nhiều cột thì bắt buộc; văn xuôi dài thì giữ measure dễ đọc cho khối text, còn container ngoài vẫn nên rộng.
2. Viết/sửa CSS theo token (mục 2–5) + rule full-width (mục 6).
3. Nếu là file mới hoặc sửa file đã publish qua Artifact, gọi lại `Artifact` để deploy (dùng lại `url` cũ nếu đang cập nhật trang đã có, để giữ nguyên link).
