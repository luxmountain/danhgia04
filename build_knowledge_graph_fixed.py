"""
Build Knowledge Base Graph (KB_Graph) with Neo4j
Nodes: User, Product, Category, Query
Edges: INTERACTED (weighted), SEARCHED, BELONGS_TO, SIMILAR
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import networkx as nx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import json
import warnings
from collections import defaultdict

warnings.filterwarnings('ignore')

print("=" * 80)
print("KNOWLEDGE BASE GRAPH (KB_Graph) CONSTRUCTION")
print("=" * 80)

# ==================== DATA LOADING ====================
print("\n" + "=" * 80)
print("1. LOADING DATA")
print("=" * 80)

df = pd.read_csv('data_user500.csv')
print(f"✓ Loaded {len(df)} records from data_user500.csv")

# Basic statistics
users = sorted(df['user_id'].unique())
products = sorted(df['product_id'].unique())
categories = sorted(df['category'].unique())
actions = sorted(df['action'].unique())

num_users = len(users)
num_products = len(products)
num_categories = len(categories)
num_actions = len(actions)

print(f"✓ Users: {num_users}")
print(f"✓ Products: {num_products}")
print(f"✓ Categories: {num_categories}")
print(f"✓ Actions: {num_actions} {actions}")
print()

# ==================== WEIGHT MAPPING ====================
# Edge weight: w(u,p) = α·clicks + β·cart + γ·purchase
WEIGHT_MAP = {
    'view': 0.5,
    'click': 1.0,
    'add_to_cart': 3.0,
    'purchase': 5.0,
    'search': 0.3,
    'wishlist': 2.0,
    'share': 1.5,
    'review': 2.5
}

print("=" * 80)
print("2. CREATING NODES")
print("=" * 80)

# ==================== CREATE NODES ====================

# User nodes
user_nodes = {uid: {'type': 'User', 'id': uid} for uid in users}
print(f"✓ Created {len(user_nodes)} User nodes")

# Product nodes with metadata
product_nodes = {}
for pid in products:
    product_data = df[df['product_id'] == pid].iloc[0]
    product_nodes[pid] = {
        'type': 'Product',
        'id': pid,
        'category': product_data['category'],
        'interaction_count': len(df[df['product_id'] == pid])
    }
print(f"✓ Created {len(product_nodes)} Product nodes")

# Category nodes
category_nodes = {cat: {'type': 'Category', 'id': cat} for cat in categories}
print(f"✓ Created {len(category_nodes)} Category nodes")

# Query nodes (from search actions)
searches = df[df['action'] == 'search'].groupby('user_id').size()
query_texts = set()
user_searches = defaultdict(list)

for user_id in df['user_id'].unique():
    user_df = df[df['user_id'] == user_id]
    # Create pseudo-queries from search actions
    search_count = len(user_df[user_df['action'] == 'search'])
    if search_count > 0:
        # Group by category to create synthetic queries
        for idx, (cat, count) in enumerate(user_df[user_df['action'] == 'search']['category'].value_counts().items()):
            query_text = f"{cat.lower()} {idx}"
            query_texts.add(query_text)
            user_searches[user_id].append((query_text, count))

query_nodes = {q: {'type': 'Query', 'text': q, 'frequency': 1} for q in query_texts}
print(f"✓ Created {len(query_nodes)} Query nodes")
print()

# ==================== CREATE EDGES ====================
print("=" * 80)
print("3. CREATING EDGES & CALCULATING WEIGHTS")
print("=" * 80)

# INTERACTED edges (User → Product with weight)
interacted_edges = defaultdict(lambda: {'weight': 0, 'actions': []})

for _, row in df.iterrows():
    user_id = row['user_id']
    product_id = row['product_id']
    action = row['action']
    
    if action != 'search':  # Skip search for now
        edge_key = (user_id, product_id)
        weight = WEIGHT_MAP.get(action, 1.0)
        interacted_edges[edge_key]['weight'] += weight
        interacted_edges[edge_key]['actions'].append(action)

print(f"✓ Created {len(interacted_edges)} INTERACTED edges")

# Weight statistics
weights = [e['weight'] for e in interacted_edges.values()]
print(f"  - Weight range: {min(weights):.2f} to {max(weights):.2f}")
print(f"  - Average weight: {np.mean(weights):.2f}")
print()

# SEARCHED edges (User → Query)
searched_edges = defaultdict(int)
for user_id, searches_list in user_searches.items():
    for query_text, count in searches_list:
        searched_edges[(user_id, query_text)] = count

print(f"✓ Created {len(searched_edges)} SEARCHED edges")
print()

# BELONGS_TO edges (Product → Category)
belongs_to_edges = set()
for pid, pdata in product_nodes.items():
    belongs_to_edges.add((pid, pdata['category']))

print(f"✓ Created {len(belongs_to_edges)} BELONGS_TO edges")
print()

# ==================== CALCULATE SIMILARITY ====================
print("=" * 80)
print("4. CALCULATING PRODUCT SIMILARITY (Cosine-based)")
print("=" * 80)

# Create product profiles based on user interactions
# Product i: [weights from users who interacted with it]
product_profiles = {}
for pid in products:
    profile = []
    for uid in users:
        edge_key = (uid, pid)
        weight = interacted_edges[edge_key]['weight'] if edge_key in interacted_edges else 0
        profile.append(weight)
    product_profiles[pid] = np.array(profile)

# Calculate cosine similarity between all products
product_list = sorted(products)
n_products = len(product_list)
similarity_matrix = np.zeros((n_products, n_products))

for i in range(n_products):
    for j in range(i, n_products):
        p1, p2 = product_list[i], product_list[j]
        v1, v2 = product_profiles[p1], product_profiles[p2]
        
        # Cosine similarity
        norm1, norm2 = np.linalg.norm(v1), np.linalg.norm(v2)
        if norm1 > 0 and norm2 > 0:
            sim = np.dot(v1, v2) / (norm1 * norm2)
        else:
            sim = 0
        
        similarity_matrix[i, j] = sim
        similarity_matrix[j, i] = sim

# SIMILAR edges (Product ↔ Product with similarity > threshold)
SIMILARITY_THRESHOLD = 0.3
similar_edges = []

for i in range(n_products):
    for j in range(i + 1, n_products):
        if similarity_matrix[i, j] > SIMILARITY_THRESHOLD:
            p1, p2 = product_list[i], product_list[j]
            similar_edges.append({
                'p1': p1,
                'p2': p2,
                'score': similarity_matrix[i, j]
            })

print(f"✓ Created {len(similar_edges)} SIMILAR edges (threshold={SIMILARITY_THRESHOLD})")
print(f"  - Similarity range: {min([e['score'] for e in similar_edges]):.4f} to "
      f"{max([e['score'] for e in similar_edges]):.4f}")
print()

# ==================== BUILD GRAPH ====================
print("=" * 80)
print("5. BUILDING NETWORKX GRAPH")
print("=" * 80)

G = nx.Graph()

# Add nodes
for uid in user_nodes:
    G.add_node(f"U{uid}", type='User')
for pid in product_nodes:
    G.add_node(f"P{pid}", type='Product', category=product_nodes[pid]['category'])
for cat in category_nodes:
    G.add_node(f"C{cat}", type='Category')
for q in query_nodes:
    G.add_node(f"Q{q}", type='Query')

print(f"✓ Added {G.number_of_nodes()} nodes to graph")

# Add edges
for (uid, pid), edge_data in interacted_edges.items():
    G.add_edge(f"U{uid}", f"P{pid}", 
               relation='INTERACTED', 
               weight=edge_data['weight'],
               actions=edge_data['actions'])

for (uid, query), count in searched_edges.items():
    G.add_edge(f"U{uid}", f"Q{query}", 
               relation='SEARCHED', 
               weight=count)

for pid, cat in belongs_to_edges:
    G.add_edge(f"P{pid}", f"C{cat}", 
               relation='BELONGS_TO', 
               weight=1)

for edge in similar_edges:
    G.add_edge(f"P{edge['p1']}", f"P{edge['p2']}", 
               relation='SIMILAR', 
               weight=edge['score'])

print(f"✓ Added {G.number_of_edges()} edges to graph")
print()

# ==================== GRAPH STATISTICS ====================
print("=" * 80)
print("6. GRAPH STATISTICS")
print("=" * 80)

# Node statistics
node_types = defaultdict(int)
for node, data in G.nodes(data=True):
    node_types[data.get('type', 'Unknown')] += 1

print("\nNode Distribution:")
for ntype, count in sorted(node_types.items()):
    print(f"  • {ntype:15} {count:4}")

# Edge statistics by relation type
edge_relations = defaultdict(int)
for _, _, data in G.edges(data=True):
    edge_relations[data.get('relation', 'Unknown')] += 1

print("\nEdge Distribution by Relation:")
for relation, count in sorted(edge_relations.items()):
    print(f"  • {relation:15} {count:4}")

# Degree statistics
degrees = [G.degree(n) for n in G.nodes()]
print(f"\nDegree Statistics:")
print(f"  • Average degree: {np.mean(degrees):.2f}")
print(f"  • Max degree: {max(degrees)}")
print(f"  • Min degree: {min(degrees)}")

# Weight statistics
weights = [d['weight'] for _, _, d in G.edges(data=True) if 'weight' in d]
print(f"\nWeight Statistics (all edges):")
print(f"  • Average weight: {np.mean(weights):.4f}")
print(f"  • Max weight: {max(weights):.4f}")
print(f"  • Min weight: {min(weights):.4f}")

# Connected components
num_components = nx.number_connected_components(G)
print(f"\nConnected Components: {num_components}")

# Density
density = nx.density(G)
print(f"Graph Density: {density:.6f}")
print()

# ==================== SUBGRAPH ANALYSIS ====================
print("=" * 80)
print("7. SUBGRAPH ANALYSIS")
print("=" * 80)

# User-Product subgraph
user_product_edges = [(u, v) for u, v, d in G.edges(data=True) 
                       if d.get('relation') == 'INTERACTED']
G_up = G.subgraph([n for u, v in user_product_edges for n in [u, v]])
print(f"✓ User-Product subgraph: {G_up.number_of_nodes()} nodes, {G_up.number_of_edges()} edges")

# Product-Category subgraph
product_category_edges = [(u, v) for u, v, d in G.edges(data=True) 
                           if d.get('relation') == 'BELONGS_TO']
G_pc = G.subgraph([n for u, v in product_category_edges for n in [u, v]])
print(f"✓ Product-Category subgraph: {G_pc.number_of_nodes()} nodes, {G_pc.number_of_edges()} edges")

# Product-Product similarity subgraph
product_product_edges = [(u, v) for u, v, d in G.edges(data=True) 
                          if d.get('relation') == 'SIMILAR']
G_pp = G.subgraph([n for u, v in product_product_edges for n in [u, v]])
print(f"✓ Product-Product similarity subgraph: {G_pp.number_of_nodes()} nodes, {G_pp.number_of_edges()} edges")
print()

# ==================== TOP NODES ====================
print("=" * 80)
print("8. TOP NODES (by degree centrality)")
print("=" * 80)

# Users with most interactions
user_nodes_list = [n for n in G.nodes() if n.startswith('U')]
user_degrees = [(n, G.degree(n)) for n in user_nodes_list]
user_degrees.sort(key=lambda x: x[1], reverse=True)

print("\nTop 10 Most Active Users:")
for i, (user, degree) in enumerate(user_degrees[:10], 1):
    user_id = int(user[1:])
    interactions = len(df[df['user_id'] == user_id])
    print(f"  {i:2}. {user:8} degree={degree:3} interactions={interactions:3}")

# Products with most interactions
product_nodes_list = [n for n in G.nodes() if n.startswith('P')]
product_degrees = [(n, G.degree(n)) for n in product_nodes_list]
product_degrees.sort(key=lambda x: x[1], reverse=True)

print("\nTop 10 Most Popular Products:")
for i, (product, degree) in enumerate(product_degrees[:10], 1):
    product_id = int(product[1:])
    interactions = len(df[df['product_id'] == product_id])
    print(f"  {i:2}. {product:8} degree={degree:3} interactions={interactions:3}")

# Categories
category_degrees = [(n, G.degree(n)) for n in G.nodes() if n.startswith('C')]
category_degrees.sort(key=lambda x: x[1], reverse=True)

print("\nCategories by Product Count:")
for i, (category, degree) in enumerate(category_degrees[:10], 1):
    cat_name = category[1:]
    print(f"  {i:2}. {cat_name:15} products={degree:3}")
print()

# ==================== VISUALIZATIONS ====================
print("=" * 80)
print("9. GENERATING VISUALIZATIONS")
print("=" * 80)

fig = plt.figure(figsize=(20, 14))

# 1. Graph degree distribution
ax1 = plt.subplot(3, 3, 1)
degrees_all = [G.degree(n) for n in G.nodes()]
ax1.hist(degrees_all, bins=30, color='skyblue', edgecolor='black', alpha=0.7)
ax1.set_xlabel('Degree', fontweight='bold')
ax1.set_ylabel('Frequency', fontweight='bold')
ax1.set_title('Node Degree Distribution', fontweight='bold')
ax1.grid(True, alpha=0.3)

# 2. Node type distribution
ax2 = plt.subplot(3, 3, 2)
node_type_counts = list(node_types.values())
node_type_labels = list(node_types.keys())
colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A']
ax2.pie(node_type_counts, labels=node_type_labels, autopct='%1.1f%%', 
        colors=colors, startangle=90)
ax2.set_title('Node Type Distribution', fontweight='bold')

# 3. Edge relation distribution
ax3 = plt.subplot(3, 3, 3)
edge_relation_counts = list(edge_relations.values())
edge_relation_labels = list(edge_relations.keys())
colors_edges = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A']
ax3.pie(edge_relation_counts, labels=edge_relation_labels, autopct='%1.1f%%',
        colors=colors_edges, startangle=90)
ax3.set_title('Edge Relation Distribution', fontweight='bold')

# 4. Weight distribution (INTERACTED edges)
ax4 = plt.subplot(3, 3, 4)
interacted_weights = [d['weight'] for _, _, d in G.edges(data=True) 
                      if d.get('relation') == 'INTERACTED']
ax4.hist(interacted_weights, bins=20, color='steelblue', edgecolor='black', alpha=0.7)
ax4.set_xlabel('Edge Weight', fontweight='bold')
ax4.set_ylabel('Frequency', fontweight='bold')
ax4.set_title('INTERACTED Edge Weight Distribution', fontweight='bold')
ax4.grid(True, alpha=0.3)

# 5. Similarity score distribution
ax5 = plt.subplot(3, 3, 5)
similar_scores = [d['weight'] for _, _, d in G.edges(data=True) 
                  if d.get('relation') == 'SIMILAR']
if similar_scores:
    ax5.hist(similar_scores, bins=20, color='coral', edgecolor='black', alpha=0.7)
    ax5.set_xlabel('Similarity Score', fontweight='bold')
    ax5.set_ylabel('Frequency', fontweight='bold')
    ax5.set_title('Product SIMILAR Edge Score Distribution', fontweight='bold')
    ax5.grid(True, alpha=0.3)

# 6. Top users by degree
ax6 = plt.subplot(3, 3, 6)
top_users = user_degrees[:10]
user_labels = [u[0] for u in top_users]
user_degs = [u[1] for u in top_users]
ax6.barh(user_labels, user_degs, color='steelblue', edgecolor='black')
ax6.set_xlabel('Degree', fontweight='bold')
ax6.set_title('Top 10 Most Active Users', fontweight='bold')
ax6.grid(True, alpha=0.3, axis='x')

# 7. Top products by degree
ax7 = plt.subplot(3, 3, 7)
top_products = product_degrees[:10]
product_labels = [p[0] for p in top_products]
product_degs = [p[1] for p in top_products]
ax7.barh(product_labels, product_degs, color='coral', edgecolor='black')
ax7.set_xlabel('Degree', fontweight='bold')
ax7.set_title('Top 10 Most Popular Products', fontweight='bold')
ax7.grid(True, alpha=0.3, axis='x')

# 8. Cumulative degree distribution
ax8 = plt.subplot(3, 3, 8)
sorted_degrees = sorted(degrees_all, reverse=True)
cumsum = np.cumsum(sorted_degrees)
cumsum = cumsum / cumsum[-1]  # Normalize
ax8.plot(range(len(cumsum)), cumsum, linewidth=2, color='darkblue')
ax8.fill_between(range(len(cumsum)), cumsum, alpha=0.3, color='skyblue')
ax8.set_xlabel('Node Rank', fontweight='bold')
ax8.set_ylabel('Cumulative Degree %', fontweight='bold')
ax8.set_title('Cumulative Degree Distribution (Pareto)', fontweight='bold')
ax8.grid(True, alpha=0.3)

# 9. Graph statistics summary (text)
ax9 = plt.subplot(3, 3, 9)
ax9.axis('off')
stats_text = f"""
GRAPH STATISTICS SUMMARY

