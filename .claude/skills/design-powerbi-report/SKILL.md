---
name: design-powerbi-report
description: Build or redesign a Power BI report page (via powerbi-report-mcp, PBIR format) following an operational-dashboard design language reverse-engineered from a real sample report, colored with this repo's Analytics Design System tone (Google Analytics / Data Studio). Use whenever the user asks to create a new Power BI report/dashboard page, or to restyle one "theo mẫu dashboard cũ".
---

Khi dựng hoặc redesign 1 report page Power BI qua `powerbi-report-mcp` (PBIR), áp dụng ngôn ngữ thiết kế dưới đây. Đây là **quy tắc thiết kế/style** (property JSON quyết định hình dáng — màu, font, border, padding...), không phải bộ toạ độ cố định — **AI tự quyết định x/y/w/h của từng visual theo nội dung thực tế của trang**, chỉ tuân 2 ràng buộc vị trí duy nhất: **Header neo góc trái trên**, **Filter Calendar neo góc phải trên**. Màu sắc mặc định lấy theo Analytics Design System (ADS) của repo — tone Google Analytics/Data Studio, dùng chung token với skill `design-html-page`. Cấu trúc: **Theme mặc định** → **Trang & Layout** → **Header** → **Filter** → 3 visual chính (**KPI Card**, **Chart Line**, **Table**). Mọi bảng đều 3 cột: `Điều kiện JSON | Giá trị | Mô tả ngắn`.

## Khi nào dùng
Dashboard vận hành (operational BI) nhiều widget, mật độ thông tin dày, dùng để theo dõi số liệu hàng ngày — khác với slide trình bày (`design-html-page` dùng cho HTML report/trang trình bày, ít widget hơn, nhiều khoảng trắng hơn).

## Theme mặc định (tone Google Analytics / Data Studio)

| Điều kiện JSON | Giá trị | Mô tả ngắn |
|---|---|---|
| Theme `dataColors[0]` | `#1A73E8` (ADS `primary500`) | Segment 1 — accentBar/line/cột chính, mặc định `ColorId=0` |
| Theme `dataColors[1]` | `#F29900` (ADS `warning`) | Segment 2 — khi so sánh song song 2 nhóm |
| Theme `dataColors[2]` | `#1E8E3E` (ADS `success`) | Tăng trưởng dương / trạng thái tốt |
| Theme `dataColors[3]` | `#D93025` (ADS `danger`) | Tăng trưởng âm / lỗi |
| Theme `dataColors[4]` | `#D81B60` (ADS `pink`) | Điểm nhấn phụ / segment 3 |
| Theme `dataColors[5]` | `#174EA6` (ADS `primary900`) | Biến thể đậm của primary — hover/nhấn mạnh |
| `page.json → objects.outspace`/`background` | `#F3F4F6` (ADS `gray50`) | Nền trang — ⚠️ trừ khi trang đã có sẵn ảnh nền, giữ nguyên ảnh, không thay màu phẳng |
| Theme `visualStyles["*"]["*"].border` | `#E8EAED` (ADS `gray200`), `radius 10`, `1px` | Border mọi visual (trừ Card) |
| `grid.outlineColor` | `#E8EAED` (ADS `gray200`) | Gridline bảng/matrix |
| Theme `textClasses.title` | fontSize `12`, Bold, `#202124` (ADS `gray900`) | Tiêu đề chart/table + số lớn trên Card |
| Theme `textClasses.header` | fontSize `10`, `#5F6368` (ADS `gray700`) | Header gridline bảng/matrix |
| Theme `textClasses.label` | fontSize `9`, `#BDC1C6` (ADS `gray400`) | Label nhỏ (vd label dưới KPI card) |
| Theme `textClasses.callout` | fontSize `32` | Card thực tế dùng `28D` (xem KPI Card) |
| Font family (mọi text class) | `Inter, 'Segoe UI', Roboto, sans-serif` | Không dùng font trang trí |
| Background mọi visual (Card/Chart/Table) | `#FFFFFF` (ADS `white`) | Bề mặt Card/Chart/Table |
| Breadcrumb — tên hệ thống | `#202124` (ADS `gray900`, hex hard-code) | Textbox không có theme-binding cho rich text |
| Breadcrumb — tên module/subpage | `#1A73E8` (ADS `primary500`, hex hard-code) | Điểm nhấn brand |
| Màu mark dữ liệu (line/cột/accentBar/conditional formatting) | luôn qua `ThemeDataColor.ColorId` trỏ `dataColors[]` ở trên, KHÔNG BAO GIỜ `#FFFFFF` | Không hard-code hex, trừ 3 giá trị cấu trúc + breadcrumb ở trên |
| `objects.legend[].properties.labelColor` | hard-code `#202124` (ADS `gray900`) hoặc tối hơn, KHÔNG BAO GIỜ `#FFFFFF`/trắng | ⚠️ Theme không có `textClasses.legend` riêng — nếu không set tường minh, legend text có thể thừa hưởng màu trắng/rất nhạt từ base theme và biến mất trên nền sáng. Bắt buộc set tay ở MỌI chart có `legend` |
| Mọi measure/series trong 1 chart | PHẢI có `dataPoint.fill` tường minh (qua `ColorId`), không để measure nào "trống" | Measure không set sẽ rơi vào auto-color-cycle của Power BI — không kiểm soát được, từng ra màu gần-trắng/không nhất quán trên sample thật |

