import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

def main():
    print("--- STEP 2: KMeans Customer Segmentation ---")
    # Load dữ liệu khách hàng
    df = pd.read_csv('customer_promo_data.csv')
    
    # Lựa chọn các đặc trưng (features) quan trọng để phân cụm hành vi
    # Mục đích: Ta chỉ muốn nhóm khách hàng dựa trên hành vi giao dịch và tương tác với app.
    # Giả sử bỏ biến Age hay Gender đi vì muốn gom cụm thuần túy theo giá trị tiền bạc và độ tích cực.
    features = ['Promo_Txn_Count_3M', 'Last_Active_Days', 'Avg_Monthly_Balance_VND']
    X = df[features]
    
    # Chuẩn hóa dữ liệu (Standardization)
    # Mục đích: Đưa các thang đo về cùng hệ quy chiếu (mean=0, std=1). 
    # Giả sử không chuẩn hóa, biến Txn_Amount_3M_VND (hàng chục triệu) sẽ hoàn toàn làm lu mờ biến App_Logins_3M (vài chục lần), khiến thuật toán gom cụm sai lệch.
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    # Tìm số cụm K tối ưu bằng Phương pháp Khuỷu tay (Elbow Method) và Silhouette Score
    # Mục đích: Tìm ra số nhóm KH tối ưu. Inertia đo tổng khoảng cách từ các điểm tới tâm cụm, càng nhỏ càng tốt nhưng nếu K lớn quá thì vô nghĩa (mỗi KH 1 cụm).
    # Silhouette Score đo mức độ tương đồng của một điểm với cụm của chính nó so với các cụm khác, điểm càng cao (gần 1) càng tốt.
    inertia = []
    silhouette_scores = []
    K_range = range(2, 8)
    for k in K_range:
        kmeans = KMeans(n_clusters=k, random_state=42)
        labels = kmeans.fit_predict(X_scaled)
        inertia.append(kmeans.inertia_)
        silhouette_scores.append(silhouette_score(X_scaled, labels))
        
    plt.figure(figsize=(14, 5))
    
    plt.subplot(1, 2, 1)
    plt.plot(K_range, inertia, marker='o')
    plt.title('Elbow Method for Optimal K')
    plt.xlabel('Number of clusters')
    plt.ylabel('Inertia')
    
    plt.subplot(1, 2, 2)
    plt.plot(K_range, silhouette_scores, marker='s', color='green')
    plt.title('Silhouette Score for Optimal K')
    plt.xlabel('Number of clusters')
    plt.ylabel('Silhouette Score')
    
    plt.tight_layout()
    plt.savefig('02_kmeans_evaluation.png')
    print("Saved evaluation plots to 02_kmeans_evaluation.png")
    
    # Tìm K tốt nhất dựa trên Silhouette Score
    best_k = K_range[silhouette_scores.index(max(silhouette_scores))]
    print(f"\nBest K based on Silhouette Score: {best_k}")
    
    # Fit model cuối với K tốt nhất
    kmeans = KMeans(n_clusters=best_k, random_state=42)
    df['Cluster'] = kmeans.fit_predict(X_scaled)
    
    print("\nCluster Profiling (Mean values per cluster):")
    # Phân tích xem mỗi cụm có trung bình các chỉ số là bao nhiêu để gán tên gọi cho cụm
    cluster_profile = df.groupby('Cluster')[features].mean()
    print(cluster_profile)
    
    # Lưu kết quả gom cụm ra file mới để có thể dùng cho phân tích hoặc chiến dịch marketing cụ thể
    df.to_csv('customer_promo_data_clustered.csv', index=False)
    print("Saved clustered data to customer_promo_data_clustered.csv")

if __name__ == "__main__":
    main()
