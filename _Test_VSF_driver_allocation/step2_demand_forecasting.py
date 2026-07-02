# =============================================================================
# STEP 2: MACHINE LEARNING - DỰ ĐOÁN NHU CẦU ĐẶT XE (Demand Forecasting)
# =============================================================================
# Mục tiêu: Dùng LightGBM để DỰ ĐOÁN số lượng request đặt xe
# tại mỗi ô H3 trong 30 phút tới.
#
# Tại sao quan trọng cho Business?
# → Nếu biết TRƯỚC nơi nào sắp đông khách, ta có thể:
#   1. Điều tài xế tới sẵn (giảm thời gian chờ cho khách)
#   2. Áp dụng Surge Pricing hợp lý (tăng doanh thu)
#   3. Tối ưu chi phí khuyến mãi (không thưởng tài xế ở vùng đã đủ xe)
# =============================================================================

import pandas as pd
import numpy as np
import json
import h3
from datetime import datetime, timedelta
from sklearn.model_selection import train_test_split   # Chia data train/test
from sklearn.metrics import mean_absolute_error, r2_score  # Đánh giá model
import lightgbm as lgb  # Thuật toán ML nhanh, mạnh cho tabular data

np.random.seed(42)

# =============================================================================
# 2.1 TẠO TẬP DỮ LIỆU LỊCH SỬ (Historical Dataset)
# =============================================================================
# Trong thực tế, data này lấy từ database lịch sử booking.
# Ở đây ta mô phỏng 30 ngày, mỗi ngày chia thành 48 khung 30 phút,
# cho khoảng 50 ô H3 quan trọng nhất.

# Đọc data từ Step 1 để lấy danh sách H3 cells thực tế
sd_df = pd.read_csv("data_supply_demand_h3.csv")
# Chỉ lấy top 50 ô H3 có nhiều hoạt động nhất (để model tập trung)
top_h3_cells = sd_df.nlargest(50, "demand_count")["h3_index"].tolist()

# Định nghĩa các POI (Point of Interest) quan trọng
# Mỗi POI có bán kính ảnh hưởng đến nhu cầu
POIS = {
    "airport":    (10.8184, 106.6590),  # Sân bay
    "center_q1":  (10.7769, 106.7009),  # Quận 1
    "phu_my_hung": (10.7295, 106.7218), # PMH
    "bus_station": (10.8794, 106.8190), # Bến xe
    "university":  (10.8700, 106.8030), # ĐHQG
}

def haversine_km(lat1, lng1, lat2, lng2):
    """
    Tính khoảng cách (km) giữa 2 tọa độ GPS.
    Công thức Haversine - chuẩn cho tọa độ trên mặt cầu Trái Đất.
    Business: Dùng để tính 'ô H3 này cách sân bay bao xa?'
    """
    R = 6371  # Bán kính Trái Đất (km)
    dlat = np.radians(lat2 - lat1)
    dlng = np.radians(lng2 - lng1)
    a = np.sin(dlat/2)**2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlng/2)**2
    return R * 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))