⚠️ **File theme thật KHÔNG phải lúc nào cũng đơn giản như bảng trên** — đã gặp theme có thêm: key ngữ nghĩa `good`/`neutral`/`bad`/`maximum`/`center`/`minimum` (dùng cho gauge/KPI good-bad-neutral, map tương ứng `good→success`, `bad→danger`, `neutral→gray700`, `maximum→success`, `center→warning`, `minimum→danger`); nhiều `textClasses` hơn 4 lớp cơ bản (`smallLightLabel`, `largeLightLabel`, `boldLabel`...); và `visualStyles` khai riêng theo TỪNG loại visual (`cardVisual`, `slicer`, `tableEx`, `textbox`, `shape`...) thay vì chỉ `"*": {"*": {...}}`. Khi gặp theme dạng này: đổi MỌI hex tối/đen (`#252423`, `#000000`...) → `#202124`; MỌI hex xám nhạt/label → `#BDC1C6`/`#5F6368` theo độ đậm gần nhất; giữ nguyên các key không phải màu (fontSize, fontFamily, layout...). Đặc biệt: nếu `visualStyles.cardVisual.*.title.show = true`, đổi thành `false` — Card không có title (mục KPI Card).

## Trang & Layout

| Điều kiện JSON | Giá trị | Mô tả ngắn |
|---|---|---|
| `page.json → displayOption` | `"FitToWidth"` | Trang cuộn dọc, không ép vừa 1 màn hình |
| `page.json → height` | Tự giãn theo nội dung | AI tự quyết định — không cần hỏi user |
| `page.json → width` | Hỏi user trước khi dựng trang | Không có mặc định cố định — tuỳ mật độ nội dung mong muốn |
| `report.json → resourcePackages` (type `RegisteredResources`) | trỏ `StaticResources/RegisteredResources/<tên theme>.json` | File theme JSON custom — bắt buộc phải có |
| Toạ độ (x/y/w/h) của mọi visual | **AI tự quyết định** theo nội dung trang | Không áp lại lưới toạ độ cố định từ 1 sample cụ thể |
| ⚠️ Ràng buộc vị trí — Header | Neo góc **trái trên** trang | Xem mục Header |
| ⚠️ Ràng buộc vị trí — Filter Calendar | Neo góc **phải trên** trang | Xem mục Filter |
| Gap trong cùng 1 khối nghiệp vụ | `8px` | Header/Card → Chart → Table |
| Gap giữa 2 cột cùng hàng | `16px` | Cũng là lề trái/phải trang mặc định |
| Gap giữa 2 khối nghiệp vụ | `32px` | Tới tiêu đề khối sau |
| `Title` (mọi visual trừ Card) | On — kế thừa Theme `title` | Không set font-size thủ công |
| `Border` (mọi visual trừ Card) | On — kế thừa Theme | Không set tay từng visual |
| `Effects > Shadow` | Chưa xác minh trong report mẫu thật | Mặc định Off, không tự thêm |
| `Header Icons` | Chưa xác minh trong report mẫu thật | Nếu bật, đồng bộ toàn report |

## Header

