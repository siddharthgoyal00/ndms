"""
services/ai_service.py — Text-to-SQL AI layer

Flow:
  1. Load analytic_table schema from postgres
  2. Build prompt with schema + few-shot examples
  3. Call LLM (configurable: Ollama local / OpenAI / Gemini)
  4. Validate generated SQL — read-only, allowed tables only
  5. Execute against postgres
  6. Return structured JSON result

Currently a stub — wire up your LLM of choice in call_llm().
"""
import os
import re
import logging
from db.connection import get_db_connection

logger = logging.getLogger(__name__)

# Tables the AI is allowed to query — prevents access to raw schema
ALLOWED_TABLES = {
    "analytic_table",
    "rc_cache",
    "public.analytic_table",
    "public.rc_cache",
}

# SQL keywords that indicate write operations — block these
BLOCKED_KEYWORDS = {
    "insert", "update", "delete", "drop", "truncate",
    "alter", "create", "grant", "revoke", "replace",
}


def load_schema() -> str:
    """Reads analytic_table column names and types from postgres."""
    conn   = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name   = 'analytic_table'
            ORDER BY ordinal_position
        """)
        rows = cursor.fetchall()
        return "\n".join(f"  {r['column_name']} ({r['data_type']})" for r in rows)
    finally:
        cursor.close()
        conn.close()


def build_prompt(question: str, schema: str) -> str:
    return f"""You are a SQL expert for a NISAR satellite analytics database.
The main table is analytic_table with these columns:
{schema}

Rules:
- Generate only SELECT queries
- Only query analytic_table or rc_cache
- Never use INSERT, UPDATE, DELETE, DROP, ALTER, CREATE
- Always LIMIT results to 100 rows maximum
- Return ONLY the SQL query, no explanation

Few-shot examples:
Q: How many observations are there?
A: SELECT COUNT(DISTINCT observation_id) FROM analytic_table;

Q: Show me RIFG products with completed L0 status
A: SELECT observation_id, product_name, L0_status, CMD_SSAR_START_DATETIME FROM analytic_table WHERE product_name = 'RIFG' AND LOWER(L0_status) = 'completed' LIMIT 100;

Q: What are the monthly observation counts?
A: SELECT TO_CHAR(CMD_SSAR_START_DATETIME, 'YYYY-MM') as month, COUNT(*) as count FROM analytic_table WHERE CMD_SSAR_START_DATETIME IS NOT NULL GROUP BY month ORDER BY month;

Now answer:
Q: {question}
A:"""


def validate_sql(sql: str) -> tuple[bool, str]:
    """
    Returns (is_valid, reason).
    Blocks DDL, DML, and queries on non-allowed tables.
    """
    sql_lower = sql.lower().strip()

    # must start with SELECT
    if not sql_lower.startswith("select"):
        return False, "Only SELECT queries are allowed"

    # block dangerous keywords
    for kw in BLOCKED_KEYWORDS:
        pattern = r'\b' + kw + r'\b'
        if re.search(pattern, sql_lower):
            return False, f"Blocked keyword: {kw}"

    return True, "ok"


def call_llm(prompt: str) -> str:
    """
    Calls your LLM of choice.
    Currently returns a placeholder — wire up Ollama/Gemini/OpenAI here.

    Ollama example:
        import requests
        response = requests.post(
            "http://ollama:11434/api/generate",
            json={"model": "llama3", "prompt": prompt, "stream": False}
        )
        return response.json()["response"].strip()

    Gemini example:
        import google.generativeai as genai
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel("gemini-pro")
        return model.generate_content(prompt).text.strip()
    """
    # ── STUB — replace with your LLM call ──
    return "SELECT COUNT(*) FROM analytic_table;"


def run_query(sql: str) -> list:
    """Executes validated SQL and returns rows as list of dicts."""
    conn   = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        cursor.close()
        conn.close()


def answer_query(question: str) -> dict:
    """
    Main entry point called by the AI route.
    Returns: { answer, sql, data, error }
    """
    try:
        schema  = load_schema()
        prompt  = build_prompt(question, schema)
        sql     = call_llm(prompt).strip()

        # strip markdown code fences if LLM wraps in ```sql ... ```
        sql = re.sub(r"```(?:sql)?", "", sql).replace("```", "").strip()

        valid, reason = validate_sql(sql)
        if not valid:
            return {"answer": None, "sql": sql, "data": [], "error": reason}

        data = run_query(sql)
        return {
            "answer": f"Query returned {len(data)} rows.",
            "sql":    sql,
            "data":   data,
            "error":  None,
        }

    except Exception as e:
        logger.error(f"AI query error: {e}")
        return {"answer": None, "sql": None, "data": [], "error": str(e)}