def build_historical_dataset():
    """
    Xây dựng tập dữ liệu lịch sử 30 ngày.
    
    Mỗi dòng = 1 quan sát: "Tại ô H3 X, vào lúc Y giờ, ngày Z, 
                             có bao nhiêu lượt đặt xe?"
    
    Các features (đặc trưng) mà model sẽ học:
    - hour:           Giờ trong ngày (0-23) → giờ cao điểm sẽ đông hơn
    - day_of_week:    Thứ trong tuần (0-6) → cuối tuần khác ngày thường
    - is_weekend:     Có phải cuối tuần không? (0/1)
    - is_raining:     Trời có mưa không? (0/1) → mưa = nhiều người đặt xe hơn
    - dist_to_airport: Khoảng cách đến sân bay (km)
    - dist_to_center:  Khoảng cách đến Q1 (km)
    - lag_1:          Số request ở khung 30 phút TRƯỚC (t-1)
    - lag_2:          Số request ở khung 1 tiếng trước (t-2)
    """
    records = []
    
    # Trọng số giờ (pattern giống Step 1 nhưng cho từng khung 30 phút)
    hourly_base = np.array([
        0.5, 0.3, 0.2, 0.2, 0.3, 0.5,
        1.5, 3.0, 3.5, 2.0, 1.8, 2.5,
        2.8, 2.0, 1.5, 1.8, 2.5, 4.0,
        3.5, 2.5, 2.0, 1.5, 1.0, 0.7
    ])
    
    for h3_cell in top_h3_cells:
        # Tính khoảng cách từ ô H3 này đến các POI
        cell_lat, cell_lng = h3.cell_to_latlng(h3_cell)
        dist_airport = haversine_km(cell_lat, cell_lng, *POIS["airport"])
        dist_center = haversine_km(cell_lat, cell_lng, *POIS["center_q1"])
        dist_phu_my_hung = haversine_km(cell_lat, cell_lng, *POIS["phu_my_hung"])
        
        # Hệ số vùng: ô gần trung tâm/sân bay có nhu cầu cao hơn
        location_factor = max(0.3, 2.0 - dist_center * 0.15)
        
        # Mô phỏng 30 ngày
        for day_offset in range(30):
            base_date = datetime(2025, 5, 16) + timedelta(days=day_offset)
            dow = base_date.weekday()         # 0=Mon, 6=Sun
            is_wkend = 1 if dow >= 5 else 0
            
            # Cuối tuần: nhu cầu tăng 20% (người ta đi chơi nhiều hơn)
            weekend_factor = 1.2 if is_wkend else 1.0
            
            prev_demand = 0  # Biến lag (giá trị khung trước)
            prev_demand_2 = 0
            
            for hour in range(24):
                # Mô phỏng thời tiết: mưa chiều (14-18h) xác suất 40%
                is_rain = 1 if (14 <= hour <= 18 and np.random.random() < 0.4) else (
                    1 if np.random.random() < 0.15 else 0
                )
                
                # Công thức tính nhu cầu giả lập:
                # Base demand = trọng số giờ × hệ số vùng × hệ số cuối tuần
                base = hourly_base[hour] * location_factor * weekend_factor
                
                # Mưa làm tăng nhu cầu 40% (ai cũng muốn gọi xe khi mưa)
                rain_boost = 1.4 if is_rain else 1.0
                
                # Thêm nhiễu ngẫu nhiên để data thực tế hơn
                noise = np.random.normal(0, base * 0.3)
                
                demand = max(0, int(base * rain_boost + noise))
                
                records.append({
                    "h3_index": h3_cell,
                    "date": base_date.strftime("%Y-%m-%d"),
                    "hour": hour,
                    "day_of_week": dow,
                    "is_weekend": is_wkend,
                    "is_raining": is_rain,
                    "dist_to_airport": round(dist_airport, 2),
                    "dist_to_center": round(dist_center, 2),
                    "dist_to_phu_my_hung": round(dist_phu_my_hung, 2),
                    "location_factor": round(location_factor, 2),
                    "lag_1": prev_demand,      # Demand ở giờ trước
                    "lag_2": prev_demand_2,    # Demand ở 2 giờ trước
                    "demand": demand,          # TARGET: số lượng request
                })
                
                prev_demand_2 = prev_demand
                prev_demand = demand
    
    return pd.DataFrame(records)


# =============================================================================
# 2.2 HUẤN LUYỆN MÔ HÌNH LIGHTGBM
# =============================================================================
def train_demand_model(df):
    """
    Huấn luyện mô hình LightGBM để dự đoán demand.
    
    LightGBM là gì? (Giải thích cho Business)
    → Một thuật toán "học máy" rất mạnh, giống như một hệ thống ra quyết định:
      Nó học từ dữ liệu lịch sử hàng ngàn câu hỏi dạng:
      "Nếu là 5h chiều, thứ 6, trời mưa, gần sân bay → có bao nhiêu người đặt xe?"
      Sau khi học xong, nó có thể trả lời câu hỏi tương tự cho tương lai.
    """
    # Chọn các cột sẽ dùng làm INPUT cho model
    feature_cols = [
        "hour",                # Giờ trong ngày
        "day_of_week",         # Thứ trong tuần
        "is_weekend",          # Cuối tuần hay không
        "is_raining",          # Trời mưa hay không
        "dist_to_airport",     # Cách sân bay bao xa
        "dist_to_center",      # Cách Q1 bao xa
        "dist_to_phu_my_hung", # Cách PMH bao xa
        "location_factor",     # Hệ số vùng nóng
        "lag_1",               # Nhu cầu giờ trước
        "lag_2",               # Nhu cầu 2 giờ trước
    ]
    
    X = df[feature_cols]           # Ma trận đầu vào (features)
    y = df["demand"]               # Cột mục tiêu (target)
    
    # Chia data: 80% để học (train), 20% để kiểm tra (test)
    # Giống như: cho sinh viên học 80 câu, rồi thi 20 câu chưa thấy bao giờ
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Cấu hình LightGBM
    model = lgb.LGBMRegressor(
        n_estimators=200,      # Số "cây quyết định" trong rừng
        max_depth=6,           # Độ sâu tối đa mỗi cây (tránh overfitting)
        learning_rate=0.1,     # Tốc độ học (nhỏ = cẩn thận hơn)
        num_leaves=31,         # Số lá tối đa mỗi cây
        min_child_samples=10,  # Ít nhất 10 mẫu mỗi lá (tránh học thuộc)
        random_state=42,
        verbose=-1,            # Tắt log
    )
    
    # Huấn luyện model
    print("   🧠 Đang huấn luyện LightGBM...")
    model.fit(X_train, y_train)
    
    # Đánh giá model trên tập test
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    print(f"   📏 MAE (Sai số trung bình): {mae:.2f} requests")
    print(f"      → Model sai trung bình {mae:.1f} lượt đặt xe mỗi ô H3 mỗi giờ")
    print(f"   📏 R² Score: {r2:.3f}")
    print(f"      → Model giải thích được {r2*100:.1f}% biến động của nhu cầu")
    
    # Feature Importance: Yếu tố nào ảnh hưởng nhất?
    importance = pd.DataFrame({
        "feature": feature_cols,
        "importance": model.feature_importances_
    }).sort_values("importance", ascending=False)
    
    print("\n   📊 Top yếu tố ảnh hưởng đến nhu cầu đặt xe:")
    for _, row in importance.iterrows():
        bar = "█" * int(row["importance"] / importance["importance"].max() * 20)
        print(f"      {row['feature']:25s} {bar} ({row['importance']:.0f})")
    
    return model, feature_cols, importance, X_test, y_test, y_pred


