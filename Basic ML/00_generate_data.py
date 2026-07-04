"""
00_generate_data.py — Sinh dữ liệu mock quy mô lớn (100,000 khách hàng) để thay thế
customer_promo_data.csv gốc (chỉ có 1,000 dòng).

QUAN TRỌNG: đây không phải random hoàn toàn — dữ liệu được sinh ra có chủ đích để nhiều biến
CÙNG mang tín hiệu thật (không chỉ 1 biến), vì bộ dữ liệu ban đầu (chỉ Promo_Txn_Count_3M +
Last_Active_Days có tín hiệu rõ, còn lại gần như nhiễu 100%) bị đánh giá là quá nghèo — không
đại diện cho một bài toán ML thực tế (nơi nhiều đặc trưng cùng đóng góp thông tin, có mạnh có
yếu). Thiết kế hiện tại (2026-07-03):
  - Promo_Txn_Count_3M   : tương quan DƯƠNG mạnh nhất (tần suất dùng KM trước đây)
  - Last_Active_Days     : tương quan ÂM mạnh (càng lâu không hoạt động càng ít phản hồi)
  - Txn_Count_3M         : tương quan DƯƠNG vừa (khách càng giao dịch nhiều càng dễ phản hồi)
  - App_Logins_3M        : tương quan DƯƠNG vừa (dùng app nhiều → dễ thấy/bấm khuyến mãi)
  - Avg_Monthly_Balance_VND: tương quan DƯƠNG vừa (số dư cao → có khả năng chi tiêu hơn)
  - Age                  : tương quan ÂM nhẹ (khách trẻ hơi nhạy khuyến mãi hơn)
  - Segment               : Priority > Gold > Standard về response rate
  - Gender, Txn_Amount_3M_VND: CỐ Ý giữ gần như nhiễu — Gender để có 1 biến "vô hại" làm đối
    chứng (không phải biến nào cũng quan trọng); Txn_Amount_3M_VND vì nó ăn chung "activity
    latent" với Txn_Count_3M/App_Logins_3M nên tự nhiên bị dư thừa thông tin (redundant), một
    ví dụ multicollinearity nhẹ khác ngoài cặp CLV~Balance.
  - Estimated_CLV_VND ~ Avg_Monthly_Balance_VND (tương quan ~0.95-0.99) — bẫy đa cộng
    tuyến cố ý giữ lại.

Chạy:  py 00_generate_data.py
Output: ghi đè customer_promo_data.csv (bản gốc 1,000 dòng đã backup ở
customer_promo_data_1k_backup.csv).
"""

import sys
import numpy as np
import pandas as pd
from scipy.special import expit, logit

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

N = 100_000
SEED = 42
# LƯU Ý: bộ 1,000 dòng gốc có response rate 37.3%. Với business constants MỚI (cost 500đ /
# reward 10.000đ -> break-even chỉ 5%), baseline 37% khiến hầu hết khách hàng đều vượt
# ngưỡng hoà vốn -> "gửi đại trà" và "gửi chọn lọc bằng ML" cho lợi nhuận gần như giống hệt
# nhau, làm mất hết giá trị minh hoạ của bài toán. Ta hạ baseline xuống 12% (mức phản hồi
# ZNS/SMS marketing điển hình trong thực tế) để việc target đúng người thực sự tạo ra
# khác biệt lợi nhuận rõ rệt — đúng tinh thần bài toán "tối ưu ai nên gửi khuyến mãi".
TARGET_RESPONSE_RATE = 0.12


