# =============================================================================
# STEP 3: DISPATCH & INCENTIVES ENGINE
# =============================================================================
# Mục tiêu: Xây dựng 2 module chính:
# A) Matching Algorithm: Ghép cặp tài xế - khách tối ưu
# B) Incentive Engine: Tính toán Surge Pricing & Hoa hồng động
#
# Business context:
# → Đây là "bộ não" quyết định: Xe nào đón khách nào? Giá bao nhiêu?
#   Tài xế nào được thưởng thêm để chạy về vùng thiếu xe?
# =============================================================================

import pandas as pd
import numpy as np
import json
import h3
from scipy.optimize import linear_sum_assignment  # Thuật toán Hungarian

np.random.seed(42)

# =============================================================================
# 3.1 MATCHING ALGORITHM (Thuật toán ghép cặp tài xế - khách)
# =============================================================================
# Bài toán: Có N khách đang chờ xe và M tài xế đang rảnh.
# Cần ghép cặp sao cho TỔNG KHOẢNG CÁCH (hoặc thời gian chờ) là NHỎ NHẤT.
#
# So sánh 2 cách:
# 1) GREEDY (Tham lam): Khách nào gần tài xế nhất → ghép luôn.
#    → Đơn giản nhưng KHÔNG tối ưu toàn cục.
#    Ví dụ: Tài xế A gần Khách 1 (1km) VÀ Khách 2 (1.5km),
#           Tài xế B xa Khách 1 (5km) nhưng gần Khách 2 (0.5km).
#           Greedy: A→1, B→2 (tổng: 1 + 0.5 = 1.5km)
#           Nhưng nếu A→2, B→1 thì tổng = 1.5 + 5 = 6.5km → tệ hơn!
#           Greedy may mắn ở đây, nhưng với hàng ngàn cặp, nó thường sai.
#
# 2) HUNGARIAN (Tối ưu toàn cục): Xét TẤT CẢ khả năng ghép cặp,
#    chọn phương án có TỔNG KHOẢNG CÁCH NHỎ NHẤT cho toàn hệ thống.
#    → Đây là cách Uber/Grab sử dụng (có biến thể).

def haversine_km(lat1, lng1, lat2, lng2):
    """Tính khoảng cách km giữa 2 điểm GPS."""
    R = 6371
    dlat = np.radians(lat2 - lat1)
    dlng = np.radians(lng2 - lng1)
    a = np.sin(dlat/2)**2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlng/2)**2
    return R * 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))


def greedy_matching(riders, drivers):
    """
    Thuật toán THAM LAM: Với mỗi khách, tìm tài xế GẦN NHẤT còn rảnh.
    Nhanh nhưng không tối ưu toàn hệ thống.
    """
    assignments = []
    available = set(range(len(drivers)))  # Danh sách tài xế còn rảnh
    
    for i, rider in riders.iterrows():
        best_dist = float("inf")
        best_driver = None
        
        for j in available:
            driver = drivers.iloc[j]
            dist = haversine_km(
                rider["pickup_lat"], rider["pickup_lng"],
                driver["driver_lat"], driver["driver_lng"]
            )
            if dist < best_dist:
                best_dist = dist
                best_driver = j
        
        if best_driver is not None:
            assignments.append({
                "rider_id": rider["request_id"],
                "driver_id": drivers.iloc[best_driver]["driver_id"],
                "distance_km": round(best_dist, 2),
                "eta_minutes": round(best_dist / 30 * 60, 1),  # Giả sử 30km/h
            })
            available.remove(best_driver)
    
    return pd.DataFrame(assignments)