**Breadcrumb (`textbox`):**

| Điều kiện JSON | Giá trị | Mô tả ngắn |
|---|---|---|
| Toạ độ | Neo **góc trái trên cùng** của trang (`x=0 y=0`) | Kích thước tự co giãn theo độ dài tên module, z-order cao hơn Metadata |
| Nội dung | `<TÊN HỆ THỐNG>` + `\|` + `<TÊN MODULE>` | Trang con nối thêm `/ <TÊN SUBPAGE>` cùng màu module |
| `textRuns[].textStyle.color` — tên hệ thống | `#202124` (bold, hex hard-code) | Xem Theme mặc định |
| `textRuns[].textStyle.color` — tên module/subpage | `#1A73E8` (bold, hex hard-code) | Xem Theme mặc định |
| Padding | `left=20D top=10D` | — |
| `background.show` / `border.show` | `false` / `false` | Transparent, nổi trên canvas trang |

**Metadata "Refresh At / Latest" (`pivotTable`):**

| Điều kiện JSON | Giá trị | Mô tả ngắn |
|---|---|---|
| Toạ độ | Cùng vị trí Header (`x=0 y=0`), lớp dưới breadcrumb | Kích thước tự co giãn |
| Query → Values | 2 measure: `Refresh At`, `Latest Order Created` (hoặc mốc dữ liệu tương ứng domain) | — |
| `objects.values[0].properties.valuesOnRow` | `true` | **Transpose**: biến 2 measure từ 2 cột → 2 dòng |
| `rowHeaders.fontSize` / `values.fontSize` | `9D` / `9D` | — |
| `grid.outlineStyle` | `0` | Ẩn gridline |
| `visualContainerObjects.stylePreset` | `'None'` | — |
| `visualContainerObjects.background.show` / `border.show` | `false` / `false` | — |
| `visualContainerObjects.padding.top` / `.left` | `10D` / `15D` | — |
| `objects.rowHeaders[].properties.fontColor` | hard-code `#5F6368` (ADS `gray700`), KHÔNG BAO GIỜ `#FFFFFF` | ⚠️ Cả 2 sample thật đều gán `ThemeDataColor.ColorId` cho field này (label "Refresh At"/"Latest..." ăn theo màu dữ liệu, đổi Theme là đổi màu label luôn) — sai vì đây là text NHÃN, không phải mark dữ liệu; luôn sửa lại thành hard-code neutral khi gặp |
| `objects.values[].properties.fontColorPrimary` | hard-code `#5F6368`, KHÔNG BAO GIỜ `#FFFFFF` | ⚠️ Property NÀY CÓ THẬT (đã thấy ở sample "MAG OneView", dù không thấy ở "Merchant Hub" — tuỳ layout `values` có transpose/valuesOnRow hay không). Cùng lỗi ColorId-ăn-theo-dữ-liệu như `rowHeaders`/`columnHeaders` — kiểm tra và hard-code lại |
| `objects.columnHeaders[].properties.fontColor` (mọi `tableEx`/`pivotTable`) và `visualContainerObjects.title[].properties.fontColor` (mọi chart/table) | hard-code `#5F6368` (columnHeaders) / `#202124` (title), KHÔNG BAO GIỜ qua `ColorId` | ⚠️ Lỗi LẶP LẠI ở CẢ 2 sample thật: nhiều report gán `ThemeDataColor.ColorId` cho title/column-header thay vì hard-code — khi đổi Theme, chữ tiêu đề/header vô tình đổi màu theo dữ liệu (vd biến thành xanh lá/cam dù không có ý nghĩa gì). Luôn kiểm tra 2 property này trên MỌI visual khi áp skill, không chỉ Header/KPI Card |

## Filter

**Slicer Calendar (`slicer`):**

| Điều kiện JSON | Giá trị | Mô tả ngắn |
|---|---|---|
| Toạ độ | Neo **góc phải trên cùng** của trang (`x = độ rộng trang − width slicer − lề phải`) | Cùng hàng ngang với Header, kích thước AI tự quyết định |
| Field | cột filter tháng (vd `month_filter`), alias `displayName = "Calendar"` | — |
| `data.mode` | `'Dropdown'` | — |
| `selection.singleSelect` | `false` | Cho phép multi-select/"All" |
| `border.show` / `background.show` | `false` / `false` | Đồng bộ style mọi slicer trong report |
| `padding.top` | `10D` | — |
| Toạ độ — Slicer phụ (nếu có) | Đặt liền bên trái Slicer Calendar, cùng `y`/`h` | Toạ độ chính xác do AI quyết định |
| Style — mọi slicer trong report | Đồng nhất `border`/`background`/`radius`/`header`/`items.textSize` | ⚠️ Kể cả slicer trong filter drawer ẩn |

