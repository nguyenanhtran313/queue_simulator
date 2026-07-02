# =============================================================================
# STEP 1: SINH DỮ LIỆU GIẢ LẬP (Mock Data Generation) + H3 INDEXING
# =============================================================================
# Mục tiêu: Tạo ra dữ liệu mô phỏng hoạt động gọi xe tại TP.HCM
# - Vị trí khách đặt xe (Rider GPS)
# - Vị trí tài xế (Driver GPS)
# - Chuyển tọa độ GPS -> H3 Hexagon Index (lưới lục giác Uber)
# - Xuất CSV để dùng cho các bước sau
# =============================================================================

import pandas as pd        # Thư viện xử lý bảng dữ liệu (như Excel cho Python)
import numpy as np         # Thư viện tính toán số học, sinh số ngẫu nhiên
import h3                  # Thư viện H3 của Uber: chuyển GPS -> ô lục giác
import json                # Đọc/ghi file JSON
from datetime import datetime, timedelta  # Xử lý ngày giờ

# ---- CẤU HÌNH THAM SỐ ----
# Tọa độ trung tâm TP.HCM (Nhà thờ Đức Bà) làm "điểm neo"
HCM_CENTER_LAT = 10.7769    # Vĩ độ trung tâm
HCM_CENTER_LNG = 106.7009   # Kinh độ trung tâm

# Độ phân giải H3: Resolution 8 => mỗi ô lục giác rộng ~0.74 km²
# Tưởng tượng: cỡ 1 phường nhỏ ở quận trung tâm
H3_RESOLUTION = 8

# Số lượng bản ghi cần sinh
NUM_RIDE_REQUESTS = 5000   # 5,000 lượt đặt xe trong 1 ngày
NUM_DRIVERS = 300          # 300 tài xế đang hoạt động

# Seed để kết quả lặp lại được (reproducible) - quan trọng khi trình bày
np.random.seed(42)

# =============================================================================
# 1.1 ĐỊNH NGHĨA CÁC "VÙNG NÓNG" (Hotspots) TRONG TP.HCM
# =============================================================================
# Trong thực tế, nhu cầu đặt xe KHÔNG phân bố đều.
# Sân bay, bến xe, trung tâm thương mại... luôn có nhu cầu cao hơn.
# Ta mô phỏng điều này bằng phân phối Gaussian (chuông) quanh các điểm nóng.

HOTSPOTS = {
    # Tên khu vực: (Vĩ độ, Kinh độ, Trọng số nhu cầu)
    # Trọng số càng cao = càng nhiều người đặt xe ở đó
    "Sân bay Tân Sơn Nhất":     (10.8184, 106.6590, 0.20),  # 20% tổng nhu cầu
    "Quận 1 - Trung tâm":       (10.7769, 106.7009, 0.18),  # 18% - khu vực sầm uất
    "Quận 7 - Phú Mỹ Hưng":    (10.7295, 106.7218, 0.12),  # 12% - khu đô thị mới
    "Bến xe Miền Đông mới":     (10.8794, 106.8190, 0.08),  # 8% - bến xe liên tỉnh
    "Thủ Đức - ĐHQG":          (10.8700, 106.8030, 0.10),  # 10% - khu đại học
    "Bình Thạnh - Hàng Xanh":  (10.8030, 106.7100, 0.08),  # 8% - nút giao thông
    "Tân Bình - Cộng Hòa":     (10.8020, 106.6530, 0.07),  # 7%
    "Gò Vấp":                   (10.8380, 106.6650, 0.07),  # 7%
    "Quận 3 - Hai Bà Trưng":   (10.7850, 106.6890, 0.05),  # 5%
    "Quận 10 - Ba Tháng Hai":  (10.7700, 106.6680, 0.05),  # 5%
}


