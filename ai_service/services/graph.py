import os
from neo4j import GraphDatabase

_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
_USER = os.getenv("NEO4J_USER", "neo4j")
_PWD = os.getenv("NEO4J_PASSWORD", "changeme123")

# Edge weight coefficients
ALPHA, BETA, GAMMA = 1, 3, 5
WEIGHT_MAP = {"view": ALPHA, "click": ALPHA, "cart": BETA, "purchase": GAMMA}


class GraphService:
    def __init__(self):
        self.driver = GraphDatabase.driver(_URI, auth=(_USER, _PWD))

    def close(self):
        self.driver.close()

    # ── Bootstrap ──────────────────────────────────────────────
    def create_indexes(self):
        queries = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Product) REQUIRE p.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Category) REQUIRE c.id IS UNIQUE",
        ]
        with self.driver.session() as s:
            for q in queries:
                s.run(q)

    # ── Sync from Postgres ─────────────────────────────────────
    def sync_product(self, pid, name, description, price, category_id=None, category_name=None):
        q = """
        MERGE (p:Product {id: $pid})
        SET p.name=$name, p.description=$description, p.price=$price
        """
        if category_id:
            q += """
            MERGE (c:Category {id: $cid})
            SET c.name=$cname
            MERGE (p)-[:BELONGS_TO]->(c)
            """
        with self.driver.session() as s:
            s.run(q, pid=pid, name=name, description=description,
                  price=float(price), cid=category_id, cname=category_name)

    # ── Log interaction ────────────────────────────────────────
    def log_interaction(self, user_id, product_id, event_type):
        weight = WEIGHT_MAP.get(event_type, 1)
        q = """
        MERGE (u:User {id: $uid})
        MERGE (p:Product {id: $pid})
        MERGE (u)-[r:INTERACTED]->(p)
        ON CREATE SET r.weight = $w, r.types = [$et]
        ON MATCH SET r.weight = r.weight + $w,
                     r.types = CASE WHEN $et IN r.types THEN r.types
                                    ELSE r.types + $et END
        """
        with self.driver.session() as s:
            s.run(q, uid=user_id, pid=product_id, w=weight, et=event_type)

    def log_search(self, user_id, query_text):
        q = """
        MERGE (u:User {id: $uid})
        MERGE (q:Query {text: $text})
        MERGE (u)-[:SEARCHED]->(q)
        """
        with self.driver.session() as s:
            s.run(q, uid=user_id, text=query_text)

    # ── Recommendations ────────────────────────────────────────
    def recommend(self, user_id, limit=10):
        q = """
        MATCH (u:User {id: $uid})-[r1:INTERACTED]->(p:Product)
        MATCH (other:User)-[r2:INTERACTED]->(p)
        WHERE other.id <> $uid
        MATCH (other)-[r3:INTERACTED]->(rec:Product)
        WHERE NOT (u)-[:INTERACTED]->(rec)
        RETURN rec.id AS product_id, rec.name AS name,
               SUM(r3.weight) AS score
        ORDER BY score DESC LIMIT $lim
        """
        with self.driver.session() as s:
            return [dict(r) for r in s.run(q, uid=user_id, lim=limit)]

    def get_user_context(self, user_id, limit=10):
        """Get user's recent interactions for RAG context."""
        q = """
        MATCH (u:User {id: $uid})-[r:INTERACTED]->(p:Product)
        OPTIONAL MATCH (p)-[:BELONGS_TO]->(c:Category)
        RETURN p.name AS product, p.description AS description,
               c.name AS category, r.weight AS weight
        ORDER BY r.weight DESC LIMIT $lim
        """
        with self.driver.session() as s:
            return [dict(r) for r in s.run(q, uid=user_id, lim=limit)]

    def get_similar_products(self, product_id, limit=5):
        q = """
        MATCH (p:Product {id: $pid})-[:SIMILAR]->(rec:Product)
        RETURN rec.id AS product_id, rec.name AS name
        LIMIT $lim
        """
        with self.driver.session() as s:
            return [dict(r) for r in s.run(q, pid=product_id, lim=limit)]

    def write_similar_edges(self, product_id, similar_ids, scores):
        """Write SIMILAR edges from precomputed embeddings."""
        q = """
        MATCH (a:Product {id: $pid})
        MATCH (b:Product {id: $sid})
        MERGE (a)-[r:SIMILAR]->(b)
        SET r.score = $score
        """
        with self.driver.session() as s:
            for sid, sc in zip(similar_ids, scores):
                s.run(q, pid=product_id, sid=int(sid), score=float(sc))

    # ── Export for GNN ─────────────────────────────────────────
    def export_edges(self):
        """Export all INTERACTED edges for GNN training."""
        q = """
        MATCH (u:User)-[r:INTERACTED]->(p:Product)
        RETURN u.id AS user_id, p.id AS product_id, r.weight AS weight
        """
        with self.driver.session() as s:
            return [dict(r) for r in s.run(q)]

    def export_product_categories(self):
        q = """
        MATCH (p:Product)-[:BELONGS_TO]->(c:Category)
        RETURN p.id AS product_id, c.id AS category_id
        """
        with self.driver.session() as s:
            return [dict(r) for r in s.run(q)]


graph_service = GraphService()