def hungarian_matching(riders, drivers):
    """
    Thuật toán HUNGARIAN (Kuhn-Munkres): Tìm ghép cặp TỐI ƯU TOÀN CỤC.
    
    Cách hoạt động (giải thích cho Business):
    1. Tạo bảng khoảng cách: mỗi ô = khoảng cách từ Tài xế i đến Khách j
    2. Thuật toán thử TẤT CẢ cách ghép cặp có thể
    3. Chọn cách ghép có TỔNG KHOẢNG CÁCH nhỏ nhất
    
    Kết quả: Thời gian chờ TRUNG BÌNH của khách giảm 15-25% so với Greedy.
    """
    n_riders = len(riders)
    n_drivers = len(drivers)
    n = min(n_riders, n_drivers)  # Chỉ ghép được tối đa min(N, M) cặp
    
    # Bước 1: Xây dựng ma trận chi phí (Cost Matrix)
    # cost_matrix[i][j] = khoảng cách từ Tài xế j đến Khách i
    cost_matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            cost_matrix[i][j] = haversine_km(
                riders.iloc[i]["pickup_lat"], riders.iloc[i]["pickup_lng"],
                drivers.iloc[j]["driver_lat"], drivers.iloc[j]["driver_lng"]
            )
    
    # Bước 2: Chạy thuật toán Hungarian
    # Trả về 2 mảng: row_ind[k] ghép với col_ind[k]
    row_ind, col_ind = linear_sum_assignment(cost_matrix)
    
    # Bước 3: Trích xuất kết quả
    assignments = []
    for r, c in zip(row_ind, col_ind):
        dist = cost_matrix[r][c]
        assignments.append({
            "rider_id": riders.iloc[r]["request_id"],
            "driver_id": drivers.iloc[c]["driver_id"],
            "distance_km": round(dist, 2),
            "eta_minutes": round(dist / 30 * 60, 1),
        })
    
    return pd.DataFrame(assignments)


# =============================================================================
# 3.2 INCENTIVE ENGINE (Tính toán Surge Pricing & Hoa hồng)
# =============================================================================

def calculate_surge_pricing(supply_demand_df):
    """
    Tính hệ số Surge Pricing cho từng ô H3.
    
    Logic nghiệp vụ:
    - Surge = hệ số nhân giá cước khi CẦU > CUNG
    - Ví dụ: Cuốc xe bình thường 50,000đ, Surge 1.5x → 75,000đ
    - Tiền tăng thêm (25,000đ) chia cho tài xế nhiều hơn bình thường
      để HÚT tài xế chạy về vùng thiếu xe
    
    Công thức:
    - gap_ratio = demand / supply
    - Nếu gap_ratio <= 1.0: Surge = 1.0 (giá bình thường, đủ xe)
    - Nếu gap_ratio 1.0 - 2.0: Surge = 1.0 + (gap_ratio - 1) * 0.3
    - Nếu gap_ratio 2.0 - 3.0: Surge = 1.3 + (gap_ratio - 2) * 0.5
    - Nếu gap_ratio > 3.0: Surge = cap tại 2.0 (giới hạn tối đa)
    """
    results = []
    
    for _, row in supply_demand_df.iterrows():
        demand = row["demand_count"]
        supply = max(row["supply_count"], 1)  # Tránh chia cho 0
        gap_ratio = demand / supply
        
        # Tính Surge multiplier
        if gap_ratio <= 1.0:
            surge = 1.0
        elif gap_ratio <= 2.0:
            surge = 1.0 + (gap_ratio - 1.0) * 0.3  # Tăng nhẹ: 1.0 → 1.3
        elif gap_ratio <= 3.0:
            surge = 1.3 + (gap_ratio - 2.0) * 0.5  # Tăng mạnh: 1.3 → 1.8
        else:
            surge = 2.0  # Cap tối đa 2x (để không mất khách)
        
        surge = round(surge, 2)
        
        # Tính commission (hoa hồng) cho tài xế
        # Bình thường hãng thu 25% → tài xế nhận 75%
        # Khi Surge, hãng GIẢM chiết khấu để khuyến khích tài xế
        base_commission = 0.25  # Hãng thu 25%
        if surge > 1.0:
            # Giảm commission khi surge: 25% → thấp nhất 10%
            adjusted_commission = max(0.10, base_commission - (surge - 1.0) * 0.15)
        else:
            adjusted_commission = base_commission
        
        # Giá cuốc giả định 50,000đ
        base_fare = 50000
        surged_fare = base_fare * surge
        driver_earning = surged_fare * (1 - adjusted_commission)
        
        results.append({
            "h3_index": row["h3_index"],
            "center_lat": row["center_lat"],
            "center_lng": row["center_lng"],
            "demand": int(demand),
            "supply": int(supply),
            "gap_ratio": round(gap_ratio, 2),
            "surge_multiplier": surge,
            "commission_rate": round(adjusted_commission, 2),
            "base_fare_vnd": base_fare,
            "surged_fare_vnd": int(surged_fare),
            "driver_earning_vnd": int(driver_earning),
            # Phân loại vùng (để hiển thị trên heatmap)
            "zone_type": (
                "HOT" if gap_ratio > 1.5 else
                "WARM" if gap_ratio > 1.0 else
                "BALANCED" if gap_ratio > 0.5 else
                "COLD"
            ),
        })
    
    return pd.DataFrame(results)


