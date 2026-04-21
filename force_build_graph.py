import pandas as pd
import numpy as np
import json

df = pd.read_csv('data_user500.csv')
graph_data = { 'nodes': [], 'edges': [] }

for cat in df['category'].unique():
    graph_data['nodes'].append({'id': str(cat), 'type': 'Category'})

products = df[['product_id', 'category']].drop_duplicates()
for _, row in products.iterrows():
    graph_data['nodes'].append({'id': str(row['product_id']), 'type': 'Product', 'category': str(row['category'])})

for _, row in df.iterrows():
    graph_data['edges'].append({
        'from': 'U' + str(row['user_id']),
        'to': str(row['product_id']),
        'type': str(row['action']),
        'weight': float(row['behavior_score'])
    })

def npserializer(obj):
    if isinstance(obj, (np.integer, np.int64)): return int(obj)
    if isinstance(obj, (np.floating, np.float64)): return float(obj)
    return str(obj)

with open('kb_graph_data.json', 'w') as f:
    json.dump(graph_data, f, indent=2, default=npserializer)

print('Saved: kb_graph_data.json')