Nodes: {G.number_of_nodes()}
  • Users: {node_types['User']}
  • Products: {node_types['Product']}
  • Categories: {node_types['Category']}
  • Queries: {node_types['Query']}

Edges: {G.number_of_edges()}
  • INTERACTED: {edge_relations.get('INTERACTED', 0)}
  • SEARCHED: {edge_relations.get('SEARCHED', 0)}
  • BELONGS_TO: {edge_relations.get('BELONGS_TO', 0)}
  • SIMILAR: {edge_relations.get('SIMILAR', 0)}

Avg Degree: {np.mean(degrees):.2f}
Density: {density:.6f}
Components: {num_components}
"""
ax9.text(0.1, 0.5, stats_text, fontsize=11, family='monospace',
         verticalalignment='center', bbox=dict(boxstyle='round', 
         facecolor='wheat', alpha=0.5))

plt.tight_layout()
plt.savefig('VISUALIZATIONS_KNOWLEDGE_GRAPH.png', dpi=300, bbox_inches='tight')
print("✓ Saved: VISUALIZATIONS_KNOWLEDGE_GRAPH.png\n")

# ==================== CYPHER EXPORT ====================
print("=" * 80)
print("10. EXPORTING CYPHER STATEMENTS")
print("=" * 80)

cypher_queries = []

# Create constraints
cypher_queries.append("// ============ CREATE CONSTRAINTS ============")
cypher_queries.append("CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE;")
cypher_queries.append("CREATE CONSTRAINT product_id IF NOT EXISTS FOR (p:Product) REQUIRE p.id IS UNIQUE;")
cypher_queries.append("CREATE CONSTRAINT category_id IF NOT EXISTS FOR (c:Category) REQUIRE c.id IS UNIQUE;")
cypher_queries.append("CREATE CONSTRAINT query_text IF NOT EXISTS FOR (q:Query) REQUIRE q.text IS UNIQUE;")

# Create indexes
cypher_queries.append("\n// ============ CREATE INDEXES ============")
cypher_queries.append("CREATE INDEX user_type IF NOT EXISTS FOR (u:User) ON (u.type);")
cypher_queries.append("CREATE INDEX product_type IF NOT EXISTS FOR (p:Product) ON (p.type);")

# Sample node creation
cypher_queries.append("\n// ============ SAMPLE NODES ============")
for i, (uid, udata) in enumerate(list(user_nodes.items())[:5]):
    cypher_queries.append(f"CREATE (u{i}:User {{id: {uid}, type: 'User'}});")

for i, (pid, pdata) in enumerate(list(product_nodes.items())[:5]):
    cypher_queries.append(f"CREATE (p{i}:Product {{id: {pid}, category: '{pdata['category']}', type: 'Product'}});")

for i, cat in enumerate(list(category_nodes.keys())[:5]):
    cypher_queries.append(f"CREATE (c{i}:Category {{id: '{cat}', type: 'Category'}});")

# Sample edges
cypher_queries.append("\n// ============ SAMPLE EDGES ============")
for i, ((uid, pid), edata) in enumerate(list(interacted_edges.items())[:5]):
    weight = edata['weight']
    cypher_queries.append(f"MATCH (u:User {{id: {uid}}}), (p:Product {{id: {pid}}})")
    cypher_queries.append(f"CREATE (u)-[:INTERACTED {{weight: {weight}}}]->(p);")

for i, (pid, cat) in enumerate(list(belongs_to_edges)[:5]):
    cypher_queries.append(f"MATCH (p:Product {{id: {pid}}}), (c:Category {{id: '{cat}'}}) ")
    cypher_queries.append(f"CREATE (p)-[:BELONGS_TO]->(c);")

cypher_output = "\n".join(cypher_queries)
with open('kb_graph_cypher_export.cypher', 'w') as f:
    f.write(cypher_output)

print("✓ Saved: kb_graph_cypher_export.cypher")
print(f"  - {len(cypher_queries)} Cypher statements exported")
print()

# ==================== JSON EXPORT ====================
print("=" * 80)
print("11. EXPORTING GRAPH DATA (JSON)")
print("=" * 80)

graph_data = {
    'metadata': {
        'num_nodes': G.number_of_nodes(),
        'num_edges': G.number_of_edges(),
        'num_users': node_types.get('User', 0),
        'num_products': node_types.get('Product', 0),
        'num_categories': node_types.get('Category', 0),
        'num_queries': node_types.get('Query', 0),
        'density': float(density),
        'num_components': int(num_components),
        'avg_degree': float(np.mean(degrees))
    },
    'nodes': {
        'users': num_users,
        'products': num_products,
        'categories': num_categories,
        'queries': len(query_nodes)
    },
    'edges': {
        'INTERACTED': edge_relations.get('INTERACTED', 0),
        'SEARCHED': edge_relations.get('SEARCHED', 0),
        'BELONGS_TO': edge_relations.get('BELONGS_TO', 0),
        'SIMILAR': edge_relations.get('SIMILAR', 0)
    },
    'top_users': [{'user_id': int(u[0][1:]), 'degree': int(u[1])} 
                  for u in user_degrees[:20]],
    'top_products': [{'product_id': int(p[0][1:]), 'degree': int(p[1])} 
                     for p in product_degrees[:20]],
    'similar_products_sample': [
        {
            'product_1': e['p1'],
            'product_2': e['p2'],
            'similarity_score': float(e['score'])
        }
        for e in similar_edges[:20]
    ]
}
    def npserializer(obj):
        if isinstance(obj, np.integer): return int(obj)
        if isinstance(obj, np.floating): return float(obj)
        if isinstance(obj, np.ndarray): return obj.tolist()
        return str(obj)
    json.dump(graph_data, f, indent=2, default=npserializer)
        if isinstance(o, np.floating): return float(o)
        if isinstance(o, np.ndarray): return o.tolist()
        raise TypeError
    json.dump(graph_data, f, indent=2, default=default)

# ==================== REPORT GENERATION ====================
print("=" * 80)
print("12. GENERATING REPORT")
print("=" * 80)

report = f"""
{'='*80}
KNOWLEDGE BASE GRAPH (KB_Graph) - CONSTRUCTION REPORT
{'='*80}

