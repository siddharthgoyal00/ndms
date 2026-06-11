"""
ai_service.py — Flask entry point for the AI container

Endpoints:
  POST /ai/query   — Natural language → SQL → result
  GET  /health     — Liveness probe

Port: 5002
"""
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS

from engine.schema_loader  import load_schema
from engine.prompt_builder import build_prompt
from engine.llm_client     import call_llm
from engine.sql_validator  import validate_sql
from engine.executor       import run_query

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [AI] %(levelname)s — %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)


# ── Main endpoint ─────────────────────────────────────────────────────────────

@app.route("/ai/query", methods=["POST"])
def ai_query():
    body     = request.get_json(silent=True) or {}
    question = body.get("query", "").strip()

    if not question:
        return jsonify({"error": "query field is required"}), 400

    logger.info(f"Received question: {question!r}")

    try:
        schema         = load_schema()
        prompt         = build_prompt(question, schema)
        raw_sql        = call_llm(prompt)
        sql, clean_err = _clean_sql(raw_sql)

        if clean_err:
            return jsonify({"answer": None, "sql": raw_sql, "data": [], "error": clean_err})

        valid, reason = validate_sql(sql)
        if not valid:
            logger.warning(f"SQL blocked: {reason} | SQL: {sql}")
            return jsonify({"answer": None, "sql": sql, "data": [], "error": reason})

        data = run_query(sql)
        logger.info(f"Query returned {len(data)} rows")
        return jsonify({
            "answer": f"Query returned {len(data)} row(s).",
            "sql":    sql,
            "data":   data,
            "error":  None,
        })

    except Exception as e:
        logger.error(f"Unhandled error: {e}", exc_info=True)
        return jsonify({"answer": None, "sql": None, "data": [], "error": str(e)}), 500


@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "ai"}), 200


# ── Helpers ───────────────────────────────────────────────────────────────────

def _clean_sql(raw: str) -> tuple[str, str | None]:
    """
    Strip markdown code fences the LLM may wrap around SQL.
    Returns (cleaned_sql, error_or_None).
    """
    import re
    sql = re.sub(r"```(?:sql)?", "", raw).replace("```", "").strip()
    if not sql:
        return "", "LLM returned an empty response"
    return sql, None


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=False)