def generate_ride_requests(n=NUM_RIDE_REQUESTS):
    """
    Sinh dữ liệu đặt xe giả lập.
    
    Logic nghiệp vụ:
    - Mỗi request = 1 khách hàng mở app và đặt xe
    - Vị trí đón khách phân bố quanh các điểm nóng (không đều)
    - Thời gian đặt xe phân bố theo mô hình thực tế:
      + Sáng sớm (6-9h): Cao (đi làm)
      + Trưa (11-13h): Trung bình
      + Chiều tối (17-20h): Rất cao (tan sở)
      + Đêm khuya (23-5h): Thấp
    """
    records = []
    
    # --- Sinh thời gian đặt xe theo phân bố thực tế ---
    # Tạo trọng số cho từng giờ trong ngày (0-23h)
    # Giờ cao điểm sáng (7-9h) và chiều (17-19h) có trọng số cao
    hourly_weights = np.array([
        0.5, 0.3, 0.2, 0.2, 0.3, 0.5,   # 0h-5h: đêm khuya, ít người đi
        1.5, 3.0, 3.5, 2.0, 1.8, 2.5,    # 6h-11h: sáng - đi làm, đi học
        2.8, 2.0, 1.5, 1.8, 2.5, 4.0,    # 12h-17h: trưa chiều - tan sở
        3.5, 2.5, 2.0, 1.5, 1.0, 0.7     # 18h-23h: tối - giảm dần
    ])
    # Chuẩn hóa để tổng = 1 (thành xác suất)
    hourly_probs = hourly_weights / hourly_weights.sum()
    
    # --- Chọn ngày giả lập ---
    base_date = datetime(2025, 6, 15)  # Một ngày Chủ Nhật bình thường
    
    for i in range(n):
        # Bước 1: Chọn hotspot theo trọng số
        # Ví dụ: Sân bay có 20% cơ hội được chọn, Quận 1 có 18%...
        hotspot_names = list(HOTSPOTS.keys())
        hotspot_weights = [HOTSPOTS[name][2] for name in hotspot_names]
        chosen_hotspot = np.random.choice(hotspot_names, p=hotspot_weights)
        center_lat, center_lng, _ = HOTSPOTS[chosen_hotspot]
        
        # Bước 2: Thêm nhiễu Gaussian quanh hotspot
        # std=0.008 ≈ 800m bán kính phân tán (không phải ai cũng đứng đúng tâm)
        pickup_lat = np.random.normal(center_lat, 0.008)
        pickup_lng = np.random.normal(center_lng, 0.008)
        
        # Bước 3: Sinh điểm trả khách (dropoff) - cách xa hơn
        # Trung bình cuốc xe dài 3-7km, std lớn hơn
        dropoff_lat = pickup_lat + np.random.normal(0, 0.025)
        dropoff_lng = pickup_lng + np.random.normal(0, 0.025)
        
        # Bước 4: Sinh thời gian đặt xe theo phân bố giờ cao điểm
        hour = np.random.choice(range(24), p=hourly_probs)
        minute = np.random.randint(0, 60)
        request_time = base_date + timedelta(hours=int(hour), minutes=int(minute))
        
        # Bước 5: Chuyển tọa độ GPS -> H3 Index
        # Đây là bước QUAN TRỌNG NHẤT: gán mỗi điểm vào 1 ô lục giác
        pickup_h3 = h3.latlng_to_cell(pickup_lat, pickup_lng, H3_RESOLUTION)
        dropoff_h3 = h3.latlng_to_cell(dropoff_lat, dropoff_lng, H3_RESOLUTION)
        
        records.append({
            "request_id": f"REQ_{i+1:05d}",          # Mã đặt xe: REQ_00001
            "request_time": request_time,              # Thời điểm đặt
            "hour": hour,                              # Giờ (để phân tích)
            "day_of_week": request_time.weekday(),     # 0=Thứ 2, 6=Chủ nhật
            "is_weekend": 1 if request_time.weekday() >= 5 else 0,
            "pickup_lat": round(pickup_lat, 6),        # Vĩ độ đón
            "pickup_lng": round(pickup_lng, 6),        # Kinh độ đón
            "dropoff_lat": round(dropoff_lat, 6),      # Vĩ độ trả
            "dropoff_lng": round(dropoff_lng, 6),      # Kinh độ trả
            "pickup_h3": pickup_h3,                    # Mã H3 ô đón khách
            "dropoff_h3": dropoff_h3,                  # Mã H3 ô trả khách
            "hotspot_area": chosen_hotspot,            # Khu vực hotspot gần nhất
            "is_raining": np.random.choice([0, 1], p=[0.7, 0.3]),  # 30% trời mưa
        })
    
    return pd.DataFrame(records)


