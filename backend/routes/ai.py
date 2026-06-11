"""
routes/ai.py — POST /ai/query

The backend acts as a thin proxy to the AI container (ai_service:5002).
This keeps the frontend talking to a single origin (port 5000) and lets
the AI container remain internal (not exposed to the browser directly).

Response shape passed straight through from ai_service:
  {
    "answer": "Query returned N rows.",  # or null
    "sql":    "SELECT ...",              # generated SQL
    "data":   [ {...}, ... ],            # rows as list of dicts
    "error":  null                       # or validation / runtime error string
  }
"""
import os
import logging

import requests
from flask import Blueprint, request, jsonify

ai_bp = Blueprint("ai", __name__)
logger = logging.getLogger(__name__)

# Reads AI_SERVICE_URL from environment (set in docker-compose)
# Falls back to localhost for local dev without Docker
_AI_URL = os.environ.get("AI_SERVICE_URL", "http://localhost:5002")


@ai_bp.route("/ai/query", methods=["POST"])
def ai_query():
    body     = request.get_json(silent=True) or {}
    question = body.get("query", "").strip()

    if not question:
        return jsonify({"error": "query field is required"}), 400

    try:
        resp = requests.post(
            f"{_AI_URL}/ai/query",
            json    = {"query": question},
            timeout = 130,   # slightly longer than LLM_TIMEOUT (120s) in ai container
        )
        resp.raise_for_status()
        return jsonify(resp.json())

    except requests.exceptions.ConnectionError:
        logger.error("Cannot reach ai_service container")
        return jsonify({
            "answer": None,
            "sql":    None,
            "data":   [],
            "error":  "AI service is unavailable. Please try again shortly.",
        }), 503

    except requests.exceptions.Timeout:
        logger.error("ai_service timed out")
        return jsonify({
            "answer": None,
            "sql":    None,
            "data":   [],
            "error":  "The model took too long to respond. Try a simpler question.",
        }), 504

    except Exception as e:
        logger.error(f"ai proxy error: {e}")
        return jsonify({
            "answer": None,
            "sql":    None,
            "data":   [],
            "error":  str(e),
        }), 500

