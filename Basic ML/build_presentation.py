"""
Đọc toàn bộ artifact do 00_generate_data.py -> 07_Uplift_Modeling_ROI.py sinh ra
(KHÔNG train lại gì cả) và dựng thành 1 file presentation.html tự chứa (self-contained),
phong cách Google Analytics, trình bày như 1 buổi phỏng vấn Data/ML chuyên nghiệp.

Chạy sau khi đã chạy xong (thứ tự bất kỳ, miễn là 04/04b chạy trước 04c/05/05b/06):
    00_generate_data.py, 01_EDA_and_Stats.py, 02_KMeans_Segmentation.py,
    03_Logistic_Regression_Benchmark.py, 04_XGBoost_Production.py,
    04b_LightGBM_Production.py, 04c_Model_Comparison.py, 05_SHAP_Analysis.py,
    05b_SHAP_Analysis_LightGBM.py, 06_Expected_Profit_Calculation.py,
    07_Uplift_Modeling_ROI.py, 07b_Uplift_Modeling_ROI_LightGBM.py
"""
import sys
import os
import json
import base64
import pandas as pd
import numpy as np
from sklearn.metrics import roc_curve, precision_recall_curve, confusion_matrix

sys.stdout.reconfigure(encoding='utf-8')

REQUIRED_FILES = [
    'customer_promo_data.csv',
    'customer_promo_data_clustered.csv',
    'model_metrics.json',
    'model_comparison_summary.json',
    '04_test_predictions.csv',
    '04b_test_predictions.csv',
    '06_profit_comparison.json',
    '06_campaign_decisions.csv',
    '07_uplift_decisions.csv',
    '07b_uplift_decisions.csv',
]

IMAGES = {
    'correlation':        '01_correlation_matrix.png',
    'kmeans_eval':         '02_kmeans_evaluation.png',
    'roc_comparison':      '04c_roc_comparison.png',
    'pr_comparison':       '04c_pr_comparison.png',
    'confusion_matrices':  '04c_confusion_matrices.png',
    'feature_importance':  '04c_feature_importance_comparison.png',
    'shap_bar_xgb':        '05_shap_summary_bar_xgb.png',
    'shap_dot_xgb':        '05_shap_summary_dot_xgb.png',
    'shap_dep1_xgb':       '05_shap_dependence_top1_xgb.png',
    'shap_dep2_xgb':       '05_shap_dependence_top2_xgb.png',
    'shap_bar_lgbm':       '05b_shap_summary_bar_lgbm.png',
    'shap_dot_lgbm':       '05b_shap_summary_dot_lgbm.png',
    'shap_dep1_lgbm':      '05b_shap_dependence_top1_lgbm.png',
    'shap_dep2_lgbm':      '05b_shap_dependence_top2_lgbm.png',
}

STEP_HINT = {
    'customer_promo_data.csv': 'python 00_generate_data.py',
    'customer_promo_data_clustered.csv': 'python 02_KMeans_Segmentation.py',
    'model_metrics.json': 'python 03_Logistic_Regression_Benchmark.py (+ 04, 04b)',
    'model_comparison_summary.json': 'python 04c_Model_Comparison.py',
    '04_test_predictions.csv': 'python 04_XGBoost_Production.py',
    '04b_test_predictions.csv': 'python 04b_LightGBM_Production.py',
    '06_profit_comparison.json': 'python 06_Expected_Profit_Calculation.py',
    '06_campaign_decisions.csv': 'python 06_Expected_Profit_Calculation.py',
    '07_uplift_decisions.csv': 'python 07_Uplift_Modeling_ROI.py',
    '07b_uplift_decisions.csv': 'python 07b_Uplift_Modeling_ROI_LightGBM.py',
}


def check_requirements():
    missing = [f for f in REQUIRED_FILES if not os.path.exists(f)]
    if missing:
        print("Chưa đủ artifact để dựng presentation. Hãy chạy trước:")
        for f in missing:
            print(f"  - {f}  <-  {STEP_HINT.get(f, '?')}")
        raise SystemExit(1)


def b64_img(path):
    if not os.path.exists(path):
        return None
    with open(path, 'rb') as f:
        return base64.b64encode(f.read()).decode('ascii')


def fmt_vnd(x):
    return f"{x:,.0f}"


def fmt_pct(x):
    return f"{x * 100:.1f}%"