# =============================================================================
# 2.3 DỰ BÁO NHU CẦU CHO 24 GIỜ TỚI
# =============================================================================
def predict_next_24h(model, feature_cols, top_h3_cells):
    """
    Dự báo nhu cầu đặt xe cho 24 giờ tới tại mỗi ô H3.
    
    Business value:
    → Operation Manager mở Dashboard lúc 6h sáng,
      thấy ngay: "8h sáng nay, Sân bay sẽ cần ~50 xe, Q1 cần ~40 xe"
      → Ra quyết định điều xe ngay.
    """
    predictions = []
    predict_date = datetime(2025, 6, 16)  # Ngày dự báo
    dow = predict_date.weekday()
    is_wkend = 1 if dow >= 5 else 0
    
    for h3_cell in top_h3_cells[:30]:  # Top 30 ô quan trọng nhất
        cell_lat, cell_lng = h3.cell_to_latlng(h3_cell)
        dist_airport = haversine_km(cell_lat, cell_lng, *POIS["airport"])
        dist_center = haversine_km(cell_lat, cell_lng, *POIS["center_q1"])
        dist_pmh = haversine_km(cell_lat, cell_lng, *POIS["phu_my_hung"])
        loc_factor = max(0.3, 2.0 - dist_center * 0.15)
        
        prev_demand = 0
        prev_demand_2 = 0
        
        for hour in range(24):
            is_rain = 1 if (14 <= hour <= 18) else 0  # Giả sử chiều mưa
            
            input_data = pd.DataFrame([{
                "hour": hour,
                "day_of_week": dow,
                "is_weekend": is_wkend,
                "is_raining": is_rain,
                "dist_to_airport": dist_airport,
                "dist_to_center": dist_center,
                "dist_to_phu_my_hung": dist_pmh,
                "location_factor": loc_factor,
                "lag_1": prev_demand,
                "lag_2": prev_demand_2,
            }])
            
            pred = max(0, model.predict(input_data)[0])
            
            predictions.append({
                "h3_index": h3_cell,
                "center_lat": round(cell_lat, 6),
                "center_lng": round(cell_lng, 6),
                "hour": hour,
                "predicted_demand": round(pred, 1),
                "is_raining": is_rain,
            })
            
            prev_demand_2 = prev_demand
            prev_demand = pred
    
    return pd.DataFrame(predictions)


# =============================================================================
# MAIN
# =============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("STEP 2: ML DEMAND FORECASTING - DU DOAN NHU CAU")
    print("=" * 60)
    
    # 1) Xây dựng dataset lịch sử
    print("\n📚 Dang xay dung tap du lieu lich su 30 ngay...")
    hist_df = build_historical_dataset()
    hist_df.to_csv("data_historical_demand.csv", index=False)
    print(f"   Da tao {len(hist_df):,} dong du lieu lich su")
    
    # 2) Train model
    print("\n🤖 HUAN LUYEN MO HINH:")
    model, feat_cols, importance, X_test, y_test, y_pred = train_demand_model(hist_df)
    
    # Lưu kết quả đánh giá
    eval_df = pd.DataFrame({"actual": y_test, "predicted": y_pred})
    eval_df.to_csv("data_model_evaluation.csv", index=False)
    importance.to_csv("data_feature_importance.csv", index=False)
    
    # 3) Dự báo 24h tới
    print("\n🔮 DU BAO NHU CAU 24H TOI:")
    forecast_df = predict_next_24h(model, feat_cols, top_h3_cells)
    forecast_df.to_csv("data_demand_forecast_24h.csv", index=False)
    
    # Tổng hợp dự báo theo giờ
    hourly_summary = forecast_df.groupby("hour")["predicted_demand"].sum().reset_index()
    print("\n   Tong nhu cau du bao theo gio:")
    for _, row in hourly_summary.iterrows():
        bar = "█" * int(row["predicted_demand"] / hourly_summary["predicted_demand"].max() * 30)
        print(f"   {int(row['hour']):02d}:00  {bar} {row['predicted_demand']:.0f} requests")
    
    print(f"\n   Da luu du bao vao: data_demand_forecast_24h.csv")
    print("=" * 60)
