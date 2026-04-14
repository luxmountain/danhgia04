"""
Self-built response generator — no external LLM API.
Uses template matching + graph context + vector search results
to generate structured responses.
"""

# Intent patterns: (keywords, intent_key)
_INTENTS = [
    (["recommend", "suggest", "gợi ý", "đề xuất", "nên mua", "tư vấn"], "recommend"),
    (["cheap", "rẻ", "giá rẻ", "budget", "tiết kiệm", "affordable"], "cheap"),
    (["compare", "so sánh", "khác nhau", "difference", "vs"], "compare"),
    (["similar", "tương tự", "giống", "like", "alternative"], "similar"),
    (["best", "tốt nhất", "top", "popular", "phổ biến"], "best"),
    (["info", "thông tin", "chi tiết", "detail", "about", "là gì"], "info"),
]

_TEMPLATES = {
    "recommend": (
        "Dựa trên lịch sử của bạn, tôi gợi ý các sản phẩm sau:\n{product_list}\n"
        "{history_note}"
    ),
    "cheap": (
        "Các sản phẩm giá tốt phù hợp với bạn:\n{product_list}\n"
        "Sắp xếp theo giá từ thấp đến cao."
    ),
    "compare": (
        "So sánh các sản phẩm liên quan:\n{product_list}\n"
        "Bạn có thể xem chi tiết từng sản phẩm để so sánh thêm."
    ),
    "similar": (
        "Các sản phẩm tương tự:\n{product_list}\n"
        "Dựa trên đặc điểm và mô tả sản phẩm."
    ),
    "best": (
        "Sản phẩm được đánh giá cao nhất:\n{product_list}\n"
        "Xếp hạng theo rating và số lượng đánh giá."
    ),
    "info": (
        "Thông tin sản phẩm liên quan:\n{product_list}\n"
        "{history_note}"
    ),
    "default": (
        "Đây là các sản phẩm phù hợp với yêu cầu của bạn:\n{product_list}\n"
        "{history_note}"
    ),
}


def _detect_intent(query: str) -> str:
    q = query.lower()
    for keywords, intent in _INTENTS:
        if any(kw in q for kw in keywords):
            return intent
    return "default"


def _format_product(p: dict, idx: int) -> str:
    price = p.get("price", "N/A")
    rating = p.get("rating", "N/A")
    name = p.get("name", "Unknown")
    brand = p.get("brand", "")
    brand_str = f" ({brand})" if brand else ""
    return f"  {idx}. {name}{brand_str} — ₹{price}, ⭐ {rating}"


def chat(query: str, graph_context: list[dict], vector_results: list[dict],
         products_map: dict) -> str:
    """
    Generate response from graph context + vector search results.
    No external API needed.

    Args:
        query: user's question
        graph_context: list of dicts from Neo4j (user history)
        vector_results: list of dicts from FAISS search [{id, score}]
        products_map: {product_id: dict} from product-service HTTP API
    """
    intent = _detect_intent(query)
    template = _TEMPLATES[intent]

    # Build product list from vector results
    lines = []
    for i, vr in enumerate(vector_results[:5], 1):
        p = products_map.get(vr["id"])
        if p:
            lines.append(_format_product(p, i))
    product_list = "\n".join(lines) if lines else "  Không tìm thấy sản phẩm phù hợp."

    # Build history note
    history_note = ""
    if graph_context:
        viewed = [c["product"] for c in graph_context if c.get("product")][:3]
        if viewed:
            history_note = f"Bạn đã xem: {', '.join(viewed)}."

    return template.format(product_list=product_list, history_note=history_note)
