import json
import os
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

    # scale_pos_weight: xử lý mất cân bằng dữ liệu (data có ~15% response=1).
    # Tính động theo tỉ lệ negative/positive của tập train, thay vì hard-code =1 (=vô hiệu hóa).
    neg, pos = (y_train == 0).sum(), (y_train == 1).sum()
    scale_pos_weight = neg / pos

    # XGBClassifier: Thuật toán cực kỳ mạnh cho dữ liệu dạng bảng (Tabular Data).
    # n_estimators/learning_rate vừa phải + subsample/colsample + max_depth nông: tránh overfit lên
    # các biến nhiễu (Age, Gender, Txn_Count_3M...) khi tập train đã lên tới 8,000 dòng.
    model = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', XGBClassifier(
            eval_metric='logloss',
            random_state=42,
            scale_pos_weight=scale_pos_weight,
            n_estimators=300,
            learning_rate=0.05,
            max_depth=4,
            subsample=0.8,
            colsample_bytree=0.8,
            min_child_weight=5,
            reg_lambda=1.0,
        ))
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

    # Xuất dự đoán trên tập test (khớp theo Customer_ID) để 04c_Model_Comparison.py so trực tiếp
    # với LightGBM mà không cần re-split lại (tránh phụ thuộc ngầm vào thứ tự cột/random_state).
    test_customer_ids = df.loc[X_test.index, 'Customer_ID']
    pd.DataFrame({
        'Customer_ID': test_customer_ids.values,
        'y_true': y_test.values,
        'y_proba': y_proba,
    }).to_csv('04_test_predictions.csv', index=False)
    print("Saved test-set predictions to 04_test_predictions.csv")

    # Ghi metrics vào model_metrics.json (đọc-sửa-ghi, dùng chung với 03/04b/04c)
    report = classification_report(y_test, y_pred, output_dict=True)
    metrics_path = 'model_metrics.json'
    all_metrics = {}
    if os.path.exists(metrics_path):
        with open(metrics_path, 'r', encoding='utf-8') as f:
            all_metrics = json.load(f)
    all_metrics['xgboost'] = {
        'display_name': 'XGBoost',
        'roc_auc': roc_auc_score(y_test, y_proba),
        'accuracy': report['accuracy'],
        'precision': report['1']['precision'],
        'recall': report['1']['recall'],
        'f1': report['1']['f1-score'],
        'scale_pos_weight': float(scale_pos_weight),
    }
    with open(metrics_path, 'w', encoding='utf-8') as f:
        json.dump(all_metrics, f, indent=2, ensure_ascii=False)
    print(f"Saved metrics to {metrics_path}")


if __name__ == "__main__":
    main()
