"""
RAG Chat service based on KB_Graph (Neo4j behavior graph).
Retrieves user behavior context from graph, classifies user segment,
and generates contextual responses.
"""
import os, pickle
import numpy as np
import torch
from neo4j import GraphDatabase

_NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
_NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
_NEO4J_PWD = os.getenv("NEO4J_PASSWORD", "changeme123")
_MODEL_DIR = os.getenv("MODEL_DIR", "data/models")

BEHAVIORS = ["view", "click", "cart", "purchase", "search", "wishlist", "review", "share"]

# Intent patterns for behavior-based chat
_BEHAVIOR_INTENTS = [
    (["segment", "phân loại", "nhóm", "loại khách"], "segment_info"),
    (["tương tự", "similar", "giống", "like me"], "similar_users"),
    (["hành vi", "behavior", "thói quen", "pattern"], "behavior_summary"),
    (["recommend", "gợi ý", "đề xuất", "nên"], "recommend"),
    (["thống kê", "stats", "tổng quan", "overview"], "stats"),
]


class BehaviorRAGChat:
    def __init__(self):
        self.driver = GraphDatabase.driver(_NEO4J_URI, auth=(_NEO4J_USER, _NEO4J_PWD))
        self._model = None
        self._scaler = None
        self._le = None

    def _load_model(self):
        if self._model is not None:
            return
        from ai_service.models.behavior_models import RNNClassifier
        model_path = os.path.join(_MODEL_DIR, "behavior", "rnn_model.pt")
        scaler_path = os.path.join(_MODEL_DIR, "behavior", "scaler.pkl")
        le_path = os.path.join(_MODEL_DIR, "behavior", "label_encoder.pkl")

        if all(os.path.exists(p) for p in [model_path, scaler_path, le_path]):
            with open(scaler_path, "rb") as f:
                self._scaler = pickle.load(f)
            with open(le_path, "rb") as f:
                self._le = pickle.load(f)
            self._model = RNNClassifier(1, 64, len(self._le.classes_))
            self._model.load_state_dict(torch.load(model_path, map_location="cpu", weights_only=True))
            self._model.eval()

    def _get_user_from_graph(self, user_id):
        """Retrieve user behavior data from KB_Graph."""
        with self.driver.session() as s:
            result = s.run(
                """
                MATCH (u:BehaviorUser {id: $uid})
                RETURN u.view AS view, u.click AS click, u.cart AS cart,
                       u.purchase AS purchase, u.search AS search,
                       u.wishlist AS wishlist, u.review AS review,
                       u.share AS share, u.segment AS segment
                """, uid=user_id
            )
            record = result.single()
            return dict(record) if record else None

    def _get_similar_users(self, user_id, limit=5):
        """Get similar users from graph."""
        with self.driver.session() as s:
            result = s.run(
                """
                MATCH (u:BehaviorUser {id: $uid})-[r:SIMILAR_TO]->(other:BehaviorUser)
                RETURN other.id AS user_id, other.segment AS segment, r.score AS score
                ORDER BY r.score DESC LIMIT $lim
                """, uid=user_id, lim=limit
            )
            return [dict(r) for r in result]

    def _get_segment_stats(self, segment):
        """Get segment statistics from graph."""
        with self.driver.session() as s:
            result = s.run(
                """
                MATCH (u:BehaviorUser)-[:CLASSIFIED_AS]->(s:Segment {name: $seg})
                RETURN count(u) AS count,
                       avg(u.view) AS avg_view, avg(u.purchase) AS avg_purchase,
                       avg(u.cart) AS avg_cart, avg(u.search) AS avg_search
                """, seg=segment
            )
            return dict(result.single())

    def _detect_intent(self, query):
        q = query.lower()
        for keywords, intent in _BEHAVIOR_INTENTS:
            if any(kw in q for kw in keywords):
                return intent
        return "general"

    def _predict_segment(self, user_data):
        """Use trained RNN model to predict user segment."""
        self._load_model()
        if self._model is None:
            return user_data.get("segment", "unknown")

        features = np.array([[user_data[b] for b in BEHAVIORS]], dtype=np.float32)
        features_scaled = self._scaler.transform(features)
        X = torch.tensor(features_scaled.reshape(1, 8, 1), dtype=torch.float32)
        with torch.no_grad():
            pred = self._model(X).argmax(1).item()
        return self._le.inverse_transform([pred])[0]

    def chat(self, user_id, query):
        """
        RAG chat: retrieve from KB_Graph + generate response.
        No external LLM API used.
        """
        # 1. Retrieve user context from graph
        user_data = self._get_user_from_graph(user_id)
        if not user_data:
            return {
                "answer": f"Không tìm thấy thông tin user {user_id} trong hệ thống.",
                "context": {}
            }

        intent = self._detect_intent(query)

        # 2. Retrieve relevant graph context based on intent
        context = {"user": user_data, "intent": intent}

        if intent == "similar_users":
            context["similar"] = self._get_similar_users(user_id)

        if intent in ("segment_info", "stats"):
            context["segment_stats"] = self._get_segment_stats(user_data["segment"])

        # 3. Predict segment using trained model
        predicted_segment = self._predict_segment(user_data)
        context["predicted_segment"] = predicted_segment

        # 4. Generate response (template-based, no external API)
        answer = self._generate_response(user_id, user_data, intent, context)

        return {"answer": answer, "context": context}

    def _generate_response(self, user_id, user_data, intent, context):
        """Generate response based on intent and graph context."""
        segment = user_data["segment"]

        if intent == "segment_info":
            stats = context.get("segment_stats", {})
            return (
                f"User {user_id} thuộc nhóm '{segment}'.\n"
                f"Nhóm này có {stats.get('count', '?')} users.\n"
                f"Đặc điểm: view trung bình {stats.get('avg_view', 0):.0f}, "
                f"purchase trung bình {stats.get('avg_purchase', 0):.0f}.\n"
                f"Model RNN dự đoán: '{context.get('predicted_segment', segment)}'."
            )

        elif intent == "similar_users":
            similar = context.get("similar", [])
            if not similar:
                return f"Không tìm thấy users tương tự với user {user_id}."
            lines = [f"Users tương tự với user {user_id} (nhóm '{segment}'):"]
            for s in similar:
                lines.append(f"  - User {s['user_id']} (nhóm '{s['segment']}', similarity: {s['score']:.3f})")
            return "\n".join(lines)

        elif intent == "behavior_summary":
            return (
                f"Hành vi của user {user_id}:\n"
                f"  View: {user_data['view']}, Click: {user_data['click']}\n"
                f"  Cart: {user_data['cart']}, Purchase: {user_data['purchase']}\n"
                f"  Search: {user_data['search']}, Wishlist: {user_data['wishlist']}\n"
                f"  Review: {user_data['review']}, Share: {user_data['share']}\n"
                f"Phân loại: '{segment}' (dự đoán model: '{context.get('predicted_segment', segment)}')"
            )

        elif intent == "recommend":
            similar = self._get_similar_users(user_id, limit=3)
            if segment == "high_value":
                tip = "Gợi ý: Sản phẩm premium, loyalty rewards."
            elif segment == "browser":
                tip = "Gợi ý: Flash sale, limited-time offers để thúc đẩy mua hàng."
            elif segment == "bargain_hunter":
                tip = "Gợi ý: Coupon, bundle deals, price comparison."
            elif segment == "new_user":
                tip = "Gợi ý: Welcome discount, best-seller products."
            else:
                tip = "Gợi ý: Personalized recommendations dựa trên lịch sử."
            return f"User {user_id} ({segment}):\n{tip}\nUsers tương tự: {[s['user_id'] for s in similar]}"

        elif intent == "stats":
            stats = context.get("segment_stats", {})
            return (
                f"Thống kê nhóm '{segment}':\n"
                f"  Số lượng: {stats.get('count', '?')} users\n"
                f"  View TB: {stats.get('avg_view', 0):.1f}\n"
                f"  Purchase TB: {stats.get('avg_purchase', 0):.1f}\n"
                f"  Cart TB: {stats.get('avg_cart', 0):.1f}\n"
                f"  Search TB: {stats.get('avg_search', 0):.1f}"
            )

        else:
            return (
                f"User {user_id} thuộc nhóm '{segment}'.\n"
                f"Hành vi nổi bật: view={user_data['view']}, purchase={user_data['purchase']}.\n"
                f"Hãy hỏi cụ thể hơn: 'hành vi', 'tương tự', 'gợi ý', 'thống kê'."
            )


# Singleton
behavior_rag = BehaviorRAGChat()
