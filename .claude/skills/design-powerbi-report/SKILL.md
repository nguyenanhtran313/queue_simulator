---
name: design-powerbi-report
description: Build or redesign a Power BI report page (via powerbi-report-mcp, PBIR format) following the "Merchant Hub / OMD DATA" operational-dashboard design language reverse-engineered from a real sample. Use whenever the user asks to create a new Power BI report/dashboard page, or to restyle one "giống Merchant Hub" / "theo mẫu dashboard cũ".
---

Khi dựng hoặc redesign 1 report page Power BI qua `powerbi-report-mcp` (PBIR), áp dụng ngôn ngữ thiết kế dưới đây — ban đầu rút ra từ dashboard mẫu "Merchant Hub / OMD DATA | T-SHOP" (file mẫu đã bị xoá khỏi repo), sau đó **đối chiếu lại với report PBIR thật** (`Merchant Hub.pbip`) để lấy toạ độ và tên visual chính xác. Mọi mục dưới đây đều nêu rõ **toạ độ X,Y bắt đầu** và **tên/Id visual Power BI** dùng để dựng — không mô tả chung chung nữa.

## 1. Khi nào dùng
Dashboard vận hành (operational BI) nhiều widget, mật độ thông tin dày, dùng để theo dõi số liệu hàng ngày — khác với slide trình bày (`design-html-page` dùng cho HTML report/trang trình bày, ít widget hơn, nhiều khoảng trắng hơn).

## 2. Kích thước trang, Theme & bảng tra visual

- **Khổ trang**: height tuỳ nội dung (trang càng nhiều "khối nghiệp vụ" xếp dọc thì càng cao — vd 720/1000/1848/2564), `displayOption: "FitToWidth"` (trang cuộn dọc, không ép vừa 1 màn hình) — chiều cao không cần hỏi user, cứ thêm khối/chart là tự giãn xuống. Width thì phải hỏi user trước khi dựng trang (xem mục 5) — 2 giá trị thật đã gặp: chuẩn `1280` (lề trái/phải 16px → vùng nội dung hữu ích `1248`), hoặc rộng hơn như `1500` (vd trang "OVERALL") khi cần nhồi nhiều measure/cột hơn trong 1 hàng.
- **Theme bắt buộc có 1 file theme JSON custom**, đăng ký trong `report.json` → `resourcePackages` (loại `RegisteredResources`), đặt tại `StaticResources/RegisteredResources/<tên theme>.json`. Theme này quyết định toàn bộ màu (`dataColors[]`) + border + typography mặc định của mọi visual trong report — theme dùng màu gì thì visual ra màu đó, không cần suy luận thêm. Visual nào cần khoá cứng màu theo 1 measure cụ thể (accentBar của Card, dataPoint của chart, đầu màu có nghĩa của conditional formatting — mục 4, mục 5, mục 6) thì set qua `ThemeDataColor.ColorId` tham chiếu vào `dataColors[]`, không hard-code hex, để đổi Theme là đổi được toàn bộ report.
- **Nguyên tắc phân biệt màu "cấu trúc/neutral" vs màu "dữ liệu/ngữ nghĩa"**: màu khung trang (nền trang, border, baseline của gradient) là màu trung tính cố định, được phép hard-code hex vì không mang ý nghĩa dữ liệu — xem 3 giá trị cố định ở dưới. Ngược lại, màu mang ý nghĩa dữ liệu (line/cột của chart, `accentBar` của Card, đầu màu có nghĩa của conditional formatting) **luôn luôn** set qua `ThemeDataColor.ColorId`, **không bao giờ** hard-code hex, và **không bao giờ** là `#FFFFFF` (trắng) — line/cột trắng sẽ biến mất trên nền canvas/card cũng màu sáng. Nền (background) của chart/card thì màu trắng vẫn bình thường, quy tắc "không trắng" chỉ áp dụng cho phần vẽ dữ liệu (mark), không áp dụng cho nền.
- **3 giá trị màu cấu trúc cố định** (hard-code, không qua Theme):
  - Nền trang (`page.json` → `objects.outspace`/`objects.background`): `#F5F6F8`.
  - Border mọi visual (theme `visualStyles["*"]["*"].border`): bo góc `radius: 10`, line-weight `1px`, màu `#B3B3B3`.
  - ⚠️ **Ngoại lệ nền trang**: rule `#F5F6F8` chỉ áp dụng khi trang CHƯA có background image nào được set sẵn (`page.json` → `objects.background[].properties.image`). Nếu trang đã có sẵn ảnh nền (vd ảnh brand/facade do user tự thêm) — **giữ nguyên ảnh đó khi redesign, không xoá/thay bằng màu phẳng**, kể cả khi các phần khác của trang đang được chỉnh lại theo design system này. Chỉ đổi sang `#F5F6F8` phẳng nếu trang vốn chưa có ảnh, hoặc user yêu cầu rõ ràng bỏ ảnh nền.
