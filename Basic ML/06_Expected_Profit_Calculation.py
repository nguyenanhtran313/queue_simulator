import pandas as pd
import joblib

def main():
    print("--- STEP 6: Expected Profit Calculation ---")
    # Biến số kinh doanh (Business Constraints/Assumptions) — cập nhật theo context mới:
    # Chi phí gửi 1 tin ZNS promotion là 500 VND/tin/khách hàng.
    # Nếu KH phản hồi, lợi nhuận trung bình mang lại là 10.000 VND/khách hàng.
    cost_per_email = 500  # VND — chi phí gửi ZNS
    reward_per_response = 10000  # VND — lợi nhuận trung bình/khách hàng phản hồi
    
    df = pd.read_csv('customer_promo_data.csv')
    X = df.drop(columns=['Customer_ID', 'Historical_Promo_Response', 'Estimated_CLV_VND'])
    
    # Load model XGBoost
    try:
        model = joblib.load('04_xgboost_model.pkl')
    except FileNotFoundError:
        print("Model not found. Please run 04_XGBoost_Production.py first.")
        return
        
    # Tính xác suất khách hàng sẽ phản hồi dựa vào model (Predict Proba)
    # P(Response): Khả năng mà model nghĩ KH này sẽ bấm vào Promo.
    df['Predicted_Prob'] = model.predict_proba(X)[:, 1]
    
    # Tính Lợi Nhuận Kỳ Vọng (Expected Profit) cho từng KH
    # Công thức toán kỳ vọng: Expected Value = P(Win)*Reward - P(Lose)*Cost. Ở đây ta đơn giản hóa: 
    # Profit = P(Mua)*Lợi nhuận - Chi phí tiếp cận
    df['Expected_Profit'] = (df['Predicted_Prob'] * reward_per_response) - cost_per_email
    
    # Quyết định: Gửi email KH này nếu Lợi nhuận kỳ vọng > 0 (Tức là khoản đầu tư sinh lời).
    # Equivalent to: P(Response) > Cost/Reward = 500/10000 = 5%
    # Nếu model đoán xác suất mua > 5% ta sẽ gửi ZNS, ngược lại thì không.
    df['Send_Email'] = df['Expected_Profit'] > 0
    
    # --- Tính toán ROI Simulation (Đánh giá hiệu quả kinh doanh) ---
    # Kịch bản 1: Gửi toàn bộ (Mass Marketing)
    total_cost_if_all = len(df) * cost_per_email
    revenue_if_all = df['Historical_Promo_Response'].sum() * reward_per_response
    profit_all = revenue_if_all - total_cost_if_all
    
    # Kịch bản 2: Tối ưu hóa bằng ML (Chỉ gửi nhóm Send_Email == True)
    optimized_cost = df['Send_Email'].sum() * cost_per_email
    # Dùng nhãn thực tế để tính revenue mang lại nếu áp dụng cách này
    revenue_optimized = df[df['Send_Email']]['Historical_Promo_Response'].sum() * reward_per_response
    profit_optimized = revenue_optimized - optimized_cost
    
    print(f"Tổng số khách hàng: {len(df)}")
    print(f"Số khách hàng được chọn bởi ML (Expected Profit > 0): {df['Send_Email'].sum()}")
    print(f"\nLợi nhuận nếu GỬI TOÀN BỘ (Mass Marketing): {profit_all:,.0f} VND")
    print(f"Lợi nhuận TỐI ƯU HÓA bằng ML: {profit_optimized:,.0f} VND")
    # Khoản chênh lệch chứng minh giá trị của Model (VND tiết kiệm được + VND kiếm được thêm)
    print(f"Khoản chênh lệch (ROI Increase do áp dụng ML): {profit_optimized - profit_all:,.0f} VND")
    
    # Xuất file danh sách chạy Campaign thực tế
    df[['Customer_ID', 'Predicted_Prob', 'Expected_Profit', 'Send_Email']].to_csv('06_campaign_decisions.csv', index=False)
    print("\nSaved target list to 06_campaign_decisions.csv")

if __name__ == "__main__":
    main()
