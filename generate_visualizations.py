"""
Visualization Script for AI-Service Report
Generate graphs, charts, and diagrams for documentation
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import seaborn as sns
import networkx as nx
from datetime import datetime, timedelta

# Style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 8)
plt.rcParams['font.size'] = 10

# ============================================================================
# 1. INTERACTION DISTRIBUTION (20 ROWS DATA)
# ============================================================================

def plot_interaction_distribution():
    """Plot interaction types distribution"""
    data = {
        'user_id': [1, 1, 1, 2, 2, 3, 3, 3, 4, 4, 4, 5, 5, 5, 6, 6, 6, 7, 7, 8],
        'event_type': ['view', 'click', 'cart', 'view', 'wishlist', 'search', 'view', 'click',
                       'view', 'cart', 'purchase', 'view', 'click', 'share', 'search', 'view', 'review',
                       'view', 'wishlist', 'click']
    }
    
    df = pd.DataFrame(data)
    event_counts = df['event_type'].value_counts()
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Bar chart
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E2']
    ax1.bar(event_counts.index, event_counts.values, color=colors[:len(event_counts)])
    ax1.set_xlabel('Event Type', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Count', fontsize=12, fontweight='bold')
    ax1.set_title('Distribution of 20 Interaction Records', fontsize=14, fontweight='bold')
    ax1.grid(axis='y', alpha=0.3)
    
    # Pie chart
    ax2.pie(event_counts.values, labels=event_counts.index, autopct='%1.1f%%', 
            colors=colors[:len(event_counts)], startangle=90)
    ax2.set_title('Percentage Distribution', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('VISUALIZATIONS_1_INTERACTION_DISTRIBUTION.png', dpi=300, bbox_inches='tight')
    print("✓ Saved: VISUALIZATIONS_1_INTERACTION_DISTRIBUTION.png")
    plt.close()

# ============================================================================
# 2. USER BEHAVIOR FUNNEL
# ============================================================================

def plot_conversion_funnel():
    """Plot conversion funnel"""
    stages = ['View', 'Click', 'Add to Cart', 'Purchase']
    counts = [100, 50, 20, 8]  # Funnel conversion
    percentages = [100, 50, 20, 8]
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    colors_funnel = ['#FF6B6B', '#FFA500', '#FFD700', '#90EE90']
    
    # Draw funnel
    for i, (stage, count, pct, color) in enumerate(zip(stages, counts, percentages, colors_funnel)):
        width = 0.8 * (100 - i*15) / 100
        y_pos = 3 - i
        
        # Rectangle
        rect = FancyBboxPatch((0.5-width/2, y_pos-0.35), width, 0.7,
                             boxstyle="round,pad=0.05", 
                             edgecolor='black', facecolor=color, linewidth=2)
        ax.add_patch(rect)
        
        # Text
        ax.text(0.5, y_pos, f'{stage}\n{count} users ({pct}%)',
               ha='center', va='center', fontsize=12, fontweight='bold')
        
        # Arrow
        if i < len(stages) - 1:
            arrow = FancyArrowPatch((0.5, y_pos-0.4), (0.5, y_pos-0.9),
                                  arrowstyle='->', mutation_scale=30, linewidth=2, color='gray')
            ax.add_patch(arrow)
    
    ax.set_xlim(0, 1)
    ax.set_ylim(-0.5, 3.5)
    ax.axis('off')
    ax.set_title('User Behavior Conversion Funnel', fontsize=16, fontweight='bold', pad=20)
    
    plt.tight_layout()
    plt.savefig('VISUALIZATIONS_2_CONVERSION_FUNNEL.png', dpi=300, bbox_inches='tight')
    print("✓ Saved: VISUALIZATIONS_2_CONVERSION_FUNNEL.png")
    plt.close()

# ============================================================================
# 3. KNOWLEDGE GRAPH STRUCTURE
# ============================================================================

def plot_knowledge_graph():
    """Plot Knowledge Graph structure"""
    G = nx.DiGraph()
    
    # Add nodes
    users = [f'U{i}' for i in range(1, 6)]
    products = [f'P{i}' for i in range(1, 6)]
    categories = ['Electronics', 'Fashion', 'Home']
    
    for node in users:
        G.add_node(node, node_type='user')
    for node in products:
        G.add_node(node, node_type='product')
    for node in categories:
        G.add_node(node, node_type='category')
    
    # Add edges
    edges_user_product = [
        ('U1', 'P1', {'weight': 5}),
        ('U1', 'P2', {'weight': 3}),
        ('U2', 'P1', {'weight': 4}),
        ('U2', 'P3', {'weight': 2}),
        ('U3', 'P4', {'weight': 6}),
    ]
    
    edges_product_category = [
        ('P1', 'Electronics'),
        ('P2', 'Fashion'),
        ('P3', 'Home'),
        ('P4', 'Electronics'),
        ('P5', 'Fashion'),
    ]
    
    for source, target, attr in edges_user_product:
        G.add_edge(source, target, **attr)
    for source, target in edges_product_category:
        G.add_edge(source, target)
    
    # Plot
    fig, ax = plt.subplots(figsize=(14, 10))
    
    pos = {}
    # User nodes (left)
    for i, user in enumerate(users):
        pos[user] = (0, i - 2)
    # Product nodes (middle)
    for i, product in enumerate(products):
        pos[product] = (2, i - 2)
    # Category nodes (right)
    for i, cat in enumerate(categories):
        pos[cat] = (4, i - 1)
    
    # Draw nodes
    nx.draw_networkx_nodes(G, pos, nodelist=users, node_color='#FF6B6B', 
                          node_size=1500, label='Users', ax=ax)
    nx.draw_networkx_nodes(G, pos, nodelist=products, node_color='#4ECDC4', 
                          node_size=1500, label='Products', ax=ax)
    nx.draw_networkx_nodes(G, pos, nodelist=categories, node_color='#FFD700', 
                          node_size=1500, label='Categories', ax=ax)
    
    # Draw edges
    nx.draw_networkx_edges(G, pos, edgelist=edges_user_product, 
                          edge_color='gray', arrows=True, 
                          arrowsize=20, arrowstyle='->', width=2, ax=ax)
    nx.draw_networkx_edges(G, pos, edgelist=edges_product_category, 
                          edge_color='lightgray', arrows=True,
                          arrowsize=15, arrowstyle='->', width=1.5, style='dashed', ax=ax)
    
    # Draw labels
    nx.draw_networkx_labels(G, pos, font_size=10, font_weight='bold', ax=ax)
    
    ax.set_title('Knowledge Graph Structure\n(User → Product → Category)', 
                fontsize=16, fontweight='bold', pad=20)
    ax.legend(scatterpoints=1, loc='upper right', fontsize=12)
    ax.axis('off')
    
    plt.tight_layout()
    plt.savefig('VISUALIZATIONS_3_KNOWLEDGE_GRAPH.png', dpi=300, bbox_inches='tight')
    print("✓ Saved: VISUALIZATIONS_3_KNOWLEDGE_GRAPH.png")
    plt.close()

# ============================================================================
# 4. MODEL COMPARISON (RNN vs LSTM vs BiLSTM)
# ============================================================================

def plot_model_comparison():
    """Compare RNN, LSTM, BiLSTM models"""
    models = ['RNN', 'LSTM', 'BiLSTM']
    accuracy = [0.72, 0.81, 0.85]
    precision = [0.71, 0.80, 0.84]
    recall = [0.70, 0.79, 0.83]
    f1 = [0.70, 0.79, 0.84]
    params = [28, 112, 224]  # in thousands
    training_time = [45, 120, 145]  # in seconds
    
    x = np.arange(len(models))
    width = 0.2
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
    
    # Accuracy, Precision, Recall, F1
    ax1.bar(x - 1.5*width, accuracy, width, label='Accuracy', color='#FF6B6B')
    ax1.bar(x - 0.5*width, precision, width, label='Precision', color='#4ECDC4')
    ax1.bar(x + 0.5*width, recall, width, label='Recall', color='#45B7D1')
    ax1.bar(x + 1.5*width, f1, width, label='F1-Score', color='#FFA07A')
    ax1.set_ylabel('Score', fontsize=11, fontweight='bold')
    ax1.set_title('Performance Metrics', fontsize=13, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(models)
    ax1.legend()
    ax1.set_ylim([0, 1])
    ax1.grid(axis='y', alpha=0.3)
    
    # Parameters
    colors_params = ['#FF6B6B', '#4ECDC4', '#45B7D1']
    ax2.bar(models, params, color=colors_params)
    ax2.set_ylabel('Number of Parameters (K)', fontsize=11, fontweight='bold')
    ax2.set_title('Model Complexity', fontsize=13, fontweight='bold')
    for i, v in enumerate(params):
        ax2.text(i, v + 5, str(v) + 'K', ha='center', va='bottom', fontweight='bold')
    ax2.grid(axis='y', alpha=0.3)
    
    # Training Time
    ax3.bar(models, training_time, color=colors_params)
    ax3.set_ylabel('Training Time (seconds)', fontsize=11, fontweight='bold')
    ax3.set_title('Training Duration', fontsize=13, fontweight='bold')
    for i, v in enumerate(training_time):
        ax3.text(i, v + 5, str(v) + 's', ha='center', va='bottom', fontweight='bold')
    ax3.grid(axis='y', alpha=0.3)
    
    # Efficiency Score (F1/Params ratio)
    efficiency = [f1[i] / (params[i] / 100) for i in range(len(models))]
    ax4.bar(models, efficiency, color=colors_params)
    ax4.set_ylabel('Efficiency Score (F1/Params)', fontsize=11, fontweight='bold')
    ax4.set_title('Efficiency Analysis', fontsize=13, fontweight='bold')
    for i, v in enumerate(efficiency):
        ax4.text(i, v + 0.01, f'{v:.3f}', ha='center', va='bottom', fontweight='bold')
    ax4.grid(axis='y', alpha=0.3)
    
    plt.suptitle('RNN vs LSTM vs BiLSTM Comparison', fontsize=16, fontweight='bold', y=1.00)
    plt.tight_layout()
    plt.savefig('VISUALIZATIONS_4_MODEL_COMPARISON.png', dpi=300, bbox_inches='tight')
    print("✓ Saved: VISUALIZATIONS_4_MODEL_COMPARISON.png")
    plt.close()

# ============================================================================
# 5. RAG PIPELINE FLOW
# ============================================================================

def plot_rag_pipeline():
    """Plot RAG pipeline stages"""
    fig, ax = plt.subplots(figsize=(14, 10))
    
    stages = [
        {'name': 'User Query', 'color': '#FF6B6B', 'y': 4},
        {'name': 'Intent Detection\n(6 types)', 'color': '#FFA07A', 'y': 3},
        {'name': 'Retrieval', 'color': '#4ECDC4', 'y': 2},
        {'name': 'Ranking', 'color': '#45B7D1', 'y': 1},
        {'name': 'Generation', 'color': '#FFD700', 'y': 0},
    ]
    
    # Draw boxes and connections
    for stage in stages:
        rect = FancyBboxPatch((1, stage['y']-0.3), 3, 0.6,
                            boxstyle="round,pad=0.1",
                            edgecolor='black', facecolor=stage['color'],
                            linewidth=2, alpha=0.8)
        ax.add_patch(rect)
        
        ax.text(2.5, stage['y'], stage['name'], ha='center', va='center',
               fontsize=12, fontweight='bold')
        
        # Arrows
        if stage['y'] > 0:
            arrow = FancyArrowPatch((2.5, stage['y']-0.4), (2.5, stage['y']-0.95),
                                  arrowstyle='->', mutation_scale=30, linewidth=2.5,
                                  color='darkgray')
            ax.add_patch(arrow)
    
    # Side annotations
    annotations = [
        {'x': 5.2, 'y': 3, 'text': 'Keywords:\nrecommend, cheap,\nsimilar, best, etc.'},
        {'x': 5.2, 'y': 2, 'text': 'Sources:\n• Neo4j Graph\n• FAISS Vectors'},
        {'x': 5.2, 'y': 1, 'text': 'Merge & score:\n• Graph context (60%)\n• Vector context (40%)'},
        {'x': 5.2, 'y': 0, 'text': 'Template-based:\n• Fill products\n• Context blending'},
    ]
    
    for ann in annotations:
        ax.text(ann['x'], ann['y'], ann['text'], fontsize=10,
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
               verticalalignment='center')
    
    ax.set_xlim(0, 8)
    ax.set_ylim(-1, 5)
    ax.axis('off')
    ax.set_title('RAG (Retrieval-Augmented Generation) Pipeline', 
                fontsize=16, fontweight='bold', pad=20)
    
    plt.tight_layout()
    plt.savefig('VISUALIZATIONS_5_RAG_PIPELINE.png', dpi=300, bbox_inches='tight')
    print("✓ Saved: VISUALIZATIONS_5_RAG_PIPELINE.png")
    plt.close()

# ============================================================================
# 6. EMBEDDING DIMENSIONALITY REDUCTION (t-SNE)
# ============================================================================

def plot_embeddings():
    """Plot product embeddings (simulated t-SNE)"""
    np.random.seed(42)
    
    # Simulate embeddings in 2D (t-SNE reduced)
    n_products = 100
    n_categories = 5
    
    embeddings = []
    categories = []
    colors_map = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8']
    
    for cat_idx in range(n_categories):
        cat_embeddings = np.random.randn(n_products // n_categories, 2) + cat_idx * 3
        embeddings.extend(cat_embeddings)
        categories.extend([f'Category_{cat_idx}'] * (n_products // n_categories))
    
    embeddings = np.array(embeddings)
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    for cat_idx in range(n_categories):
        mask = np.array(categories) == f'Category_{cat_idx}'
        ax.scatter(embeddings[mask, 0], embeddings[mask, 1],
                  c=colors_map[cat_idx], s=100, alpha=0.6,
                  label=f'Category_{cat_idx}', edgecolors='black', linewidth=0.5)
    
    ax.set_xlabel('t-SNE Dimension 1', fontsize=12, fontweight='bold')
    ax.set_ylabel('t-SNE Dimension 2', fontsize=12, fontweight='bold')
    ax.set_title('Product Embeddings Visualization (t-SNE)\n128D → 2D', 
                fontsize=14, fontweight='bold')
    ax.legend(loc='best', fontsize=10)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('VISUALIZATIONS_6_EMBEDDINGS.png', dpi=300, bbox_inches='tight')
    print("✓ Saved: VISUALIZATIONS_6_EMBEDDINGS.png")
    plt.close()

# ============================================================================
# 7. FAISS SEARCH PERFORMANCE
# ============================================================================

def plot_faiss_performance():
    """Plot FAISS search latency"""
    k_values = [1, 5, 10, 20, 50, 100]
    latencies = [25, 28, 32, 45, 65, 95]  # milliseconds
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    ax.plot(k_values, latencies, marker='o', linewidth=3, markersize=10,
           color='#4ECDC4', markerfacecolor='#FF6B6B', markeredgewidth=2)
    
    ax.fill_between(k_values, latencies, alpha=0.2, color='#4ECDC4')
    
    ax.set_xlabel('K (Number of Nearest Neighbors)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Latency (ms)', fontsize=12, fontweight='bold')
    ax.set_title('FAISS Vector Search Performance', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    # Add value labels
    for k, lat in zip(k_values, latencies):
        ax.text(k, lat + 3, f'{lat}ms', ha='center', fontweight='bold', fontsize=10)
    
    plt.tight_layout()
    plt.savefig('VISUALIZATIONS_7_FAISS_PERFORMANCE.png', dpi=300, bbox_inches='tight')
    print("✓ Saved: VISUALIZATIONS_7_FAISS_PERFORMANCE.png")
    plt.close()

# ============================================================================
# 8. SYSTEM ARCHITECTURE
# ============================================================================

def plot_system_architecture():
    """Plot overall system architecture"""
    fig, ax = plt.subplots(figsize=(14, 10))
    
    # Draw components
    components = [
        {'name': 'User Actions', 'pos': (2, 4), 'color': '#FF6B6B', 'size': (1.5, 0.6)},
        {'name': 'Product Service\n(8001)', 'pos': (0.5, 2.5), 'color': '#FFA07A', 'size': (1.8, 0.8)},
        {'name': 'AI Service\n(8000)', 'pos': (3.5, 2.5), 'color': '#4ECDC4', 'size': (1.8, 0.8)},
        {'name': 'PostgreSQL\n(ai_service)', 'pos': (2, 0.8), 'color': '#98D8C8', 'size': (1.5, 0.7)},
        {'name': 'Neo4j\nGraph DB', 'pos': (3.5, 0.8), 'color': '#45B7D1', 'size': (1.5, 0.7)},
        {'name': 'FAISS\nVector Index', 'pos': (5, 0.8), 'color': '#FFD700', 'size': (1.5, 0.7)},
    ]
    
    for comp in components:
        rect = FancyBboxPatch((comp['pos'][0] - comp['size'][0]/2, comp['pos'][1] - comp['size'][1]/2),
                             comp['size'][0], comp['size'][1],
                             boxstyle="round,pad=0.1",
                             edgecolor='black', facecolor=comp['color'],
                             linewidth=2, alpha=0.7)
        ax.add_patch(rect)
        
        ax.text(comp['pos'][0], comp['pos'][1], comp['name'],
               ha='center', va='center', fontsize=11, fontweight='bold')
    
    # Draw connections
    connections = [
        ((2, 3.7), (3.5, 3.1), 'HTTP'),
        ((2, 3.7), (0.5, 2.9), 'HTTP'),
        ((3.5, 2.1), (2, 1.15), 'Query/Write'),
        ((3.5, 2.1), (3.5, 1.15), 'Read/Write'),
        ((3.5, 2.1), (5, 1.15), 'Search'),
    ]
    
    for start, end, label in connections:
        arrow = FancyArrowPatch(start, end, arrowstyle='->', mutation_scale=20,
                              linewidth=2, color='gray')
        ax.add_patch(arrow)
        
        mid_x, mid_y = (start[0] + end[0]) / 2, (start[1] + end[1]) / 2
        ax.text(mid_x + 0.2, mid_y, label, fontsize=9, style='italic',
               bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    ax.set_xlim(-0.5, 6.5)
    ax.set_ylim(0, 4.8)
    ax.axis('off')
    ax.set_title('AI-Service System Architecture', fontsize=16, fontweight='bold', pad=20)
    
    plt.tight_layout()
    plt.savefig('VISUALIZATIONS_8_SYSTEM_ARCHITECTURE.png', dpi=300, bbox_inches='tight')
    print("✓ Saved: VISUALIZATIONS_8_SYSTEM_ARCHITECTURE.png")
    plt.close()

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*60)
    print("GENERATING VISUALIZATIONS FOR AI-SERVICE REPORT")
    print("="*60 + "\n")
    
    plot_interaction_distribution()
    plot_conversion_funnel()
    plot_knowledge_graph()
    plot_model_comparison()
    plot_rag_pipeline()
    plot_embeddings()
    plot_faiss_performance()
    plot_system_architecture()
    
    print("\n" + "="*60)
    print("✓ ALL VISUALIZATIONS GENERATED SUCCESSFULLY!")
    print("="*60)
    print("\nFiles created:")
    print("  1. VISUALIZATIONS_1_INTERACTION_DISTRIBUTION.png")
    print("  2. VISUALIZATIONS_2_CONVERSION_FUNNEL.png")
    print("  3. VISUALIZATIONS_3_KNOWLEDGE_GRAPH.png")
    print("  4. VISUALIZATIONS_4_MODEL_COMPARISON.png")
    print("  5. VISUALIZATIONS_5_RAG_PIPELINE.png")
    print("  6. VISUALIZATIONS_6_EMBEDDINGS.png")
    print("  7. VISUALIZATIONS_7_FAISS_PERFORMANCE.png")
    print("  8. VISUALIZATIONS_8_SYSTEM_ARCHITECTURE.png")
    print()
