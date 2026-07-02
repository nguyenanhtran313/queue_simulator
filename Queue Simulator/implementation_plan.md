# Tính năng "Thời gian thực Sân bay" - Queue Simulator

## Mô tả tổng quan

Thêm một kịch bản mô phỏng **Sân bay Tân Sơn Nhất** vào bên dưới template McDonald's hiện tại. Tính năng này biến simulator thành một mô phỏng **real-time** với:

- Đồng hồ mô phỏng chạy theo thời gian (có thể tua nhanh)
- Số khách "nhảy số" realtime phản ánh tốc độ đến sân bay
- Timeline trực quan với icon người đi bộ qua từng bước
- Phát hiện bottleneck sau 1h, 2h, 12h chạy mô phỏng

## Proposed Changes

### 1. Template Sân bay Tân Sơn Nhất

Thêm nút "✈️ Sân bay Tân Sơn Nhất" bên dưới nút McDonald's trong sidebar. Load preset với **8 bước**:

| Bước | Tên | Nhân sự/Quầy | Tốc độ (phút/khách) |
|------|-----|:---:|:---:|
| 1 | Check-in / Gửi hành lý | 12 | 3.0 |
| 2 | Kiểm tra an ninh soi chiếu | 8 | 1.5 |
| 3 | Kiểm tra hộ chiếu (Xuất cảnh) | 6 | 1.0 |
| 4 | Di chuyển đến Gate | ∞ (không giới hạn) | 5.0 |
| 5 | Chờ boarding tại Gate | 2 | 0.5 |
| 6 | Scan thẻ lên máy bay | 2 | 0.3 |
| 7 | Tìm chỗ ngồi / Cất hành lý | 1 (tự phục vụ) | 1.5 |
| 8 | Máy bay đóng cửa | 1 | 0.1 |

> [!NOTE]
> Arrival rate mặc định: **15 khách/phút** (tương đương ~900 khách/giờ, phản ánh 1 chuyến bay quốc tế lớn)

---

### 2. Simulation Engine (Real-time) — Thay đổi lớn nhất

Hiện tại app chỉ tính toán **tĩnh** (steady-state math). Cần thêm một **Discrete Event Simulation Engine** chạy song song:

#### State mới:
```javascript
// Simulation state
const [simTime, setSimTime] = useState(0);        // Thời gian mô phỏng (giây)
const [simSpeed, setSimSpeed] = useState(1);       // Tốc độ: 1x, 10x, 100x
const [isRunning, setIsRunning] = useState(false); // Đang chạy hay dừng
const [simQueues, setSimQueues] = useState({});     // { nodeId: { queue: number, processing: number } }
const [walkers, setWalkers] = useState([]);         // Danh sách icon người đang di chuyển
```

#### Logic mỗi tick (100ms real-time):
```
Mỗi tick = simSpeed * 0.1 giây mô phỏng

1. Sinh khách mới theo Poisson distribution (arrivalRate * tickDuration / 60)
2. Với mỗi bước (node), xử lý:
   - Di chuyển khách từ queue vào processing nếu có slot trống
   - Giảm thời gian processing của khách đang xử lý
   - Khách xong → chuyển sang queue bước tiếp theo + tạo walker animation
3. Cập nhật simQueues, walkers, simTime
```

> [!IMPORTANT]
> Simulation engine chạy **song song** với math engine hiện tại. Math engine vẫn hiển thị các chỉ số lý thuyết (rho, capacity). Simulation engine cung cấp số liệu **thực tế** (queue length, waiting time thực).

---

### 3. Visual Timeline (Phía trên các Step cards)

Một dải ngang full-width hiển thị pipeline trực quan:

```
[Vào SB] ──●── [Check-in] ──●── [An ninh] ──●── [Hộ chiếu] ──●── [Gate] ──●── [Boarding] ──●── [Lên MB]
             12                  45                8                 2              0              0
         🚶🚶🚶            🚶🚶🚶🚶🚶         🚶🚶              🚶
```

**Chi tiết thiết kế:**

- **Đường timeline**: Horizontal line với các node hình vuông nhỏ (40×40px)
- **Số trong ô vuông**: Số người **đang được xử lý** ở bước đó (realtime)
- **Số bên dưới ô**: Số người **đang đợi** trong queue
- **Icon người (🚶)**: CSS animation di chuyển từ trái sang phải giữa 2 bước
  - Mỗi khi 1 khách hoàn thành bước, spawn 1 icon 🚶 animate dọc theo đường line sang bước tiếp theo
  - Animation duration: 0.8s (cố định, không phụ thuộc simSpeed)
  - Giới hạn tối đa 20 walker cùng lúc để tránh lag
- **Màu sắc ô vuông**: 
  - Xanh lá: rho < 70%
  - Cam: 70% ≤ rho < 100%  
  - Đỏ nhấp nháy: rho ≥ 100% (bottleneck)

---

### 4. Realtime Counter (Số khách nhảy)

Trong sidebar, thêm panel "📊 Mô phỏng Thời gian thực":