## Tên Visual: KPI Card

Định danh: `Name: Card` · `Publisher: Microsoft` · `Id: cardVisual` · `Source: Default visual` · `Documentation: https://go.microsoft.com/fwlink/?linkid=2100001`

| Điều kiện JSON | Giá trị | Mô tả ngắn |
|---|---|---|
| Toạ độ | AI tự quyết định | Xếp hàng ngang, khoảng cách theo gap `16px` (Trang & Layout) |
| Tiêu đề khối (Card+Chart+Table) | Tuỳ report — 2 pattern thật đều đã gặp | Sample "Merchant Hub": KHÔNG có textbox chung, mỗi Chart/Table tự `visualContainerObjects.title` riêng. Sample "MAG OneView": CÓ 1 textbox tiêu đề mở đầu mỗi khối (`x=16` ngay trên hàng Card/Chart, font 12pt bold, hard-code `#202124`). Cả 2 đều hợp lệ — theo đúng convention report đang sửa, đừng mặc định là "không tồn tại" |
| `visualContainerObjects.title` | không đặt (Off) | Ngoại lệ duy nhất — mọi visual khác đều Title On |
| `query.queryState` — tên role | **`"Data"`** cho MỌI `cardVisual` (đơn lẻ lẫn small-multiples) | ⚠️ **Đã đảo ngược kết luận cũ**: từng ghi nhầm là `"Values"` mới đúng cho Card đơn lẻ — SAI. Đã kiểm chứng trực tiếp: Power BI Desktop tự chuẩn hoá `"Values"` → `"Data"` mỗi khi mở/lưu file (kể cả Card đang chạy tốt, không ai đụng tay), và **Card chỉ thực sự hiện số khi role là `"Data"`** — dùng `"Values"` là nguyên nhân khiến Card trống dù query/measure đúng 100%. Khi tự dựng Card mới qua PBIR, LUÔN dùng `"Data"` ngay từ đầu, đừng dùng `"Values"`. (Nghi ngờ trước đó rằng bật `title` mới là nguyên nhân — CHƯA được xác nhận độc lập, có thể chỉ là trùng hợp lúc điều tra) |
| `visual.objects.value[].properties.fontSize` | `28D` | Số lớn bold, màu `#202124` |
| `visual.objects.label[].properties.fontSize` | `9D`-`10D` | Label nhỏ, màu `#BDC1C6` |
| `visual.objects.accentBar[].properties.show` | `true` | ⚠️ NATIVE của `cardVisual` — KHÔNG dựng bằng shape/rectangle đè lớp |
| `visual.objects.accentBar[].properties.color` → `color.solid.color.expr.ThemeDataColor` | `{"ColorId": N, "Percent": 0}` | N trỏ `dataColors[]` (Theme mặc định), không hard-code hex |
| `visual.objects.accentBar[].properties.width` | `2D` | Độ dày thanh accent |
| `visualContainerObjects.background.show` | `false` | Tắt nền mặc định theme |
| `visualContainerObjects.border.show` | `false` | Tắt border mặc định theme |
| `visual.objects.shapeCustomRectangle[].properties.tileShape` | `'rectangleRoundedByPixel'` | Viền bo góc riêng của Card |
| `visual.objects.shapeCustomRectangle[].properties.rectangleRoundedCurve` | `10L` | Bo góc 10px |
| `visual.objects.outline[].properties.show` | `true` | Bật viền riêng thay cho border theme |
| `visualContainerObjects.padding` (`top`/`left`/`bottom`/`right`) | `0D` mọi phía | Đây là "Properties > Padding" thật — padding QUANH container Card = 0 |
| `visual.objects.padding[].properties` (`paddingUniform`, `paddingIndividual`, `leftMargin`/`topMargin`/`bottomMargin`/`rightMargin`, `selector.id="default"`) | KHÔNG mặc định 0 — tuỳ nội dung (sample thật: `paddingUniform=5L`, `leftMargin=10L`, còn lại `5L`) | ⚠️ Đây là object RIÊNG, khác `visualContainerObjects.padding` lẫn `layout.paddingUniform` — padding nội dung (số + label) bên trong 1 ô card |
| `visual.objects.layout[0].properties` (`backgroundShow`, `paddingUniform`, `selector.id="default"`) | `false` / `0L` | "Multi-card layout > Background/Uniform padding" — khoảng cách GIỮA các card trong lưới, KHÔNG phải padding nội dung 1 card (⚠️ khác mô tả bản trước) |
| `visual.objects.layout[1].properties` (`style`, `columnCount`, `rowCount`, `alignment`, `cellPadding`, `orientation`) | vd `'Cards'` / `N` / `1` / `'top'` / `10L` / `0D` | ⚠️ Phần tử này KHÔNG có `selector` (áp dụng chung) — cấu hình lưới small-multiples, không phải `{selector.id="default", backgroundFillColor}` như mô tả sai ở bản trước |
| `visual.objects.general` | ❌ Không tồn tại trong sample thật | Power BI tự lược bỏ object rỗng — KHÔNG cần set tay `{"properties": {}}` |
| Biến thể — `accentBar.color` theo measure | qua `selector.metadata` | Mỗi measure vẫn có màu riêng (đã dùng ngay ở `layout[0]`/`[1]` phía trên — Card 1 visual + nhiều measure vốn LUÔN ở dạng small-multiples này, không phải "biến thể ít dùng") |

