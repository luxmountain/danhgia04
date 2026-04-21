"""
Test suite for AI Service - Behavior Classification & KB_Graph.
Tests: data generation, model training, Neo4j graph, RAG chat, integration endpoints.

Usage: python ai_service/scripts/test_all.py
"""
import os, sys, json, time
import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:8000")
GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:8080")

PASS = "✓"
FAIL = "✗"
results = []


def test(name, condition, detail=""):
    status = PASS if condition else FAIL
    results.append((name, condition))
    print(f"  {status} {name}" + (f" — {detail}" if detail else ""))
    return condition


def test_data_file():
    """Test 1: data_user500.csv exists and has correct structure."""
    print("\n[1] DATA FILE")
    path = "data/data_user500.csv"
    test("File exists", os.path.exists(path))

    import pandas as pd
    df = pd.read_csv(path)
    test("500 users", len(df) == 500, f"got {len(df)}")
    test("10 columns", len(df.columns) == 10, f"got {list(df.columns)}")

    expected_cols = {"user_id", "view", "click", "cart", "purchase", "search", "wishlist", "review", "share", "segment"}
    test("Correct columns", set(df.columns) == expected_cols)
    test("5 segments", df["segment"].nunique() == 5, f"got {df['segment'].nunique()}")
    test("No nulls", df.isnull().sum().sum() == 0)


