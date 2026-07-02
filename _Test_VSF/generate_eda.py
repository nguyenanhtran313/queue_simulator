import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

df = pd.read_csv(r"c:\_Antigravity\_AG_playground\Test\output\mock_demand.csv")

# 1. Biểu đồ Nhu cầu theo giờ
plt.figure(figsize=(10, 5))
sns.set_theme(style="whitegrid")
hourly_demand = df.groupby('hour')['demand'].mean().reset_index()
sns.barplot(x='hour', y='demand', data=hourly_demand, color='#3498db')
plt.title('Trung bình lượng đặt xe theo Giờ trong ngày (EDA)', fontsize=14, fontweight='bold')
plt.xlabel('Giờ (0-23)')
plt.ylabel('Trung bình cuốc xe')
plt.tight_layout()
plt.savefig(r"c:\_Antigravity\_AG_playground\Test\output\eda_hourly.png", dpi=300)

# 2. Phân phối Nhu cầu cuối tuần vs ngày thường
plt.figure(figsize=(8, 5))
df['is_weekend'] = df['day_of_week'].apply(lambda x: 'Cuối tuần' if x >= 5 else 'Ngày thường')
sns.boxplot(x='is_weekend', y='demand', data=df, palette='Set2')
plt.title('Phân phối Nhu cầu: Ngày thường vs Cuối tuần', fontsize=14, fontweight='bold')
plt.xlabel('')
plt.ylabel('Nhu cầu')
plt.tight_layout()
plt.savefig(r"c:\_Antigravity\_AG_playground\Test\output\eda_weekend.png", dpi=300)
