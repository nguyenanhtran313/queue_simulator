import json
import os
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from lightgbm import LGBMClassifier
from sklearn.metrics import classification_report, roc_auc_score
import joblib


def main():
    print("--- STEP 4b: LightGBM Production Model ---")
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
    # REVIEW (data đã lên quy mô lớn, ~80K+ dòng train): LightGBM giờ đúng vào "sân nhà"
    # của nó — thiết kế vốn cho data cỡ lớn. Không cần ép nhỏ num_leaves/max_depth
    # như bản cũ (khi chỉ có 800 dòng train, ép nhỏ để chống overfit); ở quy mô này ta dùng
    # cấu hình tiêu chuẩn (num_leaves=31 mặc định) và tăng n_estimators vì có đủ data để cây
    # học sâu hơn mà không sợ overfit.
    # Ta vẫn dùng `class_weight='balanced'` để tự cân bằng tỷ lệ lớp.
    model = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', LGBMClassifier(
            random_state=42,
            class_weight='balanced',
            n_estimators=300,
            learning_rate=0.05,
            num_leaves=31,          # mặc định LightGBM, phù hợp data lớn
            max_depth=-1,           # không giới hạn, để cây tự học độ sâu cần thiết
            min_child_samples=20,   # mặc định, data lớn không cần giảm nữa
            verbose=-1
        ))
    ])

    # Huấn luyện model
    model.fit(X_train, y_train)
    y_proba = model.predict_proba(X_test)[:, 1]
    y_pred = (y_proba >= 0.5).astype(int)

    # Đánh giá Model
    print("\nClassification Report (LightGBM, threshold = 0.5):")
    print(classification_report(y_test, y_pred))
    print(f"ROC-AUC Score: {roc_auc_score(y_test, y_proba):.4f}")

    # Insight phụ: hạ threshold xuống 0.4 để tăng Recall (thà "giết lầm còn hơn bỏ sót" khi
    # chi phí gửi khuyến mãi rất rẻ so với lợi nhuận nếu khách phản hồi — xem 06_Expected_Profit_Calculation.py).
    y_pred_040 = (y_proba >= 0.4).astype(int)
    report_040 = classification_report(y_test, y_pred_040, output_dict=True)
    report_050 = classification_report(y_test, y_pred, output_dict=True)
    print(f"[Insight phu] Neu ha threshold xuong 0.4: Recall = {report_040['1']['recall']:.2f} "
          f"(so voi {report_050['1']['recall']:.2f} o threshold 0.5)")

    # Lưu model
    joblib.dump(model, '04b_lightgbm_model.pkl')
    print("\nSaved production model to 04b_lightgbm_model.pkl")

    # Xuất dự đoán trên tập test (khớp theo Customer_ID) để 04c_Model_Comparison.py so trực tiếp với XGBoost
    test_customer_ids = df.loc[X_test.index, 'Customer_ID']
    pd.DataFrame({
        'Customer_ID': test_customer_ids.values,
        'y_true': y_test.values,
        'y_proba': y_proba,
    }).to_csv('04b_test_predictions.csv', index=False)
    print("Saved test-set predictions to 04b_test_predictions.csv")

    # Ghi metrics vào model_metrics.json (đọc-sửa-ghi, dùng chung với 03/04/04c)
    report = classification_report(y_test, y_pred, output_dict=True)
    metrics_path = 'model_metrics.json'
    all_metrics = {}
    if os.path.exists(metrics_path):
        with open(metrics_path, 'r', encoding='utf-8') as f:
            all_metrics = json.load(f)
    all_metrics['lightgbm'] = {
        'display_name': 'LightGBM',
        'roc_auc': roc_auc_score(y_test, y_proba),
        'accuracy': report['accuracy'],
        'precision': report['1']['precision'],
        'recall': report['1']['recall'],
        'f1': report['1']['f1-score'],
    }
    with open(metrics_path, 'w', encoding='utf-8') as f:
        json.dump(all_metrics, f, indent=2, ensure_ascii=False)
    print(f"Saved metrics to {metrics_path}")


if __name__ == "__main__":
    main()
