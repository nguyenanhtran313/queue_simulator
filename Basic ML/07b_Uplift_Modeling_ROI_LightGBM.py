import sys
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer

sys.stdout.reconfigure(encoding='utf-8')


def main():
    print("--- STEP 7b: Uplift Modeling for ROI Optimization (S-Learner: LightGBM) ---")
    # Ban song song voi 07_Uplift_Modeling_ROI.py (S-learner XGBoost) — cung ky thuat S-Learner,
    # doi base model sang LightGBM de so sanh xem 2 base learner co dong thuan ve tap Persuadables
    # hay khong, tuong tu cach 04/04b va 05/05b da lam voi classification model.

    # Gia dinh: Nhom Treatment (Duoc can thiep) = Khach hang tung co >= 1 giao dich khuyen mai
    # (Promo_Txn_Count_3M > 0). Nhom Control (Khong can thiep) = Khach chua tung dung khuyen mai
    df = pd.read_csv('customer_promo_data.csv')
    df['Treatment'] = (df['Promo_Txn_Count_3M'] > 0).astype(int)

    y = df['Historical_Promo_Response']
    X = df.drop(columns=['Customer_ID', 'Historical_Promo_Response', 'Estimated_CLV_VND', 'Treatment', 'Promo_Txn_Count_3M'])

    # S-Learner (Single Model): dua bien Treatment (0/1) vao lam 1 feature cua LightGBM.
    X_slearner = X.copy()
    X_slearner['Treatment'] = df['Treatment']

    cat_cols = ['Gender', 'Segment']
    preprocessor = ColumnTransformer([('cat', OneHotEncoder(drop='first'), cat_cols)], remainder='passthrough')

    X_encoded = preprocessor.fit_transform(X_slearner)

    model = LGBMClassifier(random_state=42, verbose=-1)
    model.fit(X_encoded, y)

    # Tinh Uplift Score cho toan bo tap KH (Suc manh cua khuyen mai len quyet dinh cua tung nguoi)
    X_treat_1 = X_slearner.copy()
    X_treat_1['Treatment'] = 1
    prob_treat_1 = model.predict_proba(preprocessor.transform(X_treat_1))[:, 1]

    X_treat_0 = X_slearner.copy()
    X_treat_0['Treatment'] = 0
    prob_treat_0 = model.predict_proba(preprocessor.transform(X_treat_0))[:, 1]

    df['Uplift_Score'] = prob_treat_1 - prob_treat_0

    # Cung gia dinh kinh doanh voi 06/07 — kenh Zalo ZNS, cost=500d/tin gui thanh cong,
    # reward=12.000d = loi nhuan gop neu khach convert (suy tu ty le convert TB 5% va loi nhuan
    # gop sau cung TB 100d/khach hang)
    cost_per_email = 500
    reward_per_response = 12000

    df['Expected_Incremental_Profit'] = (df['Uplift_Score'] * reward_per_response) - cost_per_email
    df['Send_Email_Uplift'] = df['Expected_Incremental_Profit'] > 0

    print(f"Tong so KH nen target theo Uplift (Persuadables): {df['Send_Email_Uplift'].sum()}")
    print("\nTop 5 KH dang gui Promo nhat (Uplift cao nhat):")
    print(df[['Customer_ID', 'Uplift_Score', 'Expected_Incremental_Profit', 'Send_Email_Uplift']].sort_values(by='Uplift_Score', ascending=False).head())

    df[['Customer_ID', 'Uplift_Score', 'Expected_Incremental_Profit', 'Send_Email_Uplift']].to_csv('07b_uplift_decisions.csv', index=False)
    print("\nSaved uplift decisions to 07b_uplift_decisions.csv")


if __name__ == "__main__":
    main()