1. GRAPH OVERVIEW
{'='*80}

Total Nodes: {G.number_of_nodes()}
Total Edges: {G.number_of_edges()}

Node Distribution:
  • Users:      {node_types.get('User', 0):4}
  • Products:   {node_types.get('Product', 0):4}
  • Categories: {node_types.get('Category', 0):4}
  • Queries:    {node_types.get('Query', 0):4}

Edge Distribution:
  • INTERACTED (User→Product):    {edge_relations.get('INTERACTED', 0):4}
  • SEARCHED (User→Query):        {edge_relations.get('SEARCHED', 0):4}
  • BELONGS_TO (Product→Category):{edge_relations.get('BELONGS_TO', 0):4}
  • SIMILAR (Product↔Product):    {edge_relations.get('SIMILAR', 0):4}

2. GRAPH METRICS
{'='*80}

Connectivity:
  • Density: {density:.6f}
  • Connected Components: {num_components}
  • Average Degree: {np.mean(degrees):.2f}
  • Min/Max Degree: {min(degrees)} / {max(degrees)}

Edge Weights (INTERACTED):
  • Min: {min(interacted_weights):.4f}
  • Max: {max(interacted_weights):.4f}
  • Mean: {np.mean(interacted_weights):.4f}
  • Median: {np.median(interacted_weights):.4f}