def main():
    print("--- Đang dựng presentation.html (phong cách Google Analytics) ---")
    check_requirements()

    df = pd.read_csv('customer_promo_data.csv')
    clustered_df = pd.read_csv('customer_promo_data_clustered.csv')
    with open('model_metrics.json', encoding='utf-8') as f:
        metrics = json.load(f)
    with open('model_comparison_summary.json', encoding='utf-8') as f:
        comparison = json.load(f)
    with open('06_profit_comparison.json', encoding='utf-8') as f:
        profit = json.load(f)
    uplift_df = pd.read_csv('07_uplift_decisions.csv')
    uplift_lgbm_df = pd.read_csv('07b_uplift_decisions.csv')

    # ---------- KPI tong quan ----------
    n_customers = len(df)
    response_rate = df['Historical_Promo_Response'].mean()
    n_features = df.drop(columns=['Customer_ID', 'Historical_Promo_Response', 'Estimated_CLV_VND']).shape[1]
    # "Model tot nhat theo ROC-AUC" (thong ke) va "Model khuyen nghi trien khai theo ROI" (kinh doanh)
    # co the LA 2 MODEL KHAC NHAU — day chinh la insight quan trong nhat cua ca bai phan tich, xem card
    # "Chon Model Nao?" o tab So sanh Model va tab Business Impact.
    best_model_by_auc_name = comparison['best_model_by_auc_name']
    best_model_by_auc_auc = metrics[comparison['best_model_by_auc_key']]['roc_auc']
    lr_auc = metrics['logistic_regression']['roc_auc']
    best_model_by_profit_name = profit['best_scenario'].replace('-optimized', '')

    # ---------- EDA: phan bo Segment ----------
    seg_stats = df.groupby('Segment')['Historical_Promo_Response'].agg(['count', 'mean']).reset_index()
    seg_stats = seg_stats.sort_values('mean', ascending=False)
    seg_labels = seg_stats['Segment'].tolist()
    seg_counts = seg_stats['count'].astype(int).tolist()
    seg_rates = (seg_stats['mean'] * 100).round(1).tolist()
    seg_top_name, seg_top_rate = seg_labels[0], seg_rates[0]
    seg_bottom_name, seg_bottom_rate = seg_labels[-1], seg_rates[-1]
    seg_ratio = round(seg_top_rate / seg_bottom_rate, 1) if seg_bottom_rate else 0

    # ---------- Segmentation: cluster profile ----------
    cluster_profile = clustered_df.groupby('Cluster').agg(
        size=('Customer_ID', 'count'),
        promo=('Promo_Txn_Count_3M', 'mean'),
        last_active=('Last_Active_Days', 'mean'),
        balance=('Avg_Monthly_Balance_VND', 'mean'),
        response=('Historical_Promo_Response', 'mean'),
    ).reset_index().sort_values('response', ascending=False)

    persona_names = {}
    for _, row in cluster_profile.iterrows():
        if row['promo'] >= 1.5:
            persona_names[row['Cluster']] = 'VIP Tích Cực (High-Value Promo Lovers)'
        elif row['last_active'] < 35:
            persona_names[row['Cluster']] = 'Mới Quay Lại (Recently Active)'
        else:
            persona_names[row['Cluster']] = 'Ngủ Đông (Dormant / At-Risk)'

    cluster_rows_html = ""
    for _, row in cluster_profile.iterrows():
        cluster_rows_html += f"""
        <tr>
          <td>{persona_names[row['Cluster']]}</td>
          <td class="num">{int(row['size']):,}</td>
          <td class="num">{row['promo']:.2f}</td>
          <td class="num">{row['last_active']:.0f} ngày</td>
          <td class="num">{fmt_vnd(row['balance'])} VND</td>
          <td class="num"><span class="pill {'pill-good' if row['response'] > response_rate else 'pill-muted'}">{fmt_pct(row['response'])}</span></td>
        </tr>"""

    persona_best_name = persona_names[cluster_profile.iloc[0]['Cluster']].split(' (')[0]
    persona_worst_row = cluster_profile.iloc[-1]
    persona_worst_name = persona_names[persona_worst_row['Cluster']].split(' (')[0]
    persona_gap_ratio = round(cluster_profile.iloc[0]['response'] / persona_worst_row['response'], 1) if persona_worst_row['response'] else 0

    # ---------- Model comparison: ROC & PR curve (tinh lai tu raw predictions de ve interactive) ----------
    xgb_pred = pd.read_csv('04_test_predictions.csv')
    lgbm_pred = pd.read_csv('04b_test_predictions.csv').rename(columns={'y_proba': 'lgbm_proba'})
    merged = xgb_pred.rename(columns={'y_proba': 'xgb_proba'}).merge(
        lgbm_pred[['Customer_ID', 'lgbm_proba']], on='Customer_ID', how='inner')
    y_true = merged['y_true'].values

    def roc_points(proba, step=1):
        fpr, tpr, _ = roc_curve(y_true, proba)
        idx = np.linspace(0, len(fpr) - 1, min(len(fpr), 120)).astype(int)
        return [{'x': round(float(fpr[i]), 4), 'y': round(float(tpr[i]), 4)} for i in idx]

    def pr_points(proba):
        prec, rec, _ = precision_recall_curve(y_true, proba)
        idx = np.linspace(0, len(prec) - 1, min(len(prec), 120)).astype(int)
        return [{'x': round(float(rec[i]), 4), 'y': round(float(prec[i]), 4)} for i in idx]

    roc_xgb = roc_points(merged['xgb_proba'].values)
    roc_lgbm = roc_points(merged['lgbm_proba'].values)
    pr_xgb = pr_points(merged['xgb_proba'].values)
    pr_lgbm = pr_points(merged['lgbm_proba'].values)

    # Confusion matrix tinh chinh xac tu du lieu (khong doc so bang mat tren anh PNG) de dua so
    # that vao phan "Nhan dinh" — cm[0,0]=TN, cm[0,1]=FP, cm[1,0]=FN, cm[1,1]=TP
    cm_xgb = confusion_matrix(y_true, (merged['xgb_proba'].values >= 0.5).astype(int))
    cm_lgbm = confusion_matrix(y_true, (merged['lgbm_proba'].values >= 0.5).astype(int))
    xgb_fp, xgb_fn = int(cm_xgb[0, 1]), int(cm_xgb[1, 0])
    lgbm_fp, lgbm_fn = int(cm_lgbm[0, 1]), int(cm_lgbm[1, 0])

    # ---------- Business impact ----------
    scenarios = profit['scenarios']
    scenario_names = list(scenarios.keys())
    scenario_profits = [scenarios[n]['profit'] for n in scenario_names]
    mass_profit = scenarios['Mass Marketing (gửi toàn bộ)']['profit']

    def roi_multiple(p):
        return f"{p / mass_profit:.2f}x" if mass_profit else "N/A"

    profit_rows_html = ""
    for name, s in scenarios.items():
        profit_rows_html += f"""
        <tr>
          <td>{name}</td>
          <td class="num">{s['n_send']:,}</td>
          <td class="num">{fmt_vnd(s['cost'])}</td>
          <td class="num">{fmt_vnd(s['revenue'])}</td>
          <td class="num"><b>{fmt_vnd(s['profit'])}</b></td>
          <td class="num">{roi_multiple(s['profit'])}</td>
        </tr>"""

    # ---------- Card "Chon Model Nao?": ghep metric phan loai + ROI thuc te cho ca 3 model ----------
    model_select_map = [
        ('logistic_regression', 'Logistic Regression-optimized'),
        ('xgboost', 'XGBoost-optimized'),
        ('lightgbm', 'LightGBM-optimized'),
    ]
    model_select_rows_html = ""
    for metric_key, scenario_key in model_select_map:
        m = metrics[metric_key]
        s = scenarios[scenario_key]
        is_profit_best = scenario_key == profit['best_scenario']
        model_select_rows_html += f"""
        <tr class="{'row-best' if is_profit_best else ''}">
          <td>{m['display_name']}{' <span class="pill pill-good">Lợi nhuận cao nhất</span>' if is_profit_best else ''}</td>
          <td class="num">{m['roc_auc']:.4f}</td>
          <td class="num">{fmt_pct(m['precision'])}</td>
          <td class="num">{fmt_pct(m['recall'])}</td>
          <td class="num">{s['n_send']:,}</td>
          <td class="num"><b>{fmt_vnd(s['profit'])}</b></td>
          <td class="num">{roi_multiple(s['profit'])}</td>
        </tr>"""

    lr_scn = scenarios['Logistic Regression-optimized']
    xgb_scn = scenarios['XGBoost-optimized']
    lgbm_scn = scenarios['LightGBM-optimized']
    lgbm_vs_xgb_gain = lgbm_scn['profit'] - xgb_scn['profit']
    lgbm_vs_lr_gain = lgbm_scn['profit'] - lr_scn['profit']
    lr_excluded_n = n_customers - lr_scn['n_send']
    xgb_excluded_n = n_customers - xgb_scn['n_send']
    lgbm_excluded_n = n_customers - lgbm_scn['n_send']

    # ---------- Chon classifier "can bang": vua loi nhuan cao, vua accuracy/recall tot (yeu cau nguoi
    # dung — khong argmax loi nhuan thuan tuy, vi mot model chi toi uu loi nhuan co the bo sot qua nhieu
    # khach hang thuc su se convert, gay hai ve lau dai neu tai su dung model cho muc dich khac). Quy tac:
    # trong 2 model tree-based (ca 2 deu vuot xa Logistic Regression moi mat), neu chenh lech loi nhuan
    # giua chung < 10% thi uu tien model co Recall cao hon; nguoc lai uu tien loi nhuan. ----------
    profit_gap_xgb_lgbm_pct = abs(xgb_scn['profit'] - lgbm_scn['profit']) / max(xgb_scn['profit'], lgbm_scn['profit'], 1)
    if profit_gap_xgb_lgbm_pct < 0.10 and metrics['xgboost']['recall'] >= metrics['lightgbm']['recall']:
        recommended_classifier_key, recommended_classifier_scn = 'xgboost', xgb_scn
    elif profit_gap_xgb_lgbm_pct < 0.10 and metrics['lightgbm']['recall'] > metrics['xgboost']['recall']:
        recommended_classifier_key, recommended_classifier_scn = 'lightgbm', lgbm_scn
    elif lgbm_scn['profit'] >= xgb_scn['profit']:
        recommended_classifier_key, recommended_classifier_scn = 'lightgbm', lgbm_scn
    else:
        recommended_classifier_key, recommended_classifier_scn = 'xgboost', xgb_scn
    recommended_classifier_name = metrics[recommended_classifier_key]['display_name']

    # ---------- Uplift: 2 base learner song song (S-learner XGBoost = Buoc 7, S-learner LightGBM = Buoc 7b) ----------
    breakeven = profit['cost_per_email'] / profit['reward_per_response']

    def uplift_summary(u_df):
        persuadables = u_df[u_df['Send_Email_Uplift']]
        n_sleeping_dogs = int((u_df['Uplift_Score'] < 0).sum())
        n_below_breakeven = int(((u_df['Uplift_Score'] >= 0) & (u_df['Uplift_Score'] < breakeven)).sum())
        return {
            'n': len(persuadables),
            'profit': persuadables['Expected_Incremental_Profit'].sum(),
            'sleeping_dogs': n_sleeping_dogs,
            'below_breakeven': n_below_breakeven,
        }

    def top10_html(u_df):
        rows = ""
        for _, row in u_df.sort_values('Uplift_Score', ascending=False).head(10).iterrows():
            rows += f"""
        <tr>
          <td>{row['Customer_ID']}</td>
          <td class="num">{row['Uplift_Score']:.3f}</td>
          <td class="num">{fmt_vnd(row['Expected_Incremental_Profit'])} VND</td>
        </tr>"""
        return rows

    xgb_uplift = uplift_summary(uplift_df)
    lgbm_uplift = uplift_summary(uplift_lgbm_df)
    top10_rows_html = top10_html(uplift_df)
    top10_lgbm_rows_html = top10_html(uplift_lgbm_df)

    # Model nao thang ve loi nhuan nhan qua se la khuyen nghi chinh; model con lai la doi chieu/kiem chung
    best_uplift_is_lgbm = lgbm_uplift['profit'] > xgb_uplift['profit']
    best_uplift_name = 'LightGBM' if best_uplift_is_lgbm else 'XGBoost'
    n_persuadables = lgbm_uplift['n'] if best_uplift_is_lgbm else xgb_uplift['n']
    total_incremental_profit = lgbm_uplift['profit'] if best_uplift_is_lgbm else xgb_uplift['profit']

    # Muc do dong thuan giua 2 base learner (tuong tu 04c da lam voi model phan loai)
    uplift_compare = uplift_df[['Customer_ID', 'Uplift_Score', 'Send_Email_Uplift']].merge(
        uplift_lgbm_df[['Customer_ID', 'Uplift_Score', 'Send_Email_Uplift']],
        on='Customer_ID', suffixes=('_xgb', '_lgbm'))
    uplift_agree_rate = (uplift_compare['Send_Email_Uplift_xgb'] == uplift_compare['Send_Email_Uplift_lgbm']).mean()
    uplift_corr = uplift_compare['Uplift_Score_xgb'].corr(uplift_compare['Uplift_Score_lgbm'])
    n_both_persuadable = int((uplift_compare['Send_Email_Uplift_xgb'] & uplift_compare['Send_Email_Uplift_lgbm']).sum())
    n_only_xgb_persuadable = int((uplift_compare['Send_Email_Uplift_xgb'] & ~uplift_compare['Send_Email_Uplift_lgbm']).sum())
    n_only_lgbm_persuadable = int((~uplift_compare['Send_Email_Uplift_xgb'] & uplift_compare['Send_Email_Uplift_lgbm']).sum())

    uplift_compare_rows_html = ""
    for label, s, is_best in [('S-Learner XGBoost (Bước 7)', xgb_uplift, not best_uplift_is_lgbm),
                               ('S-Learner LightGBM (Bước 7b)', lgbm_uplift, best_uplift_is_lgbm)]:
        uplift_compare_rows_html += f"""
        <tr class="{'row-best' if is_best else ''}">
          <td>{label}{' <span class="pill pill-good">Đề xuất</span>' if is_best else ''}</td>
          <td class="num">{s['n']:,}</td>
          <td class="num">{fmt_pct(s['n'] / len(uplift_df))}</td>
          <td class="num">{s['sleeping_dogs']:,}</td>
          <td class="num">{s['below_breakeven']:,}</td>
          <td class="num"><b>{fmt_vnd(s['profit'])}</b></td>
        </tr>"""

    # ---------- Causal Reality Check: loi nhuan "so sach" (Buoc 6) vs loi nhuan NHAN QUA thuc (Uplift) ----------
    # O muc chi phi lien he re (500d) so voi loi nhuan (50,000d), breakeven chi 1% nen 3 model phan loai
    # (LogReg/XGBoost/LightGBM) deu hoi tu ve gan nhu "gui het" — khong tao khac biet loi nhuan dang ke.
    # Diem khac biet thuc su nam o Uplift: bang cach LOAI RA dung nhom co Uplift Score am/qua thap, ca 2
    # base learner deu cho loi nhuan NHAN QUA cao hon Mass Marketing, du lien he IT nguoi hon.
    camp_df = pd.read_csv('06_campaign_decisions.csv')
    causal_merged = (camp_df
                     .merge(uplift_df[['Customer_ID', 'Uplift_Score']].rename(columns={'Uplift_Score': 'Uplift_XGB'}), on='Customer_ID')
                     .merge(uplift_lgbm_df[['Customer_ID', 'Uplift_Score']].rename(columns={'Uplift_Score': 'Uplift_LGBM'}), on='Customer_ID'))

    def causal_profit(mask, col='Uplift_XGB'):
        sub = causal_merged[mask]
        return (sub[col] * profit['reward_per_response'] - profit['cost_per_email']).sum()

    causal_scenarios = [
        ('Mass Marketing (10,000)', pd.Series(True, index=causal_merged.index), mass_profit),
        ('Logistic Regression-optimized', causal_merged['LOGREG_Send_Email'], lr_scn['profit']),
        ('XGBoost-optimized', causal_merged['XGB_Send_Email'], xgb_scn['profit']),
        ('LightGBM-optimized', causal_merged['LGBM_Send_Email'], lgbm_scn['profit']),
    ]
    causal_rows_html = ""
    causal_by_scenario = {}
    for name, mask, booked_profit in causal_scenarios:
        n = int(mask.sum())
        causal = causal_profit(mask)
        causal_by_scenario[name] = causal
        causal_rows_html += f"""
        <tr>
          <td>{name}</td>
          <td class="num">{n:,}</td>
          <td class="num">{fmt_vnd(booked_profit)}</td>
          <td class="num"><b style="color:{'var(--critical)' if causal < 0 else 'var(--good)'}">{fmt_vnd(causal)}</b></td>
        </tr>"""
    mass_causal_profit = causal_by_scenario['Mass Marketing (10,000)']
    xgb_causal_profit = causal_by_scenario['XGBoost-optimized']
    lgbm_causal_profit = causal_by_scenario['LightGBM-optimized']

    mass_causal_xgb_lens = causal_profit(pd.Series(True, index=causal_merged.index), 'Uplift_XGB')
    mass_causal_lgbm_lens = causal_profit(pd.Series(True, index=causal_merged.index), 'Uplift_LGBM')

    for label, u_df, s, lens_col, mass_lens in [
        ('Uplift Targeting (S-learner XGBoost)', uplift_df, xgb_uplift, 'Uplift_XGB', mass_causal_xgb_lens),
        ('Uplift Targeting (S-learner LightGBM)', uplift_lgbm_df, lgbm_uplift, 'Uplift_LGBM', mass_causal_lgbm_lens),
    ]:
        sel_ids = set(u_df[u_df['Send_Email_Uplift']]['Customer_ID'])
        sel_mask = causal_merged['Customer_ID'].isin(sel_ids)
        booked = (int(causal_merged[sel_mask]['Historical_Promo_Response'].sum())
                  * profit['reward_per_response'] - s['n'] * profit['cost_per_email'])
        is_best = (label.endswith('LightGBM)') == best_uplift_is_lgbm)
        causal_rows_html += f"""
        <tr class="{'row-best' if is_best else ''}">
          <td>{label}{' <span class="pill pill-good">Đề xuất</span>' if is_best else ''}</td>
          <td class="num">{s['n']:,}</td>
          <td class="num">{fmt_vnd(booked)}</td>
          <td class="num"><b style="color:var(--good)">{fmt_vnd(s['profit'])}</b></td>
        </tr>"""

    uplift_xgb_gain_vs_mass = xgb_uplift['profit'] - mass_causal_xgb_lens
    uplift_lgbm_gain_vs_mass = lgbm_uplift['profit'] - mass_causal_lgbm_lens

    # ---------- Metric comparison table (03 model) ----------
    model_order = ['logistic_regression', 'xgboost', 'lightgbm']
    metric_rows_html = ""
    for key in model_order:
        m = metrics[key]
        is_best = key == comparison['best_model_by_auc_key']
        metric_rows_html += f"""
        <tr class="{'row-best' if is_best else ''}">
          <td>{m['display_name']}{' <span class="pill pill-good">ROC-AUC cao nhất</span>' if is_best else ''}</td>
          <td class="num">{m['roc_auc']:.4f}</td>
          <td class="num">{fmt_pct(m['accuracy'])}</td>
          <td class="num">{fmt_pct(m['precision'])}</td>
          <td class="num">{fmt_pct(m['recall'])}</td>
          <td class="num">{fmt_pct(m['f1'])}</td>
        </tr>"""

    # ---------- Images ----------
    images = {name: b64_img(path) for name, path in IMAGES.items()}
    missing_images = [name for name, data in images.items() if data is None]
    if missing_images:
        print(f"[Cảnh báo] Thiếu {len(missing_images)} ảnh (sẽ bỏ qua khi render): {missing_images}")

    def img_tag(key, alt, css_class="chart-img"):
        data = images.get(key)
        if not data:
            return f'<div class="img-missing">Chưa có ảnh: {IMAGES.get(key, key)}</div>'
        return f'<img class="{css_class}" alt="{alt}" src="data:image/png;base64,{data}" />'

    chart_data = {
        'seg_labels': seg_labels,
        'seg_counts': seg_counts,
        'seg_rates': seg_rates,
        'metric_models': [metrics[k]['display_name'] for k in model_order],
        'metric_roc_auc': [round(metrics[k]['roc_auc'], 4) for k in model_order],
        'metric_precision': [round(metrics[k]['precision'], 4) for k in model_order],
        'metric_recall': [round(metrics[k]['recall'], 4) for k in model_order],
        'roc_xgb': roc_xgb,
        'roc_lgbm': roc_lgbm,
        'pr_xgb': pr_xgb,
        'pr_lgbm': pr_lgbm,
        'scenario_names': scenario_names,
        'scenario_profits': scenario_profits,
    }

    html = HTML_TEMPLATE.format(
        n_customers=f"{n_customers:,}",
        response_rate=fmt_pct(response_rate),
        n_features=n_features,
        best_model_by_auc_name=best_model_by_auc_name,
        best_model_by_auc_auc=f"{best_model_by_auc_auc:.3f}",
        best_model_by_profit_name=best_model_by_profit_name,
        auc_gain=f"{(best_model_by_auc_auc - lr_auc):.3f}",
        lr_auc=f"{lr_auc:.4f}",
        xgb_auc=f"{metrics['xgboost']['roc_auc']:.4f}",
        lgbm_auc=f"{metrics['lightgbm']['roc_auc']:.4f}",
        agree_rate=fmt_pct(comparison['agree_rate_at_0.5']),
        proba_corr=f"{comparison['proba_correlation']:.3f}",
        xgb_fp=f"{xgb_fp:,}",
        xgb_fn=f"{xgb_fn:,}",
        lgbm_fp=f"{lgbm_fp:,}",
        lgbm_fn=f"{lgbm_fn:,}",
        metric_rows_html=metric_rows_html,
        model_select_rows_html=model_select_rows_html,
        lr_profit=fmt_vnd(lr_scn['profit']),
        lr_send=f"{lr_scn['n_send']:,}",
        lr_recall=fmt_pct(metrics['logistic_regression']['recall']),
        lr_precision=fmt_pct(metrics['logistic_regression']['precision']),
        xgb_precision=fmt_pct(metrics['xgboost']['precision']),
        lgbm_precision=fmt_pct(metrics['lightgbm']['precision']),
        xgb_recall=fmt_pct(metrics['xgboost']['recall']),
        lgbm_recall=fmt_pct(metrics['lightgbm']['recall']),
        xgb_accuracy=fmt_pct(metrics['xgboost']['accuracy']),
        lgbm_accuracy=fmt_pct(metrics['lightgbm']['accuracy']),
        recommended_classifier_name=recommended_classifier_name,
        recommended_classifier_profit=fmt_vnd(recommended_classifier_scn['profit']),
        profit_gap_xgb_lgbm_pct=fmt_pct(profit_gap_xgb_lgbm_pct),
        lr_excluded_n=f"{lr_excluded_n:,}",
        xgb_excluded_n=f"{xgb_excluded_n:,}",
        lgbm_excluded_n=f"{lgbm_excluded_n:,}",
        xgb_excluded_pct=fmt_pct(xgb_excluded_n / n_customers),
        lgbm_excluded_pct=fmt_pct(lgbm_excluded_n / n_customers),
        xgb_profit=fmt_vnd(xgb_scn['profit']),
        xgb_send=f"{xgb_scn['n_send']:,}",
        lgbm_profit=fmt_vnd(lgbm_scn['profit']),
        lgbm_send=f"{lgbm_scn['n_send']:,}",
        lgbm_vs_xgb_gain=fmt_vnd(lgbm_vs_xgb_gain),
        lgbm_vs_lr_gain=fmt_vnd(lgbm_vs_lr_gain),
        lr_roi_mult=roi_multiple(lr_scn['profit']),
        xgb_roi_mult=roi_multiple(xgb_scn['profit']),
        lgbm_roi_mult=roi_multiple(lgbm_scn['profit']),
        cluster_rows_html=cluster_rows_html,
        n_clusters=len(cluster_profile),
        persona_best_name=persona_best_name,
        persona_worst_name=persona_worst_name,
        persona_gap_ratio=persona_gap_ratio,
        seg_top_name=seg_top_name,
        seg_top_rate=seg_top_rate,
        seg_bottom_name=seg_bottom_name,
        seg_bottom_rate=seg_bottom_rate,
        seg_ratio=seg_ratio,
        profit_rows_html=profit_rows_html,
        cost_per_email=fmt_vnd(profit['cost_per_email']),
        reward_per_response=fmt_vnd(profit['reward_per_response']),
        best_scenario=profit['best_scenario'],
        best_scenario_uplift=fmt_vnd(profit['best_scenario_uplift_vs_mass']),
        n_persuadables=f"{n_persuadables:,}",
        pct_persuadables=fmt_pct(n_persuadables / len(uplift_df)),
        total_incremental_profit=fmt_vnd(total_incremental_profit),
        best_uplift_name=best_uplift_name,
        causal_rows_html=causal_rows_html,
        breakeven_pct=fmt_pct(breakeven),
        uplift_compare_rows_html=uplift_compare_rows_html,
        uplift_agree_rate=fmt_pct(uplift_agree_rate),
        uplift_corr=f"{uplift_corr:.3f}",
        n_both_persuadable=f"{n_both_persuadable:,}",
        n_only_xgb_persuadable=f"{n_only_xgb_persuadable:,}",
        n_only_lgbm_persuadable=f"{n_only_lgbm_persuadable:,}",
        n_persuadables_xgb=f"{xgb_uplift['n']:,}",
        n_persuadables_lgbm=f"{lgbm_uplift['n']:,}",
        pct_persuadables_xgb=fmt_pct(xgb_uplift['n'] / len(uplift_df)),
        pct_persuadables_lgbm=fmt_pct(lgbm_uplift['n'] / len(uplift_lgbm_df)),
        total_incremental_profit_xgb=fmt_vnd(xgb_uplift['profit']),
        total_incremental_profit_lgbm=fmt_vnd(lgbm_uplift['profit']),
        uplift_xgb_gain_vs_mass=fmt_vnd(uplift_xgb_gain_vs_mass),
        uplift_lgbm_gain_vs_mass=fmt_vnd(uplift_lgbm_gain_vs_mass),
        n_excluded_xgb=f"{10000 - xgb_uplift['n']:,}",
        n_excluded_lgbm=f"{10000 - lgbm_uplift['n']:,}",
        mass_causal_profit=fmt_vnd(mass_causal_profit),
        xgb_causal_profit=fmt_vnd(xgb_causal_profit),
        lgbm_causal_profit=fmt_vnd(lgbm_causal_profit),
        top10_rows_html=top10_rows_html,
        top10_lgbm_rows_html=top10_lgbm_rows_html,
        img_correlation=img_tag('correlation', 'Correlation matrix'),
        img_kmeans=img_tag('kmeans_eval', 'KMeans elbow & silhouette'),
        img_confusion=img_tag('confusion_matrices', 'Confusion matrices'),
        img_feat_importance=img_tag('feature_importance', 'Feature importance comparison'),
        img_shap_bar_xgb=img_tag('shap_bar_xgb', 'SHAP bar XGBoost'),
        img_shap_dot_xgb=img_tag('shap_dot_xgb', 'SHAP dot XGBoost'),
        img_shap_dep1_xgb=img_tag('shap_dep1_xgb', 'SHAP dependence 1 XGBoost'),
        img_shap_dep2_xgb=img_tag('shap_dep2_xgb', 'SHAP dependence 2 XGBoost'),
        img_shap_bar_lgbm=img_tag('shap_bar_lgbm', 'SHAP bar LightGBM'),
        img_shap_dot_lgbm=img_tag('shap_dot_lgbm', 'SHAP dot LightGBM'),
        img_shap_dep1_lgbm=img_tag('shap_dep1_lgbm', 'SHAP dependence 1 LightGBM'),
        img_shap_dep2_lgbm=img_tag('shap_dep2_lgbm', 'SHAP dependence 2 LightGBM'),
        chart_data_json=json.dumps(chart_data, ensure_ascii=False),
    )

    with open('presentation.html', 'w', encoding='utf-8') as f:
        f.write(html)

    size_kb = os.path.getsize('presentation.html') / 1024
    print(f"\nĐã tạo presentation.html ({size_kb:,.0f} KB)")


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Customer Promo Response — Model Review</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700&family=Roboto:wght@400;500;700&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"></script>
<style>
  :root {{
    --surface-1: #fcfcfb;
    --page-plane: #f9f9f7;
    --text-primary: #0b0b0b;
    --text-secondary: #52514e;
    --text-muted: #898781;
    --grid: #e1e0d9;
    --border: rgba(11,11,11,0.10);
    --ga-blue: #1a73e8;
    --ga-blue-dark: #174ea6;
    --series-xgb: #2a78d6;
    --series-lgbm: #1baf7a;
    --series-lr: #eda100;
    --series-mass: #898781;
    --good: #0ca30c;
    --critical: #d03b3b;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; background: var(--page-plane); color: var(--text-primary);
    font-family: 'Google Sans', Roboto, system-ui, -apple-system, "Segoe UI", sans-serif;
  }}
  header.topbar {{
    background: #fff; border-bottom: 1px solid var(--border); position: sticky; top: 0; z-index: 20;
  }}
  .topbar-inner {{
    max-width: 1240px; margin: 0 auto; padding: 14px 24px 0 24px;
  }}
  .brand {{ display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }}
  .brand .logo {{
    width: 30px; height: 30px; border-radius: 7px;
    background: linear-gradient(135deg, var(--ga-blue), #34a853);
  }}
  .brand h1 {{ font-size: 17px; margin: 0; font-weight: 700; }}
  .brand p {{ margin: 0; font-size: 12px; color: var(--text-muted); }}
  nav.tabs {{ display: flex; gap: 4px; overflow-x: auto; }}
  nav.tabs button {{
    appearance: none; background: none; border: none; cursor: pointer;
    padding: 10px 16px; font-size: 13px; font-weight: 500; color: var(--text-secondary);
    border-bottom: 3px solid transparent; white-space: nowrap; font-family: inherit;
  }}
  nav.tabs button:hover {{ color: var(--text-primary); }}
  nav.tabs button.active {{ color: var(--ga-blue); border-bottom-color: var(--ga-blue); }}

  main {{ max-width: 1240px; margin: 0 auto; padding: 24px; }}
  section.tabpanel {{ display: none; }}
  section.tabpanel.active {{ display: block; animation: fade .15s ease-in; }}
  @keyframes fade {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}

  h2.section-title {{ font-size: 20px; margin: 0 0 4px 0; font-weight: 700; }}
  p.section-sub {{ margin: 0 0 18px 0; color: var(--text-secondary); font-size: 13.5px; max-width: 820px; line-height: 1.5; }}

  .kpi-row {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 20px; }}
  .kpi-tile {{
    background: var(--surface-1); border: 1px solid var(--border); border-radius: 10px;
    padding: 16px 18px; box-shadow: 0 1px 2px rgba(11,11,11,0.04);
  }}
  .kpi-tile .kpi-label {{ font-size: 12px; color: var(--text-secondary); margin-bottom: 6px; }}
  .kpi-tile .kpi-value {{ font-size: 26px; font-weight: 700; color: var(--text-primary); }}
  .kpi-tile .kpi-delta {{ font-size: 12px; margin-top: 4px; color: var(--good); font-weight: 500; }}

  .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
  .card {{
    background: var(--surface-1); border: 1px solid var(--border); border-radius: 10px;
    padding: 18px 20px; margin-bottom: 16px; box-shadow: 0 1px 2px rgba(11,11,11,0.04);
  }}
  .card h3 {{ font-size: 14.5px; margin: 0 0 12px 0; font-weight: 700; }}
  .card p.hint {{ font-size: 12.5px; color: var(--text-secondary); margin: 8px 0 0 0; line-height: 1.5; }}
  .card p.hint b {{ color: var(--text-primary); }}
  .card-highlight {{ border-left: 4px solid var(--ga-blue); background: rgba(26,115,232,0.045); }}
  .card-highlight h3 {{ font-size: 16px; }}

  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  th {{ text-align: left; color: var(--text-secondary); font-weight: 500; font-size: 12px; padding: 8px 10px; border-bottom: 1px solid var(--grid); }}
  td {{ padding: 9px 10px; border-bottom: 1px solid var(--grid); }}
  td.num, th.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
  tr.row-best {{ background: rgba(26,115,232,0.06); }}
  tr:last-child td {{ border-bottom: none; }}

  .pill {{ display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; }}
  .pill-good {{ background: rgba(12,163,12,0.12); color: #0a6e0a; }}
  .pill-muted {{ background: rgba(137,135,129,0.15); color: var(--text-secondary); }}

  .chart-img {{ width: 100%; height: auto; border-radius: 6px; display: block; }}
  .img-missing {{ padding: 40px; text-align: center; color: var(--text-muted); font-size: 12px; border: 1px dashed var(--grid); border-radius: 6px; }}
  canvas {{ max-height: 320px; }}

  .legend-row {{ display: flex; gap: 16px; margin-bottom: 10px; font-size: 12px; color: var(--text-secondary); }}
  .legend-row .dot {{ display: inline-block; width: 9px; height: 9px; border-radius: 50%; margin-right: 5px; }}

  footer {{ max-width: 1240px; margin: 0 auto; padding: 20px 24px 40px 24px; color: var(--text-muted); font-size: 12px; }}

  @media (max-width: 900px) {{
    .kpi-row {{ grid-template-columns: repeat(2, 1fr); }}
    .grid-2 {{ grid-template-columns: 1fr; }}
  }}
</style>
</head>
<body>

<header class="topbar">
  <div class="topbar-inner">
    <div class="brand">
      <div class="logo"></div>
      <div>
        <h1>Customer Promo Response — Model Review</h1>
        <p>Basic ML case study &middot; XGBoost vs LightGBM &middot; {n_customers} khách hàng</p>
      </div>
    </div>
    <nav class="tabs" id="tabs">
      <button data-tab="overview" class="active">Tổng quan</button>
      <button data-tab="eda">EDA &amp; Thống kê</button>
      <button data-tab="segmentation">Phân khúc KH</button>
      <button data-tab="modelcompare">So sánh Model</button>
      <button data-tab="explainability">Explainability</button>
      <button data-tab="impact">Business Impact</button>
      <button data-tab="uplift">Uplift</button>
      <button data-tab="conclusion">Kết luận</button>
    </nav>
  </div>
</header>

<main>

  <!-- ===================== OVERVIEW ===================== -->
  <section class="tabpanel active" id="overview">
    <h2 class="section-title">Bài toán &amp; Dữ liệu</h2>
    <p class="section-sub">Ngân hàng cần dự đoán khách hàng nào có khả năng phản hồi 1 chiến dịch khuyến mãi,
      dựa trên lịch sử hành vi giao dịch. Mục tiêu: xây model dự đoán, giải thích được lý do, và quy đổi ra
      lợi nhuận kinh doanh cụ thể (không chỉ dừng lại ở accuracy).</p>

    <div class="kpi-row">
      <div class="kpi-tile">
        <div class="kpi-label">Tổng số khách hàng</div>
        <div class="kpi-value">{n_customers}</div>
      </div>
      <div class="kpi-tile">
        <div class="kpi-label">Tỷ lệ phản hồi (baseline)</div>
        <div class="kpi-value">{response_rate}</div>
      </div>
      <div class="kpi-tile">
        <div class="kpi-label">Biến đầu vào (features)</div>
        <div class="kpi-value">{n_features}</div>
      </div>
      <div class="kpi-tile">
        <div class="kpi-label">Chiến lược khuyến nghị (đã kiểm tra nhân quả)</div>
        <div class="kpi-value" style="font-size:20px;">Uplift Targeting</div>
        <div class="kpi-delta">+{total_incremental_profit} VND lợi nhuận NHÂN QUẢ thực, chỉ {n_persuadables} KH — xem tab Uplift</div>
      </div>
    </div>

    <div class="grid-2">
      <div class="card">
        <h3>Agenda buổi trình bày</h3>
        <table>
          <tr><td>1</td><td>EDA &amp; kiểm định thống kê — biến nào thực sự có ý nghĩa</td></tr>
          <tr><td>2</td><td>Phân khúc khách hàng (KMeans) — 3 nhóm hành vi rõ rệt</td></tr>
          <tr><td>3</td><td>Benchmark Logistic Regression vs XGBoost vs LightGBM</td></tr>
          <tr><td>4</td><td>Explainability (SHAP) — vì sao model quyết định như vậy</td></tr>
          <tr><td>5</td><td>Quy đổi ra lợi nhuận (Expected Profit) — ROI của ML</td></tr>
          <tr><td>6</td><td>Uplift Modeling — tìm đúng người "Persuadable"</td></tr>
          <tr><td>7</td><td>Kết luận &amp; khuyến nghị triển khai</td></tr>
        </table>
      </div>
      <div class="card">
        <h3>Tỷ lệ phản hồi theo Phân khúc</h3>
        <canvas id="chartSegOverview"></canvas>
        <p class="hint"><b>Nhận định:</b> {seg_top_name} có tỷ lệ phản hồi {seg_top_rate}%, cao gấp {seg_ratio}x
          so với {seg_bottom_name} ({seg_bottom_rate}%) — xem chi tiết kiểm định thống kê ở tab EDA.</p>
      </div>
    </div>
  </section>

  <!-- ===================== EDA ===================== -->
  <section class="tabpanel" id="eda">
    <h2 class="section-title">EDA &amp; Kiểm định thống kê</h2>
    <p class="section-sub">T-test (biến liên tục) và Chi-square (biến phân loại) để xác định biến nào thực sự
      có ý nghĩa thống kê (p-value &lt; 0.05) với target, trước khi đưa vào model.</p>

    <div class="grid-2">
      <div class="card">
        <h3>Ma trận tương quan (Correlation Matrix)</h3>
        {img_correlation}
        <p class="hint"><b>Nhận định:</b> <b>Avg_Monthly_Balance_VND</b> và <b>Estimated_CLV_VND</b> tương quan ~0.99 —
          bẫy đa cộng tuyến có chủ ý, phải loại 1 trong 2 trước khi train (đã loại Estimated_CLV_VND). Các biến hành vi
          thông thường (Txn_Count_3M, Txn_Amount_3M_VND, App_Logins_3M) tự tương quan chéo rất cao với nhau nhưng gần
          như bằng 0 với Historical_Promo_Response — dấu hiệu của biến nhiễu cần loại bỏ.</p>
      </div>
      <div class="card">
        <h3>Tỷ lệ phản hồi theo Segment (chi tiết)</h3>
        <canvas id="chartSegEda"></canvas>
        <table style="margin-top:14px;">
          <thead><tr><th>Segment</th><th class="num">Số KH</th><th class="num">Response rate</th></tr></thead>
          <tbody id="segTableBody"></tbody>
        </table>
        <p class="hint"><b>Nhận định:</b> chênh lệch phản hồi giữa các Segment ({seg_ratio}x) lớn hơn nhiều so với
          bất kỳ biến hành vi thông thường nào — đây là lý do Segment lọt vào nhóm 4 biến "vàng" bên dưới dù chỉ là
          1 biến phân loại 3 giá trị.</p>
      </div>
    </div>

    <div class="card">
      <h3>Kết luận chọn biến (Feature Selection)</h3>
      <table>
        <thead><tr><th>Nhóm</th><th>Biến</th><th>Ghi chú</th></tr></thead>
        <tbody>
          <tr><td><span class="pill pill-good">Giữ lại</span></td><td>Promo_Txn_Count_3M, Last_Active_Days, Avg_Monthly_Balance_VND, Segment</td><td>p-value &lt; 0.05, có ý nghĩa thống kê và kinh doanh rõ ràng</td></tr>
          <tr><td><span class="pill pill-muted">Loại bỏ</span></td><td>Age, Gender, Txn_Count_3M, Txn_Amount_3M_VND, App_Logins_3M</td><td>p-value &gt; 0.05 — tự tương quan chéo cao với nhau nhưng không liên quan tới target</td></tr>
          <tr><td><span class="pill pill-muted">Loại bỏ (bẫy)</span></td><td>Estimated_CLV_VND</td><td>Trùng lặp ~99% thông tin với Avg_Monthly_Balance_VND</td></tr>
        </tbody>
      </table>
    </div>
  </section>

  <!-- ===================== SEGMENTATION ===================== -->
  <section class="tabpanel" id="segmentation">
    <h2 class="section-title">Phân khúc khách hàng (KMeans)</h2>
    <p class="section-sub">Gom cụm theo hành vi (Promo_Txn_Count_3M, Last_Active_Days, Avg_Monthly_Balance_VND),
      tìm K tối ưu bằng Elbow Method + Silhouette Score — ra {n_clusters} nhóm hành vi rõ rệt,
      dùng song song với model dự đoán để đặt tên "chân dung" khách hàng cho team Marketing.</p>

    <div class="card">
      <h3>Elbow Method &amp; Silhouette Score</h3>
      {img_kmeans}
      <p class="hint"><b>Nhận định:</b> Silhouette Score đạt đỉnh tại K={n_clusters}, nên K={n_clusters} được chọn
        làm số cụm tối ưu — Elbow Method (đồ thị trái) chỉ mang tính tham khảo thêm vì đường cong giảm dần đều,
        không có "khuỷu tay" rõ rệt.</p>
    </div>

    <div class="card">
      <h3>Chân dung từng nhóm (Persona)</h3>
      <table>
        <thead><tr><th>Persona</th><th class="num">Số KH</th><th class="num">Promo TB (3M)</th><th class="num">Last Active TB</th><th class="num">Balance TB</th><th class="num">Response rate</th></tr></thead>
        <tbody>{cluster_rows_html}</tbody>
      </table>
      <p class="hint"><b>Nhận định:</b> nhóm <b>{persona_best_name}</b> có response rate cao gấp {persona_gap_ratio}x
        nhóm <b>{persona_worst_name}</b> — gửi khuyến mãi cho nhóm "Ngủ Đông" sẽ kém hiệu quả nhất, nên team
        Marketing có thể cân nhắc chiến dịch "đánh thức" riêng (win-back) thay vì dùng chung 1 kịch bản khuyến mãi.
        Lưu ý kỹ thuật: phân tích này độc lập với pipeline dự đoán (không feed ngược vào model 04/04b) — giá trị
        của nó là cung cấp góc nhìn "persona" song song cho team Marketing.</p>
    </div>
  </section>

  <!-- ===================== MODEL COMPARISON ===================== -->
  <section class="tabpanel" id="modelcompare">
    <h2 class="section-title">So sánh Model: Logistic Regression vs XGBoost vs LightGBM</h2>
    <p class="section-sub">Cả 3 model đánh giá trên cùng 1 test set (20%, stratified, random_state=42).
      XGBoost và LightGBM đều vượt benchmark Logistic Regression nhờ bắt được quan hệ phi tuyến /
      tương tác giữa Last_Active_Days, Promo_Txn_Count_3M và Segment.</p>

    <div class="card card-highlight">
      <h3>🏆 Chọn Model Nào? — Ưu tiên ROI, không chỉ ROC-AUC</h3>
      <table>
        <thead><tr><th>Model</th><th class="num">ROC-AUC</th><th class="num">Precision</th><th class="num">Recall</th>
          <th class="num">Số KH nên liên hệ</th><th class="num">Lợi nhuận</th><th class="num">ROI (x Mass Marketing)</th></tr></thead>
        <tbody>{model_select_rows_html}</tbody>
      </table>
      <p class="hint" style="margin-top:12px;">
        <b>Nhận định:</b> ở mức chi phí liên hệ hiện tại ({cost_per_email} VND, breakeven {breakeven_pct} — xấp xỉ
        tỷ lệ convert nền ~5%), 3 model có độ "chọn lọc" khác biệt <b>rất lớn</b>: Logistic Regression vẫn gửi tới
        {lr_send}/10,000 người (chỉ loại {lr_excluded_n}), trong khi XGBoost chỉ gửi {xgb_send} người (loại
        {xgb_excluded_pct}) và LightGBM chỉ gửi {lgbm_send} người (loại {lgbm_excluded_pct}) — nhờ mô hình hoá đúng
        quan hệ phi tuyến/tương tác mà Logistic Regression bỏ lỡ. Kết quả: LightGBM-optimized lời hơn Mass Marketing
        <b>+{best_scenario_uplift} VND</b> (gấp {lgbm_roi_mult} lần) dù liên hệ ít hơn {lgbm_excluded_n} người —
        <b>gửi đúng người quan trọng hơn nhiều so với gửi nhiều người</b>, đúng như yêu cầu bài toán.</p>
      <p class="hint">
        <b>Nhưng lợi nhuận cao nhất chưa chắc là lựa chọn tốt nhất.</b> LightGBM có Precision/Accuracy cao nhất
        ({lgbm_precision} / {lgbm_accuracy}) nhưng Recall lại <b>thấp nhất</b> ({lgbm_recall}) — nghĩa là nó bỏ sót
        nhiều khách hàng thực sự sẽ convert hơn XGBoost ({xgb_recall} Recall). Vì bài toán ưu tiên model "vừa lời
        vừa accuracy/recall tốt để còn kế thừa sau này" (không chỉ tối đa lợi nhuận ở đúng 1 giả định chi phí hiện
        tại), và chênh lệch lợi nhuận giữa XGBoost/LightGBM chỉ {profit_gap_xgb_lgbm_pct} — quá nhỏ để đánh đổi lấy
        gần {lgbm_recall} → {xgb_recall} Recall — <b>model khuyến nghị triển khai là {recommended_classifier_name}</b>
        ({recommended_classifier_profit} VND lợi nhuận, {xgb_accuracy} Accuracy, {xgb_recall} Recall, {xgb_precision}
        Precision) — cân bằng tốt nhất giữa cả 3 tiêu chí, đồng thời có ROC-AUC cao nhất ({xgb_auc}) nên khái quát
        tốt hơn nếu giả định chi phí/lợi nhuận thay đổi trong tương lai.</p>
      <p class="hint" style="background:rgba(208,59,59,0.06); padding:8px 10px; border-radius:6px;">
        ⚠️ <b>Nhưng đây vẫn chưa phải câu trả lời cuối cùng.</b> Con số lợi nhuận ở trên chưa net trừ nhân quả (đếm cả
        khách hàng "đằng nào cũng mua"). Kiểm tra lại bằng <b>Uplift Score</b> — và giữa 2 base learner của Uplift
        (XGBoost vs LightGBM), lựa chọn <b>vẫn tạo khác biệt lớn</b> ({pct_persuadables_xgb} vs {pct_persuadables_lgbm}
        khách hàng được chọn khác nhau). Xem tab <b>Uplift</b> để biết chi tiết và khuyến nghị cuối cùng.</p>
    </div>

    <div class="card">
      <h3>Bảng so sánh metric (test set)</h3>
      <table>
        <thead><tr><th>Model</th><th class="num">ROC-AUC</th><th class="num">Accuracy</th><th class="num">Precision</th><th class="num">Recall</th><th class="num">F1</th></tr></thead>
        <tbody>{metric_rows_html}</tbody>
      </table>
      <p class="hint"><b>Nhận định:</b> nhãn "ROC-AUC cao nhất" ở bảng này là xếp hạng <i>thống kê</i>, khác với
        model tối ưu <i>lợi nhuận</i> ở card phía trên — đây chính xác là điểm mấu chốt của toàn bộ phần so sánh model.</p>
    </div>

    <div class="grid-2">
      <div class="card">
        <h3>ROC Curve (XGBoost vs LightGBM)</h3>
        <div class="legend-row">
          <span><span class="dot" style="background:var(--series-xgb)"></span>XGBoost (AUC={xgb_auc})</span>
          <span><span class="dot" style="background:var(--series-lgbm)"></span>LightGBM (AUC={lgbm_auc})</span>
        </div>
        <canvas id="chartRoc"></canvas>
        <p class="hint"><b>Nhận định:</b> 2 đường cong gần như trùng nhau — phù hợp với tương quan xác suất dự đoán
          rất cao ({proba_corr}) giữa 2 model. Chênh lệch AUC nhỏ (~0.01) không đảm bảo model AUC cao hơn sẽ thắng
          ở 1 điểm ngưỡng kinh doanh cụ thể (xem card "Chọn Model Nào?" ở trên).</p>
      </div>
      <div class="card">
        <h3>Precision-Recall Curve</h3>
        <p class="hint" style="margin-top:0;">Quan trọng vì data mất cân bằng (~{response_rate} response rate) —
          PR curve nhạy cảm hơn ROC với lớp thiểu số.</p>
        <canvas id="chartPr"></canvas>
        <p class="hint"><b>Nhận định:</b> 2 đường PR cắt nhau ở vài đoạn thay vì 1 model áp đảo toàn bộ — nghĩa là
          "model nào tốt hơn" phụ thuộc vào bạn ưu tiên Precision hay Recall ở khoảng nào, đúng như những gì bảng
          Precision/Recall ở trên đã thể hiện.</p>
      </div>
    </div>

    <div class="grid-2">
      <div class="card">
        <h3>Confusion Matrix (threshold = 0.5)</h3>
        {img_confusion}
        <p class="hint"><b>Nhận định:</b> LightGBM có ít False Positive hơn ({lgbm_fp} so với {xgb_fp} của XGBoost)
          — tức ít "gọi nhầm" người không phản hồi hơn (khớp Precision cao hơn) — nhưng đổi lại nhiều False Negative
          hơn hẳn ({lgbm_fn} so với {xgb_fn}) — tức bỏ sót nhiều khách hàng thực sự sẽ convert hơn. Đây chính là gốc
          rễ của việc LightGBM lời hơn về sổ sách nhưng Recall thấp hơn XGBoost — xem card "Chọn Model Nào?" để biết
          vì sao XGBoost vẫn được khuyến nghị.</p>
      </div>
      <div class="card">
        <h3>Feature Importance — 2 model</h3>
        {img_feat_importance}
        <p class="hint"><b>Nhận định:</b> cả 2 model đều đồng thuận Last_Active_Days và Promo_Txn_Count_3M là
          2 yếu tố quan trọng nhất — xem thêm chiều hướng tác động chi tiết ở tab Explainability.</p>
      </div>
    </div>

    <div class="card">
      <h3>Mức độ đồng thuận giữa 2 model</h3>
      <div class="kpi-row" style="grid-template-columns: repeat(2, 1fr); margin-bottom: 0;">
        <div class="kpi-tile">
          <div class="kpi-label">Tỷ lệ đồng ý quyết định (threshold 0.5)</div>
          <div class="kpi-value">{agree_rate}</div>
        </div>
        <div class="kpi-tile">
          <div class="kpi-label">Tương quan xác suất dự đoán</div>
          <div class="kpi-value">{proba_corr}</div>
        </div>
      </div>
      <p class="hint"><b>Nhận định:</b> 2 model độc lập đồng ý với nhau ở {agree_rate} khách hàng — phần chênh lệch
        còn lại chỉ nằm ở nhóm khách hàng "ranh giới" gần ngưỡng quyết định, đúng nơi ảnh hưởng nhiều nhất tới lợi
        nhuận cuối cùng (xem tab Business Impact).</p>
    </div>
  </section>

  <!-- ===================== EXPLAINABILITY ===================== -->
  <section class="tabpanel" id="explainability">
    <h2 class="section-title">Explainability (SHAP)</h2>
    <p class="section-sub">Biến "hộp đen" AI thành "hộp trong suốt": XGBoost và LightGBM đồng thuận về 2 yếu tố
      quyết định lớn nhất (Last_Active_Days, Promo_Txn_Count_3M) — sự đồng thuận giữa 2 model độc lập là
      bằng chứng mạnh để thuyết phục stakeholder không rành kỹ thuật.</p>

    <div class="card">
      <h3>XGBoost — Feature Importance (SHAP Bar)</h3>
      <div class="grid-2">
        {img_shap_bar_xgb}
        {img_shap_dot_xgb}
      </div>
    </div>
    <div class="card">
      <h3>XGBoost — Dependence Plot (2 biến quan trọng nhất)</h3>
      <div class="grid-2">
        {img_shap_dep1_xgb}
        {img_shap_dep2_xgb}
      </div>
      <p class="hint"><b>Nhận định:</b> Last_Active_Days có dạng đường cong gấp khúc (không phải đường thẳng đơn
        điệu) — SHAP value cao nhất ở vùng "vừa mới hoạt động" (khoảng dưới 40 ngày) rồi giảm dần, chứ không phải
        "càng mới càng tốt" tuyến tính. Đây chính là lý do Logistic Regression (chỉ fit được đường thẳng) không thể
        khớp bằng tree-model. Promo_Txn_Count_3M có dạng bão hoà: tác động tăng nhanh ở vài lần đầu rồi chững lại.</p>
    </div>

    <div class="card">
      <h3>LightGBM — Feature Importance (SHAP Bar)</h3>
      <div class="grid-2">
        {img_shap_bar_lgbm}
        {img_shap_dot_lgbm}
      </div>
    </div>
    <div class="card">
      <h3>LightGBM — Dependence Plot (2 biến quan trọng nhất)</h3>
      <div class="grid-2">
        {img_shap_dep1_lgbm}
        {img_shap_dep2_lgbm}
      </div>
      <p class="hint"><b>Nhận định:</b> hình dạng 2 đường gần như giống hệt bản XGBoost ở trên — 2 model độc lập
        học ra cùng 1 quy luật phi tuyến từ dữ liệu, củng cố độ tin cậy của insight này khi trình bày cho stakeholder.</p>
    </div>
  </section>

  <!-- ===================== BUSINESS IMPACT ===================== -->
  <section class="tabpanel" id="impact">
    <h2 class="section-title">Business Impact — Expected Profit</h2>
    <p class="section-sub">Giả định: chi phí 1 lượt tư vấn/gọi điện = {cost_per_email} VND, lợi nhuận nếu khách
      phản hồi = {reward_per_response} VND. Chỉ gửi/gọi nếu Lợi nhuận kỳ vọng &gt; 0.</p>

    <div class="card" style="border-left: 4px solid var(--critical); background: rgba(208,59,59,0.045);">
      <h3>⚠️ Đọc trước: các con số dưới đây CHƯA net trừ nhân quả</h3>
      <p class="hint" style="margin-top:0;">"Lợi nhuận" ở tab này đếm <b>mọi</b> khách hàng phản hồi là do campaign
        tạo ra — kể cả những người đằng nào cũng sẽ mua dù không ai gọi (Sure Things). Ở mức chi phí liên hệ rẻ như
        hiện tại, con số vẫn dương (vì chi phí quá nhỏ so với lợi nhuận), nhưng <b>chưa phải con số tối ưu</b>:
        kiểm tra lại bằng Uplift Score (tab tiếp theo) cho thấy có thể đạt lợi nhuận nhân quả <b>cao hơn</b> trong
        khi liên hệ <b>ít khách hàng hơn</b> — xem tab <b>Uplift</b> để biết chiến lược targeting đúng.</p>
    </div>

    <div class="kpi-row" style="grid-template-columns: repeat(3, 1fr);">
      <div class="kpi-tile">
        <div class="kpi-label">Kịch bản tốt nhất (theo lợi nhuận)</div>
        <div class="kpi-value" style="font-size:18px;">{best_scenario}</div>
      </div>
      <div class="kpi-tile">
        <div class="kpi-label">Lợi nhuận tăng thêm vs Mass Marketing</div>
        <div class="kpi-value" style="color:var(--good);">+{best_scenario_uplift} VND</div>
      </div>
      <div class="kpi-tile">
        <div class="kpi-label">Số khách hàng trong tập Uplift Persuadables</div>
        <div class="kpi-value">{n_persuadables}</div>
        <div class="kpi-delta">{pct_persuadables} tổng số KH</div>
      </div>
    </div>

    <div class="grid-2">
      <div class="card">
        <h3>So sánh lợi nhuận 4 kịch bản</h3>
        <canvas id="chartProfit"></canvas>
        <p class="hint"><b>Nhận định:</b> ở breakeven {breakeven_pct}, Logistic Regression vẫn gần như gửi hết
          ({lr_roi_mult} so với Mass Marketing — chỉ loại {lr_excluded_n} người), trong khi XGBoost/LightGBM loại
          ra {xgb_excluded_pct}/{lgbm_excluded_pct} khách hàng và vẫn lời hơn ({xgb_roi_mult} / {lgbm_roi_mult}) —
          model tốt hơn thực sự tạo ra khác biệt lợi nhuận ở đây. Nhưng đây chưa phải con số cuối cùng: xem tab
          Uplift để biết lợi nhuận NHÂN QUẢ thực (chưa net baseline) và chiến lược targeting đúng.</p>
      </div>
      <div class="card">
        <h3>Chi tiết kịch bản</h3>
        <table>
          <thead><tr><th>Kịch bản</th><th class="num">Số KH gửi</th><th class="num">Chi phí</th><th class="num">Doanh thu</th><th class="num">Lợi nhuận</th><th class="num">ROI (x Mass)</th></tr></thead>
          <tbody>{profit_rows_html}</tbody>
        </table>
      </div>
    </div>
  </section>

  <!-- ===================== UPLIFT ===================== -->
  <section class="tabpanel" id="uplift">
    <h2 class="section-title">Uplift Modeling — Tìm đúng "Persuadables"</h2>
    <p class="section-sub">S-Learner (biến Treatment = từng dùng khuyến mãi hay chưa, đưa vào làm feature) tách
      4 nhóm: Sure things / Lost causes / Sleeping dogs / <b>Persuadables</b> (nhóm mục tiêu chính — chỉ phản hồi
      KHI có khuyến mãi). Chạy song song <b>2 base learner độc lập</b> — XGBoost (Bước 7) và LightGBM (Bước 7b) —
      để kiểm chứng chéo, giống cách 04/04b đã làm với bài toán phân loại.</p>

    <div class="card card-highlight">
      <h3>🔍 Kiểm Tra Nhân Quả (Causal Reality Check)</h3>
      <p class="hint" style="margin-top:0;">Tab Business Impact tính "lợi nhuận" bằng cách đếm mọi phản hồi của
        khách hàng được liên hệ, bất kể họ có phản hồi <i>vì</i> khuyến mãi hay đằng nào cũng phản hồi. Bảng dưới
        đây tính lại đúng các kịch bản đó, nhưng dùng <b>Uplift Score</b> (đã net trừ tỷ lệ phản hồi nền/tự nhiên)
        thay vì xác suất phản hồi thô — đây mới là lợi nhuận <b>thực sự do campaign gây ra</b>.</p>
      <table>
        <thead><tr><th>Kịch bản</th><th class="num">Số KH</th><th class="num">Lợi nhuận "sổ sách" (tab Business Impact)</th><th class="num">Lợi nhuận NHÂN QUẢ thực</th></tr></thead>
        <tbody>{causal_rows_html}</tbody>
      </table>
      <p class="hint">
        <b>Nhận định:</b> ngay cả sau khi net trừ nhân quả, thứ tự vẫn giữ nguyên như tab Business Impact — targeting
        đúng người tạo ra lợi nhuận thật sự lớn hơn nhiều so với gửi đại trà: Mass Marketing chỉ đạt
        {mass_causal_profit} VND, XGBoost-optimized đạt {xgb_causal_profit} VND, LightGBM-optimized đạt
        {lgbm_causal_profit} VND. Điều bất ngờ: dù LightGBM có lợi nhuận <i>sổ sách</i> cao hơn XGBoost (tab Business
        Impact), khi tính đúng theo nhân quả thì <b>XGBoost lại nhỉnh hơn</b> — củng cố thêm lựa chọn
        {recommended_classifier_name} ở card "Chọn Model Nào?".</p>
      <p class="hint">
        Uplift Targeting vẫn vượt trội hơn tất cả: bằng cách loại ra đúng nhóm Sleeping Dogs + dưới ngưỡng hoà vốn,
        cả 2 base learner đều cho lợi nhuận nhân quả <b>cao hơn hẳn</b> mọi kịch bản dựa trên Expected Profit thô —
        Uplift-XGBoost (+{uplift_xgb_gain_vs_mass} VND so với Mass Marketing, ít hơn {n_excluded_xgb} người) và
        Uplift-LightGBM (+{uplift_lgbm_gain_vs_mass} VND, ít hơn {n_excluded_lgbm} người).</p>
      <p class="hint"><b>Khuyến nghị cuối cùng của toàn bộ phân tích:</b> dùng <b>Uplift Score</b> (không phải
        Expected Profit thô ở tab Business Impact) làm tiêu chí quyết định gửi khuyến mãi cho ai — nó luôn cho
        lợi nhuận nhân quả cao hơn cùng lúc với chi phí thấp hơn. Model phân loại (XGBoost được khuyến nghị ở tab
        So sánh Model) vẫn hữu ích để dự đoán khả năng phản hồi tổng quát cho mục đích báo cáo/kế thừa sau này, nhưng
        <b>không nên dùng trực tiếp để quyết định chi tiêu marketing</b> vì nó không phân biệt được nhân quả.</p>
    </div>

    <div class="card">
      <h3>So sánh 2 Base Learner cho Uplift (XGBoost vs LightGBM)</h3>
      <table>
        <thead><tr><th>Base Learner</th><th class="num">Persuadables</th><th class="num">% Tổng KH</th>
          <th class="num">Sleeping Dogs</th><th class="num">Dưới ngưỡng hoà vốn</th><th class="num">Lợi nhuận nhân quả</th></tr></thead>
        <tbody>{uplift_compare_rows_html}</tbody>
      </table>
      <div class="kpi-row" style="grid-template-columns: repeat(2, 1fr); margin: 14px 0 0 0;">
        <div class="kpi-tile">
          <div class="kpi-label">Tỷ lệ đồng ý quyết định (2 base learner)</div>
          <div class="kpi-value">{uplift_agree_rate}</div>
        </div>
        <div class="kpi-tile">
          <div class="kpi-label">Tương quan Uplift Score</div>
          <div class="kpi-value">{uplift_corr}</div>
        </div>
      </div>
      <p class="hint"><b>Nhận định:</b> {n_both_persuadable} khách hàng được CẢ 2 base learner đồng ý là
        Persuadable, {n_only_xgb_persuadable} người chỉ XGBoost chọn, {n_only_lgbm_persuadable} người chỉ LightGBM
        chọn. Tỷ lệ đồng thuận ({uplift_agree_rate}) thấp hơn hẳn so với bài toán phân loại thường (~95% ở tab So
        sánh Model) — ước lượng Uplift Score (hiệu số 2 xác suất) vốn nhạy cảm/nhiễu hơn dự đoán xác suất đơn, đây
        là giới hạn cố hữu của uplift modeling, không phải lỗi code. <b>{best_uplift_name}</b> S-learner cho lợi
        nhuận nhân quả cao hơn nên được chọn làm phương án chính; base learner còn lại dùng để đối chiếu/kiểm chứng
        trước khi rollout thật.</p>
    </div>

    <div class="kpi-row" style="grid-template-columns: repeat(3, 1fr);">
      <div class="kpi-tile">
        <div class="kpi-label">Số Persuadables xác định được ({best_uplift_name})</div>
        <div class="kpi-value">{n_persuadables}</div>
      </div>
      <div class="kpi-tile">
        <div class="kpi-label">Tỷ trọng trên tổng khách hàng</div>
        <div class="kpi-value">{pct_persuadables}</div>
      </div>
      <div class="kpi-tile">
        <div class="kpi-label">Tổng lợi nhuận gia tăng NHÂN QUẢ (Incremental)</div>
        <div class="kpi-value" style="color:var(--good);">+{total_incremental_profit} VND</div>
      </div>
    </div>

    <div class="grid-2">
      <div class="card">
        <h3>Top 10 KH — Uplift Score cao nhất (S-learner XGBoost)</h3>
        <table>
          <thead><tr><th>Customer ID</th><th class="num">Uplift Score</th><th class="num">Lợi nhuận gia tăng kỳ vọng</th></tr></thead>
          <tbody>{top10_rows_html}</tbody>
        </table>
      </div>
      <div class="card">
        <h3>Top 10 KH — Uplift Score cao nhất (S-learner LightGBM)</h3>
        <table>
          <thead><tr><th>Customer ID</th><th class="num">Uplift Score</th><th class="num">Lợi nhuận gia tăng kỳ vọng</th></tr></thead>
          <tbody>{top10_lgbm_rows_html}</tbody>
        </table>
      </div>
    </div>
  </section>

  <!-- ===================== CONCLUSION ===================== -->
  <section class="tabpanel" id="conclusion">
    <h2 class="section-title">Kết luận &amp; Khuyến nghị</h2>
    <div class="card">
      <h3>Tóm tắt</h3>
      <table>
        <tr><td style="width:260px;">Chiến lược targeting khuyến nghị</td><td><b>Uplift Targeting — S-learner {best_uplift_name}</b>
          ({n_persuadables} khách hàng "Persuadables", {pct_persuadables} tổng số KH) — lợi nhuận nhân quả cao nhất
          (+{total_incremental_profit} VND), đồng thời liên hệ ÍT khách hàng hơn Mass Marketing. Xem card "Kiểm Tra Nhân Quả"
          và "So sánh 2 Base Learner" ở tab Uplift để biết chi tiết.</td></tr>
        <tr><td>Model phân loại khuyến nghị (để dự đoán/báo cáo/kế thừa sau này)</td><td><b>{recommended_classifier_name}</b> —
          cân bằng tốt nhất giữa lợi nhuận ({recommended_classifier_profit} VND), Accuracy ({xgb_accuracy}) và Recall ({xgb_recall}),
          đồng thời có ROC-AUC cao nhất ({best_model_by_auc_auc}, +{auc_gain} vs benchmark) nên khái quát tốt hơn cho tương lai.
          LightGBM có lợi nhuận <i>sổ sách</i> nhỉnh hơn (+{best_scenario_uplift} VND so với Mass Marketing) nhưng đánh đổi Recall
          thấp hơn hẳn ({lgbm_recall}) — không phù hợp tiêu chí "vừa lời vừa accuracy/recall tốt". <b>Dù chọn model nào, vẫn không
          nên dùng Expected Profit thô để quyết định chi tiêu cuối cùng</b> — dùng Uplift Score (hàng trên) vì nó net trừ nhân quả.</td></tr>
        <tr><td>Yếu tố quyết định hàng đầu</td><td>Last_Active_Days và Promo_Txn_Count_3M — đồng thuận giữa cả 2 model qua SHAP</td></tr>
        <tr><td>Giá trị kinh doanh (sổ sách, chưa net nhân quả)</td><td>Kịch bản <b>{best_scenario}</b> tạo thêm <b>+{best_scenario_uplift} VND</b> lợi nhuận so với gửi đại trà —
          nhưng khi net đúng nhân quả (tab Uplift), <b>{recommended_classifier_name}</b> ({xgb_causal_profit} VND) thực ra vượt
          LightGBM ({lgbm_causal_profit} VND) — 2 cách tính KHÔNG nhất quán, càng củng cố lý do ưu tiên Uplift Score.</td></tr>
      </table>
      <p class="hint"><b>Vì sao không chọn model đơn giản hơn (Logistic Regression)?</b> Dù dễ giải thích và Recall
        cao ({lr_recall}), Logistic Regression chỉ fit được quan hệ tuyến tính nên bỏ lỡ dạng phi tuyến của
        Last_Active_Days (xem tab Explainability) — hệ quả cụ thể: nó chỉ loại được {lr_excluded_n} khách hàng rủi ro
        thấp (so với {lgbm_excluded_n} của LightGBM), bỏ lỡ phần lớn cơ hội tối ưu chi phí liên hệ.</p>
      <p class="hint">Bước tiếp theo đề xuất: (1) chạy 1 A/B test nhỏ để kiểm chứng Uplift Score trước khi rollout
        toàn bộ (Treatment ở đây suy ra từ hành vi quá khứ, không phải từ thử nghiệm ngẫu nhiên hoá thật),
        (2) theo dõi mức độ đồng thuận giữa 2 base learner Uplift theo thời gian như 1 chỉ báo độ tin cậy,
        (3) theo dõi data drift và train lại model định kỳ.</p>
    </div>
  </section>

</main>

<footer>
  Basic ML case study &middot; Dữ liệu mô phỏng (10,000 khách hàng, seed=42) &middot; Tạo bởi build_presentation.py
</footer>

<script>
const DATA = {chart_data_json};

// ---- Tab switching ----
document.getElementById('tabs').addEventListener('click', (e) => {{
  const btn = e.target.closest('button[data-tab]');
  if (!btn) return;
  document.querySelectorAll('nav.tabs button').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('section.tabpanel').forEach(s => s.classList.remove('active'));
  btn.classList.add('active');
  document.getElementById(btn.dataset.tab).classList.add('active');
}});

// ---- EDA segment table ----
const segTableBody = document.getElementById('segTableBody');
DATA.seg_labels.forEach((label, i) => {{
  const tr = document.createElement('tr');
  tr.innerHTML = `<td>${{label}}</td><td class="num">${{DATA.seg_counts[i].toLocaleString()}}</td><td class="num">${{DATA.seg_rates[i]}}%</td>`;
  segTableBody.appendChild(tr);
}});

Chart.defaults.font.family = "'Google Sans', Roboto, system-ui, sans-serif";
Chart.defaults.color = '#52514e';
Chart.defaults.borderColor = '#e1e0d9';

function segBarConfig() {{
  return {{
    type: 'bar',
    data: {{
      labels: DATA.seg_labels,
      datasets: [{{
        label: 'Response rate (%)',
        data: DATA.seg_rates,
        backgroundColor: '#2a78d6',
        borderRadius: 4,
        maxBarThickness: 48,
      }}]
    }},
    options: {{
      responsive: true,
      plugins: {{ legend: {{ display: false }} }},
      scales: {{ y: {{ beginAtZero: true, ticks: {{ callback: v => v + '%' }} }} }}
    }}
  }};
}}
new Chart(document.getElementById('chartSegOverview'), segBarConfig());
new Chart(document.getElementById('chartSegEda'), segBarConfig());

function lineConfig(datasets, xLabel, yLabel) {{
  return {{
    type: 'line',
    data: {{ datasets }},
    options: {{
      responsive: true,
      parsing: false,
      plugins: {{ legend: {{ display: false }} }},
      elements: {{ point: {{ radius: 0 }}, line: {{ borderWidth: 2, tension: 0 }} }},
      scales: {{
        x: {{ type: 'linear', min: 0, max: 1, title: {{ display: true, text: xLabel }} }},
        y: {{ type: 'linear', min: 0, max: 1, title: {{ display: true, text: yLabel }} }}
      }}
    }}
  }};
}}

new Chart(document.getElementById('chartRoc'), lineConfig([
  {{ label: 'XGBoost', data: DATA.roc_xgb, borderColor: '#2a78d6', backgroundColor: 'transparent' }},
  {{ label: 'LightGBM', data: DATA.roc_lgbm, borderColor: '#1baf7a', backgroundColor: 'transparent' }},
  {{ label: 'Random', data: [{{x:0,y:0}},{{x:1,y:1}}], borderColor: '#c3c2b7', borderDash: [4,4], backgroundColor: 'transparent' }},
], 'False Positive Rate', 'True Positive Rate'));

new Chart(document.getElementById('chartPr'), lineConfig([
  {{ label: 'XGBoost', data: DATA.pr_xgb, borderColor: '#2a78d6', backgroundColor: 'transparent' }},
  {{ label: 'LightGBM', data: DATA.pr_lgbm, borderColor: '#1baf7a', backgroundColor: 'transparent' }},
], 'Recall', 'Precision'));

new Chart(document.getElementById('chartProfit'), {{
  type: 'bar',
  data: {{
    labels: DATA.scenario_names,
    datasets: [{{
      label: 'Lợi nhuận (VND)',
      data: DATA.scenario_profits,
      backgroundColor: ['#898781', '#eda100', '#2a78d6', '#1baf7a'],
      borderRadius: 4,
      maxBarThickness: 64,
    }}]
  }},
  options: {{
    responsive: true,
    plugins: {{ legend: {{ display: false }} }},
    scales: {{ y: {{ beginAtZero: true, ticks: {{ callback: v => (v/1e6) + 'M' }} }} }}
  }}
}});
</script>

</body>
</html>
"""

if __name__ == "__main__":
    main()