def test_models():
    """Test 2: Trained models exist and can be loaded."""
    print("\n[2] TRAINED MODELS")
    model_dir = "data/models/behavior"
    test("RNN model exists", os.path.exists(f"{model_dir}/rnn_model.pt"))
    test("LSTM model exists", os.path.exists(f"{model_dir}/lstm_model.pt"))
    test("BiLSTM model exists", os.path.exists(f"{model_dir}/bilstm_model.pt"))
    test("Scaler exists", os.path.exists(f"{model_dir}/scaler.pkl"))
    test("Label encoder exists", os.path.exists(f"{model_dir}/label_encoder.pkl"))
    test("Evaluation results", os.path.exists(f"{model_dir}/evaluation_results.json"))

    # Load and check evaluation results
    with open(f"{model_dir}/evaluation_results.json") as f:
        eval_data = json.load(f)
    best = eval_data["best_model"]
    best_f1 = eval_data["metrics"][best]["f1"]
    test(f"Best model F1 > 0.8", best_f1 > 0.8, f"{best}: F1={best_f1:.4f}")

    # Test model loading
    import torch
    import importlib.util
    spec = importlib.util.spec_from_file_location("behavior_models", "ai_service/models/behavior_models.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    model = mod.RNNClassifier(1, 64, 5)
    model.load_state_dict(torch.load(f"{model_dir}/rnn_model.pt", map_location="cpu", weights_only=True))
    test("RNN model loads correctly", True)


def test_plots():
    """Test 3: Visualization plots exist."""
    print("\n[3] PLOTS")
    plot_dir = "docs/plots"
    test("Training curves", os.path.exists(f"{plot_dir}/training_curves.png"))
    test("Model comparison", os.path.exists(f"{plot_dir}/model_comparison.png"))
    test("Confusion matrices", os.path.exists(f"{plot_dir}/confusion_matrices.png"))


def test_neo4j():
    """Test 4: KB_Graph in Neo4j."""
    print("\n[4] NEO4J KB_GRAPH")
    from neo4j import GraphDatabase
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    pwd = os.getenv("NEO4J_PASSWORD", "changeme123")

    driver = GraphDatabase.driver(uri, auth=(user, pwd))
    with driver.session() as s:
        # Count nodes
        r = s.run("MATCH (u:BehaviorUser) RETURN count(u) AS c").single()
        test("500 BehaviorUser nodes", r["c"] == 500, f"got {r['c']}")

        r = s.run("MATCH (b:BehaviorType) RETURN count(b) AS c").single()
        test("8 BehaviorType nodes", r["c"] == 8, f"got {r['c']}")

        r = s.run("MATCH (s:Segment) RETURN count(s) AS c").single()
        test("5 Segment nodes", r["c"] == 5, f"got {r['c']}")

        # Count edges
        r = s.run("MATCH ()-[r:HAS_BEHAVIOR]->() RETURN count(r) AS c").single()
        test("HAS_BEHAVIOR edges > 3000", r["c"] > 3000, f"got {r['c']}")

        r = s.run("MATCH ()-[r:SIMILAR_TO]->() RETURN count(r) AS c").single()
        test("SIMILAR_TO edges = 2500", r["c"] == 2500, f"got {r['c']}")

        r = s.run("MATCH ()-[r:CLASSIFIED_AS]->() RETURN count(r) AS c").single()
        test("CLASSIFIED_AS edges = 500", r["c"] == 500, f"got {r['c']}")

    driver.close()


def test_api_endpoints():
    """Test 5: API endpoints via ai-service."""
    print("\n[5] API ENDPOINTS (ai-service :8000)")

    # Behavior chat
    try:
        r = requests.post(f"{AI_SERVICE_URL}/api/behavior/chat/",
                          json={"user_id": 1, "query": "hành vi"}, timeout=10)
        test("POST /api/behavior/chat/ → 200", r.status_code == 200)
        data = r.json()
        test("Chat returns answer", "answer" in data and len(data["answer"]) > 0)
    except Exception as e:
        test("POST /api/behavior/chat/", False, str(e))

    # Segment
    try:
        r = requests.get(f"{AI_SERVICE_URL}/api/behavior/segment/1/", timeout=10)
        test("GET /api/behavior/segment/1/ → 200", r.status_code == 200)
        data = r.json()
        test("Segment returns predicted_segment", "predicted_segment" in data.get("context", {}))
    except Exception as e:
        test("GET /api/behavior/segment/", False, str(e))

    # Recommend
    try:
        r = requests.get(f"{AI_SERVICE_URL}/api/behavior/recommend/10/", timeout=10)
        test("GET /api/behavior/recommend/10/ → 200", r.status_code == 200)
    except Exception as e:
        test("GET /api/behavior/recommend/", False, str(e))

    # Integration search
    try:
        r = requests.get(f"{AI_SERVICE_URL}/api/integration/search/?q=shoes&user_id=1", timeout=10)
        test("GET /api/integration/search/ → 200", r.status_code == 200)
    except Exception as e:
        test("GET /api/integration/search/", False, str(e))

    # Integration cart
    try:
        r = requests.get(f"{AI_SERVICE_URL}/api/integration/cart/5/", timeout=10)
        test("GET /api/integration/cart/5/ → 200", r.status_code == 200)
        data = r.json()
        test("Cart returns segment", "segment" in data)
    except Exception as e:
        test("GET /api/integration/cart/", False, str(e))

    # Chat UI
    try:
        r = requests.get(f"{AI_SERVICE_URL}/api/integration/chat-ui/", timeout=10)
        test("GET /api/integration/chat-ui/ → 200 HTML", r.status_code == 200 and "html" in r.headers.get("content-type", ""))
    except Exception as e:
        test("GET /api/integration/chat-ui/", False, str(e))


def test_gateway():
    """Test 6: API via Gateway."""
    print("\n[6] GATEWAY (:8080)")
    try:
        r = requests.get(f"{GATEWAY_URL}/api/ai/behavior/segment/1/", timeout=10)
        test("Gateway → behavior/segment → 200", r.status_code == 200)
    except Exception as e:
        test("Gateway routing", False, str(e))

    try:
        r = requests.post(f"{GATEWAY_URL}/api/ai/behavior/chat/",
                          json={"user_id": 5, "query": "tương tự"}, timeout=10)
        test("Gateway → behavior/chat → 200", r.status_code == 200)
    except Exception as e:
        test("Gateway chat", False, str(e))


def main():
    print("=" * 60)
    print("AI SERVICE TEST SUITE")
    print("=" * 60)

    test_data_file()
    test_models()
    test_plots()
    test_neo4j()
    test_api_endpoints()
    test_gateway()

    # Summary
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    print(f"\n{'=' * 60}")
    print(f"RESULTS: {passed}/{total} tests passed")
    print(f"{'=' * 60}")

    if passed == total:
        print("🎉 All tests passed!")
    else:
        failed = [(name, ok) for name, ok in results if not ok]
        print(f"\nFailed tests:")
        for name, _ in failed:
            print(f"  {FAIL} {name}")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