## Tên Visual: Chart Line

| Điều kiện JSON | Giá trị | Mô tả ngắn |
|---|---|---|
| Toạ độ & bố cục (đều cột hay nhấn mạnh 1 chart lớn...) | AI tự quyết định theo nội dung | Giữ đúng gap `8px`/`16px`/`32px` (Trang & Layout) |
| `objects.lineStyles.lineChartType` | `'smooth'` | Đường mượt |
| `objects.lineStyles.areaShow` | `true` | Area tô mượt dưới line |
| `categoryAxis.show` | `false` | Ẩn hẳn trục ngày/category |
| `valueAxis.showAxisTitle` | `false` | Vẫn hiện số, ẩn tiêu đề trục |
| `dataPoint.fill` → `ThemeDataColor.ColorId` (set cho TỪNG measure, không bỏ sót) | khớp `ColorId` accentBar Card cùng khối | KHÔNG BAO GIỜ `#FFFFFF`; measure nào thiếu dòng này sẽ rơi vào auto-color của Power BI |
| `objects.legend[].properties.labelColor` (nếu chart có ≥2 measure/legend) | hard-code `#202124`, KHÔNG BAO GIỜ `#FFFFFF` | Theme không có `textClasses.legend` — phải set tay mỗi chart, không kế thừa được |

**Biến thể khác — Combo 2 trục (`lineStackedColumnComboChart`):**

| Điều kiện JSON | Giá trị | Mô tả ngắn |
|---|---|---|
| Dùng thay `lineChart` | khi có measure phụ nét đứt (2 measure/2 trục) | — |

**Biến thể khác — Donut (`donutChart`):**

| Điều kiện JSON | Giá trị | Mô tả ngắn |
|---|---|---|
| Nhãn % | đặt ngoài vòng kèm leader line | — |
| `dataPoint` màu | không set thủ công nếu phân loại theo 1 field tự nhiên | Power BI tự cycle qua `dataColors[]` theo thứ tự category |

**Biến thể khác — Bar ngang (`barChart`) / Treemap (`treemap`):**

| Điều kiện JSON | Giá trị | Mô tả ngắn |
|---|---|---|
| `dataPoint.fill` → `ThemeDataColor.ColorId` | theo Theme mặc định | Không hard-code hex |

## Tên Visual: Table

**Bảng chi tiết (`tableEx`):**