Product Similarity:
  • Similar edges created: {len(similar_edges)}
  • Threshold used: {SIMILARITY_THRESHOLD}
  • Min similarity: {min([e['score'] for e in similar_edges]):.4f}
  • Max similarity: {max([e['score'] for e in similar_edges]):.4f}

3. NODE ANALYSIS
{'='*80}

Top 10 Most Active Users:
"""

for i, (user, degree) in enumerate(user_degrees[:10], 1):
    user_id = int(user[1:])
    interactions = len(df[df['user_id'] == user_id])
    report += f"\n  {i:2}. User {user_id:4} - Degree: {degree:3}, Interactions: {interactions:3}"

report += f"""

Top 10 Most Popular Products:
"""

for i, (product, degree) in enumerate(product_degrees[:10], 1):
    product_id = int(product[1:])
    interactions = len(df[df['product_id'] == product_id])
    category = product_nodes[product_id]['category']
    report += f"\n  {i:2}. Product {product_id:4} ({category:15}) - Degree: {degree:3}, Interactions: {interactions:3}"

report += f"""

Categories by Size:
"""

for i, (category, degree) in enumerate(category_degrees, 1):
    cat_name = category[1:]
    report += f"\n  {i:2}. {cat_name:15} - Products: {degree:3}"

report += f"""