- **Bảng tra Id visual dùng trong skill này** (tất cả là default visual của Microsoft, Source = "Default visual", trừ khi ghi chú khác):

| Việc cần làm | `visualType` (Id) | Tên hiển thị trong Power BI Desktop |
|---|---|---|
| Breadcrumb, tiêu đề khối, footnote | `textbox` | Text box |
| Metadata "Refresh At / Latest" (transpose 2 dòng) | `pivotTable` | **Matrix** |
| Bộ lọc Calendar / dropdown khác | `slicer` | Slicer |
| KPI card | `cardVisual` | **Card** (xem mục 4 — có đủ Publisher/Documentation) |
| Chart xu hướng 1 measure/trục | `lineChart` | Line chart |
| Chart xu hướng 2 measure/2 trục (nét đứt) | `lineStackedColumnComboChart` | Line and stacked column chart |
| Bảng chi tiết / breakdown | `tableEx` | Table |
| Donut | `donutChart` | Donut chart |
| Bar ngang | `barChart` | Stacked bar chart |
| Treemap | `treemap` | Treemap |

## 3. Header & breadcrumb (lặp lại y hệt trên mọi page)

Khối header nằm gọn trong hình chữ nhật **x=0, y=0, w=368, h=96**, gồm 2 visual chồng lớp lên nhau (không phải 1 visual):

1. **Breadcrumb** — `textbox`, x=0 y=0, w≈216-400 (co giãn theo độ dài tên module) h=32-40, z-order cao hơn Matrix bên dưới. Nội dung: `<TÊN HỆ THỐNG>` (đen, bold) + `| <TÊN MODULE>` (đỏ, bold). Nếu là trang con: nối thêm `/ <TÊN SUBPAGE>` cũng tô đỏ. Padding trong textbox: `left=20, top=10`. Tắt `background.show` và `border.show` (transparent, nổi trên canvas).
   - ⚠️ Màu chữ ở đây là **hex string thường** trong `textRuns[].textStyle.color` (vd `"#000000"`, `"#ed1d24"`) — Power BI **không có cơ chế theme-binding cho rich text của textbox**, nên đây là chỗ hex hard-code là bắt buộc, không phải lỗi thiết kế.
2. **Metadata tươi dữ liệu** — visual **Matrix** (`pivotTable`), x=0 y=0, w=368 h=96, z-order thấp hơn textbox. Query: 2 measure `Refresh At` và `Latest Order Created` (hoặc mốc dữ liệu tương ứng của domain) đặt trong bucket **Values**. Bật `objects.values[0].properties.valuesOnRow = true` — đây chính là bước **transpose** biến 2 measure từ 2 cột thành 2 dòng. Font: `rowHeaders.fontSize = 9D`, `values.fontSize = 9D`. `grid.outlineStyle = 0` (ẩn gridline). `visualContainerObjects`: `stylePreset = 'None'`, `background.show = false`, `border.show = false`, `padding.top = 10D`, `padding.left = 15D`.
   - ⚠️ Màu chữ của 2 measure `Refresh At`/`Latest...` (`objects.values[].properties.fontColorPrimary` hoặc tương đương) **không bao giờ** để `#FFFFFF`/trắng — dù nền header trong suốt, trắng vẫn có thể biến mất trên nền trang sáng màu hoặc khi trang có ảnh nền sáng. Dùng màu tối (vd đen hoặc `ThemeDataColor` tối) như mọi text khác trong report.
