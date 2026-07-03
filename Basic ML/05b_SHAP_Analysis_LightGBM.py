import sys
import numpy as np
import pandas as pd
import shap
import joblib
import matplotlib.pyplot as plt

sys.stdout.reconfigure(encoding='utf-8')


def main():
    print("--- STEP 5b: SHAP Feature Importance Analysis (LightGBM) ---")
    df = pd.read_csv('customer_promo_data.csv')
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
    plt.savefig('05b_shap_summary_bar_lgbm.png')
    plt.close()
    print("- Đã lưu Biểu đồ Bar (Feature Importance) vào 05b_shap_summary_bar_lgbm.png")

    # 2. Dot Plot: Chiều hướng tác động
    plt.figure()
    shap.summary_plot(sv, X_transformed_df, show=False)
    plt.tight_layout()
    plt.savefig('05b_shap_summary_dot_lgbm.png')
    plt.close()
    print("- Đã lưu Biểu đồ Dot (Tác động chiều hướng) vào 05b_shap_summary_dot_lgbm.png")

    # Tìm 2 biến quan trọng nhất để vẽ Dependence Plot
    vals = np.abs(sv).mean(0)
    feature_importance = pd.DataFrame(list(zip(X_transformed_df.columns, vals)), columns=['col_name', 'importance'])
    feature_importance.sort_values(by=['importance'], ascending=False, inplace=True)
    top_feature_1 = feature_importance.iloc[0]['col_name']
    top_feature_2 = feature_importance.iloc[1]['col_name']

    # 3. Dependence Plot cho biến Top 1
    shap.dependence_plot(top_feature_1, sv, X_transformed_df, show=False)
    plt.tight_layout()
    plt.savefig('05b_shap_dependence_top1_lgbm.png')
    plt.close()
    print(f"- Đã lưu Biểu đồ Dependence cho '{top_feature_1}' vào 05b_shap_dependence_top1_lgbm.png")

    # 4. Dependence Plot cho biến Top 2
    shap.dependence_plot(top_feature_2, sv, X_transformed_df, show=False)
    plt.tight_layout()
    plt.savefig('05b_shap_dependence_top2_lgbm.png')
    plt.close()
    print(f"- Đã lưu Biểu đồ Dependence cho '{top_feature_2}' vào 05b_shap_dependence_top2_lgbm.png")

    print("\n" + "=" * 50)
    print("HƯỚNG DẪN ĐỌC BIỂU ĐỒ & KẾT LUẬN (LightGBM):")
    print("=" * 50)
    print("So sánh với bộ ảnh SHAP của XGBoost (05_shap_*_xgb.png): nếu 2 model đồng thuận về")
    print(f"thứ tự quan trọng của {top_feature_1}/{top_feature_2}, đó là bằng chứng mạnh (robust) hơn")
    print("là chỉ tin vào 1 model duy nhất — dùng để thuyết phục stakeholder không rành kỹ thuật.")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    main()
