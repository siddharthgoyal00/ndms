"""
routes/ai.py — POST /ai/query
Text-to-SQL AI assistant endpoint.
"""
from flask import Blueprint, request, jsonify
from services.ai_service import answer_query

ai_bp = Blueprint("ai", __name__)


@ai_bp.route("/ai/query", methods=["POST"])
def ai_query():
    body     = request.get_json(silent=True) or {}
    question = body.get("query", "").strip()

    if not question:
        return jsonify({"error": "query field is required"}), 400

    result = answer_query(question)
    return jsonify(result)