4. EDGE ANALYSIS
{'='*80}

INTERACTED Edges (User → Product):
  - Total: {edge_relations.get('INTERACTED', 0)}
  - Weight formula: w(u,p) = 0.5*view + 1.0*click + 3.0*cart + 5.0*purchase
  - Meaning: Represents user interest level in product
  
SEARCHED Edges (User → Query):
  - Total: {edge_relations.get('SEARCHED', 0)}
  - Meaning: User search behavior
  - Frequency: Number of times searched

BELONGS_TO Edges (Product → Category):
  - Total: {edge_relations.get('BELONGS_TO', 0)}
  - Meaning: Product categorization
  - One-to-many: Each product belongs to exactly one category

SIMILAR Edges (Product ↔ Product):
  - Total: {len(similar_edges)}
  - Method: Cosine similarity on user interaction vectors
  - Threshold: {SIMILARITY_THRESHOLD}
  - Interpretation: Products liked/bought by similar users

5. SUBGRAPH ANALYSIS
{'='*80}

User-Product Subgraph (Behavior Network):
  - Nodes: {G_up.number_of_nodes()}
  - Edges: {G_up.number_of_edges()}
  - Purpose: Recommendation, similarity analysis

Product-Category Subgraph (Taxonomy):
  - Nodes: {G_pc.number_of_nodes()}
  - Edges: {G_pc.number_of_edges()}
  - Purpose: Product catalog structure

