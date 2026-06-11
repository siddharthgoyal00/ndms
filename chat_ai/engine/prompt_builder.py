"""
engine/prompt_builder.py

Builds the system + user prompt sent to DeepSeek Coder 6.7B Instruct.

DeepSeek Coder Instruct uses the ChatML format:
    ### System:
    ...
    ### Human:
    ...
    ### Assistant:

Keeping the prompt compact is important for a Q4_K_M quantised model —
every extra token costs inference speed on CPU.
"""

# ── System preamble ────────────────────────────────────────────────────────────
_SYSTEM = """You are a SQL expert assistant for the NISAR satellite analytics database.
Your ONLY job is to write a single, correct PostgreSQL SELECT query.

Rules you MUST follow:
1. Output ONLY the raw SQL — no explanation, no markdown, no code fences.
2. Only use SELECT. Never use INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, GRANT, REVOKE.
3. Only query tables: analytic_table, rc_cache.
4. Always add LIMIT 100 unless the query is COUNT-only.
5. Use double-quotes for column names that contain uppercase letters.
6. If you cannot answer with the available schema, output exactly: CANNOT_ANSWER"""

# ── Few-shot examples ──────────────────────────────────────────────────────────
_EXAMPLES = [
    (
        "How many total observations are there?",
        'SELECT COUNT(DISTINCT observation_id) AS total FROM analytic_table;',
    ),
    (
        "Show RIFG products where L0 status is completed",
        "SELECT observation_id, product_name, L0_status, CMD_SSAR_START_DATETIME "
        "FROM analytic_table "
        "WHERE product_name = 'RIFG' AND LOWER(L0_status) = 'completed' "
        "LIMIT 100;",
    ),
    (
        "Monthly observation counts",
        "SELECT TO_CHAR(CMD_SSAR_START_DATETIME, 'YYYY-MM') AS month, "
        "COUNT(*) AS count "
        "FROM analytic_table "
        "WHERE CMD_SSAR_START_DATETIME IS NOT NULL "
        "GROUP BY month ORDER BY month;",
    ),
    (
        "List all distinct product names",
        "SELECT DISTINCT product_name FROM analytic_table ORDER BY product_name LIMIT 100;",
    ),
    (
        "How many observations failed at L1 stage?",
        "SELECT COUNT(*) AS failed_l1 FROM analytic_table WHERE LOWER(L1_status) = 'failed';",
    ),
]


def build_prompt(question: str, schema: str) -> str:
    """
    Returns a ChatML-formatted prompt string ready to send to Ollama.

    Args:
        question: The user's natural-language question.
        schema:   Output from schema_loader.load_schema().
    """
    shots = "\n\n".join(
        f"Q: {q}\nA: {a}" for q, a in _EXAMPLES
    )

    return (
        f"### System:\n{_SYSTEM}\n\n"
        f"Database schema:\n{schema}\n\n"
        f"Examples:\n{shots}\n\n"
        f"### Human:\n{question}\n\n"
        f"### Assistant:\n"
    )