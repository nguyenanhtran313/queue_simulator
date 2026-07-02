import pandas as pd
import numpy as np
import uuid
from datetime import datetime, timedelta

def generate_real_estate_data(num_records=5000):
    np.random.seed(42)
    
    # 1. ID
    property_ids = [str(uuid.uuid4()) for _ in range(num_records)]
    
    # 2. Basic characteristics
    area_sqm = np.random.normal(70, 20, num_records).clip(30, 200)
    bedrooms = np.where(area_sqm < 50, 1, np.where(area_sqm < 90, 2, np.where(area_sqm < 130, 3, 4)))
    bathrooms = np.where(bedrooms == 1, 1, np.where(bedrooms == 2, np.random.choice([1, 2], num_records, p=[0.3, 0.7]), np.where(bedrooms == 3, 2, 3)))
    
    # 3. Spatial Data
    total_floors = np.random.choice([15, 25, 35, 45], num_records)
    floor_level = [np.random.randint(1, tf + 1) for tf in total_floors]
    orientations = ['Đông', 'Tây', 'Nam', 'Bắc', 'Đông Nam', 'Tây Nam', 'Đông Bắc', 'Tây Bắc']
    orientation = np.random.choice(orientations, num_records)
    
    distance_to_center_km = np.random.exponential(5, num_records).clip(1, 30)
    distance_to_hospital_km = np.random.exponential(2, num_records).clip(0.1, 10)
    distance_to_school_km = np.random.exponential(1.5, num_records).clip(0.1, 5)
    distance_to_supermarket_km = np.random.exponential(1, num_records).clip(0.1, 5)
    
    # 4. Unstructured Data (Represented by extracted features/scores)
    balcony_views = ['View Thành Phố', 'View Hồ', 'View Công Viên', 'Bị Che Khuất', 'View Nội Khu']
    balcony_view_type = np.random.choice(balcony_views, num_records, p=[0.4, 0.1, 0.15, 0.1, 0.25])
    
    image_quality_score = np.random.normal(7, 1.5, num_records).clip(1, 10) # 1-10 scale
    
    living_room_image_url = [f"https://example.com/images/property_{i}_living_room.jpg" for i in range(num_records)]
    balcony_image_url = [f"https://example.com/images/property_{i}_balcony.jpg" for i in range(num_records)]
    
    # 5. Other Industry Features
    building_age_years = np.random.randint(0, 15, num_records)
    furniture_status = np.random.choice(['Cơ bản', 'Đầy đủ', 'Không nội thất', 'Cao cấp'], num_records, p=[0.4, 0.3, 0.2, 0.1])
    legal_status = np.random.choice(['Sổ đỏ', 'Hợp đồng mua bán', 'Đang chờ sổ'], num_records, p=[0.7, 0.2, 0.1])
    
    # 6. Real-time Market Fluctuation
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365*2) # past 2 years
    
    transaction_dates = [start_date + timedelta(days=np.random.randint(0, 730)) for _ in range(num_records)]
    
    # Generate market sentiment based on date (simulated wave)
    days_since_start = np.array([(d - start_date).days for d in transaction_dates])
    # Sinusoidal market wave + some random noise
    market_sentiment_index = 50 + 20 * np.sin(days_since_start / 100) + np.random.normal(0, 5, num_records)
    market_sentiment_index = market_sentiment_index.clip(0, 100)
    
    interest_rate_pct = 7.0 + 2.0 * np.cos(days_since_start / 150) + np.random.normal(0, 0.5, num_records)
    
    # 7. Calculate Price (The target variable)
    # Base price per sqm based on distance to center
    base_price_per_sqm_vnd = 60_000_000 * np.exp(-distance_to_center_km / 10) 
    
    price = base_price_per_sqm_vnd * area_sqm
    
    # Apply multipliers
    
    # Orientation multiplier
    orientation_mult = {
        'Đông Nam': 1.05, 'Nam': 1.02, 'Đông': 1.01,
        'Bắc': 0.98, 'Tây Bắc': 0.95, 'Tây': 0.95,
        'Tây Nam': 0.97, 'Đông Bắc': 0.99
    }
    price *= np.array([orientation_mult[o] for o in orientation])
    
    # Floor multiplier (mid floors usually best)
    floor_mult = []
    for f, tf in zip(floor_level, total_floors):
        if f == 1:
            floor_mult.append(1.05) # Shophouse/Ground
        elif 2 <= f <= 4:
            floor_mult.append(0.95)
        elif 5 <= f <= tf * 0.7:
            floor_mult.append(1.05) # Mid-high floors
        else:
            floor_mult.append(1.0) # Penthouse or high
    price *= np.array(floor_mult)
    
    # View multiplier
    view_mult = {
        'View Hồ': 1.15, 'View Công Viên': 1.08, 'View Thành Phố': 1.03,
        'View Nội Khu': 1.0, 'Bị Che Khuất': 0.9
    }
    price *= np.array([view_mult[v] for v in balcony_view_type])
    
    # Furniture addition
    furn_add = {
        'Cao cấp': 500_000_000, 'Đầy đủ': 200_000_000,
        'Cơ bản': 50_000_000, 'Không nội thất': 0
    }
    price += np.array([furn_add[f] for f in furniture_status])
    
    # Legal multiplier
    legal_mult = {
        'Sổ đỏ': 1.0, 'Hợp đồng mua bán': 0.95, 'Đang chờ sổ': 0.9
    }
    price *= np.array([legal_mult[l] for l in legal_status])
    
    # Age depreciation (1% per year)
    price *= (1 - building_age_years * 0.01)
    
    # Market sentiment (high sentiment -> higher price)
    price *= (1 + (market_sentiment_index - 50) / 200) # ±10% variation based on sentiment
    
    # Add some random noise
    price *= np.random.normal(1.0, 0.05, num_records)
    
    df = pd.DataFrame({
        'property_id': property_ids,
        'transaction_date': [d.strftime('%Y-%m-%d') for d in transaction_dates],
        'area_sqm': np.round(area_sqm, 1),
        'bedrooms': bedrooms,
        'bathrooms': bathrooms,
        'floor_level': floor_level,
        'total_floors': total_floors,
        'orientation': orientation,
        'distance_to_center_km': np.round(distance_to_center_km, 2),
        'distance_to_hospital_km': np.round(distance_to_hospital_km, 2),
        'distance_to_school_km': np.round(distance_to_school_km, 2),
        'distance_to_supermarket_km': np.round(distance_to_supermarket_km, 2),
        'building_age_years': building_age_years,
        'balcony_view_type': balcony_view_type,
        'furniture_status': furniture_status,
        'legal_status': legal_status,
        'image_quality_score': np.round(image_quality_score, 1),
        'living_room_image_url': living_room_image_url,
        'balcony_image_url': balcony_image_url,
        'market_sentiment_index': np.round(market_sentiment_index, 1),
        'interest_rate_pct': np.round(interest_rate_pct, 2),
        'price_vnd': np.round(price, -6) # Round to nearest million
    })
    
    return df

if __name__ == "__main__":
    print("Generating dataset...")
    df = generate_real_estate_data(5000)
    output_path = 'real_estate_valuation_dataset.csv'
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"Successfully generated {len(df)} records.")
    print(f"Saved to: {output_path}")
    print("\nDataset Sample:")
    print(df.head())
