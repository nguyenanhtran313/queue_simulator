"""
08_Model_Comparison_ROI.py — So sánh công bằng (apples-to-apples) 6 mô hình:
  Propensity: Logistic Regression, XGBoost, LightGBM (dự đoán P(phản hồi))
  Uplift (S-Learner, cùng 3 thuật toán trên): dự đoán mức TĂNG THÊM xác suất phản hồi
  nhờ khuyến mãi (Uplift Score = P(mua|có KM) − P(mua|không KM))

Khác với các script 03/04/04b/06/07 (mỗi script tự đọc data & tự chia train/test riêng,
một số bước còn đánh giá trên toàn bộ data kể cả phần đã dùng để train — dễ lạc quan giả),
script này:
  1) Chỉ CHIA train/test MỘT LẦN DUY NHẤT (80/20, stratify theo target), dùng chung cho cả
     6 model — đảm bảo so sánh công bằng.
  2) Đánh giá Accuracy/Precision/Recall/Profit CHỈ trên tập TEST (20% chưa từng thấy khi
     train) — con số phản ánh đúng hiệu quả khi triển khai thực tế, không lạc quan giả do
     data leakage.

Business context (đã cập nhật):
  - Chi phí gửi 1 tin ZNS = 500 VND/tin/khách hàng.
  - Lợi nhuận trung bình nếu khách hàng phản hồi = 10.000 VND/khách hàng.
  - Ngưỡng hoà vốn (break-even) = cost/reward = 5%.

Quy ước "quyết định gửi" (Send) dùng CHUNG cho cả 6 model để Profit so sánh được với nhau:
  - Model Propensity: gửi nếu P(phản hồi) > 5%.
  - Model Uplift: gửi nếu Uplift Score > 5% (tức khuyến mãi làm tăng >5 điểm % xác suất
    phản hồi — đúng tinh thần "chỉ gửi cho Persuadables" của Bước 7).

QUAN TRỌNG — Accuracy/Precision/Recall dùng ĐÚNG NGƯỠNG 5% này, KHÔNG dùng 0.5 mặc định:
  Bản đầu tiên của script này tính Accuracy/Precision/Recall bằng `model.predict()` (ngưỡng
  0.5 mặc định của sklearn) trong khi Profit lại dùng ngưỡng hoà vốn 5% — 2 ngưỡng khác nhau,
  không liên quan gì tới nhau về mặt kinh tế. Hậu quả: XGBoost trông như "chỉ bắt được 3%
  khách sẽ phản hồi" (recall@0.5) trong khi thực ra nó vẫn gửi cho 62% khách hàng một cách có
  lời (send@5%) — hai con số ĐÚNG nhưng đo 2 thứ khác nhau, khiến bảng số liệu trông tự mâu
  thuẫn và vô nghĩa. Ngưỡng 0.5 không có ý nghĩa kinh tế gì ở đây (0.5 chỉ hợp lý khi
  cost≈reward, còn ở đây cost/reward=5%). Vì vậy Accuracy/Precision/Recall ở bản này được
  tính tại ĐÚNG ngưỡng dùng để ra quyết định gửi (breakeven 5%) — để 3 chỉ số này giải thích
  được VÌ SAO Profit lại như vậy, thay vì mâu thuẫn với nó.

Lưu ý về Accuracy/Precision/Recall của model Uplift (đọc kỹ trước khi diễn giải số liệu):
  Uplift model KHÔNG được thiết kế để dự đoán "khách này có phản hồi không" (đó là việc
  của Propensity model) — nó trả lời câu hỏi khác: "khuyến mãi có làm khách này đổi ý
  không". Ở đây ta vẫn tính Accuracy/Precision/Recall bằng cách so (Uplift Score > 5%, cùng
  ngưỡng breakeven với quyết định gửi) với nhãn thực tế, chỉ để có một con số so sánh trực
  quan trên cùng thang đo — không phải thước đo "đúng bản chất" của Uplift model. Nhìn Profit
  mới là thước đo đúng bản chất.

ROI = Tổng lợi nhuận / Tổng chi phí (profit_vnd / (n_sent x 500đ)). VD: ROI=1.5x nghĩa là mỗi
1đ chi ra để gửi ZNS mang về 1.5đ lợi nhuận ròng. Khác Profit (đo QUY MÔ giá trị tạo ra),
ROI đo HIỆU QUẢ sử dụng ngân sách — 1 model có thể Profit cao nhưng ROI thấp nếu gửi tràn lan.

Chạy:  py 08_Model_Comparison_ROI.py   (cần đã chạy 00_generate_data.py trước)
Output: 08_model_comparison_results.csv (có cột roi), 08_uplift_gain_by_decile.csv,
        08_feature_importance.csv, 08_baselines.json (có mass_marketing_roi)
"""