- **Slicer Calendar**: `slicer`, x=1040 y=16 w=224 h=80 (neo theo mép phải trang 1280: `1280 - 224 - 16 = 1040`). Field: cột `month_filter` (hoặc tương đương) alias hiển thị thành "Calendar" qua `displayName`. `data.mode = 'Dropdown'`, `selection.singleSelect = false` (cho phép multi-select/"All"). Tắt border/background, `padding.top = 10D`.
- **Slicer phụ** (nếu có) đặt liền bên trái slicer Calendar, cùng `y`/`h`, width tuỳ nội dung — ví dụ thật: `x=688 w=336` (dropdown Operating System), `x=800 w=224` (dropdown/segmented "source").
- ⚠️ **Mọi slicer trên cùng 1 trang phải dùng chung đúng 1 style** — cùng `border.show`, cùng `radius`, cùng `background.show`, cùng `header`/`items.textSize` — dù field/nội dung mỗi slicer khác nhau. Không để slicer này có border màu, slicer kia tắt border, slicer khác lại đổi radius riêng; chọn 1 style chuẩn (khuyến nghị: tắt hẳn `border`/`background` như Slicer Calendar ở trên) rồi áp đồng nhất cho toàn bộ slicer trong report, kể cả slicer nằm trong filter drawer ẩn.

## 4. Hàng KPI card

**Định danh visual** (Power BI Desktop → pane Visualizations):
```
Name: Card
Publisher: Microsoft
Id: cardVisual
Source: Default visual
Documentation: https://go.microsoft.com/fwlink/?linkid=2100001
```

- ⚠️ **`accentBar` (thanh màu mỏng bên trái card) là property NATIVE của `cardVisual`** — set trong `visual.objects.accentBar` (`show`, `color`, `width`). **Không phải** dựng bằng 1 shape/rectangle đặt lớp dưới đè Card lên trên như từng ghi nhầm ở bản trước.
- Grid chuẩn: **4 card/hàng**, mỗi card `w=300 h=96`, `x` lần lượt `16 / 332 / 648 / 964` (gap 16px giữa các card, lề trái/phải 16px trên trang rộng 1280 → `16+300*4+16*3+16=1280`). `y` tuỳ vị trí khối (xem mục 5).
- Nội dung: **số lớn bold đen** (`objects.value.fontSize = 28D`) phía trên + **label xám nhỏ** (`objects.label.fontSize = 9-10D`) phía dưới.
- Card **không đặt `title`** trong `visualContainerObjects` (đúng như đã lưu ý — Card không cần tiêu đề).
- Card **tự tắt border/background mặc định của theme**: `visualContainerObjects.background.show = false`, `visualContainerObjects.border.show = false` — vì Card tự vẽ viền bo góc riêng qua `objects.shapeCustomRectangle` (`tileShape: 'rectangleRoundedByPixel'`, `rectangleRoundedCurve: 10L`) + `objects.outline.show = true`, không dùng border chung của theme.
- `accentBar.width = 2D` (2px), `accentBar.color` → set bằng `color.solid.color.expr.ThemeDataColor: {"ColorId": N, "Percent": 0}`, **không hard-code hex Literal** — N là index bất kỳ trong `dataColors[]` của theme đang chọn, đổi Theme là đổi luôn màu này, không cần sửa từng visual.
- **3 property bắt buộc phải set trên MỌI `cardVisual`** (Format pane trong Power BI Desktop, áp dụng dù dùng 1 Card/measure hay biến thể multi-card bên dưới):
  - `Properties > Padding = 0` (mục "Properties" trong format pane của Card).
  - `Multi-card layout > Uniform padding = 0`.
  - `Multi-card layout > Background = Off`.
  - Trong JSON, các property này nằm trong `visual.objects` của `cardVisual` (nhóm gần `layout`/`general` — xem thêm biến thể multi-card ngay dưới); nếu set trực tiếp qua JSON mà không chắc đúng tên field, mở Power BI Desktop, chỉnh 1 Card mẫu qua UI rồi đọc lại `visual.json` để lấy đúng tên property trước khi nhân bản ra các Card khác.