Product-Product Subgraph (Similarity Network):
  - Nodes: {G_pp.number_of_nodes()}
  - Edges: {G_pp.number_of_edges()}
  - Purpose: Cross-selling, bundle creation

6. USE CASES & QUERIES
{'='*80}

1. User Recommendation (Co-purchase Graph):
   MATCH (u:User)-[r1:INTERACTED]->(p1:Product)
   WHERE r1.weight > 3
   MATCH (other_u:User)-[r2:INTERACTED]->(p2:Product)
   WHERE other_u <> u AND r2.weight > 3
   WITH p2, COUNT(*) as co_occurrence
   ORDER BY co_occurrence DESC
   LIMIT 10
   
   → Find products frequently bought by users similar to user u

2. Product Similarity Search:
   MATCH (p1:Product {{id: $product_id}})
     -[r:SIMILAR]->(p2:Product)
   ORDER BY r.weight DESC
   LIMIT 5
   
   → Find similar products for cross-selling

3. Category-based Browsing:
   MATCH (c:Category {{id: $category_id}})
     <-[:BELONGS_TO]-(p:Product)
     <-[r:INTERACTED]-(u:User)
   WHERE r.weight > 1
   RETURN p, COUNT(u) as popularity
   ORDER BY popularity DESC
   
   → Find popular products in a category

