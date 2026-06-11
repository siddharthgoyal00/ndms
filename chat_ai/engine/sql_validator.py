"""
engine/sql_validator.py

Two-layer SQL safety check before any query hits postgres:

  Layer 1 — Keyword blocklist:  rejects any DDL / DML keyword.
  Layer 2 — Table allowlist:    only analytic_table and rc_cache may be queried.

Returns (is_valid: bool, reason: str).
"""
import re
import logging

logger = logging.getLogger(__name__)

# ── Blocked DML / DDL keywords ─────────────────────────────────────────────────
_BLOCKED_KEYWORDS: set[str] = {
    "insert", "update", "delete", "drop", "truncate",
    "alter",  "create", "grant",  "revoke", "replace",
    "copy",   "vacuum", "analyze", "reindex",
}

# ── Tables the AI is allowed to touch ─────────────────────────────────────────
_ALLOWED_TABLES: set[str] = {
    "analytic_table",
    "rc_cache",
    "public.analytic_table",
    "public.rc_cache",
}

# Regex to extract table names from FROM / JOIN clauses
_TABLE_PATTERN = re.compile(
    r'(?:from|join)\s+([\w.]+)',
    re.IGNORECASE,
)


def validate_sql(sql: str) -> tuple[bool, str]:
    """
    Returns (True, "ok") if safe, or (False, "<reason>") if blocked.
    """
    if not sql or not sql.strip():
        return False, "Empty SQL"

    sql_lower = sql.lower().strip()

    # ── Layer 1: must be a SELECT ──────────────────────────────────────────────
    if not sql_lower.startswith("select"):
        return False, "Only SELECT queries are allowed"

    # ── Layer 2: blocked keyword scan ─────────────────────────────────────────
    for kw in _BLOCKED_KEYWORDS:
        if re.search(r'\b' + kw + r'\b', sql_lower):
            logger.warning(f"validate_sql: blocked keyword '{kw}' found")
            return False, f"Blocked keyword detected: '{kw}'"

    # ── Layer 3: table allowlist ───────────────────────────────────────────────
    referenced = {m.group(1).lower() for m in _TABLE_PATTERN.finditer(sql)}
    disallowed  = referenced - {t.lower() for t in _ALLOWED_TABLES}
    if disallowed:
        logger.warning(f"validate_sql: disallowed tables {disallowed}")
        return False, f"Query references disallowed table(s): {', '.join(disallowed)}"

    # ── Layer 4: CANNOT_ANSWER sentinel from LLM ──────────────────────────────
    if "cannot_answer" in sql_lower:
        return False, "The model could not answer this question with the available schema"

    return True, "ok"