| Điều kiện JSON | Giá trị | Mô tả ngắn |
|---|---|---|
| Vị trí | Cuối trang, full-width | Toạ độ chính xác do AI quyết định |
| `visualContainerObjects.stylePreset` | `'Minimal'` | Header có mũi tên sort, gridline mảnh, không zebra-stripe |
| `objects.grid[].properties.outlineColor` | hard-code `#E8EAED` (khuyến nghị) | ⚠️ Field này nhận `ColorValue` bình thường — sample thật có bảng gán `ThemeDataColor.ColorId` (không hard-code) cho field này, ra gridline ăn theo màu dữ liệu (có bảng lệch hẳn sang xanh dương/hồng). Đây là màu CẤU TRÚC nên **nên** hard-code neutral, không nên để lẫn theo `ColorId` — nếu thấy `ColorId` ở đây trong report cũ, nên đổi lại |
| Dòng Total | Bold + đường kẻ trên | Phân tách data phía trên |

**Matrix / Heatmap (`pivotTable`):**

| Điều kiện JSON | Giá trị | Mô tả ngắn |
|---|---|---|
| Vị trí — heatmap | Sau khối nghiệp vụ cuối cùng, full-width | Toạ độ chính xác do AI quyết định |
| Matrix phân cấp | icon `+`/`-` expand/collapse, dòng cha in đậm | — |
| `objects.values[].properties.backColor` → `expr.FillRule.FillRule.linearGradient2.max.color` | `{"ThemeDataColor": {"ColorId": N, "Percent": 0}}` | ⚠️ Bên trong `linearGradient2`, `color` là `ColorValue` PHẲNG — `ThemeDataColor`/`Literal` nằm TRỰC TIẾP dưới `color`, KHÔNG lồng qua `color.solid.color.expr` như mọi property màu khác trong file. Đầu `max` PHẢI theo Theme, không hard-code hex (sample thật từng hard-code `'#2F80ED'` — sai, đã sửa lại) |
| `linearGradient2.min.color` | `{"Literal": {"Value": "'#FFFFFF'"}}` (được phép hard-code) | Cùng cấu trúc phẳng như trên — đại diện "không có dữ liệu" |
| Cell elements (Table/Matrix breakdown) | data bar/background color scale cùng nguyên tắc `ColorId` | Không chỉ riêng khối heatmap full-width |
| `objects.values[0].properties.valuesOnRow` | `true` | Transpose — dùng ở Header/Metadata (Refresh/Latest) |

## Footnote / ghi chú data quality

| Điều kiện JSON | Giá trị | Mô tả ngắn |
|---|---|---|
| Visual | `textbox` | Đặt ngay dưới bảng/card liên quan |
| Nội dung | bắt đầu bằng `*`, mô tả caveat (vd blank do thiếu tracking, trường free-text...) | — |
| `textRuns[].textStyle` | `fontStyle: "italic"`, `color: "#5F6368"` (ADS `gray700`), `fontSize: "9pt"` | ⚠️ Sample thật dùng `color: "#000000"` (đen tuyền) không có `fontSize` riêng — xám nhỏ là điều chỉnh chủ động theo ADS khi áp dụng, không phải điều verify được từ sample gốc |
| Vị trí hiển thị | Ngay tại chỗ, KHÔNG giấu trong tooltip | Quy ước tạo niềm tin dữ liệu cho người xem |

## Sửa trực tiếp file PBIR (JSON) trên đĩa

| Điều kiện JSON | Giá trị | Mô tả ngắn |
|---|---|---|
| Điều kiện áp dụng | Project dạng `.pbip`, Power BI Desktop **đang đóng** file đó | Check bằng `tasklist` xem có process `PBIDesktop.exe` không, trước khi sửa tay |
| Đường dẫn report layer | `<Tên Report>.Report/definition/pages/<pageId>/page.json` + `visuals/<visualId>/visual.json` | Sửa trực tiếp bằng Read/Write/Edit, không cần `powerbi-report-mcp` |
| Mọi property/JSON path cụ thể | accentBar, ColorId, layout, padding, valuesOnRow... | Đã liệt kê đầy đủ ở từng "Tên Visual" phía trên — không lặp lại ở đây |
| Measure trong query | `Expression.SourceRef.Entity` = bảng gốc chứa measure đó | Tra trong TMDL (`SemanticModel/definition/tables/*.tmdl`), không mặc định "Measure Collection" — nhiều measure sống ở bảng fact riêng (vd `f_firebase`, `f_txn_cks_hddt`) |
