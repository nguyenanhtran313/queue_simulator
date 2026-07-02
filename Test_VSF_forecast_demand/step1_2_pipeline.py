import pandas as pd
import numpy as np
import h3
import lightgbm as lgb
import math
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
import seaborn as sns
import os
import warnings
warnings.filterwarnings('ignore')
import sys
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

# Đảm bảo thư mục lưu trữ tồn tại
output_dir = r"c:\_Antigravity\_AG_playground\Test\output"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

print("=== BƯỚC 1: TẠO DỮ LIỆU MÔ PHỎNG (MOCK DATA) ===")

# 1.1 Khởi tạo Không gian (Spatial - H3 Hexagons)
# Tọa độ trung tâm (VD: Hoàn Kiếm, Hà Nội)
center_lat, center_lng = 21.0285, 105.8542
resolution = 8 # Độ phân giải 8 (khoảng 0.7 km2 mỗi lục giác)

# Tìm hexagon chứa điểm trung tâm
center_hex = h3.latlng_to_cell(center_lat, center_lng, resolution)
# Lấy các hexagon xung quanh (bán kính k=4)
hexagons = list(h3.grid_disk(center_hex, 4))
print(f"-> Tạo không gian thành phố với {len(hexagons)} ô lục giác (hexagons).")

# 1.2 Khởi tạo Thời gian (Temporal)
# 30 ngày, mỗi khoảng (time-slot) 30 phút
days = 30
slots_per_day = 48
total_slots = days * slots_per_day
date_rng = pd.date_range(start='2023-10-01', periods=total_slots, freq='30min')

print(f"-> Tạo dữ liệu thời gian trong {days} ngày, tổng cộng {total_slots} time-slots.")

# 1.3 Tạo dữ liệu Demand (Nhu cầu đặt xe)
# Tạo base_demand ngẫu nhiên cho mỗi hexagon (có khu đông, khu vắng)
np.random.seed(42)
hex_base_demand = {h: np.random.uniform(5, 20) for h in hexagons}

data = []
for i, dt in enumerate(date_rng):
    hour = dt.hour
    minute = dt.minute
    day_of_week = dt.dayofweek
    
    # Tạo curve mượt (smooth curve) bằng phân bố Gaussian
    t = hour + minute / 60.0
    # Baseline
    m = 0.5 
    # Đỉnh sáng (8h)
    m += 2.0 * math.exp(-((t - 8.0)**2) / 2.0)
    # Đỉnh trưa (12h30)
    m += 0.8 * math.exp(-((t - 12.5)**2) / 2.0)
    # Đỉnh chiều tối (18h)
    m += 2.2 * math.exp(-((t - 18.0)**2) / 3.0)
    
    time_multiplier = m
    
    # Cuối tuần ít người đi làm hơn
    if day_of_week >= 5:
        time_multiplier *= 0.7
        
    for hx in hexagons:
        # Nhu cầu = Base * Multiplier * Random Noise
        noise = np.random.normal(1.0, 0.1) # Giảm nhiễu để biểu đồ mượt hơn
        demand = int(hex_base_demand[hx] * time_multiplier * noise)
        demand = max(0, demand) # Không để số âm
        data.append([dt, hx, hour, day_of_week, demand])

df = pd.DataFrame(data, columns=['timestamp', 'hex_id', 'hour', 'day_of_week', 'demand'])
df.to_csv(os.path.join(output_dir, 'mock_demand.csv'), index=False)
print("-> Đã lưu dữ liệu nhu cầu giả lập vào 'mock_demand.csv'.\n")

print("=== BƯỚC 2: XÂY DỰNG MÔ HÌNH DỰ BÁO (FORECASTING) ===")

# 2.1 Feature Engineering (Tạo đặc trưng cho AI học)
print("-> Tạo các đặc trưng trễ (lag features) để dự báo...")
df.sort_values(by=['hex_id', 'timestamp'], inplace=True)

# Lấy nhu cầu của chính hexagon này ở 1 slot, 2 slot, 3 slot trước, và 1 ngày trước
df['lag_1'] = df.groupby('hex_id')['demand'].shift(1)
df['lag_2'] = df.groupby('hex_id')['demand'].shift(2)
df['lag_3'] = df.groupby('hex_id')['demand'].shift(3)
df['lag_48'] = df.groupby('hex_id')['demand'].shift(slots_per_day) # Cùng giờ ngày hôm trước

# Xóa các dòng bị NaN do quá trình shift
df_model = df.dropna()
# Sắp xếp lại theo thời gian để chia train/test hợp lý
df_model.sort_values(by=['timestamp', 'hex_id'], inplace=True)
df_model.reset_index(drop=True, inplace=True)

# 2.2 Huấn luyện mô hình (Training)
features = ['hour', 'day_of_week', 'lag_1', 'lag_2', 'lag_3', 'lag_48']
target = 'demand'

X = df_model[features]
y = df_model[target]

# Chia tập dữ liệu: 80% để train, 20% để test
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, shuffle=False)

print("-> Huấn luyện thuật toán LightGBM...")
model = lgb.LGBMRegressor(n_estimators=100, learning_rate=0.1, random_state=42)
model.fit(X_train, y_train)

# 2.3 Đánh giá mô hình
predictions = model.predict(X_test)
# Đảm bảo không có dự báo âm
predictions = np.maximum(0, predictions)

mae = mean_absolute_error(y_test, predictions)
rmse = np.sqrt(mean_squared_error(y_test, predictions))
print(f"-> Kết quả mô hình:")
print(f"   - Sai số trung bình tuyệt đối (MAE): {mae:.2f} cuốc xe/hexagon/slot")
print(f"   - Sai số toàn phương trung bình (RMSE): {rmse:.2f}")

# 2.4 Trực quan hóa kết quả cho 1 Hexagon ngẫu nhiên trong 2 ngày cuối
test_results = df_model.iloc[X_test.index].copy()
test_results['prediction'] = predictions

sample_hex = test_results['hex_id'].iloc[0]
sample_data = test_results[test_results['hex_id'] == sample_hex].tail(48 * 2) # Lấy 2 ngày
sample_data = sample_data.sort_values('timestamp')

plt.figure(figsize=(14, 6))
sns.set_theme(style="whitegrid")
plt.plot(sample_data['timestamp'], sample_data['demand'], label='Thực tế (Actual)', linewidth=2.5, color='#1f77b4')
plt.plot(sample_data['timestamp'], sample_data['prediction'], label='Dự báo (Predicted)', linewidth=2.5, linestyle='--', color='#ff7f0e')
plt.fill_between(sample_data['timestamp'], sample_data['demand'], alpha=0.1, color='#1f77b4')
plt.title(f'Demand Forecast for Hexagon: {sample_hex}', fontsize=16, fontweight='bold')
plt.xlabel('Thời gian (Time)', fontsize=12)
plt.ylabel('Số lượng cuốc xe (Demand)', fontsize=12)
plt.legend(fontsize=12)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'demand_forecast_chart.png'), dpi=300)
print(f"\n-> Đã vẽ và lưu biểu đồ kết quả vào 'demand_forecast_chart.png'.")
print("Hoàn thành Giai đoạn 1 & 2!")
