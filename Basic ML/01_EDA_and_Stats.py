import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

# def main():
print("--- STEP 1: Exploratory Data Analysis & Statistical Tests ---")
# Đọc dữ liệu từ file CSV chứa thông tin khách hàng và lịch sử khuyến mãi
# Giả sử file này được trích xuất ra từ Database CRM của công ty
df = pd.read_csv('customer_promo_data.csv')

# 1. Thông tin cơ bản
# Mục đích: Kiểm tra xem dữ liệu có bị khuyết thiếu (missing/null) không và các thông kê cơ bản (mean, min, max,...)
# Giả sử cột Age có max là 200, ta sẽ biết ngay có outlier/dữ liệu lỗi để xử lý.
print(df.info())
print(df.describe())

# 2. Tỷ lệ phản hồi chung (Overall Response Rate)
# Mục đích: Biết được baseline chiến dịch. Giả sử tỷ lệ chung là 5%, mục tiêu ML là chọn tập KH sao cho tỷ lệ này lên 10-15%.
response_rate = df['Historical_Promo_Response'].mean()
print(f"\nOverall Response Rate: {response_rate:.2%}")

# 3. Kiểm định thống kê (Statistical Tests)
# Mục đích: Tìm xem đặc điểm nào (Tuổi, số dư,...) thực sự có ảnh hưởng đến việc khách hàng phản hồi hay không.
print(f"\n--- Statistical Tests (Target: Historical_Promo_Response) ---")

# T-test cho các biến liên tục (dữ liệu dạng số)
# p-value <5%: Xác suất để sự khác biệt này xảy ra do may mắn hoặc ngẫu nhiên là nhỏ hơn 5%.
# Nếu p-value <5%, ta có quyền tự tin gạt bỏ yếu tố ngẫu nhiên sang một bên. Lúc này, ta kết luận: Kết quả này có ý nghĩa thống kê (Statistically Significant). Nói cách khác, có một mối quan hệ hoặc nguyên nhân thực sự đang diễn ra trong dữ liệu.
# Giả sử p-value < 0.05: Ta kết luận nhóm mua và không mua có sự khác biệt rõ rệt về biến này (VD: thu nhập cao mua nhiều hơn).
num_cols = ['Age', 'Avg_Monthly_Balance_VND', 'Txn_Count_3M', 'Txn_Amount_3M_VND', 'App_Logins_3M', 'Promo_Txn_Count_3M', 'Last_Active_Days']
for col in num_cols:
    group1 = df[df['Historical_Promo_Response'] == 1][col]
    group0 = df[df['Historical_Promo_Response'] == 0][col]
    t_stat, p_val = stats.ttest_ind(group1, group0, equal_var=False)
    print(f"\nT-test for {col}: p-value = {p_val:.4f} (Statistically Significant)" if p_val < 0.05 else f"T-test for {col}: p-value = {p_val:.4f}")
    
# Chi-square cho các biến phân loại (Categorical, VD: Giới tính nam/nữ, Phân khúc A/B)
# Mục đích tương tự T-test nhưng áp dụng cho kiểu biến phân loại. 
# Giả sử p-value < 0.05 cho Gender, nghĩa là Nam và Nữ có tỷ lệ phản hồi khác biệt có ý nghĩa thống kê.
cat_cols = ['Gender', 'Segment']
for col in cat_cols:
    contingency_table = pd.crosstab(df[col], df['Historical_Promo_Response'])
    chi2, p_val, dof, expected = stats.chi2_contingency(contingency_table)
    print(f"Chi-square for {col}: p-value = {p_val:.4f}")

# 4. Correlation Heatmap (Bản đồ nhiệt độ tương quan)
# Mục đích: Tìm các cặp biến tương quan quá mạnh với nhau. 
# Giả sử Txn_Count_3M (số GD) và Txn_Amount_3M (tổng tiền) tương quan 0.95, ta có thể chỉ cần giữ 1 biến để model không bị nhiễu (multicollinearity).
plt.figure(figsize=(10, 8))
# Chọn các cột số để tính tương quan
numeric_df = df[num_cols + ['Historical_Promo_Response', 'Estimated_CLV_VND']]
sns.heatmap(numeric_df.corr(), annot=True, cmap='coolwarm', fmt=".2f")
plt.title('Correlation Matrix')
plt.tight_layout()
plt.savefig('01_correlation_matrix.png')
print("Saved correlation matrix plot to 01_correlation_matrix.png")

# if __name__ == "__main__":
#     main()

# ### 📌 Cách đọc kết quả ở trên (số cụ thể thay đổi mỗi lần chạy lại 00_generate_data.py, nên không hard-code ở đây):
#
# 1. Nhóm biến "vàng" (giữ lại): những biến có T-test/Chi-square p-value < 0.05 VÀ hệ số tương quan
#    rõ rệt với `Historical_Promo_Response` trong 01_correlation_matrix.png.
# 2. Bẫy đa cộng tuyến: nhìn hệ số tương quan giữa `Avg_Monthly_Balance_VND` và `Estimated_CLV_VND` —
#    nếu gần 1.00, bắt buộc loại 1 trong 2 biến trước khi train (khuyên loại `Estimated_CLV_VND`).
# 3. Nhóm biến "nhiễu" (loại bỏ): p-value > 0.05, tương quan với target gần 0 — thường là nhân khẩu học
#    (Age, Gender) và cụm hành vi thông thường (Txn_Count_3M, Txn_Amount_3M_VND, App_Logins_3M, vốn tự
#    tương quan chéo cao với nhau nhưng không liên quan tới việc phản hồi khuyến mãi).
