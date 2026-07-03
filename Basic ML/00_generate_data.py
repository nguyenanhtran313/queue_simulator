import numpy as np
import pandas as pd


def main():
    print("--- STEP 0: Generate Mock Customer Promo Data ---")
    rng = np.random.default_rng(42)
    n = 10_000

    # --- Nhân khẩu học: KHÔNG có tín hiệu thật với target (giữ đúng kết luận EDA gốc) ---
    age = rng.integers(18, 71, size=n)
    gender = rng.choice(['Male', 'Female'], size=n, p=[0.52, 0.48])

    # --- Phân khúc khách hàng: CÓ tín hiệu (Priority/Gold phản hồi tốt hơn Standard) ---
    segment = rng.choice(['Standard', 'Gold', 'Priority'], size=n, p=[0.59, 0.305, 0.105])
    segment_balance_mean = {'Standard': 17_000_000, 'Gold': 90_000_000, 'Priority': 480_000_000}
    segment_response_bonus = {'Standard': -0.55, 'Gold': 0.10, 'Priority': 0.55}

    # --- Số dư trung bình: lognormal theo phân khúc, CÓ tín hiệu (nhẹ) ---
    balance_mu = np.array([np.log(segment_balance_mean[s]) for s in segment])
    avg_balance = rng.lognormal(mean=balance_mu - 0.5, sigma=1.0, size=n)
    avg_balance = np.round(avg_balance).astype(np.int64)

    # --- Cụm hành vi (Txn_Count/Txn_Amount/App_Logins): tự tương quan chéo cao nhưng
    #     KHÔNG có tín hiệu với target -> dùng chung 1 latent "activity level" ---
    activity = rng.gamma(shape=2.0, scale=1.0, size=n)
    txn_count = np.round(np.clip(activity * 9 + rng.normal(0, 4, n), 0, None)).astype(int)
    app_logins = np.round(np.clip(activity * 12 + rng.normal(0, 6, n), 0, None)).astype(int)
    txn_amount = np.round(np.clip(activity * 25_000_000 + rng.normal(0, 15_000_000, n), 0, None)).astype(np.int64)

    # --- Promo_Txn_Count_3M: tín hiệu MẠNH nhất (zero-inflated Poisson) ---
    promo_txn = rng.poisson(lam=1.4, size=n)
    promo_txn[rng.random(n) < 0.15] = 0

    # --- Last_Active_Days: tín hiệu âm (càng lâu không hoạt động càng ít phản hồi) ---
    last_active = rng.integers(0, 91, size=n)

    # --- Sinh target qua logistic model, nhưng CỐ TÌNH phi tuyến ở 2 biến quan trọng nhất
    #     (Last_Active_Days, Promo_Txn_Count_3M đều là bậc thang, không phải đường thẳng) + 4 tương tác
    #     nhân -> Logistic Regression (chỉ fit được 1 hệ số tuyến tính/biến, không tự có interaction term)
    #     sẽ hệ thống bỏ lỡ phần lớn cấu trúc này, còn tree-model (XGBoost/LightGBM) thì học được đầy đủ.
    #     Mục tiêu thiết kế: tạo khoảng cách ROC-AUC rõ rệt giữa LogReg và tree-model (~0.05-0.06), đồng thời
    #     nới rộng phổ xác suất dự đoán đủ để Business Impact/Uplift thực sự loại được một phần khách hàng
    #     thay vì hội tụ về "gửi hết" (xem _REQUIREMENT.md để biết lý do đổi). Intercept canh để response
    #     rate ~5% — khớp giả định kinh doanh "tỷ lệ convert 5%" (xem 06_Expected_Profit_Calculation.py). ---
    balance_z = (avg_balance - avg_balance.mean()) / avg_balance.std()
    # Cắt (clip) trước khi bình phương để vài khách hàng cực giàu (đuôi dài của lognormal) không tạo ra
    # z cực đoan phi thực tế — vẫn giữ hiệu ứng "quá giàu thì hơi thờ ơ" nhưng không làm hỏng phân phối.
    balance_z_clip = np.clip(balance_z, -3, 3)

    # Last_Active_Days: bậc thang không đơn điệu, biên độ lớn — "mới hoạt động nhẹ" thì hơi kém (đang lạ),
    # "vừa mới quá" (đang đắn đo, 10-40 ngày) thì tốt NHẤT, sau đó giảm dần, "im ắng lâu ngày" thì giảm rất mạnh.
    last_active_effect = np.select(
        [last_active < 10, last_active < 40, last_active < 70],
        [-0.30, 2.00, -0.80],
        default=-3.20,
    )

    # Promo_Txn_Count_3M: bậc thang bão hoà (không phải tăng tuyến tính đều theo từng lần) — từ 0 sang 1 lần
    # đã là bước nhảy nhỏ, nhưng từ 1 sang 2-3 lần là bước nhảy lớn (khách đã "quen" dùng khuyến mãi), rồi
    # bão hoà dần từ lần thứ 4 trở đi.
    promo_effect = np.select(
        [promo_txn == 0, promo_txn == 1, promo_txn <= 3],
        [-0.90, 0.20, 1.60],
        default=2.10,
    )

    z = (
        -5.28
        + promo_effect
        + last_active_effect
        + 0.22 * balance_z_clip - 0.10 * balance_z_clip ** 2
        + np.array([segment_response_bonus[s] for s in segment])
    )
    # Tương tác 1: vừa dùng khuyến mãi gần đây (>=2 lần) VÀ còn đang hoạt động (<40 ngày) -> bùng nổ phản hồi.
    z += np.where((promo_txn >= 2) & (last_active < 40), 1.2, 0.0)
    # Tương tác 2: khách Priority dùng khuyến mãi thì hiệu ứng mạnh hơn hẳn khách Standard/Gold
    # (Segment x Promo_Txn_Count_3M) — một quan hệ nhân giữa 1 biến phân loại và 1 biến số mà
    # Logistic Regression additive (không có interaction term) không tự bắt được.
    z += np.where((segment == 'Priority') & (promo_txn >= 1), 0.9, 0.0)
    # Tương tác 3: khách Gold vừa hoạt động rất gần đây VÀ có dùng khuyến mãi -> boost thêm (Segment x
    # Last_Active_Days x Promo_Txn_Count_3M, tương tác bậc 3 — hoàn toàn ngoài tầm với của mô hình tuyến tính).
    z += np.where((segment == 'Gold') & (last_active < 20) & (promo_txn >= 1), 0.7, 0.0)
    # Tương tác 4 (bộ khuếch đại tiêu cực): "ngủ đông" lâu ngày VÀ chưa từng dùng khuyến mãi -> phạt kép,
    # đẩy hẳn 1 nhóm khách hàng xuống xác suất gần 0 — đây chính là nhóm mà Business Impact/Uplift cần
    # loại ra khỏi danh sách gửi, thay vì cứ gửi hết như bản dữ liệu cũ.
    z += np.where((last_active >= 70) & (promo_txn == 0), -1.0, 0.0)

    prob = 1 / (1 + np.exp(-z))
    response = (rng.random(n) < prob).astype(int)

    # --- Estimated_CLV_VND: gần như là bản sao của Avg_Monthly_Balance_VND (bẫy đa cộng tuyến, có chủ đích) ---
    clv = avg_balance * rng.normal(loc=0.065, scale=0.003, size=n)
    clv = np.round(np.clip(clv, 1_000, None)).astype(np.int64)

    customer_id = [f"TCB{v:07d}" for v in rng.choice(np.arange(1_000_000, 9_999_999), size=n, replace=False)]

    df = pd.DataFrame({
        'Customer_ID': customer_id,
        'Age': age,
        'Gender': gender,
        'Segment': segment,
        'Avg_Monthly_Balance_VND': avg_balance,
        'Txn_Count_3M': txn_count,
        'Txn_Amount_3M_VND': txn_amount,
        'App_Logins_3M': app_logins,
        'Promo_Txn_Count_3M': promo_txn,
        'Last_Active_Days': last_active,
        'Historical_Promo_Response': response,
        'Estimated_CLV_VND': clv,
    })

    df.to_csv('customer_promo_data.csv', index=False)

    print(f"Da sinh {len(df):,} khach hang -> customer_promo_data.csv")
    print(f"Overall response rate: {df['Historical_Promo_Response'].mean():.2%}")
    print("\nResponse rate theo Segment:")
    print(df.groupby('Segment')['Historical_Promo_Response'].mean().sort_values(ascending=False))
    print(f"\nCorr(Avg_Monthly_Balance_VND, Estimated_CLV_VND) = {df[['Avg_Monthly_Balance_VND', 'Estimated_CLV_VND']].corr().iloc[0, 1]:.4f}")


if __name__ == "__main__":
    main()
