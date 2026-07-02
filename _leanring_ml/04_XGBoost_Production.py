import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier
from sklearn.metrics import classification_report, roc_auc_score
import joblib

def main():
    print("--- STEP 4: XGBoost Production Model ---")
    df = pd.read_csv('customer_promo_data.csv')
    
    # Bước chuẩn bị dữ liệu (tương tự như Logistic Regression)
    X = df.drop(columns=['Customer_ID', 'Historical_Promo_Response', 'Estimated_CLV_VND'])
    y = df['Historical_Promo_Response']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    cat_cols = ['Gender', 'Segment']
    
    # Tiền xử lý cho XGBoost
    # Ưu điểm XGBoost (Tree-based model) là nó xử lý tốt các biến số không cần scale (không cần StandardScaler).
    # Nó chỉ cần encode các biến phân loại thành dạng số. Do đó pipeline gọn nhẹ hơn.
    # Nó có thể bắt được các tương quan phi tuyến (non-linear).
    preprocessor = ColumnTransformer(
        transformers=[
            ('cat', OneHotEncoder(drop='first'), cat_cols)
        ], remainder='passthrough')
        
    # XGBClassifier: Thuật toán cực kỳ mạnh cho dữ liệu dạng bảng (Tabular Data).
    # scale_pos_weight: Dùng để xử lý mất cân bằng dữ liệu thay vì class_weight như Logistic.
    model = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', XGBClassifier(use_label_encoder=False, eval_metric='logloss', random_state=42, scale_pos_weight=1))
    ])
    
    # Huấn luyện model
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]
    
    # Đánh giá Model: Thường XGBoost sẽ có ROC-AUC cao hơn hẳn Logistic Regression
    print("\nClassification Report (XGBoost):")
    print(classification_report(y_test, y_pred))
    print(f"ROC-AUC Score: {roc_auc_score(y_test, y_proba):.4f}")
    
    # Lưu model cho các bước chạy thực tế (Production/Simulation)
    # Giả sử hàng ngày chạy model này để dự đoán KH mới thì chỉ cần load file .pkl ra dùng, không cần train lại.
    joblib.dump(model, '04_xgboost_model.pkl')
    print("\nSaved production model to 04_xgboost_model.pkl")

if __name__ == "__main__":
    main()
