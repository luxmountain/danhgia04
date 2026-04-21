"""
Build Knowledge Base Graph (KB_Graph) in Neo4j from data_user500.csv.
Creates nodes: User, Behavior, Segment
Creates edges: User-[HAS_BEHAVIOR]->Behavior, User-[BELONGS_TO]->Segment,
               User-[SIMILAR_TO]->User (based on behavior similarity)

Usage: python ai_service/scripts/build_kb_graph.py
"""
import os, sys, json
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
from dotenv import load_dotenv
load_dotenv()

from neo4j import GraphDatabase

DATA_PATH = os.path.join("data", "data_user500.csv")
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PWD = os.getenv("NEO4J_PASSWORD", "changeme123")

BEHAVIORS = ["view", "click", "cart", "purchase", "search", "wishlist", "review", "share"]
TOP_K_SIMILAR = 5


def build_graph():
    df = pd.read_csv(DATA_PATH)
    print(f"Loaded {len(df)} users from {DATA_PATH}")

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PWD))

    with driver.session() as session:
        # Create constraints
        print("Creating constraints...")
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (u:BehaviorUser) REQUIRE u.id IS UNIQUE")
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (s:Segment) REQUIRE s.name IS UNIQUE")
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (b:BehaviorType) REQUIRE b.name IS UNIQUE")

        # Create BehaviorType nodes
        print("Creating BehaviorType nodes...")
        for b in BEHAVIORS:
            session.run("MERGE (b:BehaviorType {name: $name})", name=b)

        # Create Segment nodes
        print("Creating Segment nodes...")
        for seg in df["segment"].unique():
            session.run("MERGE (s:Segment {name: $name})", name=seg)

        # Create User nodes with behavior properties + edges
        print("Creating User nodes and relationships...")
        for _, row in df.iterrows():
            uid = int(row["user_id"])
            segment = row["segment"]

            # Create user node with all behavior counts as properties
            props = {b: int(row[b]) for b in BEHAVIORS}
            props["id"] = uid
            props["segment"] = segment
            session.run(
                """
                MERGE (u:BehaviorUser {id: $id})
                SET u.view = $view, u.click = $click, u.cart = $cart,
                    u.purchase = $purchase, u.search = $search,
                    u.wishlist = $wishlist, u.review = $review, u.share = $share,
                    u.segment = $segment
                """, **props
            )

            # User -> Segment
            session.run(
                """
                MATCH (u:BehaviorUser {id: $uid})
                MATCH (s:Segment {name: $seg})
                MERGE (u)-[:CLASSIFIED_AS]->(s)
                """, uid=uid, seg=segment
            )

            # User -> BehaviorType (with count as weight)
            for b in BEHAVIORS:
                if int(row[b]) > 0:
                    session.run(
                        """
                        MATCH (u:BehaviorUser {id: $uid})
                        MATCH (bt:BehaviorType {name: $bname})
                        MERGE (u)-[r:HAS_BEHAVIOR]->(bt)
                        SET r.count = $count
                        """, uid=uid, bname=b, count=int(row[b])
                    )

        # Compute user similarity and create SIMILAR_TO edges
        print("Computing user similarities...")
        features = df[BEHAVIORS].values.astype(np.float32)
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features)
        sim_matrix = cosine_similarity(features_scaled)

        print("Creating SIMILAR_TO edges (top-5 per user)...")
        for i in range(len(df)):
            uid = int(df.iloc[i]["user_id"])
            sims = sim_matrix[i]
            # Get top-K similar (excluding self)
            top_indices = np.argsort(sims)[::-1][1:TOP_K_SIMILAR + 1]

            for j in top_indices:
                other_uid = int(df.iloc[j]["user_id"])
                score = float(sims[j])
                session.run(
                    """
                    MATCH (u1:BehaviorUser {id: $uid1})
                    MATCH (u2:BehaviorUser {id: $uid2})
                    MERGE (u1)-[r:SIMILAR_TO]->(u2)
                    SET r.score = $score
                    """, uid1=uid, uid2=other_uid, score=score
                )

    driver.close()

    # Print stats
    total_nodes = len(df) + len(BEHAVIORS) + df["segment"].nunique()
    total_edges = len(df) * (1 + sum(1 for _ in BEHAVIORS)) + len(df) * TOP_K_SIMILAR
    print(f"\nKB_Graph built successfully!")
    print(f"  Nodes: ~{total_nodes} (500 Users + {len(BEHAVIORS)} BehaviorTypes + {df['segment'].nunique()} Segments)")
    print(f"  Edges: ~{total_edges}")
    print(f"  Edge types: HAS_BEHAVIOR, CLASSIFIED_AS, SIMILAR_TO")
    print(f"\nNeo4j Browser: http://localhost:7474")
    print(f"Sample Cypher queries:")
    print(f"  MATCH (u:BehaviorUser)-[r:HAS_BEHAVIOR]->(b:BehaviorType) RETURN u, r, b LIMIT 50")
    print(f"  MATCH (u:BehaviorUser)-[:SIMILAR_TO]->(other) WHERE u.id = 1 RETURN u, other")
    print(f"  MATCH (s:Segment)<-[:CLASSIFIED_AS]-(u:BehaviorUser) RETURN s.name, count(u)")


if __name__ == "__main__":
    build_graph()