def main() -> None:
    rng = np.random.default_rng(SEED)
    print(f"--- STEP 0: Sinh dữ liệu mock {N:,} khách hàng ---")

    # ---- Customer_ID (định danh, không dùng làm feature) ----
    ids = rng.choice(np.arange(10_000_000, 99_999_999), size=N, replace=False)
    customer_id = "TCB" + pd.Series(ids).astype(str)

    # ---- Nhân khẩu học: KHÔNG ảnh hưởng target (giữ đúng phát hiện EDA gốc) ----
    age = np.clip(rng.normal(43.3, 15.3, N), 18, 70).round().astype(int)
    gender = rng.choice(["Male", "Female"], size=N, p=[0.534, 0.466])

    # ---- Segment: tỷ lệ giữ theo bộ gốc (Standard 59% / Gold 31% / Priority 10%) ----
    segment = rng.choice(["Standard", "Gold", "Priority"], size=N, p=[0.592, 0.305, 0.103])

    # ---- Avg_Monthly_Balance_VND: lognormal theo Segment (Priority >> Gold > Standard) ----
    seg_median_balance = {"Standard": 12_000_000.0, "Gold": 60_000_000.0, "Priority": 300_000_000.0}
    seg_sigma = {"Standard": 1.1, "Gold": 1.15, "Priority": 1.3}
    balance = np.empty(N)
    for seg, med in seg_median_balance.items():
        mask = segment == seg
        n_seg = mask.sum()
        balance[mask] = rng.lognormal(mean=np.log(med), sigma=seg_sigma[seg], size=n_seg)
    # ~1% khách hàng "ngủ đông" số dư gần 0 (mô phỏng đúng min=0 của bộ gốc)
    dormant = rng.random(N) < 0.01
    balance[dormant] = rng.uniform(0, 50_000, dormant.sum())
    balance = balance.round().astype(np.int64)

    # ---- Nhóm "hoạt động" dùng chung 1 biến ẩn để 3 cột này tự tương quan chéo với
    # nhau (đúng phát hiện EDA: Txn_Count/Txn_Amount/App_Logins corr chéo 0.70-0.86)
    # nhưng KHÔNG đưa activity_level vào target -> vẫn giữ "nhiễu" với response.
    activity_level = rng.gamma(shape=4.0, scale=1.0, size=N)
    txn_count_3m = rng.poisson(activity_level * 5.0)
    app_logins_3m = np.maximum(1, rng.poisson(activity_level * 8.75))
    txn_amount_noise = rng.lognormal(mean=0.0, sigma=0.4, size=N)
    txn_amount_3m = (activity_level * 13_900_000 * txn_amount_noise).round().astype(np.int64)

    # ---- Promo_Txn_Count_3M: zero-inflated, tín hiệu MẠNH NHẤT tới target ----
    promo_txn_count_3m = rng.negative_binomial(n=1, p=0.4, size=N)

    # ---- Last_Active_Days: gần như uniform 0-90 (khớp mean/std bộ gốc) ----
    last_active_days = rng.integers(0, 91, size=N)

    # ---- Historical_Promo_Response: hàm logistic của 3 biến ý nghĩa + Segment
    # + HIỆU ỨNG NHÂN QUẢ DỊ BIỆT (heterogeneous treatment effect) của khuyến mãi ----
    # Treatment = từng dùng khuyến mãi (Promo_Txn_Count_3M > 0), đúng định nghĩa ở
    # 07_Uplift_Modeling_ROI.py. Nếu khuyến mãi có tác động Y HỆT NHAU với mọi khách hàng,
    # Uplift Score sẽ luôn dương -> model Uplift suy biến thành "gửi cho tất cả" (vô nghĩa,
    # không khác gì Propensity). Thực tế khuyến mãi chỉ thực sự đổi ý được một nhóm khách
    # hàng (Persuadables); nhóm khác vốn dĩ sẽ mua/không mua bất kể có khuyến mãi hay không
    # (Sure things / Lost causes), thậm chí có nhóm phản cảm với spam khuyến mãi (Sleeping
    # dogs). Ta mô phỏng đúng 4 nhóm này bằng 1 biến ẩn (KHÔNG lưu vào CSV — ngoài đời thật
    # nhóm này cũng ẩn, model Uplift phải tự suy luận ra từ Segment/Last_Active_Days/Balance).
    z_promo = (promo_txn_count_3m - promo_txn_count_3m.mean()) / promo_txn_count_3m.std()
    z_last_active = (last_active_days - last_active_days.mean()) / last_active_days.std()
    log_balance = np.log1p(balance)
    z_log_balance = (log_balance - log_balance.mean()) / log_balance.std()
    # Thêm 3 biến sau vào phương trình response (trước đây bị cố tình giữ như nhiễu 100%,
    # nay cho tín hiệu thật vừa phải để dataset không chỉ có 1 biến mạnh cô độc):
    z_txn_count = (txn_count_3m - txn_count_3m.mean()) / txn_count_3m.std()
    z_app_logins = (app_logins_3m - app_logins_3m.mean()) / app_logins_3m.std()
    z_age = (age - age.mean()) / age.std()
    is_priority = (segment == "Priority").astype(float)
    treatment = (promo_txn_count_3m > 0).astype(float)

    # Điểm ái lực (affinity) với từng nhóm dị biệt, dựa trên đặc điểm quan sát được
    # (Priority + đang hoạt động tích cực -> dễ là "Sure things"; càng lâu không hoạt động
    # -> dễ là "Lost causes"; Priority + số dư siêu cao -> dễ là "Sleeping dogs"; còn lại
    # mặc định nghiêng về "Persuadables").
    score_persuadables = np.full(N, 0.5)
    score_sure_things = 1.5 * is_priority - 1.0 * z_last_active
    score_lost_causes = 1.4 * z_last_active - 0.6 * is_priority
    score_sleeping_dogs = 1.7 * is_priority + 0.9 * z_log_balance - 1.3

    group_scores = np.column_stack(
        [score_persuadables, score_sure_things, score_lost_causes, score_sleeping_dogs]
    )
    group_probs = np.exp(group_scores - group_scores.max(axis=1, keepdims=True))
    group_probs /= group_probs.sum(axis=1, keepdims=True)
    group_idx = (rng.random(N)[:, None] > np.cumsum(group_probs, axis=1)).sum(axis=1)
    group_names = np.array(["Persuadables", "Sure_things", "Lost_causes", "Sleeping_dogs"])[group_idx]

    # baseline_boost: đặc điểm "vốn dĩ" của nhóm, KHÔNG phụ thuộc có được gửi KM hay không.
    # treatment_h: hiệu ứng NHÂN QUẢ của khuyến mãi, khác nhau theo từng nhóm -> đây chính
    # là thứ Uplift Score (P(mua|có KM) - P(mua|không KM)) phải học ra được.
    baseline_boost_map = {"Persuadables": 0.0, "Sure_things": 1.3, "Lost_causes": -1.1, "Sleeping_dogs": 0.2}
    treatment_h_map = {"Persuadables": 1.1, "Sure_things": 0.05, "Lost_causes": 0.05, "Sleeping_dogs": -0.7}
    baseline_boost = pd.Series(group_names).map(baseline_boost_map).to_numpy()
    treatment_h = pd.Series(group_names).map(treatment_h_map).to_numpy()

    seg_logodds_offset = pd.Series(segment).map(
        {"Standard": 0.0, "Gold": 0.35, "Priority": 0.55}
    ).to_numpy()

    score = (
        0.35 * z_promo             # tần suất dùng KM nói chung -> propensity NỀN (không phải nhân quả)
        - 0.55 * z_last_active
        + 0.30 * z_log_balance
        + 0.25 * z_txn_count       # MỚI: giao dịch nhiều -> dễ phản hồi hơn (tín hiệu vừa)
        + 0.20 * z_app_logins      # MỚI: dùng app nhiều -> dễ thấy/bấm khuyến mãi (tín hiệu vừa)
        - 0.15 * z_age             # MỚI: khách trẻ hơi nhạy khuyến mãi hơn (tín hiệu nhẹ)
        + seg_logodds_offset
        + baseline_boost           # đặc điểm vốn có của nhóm dị biệt
        + treatment_h * treatment  # hiệu ứng NHÂN QUẢ dị biệt của khuyến mãi (cốt lõi bài Uplift)
        + rng.normal(0, 0.35, N)   # nhiễu ngẫu nhiên còn lại (Gender, Txn_Amount_3M_VND vẫn nhiễu)
    )

    # Hiệu chỉnh intercept để mean(sigmoid) ~= TARGET_RESPONSE_RATE
    b0 = logit(TARGET_RESPONSE_RATE) - score.mean()
    for _ in range(5):
        p = expit(score + b0)
        b0 += logit(TARGET_RESPONSE_RATE) - logit(np.clip(p.mean(), 1e-6, 1 - 1e-6))
    prob_response = expit(score + b0)
    historical_promo_response = (rng.random(N) < prob_response).astype(int)

    # ---- Estimated_CLV_VND: bẫy đa cộng tuyến, gần như trùng Avg_Monthly_Balance_VND ----
    clv_factor = np.clip(rng.normal(0.06, 0.025, N), 0.01, 0.30)
    estimated_clv = np.maximum(1000, (balance * clv_factor)).round().astype(np.int64)

    df = pd.DataFrame({
        "Customer_ID": customer_id,
        "Age": age,
        "Gender": gender,
        "Segment": segment,
        "Avg_Monthly_Balance_VND": balance,
        "Txn_Count_3M": txn_count_3m,
        "Txn_Amount_3M_VND": txn_amount_3m,
        "App_Logins_3M": app_logins_3m,
        "Promo_Txn_Count_3M": promo_txn_count_3m,
        "Last_Active_Days": last_active_days,
        "Historical_Promo_Response": historical_promo_response,
        "Estimated_CLV_VND": estimated_clv,
    })

    df.to_csv("customer_promo_data.csv", index=False)

    print(f"Đã sinh {len(df):,} dòng -> customer_promo_data.csv")
    print(f"Response rate: {df['Historical_Promo_Response'].mean():.2%} "
          f"(mục tiêu {TARGET_RESPONSE_RATE:.0%})")
    print("\nKiểm tra nhanh tương quan với target (phải khớp dấu với bản gốc):")
    corr = df.select_dtypes("number").corr()["Historical_Promo_Response"].sort_values()
    print(corr)
    print(f"\nCorr(Avg_Monthly_Balance_VND, Estimated_CLV_VND) = "
          f"{df['Avg_Monthly_Balance_VND'].corr(df['Estimated_CLV_VND']):.4f} (kỳ vọng > 0.9)")
    print(f"\nSegment distribution:\n{df['Segment'].value_counts(normalize=True)}")

    # ---- Diagnostics CHỈ để kiểm tra (không lưu vào CSV) — xác nhận Uplift thực sự có
    # tín hiệu dị biệt để học, tránh lặp lại lỗi "Uplift Score luôn dương -> gửi cho tất cả".
    diag = pd.DataFrame({
        "group": group_names, "treatment": treatment.astype(int),
        "response": historical_promo_response,
    })
    print("\n--- Diagnostics: response rate theo (nhóm ẩn x Treatment) — chỉ để kiểm tra ---")
    print(diag.groupby(["group", "treatment"])["response"].agg(["mean", "count"]))
    print(f"\nTỷ trọng nhóm ẩn:\n{diag['group'].value_counts(normalize=True)}")


if __name__ == "__main__":
    main()