- **Đồng hồ mô phỏng**: `00:15:23` format, nhảy theo simSpeed
- **Tổng khách đã đến**: Số nhảy kiểu odometer (CSS counter animation)
- **Tổng khách đã hoàn thành**: Số nhảy tương tự
- **Khách đang trong hệ thống**: Real-time count

Hiệu ứng "nhảy số":
```css
/* Odometer-style number animation */
@keyframes numberFlip {
  0% { transform: translateY(100%); opacity: 0; }
  100% { transform: translateY(0); opacity: 1; }
}
```

---

### 5. Waiting Time Indicator (mỗi Step card)

Thêm vào mỗi card bước:

- **Waiting Time (thực)**: Tính từ simulation — trung bình thời gian khách đợi trong queue ở bước đó
- Hiển thị dạng: `⏱ 4.2 phút` 
- Màu: Xanh (< 5 phút), Cam (5-15 phút), Đỏ (> 15 phút)
- Đây là **bổ sung** bên cạnh chỉ số lý thuyết hiện tại

---

### 6. Điều khiển tua nhanh (Speed Control)

Thanh điều khiển nằm trong panel simulation ở sidebar:

```
[ ▶ Play ] [ ⏸ Pause ] [ 🔄 Reset ]

Tốc độ:  [1x]  [10x]  [100x]

⏱ 00:00:00  |  Đã chạy: 0 phút mô phỏng
```

- **1x**: 1 giây thực = 1 giây mô phỏng (real-time)
- **10x**: 1 giây thực = 10 giây mô phỏng (thấy kết quả 1h sau ~6 phút)
- **100x**: 1 giây thực = 100 giây mô phỏng (thấy kết quả 1h sau ~36 giây)

> [!TIP]
> Ở tốc độ 100x, sau **36 giây** thực sẽ thấy 1 giờ mô phỏng. Sau **7 phút** thực sẽ thấy 12 giờ mô phỏng. Đủ để phát hiện bottleneck tích lũy.

---

## Cấu trúc code — Tất cả trong 1 file

Vì project hiện tại là single-file (`index.html`), tôi sẽ giữ nguyên cấu trúc này:

### [MODIFY] [index.html](file:///d:/_AntiGravity/_simulator/queue_simulator/index.html)

#### Thêm CSS mới (~50 dòng):
- Animation `@keyframes walk` cho icon người
- Animation `@keyframes numberFlip` cho odometer
- Styles cho timeline visualization
- Pulse animation cho bottleneck nodes

#### Thêm Simulation Engine (~120 dòng):
- Hook `useSimulation(nodes, arrivalRate, simSpeed, isRunning)` 
- Quản lý queue state, processing state, walker animations
- Poisson random arrival generator
- Waiting time tracker

#### Thêm Component Timeline (~80 dòng):
- `TimelineVisualization` component
- Render đường timeline ngang + ô vuông + walker icons
- Responsive: scroll ngang nếu nhiều bước

#### Thêm Simulation Control Panel trong Sidebar (~40 dòng):
- Play/Pause/Reset buttons
- Speed selector (1x, 10x, 100x)
- Sim clock display
- Realtime counters

#### Thêm Airport Template button (~20 dòng):
- Nút "✈️ Sân bay Tân Sơn Nhất" trong section Dữ Liệu Mẫu
- Preset data cho 8 bước

#### Sửa Step Cards (~15 dòng):
- Thêm hiển thị waiting time thực từ simulation
- Thêm hiển thị queue length thực

---

## Open Questions

> [!IMPORTANT]
> **1. Số bước sân bay**: Tôi đề xuất 8 bước như trên. Bạn muốn thêm/bớt bước nào không? Ví dụ: có cần bước "Mua hàng Duty Free" hay "Phòng chờ VIP"?

> [!IMPORTANT]  
> **2. Layout timeline**: Timeline nên đặt ở đâu?
> - **Phương án A (đề xuất)**: Nằm ngay trên grid các Step cards, full-width trong vùng content bên phải
> - **Phương án B**: Nằm giữa grid cards và chart

> [!WARNING]
> **3. Performance**: Ở tốc độ 100x với 8 bước và 15 khách/phút, sau 12h mô phỏng sẽ có ~10,800 khách đi qua hệ thống. Tôi sẽ **không track từng khách individual** mà chỉ track queue counts + sample waiting times để tránh memory leak. Walker animation cũng giới hạn tối đa 20 icon cùng lúc. Bạn OK với approach này?

---

## Verification Plan

### Manual Verification
1. Load template Sân bay → kiểm tra 8 bước hiển thị đúng
2. Nhấn Play → xem số khách nhảy realtime, timeline animation hoạt động
3. Tua 10x → sau 6 phút thực, kiểm tra bottleneck detection
4. Tua 100x → sau 36 giây, xem 1h mô phỏng có phát hiện bước nghẽn không
5. Reset → kiểm tra state về 0
6. Chuyển giữa McDonald's và Airport → kiểm tra không bị lỗi state
7. Kiểm tra responsive trên các kích thước màn hình

### Performance Check
- Chạy 100x trong 10 phút thực (= 1000 phút mô phỏng ≈ 16.7 giờ) → kiểm tra không bị lag/memory leak
- Mở DevTools Performance tab → kiểm tra frame rate ≥ 30fps