def generate_drivers(n=NUM_DRIVERS):
    """
    Sinh dữ liệu vị trí tài xế đang online.
    
    Logic nghiệp vụ:
    - Tài xế phân bố rộng hơn khách (vì họ đang chạy rỗng khắp nơi)
    - Một số tài xế tập trung ở trung tâm (kiếm cuốc dễ hơn)
    - Mỗi tài xế có "persona" hành vi khác nhau
    """
    drivers = []
    
    # Phân loại hành vi tài xế (Driver Personas)
    PERSONAS = {
        "center_hunter":   0.40,   # 40% thích cày cuốc ngắn trung tâm
        "long_distance":   0.25,   # 25% thích cuốc dài, đi xa
        "airport_shuttle":  0.15,  # 15% chuyên đón sân bay
        "flexible":         0.20,  # 20% linh hoạt, đi đâu cũng được
    }
    
    for i in range(n):
        # Chọn persona cho tài xế
        persona = np.random.choice(
            list(PERSONAS.keys()),
            p=list(PERSONAS.values())
        )
        
        # Vị trí ban đầu phụ thuộc persona
        if persona == "center_hunter":
            # Tập trung quanh Quận 1, 3 (bán kính hẹp)
            lat = np.random.normal(10.7800, 0.012)
            lng = np.random.normal(106.6950, 0.012)
        elif persona == "airport_shuttle":
            # Quanh sân bay Tân Sơn Nhất
            lat = np.random.normal(10.8184, 0.010)
            lng = np.random.normal(106.6590, 0.010)
        elif persona == "long_distance":
            # Phân bố rộng khắp thành phố
            lat = np.random.normal(HCM_CENTER_LAT, 0.035)
            lng = np.random.normal(HCM_CENTER_LNG, 0.035)
        else:  # flexible
            lat = np.random.normal(HCM_CENTER_LAT, 0.025)
            lng = np.random.normal(HCM_CENTER_LNG, 0.025)
        
        # Chuyển GPS -> H3 Index
        driver_h3 = h3.latlng_to_cell(lat, lng, H3_RESOLUTION)
        
        # Sinh các chỉ số hiệu suất (KPI) của tài xế
        drivers.append({
            "driver_id": f"DRV_{i+1:04d}",
            "driver_lat": round(lat, 6),
            "driver_lng": round(lng, 6),
            "driver_h3": driver_h3,
            "persona": persona,
            "is_available": np.random.choice([1, 0], p=[0.7, 0.3]),  # 70% đang rảnh
            "rating": round(np.random.uniform(3.5, 5.0), 1),        # Đánh giá 3.5-5.0 sao
            "total_trips_today": np.random.randint(0, 15),           # Đã chạy bao nhiêu cuốc
            "acceptance_rate": round(np.random.uniform(0.6, 1.0), 2),# Tỷ lệ nhận cuốc
            "online_hours": round(np.random.uniform(1, 10), 1),      # Số giờ online hôm nay
        })
    
    return pd.DataFrame(drivers)


def compute_supply_demand_by_h3(rides_df, drivers_df):
    """
    Tính toán Cung - Cầu tại mỗi ô H3.
    
    Đây là TRÁI TIM của bài toán:
    - CẦU (Demand) = Số lượt đặt xe tại ô H3 đó
    - CUNG (Supply) = Số tài xế đang rảnh tại ô H3 đó
    - Chênh lệch = Demand - Supply
      + Dương (>0): THIẾU XE → cần hút tài xế tới (VÙNG ĐỎ trên heatmap)
      + Âm (<0):    THỪA XE → tài xế nên di chuyển đi (VÙNG XANH)
      + Gần 0:      CÂN BẰNG (VÙNG VÀNG)
    """
    # Đếm số request tại mỗi ô H3
    demand = rides_df.groupby("pickup_h3").size().reset_index(name="demand_count")
    
    # Đếm số tài xế đang rảnh tại mỗi ô H3
    available_drivers = drivers_df[drivers_df["is_available"] == 1]
    supply = available_drivers.groupby("driver_h3").size().reset_index(name="supply_count")
    
    # Ghép 2 bảng lại (LEFT JOIN trên tất cả H3 xuất hiện)
    # Merge cả demand và supply, fill 0 cho ô nào không có dữ liệu
    all_h3 = set(demand["pickup_h3"].tolist() + supply["driver_h3"].tolist())
    
    result = []
    for hex_id in all_h3:
        d = demand[demand["pickup_h3"] == hex_id]["demand_count"].sum()
        s = supply[supply["driver_h3"] == hex_id]["supply_count"].sum()
        
        # Lấy tọa độ tâm của ô lục giác để vẽ trên bản đồ
        lat, lng = h3.cell_to_latlng(hex_id)
        
        result.append({
            "h3_index": hex_id,
            "center_lat": round(lat, 6),
            "center_lng": round(lng, 6),
            "demand_count": int(d),            # Số khách đặt xe
            "supply_count": int(s),            # Số tài xế rảnh
            "gap": int(d - s),                 # Chênh lệch: dương = thiếu xe
            "gap_ratio": round(d / max(s, 1), 2),  # Tỉ lệ: >1 = thiếu xe
        })
    
    return pd.DataFrame(result)