def calculate_repositioning_bonus(incentive_df, drivers_df):
    """
    Tính thưởng Repositioning cho tài xế ở vùng THỪA XE.
    
    Logic: Nếu tài xế đang ở vùng COLD (thừa xe) và chịu chạy
    đến vùng HOT (thiếu xe), sẽ được thưởng tiền.
    
    Mức thưởng phụ thuộc khoảng cách di chuyển:
    - < 3km:  20,000đ
    - 3-7km:  40,000đ
    - > 7km:  60,000đ
    """
    # Lấy danh sách vùng HOT (thiếu xe nhất)
    hot_zones = incentive_df[incentive_df["zone_type"] == "HOT"]
    cold_zones = incentive_df[incentive_df["zone_type"] == "COLD"]
    
    bonus_offers = []
    
    for _, driver in drivers_df.iterrows():
        if driver["is_available"] != 1:
            continue
        
        # Kiểm tra xem tài xế có đang ở vùng COLD không
        driver_zone = incentive_df[incentive_df["h3_index"] == driver["driver_h3"]]
        if len(driver_zone) == 0:
            continue
        if driver_zone.iloc[0]["zone_type"] not in ["COLD", "BALANCED"]:
            continue
        
        # Tìm vùng HOT gần nhất
        if len(hot_zones) == 0:
            continue
            
        best_hot = None
        best_dist = float("inf")
        
        for _, hot in hot_zones.iterrows():
            dist = haversine_km(
                driver["driver_lat"], driver["driver_lng"],
                hot["center_lat"], hot["center_lng"]
            )
            if dist < best_dist:
                best_dist = dist
                best_hot = hot
        
        if best_hot is not None and best_dist < 15:  # Trong bán kính 15km
            # Tính mức thưởng
            if best_dist < 3:
                bonus = 20000
            elif best_dist < 7:
                bonus = 40000
            else:
                bonus = 60000
            
            bonus_offers.append({
                "driver_id": driver["driver_id"],
                "driver_h3": driver["driver_h3"],
                "driver_persona": driver["persona"],
                "target_h3": best_hot["h3_index"],
                "target_lat": best_hot["center_lat"],
                "target_lng": best_hot["center_lng"],
                "distance_km": round(best_dist, 2),
                "bonus_vnd": bonus,
                "target_zone_type": best_hot["zone_type"],
                "target_surge": best_hot["surge_multiplier"],
            })
    
    return pd.DataFrame(bonus_offers)


