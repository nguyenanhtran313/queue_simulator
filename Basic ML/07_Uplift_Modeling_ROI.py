import pandas as pd
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer

def main():
    print("--- STEP 7: Uplift Modeling for ROI Optimization ---")
    # Uplift Modeling giúp tìm ra những KH chỉ giao dịch KHI CÓ KHUYẾN MÃI (Persuadables)
    # Khác với model thông thường (chỉ tìm người dễ mua), Uplift chia làm 4 nhóm:
    # 1. Sure things: Lúc nào cũng mua (Không cần tốn tiền gửi Promo).
    # 2. Lost causes: Chả bao giờ mua (Gửi Promo cũng phí).
    # 3. Sleeping dogs: Gửi Promo có khi họ ghét quá bỏ đi (Do spam).
    # 4. Persuadables: Đang lưỡng lự, có Promo là chốt đơn => Mục tiêu chính của chiến dịch.
    
    # Giả định: Nhóm Treatment (Được can thiệp) = Khách hàng từng có >= 1 giao dịch khuyến mãi (Promo_Txn_Count_3M > 0)
    # Nhóm Control (Không can thiệp) = Khách chưa từng dùng khuyến mãi
    df = pd.read_csv('customer_promo_data.csv')
    df['Treatment'] = (df['Promo_Txn_Count_3M'] > 0).astype(int)
    
    y = df['Historical_Promo_Response']
    X = df.drop(columns=['Customer_ID', 'Historical_Promo_Response', 'Estimated_CLV_VND', 'Treatment', 'Promo_Txn_Count_3M'])
    
    # S-Learner (Single Model): Đưa biến Treatment (0/1) vào làm 1 feature của XGBoost thay vì tách ra 2 model.
    # Mục đích: Máy sẽ học được việc Treatment=1 hay 0 có ảnh hưởng thế nào đến Response, khi các biến khác giữ nguyên.
    X_slearner = X.copy()
    X_slearner['Treatment'] = df['Treatment']
    
    cat_cols = ['Gender', 'Segment']
    preprocessor = ColumnTransformer([('cat', OneHotEncoder(drop='first'), cat_cols)], remainder='passthrough')
    
    X_encoded = preprocessor.fit_transform(X_slearner)
    
    model = XGBClassifier(use_label_encoder=False, eval_metric='logloss', random_state=42)
    model.fit(X_encoded, y)
    
    # Tính Uplift Score cho toàn bộ tập KH (Sức mạnh của khuyến mãi lên quyết định của từng người)
    # Kịch bản 1: Giả sử TẤT CẢ đều được nhận Promo (Treatment = 1), xem xác suất mua là bao nhiêu.
    X_treat_1 = X_slearner.copy()
    X_treat_1['Treatment'] = 1
    prob_treat_1 = model.predict_proba(preprocessor.transform(X_treat_1))[:, 1]
    
    # Kịch bản 2: Giả sử KHÔNG AI nhận Promo (Treatment = 0), xem xác suất mua tự nhiên là bao nhiêu.
    X_treat_0 = X_slearner.copy()
    X_treat_0['Treatment'] = 0
    prob_treat_0 = model.predict_proba(preprocessor.transform(X_treat_0))[:, 1]
    
    # Uplift Score = Hiệu số xác suất mua khi Có KM trừ đi xác suất mua khi Không KM
    # Nếu Điểm > 0: KM có tác dụng kích cầu. (Persuadables)
    # Nếu Điểm ~ 0: KM không có tác dụng, họ đằng nào cũng mua hoặc không. (Sure things / Lost causes)
    # Nếu Điểm < 0: KM làm giảm khả năng mua. (Sleeping dogs)
    df['Uplift_Score'] = prob_treat_1 - prob_treat_0
    
    # Tính Incremental ROI (ROI gia tăng do Uplift)
    # Giả sử chi phí 500đ, Lợi nhuận mang lại 50.000đ
    cost_per_email = 500
    reward_per_response = 50000
    
    # Quyết định: Chỉ gửi mail cho người có Lợi nhuận gia tăng > 0
    # Expected_Incremental_Profit = (Xác suất mua TĂNG THÊM do KM) * Lợi nhuận - Chi phí KM
    df['Expected_Incremental_Profit'] = (df['Uplift_Score'] * reward_per_response) - cost_per_email
    df['Send_Email_Uplift'] = df['Expected_Incremental_Profit'] > 0
    
    print(f"Tổng số KH nên target theo Uplift (Persuadables): {df['Send_Email_Uplift'].sum()}")
    print("\nTop 5 KH đáng gửi Promo nhất (Uplift cao nhất):")
    print(df[['Customer_ID', 'Uplift_Score', 'Expected_Incremental_Profit', 'Send_Email_Uplift']].sort_values(by='Uplift_Score', ascending=False).head())
    
    # Lưu file để chạy campaign Uplift
    df[['Customer_ID', 'Uplift_Score', 'Expected_Incremental_Profit', 'Send_Email_Uplift']].to_csv('07_uplift_decisions.csv', index=False)
    print("\nSaved uplift decisions to 07_uplift_decisions.csv")

if __name__ == "__main__":
    main()
