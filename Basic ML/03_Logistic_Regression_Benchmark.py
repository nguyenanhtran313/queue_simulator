import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, roc_auc_score

def main():
    print("--- STEP 3: Logistic Regression Benchmark ---")
    df = pd.read_csv('customer_promo_data.csv')
    
    # Loại bỏ ID (không mang thông tin dự đoán) và các cột target/dữ liệu tương lai (CLV - Giá trị trọn đời KH không biết trước)
    # Giả sử chúng ta quên drop ID, model có thể coi ID là 1 biến ngẫu nhiên và cố gắng học theo, dẫn tới overfitting vô ích.
    X = df.drop(columns=['Customer_ID', 'Historical_Promo_Response', 'Estimated_CLV_VND'])
    y = df['Historical_Promo_Response'] # Biến mục tiêu: Khách có phản hồi KM không (1/0)
    
    # Chia tập train/test (80% huấn luyện, 20% kiểm tra)
    # stratify=y đảm bảo tỷ lệ phản hồi 1/0 ở 2 tập train/test đều giống nhau.
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # Phân chia loại biến: Số học (continuous) và Phân loại (categorical)
    num_cols = ['Age', 'Avg_Monthly_Balance_VND', 'Txn_Count_3M', 'Txn_Amount_3M_VND', 'App_Logins_3M', 'Promo_Txn_Count_3M', 'Last_Active_Days']
    cat_cols = ['Gender', 'Segment']
    
    # Tạo pipeline tiền xử lý (Preprocessing)
    # - Standard Scaling cho biến số: Đưa về chung hệ quy chiếu.
    # - One-hot Encoding cho biến phân loại: Đổi "Nam"/"Nữ" thành các cột 0/1, do máy tính không hiểu chữ.
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), num_cols),
            ('cat', OneHotEncoder(drop='first'), cat_cols)
        ])
        
    # Tạo pipeline Model cuối
    # Sử dụng Logistic Regression làm model benchmark cơ bản. 
    # class_weight='balanced': Giả sử tỷ lệ mua chỉ có 10%, nếu không có tham số này model sẽ luôn đoán là 0 để ăn 90% accuracy, gây lỗi "mù màu".
    model = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', LogisticRegression(random_state=42, max_iter=1000, class_weight='balanced'))
    ])
    
    # Train model (Học từ dữ liệu quá khứ)
    model.fit(X_train, y_train)
    # Dự đoán trên tập test
    y_pred = model.predict(X_test) # Trả về class 0 hoặc 1
    y_proba = model.predict_proba(X_test)[:, 1] # Trả về xác suất [% mua]
    
    # Đánh giá Model
    # Giả sử ta quan tâm Precision (đoán đúng KH mua để gửi mail) hoặc Recall (không bỏ sót KH mua).
    # ROC-AUC: Điểm đánh giá khả năng phân tách 2 lớp (1=hoàn hảo, 0.5=như tung đồng xu).
    print("\nClassification Report (Logistic Regression Benchmark):")
    print(classification_report(y_test, y_pred))
    print(f"ROC-AUC Score: {roc_auc_score(y_test, y_proba):.4f}")

if __name__ == "__main__":
    main()
