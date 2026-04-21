"""
Generate full dataset: 500 users with 8 behavior types
Output: data_user500_full.csv
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)

# Parameters
NUM_USERS = 500
NUM_PRODUCTS = 1000
NUM_RECORDS = 4000
CATEGORIES = ['Electronics', 'Clothing', 'Books', 'Home', 'Fashion', 'Sports', 'Toys', 'Garden', 'Beauty', 'Automotive']
ACTIONS = ['view', 'click', 'add_to_cart', 'purchase', 'search', 'wishlist', 'share', 'review']

# Behavior scores
BEHAVIOR_SCORES = {
    'view': 0.2,
    'click': 0.4,
    'add_to_cart': 0.7,
    'purchase': 1.0,
    'search': 0.3,
    'wishlist': 0.5,
    'share': 0.5,
    'review': 0.6
}

# Generate timestamps (distributed over last 30 days)
base_date = datetime(2024, 3, 22)
dates = [base_date + timedelta(days=random.randint(0, 29), hours=random.randint(0, 23), minutes=random.randint(0, 59)) for _ in range(NUM_RECORDS)]

# Generate data
records = []

for i in range(NUM_RECORDS):
    user_id = random.randint(1, NUM_USERS)
    product_id = random.randint(1, NUM_PRODUCTS)
    action = random.choice(ACTIONS)
    timestamp = dates[i]
    behavior_score = BEHAVIOR_SCORES[action]
    category = random.choice(CATEGORIES)
    session_id = f"sess_{user_id}_{timestamp.strftime('%Y%m%d')}"
    
    records.append({
        'user_id': user_id,
        'product_id': product_id,
        'action': action,
        'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'behavior_score': behavior_score,
        'category': category,
        'session_id': session_id
    })

# Create DataFrame
df = pd.DataFrame(records)

# Sort by timestamp
df = df.sort_values('timestamp').reset_index(drop=True)

# Save to CSV
output_file = 'data_user500.csv'
df.to_csv(output_file, index=False)

# Print statistics
print("="*70)
print("DATASET GENERATION COMPLETED")
print("="*70)
print(f"\n📊 File: {output_file}")
print(f"\n📈 Statistics:")
print(f"   Total Records: {len(df)}")
print(f"   Unique Users: {df['user_id'].nunique()}")
print(f"   Unique Products: {df['product_id'].nunique()}")
print(f"   Categories: {df['category'].nunique()}")
print(f"   Time Range: {df['timestamp'].min()} to {df['timestamp'].max()}")

print(f"\n📋 Action Types:")
for action in ACTIONS:
    count = len(df[df['action'] == action])
    pct = (count / len(df)) * 100
    print(f"   • {action:15} {count:5} ({pct:5.1f}%)")

print(f"\n📂 Category Distribution:")
for cat in sorted(df['category'].unique()):
    count = len(df[df['category'] == cat])
    pct = (count / len(df)) * 100
    print(f"   • {cat:15} {count:5} ({pct:5.1f}%)")

print(f"\n👥 User Activity Distribution:")
user_counts = df['user_id'].value_counts()
print(f"   • Min interactions per user: {user_counts.min()}")
print(f"   • Max interactions per user: {user_counts.max()}")
print(f"   • Avg interactions per user: {user_counts.mean():.1f}")
print(f"   • Median interactions per user: {user_counts.median():.1f}")

print(f"\n✅ First 5 rows:")
print(df.head())

print(f"\n" + "="*70)