import sys
import json
import time

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

COST_PER_MESSAGE = 500       # VND — chi phí gửi 1 tin ZNS
REWARD_PER_RESPONSE = 10000  # VND — lợi nhuận trung bình/khách hàng phản hồi
BREAK_EVEN = COST_PER_MESSAGE / REWARD_PER_RESPONSE  # 5%

NUM_COLS = ["Age", "Avg_Monthly_Balance_VND", "Txn_Count_3M", "Txn_Amount_3M_VND",
            "App_Logins_3M", "Promo_Txn_Count_3M", "Last_Active_Days"]
CAT_COLS = ["Gender", "Segment"]
# Feature set cho Uplift: loại Promo_Txn_Count_3M (dùng để suy ra Treatment -> tránh circularity)
NUM_COLS_UPLIFT = [c for c in NUM_COLS if c != "Promo_Txn_Count_3M"]


def realized_profit(send_mask: np.ndarray, y_true: np.ndarray) -> float:
    """Lợi nhuận thực tế trên tập test: gửi cho ai -> trừ cost; nếu người đó thực sự phản
    hồi (y_true=1) -> cộng thêm reward."""
    n_sent = int(send_mask.sum())
    n_sent_and_responded = int((send_mask & (y_true == 1)).sum())
    return n_sent_and_responded * REWARD_PER_RESPONSE - n_sent * COST_PER_MESSAGE


def compute_roi(profit_vnd: float, n_sent: int) -> float:
    """ROI = Tổng lợi nhuận / Tổng chi phí. VD: ROI=1.5 nghĩa là mỗi 1đ chi phí gửi ZNS
    mang về 1.5đ lợi nhuận ròng. Không gửi ai (n_sent=0) -> ROI không xác định (NaN)."""
    total_cost = n_sent * COST_PER_MESSAGE
    return profit_vnd / total_cost if total_cost > 0 else float("nan")


def propensity_pipeline(kind: str) -> Pipeline:
    if kind == "logistic":
        pre = ColumnTransformer([
            ("num", StandardScaler(), NUM_COLS),
            ("cat", OneHotEncoder(drop="first", handle_unknown="ignore"), CAT_COLS),
        ])
        clf = LogisticRegression(random_state=42, max_iter=1000, class_weight="balanced")
    elif kind == "xgboost":
        pre = ColumnTransformer([
            ("cat", OneHotEncoder(drop="first", handle_unknown="ignore"), CAT_COLS),
        ], remainder="passthrough")
        clf = XGBClassifier(eval_metric="logloss", random_state=42,
                             tree_method="hist", n_estimators=200)
    elif kind == "lightgbm":
        pre = ColumnTransformer([
            ("cat", OneHotEncoder(drop="first", handle_unknown="ignore"), CAT_COLS),
        ], remainder="passthrough")
        # Cấu hình "data lớn" (xem ghi chú review ở 04b) — không ép nhỏ num_leaves/max_depth nữa.
        clf = LGBMClassifier(random_state=42, class_weight="balanced", n_estimators=300,
                              learning_rate=0.05, num_leaves=31, max_depth=-1,
                              min_child_samples=20, verbose=-1)
    else:
        raise ValueError(kind)
    return Pipeline([("preprocessor", pre), ("classifier", clf)])


