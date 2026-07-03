import sys
import json
import os
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, precision_recall_curve, confusion_matrix

sys.stdout.reconfigure(encoding='utf-8')


REQUIRED_FILES = [
    'model_metrics.json',
    '04_test_predictions.csv',
    '04b_test_predictions.csv',
    '04_xgboost_model.pkl',
    '04b_lightgbm_model.pkl',
]


def check_requirements():
    missing = [f for f in REQUIRED_FILES if not os.path.exists(f)]
    if missing:
        print("Thieu file dau vao, hay chay truoc:")
        for f in missing:
            if f.startswith('04_'):
                print(f"  - {f}  <-  python 04_XGBoost_Production.py")
            elif f.startswith('04b_'):
                print(f"  - {f}  <-  python 04b_LightGBM_Production.py")
            else:
                print(f"  - {f}  <-  python 03_Logistic_Regression_Benchmark.py")
        raise SystemExit(1)


def main():
    print("--- STEP 4c: Model Comparison (Logistic Regression vs XGBoost vs LightGBM) ---")
    check_requirements()

    with open('model_metrics.json', 'r', encoding='utf-8') as f:
        all_metrics = json.load(f)

    # --- Bang so sanh metric ---
    print("\nBang so sanh metric (tap test):")
    header = f"{'Model':<28}{'ROC-AUC':>10}{'Accuracy':>10}{'Precision':>11}{'Recall':>10}{'F1':>8}"
    print(header)
    print("-" * len(header))
    for key in ['logistic_regression', 'xgboost', 'lightgbm']:
        m = all_metrics[key]
        print(f"{m['display_name']:<28}{m['roc_auc']:>10.4f}{m['accuracy']:>10.4f}"
              f"{m['precision']:>11.4f}{m['recall']:>10.4f}{m['f1']:>8.4f}")

    # Luu y: day la xep hang theo ROC-AUC (chat luong rank-order tren TOAN BO nguong), khong phai
    # xep hang theo loi nhuan thuc te tai 1 nguong kinh doanh cu the — xem 06_profit_comparison.json
    # va tab "Business Impact" cua presentation.html de biet model nao thang ve ROI.
    best_key = max(['xgboost', 'lightgbm'], key=lambda k: all_metrics[k]['roc_auc'])
    lr_auc = all_metrics['logistic_regression']['roc_auc']
    print(f"\nModel co ROC-AUC cao nhat: {all_metrics[best_key]['display_name']}"
          f" ({all_metrics[best_key]['roc_auc']:.4f}), vuot Logistic Regression benchmark"
          f" (+{all_metrics[best_key]['roc_auc'] - lr_auc:.4f})")
    print("(Model toi uu ve LOI NHUAN co the khac model co ROC-AUC cao nhat — xem Buoc 6)")

    # --- Merge predictions cua 2 model theo Customer_ID ---
    xgb_pred = pd.read_csv('04_test_predictions.csv').rename(columns={'y_proba': 'xgb_proba'})
    lgbm_pred = pd.read_csv('04b_test_predictions.csv').rename(columns={'y_proba': 'lgbm_proba'})
    merged = xgb_pred.merge(lgbm_pred[['Customer_ID', 'lgbm_proba']], on='Customer_ID', how='inner')
    print(f"\nSo khach hang khop duoc ca 2 model tren test set: {len(merged)}")

    y_true = merged['y_true'].values
    xgb_proba = merged['xgb_proba'].values
    lgbm_proba = merged['lgbm_proba'].values

    agree_rate = ((xgb_proba >= 0.5) == (lgbm_proba >= 0.5)).mean()
    proba_corr = np.corrcoef(xgb_proba, lgbm_proba)[0, 1]
    print(f"Ty le 2 model dong y quyet dinh o threshold 0.5: {agree_rate:.2%}")
    print(f"Tuong quan giua 2 xac suat du doan: {proba_corr:.4f}")

    # --- ROC curve overlay ---
    fpr_xgb, tpr_xgb, _ = roc_curve(y_true, xgb_proba)
    fpr_lgbm, tpr_lgbm, _ = roc_curve(y_true, lgbm_proba)

    plt.figure(figsize=(7, 6))
    plt.plot(fpr_xgb, tpr_xgb, label=f"XGBoost (AUC={all_metrics['xgboost']['roc_auc']:.3f})", color='#2980b9')
    plt.plot(fpr_lgbm, tpr_lgbm, label=f"LightGBM (AUC={all_metrics['lightgbm']['roc_auc']:.3f})", color='#27ae60')
    plt.plot([0, 1], [0, 1], linestyle='--', color='gray', label='Random (AUC=0.5)')
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('ROC Curve: XGBoost vs LightGBM')
    plt.legend()
    plt.tight_layout()
    plt.savefig('04c_roc_comparison.png')
    plt.close()
    print("Saved 04c_roc_comparison.png")

    # --- Precision-Recall curve overlay (quan trong vi data mat can bang) ---
    prec_xgb, rec_xgb, _ = precision_recall_curve(y_true, xgb_proba)
    prec_lgbm, rec_lgbm, _ = precision_recall_curve(y_true, lgbm_proba)

    plt.figure(figsize=(7, 6))
    plt.plot(rec_xgb, prec_xgb, label='XGBoost', color='#2980b9')
    plt.plot(rec_lgbm, prec_lgbm, label='LightGBM', color='#27ae60')
    baseline = y_true.mean()
    plt.axhline(baseline, linestyle='--', color='gray', label=f'Baseline (response rate={baseline:.2%})')
    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.title('Precision-Recall Curve: XGBoost vs LightGBM')
    plt.legend()
    plt.tight_layout()
    plt.savefig('04c_pr_comparison.png')
    plt.close()
    print("Saved 04c_pr_comparison.png")

    # --- Confusion matrices canh nhau (threshold 0.5) ---
    cm_xgb = confusion_matrix(y_true, (xgb_proba >= 0.5).astype(int))
    cm_lgbm = confusion_matrix(y_true, (lgbm_proba >= 0.5).astype(int))

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    for ax, cm, title in zip(axes, [cm_xgb, cm_lgbm], ['XGBoost', 'LightGBM']):
        im = ax.imshow(cm, cmap='Blues')
        ax.set_title(f'{title} (threshold=0.5)')
        ax.set_xlabel('Predicted')
        ax.set_ylabel('Actual')
        ax.set_xticks([0, 1])
        ax.set_yticks([0, 1])
        ax.set_xticklabels(['No Response', 'Response'])
        ax.set_yticklabels(['No Response', 'Response'])
        for i in range(2):
            for j in range(2):
                ax.text(j, i, f'{cm[i, j]:,}', ha='center', va='center',
                         color='white' if cm[i, j] > cm.max() / 2 else 'black')
    plt.tight_layout()
    plt.savefig('04c_confusion_matrices.png')
    plt.close()
    print("Saved 04c_confusion_matrices.png")

    # --- Feature importance comparison ---
    xgb_pipeline = joblib.load('04_xgboost_model.pkl')
    lgbm_pipeline = joblib.load('04b_lightgbm_model.pkl')

    xgb_feat_names = xgb_pipeline.named_steps['preprocessor'].get_feature_names_out()
    lgbm_feat_names = lgbm_pipeline.named_steps['preprocessor'].get_feature_names_out()
    xgb_importance = pd.Series(xgb_pipeline.named_steps['classifier'].feature_importances_, index=xgb_feat_names)
    lgbm_importance = pd.Series(lgbm_pipeline.named_steps['classifier'].feature_importances_, index=lgbm_feat_names)

    # Chuan hoa ve % ty trong de so sanh cong bang (2 thu vien tinh importance khac thang do)
    xgb_importance = (xgb_importance / xgb_importance.sum()).sort_values(ascending=False)
    lgbm_importance = (lgbm_importance / lgbm_importance.sum()).sort_values(ascending=False)

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    xgb_importance.head(8).sort_values().plot(kind='barh', ax=axes[0], color='#2980b9')
    axes[0].set_title('XGBoost - Feature Importance (%)')
    lgbm_importance.head(8).sort_values().plot(kind='barh', ax=axes[1], color='#27ae60')
    axes[1].set_title('LightGBM - Feature Importance (%)')
    plt.tight_layout()
    plt.savefig('04c_feature_importance_comparison.png')
    plt.close()
    print("Saved 04c_feature_importance_comparison.png")

    # --- Luu tom tat cho build_presentation.py ---
    summary = {
        'metrics': all_metrics,
        'best_model_by_auc_key': best_key,
        'best_model_by_auc_name': all_metrics[best_key]['display_name'],
        'test_set_size': int(len(merged)),
        'agree_rate_at_0.5': float(agree_rate),
        'proba_correlation': float(proba_corr),
        'xgb_top_features': xgb_importance.head(8).round(4).to_dict(),
        'lgbm_top_features': lgbm_importance.head(8).round(4).to_dict(),
    }
    with open('model_comparison_summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print("\nSaved model_comparison_summary.json")


if __name__ == "__main__":
    main()
