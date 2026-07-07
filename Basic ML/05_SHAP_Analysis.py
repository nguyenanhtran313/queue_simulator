import sys
import numpy as np
import pandas as pd
import shap
import joblib
import matplotlib.pyplot as plt

sys.stdout.reconfigure(encoding='utf-8')

SHAP_SAMPLE_SIZE = 5000  # SHAP TreeExplainer chính xác nhưng vẫn tốn O(n) thời gian/bộ nhớ
# theo số dòng -> lấy mẫu ngẫu nhiên là thực hành chuẩn khi vẽ biểu đồ diễn giải
# (summary/dependence plot), không cần chạy trên toàn bộ dữ liệu dù data lớn cỡ nào.


def main():
    print("--- STEP 5: SHAP Feature Importance Analysis (XGBoost) ---")
    df = pd.read_csv('customer_promo_data.csv')
    if len(df) > SHAP_SAMPLE_SIZE:
        print(f"Lấy mẫu ngẫu nhiên {SHAP_SAMPLE_SIZE:,} dòng để tính SHAP (data gốc {len(df):,} dòng).")
        df = df.sample(n=SHAP_SAMPLE_SIZE, random_state=42)
    X = df.drop(columns=['Customer_ID', 'Historical_Promo_Response', 'Estimated_CLV_VND'])

    # Load model XGBoost đã train từ file
    try:
        model_pipeline = joblib.load('04_xgboost_model.pkl')
    except FileNotFoundError:
        print("Error: Model not found. Run 04_XGBoost_Production.py first.")
        return

    # Transform raw data sang định dạng số đã encode để đưa vào SHAP
    X_transformed = model_pipeline.named_steps['preprocessor'].transform(X)
    feature_names = model_pipeline.named_steps['preprocessor'].get_feature_names_out(X.columns)
    X_transformed_df = pd.DataFrame(X_transformed, columns=feature_names)

    # Dùng TreeExplainer của SHAP cho XGBoost
    # Mục đích SHAP: Biến AI từ "Hộp đen" (Black Box) thành "Hộp trong suốt" (White Box).
    xgb_model = model_pipeline.named_steps['classifier']
    explainer = shap.TreeExplainer(xgb_model)
    shap_values = explainer.shap_values(X_transformed_df)

    # Chuẩn hóa shap_values về dạng 2D (n_samples, n_features) — các bản shap khác nhau có thể trả về
    # list (multi-class API cũ) hoặc mảng 3D (n_samples, n_features, n_classes) cho binary classifier mới.
    if isinstance(shap_values, list):
        sv = shap_values[1]
    elif shap_values.ndim == 3:
        sv = shap_values[:, :, 1]
    else:
        sv = shap_values

    print("\n[Đang tạo biểu đồ...]")
    # 1. Bar Chart: Feature Importance tuyệt đối
    plt.figure()
    shap.summary_plot(sv, X_transformed_df, plot_type="bar", show=False)
    plt.tight_layout()
    plt.savefig('05_shap_summary_bar_xgb.png')
    plt.close()
    print("- Đã lưu Biểu đồ Bar (Feature Importance) vào 05_shap_summary_bar_xgb.png")

    # 2. Dot Plot: Chiều hướng tác động
    plt.figure()
    shap.summary_plot(sv, X_transformed_df, show=False)
    plt.tight_layout()
    plt.savefig('05_shap_summary_dot_xgb.png')
    plt.close()
    print("- Đã lưu Biểu đồ Dot (Tác động chiều hướng) vào 05_shap_summary_dot_xgb.png")

    # Tìm 2 biến quan trọng nhất để vẽ Dependence Plot
    vals = np.abs(sv).mean(0)
    feature_importance = pd.DataFrame(list(zip(X_transformed_df.columns, vals)), columns=['col_name', 'importance'])
    feature_importance.sort_values(by=['importance'], ascending=False, inplace=True)
    top_feature_1 = feature_importance.iloc[0]['col_name']
    top_feature_2 = feature_importance.iloc[1]['col_name']

    # 3. Dependence Plot cho biến Top 1
    shap.dependence_plot(top_feature_1, sv, X_transformed_df, show=False)
    plt.tight_layout()
    plt.savefig('05_shap_dependence_top1_xgb.png')
    plt.close()
    print(f"- Đã lưu Biểu đồ Dependence cho '{top_feature_1}' vào 05_shap_dependence_top1_xgb.png")

    # 4. Dependence Plot cho biến Top 2
    shap.dependence_plot(top_feature_2, sv, X_transformed_df, show=False)
    plt.tight_layout()
    plt.savefig('05_shap_dependence_top2_xgb.png')
    plt.close()
    print(f"- Đã lưu Biểu đồ Dependence cho '{top_feature_2}' vào 05_shap_dependence_top2_xgb.png")

    print("\n" + "=" * 50)
    print("HƯỚNG DẪN ĐỌC BIỂU ĐỒ & KẾT LUẬN (XGBoost):")
    print("=" * 50)
    print("Để kết luận insight một cách thuyết phục, ta phối hợp 3 loại biểu đồ như sau:")
    print(f"Bước 1 (Nhìn rộng): Xem ảnh '05_shap_summary_bar_xgb.png'. Ta thấy {top_feature_1} và {top_feature_2} là 2 nhân tố đứng đầu, đóng vai trò quyết định lớn nhất tới việc khách hàng có dùng khuyến mãi hay không.")
    print(f"Bước 2 (Nhìn chiều hướng): Xem ảnh '05_shap_summary_dot_xgb.png'. Tìm dòng chữ {top_feature_1}. Nếu các chấm màu ĐỎ nằm bên PHẢI trục 0, tức là khách hàng có chỉ số {top_feature_1} càng CAO thì xác suất 'chốt đơn' càng TĂNG. Ngược lại nếu ĐỎ nằm bên TRÁI là tác động giảm.")
    print(f"Bước 3 (Nhìn chi tiết ngưỡng): Xem ảnh '05_shap_dependence_top1_xgb.png' (của {top_feature_1}). Biểu đồ này vẽ chính xác từng mức giá trị của khách hàng, giúp tìm 'điểm bùng phát' để lọc tệp khách hàng mục tiêu trong tương lai!")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    main()