# =============================================================================
# MAIN
# =============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("STEP 3: DISPATCH & INCENTIVE ENGINE")
    print("=" * 60)
    
    # Load data tu Step 1
    rides_df = pd.read_csv("data_ride_requests.csv")
    drivers_df = pd.read_csv("data_drivers.csv")
    sd_df = pd.read_csv("data_supply_demand_h3.csv")
    
    # --- A) So sanh 2 thuat toan Matching ---
    print("\n🔄 SO SANH THUAT TOAN MATCHING:")
    
    # Lay 50 khach va 50 tai xe de demo (Hungarian cham voi n lon)
    sample_riders = rides_df.head(50)
    sample_drivers = drivers_df[drivers_df["is_available"] == 1].head(50)
    
    print(f"   So cap can ghep: {len(sample_riders)} khach x {len(sample_drivers)} tai xe")
    
    # Greedy
    greedy_result = greedy_matching(sample_riders, sample_drivers)
    greedy_avg = greedy_result["distance_km"].mean()
    greedy_total = greedy_result["distance_km"].sum()
    
    # Hungarian
    hungarian_result = hungarian_matching(sample_riders, sample_drivers)
    hungarian_avg = hungarian_result["distance_km"].mean()
    hungarian_total = hungarian_result["distance_km"].sum()
    
    improvement = (greedy_total - hungarian_total) / greedy_total * 100
    
    print(f"\n   📊 Ket qua Greedy (Tham lam):")
    print(f"      Tong khoang cach:  {greedy_total:.1f} km")
    print(f"      Trung binh/cuoc:   {greedy_avg:.2f} km")
    print(f"      ETA trung binh:    {greedy_result['eta_minutes'].mean():.1f} phut")
    
    print(f"\n   📊 Ket qua Hungarian (Toi uu):")
    print(f"      Tong khoang cach:  {hungarian_total:.1f} km")
    print(f"      Trung binh/cuoc:   {hungarian_avg:.2f} km")
    print(f"      ETA trung binh:    {hungarian_result['eta_minutes'].mean():.1f} phut")
    
    print(f"\n   🏆 Hungarian tot hon Greedy: {improvement:.1f}%")
    
    # Luu ket qua
    greedy_result.to_csv("data_matching_greedy.csv", index=False)
    hungarian_result.to_csv("data_matching_hungarian.csv", index=False)
    
    # --- B) Incentive Engine ---
    print("\n\n💰 INCENTIVE ENGINE:")
    
    # Tinh Surge Pricing
    print("\n   Dang tinh Surge Pricing...")
    incentive_df = calculate_surge_pricing(sd_df)
    incentive_df.to_csv("data_incentives.csv", index=False)
    
    surge_zones = incentive_df[incentive_df["surge_multiplier"] > 1.0]
    print(f"   🔴 Vung co Surge:  {len(surge_zones)} o H3")
    print(f"   📈 Surge cao nhat: {incentive_df['surge_multiplier'].max():.2f}x")
    print(f"   💵 Thu nhap tai xe cao nhat: {incentive_df['driver_earning_vnd'].max():,}d/cuoc")
    
    print(f"\n   Phan bo vung:")
    print(incentive_df["zone_type"].value_counts().to_string())
    
    # Tinh Repositioning Bonus
    print("\n   Dang tinh Repositioning Bonus...")
    bonus_df = calculate_repositioning_bonus(incentive_df, drivers_df)
    bonus_df.to_csv("data_repositioning_bonus.csv", index=False)
    
    print(f"   📨 So tai xe duoc de xuat di chuyen: {len(bonus_df)}")
    if len(bonus_df) > 0:
        print(f"   💰 Tong chi phi thuong: {bonus_df['bonus_vnd'].sum():,}d")
        print(f"   📊 Trung binh moi tai xe: {bonus_df['bonus_vnd'].mean():,.0f}d")
    
    print("\n" + "=" * 60)
    print("📁 Cac file da tao:")
    print("   - data_matching_greedy.csv")
    print("   - data_matching_hungarian.csv")
    print("   - data_incentives.csv")
    print("   - data_repositioning_bonus.csv")
    print("=" * 60)
