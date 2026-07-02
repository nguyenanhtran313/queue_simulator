import numpy as np
import pandas as pd
import h3
import datetime
import random

# Tọa độ giới hạn khu vực trung tâm TP.HCM (Ví dụ: Quận 1, 3, Bình Thạnh)
# Min/Max Latitude và Longitude
LAT_MIN, LAT_MAX = 10.7500, 10.8100
LON_MIN, LON_MAX = 106.6600, 106.7200

def generate_random_coordinates(num_points):
    """Tạo ngẫu nhiên danh sách tọa độ (lat, lon) trong khu vực trung tâm"""
    lats = np.random.uniform(LAT_MIN, LAT_MAX, num_points)
    lons = np.random.uniform(LON_MIN, LON_MAX, num_points)
    return list(zip(lats, lons))

def simulate_data(num_drivers=2000, num_riders=2000, h3_resolution=9):
    """
    Mô phỏng dữ liệu vị trí của Driver và Rider.
    Sử dụng H3 index độ phân giải 8.
    """
    print(f"Bắt đầu mô phỏng: {num_drivers} Drivers, {num_riders} Riders...")
    
    # Sinh dữ liệu Drivers
    driver_coords = generate_random_coordinates(num_drivers)
    drivers = []
    for i, (lat, lon) in enumerate(driver_coords):
        h3_index = h3.latlng_to_cell(lat, lon, h3_resolution)
        status = random.choice(['idle', 'idle', 'busy']) # 2/3 idle
        drivers.append({
            'driver_id': f'D_{i:04d}',
            'lat': lat,
            'lon': lon,
            'h3_index': h3_index,
            'status': status,
            'timestamp': datetime.datetime.now().isoformat()
        })
        
    df_drivers = pd.DataFrame(drivers)
    
    # Sinh dữ liệu Riders (người tìm xe)
    rider_coords = generate_random_coordinates(num_riders)
    riders = []
    for i, (lat, lon) in enumerate(rider_coords):
        h3_index = h3.latlng_to_cell(lat, lon, h3_resolution)
        riders.append({
            'rider_id': f'R_{i:04d}',
            'lat': lat,
            'lon': lon,
            'h3_index': h3_index,
            'timestamp': datetime.datetime.now().isoformat()
        })
        
    df_riders = pd.DataFrame(riders)
    
    # Tính toán Heatmap Real-time (Trạng thái cung/cầu tại mỗi H3 Hexagon)
    # 1. Đếm số lượng khách đang tìm xe mỗi ô
    demand_df = df_riders.groupby('h3_index').size().reset_index(name='demand_count')
    
    # 2. Đếm số lượng xe trống mỗi ô
    idle_drivers = df_drivers[df_drivers['status'] == 'idle']
    supply_df = idle_drivers.groupby('h3_index').size().reset_index(name='supply_count')
    
    # Merge để ra trạng thái lưới
    heatmap_df = pd.merge(demand_df, supply_df, on='h3_index', how='outer').fillna(0)
    heatmap_df['supply_count'] = heatmap_df['supply_count'].astype(int)
    heatmap_df['demand_count'] = heatmap_df['demand_count'].astype(int)
    
    # Chênh lệch: Cầu - Cung
    heatmap_df['gap'] = heatmap_df['demand_count'] - heatmap_df['supply_count']
    
    # Phân loại trạng thái (Nóng / Lạnh)
    def categorize_status(gap):
        if gap > 0: return 'Hot (Thiếu xe)'
        elif gap <= 0: return 'Cold (Thừa xe)'
        else: return 'Balanced (Cân bằng)'
        
    heatmap_df['status'] = heatmap_df['gap'].apply(categorize_status)
    
    print("\n[Mẫu Dữ liệu Drivers]")
    print(df_drivers.head())
    
    print("\n[Mẫu Dữ liệu Heatmap (H3 Index)]")
    print(heatmap_df.sort_values(by='gap', ascending=False).head())
    
    # Lưu ra file CSV
    df_drivers.to_csv('./_Test_VSF_driver_allocation/mock_drivers.csv', index=False)
    df_riders.to_csv('./_Test_VSF_driver_allocation/mock_riders.csv', index=False)
    heatmap_df.to_csv('./_Test_VSF_driver_allocation/realtime_heatmap.csv', index=False)
    print("\nĐã lưu mock_drivers.csv, mock_riders.csv và realtime_heatmap.csv")

if __name__ == "__main__":
    simulate_data()
