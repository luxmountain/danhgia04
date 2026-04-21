"""
E-commerce integration endpoints:
- GET /api/integration/search/?q=...&user_id=... → product search + behavior-based recommendations
- GET /api/integration/cart/<user_id>/ → cart recommendations based on user segment
- GET /api/integration/chat-ui/ → Chat UI HTML page (not ChatGPT style)
"""
import os, sys
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import HttpResponse

from ai_service.services.behavior_rag import behavior_rag
from ai_service.services.graph import graph_service
from ai_service.services import product_client


@api_view(["GET"])
def integration_search(request):
    """Search products + behavior-based recommendations for user."""
    query = request.query_params.get("q", "")
    user_id = request.query_params.get("user_id")

    # Get products from product-service
    products = []
    if query:
        search_result = product_client.search_products(query)
        products = search_result.get("results", []) if isinstance(search_result, dict) else search_result

    # If user_id provided, add behavior-based recommendations
    recommendations = []
    user_context = {}
    if user_id:
        uid = int(user_id)
        # Get user segment and similar users' preferences
        rag_result = behavior_rag.chat(uid, f"gợi ý cho search '{query}'")
        user_context = rag_result.get("context", {})

        # Get graph-based recommendations
        graph_recs = graph_service.recommend(uid, limit=5)
        recommendations = graph_recs

    return Response({
        "query": query,
        "products": products[:10],
        "recommendations": recommendations,
        "user_context": user_context,
    })


@api_view(["GET"])
def integration_cart(request, user_id):
    """Cart page recommendations based on user behavior segment."""
    rag_result = behavior_rag.chat(user_id, "recommend gợi ý sản phẩm cho giỏ hàng")
    graph_recs = graph_service.recommend(user_id, limit=5)

    return Response({
        "user_id": user_id,
        "segment": rag_result.get("context", {}).get("predicted_segment", "unknown"),
        "recommendations": graph_recs,
        "suggestion": rag_result.get("answer", ""),
    })


@api_view(["GET"])
def chat_ui(request):
    """Serve custom chat UI (not ChatGPT style)."""
    html = """<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Shopping Assistant</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', sans-serif; background: #f0f2f5; height: 100vh; display: flex; }

        .sidebar {
            width: 280px; background: #1a1a2e; color: #fff; padding: 20px;
            display: flex; flex-direction: column;
        }
        .sidebar h2 { font-size: 18px; margin-bottom: 20px; color: #e94560; }
        .user-input { margin-bottom: 15px; }
        .user-input label { font-size: 12px; color: #aaa; display: block; margin-bottom: 4px; }
        .user-input input {
            width: 100%; padding: 8px; border: 1px solid #333; border-radius: 6px;
            background: #16213e; color: #fff; font-size: 14px;
        }
        .quick-actions { margin-top: 20px; }
        .quick-actions h3 { font-size: 13px; color: #aaa; margin-bottom: 10px; }
        .quick-btn {
            display: block; width: 100%; padding: 10px; margin-bottom: 8px;
            background: #16213e; border: 1px solid #333; border-radius: 8px;
            color: #fff; cursor: pointer; font-size: 13px; text-align: left;
        }
        .quick-btn:hover { background: #0f3460; border-color: #e94560; }

        .main { flex: 1; display: flex; flex-direction: column; }
        .header {
            padding: 15px 25px; background: #fff; border-bottom: 1px solid #ddd;
            display: flex; align-items: center; justify-content: space-between;
        }
        .header h1 { font-size: 20px; color: #1a1a2e; }
        .status { font-size: 12px; color: #4caf50; }

        .chat-area {
            flex: 1; overflow-y: auto; padding: 20px 25px;
            display: flex; flex-direction: column; gap: 12px;
        }
        .msg { max-width: 75%; padding: 12px 16px; border-radius: 12px; font-size: 14px; line-height: 1.5; }
        .msg.user { align-self: flex-end; background: #e94560; color: #fff; border-bottom-right-radius: 4px; }
        .msg.bot { align-self: flex-start; background: #fff; color: #333; border-bottom-left-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .msg.bot pre { white-space: pre-wrap; font-family: inherit; }

        .input-area {
            padding: 15px 25px; background: #fff; border-top: 1px solid #ddd;
            display: flex; gap: 10px;
        }
        .input-area input {
            flex: 1; padding: 12px 16px; border: 1px solid #ddd; border-radius: 24px;
            font-size: 14px; outline: none;
        }
        .input-area input:focus { border-color: #e94560; }
        .input-area button {
            padding: 12px 24px; background: #e94560; color: #fff; border: none;
            border-radius: 24px; cursor: pointer; font-size: 14px; font-weight: 600;
        }
        .input-area button:hover { background: #c23152; }
    </style>
</head>
<body>
    <div class="sidebar">
        <h2>🛒 AI Assistant</h2>
        <div class="user-input">
            <label>User ID</label>
            <input type="number" id="userId" value="1" min="1" max="500">
        </div>
        <div class="quick-actions">
            <h3>Quick Actions</h3>
            <button class="quick-btn" onclick="sendQuick('hành vi của tôi')">📊 Xem hành vi</button>
            <button class="quick-btn" onclick="sendQuick('phân loại segment')">🏷️ Phân loại</button>
            <button class="quick-btn" onclick="sendQuick('users tương tự')">👥 Users tương tự</button>
            <button class="quick-btn" onclick="sendQuick('gợi ý sản phẩm')">💡 Gợi ý</button>
            <button class="quick-btn" onclick="sendQuick('thống kê nhóm')">📈 Thống kê</button>
        </div>
    </div>

    <div class="main">
        <div class="header">
            <h1>Behavior-based Shopping Assistant</h1>
            <span class="status">● Online (KB_Graph + RNN)</span>
        </div>
        <div class="chat-area" id="chatArea">
            <div class="msg bot"><pre>Xin chào! Tôi là AI Shopping Assistant.
Tôi phân tích hành vi mua sắm của bạn qua Knowledge Graph và mô hình RNN.
Hãy hỏi tôi về: hành vi, phân loại, gợi ý, users tương tự, thống kê.</pre></div>
        </div>
        <div class="input-area">
            <input type="text" id="msgInput" placeholder="Nhập câu hỏi..." onkeypress="if(event.key==='Enter')sendMsg()">
            <button onclick="sendMsg()">Gửi</button>
        </div>
    </div>

    <script>
        const API_BASE = window.location.origin;
        const API_PREFIX = window.location.pathname.includes('/api/ai/') ? '/api/ai' : '/api';

        function addMsg(text, isUser) {
            const area = document.getElementById('chatArea');
            const div = document.createElement('div');
            div.className = 'msg ' + (isUser ? 'user' : 'bot');
            div.innerHTML = isUser ? text : '<pre>' + text + '</pre>';
            area.appendChild(div);
            area.scrollTop = area.scrollHeight;
        }

        async function sendMsg() {
            const input = document.getElementById('msgInput');
            const userId = document.getElementById('userId').value;
            const query = input.value.trim();
            if (!query) return;

            addMsg(query, true);
            input.value = '';

            try {
                const resp = await fetch(API_BASE + API_PREFIX + '/behavior/chat/', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({user_id: parseInt(userId), query: query})
                });
                const data = await resp.json();
                addMsg(data.answer || 'Không có phản hồi.', false);
            } catch (e) {
                addMsg('Lỗi kết nối: ' + e.message, false);
            }
        }

        function sendQuick(text) {
            document.getElementById('msgInput').value = text;
            sendMsg();
        }
    </script>
</body>
</html>"""
    return HttpResponse(html, content_type="text/html")