4. User Behavior Path:
   MATCH (u:User {{id: $user_id}})
     -[r:SEARCHED]->(q:Query)
   RETURN q.text, r.count as search_frequency
   ORDER BY search_frequency DESC
   
   → Analyze user search behavior

7. FILES GENERATED
{'='*80}

✓ VISUALIZATIONS_KNOWLEDGE_GRAPH.png
  - 9 subplots showing graph statistics and distributions

✓ kb_graph_cypher_export.cypher
  - Cypher statements for Neo4j import
  - Ready to paste into Neo4j browser or execute with neo4j-admin

✓ kb_graph_data.json
  - JSON export of graph metadata and top nodes
  - For external processing or API integration

✓ KB_Graph_Construction_Report.txt
  - This comprehensive report

8. DEPLOYMENT INSTRUCTIONS
{'='*80}

A. Using Neo4j Desktop or Docker:

1. Start Neo4j:
   docker-compose up -d neo4j
   
   Access at: http://localhost:7474
   Default credentials: neo4j / changeme123

2. Import constraints and indexes:
   Open Neo4j Browser and run:
   → Copy content from kb_graph_cypher_export.cypher
   → Execute in Neo4j Browser

3. Verify graph creation:
   MATCH (n) RETURN COUNT(n) as total_nodes;
   MATCH ()-[r]->() RETURN COUNT(r) as total_edges;