- Biến thể ít dùng hơn: 1 Card visual duy nhất chứa nhiều measure cùng lúc qua "small multiples" (`objects.layout`: `style='Cards'`, `columnCount=N`, `rowCount=1`) — gặp ở trang tổng quan cần nhồi nhiều KPI trong 1 hàng hẹp; mỗi measure vẫn có `accentBar.color` riêng qua `selector.metadata`. Mặc định vẫn nên dùng N Card riêng biệt (dễ set accentBar/vị trí độc lập hơn). Đây chính là "Multi-card layout" ở trên — dù dùng biến thể này hay N Card riêng biệt, vẫn phải set `Uniform padding = 0` và `Background = Off`.

## 5. Biểu đồ

- **Trước khi dựng 1 trang mới (hoặc khối biểu đồ mới), PHẢI hỏi lại người dùng 2 việc** — không có mặc định cố định cho cả 2:
  1. **Bề ngang trang bao nhiêu?** — chuẩn `1280`, hoặc rộng hơn (vd `1500`, như trang "OVERALL" thật) nếu cần nhồi nhiều measure/cột hơn trong 1 hàng. Chiều cao thì không cần hỏi — cứ thêm khối/chart là trang tự giãn dài xuống, AI tự tính toạ độ Y tiếp theo.
  2. **Bố cục lưới cho từng khối**: các cột đều nhau hay bố cục bất đối xứng kiểu 1/3–2/3? Cả 2 kiểu đều là pattern thật đã dùng trong report:
     - **(a) Lưới đều cột** (dùng khi mỗi khối có đúng 4 measure cùng "trọng số"): 4 KPI card + 4 line chart bên dưới, cùng lưới cột `x=16/332/648/964, w=300`. Ví dụ toạ độ thật (1 khối nghiệp vụ trọn vẹn):
       ```
       textbox tiêu đề khối   x=16  y=Y0        w=500 h=40
       4x cardVisual          x=16/332/648/964  y=Y0+48   w=300 h=96
       4x lineChart            x=16/332/648/964  y=Y0+152  w=300 h=160
       2x tableEx (2 cột)      x=16 w=616 | x=648 w=616   y=Y0+320  h=240
       ```
       Khoảng cách card→chart→table **trong cùng 1 khối = 8px**; khoảng cách tới **khối kế tiếp (textbox tiêu đề mới) = 32px**.
       ⚠️ **`h=40` cho textbox tiêu đề khối là bắt buộc** (không phải 24) — `h=24` quá thấp, chữ dễ bị cắt mất khi tiêu đề dài hoặc bị wrap 2 dòng ở màn hình nhỏ hơn. Font của tiêu đề khối luôn `fontSize=12pt`, bold, `#111827` (khớp Theme's text class `title` ở mục 8) dù textbox không tự inherit theme (phải set thủ công trong `textRuns[].textStyle`, xem lưu ý hex hard-code bắt buộc ở mục 3).
     - **(b) Lưới bất đối xứng 1/3–2/3** (dùng khi 1 cột là danh sách KPI dọc/nhỏ, còn lại là chart/bảng lớn): ví dụ thật trang rộng 1280: `card x=16 w=224` (xếp dọc nhiều mini-card) | `comboChart x=256 w=528` | `pivotTable x=800 w=464`, cùng `y`, gap 16px giữa các cột, lề 16px. Hoặc trên trang rộng 1500: `chart x=16 w=352` | `chart x=384 w=544` | `chart x=944 w=544`.
- **Border**: KHÔNG set border thủ công cho chart/table — để mặc định kế thừa từ Theme (`radius: 10`, line-weight `1px`, `color: #B3B3B3`, `show: true`) — border tự động đồng nhất trên toàn trang, không phải set tay từng visual.
- **Title**: KHÔNG set font-size tiêu đề thủ công — để mặc định kế thừa Theme's text class `title` (fontSize 12, Bold, `#111827`, font Inter/Segoe UI/Roboto). Riêng **Card thì không có title** (mục 4).
- ⚠️ **Không bao giờ vẽ mark (line/cột) màu trắng `#FFFFFF`** — line trắng hay cột trắng sẽ biến mất trên nền canvas/card cũng sáng màu. Quy tắc này chỉ áp dụng cho phần vẽ dữ liệu (`dataPoint.fill`), **không áp dụng cho background** của chart/card — nền trắng vẫn bình thường (mặc định Theme background = `#FFFFFF`).
- Chart mặc định: `lineChart` với `objects.lineStyles.lineChartType = 'smooth'` + `areaShow = true` → area mượt 1 trục/measure. Ẩn trục: `categoryAxis.show = false`, `valueAxis.showAxisTitle = false` (vẫn hiện số, ẩn tiêu đề trục).
- Combo 2 trục (measure phụ nét đứt): dùng `lineStackedColumnComboChart` thay vì `lineChart`.
- Màu area/line nên khớp với màu accentBar của KPI card cùng khối (set cùng `ThemeDataColor.ColorId`) để nhìn rõ 2 visual thuộc cùng 1 khối nghiệp vụ.
- Donut chart (`donutChart`): nhãn % đặt ngoài vòng kèm leader line. Không cần set `dataPoint` màu thủ công nếu chỉ phân loại theo 1 field tự nhiên — để Power BI tự cycle qua `dataColors[]` của theme theo thứ tự category.

## 6. Bảng & matrix
- Style mặc định Power BI: header có mũi tên sort, gridline mảnh xám (`grid.outlineColor = '#E5E7EB'`, hard-code — không phải màu nghiệp vụ nên không cần theme-binding), không zebra-stripe. `visualContainerObjects.stylePreset = 'Minimal'`.
- Dòng **Total luôn bold + có đường kẻ trên** phân tách với data phía trên.
- Matrix phân cấp: dùng icon +/- expand/collapse, dòng cha in đậm.
- **Heatmap bằng conditional formatting** (không cần chart riêng): Matrix (`pivotTable`) áp background color scale lên chính bảng số (`objects.values[].properties.backColor` → `FillRule.linearGradient2`) — dùng cho ma trận 2 chiều dày đặc (vd giờ x ngày). Toạ độ thật: `x=16 y=1840 w=1248 h=340` (full-width, đặt sau khối nghiệp vụ cuối cùng, gap 32px).
  - ⚠️ **Đầu màu có nghĩa của gradient (`max`) phải lấy theo Theme** — set `FillRule.linearGradient2.max.color` bằng `ThemeDataColor.ColorId` khớp màu khối nghiệp vụ (không hard-code hex như `'#2F80ED'`), để đổi Theme là đổi luôn màu heatmap. Đầu `min` vẫn có thể giữ trắng/nền trung tính (đại diện "không có dữ liệu", không phải màu ngữ nghĩa nên không bắt buộc theo Theme) — xem nguyên tắc phân biệt "cấu trúc vs dữ liệu" ở mục 2.
  - Áp dụng tương tự cho data bar/background color scale trên **Cell elements** của Table/Matrix breakdown (không chỉ riêng khối heatmap full-width) — mọi đầu màu có nghĩa trong conditional formatting đều qua `ThemeDataColor.ColorId`, không hard-code hex.
- Bảng raw detail (`tableEx`) luôn đặt cuối trang, scroll ngang, phục vụ audit nhanh ngay trên dashboard. Toạ độ thật: `x=16 w=1248` (full-width), gap ~24-32px so với heatmap phía trên.

## 7. Footnote / ghi chú data quality
Dưới card có dữ liệu cần giải thích: 1 dòng *italic, xám, size nhỏ*, bắt đầu bằng `*`, mô tả caveat (vd blank do thiếu tracking, trường free-text...). Bắt buộc ghi ngay tại chỗ, không giấu trong tooltip — đây là quy ước tạo niềm tin dữ liệu cho người xem. Visual: `textbox`, đặt ngay dưới bảng/card liên quan.

## 8. Typography & mật độ
- Font theo Theme's `textClasses`: `title` (chart/table title) fontSize 12 Bold `#111827`; `header` (gridline header) fontSize 10 `#6B7280`; `label` fontSize 9 `#9CA3AF`; `callout` (số lớn trên Card) fontSize 32 — font family `Inter, 'Segoe UI', Roboto, sans-serif`. Không dùng font trang trí, không set fontSize thủ công trừ khi có lý do (Card value dùng 28D thay vì callout 32D mặc định — chấp nhận được, đã kiểm chứng trong report thật).
- Nền canvas xám rất nhạt — set ở **cấp trang** (`page.json` → `objects.outspace`/`objects.background`, không phải ở theme) = `#F5F6F8`, **trừ khi trang đã có sẵn background ảnh thì giữ nguyên** (xem ngoại lệ ở mục 2). Card/chart/table nền trắng (`background = #FFFFFF`, kế thừa từ Theme).
- Mật độ **dày đặc**, 2 mức khoảng cách đã đo được từ report thật — dùng đúng 2 số này, không áng chừng:
  - **8px**: giữa các visual trong CÙNG 1 khối nghiệp vụ (tiêu đề khối → card → chart → table).
  - **32px**: giữa 2 khối nghiệp vụ khác nhau (từ bảng cuối khối trước tới textbox tiêu đề khối sau).

## 9. Lưu ý khi dựng bằng cách sửa trực tiếp file PBIR (JSON) trên đĩa
Có thể không cần qua `powerbi-report-mcp` — nếu project là `.pbip` (đã Save As từ Power BI Desktop dạng Power BI Project), report layer nằm ở `<Tên Report>.Report/definition/pages/<pageId>/page.json` + `visuals/<visualId>/visual.json`, sửa trực tiếp bằng Read/Write/Edit là đủ, không cần MCP. Chỉ áp dụng khi Power BI Desktop **đang đóng** file đó (tránh ghi đè/xung đột với phiên đang mở) — kiểm tra bằng `tasklist` xem có process `PBIDesktop.exe` đang chạy không trước khi sửa tay.
- **KPI card `cardVisual` có sẵn property `accentBar`** (`objects.accentBar`: `show`, `color`, `width`) — accent border trái **native**, không cần dựng thủ công bằng shape+card đè lớp (xem mục 4).
- **Màu set bằng `ThemeDataColor.ColorId` tường minh, không dùng `Literal` hex** — nếu để Power BI Desktop tự động chọn màu (không set gì, UI tự gán ColorId tăng dần theo thứ tự gặp measure) thì ColorId sẽ không đoán trước được; nhưng nếu tự tay ghi thẳng `"ThemeDataColor": {"ColorId": N}` vào JSON thì N là do mình chọn, hoàn toàn tường minh — và đổi Theme là đổi được màu đó, không cần sửa từng visual.
- Theme màu khai báo thành 1 file theme JSON đăng ký trong `report.json` → `resourcePackages` (xem `StaticResources/RegisteredResources/*.json`) dùng chung cho report. `visualStyles["*"]["*"].border`/`background` trong theme áp mặc định cho MỌI visual (radius 10, line-weight 1px, `#B3B3B3`, show true / nền trắng) — Card là ngoại lệ duy nhất tự tắt border/background theme để dùng viền bo góc riêng (mục 4). Nền trang (`#F5F6F8`) set riêng ở từng `page.json`, không nằm trong file theme.
- Area+line 1 measure/trục (mini chart theo ngày): visual `lineChart` với `objects.lineStyles.areaShow: true` + `lineChartType: 'smooth'` là đủ để ra area mượt — không cần combo 2 trục nếu mỗi chart chỉ có 1 measure. Combo 2 trục (measure phụ nét đứt) mới cần `lineStackedColumnComboChart`.
- Category axis nên set `show: false` (ẩn hẳn trục ngày) cho mini chart trong dashboard dày đặc — chỉ giữ `valueAxis` với `showAxisTitle: false` (vẫn hiện số, ẩn tiêu đề).
- Heatmap matrix (mục 6): bật conditional formatting kiểu "Background color" theo value trên field số trong Matrix visual (`pivotTable`), không phải Table visual (`tableEx`).
- Measure trong query phải trỏ đúng **Entity = bảng gốc chứa measure đó** (`Expression.SourceRef.Entity`), tra trong TMDL (`SemanticModel/definition/tables/*.tmdl`) chứ không mặc định "Measure Collection" — nhiều measure thực ra sống ở bảng fact riêng (vd `f_firebase`, `f_txn_cks_hddt`).
- Matrix metadata "Refresh At/Latest" (mục 3) dùng đúng property `objects.values[0].properties.valuesOnRow: true` để transpose — không phải xoay bằng cách kéo field qua vùng Rows/Columns thủ công.
