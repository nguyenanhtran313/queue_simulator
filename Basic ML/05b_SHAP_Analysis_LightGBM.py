import pandas as pd
import shap
import joblib
import matplotlib.pyplot as plt

# FIX (review 2026-07-03): file này trước đây là bản copy y hệt 05_SHAP_Analysis.py — vẫn
# load '04_xgboost_model.pkl' và ghi đè lên đúng 4 file PNG của bản XGBoost, nên chưa từng
# thực sự phân tích SHAP cho LightGBM. Nay sửa lại: load '04b_lightgbm_model.pkl' và ghi ra
# 4 file PNG riêng (tiền tố 05b_) để không đụng vào output của 05_SHAP_Analysis.py.

SHAP_SAMPLE_SIZE = 5000  # lấy mẫu ngẫu nhiên để vẽ SHAP, không cần chạy trên toàn bộ
# dữ liệu (xem giải thích tương tự ở 05_SHAP_Analysis.py).


def main():
    print("--- STEP 5b: SHAP Feature Importance Analysis (LightGBM) ---")
    df = pd.read_csv('customer_promo_data.csv')
    if len(df) > SHAP_SAMPLE_SIZE:
        print(f"Lấy mẫu ngẫu nhiên {SHAP_SAMPLE_SIZE:,} dòng để tính SHAP (data gốc {len(df):,} dòng).")
        df = df.sample(n=SHAP_SAMPLE_SIZE, random_state=42)
    X = df.drop(columns=['Customer_ID', 'Historical_Promo_Response', 'Estimated_CLV_VND'])

    # Load model LightGBM đã train từ file
    try:
        model_pipeline = joblib.load('04b_lightgbm_model.pkl')
    except FileNotFoundError:
        print("Error: Model not found. Run 04b_LightGBM_Production.py first.")
        return

    # Transform raw data sang định dạng số đã encode để đưa vào SHAP
    X_transformed = model_pipeline.named_steps['preprocessor'].transform(X)
    feature_names = model_pipeline.named_steps['preprocessor'].get_feature_names_out(X.columns)
    X_transformed_df = pd.DataFrame(X_transformed, columns=feature_names)

    # Dùng TreeExplainer của SHAP cho LightGBM
    lgbm_model = model_pipeline.named_steps['classifier']
    explainer = shap.TreeExplainer(lgbm_model)
    shap_values = explainer.shap_values(X_transformed_df)

    import numpy as np
    # LightGBM binary classifier trả về 1 mảng (không phải list 2 lớp như 1 số bản XGBoost cũ)
    sv = shap_values[1] if isinstance(shap_values, list) else shap_values

    print("\n[Đang tạo biểu đồ...]")
    # 1. Bar Chart: Feature Importance tuyệt đối
    plt.figure()
    shap.summary_plot(shap_values, X_transformed_df, plot_type="bar", show=False)
    plt.tight_layout()
    plt.savefig('05b_shap_summary_bar.png')
    plt.close()
    print("- Đã lưu Biểu đồ Bar (Feature Importance) vào 05b_shap_summary_bar.png")

    # 2. Dot Plot: Chiều hướng tác động
    plt.figure()
    shap.summary_plot(shap_values, X_transformed_df, show=False)
    plt.tight_layout()
    plt.savefig('05b_shap_summary_dot.png')
    plt.close()
    print("- Đã lưu Biểu đồ Dot (Tác động chiều hướng) vào 05b_shap_summary_dot.png")

    # Tìm 2 biến quan trọng nhất để vẽ Dependence Plot
    vals = np.abs(sv).mean(0)
    feature_importance = pd.DataFrame(list(zip(X_transformed_df.columns, vals)), columns=['col_name', 'importance'])
    feature_importance.sort_values(by=['importance'], ascending=False, inplace=True)
    top_feature_1 = feature_importance.iloc[0]['col_name']
    top_feature_2 = feature_importance.iloc[1]['col_name']

    # 3. Dependence Plot cho biến Top 1
    shap.dependence_plot(top_feature_1, sv, X_transformed_df, show=False)
    plt.tight_layout()
    plt.savefig('05b_shap_dependence_top1.png')
    plt.close()
    print(f"- Đã lưu Biểu đồ Dependence cho '{top_feature_1}' vào 05b_shap_dependence_top1.png")

    # 4. Dependence Plot cho biến Top 2
    shap.dependence_plot(top_feature_2, sv, X_transformed_df, show=False)
    plt.tight_layout()
    plt.savefig('05b_shap_dependence_top2.png')
    plt.close()
    print(f"- Đã lưu Biểu đồ Dependence cho '{top_feature_2}' vào 05b_shap_dependence_top2.png")

    print("\n" + "=" * 50)
    print("HƯỚNG DẪN ĐỌC BIỂU ĐỒ & KẾT LUẬN (LightGBM):")
    print("=" * 50)
    print(f"Bước 1 (Nhìn rộng): Xem ảnh '05b_shap_summary_bar.png'. Ta thấy {top_feature_1} và {top_feature_2} là 2 nhân tố đứng đầu.")
    print(f"Bước 2 (Nhìn chiều hướng): Xem ảnh '05b_shap_summary_dot.png'. Tìm dòng chữ {top_feature_1} để xem chiều tác động.")
    print(f"Bước 3 (Nhìn chi tiết ngưỡng): Xem ảnh '05b_shap_dependence_top1.png' (của {top_feature_1}) để tìm 'điểm bùng phát'.")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    main()