def uplift_pipeline(kind: str) -> Pipeline:
    """S-Learner: preprocessor giống propensity nhưng bỏ Promo_Txn_Count_3M, thêm Treatment
    như 1 cột passthrough (0/1)."""
    if kind == "logistic":
        pre = ColumnTransformer([
            ("num", StandardScaler(), NUM_COLS_UPLIFT + ["Treatment"]),
            ("cat", OneHotEncoder(drop="first", handle_unknown="ignore"), CAT_COLS),
        ])
        clf = LogisticRegression(random_state=42, max_iter=1000, class_weight="balanced")
    elif kind == "xgboost":
        pre = ColumnTransformer([
            ("cat", OneHotEncoder(drop="first", handle_unknown="ignore"), CAT_COLS),
        ], remainder="passthrough")
        clf = XGBClassifier(eval_metric="logloss", random_state=42,
                             tree_method="hist", n_estimators=200)
    elif kind == "lightgbm":
        pre = ColumnTransformer([
            ("cat", OneHotEncoder(drop="first", handle_unknown="ignore"), CAT_COLS),
        ], remainder="passthrough")
        clf = LGBMClassifier(random_state=42, class_weight="balanced", n_estimators=300,
                              learning_rate=0.05, num_leaves=31, max_depth=-1,
                              min_child_samples=20, verbose=-1)
    else:
        raise ValueError(kind)
    return Pipeline([("preprocessor", pre), ("classifier", clf)])


