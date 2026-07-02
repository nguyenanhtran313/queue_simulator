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



# ### 📌 1. Nhóm Biến "Vàng" (Bắt buộc phải giữ lại)

# Đây là những biến vừa có ý nghĩa thống kê ($p\text{-value} < 0.05$), vừa thể hiện lực tương quan rõ rệt với biến mục tiêu `Historical_Promo_Response`:

# * **`Promo_Txn_Count_3M` ($p = 0.0000$, Tương quan = $0.20$):** Đây là tín hiệu mạnh nhất. Khách hàng càng chăm dùng khuyến mãi trong 3 tháng gần đây thì tỷ lệ họ tiếp tục phản hồi chiến dịch mới càng cao.
# * **`Last_Active_Days` ($p = 0.0000$, Tương quan = $-0.16$):** Mang giá trị tương quan âm. Nghĩa là số ngày rời xa hệ thống càng lớn (khách hàng càng lười hoạt động) thì khả năng họ phản hồi khuyến mãi càng thấp. Mô hình sẽ cần biến này để né các "user chết".
# * **`Avg_Monthly_Balance_VND` ($p = 0.0086$, Tương quan = $0.09$):** Số dư tài khoản trung bình thực sự có ảnh hưởng đến hành vi của khách.
# * **`Segment` ($p = 0.0046$):** Phân khúc khách hàng là yếu tố định tính quan trọng quyết định tỷ lệ tương tác.

# ---

# ### 📌 2. Cảnh báo "Bẫy dữ liệu" (🚨 Nguy hiểm)

# Hãy nhìn kỹ vào ma trận tương quan ở hai biến: **`Avg_Monthly_Balance_VND`** và **`Estimated_CLV_VND`** (Giá trị vòng đời khách hàng dự kiến).

# * Hệ số tương quan giữa 2 biến này là **`1.00`** (màu đỏ đậm). Điều này có nghĩa là chúng chứa thông tin giống hệt nhau $100\%$ (có thể CLV được tính toán trực tiếp từ số dư).
# * **Hành động:** Nếu bạn giữ lại cả 2 biến, mô hình (đặc biệt là Logistic Regression hoặc các mô hình tuyến tính) sẽ bị dính lỗi **Đa cộng tuyến (Multicollinearity)** làm sai lệch kết quả dự đoán. Bạn **bắt buộc phải xóa 1 trong 2 biến này** trước khi train model (khuyên xóa `Estimated_CLV_VND` vì T-test đã chứng minh biến Số dư chạy rất tốt).

# ---

# ### 📌 3. Nhóm Biến "Nhiễu" (Nên mạnh dạn loại bỏ)

# Những biến này có $p\text{-value} > 0.05$ và hệ số tương quan với Target gần như bằng $0$. Chúng không giúp ích gì cho mô hình mà chỉ làm model nặng và dễ bị quá khớp (overfitting):

# * **Nhân khẩu học (`Age` có $p = 0.9842$, `Gender` có $p = 0.1064$):** Tuổi tác và giới tính hoàn toàn không ảnh hưởng đến việc khách hàng có chịu nhận ưu đãi hay không.
# * **Hành vi thông thường (`Txn_Count_3M`, `Txn_Amount_3M_VND`, `App_Logins_3M`):** Khá bất ngờ là việc khách hàng đăng nhập app nhiều hay chuyển tiền nhiều (nói chung) lại không liên quan đến việc họ có thích bấm vào promo hay không. Bản thân các biến này cũng tự tương quan chéo với nhau rất cao ($0.70$ - $0.86$).

# ---

# ### 📌 Chốt hạ danh sách biến cho mô hình của bạn:

# 1. **Biến mục tiêu (Target):** `Historical_Promo_Response`
# 2. **Biến đầu vào (Features) giữ lại:** `Promo_Txn_Count_3M`, `Last_Active_Days`, `Avg_Monthly_Balance_VND`, và `Segment`.
# 3. **Biến loại bỏ:** Tất cả các biến còn lại.

# Bộ khung này sẽ giúp mô hình Machine Learning của bạn vừa nhẹ, vừa học nhanh lại vừa đạt độ chính xác tối ưu nhất!
