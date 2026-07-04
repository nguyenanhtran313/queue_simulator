import json
import sys

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def main():
    print("--- STEP 1: Exploratory Data Analysis & Statistical Tests ---")
    # Đọc dữ liệu từ file CSV chứa thông tin khách hàng và lịch sử khuyến mãi
    # Giả sử file này được trích xuất ra từ Database CRM của công ty
    df = pd.read_csv('customer_promo_data.csv')

    # 1. Thông tin cơ bản
    # Mục đích: Kiểm tra xem dữ liệu có bị khuyết thiếu (missing/null) không và các thông kê cơ bản (mean, min, max,...)
    # Giả sử cột Age có max là 200, ta sẽ biết ngay có outlier/dữ liệu lỗi để xử lý.
    print(df.info())
    print(df.describe())
    missing_counts = df.isnull().sum()
    total_missing = int(missing_counts.sum())

    # 2. Tỷ lệ phản hồi chung (Overall Response Rate)
    response_rate = df['Historical_Promo_Response'].mean()
    print(f"\nOverall Response Rate: {response_rate:.2%}")

    # 3. Kiểm định thống kê (Statistical Tests)
    print(f"\n--- Statistical Tests (Target: Historical_Promo_Response) ---")

    num_cols = ['Age', 'Avg_Monthly_Balance_VND', 'Txn_Count_3M', 'Txn_Amount_3M_VND', 'App_Logins_3M', 'Promo_Txn_Count_3M', 'Last_Active_Days']
    ttest_results = []
    for col in num_cols:
        group1 = df[df['Historical_Promo_Response'] == 1][col]
        group0 = df[df['Historical_Promo_Response'] == 0][col]
        t_stat, p_val = stats.ttest_ind(group1, group0, equal_var=False)
        sig = bool(p_val < 0.05)
        print(f"\nT-test for {col}: p-value = {p_val:.4f} (Statistically Significant)" if sig else f"T-test for {col}: p-value = {p_val:.4f}")
        ttest_results.append({
            "variable": col, "test": "T-test", "p_value": float(p_val),
            "significant": sig,
            "corr_with_target": float(df[col].corr(df['Historical_Promo_Response'])),
        })

    cat_cols = ['Gender', 'Segment']
    chi2_results = []
    for col in cat_cols:
        contingency_table = pd.crosstab(df[col], df['Historical_Promo_Response'])
        chi2, p_val, dof, expected = stats.chi2_contingency(contingency_table)
        sig = bool(p_val < 0.05)
        print(f"Chi-square for {col}: p-value = {p_val:.4f}")
        chi2_results.append({
            "variable": col, "test": "Chi-square", "p_value": float(p_val),
            "significant": sig, "corr_with_target": None,
        })

    # 4. Correlation Heatmap (Bản đồ nhiệt độ tương quan)
    plt.figure(figsize=(10, 8))
    numeric_df = df[num_cols + ['Historical_Promo_Response', 'Estimated_CLV_VND']]
    corr_matrix = numeric_df.corr()
    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', fmt=".2f")
    plt.title('Correlation Matrix')
    plt.tight_layout()
    plt.savefig('01_correlation_matrix.png')
    print("Saved correlation matrix plot to 01_correlation_matrix.png")

    clv_balance_corr = float(df['Avg_Monthly_Balance_VND'].corr(df['Estimated_CLV_VND']))

    # ---- Lưu kết quả có cấu trúc ra JSON để 09_Build_Presentation.py dùng lại — tránh phải
    # đọc lại console log hoặc hard-code số liệu trong trang trình bày. ----
    describe_stats = df[num_cols].describe().to_dict()

    eda_results = {
        "n_rows": int(len(df)),
        "n_cols": int(df.shape[1]),
        "total_missing_values": total_missing,
        "response_rate": float(response_rate),
        "describe": describe_stats,
        "significance_tests": ttest_results + chi2_results,
        "clv_balance_correlation": clv_balance_corr,
    }
    with open("01_eda_results.json", "w", encoding="utf-8") as f:
        json.dump(eda_results, f, ensure_ascii=False, indent=2)
    print("Saved structured EDA results to 01_eda_results.json")


if __name__ == "__main__":
    main()