def main() -> None:
    t_start = time.time()
    print("--- STEP 8: So sánh 6 mô hình (Propensity x3 + Uplift x3) trên cùng 1 tập test ---")
    df = pd.read_csv("customer_promo_data.csv")
    y = df["Historical_Promo_Response"]
    X = df.drop(columns=["Customer_ID", "Historical_Promo_Response", "Estimated_CLV_VND"])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    y_test_arr = y_test.to_numpy()
    print(f"Train: {len(X_train):,} | Test: {len(X_test):,} | "
          f"Response rate test: {y_test.mean():.2%}")

    results = []
    feature_importance_rows = []

    # ---------------- Propensity models ----------------
    for kind, label in [("logistic", "Logistic Regression"),
                         ("xgboost", "XGBoost"),
                         ("lightgbm", "LightGBM")]:
        t0 = time.time()
        model = propensity_pipeline(kind)
        model.fit(X_train, y_train)
        y_proba = model.predict_proba(X_test)[:, 1]
        send = y_proba > BREAK_EVEN
        # Accuracy/Precision/Recall tại ĐÚNG ngưỡng dùng để quyết định gửi (5%), không phải
        # 0.5 mặc định — xem giải thích ở docstring đầu file.
        y_pred = send.astype(int)

        profit = realized_profit(send, y_test_arr)
        n_sent = int(send.sum())
        roi = compute_roi(profit, n_sent)
        results.append({
            "model": label,
            "family": "Propensity",
            "accuracy": accuracy_score(y_test, y_pred),
            "precision": precision_score(y_test, y_pred, zero_division=0),
            "recall": recall_score(y_test, y_pred, zero_division=0),
            "roc_auc": roc_auc_score(y_test, y_proba),
            "n_sent": n_sent,
            "n_test": len(y_test),
            "profit_vnd": profit,
            "total_cost_vnd": n_sent * COST_PER_MESSAGE,
            "roi": roi,
        })
        print(f"[{label:20s}] acc={results[-1]['accuracy']:.3f} "
              f"prec={results[-1]['precision']:.3f} rec={results[-1]['recall']:.3f} "
              f"profit={profit:,.0f} VND  roi={roi:.2f}x  ({time.time()-t0:.1f}s)")

        if kind in ("xgboost", "lightgbm"):
            clf = model.named_steps["classifier"]
            feat_names = model.named_steps["preprocessor"].get_feature_names_out()
            fi = pd.Series(clf.feature_importances_, index=feat_names).sort_values(ascending=False)
            for feat, imp in fi.head(8).items():
                feature_importance_rows.append({"model": label, "feature": feat, "importance": float(imp)})

    # ---------------- Uplift S-Learner models ----------------
    treatment_train = (X_train["Promo_Txn_Count_3M"] > 0).astype(int)
    Xu_train = X_train.drop(columns=["Promo_Txn_Count_3M"]).copy()
    Xu_train["Treatment"] = treatment_train

    Xu_test_1 = X_test.drop(columns=["Promo_Txn_Count_3M"]).copy()
    Xu_test_1["Treatment"] = 1
    Xu_test_0 = X_test.drop(columns=["Promo_Txn_Count_3M"]).copy()
    Xu_test_0["Treatment"] = 0

    best_uplift_score_for_gain_chart = None
    best_uplift_profit = -np.inf

    for kind, label in [("logistic", "Logistic Regression"),
                         ("xgboost", "XGBoost"),
                         ("lightgbm", "LightGBM")]:
        t0 = time.time()
        model = uplift_pipeline(kind)
        model.fit(Xu_train, y_train)

        prob_treat_1 = model.predict_proba(Xu_test_1)[:, 1]
        prob_treat_0 = model.predict_proba(Xu_test_0)[:, 1]
        uplift_score = prob_treat_1 - prob_treat_0

        send = uplift_score > BREAK_EVEN
        # Cùng ngưỡng breakeven với quyết định gửi (xem giải thích ở docstring đầu file).
        y_pred_class = send.astype(int)
        profit = realized_profit(send, y_test_arr)
        n_sent = int(send.sum())
        roi = compute_roi(profit, n_sent)

        label_full = f"{label} (Uplift)"
        results.append({
            "model": label_full,
            "family": "Uplift",
            "accuracy": accuracy_score(y_test, y_pred_class),
            "precision": precision_score(y_test, y_pred_class, zero_division=0),
            "recall": recall_score(y_test, y_pred_class, zero_division=0),
            "roc_auc": np.nan,  # AUC không có ý nghĩa chuẩn cho uplift score (không phải xác suất)
            "n_sent": n_sent,
            "n_test": len(y_test),
            "profit_vnd": profit,
            "total_cost_vnd": n_sent * COST_PER_MESSAGE,
            "roi": roi,
        })
        print(f"[{label_full:20s}] acc={results[-1]['accuracy']:.3f} "
              f"prec={results[-1]['precision']:.3f} rec={results[-1]['recall']:.3f} "
              f"profit={profit:,.0f} VND  roi={roi:.2f}x  ({time.time()-t0:.1f}s)")

        if profit > best_uplift_profit:
            best_uplift_profit = profit
            best_uplift_score_for_gain_chart = (label_full, uplift_score)

    results_df = pd.DataFrame(results)
    results_df.to_csv("08_model_comparison_results.csv", index=False)
    print("\nĐã lưu 08_model_comparison_results.csv")

    if feature_importance_rows:
        pd.DataFrame(feature_importance_rows).to_csv("08_feature_importance.csv", index=False)
        print("Đã lưu 08_feature_importance.csv")

    # ---------------- Gain-by-decile chart cho uplift model tốt nhất ----------------
    # Xếp khách hàng test theo Uplift Score giảm dần, chia 10 nhóm bằng nhau (decile),
    # tính lợi nhuận thực tế nếu CHỈ nhắm tới top-k decile (k=1..10) -> minh hoạ lợi nhuận
    # tập trung mạnh ở nhóm Uplift cao nhất (Persuadables).
    best_label, best_scores = best_uplift_score_for_gain_chart
    order = np.argsort(-best_scores)
    y_sorted = y_test_arr[order]
    n = len(y_sorted)
    decile_rows = []
    for k in range(1, 11):
        cutoff = int(np.ceil(n * k / 10))
        send_topk = np.zeros(n, dtype=bool)
        send_topk[:cutoff] = True
        profit_topk = realized_profit(send_topk, y_sorted)
        decile_rows.append({
            "decile": k, "model": best_label,
            "cum_customers_pct": round(100 * cutoff / n, 1),
            "cum_profit_vnd": profit_topk,
        })
    pd.DataFrame(decile_rows).to_csv("08_uplift_gain_by_decile.csv", index=False)
    print(f"Đã lưu 08_uplift_gain_by_decile.csv (model tốt nhất: {best_label})")

    # ---------------- Baselines cho biểu đồ Profit ----------------
    mass_profit = int(y_test.sum()) * REWARD_PER_RESPONSE - len(y_test) * COST_PER_MESSAGE
    mass_roi = compute_roi(mass_profit, len(y_test))
    baselines = {"mass_marketing_profit_vnd": mass_profit, "do_nothing_profit_vnd": 0,
                 "mass_marketing_total_cost_vnd": len(y_test) * COST_PER_MESSAGE,
                 "mass_marketing_roi": mass_roi,
                 "break_even_threshold": BREAK_EVEN, "n_test": len(y_test),
                 "test_response_rate": float(y_test.mean())}
    with open("08_baselines.json", "w", encoding="utf-8") as f:
        json.dump(baselines, f, ensure_ascii=False, indent=2)
    print(f"Lợi nhuận Mass Marketing (gửi hết) trên tập test: {mass_profit:,.0f} VND")
    print(f"Đã lưu 08_baselines.json")

    print(f"\nTổng thời gian: {time.time()-t_start:.1f}s")


if __name__ == "__main__":
    main()
