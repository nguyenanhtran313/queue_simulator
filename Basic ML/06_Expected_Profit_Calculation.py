import sys
import json
import pandas as pd
import joblib
import matplotlib.pyplot as plt

sys.stdout.reconfigure(encoding='utf-8')


def main():
    print("--- STEP 6: Expected Profit Calculation (Logistic Regression vs XGBoost vs LightGBM) ---")
    # Biến số kinh doanh (Business Constraints/Assumptions) — kênh gửi khuyến mãi: Zalo ZNS.
    # cost=500đ/tin nhắn gửi THÀNH CÔNG. Tỷ lệ convert trung bình (khách nhận tin -> ra đơn) = 5%
    # (khớp response rate của 00_generate_data.py). Lợi nhuận gộp SAU CÙNG (đã trừ chi phí tin nhắn)
    # trung bình = 100đ/khách hàng được gửi -> suy ra reward (lợi nhuận gộp NẾU khách convert, trước
    # khi trừ chi phí tin) = (100 + cost) / ty_le_convert = (100 + 500) / 5% = 12.000đ.
    # Kiem tra: 5% * 12.000 - 500 = 100 (khop dung gia dinh). Breakeven = cost/reward = 4.17%.
    cost_per_email = 500  # VND — chi phí gửi 1 tin nhắn Zalo ZNS thành công
    reward_per_response = 12000  # VND — lợi nhuận gộp nếu khách phản hồi/convert (trước khi trừ chi phí tin)

    df = pd.read_csv('customer_promo_data.csv')
    X = df.drop(columns=['Customer_ID', 'Historical_Promo_Response', 'Estimated_CLV_VND'])

    try:
        logreg_model = joblib.load('03_logreg_model.pkl')
        xgb_model = joblib.load('04_xgboost_model.pkl')
        lgbm_model = joblib.load('04b_lightgbm_model.pkl')
    except FileNotFoundError:
        print("Model not found. Please run 03_Logistic_Regression_Benchmark.py, 04_XGBoost_Production.py va 04b_LightGBM_Production.py first.")
        return

    # Tính xác suất phản hồi + lợi nhuận kỳ vọng riêng cho từng model, trên TOÀN BỘ khách hàng.
    # Bao gồm CẢ Logistic Regression benchmark — để trả lời thẳng câu hỏi kinh doanh: ROC-AUC nhỉnh
    # hơn của XGBoost/LightGBM có thực sự đổi ra lợi nhuận cao hơn benchmark rẻ tiền/dễ giải thích hay không?
    for prefix, model in [('LOGREG', logreg_model), ('XGB', xgb_model), ('LGBM', lgbm_model)]:
        df[f'{prefix}_Prob'] = model.predict_proba(X)[:, 1]
        df[f'{prefix}_Expected_Profit'] = (df[f'{prefix}_Prob'] * reward_per_response) - cost_per_email
        df[f'{prefix}_Send_Email'] = df[f'{prefix}_Expected_Profit'] > 0

    # --- 4 kịch bản lợi nhuận ---
    total_cost_if_all = int(len(df) * cost_per_email)
    revenue_if_all = int(df['Historical_Promo_Response'].sum() * reward_per_response)
    profit_all = revenue_if_all - total_cost_if_all

    scenarios = {'Mass Marketing (gửi toàn bộ)': {
        'n_send': len(df), 'cost': total_cost_if_all, 'revenue': revenue_if_all, 'profit': profit_all,
    }}

    for prefix, name in [('LOGREG', 'Logistic Regression-optimized'), ('XGB', 'XGBoost-optimized'), ('LGBM', 'LightGBM-optimized')]:
        n_send = int(df[f'{prefix}_Send_Email'].sum())
        cost = n_send * cost_per_email
        revenue = df[df[f'{prefix}_Send_Email']]['Historical_Promo_Response'].sum() * reward_per_response
        profit = revenue - cost
        scenarios[name] = {'n_send': n_send, 'cost': int(cost), 'revenue': int(revenue), 'profit': int(profit)}

    print(f"\nTổng số khách hàng: {len(df)}")
    print(f"\n{'Kịch bản':<32}{'Số KH gửi':>12}{'Chi phí (VND)':>18}{'Doanh thu (VND)':>18}{'Lợi nhuận (VND)':>18}")
    print("-" * 98)
    for name, s in scenarios.items():
        print(f"{name:<32}{s['n_send']:>12,}{s['cost']:>18,}{s['revenue']:>18,}{s['profit']:>18,}")

    best_scenario = max(
        [(name, s) for name, s in scenarios.items() if name != 'Mass Marketing (gửi toàn bộ)'],
        key=lambda kv: kv[1]['profit'],
    )
    print(f"\nChênh lệch lợi nhuận (model tốt nhất - Mass Marketing): "
          f"{best_scenario[1]['profit'] - profit_all:,.0f} VND ({best_scenario[0]})")

    # --- Biểu đồ so sánh lợi nhuận 4 kịch bản ---
    plt.figure(figsize=(9, 5))
    names = list(scenarios.keys())
    profits = [scenarios[n]['profit'] for n in names]
    colors = ['#95a5a6', '#eda100', '#2980b9', '#27ae60']
    plt.bar(names, profits, color=colors)
    plt.ylabel('Lợi nhuận (VND)')
    plt.title('So sánh lợi nhuận: Mass Marketing vs Logistic Regression vs XGBoost vs LightGBM')
    plt.xticks(rotation=15, ha='right')
    for i, p in enumerate(profits):
        plt.text(i, p, f"{p:,.0f}", ha='center', va='bottom' if p >= 0 else 'top')
    plt.tight_layout()
    plt.savefig('06_profit_comparison.png')
    plt.close()
    print("\nSaved 06_profit_comparison.png")

    # Xuất file danh sách chạy Campaign thực tế (đủ cả 3 model để team Marketing tự chọn)
    df[['Customer_ID', 'Historical_Promo_Response',
        'LOGREG_Prob', 'LOGREG_Expected_Profit', 'LOGREG_Send_Email',
        'XGB_Prob', 'XGB_Expected_Profit', 'XGB_Send_Email',
        'LGBM_Prob', 'LGBM_Expected_Profit', 'LGBM_Send_Email']].to_csv('06_campaign_decisions.csv', index=False)
    print("Saved target list to 06_campaign_decisions.csv")

    with open('06_profit_comparison.json', 'w', encoding='utf-8') as f:
        json.dump({
            'cost_per_email': cost_per_email,
            'reward_per_response': reward_per_response,
            'scenarios': scenarios,
            'best_scenario': best_scenario[0],
            'best_scenario_uplift_vs_mass': best_scenario[1]['profit'] - profit_all,
        }, f, indent=2, ensure_ascii=False)
    print("Saved 06_profit_comparison.json")


if __name__ == "__main__":
    main()