# =============================================================================
# MAIN: Chạy tất cả và xuất CSV
# =============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("STEP 1: SINH DỮ LIỆU GIẢ LẬP XANH SM - TP.HCM")
    print("=" * 60)
    
    # 1) Sinh dữ liệu đặt xe
    print("\n📍 Đang sinh 5,000 lượt đặt xe...")
    rides_df = generate_ride_requests()
    rides_df.to_csv("data_ride_requests.csv", index=False)
    print(f"   ✅ Đã tạo {len(rides_df)} ride requests")
    print(f"   📊 Phân bố theo khu vực:")
    print(rides_df["hotspot_area"].value_counts().to_string())
    
    # 2) Sinh dữ liệu tài xế
    print(f"\n🚗 Đang sinh {NUM_DRIVERS} tài xế...")
    drivers_df = generate_drivers()
    drivers_df.to_csv("data_drivers.csv", index=False)
    print(f"   ✅ Đã tạo {len(drivers_df)} drivers")
    print(f"   📊 Phân bố theo persona:")
    print(drivers_df["persona"].value_counts().to_string())
    
    # 3) Tính cung-cầu theo H3
    print("\n🔥 Đang tính Cung-Cầu theo từng ô H3...")
    sd_df = compute_supply_demand_by_h3(rides_df, drivers_df)
    sd_df.to_csv("data_supply_demand_h3.csv", index=False)
    print(f"   ✅ Tổng số ô H3 có hoạt động: {len(sd_df)}")
    print(f"   🔴 Ô THIẾU XE (gap > 0): {len(sd_df[sd_df['gap'] > 0])}")
    print(f"   🟢 Ô THỪA XE (gap < 0):  {len(sd_df[sd_df['gap'] < 0])}")
    print(f"   🟡 Ô CÂN BẰNG (gap = 0): {len(sd_df[sd_df['gap'] == 0])}")
    
    # 4) Xuất H3 boundaries (đường viền lục giác) để vẽ trên bản đồ
    print("\n🗺️ Đang xuất H3 boundaries cho visualization...")
    h3_geojson_features = []
    for _, row in sd_df.iterrows():
        # Lấy tọa độ các đỉnh của hình lục giác
        boundary = h3.cell_to_boundary(row["h3_index"])
        # Chuyển sang GeoJSON format (lng, lat) - ngược với (lat, lng)
        coords = [[lng, lat] for lat, lng in boundary]
        coords.append(coords[0])  # Đóng polygon (điểm cuối = điểm đầu)
        
        feature = {
            "type": "Feature",
            "properties": {
                "h3_index": row["h3_index"],
                "demand": row["demand_count"],
                "supply": row["supply_count"],
                "gap": row["gap"],
                "gap_ratio": row["gap_ratio"],
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [coords]
            }
        }
        h3_geojson_features.append(feature)
    
    geojson = {
        "type": "FeatureCollection",
        "features": h3_geojson_features
    }
    
    with open("data_h3_geojson.json", "w") as f:
        json.dump(geojson, f)
    
    print(f"   ✅ Đã xuất GeoJSON với {len(h3_geojson_features)} hexagons")
    print("\n" + "=" * 60)
    print("📁 Các file đã tạo:")
    print("   - data_ride_requests.csv    (5,000 lượt đặt xe)")
    print("   - data_drivers.csv          (300 tài xế)")
    print("   - data_supply_demand_h3.csv (Cung-Cầu theo H3)")
    print("   - data_h3_geojson.json      (Bản đồ lục giác GeoJSON)")
    print("=" * 60)
