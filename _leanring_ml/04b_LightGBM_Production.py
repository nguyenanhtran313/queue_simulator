import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from lightgbm import LGBMClassifier
from sklearn.metrics import classification_report, roc_auc_score
import joblib

def main():
    print("--- STEP 4b: LightGBM Production Model (Optimized for Recall) ---")
    df = pd.read_csv('customer_promo_data.csv')
    
    # Chuẩn bị dữ liệu
    X = df.drop(columns=['Customer_ID', 'Historical_Promo_Response', 'Estimated_CLV_VND'])
    y = df['Historical_Promo_Response']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    cat_cols = ['Gender', 'Segment']
    
    # Tiền xử lý cho LightGBM
    preprocessor = ColumnTransformer(
        transformers=[
            ('cat', OneHotEncoder(drop='first'), cat_cols)
        ], remainder='passthrough')
        
    # LGBMClassifier: Thuật toán cực mạnh (thường nhanh hơn XGBoost).
    # ĐỂ TĂNG RECALL: 
    # 1. Dataset của bạn quá bé (chỉ có 800 dòng train). LightGBM mặc định thiết kế cho data hàng triệu dòng nên sẽ bị ngợp. Ta ép nhỏ `num_leaves` và `max_depth`.
    # 2. Ta dùng `class_weight='balanced'` để tự cân bằng tỷ lệ.
    model = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', LGBMClassifier(
            random_state=42, 
            class_weight='balanced',
            n_estimators=100, 
            learning_rate=0.01,
            num_leaves=15,          # Ép nhỏ cây lại cho data ít
            max_depth=4,            # Chống overfit
            min_child_samples=10,   # Data quá bé nên giảm số lượng sample tối thiểu ở lá
            verbose=-1
        ))
    ])
    
    # Huấn luyện model
    model.fit(X_train, y_train)
    y_proba = model.predict_proba(X_test)[:, 1]
    
    # ĐỂ TĂNG RECALL TỐI ĐA: Dịch chuyển Threshold (Ngưỡng quyết định)
    # Mặc định hàm predict() dùng mốc 0.5. Nếu xác suất > 0.5 mới gọi là mua.
    # Bây giờ ta hạ mốc này xuống, ví dụ chỉ cần mô hình nghi ngờ > 0.4 (40%) là ta quyết định GỬI KHUYẾN MÃI luôn (thà giết lầm còn hơn bỏ sót).
    custom_threshold = 0.4
    y_pred = (y_proba >= custom_threshold).astype(int)
    
    # Đánh giá Model
    print(f"\nClassification Report (LightGBM - Threshold = {custom_threshold}):")
    print(classification_report(y_test, y_pred))
    print(f"ROC-AUC Score: {roc_auc_score(y_test, y_proba):.4f}")
    
    # Lưu model
    joblib.dump(model, '04b_lightgbm_model.pkl')
    print("\nSaved production model to 04b_lightgbm_model.pkl")

if __name__ == "__main__":
    main()