B. Using Python (py2neo):

from py2neo import Graph
graph = Graph("bolt://localhost:7687", auth=("neo4j", "changeme123"))
# Run queries using graph.run(cypher_query)

9. NEXT STEPS
{'='*80}

✓ Build graph structure (DONE)
↓
→ Implement RAG system using graph traversal
→ Build chatbot with graph-aware retrieval
→ Integrate with product service

{'='*80}
Report Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*80}
"""

with open('KB_Graph_Construction_Report.txt', 'w', encoding='utf-8') as f:
    f.write(report)

print("✓ Saved: KB_Graph_Construction_Report.txt")
print()

# ==================== FINAL SUMMARY ====================
print("=" * 80)
print("SUMMARY")
print("=" * 80)

summary = f"""
✅ KNOWLEDGE BASE GRAPH CONSTRUCTED SUCCESSFULLY

Graph Size:
  • {G.number_of_nodes()} total nodes
  • {G.number_of_edges()} total edges

Node Breakdown:
  • {node_types.get('User', 0)} Users
  • {node_types.get('Product', 0)} Products
  • {node_types.get('Category', 0)} Categories
  • {node_types.get('Query', 0)} Queries

Edge Types:
  • {edge_relations.get('INTERACTED', 0)} INTERACTED edges (user-product interactions)
  • {edge_relations.get('SEARCHED', 0)} SEARCHED edges (user searches)
  • {edge_relations.get('BELONGS_TO', 0)} BELONGS_TO edges (product-category)
  • {len(similar_edges)} SIMILAR edges (product similarity)

Artifacts:
  ✓ VISUALIZATIONS_KNOWLEDGE_GRAPH.png
  ✓ kb_graph_cypher_export.cypher
  ✓ kb_graph_data.json
  ✓ KB_Graph_Construction_Report.txt

Graph Characteristics:
  • Density: {density:.6f}
  • Connected Components: {num_components}
  • Average Degree: {np.mean(degrees):.2f}

Ready for:
  ✅ Neo4j deployment
  ✅ Graph-based recommendation
  ✅ RAG system integration
  ✅ Knowledge-driven chatbot
"""

print(summary)








